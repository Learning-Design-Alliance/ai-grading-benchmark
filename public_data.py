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
    "google/gemini-3.8-flash": ("Gemini 3.8 Flash", "Google", "frontier"),
    "google/gemini-4-argon": ("Gemini 4 Argon", "Google", "frontier"),
    "xiaomi/mimo-v2.6-flash": ("MiMo v2.6 Flash", "Xiaomi", "open weights"),
    "meta/muse-spark-open": ("Muse Spark Open", "Meta", "open weights"),
    "perceptron/perceptron-mk1.5": ("Perceptron mk1.5", "Perceptron", "small hosted"),
    "mistralai/voxtral-small-24b-2507": ("Voxtral Small 24B", "Mistral", "open weights"),
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
            "decision_share": None if not r.get("decision_share") else r4(r["decision_share"]["estimate"]),
            "decision_kappa": None if not r.get("decision_kappa") else r4(r["decision_kappa"]["estimate"]),
            "published_share": r4(r.get("share_of_published_ceiling")),
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


def overall():
    """out/overall.json (leaderboard.py overall): one row per model with its strand scores."""
    p = os.path.join(HERE, "out", "overall.json")
    if not os.path.exists(p):
        return []
    o = json.load(open(p))
    rows = []
    for r in o["rows"]:
        m, vendor, kind = NAMES.get(r["model"], (r["model"], "", ""))
        row = {"key": r["model"], "model": m, "vendor": vendor, "kind": kind, "complete": r["complete"],
               "tasks": ", ".join(TASKS.get(t, t) for t in r["tasks"]), "overall": None if r["overall"] is None else round(r["overall"], 1),
               "rank": r.get("rank"), "rank_lo": (r.get("rank_ci95") or [None, None])[0], "rank_hi": (r.get("rank_ci95") or [None, None])[1],
               "flags": "; ".join(r["flags"])}
        for k, v in r["strands"].items():
            row[k] = None if v is None else round(v, 1)
        rows.append(row)
    return rows


def weights():
    p = os.path.join(HERE, "out", "overall.json")
    if not os.path.exists(p):
        return []
    o = json.load(open(p))
    return [{"strand": k, "weight": w, "means": o["strand_help"][k]} for k, w in o["weights"].items()]


def modality(prefix, task, out_name):
    """Rows for a media task from its runs' report.json (runs are not committed; their aggregates are copied
    to out/<out_name>/ by this function's caller)."""
    rows = []
    d = os.path.join(HERE, "out", out_name)
    if not os.path.isdir(d):
        return rows
    for f in sorted(os.listdir(d)):
        r = json.load(open(os.path.join(d, f)))
        model = r["config"]["model"]
        m, vendor, kind = NAMES.get(model, (model, "", ""))
        v, rl, fa = r["validity"], r["reliability"], r["fairness"]
        lo, hi = r["scale"]
        w = hi - lo
        sh = v.get("share_of_ceiling")
        na = v.get("null_answers") or {}
        lab = (fa.get("attainment") or {}).get("label_effect")
        pc = lambda iv: (None, None, None) if not iv else (round(100 * iv["estimate"] / w, 2), round(100 * iv["ci95"][0] / w, 2), round(100 * iv["ci95"][1] / w, 2))
        g = [x for x in (v.get("injection"), v.get("forged")) if x]
        gm = max(g, key=lambda x: x["estimate"]) if g else None
        row = {"key": f"{f}", "task": task, "model": m, "vendor": vendor, "scale": f"{lo:g}-{hi:g}",
               "qwk": round(v["agreement"]["qwk"]["estimate"], 4),
               "share": None if not sh else round(sh["estimate"], 4),
               "retest": None if not rl.get("retest") else round(rl["retest"]["qwk"]["estimate"], 4),
               "hallucination_pct": None if na.get("credited") is None else round(100 * na["credited"], 1),
               "silence_pct": None if "null_silence" not in (na.get("by_kind") or {}) else round(100 * na["by_kind"]["null_silence"]["credited"], 1),
               "tone_pct": None if "null_tone" not in (na.get("by_kind") or {}) else round(100 * na["by_kind"]["null_tone"]["credited"], 1),
               "offtask_pct": None if not v.get("off_task") else round(100 * v["off_task"]["mean_share_of_scale"], 1),
               "label_pct": pc(lab)[0], "label_lo": pc(lab)[1], "label_hi": pc(lab)[2],
               "noise_pct": pc(rl.get("noise_10db"))[0], "phone_pct": pc(rl.get("phone_band"))[0],
               "gaming_pct": pc(gm)[0], "gaming_lo": pc(gm)[1], "gaming_hi": pc(gm)[2],
               "failed": v["failed_gradings"]["n"],
               "cost_per_1k": None if r["sustainability"].get("cost_per_1000_gradings_usd") is None else round(r["sustainability"]["cost_per_1000_gradings_usd"], 3)}
        rows.append(row)
    return rows


