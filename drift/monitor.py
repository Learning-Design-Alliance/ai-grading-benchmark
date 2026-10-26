#!/usr/bin/env python3
"""Monthly drift watch for every model on the board. PRE-REGISTERED 2026-10-26, before the first (baseline) run.

WHY. On 2026-10-25 the board found, by chance, that DeepSeek's 17 October "minor update" of V4.1 Flash marks code
about 2% of the scale higher, under a model name that did not change on its own API. Nothing else on the board
would have noticed. This runs the same small check every month, so a silent change is seen within a month.

DESIGN.
- Models: every model on the board with a zero-retention route, called by the name a school would use (so an
  alias that moves to a new snapshot is caught). Claude Fable 5.1 (no zero-retention route) and Olmo 3.1 32B
  (no hosted zero-retention route) are left out.
- Battery: bench.py's anchor battery on short answers, code and essays: 30 fixed cases per task, stratified on
  the human mark, each graded three times (base, retest, retest2). Default prompt, the board's settings per
  model (taken from its leaderboard run config).
- What is kept: marks only, per case and grading, with the hosts that served them, in drift/out/<date>/<model>.json.
  No text, so nothing of the student work is committed.
- Baseline: the first month a model is run.

MEASURE per model and task, against the baseline: the mean over cases of (this month's mean of three marks minus
the baseline's mean of three marks), as a share of the scale, with a 95% bootstrap interval over cases (2,000
draws, seed 7). Averaging three gradings per case divides the retest noise. Signed: positive = marks went up.

VERDICT per model and task (CHANGE 1):
  DRIFT        the interval excludes 0; the shift is reported, and marked "material" when it is at least 2% of
               the scale
  NO DRIFT DETECTED  otherwise, with the largest shift the interval does not rule out
A host mix that changed between the two months is reported beside any DRIFT, since a change of host can move
marks too (hosting/study.py tests whether precision does).

FLOOR (run with every analysis, no calls): on each task's baseline marks, add a planted shift of 2% of the scale
to every case and check the measure detects it in at least 80% of 200 resampled draws (each draw resamples the
three gradings per case from the baseline's own spread). If the floor fails for a task, its verdicts read
UNDERPOWERED.

CHANGES:
1. (2026-10-26, after the baseline month and before any comparison) The first floor FAILED (detection 49-56%):
   the verdict needed the shift to be at least 2% as well as an interval excluding 0, so a true 2% shift was
   called only when its estimate happened to land above 2%, about half the time. DRIFT now needs only the
   interval to exclude 0, and 2% marks a material shift. On the board's own base-and-retest marks, this design
   detects a planted 2% shift in 88-94% of draws, with 4-9% false alarms (an estimate run before the change;
   the floor below is re-run with the new rule). The baseline is unchanged.
   RESULT: the floor still FAILED, at 68-75% (the in-script floor resamples each case's own three gradings).
2. (2026-10-26, before any comparison) More cases, one grading each, at about the same cost: the battery is now
   the board's own 100 cases per task (seed 7, base probe, once), 300 calls a model against 270. The noise model
   for the floor is the board's own two gradings (base and retest) of those same 100 cases, from submissions/,
   and the floor plants 2% on those, 200 draws. The 30-case anchor month is kept as drift/out/2026-10-26-anchor/
   and a new baseline month is run with this battery. Measure, verdicts and material threshold as in CHANGE 1.

COST. About $13-15 a month (GPT-6 Astra alone about $7), cap $20 a run; across the board at current prices; a cap of $15 a run (--max-usd per model, from what
is left).

Usage:
    python3 drift/monitor.py run --cases-dir <dir> [--models ...] [--go]      # this month's marks
    python3 drift/monitor.py analyse [--cases-dir <dir>]                       # compare every month to baseline
"""

import argparse
import datetime
import glob
import json
import os
import random
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from metrics import mean  # noqa: E402

OUT = os.path.join(ROOT, "drift", "out")
FILES = {"mohler": "mohler.jsonl", "code": "harmogen-code.jsonl", "asap2": "asap2.jsonl"}
PROBES = ("base",)  # CHANGE 2: one grading of each of the board's 100 cases
EXCLUDE = {"anthropic/claude-fable-5.1", "allenai/olmo-3.1-32b-instruct"}
BASE_URL = "https://openrouter.ai/api/v1"
CAP = 20.0
SHIFT, SEED, REPS = 0.02, 7, 2000
# The board's settings per model, so a fresh session without the board's run folders uses the same requests.
EXTRA = {"usage": {"include": True}, "provider": {"zdr": True}}


