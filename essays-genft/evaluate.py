#!/usr/bin/env python3
"""The battery of essays-genft/study.py (E1-E5, its docstring), for one served model. Runs on the pod, against the vLLM
server on localhost; every arm gets exactly the same commands.

    python3 essays-genft/evaluate.py battery --slug <slug> --served <name> --label <row name> --data <dir> --runs <dir>
        --corpus <asap2.jsonl> --split <genft-split.json> [--route-note <text>]
    python3 essays-genft/evaluate.py fold --slug <slug> --served <name> --label ... --prompt <ASAP 2.0 prompt> ...

The board's settings for Gemma 4 26B A4B (submissions/google__gemma-4-26b-a4b-it): temperature unset, max_tokens 4096.
The key is the server's (CTL_TOKEN in the pod's environment), named, never passed.
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

URL = "http://127.0.0.1:8000/v1"
ROUTE = ("self-hosted: vLLM v0.32.0 on one rented RunPod A100 80GB pod, bf16; bench.py ran on the pod against localhost, "
         "so no request left it; the pod and its disk were deleted after the run, so nothing is retained")
SETTINGS = ["--max-tokens", "4096", "--workers", "16", "--seed", "7", "--key-env", "CTL_TOKEN"]


def sh(cmd):
    print("$", " ".join(cmd[:12]), "...", flush=True)
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    tail = (r.stdout + r.stderr).strip().splitlines()[-4:]
    print("  " + "\n  ".join(tail), flush=True)
    if r.returncode:
        raise SystemExit(f"failed ({r.returncode}): {' '.join(cmd[:6])}")


def bench(a, cases, prompt, out, *extra):
    sh([sys.executable, "bench.py", "run", "--cases", cases, "--prompt", prompt, "--base-url", URL, "--model", a.served,
        "--label", a.label, "--route", ROUTE + (f"; {a.route_note}" if a.route_note else ""), *SETTINGS, *extra,
        "--out", out, "--go"])


def test_file(a, prompt_filter=None):
    import cases as cases_mod
    sp = json.load(open(a.split))
    byid = {c["id"]: c for c in cases_mod.load(a.corpus)}
    keep = [i for i in sp["test_order"] if prompt_filter is None or byid[i]["task"] == prompt_filter]
    import hashlib
    name = "test.jsonl" if prompt_filter is None else f"test-{hashlib.md5(prompt_filter.encode()).hexdigest()[:8]}.jsonl"
    path = os.path.join(os.path.dirname(os.path.abspath(a.split)), name)
    with open(path, "w") as fh:
        for i in keep:
            fh.write(json.dumps(byid[i]) + "\n")
    return path, len(keep)


def cmd_battery(a):
    d, r, s = a.data, a.runs, a.slug
    for task, f in (("mohler", "mohler.jsonl"), ("code", "harmogen-code.jsonl"), ("asap2", "asap2.jsonl")):
        bench(a, os.path.join(d, f), "prompts/default.txt", os.path.join(r, f"lb-{task}-{s}"), "--battery", "leaderboard",
              "--n", "100")
    bench(a, os.path.join(d, "vtg-cells.jsonl"), "prompts/maths-steps.txt", os.path.join(r, f"maths-{s}"), "--probes", "base",
          "--n", "800")
    for kind, p in (("feedback", "feedback.txt"), ("blind", "feedback-blind.txt"), ("shown", "feedback-shown.txt")):
        bench(a, os.path.join(d, "mohler.jsonl"), f"prompts/{p}", os.path.join(r, f"fbb-{kind}-{s}"), "--probes", "base",
              "--n", "100")
    sh([sys.executable, "feedback-board/pushback.py", "run", "--models", s, "--runs", r, "--cases",
        os.path.join(d, "mohler.jsonl"), "--key-env", "CTL_TOKEN", "--workers", "16", "--go"])
    path, n = test_file(a)
    bench(a, path, "prompts/default.txt", os.path.join(r, f"test-{s}"), "--probes", "base", "--n", str(n))
    dirs = [os.path.join(r, x) for x in sorted(os.listdir(r)) if x.endswith(s) and os.path.isdir(os.path.join(r, x))]
    subprocess.run([sys.executable, "scripts/check_runs.py", *dirs], cwd=ROOT)
    print("BATTERY DONE", s, flush=True)


def cmd_fold(a):
    path, n = test_file(a, a.prompt)
    bench(a, path, "prompts/default.txt", os.path.join(a.runs, f"test-{a.slug}"), "--probes", "base", "--n", str(n))
    subprocess.run([sys.executable, "scripts/check_runs.py", os.path.join(a.runs, f"test-{a.slug}")], cwd=ROOT)
    print("FOLD DONE", a.slug, flush=True)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("battery", cmd_battery), ("fold", cmd_fold)):
        p = sub.add_parser(name)
        for k in ("--slug", "--served", "--label", "--data", "--runs", "--corpus", "--split"):
            p.add_argument(k, required=True)
        p.add_argument("--route-note")
        if name == "fold":
            p.add_argument("--prompt", required=True)
        p.set_defaults(fn=fn)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
