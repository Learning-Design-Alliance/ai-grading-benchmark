#!/usr/bin/env python3
"""How much of a model's agreement with the experts is more than length? PRE-REGISTERED 2026-10-26, before this
script read any submission. No new calls: it reads the board's submissions (marks only).

WHY. On essays, the length of the answer alone (the `length` baseline) agrees with the experts at QWK 0.64, above
16 of the board's 22 models. The existing length check (standard_checks.py, check 3) asks whether a model rewards
length MORE than the experts did. This asks the converse: once length is set aside, does a model still agree with
the experts? A grader whose agreement is mostly length is reading the essay's size, not its quality, and would
be fooled by padding the experts would not reward.

DESIGN. The board's 100 cases per task and its submissions' base gradings; no new calls. (Heading added
2026-10-26 for scripts/check_study.py; the design is unchanged.)

MEASURES, per model and task (short answers, code, essays), on the base gradings of the board's 100 cases:
- r: Pearson correlation of the model's mark with the experts' mean mark;
- r_length: Pearson correlation of log(1 + words) with the experts' mean (the task's, same for every model);
- PARTIAL r: the correlation of model and experts with log(1 + words) partialled out of both. This is the
  agreement that is more than length. 95% interval by bootstrap over cases (2,000 draws, seed 7);
- WITHIN-BAND r: the cases cut into five length bands (quintiles of words); Pearson within each band; the mean of
  the five. A second, model-free view of the same thing;
- share beyond length: partial r / r, descriptive.
Signs: all correlations are signed; a negative partial r would mean the model ranks essays of the same length in
the opposite order to the experts.

VERDICT per model and task:
  AGREES BEYOND LENGTH   the partial r interval lies above 0
  LENGTH-BOUND           the interval contains 0 (its upper bound is reported as what is not ruled out)
  INVERTED               the interval lies below 0
And for the board, on essays: how many models agree beyond length, and the rank order of partial r beside the
order of QWK (Spearman between the two orders, descriptive).

FLOOR (synthetic, on the real essays' lengths and expert marks, 200 draws each, run before any submission is read):
  - LENGTH-ONLY marks: the experts' mean predicted from log words by OLS, plus noise with the residual SD, rounded
    to the scale. Must read LENGTH-BOUND or INVERTED in at least 90% of draws (false positive at most 10%).
  - A REAL GRADER: the experts' mean plus noise sized so that r with the experts is 0.60 (about the board's
    essay median), rounded. Must read AGREES BEYOND LENGTH in at least 90% of draws.
If either fails, the verdicts are reported as UNMEASURED and only the descriptive figures stand.

Usage:
    python3 analyses/length_partial.py --cases-dir <dir> [--out out/length_partial.json]
"""

import argparse
import glob
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import cases as cases_mod  # noqa: E402
from metrics import mean  # noqa: E402

FILES = {"mohler": "mohler.jsonl", "code": "harmogen-code.jsonl", "asap2": "asap2.jsonl"}
N, SEED, REPS = 100, 7, 2000


