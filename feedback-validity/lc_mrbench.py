"""
Learning Commons' Withholding Answers and Revision Actionability evaluators against MRBench's trained
annotators: an OUT-OF-SCOPE stress test.

PRE-REGISTERED 2026-10-24, before any call. MRBench's labels were read for validate.py (1d22f184), so
the class sizes below are known; no evaluator output exists.

WHY. `(private pre-registration)` fixed an in-scope test of Learning
Commons' seven Feedback evaluators and found no data for it. MRBench (registry id `mrbench`) has
trained annotators' labels for two of the same constructs, on maths tutoring rather than the
evaluators' scope (Quill "because" completions, grades 6-12, ELA writing). That makes this a stress
test: a pass says the construct travels to tutoring; a failure is NOT evidence against the evaluators
in their own scope. Every report of this result must say so.

| evaluator (Learning Commons, clone b9d4789) | MRBench label | evaluator 1 should go with |
|---|---|---|
| feedback.ela_writing.withholding_answers ("Does the feedback avoid giving away the answer?") | Revealing_of_the_Answer | "No" (not revealed) |
| feedback.ela_writing.revision_actionability | Actionability | "Yes" |

Not tested: Tone Appropriateness. Its criterion counts neutral, professional language as meeting it,
so MRBench's Encouraging vs Neutral is not its construct, and MRBench has 1 Offensive response:
UNANSWERABLE here. The other four Feedback evaluators have no MRBench counterpart.

HOW THE EVALUATORS ARE CALLED. Their own system.txt and user.txt, rendered with student_text = the
MRBench conversation_history (which ends with the student's mistake) and feedback_text = the tutor
response; their output_schema.json as a strict JSON schema; their default model and temperature
(openai/gpt-5.4, T = 1), through OpenRouter with zero data retention. Not through their SDK: the
prompts, schema, model and temperature are the evaluator, and the SDK adds validation and resampling
on a parse failure, which here is one retry. Score = quality_score.

SAMPLES (seed 20261024, from MRBench_V2.json):
- WITHHOLD: all 266 responses labelled "Yes (and the answer is correct)" or "Yes (but the answer is
  incorrect)", plus 334 drawn at random from the 1,389 labelled "No": 600.
- ACTION: 300 drawn from the 916 "Yes" and 300 from the 541 "No"; "To some extent" left out: 600.
- RETEST: the first 100 of each sample by response id, called a second time (T = 1).
1,400 calls in all.

STATISTIC. For a binary score the AUC is the balanced accuracy, (sensitivity + specificity) / 2, with
a 95% interval from a bootstrap over DIALOGUES (validate.evaluate). Cohen's kappa is reported beside
it; on these stratified samples it is not comparable to a population kappa. The content-free bar is
response length in its better direction, as in validate.py. Annotator agreement on MRBench, the
ceiling: Cohen's kappa 0.71 (paper), Fleiss' 0.65 (BEA 2025).

VERDICTS (validate.py's thresholds):
- VALIDATED: the AUC interval's lower bound exceeds 0.60 and the difference from length has its lower
  bound above 0.
- VALID, NOT BEYOND LENGTH; NOT VALIDATED (upper bound below 0.60); WRONG DIRECTION (upper bound
  below 0.50); INCONCLUSIVE.
- Retest exact agreement is reported, not a verdict.
Parse failures after the retry are reported and left out; if they exceed 5% in either class the
verdict carries that warning.

FLOOR (`--floor`, before any call). On each real sample and its dialogue structure, a simulated binary
evaluator that agrees with the human label with probability p, tuned to a population AUC of 0.72:
VALIDATED in at least 45 of 50 seeds. A simulated evaluator whose output follows length only, at the
same strength: VALIDATED in at most 3 of 50. A coin-flip evaluator: VALIDATED in at most 3 of 50.

    python3 lc_mrbench.py --floor
    python3 lc_mrbench.py --run --go       # calls the model; --run alone is a dry run with a cost estimate
    python3 lc_mrbench.py --analyse

CHANGES:
1. (after one smoke call, which returned HTTP 400 and no output) OpenAI's strict structured output
   rejects keywords beside a $ref, which output_schema.json uses. The schema's $defs are inlined; no
   field, type, enum or requirement changes. The `$schema` and `$id` metadata keys are dropped for the
   same reason.
"""

import argparse
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import validate as V  # noqa: E402
from client import OpenAICompatible  # noqa: E402

LC = os.environ.get("LC_EVALUATORS_DIR", "evaluators")
SEED = 20261024
MODEL = "openai/gpt-5.4"
EVALUATORS = {
    "WITHHOLD": ("withholding-answers", "Revealing_of_the_Answer",
                 {"No"}, {"Yes (and the answer is correct)", "Yes (but the answer is incorrect)"}),
    "ACTION": ("revision-actionability", "Actionability", {"Yes"}, {"No"}),
}
RUN_DIR = os.environ.get("LC_MRBENCH_RUN", "runs/lc-mrbench")


