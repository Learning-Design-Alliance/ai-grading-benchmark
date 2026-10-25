#!/usr/bin/env python3
"""Are the intervals too narrow because answers to the same question are not independent?

Added 2026-10-25 after O'Neill (2026, "Presumed Effective", EdArXiv n29zd v3), whose audit found effect sizes
computed on the wrong unit (students counted where teams were the unit). Every interval on the board resamples
CASES. But cases share a question (short answers: 100 cases over 60 questions), a writing prompt (essays: 7
prompts) or a programming exercise (code: 3). If marks within a question move together, a case bootstrap is
too narrow. No new calls; thresholds fixed before this script read any submission.

DESIGN.
- Short answers (60 questions): for each model, the statistics the board reports from the base and probe
  gradings, each with a case bootstrap and a question (cluster) bootstrap, 2,000 draws, seed 7:
  QWK against the raters' mean; the injection, forged-note and nonsense-key-word (blicket) shifts and the
  attainment-label effect, as shares of the scale; and the pushback effect (push minus recheck, share of
  the scale) on the pushback task, whose answers are the same short answers.
  Reported: the ratio of cluster to case interval width (the design effect on the interval), and every
  statistic whose "interval excludes 0" flag changes. VERDICT per statistic family: ROBUST if no flag
  changes, CHANGES otherwise (listing them).
- Essays (7 prompts) and code (3 exercises): too few clusters for a cluster bootstrap (fewer than 20; a
  bootstrap over 7 or 3 units is not an interval). Reported instead: QWK per prompt or exercise, per model,
  and its range. The reading is that these tasks' results hold for these prompts and exercises, and the
  spread across them is the honest guide to a new one.
- Maths already resamples the problem, the unit the four versions share. Video: LASANA publishes no
  participant identifiers, so recordings by the same surgeon cannot be grouped; stated as a limit.

    python3 analyses/cluster_check.py --cases-dir <dir> --out out/cluster_check.json
"""
import argparse
import glob
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "feedback-board"))

import cases as cases_mod  # noqa: E402
import leaderboard as lb  # noqa: E402
from metrics import mean, qwk  # noqa: E402

FILES = {"mohler": "mohler.jsonl", "code": "harmogen-code.jsonl", "asap2": "asap2.jsonl"}
REPS, SEED = 2000, 7


def boot(units, stat, cluster=None):
    """95% interval; resample units, or whole clusters of units when cluster(u) is given."""
    rng = random.Random(SEED)
    if cluster:
        groups = {}
        for u in units:
            groups.setdefault(cluster(u), []).append(u)
        groups = list(groups.values())
        draw = lambda: [u for _ in groups for u in rng.choice(groups)]
    else:
        draw = lambda: [rng.choice(units) for _ in units]
    v = sorted(x for x in (stat(draw()) for _ in range(REPS)) if x is not None and x == x)
    return [v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]] if v else None


def excl0(iv):
    return iv is not None and (iv[0] > 0 or iv[1] < 0)


def compare(name, units, stat, cluster):
    a, b = boot(units, stat), boot(units, stat, cluster)
    wa, wb = (a[1] - a[0]) if a else None, (b[1] - b[0]) if b else None
    return {"statistic": name, "estimate": stat(units), "n": len(units), "case_ci95": a, "cluster_ci95": b,
            "width_ratio": (wb / wa) if wa else None, "excludes_0_case": excl0(a), "excludes_0_cluster": excl0(b)}


