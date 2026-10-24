"""
Do the benchmark's rule-coded feedback measures agree with trained human annotators?

PRE-REGISTERED 2026-10-23, before any MRBench annotation was read. Only the README's schema, the
field names of MRBench_V2.json and the annotation guideline's file list had been seen.

WHY. `../feedback.py` scores the feedback a grader writes with word-list rules (answer leakage,
action phrases, tone, critical phrases). They have no human reference, so CLAUDE.md forbids using them
as a gate, target or leaderboard column. MRBench (Maurya et al., NAACL 2025; CC BY-SA 4.0; registry id
`mrbench`) is the closest open reference: 1,600 tutor responses (seven LLM tutors and a human expert)
to a student's maths mistake in 200 dialogues, each annotated by trained annotators on eight
pedagogical dimensions. Reported annotator agreement, the ceiling for any automatic measure: average
Cohen's kappa 0.71 on 40 doubly-annotated instances (Maurya et al.), Fleiss' kappa 0.65 on the BEA 2025
shared-task set (Kochmar et al. 2025). These were read from search summaries of the papers, not from
the papers themselves.

READS: $MRBENCH_DIR/MRBench/MRBench_V2.json (the repository clone; see data/data-sources.json).
Nothing from it is committed beyond aggregate statistics.

THE FOUR PAIRS. Each rule is the function in feedback.py, applied unchanged to the tutor response:

| pair    | rule (feedback.py)                                      | human label: positive vs negative |
|---------|---------------------------------------------------------|-----------------------------------|
| LEAK    | five or more consecutive content tokens of the reference | Revealing_of_the_Answer: "Yes (correct)" or "Yes (incorrect)" vs "No" |
|         | solution (`shingles`, as `leaks_answer`); only dialogues |                                   |
|         | whose Ground_Truth_Solution is available                 |                                   |
| ACTION  | action phrases per 100 words (`RX["action"]`)            | Actionability: "Yes" vs "No"      |
| TONE    | praise minus criticism per 100 words (`tone`)            | Tutor_Tone: "Encouraging" vs "Neutral" |
| MISTAKE | critical phrases per 100 words (`RX["critical"]`)        | Mistake_Identification: "Yes" vs "No" |

"To some extent" and "Offensive" are left out of the AUC and counted in the output. Spearman's rho
against the three-level ordinal label is reported beside each AUC, not used for the verdict.

STATISTIC. AUC of the rule score for the positive label (ties count half), with a 95% interval from a
bootstrap over DIALOGUES (2,000 draws): the eight responses to one dialogue share a context and are
not independent. Direction is signed: AUC below 0.5 means the rule points the wrong way.

CONTENT-FREE BAR. Response length in words, in whichever direction gives the higher AUC on the real
labels. Choosing the direction after looking makes the bar higher, not lower. The paired difference
AUC(rule) - AUC(length) is bootstrapped over the same dialogues.

MODEL-IDENTITY CHECK. Tutors differ in style and in their labels, so a rule can score above 0.5 by
recognising the tutor, not the property. The null derangement (below) keeps each tutor's labels with
that tutor. If the null's mean AUC exceeds 0.55 for a pair, that pair's verdict uses the within-tutor
AUC (computed per tutor, then averaged over tutors with at least 10 of each class) in place of the
pooled AUC, with the same bootstrap and bar.

POSITIVITY. A pair with fewer than 30 positive or 30 negative responses, or positives spread over
fewer than 15 dialogues, is UNANSWERABLE, not null.

VERDICTS (per pair, written before the run):
- UNANSWERABLE: positivity fails.
- WRONG DIRECTION: the AUC interval lies wholly below 0.50.
- VALIDATED: the AUC interval's lower bound exceeds 0.60 AND the paired difference from the length bar
  has its lower bound above 0.
- VALID, NOT BEYOND LENGTH: the lower bound exceeds 0.60 but the difference from length does not.
- NOT VALIDATED: the AUC interval's upper bound is below 0.60.
- INCONCLUSIVE: anything else.

WHAT A VERDICT ALLOWS. VALIDATED lets that measure be reported beside a grader's feedback as validated
against MRBench, for tutoring-style responses to a mistake. It does not show that the measure transfers
to feedback on essays or short answers; the benchmark must say so wherever it is used. Every other
verdict leaves the measure descriptive.

DETECTION FLOOR (`--floor`, run before the real labels are read; must pass first):
- PLANTED: on the real response texts and the real dialogue structure, labels are drawn from the rule
  score plus noise, tuned so the population AUC is about 0.72. VALIDATED must come back in at least
  45 of 50 seeds for every pair.
- LENGTH-ONLY: labels drawn from length alone, at the same strength. VALIDATED must come back in at
  most 3 of 50 seeds (the length bar has to stop a rule that only tracks length).
- NULL: the real labels deranged across dialogues within each tutor (every response gets another
  dialogue's label from the same tutor; no response keeps its own). VALIDATED in at most 3 of 50, and
  the mean AUC is reported: a mean away from 0.5 is the model-identity tell.
In --floor mode the real labels are read only to build the NULL derangement and the class sizes; no
real AUC is computed or printed.

EXPLORATORY (reported, never a verdict): for LEAK, whether the solution's final number appears in the
response, a rule the benchmark could adopt if the pre-registered one fails.

CHANGES (each made before any real AUC was computed):
1. (after the first --floor run) LEAK read 0 positives of 1,070. The README's schema gives the labels
   as "Yes (correct)" / "Yes (incorrect)"; MRBench_V2.json spells them "Yes (and the answer is
   correct)" / "Yes (but the answer is incorrect)". The positive set now uses the file's strings. The
   other three pairs' label strings match the file. V2 holds 1,655 responses, not 1,600: some
   dialogues have more than eight. The floor is re-run.
"""

