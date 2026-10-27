#!/usr/bin/env python3
"""The generative fine-tune of essays-genft/study.py (its docstring is the pre-registration). Runs on the rented GPU.

    python3 essays-genft/train_gen.py train --corpus <asap2.jsonl> --split <genft-split.json> --fold same|<prompt>
        --adapter <dir> --stats <json> [--deadline <unix time>] [--limit N]      # LoRA; adapter + merge-check grades
    python3 essays-genft/train_gen.py merge --adapter <dir> --out <dir> [--dry]  # W + (alpha/r) B A into the shards
    python3 essays-genft/train_gen.py template-check --corpus ... --split ... --served <name>   # vs vLLM /tokenize
    python3 essays-genft/train_gen.py merge-check --stats <json> --corpus ... --served <name>  # vs vLLM, temperature 0

The input is the board's default prompt rendered as bench.py renders a base grading, through the checkpoint's chat
template (add_generation_prompt, thinking off by the template's default). The target is the tokens of
`{"score": N`, appended to the prompt's tokens; the loss is on those tokens only. No reason text is taught.
"""

import argparse
import json
import math
import os
import random
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import cases as cases_mod  # noqa: E402
import prompting  # noqa: E402

GEMMA = ("google/gemma-4-26B-A4B-it", "4d7ae4984b7db7de8f8457170b3f1a419ee76d52")
TARGETS = r".*language_model.*\.(q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)"
CHANGE1_TRAINABLE = 18_588_416 - 2_816  # essays-finetune CHANGE 1's count less its regression head (hidden 2,816 -> 1)
HP = {"r": 16, "alpha": 32, "dropout": 0.05, "lr": 1e-4, "epochs": 1, "batch": 16, "micro": 1, "warmup": 0.1,
      "weight_decay": 0.01, "clip": 1.0, "seed": 7, "max_len": 6144}
CHECK_N = 100
PROMPT = os.path.join(ROOT, "prompts", "default.txt")


class OverDeadline(Exception):
    pass


def tokenizer():
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(GEMMA[0], revision=GEMMA[1])


def messages(c, prompt):
    return prompt.build(c, *prompting.probe_input(c, "base"))


def encode(tok, prompt, c):
    """(prompt ids, target ids) for one essay."""
    text = tok.apply_chat_template(messages(c, prompt), tokenize=False, add_generation_prompt=True)
    p = tok(text, add_special_tokens=False)["input_ids"]
    t = tok('{"score": %d' % int(round(float(c["human"]["rater"]))), add_special_tokens=False)["input_ids"]
    return p, t


def check_ids(sp, byid):
    """Merge-check essays: 100 from TRAIN (seed 7), never TEST."""
    return random.Random(7).sample(sorted(sp["train"]), CHECK_N)


def load_model():
    import torch
    from transformers import AutoModelForImageTextToText
    impl = "grouped_mm"
    try:
        model = AutoModelForImageTextToText.from_pretrained(GEMMA[0], revision=GEMMA[1], dtype=torch.bfloat16,
                                                            device_map={"": 0}, experts_implementation=impl)
    except Exception as e:  # an older stack without grouped_mm experts
        print("grouped_mm experts unavailable:", str(e)[:200], "-> eager", flush=True)
        impl = "eager"
        model = AutoModelForImageTextToText.from_pretrained(GEMMA[0], revision=GEMMA[1], dtype=torch.bfloat16,
                                                            device_map={"": 0})
    return model, impl


def extra_inputs(model, ids):
    """Gemma's multimodal wrapper may want token-type ids in training; text only, so all zeros."""
    import inspect
    import torch
    params = inspect.signature(model.forward).parameters
    out = {}
    for k in ("token_type_ids", "mm_token_type_ids"):
        if k in params:
            out[k] = torch.zeros_like(ids)
    return out


def target_logits(model, ids, n_target, base_forward):
    """Logits that predict the last n_target tokens of ids (positions -n_target-1 .. -2)."""
    out = model(input_ids=ids, attention_mask=None, use_cache=False, logits_to_keep=n_target + 1,
                **extra_inputs(base_forward, ids))
    return out.logits[:, :-1]


