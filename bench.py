#!/usr/bin/env python3
"""
bench.py — an AI-grading benchmark you run yourself: your model, your prompt, data you fetched.

Standard library only. Python 3.8+.

    python3 bench.py prepare mohler --src mohler_en.csv --out mohler.jsonl
    python3 bench.py run --cases mohler.jsonl --prompt prompts/default.txt \\
        --base-url https://openrouter.ai/api/v1 --model openai/gpt-5-mini --key-env OPENROUTER_API_KEY \\
        --n 200 --out runs/gpt5mini-default                  # prints the plan and stops
    python3 bench.py run ... --go                            # makes the calls
    python3 bench.py score runs/gpt5mini-default --price-in 0.25 --price-out 2.00
    python3 bench.py compare runs/gpt5mini-default runs/gpt5mini-mine
    python3 floor.py                                         # the detection floor; no model, no data

It reports four things a decision to use AI marking turns on (report.py's docstring defines each):

    validity       does it agree with human markers, as a share of how well they agree with each other;
                   is it moved by padding, by an instruction hidden in the work, by work for another task
    reliability    does it give the same mark twice, and when the same work is laid out differently
    fairness       does telling it a learner's prior attainment move the mark on identical work;
                   are its errors the same size for each group the data records
    sustainability tokens, latency, cost, and energy and carbon from coefficients you supply

BRING YOUR OWN PROMPT. `--prompt` is a template or a Python file (prompting.py's docstring). The
benchmark's own `prompts/default.txt` is a plain, neutral prompt and a reference point, not a
recommendation. Run your prompt and the default on the same cases and `compare` them: the
difference is what your prompt buys, with an interval.

BRING YOUR OWN DATA. Nothing is shipped. `prepare` turns Mohler or ASAP 2.0 into the case format
(cases.py), or write your own cases in it.

WHAT A RUN COSTS. Every case is graded once per probe that changes it: up to fourteen calls a case,
so 200 cases is up to 2,800 calls. `run` without `--go` prints this and the size of one prompt, and sends nothing.
`--max-calls` (default 3,000) refuses a bigger plan; `--max-usd` stops sending once the endpoint's
reported spend reaches it.

WHAT IS WRITTEN. `<out>/config.json` (endpoint, model, parameters, prompt and cases hashes, the
seed), `<out>/calls.jsonl` (one line per grading: mark, usage, latency, the model that answered;
the reply text too, which can quote student work, so keep run folders out of version control),
`<out>/report.json` and `<out>/report.md` (aggregates only).
"""

import argparse
import hashlib
import json
import re
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import cases as cases_mod  # noqa: E402
import report as report_mod  # noqa: E402
from client import OpenAICompatible  # noqa: E402
from prompting import (CONTEXT_PROBES, DELETION_PROBES, NULL_CASES, NULL_PROBES, PROBES, cited_and_random,  # noqa: E402
                       MEDIA_NULL_PROBES, attach_media, off_task_cases, probe_media, text_len,  # noqa: E402
                       load_prompt, off_task_map, probe_input)

VERSION = "0.2.0"

# Batteries: named probe sets and sample sizes, so a typical user runs "core" and never pays for the
# research battery. A --probes or --n given on the command line overrides the battery's.
BATTERIES = {
    "full": {"n": 200, "probes": [p for p in PROBES if p not in ("retest2", "retest3", "retest4")]},
    "core": {"n": 100, "probes": ["base", "retest", "injection", "forged", "blicket", "off_task", "ctx_low", "ctx_high",
                                  *NULL_PROBES]},
    "abstain": {"n": 200, "probes": ["base", "retest", "retest2", "retest3", "retest4"]},
    "faithful": {"n": 200, "probes": ["base", *DELETION_PROBES]},
    "anchor": {"n": 30, "probes": ["base", "retest", "retest2"]},
    # What the public leaderboard ranks (leaderboard.py): agreement, consistency, the two gaming probes, the
    # attainment label, blicket, surface sensitivity and blank answers. Prose probes skip code by themselves.
    "leaderboard": {"n": 100, "probes": ["base", "retest", "injection", "forged", "blicket", "surface", "ctx_low",
                                         "ctx_high", *NULL_PROBES]},
    # The maths-working task (maths-process/): every problem in its four versions, graded once.
    "maths": {"n": 800, "probes": ["base"]},
}
# Probes written for prose: on code they either change nothing or change what the program means.
PROSE_PROBES = {"surface", "typos", "repeat", "shuffled", "blicket", "del_cited", "del_random"}


