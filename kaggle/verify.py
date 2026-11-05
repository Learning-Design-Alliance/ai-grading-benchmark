#!/usr/bin/env python3
"""Check that the Kaggle tasks reproduce the leaderboard, before anything is published.

1. SCORING (no model calls): every model's committed leaderboard grades (submissions/<model>/<task>.json) and
   pushback turns are scored by kaggle_scoring.py from the built dataset, and each per-task value is compared with
   out/leaderboard.json: share of the raters' agreement (essays: QWK / 0.745), the larger note gain, the share of
   blank answers credited, and the pushback effect. They must match to 1e-9. It also checks that the dataset's
   cases are the leaderboard's (the case ids every submission graded).

2. TASK FILES (no model calls, optional): --replay RUNS runs each kaggle/tasks/*.py against a stand-in for
   kaggle_benchmarks whose model replays one model's recorded replies from its run directories (lb-<task>-<slug>,
   fbb-feedback-, push-, fbd-mirror-/fbb-shown-/fbb-blind-), so the task code itself (which prompt goes where, the
   pushback branches, the parsing) is exercised end to end. Run records hold reply text and are never committed.

    python3 kaggle/verify.py --data DATASET [--replay RUNS --slug anthropic_claude-opus-5.5]
"""

import argparse
import contextlib
import glob
import json
import os
import runpy
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load_ks(data):
    sys.path.insert(0, os.path.join(data, "gbench"))
    import kaggle_scoring as ks
    return ks


def check_scoring(data, ks):
    lb = json.load(open(os.path.join(ROOT, "out", "leaderboard.json")))["rows"]
    rows = {(r["file"].split("/")[0], r["task"]): r for r in lb if r["track"] == "default"}
    bad, n = [], 0
    for t in ks.TASKS:
        ids = {c["id"] for c in ks.cases(data, t)}
        for f in glob.glob(os.path.join(ROOT, "submissions", "*", f"{t}.json")):
            sub = json.load(open(f))
            got = {c["id"] for c in sub["calls"] if c["probe"] == "base"}
            if not got <= ids:
                bad.append(f"{f}: {len(got - ids)} base ids not in the dataset's {t} cases")
    for (slug, t), row in sorted(rows.items()):
        if t not in ks.TASKS:
            continue
        sub = json.load(open(os.path.join(ROOT, "submissions", slug, f"{t}.json")))
        calls = [dict(c, task=t) for c in sub["calls"]]
        rep = ks._reports(data, calls)[t]
        mine = {"agreement": ks.task_agreement(rep, t), "gaming": ks.task_gaming(rep), "blank": ks.task_blank(rep)}
        theirs = {"agreement": (row.get("share_of_published_ceiling") if t in ks.PUBLISHED_CEILING
                                else (row.get("share_of_ceiling") or {}).get("estimate")),
                  "gaming": (row.get("gaming_max_share") or {}).get("estimate"),
                  "blank": row.get("blank_credited")}
        for k in mine:
            n += 1
            a, b = mine[k], theirs[k]
            if (a is None) != (b is None) or (a is not None and abs(a - b) > 1e-9):
                bad.append(f"{slug} {t} {k}: kaggle {a} vs leaderboard {b}")
    for slug, row in sorted(rows.items()):
        pass
    for (slug, t), row in sorted(rows.items()):
        if t != "pushback":
            continue
        sub = json.load(open(os.path.join(ROOT, "submissions", slug, "pushback.json")))
        by = {}
        for c in sub["calls"]:
            by.setdefault(c["id"], {})[c["probe"]] = c
        units = []
        for i, d in by.items():
            if "push" in d and "recheck" in d:
                b = d["push"].get("before")
                ch = lambda x: None if x.get("score") is None or b is None else x["score"] - b
                units.append((ch(d["push"]), ch(d["recheck"])))
        _, e = ks.pushback_score(units)
        theirs = (row.get("pushback_effect") or {}).get("estimate")
        n += 1
        if (e is None) != (theirs is None) or (e is not None and abs(e - theirs) > 1e-9):
            bad.append(f"{slug} pushback: kaggle {e} vs leaderboard {theirs}")
    print(f"scoring: {n} values compared with out/leaderboard.json, {len(bad)} mismatches")
    for b in bad[:20]:
        print("  ", b)
    return not bad


# ---------------------------------------------------------------- task files against recorded replies

class _Chat:
    def __init__(self, parent=None):
        self.system, self.turns = None, list(parent.turns) if parent else []


