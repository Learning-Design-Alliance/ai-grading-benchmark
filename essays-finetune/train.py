#!/usr/bin/env python3
"""Fine-tuned arms of essays-finetune/study.py (its docstring is the pre-registration). Runs on the rented GPU.

    python3 essays-finetune/train.py --corpus <asap2.jsonl> --split <split-full.json> --kind deberta|qwen|gemma --out <json>
        [--only same|cross|all] [--deadline <unix time>] [--micro <n>]

Writes {kind: {"same": {id: mark}, "cross": {prompt: {id: mark}}, "board": {probe: {id: mark}},
"battery": {probe: {id: mark}}}} for the TEST essays and the board's 100. Marks are on the 1-6 scale, unrounded.
"battery" is every grading the leaderboard battery plans for the board's 100 essays (bench.plan over
leaderboard battery probes, the inputs from prompting.probe_input), added by CHANGE 1 of study.py; "board" is the
original probe set, kept for the study's own board checks.

--deadline (CHANGE 1, the GPU cap): a cross-prompt fold whose projected end, from the measured seconds per
training essay, falls after the deadline is not started and is recorded under "not_run"; a run still going at the
deadline stops and records its fold as not run. Nothing is truncated silently.
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
GEMMA = ("google/gemma-4-26B-A4B-it", "4d7ae4984b7db7de8f8457170b3f1a419ee76d52")
LORA_TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
LO, HI = 1, 6
BOARD_PROBES = ("base", "injection", "forged", "vouched", "padding", "null_blank", "null_dot", "null_think",
                "null_restate", "null_gibberish")


def text(c, response):
    return f"{c['task']} || {response}"


def y(c):
    return (c["human"]["rater"] - LO) / (HI - LO)


class OverDeadline(Exception):
    pass


def last_token_regressor(backbone, hidden):
    """The QWEN arm's head for a backbone that has no sequence-classification class: one output, no bias, read
    from the last token (inputs are left-padded)."""
    import types
    import torch

    class Regressor(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.backbone = backbone
            self.score = torch.nn.Linear(hidden, 1, bias=False)
            torch.nn.init.normal_(self.score.weight, std=0.02)

        def forward(self, input_ids=None, attention_mask=None, **_):
            h = self.backbone(input_ids=input_ids, attention_mask=attention_mask, use_cache=False).last_hidden_state
            return types.SimpleNamespace(logits=self.score(h[:, -1].to(self.score.weight.dtype)))
    return Regressor()


def gemma_backbone(backbone, micro):
    """Gemma 4 26B A4B: the text decoder of the instruction-tuned checkpoint, LoRA on attention and the dense
    MLP. Its 128 experts per layer are fused 3-D parameters, not linear layers, so PEFT cannot put LoRA on them;
    they stay frozen (study.py CHANGE 1)."""
    import torch
    from peft import LoraConfig, get_peft_model
    backbone.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, target_modules=LORA_TARGETS)
    peft_bb = get_peft_model(backbone, cfg)
    model = last_token_regressor(peft_bb, backbone.config.hidden_size).to(dtype=torch.bfloat16)
    return model, {"lr": 1e-4, "epochs": 1, "batch": 16, "micro": micro, "max_len": 1024}


def build(kind, micro=4):
    import torch
    if kind == "gemma":
        from transformers import AutoModelForImageTextToText, AutoTokenizer
        tok = AutoTokenizer.from_pretrained(GEMMA[0], revision=GEMMA[1])
        tok.padding_side = "left"  # the head reads the last token
        impl = "grouped_mm"
        try:
            full = AutoModelForImageTextToText.from_pretrained(GEMMA[0], revision=GEMMA[1], dtype=torch.bfloat16,
                                                               device_map={"": 0}, experts_implementation=impl)
        except Exception as e:  # an older stack without grouped_mm experts
            print("grouped_mm experts unavailable:", str(e)[:200], "-> eager", flush=True)
            impl = "eager"
            full = AutoModelForImageTextToText.from_pretrained(GEMMA[0], revision=GEMMA[1], dtype=torch.bfloat16,
                                                               device_map={"": 0})
        backbone = full.model.language_model
        del full  # vision and audio towers and the LM head are not used
        torch.cuda.empty_cache()
        model, hp = gemma_backbone(backbone, micro)
        model = model.cuda()
        if impl != "eager":  # grouped_mm can load and still fail at run time on an older torch
            try:
                ids = torch.full((2, 16), 2, device="cuda")
                with torch.autocast("cuda", dtype=torch.bfloat16):
                    model(input_ids=ids, attention_mask=torch.ones_like(ids)).logits.float().sum().backward()
                model.zero_grad(set_to_none=True)
            except Exception as e:
                print("grouped_mm experts failed at run time:", str(e)[:200], "-> eager", flush=True)
                model.zero_grad(set_to_none=True)
                backbone.set_experts_implementation("eager")
                impl = "eager"
        hp["experts_implementation"] = impl
        n_lora = sum(p.numel() for p in model.parameters() if p.requires_grad)
        print(f"gemma: trainable {n_lora:,} parameters; experts {impl}; GPU memory "
              f"{torch.cuda.memory_allocated() / 2**30:.1f} GiB", flush=True)
        return tok, model, hp
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
                     target_modules=LORA_TARGETS, modules_to_save=["score"])
    model = get_peft_model(model, cfg).cuda()
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()
    return tok, model, {"lr": 1e-4, "epochs": 1, "batch": 16, "micro": 4, "max_len": 1024}


def train(kind, train_cases, label, deadline=None, micro=4, stats=None):
    import torch
    from transformers import get_linear_schedule_with_warmup
    torch.manual_seed(7)
    tok, model, hp = build(kind, micro) if kind == "gemma" else build(kind)
    texts, ys = [text(c, c["response"]) for c in train_cases], [y(c) for c in train_cases]
    steps = hp["epochs"] * math.ceil(len(texts) / hp["batch"])
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=hp["lr"], weight_decay=0.01)
    sched = get_linear_schedule_with_warmup(opt, int(0.1 * steps), steps)
    model.train()
    order = list(range(len(texts)))
    rnd = random.Random(7)
    t0 = time.time()
    nstep = 0
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
            nstep += 1
            if nstep % 50 == 0:
                el = time.time() - t0
                print(f"{kind} {label} step {nstep}/{steps} {el:.0f}s, about {el / nstep * (steps - nstep):.0f}s left, "
                      f"peak {torch.cuda.max_memory_allocated() / 2**30:.1f} GiB", flush=True)
            if deadline and time.time() > deadline:
                raise OverDeadline(f"{label}: deadline reached at step {nstep}/{steps}")
        mse = tot / len(texts)
        print(f"{kind} {label} epoch {ep + 1}/{hp['epochs']} train mse {mse:.4f} ({time.time() - t0:.0f}s)", flush=True)
        if mse != mse:
            raise SystemExit("loss is NaN")
    if stats is not None:
        stats["sec_per_train_essay"] = (time.time() - t0) / max(1, len(texts))
        stats.setdefault("runs", []).append({"label": label, "n": len(texts), "seconds": time.time() - t0,
                                             "peak_gib": torch.cuda.max_memory_allocated() / 2**30, **hp})
    model.eval()

    def predict(pairs):
        """Each distinct input text is scored once, so identical inputs (base, retest, a label in the context
        the model never sees) get identical marks whatever the batch."""
        out = {}
        bs = 16
        uniq = sorted({t for _, t in pairs})
        memo = {}
        for i in range(0, len(uniq), bs):
            chunk = [(t, t) for t in uniq[i:i + bs]]
            enc = tok([t for _, t in chunk], truncation=True, max_length=hp["max_len"], padding=True,
                      return_tensors="pt").to("cuda")
            with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16):
                v = model(**enc).logits.squeeze(-1).float().tolist()
            for (k, _), p in zip(chunk, v if isinstance(v, list) else [v]):
                memo[k] = LO + (HI - LO) * p
        for k, t in pairs:
            out[k] = memo[t]
        return out
    return predict, model


def battery_pairs(board, cs):
    """Every grading the leaderboard battery plans for the board's essays, built as baselines/baselines.py run()
    builds them: bench.plan over the battery's probes, the input from prompting.probe_input."""
    import bench
    import leaderboard as lb
    prompt = prompting.load_prompt(lb.DEFAULT_PROMPT)
    jobs, _ = bench.plan(board, cs, prompt, list(lb.battery()["probes"]), lb.SEED)
    out = {}
    for c, p, _ in jobs:
        got = prompting.probe_input(c, p, None, lb.SEED)
        resp = got[0] if got else c["response"]
        out.setdefault(p, []).append((c["id"], text(c, resp or "")))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--split", required=True)
    ap.add_argument("--kind", required=True, choices=["deberta", "qwen", "gemma"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default="all", choices=["same", "cross", "all"])
    ap.add_argument("--deadline", type=float, help="unix time: no training past it (the GPU cap)")
    ap.add_argument("--micro", type=int, default=4, help="gemma: micro-batch (batch 16 by gradient accumulation)")
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
    import transformers
    r["env"] = {"torch": torch.__version__, "transformers": transformers.__version__,
                "gpu": torch.cuda.get_device_name(0)}
    try:
        import peft
        r["env"]["peft"] = peft.__version__
    except ImportError:
        pass
    stats = r.setdefault("train_stats", {})
    r.setdefault("not_run", {})
    # same-prompt, then the board's checks with the same model
    if "same" not in r and a.only in ("same", "all"):
        try:
            predict, model = train(a.kind, [byid[i] for i in sp["train"]], "same-prompt", a.deadline, a.micro, stats)
        except OverDeadline as e:
            r["not_run"]["same"] = f"GPU cap: {e}"
            save()
            raise SystemExit(str(e))
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
        r["battery"] = {p: predict(pairs) for p, pairs in battery_pairs(board, cs).items()}
        save()
        del model
        torch.cuda.empty_cache()
    if a.only == "same":
        print("done", a.kind, flush=True)
        return
    r.setdefault("cross", {})
    for p, ids in sp["folds"].items():
        if p in r["cross"]:
            continue
        spe = stats.get("sec_per_train_essay")
        if a.deadline and spe and time.time() + 1.15 * spe * len(ids) + 120 > a.deadline:
            r["not_run"][f"cross {p}"] = f"GPU cap: projected {spe * len(ids):.0f}s, {a.deadline - time.time():.0f}s left"
            print("not run:", p, r["not_run"][f"cross {p}"], flush=True)
            save()
            continue
        try:
            predict, model = train(a.kind, [byid[i] for i in ids], f"cross {p}", a.deadline, a.micro, stats)
        except OverDeadline as e:
            r["not_run"][f"cross {p}"] = f"GPU cap: {e}"
            print("not run:", e, flush=True)
            save()
            torch.cuda.empty_cache()
            continue
        r["cross"][p] = predict([(c["id"], text(c, c["response"])) for c in test if c["task"] == p])
        save()
        del model
        torch.cuda.empty_cache()
    print("done", a.kind, flush=True)


if __name__ == "__main__":
    main()