def looks_like_code(text):
    t = text or ""
    if re.search(r"#include|\bint main\b|\bdef \w+\(|\bpublic (?:static )?\w+|\bcout\s*<<|\bprintf\(", t):
        return True
    lines = max(1, t.count("\n") + 1)
    return (t.count(";") + t.count("{") + t.count("}")) / lines > 0.6


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def plan(cases, pool, prompt, probes, seed):
    """Every grading to make: (case, probe, messages). A probe that would not change a case is skipped."""
    if not prompt.context_slot:
        probes = [p for p in probes if p not in CONTEXT_PROBES]
    if not any(c.get("media") for c in cases):
        probes = [p for p in probes if p not in MEDIA_NULL_PROBES + ("noise_10db", "phone_band")]
    ot = off_task_map(cases, pool, seed) if "off_task" in probes else {}
    ot_case = off_task_cases(cases, pool, seed) if "off_task" in probes and any(c.get("media") for c in cases) else {}
    if "off_task" in probes and not ot:
        probes = [p for p in probes if p != "off_task"]
    # Null answers do not depend on the case, so they run on one case per task, up to NULL_CASES.
    first = {}
    for c in sorted(cases, key=lambda c: c["id"]):
        first.setdefault(c["task"], c["id"])
    null_ids = set(sorted(first.values())[:NULL_CASES])
    if any((c.get("media") or [{}])[0].get("kind") == "video" for c in cases):
        # A video task has few task labels (LASANA has four), so the blank-video probes run on the first
        # NULL_CASES cases by id instead: one per task would leave too few for a hallucination rate.
        null_ids = {c["id"] for c in sorted(cases, key=lambda c: c["id"])[:NULL_CASES]}
    jobs = []
    for c in cases:
        code = looks_like_code(c["response"])
        for p in probes:
            if p in DELETION_PROBES or (code and p in PROSE_PROBES) or (p in NULL_PROBES and c["id"] not in null_ids):
                continue
            got = probe_input(c, p, ot.get(c["id"]), seed)
            if got is None:
                continue
            msgs = prompt.build(c, *got)
            if c.get("media"):
                parts = probe_media(c, p, ot_case.get(c["id"]), seed)
                if parts is None:
                    continue
                msgs = attach_media(msgs, parts)
            jobs.append((c, p, msgs))
    return jobs, probes


def deletion_jobs(cases, calls, prompt, seed):
    """Phase two: for each base grading with a rationale, the response with the sentence the rationale
    leans on deleted, and with a random other sentence deleted (prompting.cited_and_random)."""
    from feedback import feedback_text
    by_id = {c["id"]: c for c in cases}
    jobs = []
    for r in calls:
        if r["probe"] != "base" or r.get("score") is None or looks_like_code(by_id[r["id"]]["response"]):
            continue
        rationale, _ = feedback_text(r.get("text"))
        got = cited_and_random(by_id[r["id"]]["response"], rationale, f"{seed}|{r['id']}")
        if got:
            c = by_id[r["id"]]
            jobs.append((c, "del_cited", prompt.build(c, got[0], "")))
            jobs.append((c, "del_random", prompt.build(c, got[1], "")))
    return jobs


_PRICES = {}


def openrouter_price(model):
    """(USD per prompt token, per completion token) from OpenRouter's public model list, or None."""
    if not _PRICES:
        try:
            import urllib.request
            with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=30) as resp:
                for m in json.loads(resp.read().decode())["data"]:
                    _PRICES[m["id"]] = (float(m["pricing"]["prompt"]), float(m["pricing"]["completion"]))
        except Exception:  # noqa: BLE001 - an estimate is optional
            return None
    return _PRICES.get(model)


def grade(client, prompt, jobs, workers, log=None, max_usd=None, cached_only=False):
    """Grade every job. With max_usd, stop sending once the endpoint-reported spend reaches it: the
    remaining jobs are recorded as not sent, never silently dropped."""
    spent = [0.0]
    lock = threading.Lock()
    rf = getattr(prompt, "response_format", None)

    def one(job):
        c, p, msgs = job
        with lock:
            over = max_usd is not None and spent[0] >= max_usd
        if over:
            rec = {"text": None, "usage": {}, "latency_s": None, "served_model": None, "provider": None,
                   "error": f"not sent: spend cap ${max_usd} reached", "cached": False}
        else:
            fmt = rf(c) if callable(rf) else rf
            rec = client.call(msgs, tag=p, extra={"response_format": fmt} if fmt else None,
                              **({"cached_only": True} if cached_only else {}))
            if not rec.get("cached"):
                with lock:
                    spent[0] += rec["usage"].get("cost_reported") or 0.0
        lo, hi = c["scale"]
        score = prompt.parse(rec["text"], lo, hi) if rec["error"] is None else None
        return {"id": c["id"], "task": c["task"], "probe": p, "score": score, **rec}

    out, t0 = [], time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for i, r in enumerate(ex.map(one, jobs), 1):
            out.append(r)
            if log and (i % 200 == 0 or i == len(jobs)):
                bad = sum(1 for x in out if x["score"] is None)
                log(f"  {i}/{len(jobs)} gradings, {bad} without a mark, ${spent[0]:.2f} reported, {time.time() - t0:.0f}s")
    return out


def cmd_prepare(a):
    cs = cases_mod.LOADERS[a.corpus](a.src)
    cases_mod.write(cs, a.out)
    tasks = len({c["task"] for c in cs})
    multi = sum(1 for c in cs if len(c["human"]) >= 2)
    print(f"{len(cs)} cases, {tasks} tasks, {multi} with two or more human raters -> {a.out}")


