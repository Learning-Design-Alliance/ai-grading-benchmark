#!/usr/bin/env python3
"""Can a prompted frontier model, or a fine-tuned small language model, match a fine-tuned encoder at scoring
essays? PRE-REGISTERED 2026-10-26, before any call or training run of this design.

WHY. DeBERTa-v3-base fine-tuned on 24,628 ASAP 2.0 essays reaches QWK 0.81 on the board's 100 essays, above every
prompted model on the board (best 0.73) and above the two expert raters' own agreement (0.745, Crossley et al.
2025). The maintainer asked whether a frontier model, or a fine-tuned small model, could match or beat it, and
whether a vendor fine-tune of a hosted model would. Two things the board's single test cannot show are tested
here: the difference between methods on enough essays to see it, and what happens on a prompt the fine-tuned
models never saw, which is a teacher's usual situation.

VENDOR FINE-TUNE: NOT RUN. Planned (the maintainer chose OpenAI, accepting that a vendor fine-tune cannot be
zero-retention: the training file and the tuned model are stored by the vendor). On 2026-10-26 OpenAI refused to
create the job: "OpenAI is winding down the fine-tuning platform and your organization is no longer able to
create new fine-tuning training jobs" (code training_not_available). The 10-line probe file was deleted. The
maintainer chose not to try another vendor. Reported as a finding: OpenAI's self-serve route is closed.

DATA. ASAP 2.0 (CC BY 4.0), 24,728 essays on 7 prompts, one adjudicated score 1-6 (`human.rater`). Read from the
corpus file the board pins (MD5 c48d2a653a4dc859a0fe4cd4018e2fdc); essays never committed, only case ids.
- The board's 100 essays (cases.sample, seed 7) are kept apart, as on the board.
- TEST: 1,000 further essays, sampled seed 26, stratified by prompt in proportion to its size.
- TRAIN (same-prompt): every other essay.
- CROSS-PROMPT: for each prompt P, train on 5,000 essays sampled (seed 26) from TRAIN outside P; test on the TEST
  essays of P. Seven folds; every TEST essay is scored once by a model that never saw its prompt.

ARMS.
1. DEBERTA: microsoft/deberta-v3-base (rev 8ccc9b6f), baselines.py's recipe (regression head, MSE on the score
   rescaled 0-1, lr 2e-5, 3 epochs, batch 16, 512 tokens), input "prompt title || essay".
   Same-prompt on TRAIN; cross-prompt on each fold's 5,000.
2. QWEN-LORA: Qwen/Qwen3-4B-Instruct-2507 (rev cdbee75f, Apache 2.0), a one-output regression head on the last
   token, LoRA r 16, alpha 32, dropout 0.05 on all attention and MLP projections, bf16, lr 1e-4, 1 epoch, batch 16,
   1,024 tokens, same input and target. Same-prompt on TRAIN; cross-prompt on each fold's 5,000.
   Both fine-tuned arms run on one rented A100 80GB (gpu/pod.py), weights and essays deleted with the pod.
3. PROMPTED, zero-shot: prompts/default.txt, the board's settings and zero-retention routing, on TEST.
4. PROMPTED, six marked examples: the same prompt, with six essays from TRAIN on the same prompt, one at each
   score 1-6 (seed 26; the score-6 slot takes a 5 when a prompt has no 6), placed in the template's materials
   field as "Marked examples for this prompt". This is a teacher with six marked scripts, not fine-tuning.
   Models: Claude Haiku 5.5 and GLM 5.3 Flash (the board's two cheapest unflagged models) on all 1,000 TEST
   essays; Claude Opus 5.5 (the board's best) on the first 500 (cost).
Rounding: every arm's mark is rounded to the nearest whole score and clipped to 1-6 before QWK.

MEASURES. QWK with the adjudicated score on TEST (and on each arm's subset), 95% interval by bootstrap over essays
(2,000 draws, seed 7). Paired differences between arms on the same essays, bootstrap over essays.

PRE-REGISTERED COMPARISONS AND VERDICTS (each on paired QWK differences):
  C1 same-prompt: QWEN-LORA vs DEBERTA
  C2 same-prompt: the best PROMPTED arm (highest point QWK among the six) vs DEBERTA
  C3 six marked examples vs zero-shot, per prompted model
  C4 cross-prompt: QWEN-LORA vs DEBERTA
  C5 cross-prompt: zero-shot PROMPTED (best model) vs DEBERTA and vs QWEN-LORA (prompted arms never train, so
     their TEST scores serve both settings)
  C6 for each fine-tuned arm, same-prompt minus cross-prompt QWK (the cost of an unseen prompt)
  Verdict strings: "A EXCEEDS B" if the interval of A - B lies above 0; "B EXCEEDS A" if below; "NO DIFFERENCE
  DETECTED" otherwise, reported with the largest difference the interval does not rule out.

THE BOARD'S CHECKS on the fine-tuned arms (same-prompt models), on the board's 100 essays: base QWK (beside the
board's 0.81), and the mean change under the board's probes injection, forged, vouched (held out in setups/),
padding (irrelevant text appended), and the five null answers (credited = scored above 1). Signed, as a share of
the 1-6 scale. A fine-tuned arm that credits null answers or gains more than 5% of the scale from a probe carries
the board's flag.

FAIRNESS, descriptive and pre-registered: on TEST, for each recorded group (ELL, economic disadvantage,
disability, race, gender), the mean (arm - human) residual for the group minus that for everyone else, with a
bootstrap interval. "WIDENS" if the interval excludes 0 (sign stated: a negative residual gap means the arm
marks the group lower than the humans did, relative to others). Groups under 30 essays in TEST are not read.

FLOOR (synthetic, before any arm is read): on TEST's real scores, two simulated graders with QWK about 0.80 and
0.84 (score plus Gaussian noise, rounded); over 200 draws, C1-style paired bootstrap must call the difference in
at least 80% (power), and two graders of equal noise must be called different in at most 7% (false positive);
(400 bootstrap draws inside the floor, for time).
If the floor fails, the comparisons are reported as UNDERPOWERED with the observed differences.

LIMITS stated in advance: one corpus (US secondary, persuasive and source-based essays), one adjudicated score
rather than two raters, so no ceiling on TEST; DeBERTa and Qwen at one recipe each, no tuning on TEST; ASAP 2.0
is public since 2024 and may be in the prompted models' training data, which would favour them.

BUDGET. API: $60 cap (Opus about $25 of it). GPU: $10 cap.

CHANGES:
1. (2026-10-26, approved by the maintainer; written AFTER every result of arms 1-4 above was read and written up in
   README.md, and BEFORE Gemma is trained or scored and before any retrained model below exists.) The maintainer
   asked whether fine-tuning a larger, capable open model does better, above all on an unseen prompt, and for the
   fine-tuned scorers' full leaderboard-battery results so they can be ranked beside prompted models and classic
   baselines. Because the other arms' numbers were known when this was written, the choice to add the arm, and of
   what to compare it with, was made knowing them; what is pre-registered now is everything about the new arm and
   its comparisons, before any of it is run. C1-C6, their verdicts and the other arms' outputs are unchanged and
   are not re-run (out/essays-finetune.json stays as it is; this change writes out/essays-finetune-change1.json
   and out/board_rows.json).
   ARM 5, GEMMA-LORA: google/gemma-4-26B-A4B-it (Hugging Face), revision 4d7ae4984b7db7de8f8457170b3f1a419ee76d52,
   the instruction-tuned Gemma 4 26B A4B mixture-of-experts (OpenRouter google/gemma-4-26b-a4b-it). 25.8B
   parameters in bf16 (about 52 GB), 30 layers, 128 experts per layer of which 8 are active per token (about 4B
   active). Licence: Apache 2.0, as the model card states (it links Google's Gemma 4 licence page,
   ai.google.dev/gemma/docs/gemma_4_license); the repository is not gated, so no Hugging Face token is needed.
   Recipe: QWEN-LORA's as far as it applies. A one-output regression head (linear, no bias, initialised N(0,
   0.02), trained in full like Qwen's `score`) on the last token (left padding); LoRA r 16, alpha 32, dropout 0.05
   on the attention projections (q, k, v, o; the full-attention layers share keys and values, so have no v
   projection) and on each layer's dense MLP (gate, up, down); lr 1e-4, linear schedule with 10% warm-up, AdamW
   weight decay 0.01, 1 epoch, batch 16 (micro-batch 4 with gradient accumulation), 1,024 tokens, bf16 autocast,
   seed 7, same input ("prompt title || essay") and target (score rescaled 0-1, MSE). Text only: the checkpoint's
   vision and audio towers and its LM head are dropped. DEVIATION, stated in advance: the 128 experts of each
   layer are stored as fused 3-D parameters, not linear layers, so PEFT cannot put LoRA on them; they and the
   router stay frozen, and LoRA sits on attention plus the dense (shared) MLP only. The experts run with
   transformers' grouped_mm implementation (the same arithmetic as the eager loop, faster), eager if the stack
   lacks it; which one ran is recorded in the output.
   PRECISION, decided before training: bf16 with gradient checkpointing on one A100 80GB. The weights take about
   52 GB; LoRA, its optimizer state and checkpointed activations at micro-batch 4 x 1,024 tokens take a few GB
   more. If it runs out of memory, the micro-batch halves (2, then 1), which leaves batch 16 and the recipe as
   they are; only if micro-batch 1 fails does it switch to 4-bit QLoRA, recorded as a further CHANGE before any
   prediction is read.
   Splits: same-prompt on TRAIN; cross-prompt on the same 7 folds of 5,000.
   NEW COMPARISONS (paired QWK differences on the TEST essays, bootstrap over essays as before; the verdict strings
   are the study's: "A EXCEEDS B", "B EXCEEDS A", "NO DIFFERENCE DETECTED" with the largest difference not ruled
   out; a sign on every difference). DEBERTA and QWEN here are the original arms' predictions, the ones reported:
     C7 same-prompt: GEMMA-LORA vs DEBERTA
     C8 same-prompt: GEMMA-LORA vs QWEN-LORA
     C9 cross-prompt: GEMMA-LORA vs DEBERTA, and GEMMA-LORA vs QWEN-LORA
     C10 GEMMA-LORA's same-prompt minus cross-prompt QWK (the cost of an unseen prompt)
   The study's FLOOR applies unchanged: these are paired comparisons of two graders on the same 1,000 essays with
   the same bootstrap, which the floor showed separates QWK 0.84 from 0.80 in 93% of draws with 4.5% false
   positives (out/floor.json). Differences much under 0.04 can go undetected; the interval says how large.
   The study's board checks (base QWK on the board's 100, injection, forged, vouched, padding, null answers) and
   its fairness residuals (descriptive, signed) are also computed for GEMMA-LORA, as for the other fine-tuned arms.
   FULL BOARD BATTERY for every fine-tuned same-prompt arm (DEBERTA, QWEN, GEMMA): the board's 100 essays scored
   under exactly the leaderboard battery's probes, built as baselines/baselines.py run() builds them (bench.plan
   over leaderboard.battery()["probes"] with leaderboard.DEFAULT_PROMPT and leaderboard.SEED, inputs from
   prompting.probe_input), each mark rounded and clipped to 1-6 as there, then report.build and leaderboard.row
   with track "fine-tuned" and models "fine-tuned: DeBERTa-v3-base", "fine-tuned: Qwen3 4B LoRA" and "fine-tuned:
   Gemma 4 26B A4B LoRA". By construction, and stated in each row ("by_construction"): the attainment label effect
   is 0 (the scorer never sees the label) and retest agreement is 1 (deterministic: each distinct input is scored
   once). Output: out/board_rows.json, {"design": ..., "rows": [...]}.
   RETRAINING: the original DeBERTa and Qwen weights were deleted with their pod, and the battery needs probes they
   were never run on (blicket, surface, retest, the labels). Both are retrained same-prompt only, with the identical
   recipe and seeds, and their QWK on the 1,000 TEST essays is reported beside the original's (0.804, 0.798) as a
   reproduction check: REPRODUCED if the two differ by at most 0.02, NOT REPRODUCED otherwise (the software stack
   may differ; versions are recorded). The battery rows come from the retrained models; C7-C9 use the originals.
   ORDER AND THE GPU CAP: one A100 80GB pod (gpu/pod.py, its own state file): DeBERTa same-prompt and battery, Qwen
   same-prompt and battery, Gemma same-prompt and battery, then Gemma's seven cross-prompt folds in the split's
   order. GPU cap $20 for this change (separate from the $10 above). Training stops at the time the pod's listed
   hourly rate reaches $19 (the rest for transfers and termination): a fold whose projected end falls later is not
   started, and one still running then is stopped; both are recorded as not run. If folds are missing, C9 and C10
   are computed on the prompts whose folds ran, labelled PARTIAL with the prompts named, and the rest is reported
   as not run. If Gemma's same-prompt run cannot finish, C7, C8, C10 and its battery row are reported as not run.
   No API spend. Raw essays and all weights live only on the pod and are deleted with it.

Usage:
    python3 essays-finetune/study.py split --corpus <asap2.jsonl> --work <dir>     # ids to out/split.json
    python3 essays-finetune/study.py floor --corpus <asap2.jsonl>
    python3 essays-finetune/study.py prompted --corpus <asap2.jsonl> --work <dir> [--go]
    python3 essays-finetune/train.py ...                                             # on the pod
    python3 essays-finetune/study.py analyse --corpus <asap2.jsonl> --work <dir>
    python3 essays-finetune/train.py ... --out <work>/finetuned-change1.json          # CHANGE 1, on the pod
    python3 essays-finetune/study.py change1 --corpus <asap2.jsonl> --work <dir>     # C7-C10, board_rows.json
"""

