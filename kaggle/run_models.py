"""Run the five Kaggle tasks on more models, within the quota left today. Meant to run every few hours: the daily
quota refills 24 hours after the day's first spend, not at a fixed time, and a run that finds runs in flight stops.

    python3 kaggle/run_models.py            # run what fits, then print what ran, the scores and the quota
    python3 kaggle/run_models.py --dry-run  # print the plan only; starts nothing

It keeps no state of its own: it asks Kaggle which models already have a completed run of each task (the latest
version) and reads each model's cost from its blank-answers run record, so it can run from a fresh checkout. Needs the
Kaggle CLI (`pip install kaggle`) and KAGGLE_API_TOKEN from the environment; it never prints the token.

Order: the models that are also on the leaderboard (LEADERBOARD), then models Kaggle added after 2026-11-06 (any slug
not in KNOWN), one model at a time. A model starts with grader-blank-answers, which measures its cost; each other task
is estimated as that cost times the task's ratio on gemini-3.8-flash (RATIO), and starts only if 1.5 times its estimate
fits in what is left of both the daily and the monthly quota, cheapest first. What does not fit waits for a later day.

No second runs: Kaggle keeps only the latest run of a task on a model, so a re-run replaces a score rather than adding a
sample (tested 2026-11-06 on grader-pushback). A failed run is reported, not retried.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import tempfile

TASKS = ["blank-answers", "pushback", "feedback-told-grade", "agreement", "note-gaming"]
# Cost of each task relative to grader-blank-answers, from gemini-3.8-flash's version-2 run records (2026-11-06).
RATIO = {"blank-answers": 1.0, "pushback": 4.4, "feedback-told-grade": 4.5, "agreement": 6.0, "note-gaming": 18.9}
MARGIN = 1.5
PROBE = 1.00  # assumed cost of a first blank-answers run on a model with no record yet
LEADERBOARD = ["claude-haiku-5-5", "gemma-4-26b-a4b-it", "gemma-4-31b-it", "gemini-3.5-flash-lite", "gpt-5.6-luna",
               "claude-opus-5-5-default", "gpt-6-astra"]
KNOWN = set("""gemini-3.8-flash claude-haiku-4-5-20251001 claude-haiku-5-5 claude-opus-4-5-20251101 claude-opus-4-6-default
claude-opus-4-7-default claude-opus-4-8-default claude-opus-5-default claude-opus-5-5-default claude-sonnet-4-6-default
claude-sonnet-5-default claude-sonnet-5-5-default gemini-2.5-flash gemini-2.5-pro gemini-3-flash-preview
gemini-3.1-flash-lite-preview gemini-3.1-pro-preview gemini-3.5-flash-lite gemini-3.6-flash gemini-4-argon
gemma-4-26b-a4b-it gemma-4-31b-it gpt-5.4-2026-03-05 gpt-5.4-mini-2026-03-17 gpt-5.4-nano-2026-03-17 gpt-5.5-2026-04-23
gpt-5.6-luna gpt-5.6-sol gpt-5.6-terra gpt-6-astra gpt-6-luna gpt-6-sol gpt-6.1-sol gpt-oss-120b grok-4.5-0708 grok-4.6
grok-4.7""".split())  # Kaggle's model list on 2026-11-06
SECRET = re.compile(r"api[_ ]?key|token|secret|bearer|password", re.I)


def kaggle(*args, check=True):
    p = subprocess.run(["kaggle", *args], capture_output=True, text=True)
    out = "\n".join(line for line in (p.stdout + p.stderr).splitlines() if not SECRET.search(line))
    if check and p.returncode:
        sys.exit(f"kaggle {' '.join(args)} failed:\n{out[-800:]}")
    return out


def quota():
    """What is left today: the smaller of the daily and the monthly remaining."""
    left = [float(m) for m in re.findall(r"^(?:Daily|Monthly)\s+\$[\d.]+\s+\$([\d.]+)", kaggle("b", "quota"), re.M)]
    if len(left) != 2:
        sys.exit("could not read the quota")
    return min(left)


def status(task):
    """{model: state} for the task's latest version."""
    out = kaggle("b", "t", "status", f"grader-{task}")
    return dict(re.findall(r"^([a-z0-9][\w.\-]*)\s+(Completed|Running|Queued|Failed|Errored|Cancelled|\w+)\s", out.split("Model", 1)[-1], re.M))


