#!/usr/bin/env python3
"""Is the shared disability gap a measurement artifact, and do essay length and convention errors carry it?
PRE-REGISTERED 2026-10-27, before any result of this design was computed.

WHY. On 3,000 ASAP 2.0 essays matched on the human mark (disability/gap.py), 20 of the 22 board models mark essays
by students identified with a disability lower than essays by other students with the same human mark (SHARED
GAP). Two readings remain open (literature review, analysis 5: research/readiness/ai-grading-benchmark-2026/
literature.md, entries 5.2, 5.3 and Kucia et al. 2026):
1. Measurement error (Johnson, Liu and McCaffrey 2022; the reverse-regression argument of Conway and Roberts
   1983). The identified group writes lower-scoring essays on average. When the human mark measures quality with
   error, essays from the lower-scoring group that share a human mark with others are, on average, a little
   weaker, so an unbiased grader marks them lower too. A gap at equal human marks then needs no bias in the model.
   The test: at equal MACHINE marks, do the identified essays get HIGHER human marks (the model under-marks them
   relative to the humans: the gap survives) or LOWER (both measures agree the group's essays are weaker: the
   gap is what measurement error would produce)?
2. Surface features (Buzick et al. 2016; Kucia et al. 2026). If the models are harsher than the human raters on
   length or on spelling and capitalization, and the identified group writes shorter essays with more such
   errors at the same human mark, those features carry the gap.

DATA. Reanalysis only: no calls. ASAP 2.0 (CC BY 4.0; `asap2` in data/data-sources.json; read from the local
corpus, nothing committed but aggregates): the 3,000 matched essays of disability/gap.py (1,500 identified, a
random sample of that group; 1,500 not identified, drawn to the identified group's human-mark distribution), and
the whole corpus's human-mark distribution by group (for the weights below). Model marks: the 22 default-prompt
runs of disability/gap.py (one per board model). Only the adjudicated mark is released, so "human mark" is that.

MEASURES.
(A) REVERSE REGRESSION, per model. Weighted least squares of the human mark on indicators of the machine mark
    (one per mark 1-6) and a group indicator (identified = 1). Weights undo the matching so both groups are
    representative of their populations: identified essays weight 1; not-identified essays weight
    p_N(h) / p_I(h), the corpus share of mark h among not-identified essays over that among identified essays.
    C = the group coefficient: identified minus not, in human-mark points, at equal machine marks. Signed:
    POSITIVE = at the same machine mark the humans gave the identified essays more, so the model marks them lower
    than the humans do. Interval: 2,000 bootstrap draws (seed 7) resampling essays within each group.
(B) SURFACE FEATURES, per model whose gap.py verdict is GAP REPLICATES. Two features per essay, computed by fixed
    rules (rule-coded proxies, NOT validated constructs; no person or model coded them):
    - LENGTH: log(1 + words), words = whitespace-separated tokens;
    - CONVENTION ERRORS per 100 words = misspellings + lowercase standalone "i" + sentences opening in lowercase.
      A misspelling is an alphabetic token (lowercased, apostrophes kept) that pyspellchecker 0.8.1's English
      dictionary does not know (wheel sha256 d91e9e10...b640) and that does not occur in the assignment's own
      prompt or source texts (so names such as "Bomberger" are not errors). A sentence opening is the first
      letter after ". ", "! " or "? " (one or more spaces or a newline).
    Ordinary least squares on the matched sample (as gap.py), of the machine mark on indicators of the human
    mark and the group indicator: B0, the gap. The same with both features added: B1. SHARE = (B0 - B1) / B0,
    the part of the gap the two features account for. Signed: positive = the features account for part of the
    gap. Interval as in (A), the same draws. Descriptive: the groups' mean features at matched marks, and each
    feature's coefficient per model (negative = the model gives less to more of it at the same human mark).

VERDICTS.
(A) per model:
  GAP SURVIVES REVERSE REGRESSION        C's interval above 0
  GAP CONSISTENT WITH MEASUREMENT ERROR  C's interval below 0
  REVERSE REGRESSION INCONCLUSIVE        C's interval contains 0
(B) per model with a replicated gap:
  SURFACE FEATURES ACCOUNT FOR MOST OF THE GAP   SHARE's interval above 0.5
  SURFACE FEATURES ACCOUNT FOR PART OF THE GAP   SHARE's interval above 0, not above 0.5
  SURFACE FEATURES DO NOT ACCOUNT FOR THE GAP    SHARE's interval contains 0 (its upper end reported)
  GAP WIDER AT EQUAL SURFACE FEATURES            SHARE's interval below 0
Either part reads UNMEASURED if its floor fails.

FLOOR (`floor`, before `analyse`; it reads the essays' texts, groups and human marks, never a model mark).
(A) A latent quality T per essay, normal within each group with the group's corpus mean and a variance such that
    a human mark H = round(T + N(0, 0.4)) clipped to 1-6 reproduces the group's corpus mean and SD (reliability
    about 0.85, near the adjudicated mark's). A model mark M = round(T + N(0, 0.875) + delta * identified),
    clipped (0.875 = the model residual SD gap.py's floor used). A population of 20,000 per group is simulated,
    the matched sample drawn by gap.py's rule (1,500 identified at random; 1,500 not identified matched on H),
    and C estimated with the weights above and a normal interval from the weighted sandwich standard error (the
    real analysis keeps the bootstrap). 200 simulations each. Null: delta = 0 (a gap from measurement error
    alone) must read GAP SURVIVES in at most 5%. Planted: delta = -0.30 (a model bias of -0.30 marks, the size
    of the observed gaps) must read GAP SURVIVES in at least 80%. Detection at delta = -0.50 is reported, not
    used for the pass.
(B) On the real 3,000 essays, their real features and human marks: M = round(H + N(0, 0.875) + k * z), clipped,
    z = the convention-error rate standardized over the 3,000; k is set so that, through the groups' real
    difference in z at matched marks, the expected gap is -0.25. Planted world: that alone (the gap is carried
    entirely by conventions) must read MOST in at least 80%. Null world: M = round(H + N(0, 0.875) - 0.25 *
    identified), the features unused, must read MOST or PART in at most 5%. 200 simulations each, normal-
    approximation intervals for SHARE by the delta method from the two OLS fits (the real analysis keeps the
    bootstrap). If the real difference in z at matched marks is too small to carry a -0.25 gap with |k| <= 1.5
    marks per SD, (B)'s floor fails by design: the features could not carry the gap.
The planted sizes are not changed after the floor runs.

LIMITS stated in advance: one released mark per essay (the adjudicated one), so the measurement-error test uses
the corpus reliability only through the simulation; the features are proxies; the weights assume the matched
not-identified essays are a random draw within each mark (true of gap.py's draw); 22 models on one corpus.

BUDGET. No calls.

CHANGES:

Usage:
    python3 disability-mechanism/study.py floor --matched <disability-matched.jsonl> --corpus <asap2.jsonl>
    python3 disability-mechanism/study.py analyse --matched <...> --corpus <...> --runs <gap.py run dirs>
"""

