"""
Feedback quality: the paragraph the learner actually reads, measured without a human gold standard.

Ported from the research harness (the authors' earlier research harness, 2026-09-15), generalised from
Java submissions to any text, and extended with two checks it did not have (varied-by-quality within
a task, and answer leakage). Every measure here is a NECESSARY condition, not a sufficient one:
feedback can pass all of them and still be wrong about the work. Whether its claims are true of the
submission needs a marker reading both, and whether a learner acts on it needs a study. Neither is
approximated.

These are RULE-CODED, DESCRIPTIVE measures with no human reference sample (CLAUDE.md: a coded
construct names its coder and its agreement with an independent reference; this has none yet). They
describe a grader's feedback; they may not be used as a gate or target until validated.

WHERE THE FEEDBACK COMES FROM. The reply's JSON field `feedback`, else `evaluation` (used by some product prompts),
else `reason` (the default prompt's one-line reason, which is not feedback and is reported as such).
Only base gradings are read.

THE MEASURES, per run (within task, then averaged over tasks):
- words: mean length.
- generic: mean pairwise cosine (bag of content words) between feedback for DIFFERENT students on the
  same task. High = the same paragraph for everyone.
- varied_by_quality: mean cosine within the same human band minus mean cosine between bands at least
  half the scale apart. Positive = feedback for strong work differs from feedback for weak work. The
  harness found it at about 0 for its grader: "specific without discriminating".
- grounded: share of feedback naming at least one word that appears in THIS student's work but not in
  the question, model answer, rubric or materials, and in fewer than a fifth of the task's other
  responses: evidence the grader read this work rather than the brief.
- coherence: correlation between critical-phrase count and the mark. Should be negative.
- self_per100 / task_per100: phrases aimed at the person ("you", "the student") and at the work
  ("the code", "the answer"), per 100 words. Feedback aimed at the person is the least effective kind
  (Kluger and DeNisi 1996; Hattie and Timperley 2007).
- action_per100: phrases that say what to do next, per 100 words.
- leaks_answer: share of feedback on work the humans marked below the midpoint that reproduces five
  or more consecutive words of the model answer, i.e. hands the student the answer.
- same_opening: share of pairs that open with the same eight words.

The phrase measures (self, task, action, coherence) use English word lists and are skipped for
feedback that is not in English.
"""

import json
import re
from collections import defaultdict

from metrics import mean, pearson

STOP = set("""the a an and or but if of to in on for with is are was were be been being this that these those it
its as at by from not no you your they their there here have has had do does did will would can could should may
might must""".split())

RX = {
    "self": re.compile(r"\b(?:you|your|yours|the student|the author|the writer)\b", re.I),
    "task": re.compile(r"\b(?:the code|the class|the method|the function|the program|the answer|the response|the essay|"
                       r"the argument|the submission|the implementation|the explanation|the solution)\b", re.I),
    "action": re.compile(r"\b(?:should|could|consider|try|recommend|suggest|instead of|would benefit|needs? to|to improve|"
                         r"rather than|next time|make sure)\b", re.I),
    "critical": re.compile(r"\b(?:however|although|but |lacks?|missing|fails?|incorrect|inconsistent|unclear|poor|weak|"
                           r"does not|doesn't|could be improved|problem|issue|error|wrong)\b", re.I),
}


def english(s):
    """The phrase measures are English word lists: on other languages they read a false zero, so they
    are skipped (reported as n/a) where the common English words are rare."""
    w = re.findall(r"[a-z']+", (s or "").lower())
    return len(w) >= 8 and sum(x in ("the", "and", "is", "to", "of", "your", "with", "this") for x in w) / len(w) > 0.04


def tokens(s):
    return [w for w in re.findall(r"[a-zà-ÿ][a-zà-ÿ0-9_]{2,}", (s or "").lower()) if w not in STOP]


def cosine(a, b):
    ca, cb = defaultdict(int), defaultdict(int)
    for w in a:
        ca[w] += 1
    for w in b:
        cb[w] += 1
    dot = sum(n * cb.get(w, 0) for w, n in ca.items())
    na = sum(n * n for n in ca.values()) ** 0.5
    nb = sum(n * n for n in cb.values()) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def feedback_text(reply):
    """(text, field) from a reply, or (None, None)."""
    if not reply:
        return None, None
    t = reply.strip()
    if t.startswith("```"):
        t = t.strip("`").split("\n", 1)[-1]
    for cand in (t, t[t.find("{"): t.rfind("}") + 1] if "{" in t else ""):
        try:
            obj = json.loads(cand)
        except ValueError:
            continue
        if isinstance(obj, dict):
            for f in ("feedback", "evaluation", "reason"):
                if isinstance(obj.get(f), str) and obj[f].strip():
                    return obj[f].strip(), f
    return None, None


def shingles(ws, k=5):
    return {" ".join(ws[i:i + k]) for i in range(len(ws) - k + 1)}


