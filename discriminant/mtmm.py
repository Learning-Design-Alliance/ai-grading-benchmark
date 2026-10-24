#!/usr/bin/env python3
"""
Discriminant validity: when an AI grader scores several traits of the same essay, does it tell them apart
as well as a second human rater does, or does it give one overall impression six times?

PRE-REGISTERED 2026-10-24, before any call of this design. The ELLIPSE raters' trait scores had been read
for other studies (fairness-ellipse/, and the research repository's rater-structure work); no model has
scored ELLIPSE's analytic traits.

CORPUS. ELLIPSE (Crossley et al. 2023; CC BY-NC-SA 4.0; docs/DATA-SOURCES.md): essays by English learners in
grades 8-12, each scored by two of 27 raters on six analytic traits, 1-5 (cohesion, syntax, vocabulary,
phraseology, grammar, conventions), from the raw-rater file. Only essays in the authors' final corpus are
used, with both raters' six scores present. $ELLIPSE_DIR holds the raw-rater CSV and the final train/test CSVs.

DRAW. 300 essays, stratified on rater 1's mean trait score in five equal-count bands, seed 20261024.

THE TASK. One call per essay and model: the ELLIPSE analytic rubric for all six traits (rubric text from
ELL_Rubrics.docx, levels 1-5 per trait) and the essay; the reply is a JSON object with an integer 1-5 for each
trait. prompts/traits.txt, fixed by this commit. Default sampling settings; OpenRouter with zero data
retention; max_tokens 16384.

GRADERS. Claude Haiku 5.5, Gemini 3.5 Flash Lite, GPT-5 Mini, Qwen3 235B (DeepInfra), DeepSeek V4.1 Flash,
Gemma 4 31B (CoreWeave), Claude Opus 5.5 (Google endpoint).

STATISTICS, per grader, with a 2,000-draw bootstrap over essays:
- trait agreement: QWK of the grader with rater 1 and with rater 2, per trait, averaged; beside the
  human ceiling, QWK of rater 1 with rater 2 per trait.
- DISCRIMINATION (PRIMARY): for each trait t, convergent r(grader t, rater-2 t) minus the mean discriminant
  r(grader t, rater-2 u) over the five other traits u; averaged over traits. The human reference is the
  same quantity with rater 1 in the grader's place. A grader that gives one overall impression has
  convergent about equal to discriminant and a gap near 0. Rater 2 is the reference for both, so neither
  side is compared with itself.
- D = grader's discrimination minus rater 1's (negative = blurs traits more than a second human).
- halo index (reported): mean off-diagonal correlation among the grader's own six traits, beside the same
  for rater 1.

VERDICTS (per grader):
- "DISTINGUISHES TRAITS AS WELL AS A SECOND RATER": D's interval lies above -0.05.
- "BLURS TRAITS": D's interval lies wholly below -0.05.
- "INCONCLUSIVE": anything else.
Failed or unparseable replies are reported; if more than 5% of essays fail for a grader, its verdict
carries a warning and is computed on the essays it scored.

FLOOR (`mtmm.py floor`, before any call). On the real draw's human scores: a simulated grader that copies the
human trait structure (rater 1's six scores plus N(0, 0.6) per trait, rounded, clipped) must read
DISTINGUISHES in at least 90% of 200 simulations; a halo grader (rater 1's mean of six plus the same noise,
the one value given to every trait) must read BLURS in at least 90%; and a grader of independent noise
around the mean must not read DISTINGUISHES in more than 5%.

    python3 mtmm.py draw
    python3 mtmm.py floor
    python3 mtmm.py run --model <m> [--provider <p>] --go
    python3 mtmm.py analyse --runs <run dir> [...]

Reads $ELLIPSE_DIR. Commits aggregates only (out/).

CHANGES: none yet.
"""

import argparse
import csv
import json
import math
import os
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from metrics import qwk  # noqa: E402

TRAITS = ["Cohesion", "Syntax", "Vocabulary", "Phraseology", "Grammar", "Conventions"]
SEED = 20261024
N = 300
PROMPT = os.path.join(HERE, "prompts", "traits.txt")


def essays():
    d = os.environ.get("ELLIPSE_DIR")
    if not d:
        sys.exit("set ELLIPSE_DIR (docs/DATA-SOURCES.md, ELLIPSE)")
    csv.field_size_limit(10 ** 9)
    final = {}
    for name in ("ELLIPSE_Final_github_train.csv", "ELLIPSE_Final_github_test.csv"):
        for r in csv.DictReader(open(os.path.join(d, name), encoding="utf-8", errors="replace")):
            final[r["text_id_kaggle"]] = r
    out = []
    for r in csv.DictReader(open(os.path.join(d, "ellipsis_raw_rater_scores_anon_all_essay.csv"), encoding="utf-8", errors="replace")):
        m = final.get(r["text_id_kaggle"])
        if not m:
            continue
        try:
            r1 = [float(r[f"{t}_1"]) for t in TRAITS]
            r2 = [float(r[f"{t}_2"]) for t in TRAITS]
        except (TypeError, ValueError):
            continue
        if min(r1 + r2) < 1:
            continue
        out.append({"id": r["text_id_kaggle"], "text": (m.get("full_text") or r["Text"]).strip(), "prompt": (m.get("prompt") or "").strip(),
                    "r1": r1, "r2": r2})
    return out