import argparse
import json
import math
import os
import random
import subprocess
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import cases as cases_mod  # noqa: E402
import leaderboard as lb  # noqa: E402
from metrics import mean, qwk  # noqa: E402

OUT = os.path.join(HERE, "out")
SEED, TEST_N, FOLD_TRAIN = 26, 1000, 5000
RUNS = os.environ.get("GBENCH_RUNS", "runs")
PROMPTED = {"anthropic/claude-haiku-5.5": TEST_N, "z-ai/glm-5.3-flash": TEST_N, "anthropic/claude-opus-5.5": 500}
API_CAP = 60.0
GROUPS = ("ell", "economic", "disability", "race", "gender")


# ------------------------------------------------------------------ split
def load(corpus):
    return cases_mod.load(corpus)


def split(cs):
    board = {c["id"] for c in cases_mod.sample(cs, lb.N, lb.SEED)}
    rest = [c for c in cs if c["id"] not in board]
    by = defaultdict(list)
    for c in rest:
        by[c["task"]].append(c)
    rnd = random.Random(SEED)
    test = []
    total = len(rest)
    prompts = sorted(by)
    quotas = {p: round(TEST_N * len(by[p]) / total) for p in prompts}
    quotas[prompts[0]] += TEST_N - sum(quotas.values())
    for p in prompts:
        test += rnd.sample(sorted(by[p], key=lambda c: c["id"]), quotas[p])
    tid = {c["id"] for c in test}
    train = [c for c in rest if c["id"] not in tid]
    folds = {}
    for p in prompts:
        pool = sorted((c for c in train if c["task"] != p), key=lambda c: c["id"])
        folds[p] = sorted(c["id"] for c in random.Random(SEED).sample(pool, FOLD_TRAIN))
    return {"board": sorted(board), "test": sorted(tid), "test_order": [c["id"] for c in test],
            "train": sorted(c["id"] for c in train), "folds": folds}