def cmd_run(a):
    pool = cases_mod.load(a.cases)
    prompt = load_prompt(a.prompt)
    bat = BATTERIES[a.battery]
    if a.n is None:
        a.n = bat["n"]
    cs = cases_mod.sample(pool, a.n, a.seed)
    if a.probes is None:
        probes = list(bat["probes"])
    else:
        probes = [p.strip() for p in a.probes.split(",")] if a.probes != "all" else list(PROBES)
    bad = [p for p in probes if p not in PROBES]
    if bad:
        sys.exit(f"unknown probe(s) {', '.join(bad)}; choose from {', '.join(PROBES)}")
    if "base" not in probes:
        sys.exit("the base probe is required: every other probe is read against it")
    import prompting
    prompting.VIDEO_FRAMES = a.video_frames
    jobs, probes = plan(cs, pool, prompt, probes, a.seed)
    skipped = sorted(set(PROBES if a.probes == "all" else probes) - set(probes))
    size = max(text_len(j[2]) for j in jobs)
    n_del = 2 * len(cs) if any(p in DELETION_PROBES for p in probes) else 0
    print(f"battery {a.battery}: {len(cs)} cases, {len(jobs)} gradings" + (f" (+ up to {n_del} deletion gradings in phase two)" if n_del else "")
          + f" with {a.model} at {a.base_url}")
    print(f"probes: {', '.join(probes)}" + (f"   (not run: {', '.join(skipped)})" if skipped else ""))
    print(f"largest prompt: {size:,} characters (about {size // 4:,} tokens)")
    price = openrouter_price(a.model) if "openrouter.ai" in a.base_url else None
    if price:
        tin = sum(text_len(j[2]) for j in jobs) / 3.6
        tout = (len(jobs) + n_del) * a.assume_out
        est = tin * price[0] * (1 + n_del / max(1, len(jobs))) + tout * price[1]
        print(f"estimated cost ${est:,.2f} at OpenRouter list prices, assuming {a.assume_out} output tokens a grading "
              "(reasoning models can use several times that)")
    if len(jobs) > a.max_calls:
        sys.exit(f"refused: {len(jobs)} calls exceeds --max-calls {a.max_calls}")
    pin = ((json.loads(a.extra_body) if a.extra_body else {}).get("provider") or {}).get("quantizations")
    if "openrouter.ai" in a.base_url and not pin:
        # docs/METHODOLOGY.md 2.2: an open model on a router is served at whatever precision the host runs; at 4-bit
        # the same model was far easier to game (hosting/). Closed models publish no precision: ignore this for them.
        print("note: precision not pinned; for an open-weights model add provider.quantizations (e.g. [\"fp8\", "
              "\"bf16\"]) and a --label")
    if not a.go:
        print("dry run: nothing sent. Add --go to make the calls.")
        return
    extra = json.loads(a.extra_body) if a.extra_body else None
    client = OpenAICompatible(a.base_url, a.model, a.key_env, a.cache_dir or os.path.join(a.out, ".cache"),
                              temperature=a.temperature, max_tokens=a.max_tokens, extra=extra,
                              retention_exception=a.retention_exception)
    if a.key_env and not client.key:
        sys.exit(f"no key: set {a.key_env} in the environment or a .env file (never on the command line)")
    print(f"key from {client.key_source}" if client.key_source else "no key sent")
    os.makedirs(a.out, exist_ok=True)
    config = {
        "benchmark_version": VERSION, "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "base_url": a.base_url, "model": a.model, "request_template": client.body([]),
        "temperature": a.temperature, "max_tokens": a.max_tokens, "extra_body": extra,
        "prompt": os.path.basename(a.prompt), "prompt_path": os.path.abspath(a.prompt), "prompt_sha256": prompt.sha256,
        "battery": a.battery if a.probes is None else "custom",
        "context_slot": prompt.context_slot, "response_format": bool(getattr(prompt, "response_format", None)), "cases": a.cases,
        "cases_sha256": file_sha256(a.cases), "n": len(cs), "seed": a.seed, "probes": probes,
        "case_ids": [c["id"] for c in cs], "video_frames": a.video_frames,
        "retention_exception": a.retention_exception, "route": a.route,
        "key_env": a.key_env,  # the variable's name only, never its value
        "precision_pin": ((extra or {}).get("provider") or {}).get("quantizations"),  # None: unpinned
        "label": a.label,  # a row name when one model is entered in more than one setup (e.g. "<model>@8bit")
    }
    with open(os.path.join(a.out, "config.json"), "w") as fh:
        json.dump(config, fh, indent=1)
    calls = grade(client, prompt, jobs, a.workers, log=print, max_usd=a.max_usd, cached_only=a.cached_only)
    if any(p in DELETION_PROBES for p in probes):
        dj = deletion_jobs(cs, calls, prompt, a.seed)
        print(f"phase two: {len(dj)} deletion gradings")
        spent = sum((r["usage"].get("cost_reported") or 0) for r in calls if not r.get("cached"))
        calls += grade(client, prompt, dj, a.workers, log=print,
                       max_usd=None if a.max_usd is None else max(0.0, a.max_usd - spent), cached_only=a.cached_only)
    with open(os.path.join(a.out, "calls.jsonl"), "w", encoding="utf-8") as fh:
        for r in calls:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    errors = sum(1 for r in calls if r["error"])
    if errors:
        print(f"{errors} calls failed after retries; first: {next(r['error'] for r in calls if r['error'])}")
    print(f"wrote {a.out}/calls.jsonl. Next: python3 bench.py score {a.out}")


