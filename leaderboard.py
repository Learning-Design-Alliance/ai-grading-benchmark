"""
The leaderboard: what a submission is, how it is checked, and how rows are built.

Anyone can run the `leaderboard` battery on their own machine and submit the result as a pull request.
A submission carries every grading's mark and none of its text, so it holds no student work and can be
public whatever the corpus licence. The checks below rebuild every number from those marks and the
human marks in the public cases file; nothing a submitter reports is taken on trust except cost, which
is labelled self-reported.

    python3 leaderboard.py export <run dir> --task mohler --out submissions/<slug>/mohler.json [--submitter NAME]
    python3 leaderboard.py verify submissions/<slug>/mohler.json --cases <mohler.jsonl>
    python3 leaderboard.py build submissions/ --cases-dir <dir with mohler.jsonl, harmogen-code.jsonl, asap2.jsonl>
    python3 leaderboard.py spotcheck submissions/<slug>/mohler.json --cases <mohler.jsonl> --k 25 --go

WHAT IS FIXED. The battery (bench.py BATTERIES["leaderboard"]), the three tasks and their cases files
(sha256 below; build them with `bench.py prepare` from the data-sources.json entries), the case draw
(bench.py sample, n = 100, seed 7) and, for the default track, the prompt (prompts/default.txt, by
sha256). A submission that differs in any of these is refused, not adjusted.

TRACKS. "default": the fixed prompt, so rows compare models. "byop": any prompt, which must be published
in the submission (its text, not only its hash), so rows compare prompts and anyone can rerun them.

WHAT A ROW SHOWS, and why each column is there (README, "What goes on the leaderboard"):
- agreement: machine QWK and, where the task has two or more raters, its share of the human ceiling;
- consistency: QWK between two gradings of the same work;
- gaming: the larger gain, as a share of the scale, from a polite request for marks or a forged
  grading override in the submission;
- attainment label: the mark change when the same work is described as from a strong rather than a
  weak learner, as a share of the scale;
- blicket: the change when the key content word is replaced by a nonsense word (should be negative);
- surface sensitivity: the change from re-wrapping the text's line breaks (should be near zero; it is a
  weak memorisation check, not a paraphrase test);
- blank answers: the share of empty or master-key answers given more than the minimum mark;
- refusals: gradings a provider's content filter refused (a refusal is not credit; it is work sent to
  a person);
- cost per 1,000 gradings, self-reported.
No overall score: combining these needs weights that are a matter of opinion, and an average would hide
the one column that matters most for a given use.

SPOT CHECK. `spotcheck` re-grades k random base cases with the submission's declared model, endpoint and
settings, and compares the marks with the submitted ones. VERIFIED when their QWK is at least the
submission's own retest QWK minus 0.10; otherwise NOT REPRODUCED. A spot check costs the checker the
price of k gradings.
"""

import argparse
import datetime
import glob
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cases as cases_mod  # noqa: E402
import report as report_mod  # noqa: E402
from metrics import qwk  # noqa: E402

FORMAT = "grader-benchmark-submission/1"
N, SEED = 100, 7
DEFAULT_PROMPT = os.path.join(HERE, "prompts", "default.txt")

#: task -> (prepare corpus key, data-sources id, sha256 of the prepared cases file)
TASKS = {
    "mohler": ("mohler", "mohler-asag", None),
    "code": ("harmogen-code", "harmogen-r", None),
    "asap2": ("asap2", "asap2", None),
}
SHA_FILE = os.path.join(HERE, "leaderboard-cases.json")
#: tasks whose released data has no two raters per item: the corpus's own published rater agreement, used only
#: to put agreement on the same footing as the other tasks, and always shown as "against a published figure"
PUBLISHED_CEILING = {"asap2": {"value": 0.745, "statistic": "pre-adjudication weighted kappa between two expert raters",
                               "source": "Crossley, Baffour, Burleigh and King (2025), Assessing Writing 65, 100954, section 3"}}


def task_sha():
    """Pinned cases-file hashes, kept in leaderboard-cases.json (written by `pin`)."""
    if os.path.exists(SHA_FILE):
        return json.load(open(SHA_FILE))
    return {}


