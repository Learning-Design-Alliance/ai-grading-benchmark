#!/usr/bin/env python3
"""Does rewording the grading prompt reorder the models? PRE-REGISTERED 2026-10-27, before any result of this design.

WHY. The board ranks 22 models on one prompt. The rewording study (paraphrase/) found 11 of the 22 models
PROMPT-SENSITIVE: rewording moves their marks more than asking again. That is a statement about each model's own
marks. A school choosing between models needs a different answer: would the ORDER of the models survive a
different, equally reasonable wording? Mizrahi et al. 2024 and Sclar et al. 2024 found that single-prompt model
rankings are brittle and that format performance only weakly correlates between models (literature review,
analysis 3: research/readiness/ai-grading-benchmark-2026/literature.md, entries 2.16 and 2.17).

DESIGN. Reanalysis only: no calls.
- Runs: the rewording study's own (paraphrase/study.py), for the 22 board models (the `model` keys of
  out/overall.json that are not reference rows): on short answers, code and essays, the board's 100 cases per
  task (seed 7), base probe.
- Seven PROMPTS: the default prompt (the board's own base grading, submissions/) and the six rewrites p1-p6.
- Six RE-ASKS of the default prompt: the board's base and retest (submissions/), and retest, retest2, retest3 and
  retest4 of the rewording study's default run (paraphrase CHANGE 3; its base is not used, as there).
- Cases: per task, the cases every one of the 22 models graded under all 13 conditions (7 prompts, 6 re-asks;
  the default prompt's base is shared by both sets). The number kept is reported.

MEASURES.
- A model's AGREEMENT under a condition: QWK with the human raters on each task (marks rounded half-up to the
  scale, one QWK per rater, averaged over raters, as in paraphrase/study.py), then the mean over the three tasks.
  QWK is computed by its closed form, 2 cov(a, b) / (var a + var b + (mean a - mean b)^2) on the rounded marks,
  which equals metrics.qwk exactly.
- A RANKING per condition: the 22 models ordered by agreement (rank 1 = highest; ties get the mean rank).
- RANK AGREEMENT of a set of rankings: the mean Spearman correlation over its pairs (21 pairs of prompts; 15 pairs
  of re-asks).
- D = rank agreement across prompts - rank agreement across re-asks. Signed: NEGATIVE = rewording reorders the
  models more than asking again does. 95% percentile interval from 2,000 bootstrap draws (seed 7) resampling cases
  within each task, the same draw used for all 13 conditions (paired). The prompt is assigned per run, so the
  re-asks, which are separate runs and separate asks of one prompt, are the reference for what a new run does.
- Descriptive: per model, its rank under each prompt; its 95% rank interval from the case bootstrap under the
  default prompt alone, and from the same bootstrap with one of the seven prompts drawn at random per draw (the
  same prompt for every model in a draw: a school uses one wording); how many models' rank intervals widen;
  which model is first under each prompt. The board's overall ranking is not recomputed: the rewording runs
  hold base gradings only, so this is the agreement ranking.

VERDICT (one, for the board):
  WORDING REORDERS THE MODELS     D's interval lies below 0
  RANKING WITHIN RE-ASK NOISE     D's interval contains 0 (its lower end reported as the reordering not ruled
                                  out)
  PROMPTS AGREE MORE THAN RE-ASKS D's interval lies above 0

FLOOR (`floor`, synthetic, run and committed before `analyse` reads any run). On the board's real cases (the
experts' marks on the 100 cases of each task, each rater kept), 22 simulated graders: grader m marks
expert mean + b_m + N(0, s_m), rounded half-up and clipped to the scale, with b_m ~ N(0, 0.05) and s_m ~
U(0.08, 0.30), both as shares of the scale width, so agreement spans roughly the board's range. A re-ask redraws
the noise. Under PROMPT k, b_mk = b_m + N(0, tau_b) and s_mk = s_m * exp(N(0, tau_s)). Null world: tau = 0.
Planted world: tau_b = 0.03 and tau_s = 0.20 (a model-by-wording interaction that moves a model's agreement by
a few hundredths of QWK, about the spread the rewording study reported for its models). 100 worlds each, 500
bootstrap draws per world. Pass: the planted world reads WORDING REORDERS THE MODELS in at least 80%, and the
null world reads it in at most 5%. If the floor fails, the verdict reads UNMEASURED and the figures are
descriptive. The planted size is not changed after the floor runs.

LIMITS stated in advance: the ranking is by agreement alone, not the board's overall score; seven wordings, all
written by the benchmark (none by a teacher); three tasks, 100 cases each; the default prompt's base grading
belongs to both sets; the re-asks are of one wording only.

BUDGET. No calls: a reanalysis of held runs (scripts/check_runs.py on them before analysing).

CHANGES:

Usage:
    python3 prompt-ranking/study.py floor --cases-dir <dir>
    python3 prompt-ranking/study.py analyse --cases-dir <dir>
"""

