#!/usr/bin/env python3
"""The board's open models, re-run pinned to 8-bit or full-precision hosts. PRE-REGISTERED 2026-10-26, before any
call of this design. Approved by the maintainer (8-bit, rows beside the current ones).

WHY. hosting/ found that the same open model served at 4-bit is far easier to game than at 8-bit (all three
comparisons; forged-override gains 11-51 points of the scale higher at 4-bit), and that the board's DeepSeek V4 Pro
and GLM 5.3 rows were served mostly by 4-bit hosts. The board pins no host, so an open model's row describes it as
whichever hosts answered. These rows show each open model as its makers released it, or at 8-bit.

MODELS. Every board model with weights published and zero-retention hosts at fp8, bf16 or fp16 on OpenRouter:
DeepSeek V4 Pro, V4.1 Flash (10 Sep and 17 Oct), Gemma 3 27B, Gemma 4 26B A4B, Gemma 4 31B, Llama 3.2 3B,
GPT-OSS 20B (released in MXFP4; its 8-bit and bf16 hosts serve it dequantised), Qwen3 235B, GLM 5.3 and GLM 5.3
Flash. Not re-run:
- Phi-4 and Gemma 3 4B: their only zero-retention hosts run bf16, and every board grading came from them
  (DeepInfra, Parasail).
- Ministral 8B: its hosts state no precision.
- Olmo 3.1 32B: run in bf16 on our own GPU.
- Closed models: precision not published.

DESIGN. The board's whole battery, unchanged:
- leaderboard runs on short answers, code and essays;
- maths working (800 cases);
- the feedback board (feedback, blind, shown);
- pushback.

Each model uses its own board settings (max tokens, extra body), with one addition: OpenRouter's provider filter
`quantizations: ["fp8", "bf16", "fp16"]`, on top of the zero-retention pin. Each run is labelled "<model>@8bit"
(`bench.py --label`), so its row sits beside the board's. The board's own rows are unchanged.

MEASURES AND READING. The board's own: every strand, flag and overall score, computed by leaderboard.py exactly as
for the existing rows. For each model, the change from its board row in:
- gaming (worst task);
- QWK per task;
- blank credit;
- pushback;
- overall.

These are descriptive comparisons of two runs. The paired precision test is hosting/'s. After the runs, every
grading's host is checked against OpenRouter's precision labels, and any grading from a host with no 8-bit or
full-precision endpoint for that model is counted and reported.

BUDGET. A cap of $35 across the study (per-run caps from what is left).

Usage:
    python3 precision/run.py run --cases-dir <dir with mohler.jsonl, harmogen-code.jsonl, asap2.jsonl, vtg-cells.jsonl> [--models ...] [--go]
    python3 precision/run.py export --cases-dir <dir>
"""

import argparse
import glob
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = os.environ.get("GBENCH_RUNS", "runs")
MODELS = ["deepseek/deepseek-v4-pro-0813", "deepseek/deepseek-v4.1-flash", "deepseek/deepseek-v4.1-flash-1017",
          "google/gemma-3-27b-it", "google/gemma-4-26b-a4b-it", "google/gemma-4-31b-it", "meta-llama/llama-3.2-3b-instruct",
          "openai/gpt-oss-20b", "qwen/qwen3-235b-a22b-2507", "z-ai/glm-5.3", "z-ai/glm-5.3-flash"]
QUANTS = ["fp8", "bf16", "fp16"]
FILES = {"mohler": "mohler.jsonl", "code": "harmogen-code.jsonl", "asap2": "asap2.jsonl"}
CAP = 35.0


def slug(m):
    return m.replace("/", "_") + "-8bit"


def spent():
    tot = 0.0
    for p in glob.glob(os.path.join(RUNS, "*-8bit", "calls.jsonl")):
        for line in open(p):
            r = json.loads(line)
            if not r.get("cached"):
                tot += (r.get("usage") or {}).get("cost_reported") or (r.get("cost") or 0.0)
    return tot


