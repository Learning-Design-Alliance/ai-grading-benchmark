#!/usr/bin/env python3
"""Reasoning and repeatability: three checks. PRE-REGISTERED 2026-10-25, before any call of these designs and
before the length signal was computed.

WHY. Two gradings of the same work (the board's consistency strand) say how often a mark changes, not how far
it can wander, and nothing on the board says whether paying for more reasoning buys better marking. A first
look at the leaderboard's own gradings showed that gradings which changed on a second try were the ones the
model reasoned longer about, which suggests reasoning length could flag work to send to a person.

1. REASONING LENGTH AS AN UNCERTAINTY SIGNAL (`signal`; no calls). From the leaderboard submissions, per
   model and task (short answers, code, essays), for models that report reasoning tokens on at least 80% of
   base gradings:
   - AUC of the base grading's reasoning tokens for predicting that the retest gave a different mark;
   - AUC of the same for predicting a large error: |base mark - experts' mean| above a fifth of the scale.
   95% interval by bootstrap over cases (2,000 draws, seed 7).
   VERDICT per model and task, on the error AUC:
     FLAGS ITS OWN ERRORS    interval lies above 0.5
     NO SIGNAL DETECTED      interval contains 0.5 (the upper bound is reported)
     INVERTED                interval lies below 0.5
   A signal is useful in practice only if it is well above chance; AUC >= 0.70 is reported as "usable".
   FLOOR (`signal-floor`, before reading real data): simulated graders whose reasoning length is lognormal and
   whose error probability rises with length (true AUC about 0.70) must read FLAGS in at least 80% of
   worlds at the real case counts; with no relation, in at most 5%.

2. NOISE FLOOR (`noise`). 25 cases per task (the first 25 of the leaderboard's canonical draw), graded 5 times
   each (probes base, retest, retest2-4), fresh calls for every model, at the leaderboard's settings with
   every request pinned to zero-retention endpoints (Claude Fable 5.1 alone runs through the maintainers' own
   key under a recorded retention exception: 30-day safety retention, public corpora). Per model and task:
   - the mean within-case SD of the 5 marks, as a share of the scale;
   - the share of cases whose 5 marks are not all equal;
   - the largest spread (max - min) on any case, as a share of the scale;
   - the mean pairwise QWK among the 5 gradings.
   This is descriptive: it sets the noise against which a probe effect is read. No verdict.

3. REASONING EFFORT (`effort`). Models that accept OpenRouter's `reasoning.effort`: Claude Opus 5.5, Claude
   Haiku 5.5, Claude Fable 5.1, GPT-6 Astra, GPT-5 Mini, GPT-5.6 Luna, GPT-OSS 20B, DeepSeek V4.1 Flash, Gemini
   3.5 Flash Lite, Gemma 4 31B and Gemma 4 26B. Effort "low" and "high", against the leaderboard's own run at
   the model's default as the middle. Short answers (the 100 leaderboard cases) and code (its first 50),
   probes base, retest and injection. Per model, task and level: QWK against the raters; retest QWK; the
   injection gain as a share of the scale; reasoning and output tokens; reported cost.
   The effect of effort is high minus low on each, paired over cases, with a 95% bootstrap interval.
   VERDICT per model and task, on agreement (QWK, high minus low):
     MORE REASONING HELPS     interval lies above 0
     NO DETECTED CHANGE       interval contains 0 (the bounds are reported)
     MORE REASONING HURTS     interval lies below 0
   The default run is shown beside the two levels; it was graded earlier and, for Claude Haiku 5.5, partly
   through another route, so it is not part of the verdict.

BUDGET. A hard cap of $130 across checks 2 and 3, enforced per run with --max-usd. A run cut short by its cap
is reported as incomplete, never filled in.

    python3 reasoning/study.py signal-floor
    python3 reasoning/study.py signal
    python3 reasoning/study.py subsets --cases-dir <dir>
    python3 reasoning/study.py noise --go
    python3 reasoning/study.py effort --go
    python3 reasoning/study.py analyse

Reads the corpora's cases (aggregates out only).
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

RUNS = os.environ.get("GB_RUNS", "runs")
FILES = {"mohler": "mohler.jsonl", "code": "harmogen-code.jsonl", "asap2": "asap2.jsonl"}
OUT = os.path.join(HERE, "out")
FABLE = "anthropic/claude-fable-5.1"
FABLE_EXCEPTION = "own Anthropic key (bring-your-own-key), 30-day safety retention; public corpora only"
EFFORT_MODELS = ["anthropic/claude-opus-5.5", "anthropic/claude-haiku-5.5", FABLE, "openai/gpt-6-astra",
                 "openai/gpt-5-mini", "openai/gpt-5.6-luna", "openai/gpt-oss-20b", "deepseek/deepseek-v4.1-flash",
                 "google/gemini-3.5-flash-lite", "google/gemma-4-31b-it", "google/gemma-4-26b-a4b-it"]
SEED = 7


def slug(m):
    return m.replace("/", "_")


def boot(units, stat, reps=2000, seed=SEED):
    rng = random.Random(seed)
    v = sorted(x for x in (stat([rng.choice(units) for _ in units]) for _ in range(reps)) if x is not None and x == x)
    return [v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]] if v else None


def auc(pos, neg):
    if not pos or not neg:
        return None
    s = 0.0
    for p in pos:
        for n in neg:
            s += 1.0 if p > n else 0.5 if p == n else 0.0
    return s / (len(pos) * len(neg))


def auc_units(units):
    """units: (score, label)"""
    return auc([s for s, l in units if l], [s for s, l in units if not l])


def verdict_signal(iv):
    if iv is None:
        return None
    return "FLAGS ITS OWN ERRORS" if iv[0] > 0.5 else "INVERTED" if iv[1] < 0.5 else "NO SIGNAL DETECTED"


# ------------------------------------------------------------------ 1. signal
def cmd_signal_floor(a):
    res = {}
    for n, name in ((100, "n=100"), (60, "n=60")):
        hits = {"planted": 0, "null": 0}
        for w in range(a.worlds):
            rng = random.Random(w)
            for kind in hits:
                units = []
                for _ in range(n):
                    z = rng.gauss(0, 1)
                    p = 1 / (1 + math.exp(-(-1.2 + (0.9 * z if kind == "planted" else 0))))
                    units.append((math.exp(5 + z), rng.random() < p))
                iv = boot(units, auc_units, reps=300, seed=w)
                hits[kind] += verdict_signal(iv) == "FLAGS ITS OWN ERRORS"
        res[name] = {k: v / a.worlds for k, v in hits.items()}
        res[name]["passes"] = res[name]["planted"] >= 0.8 and res[name]["null"] <= 0.05
        print(name, res[name], flush=True)
    os.makedirs(OUT, exist_ok=True)
    json.dump({"design": "reasoning/study.py signal-floor", "worlds": a.worlds, "result": res}, open(os.path.join(OUT, "signal-floor.json"), "w"), indent=1)


def cmd_signal(a):
    cs_by = {t: {c["id"]: c for c in cases_mod.sample(cases_mod.load(os.path.join(a.cases_dir, f)), lb.N, lb.SEED)}
             for t, f in FILES.items()}
    rows = []
    for path in sorted(glob.glob(os.path.join(ROOT, "submissions", "*", "*.json"))):
        sub = json.load(open(path))
        task = sub["task"]
        if task not in FILES:
            continue
        cs = cs_by[task]
        lo, hi = next(iter(cs.values()))["scale"]
        by = {}
        for c in sub["calls"]:
            by.setdefault(c["id"], {})[c["probe"]] = c
        base = [t["base"] for t in by.values() if "base" in t and t["base"].get("score") is not None]
        rt = [(c.get("usage") or {}).get("reasoning_tokens") for c in base]
        cover = sum(1 for x in rt if x) / max(1, len(base))
        row = {"model": sub["model"], "task": task, "reasoning_reported": cover}
        if cover >= 0.8:
            flip, err = [], []
            for i, t in by.items():
                b, r = t.get("base"), t.get("retest")
                if not b or b.get("score") is None or i not in cs:
                    continue
                x = (b.get("usage") or {}).get("reasoning_tokens") or 0
                if r and r.get("score") is not None:
                    flip.append((x, b["score"] != r["score"]))
                hm = mean(list(cs[i]["human"].values()))
                err.append((x, abs(b["score"] - hm) > 0.2 * (hi - lo)))
            for nm, units in (("retest_change", flip), ("large_error", err)):
                iv = boot(units, auc_units)
                row[nm] = {"auc": auc_units(units), "ci95": iv, "n": len(units), "positives": sum(l for _, l in units)}
            row["verdict"] = verdict_signal(row["large_error"]["ci95"])
            row["usable"] = (row["large_error"]["auc"] or 0) >= 0.70
        rows.append(row)
        if cover >= 0.8:
            e, f = row["large_error"], row["retest_change"]
            print(f"{sub['model'][:30]:30s} {task:6s} error AUC {e['auc']:.2f} {e['ci95'] and [round(x, 2) for x in e['ci95']]} "
                  f"(n {e['n']}, {e['positives']} errors) | change AUC {f['auc'] if f['auc'] is None else round(f['auc'], 2)} -> {row['verdict']}", flush=True)
        else:
            print(f"{sub['model'][:30]:30s} {task:6s} reasoning reported on {cover:.0%}: not analysed", flush=True)
    os.makedirs(OUT, exist_ok=True)
    json.dump({"design": "reasoning/study.py docstring, check 1", "rows": rows}, open(os.path.join(OUT, "signal.json"), "w"), indent=1)


# ------------------------------------------------------------------ runs
def cmd_subsets(a):
    os.makedirs(a.out_dir, exist_ok=True)
    for task, fn in FILES.items():
        canon = cases_mod.sample(cases_mod.load(os.path.join(a.cases_dir, fn)), lb.N, lb.SEED)
        for k in (25, 50, 100):
            with open(os.path.join(a.out_dir, f"{task}-first{k}.jsonl"), "w") as fh:
                for c in canon[:k]:
                    fh.write(json.dumps(c) + "\n")
    print("written to", a.out_dir)


def lb_config(model, task):
    return json.load(open(os.path.join(RUNS, f"lb-{task}-{slug(model)}", "config.json")))


BUDGET = 130.0


def spent():
    tot = 0.0
    for p in glob.glob(os.path.join(RUNS, "noise-*", "calls.jsonl")) + glob.glob(os.path.join(RUNS, "effort-*", "calls.jsonl")):
        for l in open(p):
            tot += (json.loads(l).get("usage") or {}).get("cost_reported") or 0.0
    return tot


def run(model, task, cases, out, probes, extra_reasoning, max_usd, go):
    left = BUDGET - spent()
    if go and left <= 0.5:
        print(f"budget of ${BUDGET:.0f} reached: {model} {task} {os.path.basename(out)} not run", flush=True)
        return
    max_usd = min(max_usd, left)
    cfg = lb_config(model, task)
    extra = json.loads(json.dumps(cfg["extra_body"] or {}))
    if extra_reasoning:
        extra["reasoning"] = extra_reasoning
    cmd = [sys.executable, os.path.join(ROOT, "bench.py"), "run", "--cases", cases, "--base-url", cfg["base_url"],
           "--model", model, "--key-env", "OPENROUTER_API_KEY", "--n", str(sum(1 for _ in open(cases))), "--seed", str(SEED),
           "--probes", ",".join(probes), "--extra-body", json.dumps(extra), "--out", out, "--workers", "6",
           "--max-usd", str(max_usd), "--max-calls", "5000"]
    if cfg.get("max_tokens"):
        cmd += ["--max-tokens", str(cfg["max_tokens"])]
    if model == FABLE:
        cmd += ["--retention-exception", FABLE_EXCEPTION]
    if go:
        cmd.append("--go")
    print(" ".join(os.path.basename(x) if x.startswith("/") else x for x in cmd[:6]), model, task, out.split("/")[-1], flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
    print("   ", " | ".join(tail), flush=True)


def models_on_board():
    return sorted({json.load(open(p))["model"] for p in glob.glob(os.path.join(ROOT, "submissions", "*", "mohler.json"))})


def cmd_noise(a):
    for model in (a.models or models_on_board()):
        for task in FILES:
            run(model, task, os.path.join(a.subsets, f"{task}-first25.jsonl"), os.path.join(RUNS, f"noise-{task}-{slug(model)}"),
                ["base", "retest", "retest2", "retest3", "retest4"], None, a.max_usd, a.go)


def cmd_effort(a):
    for model in (a.models or EFFORT_MODELS):
        for level in ("low", "high"):
            for task, cases in (("mohler", f"{a.subsets}/mohler-first100.jsonl"), ("code", f"{a.subsets}/code-first50.jsonl")):
                run(model, task, cases, os.path.join(RUNS, f"effort-{level}-{task}-{slug(model)}"),
                    ["base", "retest", "injection"], {"effort": level}, a.max_usd, a.go)


# ------------------------------------------------------------------ analyse
def load_calls(d):
    p = os.path.join(d, "calls.jsonl")
    return [json.loads(l) for l in open(p)] if os.path.exists(p) else None


def cmd_analyse(a):
    cs_all = {t: {c["id"]: c for c in cases_mod.load(os.path.join(a.cases_dir, f))} for t, f in FILES.items()}
    res = {"design": "reasoning/study.py docstring, checks 2 and 3", "noise": [], "effort": []}
    for d in sorted(glob.glob(os.path.join(RUNS, "noise-*"))):
        if not os.path.isdir(d):
            continue
        calls = load_calls(d)
        if not calls:
            continue
        cfg = json.load(open(os.path.join(d, "config.json")))
        task = os.path.basename(d).split("-")[1]
        cs = cs_all[task]
        lo, hi = next(iter(cs.values()))["scale"]
        w = hi - lo
        by = {}
        for c in calls:
            if c.get("score") is not None:
                by.setdefault(c["id"], {})[c["probe"]] = c["score"]
        full = {i: v for i, v in by.items() if len(v) == 5}
        sds, spread, varied = [], [], 0
        for v in full.values():
            xs = list(v.values())
            m = mean(xs)
            sds.append(math.sqrt(sum((x - m) ** 2 for x in xs) / 4) / w)
            spread.append((max(xs) - min(xs)) / w)
            varied += len(set(xs)) > 1
        probes = ["base", "retest", "retest2", "retest3", "retest4"]
        pq = []
        for i in range(5):
            for j in range(i + 1, 5):
                pairs = [(round(v[probes[i]]), round(v[probes[j]])) for v in full.values()]
                if pairs:
                    pq.append(qwk([x for x, _ in pairs], [y for _, y in pairs], lo, hi))
        res["noise"].append({"model": cfg["model"], "task": task, "cases_complete": len(full), "cases": cfg["n"],
                             "mean_sd_share": mean(sds) if sds else None, "share_varied": varied / len(full) if full else None,
                             "max_spread_share": max(spread) if spread else None, "pairwise_qwk": mean(pq) if pq else None,
                             "failed": sum(1 for c in calls if c.get("score") is None),
                             "spend": sum((c.get("usage") or {}).get("cost_reported") or 0 for c in calls)})
    for model in EFFORT_MODELS:
        for task in ("mohler", "code"):
            cs = cs_all[task]
            lo, hi = next(iter(cs.values()))["scale"]
            w = hi - lo
            levels = {}
            for level in ("low", "default", "high"):
                d = os.path.join(RUNS, f"lb-{task}-{slug(model)}" if level == "default" else f"effort-{level}-{task}-{slug(model)}")
                calls = load_calls(d)
                if calls is None:
                    continue
                by = {}
                for c in calls:
                    by.setdefault(c["id"], {})[c["probe"]] = c
                levels[level] = by
            if "low" not in levels or "high" not in levels:
                continue
            ids = sorted(set(levels["low"]) & set(levels["high"]))
            hm = {i: mean(list(cs[i]["human"].values())) for i in ids}

            def stats(by, ids_):
                g = [(round(hm[i]), round(by[i]["base"]["score"])) for i in ids_ if i in by and by[i].get("base", {}).get("score") is not None]
                rt = [(round(by[i]["base"]["score"]), round(by[i]["retest"]["score"])) for i in ids_
                      if i in by and by[i].get("base", {}).get("score") is not None and by[i].get("retest", {}).get("score") is not None]
                inj = [(by[i]["injection"]["score"] - by[i]["base"]["score"]) / w for i in ids_
                       if i in by and by[i].get("base", {}).get("score") is not None and by[i].get("injection", {}).get("score") is not None]
                toks = [((by[i]["base"].get("usage") or {}).get("reasoning_tokens") or 0) for i in ids_ if i in by and "base" in by[i]]
                cost = sum(((c.get("usage") or {}).get("cost_reported") or 0) for i in ids_ if i in by for c in by[i].values())
                return {"qwk": qwk([x for x, _ in g], [y for _, y in g], lo, hi) if len(g) > 5 else None,
                        "retest_qwk": qwk([x for x, _ in rt], [y for _, y in rt], lo, hi) if len(rt) > 5 else None,
                        "injection_share": mean(inj) if inj else None, "reasoning_tokens_median": sorted(toks)[len(toks) // 2] if toks else None,
                        "cost": cost, "graded": len(g)}
            row = {"model": model, "task": task, "cases": len(ids)}
            for level, by in levels.items():
                row[level] = stats(by, ids)
            both = [i for i in ids if levels["low"].get(i, {}).get("base", {}).get("score") is not None
                    and levels["high"].get(i, {}).get("base", {}).get("score") is not None]
            dq = lambda u: (lambda a_, b_: None if a_ is None or b_ is None else b_ - a_)(
                qwk([round(hm[i]) for i in u], [round(levels["low"][i]["base"]["score"]) for i in u], lo, hi) if len(u) > 5 else None,
                qwk([round(hm[i]) for i in u], [round(levels["high"][i]["base"]["score"]) for i in u], lo, hi) if len(u) > 5 else None)
            iv = boot(both, dq)
            row["agreement_high_minus_low"] = {"estimate": dq(both), "ci95": iv}
            row["verdict"] = None if iv is None else ("MORE REASONING HELPS" if iv[0] > 0 else "MORE REASONING HURTS" if iv[1] < 0 else "NO DETECTED CHANGE")
            res["effort"].append(row)
            f = lambda x: "—" if x is None else f"{x:+.3f}"
            print(f"{model[:30]:30s} {task:6s} QWK low {row['low']['qwk']} high {row['high']['qwk']} diff {f(row['agreement_high_minus_low']['estimate'])} "
                  f"{iv and [round(x, 3) for x in iv]} -> {row['verdict']}", flush=True)
    for r in res["noise"]:
        print(f"noise {r['model'][:30]:30s} {r['task']:6s} sd {r['mean_sd_share']} varied {r['share_varied']} pairwise {r['pairwise_qwk']}")
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "runs.json"), "w"), indent=1)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("signal-floor"); p.add_argument("--worlds", type=int, default=200)
    p = sub.add_parser("signal"); p.add_argument("--cases-dir", required=True)
    p = sub.add_parser("subsets"); p.add_argument("--cases-dir", required=True); p.add_argument("--out-dir", required=True)
    for nm in ("noise", "effort"):
        p = sub.add_parser(nm); p.add_argument("--subsets", required=True); p.add_argument("--models", nargs="+")
        p.add_argument("--max-usd", type=float, default=8.0); p.add_argument("--go", action="store_true")
    p = sub.add_parser("analyse"); p.add_argument("--cases-dir", required=True)
    a = ap.parse_args()
    {"signal-floor": cmd_signal_floor, "signal": cmd_signal, "subsets": cmd_subsets, "noise": cmd_noise,
     "effort": cmd_effort, "analyse": cmd_analyse}[a.cmd](a)


if __name__ == "__main__":
    main()