def cmd_train(a):
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import get_linear_schedule_with_warmup
    t_start = time.time()
    cs = cases_mod.load(a.corpus)
    byid = {c["id"]: c for c in cs}
    sp = json.load(open(a.split))
    ids = sp["train"] if a.fold == "same" else sp["folds"][a.fold]
    if a.limit:
        ids = random.Random(1).sample(sorted(ids), a.limit)
    prompt = prompting.load_prompt(PROMPT)
    tok = tokenizer()
    data, dropped = [], []
    for i in ids:
        p, t = encode(tok, prompt, byid[i])
        if len(p) + len(t) > HP["max_len"]:
            dropped.append(i)
            continue
        data.append((i, p, t))
    t_lens = {len(t) for _, _, t in data}
    assert t_lens == {5}, f"target token counts {t_lens}: expected '{{\"', 'score', '\":', ' ', digit"
    n_tok = sum(len(p) + len(t) for _, p, t in data)
    stats = {"fold": a.fold, "n_essays": len(data), "dropped_too_long": dropped, "train_tokens": n_tok,
             "hp": HP, "gemma": GEMMA}
    print(f"{a.fold}: {len(data)} essays, {n_tok / 1e6:.2f}M tokens, {len(dropped)} dropped as too long", flush=True)

    torch.manual_seed(HP["seed"])
    model, impl = load_model()
    model.config.use_cache = False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    base_forward = model
    cfg = LoraConfig(r=HP["r"], lora_alpha=HP["alpha"], lora_dropout=HP["dropout"], target_modules=TARGETS)
    model = get_peft_model(model, cfg)
    n_train = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"trainable {n_train:,} parameters (CHANGE 1: {CHANGE1_TRAINABLE:,}); experts {impl}; "
          f"GPU {torch.cuda.memory_allocated() / 2**30:.1f} GiB", flush=True)
    assert n_train == CHANGE1_TRAINABLE, "LoRA does not sit on CHANGE 1's modules"
    import peft
    import transformers
    stats["env"] = {"torch": torch.__version__, "transformers": transformers.__version__, "peft": peft.__version__,
                    "gpu": torch.cuda.get_device_name(0), "experts_implementation": impl,
                    "adapter_dtype": str(next(p for p in model.parameters() if p.requires_grad).dtype)}
    stats["trainable"] = n_train

    order = list(range(len(data)))
    random.Random(HP["seed"]).shuffle(order)
    steps = math.ceil(len(order) / HP["batch"])
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=HP["lr"],
                            weight_decay=HP["weight_decay"])
    sched = get_linear_schedule_with_warmup(opt, int(HP["warmup"] * steps), steps)
    model.train()
    t0 = time.time()
    done_tok = 0
    losses = []
    for s in range(steps):
        idx = order[s * HP["batch"]:(s + 1) * HP["batch"]]
        tot = 0.0
        for k in idx:
            _, p, t = data[k]
            x = torch.tensor([p + t], device="cuda")
            with torch.autocast("cuda", dtype=torch.bfloat16):
                lg = target_logits(model, x, len(t), base_forward)
            loss = torch.nn.functional.cross_entropy(lg.float().reshape(-1, lg.shape[-1]),
                                                     torch.tensor(t, device="cuda"))
            (loss / len(idx)).backward()
            tot += loss.item()
            done_tok += len(p) + len(t)
        torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], HP["clip"])
        opt.step()
        sched.step()
        opt.zero_grad(set_to_none=True)
        losses.append(tot / len(idx))
        el = time.time() - t0
        if (s + 1) % 25 == 0 or s == steps - 1:
            rate = done_tok / el
            left = (n_tok - done_tok) / rate
            print(f"{a.fold} step {s + 1}/{steps} loss(last 25) {sum(losses[-25:]) / len(losses[-25:]):.4f} "
                  f"{el:.0f}s, {rate:.0f} tok/s, about {left:.0f}s left, peak "
                  f"{torch.cuda.max_memory_allocated() / 2**30:.1f} GiB", flush=True)
            if a.deadline and s + 1 >= 25 and time.time() + left > a.deadline:
                stats["not_run"] = f"GPU cap: projected end {left:.0f}s from now passes the deadline (step {s + 1}/{steps})"
                json.dump(stats, open(a.stats, "w"), indent=1)
                raise OverDeadline(stats["not_run"])
        if any(l != l for l in losses[-1:]):
            raise SystemExit("loss is NaN")
    stats.update({"seconds": time.time() - t0, "tokens_per_second": done_tok / (time.time() - t0), "steps": steps,
                  "loss_by_step": losses, "peak_gib": torch.cuda.max_memory_allocated() / 2**30})
    os.makedirs(a.adapter, exist_ok=True)
    model.save_pretrained(a.adapter)
    # merge-check grades: the in-process greedy grade after `{"score": ` on 100 TRAIN essays
    model.eval()
    grades = {}
    with torch.no_grad():
        for i in check_ids(sp, byid)[: (4 if a.limit else CHECK_N)]:
            p, t = encode(tok, prompt, byid[i])
            x = torch.tensor([p + t[:-1]], device="cuda")
            with torch.autocast("cuda", dtype=torch.bfloat16):
                lg = model(input_ids=x, use_cache=False, logits_to_keep=1, **extra_inputs(base_forward, x)).logits
            grades[i] = tok.decode([int(lg[0, -1].argmax())])
    stats["check_grades"] = grades
    stats["wall_seconds"] = time.time() - t_start
    json.dump(stats, open(a.stats, "w"), indent=1)
    print("done", a.fold, "| check grades", list(grades.values())[:10], flush=True)


