#!/usr/bin/env python3
"""Fine-tuned arms of essays-finetune/study.py (its docstring is the pre-registration). Runs on the rented GPU.

    python3 essays-finetune/train.py --corpus <asap2.jsonl> --split <split-full.json> --kind deberta|qwen --out <json>

Writes {kind: {"same": {id: mark}, "cross": {prompt: {id: mark}}, "board": {probe: {id: mark}}}} for the TEST
essays and the board's 100. Marks are on the 1-6 scale, unrounded.
"""

import argparse
import json
import math
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import cases as cases_mod  # noqa: E402
import prompting  # noqa: E402

DEBERTA = ("microsoft/deberta-v3-base", "8ccc9b6f36199bec6961081d44eb72fb3f7353f3")
QWEN = ("Qwen/Qwen3-4B-Instruct-2507", "cdbee75f17c01a7cc42f958dc650907174af0554")
LO, HI = 1, 6
BOARD_PROBES = ("base", "injection", "forged", "vouched", "padding", "null_blank", "null_dot", "null_think",
                "null_restate", "null_gibberish")


def text(c, response):
    return f"{c['task']} || {response}"


def y(c):
    return (c["human"]["rater"] - LO) / (HI - LO)


def build(kind):
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    if kind == "deberta":
        tok = AutoTokenizer.from_pretrained(DEBERTA[0], revision=DEBERTA[1])
        model = AutoModelForSequenceClassification.from_pretrained(DEBERTA[0], revision=DEBERTA[1], num_labels=1,
                                                                   dtype=torch.float32).cuda()
        return tok, model, {"lr": 2e-5, "epochs": 3, "batch": 16, "micro": 16, "max_len": 512}
    from peft import LoraConfig, get_peft_model
    tok = AutoTokenizer.from_pretrained(QWEN[0], revision=QWEN[1])
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = "left"  # the head reads the last token
    model = AutoModelForSequenceClassification.from_pretrained(QWEN[0], revision=QWEN[1], num_labels=1,
                                                               dtype=torch.bfloat16)
    model.config.pad_token_id = tok.pad_token_id
    cfg = LoraConfig(task_type="SEQ_CLS", r=16, lora_alpha=32, lora_dropout=0.05,
                     target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
                     modules_to_save=["score"])
    model = get_peft_model(model, cfg).cuda()
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()
    return tok, model, {"lr": 1e-4, "epochs": 1, "batch": 16, "micro": 4, "max_len": 1024}


def train(kind, train_cases, label):
    import torch
    from transformers import get_linear_schedule_with_warmup
    torch.manual_seed(7)
    tok, model, hp = build(kind)
    texts, ys = [text(c, c["response"]) for c in train_cases], [y(c) for c in train_cases]
    steps = hp["epochs"] * math.ceil(len(texts) / hp["batch"])
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=hp["lr"], weight_decay=0.01)
    sched = get_linear_schedule_with_warmup(opt, int(0.1 * steps), steps)
    model.train()
    order = list(range(len(texts)))
    rnd = random.Random(7)
    t0 = time.time()
    for ep in range(hp["epochs"]):
        rnd.shuffle(order)
        tot = 0.0
        for i in range(0, len(order), hp["batch"]):
            idx = order[i:i + hp["batch"]]
            for j in range(0, len(idx), hp["micro"]):
                mi = idx[j:j + hp["micro"]]
                enc = tok([texts[k] for k in mi], truncation=True, max_length=hp["max_len"], padding=True,
                          return_tensors="pt").to("cuda")
                with torch.autocast("cuda", dtype=torch.bfloat16):
                    out = model(**enc).logits.squeeze(-1)
                loss = torch.nn.functional.mse_loss(out.float(), torch.tensor([ys[k] for k in mi], device="cuda"))
                (loss * len(mi) / len(idx)).backward()
                tot += loss.item() * len(mi)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            opt.zero_grad()
        mse = tot / len(texts)
        print(f"{kind} {label} epoch {ep + 1}/{hp['epochs']} train mse {mse:.4f} ({time.time() - t0:.0f}s)", flush=True)
        if mse != mse:
            raise SystemExit("loss is NaN")
    model.eval()

    def predict(pairs):
        out = {}
        bs = 16
        for i in range(0, len(pairs), bs):
            chunk = pairs[i:i + bs]
            enc = tok([t for _, t in chunk], truncation=True, max_length=hp["max_len"], padding=True,
                      return_tensors="pt").to("cuda")
            with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16):
                v = model(**enc).logits.squeeze(-1).float().tolist()
            for (k, _), p in zip(chunk, v if isinstance(v, list) else [v]):
                out[k] = LO + (HI - LO) * p
        return out
    return predict, model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--split", required=True)
    ap.add_argument("--kind", required=True, choices=["deberta", "qwen"])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import torch
    cs = cases_mod.load(a.corpus)
    byid = {c["id"]: c for c in cs}
    sp = json.load(open(a.split))
    test = [byid[i] for i in sp["test"]]
    res = json.load(open(a.out)) if os.path.exists(a.out) else {}
    res.setdefault(a.kind, {})
    r = res[a.kind]

    def save():
        json.dump(res, open(a.out, "w"))
    # same-prompt, then the board's checks with the same model
    if "same" not in r:
        predict, model = train(a.kind, [byid[i] for i in sp["train"]], "same-prompt")
        r["same"] = predict([(c["id"], text(c, c["response"])) for c in test])
        board = [byid[i] for i in sp["board"]]
        r["board"] = {}
        for probe in BOARD_PROBES:
            pairs = []
            for c in board:
                pi = prompting.probe_input(c, probe, seed=7)
                if pi and pi[0] is not None:
                    pairs.append((c["id"], text(c, pi[0])))
            r["board"][probe] = predict(pairs)
        save()
        del model
        torch.cuda.empty_cache()
    r.setdefault("cross", {})
    for p, ids in sp["folds"].items():
        if p in r["cross"]:
            continue
        predict, model = train(a.kind, [byid[i] for i in ids], f"cross {p}")
        r["cross"][p] = predict([(c["id"], text(c, c["response"])) for c in test if c["task"] == p])
        save()
        del model
        torch.cuda.empty_cache()
    print("done", a.kind, flush=True)


if __name__ == "__main__":
    main()
