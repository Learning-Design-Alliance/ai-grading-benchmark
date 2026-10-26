#!/usr/bin/env python3
"""A floor for the recording-quality probes. PRE-REGISTERED 2026-10-26, before any call or simulation of this design.

WHY. The speech and video tasks probe recording quality: white noise at 10 dB SNR and a telephone channel for
speech, and a low-resolution copy and the stereo pair's other camera for video. A sound grader should not move
its mark for these, because the experts scored the clean recording. These probes are reported, not ranked,
because nothing yet shows the instrument could see an effect if there were one. The programme's rule is that a
null from an instrument that cannot see a planted effect is not a finding. Two steps, cheapest first.

DESIGN. Two steps, cheapest first; a third (video) is written only if these support it. (Heading added for
scripts/check_study.py before step 2 ran; the design is unchanged.)

STEP 1: SIMULATED FLOOR (`simulate`; no calls). For every existing speech and video run, from its own base and
retest marks:
- A world is the run's cases resampled with replacement.
- A simulated degraded grading of each case is its retest mark, a fresh grading with the run's own noise, plus a
  planted shift of d x the scale width.
- The probe statistic is the board's: the paired mean (degraded - base) with report._mean_iv's bootstrap interval.
  Detection means the interval excludes 0 with the planted sign.
- 200 worlds per run and size: d = 0, -0.05 and -0.10.

VERDICT per run:
  CAN SEE 5%    detection at d = -0.05 in at least 80% of worlds, and a false alarm at d = 0 in at most 7%
  CAN SEE 10%   not the above, but detection at d = -0.10 in at least 80% (false alarm as above)
  CANNOT SEE    otherwise
The probes of a run that CAN SEE 5% or 10% may be read as verdicts at that size. That is the size this
instrument, on these cases, could detect in a grader with this run's own noise.

STEP 2: SPEECH POSITIVE CONTROL (`control`, about $5). The six speech graders, the same 100 recordings (seed 7) and
prompt, with two new probes:
- noise_0db: noise as loud as the speech;
- noise_m10db: noise ten times louder, where the sentence is largely unintelligible.

What a sound grader does is not obvious, so both directions are reported. Pronunciation cannot be judged from
speech that cannot be heard, so the mark should fall, or the grader should give the minimum. A grader whose mark
does not move at -10 dB is marking something other than the audio it was sent.

VERDICT per model, at -10 dB, on the paired mean change (signed, share of the 0-10 scale):
  RESPONDS TO UNINTELLIGIBLE AUDIO   interval below 0
  DOES NOT RESPOND                   interval contains 0, with what it does not rule out
  RAISES THE MARK                    interval above 0
Dose-response, descriptive: 10 dB (from the existing runs), 0 dB and -10 dB.

THE CONTROL PASSES, and the audio-quality probes can be ranked at the size step 1 found, if at least four of the
six graders RESPOND at -10 dB. If fewer do, the graders are not using the audio closely enough for a quality probe
to mean anything, and the probes stay reported, not ranked.

CHANGES:
1. (2026-10-26, after step 1's first run, before any real quality-probe result was read and before any call)
   Step 1's false-alarm rate was 10-40% for half the runs (out/simulate-run1-failed.json). A resampled world
   keeps the run's own observed mean of (retest - base), so d = 0 is not a null world whenever that sample
   mean differs from 0. Now each case's two gradings are swapped at random (a fair coin per case per world)
   before the planted shift, so the null world is exchangeable and centred on 0. Re-run once; sizes and
   verdicts unchanged. The observed base-retest mean shifts are reported beside each run, descriptively.

VIDEO POSITIVE CONTROL: not in this design. It will be written after these two steps, if they support it.

Usage:
    python3 media/floor.py simulate
    python3 media/floor.py control [--go]
    python3 media/floor.py analyse
"""

import argparse
import glob
import json
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import cases as cases_mod  # noqa: E402
import report  # noqa: E402

RUNS = os.environ.get("GBENCH_RUNS", "runs")
OUT = os.path.join(HERE, "out")
SIZES = (0.0, -0.05, -0.10)
WORLDS = 200
CAP = 8.0


def load_run(d):
    cfg = json.load(open(os.path.join(d, "config.json")))
    calls = [json.loads(line) for line in open(os.path.join(d, "calls.jsonl"))]
    return cfg, calls


def scale_of(cfg):
    c = cases_mod.load(cfg["cases"])[0] if os.path.exists(cfg["cases"]) else None
    return (c["scale"][1] - c["scale"][0]) if c else None


