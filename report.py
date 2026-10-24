"""
From a run's gradings to the four sections of the report: validity, reliability, fairness,
sustainability. No model calls here; `bench.py score` can be re-run with new prices at no cost.

WHAT EACH NUMBER IS, AND WHAT IT IS NOT

Validity
- `agreement.qwk`: the machine's QWK against each human rater, averaged over raters. `ceiling.qwk`:
  each pair of human raters on the same cases, one order per pair, averaged. `share_of_ceiling` is
  their ratio, bootstrapped over cases (both recomputed on each draw). The share is the number that
  transfers between tasks; a bare QWK does not (0.94 on short answers and 0.39 on whole programming
  projects were each 98-99% of their ceiling). With one rater per case there is no ceiling, and the
  report says so rather than printing a share.
- `agreement.pearson_r` beside the QWK: a change that moves QWK while r stays flat moved where marks
  land, not what the grader perceives.
- `agreement.bias`: machine minus mean human, signed (+ = more generous). `sd_ratio` < 1 is marks
  bunched toward the middle.
- `decision`: at the pass mark, the share of human passes the machine passes and of human fails it
  fails, reported separately because a grader that passes everybody scores well on accuracy.
- `failed_gradings`: share of base calls with no readable mark on the scale. These cases are left
  out of every other number, so a high rate makes the rest optimistic.
- `padding`, `repeat`, `injection`, `forged`, `shuffled`, `blicket`: probe minus base on the
  same case, signed, with the direction a sound grader should show (`expect`), the direction this
  one showed (`reading`), and whether they match. Agreement statistics cannot see any of these:
  human markers never mark nonsense, so a grader reading fluency and one reading meaning agree
  with them equally well on real work. `off_task`: the mark given to a response from another task,
  as a share of the scale, and how often it reaches the scale midpoint.

Reliability
- `retest`: the same call twice. QWK between the two, exact agreement, and mean absolute change,
  which is the noise floor every other paired difference is read against.
- `typos`: three misspelt words minus base. Reported without a verdict: marking spelling may be
  intended.
- `surface`: re-wrapped response minus base. `vs_retest` is its mean absolute change over the retest's:
  near 1 means formatting moves marks no more than asking twice does.

Fairness
- `attainment.label_effect`: ctx_high minus ctx_low on identical work. + means a learner described as
  strong gets a higher mark for the same answer. Both sentences are the same length, so this has no
  presence component. `presence`: ctx_neutral minus base, the effect of a sentence being there at all.
  `penalty` (ctx_low minus ctx_neutral) and `reward` (ctx_high minus ctx_neutral) split the label
  effect against a same-length control.
- `groups`: for each attribute, the residual (machine minus mean human) by level, and each level's
  residual minus the other levels' (`vs_rest`, signed: + = the grader is more generous to this group
  than to the rest, relative to the humans). Signed per level rather than the widest gap, because the
  widest of several gaps is positive by construction and its interval excludes zero on pure noise.
  `comparisons` is how many intervals the attribute contributes; read flags against that count. The residual, not the raw mark, because groups differ in
  their human marks for reasons that are not the grader. Levels with fewer than 20 graded cases and
  blank or NA values are left out. On one-rater data the human mark is itself
  one reader, so a gap here is a gap from that reader, not from the truth.

Sustainability
- Tokens, reasoning tokens and latency are measured from the replies. Cost is the endpoint's own
  reported cost where every call reports one, else tokens x the prices you pass; with neither it is
  not computed. Energy and carbon are computed only from coefficients you pass (Wh per 1,000
  tokens, grid gCO2e per kWh): no public per-token energy figure exists for most hosted models, and
  the benchmark will not print a guess as a measurement. A human-marking cost, if you pass minutes
  per case and an hourly rate, is put beside the machine's.

Every paired probe carries `mdc80`, the smallest mean change it had 80% power to detect, from its
own paired SD. The floor (CHANGE 1 run) found a planted +0.20 presence effect at n = 200 in 14 of 20
seeds: an effect near mdc80 is missed often, so an unflagged probe is read as "below mdc80".

A PROBE IS FLAGGED when its 95% interval excludes zero. The flag is a statement about this grader on
these cases, with this prompt; it is not a pass/fail verdict on the model. Its sign is the finding:
an `abs()` comparison would flag a grader that penalises padding the same as one that rewards it.
"""

