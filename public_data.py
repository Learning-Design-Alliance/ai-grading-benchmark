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
- floor.json         out/floor.json;
- baselines, agreement_flags, pushback_split, length_check, per_prompt, multiplicity: the reference baselines
  and the standard checks (out/baselines.json, out/standard_checks.json, out/cluster_check.json,
  out/overall.json);
- corrections.json   docs/CORRECTIONS.md; energy.json from docs/energy.json.

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
    "amazon/nova-2-lite-v1": ("Nova 2 Lite", "Amazon", "small hosted"),
    "qwen/qwen3.8-27b": ("Qwen3.8 27B", "Alibaba (Qwen)", "open weights"),
    "mistralai/voxtral-small-24b-2507": ("Voxtral Small 24B", "Mistral", "open weights"),
}
TASKS = {"mohler": "Short answers", "code": "Code", "asap2": "Essays", "maths": "Maths working", "pushback": "Pushback"}


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
        if r["task"] not in ("mohler", "code", "asap2"):  # maths and pushback have their own datasets
            continue
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
               "flags": "; ".join(r["flags"]),
               "task_lo": None if not r.get("task_range") else round(r["task_range"][0], 1),
               "task_hi": None if not r.get("task_range") else round(r["task_range"][1], 1)}
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


def video():
    """The video task (LASANA): one row per run, from out/video/ (bench.py reports + video/analyse.py extras).
    Blank-video shares count declined gradings in the denominator, as video/PREREG.md defines hallucination."""
    d = os.path.join(HERE, "out", "video")
    ex_p = os.path.join(d, "extras.json")
    if not os.path.exists(ex_p):
        return []
    ex = json.load(open(ex_p))
    rows = []
    for run, e in ex["runs"].items():
        rp = os.path.join(d, f"{run}.json")
        r = json.load(open(rp)) if os.path.exists(rp) else None
        m, vendor, kind = NAMES.get(e["model"], (e["model"], "", ""))
        v, rl, fa = (r["validity"], r["reliability"], r["fairness"]) if r else ({}, {}, {})
        w = 16
        pc = lambda iv: None if not iv else round(100 * iv["estimate"] / w, 1)
        g = [x for x in (v.get("injection"), v.get("forged")) if x]
        gm = max(g, key=lambda x: x["estimate"]) if g else None
        b = e.get("blank") or {}
        share = lambda k: None if not b.get(k) or not b[k]["n"] else round(100 * b[k]["credited"] / b[k]["n"], 1)
        bl = e["base"]
        sc = (v.get("share_of_ceiling") or {}).get("estimate") if v else None
        nb = e["base"]["n"]
        rows.append({"key": run, "model": m, "vendor": vendor,
                     "input": "16 frames" if e.get("video_frames") else "video",
                     "graded": nb, "qwk": None if bl["qwk"] is None else round(bl["qwk"], 3),
                     "text_only_qwk": None if e["text_only"]["qwk"] is None else round(e["text_only"]["qwk"], 3),
                     "share": None if sc is None or nb < 50 else round(sc, 3),
                     "beyond": None if bl["beyond_length"] is None else round(bl["beyond_length"], 3),
                     "beyond_lo": None if not bl["beyond_length_ci95"] else round(bl["beyond_length_ci95"][0], 3),
                     "beyond_hi": None if not bl["beyond_length_ci95"] else round(bl["beyond_length_ci95"][1], 3),
                     "verdict": e["verdict"] or ("DID NOT RATE" if nb < 50 else None),
                     "not_ruled_out": None if not e.get("not_ruled_out") else round(e["not_ruled_out"]["beyond_length_up_to"], 2),
                     "black_pct": share("null_black"), "still_pct": share("null_still"),
                     "gaming_pct": pc(gm), "label_pct": pc((fa.get("attainment") or {}).get("label_effect")),
                     "lowres_pct": pc(rl.get("low_res")), "camera_pct": pc(rl.get("other_camera")),
                     "retest": None if not rl.get("retest") else round(rl["retest"]["qwk"]["estimate"], 3),
                     "tokens": e.get("median_prompt_tokens"),
                     "cost_per_1k": None if not r or r["sustainability"].get("cost_per_1000_gradings_usd") is None else round(r["sustainability"]["cost_per_1000_gradings_usd"], 2)})
    rows.sort(key=lambda x: -(x["beyond"] if x["beyond"] is not None else -9))
    h = ex["human"]
    rows.append({"key": "human", "model": "Raters (one against the others)", "vendor": "", "input": "video", "graded": None,
                 "qwk": round(h["ceiling_qwk"], 3), "text_only_qwk": None, "share": 1.0, "beyond": round(h["beyond_length"], 3),
                 "beyond_lo": None, "beyond_hi": None, "verdict": "REFERENCE", "black_pct": None, "still_pct": None,
                 "gaming_pct": None, "label_pct": None, "lowres_pct": None, "camera_pct": None, "retest": None, "tokens": None,
                 "cost_per_1k": None})
    return rows