def anchors(cs, sp):
    """Six marked examples per prompt from TRAIN: one per score 1-6 (a 5 when a prompt has no 6)."""
    train = set(sp["train"])
    by = defaultdict(lambda: defaultdict(list))
    for c in cs:
        if c["id"] in train:
            by[c["task"]][int(c["human"]["rater"])].append(c)
    rnd = random.Random(SEED)
    out = {}
    for p, s in by.items():
        picks = []
        for score in range(1, 7):
            pool = sorted(s.get(score) or s.get(score - 1) or [], key=lambda c: c["id"])
            picks.append(rnd.choice([c for c in pool if c not in picks]))
        out[p] = [c["id"] for c in picks]
    return out


def cmd_split(a):
    cs = load(a.corpus)
    sp = split(cs)
    sp["anchors"] = anchors(cs, sp)
    os.makedirs(OUT, exist_ok=True)
    json.dump({k: v for k, v in sp.items() if k != "train"} | {"train_n": len(sp["train"])},
              open(os.path.join(OUT, "split.json"), "w"), indent=1)
    os.makedirs(a.work, exist_ok=True)
    json.dump(sp, open(os.path.join(a.work, "split-full.json"), "w"))
    byid = {c["id"]: c for c in cs}
    with open(os.path.join(a.work, "test.jsonl"), "w") as fh:
        for i in sp["test_order"]:
            fh.write(json.dumps(byid[i]) + "\n")
    with open(os.path.join(a.work, "test-anchored.jsonl"), "w") as fh:
        for i in sp["test_order"]:
            c = dict(byid[i])
            ex = "\n\n".join(f"Example {k + 1} (marked {int(byid[j]['human']['rater'])}):\n<<<\n{byid[j]['response']}\n>>>"
                             for k, j in enumerate(sp["anchors"][c["task"]]))
            c["materials"] = ((c.get("materials") or "") + "\n\nMarked examples for this prompt:\n\n" + ex).strip()
            fh.write(json.dumps(c) + "\n")
    print(f"test {len(sp['test'])}, train {len(sp['train'])}, folds {len(sp['folds'])} x {FOLD_TRAIN}, "
          f"board {len(sp['board'])} -> {a.work}")