def pearson(x, y):
    mx, my = mean(x), mean(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return float("nan") if sx == 0 or sy == 0 else sxy / (sx * sy)


def partial(m, h, l):
    rmh, rml, rhl = pearson(m, h), pearson(m, l), pearson(h, l)
    d = math.sqrt(max(0.0, (1 - rml ** 2) * (1 - rhl ** 2)))
    return float("nan") if d == 0 else (rmh - rml * rhl) / d


def within_band(m, h, l, k=5):
    order = sorted(range(len(l)), key=lambda i: l[i])
    rs = []
    for b in range(k):
        idx = order[b * len(order) // k:(b + 1) * len(order) // k]
        r = pearson([m[i] for i in idx], [h[i] for i in idx])
        if r == r:
            rs.append(r)
    return mean(rs) if rs else float("nan")


def boot_partial(m, h, l, seed=SEED):
    rnd = random.Random(seed)
    n = len(m)
    vals = []
    for _ in range(REPS):
        idx = [rnd.randrange(n) for _ in range(n)]
        v = partial([m[i] for i in idx], [h[i] for i in idx], [l[i] for i in idx])
        if v == v:
            vals.append(v)
    vals.sort()
    return [vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]]


def verdict(iv):
    return "AGREES BEYOND LENGTH" if iv[0] > 0 else "INVERTED" if iv[1] < 0 else "LENGTH-BOUND"


def floor(cs, draws=200):
    h = [mean(list(c["human"].values())) for c in cs]
    l = [math.log1p(len(c["response"].split())) for c in cs]
    lo, hi = cs[0]["scale"]
    ml, mh = mean(l), mean(h)
    b = sum((a - ml) * (y - mh) for a, y in zip(l, h)) / sum((a - ml) ** 2 for a in l)
    pred = [mh + b * (a - ml) for a in l]
    res_sd = math.sqrt(sum((y - p) ** 2 for y, p in zip(h, pred)) / (len(h) - 2))
    sd_h = math.sqrt(sum((y - mh) ** 2 for y in h) / (len(h) - 1))
    noise_real = sd_h * math.sqrt(1 / 0.6 ** 2 - 1)  # r with the experts about 0.60
    clip = lambda v: max(lo, min(hi, round(v)))
    fp = tp = 0
    for d in range(draws):
        rnd = random.Random(1000 + d)
        m_len = [clip(p + rnd.gauss(0, res_sd)) for p in pred]
        m_real = [clip(y + rnd.gauss(0, noise_real)) for y in h]
        fp += verdict(boot_partial(m_len, h, l, seed=d)) == "AGREES BEYOND LENGTH"
        tp += verdict(boot_partial(m_real, h, l, seed=d)) == "AGREES BEYOND LENGTH"
    return {"draws": draws, "false_positive": fp / draws, "detection": tp / draws,
            "passes": fp / draws <= 0.10 and tp / draws >= 0.90}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cases-dir", required=True)
    ap.add_argument("--out", default=os.path.join(ROOT, "out", "length_partial.json"))
    ap.add_argument("--floor-draws", type=int, default=200)
    a = ap.parse_args()
    global REPS
    res = {"design": "analyses/length_partial.py docstring", "floor": {}, "rows": [], "board": {}}
    canon = {t: cases_mod.sample(cases_mod.load(os.path.join(a.cases_dir, f)), N, SEED) for t, f in FILES.items()}
    # floor first, before any submission is read (smaller bootstrap inside the floor to keep it quick)
    REPS, keep = 500, REPS
    for t, cs in canon.items():
        res["floor"][t] = floor(cs, a.floor_draws)
        print(f"floor {t:6s} false positive {res['floor'][t]['false_positive']:.0%} detection "
              f"{res['floor'][t]['detection']:.0%} -> {'passes' if res['floor'][t]['passes'] else 'FAILS'}", flush=True)
    REPS = keep
    for p in sorted(glob.glob(os.path.join(ROOT, "submissions", "*", "*.json"))):
        sub = json.load(open(p))
        t = sub.get("task")
        if t not in FILES or sub.get("track") != "default":
            continue
        by = {c["id"]: c for c in canon[t]}
        marks = {r["id"]: r["score"] for r in sub["calls"] if r["probe"] == "base" and r.get("score") is not None}
        ids = [i for i in by if i in marks]
        m = [marks[i] for i in ids]
        h = [mean(list(by[i]["human"].values())) for i in ids]
        l = [math.log1p(len(by[i]["response"].split())) for i in ids]
        iv = boot_partial(m, h, l)
        r, pr = pearson(m, h), partial(m, h, l)
        row = {"model": sub["model"], "task": t, "n": len(ids), "r": r, "r_length": pearson(l, h),
               "partial_r": pr, "ci95": iv, "within_band_r": within_band(m, h, l),
               "share_beyond_length": pr / r if r and r == r else None,
               "verdict": verdict(iv) if res["floor"][t]["passes"] else "UNMEASURED"}
        res["rows"].append(row)
        print(f"{t:6s} {sub['model'][:32]:32s} r {r:.2f} | partial {pr:+.2f} [{iv[0]:+.2f}, {iv[1]:+.2f}] | "
              f"within-band {row['within_band_r']:+.2f} -> {row['verdict']}", flush=True)
    for t in FILES:
        rows = [x for x in res["rows"] if x["task"] == t]
        if rows:
            res["board"][t] = {"models": len(rows), "r_length": rows[0]["r_length"],
                               "beyond_length": sum(x["verdict"] == "AGREES BEYOND LENGTH" for x in rows),
                               "median_share_beyond_length": sorted(x["share_beyond_length"] for x in rows)[len(rows) // 2]}
            print(f"{t}: {res['board'][t]['beyond_length']} of {len(rows)} agree beyond length; experts vs length r "
                  f"{res['board'][t]['r_length']:+.2f}; median share beyond length {res['board'][t]['median_share_beyond_length']:.2f}")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