import argparse
import json
import os
import sys

import numpy as np
from scipy.stats import rankdata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import cases as cases_mod  # noqa: E402
import leaderboard as lb  # noqa: E402

RUNS = os.environ.get("GBENCH_RUNS", "runs")
OUT = os.path.join(HERE, "out")
FILES = {"mohler": "mohler.jsonl", "code": "harmogen-code.jsonl", "asap2": "asap2.jsonl"}
PARA = [f"p{i}" for i in range(1, 7)]
PROMPTS = ["default"] + PARA
REASKS = ["board-base", "board-retest", "retest", "retest2", "retest3", "retest4"]
B, SEED = 2000, 7


def models():
    return [r["model"] for r in json.load(open(os.path.join(ROOT, "out", "overall.json")))["rows"] if not r.get("reference")]


def slug(m):
    return m.replace("/", "_")


def half_up(x):
    return np.floor(np.asarray(x, dtype=float) + 0.5)


def task_cases(cases_dir, task):
    return cases_mod.sample(cases_mod.load(os.path.join(cases_dir, FILES[task])), lb.N, lb.SEED)


def human_matrix(cs, lo, hi):
    """(raters, cases) rounded human marks, NaN where a rater did not mark a case."""
    raters = sorted({k for c in cs for k in c["human"]})
    H = np.full((len(raters), len(cs)), np.nan)
    for j, c in enumerate(cs):
        for i, r in enumerate(raters):
            if r in c["human"]:
                H[i, j] = min(hi, max(lo, half_up(c["human"][r])))
    return H


def qwk_boot(H, M, idx):
    """H (raters, n) rounded human marks (NaN where a rater did not mark); M (conds, models, n) rounded marks;
    idx (B, n) case indices. Returns (B, conds, models): QWK per rater by its closed form, averaged over raters."""
    out, k = 0.0, 0
    b = np.moveaxis(M[:, :, idx], 2, 0)          # (B, conds, models, n)
    for h in H:
        w = (~np.isnan(h))[idx].astype(float)    # (B, n): this rater marked the drawn case
        if w.sum(-1).min() < 2:
            continue
        a = np.nan_to_num(h)[idx]
        sw = w.sum(-1)
        am = (w * a).sum(-1) / sw
        va = (w * (a - am[:, None]) ** 2).sum(-1) / sw
        W = w[:, None, None, :]
        bm = (W * b).sum(-1) / sw[:, None, None]
        vb = (W * (b - bm[..., None]) ** 2).sum(-1) / sw[:, None, None]
        cov = (W * (b - bm[..., None]) * (a - am[:, None])[:, None, None, :]).sum(-1) / sw[:, None, None]
        am3, va3 = am[:, None, None], va[:, None, None]
        out = out + 2 * cov / (va3 + vb + (am3 - bm) ** 2)
        k += 1
    return out / k


def ranks(x):
    """x (..., models) -> ranks, 1 = highest agreement, ties averaged."""
    return rankdata(-x, axis=-1)


def mean_spearman(R):
    """R (..., k, models) ranks -> (...,) mean pairwise Pearson correlation of ranks (Spearman)."""
    z = R - R.mean(-1, keepdims=True)
    z = z / np.sqrt((z ** 2).sum(-1, keepdims=True))
    C = np.einsum("...im,...jm->...ij", z, z)
    k = R.shape[-2]
    iu = np.triu_indices(k, 1)
    return C[..., iu[0], iu[1]].mean(-1)