_CACHE = {}


def load_cases(path):
    """Each cases file is read and hashed once per process: the essay file is about 240 MB."""
    if path not in _CACHE:
        _CACHE[path] = (sha256(path), cases_mod.load(path))
    return _CACHE[path]


def sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def battery():
    import bench
    return bench.BATTERIES["leaderboard"]


def prompt_for(sub):
    """The prompt a submission declares. Bring-your-own prompts are accepted as templates only: a Python
    prompt would run a stranger's code in the checker."""
    import tempfile
    from prompting import TemplatePrompt, load_prompt
    if sub.get("track") == "default":
        return load_prompt(DEFAULT_PROMPT)
    fd, path = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(sub["prompt"])
    return TemplatePrompt(path)


# ------------------------------------------------------------------- export
def cmd_export(a):
    import bench
    config, cs, calls = bench.load_run(a.run, a.cases)
    pp = config.get("prompt_path")
    prompt_text = open(pp, encoding="utf-8").read() if pp and os.path.exists(pp) else None
    track = "default" if config.get("prompt_sha256") == sha256(DEFAULT_PROMPT) else "byop"
    if track == "byop" and prompt_text is None and not a.prompt:
        sys.exit("a bring-your-own-prompt submission must publish its prompt: pass --prompt <file>")
    if a.prompt:
        prompt_text = open(a.prompt).read()
    keep = ("id", "probe", "score", "finish_reason", "served_model", "provider", "error")
    sub = {
        "format": FORMAT,
        "task": a.task,
        "track": track,
        "submitter": a.submitter,
        "exported": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "benchmark_version": config.get("benchmark_version"),
        "battery": config.get("battery"),
        "probes": config.get("probes"),
        "model": config["model"],
        "base_url": config.get("base_url"),
        "settings": {k: config.get(k) for k in ("temperature", "max_tokens", "extra_body")},
        "cases_sha256": config["cases_sha256"],
        "case_ids": config["case_ids"],
        "prompt_sha256": config.get("prompt_sha256"),
        "prompt": prompt_text if track == "byop" else None,
        "calls": [{**{k: r.get(k) for k in keep},
                   "usage": {k: (r.get("usage") or {}).get(k) for k in ("prompt_tokens", "completion_tokens",
                                                                         "reasoning_tokens", "cost_reported")}}
                  for r in calls],
    }
    if any("text" in c for c in sub["calls"]):
        sys.exit("internal error: text in a submission")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(sub, open(a.out, "w"), indent=1)
    print(f"{a.out}: {len(sub['calls'])} gradings, track {track}, no text")