import argparse
import json
import os
import random
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import feedback as fb  # noqa: E402

PAIRS = {
    "LEAK": ("Revealing_of_the_Answer", {"Yes (and the answer is correct)", "Yes (but the answer is incorrect)"}, {"No"}),
    "ACTION": ("Actionability", {"Yes"}, {"No"}),
    "TONE": ("Tutor_Tone", {"Encouraging"}, {"Neutral"}),
    "MISTAKE": ("Mistake_Identification", {"Yes"}, {"No"}),
}
REPS = 2000


def load():
    root = os.environ.get("MRBENCH_DIR")
    if not root:
        sys.exit("set MRBENCH_DIR to the MRBench repository clone (data/data-sources.json: mrbench)")
    data = json.load(open(os.path.join(root, "MRBench", "MRBench_V2.json")))
    rows = []
    for d in data:
        sol = d.get("Ground_Truth_Solution") or ""
        has_sol = bool(sol.strip()) and sol.strip().lower() != "not available"
        for tutor, r in d["anno_llm_responses"].items():
            rows.append({"dialogue": d["conversation_id"], "tutor": tutor, "text": r["response"] or "",
                         "solution": sol if has_sol else None, "labels": r["annotation"]})
    return rows


def words(t):
    return max(1, len(t.split()))


def rule_score(pair, row):
    t = row["text"]
    if pair == "LEAK":
        ref = fb.shingles(fb.tokens(row["solution"]))
        return 1.0 if ref & fb.shingles(fb.tokens(t)) else 0.0
    if pair == "ACTION":
        return 100 * len(fb.RX["action"].findall(t)) / words(t)
    if pair == "TONE":
        return fb.tone(t)
    if pair == "MISTAKE":
        return 100 * len(fb.RX["critical"].findall(t)) / words(t)


def final_number_leak(row):
    nums = re.findall(r"-?\d+(?:\.\d+)?", row["solution"] or "")
    return 1.0 if nums and re.search(r"(?<![\d.])" + re.escape(nums[-1]) + r"(?![\d.])", row["text"]) else 0.0


