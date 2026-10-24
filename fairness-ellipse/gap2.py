#!/usr/bin/env python3
"""
Do AI graders mark English learners' essays differently by economic status or race, BEYOND what a second
human rater does? A two-rater version of `../disability/gap.py`.

PRE-REGISTERED 2026-10-23, before any machine grading of ELLIPSE. Group sizes, the two raters' marks by
mark level and the overall rater correlation had been read (to size the draw and calibrate the floor); no
group-by-rater gap had been computed.

WHY A SECOND RATER CHANGES THE DESIGN. `../disability/gap.py` matched two groups on the released human
mark and compared the machine's marks. If the groups differ in true writing quality, that design reads a
gap even for a perfect grader: essays matched on one noisy mark still differ in true quality, so ANY
second noisy measure, a model or another person, regresses toward each group's own mean (Kelley 1927;
the same mechanism behind the H-MOVE lesson in CLAUDE.md, a null not centred at zero). ASAP 2.0 releases
one mark per essay, so it cannot measure this. ELLIPSE releases both raters, so it can: matched on rater
1, the second rater's own gap (H) is the size of the artefact, and the model's gap beyond it (M - H) is
the model's.

CORPUS. ELLIPSE (Crossley et al. 2023; CC BY-NC-SA 4.0; registry id `persuade-ellipse`), cases built by
`../bench.py prepare ellipse` (cases.from_ellipse): 6,464 essays by English learners in grades 8-12, each
rated by two of 27 raters on a 1-5 holistic proficiency rubric, joined to the final corpus's demographic
fields. The demographic fields never enter a prompt.

CONTRASTS (A minus B; negative = the grader marks group A lower):
- C1 (PRIMARY): economic = "Economically disadvantaged" (A) vs "Not economically disadvantaged" (B).
- C2: race = "Black/African American" (A) vs "White" (B).
- C3: race = "Hispanic/Latino" (A) vs "White" (B).

DRAW (`gap2.py draw`). For each contrast, essays matched EXACTLY on rater 1's mark: for each mark 1-5,
the same number from each group, the smaller group's count, scaled down proportionally if the group would
exceed 1,000 essays. Seed 20261023. The union of the three draws is graded once.

GRADERS. `../bench.py run --probes base --n <all>` on the union, default prompt, OpenRouter with zero
data retention, max_tokens 16384, model defaults: Claude Haiku 5.5, Gemini 3.5 Flash Lite, Qwen3 235B
(pinned to DeepInfra), GPT-5 Mini. The first three are the disability study's graders.

STATISTICS, per grader and contrast, on that contrast's draw:
- M = mean machine mark (A) - mean machine mark (B): the old design's gap.
- H = mean rater-2 mark (A) - mean rater-2 mark (B): a second human's gap at matched rater-1 marks.
- D = M - H (PRIMARY): the model's gap beyond a second human's.
95% percentile bootstrap, 4,000 draws, resampling essays within each group (the same draw gives M, H and
D, so D's interval accounts for their correlation).

VERDICTS (per grader, per contrast; thresholds in marks on the 1-5 scale):
- "MODEL-SPECIFIC GAP AGAINST A": D's interval lies wholly below -0.10.
- "MODEL-SPECIFIC GAP FAVOURING A": D's interval lies wholly above +0.10.
- "NO MORE THAN A SECOND HUMAN": D's interval lies within (-0.15, +0.15).
- "INCONCLUSIVE": anything else.
And, once per contrast, about the design itself:
- "MATCHING ARTEFACT PRESENT": H's interval excludes 0. Then a one-mark matched gap (the ASAP disability
  design) is not interpretable as a grader's bias by itself, and its README must say so.
- "NO MATCHING ARTEFACT SHOWN": otherwise.
Failed gradings are reported per group; if their rates differ by more than 5 points, the verdict carries
that warning.

FLOOR (`gap2.py floor`, before any call). A generative world on each contrast's real draw sizes:
true quality theta ~ N(mu_g, s_t) with each group's mean set from its observed rater-1 mean, raters =
clip(round(theta + N(0, s_e)), 1, 5), with s_t and s_e chosen so the rater-1/rater-2 correlation equals
the observed one; the world is re-drawn and re-matched on its own rater 1 every simulation. The machine =
clip(round(theta + N(0, k * s_e) + bias on A), 1, 5), with k = 0.7 and 1.3 (a grader noisier or less noisy
than a person). 300 simulations per setting, normal-approximation intervals (the real analysis keeps the
bootstrap). Pass, for C1 and for every k:
- planted bias -0.30 reads MODEL-SPECIFIC GAP AGAINST A in at least 90%;
- planted bias 0 reads either MODEL-SPECIFIC verdict in at most 5%.
Also reported, not a pass condition: how often M alone (the old design) reads a gap below -0.10 at
planted bias 0. C2 and C3 are smaller and are reported with their own floor; if a contrast's floor fails,
that contrast is reported as below the floor, not as a finding.

    python3 gap2.py draw --cases <ellipse.jsonl> --out <union.jsonl>
    python3 gap2.py floor --cases <ellipse.jsonl>
    python3 gap2.py analyse --cases <ellipse.jsonl> --runs <run dir> [<run dir> ...]

No essay text or per-essay mark is committed: out/ holds the draw summary, the floor and the aggregates.

CHANGES: none yet.
"""