def rows():
    out = []
    root = os.environ.get("MRBENCH_DIR")
    data = json.load(open(os.path.join(root, "MRBench", "MRBench_V2.json")))
    for d in data:
        for tutor, r in d["anno_llm_responses"].items():
            out.append({"rid": f"{d['conversation_id']}|{tutor}", "dialogue": d["conversation_id"], "tutor": tutor,
                        "history": d["conversation_history"], "text": r["response"] or "", "labels": r["annotation"]})
    return out


def samples(rs):
    rng = random.Random(SEED)
    w_pos = [r for r in rs if r["labels"]["Revealing_of_the_Answer"] in EVALUATORS["WITHHOLD"][3]]
    w_neg = sorted([r for r in rs if r["labels"]["Revealing_of_the_Answer"] == "No"], key=lambda r: r["rid"])
    a_yes = sorted([r for r in rs if r["labels"]["Actionability"] == "Yes"], key=lambda r: r["rid"])
    a_no = sorted([r for r in rs if r["labels"]["Actionability"] == "No"], key=lambda r: r["rid"])
    s = {"WITHHOLD": sorted(w_pos, key=lambda r: r["rid"]) + rng.sample(w_neg, 600 - len(w_pos)),
         "ACTION": rng.sample(a_yes, 300) + rng.sample(a_no, 300)}
    return s


def human_y(name, r):
    """1 where the evaluator should output 1."""
    _, field, good, bad = EVALUATORS[name]
    lab = r["labels"][field]
    return 1 if lab in good else 0 if lab in bad else None


def messages(name, r):
    d = os.path.join(LC, "evals", "feedback", "ela-writing", EVALUATORS[name][0])
    system = open(os.path.join(d, "system.txt")).read()
    user = open(os.path.join(d, "user.txt")).read()
    user = user.replace("{student_text}", r["history"]).replace("{feedback_text}", r["text"])
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def schema(name):
    d = os.path.join(LC, "evals", "feedback", "ela-writing", EVALUATORS[name][0])
    sch = json.load(open(os.path.join(d, "output_schema.json")))
    for k in ("$schema", "$id"):  # metadata keys; strict structured output rejects them, the schema is unchanged
        sch.pop(k, None)
    defs = sch.pop("$defs", {})

    def inline(x):  # CHANGE 1: strict mode forbids keywords beside a $ref, so definitions are inlined
        if isinstance(x, dict):
            if "$ref" in x:
                base = dict(defs[x["$ref"].split("/")[-1]])
                base.update({k: v for k, v in x.items() if k != "$ref"})
                return inline(base)
            return {k: inline(v) for k, v in x.items()}
        if isinstance(x, list):
            return [inline(v) for v in x]
        return x
    sch = inline(sch)
    return {"type": "json_schema", "json_schema": {"name": "EvaluatorOutput", "strict": True, "schema": sch}}


def parse(text):
    try:
        v = json.loads(text)["quality_score"]
        return int(v) if v in (0, 1) else None
    except (TypeError, ValueError, KeyError):
        return None


def items(name, sample, score_of):
    """validate.py's item tuples: (dialogue, tutor, rule score, length, y)."""
    out = []
    for r in sample:
        s = score_of(r)
        if s is None:
            continue
        out.append((r["dialogue"], r["tutor"], float(s), V.words(r["text"]), human_y(name, r)))
    return out