def slug(m):
    return m.replace("/", "_")


def board_models():
    return sorted({json.load(open(p))["model"] for p in glob.glob(os.path.join(ROOT, "submissions", "*", "mohler.json"))}
                  - EXCLUDE)


def settings(model, task):
    """max_tokens and extra body from the model's own leaderboard submission, so the check asks as the board did."""
    p = os.path.join(ROOT, "submissions", model.replace("/", "__"), f"{task}.json")
    s = json.load(open(p)).get("settings", {}) if os.path.exists(p) else {}
    return s.get("max_tokens") or 16384, s.get("extra_body") or EXTRA


def cmd_run(a):
    date = a.date or datetime.date.today().isoformat()
    os.makedirs(os.path.join(OUT, date), exist_ok=True)
    spent = 0.0
    for model in a.models or board_models():
        dest = os.path.join(OUT, date, slug(model) + ".json")
        if os.path.exists(dest) and not a.force:
            print(f"{model}: already run for {date}")
            continue
        rec = {"model": model, "date": date, "battery": "anchor", "tasks": {}}
        for task, fn in FILES.items():
            if a.go and spent >= CAP:
                print(f"cap of ${CAP:.0f} reached; {model} {task} not run")
                break
            max_tokens, extra = settings(model, task)
            with tempfile.TemporaryDirectory() as d:
                cmd = [sys.executable, os.path.join(ROOT, "bench.py"), "run", "--cases", os.path.join(a.cases_dir, fn),
                       "--n", "100", "--seed", "7", "--probes", "base", "--base-url", BASE_URL, "--model", model, "--key-env", "OPENROUTER_API_KEY",
                       "--max-tokens", str(max_tokens), "--extra-body", json.dumps(extra), "--out", d,
                       "--workers", "6", "--max-usd", str(max(0.5, min(3.0, CAP - spent)))]
                if a.go:
                    cmd.append("--go")
                r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
                p = os.path.join(d, "calls.jsonl")
                if not a.go or not os.path.exists(p):
                    print(f"{model} {task}: " + (r.stdout + r.stderr).strip().splitlines()[-1][:160])
                    continue
                calls = [json.loads(line) for line in open(p)]
            spent += sum((c.get("usage") or {}).get("cost_reported") or 0 for c in calls if not c.get("cached"))
            marks = {}
            for c in calls:
                marks.setdefault(c["id"], {})[c["probe"]] = c.get("score")
            hosts = {}
            for c in calls:
                h = str(c.get("provider"))  # None when a grading failed before any host answered
                hosts[h] = hosts.get(h, 0) + 1
            rec["tasks"][task] = {"marks": marks, "hosts": hosts,
                                  "served_models": sorted({str(c.get("served_model")) for c in calls if c.get("served_model")}),
                                  "failed": sum(1 for c in calls if c.get("score") is None)}
            print(f"{model} {task}: {len(calls)} gradings, {rec['tasks'][task]['failed']} without a mark", flush=True)
        if a.go and rec["tasks"]:
            with open(dest + ".tmp", "w") as fh:  # atomic: a crash never leaves a half-written month
                json.dump(rec, fh, indent=1, sort_keys=True)
            os.replace(dest + ".tmp", dest)
    print(f"spent ${spent:.2f} (cap ${CAP:.0f})")


def per_case(task_rec):
    out = {}
    for i, m in task_rec["marks"].items():
        xs = [m[p] for p in PROBES if m.get(p) is not None]
        if xs:
            out[i] = xs
    return out


def shift_iv(a, b, width, seed=SEED):
    ids = [i for i in a if i in b]
    d = [(mean(b[i]) - mean(a[i])) / width for i in ids]
    rnd = random.Random(seed)
    vals = sorted(mean([rnd.choice(d) for _ in d]) for _ in range(REPS))
    return {"estimate": mean(d), "ci95": [vals[int(0.025 * REPS)], vals[int(0.975 * REPS) - 1]], "n": len(ids)}


def board_noise(model, task):
    """CHANGE 2: each case's two board gradings (base, retest) for the floor's noise model."""
    p = os.path.join(ROOT, "submissions", model.replace("/", "__"), f"{task}.json")
    if not os.path.exists(p):
        return None
    sc = {}
    for r in json.load(open(p))["calls"]:
        if r["probe"] in ("base", "retest") and r.get("score") is not None:
            sc.setdefault(r["id"], []).append(r["score"])
    return {i: v for i, v in sc.items() if len(v) == 2}