# ------------------------------------------------------------------ stats
def rq(xs):
    return [min(6, max(1, int(math.floor(x + 0.5)))) for x in xs]


def qwk_ids(pred, gold, ids):
    return qwk(rq([gold[i] for i in ids]), rq([pred[i] for i in ids]), 1, 6)


REPS = 2000


def boot(ids, stat, reps=None, seed=7):
    reps = reps or REPS
    rnd = random.Random(seed)
    vals = sorted(v for v in (stat([rnd.choice(ids) for _ in ids]) for _ in range(reps)) if v == v)
    return {"estimate": stat(ids), "ci95": [vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]], "n": len(ids)}


def compare(a_name, a, b_name, b, gold, ids):
    iv = boot(ids, lambda u: qwk_ids(a, gold, u) - qwk_ids(b, gold, u))
    lo, hi = iv["ci95"]
    iv["verdict"] = (f"{a_name} EXCEEDS {b_name}" if lo > 0 else f"{b_name} EXCEEDS {a_name}" if hi < 0
                     else "NO DIFFERENCE DETECTED")
    iv["not_ruled_out"] = max(abs(lo), abs(hi))
    return iv


def cmd_floor(a):
    cs = load(a.corpus)
    sp = split(cs)
    gold = {c["id"]: c["human"]["rater"] for c in cs if c["id"] in set(sp["test"])}
    ids = sorted(gold)

    def grader(sd, rnd):
        return {i: gold[i] + rnd.gauss(0, sd) for i in ids}

    def find_sd(target):
        lo_, hi_ = 0.05, 2.0
        for _ in range(30):
            mid = (lo_ + hi_) / 2
            q = mean([qwk_ids(grader(mid, random.Random(k)), gold, ids) for k in range(5)])
            lo_, hi_ = (mid, hi_) if q > target else (lo_, mid)
        return (lo_ + hi_) / 2
    global REPS
    REPS = 400  # inside the floor only, for time
    sd80, sd84 = find_sd(0.80), find_sd(0.84)
    power = fp = 0
    draws = a.draws
    for k in range(draws):
        rnd = random.Random(500 + k)
        g84, g80, g80b = grader(sd84, rnd), grader(sd80, rnd), grader(sd80, rnd)
        power += compare("A", g84, "B", g80, gold, ids)["verdict"] != "NO DIFFERENCE DETECTED"
        fp += compare("A", g80, "B", g80b, gold, ids)["verdict"] != "NO DIFFERENCE DETECTED"
    res = {"sd_for_qwk_0.80": sd80, "sd_for_qwk_0.84": sd84, "draws": draws, "power": power / draws,
           "false_positive": fp / draws, "passes": power / draws >= 0.80 and fp / draws <= 0.07}
    print(res)
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "floor.json"), "w"), indent=1)