def snapshot():
    from huggingface_hub import snapshot_download
    return snapshot_download(GEMMA[0], revision=GEMMA[1])


def cmd_merge(a):
    import torch
    from safetensors.torch import load_file, save_file
    cfg = json.load(open(os.path.join(a.adapter, "adapter_config.json")))
    scale = cfg["lora_alpha"] / cfg["r"]
    ad = load_file(os.path.join(a.adapter, "adapter_model.safetensors"))
    deltas = {}
    for k, A in ad.items():
        if k.endswith(".lora_A.weight"):
            mod = k[len("base_model.model."):-len(".lora_A.weight")]
            B = ad[k.replace(".lora_A.weight", ".lora_B.weight")]
            deltas[mod + ".weight"] = (B.float() @ A.float()) * scale
    src = snapshot()
    index = json.load(open(os.path.join(src, "model.safetensors.index.json")))
    missing = [k for k in deltas if k not in index["weight_map"]]
    assert not missing, f"adapter modules with no checkpoint weight: {missing[:5]}"
    rec = {"modules": len(deltas), "scale": scale, "shards": sorted(set(index["weight_map"].values()))}
    print(f"merge: {len(deltas)} adapted weights (scale {scale}) into {len(rec['shards'])} shards", flush=True)
    if a.dry:
        print("dry run: key mapping checked", flush=True)
        return
    if os.path.exists(a.out):
        shutil.rmtree(a.out)
    os.makedirs(a.out)
    changed, rel = 0, []
    for shard in rec["shards"]:
        ts = load_file(os.path.join(src, shard))
        for k in list(ts):
            if k in deltas:
                W = ts[k]
                assert tuple(W.shape) == tuple(deltas[k].shape), f"{k}: {W.shape} vs {deltas[k].shape}"
                new = (W.float() + deltas[k]).to(W.dtype)
                rel.append(float((new.float() - W.float()).norm() / W.float().norm()))
                ts[k] = new
                changed += 1
        save_file(ts, os.path.join(a.out, shard), metadata={"format": "pt"})
        del ts
    assert changed == len(deltas), f"merged {changed} of {len(deltas)}"
    for f in os.listdir(src):
        if not f.endswith(".safetensors"):
            pth = os.path.join(src, f)
            if os.path.isfile(pth):
                shutil.copy(os.path.realpath(pth), os.path.join(a.out, f))
    rec.update({"merged": changed, "relative_change_mean": sum(rel) / len(rel), "relative_change_max": max(rel)})
    json.dump(rec, open(os.path.join(a.out, "genft-merge.json"), "w"), indent=1)
    print("merged", json.dumps(rec), flush=True)