def video_length():
    p = os.path.join(HERE, "out", "video", "padding.json")
    if not os.path.exists(p):
        return []
    rows = []
    for run, e in json.load(open(p))["runs"].items():
        m, vendor, kind = NAMES.get(e["model"], (e["model"], "", ""))
        b1, b4 = e["by_length"]["x1"], e["by_length"]["x4"]
        ch = e["change"]["x4-x1"]["balanced"]
        r1 = lambda x: None if x is None else round(x, 3)
        rows.append({"key": run, "model": m, "bal_x1": r1(b1["balanced"]), "bal_x4": r1(b4["balanced"]),
                     "sens_x1": r1(b1["sensitivity"]), "sens_x4": r1(b4["sensitivity"]),
                     "spec_x1": r1(b1["specificity"]), "spec_x4": r1(b4["specificity"]),
                     "change": r1(ch[0]), "change_lo": r1(ch[1][0]), "change_hi": r1(ch[1][1]),
                     "failed": sum(e["failed"].values()), "verdict": e["verdict"],
                     "loss_not_ruled_out": None if not e.get("not_ruled_out") else round(e["not_ruled_out"]["balanced_accuracy_loss_up_to"], 2)})
    return rows


def maths():
    p = os.path.join(HERE, "maths-process", "out", "process.json")
    if not os.path.exists(p):
        return []
    rows = []
    for g in json.load(open(p))["graders"]:
        m = NAMES.get(g["grader"], (g["grader"], "", ""))[0]
        mc, loc = g["mean_credit"], g.get("first_wrong_step_exact") or {}
        r2 = lambda x: None if x is None else round(x, 3)
        rows.append({"key": g["grader"], "model": m, "working": r2(g["reasoning_effect"]),
                     "working_lo": r2(g["reasoning_ci95"][0]), "working_hi": r2(g["reasoning_ci95"][1]),
                     "answer": r2(g["answer_effect"]), "correct": r2(mc["correct"]), "slip": r2(mc["slip"]),
                     "lucky": r2(mc["lucky"]), "wrong": r2(mc["wrong"]), "lucky_full_pct": round(100 * g["lucky_accepted"], 1),
                     "first_step_pct": None if loc.get("wrong") is None else round(100 * loc["wrong"], 1), "verdict": g["verdict"]})
    return rows


def pushback():
    p = os.path.join(HERE, "feedback-board", "out", "pushback.json")
    if not os.path.exists(p):
        return []
    rows = []
    for model, v in json.load(open(p))["models"].items():
        m = NAMES.get(model, (model, "", ""))[0]
        pb, pc = v.get("pushback") or {}, v.get("praise_calibration") or {}
        if not pb:
            continue
        rows.append({"key": model, "model": m, "effect_pct": round(100 * pb["effect"], 1),
                     "effect_lo": round(100 * pb["ci95"][0], 1), "effect_hi": round(100 * pb["ci95"][1], 1),
                     "full_push_pct": round(100 * pb["to_full_marks"]["push"], 1),
                     "full_recheck_pct": round(100 * pb["to_full_marks"]["recheck"], 1), "verdict": pb["verdict"],
                     "yield_not_ruled_out_pct": None if not pb.get("not_ruled_out") else round(100 * pb["not_ruled_out"]["yielding_up_to"], 1),
                     "praise_rho": None if pc.get("spearman_tone_vs_experts") is None else round(pc["spearman_tone_vs_experts"], 3)})
    rows.sort(key=lambda x: -x["effect_pct"])
    return rows


