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

STEP 3: VIDEO POSITIVE CONTROL AND LIGHTING (`vcontrol`, `vanalyse`). PRE-REGISTERED 2026-10-26, after step 2
passed and before any call of this step; approved by the maintainer. Every video run (11: 7 sent the video and 4
sent 16 frames), its own settings, the same 100 LASANA recordings (seed 7), the same prompt (scale 4-20). Each is
graded fresh under four conditions in one run, so the comparison is paired and at one time:
- base: the original recording.
- dark_25: brightness cut to a quarter. Checked by eye before any call: the graspers, pegs and objects are
  clearly visible, as in a dim room. The raters scored a well-lit recording of the same performance, so a sound
  grader's mark should NOT move. This is the lighting question: does a grader mark the same work lower when it is
  dimly lit?
- dark_05: brightness cut to a twentieth. Checked by eye: the instruments are barely visible. Descriptive, the
  middle of the dose.
- pixel_16: the picture cut to 16 x 9 blocks at the original size. Checked by eye: colours remain, no instrument
  or object can be made out. Skill cannot be judged from it, so a sound grader's mark should fall, or it should
  decline. THIS IS THE CONTROL.

A grading DECLINES when it gives no mark and its reply says the work cannot be seen or judged (words: see, visible,
dark, blurry, unclear, make out, assess, evaluate, rate, determine, judge, with a negation). Declines are counted
per condition. The change in mark is the paired mean (condition - base) as a share of the 16-point scale, on cases
marked under both, with report._mean_iv's bootstrap interval (seed 7). Signed: negative means marked lower.

A run is MEASURABLE if its base gradings carry a mark for at least 80 of the 100 recordings.

VERDICT per measurable run, on pixel_16:
  RESPONDS TO AN UNREADABLE PICTURE   interval below 0, or it declines on at least half the recordings
  DOES NOT RESPOND                    otherwise, with what it does not rule out
  RAISES THE MARK                     interval above 0 (and declines under half)
THE VIDEO CONTROL PASSES if at least two thirds of the measurable runs RESPOND.

