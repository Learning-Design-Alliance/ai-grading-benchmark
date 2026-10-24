#!/usr/bin/env python3
"""The video task's pre-registered statistics beyond bench.py's report (video/PREREG.md).

For each run (one model, video or 16 frames), from its calls.jsonl and the cases file:

- AGREEMENT BEYOND LENGTH. The partial Spearman correlation of the model's base mark with the raters' mean
  GRS, controlling for the recording's length: ranks are taken within each task, each rank is residualised
  on the length rank by least squares within the task, and the residuals are correlated. Per task, and
  pooled over the four tasks' residuals. 95% interval by bootstrap over recordings, resampled within task,
  2,000 draws, seed 7. HUMAN REFERENCE: the same statistic for each rater's GRS against the mean of the
  other raters on the recordings that rater scored, averaged over raters (raters 1 and 3 scored all; 0 and 2
  halves). Verdict per model, as pre-registered: WATCHES THE RECORDING if the pooled interval lies above 0;
  ADDS NOTHING TO THE STOPWATCH if it contains 0.
- TEXT ONLY. QWK of the text_only marks against the raters (mean over raters), and the same partial
  correlation, beside the base figures.
- LENGTH ALONE. The Spearman correlation of minus the length with the raters' mean GRS (no model).
- FAILED ATTEMPTS. On balloon resection and suture and knot: recordings most raters marked failed, and how
  many of them the model gave 4.
- HUMAN CEILING. The raters' mean pairwise QWK on these recordings, overall and per task.

    python3 video/analyse.py --cases $LASANA_DIR/lasana.jsonl --runs <run dir> ... --out out/video/extras.json

Reads the cases file (the corpus's ratings and lengths) and the runs' marks; writes aggregates only.
"""
import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cases as cases_mod  # noqa: E402
from metrics import mean, qwk  # noqa: E402

LO, HI = 4, 20


def length_s(c):
    t = c["response"].split("length ", 1)[1]
    m, s = t.split(" min ")
    return int(m) * 60 + int(s.split(" s")[0])


def ranks(x):
    order = sorted(range(len(x)), key=lambda i: x[i])
    r = [0.0] * len(x)
    i = 0
    while i < len(order):  # average ranks for ties
        j = i
        while j + 1 < len(order) and x[order[j + 1]] == x[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2
        i = j + 1
    return r


def resid(y, x):
    my, mx = mean(y), mean(x)
    vx = sum((a - mx) ** 2 for a in x)
    b = 0.0 if vx == 0 else sum((a - mx) * (c - my) for a, c in zip(x, y)) / vx
    return [c - my - b * (a - mx) for a, c in zip(x, y)]


def corr(a, b):
    ma, mb = mean(a), mean(b)
    da = sum((x - ma) ** 2 for x in a) ** 0.5
    db = sum((y - mb) ** 2 for y in b) ** 0.5
    return None if da == 0 or db == 0 else sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (da * db)


def partial(units):
    """units: [(task, y, x, length)] -> pooled partial Spearman of y and x controlling for length, ranks and
    residuals within task, and per task."""
    by = {}
    for t, y, x, L in units:
        by.setdefault(t, []).append((y, x, L))
    ry, rx, per = [], [], {}
    for t, us in by.items():
        if len(us) < 4:
            continue
        L = ranks([u[2] for u in us])
        a, b = resid(ranks([u[0] for u in us]), L), resid(ranks([u[1] for u in us]), L)
        per[t] = corr(a, b)
        ry += a
        rx += b
    return corr(ry, rx), per


def boot(units, stat, reps=2000, seed=7):
    by = {}
    for u in units:
        by.setdefault(u[0], []).append(u)
    rng = random.Random(seed)
    vals = []
    for _ in range(reps):
        s = [rng.choice(us) for us in by.values() for _ in us]
        v = stat(s)
        if v is not None:
            vals.append(v)
    vals.sort()
    return [vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]] if vals else None