def auc(scores, labels):
    pos = [s for s, y in zip(scores, labels) if y == 1]
    neg = [s for s, y in zip(scores, labels) if y == 0]
    if not pos or not neg:
        return float("nan")
    allv = sorted((s, y) for s, y in zip(scores, labels))
    # rank-sum with mid-ranks for ties
    ranks, i = {}, 0
    vals = [s for s, _ in allv]
    rank_of = []
    while i < len(vals):
        j = i
        while j + 1 < len(vals) and vals[j + 1] == vals[i]:
            j += 1
        r = (i + j) / 2 + 1
        rank_of.extend([r] * (j - i + 1))
        i = j + 1
    rs = sum(r for r, (_, y) in zip(rank_of, allv) if y == 1)
    return (rs - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def spearman(x, y):
    def rank(v):
        o = sorted(range(len(v)), key=lambda k: v[k])
        r = [0.0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for k in range(i, j + 1):
                r[o[k]] = (i + j) / 2
            i = j + 1
        return r
    a, b = rank(x), rank(y)
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    num = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    den = (sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b)) ** 0.5
    return num / den if den else float("nan")


def items_for(pair, rows, labels_of):
    """(dialogue, tutor, rule, length, y) for rows with a usable label; labels_of(row) -> label string."""
    field, posset, negset = PAIRS[pair]
    out = []
    for r in rows:
        if pair == "LEAK" and r["solution"] is None:
            continue
        lab = labels_of(r)
        if lab in posset:
            y = 1
        elif lab in negset:
            y = 0
        else:
            continue
        out.append((r["dialogue"], r["tutor"], rule_score(pair, r), words(r["text"]), y))
    return out


def within_tutor_auc(its, col):
    by = defaultdict(list)
    for it in its:
        by[it[1]].append(it)
    vals = []
    for v in by.values():
        ys = [x[4] for x in v]
        if sum(ys) >= 10 and len(ys) - sum(ys) >= 10:
            vals.append(auc([x[col] for x in v], ys))
    return sum(vals) / len(vals) if vals else float("nan")


def evaluate(its, within, seed=11, reps=REPS, len_dir=None):
    """Point AUCs, the length bar and dialogue-bootstrap intervals."""
    stat = (lambda xs, col: within_tutor_auc(xs, col)) if within else \
        (lambda xs, col: auc([x[col] for x in xs], [x[4] for x in xs]))
    a_rule = stat(its, 2)
    a_len_up = stat(its, 3)
    if len_dir is None:
        len_dir = 1 if a_len_up >= 0.5 else -1
    flip = lambda xs: [(d, t, r, -l, y) for d, t, r, l, y in xs] if len_dir < 0 else xs
    a_len = stat(flip(its), 3)
    by_d = defaultdict(list)
    for it in its:
        by_d[it[0]].append(it)
    ds = sorted(by_d)
    rng = random.Random(seed)
    ra, rd = [], []
    for _ in range(reps):
        draw = [it for _ in ds for it in by_d[ds[rng.randrange(len(ds))]]]
        x, l_ = stat(draw, 2), stat(flip(draw), 3)
        if x == x and l_ == l_:
            ra.append(x)
            rd.append(x - l_)
    ra.sort()
    rd.sort()
    ci = lambda v: [v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]]
    return {"auc": a_rule, "auc_ci": ci(ra), "length_auc": a_len, "length_direction": len_dir,
            "minus_length": a_rule - a_len, "minus_length_ci": ci(rd)}


def verdict(ev):
    lo, hi = ev["auc_ci"]
    if hi < 0.50:
        return "WRONG DIRECTION"
    if lo > 0.60:
        return "VALIDATED" if ev["minus_length_ci"][0] > 0 else "VALID, NOT BEYOND LENGTH"
    if hi < 0.60:
        return "NOT VALIDATED"
    return "INCONCLUSIVE"


def positivity(its):
    pos = [it for it in its if it[4] == 1]
    return {"positive": len(pos), "negative": len(its) - len(pos), "positive_dialogues": len({p[0] for p in pos}),
            "ok": len(pos) >= 30 and len(its) - len(pos) >= 30 and len({p[0] for p in pos}) >= 15}


def derange_within_tutor(rows, field, rng):
    by = defaultdict(list)
    for i, r in enumerate(rows):
        by[r["tutor"]].append(i)
    lab = {}
    for idx in by.values():
        perm = idx[:]
        while True:
            rng.shuffle(perm)
            if all(rows[a]["dialogue"] != rows[b]["dialogue"] for a, b in zip(idx, perm)):
                break
        for a, b in zip(idx, perm):
            lab[a] = rows[b]["labels"].get(field)
    return lab