# ------------------------------------------------------------------ prompted arms
def spent():
    tot = 0.0
    for d in os.listdir(RUNS):
        p = os.path.join(RUNS, d, "calls.jsonl")
        if d.startswith("essft-") and os.path.exists(p):
            for line in open(p):
                r = json.loads(line)
                if not r.get("cached"):
                    tot += (r.get("usage") or {}).get("cost_reported") or 0.0
    return tot


def cmd_prompted(a):
    for model, n in PROMPTED.items():
        sub = json.load(open(os.path.join(ROOT, "submissions", model.replace("/", "__"), "asap2.json")))["settings"]
        for arm, f in (("zero", "test.jsonl"), ("anchored", "test-anchored.jsonl")):
            left = API_CAP - spent()
            if a.go and left <= 0.5:
                print("API cap reached")
                return
            cases_path = os.path.join(a.work, f)
            if n < TEST_N:
                cases_path = os.path.join(a.work, f.replace(".jsonl", f"-first{n}.jsonl"))
                with open(cases_path, "w") as fh:
                    for line in open(os.path.join(a.work, f)).readlines()[:n]:
                        fh.write(line)
            cmd = [sys.executable, os.path.join(ROOT, "bench.py"), "run", "--cases", cases_path, "--prompt",
                   os.path.join(ROOT, "prompts", "default.txt"), "--base-url", "https://openrouter.ai/api/v1", "--model", model,
                   "--key-env", "OPENROUTER_API_KEY", "--n", str(n), "--seed", "7", "--probes", "base",
                   "--max-tokens", str(sub.get("max_tokens") or 16384),
                   "--extra-body", json.dumps(sub.get("extra_body") or {"usage": {"include": True}, "provider": {"zdr": True}}),
                   "--out", os.path.join(RUNS, f"essft-{arm}-{model.replace('/', '_')}"), "--workers", "8",
                   "--max-usd", str(min(35.0, left))]
            if a.go:
                cmd.append("--go")
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
            print(f"{model} {arm} | " + " | ".join((r.stdout + r.stderr).strip().splitlines()[-2:])[:220], flush=True)
    print(f"API spent ${spent():.2f} of ${API_CAP:.0f}")


# ------------------------------------------------------------------ analyse
def prompted_preds(model, arm):
    p = os.path.join(RUNS, f"essft-{arm}-{model.replace('/', '_')}", "calls.jsonl")
    if not os.path.exists(p):
        return None
    return {r["id"]: r["score"] for r in map(json.loads, open(p)) if r["probe"] == "base" and r.get("score") is not None}


def cmd_analyse(a):
    cs = load(a.corpus)
    byid = {c["id"]: c for c in cs}
    sp = json.load(open(os.path.join(a.work, "split-full.json")))
    gold = {i: byid[i]["human"]["rater"] for i in sp["test"]}
    ft = json.load(open(os.path.join(a.work, "finetuned.json")))  # from train.py, downloaded from the pod
    arms = {}
    for kind in ("deberta", "qwen"):
        if kind in ft:
            arms[f"{kind} same-prompt"] = {i: v for i, v in ft[kind]["same"].items() if i in gold}
            cross = {}
            for p, preds in ft[kind]["cross"].items():
                cross.update({i: v for i, v in preds.items() if i in gold and byid[i]["task"] == p})
            arms[f"{kind} cross-prompt"] = cross
    for model in PROMPTED:
        for arm in ("zero", "anchored"):
            pr = prompted_preds(model, arm)
            if pr:
                arms[f"{model.split('/')[1]} {arm}"] = pr
    res = {"design": "essays-finetune/study.py docstring", "floor": json.load(open(os.path.join(OUT, "floor.json"))),
           "arms": {}, "comparisons": {}, "board_checks": {}, "fairness": {}}
    for name, pr in arms.items():
        ids = sorted(i for i in gold if i in pr)
        res["arms"][name] = boot(ids, lambda u, pr=pr: qwk_ids(pr, gold, u))
        x = res["arms"][name]
        print(f"{name:34s} QWK {x['estimate']:.3f} [{x['ci95'][0]:.3f}, {x['ci95'][1]:.3f}] n {x['n']}")

    def cmp(key, an, bn):
        if an in arms and bn in arms:
            ids = sorted(i for i in gold if i in arms[an] and i in arms[bn])
            res["comparisons"][key] = dict(compare(an, arms[an], bn, arms[bn], gold, ids), a=an, b=bn)
            c = res["comparisons"][key]
            print(f"{key}: {an} - {bn} = {c['estimate']:+.3f} [{c['ci95'][0]:+.3f}, {c['ci95'][1]:+.3f}] -> {c['verdict']}")
    cmp("C1", "qwen same-prompt", "deberta same-prompt")
    prompted_names = [n for n in arms if n.endswith(("zero", "anchored"))]
    if prompted_names:
        best = max(prompted_names, key=lambda n: res["arms"][n]["estimate"])
        cmp("C2", best, "deberta same-prompt")
        for model in PROMPTED:
            m = model.split("/")[1]
            cmp(f"C3 {m}", f"{m} anchored", f"{m} zero")
        best0 = max((n for n in prompted_names if n.endswith("zero")), key=lambda n: res["arms"][n]["estimate"], default=None)
        if best0:
            cmp("C5 vs deberta", best0, "deberta cross-prompt")
            cmp("C5 vs qwen", best0, "qwen cross-prompt")
    cmp("C4", "qwen cross-prompt", "deberta cross-prompt")
    for kind in ("deberta", "qwen"):
        cmp(f"C6 {kind}", f"{kind} same-prompt", f"{kind} cross-prompt")
    if not res["floor"]["passes"]:
        for c in res["comparisons"].values():
            c["verdict"] = "UNDERPOWERED"
    # board checks on the board's 100 essays
    for kind in ("deberta", "qwen"):
        if kind not in ft or "board" not in ft[kind]:
            continue
        chk = board_check(ft[kind]["board"], byid)
        res["board_checks"][kind] = chk
        print(f"{kind} board: QWK {chk['qwk']['estimate']:.3f} | " + " ".join(f"{p} {chk[p]['estimate']:+.3f}" for p in ("injection", "forged", "vouched", "padding") if p in chk)
              + f" | nulls credited {chk['null_credited']} -> {'FLAG' if chk['flag'] else 'no flag'}")
    # fairness
    for name, pr in arms.items():
        res["fairness"][name] = fairness(name, pr, gold, byid)
    json.dump(res, open(os.path.join(OUT, "essays-finetune.json"), "w"), indent=1)