def records(task, tmp):
    """{model: (score, cost in dollars)} from the latest version's run records."""
    d = os.path.join(tmp, task)
    kaggle("b", "t", "download", f"grader-{task}", "-o", d)
    out = {}
    versions = sorted(glob.glob(os.path.join(d, f"grader-{task}", "*")), key=lambda p: int(os.path.basename(p)))
    for f in glob.glob(os.path.join(versions[-1], "*", "*", "*.run.json")) if versions else []:
        r = json.load(open(f))
        cost = sum(int(c["metrics"].get(k, 0)) for c in r["conversations"] if c.get("metrics")
                   for k in ("inputTokensCostNanodollars", "outputTokensCostNanodollars")) / 1e9
        res = r.get("results") or [{}]
        out[f.split(os.sep)[-3]] = (res[0].get("numericResult", {}).get("value"), cost)
    return out


def run(task, model, dry):
    print(f"  start grader-{task} on {model}", flush=True)
    if dry:
        return None
    return subprocess.Popen(["kaggle", "b", "t", "run", f"grader-{task}", "-m", model, "--wait", "--poll-interval", "120"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    available = kaggle("b", "t", "models").split()
    queue = LEADERBOARD + [m for m in re.findall(r"^([a-z0-9][\w.\-]+)\s", kaggle("b", "t", "models"), re.M)
                           if m not in KNOWN and m not in LEADERBOARD and m != "Slug"]
    # The quota does not count runs still in flight, so a second copy of this script would overspend: never overlap.
    inflight = [f"grader-{t} on {m}" for t in TASKS for m, s in status(t).items() if s in ("Running", "Queued")]
    if inflight:
        print("runs still in progress, so nothing started:", *inflight, sep="\n  ")
        print(f"\nquota left: ${quota():.2f}\nFINISHED")
        return
    ran, problems = [], []
    with tempfile.TemporaryDirectory() as tmp:
        for model in queue:
            if model not in available:
                problems.append(f"{model}: not in Kaggle's model list")
                continue
            states = {t: status(t).get(model) for t in TASKS}
            failed = [t for t, s in states.items() if s and s != "Completed"]
            problems += [f"{model}: grader-{t} {states[t]}" for t in failed]
            todo = [t for t in TASKS if states[t] is None]
            if not todo:
                continue
            left = quota()
            if "blank-answers" in todo:  # measure the model's cost first
                if a.dry_run or left < MARGIN * PROBE:
                    print(f"{model}: blank-answers first (needs ${MARGIN * PROBE:.2f}, ${left:.2f} left)")
                    if left < MARGIN * PROBE:
                        continue
                if a.dry_run:
                    continue
                run("blank-answers", model, False).wait()
                ran.append(("blank-answers", model))
                todo.remove("blank-answers")
                left = quota()
            blank = records("blank-answers", tmp).get(model)
            unit = blank[1] if blank and blank[1] > 0 else PROBE
            jobs = []
            for t in sorted(todo, key=RATIO.get):
                need = MARGIN * unit * RATIO[t]
                if need <= left:
                    left -= need
                    jobs.append((t, run(t, model, a.dry_run)))
                else:
                    print(f"{model}: grader-{t} waits (estimate ${unit * RATIO[t]:.2f}, ${left:.2f} left)")
            for t, p in jobs:
                if p:
                    p.wait()
                    ran.append((t, model))
        if ran:
            print("\nscores of the runs started today (reply counts are in `kaggle b t log grader-<task> -m <model>`):")
            for t in TASKS:
                rec = records(t, tmp)
                for tt, m in ran:
                    if tt == t:
                        s, c = rec.get(m, (None, None))
                        print(f"  grader-{t:20s} {m:28s} score {s}  cost ${c if c is None else round(c, 3)}  ({status(t).get(m)})")
    print("\nproblems for a person to look at:", *(problems or ["none"]), sep="\n  ")
    print(f"\nquota left: ${quota():.2f}\nFINISHED")


if __name__ == "__main__":
    main()
