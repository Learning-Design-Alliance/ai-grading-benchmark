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

Usage:
    python3 essays-finetune/study.py split --corpus <asap2.jsonl> --work <dir>     # ids to out/split.json
    python3 essays-finetune/study.py floor --corpus <asap2.jsonl>
    python3 essays-finetune/study.py prompted --corpus <asap2.jsonl> --work <dir> [--go]
    python3 essays-finetune/train.py ...                                             # on the pod
    python3 essays-finetune/study.py analyse --corpus <asap2.jsonl> --work <dir>
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
        b = ft[kind]["board"]
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
        res["board_checks"][kind] = chk
        print(f"{kind} board: QWK {chk['qwk']['estimate']:.3f} | " + " ".join(f"{p} {chk[p]['estimate']:+.3f}" for p in ("injection", "forged", "vouched", "padding") if p in chk)
              + f" | nulls credited {chk['null_credited']} -> {'FLAG' if chk['flag'] else 'no flag'}")
    # fairness
    for name, pr in arms.items():
        ids = sorted(i for i in gold if i in pr)
        resid = {i: pr[i] - gold[i] for i in ids}
        res["fairness"][name] = {}
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
                res["fairness"][name][f"{g}={level}"] = {"estimate": est, "ci95": ci, "n": len(members),
                                                         "verdict": "WIDENS" if ci[0] > 0 or ci[1] < 0 else "NO GAP DETECTED"}
        w = {k: v for k, v in res["fairness"][name].items() if v["verdict"] == "WIDENS"}
        if w:
            print(f"fairness {name}: " + "; ".join(f"{k} {v['estimate']:+.2f} [{v['ci95'][0]:+.2f}, {v['ci95'][1]:+.2f}]" for k, v in w.items()))
    json.dump(res, open(os.path.join(OUT, "essays-finetune.json"), "w"), indent=1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("split", cmd_split), ("prompted", cmd_prompted), ("analyse", cmd_analyse)):
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
