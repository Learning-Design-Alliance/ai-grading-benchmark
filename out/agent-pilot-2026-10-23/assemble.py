"""Turn the Fable subagents' outputs into run folders bench.py can score (agent-harness condition)."""
import json, os, sys, glob, hashlib, time
B = "."
sys.path.insert(0, B)
from prompting import load_prompt
FD = os.path.dirname(os.path.abspath(__file__))
R = "runs"
CASES = {"mohler": "data/mohler/mohler.jsonl",
         "code": "data/harmogen/harmogen-code.jsonl"}
prompt = load_prompt(f"{B}/prompts/default.txt")
keymap = json.load(open(f"{FD}/keys/keymap.json"))
ids = json.load(open(f"{FD}/keys/ids.json"))
cases = {t: {json.loads(l)["id"]: json.loads(l) for l in open(p)} for t, p in CASES.items()}
replies, missing_files = {}, []
for f in sorted(glob.glob(f"{FD}/in/*.jsonl")):
    out = f.replace("/in/", "/out/")
    if not os.path.exists(out):
        missing_files.append(os.path.basename(f)); continue
    for line in open(out):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue
        r = d.get("reply")
        replies[d.get("key")] = r if isinstance(r, str) else json.dumps(r)
for t in ("mohler", "code"):
    calls = []
    for k, m in keymap.items():
        if m["task"] != t:
            continue
        c = cases[t][m["id"]]
        text = replies.get(k)
        lo, hi = c["scale"]
        score = prompt.parse(text, lo, hi) if text else None
        calls.append({"id": m["id"], "task": c["task"], "probe": m["probe"], "score": score, "text": text,
                      "usage": {}, "latency_s": None, "served_model": "claude-fable-5.1 (agent harness)", "provider": "Claude Code subagent",
                      "error": None if text else "no reply in agent output", "cached": False})
    out = f"{R}/{t}-fable-agent-default"
    os.makedirs(out, exist_ok=True)
    sha = hashlib.sha256(open(CASES[t], "rb").read()).hexdigest()
    json.dump({"benchmark_version": "0.2.0-agent", "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "model": "claude-fable-5.1 (agent harness)", "base_url": "Claude Code subagent", "prompt": "default.txt",
               "prompt_sha256": prompt.sha256, "cases": CASES[t], "cases_sha256": sha, "seed": 7,
               "case_ids": ids["mohler_ids" if t == "mohler" else "code_ids"],
               "note": "graded by Claude Code subagents on Fable reading pre-rendered prompts in batches; not an API call"},
              open(f"{out}/config.json", "w"), indent=1)
    with open(f"{out}/calls.jsonl", "w") as fh:
        for x in calls:
            fh.write(json.dumps(x, ensure_ascii=False) + "\n")
    print(t, len(calls), "calls,", sum(1 for x in calls if x["score"] is None), "without a mark ->", out)
print("missing output files:", missing_files)