def floor(base, width, draws=200):
    hits = 0
    ids = list(base)
    for k in range(draws):
        rnd = random.Random(1000 + k)
        a = {i: [rnd.choice(base[i])] for i in ids}
        b = {i: [rnd.choice(base[i]) + SHIFT * width] for i in ids}
        global REPS
        keep, REPS = REPS, 400
        iv = shift_iv(a, b, width, seed=k)
        REPS = keep
        hits += iv["ci95"][0] > 0  # CHANGE 1
    return hits / draws


def scale_of(cases_dir, task):
    if not cases_dir:
        return None
    import cases as cases_mod
    c = cases_mod.load(os.path.join(cases_dir, FILES[task]))[0]
    return c["scale"][1] - c["scale"][0]


def cmd_analyse(a):
    import re
    months = sorted(d for d in os.listdir(OUT) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d)
                    and os.path.isdir(os.path.join(OUT, d))) if os.path.isdir(OUT) else []  # CHANGE 2: dated folders only
    widths = {t: scale_of(a.cases_dir, t) or {"mohler": 5, "code": 90, "asap2": 5}[t] for t in FILES}
    res = {"design": "drift/monitor.py docstring", "months": months, "floor": {}, "rows": []}
    if not months:
        print("no months yet")
        return
    recs = {}
    for m in months:
        for p in glob.glob(os.path.join(OUT, m, "*.json")):
            r = json.load(open(p))
            recs.setdefault(r["model"], []).append(r)
    first = {model: sorted(rs, key=lambda r: r["date"])[0] for model, rs in recs.items()}
    for t in FILES:
        fl = [floor(board_noise(m, t), widths[t]) for m in sorted(first)[:8] if board_noise(m, t)]
        res["floor"][t] = {"detection": mean(fl) if fl else None, "passes": bool(fl) and mean(fl) >= 0.80}
    for model, rs in sorted(recs.items()):
        rs = sorted(rs, key=lambda r: r["date"])
        for r in rs[1:]:
            for t in FILES:
                if t not in r["tasks"] or t not in rs[0]["tasks"]:
                    continue
                iv = shift_iv(per_case(rs[0]["tasks"][t]), per_case(r["tasks"][t]), widths[t])
                moved = iv["ci95"][0] > 0 or iv["ci95"][1] < 0  # CHANGE 1
                v = ("UNDERPOWERED" if not res["floor"][t]["passes"] else "DRIFT" if moved else "NO DRIFT DETECTED")
                hosts_changed = set(rs[0]["tasks"][t]["hosts"]) != set(r["tasks"][t]["hosts"])
                served_changed = rs[0]["tasks"][t]["served_models"] != r["tasks"][t]["served_models"]
                res["rows"].append({"model": model, "task": t, "baseline": rs[0]["date"], "date": r["date"], **iv,
                                    "material": abs(iv["estimate"]) >= SHIFT,
                                    "verdict": v, "hosts_changed": hosts_changed, "served_model_changed": served_changed})
                if v == "DRIFT" or served_changed:
                    print(f"{model} {t} {rs[0]['date']} -> {r['date']}: {iv['estimate']:+.3f} of the scale "
                          f"[{iv['ci95'][0]:+.3f}, {iv['ci95'][1]:+.3f}] -> {v}"
                          + ("; served model changed" if served_changed else "") + ("; hosts changed" if hosts_changed else ""))
    n_drift = sum(r["verdict"] == "DRIFT" for r in res["rows"])
    print(f"floor: " + ", ".join(f"{t} {res['floor'][t]['detection'] or 0:.0%}" for t in FILES)
          + f" | {len(res['rows'])} comparisons, {n_drift} DRIFT")
    json.dump(res, open(os.path.join(OUT, "drift.json"), "w"), indent=1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--cases-dir", required=True)
    r.add_argument("--models", nargs="+")
    r.add_argument("--date")
    r.add_argument("--force", action="store_true")
    r.add_argument("--go", action="store_true")
    r.set_defaults(fn=cmd_run)
    an = sub.add_parser("analyse")
    an.add_argument("--cases-dir")
    an.set_defaults(fn=cmd_analyse)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
