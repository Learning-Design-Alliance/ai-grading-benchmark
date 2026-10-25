#!/usr/bin/env python3
"""Measured GPU energy per grading for the open-weight models on the board. PRE-REGISTERED 2026-10-25, before any
measured call.

WHY. docs/ENERGY.md estimates a grading's energy from a per-token model fitted to Jegham et al. 2025 (Table 4),
which infers energy from API speed and assumed hardware. No one has measured it for grading. The open models on
the board can be run on a GPU we rent, so their energy can be read off the GPU instead. The measurements sit
beside the estimates; they never replace them.

MODELS. The eight open-weight models on the board: Gemma 3 4B and 27B, Gemma 4 26B A4B and 31B, Llama 3.2 3B,
Phi-4, Ministral 8B (2512) and GPT-OSS 20B, plus Olmo 3.1 32B Instruct, whose measured runs are also its
leaderboard runs (docs/MODELS.md). Weights from Hugging Face at the revisions in MODELS below. Gemma 3 and Llama
3.2 are gated on Hugging Face and this environment has no Hugging Face token, so their ungated unsloth copies are
used. Their hashes cannot be checked against the gated originals, which hide them. The marks are compared with
the board's instead (descriptive, below).

HARDWARE AND SERVING. One NVIDIA A100 80GB PCIe on RunPod (community cloud), the cheapest GPU that holds every
model unquantised, so every figure comes from the same hardware. vLLM v0.32.0 (the vllm/vllm-openai:v0.32.0
image), bf16 weights except GPT-OSS's native MXFP4, max model length 16,384, its default scheduler and
prefix caching (as anyone would serve it). Olmo's chat template fails vLLM 0.32's start-up check (it applies
`tojson` to `tools`, which that check leaves undefined), so it is served with the same template preceded by
`{%- set tools = tools if tools is defined else none -%}`; real requests pass tools = none, and the two templates
were checked to render identical prompts. The first pod's host restarted the container five times, so Olmo
ran on a second pod with the same GPU model (secure cloud). gpu/controller.py on the pod. bench.py runs on the pod itself
against localhost, so the network does not pace the GPU.

RUNS, per model (`measure`, on the pod):
1. idle: 60 s with the model loaded and no requests;
2. the leaderboard battery (bench.py --battery leaderboard, prompts/default.txt, the canonical 100 cases, seed 7,
   max_tokens 4096, temperature unset, as on the board), short answers (mohler), essays (asap2) and code, one task
   after another, at 16 concurrent requests (`--workers 16`: a school or a vendor marking a batch);
3. idle again: 60 s;
4. SENSITIVITY: one request at a time (`--workers 1`), the base probe only, 30 cases drawn with seed 8, short
   answers and essays (code has too few cases outside the canonical draw). This is how the AI Energy Score
   measures, and it bounds the figure from above.

MEASUREMENT. The GPU's own cumulative energy counter (NVML nvmlDeviceGetTotalEnergyConsumption, mJ), read every
1 s (CHANGE 1) by the driver on the pod together with the count of gradings completed (bench.py's cache: one file per
completed reply). IDLE POWER = the mean power over the two idle windows (counter difference / time).

STATISTICS, per model and task:
- NET Wh per grading = (energy over the task's run - idle power x its duration) / gradings completed. The
  primary figure, as the task asks: the energy the grading adds to a GPU that is already on.
- GROSS Wh per grading = energy over the run / gradings, idle included (what the GPU drew while marking).
- FULL-STACK Wh per grading = NET x 1.72: the ratio of Google's comprehensive per-prompt energy to its active-
  accelerator energy (Elsworth et al. 2025, arXiv 2508.15734, Table 1: active AI accelerators 0.14 of 0.24 Wh,
  58%; the rest is host CPU and memory 25%, idle machines 10%, data-centre overhead 8%). A stated assumption,
  not a measurement of this node.
- 95% interval: a block bootstrap over the run's 20 equal windows (2,000 draws, seed 7): the estimate plus or
  minus t(0.975, windows - 1) times the bootstrap standard error (CHANGE 1), of the ratio sum(net energy) /
  sum(gradings completed) over the resampled windows. It covers the variation of energy over the run, not
  other hardware.
- Per full leaderboard run: the three tasks' gradings added, as kWh.
The BOUNDARY is the GPU only (NET, GROSS) or the GPU with Google's stated overheads (FULL-STACK). Not counted:
the CPU, memory, disk and network of this node as measured, cooling, the GPU's manufacture, and the time to
load the model.

COMPARISON WITH THE ESTIMATES. For each model and task, docs/energy.json's per-token model (fixed + per 1k input
+ per 1k output tokens) applied to that model's own mean input and output tokens in the measured run, at the
small-model tier (Llama 3.1 8B in Jegham et al.) and the mid-size tier (GPT-4o). Jegham et al. count the node
and the data centre, so the FULL-STACK figure is compared, with these verdicts on its 95% interval:
  BELOW THE SMALL-MODEL ESTIMATE    upper bound below the small-model tier
  WITHIN THE ESTIMATES' RANGE       the interval overlaps [small-model tier, mid-size tier]
  ABOVE THE MID-SIZE ESTIMATE       lower bound above the mid-size tier
and the ratio measured / estimate at each tier. Sign: a ratio below 1 means the estimate overstates the energy.

FLOOR (before any figure is read):
- `floor` (no GPU): 300 simulated runs with a known net energy per grading, 1-s power noise of 15%, per-grading
  energy noise of 15%, and the real poll and window sizes, idle power known. The estimator must recover the truth
  within 3% on average and the 95% interval must cover it in at least 90% of runs.
- Idle drift is not in the interval. So NET is also computed with each idle window alone, and that range is
  reported beside the interval.
- On the pod, per model: the counter's energy over the run and the integral of the 1-s power samples must agree
  within 5%, and the two idle windows' mean power within 10%. A model that fails is reported UNMEASURED.

DESCRIPTIVE, no verdict: QWK between the self-hosted base marks and the board's base marks for the same cases
(an identity check for the served weights, beside the board's own retest QWK); output tokens against the
board's.

CHANGES:
1. (2026-10-25, after the first model's runs, before any energy figure was read) The runs are far faster than
   planned: Llama 3.2 3B graded 909 short answers in 22 s at 16 concurrent requests. With 5-s polls and 30-s
   windows that is one window, and no interval. Now the counter and the completed count are read every 1 s, and
   each run is cut into 20 windows of equal length for the block bootstrap. The floor is re-run with runs of
   20-3,000 s. That floor FAILED narrowly (coverage 89.3%, bar 90%; mean error 0.5%; out/floor-change1-
   percentile-failed.json): a percentile interval from 20 blocks is too narrow. The interval is now the estimate
   plus or minus t(0.975, 19 df) times the bootstrap standard error, the usual small-sample correction, and the
   floor was re-run once, unchanged otherwise. Llama's first runs are discarded unread and repeated after a vLLM restart, so the prefix cache
   starts empty as for every other model.
2. (2026-10-25, after Llama 3.2 3B's figures were read) Llama failed the idle check: 65.8 W in the idle window
   before its runs, 77.3 W in the one straight after (ratio 1.17, bar 1.10), while the counter agreed with the
   integrated power (1.005). The likely cause is heat: a GPU idles higher just after work. The registered rule
   stands for every model: a model that fails is UNMEASURED, and the protocol is unchanged for the rest. Added,
   descriptive only and labelled as such: the verdict the FULL-STACK figure would get with each idle window
   alone, and with the GROSS figure (nothing subtracted, so an upper bound on the GPU's energy).

    python3 energy/energy.py floor
    python3 energy/energy.py measure --slug <slug> --model <served name> --cases-dir DIR --runs DIR   # on the pod
    python3 energy/energy.py analyse --runs DIR --out energy/out/energy.json                         # here

Reads the corpora's cases on the pod (aggregates out only). Run folders stay outside the repository.
"""
import argparse
import json
import math
import os
import random
import subprocess
import sys
import threading
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

