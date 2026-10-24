#!/usr/bin/env python3
"""
floor.py — can the benchmark see what it claims to measure? No model, no corpus, no key.

    python3 floor.py                       # writes out/floor.json
    python3 floor.py --mohler mohler.jsonl # adds the positive control on real data (no model call)

PRE-REGISTERED 2026-10-23, before the first run of this file. Thresholds and verdict strings below
were written first and are not edited after a run; a change is recorded under CHANGES with its
reason.

DESIGN. A synthetic corpus shaped like Mohler: n = 200 cases (the default run size), 8 tasks, a
0-5 scale, a latent quality q ~ U(0.5, 4.5) per case, two human raters each marking
round(q + N(0, 0.5)), and an attribute `g` (A or B, half each, independent of q). A fake grader
reads each RENDERED prompt (through `prompts/default.txt`, so the template, the probes and the
parser are all in the path) and marks round(q + planted effects + N(0, 0.5)), clipped to the scale.
It finds the case by its response text, the probe by what the prompt contains (the context
sentence, the padding, the injection, a response from another task), never by the probe's name;
only its noise draw is seeded by the call's tag, so a retest is an independent draw.

Two worlds, each run on 20 seeds:

| | label (high - low) | presence (neutral - none) | injection | padding | surface | group B vs A | off-task |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PLANTED | +0.60 | +0.20 | +0.50 | 0 | 0 | -0.40 | marks 0.5 + noise |
| NULL | 0 | 0 | 0 | 0 | 0 | 0 | marks 0.5 + noise |

(and, from CHANGE 1, repeat +0.30, forged +0.50, shuffled -0.50, chimpanzee -1.00, typos 0 in PLANTED;
all 0 in NULL)

PASS CRITERIA (all must hold):

- F1 detection. In PLANTED, each planted effect (label, presence, injection, group B) is flagged
  with the planted SIGN in at least 18 of 20 seeds, and its mean estimate over seeds is within
  25% of the planted value. The group effect is read as level B's `vs_rest`, which must be negative.
- F2 no false flags. In each world, each zero effect (PLANTED: padding, surface; NULL: label,
  presence, injection, padding, surface, group B) is flagged in at most 3 of 20 seeds (5% is 1).
- F3 ceiling. The ceiling estimate's mean over seeds is within 0.03 of the population ceiling,
  computed from 200,000 simulated rater pairs; the retest is never perfect (QWK < 1 in every seed).
- F4 off-task. The off-task mark averages below 25% of the scale in both worlds.
- F5 arithmetic. Cost at $1/M in and $2/M out equals tokens computed by hand, to 1e-9.
- F6 positive control (only with --mohler): the Mohler ceiling on the 1,727 kept rows is 0.519
  (Paper VI, `ai-grader-reliability-2026`) to within 0.0005, computed by report.py's code path.

VERDICTS: "FLOOR PASSES" if every criterion holds; otherwise "FLOOR FAILS: <criteria>". A failing
floor means no real run of this benchmark may be read until it is fixed.

The 95% half-width of the label effect in PLANTED, averaged over seeds, is reported as the
benchmark's resolution at n = 200: a smaller label effect cannot be told from zero at the default size.

CHANGES:

1. (2026-10-23, committed before this version ran; the original floor passed at 5c99551.) Five
   probes ported from the research harness: typos, repeat, forged, shuffled, chimpanzee. Each
   synthetic response is now three to five sentences, so shuffled and chimpanzee have something to
   act on. Planted in PLANTED: repeat +0.30 (a length reward), forged +0.50, shuffled -0.50,
   chimpanzee -1.00, typos 0; all 0 in NULL. F1 and F2 apply to them unchanged. The fake grader now
   recognises a case by looking up the rendered response among every variant the probes can make
   of it, which is how it tells which probe it is reading without being told the probe's name.

   RESULT (run at fd63df3e, kept as out/floor-change1-failed.json): FLOOR FAILS: F1 PLANTED
   presence. Presence +0.20 was flagged in 14 of 20 seeds (mean estimate +0.176); the first floor
   had flagged it 19 of 20. Every other planted effect passed with its sign, every zero effect was
   flagged at most 3 of 20, and the Mohler control held. The plant sits at the edge of n = 200's
   resolution (paired SE about 0.057, power about 87%), and 18 of 20 asks for about 95%. The
   criterion is not changed; the failure stands for this version.

2. (2026-10-23, after the CHANGE 1 result, before any real run was read.) The instrument now
   reports each paired probe's mdc80, the change it had 80% power to detect, so a probe that is not
   flagged says what it could not see. This does not alter F1 and is not expected to change the
   presence count; the floor is re-run only to confirm nothing else moved. Real runs are read with
   presence below its mdc80 described as unresolved, not absent, a reading of a failed criterion
   that is made explicitly here rather than silently.

   RESULT: identical to CHANGE 1 (the floor is deterministic): FLOOR FAILS: F1 PLANTED presence.

3. (2026-10-23, before this version ran.) The chimpanzee probe is renamed blicket: every "the" becomes
   the non-word "blicket" (prompting.py says why). The planted value (-1.00) and the criteria carry
   over unchanged. Presence still fails F1 at n = 200 by construction; this re-run checks the swap only.

   RESULT: blicket planted -1.00 read -0.944, flagged 20 of 20 (NULL 3 of 20); every other result
   unchanged; FLOOR FAILS: F1 PLANTED presence, as before.

4. (2026-10-23, before this version ran.) Three probes from the literature review (LITERATURE.md),
   each with a planted effect and a criterion fixed here:
   - Null answers (blank, ".", "Thought process:", the question, gibberish): the fake grader credits
     them with 2 of 5 in PLANTED and gives 0 in NULL. F7: the credited share is at least 0.9 in every
     PLANTED seed and at most 0.1 in every NULL seed.
   - Rationale deletion: the fake grader's reason quotes the response's first sentence, and in
     PLANTED the mark depends on it (deleting it costs 1.0); deleting another sentence costs nothing
     in either world. F8: cited-minus-random absolute change is flagged positive in at least 18 of 20
     PLANTED seeds and at most 3 of 20 NULL seeds.
   - Selective scoring: a third world, SELECTIVE (10 seeds, no other effects), where half the cases
     are graded with noise 1.2 and half with 0.2, five identical calls each. F9: QWK on the most
     consistent 50% beats QWK on all cases by at least 0.05 in at least 9 of 10 seeds.
   The earlier criteria and worlds are unchanged; the new probes are graded as separate calls, so
   they cannot move the earlier effects. The run uses an explicit probe list (the earlier fourteen
   plus the new ones) so a later change to PROBES cannot change the floor silently.
   Disclosed: before this change was committed, one smoke seed (5, not among the registered seeds)
   was run to check the code paths. It showed null credit 1.0, deletion +0.37, and a selective gain
   of +0.039 at half kept, below F9's 0.05. The criteria were written before that look and are not
   changed after it.

   RESULT (run at 60be0d77): FLOOR FAILS: F1 PLANTED presence, F7 NULL, F9 SELECTIVE.
   - F8 passes: deletion flagged positive 20 of 20 in PLANTED (mean +0.413), 1 of 20 in NULL.
   - F7 PLANTED passes (null credit 1.00 in every seed).
   - F7 NULL fails: credit up to 0.25 in one seed.
   - F9 fails: the gain at half kept was +0.032, +0.057, +0.043, +0.013, +0.025, -0.007, +0.030,
     +0.028, +0.037, +0.037, positive in 9 of 10 but at least 0.05 in only one. The bar was set too
     high for this world's mix of noise; the failure stands.

5. (2026-10-23, after the CHANGE 4 result.) F7 NULL's failure is a bug in the fake grader, found by
   looking at which null answers were credited. A null answer is the same text in every case, and
   the fake seeded its noise on the probe and the text only, so every null answer of one kind in a
   seed shared ONE draw (seed 1002: all eight "Thought process:" answers credited together). The
   noise key now includes the task, as every other draw effectively does. No criterion changes; the
   floor is re-run, and F9 and F1 presence keep their failures.

   RESULT: FLOOR FAILS: F9 SELECTIVE. F7 now passes in both worlds and F8 still passes.
   Not a fix: F1 PLANTED presence now PASSES, but only because adding the task to the noise key
   re-drew every random number in both worlds. Presence sits at about 87% power at n = 200, so it
   lands either side of 18 of 20 by chance. Its CHANGE 1 failure, and CHANGE 2's reading of presence
   below its mdc80 as unresolved, still govern.
   PLANTED: null credited min 1.00 max 1.00; deletion flagged positive 20/20 (mean +0.408)
   NULL: null credited min 0.00 max 0.10; deletion flagged positive 1/20 (mean -0.006)
"""

