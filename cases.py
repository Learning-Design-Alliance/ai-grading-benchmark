"""
The case format, and loaders that turn a corpus you downloaded yourself into it.

A case is one piece of student work, as one JSON object per line:

    {"id": "E01.Q01.A00",            unique
     "task": "E01.Q01",              the question or assignment it answers; probes and the
                                     off-task control use it, so cases from one task share it
     "question": "...",              what the student was asked
     "reference": "...",             a model answer, if there is one ("" otherwise)
     "rubric": "...",                the marking guide ("" otherwise)
     "materials": "...",             source texts the task supplied ("" otherwise)
     "response": "...",              the student's work
     "scale": [0, 5],                the mark range
     "human": {"grader_1": 3, "grader_2": 4},
                                     every human mark, by rater. Two or more raters on some cases
                                     give the benchmark a ceiling; with one, it says so and
                                     reports no share of the ceiling.
     "groups": {"ell": "Yes"}}       optional. Analysis only: NEVER rendered into a prompt.

Your own data in this format works the same as the built-in corpora.

LICENCES. Neither loader ships data. Mohler (CC BY 4.0, Mohler, Bunescu and Mihalcea 2011) and
ASAP 2.0 (CC BY 4.0, Crossley, Baffour, Burleigh and King 2025) are fetched by the user; see the
README for where. Credit both if you publish results from them.
"""

import csv
import json
import os
import re
import sys

FIELDS = ("id", "task", "question", "reference", "rubric", "materials", "response", "scale", "human")


def validate(case):
    errs = []
    for f in ("id", "task", "response", "scale", "human"):
        if f not in case:
            errs.append(f"missing {f}")
    if errs:
        return errs
    lo, hi = case["scale"]
    if not lo < hi:
        errs.append("scale must be [low, high] with low < high")
    if not case["human"] and not case.get("generator"):
        errs.append("no human mark")
    for r, s in case["human"].items():
        if not (isinstance(s, (int, float)) and lo <= s <= hi):
            errs.append(f"human mark {r}={s!r} outside the scale")
    if not str(case["response"]).strip():
        errs.append("empty response")
    return errs


def normalise(case):
    out = {f: case.get(f, "") for f in FIELDS}
    out["groups"] = {k: str(v) for k, v in (case.get("groups") or {}).items() if str(v).strip()}
    for k in ("generator", "level"):
        if case.get(k):
            out[k] = case[k]
    return out


def load(path):
    cases, seen = [], set()
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            c = json.loads(line)
            errs = validate(c)
            if errs:
                sys.exit(f"{path}:{n}: {'; '.join(errs)}")
            if c["id"] in seen:
                sys.exit(f"{path}:{n}: duplicate id {c['id']}")
            seen.add(c["id"])
            cases.append(normalise(c))
    return cases


def write(cases, path):
    with open(path, "w", encoding="utf-8") as fh:
        for c in cases:
            fh.write(json.dumps(c, ensure_ascii=False) + "\n")