FILES = {"mohler": "mohler.jsonl", "asap2": "asap2.jsonl", "code": "harmogen-code.jsonl"}
TASK_NAMES = {"mohler": "short answer", "asap2": "essay", "code": "code"}
#: slug -> (board model id, Hugging Face repo, revision, extra vLLM arguments)
MODELS = {
    "google_gemma-3-4b-it": ("google/gemma-3-4b-it", "unsloth/gemma-3-4b-it", "bf46152c47f5dd20b896357cb51abc4c03b8ee8c", []),
    "google_gemma-3-27b-it": ("google/gemma-3-27b-it", "unsloth/gemma-3-27b-it", "7a5a3053dbd5d1d58e48159e87b9df2fc545a49a", []),
    "google_gemma-4-26b-a4b-it": ("google/gemma-4-26b-a4b-it", "google/gemma-4-26B-A4B-it", "4d7ae4984b7db7de8f8457170b3f1a419ee76d52", []),
    "google_gemma-4-31b-it": ("google/gemma-4-31b-it", "google/gemma-4-31B-it", "842da3794eaa0b77d5f08bae87a17459d91ff475", []),
    "meta-llama_llama-3.2-3b-instruct": ("meta-llama/llama-3.2-3b-instruct", "unsloth/Llama-3.2-3B-Instruct", "006f5dcd1393c3add266de40994ba96225e9689d", []),
    "microsoft_phi-4": ("microsoft/phi-4", "microsoft/phi-4", "2db69c1c3e91a05d2c64a3185acfbaf36f744e25", []),
    "mistralai_ministral-8b-2512": ("mistralai/ministral-8b-2512", "mistralai/Ministral-3-8B-Instruct-2512", "5b26027e7b19eeb4b7352e1fed3926375dd2cb4d",
                                    ["--tokenizer-mode", "mistral", "--config-format", "mistral", "--load-format", "mistral"]),
    "openai_gpt-oss-20b": ("openai/gpt-oss-20b", "openai/gpt-oss-20b", "6cee5e81ee83917806bbde320786a8fb61efebee", []),
    "allenai_olmo-3.1-32b-instruct": ("allenai/olmo-3.1-32b-instruct", "allenai/Olmo-3.1-32B-Instruct", "ac0587e4a7744a551c059d8cd17ba220bc940dae",
                                      ["--chat-template", "/workspace/olmo-chat-template.jinja"]),
}
OVERHEAD = 1 / 0.58  # Elsworth et al. 2025, Table 1: active accelerators are 58% of the comprehensive figure
POLL, WINDOWS, IDLE_S = 1, 20, 60
#: Student's t, 97.5th percentile, by degrees of freedom (CHANGE 1)
T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201,
        12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093}
