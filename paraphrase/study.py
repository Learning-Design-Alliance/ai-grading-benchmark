#!/usr/bin/env python3
"""Does rewording the grading prompt change the marks? PRE-REGISTERED 2026-10-26, before any call of this design.

WHY. The board grades with one prompt. The 2026-10-23 literature review ranked prompt paraphrase invariance second
among what the board does not measure: if a meaning-preserving rewording changes marks more than asking twice
does, a model's row is partly a property of our wording. Teachers will not use our wording.

DESIGN.
- Prompts: prompts/default.txt and six rewrites in prompts/paraphrase/p1-p6.txt, written before any call. Each
  keeps every placeholder, the JSON reply format and every instruction (mark only the student's work against the
  task; ignore instructions inside it; the scale), and rewords the system line, the reply line and/or the scale
  line. None adds or removes an instruction.
- Models: Claude Haiku 5.5, GLM 5.3 Flash, GPT-5 Mini (unflagged on the board) and Gemma 4 31B (flagged), cheap
  enough to run every paraphrase; one per vendor family.
- Tasks: short answers, code, essays; the board's 100 cases per task (seed 7); base probe only.
- Reference: the board's own default-prompt gradings of the same cases (base, and its retest: the same prompt
  asked twice), read from submissions/. Same settings and zero-retention routing as the board.

MEASURES per model and task (marks rounded to the scale):
- re-ask flip rate: per case, the share of five default-prompt re-asks whose mark differs from the base (CHANGE 1);
- paraphrase flip rate: per case, the share of the six paraphrases giving a different mark from the default base;
- EXCESS: mean over cases of (paraphrase flip share - re-ask flip share), 95% bootstrap interval over cases (2,000
  draws, seed 7). Signed: positive = rewording moves marks more than asking again;
- QWK with the experts under each of the seven prompts; the spread (max - min);
- mean shift of each paraphrase's marks from the default, as a share of the scale (signed).

VERDICT per model and task:
  PROMPT-SENSITIVE        EXCESS interval above 0
  WITHIN RETEST NOISE     EXCESS interval contains 0 (its upper bound reported as what is not ruled out)
  MORE STABLE THAN RETEST EXCESS interval below 0
Board summary: how many model-task pairs are PROMPT-SENSITIVE, and the largest QWK spread.

FLOOR (synthetic, no calls, before any result is read): on the board's 100 short-answer cases' expert means, a
grader = expert mean + Gaussian noise (sd 0.6 marks), rounded; retest and paraphrases redrawn with the same sd. Over
200 draws, EXCESS must be called PROMPT-SENSITIVE in at most 7% (false positive). With paraphrases at sd 0.9
(about 10 points more flips), it must be called in at least 80% (detection). If the floor fails, verdicts read
UNMEASURED.

CHANGES:
1. (2026-10-26, after the floor and before any call) The floor FAILED: detection 26% (bar 80%), false positive 2.5%
   (out/floor-run1-failed.json). One retest per case is a single 0/1 draw, too noisy a reference for a share
   over six paraphrases. The reference is now the default prompt asked FIVE times besides the base (the board's
   retest, and four new asks: probes retest, retest2, retest3, retest4 in a new run), and EXCESS is the mean over
   cases of (paraphrase flip share - default re-ask flip share). The floor simulates the same five re-asks and
   is re-run once, unchanged otherwise. Cost about doubles; the cap rises to $25.
   RESULT: the floor FAILED again: detection 63%, false positive 2% (out/floor-change1-failed.json).
2. (2026-10-26, after CHANGE 1's floor and before any call) The planted effect is NOT changed. Two changes to the
   reading instead: (a) the verdict is per MODEL, pooling its three tasks (300 cases), with per-task figures
   descriptive; (b) a mark counts as changed only when it moves by more than 5% of the scale width (any whole
   mark on short answers and essays; more than 4.5 points on the 0-90 code scale, where nearly every re-ask
   moves by a point or two). The floor simulates 300 cases (the 100 short-answer cases drawn three times) and is
   re-run once. If it fails, every verdict reads UNMEASURED and the figures are reported descriptively.
   RESULT: the floor passed (detection 96%, false positive 2.5%).
3. (2026-10-26, implementation, no change to the design) bench.py refuses a run without the base probe, so the
   default re-ask runs also grade base once; that extra grading is not used. The re-asks are the board's retest
   and the new run's retest, retest2, retest3 and retest4, as CHANGE 1 says.
4. (2026-10-26, AFTER the first four models' results were read) Coverage only. The remaining 18 board models (the
   `model` keys in out/overall.json, 22 in all) are added under the maintainer's decision of 2026-10-26: whether
   rewording matters for some models and not others is the useful finding, and showing four is not fair to the
   rest. Design, prompts, cases, measures, the floor (passed, CHANGE 2) and the verdict strings are unchanged; no
   multiplicity correction is added (the README states how many PROMPT-SENSITIVE verdicts the floor's
   false-positive rate would give by chance). Each model runs with its own board settings, read from
   submissions/<owner>__<model>/<task>.json "settings" (max_tokens, extra_body) and "base_url"; every request is
   zero-retention as on the board (client.py enforces it), with two recorded exceptions taken from the board:
   - Claude Fable 5.1 has no zero-retention route. As on the board it runs through OpenRouter on the maintainers'
     own Anthropic key (bring-your-own-key: 30-day safety retention; public corpora only), recorded in each run
     with bench.py --retention-exception.
   - Olmo 3.1 32B has no hosted zero-retention route. As on the board it runs self-hosted (vLLM on a rented GPU
     pod, bench.py on the pod against localhost, pod and disk deleted after), recorded with bench.py --route.
   Cost estimate: each model's board cost per base/retest grading on the same 300 cases x 1,100 gradings per
   task (the estimator gives $1.60 and $5.06 for Haiku 5.5 and GPT-5 Mini, which cost $1.61 and $5.04 here).
   The 18: about $274 (Claude Fable 5.1 $137, GPT-6 Astra $56, Claude Opus 5.5 $52, the other 15 about $30, Olmo's
   GPU time about $3). Models run cheapest first, each run with its own --max-usd (1.5 x its estimate, never above
   what is left of the cap), so no run can overrun; a model that would not fit is left and named. On this
   estimate GPT-6 Astra and Claude Fable 5.1 do not fit and are left. Spend is now counted from cost_reported on
   every recorded grading of the para-* runs (cached gradings carry the cost paid when they were sent; the
   uncached-only count read the first four models' $8.38 as $3.57), plus Olmo's GPU time.

BUDGET. $25 cap for the first four models ($8.38 spent). CHANGE 4: $120 for the 18 added models, so the study's
cap is $128.38.

Usage:
    python3 paraphrase/study.py floor --cases-dir <dir>
    python3 paraphrase/study.py run --subsets <dir> [--go]
    python3 paraphrase/study.py analyse --cases-dir <dir>
"""