def measure(cases, calls):
    by_id = {c["id"]: c for c in cases}
    items = []
    fields = defaultdict(int)
    for r in calls:
        if r["probe"] != "base" or r.get("score") is None:
            continue
        text, field = feedback_text(r.get("text"))
        if not text:
            continue
        fields[field] += 1
        items.append((by_id[r["id"]], r["score"], text))
    if len(items) < 20:
        return None
    lo, hi = cases[0]["scale"]
    width = hi - lo
    by_task = defaultdict(list)
    for c, s, t in items:
        by_task[c["task"]].append((c, s, t))
    task_resp_tokens = {k: [set(tokens(c["response"])) for c, _, _ in v] for k, v in by_task.items()}
    out = defaultdict(list)
    for task, rows in by_task.items():
        toks = [tokens(t) for _, _, t in rows]
        hmean = [mean(c["human"].values()) for c, _, _ in rows]
        sims, within, across, opens, same_open = [], [], [], [t.lower().split()[:8] for _, _, t in rows], 0
        pairs = 0
        for i in range(len(rows)):
            for k in range(i + 1, len(rows)):
                c_ = cosine(toks[i], toks[k])
                sims.append(c_)
                pairs += 1
                same_open += opens[i] == opens[k]
                d = abs(hmean[i] - hmean[k])
                if d < 0.5:
                    within.append(c_)
                elif d >= width / 2:
                    across.append(c_)
        if sims:
            out["generic"].append(mean(sims))
            out["same_opening"].append(same_open / pairs)
        if within and across:
            out["varied_by_quality"].append(mean(within) - mean(across))
        resp_sets = task_resp_tokens[task]
        for (c, s, t), ft in zip(rows, toks):
            brief = set(tokens(" ".join([c["question"], c["reference"], c["rubric"], c["materials"]])))
            mine = set(tokens(c["response"])) - brief
            common = {w for w in mine if sum(w in rs for rs in resp_sets) > max(1, len(resp_sets) / 5)}
            own = mine - common
            if own:
                out["grounded"].append(1.0 if own & set(ft) else 0.0)
            words = max(1, len(t.split()))
            out["words"].append(words)
            if english(t):
                out["self_per100"].append(100 * len(RX["self"].findall(t)) / words)
                out["task_per100"].append(100 * len(RX["task"].findall(t)) / words)
                out["action_per100"].append(100 * len(RX["action"].findall(t)) / words)
            if c["reference"] and mean(c["human"].values()) < lo + width / 2:
                ref = shingles(tokens(c["reference"]))
                if ref:
                    out["leaks_answer"].append(1.0 if ref & shingles(ft) else 0.0)
        if not all(english(t) for _, _, t in rows[:20]):
            continue
        crit = [len(RX["critical"].findall(t)) for _, _, t in rows]
        marks = [s for _, s, _ in rows]
        if len(rows) >= 10 and len(set(crit)) > 1 and len(set(marks)) > 1:
            out["coherence"].append(pearson(crit, marks))
    res = {k: mean(v) for k, v in out.items()}
    res["n"] = len(items)
    res["field"] = max(fields, key=fields.get)
    res["note"] = ("rule-coded descriptive measures with no human reference; see feedback.py"
                   + ("; the prompt returned a one-line reason, not feedback" if res["field"] == "reason" else ""))
    return res


POSITIVE = re.compile(r"\b(?:good|well|clear|correct|correctly|excellent|strong|effective|appropriate|accurate|great|"
                      r"solid|thorough|nice)\b", re.I)


def tone(text):
    """Praise minus criticism phrases per 100 words (English only)."""
    words = max(1, len(text.split()))
    return 100 * (len(POSITIVE.findall(text)) - len(RX["critical"].findall(text))) / words


def halo(cases, blind_calls, shown_calls, reps=2000, seed=7):
    """Does feedback follow the MARK it is told, beyond what the work itself shows?

    The same feedback-only prompt, once with the teacher's mark hidden and once with it shown
    (prompts/feedback-blind.txt, feedback-shown.txt; Bulut et al. 2026's design). Tone is praise minus
    criticism phrases per 100 words. Blind feedback can track the mark only through the work; shown
    feedback can also copy the mark. halo = corr(tone, mark | shown) - corr(tone, mark | blind),
    bootstrapped over cases. Positive = the stated mark warms or cools the feedback on its own.
    Rule-coded, English only, no human reference: descriptive.
    """
    import random
    by_id = {c["id"]: c for c in cases}
    def texts(calls):
        out = {}
        for r in calls:
            if r["probe"] == "base":
                t, _ = feedback_text(r.get("text"))
                if t and english(t):
                    out[r["id"]] = t
        return out
    b, s_ = texts(blind_calls), texts(shown_calls)
    ids = sorted(set(b) & set(s_))
    if len(ids) < 30:
        return None
    rows = [(mean(by_id[i]["human"].values()), tone(b[i]), tone(s_[i])) for i in ids]
    def stat(rs):
        m = [r[0] for r in rs]
        return pearson([r[2] for r in rs], m) - pearson([r[1] for r in rs], m)
    point = stat(rows)
    rng = random.Random(seed)
    draws = sorted(v for v in (stat([rows[rng.randrange(len(rows))] for _ in rows]) for _ in range(reps)) if v == v)
    lo_, hi_ = draws[int(0.025 * len(draws))], draws[int(0.975 * len(draws)) - 1]
    return {"n": len(rows), "corr_blind": pearson([r[1] for r in rows], [r[0] for r in rows]),
            "corr_shown": pearson([r[2] for r in rows], [r[0] for r in rows]),
            "halo": point, "ci95": [lo_, hi_], "flag": lo_ > 0 or hi_ < 0,
            "note": "corr(tone, teacher mark) when the mark is shown minus when hidden; rule-coded, descriptive"}
