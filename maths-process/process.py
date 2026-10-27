#!/usr/bin/env python3
"""Does a grader read the working, or only check the answer? Multi-step maths with the reasoning and the final
answer varied independently. PRE-REGISTERED 2026-10-24, before any call of this design.

WHY. A final answer can be checked deterministically. An LLM grader earns its cost only where the working
matters: a right answer reached by wrong working, or right working ending in a wrong answer. This tests
exactly those cases, against an answer checker.

DATA. VtG (Daheim et al., EMNLP 2024; github.com/eth-lre/verify-then-generate, dataset/dataset.json, commit
161019e, MD5 3aa4f6bf8b0185e26fe859b749165b13). The README gives CC BY 4.0 in its badge and CC BY-SA 4.0 in
its licence section; the stricter, CC BY-SA 4.0, is followed. It holds 1,002 GSM8K word problems from MathDial.
Each has:
- an incorrect step-by-step solution, with the FIRST WRONG STEP marked by a teacher;
- a correct solution, a model's rephrasing of the reference solution;
- the reference solution, ending in the answer.
CAVEAT: the "students" are a language model prompted to make student-like errors (MathDial). This measures
whether a grader reads the working; it is not a sample of real students' work.

CELLS. Per problem, four versions, numbered step by step, each ending in a bare final-answer line:

| cell | reasoning | final answer | what it is |
|---|---|---|---|
| correct | right | right | the correct solution, split into sentences |
| slip | right | wrong | the correct solution, ending in the student's wrong answer |
| lucky | wrong | right | the incorrect solution, its final line replaced by the right answer |
| wrong | wrong | wrong | the incorrect solution as written |

The wrong answer is the same number in slip and wrong, and the right answer is the same in correct and lucky.
So an answer checker cannot tell the rows apart, by construction.

CASES. 200 problems drawn at seed 7, excluding two kinds:
- problems whose first wrong step is the final line (replacing that line would remove the error);
- problems whose incorrect final answer already equals the right one.
That gives 800 gradings a grader.

PROMPT. prompts/maths-steps.txt carries the problem, the reference solution (a marker has the answer key),
and the numbered solution. It asks for credit 0-4 for the solution as a whole, whether the final answer is
right, and the number of the first wrong step (0 if none).

GRADERS. Claude Opus 5.5, Claude Haiku 5.5, GPT-5 Mini, DeepSeek V4.1 Flash, Gemini 3.5 Flash Lite,
Gemma 4 31B and Qwen3 235B, at their leaderboard settings, with zero data retention. Also the ANSWER CHECKER,
which makes no calls: 4 if the final line equals the reference answer, else 0.

MEASURES, per grader (95% intervals by bootstrap over problems, 2,000 draws, seed 7):
- **Reasoning effect** = mean over problems of ((correct - lucky) + (slip - wrong)) / 2: how much the credit
  depends on the working, with the answer held fixed. The answer checker scores exactly 0.
- **Answer effect** = mean of ((correct - slip) + (lucky - wrong)) / 2. The answer checker scores 4.
- **Lucky accepted**: the share of lucky solutions given full credit (4). A grader that accepts wrong working
  for a right answer is doing the checker's job at a model's price.
- **First wrong step**: exact agreement with the teacher's step on wrong and on lucky (the same step in both),
  and the share of correct solutions where no step is flagged.

VERDICTS (pre-registered), on the reasoning effect:
  READS THE WORKING  the interval lies above 0.5 (an eighth of the scale);
  ANSWER ONLY        the interval contains 0;
  WEAKLY             otherwise.

FLOOR (`floor`, before any call). Planted graders on the real cell structure:
- an answer checker with noise must read READS THE WORKING in at most 5% of worlds, and ANSWER ONLY in at
  least 90%;
- a grader whose credit falls by 1 point for wrong working must read READS THE WORKING in at least 80%.
The first version asked for ANSWER ONLY in 95% of worlds. That is the nominal coverage of a 95% interval,
which a noisy checker reaches only by chance, and it read 94%. It was restated before any call. The error
that matters is a checker read as reading the working, and that rate is the one bounded at 5%.

CHANGES
1. 2026-10-27: Olmo 3.1 32B was graded on these 800 cells for the board (submissions/allenai__olmo-3.1-32b-instruct/
   maths.json, self-hosted), but its replies were not kept when its pod was deleted, so it had no run here.
   `analyse --submissions` adds a grader from its board submission. The working effect, answer effect, mean
   credit and lucky-accepted share need only the scores and are computed exactly as for a run; the first wrong
   step needs the reply text, so that row has none. No measure, threshold or verdict changed.
2. 2026-10-27: credits were rounded with Python's round (half to even) where the benchmark rounds half-up
   (metrics.py); now half_up. No run or submission holds a half-point math score, so the output is unchanged.

    python3 maths-process/process.py build --src $VTG_DIR/src/dataset/dataset.json --out $VTG_DIR/vtg-cells.jsonl
    python3 maths-process/process.py floor
    python3 maths-process/process.py analyse --cases $VTG_DIR/vtg-cells.jsonl --runs <run dir> ... [--submissions <board submission> ...] --out maths-process/out/process.json
"""
import argparse
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from metrics import half_up  # noqa: E402