import argparse
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

OUT = os.path.join(HERE, "out")
IDENT, NOT = "Identified as having disability", "Not identified as having disability"
B, SEED = 2000, 7
WORD = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
OPEN_LOWER = re.compile(r"[.!?]\s+([a-z])")


def load(path):
    return [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]


def corpus_shares(corpus):
    counts = {IDENT: np.zeros(7), NOT: np.zeros(7)}
    for c in load(corpus):
        g = c.get("groups", {}).get("disability")
        if g in counts:
            counts[g][int(c["human"]["rater"])] += 1
    return {g: v / v.sum() for g, v in counts.items()}, counts


def features(cs):
    from spellchecker import SpellChecker
    sp = SpellChecker(language="en")
    vocab = {}
    out = []
    for c in cs:
        if c["task"] not in vocab:
            vocab[c["task"]] = {w.lower() for w in WORD.findall(" ".join([c.get("question") or "", c.get("materials") or ""]))}
        text = c["response"]
        words = len(text.split())
        toks = [w.lower() for w in WORD.findall(text)]
        cand = {w for w in toks if w not in vocab[c["task"]]}
        unknown = sp.unknown(cand)
        miss = sum(1 for w in toks if w in unknown)
        low_i = sum(1 for w in WORD.findall(text) if w == "i")
        opens = len(OPEN_LOWER.findall(text))
        out.append({"words": words, "log_words": math.log1p(words),
                    "conv_per100": 100 * (miss + low_i + opens) / max(1, words),
                    "miss_per100": 100 * miss / max(1, words)})
    return out