def load_run(run, cases_path=None):
    with open(os.path.join(run, "config.json")) as fh:
        config = json.load(fh)
    path = cases_path or config["cases"]
    if not os.path.exists(path):
        sys.exit(f"cases file {path} not found; pass --cases")
    if file_sha256(path) != config["cases_sha256"]:
        sys.exit(f"{path} is not the cases file this run graded (sha256 differs)")
    by_id = {c["id"]: c for c in cases_mod.load(path)}
    cs = [by_id[i] for i in config["case_ids"]]
    with open(os.path.join(run, "calls.jsonl"), encoding="utf-8") as fh:
        calls = [json.loads(l) for l in fh if l.strip()]
    return config, cs, calls


def prices_from(a):
    return {"price_in": a.price_in, "price_out": a.price_out, "wh_per_1k_tokens": a.wh_per_1k_tokens,
            "gco2_per_kwh": a.gco2_per_kwh, "human_minutes": a.human_minutes, "human_rate": a.human_rate}


def cmd_score(a):
    config, cs, calls = load_run(a.run, a.cases)
    rep = report_mod.build(cs, calls, prices_from(a), a.pass_mark)
    # A report may be committed: keep only the file name of any machine-local path in its config.
    rep["config"] = {k: (os.path.basename(v) if isinstance(v, str) and os.path.isabs(v) else v)
                     for k, v in config.items() if k != "case_ids"}
    with open(os.path.join(a.run, "report.json"), "w") as fh:
        json.dump(rep, fh, indent=1)
    md = render_md(rep)
    with open(os.path.join(a.run, "report.md"), "w") as fh:
        fh.write(md)
    print(md)


def cmd_compare(a):
    """Paired differences between two runs on the cases both graded: B minus A."""
    from metrics import bootstrap, interval, mean, qwk
    ca, csa, calls_a = load_run(a.a, a.cases)
    cb, csb, calls_b = load_run(a.b, a.cases)
    sa = {(r["id"], r["probe"]): r["score"] for r in calls_a if r["score"] is not None}
    sb = {(r["id"], r["probe"]): r["score"] for r in calls_b if r["score"] is not None}
    shared = [c for c in csa if c["id"] in {x["id"] for x in csb}
              and (c["id"], "base") in sa and (c["id"], "base") in sb]
    if len(shared) < 20:
        sys.exit(f"only {len(shared)} cases graded by both runs; need 20+")
    lo, hi = shared[0]["scale"]
    raters = sorted({k for c in shared for k in c["human"]})

    def q(s, cs):
        vals = []
        for rt in raters:
            p = [(c["human"][rt], s[(c["id"], "base")]) for c in cs if rt in c["human"]]
            if len(p) >= 2:
                vals.append(qwk([x[0] for x in p], [x[1] for x in p], lo, hi))
        return mean(vals)

    def label(s, cs):
        d = [s[(c["id"], "ctx_high")] - s[(c["id"], "ctx_low")] for c in cs
             if (c["id"], "ctx_high") in s and (c["id"], "ctx_low") in s]
        return mean(d)

    rows = [("QWK vs humans", lambda cs: q(sb, cs) - q(sa, cs))]
    if any(k[1] == "ctx_high" for k in sa) and any(k[1] == "ctx_high" for k in sb):
        rows.append(("attainment label effect", lambda cs: label(sb, cs) - label(sa, cs)))
    print(f"B = {a.b} ({cb['prompt']}, {cb['model']})\nA = {a.a} ({ca['prompt']}, {ca['model']})")
    print(f"{len(shared)} cases graded by both\n")
    for name, f in rows:
        iv = interval(*bootstrap(shared, f))
        print(f"  {name:28} B - A = {iv['estimate']:+.3f}  [{iv['ci95'][0]:+.3f}, {iv['ci95'][1]:+.3f}]")
    for side, run, cfg, cs, calls in (("A", a.a, ca, csa, calls_a), ("B", a.b, cb, csb, calls_b)):
        s = report_mod.sustainability(calls, cs, prices_from(a))
        pg = s["per_grading"] or {}
        cost = s["cost_per_1000_gradings_usd"]
        print(f"  {side}: {pg.get('prompt_tokens', 0):.0f} in / {pg.get('completion_tokens', 0):.0f} out tokens per grading"
              + (f", ${cost:.2f} per 1,000" if cost is not None else ""))