def sample(cases, n, seed):
    """n cases, stratified on the mean human mark: sorted by (mark, id) and taken at an even step,
    as the research harness draws (stratifying cut the sampling SD threefold on JorGPT). The same
    file and n give the same cases on any machine; `seed` is unused here and kept for the probes."""
    if n is None or n >= len(cases):
        return list(cases)
    key = lambda c: (sum(c["human"].values()) / len(c["human"]), c["id"])
    ordered = sorted(cases, key=key)
    step = max(1, len(ordered) // n)
    return sorted([c for i, c in enumerate(ordered) if i % step == 0][:n], key=lambda c: c["id"])


# ------------------------------------------------------------------ built-in corpora

def from_mohler(path):
    """Mohler ASAG, the CSV derived from the Hugging Face parquet (see README).

    Kept rows are the research harness's (`harness/dataset.ts` loadMohler): both graders on 0-5 (the
    0-10 questions E11-E12 are dropped, not rescaled), the published average equal to the two marks'
    mean, and non-empty question and answer. 1,727 rows; human ceiling QWK 0.519.
    """
    out = []
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                a, b, avg = float(r["score_grader_1"]), float(r["score_grader_2"]), float(r["score_avg"])
            except (TypeError, ValueError):
                continue
            if not (0 <= a <= 5 and 0 <= b <= 5) or abs((a + b) / 2 - avg) > 1e-9:
                continue
            q, ans = r["question"].replace("<STOP>", "").strip(), r["student_answer"].replace("<STOP>", "").strip()
            if not q or not ans:
                continue
            out.append(normalise({
                "id": r["id"], "task": ".".join(r["id"].split(".")[:2]), "question": q,
                "reference": r["instructor_answer"].replace("<STOP>", "").strip(),
                "response": ans, "scale": [0, 5], "human": {"grader_1": a, "grader_2": b},
            }))
    return out


# ASAP 2.0 ships prompts and scores but not the raters' rubric text. This is the corpus's 1-6
# holistic scale in its data paper's terms, as the research harness states it (harness/asap2.ts).
ASAP2_RUBRIC = (
    "Score the essay holistically from 1 to 6 on how effectively it argues or explains its position "
    "using the source text(s) provided in the assignment.\n"
    "6: a well-developed, clearly organised response that takes a clear position, supports it with "
    "specific and well-chosen evidence from the sources, and controls language and conventions.\n"
    "5: a developed and organised response with adequate source evidence and generally controlled language.\n"
    "4: an adequate response with a discernible position and some source evidence; organisation and "
    "control are inconsistent.\n"
    "3: a partially developed response; the position may be unclear, evidence thin or only loosely "
    "tied to the sources, with lapses in organisation and control.\n"
    "2: a minimally developed response with little source evidence and weak organisation or control.\n"
    "1: a response that is undeveloped, off-topic, or too brief to show a position."
)

ASAP2_GROUPS = {"ell": "ell_status", "economic": "economically_disadvantaged",
                "disability": "student_disability_status", "race": "race_ethnicity", "gender": "gender"}


def from_asap2(path, max_chars=12000):
    """ASAP 2.0, ASAP2_train_sourcetexts.csv. One rater, so no ceiling; five demographic fields.

    Blank demographic values are left out, never coded as a group: a blank is not a group, and
    missingness differs by field (4,005 essays lack economic status, 442 lack ELL status).
    """
    csv.field_size_limit(10 ** 9)
    out = []
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                s = float(r["score"])
            except (TypeError, ValueError):
                continue
            text = (r["full_text"] or "").strip()
            if not text:
                continue
            sources = [r.get(f"source_text_{i}", "").strip() for i in range(1, 5)]
            out.append(normalise({
                "id": r["essay_id"], "task": r["prompt_name"], "question": r["assignment"].strip(),
                "rubric": ASAP2_RUBRIC,
                "materials": "\n\n".join(f"Source {i + 1}:\n{t}" for i, t in enumerate(sources) if t),
                "response": text[:max_chars], "scale": [1, 6], "human": {"rater": s},
                "groups": {k: r.get(col, "") for k, col in ASAP2_GROUPS.items() if r.get(col, "").strip().upper() != "NA"},
            }))
    return out


def from_harmogen(root, kind="code"):
    """HARMOGEN-R (Mendonca, Quintal, Mendonca and Baras 2026, CC BY 4.0), a university data-structures
    course in Portuguese: four instructors marked every response. `root` is the extracted deposit
    (the folder holding csv/tables/). Kept: open responses only (a bare option letter, the deposit's
    multiple-choice half, is dropped: every marker agrees on it, which inflates any ceiling), of
    question type `kind` ("code" or "text"), with the instructors' own rubric (rubric source 1 of
    the five; the other four are AI-generated) and the four instructors' active marks under it.
    The scale is the question's points (code: 0-90). One loader call gives one scale; for "text" the
    20- and 50-point questions are split by `kind="text20"` / `"text50"`.
    """
    import html as _html
    import re as _re
    csv.field_size_limit(10 ** 9)
    t = os.path.join(root, "csv", "tables")
    rd = lambda f: [{k.lstrip("\ufeff").strip('"'): v for k, v in r.items()}
                    for r in csv.DictReader(open(os.path.join(t, f + ".csv"), encoding="utf-8"))]
    strip = lambda x: _re.sub(r"\s+\n", "\n", _html.unescape(_re.sub(r"<[^>]+>", " ", x or ""))).strip()
    qs = {q["id"]: q for q in rd("questions") if q["is_active"] == "1"}
    crit = {}
    for c in rd("question_criterias"):
        if c["source"] == "1" and c["is_active"] == "1":
            crit.setdefault(c["question_id"], []).append(
                f"- {c['title'].strip()} ({float(c['score']):g} points): {c['description'].strip()}\n  {c['score_criteria'].strip()}")
    marks = {}
    for e in rd("evaluations"):
        if e["evaluator_type"] == "teacher" and e["source_question_criteria"] == "1" and e["is_active"] == "1" and e["score"] != "":
            marks.setdefault(e["student_response_id"], {})[f"instructor_{e['evaluator_id']}"] = float(e["score"])
    bare = _re.compile(r"^\s*[A-Ea-e]\s*[).]?\s*$")
    want_type, want_max = {"code": ("code", None), "text20": ("text", 20.0), "text50": ("text", 50.0)}[kind]
    out = []
    for r in rd("student_responses"):
        q = qs.get(r["question_id"])
        if not q or r["is_active"] != "1" or bare.match(r["response"] or "") or q["type"] != want_type:
            continue
        top = float(q["score"])
        if want_max is not None and top != want_max:
            continue
        h = marks.get(r["id"], {})
        if len(h) < 2 or not (r["response"] or "").strip():
            continue
        out.append(normalise({"id": f"hg{r['id']}", "task": f"Q{r['question_id']}", "question": strip(q["question"]),
                              "rubric": "\n".join(crit.get(r["question_id"], [])), "response": r["response"].strip(),
                              "scale": [0, top], "human": h}))
    return out


MENAGERIE_SCALE = ["F", "D-", "D", "D+", "C-", "C", "C+", "B-", "B", "B+", "A-", "A", "A+", "A++"]
MENAGERIE_TASK = ("A second-semester CS1 Java assignment. Students extended a supplied predator/prey simulation template "
                  "(a field as a 2D array, plus Fox and Rabbit) to add at least five species with at least two predators "
                  "and two non-predators, at least two predators competing for one food source, sex-based propagation "
                  "requiring neighbouring male and female animals, and time of day affecting some species' behaviour. "
                  "Students then chose one or more challenge tasks of their own, such as plant lifecycles, weather, or disease.")
MENAGERIE_RUBRIC = {
    "Correctness": ["A: The application works as described in the assignment; all base tasks are completed; the student has completed some of the challenge tasks; the student included documentation describing the challenge tasks that were completed and how; all submission instructions were followed correctly. (Higher A grades add originality, creativity and technical excellence in all challenge tasks.)",
                    "B: The application works as described in the assignment; all the base tasks are completed, however, no challenge task was attempted; all submission instructions were followed correctly.",
                    "C: Minor details of a task(s) are violated; the application functions correctly on the majority inputs/actions.",
                    "D: Some tasks are incomplete; the application functions incorrectly on some inputs/actions.",
                    "F: Significant details of a task are violated, or the program often exhibits incorrect behaviour; the applications does not open or run in BlueJ; Java files are missing."],
    "Code Elegance": ["A: All of the base tasks and some of the challenge tasks are implemented in such a way that code can be reused, where possible; the majority of the code is written in such a way that is easy to maintain, i.e., add new or extend features; the code is efficient without sacrificing readability and understanding.",
                      "B: The application is implemented in such a way that only a few code segments could be rewritten to increase code re-usability; the code is fairly efficient without sacrificing readability and understanding; the student made a poor design choice in a single area.",
                      "C: The application is implemented in such a way that many code segments (or functions) could be rewritten to increase code re-usability; some of the code is unnecessarily complex or poorly designed.",
                      "D: The application is unnecessarily complex and/or uses brute force; the application contains many instances where the code could have been written in an easier, faster or better fashion.",
                      "F: The application is not organised for re-usability, e.g., all the code is in a single class (or function); no effort is made to create reusable code; the application is excessively long and poorly organised."],
    "Documentation": ["A: The documentation consists of comments that are useful in understanding the code and/or structure of the program; each file has header information (e.g., student name and k-number). (Higher A grades: every class, function, and non-obvious block documented.)",
                      "B: The documentation consists of comments that are somewhat useful in understanding the code; some of the comments state the obvious.",
                      "C: The documentation is simply comments embedded in the code but does not help the reader understand the code.",
                      "D: One or more code segments could benefit from comments or the code is overly commented.",
                      "F: The application has no comments, not even the header with the student's name or k-number."],
    "Readability": ["A: The code is clean, understandable and organised; the student used meaningful identifier names, i.e., good function and variables names; the student used white space between logical code blocks. (Higher A grades: exceptionally well organised, consistent indentation and spacing, single-purpose functions, encapsulation.)",
                    "B: The application has minor issues such as inconsistent indentation.",
                    "C: The application has one or two issues that makes the program difficult to understand such as poorly named identifiers and disorganised code.",
                    "D: The application has more than two issues that makes the program difficult to understand.",
                    "F: The code is readable only by someone who knows what it is supposed do; the application has several issues that makes the program difficult to understand."],
}


def from_menagerie(root, max_chars=90000):
    """Menagerie (Messer et al. 2024, OSF q8jbt, CC BY 4.0): 279 CS1 Java projects re-graded on four rubric
    dimensions by 28 recruited graders, three or four per item. `root` holds grades.csv and src/ with the
    four year archives extracted into directories of their own names (data/data-sources.json says how).

    One case per (submission, dimension): the task is the dimension, so each dimension is its own task. The
    response is the submission's .java files as written (layout is evidence for readability), cut at
    max_chars with a marker; the rubric is the markers' own band descriptors for that dimension
    (research harness: harness/menagerie.ts). Letter grades are collapsed to the bare letter, F=0 to A=4,
    the granularity the earlier study compared with Mohler's 0-5. These are recruited re-grades, not the
    students' awarded grades. Raters' written comments are in grades.csv and are not used here.
    """
    import glob as _glob
    csv.field_size_limit(10 ** 9)
    letter = lambda g: "FDCBA".index(g[0]) if g in MENAGERIE_SCALE else None
    grades = {}
    with open(os.path.join(root, "grades.csv"), newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            v = letter((r.get("grade") or "").strip())
            if v is None:
                continue
            aid = str(r["assignment_number"]).strip()
            aid = aid[:-2] if aid.endswith(".0") else aid
            grades.setdefault((aid, r["skill"].strip()), {})[f"grader_{r['participant_id']}"] = float(v)
    code = {}
    for sub in sorted(_glob.glob(os.path.join(root, "src", "*", "*", "*_Submission_*"))) + \
               sorted(_glob.glob(os.path.join(root, "src", "*", "*_Submission_*"))):
        m = re.search(r"_Submission_(\d+)$", sub)
        if not m or m.group(1) in code or "__MACOSX" in sub:
            continue
        files = sorted(_glob.glob(os.path.join(sub, "**", "*.java"), recursive=True))
        if not files:
            continue
        text = "\n\n".join(f"// ==== {os.path.basename(f)} ====\n" + open(f, encoding="utf-8", errors="replace").read() for f in files)
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n// [truncated]"
        code[m.group(1)] = text
    out = []
    for (aid, skill), h in sorted(grades.items()):
        if len(h) < 2 or aid not in code or skill not in MENAGERIE_RUBRIC:
            continue
        out.append(normalise({"id": f"men{aid}|{skill}", "task": skill,
                              "question": f"{MENAGERIE_TASK}\n\nGrade the submission on {skill} only.",
                              "rubric": "\n".join(MENAGERIE_RUBRIC[skill]) + "\nMark on 0-4: F=0, D=1, C=2, B=3, A=4.",
                              "response": code[aid], "scale": [0, 4], "human": h}))
    return out


PERSUADE_GROUPS = {"grade": "grade_level", "ell": "ell_status", "economic": "economically_disadvantaged",
                   "disability": "student_disability_status", "race": "race_ethnicity", "gender": "gender"}


def from_persuade(path, task_kind="Independent", exclude=None, max_chars=12000):
    """PERSUADE 2.0 (Crossley et al. 2024, CC BY-NC-SA 4.0: non-commercial use only), train.csv: argumentative
    essays from grades 6-12 with a holistic 1-6 score (one rater) and six demographic fields, one row per
    discourse element, so essays are de-duplicated on essay_id_comp. `task_kind` "Independent" keeps the
    essays written without source texts (cheap prompts, a different answer type from ASAP 2.0's); "Text
    dependent" keeps the source-based ones. `exclude` is a cases file whose essay texts are dropped (pass
    ASAP 2.0's, which was drawn from PERSUADE, so the two corpora stay independent). Grade level is kept as
    a group: the earlier study's widest gap was grade 6 against grade 9.
    """
    csv.field_size_limit(10 ** 9)
    skip = set()
    if exclude:
        with open(exclude, encoding="utf-8") as fh:
            for line in fh:
                skip.add(" ".join(json.loads(line)["response"].split())[:300])
    out, seen = [], set()
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            eid = r["essay_id_comp"]
            if eid in seen or r["task"] != task_kind:
                continue
            seen.add(eid)
            text = (r["full_text"] or "").strip()
            try:
                score = float(r["holistic_essay_score"])
            except (TypeError, ValueError):
                continue
            if not text or " ".join(text.split())[:300] in skip:
                continue
            out.append(normalise({
                "id": f"per{eid}", "task": r["prompt_name"], "question": (r["assignment"] or "").strip(),
                "rubric": ASAP2_RUBRIC.replace("using the source text(s) provided in the assignment", "in response to the assignment")
                if task_kind == "Independent" else ASAP2_RUBRIC,
                "materials": (r["source_text"] or "").strip(), "response": text[:max_chars], "scale": [1, 6],
                "human": {"rater": score},
                "groups": {k: (f"grade {r[col].strip()}" if k == "grade" else r[col].strip())
                           for k, col in PERSUADE_GROUPS.items() if (r.get(col) or "").strip() and r[col].strip().upper() != "NA"},
            }))
    return out


ELLIPSE_RUBRIC = (
    "Score the essay holistically from 1 to 5 for the writer's overall English language proficiency (ELLIPSE "
    "holistic rubric, Crossley et al. 2023). 5: native-like facility in the use of language with syntactic "
    "variety; appropriate word choice and phrases; well-controlled text organization; precise use of grammar and "
    "conventions; rare language inaccuracies that do not impede communication. 4: facility in the use of language "
    "with syntactic variety and range of words and phrases; controlled organization; accuracy in grammar and "
    "conventions; occasional language inaccuracies that rarely impede communication. 3: facility limited to the "
    "use of common structures and generic vocabulary; organization generally controlled although connection "
    "sometimes absent or unsuccessful; errors in grammar and syntax and usage; communication is impeded by "
    "language inaccuracies in some cases. 2: inconsistent facility in sentence formation, word choice, and "
    "mechanics; organization partially developed but may be missing or unsuccessful; communication impeded in "
    "many instances by language inaccuracies. 1: a limited range of familiar words or phrases loosely strung "
    "together; frequent errors in grammar (including syntax) and usage; communication impeded in most cases by "
    "language inaccuracies.")
ELLIPSE_GROUPS = {"economic": "SES", "race": "race_ethnicity", "gender": "gender", "grade": "grade"}


def from_ellipse(path, max_chars=12000):
    """ELLIPSE (Crossley et al. 2023, CC BY-NC-SA 4.0; registry id `persuade-ellipse`): essays by English
    learners in grades 8-12, each rated independently by TWO raters on a 1-5 holistic proficiency rubric.
    `path` is the directory holding the raw rater file (ellipsis_raw_rater_scores_anon_all_essay.csv, from the
    password-protected zip in the ellipse-corpus repo) and the final corpus's train and test CSVs, which carry
    the prompt and the demographic fields. Only essays in the final corpus are kept (the authors dropped
    essays and raters they found unreliable), joined on text_id_kaggle; a rating of 0 (unscorable) drops the
    essay. Both raters are kept as human marks, so the benchmark computes a ceiling."""
    csv.field_size_limit(10 ** 9)
    meta = {}
    for name in ("ELLIPSE_Final_github_train.csv", "ELLIPSE_Final_github_test.csv"):
        f = os.path.join(path, name)
        with open(f, newline="", encoding="utf-8", errors="replace") as fh:
            for r in csv.DictReader(fh):
                meta[r["text_id_kaggle"]] = r
    out = []
    with open(os.path.join(path, "ellipsis_raw_rater_scores_anon_all_essay.csv"), newline="", encoding="utf-8",
              errors="replace") as fh:
        for r in csv.DictReader(fh):
            m = meta.get(r["text_id_kaggle"])
            if m is None:
                continue
            try:
                a, b = float(r["Overall_1"]), float(r["Overall_2"])
            except (TypeError, ValueError):
                continue
            if a < 1 or b < 1:
                continue
            text = (m.get("full_text") or r["Text"] or "").strip()
            if not text:
                continue
            out.append(normalise({
                "id": f"ell{r['text_id_kaggle']}", "task": (m.get("prompt") or "ELLIPSE").strip(),
                "question": (m.get("prompt") or "").strip(), "rubric": ELLIPSE_RUBRIC, "materials": "",
                "response": text[:max_chars], "scale": [1, 5],
                "human": {"rater1": a, "rater2": b},
                "groups": {k: m[col].strip() for k, col in ELLIPSE_GROUPS.items() if (m.get(col) or "").strip()},
            }))
    return out


LOADERS = {"mohler": from_mohler, "asap2": from_asap2, "harmogen-code": lambda p: from_harmogen(p, "code"),
           "harmogen-text20": lambda p: from_harmogen(p, "text20"), "harmogen-text50": lambda p: from_harmogen(p, "text50"),
           "menagerie": from_menagerie, "persuade": from_persuade,
           "ellipse": from_ellipse}