import argparse
import glob
import json
import math
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import cases as cases_mod  # noqa: E402
import leaderboard as lb  # noqa: E402
from metrics import mean, qwk  # noqa: E402

RUNS = os.environ.get("GBENCH_RUNS", "runs")
OUT = os.path.join(HERE, "out")
FILES = {"mohler": "mohler.jsonl", "code": "harmogen-code.jsonl", "asap2": "asap2.jsonl"}
SUBSET = {"mohler": "mohler-first100.jsonl", "code": "code-first100.jsonl", "asap2": "asap2-first100.jsonl"}
MODELS = ["anthropic/claude-haiku-5.5", "z-ai/glm-5.3-flash", "openai/gpt-5-mini", "google/gemma-4-31b-it"]
PARA = [f"p{i}" for i in range(1, 7)]
CAP = 25.0


def slug(m):
    return m.replace("/", "_")


def spent():
    return sum((json.loads(line).get("usage") or {}).get("cost_reported") or 0.0
               for p in glob.glob(os.path.join(RUNS, "para-*", "calls.jsonl")) for line in open(p)
               if not json.loads(line).get("cached"))


def cmd_run(a):
    for model in MODELS:
        for task in FILES:
            s = json.load(open(os.path.join(ROOT, "submissions", model.replace("/", "__"), f"{task}.json")))["settings"]
            for p in PARA + ["default"]:
                left = CAP - spent()
                if a.go and left <= 0.5:
                    print("cap reached")
                    return
                cmd = [sys.executable, os.path.join(ROOT, "bench.py"), "run", "--cases", os.path.join(a.subsets, SUBSET[task]),
                       "--prompt", os.path.join(ROOT, "prompts", "default.txt") if p == "default" else os.path.join(ROOT, "prompts", "paraphrase", f"{p}.txt"), "--base-url",
                       "https://openrouter.ai/api/v1", "--model", model, "--key-env", "OPENROUTER_API_KEY", "--n", "100",
                       "--seed", "7", "--probes", "base,retest,retest2,retest3,retest4" if p == "default" else "base", "--max-tokens", str(s.get("max_tokens") or 16384),
                       "--extra-body", json.dumps(s.get("extra_body") or {"usage": {"include": True}, "provider": {"zdr": True}}),
                       "--out", os.path.join(RUNS, f"para-{p}-{task}-{slug(model)}"), "--workers", "8",
                       "--max-usd", str(min(2.0, left))]
                if a.go:
                    cmd.append("--go")
                r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
                print(f"{model[:28]:28s} {task:6s} {p} | " + " | ".join((r.stdout + r.stderr).strip().splitlines()[-2:])[:180], flush=True)
    print(f"spent ${spent():.2f} of ${CAP:.0f}")