def cmd_drift(a):
    """Has a model's marking moved? Base marks of run B against run A on the cases both graded (the
    anchor battery: the same frozen cases, re-run after a provider update or on an older release).
    Read against A's own retest noise: a shift within it is not drift."""
    from metrics import bootstrap, interval, mean, qwk
    ca, csa, calls_a = load_run(a.a, a.cases)
    cb, csb, calls_b = load_run(a.b, a.cases)
    sa = {(r["id"], r["probe"]): r["score"] for r in calls_a if r["score"] is not None}
    sb = {(r["id"], r["probe"]): r["score"] for r in calls_b if r["score"] is not None}
    ids = [c["id"] for c in csa if (c["id"], "base") in sa and (c["id"], "base") in sb]
    if len(ids) < 10:
        sys.exit(f"only {len(ids)} cases graded by both; need 10+")
    lo, hi = csa[0]["scale"]
    diffs = [sb[(i, "base")] - sa[(i, "base")] for i in ids]
    iv = interval(*bootstrap(diffs, mean))
    cross = qwk([sa[(i, "base")] for i in ids], [sb[(i, "base")] for i in ids], lo, hi)
    rt = [i for i in ids if (i, "retest") in sa]
    within = qwk([sa[(i, "base")] for i in rt], [sa[(i, "retest")] for i in rt], lo, hi) if len(rt) >= 10 else None
    served = lambda calls: sorted({str(r.get("served_model")) for r in calls if r.get("error") is None})
    print(f"A = {a.a} ({ca['model']}, started {ca.get('started')}); served as {', '.join(served(calls_a))}")
    print(f"B = {a.b} ({cb['model']}, started {cb.get('started')}); served as {', '.join(served(calls_b))}")
    print(f"{len(ids)} cases graded by both\n")
    print(f"  mean shift B - A        {iv['estimate']:+.3f} [{iv['ci95'][0]:+.3f}, {iv['ci95'][1]:+.3f}] marks")
    print(f"  agreement A with B      QWK {cross:.3f}")
    if within is not None:
        print(f"  agreement A with itself QWK {within:.3f} (same version, asked twice)")
    moved = iv["ci95"][0] > 0 or iv["ci95"][1] < 0
    print("\n  " + ("DRIFT: marks moved" if moved else "no shift in mean marks detected")
          + ("; individual marks agree less across versions than within one" if within is not None and cross < within - 0.05 else ""))


def cmd_generate(a):
    """AI-written answers for the self-preference test: each generator model writes a strong, a
    partial and a weak student answer to the same sampled questions. Written to a cases file with no
    human marks; every grader then grades every generator's answers (bench.py run --probes base)."""
    pool = cases_mod.load(a.cases)
    tasks = {}
    for c in sorted(pool, key=lambda c: c["id"]):
        tasks.setdefault(c["task"], c)
    picked = sorted(tasks.values(), key=lambda c: c["task"])[: a.tasks]
    levels = {"strong": "a strong answer that would earn high marks",
              "partial": "a partly correct answer that would earn about half marks",
              "weak": "a weak answer with a common misconception that would earn low marks"}
    out = []
    for gen in a.models:
        client = OpenAICompatible(a.base_url, gen, a.key_env, os.path.join(os.path.dirname(a.out) or ".", ".gen-cache"),
                                  max_tokens=a.max_tokens, extra=json.loads(a.extra_body) if a.extra_body else None)
        jobs = []
        for c in picked:
            length = len(c["response"].split())
            for lv, desc in levels.items():
                msg = [{"role": "user", "content":
                        f"Write {desc} to the task below, as a student would write it, in about {length} words. "
                        f"Reply with the answer text only.\n\nTask:\n{c['question']}\n\n{c['materials']}".strip()}]
                jobs.append((c, lv, msg))
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            res = list(ex.map(lambda j: (j, client.call(j[2], tag=f"gen|{j[1]}")), jobs))
        for (c, lv, _), rec in res:
            if rec["error"] is None and (rec["text"] or "").strip():
                out.append({**{k: c[k] for k in ("task", "question", "reference", "rubric", "materials", "scale")},
                            "id": f"gen|{gen}|{c['task']}|{lv}", "response": rec["text"].strip(), "human": {},
                            "generator": gen, "level": lv})
        print(f"{gen}: {sum(1 for o in out if o['generator'] == gen)} answers")
    cases_mod.write([cases_mod.normalise(o) for o in out], a.out)
    print(f"{len(out)} generated answers -> {a.out}. Grade them with: bench.py run --cases {a.out} --probes base --n 100000")


def family(model):
    return model.split("/")[0].split("-")[0] if "/" in model else model


def cmd_selfpref(a):
    """Do graders over-mark their own model's (or family's) answers? Each grader's mark on each
    generated answer, minus the mean mark all graders gave that answer (so how good the answer is
    cancels). Self-preference = that residual on its own model's answers minus on everyone else's."""
    from metrics import bootstrap, interval, mean
    runs = []
    for r in a.runs:
        cfg, cs, calls = load_run(r, a.cases)
        runs.append((cfg["model"], {c["id"]: c for c in cs}, {x["id"]: x["score"] for x in calls if x["probe"] == "base" and x["score"] is not None}))
    ids = sorted(set.intersection(*[set(m) for _, _, m in runs]))
    if len(ids) < 20:
        sys.exit(f"only {len(ids)} answers graded by every run; need 20+")
    cases = runs[0][1]
    lo, hi = cases[ids[0]]["scale"]
    w = hi - lo
    centre = {i: mean(m[i] for _, _, m in runs) for i in ids}
    print(f"{len(ids)} generated answers, {len(runs)} graders; marks as % of the scale\n")
    print(f"  {'grader':34} {'own model':>22} {'own family':>22}   strong / partial / weak")
    for model, _, m in runs:
        res = {i: m[i] - centre[i] for i in ids}
        lines = []
        for same in (lambda g: g == model, lambda g: family(g) == family(model)):
            own = [res[i] for i in ids if same(cases[i]["generator"])]
            other = [res[i] for i in ids if not same(cases[i]["generator"])]
            if len(own) >= 5 and len(other) >= 5:
                units = [(1, x) for x in own] + [(0, x) for x in other]
                stat = lambda us: mean(x for g, x in us if g) - mean(x for g, x in us if not g)
                iv = interval(*bootstrap(units, stat))
                lines.append(f"{100 * iv['estimate'] / w:+5.1f}% [{100 * iv['ci95'][0] / w:+.1f}, {100 * iv['ci95'][1] / w:+.1f}]")
            else:
                lines.append(f"{'not generated':>22}")
        lv = " / ".join(f"{100 * (mean(m[i] for i in ids if cases[i]['level'] == L) - lo) / w:.0f}%" for L in ("strong", "partial", "weak"))
        print(f"  {model[:34]:34} {lines[0]:>22} {lines[1]:>22}   {lv}")
    print("\n  Positive = the grader marks its own model's answers higher than the other graders do."
          "\n  The last column checks the answers are graded in the order they were written to.")