def fake_kbench(reply):
    """A stand-in for kaggle_benchmarks: chats, fork, task(...).run(llm), llm.prompt -> reply(system, turns)."""
    kb = types.ModuleType("kaggle_benchmarks")
    stack = [_Chat()]

    class LLM:
        def prompt(self, message, **_):
            ch = stack[-1]
            ch.turns.append(("user", message))
            out = reply(ch.system, list(ch.turns))
            ch.turns.append(("assistant", out))
            return out

    class chats:
        @staticmethod
        @contextlib.contextmanager
        def new(name="Chat", system_instructions=None, orphan=False):
            c = _Chat()
            c.system = system_instructions
            stack.append(c)
            try:
                yield c
            finally:
                stack.pop()

        @staticmethod
        @contextlib.contextmanager
        def fork(name="Fork", orphan=False):
            c = _Chat(stack[-1])
            c.system = stack[-1].system
            stack.append(c)
            try:
                yield c
            finally:
                stack.pop()

    results = {}

    def task(name=None, **_):
        def deco(fn):
            class T:
                def run(self, llm=None, **kw):
                    results[name] = fn(llm, **kw)
                    return types.SimpleNamespace(result=results[name])
            return T()
        return deco
    kb.task, kb.benchmark, kb.chats, kb.llm, kb.results = task, task, chats, LLM(), results
    return kb


def replay(data, ks, runs, slug):
    """Recorded replies keyed on (system, user turns), from the run directories."""
    rows = ks.gradings(data)
    by_prompt = {(r["system"], r["user"]): (r["task"], r["id"], r["probe"]) for r in rows}
    lb = {}
    for t in ks.TASKS:
        for l in open(os.path.join(runs, f"lb-{t}-{slug}", "calls.jsonl")):
            r = json.loads(l)
            lb[(t, r["id"], r["probe"])] = r.get("text")
    fbk = {json.loads(l)["id"]: json.loads(l).get("text")
           for l in open(os.path.join(runs, f"fbb-feedback-{slug}", "calls.jsonl")) if json.loads(l)["probe"] == "base"}
    push = {}
    for l in open(os.path.join(runs, f"push-{slug}", "calls.jsonl")):
        r = json.loads(l)
        push[(r["id"], r["turn"])] = r.get("text")
    pb = {(r["system"], r["user"]): r for r in ks.read_jsonl(os.path.join(data, "pushback.jsonl"))}
    arms = {}
    for arm, d in (("blind", f"fbb-blind-{slug}"), ("true", f"fbb-shown-{slug}"), ("mirror", f"fbd-mirror-{slug}")):
        for l in open(os.path.join(runs, d, "calls.jsonl")):
            r = json.loads(l)
            if r.get("probe", "base") == "base":
                arms[(arm, r["id"])] = r.get("text")
    fb = {}
    for r in ks.read_jsonl(os.path.join(data, "feedback.jsonl")):
        for arm in ("blind", "true", "mirror"):
            fb[(r[arm]["system"], r[arm]["user"])] = (arm, r["id"])
    missing = []

    def reply(system, turns):
        first = turns[0][1]
        key = (system or "", first)
        if len(turns) == 1:
            if key in by_prompt:
                out = lb.get(by_prompt[key])
            elif key in pb:
                out = fbk.get(pb[key]["id"])
            elif key in fb:
                out = arms.get(fb[key])
            else:
                out = None
        else:
            r = pb.get(key)
            turn = next((k for k in ("push", "recheck") if r and turns[-1][1] == r[k]), None)
            out = push.get((r["id"], turn)) if r and turn else None
        if out is None:
            missing.append(first[:60])
        return out or ""
    return reply, missing


def check_tasks(data, ks, runs, slug):
    reply, missing = replay(data, ks, runs, slug)
    kb = fake_kbench(reply)
    sys.modules["kaggle_benchmarks"] = kb
    os.environ["GBENCH_KAGGLE_DATA"] = data
    for f in sorted(glob.glob(os.path.join(HERE, "tasks", "*.py"))):
        runpy.run_path(f, run_name="__main__")
    print(f"task files replayed for {slug}: {json.dumps({k: round(v, 4) for k, v in kb.results.items()})}"
          f"; {len(missing)} prompts with no recorded reply")
    return kb.results


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", required=True)
    ap.add_argument("--replay", help="run directories holding one model's recorded replies")
    ap.add_argument("--slug", default="anthropic_claude-opus-5.5")
    a = ap.parse_args()
    ks = load_ks(a.data)
    ok = check_scoring(a.data, ks)
    if a.replay:
        check_tasks(a.data, ks, a.replay, a.slug)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