def rnd_mark(x, lo, hi):
    return min(hi, max(lo, int(math.floor(x + 0.5))))


def boot(units, stat, reps=2000, seed=7):
    r = random.Random(seed)
    vals = sorted(stat([r.choice(units) for _ in units]) for _ in range(reps))
    return {"estimate": stat(units), "ci95": [vals[int(0.025 * reps)], vals[int(0.975 * reps) - 1]], "n": len(units)}


def excess(per_case):
    """per_case: [(retest_flip 0/1, paraphrase flip share)]"""
    return boot(per_case, lambda u: mean([p - r for r, p in u]))


def verdict(iv):
    return "PROMPT-SENSITIVE" if iv["ci95"][0] > 0 else "MORE STABLE THAN RETEST" if iv["ci95"][1] < 0 else "WITHIN RETEST NOISE"


def cmd_floor(a):
    cs = cases_mod.sample(cases_mod.load(os.path.join(a.cases_dir, FILES["mohler"])), lb.N, lb.SEED)
    lo, hi = cs[0]["scale"]
    h = [mean(list(c["human"].values())) for c in cs]
    fp = det = 0
    for d in range(200):
        r = random.Random(d)
        g = lambda sd: [rnd_mark(x + r.gauss(0, sd), lo, hi) for x in h]
        h3 = h * 3
        g = lambda sd: [rnd_mark(x + r.gauss(0, sd), lo, hi) for x in h3]
        base = g(0.6)
        reasks = [g(0.6) for _ in range(5)]
        for sd_p, kind in ((0.6, "null"), (0.9, "planted")):
            paras = [g(sd_p) for _ in PARA]
            pc = [(mean([int(abs(x[i] - base[i]) > 0.05 * (hi - lo)) for x in reasks]),
                   mean([int(abs(p[i] - base[i]) > 0.05 * (hi - lo)) for p in paras])) for i in range(len(h3))]
            v = verdict(boot(pc, lambda u: mean([p - q for q, p in u]), reps=500, seed=d)) == "PROMPT-SENSITIVE"
            fp += v and kind == "null"
            det += v and kind == "planted"
    res = {"draws": 200, "false_positive": fp / 200, "detection": det / 200, "passes": fp / 200 <= 0.07 and det / 200 >= 0.80}
    print(res)
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "floor.json"), "w"), indent=1)