import argparse
import json
import math
import os
import random
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import cases as cases_mod  # noqa: E402

SEED = 20261023
CAP = 1000
CONTRASTS = {
    "C1": ("economic", "Economically disadvantaged", "Not economically disadvantaged"),
    "C2": ("race", "Black/African American", "White"),
    "C3": ("race", "Hispanic/Latino", "White"),
}


def r1(c):
    return int(round(c["human"]["rater1"]))


def draw_contrast(cs, key, a, b, rng):
    by = {a: defaultdict(list), b: defaultdict(list)}
    for c in cs:
        g = c["groups"].get(key)
        if g in by:
            by[g][r1(c)].append(c)
    take = {m: min(len(by[a][m]), len(by[b][m])) for m in range(1, 6)}
    total = sum(take.values())
    if total > CAP:
        f = CAP / total
        take = {m: int(round(v * f)) for m, v in take.items()}
    out = {a: [], b: []}
    for m in range(1, 6):
        for g in (a, b):
            pool = sorted(by[g][m], key=lambda c: c["id"])
            out[g] += rng.sample(pool, take[m])
    return out


def draws(cs):
    res = {}
    for name, (key, a, b) in CONTRASTS.items():
        res[name] = draw_contrast(cs, key, a, b, random.Random(f"{SEED}-{name}"))
    return res


def cmd_draw(args):
    cs = cases_mod.load(args.cases)
    d = draws(cs)
    union = {}
    summary = {}
    for name, groups in d.items():
        summary[name] = {g: len(v) for g, v in groups.items()}
        for v in groups.values():
            for c in v:
                union[c["id"]] = c
    cases_mod.write(list(union.values()), args.out)
    summary["union"] = len(union)
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    json.dump(summary, open(os.path.join(HERE, "out", "draw.json"), "w"), indent=1)
    print(json.dumps(summary))


def norm_ci(xa, xb):
    ma, mb = sum(xa) / len(xa), sum(xb) / len(xb)
    va = sum((x - ma) ** 2 for x in xa) / (len(xa) - 1)
    vb = sum((x - mb) ** 2 for x in xb) / (len(xb) - 1)
    d = ma - mb
    se = math.sqrt(va / len(xa) + vb / len(xb))
    return d, d - 1.96 * se, d + 1.96 * se