def human_reference(cs):
    raters = sorted({r for c in cs for r in c["human"]})
    out = {}
    for r in raters:
        units = [(c["task"], c["human"][r], mean([v for k, v in c["human"].items() if k != r]), length_s(c))
                 for c in cs if r in c["human"] and len(c["human"]) >= 2]
        if len(units) >= 20:
            out[r] = partial(units)[0]
    return mean(list(out.values())), out


def ceiling(cs):
    raters = sorted({r for c in cs for r in c["human"]})
    qs = []
    for i, a in enumerate(raters):
        for b in raters[i + 1:]:
            p = [(c["human"][a], c["human"][b]) for c in cs if a in c["human"] and b in c["human"]]
            if len(p) >= 20:
                qs.append(qwk([round(x) for x, _ in p], [round(y) for _, y in p], LO, HI))
    return mean(qs) if qs else None


def model_qwk(cs, marks):
    raters = sorted({r for c in cs for r in c["human"]})
    vals = []
    for r in raters:
        p = [(round(c["human"][r]), marks[c["id"]]) for c in cs if r in c["human"] and c["id"] in marks]
        if len(p) >= 20:
            vals.append(qwk([x for x, _ in p], [y for _, y in p], LO, HI))
    return mean(vals) if vals else None


def analyse_run(cs, run):
    calls = [json.loads(l) for l in open(os.path.join(run, "calls.jsonl"))]
    cfg = json.load(open(os.path.join(run, "config.json")))
    by = {}
    for r in calls:
        if r.get("score") is not None:
            by.setdefault(r["probe"], {})[r["id"]] = max(LO, min(HI, round(r["score"])))
    out = {"model": cfg["model"], "video_frames": cfg.get("video_frames", 0)}
    for probe in ("base", "text_only"):
        marks = by.get(probe, {})
        units = [(c["task"], mean(list(c["human"].values())), marks[c["id"]], length_s(c)) for c in cs if c["id"] in marks]
        est, per = partial(units) if units else (None, {})
        out[probe] = {"n": len(units), "qwk": model_qwk(cs, marks),
                      "beyond_length": est, "beyond_length_ci95": boot(units, lambda s: partial(s)[0]) if units else None,
                      "beyond_length_by_task": per}
    iv = out["base"]["beyond_length_ci95"]
    out["verdict"] = None if not iv else ("WATCHES THE RECORDING" if iv[0] > 0 else "ADDS NOTHING TO THE STOPWATCH")
    fails = [c for c in cs if sum(v == 4 for v in c["human"].values()) * 2 > len(c["human"])]
    base = by.get("base", {})
    out["failed_attempts"] = {"n": len(fails), "graded": sum(1 for c in fails if c["id"] in base),
                              "given_minimum": sum(1 for c in fails if base.get(c["id"]) == LO)}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True)
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    cs = cases_mod.load(a.cases)
    href, hby = human_reference(cs)
    len_alone = {}
    for t in sorted({c["task"] for c in cs}):
        sub = [c for c in cs if c["task"] == t]
        len_alone[t] = corr(ranks([-length_s(c) for c in sub]), ranks([mean(list(c["human"].values())) for c in sub]))
    res = {"design": "video/analyse.py docstring; video/PREREG.md",
           "human": {"ceiling_qwk": ceiling(cs),
                     "ceiling_qwk_by_task": {t: ceiling([c for c in cs if c["task"] == t]) for t in sorted({c["task"] for c in cs})},
                     "beyond_length": href, "beyond_length_by_rater": hby, "length_alone_spearman_by_task": len_alone},
           "runs": {}}
    for run in a.runs:
        r = analyse_run(cs, run)
        res["runs"][os.path.basename(run.rstrip("/"))] = r
        b, t = r["base"], r["text_only"]
        f = lambda v: "—" if v is None else f"{v:+.2f}"
        print(f"{os.path.basename(run):45s} qwk {f(b['qwk'])} text-only {f(t['qwk'])} | beyond length {f(b['beyond_length'])} "
              f"{b['beyond_length_ci95'] and [round(x, 2) for x in b['beyond_length_ci95']]} -> {r['verdict']}", flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1)
    print("human ceiling QWK %.3f; human beyond length %.3f" % (res["human"]["ceiling_qwk"], href))


if __name__ == "__main__":
    main()