def draw(es):
    rng = random.Random(SEED)
    es = sorted(es, key=lambda e: (sum(e["r1"]), e["id"]))
    bands = [es[i * len(es) // 5:(i + 1) * len(es) // 5] for i in range(5)]
    pick = []
    for b in bands:
        pick += rng.sample(b, N // 5)
    return pick


def corr(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy) if sx and sy else float("nan")


def discrimination(g, ref):
    """g, ref: lists of six-score rows. Mean over traits of convergent minus mean discriminant correlation."""
    vals = []
    for t in range(6):
        gt = [row[t] for row in g]
        conv = corr(gt, [row[t] for row in ref])
        disc = [corr(gt, [row[u] for row in ref]) for u in range(6) if u != t]
        vals.append(conv - sum(disc) / len(disc))
    return sum(vals) / len(vals)


def halo(g):
    cs = [corr([r[t] for r in g], [r[u] for r in g]) for t in range(6) for u in range(t + 1, 6)]
    return sum(cs) / len(cs)


def d_stat(rows):
    """rows: [(grader six, rater1 six, rater2 six)]."""
    g = [r[0] for r in rows]
    h1 = [r[1] for r in rows]
    h2 = [r[2] for r in rows]
    return discrimination(g, h2) - discrimination(h1, h2)


def verdict(lo, hi):
    if lo > -0.05:
        return "DISTINGUISHES TRAITS AS WELL AS A SECOND RATER"
    if hi < -0.05:
        return "BLURS TRAITS"
    return "INCONCLUSIVE"


def boot(rows, fn, reps, seed):
    rng = random.Random(seed)
    vals = sorted(fn([rows[rng.randrange(len(rows))] for _ in rows]) for _ in range(reps))
    vals = [v for v in vals if v == v]
    return fn(rows), vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]


def clip(x):
    return min(5, max(1, int(round(x))))


def cmd_draw(a):
    pick = draw(essays())
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    json.dump({"n": len(pick), "seed": SEED, "ids_sha256": __import__("hashlib").sha256(",".join(e["id"] for e in pick).encode()).hexdigest()},
              open(os.path.join(HERE, "out", "draw.json"), "w"), indent=1)
    print(len(pick), "essays")


def cmd_floor(a):
    pick = draw(essays())
    res = {}
    for kind in ("structure", "halo", "noise"):
        hits = {"DISTINGUISHES TRAITS AS WELL AS A SECOND RATER": 0, "BLURS TRAITS": 0, "INCONCLUSIVE": 0}
        for s in range(a.sims):
            rng = random.Random(f"floor-{kind}-{s}")
            rows = []
            for e in pick:
                if kind == "structure":
                    g = [clip(x + rng.gauss(0, 0.6)) for x in e["r1"]]
                elif kind == "halo":
                    v = clip(sum(e["r1"]) / 6 + rng.gauss(0, 0.6))
                    g = [v] * 6
                else:
                    m = sum(e["r1"]) / 6
                    g = [clip(m + rng.gauss(0, 1.0)) for _ in range(6)]
                rows.append((g, e["r1"], e["r2"]))
            _, lo, hi = boot(rows, d_stat, 200, s)
            hits[verdict(lo, hi)] += 1
        res[kind] = {k: v / a.sims for k, v in hits.items()}
        print(kind, res[kind], flush=True)
    res["pass"] = (res["structure"]["DISTINGUISHES TRAITS AS WELL AS A SECOND RATER"] >= 0.9 and res["halo"]["BLURS TRAITS"] >= 0.9
                   and res["noise"]["DISTINGUISHES TRAITS AS WELL AS A SECOND RATER"] <= 0.05)
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    json.dump(res, open(os.path.join(HERE, "out", "floor.json"), "w"), indent=1)
    print("FLOOR PASSES" if res["pass"] else "FLOOR FAILS")


def render(e):
    t = open(PROMPT, encoding="utf-8").read()
    return [{"role": "user", "content": t.replace("{assignment}", e["prompt"]).replace("{essay}", e["text"])}]


def parse(text):
    if not text:
        return None
    for m in re.finditer(r"\{[^{}]*\}", text, flags=re.S):
        try:
            o = json.loads(m.group(0))
        except ValueError:
            continue
        try:
            vals = [int(round(float(o[t.lower()]))) for t in TRAITS]
        except (KeyError, TypeError, ValueError):
            continue
        if all(1 <= v <= 5 for v in vals):
            return vals
    return None


def cmd_run(a):
    from client import OpenAICompatible
    pick = draw(essays())
    out = a.out or os.path.join(os.environ.get("GBENCH_RUNS", "runs"), "mtmm-" + a.model.replace("/", "_"))
    prov = {"zdr": True}
    if a.provider:
        prov.update({"order": [a.provider], "allow_fallbacks": False})
    chars = sum(len(render(e)[0]["content"]) for e in pick)
    print(f"{len(pick)} calls, about {chars / 4 / 1e6:.2f}M prompt tokens with {a.model}")
    if not a.go:
        return
    cl = OpenAICompatible("https://openrouter.ai/api/v1", a.model, "OPENROUTER_API_KEY", os.path.join(out, ".cache"),
                          max_tokens=16384, extra={"usage": {"include": True}, "provider": prov})
    os.makedirs(out, exist_ok=True)

    def one(e):
        rec = cl.call(render(e), tag="traits")
        return {"id": e["id"], "scores": parse(rec["text"]) if rec["error"] is None else None, "error": rec["error"],
                "usage": rec["usage"], "served_model": rec["served_model"], "provider": rec["provider"]}
    with ThreadPoolExecutor(a.workers) as ex:
        res = list(ex.map(one, pick))
    json.dump({"model": a.model, "provider": prov}, open(os.path.join(out, "config.json"), "w"))
    with open(os.path.join(out, "calls.jsonl"), "w") as fh:
        for r in res:
            fh.write(json.dumps(r) + "\n")
    print(f"{sum(r['scores'] is None for r in res)} unparsed, ${sum((r['usage'].get('cost_reported') or 0) for r in res):.2f}")


def cmd_analyse(a):
    pick = {e["id"]: e for e in draw(essays())}
    human = list(pick.values())
    h_rows = [(e["r1"], e["r1"], e["r2"]) for e in human]
    ceil = [qwk([e["r1"][t] for e in human], [e["r2"][t] for e in human], 1, 5) for t in range(6)]
    out = {"design": "mtmm.py docstring", "n": len(human), "human": {
        "trait_qwk_r1_r2": dict(zip(TRAITS, ceil)), "discrimination_r1": discrimination([e["r1"] for e in human], [e["r2"] for e in human]),
        "halo_r1": halo([e["r1"] for e in human])}, "graders": {}}
    for run in a.runs:
        model = json.load(open(os.path.join(run, "config.json")))["model"]
        calls = [json.loads(l) for l in open(os.path.join(run, "calls.jsonl"))]
        ok = [(c["scores"], pick[c["id"]]["r1"], pick[c["id"]]["r2"]) for c in calls if c["scores"]]
        d, lo, hi = boot(ok, d_stat, 2000, 7)
        tq = [(qwk([r[0][t] for r in ok], [r[1][t] for r in ok], 1, 5) + qwk([r[0][t] for r in ok], [r[2][t] for r in ok], 1, 5)) / 2 for t in range(6)]
        g = {"n": len(ok), "failed_share": 1 - len(ok) / len(calls), "D": {"estimate": d, "ci95": [lo, hi]}, "verdict": verdict(lo, hi),
             "discrimination": discrimination([r[0] for r in ok], [r[2] for r in ok]), "halo": halo([r[0] for r in ok]),
             "trait_qwk": dict(zip(TRAITS, tq)), "trait_share_of_ceiling": {t: q / c for t, q, c in zip(TRAITS, tq, ceil)},
             "cost_reported_usd": sum((c["usage"].get("cost_reported") or 0) for c in calls)}
        if g["failed_share"] > 0.05:
            g["warning"] = "more than 5% of essays failed"
        out["graders"][model] = g
        print(model, g["verdict"], f"D {d:+.3f} [{lo:+.3f}, {hi:+.3f}]", f"halo {g['halo']:.2f} vs human {out['human']['halo_r1']:.2f}")
    json.dump(out, open(os.path.join(HERE, "out", "result.json"), "w"), indent=1)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("draw")
    p = sub.add_parser("floor"); p.add_argument("--sims", type=int, default=200)
    p = sub.add_parser("run"); p.add_argument("--model", required=True); p.add_argument("--provider")
    p.add_argument("--out"); p.add_argument("--workers", type=int, default=6); p.add_argument("--go", action="store_true")
    p = sub.add_parser("analyse"); p.add_argument("--runs", nargs="+", required=True)
    a = ap.parse_args()
    {"draw": cmd_draw, "floor": cmd_floor, "run": cmd_run, "analyse": cmd_analyse}[a.cmd](a)


if __name__ == "__main__":
    main()