# ------------------------------------------------------------------- verify
def check(sub, cases_path):
    """(problems, cases, calls). Problems are reasons to refuse the submission."""
    import bench
    probs = []
    if sub.get("format") != FORMAT:
        probs.append(f"format is {sub.get('format')!r}, expected {FORMAT!r}")
    if sub.get("task") not in TASKS:
        probs.append(f"unknown task {sub.get('task')!r}")
        return probs, None, None
    if sub.get("battery") != "leaderboard":
        probs.append(f"battery is {sub.get('battery')!r}; only the leaderboard battery is ranked")
    pinned = task_sha().get(sub["task"])
    if pinned and sub.get("cases_sha256") != pinned:
        probs.append("cases_sha256 is not the pinned cases file for this task")
    file_sha, allc = load_cases(cases_path)
    if file_sha != sub.get("cases_sha256"):
        probs.append(f"{cases_path} does not match the submission's cases_sha256")
        return probs, None, None
    canon = [c["id"] for c in cases_mod.sample(allc, N, SEED)]
    if sub.get("case_ids") != canon:
        probs.append("case_ids are not the canonical draw (n = 100, seed 7)")
    if sub.get("track") == "default" and sub.get("prompt_sha256") != sha256(DEFAULT_PROMPT):
        probs.append("default track but the prompt is not prompts/default.txt")
    if sub.get("track") == "byop":
        if not sub.get("prompt"):
            probs.append("byop track without the prompt text")
        else:
            import hashlib
            if hashlib.sha256(sub["prompt"].encode()).hexdigest() != sub.get("prompt_sha256"):
                probs.append("published prompt does not match prompt_sha256")
    if any(set(c) - {"id", "probe", "score", "finish_reason", "served_model", "provider", "error", "usage"} for c in sub["calls"]):
        probs.append("calls carry fields beyond the submission format (text is never allowed)")
    by_id = {c["id"]: c for c in allc}
    cs = [by_id[i] for i in sub.get("case_ids", []) if i in by_id]
    if sub.get("track") == "byop" and sub.get("prompt") is None:
        return probs, None, None
    prompt = prompt_for(sub)
    jobs, ran = bench.plan(cs, allc, prompt, list(battery()["probes"]), SEED) if cs else ([], [])
    if sorted(sub.get("probes") or []) != sorted(ran):
        probs.append("probe list differs from the leaderboard battery")
    expected = {(c["id"], p) for c, p, _ in jobs}
    got = [(r["id"], r["probe"]) for r in sub["calls"]]
    if len(got) != len(set(got)):
        probs.append("duplicate gradings")
    if set(got) != expected:
        probs.append(f"gradings differ from the battery's plan: {len(expected - set(got))} missing, "
                     f"{len(set(got) - expected)} extra")
    lo, hi = (cs[0]["scale"] if cs else (None, None))
    bad = [r for r in sub["calls"] if r.get("score") is not None and not (lo <= r["score"] <= hi)]
    if bad:
        probs.append(f"{len(bad)} marks outside the scale {lo}-{hi}")
    return probs, cs, sub["calls"]


def row(sub, rep):
    v, rl, fa, su = rep["validity"], rep["reliability"], rep["fairness"], rep.get("sustainability", {})
    lo, hi = rep["scale"]
    w = hi - lo

    def est(x, scale=True):
        if not x:
            return None
        return {"estimate": x["estimate"] / (w if scale else 1), "ci95": [c / (w if scale else 1) for c in x["ci95"]],
                "flag": x.get("flag")}
    gaming = [g for g in (est(v.get("injection")), est(v.get("forged"))) if g]
    fails = v.get("failed_by_probe", {})
    refused = sum(x["content_filter"] for x in fails.values())
    return {
        "model": sub["model"], "task": sub["task"], "track": sub["track"], "submitter": sub.get("submitter"),
        "served_models": sorted({r.get("served_model") for r in sub["calls"] if r.get("served_model")}),
        "providers": sorted({r.get("provider") for r in sub["calls"] if r.get("provider")}),
        "qwk": v["agreement"]["qwk"], "share_of_ceiling": v.get("share_of_ceiling"),
        "retest_qwk": (rl.get("retest") or {}).get("qwk"),
        "gaming_max_share": max(gaming, key=lambda g: g["estimate"]) if gaming else None,
        "attainment_label_share": est((fa.get("attainment") or {}).get("label_effect")),
        "blicket_share": est(v.get("blicket")),
        "surface_share": est(rl.get("surface")),
        "blank_credited": (v.get("null_answers") or {}).get("credited"),
        "decision_kappa": (v.get("decision") or {}).get("kappa"),
        "decision_share": (v.get("decision") or {}).get("share_of_ceiling"),
        "decision_n_fail": (v.get("decision") or {}).get("n_fail"),
        # where a task has no computed ceiling, agreement against the corpus's published reliability, labelled
        "published_ceiling": PUBLISHED_CEILING.get(sub["task"]),
        "share_of_published_ceiling": (v["agreement"]["qwk"]["estimate"] / PUBLISHED_CEILING[sub["task"]]["value"]
                                       if sub["task"] in PUBLISHED_CEILING else None),
        "refused": refused, "gradings": len(sub["calls"]),
        "cost_per_1000_usd_self_reported": su.get("cost_per_1000_gradings_usd"),
        "benchmark_version": sub.get("benchmark_version"),
    }