def _load(*parts):
    p = os.path.join(HERE, *parts)
    return json.load(open(p)) if os.path.exists(p) else None


def baselines():
    """out/baselines.json: classic non-LLM scorers on the same cases and probes, as reference rows."""
    d = _load("out", "baselines.json")
    if not d:
        return []
    rows = []
    for r in d["rows"]:
        sh = (r.get("share_of_ceiling") or {}).get("estimate")
        g = (r.get("gaming_max_share") or {}).get("estimate")
        rows.append({"key": f"{r['task']}:{r['model']}", "task": TASKS.get(r["task"], r["task"]), "baseline": r["model"].replace("baseline: ", ""),
                     "qwk": round(r["qwk"]["estimate"], 3), "qwk_lo": round(r["qwk"]["ci95"][0], 3), "qwk_hi": round(r["qwk"]["ci95"][1], 3),
                     "share": None if sh is None else round(sh, 3),
                     "share_published": None if r.get("share_of_published_ceiling") is None else round(r["share_of_published_ceiling"], 3),
                     "blank_pct": None if r.get("blank_credited") is None else round(100 * r["blank_credited"], 1),
                     "gaming_pct": None if g is None else round(100 * g, 1), "n_train": r["n_train"]})
    return rows


def agreement_flags():
    """analyses/standard_checks.py: Williamson, Xi and Breyer flags per model and task."""
    d = _load("out", "standard_checks.json")
    if not d:
        return []
    r3 = lambda x: None if x is None else round(x, 3)
    return [{"key": f"{r['model']}:{r['task']}", "model": name(r["model"]), "task": TASKS.get(r["task"], r["task"]),
             "qwk": r3(r["qwk"]), "qwk_flag": r["qwk_flag"], "degradation": r3(r["degradation"]), "degradation_flag": r["degradation_flag"],
             "smd": r3(r["smd"]), "smd_lo": r3((r["smd_ci95"] or [None])[0]), "smd_hi": r3((r["smd_ci95"] or [None, None])[1]),
             "smd_flag": r["smd_flag"]} for r in d["agreement"]]


def pushback_split():
    d = _load("out", "standard_checks.json")
    if not d:
        return []
    out = []
    for r in d["pushback"]:
        iv = r["effect_not_under_marked_ci95"]
        out.append({"key": r["model"], "model": name(r["model"]), "corrections": r["raises"]["progressive"],
                    "sycophantic": r["raises"]["regressive"],
                    "regressive_pct": None if r["regressive_share"] is None else round(100 * r["regressive_share"], 1),
                    "effect_fair_pct": None if r["effect_not_under_marked"] is None else round(100 * r["effect_not_under_marked"], 1),
                    "effect_fair_lo": None if not iv else round(100 * iv[0], 1), "effect_fair_hi": None if not iv else round(100 * iv[1], 1),
                    "n": r["n_not_under_marked"]})
    return sorted(out, key=lambda x: -(x["effect_fair_pct"] or -99))


def length_check():
    d = _load("out", "standard_checks.json")
    if not d:
        return []
    rows = [{"key": f"{r['model']}:{r['task']}", "model": name(r["model"]), "task": TASKS.get(r["task"], r["task"]),
             "coef": None if r["coef"] is None else round(r["coef"], 3), "lo": None if not r["ci95"] else round(r["ci95"][0], 3),
             "hi": None if not r["ci95"] else round(r["ci95"][1], 3)} for r in d["length"]]
    for t, v in d["length_human"].items():
        rows.append({"key": f"raters:{t}", "model": "Raters (reference)", "task": TASKS.get(t, t),
                     "coef": None if v["coef"] is None else round(v["coef"], 3),
                     "lo": None if not v["ci95"] else round(v["ci95"][0], 3), "hi": None if not v["ci95"] else round(v["ci95"][1], 3)})
    return rows


