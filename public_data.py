#!/usr/bin/env python3
"""
Builds the public report's data files from committed aggregates, so every number on the report can be
regenerated:

- leaderboard.json   from out/leaderboard.json (`leaderboard.py build submissions/ ...`): one row per model
                     and task, every number recomputed from the submitted marks;
- halo.json          out/feedback-2026-10-23/halo.json;
- fairness.json      fairness-ellipse/out/result.json, rep-result.json and disability/out/result.json;
- feedback_checks.json  feedback-validity/out/result.json and lc-result.json;
- drift.json         out/lineage-2026-10-23/drift.txt;
- floor.json         out/floor.json.

    python3 public_data.py <out dir>

Only default-prompt results are included: the product prompt's results stay internal. Shares are of the
scale (marks / scale width), so tasks with different scales sit on one axis.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = {
    "anthropic/claude-opus-5.5": ("Claude Opus 5.5", "Anthropic", "frontier"),
    "anthropic/claude-fable-5.1": ("Claude Fable 5.1", "Anthropic", "frontier"),
    "openai/gpt-6-astra": ("GPT-6 Astra", "OpenAI", "frontier"),
    "openai/gpt-5-mini": ("GPT-5 Mini", "OpenAI", "small hosted"),
    "openai/gpt-5.6-luna": ("GPT-5.6 Luna", "OpenAI", "small hosted"),
    "anthropic/claude-haiku-5.5": ("Claude Haiku 5.5", "Anthropic", "small hosted"),
    "google/gemini-3.5-flash-lite": ("Gemini 3.5 Flash Lite", "Google", "small hosted"),
    "qwen/qwen3-235b-a22b-2507": ("Qwen3 235B", "Alibaba (Qwen)", "open weights"),
    "deepseek/deepseek-v4.1-flash": ("DeepSeek V4.1 Flash", "DeepSeek", "open weights"),
    "google/gemma-4-31b-it": ("Gemma 4 31B", "Google", "open weights"),
    "google/gemma-4-26b-a4b-it": ("Gemma 4 26B A4B", "Google", "open weights"),
    "google/gemma-3-27b-it": ("Gemma 3 27B", "Google", "open weights"),
    "google/gemma-3-4b-it": ("Gemma 3 4B", "Google", "open weights"),
    "openai/gpt-oss-20b": ("GPT-OSS 20B", "OpenAI", "open weights"),
    "microsoft/phi-4": ("Phi-4", "Microsoft", "open weights"),
    "mistralai/ministral-8b-2512": ("Ministral 8B", "Mistral", "open weights"),
    "meta-llama/llama-3.2-3b-instruct": ("Llama 3.2 3B", "Meta", "open weights"),
    "deepseek_deepseek-v4.1-flash": ("DeepSeek V4.1 Flash", "DeepSeek", "open weights"),
}
TASKS = {"mohler": "Short answers", "code": "Code", "asap2": "Essays"}


def name(model):
    return NAMES.get(model, (model, "", ""))[0]


def r4(x):
    return None if x is None else round(x, 4)


def pct(iv):
    return (None, None, None) if not iv else (round(100 * iv["estimate"], 2), round(100 * iv["ci95"][0], 2),
                                              round(100 * iv["ci95"][1], 2))


def leaderboard():
    rows = []
    for r in json.load(open(os.path.join(HERE, "out", "leaderboard.json")))["rows"]:
        m, vendor, kind = NAMES.get(r["model"], (r["model"], "", ""))
        sh = r.get("share_of_ceiling")
        g, gl, gh = pct(r.get("gaming_max_share"))
        lb, lbl, lbh = pct(r.get("attainment_label_share"))
        bl, _, _ = pct(r.get("blicket_share"))
        su, _, _ = pct(r.get("surface_share"))
        rows.append({
            "key": f"{r['task']}|{r['model']}", "task": TASKS[r["task"]], "model": m, "vendor": vendor, "kind": kind,
            "qwk": r4(r["qwk"]["estimate"]), "qwk_lo": r4(r["qwk"]["ci95"][0]), "qwk_hi": r4(r["qwk"]["ci95"][1]),
            "share": r4(sh["estimate"]) if sh else None, "share_lo": r4(sh["ci95"][0]) if sh else None,
            "share_hi": r4(sh["ci95"][1]) if sh else None,
            "retest": r4((r.get("retest_qwk") or {}).get("estimate")),
            "gaming_pct": g, "gaming_lo": gl, "gaming_hi": gh,
            "label_pct": lb, "label_lo": lbl, "label_hi": lbh,
            "blicket_pct": bl, "surface_pct": su,
            "blank_pct": None if r.get("blank_credited") is None else round(100 * r["blank_credited"], 1),
            "refused": r["refused"], "gradings": r["gradings"],
            "cost_per_1k": None if r.get("cost_per_1000_usd_self_reported") is None else round(r["cost_per_1000_usd_self_reported"], 3),
            "verified": bool(r.get("verified")), "served_by": ", ".join(r.get("providers") or []),
        })
    return rows


def halo():
    d = json.load(open(os.path.join(HERE, "out", "feedback-2026-10-23", "halo.json")))["runs"]
    out = []
    for k, v in d.items():
        task, slug = k.split("|")
        model = slug.replace("_", "/", 1)
        out.append({"key": k, "task": {"mohler": "Short answers", "persuade": "Essays"}[task],
                    "model": name(model), "halo": r4(v["halo"]), "lo": r4(v["ci95"][0]), "hi": r4(v["ci95"][1]),
                    "corr_hidden": r4(v["corr_blind"]), "corr_shown": r4(v["corr_shown"]), "n": v["n"], "flag": v["flag"]})
    return out


def fairness():
    out = []
    labels = {"C1": "ELLIPSE: economically disadvantaged vs not", "C2": "ELLIPSE: Black vs White",
              "C3": "ELLIPSE: Hispanic vs White (first draw)"}
    e = json.load(open(os.path.join(HERE, "fairness-ellipse", "out", "result.json")))
    for c, v in e["contrasts"].items():
        for m, g in v["graders"].items():
            out.append({"key": f"{c}|{m}", "test": labels[c], "grader": name(m), "gap": r4(g["D"]["estimate"]),
                        "lo": r4(g["D"]["ci95"][0]), "hi": r4(g["D"]["ci95"][1]), "verdict": g["verdict"],
                        "reference": "beyond a second human rater", "scale": "1-5"})
    rp = json.load(open(os.path.join(HERE, "fairness-ellipse", "out", "rep-result.json")))
    for m, g in rp["arms"]["RA"]["graders"].items():
        out.append({"key": f"RA|{m}", "test": "ELLIPSE: Hispanic vs White (replication)", "grader": name(m),
                    "gap": r4(g["D"]["estimate"]), "lo": r4(g["D"]["ci95"][0]), "hi": r4(g["D"]["ci95"][1]),
                    "verdict": g["verdict"], "reference": "beyond a second human rater", "scale": "1-5"})
    dg = json.load(open(os.path.join(HERE, "disability", "out", "result.json")))
    for k, x in dg.items():
        if k.endswith("default.txt"):
            m = k.split(" / ")[0]
            out.append({"key": f"ASAP|{m}", "test": "ASAP 2.0: identified with a disability vs not", "grader": name(m),
                        "gap": r4(x["gap"]), "lo": r4(x["ci95"][0]), "hi": r4(x["ci95"][1]), "verdict": x["verdict"],
                        "reference": "against the released mark (one per essay)", "scale": "1-6"})
    return out


def feedback_checks():
    out = []
    v = json.load(open(os.path.join(HERE, "feedback-validity", "out", "result.json")))["pairs"]
    names = {"LEAK": ("Copies 5 words of the solution", "Reveals the answer"), "ACTION": ("Action phrases", "Actionable"),
             "TONE": ("Tone (praise minus criticism)", "Encouraging vs neutral"), "MISTAKE": ("Critical phrases", "Identifies the mistake")}
    for k, x in v.items():
        out.append({"key": f"rule|{k}", "measure": names[k][0], "by": "this benchmark (word rules)", "label": names[k][1],
                    "auc": r4(x.get("auc")), "lo": r4((x.get("auc_ci") or [None, None])[0]), "hi": r4((x.get("auc_ci") or [None, None])[1]),
                    "length_auc": r4(x.get("length_auc")), "verdict": x["verdict"]})
    lc = json.load(open(os.path.join(HERE, "feedback-validity", "out", "lc-result.json")))["evaluators"]
    lcn = {"WITHHOLD": ("Withholding Answers", "Reveals the answer"), "ACTION": ("Revision Actionability", "Actionable")}
    for k, x in lc.items():
        out.append({"key": f"lc|{k}", "measure": lcn[k][0], "by": "Learning Commons (GPT-5.4), out of scope", "label": lcn[k][1],
                    "auc": r4(x["auc"]), "lo": r4(x["auc_ci"][0]), "hi": r4(x["auc_ci"][1]),
                    "length_auc": r4(x["length_auc"]), "verdict": x["verdict"]})
    return out


def drift():
    txt = open(os.path.join(HERE, "out", "lineage-2026-10-23", "drift.txt")).read()
    out = []
    for blk in txt.split("== ")[1:]:
        head = blk.splitlines()[0].strip()
        a, b = [s.strip() for s in head.split("->")]
        m = re.search(r"mean shift B - A\s+([+-][\d.]+) \[([+-][\d.]+), ([+-][\d.]+)\]", blk)
        x = re.search(r"agreement A with B\s+QWK ([\d.]+)", blk)
        y = re.search(r"agreement A with itself QWK ([\d.]+)", blk)
        out.append({"key": head, "from": a, "to": b, "shift": float(m.group(1)), "lo": float(m.group(2)),
                    "hi": float(m.group(3)), "qwk_across": float(x.group(1)), "qwk_within": float(y.group(1))})
    return out


def floor():
    fl = json.load(open(os.path.join(HERE, "out", "floor.json")))
    return [{"key": f"{wn}|{k}", "world": wn, "effect": k, "planted": e["planted"], "recovered": round(e["mean_estimate"], 3),
             "flagged": e["flagged"], "of": e["of"], "passed": e["ok"]}
            for wn, wd in fl["worlds"].items() for k, e in wd["effects"].items()]


def main(out):
    os.makedirs(out, exist_ok=True)
    for nm, fn in (("leaderboard", leaderboard), ("halo", halo), ("fairness", fairness),
                   ("feedback_checks", feedback_checks), ("drift", drift), ("floor", floor)):
        rows = fn()
        json.dump(rows, open(os.path.join(out, f"{nm}.json"), "w"), indent=0)
        print(f"{nm}: {len(rows)} rows")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "public"))