CELLS = ("correct", "slip", "lucky", "wrong")


def ref_answer(r):
    return re.search(r"\n\s*(-?[\d,\.]+)\s*$", r["reference_solution"]).group(1).replace(",", "")


def num(s):
    try:
        return float(s.replace(",", "").strip())
    except ValueError:
        return None


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z])", text.strip()) if s.strip()]


def numbered(steps):
    return "\n".join(f"Step {i + 1}: {s}" for i, s in enumerate(steps))


def cmd_build(a):
    from cases import normalise, write
    d = json.load(open(a.src))
    keep = []
    for i, r in enumerate(d):
        steps = r["student_incorrect_solution"]
        if r["incorrect_index"] >= len(steps) - 1:
            continue
        wrong_ans, right_ans = num(steps[-1]), num(ref_answer(r))
        if wrong_ans is None or right_ans is None or wrong_ans == right_ans:
            continue
        keep.append(i)
    rng = random.Random(7)
    chosen = sorted(rng.sample(keep, min(a.n, len(keep))))
    out = []
    for i in chosen:
        r = d[i]
        inc = [s.strip() for s in r["student_incorrect_solution"]]
        right, wrong = ref_answer(r), inc[-1].strip()
        cor = sentences(r["student_correct_response"])
        versions = {"correct": cor + [right], "slip": cor + [wrong], "lucky": inc[:-1] + [right], "wrong": inc}
        for cell, steps in versions.items():
            ok = cell in ("correct", "slip")
            out.append(normalise({
                "id": f"vtg{i}-{cell}", "task": f"vtg{i}", "question": r["problem"].strip(),
                "reference": r["reference_solution"].strip(), "rubric": "", "materials": "",
                "response": numbered(steps), "scale": [0, 4],
                "human": {"teacher_reasoning_ok": 1.0 if ok else 0.0},
                "groups": {"cell": cell, "error_category": r["error_category"]},
                "meta": {"first_error_step": None if ok else r["incorrect_index"] + 1, "n_steps": len(steps),
                         "final_right": cell in ("correct", "lucky")},
            }))
    write(out, a.out)
    print(f"{len(chosen)} problems x 4 cells = {len(out)} cases (from {len(keep)} eligible of {len(d)}) -> {a.out}")


def effects(units):
    """units: [{cell: credit}] per problem -> (reasoning effect, answer effect)"""
    us = [u for u in units if all(u.get(c) is not None for c in CELLS)]
    if not us:
        return None, None
    re_ = sum(((u["correct"] - u["lucky"]) + (u["slip"] - u["wrong"])) / 2 for u in us) / len(us)
    ae = sum(((u["correct"] - u["slip"]) + (u["lucky"] - u["wrong"])) / 2 for u in us) / len(us)
    return re_, ae


def boot(units, reps=2000, seed=7):
    rng = random.Random(seed)
    rs, as_ = [], []
    for _ in range(reps):
        s = [rng.choice(units) for _ in units]
        r, a = effects(s)
        if r is not None:
            rs.append(r)
            as_.append(a)
    rs.sort()
    as_.sort()
    q = lambda v: [v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]] if v else None
    return q(rs), q(as_)


def verdict(iv):
    if iv is None:
        return None
    if iv[0] > 0.5:
        return "READS THE WORKING"
    if iv[0] <= 0 <= iv[1]:
        return "ANSWER ONLY"
    return "WEAKLY"


def cmd_floor(a):
    rng = random.Random(5)
    res, false_reads = {}, 0
    for name, drop in (("answer_checker", 0.0), ("reads_working", 1.0)):
        hits = 0
        for w in range(a.worlds):
            units = []
            for _ in range(200):
                base = {"correct": 4, "slip": 1.5, "lucky": 4 - drop, "wrong": 1.5 - drop}
                units.append({c: max(0, min(4, round(v + rng.gauss(0, 1.0)))) for c, v in base.items()})
            v = verdict(boot(units, reps=400, seed=w)[0])
            hits += v == ("ANSWER ONLY" if drop == 0 else "READS THE WORKING")
            if drop == 0:
                false_reads += v == "READS THE WORKING"
        res[name] = hits / a.worlds
    res["answer_checker_read_as_reads"] = false_reads / a.worlds
    ok = res["answer_checker"] >= 0.90 and res["answer_checker_read_as_reads"] <= 0.05 and res["reads_working"] >= 0.80
    print(f"answer checker read as ANSWER ONLY in {res['answer_checker']:.0%}, as READS in "
          f"{res['answer_checker_read_as_reads']:.0%}; working reader read as READS in {res['reads_working']:.0%} -> "
          f"{'FLOOR PASSES' if ok else 'FLOOR FAILS'}")
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    json.dump({"design": "process.py floor", "worlds": a.worlds, "correct_verdict_rate": res, "passes": ok},
              open(os.path.join(HERE, "out", "floor.json"), "w"), indent=1)