def cmd_simulate(a):
    res = {"design": "media/floor.py docstring, step 1", "runs": []}
    for d in sorted(x for x in glob.glob(os.path.join(RUNS, "speech-*")) + glob.glob(os.path.join(RUNS, "video-*"))
                    + glob.glob(os.path.join(RUNS, "video16f-*")) if os.path.isdir(x)):
        if not os.path.exists(os.path.join(d, "calls.jsonl")):
            continue
        cfg, calls = load_run(d)
        w = scale_of(cfg)
        if not w:
            print("no cases file for", d)
            continue
        sc = {}
        for r in calls:
            if r["probe"] in ("base", "retest") and r.get("score") is not None:
                sc.setdefault(r["id"], {})[r["probe"]] = r["score"]
        ids = [i for i, v in sc.items() if len(v) == 2]
        out = {"run": os.path.basename(d), "model": cfg["model"], "task": "speech" if "speech" in d else "video",
               "cases": len(ids), "detection": {},
               "observed_retest_minus_base": (sum(sc[i]["retest"] - sc[i]["base"] for i in ids) / len(ids) / w) if ids else None}
        for dsz in SIZES:
            hits = 0
            for k in range(WORLDS):
                rnd = random.Random(1000 * k + int(abs(dsz) * 100))
                world = [rnd.choice(ids) for _ in ids]
                diffs = []
                for i in world:  # CHANGE 1: a fair coin decides which grading plays the base
                    b, rt = (sc[i]["base"], sc[i]["retest"]) if rnd.random() < 0.5 else (sc[i]["retest"], sc[i]["base"])
                    diffs.append(rt + dsz * w - b)
                iv = report._mean_iv(diffs, seed=k)
                if iv is None:
                    continue
                lo, hi = iv["ci95"]
                hits += (hi < 0) if dsz < 0 else (lo > 0 or hi < 0)
            out["detection"][str(dsz)] = hits / WORLDS
        fa, d5, d10 = out["detection"]["0.0"], out["detection"]["-0.05"], out["detection"]["-0.1"]
        out["verdict"] = ("CAN SEE 5%" if fa <= 0.07 and d5 >= 0.80 else "CAN SEE 10%" if fa <= 0.07 and d10 >= 0.80
                          else "CANNOT SEE")
        res["runs"].append(out)
        print(f"{out['run'][:44]:44s} n {len(ids):3d} | false alarm {fa:.0%} | 5% {d5:.0%} | 10% {d10:.0%} -> {out['verdict']}", flush=True)
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "simulate.json"), "w"), indent=1)


def spent():
    return sum((json.loads(line).get("usage") or {}).get("cost_reported") or 0.0
               for p in glob.glob(os.path.join(RUNS, "speechctl-*", "calls.jsonl")) for line in open(p)
               if not json.loads(line).get("cached"))


def cmd_control(a):
    for d in sorted(x for x in glob.glob(os.path.join(RUNS, "speech-*")) if os.path.isdir(x)):
        cfg, _ = load_run(d)
        left = CAP - spent()
        if a.go and left <= 0.5:
            print("cap reached")
            return
        out = os.path.join(RUNS, "speechctl-" + os.path.basename(d)[len("speech-"):])
        cmd = [sys.executable, "bench.py", "run", "--cases", cfg["cases"], "--prompt", os.path.join("prompts", cfg["prompt"]),
               "--base-url", cfg["base_url"], "--model", cfg["model"], "--key-env", "OPENROUTER_API_KEY", "--n", str(cfg["n"]),
               "--seed", str(cfg["seed"]), "--probes", "base,noise_0db,noise_m10db", "--max-tokens", str(cfg.get("max_tokens") or 4096),
               "--extra-body", json.dumps(cfg.get("extra_body") or {}), "--out", out, "--workers", "6", "--max-usd", str(min(2.5, left))]
        if a.go:
            cmd.append("--go")
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        print(f"{cfg['model'][:34]:34s} | " + " | ".join((r.stdout + r.stderr).strip().splitlines()[-2:])[:180], flush=True)
    print(f"spent ${spent():.2f} of ${CAP:.0f}")


def cmd_analyse(a):
    res = {"design": "media/floor.py docstring, step 2", "models": []}
    for d in sorted(x for x in glob.glob(os.path.join(RUNS, "speechctl-*")) if os.path.isdir(x)):
        if not os.path.exists(os.path.join(d, "calls.jsonl")):
            continue
        cfg, calls = load_run(d)
        w = scale_of(cfg)
        sc = {(r["id"], r["probe"]): r["score"] for r in calls if r.get("score") is not None}
        # the 10 dB step from the original run, against its own base
        orig = os.path.join(RUNS, "speech-" + os.path.basename(d)[len("speechctl-"):])
        _, ocalls = load_run(orig)
        osc = {(r["id"], r["probe"]): r["score"] for r in ocalls if r.get("score") is not None}
        row = {"model": cfg["model"], "steps": {}}
        for name, src, probe in (("10 dB", osc, "noise_10db"), ("0 dB", sc, "noise_0db"), ("-10 dB", sc, "noise_m10db")):
            ids = sorted({i for i, p in src if p == probe and (i, "base") in src})
            diffs = [(src[(i, probe)] - src[(i, "base")]) / w for i in ids]
            iv = report._mean_iv(diffs, seed=7)
            row["steps"][name] = iv
        iv = row["steps"]["-10 dB"]
        lo, hi = iv["ci95"]
        row["verdict"] = ("RESPONDS TO UNINTELLIGIBLE AUDIO" if hi < 0 else "RAISES THE MARK" if lo > 0 else "DOES NOT RESPOND")
        row["not_ruled_out"] = lo if row["verdict"] == "DOES NOT RESPOND" else None
        fails = {p: sum(1 for r in calls if r["probe"] == p and r.get("score") is None) for p in ("base", "noise_0db", "noise_m10db")}
        row["failed"] = fails
        res["models"].append(row)
        s = row["steps"]
        print(f"{cfg['model'][:32]:32s} " + " | ".join(f"{k} {v['estimate']:+.3f} [{v['ci95'][0]:+.3f}, {v['ci95'][1]:+.3f}]" for k, v in s.items())
              + f" -> {row['verdict']} (failed {fails})")
    n = sum(m["verdict"] == "RESPONDS TO UNINTELLIGIBLE AUDIO" for m in res["models"])
    res["passes"] = n >= 4
    print(f"{n} of {len(res['models'])} respond at -10 dB -> control {'PASSES' if res['passes'] else 'FAILS'}")
    json.dump(res, open(os.path.join(OUT, "control.json"), "w"), indent=1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("simulate").set_defaults(fn=cmd_simulate)
    p = sub.add_parser("control"); p.add_argument("--go", action="store_true"); p.set_defaults(fn=cmd_control)
    sub.add_parser("analyse").set_defaults(fn=cmd_analyse)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