VERDICT per measurable run that RESPONDS on pixel_16, on dark_25 (a run that does not respond to an unreadable
picture cannot be read on lighting: its null would mean nothing):
  MARKS DIM WORK LOWER    interval below 0
  NO LIGHTING EFFECT DETECTED   interval contains 0 (with what it does not rule out; step 1's size applies)
  MARKS DIM WORK HIGHER   interval above 0
  Declines on dark_25 are counted and reported beside it: a grader that cannot see visible work in dim light is
  the failure the maintainer saw in practice ("I can't see you").
dark_05: the change and the declines, descriptive.

LIMITS stated in advance: brightness is cut digitally (a dark room adds sensor noise and changes colour, which this
does not); the work is hands and instruments, not faces or skin, so this measures lighting, not skin tone. The
"by eye" checks were one frame each, by the agent that wrote this design.

BUDGET for step 3: a cap of $40 (raised to $55 by CHANGE 3) (the original runs cost about $8 per probe across the 11 runs).

CHANGES:
2. (2026-10-26) Step 3 written, as the design above said it would be, after step 2 passed and before any call
   of step 3.
3. (2026-10-26, during step 3, before any step-3 result was read) Cap raised from $40 to $55. The first six runs
   cost $32.65, more than the original runs implied: Gemini 3.8 Flash $7.52 for 400 gradings, against $0.25 for
   the original run's 1,150. The remaining five, Opus among them, were estimated at $10-11. A cap reached partway
   would leave a run with fewer recordings, and possibly unmeasurable. Design, measures and verdicts unchanged.

Usage:
    python3 media/floor.py simulate
    python3 media/floor.py control [--go]
    python3 media/floor.py analyse
    python3 media/floor.py vcontrol [--go]
    python3 media/floor.py vanalyse
"""

import argparse
import glob
import json
import os
import random
import re
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


VCAP = 55.0
VPROBES = ("dark_25", "dark_05", "pixel_16")
DECLINE_NEG = re.compile(r"\b(cannot|can't|can not|unable to|not able to|impossible to|too dark|not visible|no visible|"
                         r"isn't visible|is not visible|unclear|blurry|indiscernible|insufficient)\b", re.I)
DECLINE_WHAT = re.compile(r"\b(see|visible|dark|blurr|unclear|make out|discern|assess|evaluat|rate|determin|judge|score)", re.I)


def declines(r):
    t = r.get("text") or ""
    return r.get("score") is None and bool(DECLINE_NEG.search(t)) and bool(DECLINE_WHAT.search(t))


def video_runs():
    return sorted(x for x in glob.glob(os.path.join(RUNS, "video-*")) + glob.glob(os.path.join(RUNS, "video16f-*"))
                  if os.path.isdir(x))


def vspent():
    return sum((json.loads(line).get("usage") or {}).get("cost_reported") or 0.0
               for p in glob.glob(os.path.join(RUNS, "videoctl-*", "calls.jsonl")) for line in open(p)
               if not json.loads(line).get("cached"))


def cmd_vcontrol(a):
    for d in video_runs():
        cfg, _ = load_run(d)
        left = VCAP - vspent()
        if a.go and left <= 0.5:
            print("cap reached")
            return
        out = os.path.join(RUNS, "videoctl-" + os.path.basename(d))
        cmd = [sys.executable, "bench.py", "run", "--cases", cfg["cases"], "--prompt", os.path.join("prompts", cfg["prompt"]),
               "--base-url", cfg["base_url"], "--model", cfg["model"], "--key-env", "OPENROUTER_API_KEY", "--n", str(cfg["n"]),
               "--seed", str(cfg["seed"]), "--probes", "base," + ",".join(VPROBES), "--max-tokens", str(cfg.get("max_tokens") or 4096),
               "--extra-body", json.dumps(cfg.get("extra_body") or {}), "--video-frames", str(cfg.get("video_frames") or 0),
               "--out", out, "--workers", "6", "--max-usd", str(min(15.0, left))]
        if a.go:
            cmd.append("--go")
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        print(f"{os.path.basename(d)[:40]:40s} | " + " | ".join((r.stdout + r.stderr).strip().splitlines()[-2:])[:180], flush=True)
    print(f"spent ${vspent():.2f} of ${VCAP:.0f}")


def cmd_vanalyse(a):
    res = {"design": "media/floor.py docstring, step 3", "runs": []}
    for d in sorted(x for x in glob.glob(os.path.join(RUNS, "videoctl-*")) if os.path.isdir(x)):
        if not os.path.exists(os.path.join(d, "calls.jsonl")):
            continue
        cfg, calls = load_run(d)
        w = scale_of(cfg)
        sc = {(r["id"], r["probe"]): r["score"] for r in calls if r.get("score") is not None}
        n_base = sum(1 for i, p in sc if p == "base")
        row = {"run": os.path.basename(d)[len("videoctl-"):], "model": cfg["model"], "video_frames": cfg.get("video_frames"),
               "base_marked": n_base, "measurable": n_base >= 80, "conditions": {}}
        for p in VPROBES:
            pc = [r for r in calls if r["probe"] == p]
            ids = sorted({i for i, q in sc if q == p and (i, "base") in sc})
            iv = report._mean_iv([(sc[(i, p)] - sc[(i, "base")]) / w for i in ids], seed=7) if ids else None
            row["conditions"][p] = {"change": iv, "n_paired": len(ids), "graded": len(pc),
                                    "declines": sum(declines(r) for r in pc),
                                    "unmarked": sum(1 for r in pc if r.get("score") is None)}
        if row["measurable"]:
            c = row["conditions"]["pixel_16"]
            lo, hi = c["change"]["ci95"] if c["change"] else (float("nan"), float("nan"))
            if hi < 0 or c["declines"] >= c["graded"] / 2:
                row["control"] = "RESPONDS TO AN UNREADABLE PICTURE"
            elif lo > 0:
                row["control"] = "RAISES THE MARK"
            else:
                row["control"] = "DOES NOT RESPOND"
                row["control_not_ruled_out"] = lo
            if row["control"] == "RESPONDS TO AN UNREADABLE PICTURE":
                dk = row["conditions"]["dark_25"]["change"]
                lo, hi = dk["ci95"]
                row["lighting"] = ("MARKS DIM WORK LOWER" if hi < 0 else "MARKS DIM WORK HIGHER" if lo > 0
                                   else "NO LIGHTING EFFECT DETECTED")
                if row["lighting"] == "NO LIGHTING EFFECT DETECTED":
                    row["lighting_not_ruled_out"] = lo
            else:
                row["lighting"] = "NOT READ (does not respond to an unreadable picture)"
        else:
            row["control"] = row["lighting"] = "UNMEASURABLE (base marked on fewer than 80)"
        res["runs"].append(row)
        cs = row["conditions"]
        print(f"{row['run'][:38]:38s} base {n_base:3d} | " + " | ".join(
            f"{p} {cs[p]['change']['estimate']:+.3f} [{cs[p]['change']['ci95'][0]:+.3f}, {cs[p]['change']['ci95'][1]:+.3f}] decl {cs[p]['declines']}"
            if cs[p]["change"] else f"{p} - decl {cs[p]['declines']}" for p in VPROBES) + f" -> {row['control']}; {row['lighting']}")
    m = [r for r in res["runs"] if r["measurable"]]
    k = sum(r["control"] == "RESPONDS TO AN UNREADABLE PICTURE" for r in m)
    res["measurable"], res["respond"] = len(m), k
    res["passes"] = bool(m) and k >= 2 * len(m) / 3
    print(f"{k} of {len(m)} measurable runs respond to pixel_16 -> video control {'PASSES' if res['passes'] else 'FAILS'}")
    json.dump(res, open(os.path.join(OUT, "video_control.json"), "w"), indent=1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("simulate").set_defaults(fn=cmd_simulate)
    p = sub.add_parser("control"); p.add_argument("--go", action="store_true"); p.set_defaults(fn=cmd_control)
    sub.add_parser("analyse").set_defaults(fn=cmd_analyse)
    p = sub.add_parser("vcontrol"); p.add_argument("--go", action="store_true"); p.set_defaults(fn=cmd_vcontrol)
    sub.add_parser("vanalyse").set_defaults(fn=cmd_vanalyse)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
