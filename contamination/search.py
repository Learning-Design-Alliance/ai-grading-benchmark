#!/usr/bin/env python3
"""Are the benchmark's student texts in open training data? A direct search of two published training sets.
PRE-REGISTERED 2026-10-25, before any query of the benchmark's texts.

WHY. Every corpus here is public, so a model may have seen the answers, and even the marks, in training.
For closed models this cannot be checked. Two open training sets can be searched exactly with infini-gram
(Liu et al. 2024; api.infini-gram.io):
- `v4_olmo-2-0325-32b-instruct_llama`: everything OLMo 2 32B Instruct was trained on (pre-training,
  mid-training and post-training data, about 4.6 trillion tokens). No index of Olmo 3's data is offered.
- `v4_dclm-baseline_llama`: DCLM-baseline, about 4 trillion tokens of filtered Common Crawl that many
  open models train on.
A hit shows that the text is in that training set, and so is in the public web data models are built from.
A miss in these two does not clear a closed model, which may train on more.

UNITS. Exactly the cases the board grades: the 100 leaderboard cases of each of short answers (Mohler),
essays (ASAP 2.0) and code (HARMOGEN-R), and the 200 maths problems' "wrong" versions (VtG's student-like
solutions as written; the other versions are rearrangements of the same text).

SPANS. 13 consecutive words, the overlap length GPT-3's contamination analysis used (Brown et al. 2020).
From each case's response text, two spans at positions drawn at random (seed 7), each taken as the exact
characters of 13 whitespace-separated words within one line. A response with fewer than 13 words on any
line is not eligible, and the count of eligible cases is reported. A case is FOUND if either span occurs
at least once in the index.

CONTROLS (the floor, run before the benchmark's texts are queried, in the same session):
- POSITIVE: 40 spans of 13 words copied from documents the index itself returns (`get_doc_by_rank` on a
  common phrase, ranks drawn at random). They are in the index by construction, so this tests the query
  pipeline, the tokenizer and span cutting. Must be found in at least 90%.
- NEGATIVE: 40 spans of 13 words from this repository's own documents written in October 2026, after both
  training sets were collected (2024), so they cannot be in them. Tests chance collisions of ordinary
  English. Must be found in at most 5%.
If either control fails, the result is reported as UNMEASURED, not as found or not found.

STATISTIC AND VERDICTS (per corpus and index): the share of eligible cases FOUND, with a Wilson 95% interval.
  IN THE TRAINING DATA   the interval's lower bound exceeds the negative control's observed rate and is
                         at least 5%
  NOT DETECTED           otherwise; the upper bound is reported as the largest share not ruled out
Also the question texts (prompts), reported descriptively: a public question is expected to be on the web.

    python3 contamination/search.py --cases-dir <dir> --out contamination/out/search.json

Sends only 13-word spans of public corpora to a public search API; no credentials. Writes aggregates and
the hit counts, never the spans' text for corpora whose licence restricts redistribution (none here are
restricted; spans are still not written, only counts).
"""
import argparse
import glob
import json
import math
import os
import random
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import cases as cases_mod  # noqa: E402
import leaderboard as lb  # noqa: E402

API = "https://api.infini-gram.io/"
INDEXES = ("v4_olmo-2-0325-32b-instruct_llama", "v4_dclm-baseline_llama")
SPAN, PER_CASE, SEED = 13, 2, 7
FILES = {"mohler": "mohler.jsonl", "asap2": "asap2.jsonl", "code": "harmogen-code.jsonl", "maths": "vtg-cells.jsonl"}
NEG_DOCS = ("BENCHMARK-CARD.md", "docs/ENERGY.md", "docs/CORRECTIONS.md", "analyses/README.md", "docs/MODELS.md")


def post(body, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(API, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.loads(r.read().decode())
            if "error" in d:
                raise RuntimeError(d["error"])
            return d
        except Exception:  # noqa: BLE001 - retried, then raised
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))


def count(index, text):
    return post({"index": index, "query_type": "count", "query": text})["count"]


