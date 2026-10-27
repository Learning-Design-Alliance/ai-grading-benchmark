#!/usr/bin/env python3
"""Does a model's feedback follow the grade it is told, when that grade is wrong? PRE-REGISTERED 2026-10-27, before
any call of this design.

WHY. The board's halo (feedback-board/fb.py) compares feedback written with the teachers' mark shown against
feedback written with it hidden. Because the mark shown is the right one, a model that reads the mark as
information about the work, and writes warmer feedback on work the teacher rated well, looks the same as a model
whose tone simply copies whatever grade it is told (Kapetanovic 2026; Bulut et al. 2026 use the same shown-or-hidden
design). The literature review for the benchmark paper (research readiness, literature.md, analysis 1; entries 3.18
and 3.19) ranks a discordant arm first: tell the model a grade that disagrees with the work, and see whether the
tone follows the told grade with the work held fixed. A teacher who mis-enters a grade, or a system that passes a
wrong grade to the feedback writer, gets feedback that contradicts the work if the answer is yes.

DESIGN.
- Models: the 22 on the board. The 21 hosted ones run with the exact settings of their feedback-board runs (the
  config.json of runs/fbb-shown-<slug>: host, provider routing with zero data retention, max tokens,
  temperature, extra body), so the discordant arm differs from the board's shown arm only in the mark told.
  Olmo 3.1 32B is self-hosted; it runs only if a pod can be started for it (its own GPU_POD_STATE, vLLM as for
  its board run), otherwise it is recorded as NOT RUN with the reason.
- Cases: the leaderboard's 100 Mohler short answers (cases.sample, n = 100, seed 7; Mohler, Bunescu & Mihalcea
  2011, public), the same cases as the board's feedback columns. Expert mean m on 0-5 (46 of the 100 are 5).
- Conditions: prompts/feedback-shown.txt, unchanged, with {mark} filled with the MIRRORED grade 5 - m (a 5 is told
  as 0, a 1.5 as 3.5, a 2.5 stays 2.5), via the case field told_mark (prompting.py; nothing else in the case
  changes). The concordant arm is the board's existing shown run (the true mark m), graded with the same model,
  prompt and settings on 2026-10-24 to 2026-10-26; the date difference is stated as a limit.
- Probe: base only. A model whose feedback depends only on the work writes the same tone in both arms; a model
  whose tone copies the told grade writes cooler feedback when told the mirrored (lower) grade on good work and
  warmer feedback when told a higher grade on weak work.

MEASURES.
- tone: feedback.tone (praise minus criticism phrases per 100 words; English only), the measure that passed
  validation on MRBench (AUC 0.669). Rule-coded; its transfer to short-answer feedback is stated as a limit.
- TOLD-GRADE SLOPE S, per model: the change in tone per point of told grade with the work fixed. On each case,
  dtone = tone(true mark told) - tone(mirrored mark told) and dmark = m - (5 - m) = 2m - 5; S = sum(dtone * dmark)
  / sum(dmark^2) (least squares through the origin; cases with m = 2.5 carry no weight). Units: tone points per
  grade point; S x 5 is the tone shift across the whole 0-5 scale. POSITIVE = tone follows the told grade.
  NEGATIVE = tone moves against the told grade. 95% interval by bootstrap over cases (2,000 draws, seed 7);
  cases where either arm has no English feedback are dropped and counted.
- Beside it, the WORK SLOPE W: least-squares slope of blind tone (prompts/feedback-blind.txt, the board's hidden
  arm) on m, the tone a model gives per grade point of the work itself when no grade is told. The share S / W
  is descriptive only (W can be near 0).
- Multiplicity: across the models run, Benjamini-Hochberg at q = 0.05 on the two-sided bootstrap p-value
  (2 x the smaller share of draws on either side of 0). A model flagged by its interval but not by BH is
  reported as such.

VERDICT, per model, on S:
  TONE FOLLOWS THE TOLD GRADE            95% interval above 0 and BH-significant
  TONE MOVES AGAINST THE TOLD GRADE      95% interval below 0 and BH-significant
  NO EFFECT OF THE TOLD GRADE DETECTED   otherwise; the interval's bounds are what is not ruled out
Study-level reading (written before the run): if most models FOLLOW, the board's halo is at least partly the told
grade itself, not information use; if most show NO EFFECT with intervals that exclude a shift of half the
model's blind-tone SD across the scale, the board's halo is better read as information use.

FLOOR (run before any real discordant number is read; never enlarged to pass). Worlds shaped like the real data:
the 100 real expert means m; for each world one of four real models' blind tones (GPT-5 Mini, Claude Opus 5.5,
Gemma 3 4B, Llama 3.2 3B: blind-tone SD 1.5 to 2.3, shown-minus-blind SD 1.5 to 2.9, English coverage 81 to 100)
as the work-driven tone, resampled with replacement over cases, and noise drawn from that model's real
shown-minus-blind differences (centred to mean 0), so the null world is centred at S = 0. Planted effect: tone
moves by 0.5 of the model's blind-tone SD across the 0-5 scale (S = 0.1 SD per grade point), in both arms by the
mark each arm is told. Pass bars: the interval-and-sign rule finds the planted effect in at least 80% of worlds,
and in the null world (S = 0) flags at most 7.5%; 400 worlds each, 500 bootstrap draws per world. If it fails,
every verdict is UNMEASURED and S is shown descriptively.

LIMITS stated in advance. Tone is a rule-coded measure validated on tutoring replies, not on this feedback; it
has no human reference here, so S is about what the rule counts. The concordant arm was run up to three days
earlier, so a provider-side model change between the dates would add noise (not bias toward either sign unless
the change is in tone). A mirrored grade of 0 on a perfect answer is an extreme disagreement; S says how tone
responds to that range of disagreement, not to small errors. One prompt, one corpus, English.

BUDGET. A hard cap of $60 for the study. The board's 21 hosted shown runs cost $2.51 in all (cost_reported), so
the estimate is about $3 for one arm; per-run caps of $4, as on the board. Olmo's pod at most $5 of the cap.
Runs are checked with scripts/check_runs.py before analysis.

CHANGES:
1. 2026-10-27, before any call: cases.load dropped unknown fields, so told_mark never reached the prompt; a dry
   render through cases.load showed the true mark. cases.normalise now keeps told_mark (cases without it are
   unchanged). No design, threshold or verdict changed; the floor had run, no discordant call had been made.

Usage:
    python3 feedback-discordant/study.py cases --cases $MOHLER_CASES --out <scratch>/mohler-discordant.jsonl
    python3 feedback-discordant/study.py floor --cases $MOHLER_CASES
    python3 feedback-discordant/study.py run --cases <scratch>/mohler-discordant.jsonl [--models <slug> ...] --go
    python3 feedback-discordant/study.py analyse --cases $MOHLER_CASES
Reads the Mohler corpus (aggregates out only); runs from GBENCH_RUNS.
"""
import argparse
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
from feedback import english, feedback_text, tone  # noqa: E402
from metrics import mean  # noqa: E402

