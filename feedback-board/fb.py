#!/usr/bin/env python3
"""
Feedback on the leaderboard: every model's feedback scored with the two measures that passed validation.

PRE-REGISTERED 2026-10-24, before any call of this design.

WHY THESE TWO. feedback-validity/ tested the benchmark's word-rule measures and Learning Commons' evaluators
against trained annotators on MRBench. Two passed: the tone measure (feedback.tone, AUC 0.669) and Learning
Commons' Withholding Answers (AUC 0.804, kappa 0.58 against the annotators' 0.65-0.71; out of its ELA scope).
Only validated measures become leaderboard columns; the others stay descriptive.

CASES. The leaderboard's 100 Mohler short answers (cases.sample, n = 100, seed 7): the same cases as the
leaderboard rows, so a model's feedback columns sit beside its marking columns.

RUNS, per model (bench.py, base probe only, the model's leaderboard settings):
- prompts/feedback.txt: a mark and feedback to the student;
- prompts/feedback-blind.txt and prompts/feedback-shown.txt: feedback only, with the teacher's mark hidden or
  shown (the mark shown is the experts' mean, as prompting.py fills {mark}).

MEASURES, per model:
- HALO = corr(tone, expert mark | mark shown) - corr(tone, expert mark | mark hidden), bootstrap over cases
  (feedback.halo). Positive = feedback follows the mark it is told beyond what the work shows. Reported on
  the English-feedback cases; tone is validated on tutoring text, and its transfer to short-answer feedback
  is stated wherever it is shown.
- GIVES AWAY THE ANSWER = the share of the model's feedback (prompts/feedback.txt) on answers the experts did
  NOT give full marks (expert mean below 5) that Learning Commons' Withholding Answers scores 0 ("does the
  work for the student"). Called exactly as feedback-validity/lc_mrbench.py does (their prompt, schema,
  GPT-5.4 at T = 1, zero retention), with student_text = the question and the student's answer, and
  feedback_text = the model's feedback. 95% interval by bootstrap over answers. The evaluator over-flags
  (specificity 0.985, sensitivity 0.62 on MRBench), so the share is an upper estimate; models are compared
  with each other under the same evaluator, not against zero.

No verdict strings: these are leaderboard columns, signed and with intervals, like the marking columns.
Failures are reported per model.

    python3 fb.py run --models <slug> ... --go
    python3 fb.py analyse --out out/feedback-board.json

CHANGES: none yet.
"""

import argparse
import json
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "feedback-validity"))

RUNS = os.environ.get("GBENCH_RUNS", "runs")
CASES = os.environ.get("MOHLER_CASES", "data/mohler/mohler.jsonl")
PROMPTS = {"feedback": "prompts/feedback.txt", "blind": "prompts/feedback-blind.txt", "shown": "prompts/feedback-shown.txt"}


def leaderboard_config(slug):
    return json.load(open(os.path.join(RUNS, f"lb-mohler-{slug}", "config.json")))


def cmd_run(a):
    for slug in a.models:
        cfg = leaderboard_config(slug)
        for kind, prompt in PROMPTS.items():
            out = os.path.join(RUNS, f"fbb-{kind}-{slug}")
            cmd = ["python3", "bench.py", "run", "--cases", CASES, "--prompt", prompt, "--probes", "base", "--n", "100",
                   "--base-url", cfg["base_url"], "--model", cfg["model"], "--key-env", "OPENROUTER_API_KEY", "--workers", "4",
                   "--max-usd", "4", "--out", out] + (["--go"] if a.go else [])
            if cfg.get("max_tokens"):
                cmd += ["--max-tokens", str(cfg["max_tokens"])]
            if cfg.get("temperature") is not None:
                cmd += ["--temperature", str(cfg["temperature"])]
            if cfg.get("extra_body"):
                cmd += ["--extra-body", json.dumps(cfg["extra_body"])]
            p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            last = [l for l in (p.stdout + p.stderr).splitlines() if "gradings," in l or "Error" in l or "estimated" in l]
            print(slug, kind, last[-1] if last else p.returncode, flush=True)