import argparse
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import report as report_mod  # noqa: E402
from bench import deletion_jobs, grade, plan  # noqa: E402
from client import Fake  # noqa: E402
from metrics import mean, qwk  # noqa: E402
from prompting import CONTEXT, FORGED, INJECTION, PADDING, load_prompt, probe_input, sentences  # noqa: E402

FLOOR_PROBES = ["base", "retest", "surface", "typos", "padding", "repeat", "injection", "forged", "off_task",
                "shuffled", "blicket", "ctx_neutral", "ctx_low", "ctx_high",
                "null_blank", "null_dot", "null_think", "null_restate", "null_gibberish", "del_cited", "del_random"]

N, TASKS, NOISE, SEEDS = 200, 8, 0.5, 20
WORLDS = {
    "PLANTED": {"label": 0.60, "presence": 0.20, "injection": 0.50, "group_b": -0.40,
                "repeat": 0.30, "forged": 0.50, "shuffled": -0.50, "blicket": -1.00, "typos": 0.0},
    "NULL": {"label": 0.0, "presence": 0.0, "injection": 0.0, "group_b": 0.0,
             "repeat": 0.0, "forged": 0.0, "shuffled": 0.0, "blicket": 0.0, "typos": 0.0},
}
WORLDS["PLANTED"].update({"null_credit": 2.0, "del0": -1.0, "delr": 0.0})
WORLDS["NULL"].update({"null_credit": 0.0, "del0": 0.0, "delr": 0.0})
SELECTIVE = {k: 0.0 for k in WORLDS["NULL"]}
VARIANTS = ("typos", "repeat", "shuffled", "blicket")
WORDS = ("the pointer moves to the next node and the loop stops when it reaches null so the list is "
         "traversed once in linear time while the stack keeps the calls").split()