def feedback_board():
    p = os.path.join(HERE, "feedback-board", "out", "feedback-board.json")
    if not os.path.exists(p):
        return []
    rows = []
    for model, v in json.load(open(p))["models"].items():
        m, vendor, kind = NAMES.get(model, (model, "", ""))
        h, g = v.get("halo") or {}, v.get("gives_away") or {}
        rows.append({"key": model, "model": m, "vendor": vendor,
                     "halo": None if not h else round(h["halo"], 3), "halo_lo": None if not h else round(h["ci95"][0], 3),
                     "halo_hi": None if not h else round(h["ci95"][1], 3),
                     "gives_away_pct": None if g.get("share") is None else round(100 * g["share"], 1),
                     "gives_away_lo": None if not g.get("ci95") else round(100 * g["ci95"][0], 1),
                     "gives_away_hi": None if not g.get("ci95") else round(100 * g["ci95"][1], 1), "n": g.get("n")})
    return rows


def images_pooled():
    """The image task's three mark scales pooled per model, weighting each scale by its number of solutions.
    Intervals are not pooled (shown per scale in out/images/); the pooled row carries point estimates only."""
    rows = modality("image", "Handwritten maths (images)", "images")
    by = {}
    for r in rows:
        n = json.load(open(os.path.join(HERE, "out", "images", r["key"])))["validity"]["agreement"]["n"]
        by.setdefault(r["model"], []).append((n, r))
    out = []
    for m, rs in by.items():
        tot = sum(n for n, _ in rs)
        avg = lambda k: None if any(r[k] is None for _, r in rs) else round(sum(n * r[k] for n, r in rs) / tot, 3)
        worst = max(rs, key=lambda x: x[1]["gaming_pct"] if x[1]["gaming_pct"] is not None else -1e9)[1]
        out.append({"key": m, "task": "Handwritten maths (images)", "model": m, "vendor": rs[0][1]["vendor"], "n": tot,
                    "qwk": avg("qwk"), "retest": avg("retest"), "gaming_pct": avg("gaming_pct"),
                    "gaming_worst_scale_pct": worst["gaming_pct"], "gaming_worst_lo": worst["gaming_lo"],
                    "gaming_worst_hi": worst["gaming_hi"], "label_pct": avg("label_pct"), "offtask_pct": avg("offtask_pct"),
                    "cost_per_1k": avg("cost_per_1k")})
    return out


def main(out):
    os.makedirs(out, exist_ok=True)
    for nm, fn in (("leaderboard", leaderboard), ("halo", halo), ("fairness", fairness),
                   ("feedback_checks", feedback_checks), ("drift", drift), ("floor", floor),
                   ("overall", overall), ("weights", weights), ("feedback_board", feedback_board),
                   ("speech", lambda: modality("speech", "Speech (pronunciation)", "speech")),
                   ("images", images_pooled)):
        rows = fn()
        json.dump(rows, open(os.path.join(out, f"{nm}.json"), "w"), indent=0)
        print(f"{nm}: {len(rows)} rows")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "public"))