def lc_calls(slug, cases_by_id, go):
    """Withholding Answers on the model's feedback for answers below full marks; cached."""
    import lc_mrbench as L
    from client import OpenAICompatible
    from feedback import feedback_text
    calls = [json.loads(l) for l in open(os.path.join(RUNS, f"fbb-feedback-{slug}", "calls.jsonl"))]
    cl = OpenAICompatible("https://openrouter.ai/api/v1", L.MODEL, "OPENROUTER_API_KEY", os.path.join(RUNS, "fbb-lc", ".cache"),
                          temperature=1, extra={"usage": {"include": True}, "provider": {"zdr": True}})
    out = []
    for r in calls:
        c = cases_by_id[r["id"]]
        if sum(c["human"].values()) / len(c["human"]) >= 5:
            continue
        text, _ = feedback_text(r.get("text"))
        if not text:
            out.append({"id": r["id"], "score": None, "why": "no feedback"})
            continue
        row = {"history": f"Question: {c['question']}\nStudent answer: {c['response']}", "text": text}
        msgs = L.messages("WITHHOLD", row)
        if not go and not os.path.exists(os.path.join(RUNS, "fbb-lc", ".cache")):
            continue
        rec = cl.call(msgs, tag="WITHHOLD|fbb", extra={"response_format": L.schema("WITHHOLD")}, cached_only=not go)
        sc = L.parse(rec["text"]) if rec["error"] is None else None
        out.append({"id": r["id"], "score": sc, "cost": (rec.get("usage") or {}).get("cost_reported")})
    return out


def cmd_analyse(a):
    import cases as cases_mod
    import feedback as fb
    cs = cases_mod.load(CASES)
    by_id = {c["id"]: c for c in cs}
    res = {"design": "fb.py docstring", "models": {}}
    slugs = sorted({d.split("fbb-feedback-", 1)[1] for d in os.listdir(RUNS) if d.startswith("fbb-feedback-")})
    for slug in slugs:
        paths = {k: os.path.join(RUNS, f"fbb-{k}-{slug}", "calls.jsonl") for k in PROMPTS}
        if not all(os.path.exists(p) for p in paths.values()):
            continue
        calls = {k: [json.loads(l) for l in open(p)] for k, p in paths.items()}
        model = json.load(open(os.path.join(RUNS, f"fbb-feedback-{slug}", "config.json")))["model"]
        h = fb.halo(cs, calls["blind"], calls["shown"])
        lc = lc_calls(slug, by_id, a.go)
        scored = [x for x in lc if x["score"] is not None]
        give = [1 - x["score"] for x in scored]
        rng = random.Random(7)
        draws = sorted(sum(rng.choice(give) for _ in give) / len(give) for _ in range(2000)) if give else []
        res["models"][model] = {
            "halo": h,
            "gives_away": {"share": sum(give) / len(give) if give else None, "ci95": [draws[50], draws[1949]] if draws else None,
                           "n": len(give), "unscored": len(lc) - len(scored),
                           "evaluator_cost_usd": sum((x.get("cost") or 0) for x in scored)},
            "feedback_measures_descriptive": fb.measure(cs, calls["feedback"]),
        }
        g = res["models"][model]["gives_away"]
        print(model, "halo", None if not h else f"{h['halo']:+.2f} [{h['ci95'][0]:+.2f}, {h['ci95'][1]:+.2f}]",
              "gives away", None if g["share"] is None else f"{100 * g['share']:.0f}% of {g['n']}", flush=True)
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run"); p.add_argument("--models", nargs="+", required=True); p.add_argument("--go", action="store_true")
    p = sub.add_parser("analyse"); p.add_argument("--out", default=os.path.join(HERE, "out", "feedback-board.json"))
    p.add_argument("--go", action="store_true", help="call the evaluator for feedback not yet scored")
    a = ap.parse_args()
    {"run": cmd_run, "analyse": cmd_analyse}[a.cmd](a)


if __name__ == "__main__":
    main()