def planted_labels(its, col, target_noise, rng):
    """Labels drawn from column `col` (rule or length) plus Gaussian noise, matching the real base rate."""
    xs = [it[col] for it in its]
    m = sum(xs) / len(xs)
    sd = (sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5 or 1.0
    rate = sum(it[4] for it in its) / len(its)
    z = [(x - m) / sd + rng.gauss(0, target_noise) for x in xs]
    cut = sorted(z)[int((1 - rate) * len(z))]
    return [(d, t, r, l, 1 if zz >= cut else 0) for (d, t, r, l, _), zz in zip(its, z)]


def tune_noise(its, col, target=0.72, rng_seed=5):
    best = None
    for noise in [0.2 * k for k in range(1, 30)]:
        vals = [auc([x[col] for x in planted_labels(its, col, noise, random.Random(rng_seed + s))],
                    [x[4] for x in planted_labels(its, col, noise, random.Random(rng_seed + s))]) for s in range(5)]
        a = sum(vals) / len(vals)
        if best is None or abs(a - target) < abs(best[1] - target):
            best = (noise, a)
    return best


def run_floor(rows, seeds=50):
    out = {}
    for pair, (field, _, _) in PAIRS.items():
        its = items_for(pair, rows, lambda r: r["labels"].get(field))
        pos = positivity(its)
        res = {"positivity": pos}
        if not pos["ok"]:
            res["note"] = "positivity fails; floor not run"
            out[pair] = res
            print(pair, res)
            continue
        if len({it[2] for it in its}) < 2:
            res["note"] = "rule is constant on these responses; floor not run"
            out[pair] = res
            print(pair, res)
            continue
        n_rule, a_rule = tune_noise(its, 2)
        n_len, a_len = tune_noise(its, 3)
        counts = {"PLANTED": 0, "LENGTH-ONLY": 0, "NULL": 0}
        null_aucs = []
        for s in range(seeds):
            rng = random.Random(1000 + s)
            pl = planted_labels(its, 2, n_rule, rng)
            counts["PLANTED"] += verdict(evaluate(pl, False, seed=s, reps=300)) == "VALIDATED"
            ll = planted_labels(its, 3, n_len, rng)
            counts["LENGTH-ONLY"] += verdict(evaluate(ll, False, seed=s, reps=300)) == "VALIDATED"
            lab = derange_within_tutor(rows, field, rng)
            nl = items_for(pair, rows, lambda r, _l=lab, _i={id(x): k for k, x in enumerate(rows)}: _l[_i[id(r)]])
            ev = evaluate(nl, False, seed=s, reps=300)
            null_aucs.append(ev["auc"])
            counts["NULL"] += verdict(ev) == "VALIDATED"
        res.update({"planted_population_auc": a_rule, "length_planted_auc": a_len, "validated_of_50": counts,
                    "null_mean_auc": sum(null_aucs) / len(null_aucs),
                    "pass": counts["PLANTED"] >= 45 and counts["LENGTH-ONLY"] <= 3 and counts["NULL"] <= 3})
        out[pair] = res
        print(pair, json.dumps(res))
    return out


def run_real(rows, floor):
    out = {}
    for pair, (field, _, _) in PAIRS.items():
        its = items_for(pair, rows, lambda r: r["labels"].get(field))
        pos = positivity(its)
        levels = defaultdict(int)
        for r in rows:
            if pair != "LEAK" or r["solution"] is not None:
                levels[r["labels"].get(field)] += 1
        res = {"positivity": pos, "label_counts": dict(levels)}
        if not pos["ok"]:
            res["verdict"] = "UNANSWERABLE"
            out[pair] = res
            continue
        within = floor.get(pair, {}).get("null_mean_auc", 0.5) > 0.55
        ev = evaluate(its, within)
        res.update(ev)
        res["statistic"] = "within-tutor AUC (model-identity check tripped)" if within else "pooled AUC"
        order = {"No": 0, "To some extent": 1, "Yes": 2, "Neutral": 0, "Encouraging": 1,
                 "Yes (and the answer is correct)": 1, "Yes (but the answer is incorrect)": 1}
        ordv = [(rule_score(pair, r), order[r["labels"].get(field)]) for r in rows
                if r["labels"].get(field) in order and (pair != "LEAK" or r["solution"] is not None)]
        res["spearman_vs_ordinal"] = spearman([a for a, _ in ordv], [b for _, b in ordv])
        res["verdict"] = verdict(ev)
        if pair == "LEAK":
            ex = [(final_number_leak(r), 1 if r["labels"].get(field) in PAIRS["LEAK"][1] else 0) for r in rows
                  if r["solution"] is not None and r["labels"].get(field) in PAIRS["LEAK"][1] | PAIRS["LEAK"][2]]
            res["exploratory_final_number_auc"] = auc([a for a, _ in ex], [b for _, b in ex])
        out[pair] = res
        print(pair, res["verdict"], json.dumps({k: res[k] for k in ("auc", "auc_ci", "length_auc", "minus_length_ci")}))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--floor", action="store_true", help="run the detection floor only")
    a = ap.parse_args()
    rows = load()
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    fpath = os.path.join(HERE, "out", "floor.json")
    if a.floor:
        res = run_floor(rows)
        json.dump(res, open(fpath, "w"), indent=1)
        print("FLOOR PASSES" if all(v.get("pass") for v in res.values() if "pass" in v) else "FLOOR FAILS")
        return
    if not os.path.exists(fpath):
        sys.exit("run --floor first")
    floor = json.load(open(fpath))
    res = run_real(rows, floor)
    json.dump({"design": "validate.py docstring", "n_responses": len(rows), "pairs": res},
              open(os.path.join(HERE, "out", "result.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