def design_forward(H, g, X=None):
    cols = [np.ones_like(H)] + [(H == h).astype(float) for h in range(2, 7)] + [g]
    if X is not None:
        cols += list(X.T)
    return np.column_stack(cols)


def design_reverse(M, g):
    return np.column_stack([np.ones_like(M)] + [(M == m).astype(float) for m in range(2, 7)] + [g])


def wls(X, y, w):
    Xw = X * w[:, None]
    beta, *_ = np.linalg.lstsq(Xw.T @ X, Xw.T @ y, rcond=None)
    return beta


def sandwich_se(X, y, w, beta, col):
    r = y - X @ beta
    XtWX = (X * w[:, None]).T @ X
    try:
        inv = np.linalg.pinv(XtWX)
    except np.linalg.LinAlgError:
        return float("nan")
    meat = (X * (w * r)[:, None]).T @ (X * (w * r)[:, None])
    V = inv @ meat @ inv
    return math.sqrt(max(V[col, col], 0))


def weights(groups, H, shares):
    return np.array([1.0 if g == 1 else shares[NOT][int(h)] / shares[IDENT][int(h)] for g, h in zip(groups, H)])


def verdict_a(lo, hi):
    return "GAP SURVIVES REVERSE REGRESSION" if lo > 0 else "GAP CONSISTENT WITH MEASUREMENT ERROR" if hi < 0 else "REVERSE REGRESSION INCONCLUSIVE"


def verdict_b(lo, hi):
    if lo > 0.5:
        return "SURFACE FEATURES ACCOUNT FOR MOST OF THE GAP"
    if lo > 0:
        return "SURFACE FEATURES ACCOUNT FOR PART OF THE GAP"
    if hi < 0:
        return "GAP WIDER AT EQUAL SURFACE FEATURES"
    return "SURFACE FEATURES DO NOT ACCOUNT FOR THE GAP"


def rnd(x):
    return np.clip(np.floor(x + 0.5), 1, 6)