def parse_extra(text):
    """(final_answer_correct, first_error_step) from a grader's JSON reply, or (None, None)."""
    if not text:
        return None, None
    m = re.search(r"\{.*\}", text, re.S)
    try:
        o = json.loads(m.group(0)) if m else {}
    except ValueError:
        return None, None
    fe = o.get("first_wrong_step")
    return o.get("final_answer_correct"), (int(fe) if isinstance(fe, (int, float)) else None)


def summarise(name, cs, credit, extra):
    units = {}
    for c in cs:
        units.setdefault(c["task"], {})[c["groups"]["cell"]] = credit.get(c["id"])
    u = list(units.values())
    r, an = effects(u)
    ri, ai = boot(u)
    full = lambda cell: [credit[c["id"]] == 4 for c in cs if c["groups"]["cell"] == cell and c["id"] in credit]
    row = {"grader": name, "reasoning_effect": r, "reasoning_ci95": ri, "answer_effect": an, "answer_ci95": ai,
           "mean_credit": {cell: (lambda v: sum(v) / len(v) if v else None)(
               [credit[c["id"]] for c in cs if c["groups"]["cell"] == cell and c["id"] in credit]) for cell in CELLS},
           "lucky_accepted": (lambda v: sum(v) / len(v) if v else None)(full("lucky")),
           "verdict": verdict(ri)}
    if extra is not None:
        loc = {}
        for cell in ("wrong", "lucky"):
            v = [extra[c["id"]][1] == c["meta"]["first_error_step"] for c in cs
                 if c["groups"]["cell"] == cell and c["id"] in extra and extra[c["id"]][1] is not None]
            loc[cell] = sum(v) / len(v) if v else None
        v = [extra[c["id"]][1] == 0 for c in cs if c["groups"]["cell"] == "correct" and c["id"] in extra and extra[c["id"]][1] is not None]
        loc["correct_none_flagged"] = sum(v) / len(v) if v else None
        row["first_wrong_step_exact"] = loc
    return row


def cmd_analyse(a):
    cs = [json.loads(l) for l in open(a.cases)]
    checker = {}
    for c in cs:
        last = c["response"].rsplit("\n", 1)[-1].split(":", 1)[-1]
        ref = re.search(r"\n\s*(-?[\d,\.]+)\s*$", c["reference"]).group(1)
        checker[c["id"]] = 4 if num(last) == num(ref) else 0
    rows = [summarise("answer checker (no model)", cs, checker, None)]
    for run in a.runs:
        cfg = json.load(open(os.path.join(run, "config.json")))
        credit, extra, failed = {}, {}, 0
        for l in open(os.path.join(run, "calls.jsonl")):
            r = json.loads(l)
            if r["probe"] != "base":
                continue
            if r.get("score") is None:
                failed += 1
                continue
            credit[r["id"]] = max(0, min(4, int(half_up(r["score"]))))
            extra[r["id"]] = parse_extra(r.get("text"))
        row = summarise(cfg.get("label") or cfg["model"], cs, credit, extra)
        row["failed"] = failed
        rows.append(row)
    for path in a.submissions:  # CHANGE 1: a board submission holds scores only, so no first-wrong-step row
        sub = json.load(open(path))
        credit, failed = {}, 0
        for r in sub["calls"]:
            if r["probe"] != "base":
                continue
            if r.get("score") is None:
                failed += 1
                continue
            credit[r["id"]] = max(0, min(4, int(half_up(r["score"]))))
        row = summarise(sub["model"], cs, credit, None)
        row["failed"] = failed
        row["source"] = "board submission (scores only; replies not kept)"
        rows.append(row)
    for row in rows:
        f = lambda v: "—" if v is None else f"{v:+.2f}"
        mc = row["mean_credit"]
        print(f"{row['grader']:36s} reasoning {f(row['reasoning_effect'])} {row['reasoning_ci95'] and [round(x, 2) for x in row['reasoning_ci95']]} "
              f"answer {f(row['answer_effect'])} | credit C/S/L/W {mc['correct']:.2f}/{mc['slip']:.2f}/{mc['lucky']:.2f}/{mc['wrong']:.2f} "
              f"| lucky full {row['lucky_accepted']:.0%} | step {row.get('first_wrong_step_exact')} -> {row['verdict']}")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump({"design": "maths-process/process.py docstring", "graders": rows}, open(a.out, "w"), indent=1)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("build"); p.add_argument("--src", required=True); p.add_argument("--out", required=True)
    p.add_argument("--n", type=int, default=200)
    p = sub.add_parser("floor"); p.add_argument("--worlds", type=int, default=300)
    p = sub.add_parser("analyse"); p.add_argument("--cases", required=True); p.add_argument("--runs", nargs="*", default=[]); p.add_argument("--submissions", nargs="*", default=[])
    p.add_argument("--out", required=True)
    a = ap.parse_args()
    {"build": cmd_build, "floor": cmd_floor, "analyse": cmd_analyse}[a.cmd](a)


if __name__ == "__main__":
    main()