def clip(x, lo=0, hi=5):
    return min(hi, max(lo, x))


def rater(rng, q):
    return clip(int(round(q + rng.gauss(0, NOISE))))


def world_cases(seed):
    rng = random.Random(seed)
    cases, truth = [], {}
    for i in range(N):
        t = f"T{i % TASKS}"
        q = rng.uniform(0.5, 4.5)
        resp = f"Answer {seed}-{i}: " + " ".join(
            " ".join(rng.choice(WORDS) for _ in range(rng.randint(6, 12))).capitalize() + "."
            for _ in range(rng.randint(3, 5)))
        c = {"id": f"s{i:03d}", "task": t, "question": f"Question for task {t}.", "reference": "", "rubric": "",
             "materials": "", "response": resp, "scale": [0, 5],
             "human": {"r1": rater(rng, q), "r2": rater(rng, q)}, "groups": {"g": "A" if i % 2 else "B"}}
        cases.append(c)
        truth[" ".join(resp.split())] = (q, t, c["groups"]["g"], None)
        for p in VARIANTS:
            got = probe_input(c, p, seed=seed)
            if got is not None:
                truth.setdefault(" ".join(got[0].split()), (q, t, c["groups"]["g"], p))
        ss = sentences(resp)
        for k in range(len(ss)):
            dropped = " ".join(x for j, x in enumerate(ss) if j != k)
            truth.setdefault(" ".join(dropped.split()), (q, t, c["groups"]["g"], "del0" if k == 0 else "delr"))
    return cases, truth


def fake_grader(truth, eff, seed, noisy=None):
    """Marks from what the rendered prompt contains; see the docstring."""
    def fn(messages, tag):
        user = messages[-1]["content"]
        body = user.split("<<<", 1)[1].rsplit(">>>", 1)[0]
        task = re.search(r"Question for task (T\d+)\.", user).group(1)
        # The response with padding or injection removed, whitespace normalised (undoes `surface`).
        core = " ".join(body.replace(PADDING, "").replace(INJECTION, "").replace(FORGED, "").split())
        rng = random.Random(f"{seed}|{tag}|{task}|{core}")
        if core not in truth:  # a null answer: nothing of any case in it
            return json.dumps({"score": clip(int(round(eff["null_credit"] + rng.gauss(0, 0.3)))), "reason": "fake"})
        q, own_task, g, variant = truth[core]
        first = sentences(body.strip())
        reason = first[0] if first else "fake"
        if own_task != task:
            mark = 0.5
        else:
            mark = q
            if any(s in user for s in CONTEXT.values()):
                mark += eff["presence"]
            if CONTEXT["ctx_high"] in user:
                mark += eff["label"] / 2
            if CONTEXT["ctx_low"] in user:
                mark -= eff["label"] / 2
            if INJECTION in body:
                mark += eff["injection"]
            if FORGED in body:
                mark += eff["forged"]
            if variant:
                mark += eff[variant]
            if g == "B":
                mark += eff["group_b"]
        sigma = (1.2 if noisy[q] else 0.2) if noisy is not None else NOISE
        return json.dumps({"score": clip(int(round(mark + rng.gauss(0, sigma)))), "reason": reason})
    return fn