def settings(model, task):
    s = json.load(open(os.path.join(ROOT, "submissions", model.replace("/", "__"), f"{task}.json")))["settings"]
    extra = json.loads(json.dumps(s.get("extra_body") or {"usage": {"include": True}, "provider": {"zdr": True}}))
    extra["provider"] = dict(extra.get("provider") or {}, quantizations=QUANTS)
    return s.get("max_tokens") or 16384, extra


def bench(model, out, cases, extra_args, max_tokens, extra, go):
    left = CAP - spent()
    if go and left <= 0.5:
        print("cap reached:", out)
        return False
    cmd = [sys.executable, "bench.py", "run", "--cases", cases, "--base-url", "https://openrouter.ai/api/v1", "--model", model,
           "--key-env", "OPENROUTER_API_KEY", "--seed", "7", "--max-tokens", str(max_tokens), "--extra-body", json.dumps(extra),
           "--label", f"{model}@8bit", "--out", out, "--workers", "6", "--max-usd", str(min(8.0, left)), *extra_args]
    if go:
        cmd.append("--go")
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    print(f"{model[:32]:32s} {os.path.basename(out)[:40]:40s} | " + " | ".join((r.stdout + r.stderr).strip().splitlines()[-2:])[:160], flush=True)
    return True


def cmd_run(a):
    env = dict(os.environ, GBENCH_RUNS=RUNS, MOHLER_CASES=os.path.join(a.cases_dir, "mohler.jsonl"))
    for model in a.models or MODELS:
        s = slug(model)
        for task, f in FILES.items():
            mt, extra = settings(model, task)
            bench(model, os.path.join(RUNS, f"lb-{task}-{s}"), os.path.join(a.cases_dir, f),
                  ["--battery", "leaderboard", "--n", "100"], mt, extra, a.go)
        mt, extra = settings(model, "maths")
        bench(model, os.path.join(RUNS, f"maths-{s}"), os.path.join(a.cases_dir, "vtg-cells.jsonl"),
              ["--prompt", "prompts/maths-steps.txt", "--probes", "base", "--n", "800"], mt, extra, a.go)
        if a.go and CAP - spent() <= 0.5:
            print("cap reached before feedback:", model)
            return
        for script, extra_args in (("feedback-board/fb.py", []), ("feedback-board/pushback.py", ["--runs", RUNS])):
            cmd = [sys.executable, script, "run", "--models", s, *extra_args] + (["--go"] if a.go else [])
            r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env)
            print(f"{model[:32]:32s} {os.path.basename(script)} | " + " | ".join((r.stdout + r.stderr).strip().splitlines()[-3:])[:220], flush=True)
    print(f"spent ${spent():.2f} of ${CAP:.0f}")


def cmd_export(a):
    for model in a.models or MODELS:
        s = slug(model)
        out = os.path.join(ROOT, "submissions", model.replace("/", "__") + "@8bit")
        os.makedirs(out, exist_ok=True)
        for task, pre, cases in (("mohler", "lb-mohler", "mohler.jsonl"), ("code", "lb-code", "harmogen-code.jsonl"),
                                 ("asap2", "lb-asap2", "asap2.jsonl"), ("maths", "maths", "vtg-cells.jsonl"),
                                 ("pushback", "push", "mohler.jsonl")):
            run = os.path.join(RUNS, f"{pre}-{s}")
            if not os.path.exists(os.path.join(run, "calls.jsonl")):
                print("missing", run)
                continue
            dest = os.path.join(out, f"{task}.json")
            subprocess.run([sys.executable, "leaderboard.py", "export", run, "--task", task, "--out", dest,
                            "--submitter", "benchmark maintainers"], cwd=ROOT, capture_output=True, text=True)
            v = subprocess.run([sys.executable, "leaderboard.py", "verify", dest, "--cases", os.path.join(a.cases_dir, cases)],
                               cwd=ROOT, capture_output=True, text=True)
            print(model, task, (v.stdout + v.stderr).strip().splitlines()[-1][:120])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for nm, fn in (("run", cmd_run), ("export", cmd_export)):
        p = sub.add_parser(nm)
        p.add_argument("--cases-dir", required=True)
        p.add_argument("--models", nargs="+")
        if nm == "run":
            p.add_argument("--go", action="store_true")
        p.set_defaults(fn=fn)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
