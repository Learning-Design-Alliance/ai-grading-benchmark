#!/usr/bin/env python3
"""Non-LLM baselines on the leaderboard's tasks: how far does classic automated scoring get, and how does it
behave under the same probes? PRE-REGISTERED 2026-10-25, before any baseline was scored on the test cases.

WHY. A buyer weighing an LLM grader should see what a cheap, deterministic method does on the same cases,
including the probes. Classic automated scoring is trained per item on human marks; an LLM is not. The
comparison is a reference, not a ranking: baselines are shown beside the leaderboard, never in it.

BASELINES (scikit-learn; every one trained only on the corpus's cases OUTSIDE the canonical 100-case draw,
target = the mean human mark; predictions rounded and clipped to the scale):
- **length**: linear regression on log(1 + words) (code: log(1 + characters)).
- **tfidf-ridge**: TF-IDF of word 1-2 grams (code: character 3-5 grams), min_df 2, sublinear tf, Ridge (alpha 1).
  For short answers the question text is prefixed to the answer, so the model can learn per-question patterns,
  as item-specific ASAG systems do.
- **reference-similarity** (short answers and code, which have a reference answer): cosine similarity between
  the answer's and the reference's TF-IDF vectors, mapped to the scale by linear regression.
The maths task's baseline is the answer checker in maths-process/ (already reported). Pushback is not run: a
deterministic grader never changes its mark, so its effect is 0 by construction.

PROBES. Exactly the leaderboard battery's probes and cases (bench.plan), each probe's altered answer scored by
the baseline. A baseline ignores the learner label and is deterministic, so the label effect and retest are
reported as 0 and 1 by construction and marked as such. Scored with report.py and leaderboard.row, like a
submission; also the agreement on the 100 cases.

EXPECTED (written before scoring, to be checked, not a verdict): length and tf-idf reach a large share of the
human ceiling on essays (length is a known strong predictor of essay scores); the blank answers get the
lowest marks; padding-like probes (forged note, the request appended) RAISE the length baseline's mark, since
they add words. Code has only 29 training cases, so its baselines are expected to be weak.

CHANGE 1 (2026-10-25, before this baseline was scored): a small pretrained encoder.
- **encoder-ridge**: sentence embeddings from all-MiniLM-L6-v2 (22M parameters, Apache 2.0, revision
  1110a243fdf4706b3f48f1d95db1a4f5529b4d41), normalised, then Ridge (alpha 1) on the mean human mark. The
  same text as tfidf-ridge (question prefixed for short answers). The encoder reads at most 256 word pieces,
  so long essays are truncated, which is stated beside the result. It is the "small model" tier between the
  classic baselines and the smallest language models on the board, and runs on a laptop CPU.
Expected (written before scoring): close to tfidf-ridge on essays and short answers; weak on code (29
training cases); blank answers credited as by the others, since a regression has no floor.
Run with `--kinds encoder-ridge` to add its rows to an existing output.

CHANGE 2 (2026-10-25, before this baseline was trained or scored): a fine-tuned encoder.
- **deberta-ft**: DeBERTa-v3-base (microsoft/deberta-v3-base, revision 8ccc9b6f36199bec6961081d44eb72fb3f7353f3,
  184M parameters, MIT), fine-tuned per task with a one-output regression head (mean squared error) on the mean
  human mark rescaled to 0-1, on the same training cases as the others (outside the canonical 100) and the same
  text as tfidf-ridge (question prefixed for short answers). Inputs truncated to 512 word pieces, which cuts
  long essays and code; the share truncated is reported. Fixed settings, no tuning and no validation split
  (nothing is chosen on any result): AdamW, learning rate 2e-5, weight decay 0.01, batch 16, linear decay
  after 10% warm-up, bf16, seed 7; 3 epochs for short answers and essays, 30 for code (29 training cases, so 3
  epochs would be 6 steps). Predictions are rescaled, rounded and clipped to the scale, then scored under the
  same probes as the others. Trained on one rented GPU (gpu/pod.py), not a laptop.
  It is the classic strong automated-scoring baseline: item-trained, like tfidf-ridge, with a pretrained reader.
Expected (written before training): above tfidf-ridge and encoder-ridge on essays and short answers (fine-
tuned encoders lead the ASAP-style benchmarks); weak on code; blank answers credited, since a regression has no
floor; and, unlike length, no reliable gain from the padding probes. Run with `--kinds deberta-ft`.

    python3 baselines/baselines.py --cases-dir <dir with mohler.jsonl, harmogen-code.jsonl, asap2.jsonl> --out out/baselines.json

Reads the corpora's cases (aggregates out only).
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import bench  # noqa: E402
import cases as cases_mod  # noqa: E402
import leaderboard as lb  # noqa: E402
import prompting  # noqa: E402
import report as report_mod  # noqa: E402

FILES = {"mohler": "mohler.jsonl", "code": "harmogen-code.jsonl", "asap2": "asap2.jsonl"}


def target(c):
    return sum(c["human"].values()) / len(c["human"])


def text_of(task, c, response):
    return (c.get("question", "") + " || " + response) if task == "mohler" else response


def fit(task, train, kind):
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LinearRegression, Ridge
    y = np.array([target(c) for c in train])
    if kind == "length":
        f = (lambda r: math.log1p(len(r))) if task == "code" else (lambda r: math.log1p(len(r.split())))
        m = LinearRegression().fit(np.array([[f(c["response"])] for c in train]), y)
        return lambda c, r: float(m.predict(np.array([[f(r)]]))[0])
    if kind == "tfidf-ridge":
        vec = (TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True) if task == "code"
               else TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, max_features=50000))
        X = vec.fit_transform([text_of(task, c, c["response"]) for c in train])
        m = Ridge(alpha=1.0).fit(X, y)
        return lambda c, r: float(m.predict(vec.transform([text_of(task, c, r)]))[0])
    if kind == "reference-similarity":
        from sklearn.metrics.pairwise import cosine_similarity
        vec = (TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True) if task == "code"
               else TfidfVectorizer(sublinear_tf=True))
        vec.fit([c["response"] for c in train] + [c.get("reference", "") for c in train])
        sim = lambda c, r: float(cosine_similarity(vec.transform([r or ""]), vec.transform([c.get("reference", "") or ""]))[0, 0])
        m = LinearRegression().fit(np.array([[sim(c, c["response"])] for c in train]), y)
        return lambda c, r: float(m.predict(np.array([[sim(c, r)]]))[0])
    if kind == "encoder-ridge":
        enc = encoder()
        emb = lambda texts: enc.encode(texts, batch_size=64, normalize_embeddings=True, show_progress_bar=False)
        m = Ridge(alpha=1.0).fit(emb([text_of(task, c, c["response"]) for c in train]), y)
        cache = {}

        def pred(c, r):
            k = text_of(task, c, r)
            if k not in cache:
                cache[k] = float(m.predict(emb([k]))[0])
            return cache[k]
        return pred
    if kind == "deberta-ft":
        return deberta(task, train)
    raise ValueError(kind)


DEBERTA = ("microsoft/deberta-v3-base", "8ccc9b6f36199bec6961081d44eb72fb3f7353f3")
TRUNCATED = {}


def deberta(task, train):
    """CHANGE 2: fine-tune DeBERTa-v3-base on the mean human mark (0-1); returns a predictor on the scale."""
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup
    torch.manual_seed(7)
    random_state = __import__("random").Random(7)
    lo, hi = train[0]["scale"]
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(DEBERTA[0], revision=DEBERTA[1])
    model = AutoModelForSequenceClassification.from_pretrained(DEBERTA[0], revision=DEBERTA[1], num_labels=1).to(dev)
    texts = [text_of(task, c, c["response"]) for c in train]
    ys = [(target(c) - lo) / (hi - lo) for c in train]
    TRUNCATED[task] = sum(len(tok(t)["input_ids"]) > 512 for t in texts) / len(texts)
    epochs, bs = (30 if task == "code" else 3), 16
    steps = epochs * math.ceil(len(texts) / bs)
    opt = torch.optim.AdamW(model.parameters(), lr=2e-5, weight_decay=0.01)
    sched = get_linear_schedule_with_warmup(opt, int(0.1 * steps), steps)
    model.train()
    order = list(range(len(texts)))
    for ep in range(epochs):
        random_state.shuffle(order)
        tot = 0.0
        for i in range(0, len(order), bs):
            idx = order[i:i + bs]
            enc = tok([texts[j] for j in idx], truncation=True, max_length=512, padding=True, return_tensors="pt").to(dev)
            with torch.autocast(dev, dtype=torch.bfloat16, enabled=dev == "cuda"):
                out = model(**enc).logits.squeeze(-1)
            loss = torch.nn.functional.mse_loss(out.float(), torch.tensor([ys[j] for j in idx], device=dev))
            loss.backward()
            opt.step()
            sched.step()
            opt.zero_grad()
            tot += loss.item() * len(idx)
        print(f"  deberta-ft {task} epoch {ep + 1}/{epochs} train mse {tot / len(texts):.4f}", flush=True)
    model.eval()
    cache = {}

    def pred(c, r):
        k = text_of(task, c, r)
        if k not in cache:
            with torch.no_grad():
                enc = tok([k], truncation=True, max_length=512, return_tensors="pt").to(dev)
                cache[k] = lo + (hi - lo) * float(model(**enc).logits.squeeze().float())
        return cache[k]
    return pred


_ENC = []


def encoder():
    if not _ENC:
        from sentence_transformers import SentenceTransformer
        _ENC.append(SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2",
                                        revision="1110a243fdf4706b3f48f1d95db1a4f5529b4d41", device="cpu"))
    return _ENC[0]


def run(task, path, kind):
    allc = cases_mod.load(path)
    test = cases_mod.sample(allc, lb.N, lb.SEED)
    test_ids = {c["id"] for c in test}
    train = [c for c in allc if c["id"] not in test_ids]
    pred = fit(task, train, kind)
    lo, hi = test[0]["scale"]
    prompt = prompting.load_prompt(lb.DEFAULT_PROMPT)
    jobs, ran = bench.plan(test, allc, prompt, list(lb.battery()["probes"]), lb.SEED)
    calls = []
    for c, p, _ in jobs:
        got = prompting.probe_input(c, p, None, lb.SEED)
        resp = got[0] if got else c["response"]
        s = max(lo, min(hi, round(pred(c, resp or ""))))
        calls.append({"id": c["id"], "task": c["task"], "probe": p, "score": float(s), "text": None, "error": None,
                      "usage": {}, "finish_reason": "stop", "served_model": f"baseline:{kind}", "provider": "local"})
    rep = report_mod.build(test, calls)
    sub = {"model": f"baseline: {kind}", "task": task, "track": "baseline", "submitter": "benchmark maintainers",
           "calls": calls, "benchmark_version": None}
    row = lb.row(sub, rep)
    row["n_train"] = len(train)
    if kind in ("deberta-ft",):
        row["truncated_share_train"] = TRUNCATED.get(task)
        row["model_revision"] = "/".join(DEBERTA)
    row["by_construction"] = ["attainment label effect is 0 (the baseline never sees the label)",
                              "retest agreement is 1 (deterministic)"]
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases-dir", required=True)
    ap.add_argument("--out", default=os.path.join(ROOT, "out", "baselines.json"))
    ap.add_argument("--kinds", nargs="+", help="only these baselines, added to the existing output")
    a = ap.parse_args()
    rows = []
    if a.kinds and os.path.exists(a.out):
        rows = [r for r in json.load(open(a.out))["rows"] if r["model"].replace("baseline: ", "") not in a.kinds]
    for task, fn in FILES.items():
        kinds = ["length", "tfidf-ridge"] + (["reference-similarity"] if task in ("mohler", "code") else []) + ["encoder-ridge", "deberta-ft"]
        kinds = [k for k in kinds if not a.kinds or k in a.kinds]
        for kind in kinds:
            r = run(task, os.path.join(a.cases_dir, fn), kind)
            rows.append(r)
            g = (r.get("gaming_max_share") or {}).get("estimate")
            sh = (r.get("share_of_ceiling") or {}).get("estimate")
            print(f"{task:7s} {kind:21s} qwk {r['qwk']['estimate']:.3f}  share {'—' if sh is None else f'{sh:.2f}'}  "
                  f"published {'—' if r['share_of_published_ceiling'] is None else round(r['share_of_published_ceiling'], 2)}  "
                  f"blank {r['blank_credited']}  gaming {'—' if g is None else f'{100 * g:+.1f}%'}  train {r['n_train']}", flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump({"design": "baselines/baselines.py docstring", "rows": rows}, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