ROUTE = ("self-hosted: vLLM v0.32.0 on one rented RunPod A100 80GB PCIe pod; bench.py ran on the pod against "
         "localhost, so no request left it; the pod and its disk were deleted after the run, so nothing is retained")


def vllm_args(slug):
    board, repo, rev, extra = MODELS[slug]
    return ["--model", repo, "--revision", rev, "--served-model-name", board, "--max-model-len", "16384",
            "--gpu-memory-utilization", "0.92", "--api-key", os.environ.get("CTL_TOKEN", ""), *extra]


# ------------------------------------------------------------------ on the pod

def read_energy():
    req = urllib.request.Request("http://127.0.0.1:8001/energy", headers={"X-Token": os.environ["CTL_TOKEN"]})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def idle(seconds):
    a = read_energy()
    time.sleep(seconds)
    b = read_energy()
    return {"t0": a["t"], "t1": b["t"], "j": (b["mj"] - a["mj"]) / 1000, "w": (b["mj"] - a["mj"]) / 1000 / (b["t"] - a["t"])}


def monitored(cmd, cache_dir):
    """Runs cmd, polling the energy counter and the count of completed gradings every POLL seconds."""
    polls = []

    def count():
        return len(os.listdir(cache_dir)) if os.path.isdir(cache_dir) else 0
    start = count()
    e = read_energy()
    polls.append({"t": e["t"], "mj": e["mj"], "done": 0})
    p = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    out = []
    threading.Thread(target=lambda: out.extend(p.stdout), daemon=True).start()
    while p.poll() is None:
        time.sleep(POLL)
        e = read_energy()
        polls.append({"t": e["t"], "mj": e["mj"], "done": count() - start})
    time.sleep(1)
    e = read_energy()
    polls.append({"t": e["t"], "mj": e["mj"], "done": count() - start})
    return {"cmd": cmd, "rc": p.returncode, "polls": polls, "log_tail": "".join(out)[-3000:]}