def post(path, body):
    import urllib.request
    req = urllib.request.Request("http://127.0.0.1:8000" + path, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + os.environ.get("CTL_TOKEN", "")})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())


def cmd_template_check(a):
    cs = cases_mod.load(a.corpus)
    byid = {c["id"]: c for c in cs}
    sp = json.load(open(a.split))
    prompt = prompting.load_prompt(PROMPT)
    tok = tokenizer()
    ids = random.Random(11).sample(sorted(sp["train"]), 20)
    same = 0
    for i in ids:
        p, _ = encode(tok, prompt, byid[i])
        got = post("/tokenize", {"model": a.served, "messages": messages(byid[i], prompt), "add_generation_prompt": True})
        if got.get("tokens") == p:
            same += 1
        else:
            g = got.get("tokens") or []
            k = next((j for j in range(min(len(g), len(p))) if g[j] != p[j]), min(len(g), len(p)))
            print(f"{i}: differs at token {k} (served {len(g)} tokens, training {len(p)}): "
                  f"served {tok.decode(g[max(0, k - 5):k + 5])!r} training {tok.decode(p[max(0, k - 5):k + 5])!r}")
    res = {"checked": len(ids), "identical": same, "passes": same == len(ids)}
    json.dump(res, open(a.out, "w"), indent=1)
    print("TEMPLATE CHECK", "PASSES" if res["passes"] else "FAILS", res, flush=True)
    if not res["passes"]:
        sys.exit(2)


def cmd_merge_check(a):
    st = json.load(open(a.stats))
    cs = cases_mod.load(a.corpus)
    byid = {c["id"]: c for c in cs}
    prompt = prompting.load_prompt(PROMPT)
    agree = off = 0
    rows = []
    for i, g in st["check_grades"].items():
        r = post("/v1/chat/completions", {"model": a.served, "messages": messages(byid[i], prompt), "temperature": 0,
                                          "max_tokens": 32})
        txt = r["choices"][0]["message"]["content"] or ""
        s = prompting.parse_score(txt, 1, 6)
        if s is None:
            m = __import__("re").search(r'"score":\s*(\d)', txt)
            s = float(m.group(1)) if m else None
        try:
            gi = float(g.strip())
        except ValueError:
            gi = None
        agree += s is not None and gi is not None and s == gi
        off += s is None or gi is None or abs(s - gi) > 1
        rows.append((g, s))
    n = len(rows)
    res = {"n": n, "agree": agree, "more_than_one_point_or_unreadable": off,
           "passes": agree >= math.ceil(0.95 * n) and off == 0, "served": a.served}
    json.dump(res, open(a.out, "w"), indent=1)
    print("MERGE CHECK", "PASSES" if res["passes"] else "FAILS", res, flush=True)
    if not res["passes"]:
        sys.exit(3)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("train")
    p.add_argument("--corpus", required=True); p.add_argument("--split", required=True)
    p.add_argument("--fold", required=True); p.add_argument("--adapter", required=True); p.add_argument("--stats", required=True)
    p.add_argument("--deadline", type=float); p.add_argument("--limit", type=int)
    p.set_defaults(fn=cmd_train)
    p = sub.add_parser("merge"); p.add_argument("--adapter", required=True); p.add_argument("--out")
    p.add_argument("--dry", action="store_true"); p.set_defaults(fn=cmd_merge)
    p = sub.add_parser("template-check")
    p.add_argument("--corpus", required=True); p.add_argument("--split", required=True); p.add_argument("--served", required=True)
    p.add_argument("--out", required=True); p.set_defaults(fn=cmd_template_check)
    p = sub.add_parser("merge-check")
    p.add_argument("--corpus", required=True); p.add_argument("--stats", required=True); p.add_argument("--served", required=True)
    p.add_argument("--out", required=True); p.set_defaults(fn=cmd_merge_check)
    a = ap.parse_args()
    try:
        a.fn(a)
    except OverDeadline as e:
        print("NOT RUN:", e, flush=True)
        sys.exit(4)


if __name__ == "__main__":
    main()