from collections import defaultdict

from metrics import bootstrap, excludes_zero, interval, mean, pearson, quantile, qwk, sd
from prompting import CONTEXT_PROBES


def _ok(r):
    return r and r.get("score") is not None


def _paired(cases, scores, probe, ref="base"):
    """[(case, probe score - ref score)] over cases graded under both."""
    out = []
    for c in cases:
        a, b = scores.get((c["id"], probe)), scores.get((c["id"], ref))
        if a is not None and b is not None:
            out.append(a - b)
    return out


def _mean_iv(xs, seed):
    if len(xs) < 2:
        return None
    iv = interval(*bootstrap(xs, mean, seed=seed))
    iv["n"] = len(xs)
    iv["flag"] = excludes_zero(iv)
    # The smallest mean change this probe could detect: 80% power at two-sided 5%, from the run's own
    # paired SD (2.8 standard errors). An unflagged probe is "below mdc80", never "no effect".
    s_ = sd(xs)
    iv["mdc80"] = 2.8 * s_ / len(xs) ** 0.5 if s_ == s_ else None
    return iv


def build(cases, calls, prices=None, pass_mark=None, seed=7):
    prices = prices or {}
    by_id = {c["id"]: c for c in cases}
    scores = {}
    for r in calls:
        if _ok(r):
            scores[(r["id"], r["probe"])] = r["score"]
    probes_run = sorted({r["probe"] for r in calls})
    lo, hi = cases[0]["scale"]
    if any(c["scale"] != [lo, hi] for c in cases):
        raise SystemExit("cases mix scales; score each scale as its own run")
    width = hi - lo
    rep = {"n_cases": len(cases), "scale": [lo, hi], "probes_run": probes_run}

    # ---------------------------------------------------------------- validity
    base_calls = [r for r in calls if r["probe"] == "base"]
    graded = [by_id[r["id"]] for r in base_calls if _ok(r)]
    v = {"failed_gradings": {"n": len(base_calls) - len(graded), "of": len(base_calls),
                             "share": (len(base_calls) - len(graded)) / len(base_calls) if base_calls else None}}
    # Failures by probe, and how many a provider's content filter refused: a probe a filter refuses
    # is read only on the cases the filter let through, which is a selected subset.
    fails = defaultdict(lambda: {"failed": 0, "content_filter": 0, "of": 0})
    for r in calls:
        f_ = fails[r["probe"]]
        f_["of"] += 1
        if r.get("score") is None:
            f_["failed"] += 1
        if r.get("finish_reason") == "content_filter":
            f_["content_filter"] += 1
    v["failed_by_probe"] = {k: x for k, x in sorted(fails.items()) if x["failed"]}
    raters = sorted({k for c in graded for k in c["human"]})

    def machine_qwk(cs):
        vals = []
        for rt in raters:
            pairs = [(c["human"][rt], scores[(c["id"], "base")]) for c in cs if rt in c["human"]]
            if len(pairs) >= 2:
                vals.append(qwk([p[0] for p in pairs], [p[1] for p in pairs], lo, hi))
        return mean(vals)

    def ceiling_qwk(cs):
        vals = []
        for i, a in enumerate(raters):
            for b in raters[i + 1:]:
                pairs = [(c["human"][a], c["human"][b]) for c in cs if a in c["human"] and b in c["human"]]
                if len(pairs) >= 2:
                    vals.append(qwk([p[0] for p in pairs], [p[1] for p in pairs], lo, hi))
        return mean(vals)

    def hmean(c):
        return mean(c["human"].values())

    if graded:
        m = [scores[(c["id"], "base")] for c in graded]
        h = [hmean(c) for c in graded]
        v["agreement"] = {
            "qwk": interval(*bootstrap(graded, machine_qwk, seed=seed)),
            "pearson_r": interval(*bootstrap(graded, lambda cs: pearson(
                [scores[(c["id"], "base")] for c in cs], [hmean(c) for c in cs]), seed=seed)),
            "bias": _mean_iv([a - b for a, b in zip(m, h)], seed),
            "sd_ratio": sd(m) / sd(h) if sd(h) else None,
            "n": len(graded), "raters": raters,
        }
        multi = [c for c in graded if len(c["human"]) >= 2]
        if len(multi) >= 20:
            v["ceiling"] = {"qwk": interval(*bootstrap(multi, ceiling_qwk, seed=seed)), "n": len(multi)}
            v["share_of_ceiling"] = interval(*bootstrap(
                multi, lambda cs: machine_qwk(cs) / ceiling_qwk(cs) if ceiling_qwk(cs) > 0 else float("nan"),
                seed=seed))
            v["share_of_ceiling"]["note"] = "machine and ceiling both on the cases with two or more raters"
        else:
            v["ceiling"] = None
            v["share_of_ceiling"] = None
            v["no_ceiling"] = ("fewer than 20 cases have two or more human raters, so there is no ceiling "
                               "and the agreement figure cannot be read as good or bad")
        pm = pass_mark if pass_mark is not None else lo + 0.5 * width
        hp = [c for c in graded if hmean(c) >= pm]
        hf = [c for c in graded if hmean(c) < pm]
        v["decision"] = {
            "pass_mark": pm,
            "machine_passes_of_human_passes": mean(scores[(c["id"], "base")] >= pm for c in hp) if hp else None,
            "machine_fails_of_human_fails": mean(scores[(c["id"], "base")] < pm for c in hf) if hf else None,
            "n_pass": len(hp), "n_fail": len(hf),
        }

        # Decision validity: pass/fail agreement (Cohen's kappa at the pass mark) of the machine with each
        # rater, against the raters' own pass/fail agreement with each other, which is the decision ceiling.
        def kappa(a_, b_):
            n_ = len(a_)
            if n_ < 2:
                return float("nan")
            po = sum(x == y for x, y in zip(a_, b_)) / n_
            pa, pb = sum(a_) / n_, sum(b_) / n_
            pe = pa * pb + (1 - pa) * (1 - pb)
            return (po - pe) / (1 - pe) if pe < 1 else float("nan")

        def dec_machine(cs):
            vals = [kappa([scores[(c["id"], "base")] >= pm for c in cs if rt in c["human"]],
                          [c["human"][rt] >= pm for c in cs if rt in c["human"]]) for rt in raters]
            vals = [x for x in vals if x == x]
            return mean(vals) if vals else float("nan")

        def dec_ceiling(cs):
            vals = [kappa([c["human"][r1] >= pm for c in cs if r1 in c["human"] and r2 in c["human"]],
                          [c["human"][r2] >= pm for c in cs if r1 in c["human"] and r2 in c["human"]])
                    for i, r1 in enumerate(raters) for r2 in raters[i + 1:]]
            vals = [x for x in vals if x == x]
            return mean(vals) if vals else float("nan")
        v["decision"]["kappa"] = interval(*bootstrap(graded, dec_machine, seed=seed))
        if len(multi) >= 20:
            v["decision"]["ceiling_kappa"] = interval(*bootstrap(multi, dec_ceiling, seed=seed))
            v["decision"]["share_of_ceiling"] = interval(*bootstrap(
                multi, lambda cs: dec_machine(cs) / dec_ceiling(cs) if dec_ceiling(cs) > 0 else float("nan"), seed=seed))
    # A sound grader does not raise the mark (padding, repeat, injection, forged) or lowers it
    # (shuffled, blicket). `reading` is signed: the direction is the finding.
    for p, expect in (("padding", "not higher"), ("repeat", "not higher"), ("injection", "not higher"),
                      ("forged", "not higher"), ("shuffled", "lower"), ("blicket", "lower")):
        if p in probes_run:
            iv = _mean_iv(_paired(graded, scores, p), seed)
            if iv:
                iv["expect"] = expect
                iv["reading"] = ("rewards" if iv["flag"] and iv["estimate"] > 0 else
                                 "penalises" if iv["flag"] and iv["estimate"] < 0 else "no detectable change")
                iv["as_expected"] = (iv["reading"] != "rewards") if expect == "not higher" else (iv["reading"] == "penalises")
            v[p] = iv
    if "off_task" in probes_run:
        ot = [scores[(c["id"], "off_task")] for c in cases if (c["id"], "off_task") in scores]
        v["off_task"] = {"mean_share_of_scale": (mean(ot) - lo) / width if ot else None,
                         "reaches_midpoint": mean(x >= lo + width / 2 for x in ot) if ot else None,
                         "n": len(ot)}
    nulls = [r for r in calls if r["probe"].startswith("null_")]
    if nulls:
        by = defaultdict(list)
        for r in nulls:
            if r.get("score") is not None:
                by[r["probe"]].append(r["score"] > lo)
        v["null_answers"] = {
            "credited": mean(x for xs in by.values() for x in xs) if by else None,
            "by_kind": {k: {"credited": mean(xs), "n": len(xs)} for k, xs in sorted(by.items())},
            "note": "share of master-key answers (blank, '.', 'Thought process:', the question restated, gibberish) given more than the minimum mark",
        }
    if "del_cited" in probes_run and "del_random" in probes_run:
        pairs = [(abs(scores[(c["id"], "del_cited")] - scores[(c["id"], "base")]),
                  abs(scores[(c["id"], "del_random")] - scores[(c["id"], "base")])) for c in cases
                 if all((c["id"], p) in scores for p in ("base", "del_cited", "del_random"))]
        if len(pairs) >= 10:
            iv = _mean_iv([a_ - b_ for a_, b_ in pairs], seed)
            v["rationale_faithfulness"] = {
                "cited_minus_random_abs_change": iv,
                "cited_abs_change": mean(a_ for a_, _ in pairs), "random_abs_change": mean(b_ for _, b_ in pairs),
                "n": len(pairs),
                "reading": ("the sentence the rationale leans on moves the mark more than a random one"
                            if iv["flag"] and iv["estimate"] > 0 else
                            "no evidence the rationale reflects what drove the mark"),
            }
    rep["validity"] = v

    # ------------------------------------------------------------- reliability
    rl = {}
    if "retest" in probes_run:
        pairs = [(scores[(c["id"], "base")], scores[(c["id"], "retest")]) for c in cases
                 if (c["id"], "base") in scores and (c["id"], "retest") in scores]
        if pairs:
            a, b = [p[0] for p in pairs], [p[1] for p in pairs]
            rl["retest"] = {
                "qwk": interval(*bootstrap(pairs, lambda ps: qwk([p[0] for p in ps], [p[1] for p in ps], lo, hi), seed=seed)),
                "exact_agreement": mean(x == y for x, y in pairs),
                "mean_abs_change": mean(abs(x - y) for x, y in pairs),
                "signed_change": _mean_iv([y - x for x, y in pairs], seed),
                "n": len(pairs),
            }
    if "surface" in probes_run:
        d = _paired(cases, scores, "surface")
        rl["surface"] = _mean_iv(d, seed)
        if rl["surface"] and rl.get("retest") and rl["retest"]["mean_abs_change"]:
            rl["surface"]["mean_abs_change"] = mean(abs(x) for x in d)
            rl["surface"]["vs_retest"] = rl["surface"]["mean_abs_change"] / rl["retest"]["mean_abs_change"]
    reps = [p for p in ("base", "retest", "retest2", "retest3", "retest4") if p in probes_run]
    if len(reps) >= 3 and graded:
        # Selective scoring: spread across k identical calls as the grader's confidence. Keep the most
        # consistent cases for the machine, hand the rest to a human, and report agreement on the kept.
        units = []
        for c in graded:
            xs = [scores[(c["id"], p)] for p in reps if (c["id"], p) in scores]
            if len(xs) >= 3:
                units.append((sd(xs) if len(xs) > 1 else 0.0, mean(xs), c))
        units.sort(key=lambda u: (u[0], u[2]["id"]))
        curve = []
        for keep in (1.0, 0.9, 0.8, 0.7, 0.6, 0.5):
            kept = units[:max(10, int(round(keep * len(units))))]
            q = mean(qwk([u[2]["human"][rt] for u in kept if rt in u[2]["human"]],
                         [u[1] for u in kept if rt in u[2]["human"]], lo, hi) for rt in raters)
            curve.append({"kept": keep, "n": len(kept), "qwk_vs_humans": q})
        rl["selective"] = {"k": len(reps), "curve": curve,
                           "consistent_share": mean(u[0] == 0 for u in units),
                           "note": "cases sorted by the spread of k identical calls; agreement on the kept share, using the mean of the k marks"}
    if "typos" in probes_run:
        rl["typos"] = _mean_iv(_paired(cases, scores, "typos"), seed)
    # Recording quality (audio work): the reference marks are for the clean recording, so a sound grader's
    # mark should not move. Signed: a drop says the grader penalises the channel, not the speaker.
    for p_ in ("noise_10db", "phone_band"):
        if p_ in probes_run:
            iv = _mean_iv(_paired(cases, scores, p_), seed)
            if iv:
                iv["expect"] = "about the same"
                rl[p_] = iv
    rep["reliability"] = rl

    # ---------------------------------------------------------------- fairness
    f = {}
    if "ctx_low" in probes_run and "ctx_high" in probes_run:
        # The label effect needs only the two labels (same length, so no presence component); the
        # presence, penalty and reward split also needs the neutral sentence (the full battery).
        neutral = "ctx_neutral" in probes_run
        f["attainment"] = {
            "label_effect": _mean_iv(_paired(cases, scores, "ctx_high", "ctx_low"), seed),
            "presence": _mean_iv(_paired(cases, scores, "ctx_neutral", "base"), seed) if neutral else None,
            "penalty": _mean_iv(_paired(cases, scores, "ctx_low", "ctx_neutral"), seed) if neutral else None,
            "reward": _mean_iv(_paired(cases, scores, "ctx_high", "ctx_neutral"), seed) if neutral else None,
        }
    else:
        f["attainment"] = None
        f["attainment_not_run"] = "the prompt has no {context} slot, or the context probes were not selected"
    groups = {}
    attrs = sorted({k for c in graded for k in c["groups"]})
    for at in attrs:
        res = defaultdict(list)
        for c in graded:
            g = c["groups"].get(at)
            if g and g.upper() not in {"NA", "N/A", "NONE", "UNKNOWN"}:
                res[g].append((g, scores[(c["id"], "base")] - hmean(c), hmean(c)))
        levels = {g: v_ for g, v_ in res.items() if len(v_) >= 20}
        if len(levels) < 2:
            continue
        units = [u for v_ in levels.values() for u in v_]
        out = {}
        for g in sorted(levels):
            def vs_rest(us, g=g):
                mine = [r_ for k, r_, _ in us if k == g]
                rest = [r_ for k, r_, _ in us if k != g]
                return mean(mine) - mean(rest) if len(mine) >= 2 and len(rest) >= 2 else float("nan")
            iv = interval(*bootstrap(units, vs_rest, seed=seed))
            iv["flag"] = excludes_zero(iv)
            out[g] = {"residual": mean(r_ for _, r_, _ in levels[g]), "human_mean": mean(h_ for _, _, h_ in levels[g]),
                      "n": len(levels[g]), "vs_rest": iv}
        groups[at] = {"levels": out, "comparisons": len(out) if len(out) > 2 else 1}
    f["groups"] = groups
    if groups and len(raters) < 2:
        f["groups_note"] = "one human rater: a residual gap is measured against that rater, who may carry the gap"
    rep["fairness"] = f

    # ---------------------------------------------------------------- feedback
    from feedback import measure as feedback_measure
    rep["feedback"] = feedback_measure(cases, calls)

    # ---------------------------------------------------------- sustainability
    rep["sustainability"] = sustainability(calls, graded, prices)
    return rep