def cmd_measure(a):
    board = MODELS[a.slug][0] if a.slug in MODELS else a.model
    res = {"slug": a.slug, "model": board, "gpu_samples_from": time.time(), "idle": [], "runs": {}, "sensitivity": {}}
    log = os.path.join(a.runs, f"energy-{a.slug}.json")
    save = lambda: json.dump(res, open(log, "w"), indent=1)
    res["idle"].append(idle(IDLE_S))
    save()
    common = ["--base-url", "http://127.0.0.1:8000/v1", "--model", board, "--key-env", "CTL_TOKEN", "--max-tokens", "4096",
              "--max-calls", "5000", "--go",
              "--route", ROUTE]
    for task in a.tasks.split(","):
        out = os.path.join(a.runs, f"{a.prefix}{task}-{a.slug}")
        cmd = [sys.executable, "bench.py", "run", "--cases", os.path.join(a.cases_dir, FILES[task]), "--battery", "leaderboard",
               "--prompt", "prompts/default.txt", "--workers", "16", "--out", out, *common]
        res["runs"][task] = monitored(cmd, os.path.join(out, ".cache"))
        print(task, "rc", res["runs"][task]["rc"], res["runs"][task]["log_tail"][-300:], flush=True)
        save()
    res["idle"].append(idle(IDLE_S))
    save()
    if not a.no_sensitivity:
        for task in ("mohler", "asap2"):
            out = os.path.join(a.runs, f"en1-{task}-{a.slug}")
            cmd = [sys.executable, "bench.py", "run", "--cases", os.path.join(a.cases_dir, FILES[task]), "--probes", "base",
                   "--n", "30", "--seed", "8", "--prompt", "prompts/default.txt", "--workers", "1", "--out", out, *common]
            res["sensitivity"][task] = monitored(cmd, os.path.join(out, ".cache"))
            save()
    res["gpu_samples_to"] = time.time()
    req = urllib.request.Request(f"http://127.0.0.1:8001/samples?since={res['gpu_samples_from']}",
                                 headers={"X-Token": os.environ["CTL_TOKEN"]})
    res["gpu_samples"] = json.loads(urllib.request.urlopen(req, timeout=60).read())
    save()
    print("wrote", log)


# ------------------------------------------------------------------ analysis (here)

def windows(polls):
    """The run cut into WINDOWS windows of equal length: (seconds, joules, gradings) each (CHANGE 1)."""
    t0, t1 = polls[0]["t"], polls[-1]["t"]
    edges = [t0 + (t1 - t0) * k / WINDOWS for k in range(WINDOWS + 1)]
    out = [[0.0, 0.0, 0] for _ in range(WINDOWS)]
    for p0, p1 in zip(polls, polls[1:]):
        k = min(WINDOWS - 1, max(0, sum(1 for e in edges[1:-1] if p0["t"] >= e)))
        out[k][0] += p1["t"] - p0["t"]
        out[k][1] += (p1["mj"] - p0["mj"]) / 1000
        out[k][2] += p1["done"] - p0["done"]
    return [tuple(w) for w in out if w[0] > 0]


def estimate(wins, idle_w, draws=2000, seed=7):
    """NET and GROSS Wh per grading, with a block-bootstrap 95% interval for NET."""
    s = sum(w[0] for w in wins)
    j = sum(w[1] for w in wins)
    n = sum(w[2] for w in wins)
    if not n:
        return None
    net = (j - idle_w * s) / 3600 / n
    rng = random.Random(seed)
    reps = []
    for _ in range(draws):
        pick = [wins[rng.randrange(len(wins))] for _ in wins]
        nn = sum(w[2] for w in pick)
        if nn:
            reps.append((sum(w[1] for w in pick) - idle_w * sum(w[0] for w in pick)) / 3600 / nn)
    mu = sum(reps) / len(reps)
    se = math.sqrt(sum((r - mu) ** 2 for r in reps) / (len(reps) - 1)) if len(reps) > 1 else 0.0
    half = T975.get(len(wins) - 1, 1.96) * se
    ci = [net - half, net + half]
    return {"net_wh": net, "net_ci95": ci, "net_se": se, "windows": len(wins),
            "gross_wh": j / 3600 / n, "gradings": n, "seconds": s, "joules": j,
            "full_stack_wh": net * OVERHEAD, "full_stack_ci95": [ci[0] * OVERHEAD, ci[1] * OVERHEAD]}