def cmd_floor(a):
    shares, counts = corpus_shares(a.corpus)
    marks = np.arange(7)
    stats = {}
    for g in (IDENT, NOT):
        p = shares[g]
        m = (p * marks).sum()
        v = (p * (marks - m) ** 2).sum()
        stats[g] = (m, math.sqrt(max(v - 0.4 ** 2 - 1 / 12, 0.05)))  # rounding adds about 1/12
    rng = np.random.default_rng(SEED)
    res = {"A": {}, "B": {}}
    sims = 200
    for name, delta in (("null", 0.0), ("planted", -0.30), ("reported_-0.50", -0.50)):
        hits = 0
        for _ in range(sims):
            pop = {}
            for gi, g in ((1, IDENT), (0, NOT)):
                T = rng.normal(stats[g][0], stats[g][1], 20000)
                H = rnd(T + rng.normal(0, 0.4, T.size))
                M = rnd(T + rng.normal(0, 0.875, T.size) + delta * gi)
                pop[gi] = (H, M)
            Hi, Mi = pop[1]
            pick = rng.choice(Hi.size, 1500, replace=False)
            Hs, Ms, gs = [Hi[pick]], [Mi[pick]], [np.ones(1500)]
            Hn, Mn = pop[0]
            for h in range(1, 7):
                k = int((Hi[pick] == h).sum())
                pool = np.where(Hn == h)[0]
                if k:
                    sel = rng.choice(pool, k, replace=pool.size < k)
                    Hs.append(Hn[sel]); Ms.append(Mn[sel]); gs.append(np.zeros(k))
            H, M, gg = np.concatenate(Hs), np.concatenate(Ms), np.concatenate(gs)
            sim_shares = {IDENT: np.bincount(Hi.astype(int), minlength=7) / Hi.size,
                          NOT: np.bincount(Hn.astype(int), minlength=7) / Hn.size}
            w = np.array([1.0 if gi == 1 else sim_shares[NOT][int(h)] / max(sim_shares[IDENT][int(h)], 1e-9) for gi, h in zip(gg, H)])
            X = design_reverse(M, gg)
            beta = wls(X, H, w)
            se = sandwich_se(X, H, w, beta, 6)
            hits += verdict_a(beta[6] - 1.96 * se, beta[6] + 1.96 * se) == "GAP SURVIVES REVERSE REGRESSION"
        res["A"][name] = hits / sims
    res["A"]["passes"] = res["A"]["null"] <= 0.05 and res["A"]["planted"] >= 0.80
    print("A", res["A"], flush=True)

    cs = load(a.matched)
    f = features(cs)
    H = np.array([c["human"]["rater"] for c in cs], dtype=float)
    gg = np.array([1.0 if c["groups"]["disability"] == IDENT else 0.0 for c in cs])
    X2 = np.column_stack([[x["log_words"] for x in f], [x["conv_per100"] for x in f]])
    z = (X2[:, 1] - X2[:, 1].mean()) / X2[:, 1].std()
    # the groups' difference in z at matched marks
    dz = float(np.linalg.lstsq(design_forward(H, gg), z, rcond=None)[0][6])
    k = -0.25 / dz if dz != 0 else float("inf")
    res["B"]["z_gap_at_matched_marks"] = dz
    res["B"]["k"] = k
    if not abs(k) <= 1.5:
        res["B"].update(planted=0.0, null=None, passes=False, note="the convention-error difference at matched marks is too small to carry a -0.25 gap")
    else:
        for name in ("planted", "null"):
            hits = 0
            for _ in range(sims):
                e = rng.normal(0, 0.875, H.size)
                M = rnd(H + e + k * z) if name == "planted" else rnd(H + e - 0.25 * gg)
                X0, X1 = design_forward(H, gg), design_forward(H, gg, X2)
                b0, b1 = np.linalg.lstsq(X0, M, rcond=None)[0], np.linalg.lstsq(X1, M, rcond=None)[0]
                share = (b0[6] - b1[6]) / b0[6]
                # delta method on (b0, b1) with a paired sandwich via stacked residual influence
                r0, r1 = M - X0 @ b0, M - X1 @ b1
                i0 = (np.linalg.pinv(X0.T @ X0) @ (X0 * r0[:, None]).T)[6]
                i1 = (np.linalg.pinv(X1.T @ X1) @ (X1 * r1[:, None]).T)[6]
                infl = (i0 - i1) / b0[6] - (b0[6] - b1[6]) * i0 / b0[6] ** 2
                se = math.sqrt((infl ** 2).sum())
                v = verdict_b(share - 1.96 * se, share + 1.96 * se)
                hits += (v == "SURFACE FEATURES ACCOUNT FOR MOST OF THE GAP") if name == "planted" else (
                    v in ("SURFACE FEATURES ACCOUNT FOR MOST OF THE GAP", "SURFACE FEATURES ACCOUNT FOR PART OF THE GAP"))
            res["B"][name] = hits / sims
        res["B"]["passes"] = res["B"]["planted"] >= 0.80 and res["B"]["null"] <= 0.05
    print("B", res["B"])
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "floor.json"), "w"), indent=1)