def calls_by(sub):
    by = {}
    for r in sub["calls"]:
        by.setdefault(r["id"], {})[r["probe"]] = r.get("score")
    return by


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases-dir", required=True)
    ap.add_argument("--out", default=os.path.join(ROOT, "out", "cluster_check.json"))
    a = ap.parse_args()
    cs_by = {t: cases_mod.sample(cases_mod.load(os.path.join(a.cases_dir, f)), lb.N, lb.SEED) for t, f in FILES.items()}
    res = {"design": "analyses/cluster_check.py docstring",
           "clusters": {t: len({c["task"] for c in cs}) for t, cs in cs_by.items()}, "mohler": [], "per_prompt": {}}
    cs = cs_by["mohler"]
    byid = {c["id"]: c for c in cs}
    lo, hi = cs[0]["scale"]
    w = hi - lo
    q_of = lambda u: byid[u[0]]["task"]
    for path in sorted(glob.glob(os.path.join(ROOT, "submissions", "*", "mohler.json"))):
        sub = json.load(open(path))
        by = calls_by(sub)
        rows = []
        base = [(i, t["base"]) for i, t in by.items() if i in byid and t.get("base") is not None]
        rows.append(compare("qwk", base, lambda us: qwk([round(mean(list(byid[i]["human"].values()))) for i, _ in us],
                                                        [round(s) for _, s in us], lo, hi) if len(us) > 1 else None, q_of))
        for probe in ("injection", "forged", "blicket"):
            d = [(i, (t[probe] - t["base"]) / w) for i, t in by.items()
                 if i in byid and t.get(probe) is not None and t.get("base") is not None]
            if len(d) >= 10:
                rows.append(compare(probe, d, lambda us: mean([x for _, x in us]), q_of))
        d = [(i, (t["ctx_high"] - t["ctx_low"]) / w) for i, t in by.items()
             if i in byid and t.get("ctx_high") is not None and t.get("ctx_low") is not None]
        if len(d) >= 10:
            rows.append(compare("attainment_label", d, lambda us: mean([x for _, x in us]), q_of))
        pp = os.path.join(os.path.dirname(path), "pushback.json")
        if os.path.exists(pp):
            pb = json.load(open(pp))
            t2 = {}
            for r in pb["calls"]:
                t2.setdefault(r["id"], {})[r["probe"]] = r
            d = [(i, ((t["push"]["score"] - t["push"]["before"]) - (t["recheck"]["score"] - t["recheck"]["before"])) / w)
                 for i, t in t2.items() if i in byid and all(t.get(k) and t[k].get("score") is not None for k in ("push", "recheck"))]
            if len(d) >= 10:
                rows.append(compare("pushback", d, lambda us: mean([x for _, x in us]), q_of))
        res["mohler"].append({"model": sub["model"], "rows": rows})
    for task in ("asap2", "code"):
        cs = cs_by[task]
        byid = {c["id"]: c for c in cs}
        lo, hi = cs[0]["scale"]
        out = []
        for path in sorted(glob.glob(os.path.join(ROOT, "submissions", "*", f"{task}.json"))):
            sub = json.load(open(path))
            by = calls_by(sub)
            per = {}
            for i, t in by.items():
                if i in byid and t.get("base") is not None:
                    per.setdefault(byid[i]["task"], []).append((round(mean(list(byid[i]["human"].values()))), round(t["base"])))
            q = {k: (qwk([x for x, _ in v], [y for _, y in v], lo, hi) if len(v) >= 10 else None) for k, v in per.items()}
            vals = [x for x in q.values() if x is not None]
            out.append({"model": sub["model"], "per_prompt_qwk": q, "n_per_prompt": {k: len(v) for k, v in per.items()},
                        "range": [min(vals), max(vals)] if vals else None})
        res["per_prompt"][task] = out
    changes = [(m["model"], r["statistic"]) for m in res["mohler"] for r in m["rows"]
               if r["excludes_0_case"] != r["excludes_0_cluster"] and r["statistic"] != "qwk"]
    ratios = sorted(r["width_ratio"] for m in res["mohler"] for r in m["rows"] if r["width_ratio"])
    res["summary"] = {"verdict": "ROBUST" if not changes else "CHANGES", "flag_changes": changes,
                      "width_ratio_median": ratios[len(ratios) // 2] if ratios else None,
                      "width_ratio_range": [ratios[0], ratios[-1]] if ratios else None}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1)
    print("clusters", res["clusters"])
    print("summary", json.dumps(res["summary"], indent=1))
    by_stat = {}
    for m in res["mohler"]:
        for r in m["rows"]:
            by_stat.setdefault(r["statistic"], []).append(r["width_ratio"])
    for k, v in by_stat.items():
        v = sorted(x for x in v if x)
        print(f"  {k:17s} width ratio median {v[len(v) // 2]:.2f} range {v[0]:.2f}-{v[-1]:.2f}")
    for task, out in res["per_prompt"].items():
        for o in out:
            print(f"  {task:6s} {o['model'][:32]:32s} per-prompt QWK range {o['range'] and [round(x, 2) for x in o['range']]}")


if __name__ == "__main__":
    main()