def statistic(Q):
    """Q (B, 12, models): conditions = 7 prompts, then the 5 re-asks other than board-base (board-base = prompt 0).
    Returns D per draw."""
    Rk = ranks(Q)
    prompts = Rk[:, :7]
    reasks = np.concatenate([Rk[:, :1], Rk[:, 7:]], axis=1)
    return mean_spearman(prompts) - mean_spearman(reasks)


def verdict(lo, hi):
    return "WORDING REORDERS THE MODELS" if hi < 0 else "PROMPTS AGREE MORE THAN RE-ASKS" if lo > 0 else "RANKING WITHIN RE-ASK NOISE"


def cmd_floor(a):
    res = {"worlds": 100, "boot": 500}
    tasks = {t: task_cases(a.cases_dir, t) for t in FILES}
    rng = np.random.default_rng(SEED)
    calls = {"null": 0, "planted": 0}
    for kind, (tb, ts) in (("null", (0.0, 0.0)), ("planted", (0.03, 0.20))):
        for w in range(res["worlds"]):
            nm = 22
            b = rng.normal(0, 0.05, nm)
            s = rng.uniform(0.08, 0.30, nm)
            bp = b[None] + rng.normal(0, tb, (7, nm))
            sp = s[None] * np.exp(rng.normal(0, ts, (7, nm)))
            bp[0], sp[0] = b, s  # prompt 0 is the default wording, the one the re-asks repeat
            Q = 0.0
            for t, cs in tasks.items():
                lo, hi = cs[0]["scale"]
                wdt = hi - lo
                H = human_matrix(cs, lo, hi)
                hm = np.array([np.mean(list(c["human"].values())) for c in cs])
                n = len(cs)
                prm = hm[None, None] + wdt * (bp[..., None] + sp[..., None] * rng.normal(0, 1, (7, nm, n)))
                rea = hm[None, None] + wdt * (b[None, :, None] + s[None, :, None] * rng.normal(0, 1, (5, nm, n)))
                M = np.clip(half_up(np.concatenate([prm, rea])), lo, hi)
                idx = rng.integers(0, n, (res["boot"], n))
                Q = Q + qwk_boot(H, M, idx) / len(tasks)
            d = statistic(Q)
            lo_, hi_ = np.percentile(d, [2.5, 97.5])
            calls[kind] += verdict(lo_, hi_) == "WORDING REORDERS THE MODELS"
            print(f"{kind} world {w}: D [{lo_:+.3f}, {hi_:+.3f}]", flush=True) if w % 20 == 0 else None
    res["false_alarm"] = calls["null"] / res["worlds"]
    res["detection"] = calls["planted"] / res["worlds"]
    res["passes"] = res["false_alarm"] <= 0.05 and res["detection"] >= 0.80
    print(res)
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "floor.json"), "w"), indent=1)


def load_marks(cases_dir):
    ms = models()
    data = {}
    for t in FILES:
        cs = task_cases(cases_dir, t)
        lo, hi = cs[0]["scale"]
        ids = [c["id"] for c in cs]
        M = np.full((12, len(ms), len(ids)), np.nan)  # 7 prompts, then retest (board) and retest..retest4 (para run)
        pos = {i: j for j, i in enumerate(ids)}
        for mi, m in enumerate(ms):
            sub = json.load(open(os.path.join(ROOT, "submissions", m.replace("/", "__"), f"{t}.json")))
            for r in sub["calls"]:
                if r.get("score") is None or r["id"] not in pos:
                    continue
                if r["probe"] == "base":
                    M[0, mi, pos[r["id"]]] = r["score"]
                elif r["probe"] == "retest":
                    M[7, mi, pos[r["id"]]] = r["score"]
            for k, p in enumerate(PARA, start=1):
                for r in map(json.loads, open(os.path.join(RUNS, f"para-{p}-{t}-{slug(m)}", "calls.jsonl"))):
                    if r.get("score") is not None and r["probe"] == "base" and r["id"] in pos:
                        M[k, mi, pos[r["id"]]] = r["score"]
            for r in map(json.loads, open(os.path.join(RUNS, f"para-default-{t}-{slug(m)}", "calls.jsonl"))):
                if r.get("score") is not None and r["probe"] in ("retest", "retest2", "retest3", "retest4") and r["id"] in pos:
                    M[8 + ["retest", "retest2", "retest3", "retest4"].index(r["probe"]), mi, pos[r["id"]]] = r["score"]
        keep = ~np.isnan(M).any(axis=(0, 1))
        data[t] = {"cs": [c for c, k in zip(cs, keep) if k], "M": np.clip(half_up(M[:, :, keep]), lo, hi),
                   "lo": lo, "hi": hi, "n_total": len(ids), "n_kept": int(keep.sum())}
    return ms, data