def spans(text, rng, k=PER_CASE):
    """k exact-character spans of SPAN words, each within one line; [] if no line has SPAN words."""
    cands = []
    for line in (text or "").split("\n"):
        ws = list(re.finditer(r"\S+", line))
        for i in range(len(ws) - SPAN + 1):
            cands.append(line[ws[i].start():ws[i + SPAN - 1].end()])
    if not cands:
        return []
    return rng.sample(cands, min(k, len(cands)))


def wilson(k, n):
    if n == 0:
        return None
    p, z = k / n, 1.96
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [max(0.0, c - h), min(1.0, c + h)]


def positive_spans(index, rng, n=40):
    out = []
    probe = "the student"
    d = post({"index": index, "query_type": "find", "query": probe})
    shards = [(s, a, b) for s, (a, b) in enumerate(d["segment_by_shard"]) if b > a]
    while len(out) < n:
        s, a, b = rng.choice(shards)
        doc = post({"index": index, "query_type": "get_doc_by_rank", "query": probe, "s": s, "rank": rng.randrange(a, b),
                    "max_disp_len": 200})
        text = "".join(t for t, _ in doc["spans"]).replace("\xa0", " ")
        sp = spans(text, rng, 1)
        if sp:
            out.append(sp[0])
    return out


def negative_spans(rng, n=40):
    text = "\n".join(open(os.path.join(ROOT, p), encoding="utf-8").read() for p in NEG_DOCS)
    lines = [l for l in text.split("\n") if len(l.split()) >= SPAN and "|" not in l and "http" not in l]
    out = []
    for l in rng.sample(lines, len(lines)):
        sp = spans(l, rng, 1)
        if sp:
            out.append(sp[0])
        if len(out) == n:
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases-dir", required=True)
    ap.add_argument("--out", default=os.path.join(HERE, "out", "search.json"))
    a = ap.parse_args()
    res = {"design": "contamination/search.py docstring", "indexes": {}}
    for index in INDEXES:
        rng = random.Random(SEED)
        pos = positive_spans(index, rng)
        neg = negative_spans(rng)
        pf = sum(count(index, s) > 0 for s in pos) / len(pos)
        nf = sum(count(index, s) > 0 for s in neg) / len(neg)
        ok = pf >= 0.90 and nf <= 0.05
        r = {"floor": {"positive_found": pf, "negative_found": nf, "n": [len(pos), len(neg)], "passes": ok}, "corpora": {}}
        print(f"{index}: floor positive {pf:.0%} negative {nf:.0%} -> {'passes' if ok else 'FAILS'}", flush=True)
        for task, fn in FILES.items():
            allc = cases_mod.load(os.path.join(a.cases_dir, fn))
            if task == "maths":
                cs = [c for c in allc if c["id"].endswith("-wrong")]
            else:
                cs = cases_mod.sample(allc, lb.N, lb.SEED)
            crng = random.Random(f"{SEED}-{task}")
            found = eligible = 0
            qfound = qseen = 0
            seen_q = set()
            for c in cs:
                sp = spans(c["response"], crng)
                if sp:
                    eligible += 1
                    found += any(count(index, s) > 0 for s in sp)
                q = c.get("question") or ""
                if q and q not in seen_q:
                    seen_q.add(q)
                    qs = spans(q, crng, 1)
                    if qs:
                        qseen += 1
                        qfound += count(index, qs[0]) > 0
            iv = wilson(found, eligible)
            share = found / eligible if eligible else None
            if not ok:
                verdict = "UNMEASURED"
            elif iv and iv[0] > nf and iv[0] >= 0.05:
                verdict = "IN THE TRAINING DATA"
            else:
                verdict = "NOT DETECTED"
            r["corpora"][task] = {"cases": len(cs), "eligible": eligible, "found": found, "share": share, "ci95": iv,
                                  "verdict": verdict, "questions": {"eligible": qseen, "found": qfound}}
            print(f"  {task:7s} {found}/{eligible} answers found ({'—' if share is None else f'{share:.0%}'}) {iv and [round(x, 3) for x in iv]} "
                  f"-> {verdict}; questions {qfound}/{qseen}", flush=True)
        res["indexes"][index] = r
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