def per_prompt():
    """analyses/cluster_check.py: agreement per essay prompt and per code exercise."""
    d = _load("out", "cluster_check.json")
    if not d:
        return []
    rows = []
    for task, out in d["per_prompt"].items():
        for o in out:
            for item, q in o["per_prompt_qwk"].items():
                rows.append({"key": f"{o['model']}:{task}:{item}", "model": name(o["model"]), "task": TASKS.get(task, task),
                             "item": item, "n": o["n_per_prompt"][item], "qwk": None if q is None else round(q, 3)})
    return rows


def multiplicity():
    o = _load("out", "overall.json")
    if not o or "multiplicity" not in o:
        return []
    mu = o["multiplicity"]
    rows = [{"key": "summary", "model": "", "task": "", "probe": f"{mu['tests']} intervals; {mu['flagged']} exclude 0; {mu['survive']} survive",
             "p": None, "q": None}]
    rows += [{"key": f"{x['model']}:{x['task']}:{x['probe']}", "model": name(x["model"]), "task": TASKS.get(x["task"], x["task"]),
              "probe": x["probe"], "p": round(x["p"], 4), "q": round(x["q"], 4)} for x in mu["do_not_survive"]]
    return rows


def corrections():
    p = os.path.join(HERE, "docs", "CORRECTIONS.md")
    if not os.path.exists(p):
        return []
    rows = []
    for line in open(p, encoding="utf-8"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 6 and re.match(r"\d{4}-\d{2}-\d{2}$", cells[0]):
            rows.append({"key": f"{cells[0]}:{len(rows)}", "date": cells[0], "what": cells[1], "was": cells[2], "now": cells[3],
                         "why": cells[4], "where": cells[5].replace("`", "")})
    return rows


def energy():
    e = _load("docs", "energy.json")
    if not e:
        return []
    q = e["per_query_wh"]
    rows = []
    for s in e["scenarios"]:
        n = s["gradings"]
        for kind, lo, hi in (("ordinary model", q["ordinary_low"], q["ordinary_high"]), ("reasoning model", q["reasoning"], q["reasoning"])):
            kwh = (n * lo / 1000, n * hi / 1000)
            co2 = tuple(k * e["grid_kg_co2_per_kwh"] for k in kwh)
            rows.append({"key": f"{s['name']}:{kind}", "scenario": s["name"], "model_kind": kind,
                         "wh_lo": round(1000 * kwh[0], 2), "wh_hi": round(1000 * kwh[1], 2),
                         "stream_hours_lo": round(kwh[0] / e["streaming_kwh_per_hour"], 3), "stream_hours_hi": round(kwh[1] / e["streaming_kwh_per_hour"], 3),
                         "co2_g_lo": round(1000 * co2[0], 2), "co2_g_hi": round(1000 * co2[1], 2),
                         "car_km_lo": round(1000 * co2[0] / e["petrol_car_g_per_km"], 4), "car_km_hi": round(1000 * co2[1] / e["petrol_car_g_per_km"], 4),
                         "water_ml_lo": round(n * e["water_ml_per_query"]["low"], 2), "water_ml_hi": round(n * e["water_ml_per_query"]["high_high"], 1)})
    return rows


def main(out):
    os.makedirs(out, exist_ok=True)
    for nm, fn in (("leaderboard", leaderboard), ("halo", halo), ("fairness", fairness),
                   ("feedback_checks", feedback_checks), ("drift", drift), ("floor", floor),
                   ("overall", overall), ("weights", weights), ("feedback_board", feedback_board),
                   ("speech", lambda: modality("speech", "Speech (pronunciation)", "speech")),
                   ("images", images_pooled), ("video", video), ("video_length", video_length),
                   ("maths", maths), ("pushback", pushback), ("baselines", baselines), ("agreement_flags", agreement_flags),
                   ("pushback_split", pushback_split), ("length_check", length_check), ("per_prompt", per_prompt),
                   ("multiplicity", multiplicity), ("corrections", corrections), ("energy", energy)):
        rows = fn()
        json.dump(rows, open(os.path.join(out, f"{nm}.json"), "w"), indent=0)
        print(f"{nm}: {len(rows)} rows")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "public"))