def cmd_verify(a):
    sub = json.load(open(a.submission))
    probs, cs, calls = check(sub, a.cases)
    if probs:
        print("REFUSED:\n  " + "\n  ".join(probs))
        sys.exit(1)
    rep = report_mod.build(cs, calls)
    r = row(sub, rep)
    print(json.dumps(r, indent=1))
    print("ACCEPTED (self-reported until spot-checked)")


CASE_FILES = {"mohler": "mohler.jsonl", "code": "harmogen-code.jsonl", "asap2": "asap2.jsonl"}
#: everything a row depends on besides the submission itself: change any of these and every cached row is stale
CODE_FILES = ["leaderboard.py", "report.py", "metrics.py", "bench.py", "prompting.py", "cases.py", "leaderboard-cases.json",
              "prompts/default.txt"]


def code_hash():
    import hashlib
    h = hashlib.sha256()
    for f in CODE_FILES:
        h.update(f.encode())
        h.update(open(os.path.join(HERE, f), "rb").read())
    return h.hexdigest()


def build_one(args):
    """(relative path, row or None, problems) for one submission; run in a worker process."""
    path, root, cases_dir, cache_dir, ch = args
    import hashlib
    raw = open(path, "rb").read()
    key = hashlib.sha256(raw + ch.encode()).hexdigest()
    rel = os.path.relpath(path, root)
    cpath = os.path.join(cache_dir, key + ".json") if cache_dir else None
    if cpath and os.path.exists(cpath):
        hit = json.load(open(cpath))
        return rel, hit["row"], hit["problems"], True
    sub = json.loads(raw)
    if sub.get("format") != FORMAT:
        return rel, None, None, False
    cases_path = os.path.join(cases_dir, CASE_FILES.get(sub.get("task"), "?"))
    probs, cs, calls = check(sub, cases_path) if os.path.exists(cases_path) else (["cases file missing"], None, None)
    r = None if probs else row(sub, report_mod.build(cs, calls))
    if cpath:
        os.makedirs(cache_dir, exist_ok=True)
        json.dump({"row": r, "problems": probs}, open(cpath, "w"))
    return rel, r, probs, False


def cmd_build(a):
    """Verify every submission and build the leaderboard. Rows are cached by (submission bytes, scoring code,
    pinned cases), so an unchanged submission is never recomputed; cache misses run in parallel. A cached
    row is only as trustworthy as the cache directory: CI keeps it in its own cache, which a pull request
    from a fork cannot write to for the main branch."""
    from concurrent.futures import ProcessPoolExecutor
    import time
    t0 = time.time()
    paths = sorted(p for p in glob.glob(os.path.join(a.submissions, "**", "*.json"), recursive=True)
                   if not p.endswith(".spotcheck.json"))
    pins = task_sha()
    for task, fn in CASE_FILES.items():  # the cases files must be the pinned ones before any cached row is trusted
        fp = os.path.join(a.cases_dir, fn)
        if os.path.exists(fp) and pins.get(task) and sha256(fp) != pins[task]:
            sys.exit(f"{fp} is not the pinned cases file for {task}; rebuild it with fetch_data.py")
    ch = code_hash()
    jobs = [(p, a.submissions, a.cases_dir, a.cache_dir, ch) for p in paths]
    # The essay file is large: order work so each worker loads as few cases files as possible.
    with ProcessPoolExecutor(max_workers=a.jobs) as ex:
        results = list(ex.map(build_one, jobs))
    rows, refused, hits = [], [], 0
    for (rel, r, probs, hit), path in zip(results, paths):
        hits += hit
        if probs:
            refused.append({"file": rel, "problems": probs})
            continue
        if r is None:
            continue
        sc = path[:-5] + ".spotcheck.json"
        r = dict(r, verified=json.load(open(sc)).get("verdict") == "VERIFIED" if os.path.exists(sc) else False, file=rel)
        rows.append(r)
    out = {"built": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "code_sha256": ch,
           "rows": rows, "refused": refused}
    json.dump(out, open(a.out, "w"), indent=1)
    print(f"{len(rows)} rows, {len(refused)} refused, {hits} from cache, {time.time() - t0:.0f}s -> {a.out}")
    for x in refused:
        print("  refused", x["file"], "; ".join(x["problems"]))
    if refused and a.strict:
        sys.exit(1)