def cmd_analyse(a):
    floor = json.load(open(os.path.join(OUT, "floor.json")))
    gap = json.load(open(os.path.join(ROOT, "disability", "out", "result.json")))
    shares, _ = corpus_shares(a.corpus)
    cs = load(a.matched)
    ids = [c["id"] for c in cs]
    pos = {i: j for j, i in enumerate(ids)}
    f = features(cs)
    H = np.array([c["human"]["rater"] for c in cs], dtype=float)
    gg = np.array([1.0 if c["groups"]["disability"] == IDENT else 0.0 for c in cs])
    X2 = np.column_stack([[x["log_words"] for x in f], [x["conv_per100"] for x in f]])
    w = weights(gg, H, shares)
    rng = np.random.default_rng(SEED)
    gi, gn = np.where(gg == 1)[0], np.where(gg == 0)[0]
    draws = [np.concatenate([rng.choice(gi, gi.size), rng.choice(gn, gn.size)]) for _ in range(B)]
    desc = {"features_by_group": {}}
    for name, col in (("words", [x["words"] for x in f]), ("conv_per100", X2[:, 1]), ("miss_per100", [x["miss_per100"] for x in f])):
        col = np.asarray(col, dtype=float)
        desc["features_by_group"][name] = {"identified": float(col[gg == 1].mean()), "not": float(col[gg == 0].mean()),
                                           "difference_at_matched_marks": float(np.linalg.lstsq(design_forward(H, gg), col, rcond=None)[0][6])}
    res = {"design": "disability-mechanism/study.py docstring", "floor": floor, "descriptive": desc, "models": {}}
    for run in a.runs:
        cfg = json.load(open(os.path.join(run, "config.json")))
        if cfg["prompt"] != "default.txt":
            continue
        M = np.full(len(cs), np.nan)
        for r in map(json.loads, open(os.path.join(run, "calls.jsonl"))):
            if r["probe"] == "base" and r["id"] in pos and r.get("score") is not None:
                M[pos[r["id"]]] = r["score"]
        ok = ~np.isnan(M)
        Mr = np.clip(np.floor(M + 0.5), 1, 6)

        def rev(ix):
            ix = ix[ok[ix]]
            return wls(design_reverse(Mr[ix], gg[ix]), H[ix], w[ix])[6]

        def fwd(ix):
            ix = ix[ok[ix]]
            b0 = np.linalg.lstsq(design_forward(H[ix], gg[ix]), M[ix], rcond=None)[0]
            b1 = np.linalg.lstsq(design_forward(H[ix], gg[ix], X2[ix]), M[ix], rcond=None)[0]
            return b0[6], b1[6], b1[7], b1[8]
        all_ix = np.arange(len(cs))
        c_pt = rev(all_ix)
        c_d = np.array([rev(d) for d in draws])
        f_pt = fwd(all_ix)
        f_d = np.array([fwd(d) for d in draws])
        sh_pt = (f_pt[0] - f_pt[1]) / f_pt[0]
        sh_d = (f_d[:, 0] - f_d[:, 1]) / f_d[:, 0]
        clo, chi = np.percentile(c_d, [2.5, 97.5])
        slo, shi = np.percentile(sh_d, [2.5, 97.5])
        key = f"{cfg['model']} / {cfg['prompt']}"
        gv = (gap.get(key) or {}).get("verdict")
        row = {"model": cfg["model"], "graded": int(ok.sum()), "gap_verdict": gv,
               "reverse_C": {"estimate": float(c_pt), "ci95": [float(clo), float(chi)]},
               "verdict_A": verdict_a(clo, chi) if floor["A"]["passes"] else "UNMEASURED",
               "gap_B0": {"estimate": float(f_pt[0]), "ci95": [float(x) for x in np.percentile(f_d[:, 0], [2.5, 97.5])]},
               "gap_B1": {"estimate": float(f_pt[1]), "ci95": [float(x) for x in np.percentile(f_d[:, 1], [2.5, 97.5])]},
               "coef_log_words": {"estimate": float(f_pt[2]), "ci95": [float(x) for x in np.percentile(f_d[:, 2], [2.5, 97.5])]},
               "coef_conv_per100": {"estimate": float(f_pt[3]), "ci95": [float(x) for x in np.percentile(f_d[:, 3], [2.5, 97.5])]},
               "share": {"estimate": float(sh_pt), "ci95": [float(slo), float(shi)]},
               "verdict_B": (verdict_b(slo, shi) if floor["B"]["passes"] else "UNMEASURED") if gv == "GAP REPLICATES" else "not tested (no replicated gap)"}
        res["models"][cfg["model"]] = row
        print(f"{cfg['model'][:30]:30s} C {c_pt:+.3f} [{clo:+.3f}, {chi:+.3f}] {row['verdict_A']} | gap {f_pt[0]:+.3f} -> {f_pt[1]:+.3f}, "
              f"share {sh_pt:+.2f} [{slo:+.2f}, {shi:+.2f}] {row['verdict_B']}", flush=True)
    json.dump(res, open(os.path.join(OUT, "mechanism.json"), "w"), indent=1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("floor"); p.add_argument("--matched", required=True); p.add_argument("--corpus", required=True); p.set_defaults(fn=cmd_floor)
    p = sub.add_parser("analyse"); p.add_argument("--matched", required=True); p.add_argument("--corpus", required=True)
    p.add_argument("--runs", nargs="+", required=True); p.set_defaults(fn=cmd_analyse)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