def cmd_halo(a):
    """Feedback halo: the same feedback prompt with the teacher's mark hidden (run A) and shown (B)."""
    import feedback as fb
    _, cs, blind = load_run(a.blind, a.cases)
    _, _, shown = load_run(a.shown, a.cases)
    h = fb.halo(cs, blind, shown)
    if not h:
        sys.exit("fewer than 30 cases with English feedback in both runs")
    print(f"{h['n']} cases. Tone tracks the teacher's mark: r {h['corr_blind']:+.2f} when the mark is hidden, "
          f"{h['corr_shown']:+.2f} when it is shown.")
    print(f"Halo {h['halo']:+.2f} [{h['ci95'][0]:+.2f}, {h['ci95'][1]:+.2f}]"
          + (" : the stated mark changes the feedback beyond what the work shows" if h["flag"] and h["halo"] > 0 else ""))


# ---------------------------------------------------------------- markdown

def fmt_iv(iv, d=3, scale=None):
    if not iv:
        return "not run"
    e, (lo, hi) = iv["estimate"], iv["ci95"]
    s = f"{e:+.{d}f} [{lo:+.{d}f}, {hi:+.{d}f}]"
    if scale:
        s += f" ({100 * e / scale:+.1f}% of scale)"
    if iv.get("flag"):
        s += " **moves marks**"
    elif iv.get("mdc80") is not None:
        s += f" (could detect {iv['mdc80']:.2f}+)"
    return s