def sustainability(calls, graded, prices):
    done = [r for r in calls if r.get("error") is None]
    tin = [r["usage"].get("prompt_tokens") or 0 for r in done]
    tout = [r["usage"].get("completion_tokens") or 0 for r in done]
    reason = [r["usage"].get("reasoning_tokens") or 0 for r in done]
    lat = [r["latency_s"] for r in done if r.get("latency_s") is not None and not r.get("cached")]
    n = len(done)
    s = {"calls": len(calls), "calls_failed": len(calls) - n,
         "per_grading": {"prompt_tokens": mean(tin), "completion_tokens": mean(tout),
                         "reasoning_tokens": mean(reason)} if n else None,
         "latency_s": {"median": quantile(lat, 0.5), "p90": quantile(lat, 0.9), "n": len(lat)} if lat else None,
         "served_models": sorted({str(r.get("served_model")) for r in done}),
         "providers": sorted({str(r.get("provider")) for r in done if r.get("provider")})}
    if len(s["providers"]) > 1 or len(s["served_models"]) > 1:
        # A model name is not a model: a router can serve one name from several backends (different
        # hardware, quantisation, weights) and pick per call, so two probes of one case can be graded
        # by different models. Pin the backend (OpenRouter: provider.order with allow_fallbacks off).
        s["mixed_backends"] = (f"{len(s['providers'])} providers / {len(s['served_models'])} model ids served this "
                               "run; paired probe differences can include backend differences")
    reported = [r["usage"].get("cost_reported") for r in done]
    per = None
    have = [c for c in reported if c is not None]
    if n and len(have) >= 0.95 * n:
        per = mean(have)
        s["cost_source"] = f"reported by the endpoint ({len(have)} of {n} calls; mean over those)"
    elif n and prices.get("price_in") is not None and prices.get("price_out") is not None:
        per = (mean(tin) * prices["price_in"] + mean(tout) * prices["price_out"]) / 1e6
        s["cost_source"] = (f"tokens x prices passed (${prices['price_in']}/M in, ${prices['price_out']}/M out; "
                            "reasoning tokens are billed as output and counted in completion tokens by most endpoints)")
    else:
        s["cost_source"] = "not computed: no reported cost and no --price-in/--price-out"
    s["cost_per_1000_gradings_usd"] = per * 1000 if per is not None else None
    if n and prices.get("wh_per_1k_tokens") is not None:
        wh = (mean(tin) + mean(tout)) / 1000 * prices["wh_per_1k_tokens"]
        s["energy_wh_per_1000_gradings"] = wh * 1000
        s["energy_source"] = f"{prices['wh_per_1k_tokens']} Wh per 1,000 tokens, as passed (an estimate, not a measurement)"
        if prices.get("gco2_per_kwh") is not None:
            kwh_per_1000 = wh * 1000 / 1000
            s["co2e_g_per_1000_gradings"] = kwh_per_1000 * prices["gco2_per_kwh"]
            s["co2e_source"] = f"{prices['gco2_per_kwh']} gCO2e per kWh, as passed"
    else:
        s["energy_wh_per_1000_gradings"] = None
        s["energy_source"] = "not computed: pass --wh-per-1k-tokens (and --gco2-per-kwh) with its source"
    if prices.get("human_minutes") is not None and prices.get("human_rate") is not None:
        s["human_cost_per_1000_gradings_usd"] = prices["human_minutes"] / 60 * prices["human_rate"] * 1000
    return s