def cmd_floor(s):
    res = {}
    for name, sample in s.items():
        ys = [human_y(name, r) for r in sample]
        counts = {"PLANTED": 0, "LENGTH-ONLY": 0, "COIN": 0}
        for seed in range(50):
            rng = random.Random(f"lcfloor-{name}-{seed}")
            p = 0.72  # binary: balanced accuracy = p when errors are symmetric
            planted = {r["rid"]: (y if rng.random() < p else 1 - y) for r, y in zip(sample, ys)}
            lens = sorted(V.words(r["text"]) for r in sample)
            cut = lens[len(lens) // 2]
            # length-only evaluator, at the same strength in its own terms
            lonly = {r["rid"]: ((1 if V.words(r["text"]) >= cut else 0) if rng.random() < p else rng.randrange(2)) for r in sample}
            coin = {r["rid"]: rng.randrange(2) for r in sample}
            for key, sc in (("PLANTED", planted), ("LENGTH-ONLY", lonly), ("COIN", coin)):
                ev = V.evaluate(items(name, sample, lambda r, _s=sc: _s[r["rid"]]), False, seed=seed, reps=300)
                counts[key] += V.verdict(ev) == "VALIDATED"
        res[name] = {"validated_of_50": counts, "n": len(sample), "positive": sum(ys),
                     "pass": counts["PLANTED"] >= 45 and counts["LENGTH-ONLY"] <= 3 and counts["COIN"] <= 3}
        print(name, res[name])
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    json.dump(res, open(os.path.join(HERE, "out", "lc-floor.json"), "w"), indent=1)
    print("FLOOR PASSES" if all(v["pass"] for v in res.values()) else "FLOOR FAILS")


def jobs(s):
    out = []
    for name, sample in s.items():
        for r in sample:
            out.append((name, r, "main"))
        for r in sorted(sample, key=lambda r: r["rid"])[:100]:
            out.append((name, r, "retest"))
    return out


def cmd_run(s, go):
    js = jobs(s)
    chars = sum(len(m["content"]) for n, r, _ in js for m in messages(n, r))
    est = chars / 4 * 2.5e-6 + len(js) * 900 * 15e-6
    print(f"{len(js)} calls, about {chars / 4 / 1e6:.2f}M prompt tokens; estimate ${est:.2f} at list price "
          f"assuming 900 output tokens a call")
    if not go:
        return
    from concurrent.futures import ThreadPoolExecutor
    cl = OpenAICompatible("https://openrouter.ai/api/v1", MODEL, key_env="OPENROUTER_API_KEY",
                          cache_dir=os.path.join(RUN_DIR, ".cache"),
                          temperature=1, extra={"usage": {"include": True}, "provider": {"zdr": True}})
    os.makedirs(RUN_DIR, exist_ok=True)

    def one(job):
        name, r, tag = job
        rec = cl.call(messages(name, r), tag=f"{name}|{tag}", extra={"response_format": schema(name)})
        sc = parse(rec["text"]) if rec["error"] is None else None
        if sc is None:
            rec = cl.call(messages(name, r), tag=f"{name}|{tag}|retry", extra={"response_format": schema(name)})
            sc = parse(rec["text"]) if rec["error"] is None else None
        return {"evaluator": name, "rid": r["rid"], "tag": tag, "score": sc, "error": rec["error"],
                "usage": rec["usage"], "served_model": rec["served_model"], "provider": rec["provider"]}

    with ThreadPoolExecutor(6) as ex:
        out = list(ex.map(one, js))
    with open(os.path.join(RUN_DIR, "calls.jsonl"), "w") as fh:
        for o in out:
            fh.write(json.dumps(o) + "\n")
    cost = sum((o["usage"].get("cost_reported") or 0) for o in out)
    print(f"{len(out)} calls, {sum(o['score'] is None for o in out)} unparsed, ${cost:.2f} reported")


def cmd_analyse(s):
    calls = [json.loads(l) for l in open(os.path.join(RUN_DIR, "calls.jsonl"))]
    main = {(c["evaluator"], c["rid"]): c["score"] for c in calls if c["tag"] == "main"}
    ret = {(c["evaluator"], c["rid"]): c["score"] for c in calls if c["tag"] == "retest"}
    res = {"design": "lc_mrbench.py docstring", "scope": "OUT OF SCOPE: maths tutoring, not the evaluators' ELA writing",
           "model_served": sorted({c["served_model"] for c in calls if c["served_model"]}),
           "cost_reported_usd": sum((c["usage"].get("cost_reported") or 0) for c in calls), "evaluators": {}}
    for name, sample in s.items():
        its = items(name, sample, lambda r: main.get((name, r["rid"])))
        ev = V.evaluate(its, False)
        ys = [human_y(name, r) for r in sample]
        miss = {k: sum(1 for r, y in zip(sample, ys) if y == k and main.get((name, r["rid"])) is None) /
                max(1, sum(1 for y in ys if y == k)) for k in (0, 1)}
        tp = sum(1 for it in its if it[2] == 1 and it[4] == 1)
        tn = sum(1 for it in its if it[2] == 0 and it[4] == 0)
        n = len(its)
        po = (tp + tn) / n
        p1 = sum(it[2] for it in its) / n
        q1 = sum(it[4] for it in its) / n
        pe = p1 * q1 + (1 - p1) * (1 - q1)
        pairs = [(main.get((name, k[1])), v) for k, v in ret.items() if k[0] == name and v is not None and main.get((name, k[1])) is not None]
        r_ = {**ev, "verdict": V.verdict(ev), "kappa": (po - pe) / (1 - pe) if pe < 1 else None,
              "sensitivity": tp / max(1, sum(it[4] for it in its)), "specificity": tn / max(1, n - sum(it[4] for it in its)),
              "evaluator_rate_1": p1, "missing_by_class": miss,
              "retest_exact": sum(a == b for a, b in pairs) / len(pairs) if pairs else None, "retest_n": len(pairs)}
        if max(miss.values()) > 0.05:
            r_["warning"] = "more than 5% of a class unparsed"
        res["evaluators"][name] = r_
        print(name, r_["verdict"], f"AUC {ev['auc']:.3f} [{ev['auc_ci'][0]:.3f}, {ev['auc_ci'][1]:.3f}]",
              f"length {ev['length_auc']:.3f}", f"kappa {r_['kappa']:.3f}", f"retest {r_['retest_exact']}")
    json.dump(res, open(os.path.join(HERE, "out", "lc-result.json"), "w"), indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--floor", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--go", action="store_true")
    ap.add_argument("--analyse", action="store_true")
    a = ap.parse_args()
    s = samples(rows())
    if a.floor:
        cmd_floor(s)
    elif a.run:
        cmd_run(s, a.go)
    elif a.analyse:
        cmd_analyse(s)


if __name__ == "__main__":
    main()