def cmd_analyse(a):
    floor = json.load(open(os.path.join(OUT, "floor.json")))
    ms, data = load_marks(a.cases_dir)
    rng = np.random.default_rng(SEED)
    Qb = 0.0
    Qp = 0.0
    for t, d in data.items():
        H = human_matrix(d["cs"], d["lo"], d["hi"])
        n = d["M"].shape[-1]
        idx = rng.integers(0, n, (B, n))
        Qb = Qb + qwk_boot(H, d["M"], idx) / len(data)
        Qp = Qp + qwk_boot(H, d["M"], np.arange(n)[None]) / len(data)
    Qp = Qp[0]                       # (12, models): point estimates
    d_point = float(statistic(Qp[None])[0])
    dist = statistic(Qb)
    lo_, hi_ = (float(x) for x in np.percentile(dist, [2.5, 97.5]))
    rk = ranks(Qp)
    # rank intervals: default prompt only, and a random prompt per draw
    rb = ranks(Qb)
    pick = rng.integers(0, 7, B)
    r_def = rb[:, 0]
    r_any = rb[np.arange(B), pick]
    iv_def = np.percentile(r_def, [2.5, 97.5], axis=0)
    iv_any = np.percentile(r_any, [2.5, 97.5], axis=0)
    per_model = []
    for mi, m in enumerate(ms):
        per_model.append({"model": m, "agreement": {c: float(Qp[k, mi]) for k, c in enumerate(PROMPTS)},
                          "rank": {c: float(rk[k, mi]) for k, c in enumerate(PROMPTS)},
                          "rank_range_over_prompts": [float(rk[:7, mi].min()), float(rk[:7, mi].max())],
                          "rank_ci95_default_prompt": [float(x) for x in iv_def[:, mi]],
                          "rank_ci95_any_prompt": [float(x) for x in iv_any[:, mi]]})
    widened = sum((p["rank_ci95_any_prompt"][1] - p["rank_ci95_any_prompt"][0]) > (p["rank_ci95_default_prompt"][1] - p["rank_ci95_default_prompt"][0]) for p in per_model)
    first = {c: ms[int(np.argmin(rk[k]))] for k, c in enumerate(PROMPTS)}
    rho_p = float(mean_spearman(rk[None, :7])[0])
    rho_r = float(mean_spearman(np.concatenate([rk[None, :1], rk[None, 7:]], axis=1))[0])
    res = {"design": "prompt-ranking/study.py docstring", "floor": floor,
           "cases": {t: {"kept": d["n_kept"], "of": d["n_total"]} for t, d in data.items()},
           "rank_agreement_prompts": rho_p, "rank_agreement_reasks": rho_r,
           "D": {"estimate": d_point, "ci95": [lo_, hi_]},
           "verdict": verdict(lo_, hi_) if floor["passes"] else "UNMEASURED",
           "rank_intervals_widened_by_prompt": widened, "first_by_prompt": first, "models": per_model}
    print(f"rank agreement: prompts {rho_p:.3f}, re-asks {rho_r:.3f}; D {d_point:+.3f} [{lo_:+.3f}, {hi_:+.3f}] -> {res['verdict']}")
    print(f"rank intervals widened by the prompt for {widened} of {len(ms)}; first by prompt: {first}")
    json.dump(res, open(os.path.join(OUT, "ranking.json"), "w"), indent=1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("floor", cmd_floor), ("analyse", cmd_analyse)):
        p = sub.add_parser(name)
        p.add_argument("--cases-dir", required=True)
        p.set_defaults(fn=fn)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