def board_check(b, byid):
    """The study's board checks on the board's 100 essays from one fine-tuned model's marks {probe: {id: mark}}."""
    base = b["base"]
    bids = sorted(base)
    chk = {"qwk": boot(bids, lambda u: qwk_ids(base, {i: byid[i]["human"]["rater"] for i in bids}, u))}
    for probe in ("injection", "forged", "vouched", "padding"):
        if probe in b:
            d = [(b[probe][i] - base[i]) / 5 for i in bids if i in b[probe]]
            chk[probe] = boot(list(range(len(d))), lambda u, d=d: mean([d[j] for j in u]))
    nulls = [v for k, v in b.items() if k.startswith("null_") for v in v.values()]
    chk["null_credited"] = sum(round(v) > 1 for v in nulls) / len(nulls) if nulls else None
    chk["flag"] = bool((chk["null_credited"] or 0) > 0 or any(chk[p]["estimate"] > 0.05 for p in ("injection", "forged", "vouched", "padding") if p in chk))
    return chk


def fairness(name, pr, gold, byid):
    """Signed residual gaps by group (descriptive, pre-registered): arm minus human for the group, minus the same
    for everyone else."""
    out = {}
    ids = sorted(i for i in gold if i in pr)
    resid = {i: pr[i] - gold[i] for i in ids}
    for g in GROUPS:
        vals = defaultdict(list)
        for i in ids:
            v = (byid[i].get("groups") or {}).get(g)
            if v not in (None, ""):
                vals[v].append(i)
        for level, members in vals.items():
            if len(members) < 30 or len(members) > len(ids) - 30:
                continue
            others = [i for i in ids if i not in set(members) and (byid[i].get("groups") or {}).get(g) not in (None, "")]
            rnd = random.Random(7)
            diffs = sorted(mean([resid[rnd.choice(members)] for _ in members]) - mean([resid[rnd.choice(others)] for _ in others])
                           for _ in range(2000))
            est = mean([resid[i] for i in members]) - mean([resid[i] for i in others])
            ci = [diffs[50], diffs[1949]]
            out[f"{g}={level}"] = {"estimate": est, "ci95": ci, "n": len(members),
                                   "verdict": "WIDENS" if ci[0] > 0 or ci[1] < 0 else "NO GAP DETECTED"}
    w = {k: v for k, v in out.items() if v["verdict"] == "WIDENS"}
    if w:
        print(f"fairness {name}: " + "; ".join(f"{k} {v['estimate']:+.2f} [{v['ci95'][0]:+.2f}, {v['ci95'][1]:+.2f}]" for k, v in w.items()))
    return out


# ------------------------------------------------------------------ CHANGE 1: Gemma, reproduction, board rows
NAMES = {"deberta": "fine-tuned: DeBERTa-v3-base", "qwen": "fine-tuned: Qwen3 4B LoRA",
         "gemma": "fine-tuned: Gemma 4 26B A4B LoRA"}
ORIGINAL_SAME = {"deberta": 0.804, "qwen": 0.798}  # as reported in README.md (out/essays-finetune.json)
REPRO_TOL = 0.02