def render_md(rep):
    c, v, rl, f, s = rep.get("config", {}), rep["validity"], rep["reliability"], rep["fairness"], rep["sustainability"]
    lo, hi = rep["scale"]
    w = hi - lo
    L = [f"# Grading benchmark: {c.get('model', '?')} with {c.get('prompt', '?')}", "",
         f"{rep['n_cases']} cases from {c.get('cases', '?')} (seed {c.get('seed')}), scale {lo:g}-{hi:g}. "
         f"Prompt sha256 {str(c.get('prompt_sha256', ''))[:12]}. Benchmark {c.get('benchmark_version')}.", "",
         "## Validity", ""]
    ag = v.get("agreement")
    if ag:
        L.append(f"- QWK vs human raters: {ag['qwk']['estimate']:.3f} [{ag['qwk']['ci95'][0]:.3f}, {ag['qwk']['ci95'][1]:.3f}] "
                 f"(n {ag['n']}); Pearson r {ag['pearson_r']['estimate']:.3f}")
        if v.get("ceiling"):
            ce, sh = v["ceiling"]["qwk"], v["share_of_ceiling"]
            L.append(f"- Human ceiling (rater vs rater): {ce['estimate']:.3f}; **share of ceiling "
                     f"{100 * sh['estimate']:.0f}% [{100 * sh['ci95'][0]:.0f}%, {100 * sh['ci95'][1]:.0f}%]**")
        else:
            L.append(f"- No human ceiling: {v.get('no_ceiling')}")
        L.append(f"- Bias (machine minus human): {fmt_iv(ag['bias'], scale=w)}; spread ratio " + (f"{ag['sd_ratio']:.2f}" if ag['sd_ratio'] is not None else "n/a (marks do not vary)"))
    dec = v.get("decision")
    if dec and dec["machine_passes_of_human_passes"] is not None and dec["machine_fails_of_human_fails"] is not None:
        L.append(f"- At a pass mark of {dec['pass_mark']:g}: passes {100 * dec['machine_passes_of_human_passes']:.0f}% "
                 f"of human passes, fails {100 * dec['machine_fails_of_human_fails']:.0f}% of human fails")
    fg = v["failed_gradings"]
    L.append(f"- Gradings with no readable mark: {fg['n']} of {fg['of']}")
    for k, x in v.get("failed_by_probe", {}).items():
        if k != "base" and x["failed"] >= max(3, 0.05 * x["of"]):
            L.append(f"  - {k}: {x['failed']} of {x['of']} failed" +
                     (f", {x['content_filter']} refused by a content filter (the probe is read on the rest only)"
                      if x["content_filter"] else ""))
    for k, label in (("padding", "Off-topic paragraph appended"), ("repeat", "Every sentence written twice"),
                     ("injection", "Polite request for full marks"), ("forged", "Forged grading override"),
                     ("shuffled", "Sentences shuffled"), ("blicket", "Every \"the\" -> \"blicket\"")):
        iv = v.get(k)
        if iv:
            L.append(f"- {label} (n {iv['n']}): {fmt_iv(iv, scale=w)}; should be {iv['expect']}, "
                     f"{iv['reading']}" + ("" if iv["as_expected"] else " **(not as a sound grader would)**"))
    ot = v.get("off_task")
    if ot and ot["n"]:
        L.append(f"- Work for a different task: mean mark at {100 * ot['mean_share_of_scale']:.0f}% of the scale; "
                 f"{100 * ot['reaches_midpoint']:.0f}% reach the midpoint")
    na = v.get("null_answers")
    if na and na["credited"] is not None:
        L.append(f"- Blank or master-key answers given credit: {100 * na['credited']:.0f}% ("
                 + ", ".join(f"{k[5:]} {100 * x['credited']:.0f}%" for k, x in na["by_kind"].items()) + ")")
    rf_ = v.get("rationale_faithfulness")
    if rf_:
        L.append(f"- Deleting the sentence the rationale leans on, against a random sentence: "
                 f"{fmt_iv(rf_['cited_minus_random_abs_change'])} marks of extra change; {rf_['reading']}")
    L += ["", "## Reliability", ""]
    rt = rl.get("retest")
    if rt:
        L.append(f"- Same call twice: QWK {rt['qwk']['estimate']:.3f}, identical {100 * rt['exact_agreement']:.0f}%, "
                 f"mean change {rt['mean_abs_change']:.3f} marks")
    se = rl.get("selective")
    if se:
        L.append(f"- Selective scoring over {se['k']} identical calls: identical marks on {100 * se['consistent_share']:.0f}% of cases; "
                 + ", ".join(f"keep {int(100 * x['kept'])}% QWK {x['qwk_vs_humans']:.3f}" for x in se["curve"]))
    if rl.get("typos"):
        L.append(f"- Three words misspelt (n {rl['typos']['n']}): {fmt_iv(rl['typos'], scale=w)}")
    sf = rl.get("surface")
    if sf:
        L.append(f"- Same work re-wrapped: {fmt_iv(sf, scale=w)}"
                 + (f"; {sf['vs_retest']:.2f}x the retest change" if sf.get("vs_retest") else ""))
    L += ["", "## Fairness", ""]
    at = f.get("attainment")
    if at:
        L.append(f"- Told attainment 8/10 vs 3/10, identical work: {fmt_iv(at['label_effect'], scale=w)}")
        L.append(f"- A neutral same-length sentence vs none: {fmt_iv(at['presence'], scale=w)}")
        L.append(f"- Low label vs neutral: {fmt_iv(at['penalty'])}; high label vs neutral: {fmt_iv(at['reward'])}")
    else:
        L.append(f"- Attainment probe not run: {f.get('attainment_not_run')}")
    for name, g in f.get("groups", {}).items():
        L.append(f"- {name} (residual vs the other groups):")
        for k, x in g["levels"].items():
            L.append(f"  - {k} (n {x['n']}): {fmt_iv(x['vs_rest'], scale=w)}")
    if f.get("groups_note"):
        L.append(f"- Note: {f['groups_note']}")
    fb = rep.get("feedback")
    L += ["", "## Feedback", ""]
    if not fb:
        L.append("- No feedback text in the replies (the prompt asks for a mark only).")
    else:
        g = lambda k, f: (f.format(fb[k]) if fb.get(k) is not None else "n/a")
        L.append(f"- Read from the `{fb['field']}` field of {fb['n']} base gradings; {fb['note']}.")
        L.append(f"- Length {g('words', '{:.0f}')} words; generic (similarity between students) {g('generic', '{:.2f}')}; "
                 f"varied by quality {g('varied_by_quality', '{:+.3f}')} (positive = strong and weak work get different feedback)")
        L.append(f"- Grounded in this student's own words {g('grounded', '{:.0%}')}; critical phrases track the mark "
                 f"{g('coherence', '{:+.2f}')} (should be negative); gives away the model answer {g('leaks_answer', '{:.0%}')}")
        L.append(f"- Per 100 words: aimed at the person {g('self_per100', '{:.1f}')}, at the work {g('task_per100', '{:.1f}')}, "
                 f"next steps {g('action_per100', '{:.1f}')}; same opening {g('same_opening', '{:.0%}')}")
    L += ["", "## Sustainability", ""]
    pg = s.get("per_grading") or {}
    L.append(f"- {s['calls']} calls, {s['calls_failed']} failed. Per grading: {pg.get('prompt_tokens', 0):.0f} prompt, "
             f"{pg.get('completion_tokens', 0):.0f} completion, {pg.get('reasoning_tokens', 0):.0f} reasoning tokens")
    if s.get("latency_s"):
        L.append(f"- Latency: median {s['latency_s']['median']:.1f}s, 90th percentile {s['latency_s']['p90']:.1f}s")
    cost = s.get("cost_per_1000_gradings_usd")
    L.append(f"- Cost per 1,000 gradings: " + (f"${cost:.2f} ({s['cost_source']})" if cost is not None else s["cost_source"]))
    if s.get("human_cost_per_1000_gradings_usd") is not None:
        L.append(f"- Human marking per 1,000, at the minutes and rate passed: ${s['human_cost_per_1000_gradings_usd']:.0f}")
    e = s.get("energy_wh_per_1000_gradings")
    L.append(f"- Energy per 1,000 gradings: " + (f"{e:.0f} Wh ({s['energy_source']})" if e is not None else s["energy_source"]))
    if s.get("co2e_g_per_1000_gradings") is not None:
        L.append(f"- Carbon per 1,000 gradings: {s['co2e_g_per_1000_gradings']:.0f} gCO2e ({s['co2e_source']})")
    L.append(f"- Served by: {', '.join(s['served_models'])}" + (f" via {', '.join(s['providers'])}" if s["providers"] else ""))
    if s.get("mixed_backends"):
        L.append(f"- **Mixed backends:** {s['mixed_backends']}. Pin one backend and re-run before reading the probes.")
    L += ["", "Intervals are 95% bootstrap over cases. **moves marks** = the interval excludes zero; the sign is the direction.", ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1], formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("prepare", help="turn a downloaded corpus into cases")
    p.add_argument("corpus", choices=sorted(cases_mod.LOADERS))
    p.add_argument("--src", required=True)
    p.add_argument("--out", required=True)

    def money(q):
        q.add_argument("--price-in", type=float, help="USD per million prompt tokens")
        q.add_argument("--price-out", type=float, help="USD per million completion tokens")
        q.add_argument("--wh-per-1k-tokens", type=float, help="energy coefficient, with your source")
        q.add_argument("--gco2-per-kwh", type=float, help="grid carbon intensity")
        q.add_argument("--human-minutes", type=float, help="human minutes to mark one case")
        q.add_argument("--human-rate", type=float, help="human marker USD per hour")
        q.add_argument("--cases", help="the cases file, if not where the run found it")

    p = sub.add_parser("run", help="grade cases with a model and prompt")
    p.add_argument("--cases", required=True)
    p.add_argument("--prompt", default=os.path.join(HERE, "prompts", "default.txt"))
    p.add_argument("--base-url", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--key-env", default="OPENAI_API_KEY", help="the environment variable holding the key ('' for none)")
    p.add_argument("--battery", choices=sorted(BATTERIES), default="core",
                   help="core (default, cheapest useful), full (research), abstain, faithful, anchor (drift)")
    p.add_argument("--n", type=int, help="cases per run (default: the battery's)")
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--probes", help="comma-separated, or 'all' (default: the battery's)")
    p.add_argument("--assume-out", type=int, default=300, help="output tokens a grading, for the cost estimate")
    p.add_argument("--temperature", type=float, help="unset by default: the model's own default applies")
    p.add_argument("--max-tokens", type=int)
    p.add_argument("--extra-body", help="JSON merged into each request, e.g. reasoning settings")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--max-calls", type=int, default=3000)
    p.add_argument("--max-usd", type=float, help="stop sending once the endpoint-reported cost reaches this")
    p.add_argument("--retention-exception", help="for a model with no zero-retention endpoint: the route and its "
                   "retention, recorded in the run (e.g. 'own Anthropic key, 30-day safety retention; public corpora')")
    p.add_argument("--label", help="row name for this setup of the model (recorded in the config; default: the model id)")
    p.add_argument("--route", help="where the model ran and what it retains, recorded in the config "
                                    "(e.g. a self-hosted pod)")
    p.add_argument("--video-frames", type=int, default=0,
                   help="send video work as this many evenly spaced frames, for models without video input (0: the video)")
    p.add_argument("--out", required=True)
    p.add_argument("--go", action="store_true", help="make the calls (otherwise a dry run)")
    p.add_argument("--cached-only", action="store_true",
                   help="send nothing: rebuild calls.jsonl from the cache, recording the rest as not sent")
    p.add_argument("--cache-dir", help="response cache (default <out>/.cache); point at another run's to reuse its gradings")

    p = sub.add_parser("score", help="build the report from a run")
    p.add_argument("run")
    p.add_argument("--pass-mark", type=float)
    money(p)

    p = sub.add_parser("compare", help="paired difference between two runs (B minus A)")
    p.add_argument("a")
    p.add_argument("b")
    money(p)

    p = sub.add_parser("drift", help="has a model's marking moved? (run B against run A on the same cases)")
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--cases")

    p = sub.add_parser("generate", help="AI-written answers for the self-preference test")
    p.add_argument("--cases", required=True)
    p.add_argument("--models", nargs="+", required=True)
    p.add_argument("--tasks", type=int, default=30)
    p.add_argument("--base-url", default="https://openrouter.ai/api/v1")
    p.add_argument("--key-env", default="OPENROUTER_API_KEY")
    p.add_argument("--max-tokens", type=int, default=4096)
    p.add_argument("--extra-body")
    p.add_argument("--workers", type=int, default=6)
    p.add_argument("--out", required=True)

    p = sub.add_parser("selfpref", help="do graders over-mark their own model's answers?")
    p.add_argument("runs", nargs="+")
    p.add_argument("--cases")

    p = sub.add_parser("halo", help="does feedback follow a mark it is shown?")
    p.add_argument("blind")
    p.add_argument("shown")
    p.add_argument("--cases")

    a = ap.parse_args(argv)
    {"prepare": cmd_prepare, "run": cmd_run, "score": cmd_score, "compare": cmd_compare, "drift": cmd_drift,
     "generate": cmd_generate, "selfpref": cmd_selfpref, "halo": cmd_halo}[a.cmd](a)


if __name__ == "__main__":
    main()