def cmd_floor(a):
    rng = random.Random(11)
    errs, cover = [], 0
    for _ in range(300):
        truth = rng.uniform(0.005, 0.5)       # Wh per grading
        idle_w = rng.uniform(40, 80)
        rate = rng.uniform(1, 40)              # gradings per second
        dur = rng.uniform(20, 3000)
        polls, t, mj, done = [{"t": 0.0, "mj": 0, "done": 0}], 0.0, 0.0, 0
        while t < dur:
            k = sum(1 for _ in range(int(rate * POLL * 2)) if rng.random() < 0.5)  # completions in this poll
            for _ in range(POLL):  # 1-s power noise
                mj += idle_w * 1000 * (1 + rng.gauss(0, 0.15))
            mj += k * truth * 3600 * 1000 * (1 + rng.gauss(0, 0.15))
            t += POLL
            done += k
            polls.append({"t": t, "mj": mj, "done": done})
        e = estimate(windows(polls), idle_w, draws=400)
        errs.append(abs(e["net_wh"] - truth) / truth)
        cover += e["net_ci95"][0] <= truth <= e["net_ci95"][1]
    mean_err = sum(errs) / len(errs)
    res = {"worlds": 300, "mean_abs_rel_error": mean_err, "coverage": cover / 300,
           "pass": mean_err <= 0.03 and cover / 300 >= 0.90}
    print(json.dumps(res, indent=1))
    if a.out:
        json.dump(res, open(a.out, "w"), indent=1)


def instrument_check(m):
    """Counter vs integrated 1-s power over the measured runs, and idle stability."""
    out = {}
    samples = m.get("gpu_samples") or []
    if samples:
        runs = list(m["runs"].values())
        t0, t1 = runs[0]["polls"][0]["t"], runs[-1]["polls"][-1]["t"]
        ss = [s for s in samples if t0 <= s["t"] <= t1]
        integ = sum((b["t"] - a["t"]) * (a["w"] + b["w"]) / 2 for a, b in zip(ss, ss[1:]))
        counter = (ss[-1]["mj"] - ss[0]["mj"]) / 1000 if len(ss) > 1 else None
        out["counter_vs_power"] = counter and integ / counter
    i0, i1 = m["idle"][0]["w"], m["idle"][-1]["w"]
    out["idle_w"] = [i0, i1]
    out["idle_ratio"] = max(i0, i1) / min(i0, i1)
    out["pass"] = (out.get("counter_vs_power") is not None and abs(out["counter_vs_power"] - 1) <= 0.05
                   and out["idle_ratio"] <= 1.10)
    return out


def tokens(run_dir):
    calls = [json.loads(l) for l in open(os.path.join(run_dir, "calls.jsonl"))]
    u = [c["usage"] for c in calls if c.get("usage") and c["usage"].get("prompt_tokens") is not None]
    return (sum(x["prompt_tokens"] for x in u) / len(u), sum(x["completion_tokens"] for x in u) / len(u), len(calls),
            sum(1 for c in calls if c.get("error")))


def tier(coef, tin, tout):
    return coef[0] + coef[1] * tin / 1000 + coef[2] * tout / 1000


def verdict(ci, small, mid):
    if ci[1] < small:
        return "BELOW THE SMALL-MODEL ESTIMATE"
    if ci[0] > mid:
        return "ABOVE THE MID-SIZE ESTIMATE"
    return "WITHIN THE ESTIMATES' RANGE"


def board_agreement(slug, task, run_dir):
    from metrics import qwk
    sub = os.path.join(ROOT, "submissions", MODELS[slug][0].replace("/", "__"), f"{task}.json")
    if not os.path.exists(sub):
        return None
    theirs = {c["id"]: c["score"] for c in json.load(open(sub))["calls"] if c["probe"] == "base" and c.get("score") is not None}
    ours = {c["id"]: c["score"] for c in map(json.loads, open(os.path.join(run_dir, "calls.jsonl")))
            if c["probe"] == "base" and c.get("score") is not None}
    ids = sorted(set(theirs) & set(ours))
    lo, hi = {"mohler": (0, 5), "asap2": (1, 6), "code": (0, 90)}[task]
    return {"qwk_with_board": qwk([ours[i] for i in ids], [theirs[i] for i in ids], lo, hi), "n": len(ids)}