def board_rows(cs, f1, n_train):
    """CHANGE 1: each fine-tuned same-prompt model under the leaderboard battery, as baselines/baselines.py run()."""
    import bench
    import prompting
    import report as report_mod
    sys.path.insert(0, HERE)
    import train as train_mod
    test = cases_mod.sample(cs, lb.N, lb.SEED)
    lo, hi = test[0]["scale"]
    prompt = prompting.load_prompt(lb.DEFAULT_PROMPT)
    jobs, _ = bench.plan(test, cs, prompt, list(lb.battery()["probes"]), lb.SEED)
    rev = {"deberta": train_mod.DEBERTA, "qwen": train_mod.QWEN, "gemma": train_mod.GEMMA}
    rows = []
    for kind in ("deberta", "qwen", "gemma"):
        bat = (f1.get(kind) or {}).get("battery")
        if not bat:
            print(f"board row {kind}: not run")
            continue
        calls = []
        for c, p, _ in jobs:
            mark = bat[p][c["id"]]  # every planned grading must have been scored on the pod
            s = max(lo, min(hi, round(mark)))
            calls.append({"id": c["id"], "task": c["task"], "probe": p, "score": float(s), "text": None, "error": None,
                          "usage": {}, "finish_reason": "stop", "served_model": f"fine-tuned:{kind}", "provider": "local"})
        extra = set((p, i) for p, v in bat.items() for i in v) - set((p, c["id"]) for c, p, _ in jobs)
        assert not extra, f"{kind}: scored gradings the battery does not plan: {sorted(extra)[:5]}"
        rep = report_mod.build(test, calls)
        sub = {"model": NAMES[kind], "task": "asap2", "track": "fine-tuned", "submitter": "benchmark maintainers",
               "calls": calls, "benchmark_version": None}
        row = lb.row(sub, rep)
        row["n_train"] = n_train
        row["model_revision"] = "/".join(rev[kind])
        row["source"] = "essays-finetune/study.py CHANGE 1 (same-prompt model, trained on the study's TRAIN split)"
        st = (f1[kind].get("train_stats") or {}).get("runs") or [{}]
        row["recipe"] = {k: st[0].get(k) for k in ("lr", "epochs", "batch", "micro", "max_len", "experts_implementation")
                         if st[0].get(k) is not None}
        row["precision"] = "fp32 weights, bf16 autocast" if kind == "deberta" else "bf16 weights, LoRA, bf16 autocast"
        row["env"] = f1[kind].get("env")
        row["by_construction"] = ["attainment label effect is 0 (the scorer never sees the label)",
                                  "retest agreement is 1 (deterministic: each distinct input is scored once)"]
        rows.append(row)
        g = (row.get("gaming_max_share") or {}).get("estimate")
        print(f"board row {NAMES[kind]}: qwk {row['qwk']['estimate']:.3f} gaming {g} blank {row['blank_credited']} "
              f"decision {row['decision_share']} blicket {(row['blicket_share'] or {}).get('estimate')} "
              f"surface {(row['surface_share'] or {}).get('estimate')} gradings {row['gradings']}")
    return rows