def verdict(lo, hi):
    if hi < -0.10:
        return "MODEL-SPECIFIC GAP AGAINST A"
    if lo > 0.10:
        return "MODEL-SPECIFIC GAP FAVOURING A"
    if lo > -0.15 and hi < 0.15:
        return "NO MORE THAN A SECOND HUMAN"
    return "INCONCLUSIVE"


def clip(x):
    return min(5, max(1, int(round(x))))


def calibrate(cs):
    a = [c["human"]["rater1"] for c in cs]
    b = [c["human"]["rater2"] for c in cs]
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b)) / len(a)
    va = sum((x - ma) ** 2 for x in a) / len(a)
    vb = sum((y - mb) ** 2 for y in b) / len(b)
    r = cov / math.sqrt(va * vb)
    total = (va + vb) / 2
    # rater = theta + e: r = s_t^2 / (s_t^2 + s_e^2), total = s_t^2 + s_e^2 (rounding ignored)
    return r, math.sqrt(r * total), math.sqrt((1 - r) * total)


def cmd_floor(args):
    cs = cases_mod.load(args.cases)
    r, s_t, s_e = calibrate(cs)
    real = draws(cs)
    out = {"rater_correlation": r, "s_theta": s_t, "s_error": s_e, "contrasts": {}}
    for name, (key, a, b) in CONTRASTS.items():
        grp = {g: [c for c in cs if c["groups"].get(key) == g] for g in (a, b)}
        mu = {g: sum(c["human"]["rater1"] for c in v) / len(v) for g, v in grp.items()}
        n = {g: len(v) for g, v in grp.items()}
        res = {"group_rater1_mean": mu, "group_n": n, "draw": {g: len(v) for g, v in real[name].items()}}
        for k in (0.7, 1.3):
            for bias in (-0.30, 0.0):
                hits, old_false = 0, 0
                for s in range(args.sims):
                    rng = random.Random(f"floor-{name}-{k}-{bias}-{s}")
                    world = []
                    for g in (a, b):
                        for _ in range(n[g]):
                            th = rng.gauss(mu[g], s_t)
                            world.append({"g": g, "r1": clip(th + rng.gauss(0, s_e)), "r2": clip(th + rng.gauss(0, s_e)),
                                          "m": clip(th + rng.gauss(0, k * s_e) + (bias if g == a else 0.0))})
                    by = {g: defaultdict(list) for g in (a, b)}
                    for w in world:
                        by[w["g"]][w["r1"]].append(w)
                    take = {m: min(len(by[a][m]), len(by[b][m])) for m in range(1, 6)}
                    tot = sum(take.values())
                    if tot > CAP:
                        take = {m: int(round(v * CAP / tot)) for m, v in take.items()}
                    sel = {g: [x for m in range(1, 6) for x in rng.sample(by[g][m], take[m])] for g in (a, b)}
                    da = [x["m"] - x["r2"] for x in sel[a]]
                    db = [x["m"] - x["r2"] for x in sel[b]]
                    _, lo, hi = norm_ci(da, db)
                    v = verdict(lo, hi)
                    if bias < 0:
                        hits += v == "MODEL-SPECIFIC GAP AGAINST A"
                    else:
                        hits += v.startswith("MODEL-SPECIFIC")
                        _, _, mhi = norm_ci([x["m"] for x in sel[a]], [x["m"] for x in sel[b]])
                        old_false += mhi < -0.10
                key_ = f"k={k} bias={bias:+.2f}"
                res[key_] = {"rate": hits / args.sims}
                if bias == 0.0:
                    res[key_]["old_design_gap_rate"] = old_false / args.sims
                print(name, key_, res[key_], flush=True)
        res["pass"] = all(res[f"k={k} bias=-0.30"]["rate"] >= 0.90 and res[f"k={k} bias=+0.00"]["rate"] <= 0.05
                          for k in (0.7, 1.3))
        out["contrasts"][name] = res
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    json.dump(out, open(os.path.join(HERE, "out", "floor.json"), "w"), indent=1)
    print("FLOOR PASSES (C1)" if out["contrasts"]["C1"]["pass"] else "FLOOR FAILS (C1)")