def cmd_analyse(a):
    e = json.load(open(os.path.join(ROOT, "docs", "energy.json")))["per_token_model"]["tiers"]
    small, mid = e["small model (Llama 3.1 8B)"], e["mid-size model (GPT-4o)"]
    floor = json.load(open(os.path.join(HERE, "out", "floor.json")))
    res = {"design": "energy/energy.py docstring", "floor": floor, "hardware": "1x NVIDIA A100 80GB PCIe (RunPod community cloud)",
           "serving": "vLLM v0.32.0, 16 concurrent requests", "overhead_factor": OVERHEAD, "models": {}}
    for slug in MODELS:
        p = os.path.join(a.runs, f"energy-{slug}.json")
        if not os.path.exists(p):
            continue
        m = json.load(open(p))
        chk = instrument_check(m)
        idle_w = sum(i["w"] for i in m["idle"]) / len(m["idle"])
        row = {"model": m["model"], "hf_repo": MODELS[slug][1], "revision": MODELS[slug][2], "instrument": chk,
               "idle_w": idle_w, "tasks": {}, "sensitivity": {}}
        prefix = "lb-" if slug.startswith("allenai") else "en-"
        for task, r in m["runs"].items():
            run_dir = os.path.join(a.runs, f"{prefix}{task}-{slug}")
            est = estimate(windows(r["polls"]), idle_w)
            est["net_wh_idle_range"] = sorted(estimate(windows(r["polls"]), i["w"], draws=1)["net_wh"] for i in m["idle"])
            tin, tout, n_calls, n_err = tokens(run_dir)
            s_, m_ = tier(small, tin, tout), tier(mid, tin, tout)
            row["tasks"][task] = dict(est, mean_tokens_in=tin, mean_tokens_out=tout, calls=n_calls, errors=n_err,
                                      estimate_small_wh=s_, estimate_mid_wh=m_,
                                      ratio_to_small=est["full_stack_wh"] / s_, ratio_to_mid=est["full_stack_wh"] / m_,
                                      verdict=verdict(est["full_stack_ci95"], s_, m_) if chk["pass"] else "UNMEASURED",
                                      board=board_agreement(slug, task, run_dir),
                                      descriptive_verdicts={  # CHANGE 2: not a verdict
                                          "idle_before_only": verdict([est["net_wh_idle_range"][0] * OVERHEAD] * 2, s_, m_),
                                          "idle_after_only": verdict([est["net_wh_idle_range"][1] * OVERHEAD] * 2, s_, m_),
                                          "gross": verdict([est["gross_wh"] * OVERHEAD] * 2, s_, m_)})
        tot = sum(t["net_wh"] * t["gradings"] for t in row["tasks"].values())
        row["leaderboard_run_kwh_net"] = tot / 1000
        row["leaderboard_run_gradings"] = sum(t["gradings"] for t in row["tasks"].values())
        for task, r in (m.get("sensitivity") or {}).items():
            est = estimate(windows(r["polls"]), idle_w)
            if est:
                row["sensitivity"][task] = {"net_wh": est["net_wh"], "net_ci95": est["net_ci95"], "gradings": est["gradings"],
                                            "ratio_to_batched": est["net_wh"] / row["tasks"][task]["net_wh"]}
        res["models"][m["model"]] = row
        print(m["model"], "instrument", "pass" if chk["pass"] else "FAIL", {k: round(v, 3) if isinstance(v, float) else v for k, v in chk.items() if k != "pass"})
        for task, t in row["tasks"].items():
            print(f"  {task:7s} net {t['net_wh'] * 1000:7.2f} mWh [{t['net_ci95'][0] * 1000:.2f}, {t['net_ci95'][1] * 1000:.2f}]  "
                  f"gross {t['gross_wh'] * 1000:7.2f}  full-stack {t['full_stack_wh'] * 1000:7.2f}  est small {t['estimate_small_wh'] * 1000:6.1f} "
                  f"mid {t['estimate_mid_wh'] * 1000:6.1f}  {t['verdict']}  tok {t['mean_tokens_in']:.0f}/{t['mean_tokens_out']:.0f}  "
                  f"board qwk {t['board'] and round(t['board']['qwk_with_board'], 2)}")
        for task, s in row["sensitivity"].items():
            print(f"  one at a time {task}: {s['net_wh'] * 1000:.1f} mWh ({s['ratio_to_batched']:.1f}x batched)")
    json.dump(res, open(a.out, "w"), indent=1)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("floor"); p.add_argument("--out", default=os.path.join(HERE, "out", "floor.json"))
    p = sub.add_parser("measure"); p.add_argument("--slug", required=True); p.add_argument("--model")
    p.add_argument("--cases-dir", required=True); p.add_argument("--runs", required=True)
    p.add_argument("--tasks", default="mohler,asap2,code"); p.add_argument("--prefix", default="en-")
    p.add_argument("--no-sensitivity", action="store_true")
    p = sub.add_parser("analyse"); p.add_argument("--runs", required=True); p.add_argument("--out", default=os.path.join(HERE, "out", "energy.json"))
    a = ap.parse_args()
    {"floor": cmd_floor, "measure": cmd_measure, "analyse": cmd_analyse}[a.cmd](a)


if __name__ == "__main__":
    main()