def cmd_spotcheck(a):
    import bench
    from client import OpenAICompatible
    sub = json.load(open(a.submission))
    probs, cs, calls = check(sub, a.cases)
    if probs:
        sys.exit("refused before spot check: " + "; ".join(probs))
    rng = random.Random(f"spot-{sub['model']}-{sub['exported']}")
    pick = rng.sample(cs, min(a.k, len(cs)))
    s = sub["settings"]
    if not a.go:
        print(f"would re-grade {len(pick)} cases with {sub['model']} at {sub['base_url']}; pass --go")
        return
    cl = OpenAICompatible(sub["base_url"], sub["model"], key_env=a.key_env, cache_dir=a.cache_dir,
                          temperature=s.get("temperature"), max_tokens=s.get("max_tokens"), extra=s.get("extra_body") or {})
    prompt = prompt_for(sub)
    allc = cases_mod.load(a.cases)
    jobs, _ = bench.plan(pick, allc, prompt, ["base"], SEED)
    mine, theirs = [], []
    by = {(r["id"], r["probe"]): r["score"] for r in calls}
    for c, _p, msgs in jobs:
        rec = cl.call(msgs, tag="spotcheck")
        sc = prompt.parse(rec["text"], *c["scale"]) if rec["error"] is None else None
        if sc is not None and by.get((c["id"], "base")) is not None:
            mine.append(sc)
            theirs.append(by[(c["id"], "base")])
    rep = report_mod.build(cs, calls)
    rt = ((rep["reliability"].get("retest") or {}).get("qwk") or {}).get("estimate")
    lo, hi = cs[0]["scale"]
    q = qwk(theirs, mine, lo, hi) if len(mine) >= 10 else None
    verdict = "VERIFIED" if q is not None and rt is not None and q >= rt - 0.10 else "NOT REPRODUCED"
    res = {"k": len(mine), "qwk_vs_submitted": q, "submission_retest_qwk": rt, "verdict": verdict,
           "checked": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    json.dump(res, open(a.submission[:-5] + ".spotcheck.json", "w"), indent=1)
    print(json.dumps(res))


def cmd_pin(a):
    """Record the sha256 of each task's prepared cases file (maintainers only)."""
    pins = task_sha()
    for spec in a.files:
        task, path = spec.split("=", 1)
        if task not in TASKS:
            sys.exit(f"unknown task {task}")
        pins[task] = sha256(path)
    json.dump(pins, open(SHA_FILE, "w"), indent=1, sort_keys=True)
    print(json.dumps(pins, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("export"); p.add_argument("run"); p.add_argument("--task", required=True, choices=sorted(TASKS))
    p.add_argument("--out", required=True); p.add_argument("--submitter"); p.add_argument("--cases"); p.add_argument("--prompt")
    p = sub.add_parser("verify"); p.add_argument("submission"); p.add_argument("--cases", required=True)
    p = sub.add_parser("build"); p.add_argument("submissions"); p.add_argument("--cases-dir", required=True)
    p.add_argument("--out", default="leaderboard.json"); p.add_argument("--strict", action="store_true")
    p.add_argument("--jobs", type=int, default=os.cpu_count()); p.add_argument("--cache-dir", default=".leaderboard-cache",
                   help="row cache ('' to disable)")
    p = sub.add_parser("spotcheck"); p.add_argument("submission"); p.add_argument("--cases", required=True)
    p.add_argument("--k", type=int, default=25); p.add_argument("--go", action="store_true")
    p.add_argument("--key-env", default="OPENROUTER_API_KEY"); p.add_argument("--cache-dir", default=".spotcheck-cache")
    p = sub.add_parser("pin"); p.add_argument("files", nargs="+", help="task=path")
    a = ap.parse_args()
    {"export": cmd_export, "verify": cmd_verify, "build": cmd_build, "spotcheck": cmd_spotcheck, "pin": cmd_pin}[a.cmd](a)


if __name__ == "__main__":
    main()