RUNS = os.environ.get("GBENCH_RUNS", "runs")
OUT = os.path.join(HERE, "out")
FLOOR_MODELS = ["openai_gpt-5-mini", "anthropic_claude-opus-5.5", "google_gemma-3-4b-it", "meta-llama_llama-3.2-3b-instruct"]
REPS, SEED = 2000, 7


def board_ids():
    return json.load(open(os.path.join(RUNS, f"fbb-shown-{FLOOR_MODELS[0]}", "config.json")))["case_ids"]


def expert_mean(c):
    return sum(c["human"].values()) / len(c["human"])


def tones(path):
    out = {}
    for l in open(path):
        r = json.loads(l)
        if r.get("probe", "base") != "base":
            continue
        t, _ = feedback_text(r.get("text"))
        if t and english(t):
            out[r["id"]] = tone(t)
    return out


def slope_origin(pairs):
    """pairs: (dmark, dtone). Least squares through the origin."""
    den = sum(x * x for x, _ in pairs)
    return None if den == 0 else sum(x * y for x, y in pairs) / den


def slope(xs, ys):
    mx, my = mean(xs), mean(ys)
    den = sum((x - mx) ** 2 for x in xs)
    return None if den == 0 else sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den


def boot(pairs, reps=REPS, seed=SEED):
    rng = random.Random(seed)
    d = sorted(v for v in (slope_origin([pairs[rng.randrange(len(pairs))] for _ in pairs]) for _ in range(reps)) if v is not None)
    lo, hi = d[int(0.025 * len(d))], d[int(0.975 * len(d)) - 1]
    p = 2 * min(sum(v <= 0 for v in d), sum(v >= 0 for v in d)) / len(d)
    return [lo, hi], min(1.0, p)


