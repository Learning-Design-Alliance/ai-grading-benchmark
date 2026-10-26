#!/usr/bin/env python3
"""Before analysing runs: are they complete, and what produced them? (docs/METHODOLOGY.md 2.1, 3.1, 3.2)

For each run folder (a bench.py run, or a pushback run), it reports:
- gradings, and those never sent because a spend cap was reached;
- gradings that failed (no mark), by reason;
- the model served, the hosts and their counts;
- the setup recorded: prompt, label, reasoning effort, precision pin, retention exception, route.

It exits non-zero when any grading was left unsent by a cap, when more than 2% failed, or when a file does not
parse (a half-written file from a crash).

    python3 scripts/check_runs.py <run dir> [...]
"""
import collections
import json
import os
import sys


def check(d):
    out, bad = [], False
    try:
        cfg = json.load(open(os.path.join(d, "config.json")))
        calls = [json.loads(line) for line in open(os.path.join(d, "calls.jsonl"))]
    except (OSError, json.JSONDecodeError) as e:
        return [f"UNREADABLE: {e}"], True
    unsent = sum(1 for r in calls if str(r.get("error") or "").startswith("not sent"))
    failed = sum(1 for r in calls if r.get("score") is None and r.get("after", 0) is None or
                 (r.get("score") is None and "after" not in r))
    reasons = collections.Counter(str(r.get("error") or "no readable mark")[:50] for r in calls
                                  if (r.get("score") if "after" not in r else r.get("after")) is None)
    hosts = collections.Counter(r.get("provider") for r in calls)
    extra = cfg.get("extra_body") or {}
    prov = extra.get("provider") or {}
    setup = {"prompt": cfg.get("prompt"), "label": cfg.get("label"), "reasoning": extra.get("reasoning"),
             "precision": prov.get("quantizations") or "unpinned", "retention_exception": cfg.get("retention_exception"),
             "route": (cfg.get("route") or "")[:40] or None}
    out.append(f"{len(calls)} gradings, {unsent} unsent (cap), {failed} without a mark ({failed / max(1, len(calls)):.1%})")
    if reasons:
        out.append("reasons: " + "; ".join(f"{k} x{v}" for k, v in reasons.most_common(3)))
    out.append(f"model {cfg.get('model')} | served {sorted({str(r.get('served_model')) for r in calls if r.get('served_model')})[:3]}")
    out.append("hosts: " + ", ".join(f"{k} {v}" for k, v in hosts.most_common(5)))
    out.append("setup: " + ", ".join(f"{k}={v}" for k, v in setup.items() if v))
    if unsent or failed / max(1, len(calls)) > 0.02:
        bad = True
    return out, bad


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    nbad = 0
    for d in argv:
        lines, bad = check(d)
        nbad += bad
        print(("INCOMPLETE " if bad else "ok ") + os.path.basename(os.path.normpath(d)))
        for l in lines:
            print("   " + l)
    print(f"{len(argv)} runs, {nbad} incomplete or failing")
    return 1 if nbad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