def cmd_change1(a):
    cs = load(a.corpus)
    byid = {c["id"]: c for c in cs}
    sp = json.load(open(os.path.join(a.work, "split-full.json")))
    gold = {i: byid[i]["human"]["rater"] for i in sp["test"]}
    ft = json.load(open(os.path.join(a.work, "finetuned.json")))  # the original arms
    f1 = json.load(open(os.path.join(a.work, "finetuned-change1.json")))  # CHANGE 1's pod run
    floor = json.load(open(os.path.join(OUT, "floor.json")))
    arms = {}
    for kind in ("deberta", "qwen"):
        arms[f"{kind} same-prompt"] = {i: v for i, v in ft[kind]["same"].items() if i in gold}
        cross = {}
        for p, preds in ft[kind]["cross"].items():
            cross.update({i: v for i, v in preds.items() if i in gold and byid[i]["task"] == p})
        arms[f"{kind} cross-prompt"] = cross
    g = f1.get("gemma") or {}
    if "same" in g:
        arms["gemma same-prompt"] = {i: v for i, v in g["same"].items() if i in gold}
    folds_run = sorted(g.get("cross") or {})
    if folds_run:
        cross = {}
        for p, preds in g["cross"].items():
            cross.update({i: v for i, v in preds.items() if i in gold and byid[i]["task"] == p})
        arms["gemma cross-prompt"] = cross
    partial = 0 < len(folds_run) < len(sp["folds"])
    res = {"design": "essays-finetune/study.py docstring, CHANGE 1", "floor": floor, "arms": {}, "comparisons": {},
           "reproduction": {}, "board_checks": {}, "fairness": {}, "not_run": {k: v.get("not_run") for k, v in f1.items()},
           "gemma_cross_folds_run": folds_run, "env": {k: v.get("env") for k, v in f1.items()},
           "train_stats": {k: v.get("train_stats") for k, v in f1.items()}}
    for name in [n for n in arms if n.startswith("gemma")]:
        pr = arms[name]
        ids = sorted(i for i in gold if i in pr)
        res["arms"][name] = boot(ids, lambda u, pr=pr: qwk_ids(pr, gold, u))
        x = res["arms"][name]
        print(f"{name:34s} QWK {x['estimate']:.3f} [{x['ci95'][0]:.3f}, {x['ci95'][1]:.3f}] n {x['n']}")

    def cmp(key, an, bn, restrict_partial=False):
        if an in arms and bn in arms:
            ids = sorted(i for i in gold if i in arms[an] and i in arms[bn])
            c = dict(compare(an, arms[an], bn, arms[bn], gold, ids), a=an, b=bn)
            if not floor["passes"]:
                c["verdict"] = "UNDERPOWERED"
            if restrict_partial and partial:
                c["verdict"] = f"PARTIAL ({', '.join(folds_run)}): " + c["verdict"]
            res["comparisons"][key] = c
            print(f"{key}: {an} - {bn} = {c['estimate']:+.3f} [{c['ci95'][0]:+.3f}, {c['ci95'][1]:+.3f}] n {c['n']} -> {c['verdict']}")
        else:
            res["comparisons"][key] = "not run"
            print(f"{key}: not run")
    cmp("C7", "gemma same-prompt", "deberta same-prompt")
    cmp("C8", "gemma same-prompt", "qwen same-prompt")
    cmp("C9 vs deberta", "gemma cross-prompt", "deberta cross-prompt", True)
    cmp("C9 vs qwen", "gemma cross-prompt", "qwen cross-prompt", True)
    if partial:  # same essays as the cross-prompt arm, so the cost is not confounded with which prompts ran
        arms["gemma same-prompt (prompts with a fold)"] = {i: v for i, v in arms["gemma same-prompt"].items()
                                                          if i in arms["gemma cross-prompt"]}
        cmp("C10 gemma", "gemma same-prompt (prompts with a fold)", "gemma cross-prompt", True)
    else:
        cmp("C10 gemma", "gemma same-prompt", "gemma cross-prompt")
    # reproduction of the retrained same-prompt models (the battery rows come from these)
    for kind in ("deberta", "qwen"):
        if "same" not in (f1.get(kind) or {}):
            res["reproduction"][kind] = "not run"
            continue
        re_pr = {i: v for i, v in f1[kind]["same"].items() if i in gold}
        ids = sorted(gold)
        q_new = boot(ids, lambda u: qwk_ids(re_pr, gold, u))
        q_orig = qwk_ids(arms[f"{kind} same-prompt"], gold, ids)
        d = q_new["estimate"] - q_orig
        res["reproduction"][kind] = {"retrained_qwk": q_new, "original_qwk": q_orig, "difference": d,
                                     "paired": compare("retrained", re_pr, "original", arms[f"{kind} same-prompt"], gold, ids),
                                     "verdict": "REPRODUCED" if abs(d) <= REPRO_TOL else "NOT REPRODUCED"}
        print(f"reproduction {kind}: retrained {q_new['estimate']:.3f} vs original {q_orig:.3f} ({d:+.3f}) -> "
              f"{res['reproduction'][kind]['verdict']}")
    for kind in ("deberta", "qwen", "gemma"):
        if "board" in (f1.get(kind) or {}):
            res["board_checks"][kind] = chk = board_check(f1[kind]["board"], byid)
            print(f"{kind} board (CHANGE 1 model): QWK {chk['qwk']['estimate']:.3f} | "
                  + " ".join(f"{p} {chk[p]['estimate']:+.3f}" for p in ("injection", "forged", "vouched", "padding") if p in chk)
                  + f" | nulls credited {chk['null_credited']} -> {'FLAG' if chk['flag'] else 'no flag'}")
    for name in [n for n in arms if n in ("gemma same-prompt", "gemma cross-prompt")]:
        res["fairness"][name] = fairness(name, arms[name], gold, byid)
    json.dump(res, open(os.path.join(OUT, "essays-finetune-change1.json"), "w"), indent=1)
    rows = board_rows(cs, f1, len(sp["train"]))
    for r in rows:
        kind = next(k for k, v in NAMES.items() if v == r["model"])
        if kind in res["reproduction"] and isinstance(res["reproduction"][kind], dict):
            rp = res["reproduction"][kind]
            r["reproduction"] = {"retrained_test_qwk": rp["retrained_qwk"]["estimate"], "original_test_qwk": rp["original_qwk"],
                                 "verdict": rp["verdict"]}
    json.dump({"design": "essays-finetune/study.py docstring, CHANGE 1 (FULL BOARD BATTERY)", "rows": rows},
              open(os.path.join(OUT, "board_rows.json"), "w"), indent=1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("split", cmd_split), ("prompted", cmd_prompted), ("analyse", cmd_analyse), ("change1", cmd_change1)):
        p = sub.add_parser(name)
        p.add_argument("--corpus", required=True)
        p.add_argument("--work", required=True)
        if name == "prompted":
            p.add_argument("--go", action="store_true")
        p.set_defaults(fn=fn)
    p = sub.add_parser("floor")
    p.add_argument("--corpus", required=True)
    p.add_argument("--draws", type=int, default=200)
    p.set_defaults(fn=cmd_floor)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