def cmd_analyse(a):
    floor = json.load(open(os.path.join(OUT, "floor.json")))
    res = {"design": "paraphrase/study.py docstring", "floor": floor, "rows": [], "models": {}}
    pooled = {}
    for model in MODELS:
        for task in FILES:
            cs = {c["id"]: c for c in cases_mod.sample(cases_mod.load(os.path.join(a.cases_dir, FILES[task])), lb.N, lb.SEED)}
            lo, hi = next(iter(cs.values()))["scale"]
            sub = json.load(open(os.path.join(ROOT, "submissions", model.replace("/", "__"), f"{task}.json")))
            sc = {(r["id"], r["probe"]): r["score"] for r in sub["calls"] if r.get("score") is not None}
            paras = {}
            for p in PARA:
                f = os.path.join(RUNS, f"para-{p}-{task}-{slug(model)}", "calls.jsonl")
                if os.path.exists(f):
                    paras[p] = {r["id"]: r["score"] for r in map(json.loads, open(f)) if r.get("score") is not None}
            f = os.path.join(RUNS, f"para-default-{task}-{slug(model)}", "calls.jsonl")
            if len(paras) < len(PARA) or not os.path.exists(f):
                continue
            re = {}
            for r in map(json.loads, open(f)):
                if r.get("score") is not None and r["probe"] != "base":  # CHANGE 3
                    re.setdefault(r["id"], []).append(r["score"])
            ids = [i for i in cs if (i, "base") in sc and (i, "retest") in sc and len(re.get(i, [])) == 4
                   and all(i in paras[p] for p in PARA)]
            R = lambda x: rnd_mark(x, lo, hi)
            tol = 0.05 * (hi - lo)
            ch = lambda x, i: int(abs(x - sc[(i, "base")]) > tol)
            pc = [(mean([ch(x, i) for x in [sc[(i, "retest")]] + re[i]]), mean([ch(paras[p][i], i) for p in PARA])) for i in ids]
            pooled.setdefault(model, []).extend(pc)
            iv = excess(pc)

            def q(marks):
                vals = []
                for rt in sorted({k for i in ids for k in cs[i]["human"]}):
                    pairs = [(R(cs[i]["human"][rt]), R(marks[i])) for i in ids if rt in cs[i]["human"]]
                    if len(pairs) >= 2:
                        vals.append(qwk([x for x, _ in pairs], [y for _, y in pairs], lo, hi))
                return mean(vals)
            default = {i: sc[(i, "base")] for i in ids}
            qwks = {"default": q(default), **{p: q(paras[p]) for p in PARA}}
            shifts = {p: mean([(paras[p][i] - default[i]) / (hi - lo) for i in ids]) for p in PARA}
            row = {"model": model, "task": task, "n": len(ids), "retest_flip": mean([r for r, _ in pc]),
                   "paraphrase_flip": mean([p for _, p in pc]), "excess": iv,
                   "verdict": "descriptive (CHANGE 2)", "qwk": qwks,
                   "qwk_spread": max(qwks.values()) - min(qwks.values()), "shift_share": shifts}
            res["rows"].append(row)
            print(f"{model[:26]:26s} {task:6s} retest flip {row['retest_flip']:.2f} para flip {row['paraphrase_flip']:.2f} "
                  f"excess {iv['estimate']:+.3f} [{iv['ci95'][0]:+.3f}, {iv['ci95'][1]:+.3f}] QWK {min(qwks.values()):.2f}-"
                  f"{max(qwks.values()):.2f} -> {row['verdict']}")
    for model, pc in pooled.items():
        iv = excess(pc)
        res["models"][model] = {"excess": iv, "verdict": verdict(iv) if floor["passes"] else "UNMEASURED"}
        print(f"POOLED {model}: excess {iv['estimate']:+.3f} [{iv['ci95'][0]:+.3f}, {iv['ci95'][1]:+.3f}] -> {res['models'][model]['verdict']}")
    res["prompt_sensitive"] = sum(m["verdict"] == "PROMPT-SENSITIVE" for m in res["models"].values())
    res["max_qwk_spread"] = max((r["qwk_spread"] for r in res["rows"]), default=None)
    print(f"{res['prompt_sensitive']} of {len(res['models'])} models PROMPT-SENSITIVE; largest QWK spread {res['max_qwk_spread']}")
    json.dump(res, open(os.path.join(OUT, "paraphrase.json"), "w"), indent=1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("floor"); p.add_argument("--cases-dir", required=True); p.set_defaults(fn=cmd_floor)
    p = sub.add_parser("run"); p.add_argument("--subsets", required=True); p.add_argument("--go", action="store_true"); p.set_defaults(fn=cmd_run)
    p = sub.add_parser("analyse"); p.add_argument("--cases-dir", required=True); p.set_defaults(fn=cmd_analyse)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