def bh(ps, q=0.05):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    k = 0
    for rank, i in enumerate(order, 1):
        if ps[i] <= q * rank / len(ps):
            k = rank
    return {order[r] for r in range(k)}


def cmd_cases(a):
    cs = {c["id"]: c for c in cases_mod.load(a.cases)}
    with open(a.out, "w") as fh:
        for i in board_ids():
            c = dict(cs[i])
            lo, hi = c["scale"]
            c["told_mark"] = f"{hi + lo - expert_mean(c):g}"
            fh.write(json.dumps(c) + "\n")
    print("wrote", a.out)


def cmd_floor(a):
    cs = {c["id"]: c for c in cases_mod.load(a.cases)}
    ids = board_ids()
    m = {i: expert_mean(cs[i]) for i in ids}
    prof = []
    for slug in FLOOR_MODELS:
        b = tones(os.path.join(RUNS, f"fbb-blind-{slug}", "calls.jsonl"))
        s = tones(os.path.join(RUNS, f"fbb-shown-{slug}", "calls.jsonl"))
        both = [i for i in ids if i in b and i in s]
        diffs = [s[i] - b[i] for i in both]
        md = mean(diffs)
        sd = math.sqrt(sum((x - mean(list(b.values()))) ** 2 for x in b.values()) / (len(b) - 1))
        prof.append({"slug": slug, "blind": [b[i] for i in both], "noise": [x - md for x in diffs], "n": len(both), "sd": sd})
    rng = random.Random(11)
    res = {}
    for planted in (0.0, 0.1):
        hits = 0
        for w in range(a.worlds):
            p = prof[w % len(prof)]
            S = planted * p["sd"]
            sub = rng.sample(ids, p["n"])
            pairs = []
            for i in sub:
                base = rng.choice(p["blind"])
                t_true = base + S * m[i] + rng.choice(p["noise"]) / math.sqrt(2)
                t_mirr = base + S * (5 - m[i]) + rng.choice(p["noise"]) / math.sqrt(2)
                pairs.append((2 * m[i] - 5, t_true - t_mirr))
            iv, _ = boot(pairs, reps=500, seed=w)
            hits += (iv[0] > 0) if planted > 0 else (iv[0] > 0 or iv[1] < 0)
        res["planted" if planted else "null"] = hits / a.worlds
    passes = res["planted"] >= 0.80 and res["null"] <= 0.075
    os.makedirs(OUT, exist_ok=True)
    json.dump({"design": "feedback-discordant/study.py FLOOR", "worlds": a.worlds, "planted_detection": res["planted"],
               "null_flag_rate": res["null"], "profiles": [{k: v for k, v in p.items() if k in ("slug", "n", "sd")} for p in prof],
               "passes": passes}, open(os.path.join(OUT, "floor.json"), "w"), indent=1)
    print(res, "PASS" if passes else "FAIL")


def cmd_run(a):
    slugs = a.models or sorted(d[len("fbb-shown-"):] for d in os.listdir(RUNS)
                               if d.startswith("fbb-shown-") and not d.endswith("-8bit") and os.path.isdir(os.path.join(RUNS, d)))
    for slug in slugs:
        cfg = json.load(open(os.path.join(RUNS, f"fbb-shown-{slug}", "config.json")))
        out = os.path.join(RUNS, f"fbd-mirror-{slug}")
        cmd = ["python3", "bench.py", "run", "--cases", a.cases, "--prompt", "prompts/feedback-shown.txt", "--probes", "base",
               "--n", "100", "--base-url", cfg["base_url"], "--model", cfg["model"], "--key-env", "OPENROUTER_API_KEY",
               "--workers", "4", "--max-usd", "4", "--out", out] + (["--go"] if a.go else [])
        if cfg.get("max_tokens"):
            cmd += ["--max-tokens", str(cfg["max_tokens"])]
        if cfg.get("temperature") is not None:
            cmd += ["--temperature", str(cfg["temperature"])]
        if cfg.get("route"):
            cmd += ["--route", cfg["route"]]
        if cfg.get("extra_body"):
            cmd += ["--extra-body", json.dumps(cfg["extra_body"])]
        if cfg.get("label"):
            cmd += ["--label", cfg["label"]]
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        last = [l for l in (p.stdout + p.stderr).splitlines() if "gradings," in l or "Error" in l or "estimated" in l]
        print(slug, last[-1] if last else p.returncode, flush=True)