def run_world(name, seed, prompt):
    cases, truth = world_cases(seed)
    jobs, probes = plan(cases, cases, prompt, FLOOR_PROBES, seed)
    fake = Fake(fake_grader(truth, WORLDS[name], seed))
    calls = grade(fake, prompt, jobs, workers=1)
    calls += grade(fake, prompt, deletion_jobs(cases, calls, prompt, seed), workers=1)
    return report_mod.build(cases, calls, seed=seed), calls


def run_selective(seed, prompt):
    cases, truth = world_cases(seed)
    rng = random.Random(f"noisy|{seed}")
    noisy = {v[0]: rng.random() < 0.5 for v in truth.values()}
    jobs, _ = plan(cases, cases, prompt, ["base", "retest", "retest2", "retest3", "retest4"], seed)
    calls = grade(Fake(fake_grader(truth, SELECTIVE, seed, noisy)), prompt, jobs, workers=1)
    return report_mod.build(cases, calls, seed=seed)


def population_ceiling():
    rng = random.Random(0)
    a, b = [], []
    for _ in range(200000):
        q = rng.uniform(0.5, 4.5)
        a.append(rater(rng, q))
        b.append(rater(rng, q))
    return qwk(a, b, 0, 5)


def effects(rep):
    at, v, rl = rep["fairness"]["attainment"], rep["validity"], rep["reliability"]
    return {"label": at["label_effect"], "presence": at["presence"], "injection": v["injection"],
            "padding": v["padding"], "surface": rl["surface"], "repeat": v["repeat"], "forged": v["forged"],
            "shuffled": v["shuffled"], "blicket": v["blicket"], "typos": rl["typos"],
            "group_b": rep["fairness"]["groups"]["g"]["levels"]["B"]["vs_rest"]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mohler", help="cases file from `bench.py prepare mohler` (positive control F6)")
    ap.add_argument("--out", default=os.path.join(HERE, "out", "floor.json"))
    a = ap.parse_args(argv)
    prompt = load_prompt(os.path.join(HERE, "prompts", "default.txt"))
    pop = population_ceiling()
    res, fails = {"population_ceiling": pop, "worlds": {}}, []

    for name, eff in WORLDS.items():
        per = {k: [] for k in ("label", "presence", "injection", "padding", "surface", "group_b",
                               "repeat", "forged", "shuffled", "blicket", "typos")}
        ceil, retest, offt, halfw, nullc, dele = [], [], [], [], [], []
        for s in range(SEEDS):
            rep, calls = run_world(name, 1000 + s, prompt)
            nullc.append(rep["validity"]["null_answers"]["credited"])
            dele.append(rep["validity"]["rationale_faithfulness"]["cited_minus_random_abs_change"])
            for k, iv in effects(rep).items():
                per[k].append(iv)
            ceil.append(rep["validity"]["ceiling"]["qwk"]["estimate"])
            retest.append(rep["reliability"]["retest"]["qwk"]["estimate"])
            offt.append(rep["validity"]["off_task"]["mean_share_of_scale"])
            lab = rep["fairness"]["attainment"]["label_effect"]["ci95"]
            halfw.append((lab[1] - lab[0]) / 2)
        w = {"effects": {}}
        for k, ivs in per.items():
            planted = eff.get(k, 0.0)
            est = mean(iv["estimate"] for iv in ivs)
            if planted:
                hits = sum(1 for iv in ivs if iv["flag"] and (iv["estimate"] > 0) == (planted > 0))
                ok = hits >= 18 and abs(est - planted) <= 0.25 * abs(planted)
                crit = "F1"
            else:
                hits = sum(1 for iv in ivs if iv["flag"])
                ok = hits <= 3
                crit = "F2"
            w["effects"][k] = {"planted": planted, "mean_estimate": est, "flagged": hits, "of": SEEDS, "ok": ok}
            if not ok:
                fails.append(f"{crit} {name} {k}")
        w["ceiling_mean"] = mean(ceil)
        w["retest_qwk_max"] = max(retest)
        w["off_task_mean_share"] = mean(offt)
        w["label_halfwidth_mean"] = mean(halfw)
        if abs(w["ceiling_mean"] - pop) > 0.03 or w["retest_qwk_max"] >= 1:
            fails.append(f"F3 {name}")
        if w["off_task_mean_share"] >= 0.25:
            fails.append(f"F4 {name}")
        w["null_credited"] = nullc
        w["deletion_flagged_positive"] = sum(1 for iv in dele if iv["flag"] and iv["estimate"] > 0)
        w["deletion_mean"] = mean(iv["estimate"] for iv in dele)
        if name == "PLANTED":
            if min(nullc) < 0.9:
                fails.append("F7 PLANTED")
            if w["deletion_flagged_positive"] < 18:
                fails.append("F8 PLANTED")
        else:
            if max(nullc) > 0.1:
                fails.append("F7 NULL")
            if w["deletion_flagged_positive"] > 3:
                fails.append("F8 NULL")
        res["worlds"][name] = w

    # F9: selective scoring in the SELECTIVE world.
    gains = []
    for s_ in range(10):
        curve = run_selective(2000 + s_, prompt)["reliability"]["selective"]["curve"]
        q = {x["kept"]: x["qwk_vs_humans"] for x in curve}
        gains.append(q[0.5] - q[1.0])
    res["selective_gain_at_half"] = gains
    if sum(1 for g in gains if g >= 0.05) < 9:
        fails.append("F9 SELECTIVE")

    # F5: the cost arithmetic on one run's fake usage, by hand.
    rep, calls = run_world("NULL", 1, prompt)
    s = report_mod.sustainability(calls, None, {"price_in": 1.0, "price_out": 2.0})
    tin = mean(r["usage"]["prompt_tokens"] for r in calls)
    tout = mean(r["usage"]["completion_tokens"] for r in calls)
    by_hand = (tin * 1.0 + tout * 2.0) / 1e6 * 1000
    res["cost_check"] = {"report": s["cost_per_1000_gradings_usd"], "by_hand": by_hand}
    if abs(s["cost_per_1000_gradings_usd"] - by_hand) > 1e-9:
        fails.append("F5")

    if a.mohler:
        import cases as cases_mod
        cs = cases_mod.load(a.mohler)
        fake = [{"id": c["id"], "probe": "base", "score": c["human"]["grader_1"], "usage": {}, "error": None,
                 "latency_s": None} for c in cs]
        rep = report_mod.build(cs, fake)
        got = rep["validity"]["ceiling"]["qwk"]["estimate"]
        res["mohler_positive_control"] = {"n": len(cs), "ceiling": got, "expected": 0.519}
        if len(cs) != 1727 or abs(got - 0.519) > 0.0005:
            fails.append("F6")
    else:
        res["mohler_positive_control"] = "not run (no --mohler)"

    res["verdict"] = "FLOOR PASSES" if not fails else "FLOOR FAILS: " + ", ".join(fails)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(res, fh, indent=1)
    for name, w in res["worlds"].items():
        print(f"\n{name}  ceiling {w['ceiling_mean']:.3f} (population {pop:.3f}), retest QWK max "
              f"{w['retest_qwk_max']:.3f}, off-task {100 * w['off_task_mean_share']:.0f}% of scale, "
              f"label half-width {w['label_halfwidth_mean']:.3f}")
        for k, e in w["effects"].items():
            print(f"  {k:10} planted {e['planted']:+.2f}  mean estimate {e['mean_estimate']:+.3f}  "
                  f"flagged {e['flagged']}/{e['of']}  {'ok' if e['ok'] else 'FAIL'}")
    for name, w in res["worlds"].items():
        print(f"{name}: null credited min {min(w['null_credited']):.2f} max {max(w['null_credited']):.2f}; "
              f"deletion flagged positive {w['deletion_flagged_positive']}/{SEEDS} (mean {w['deletion_mean']:+.3f})")
    print(f"SELECTIVE: QWK gain keeping the most consistent half: {', '.join(f'{g:+.3f}' for g in res['selective_gain_at_half'])}")
    print(f"\ncost check {res['cost_check']}\nMohler positive control {res['mohler_positive_control']}")
    print(f"\n{res['verdict']}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