def boot(xa, xb, reps, rng):
    d = sum(xa) / len(xa) - sum(xb) / len(xb)
    vals = []
    for _ in range(reps):
        sa = [xa[rng.randrange(len(xa))] for _ in xa]
        sb = [xb[rng.randrange(len(xb))] for _ in xb]
        vals.append(sum(sa) / len(sa) - sum(sb) / len(sb))
    vals.sort()
    return d, vals[int(0.025 * reps)], vals[int(0.975 * reps) - 1]


def cmd_analyse(args):
    cs = cases_mod.load(args.cases)
    real = draws(cs)
    floor = json.load(open(os.path.join(HERE, "out", "floor.json")))
    out = {"design": "gap2.py docstring", "contrasts": {}}
    for name, (key, a, b) in CONTRASTS.items():
        sel = real[name]
        h = boot([c["human"]["rater2"] for c in sel[a]], [c["human"]["rater2"] for c in sel[b]], 4000,
                 random.Random(f"H-{name}"))
        res = {"n": {g: len(v) for g, v in sel.items()}, "floor_pass": floor["contrasts"][name]["pass"],
               "H": {"estimate": h[0], "ci95": [h[1], h[2]]},
               "design_reading": "MATCHING ARTEFACT PRESENT" if h[1] > 0 or h[2] < 0 else "NO MATCHING ARTEFACT SHOWN",
               "graders": {}}
        for run in args.runs:
            calls = [json.loads(l) for l in open(os.path.join(run, "calls.jsonl"))]
            cfg = json.load(open(os.path.join(run, "config.json")))
            mark = {r["id"]: r["score"] for r in calls if r["probe"] == "base"}
            ga = [c for c in sel[a] if mark.get(c["id"]) is not None]
            gb = [c for c in sel[b] if mark.get(c["id"]) is not None]
            fail = {g: 1 - len(x) / len(sel[gg]) for g, x, gg in (("A", ga, a), ("B", gb, b))}
            rng = random.Random(f"D-{name}-{cfg['model']}")
            m = boot([mark[c["id"]] for c in ga], [mark[c["id"]] for c in gb], 4000, rng)
            d = boot([mark[c["id"]] - c["human"]["rater2"] for c in ga],
                     [mark[c["id"]] - c["human"]["rater2"] for c in gb], 4000, rng)
            g = {"M": {"estimate": m[0], "ci95": [m[1], m[2]]}, "D": {"estimate": d[0], "ci95": [d[1], d[2]]},
                 "verdict": verdict(d[1], d[2]), "failed": fail}
            if abs(fail["A"] - fail["B"]) > 0.05:
                g["warning"] = "failed-grading rates differ by more than 5 points between groups"
            res["graders"][cfg["model"]] = g
            print(name, cfg["model"], g["verdict"], f"D {d[0]:+.3f} [{d[1]:+.3f}, {d[2]:+.3f}]",
                  f"M {m[0]:+.3f}", f"H {h[0]:+.3f}")
        print(name, res["design_reading"], f"H {h[0]:+.3f} [{h[1]:+.3f}, {h[2]:+.3f}]")
        out["contrasts"][name] = res
    json.dump(out, open(os.path.join(HERE, "out", "result.json"), "w"), indent=1)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("draw")
    p.add_argument("--cases", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("floor")
    p.add_argument("--cases", required=True)
    p.add_argument("--sims", type=int, default=300)
    p = sub.add_parser("analyse")
    p.add_argument("--cases", required=True)
    p.add_argument("--runs", nargs="+", required=True)
    a = ap.parse_args()
    {"draw": cmd_draw, "floor": cmd_floor, "analyse": cmd_analyse}[a.cmd](a)


if __name__ == "__main__":
    main()