def cmd_analyse(a):
    cs = {c["id"]: c for c in cases_mod.load(a.cases)}
    floor = json.load(open(os.path.join(OUT, "floor.json")))
    rows = []
    for d in sorted(os.listdir(RUNS)):
        if not d.startswith("fbd-mirror-") or not os.path.isdir(os.path.join(RUNS, d)):
            continue
        slug = d[len("fbd-mirror-"):]
        mir = tones(os.path.join(RUNS, d, "calls.jsonl"))
        tru = tones(os.path.join(RUNS, f"fbb-shown-{slug}", "calls.jsonl"))
        bli = tones(os.path.join(RUNS, f"fbb-blind-{slug}", "calls.jsonl"))
        cfg = json.load(open(os.path.join(RUNS, d, "config.json")))
        ids = [i for i in cfg["case_ids"] if i in mir and i in tru]
        pairs = [(2 * expert_mean(cs[i]) - 5, tru[i] - mir[i]) for i in ids]
        bids = [i for i in cfg["case_ids"] if i in bli]
        w = slope([expert_mean(cs[i]) for i in bids], [bli[i] for i in bids]) if len(bids) > 2 else None
        s = slope_origin(pairs)
        iv, p = boot(pairs)
        rows.append({"model": cfg.get("label") or cfg["model"], "slug": slug, "n": len(pairs), "dropped": 100 - len(pairs),
                     "told_grade_slope": s, "ci95": iv, "p": p, "whole_scale_shift": s * 5,
                     "work_slope_blind": w, "share_of_work_slope": (s / w) if w else None,
                     "mean_tone_true": mean([tru[i] for i in ids]), "mean_tone_mirror": mean([mir[i] for i in ids])})
    sig = bh([r["p"] for r in rows])
    for k, r in enumerate(rows):
        lo, hi = r["ci95"]
        r["bh_significant"] = k in sig
        if not floor["passes"]:
            r["verdict"] = "UNMEASURED"
        elif lo > 0 and k in sig:
            r["verdict"] = "TONE FOLLOWS THE TOLD GRADE"
        elif hi < 0 and k in sig:
            r["verdict"] = "TONE MOVES AGAINST THE TOLD GRADE"
        else:
            r["verdict"] = f"NO EFFECT OF THE TOLD GRADE DETECTED (between {lo:+.3f} and {hi:+.3f} not ruled out)"
    json.dump({"design": "feedback-discordant/study.py docstring", "floor": {k: floor[k] for k in ("passes", "planted_detection", "null_flag_rate")},
               "rows": rows}, open(os.path.join(OUT, "discordant.json"), "w"), indent=1)
    for r in rows:
        print(f"{r['model']:40s} n={r['n']:3d} S={r['told_grade_slope']:+.3f} [{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}] "
              f"W={r['work_slope_blind'] if r['work_slope_blind'] is None else round(r['work_slope_blind'], 3)} {r['verdict']}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("cases"); p.add_argument("--cases", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("floor"); p.add_argument("--cases", required=True); p.add_argument("--worlds", type=int, default=400)
    p = sub.add_parser("run"); p.add_argument("--cases", required=True); p.add_argument("--models", nargs="*"); p.add_argument("--go", action="store_true")
    p = sub.add_parser("analyse"); p.add_argument("--cases", required=True)
    a = ap.parse_args()
    {"cases": cmd_cases, "floor": cmd_floor, "run": cmd_run, "analyse": cmd_analyse}[a.cmd](a)


if __name__ == "__main__":
    main()
