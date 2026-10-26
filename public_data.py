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
- corrections.json   docs/CORRECTIONS.md; energy.json from docs/energy.json; models.json from docs/models.json;
- contamination.json from contamination/out/search.json; energy_measured.json from docs/energy.json's measured
  block (energy/).

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
    "allenai/olmo-3.1-32b-instruct": ("Olmo 3.1 32B", "Ai2", "open weights"),
    "deepseek_deepseek-v4.1-flash": ("DeepSeek V4.1 Flash", "DeepSeek", "open weights"),
    "google/gemini-3.8-flash": ("Gemini 3.8 Flash", "Google", "frontier"),
    "google/gemini-4-argon": ("Gemini 4 Argon", "Google", "frontier"),
    "xiaomi/mimo-v2.6-flash": ("MiMo v2.6 Flash", "Xiaomi", "open weights"),
    "meta/muse-spark-open": ("Muse Spark Open", "Meta", "open weights"),
    "perceptron/perceptron-mk1.5": ("Perceptron mk1.5", "Perceptron", "small hosted"),
    "amazon/nova-2-lite-v1": ("Nova 2 Lite", "Amazon", "small hosted"),
    "qwen/qwen3.8-27b": ("Qwen3.8 27B", "Alibaba (Qwen)", "open weights"),
    "mistralai/voxtral-small-24b-2507": ("Voxtral Small 24B", "Mistral", "open weights"),
    "deepseek/deepseek-v4.1-flash-1017": ("DeepSeek V4.1 Flash (Oct 17 snapshot)", "DeepSeek", "open weights"),
    "deepseek/deepseek-v4-pro-0813": ("DeepSeek V4 Pro", "DeepSeek", "open weights"),
    "z-ai/glm-5.3": ("GLM 5.3", "Zhipu AI (Z.ai)", "open weights"),
    "z-ai/glm-5.3-flash": ("GLM 5.3 Flash", "Zhipu AI (Z.ai)", "open weights"),
}
TASKS = {"mohler": "Short answers", "code": "Code", "asap2": "Essays", "maths": "Maths working", "pushback": "Pushback"}


# Runs not made under zero data retention, footnoted wherever the model's results are shown.
RETENTION_NOTES = {
    "anthropic/claude-fable-5.1": "Run through the maintainers' own Anthropic key, under its 30-day safety retention: Fable 5.1 "
                                  "has no zero-retention route. Public corpora only, no student identities.",
}


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
               "retention_note": RETENTION_NOTES.get(r["model"]),
               "task_lo": None if not r.get("task_range") else round(r["task_range"][0], 1),
               "task_hi": None if not r.get("task_range") else round(r["task_range"][1], 1)}
        for k, v in r["strands"].items():
            row[k] = None if v is None else round(v, 1)
        rows.append(row)
    return rows


#: Non-prompted graders on the scoring board, named by base model, maker, size and what they were trained on, so a
#: reader always knows what a row is (the maintainer's request, 2026-10-26).
TRAINED = {
    "baseline: length": ("Length alone", "classic", "linear regression on log word count (code: characters)"),
    "baseline: tfidf-ridge": ("Word features (TF-IDF + ridge)", "classic", "word 1-2 grams (code: character 3-5 grams), ridge regression"),
    "baseline: reference-similarity": ("Similarity to the reference answer", "classic", "TF-IDF cosine similarity to the model answer, mapped to the scale"),
    "baseline: encoder-ridge": ("MiniLM-L6 embeddings + ridge", "small encoder", "all-MiniLM-L6-v2 (sentence-transformers, from Microsoft's MiniLM; 22M parameters) sentence embeddings, ridge regression"),
    "baseline: deberta-ft": ("DeBERTa-v3-base, fine-tuned", "fine-tuned encoder", "microsoft/deberta-v3-base (Microsoft, 184M parameters), fine-tuned with a regression head"),
    "fine-tuned: DeBERTa-v3-base": ("DeBERTa-v3-base, fine-tuned (essay study)", "fine-tuned encoder", "microsoft/deberta-v3-base (Microsoft, 184M parameters), fine-tuned on ASAP 2.0's training essays"),
    "fine-tuned: Qwen3 4B LoRA": ("Qwen3 4B Instruct, fine-tuned (LoRA)", "fine-tuned language model", "Qwen/Qwen3-4B-Instruct-2507 (Alibaba Qwen, 4B parameters), LoRA and a regression head"),
    "fine-tuned: Gemma 4 26B A4B LoRA": ("Gemma 4 26B A4B, fine-tuned (LoRA)", "fine-tuned language model", "Gemma 4 26B A4B instruction-tuned (Google, 26B parameters, 4B active), LoRA and a regression head"),
}


def _trained_label(model, n_train):
    """A trained grader's display name, group and a description with what it learned from."""
    label, group, how = TRAINED.get(model, (model, "trained", ""))
    n = {TASKS.get(t, t): v for t, v in (n_train or {}).items() if v}
    learned = "; ".join(f"{k.lower()}: {v:,} marked answers" for k, v in n.items())
    return label, group, how + (f". Trained on this corpus's own marked answers ({learned})" if learned else "")


def scoring():
    """out/scoring.json (leaderboard.py scoring): every grader on the six scoring strands, across tasks and by task."""
    p = os.path.join(HERE, "out", "scoring.json")
    if not os.path.exists(p):
        return []
    o = json.load(open(p))
    rows = []
    tracks = {r["model"]: (r.get("track"), r.get("n_train"), r.get("by_construction")) for r in o["rows"]}

    def describe(model, task=None):
        track, n_train, bc = tracks.get(model, ("prompted", None, None))
        if track in ("baseline", "fine-tuned"):
            if task and n_train:
                n_train = {task: n_train.get(task)}
            label, group, how = _trained_label(model, n_train)
            return {"model": label, "vendor": "", "kind": "trained", "group": group, "how": how, "by_construction": bc}
        m, vendor, kind = NAMES.get(model, (model, "", ""))
        return {"model": m, "vendor": vendor, "kind": kind, "group": kind, "how": None, "by_construction": None}
    for r in o["rows"]:
        row = {"key": "all|" + r["model"], "task": "All tasks", "model_id": r["model"], **describe(r["model"]),
               "complete": r["complete"], "tasks": ", ".join(TASKS.get(t, t) for t in r["tasks"]),
               "score": None if r["overall"] is None else round(r["overall"], 1), "rank": r.get("rank"),
               "rank_lo": (r.get("rank_ci95") or [None, None])[0], "rank_hi": (r.get("rank_ci95") or [None, None])[1],
               "flags": "; ".join(r["flags"]), "reference": bool(r.get("reference"))}
        for k in o["strands"]:
            v = r["strands"].get(k)
            row[k] = None if v is None else round(v, 1)
        rows.append(row)
    for t, tr in o["by_task"].items():
        for r in tr:
            row = {"key": t + "|" + r["model"], "task": TASKS.get(t, t), "model_id": r["model"], **describe(r["model"], t),
                   "complete": True, "score": None if r["score"] is None else round(r["score"], 1), "rank": r["rank"],
                   "rank_lo": None, "rank_hi": None, "flags": "; ".join(r["flags"]), "reference": bool(r.get("reference"))}
            for k in o["strands"]:
                v = r["strands"].get(k)
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


def models():
    """docs/models.json: what each vendor documents, beside two of the benchmark's own measurements."""
    d = _load("docs", "models.json")
    if not d:
        return []
    pb = {k: v.get("pushback") for k, v in (_load("feedback-board", "out", "pushback.json") or {"models": {}})["models"].items()}
    ov = {r["model"]: r for r in (_load("out", "overall.json") or {"rows": []})["rows"]}
    fmti = d["fmti"]["scores"]
    rows = []
    for m in d["models"]:
        k = m["model"]
        p = pb.get(k) or {}
        vendor = NAMES.get(k, (k, "", ""))[1]
        rows.append({"key": k, "model": name(k) if k in NAMES else k.split("/")[-1], "vendor": vendor,
                     "candidate": bool(m.get("candidate")), "weights": m["weights"], "licence": m["licence"],
                     "params": m["params"], "cutoff": m["cutoff"], "training_data": m["training_data"],
                     "training_tokens": m.get("training_tokens"), "training_sources": m.get("training_sources"),
                     "user_data": m.get("user_data"), "decontamination": m.get("decontamination"),
                     "distilled_from": m.get("distilled_from"), "education_data": m.get("education_data"),
                     "card": m["card"], "card_date": m["card_date"], "sycophancy_claim": m["sycophancy_eval"],
                     "pushback_measured": None if not p else f"{p['verdict']} ({100 * p['effect']:+.1f}% of the scale)",
                     "injection_claim": m["injection_eval"],
                     "gaming_measured": None if k not in ov else ("gamed by more than 5% of the scale" if any("gamed" in f for f in ov[k]["flags"]) else "not gamed above 5%"),
                     "bias_claim": m["bias_eval"], "education_eval": m["education_eval"], "energy": m["energy"], "zdr": m["zdr"],
                     "fmti": fmti.get(vendor)})
    return rows


def contamination():
    """contamination/out/search.json: the benchmark's texts searched for in two open training sets."""
    d = _load("contamination", "out", "search.json")
    if not d:
        return []
    rows = []
    for index, r in d["indexes"].items():
        nm = {"v4_olmo-2-0325-32b-instruct_llama": "OLMo 2 32B Instruct (all training data)",
              "v4_dclm-baseline_llama": "DCLM-baseline (filtered Common Crawl)"}.get(index, index)
        fl = r["floor"]
        for task, c in r["corpora"].items():
            rows.append({"key": f"{index}:{task}", "index": nm, "task": TASKS.get(task, task), "eligible": c["eligible"],
                         "found": c["found"], "share": None if c["share"] is None else round(c["share"], 3),
                         "lo": None if not c["ci95"] else round(c["ci95"][0], 3), "hi": None if not c["ci95"] else round(c["ci95"][1], 3),
                         "verdict": c["verdict"], "questions_found": c["questions"]["found"], "questions": c["questions"]["eligible"],
                         "floor_positive": round(fl["positive_found"], 3), "floor_negative": round(fl["negative_found"], 3)})
    return rows


def energy_tasks():
    """docs/energy.json: energy per grading by task and model size, with a half-pound beef burger for scale."""
    e = _load("docs", "energy.json")
    if not e or "tasks" not in e:
        return []
    tiers = e["per_token_model"]["tiers"]
    g = e["grid_kg_co2_per_kwh"]  # kg per kWh = g per Wh
    b = e["burger"]
    burger_g = b["kg"] * b["kg_co2e_per_kg"] * 1000
    rows = []
    for tk in e["tasks"]:
        wh = {k: c + a * tk["input_tokens"] / 1000 + o * tk["output_tokens"] / 1000 for k, (c, a, o) in tiers.items()}
        names = list(tiers)
        mid = wh[names[1]]
        rows.append({"key": tk["task"], "task": tk["task"], "input_tokens": tk["input_tokens"], "output_tokens": tk["output_tokens"],
                     "wh_small": round(wh[names[0]], 3), "wh_mid": round(mid, 3), "wh_large": round(wh[names[2]], 3),
                     "stream_seconds_mid": round(mid / e["streaming_kwh_per_hour"] * 3.6, 1),
                     "co2_g_mid": round(mid * g, 3), "water_ml_mid_on_site": round(mid * e["water_ml_per_wh_on_site"], 2),
                     "per_burger_mid": round(burger_g / (mid * g))})
    rows.append({"key": "burger", "task": b["item"], "input_tokens": None, "output_tokens": None, "wh_small": None, "wh_mid": None,
                 "wh_large": None, "stream_seconds_mid": None, "co2_g_mid": round(burger_g, 0),
                 "water_ml_mid_on_site": round(b["kg"] * b["litres_withdrawn_per_kg"] * 1000, 0), "per_burger_mid": 1})
    return rows


def energy_measured():
    """docs/energy.json measured: GPU energy per grading for the open models (energy/), beside the estimates."""
    e = _load("docs", "energy.json")
    if not e or "measured" not in e:
        return []
    m = e["measured"]
    rows = []
    for r in m["rows"]:
        rows.append({"key": f"{r['model']}:{r['task']}", "model": name(r["model"]), "model_id": r["model"],
                     "task": TASKS.get(r["task"], r["task"]), **{k: v for k, v in r.items() if k not in ("model", "task")},
                     "status": m["status"], "boundary": m["boundary"], "hardware": m["hardware"]})
    return rows


def _lifecycle_task(e, tk):
    c, a, o = e["per_token_model"]["tiers"]["mid-size model (GPT-4o)"]
    op = c + a * tk["input_tokens"] / 1000 + o * tk["output_tokens"] / 1000
    lc = e["lifecycle"]
    out = {}
    for case, p in lc["cases"].items():
        en = op * (1 + p["m"]) * (1 + p["manufacturing_energy_share"])
        out[case] = {"wh": en, "g": en * p["g_co2_per_wh"] + op * p["embodied_g_per_op_wh"],
                     "ml": op * (lc["on_site_water_ml_per_wh"] + p["electricity_water_ml_per_wh"]) * (1 + p["m"]) + op * p["chip_water_ml_per_op_wh"]}
    return op, out


def lifecycle_tasks():
    """docs/energy.json lifecycle: each task's full footprint, low / central / high (docs/LIFECYCLE.md)."""
    e = _load("docs", "energy.json")
    if not e or "lifecycle" not in e:
        return []
    rows = []
    for tk in e["tasks"]:
        op, out = _lifecycle_task(e, tk)
        row = {"key": tk["task"], "task": tk["task"], "operational_wh": round(op, 3)}
        for case, v in out.items():
            row[f"wh_{case}"] = round(v["wh"], 3)
            row[f"g_{case}"] = round(v["g"], 3)
            row[f"ml_{case}"] = round(v["ml"], 2)
        rows.append(row)
    return rows


def lifecycle_compare():
    """Everyday choices against short-answer gradings (central full life-cycle case)."""
    e = _load("docs", "energy.json")
    if not e or "lifecycle" not in e:
        return []
    short = [tk for tk in e["tasks"] if tk["task"] == "short answer"][0]
    central = _lifecycle_task(e, short)[1]["central"]
    g, ml, wh = central["g"], central["ml"], central["wh"]
    rows = [{"key": "term", "item": "a teacher's term of short answers (150 students x 10 assignments)", "g_co2e": round(1500 * g, 1),
             "boundary": "full life cycle, central case (this benchmark's estimate)", "source": "docs/LIFECYCLE.md", "gradings": 1500,
             "ml_water": round(1500 * ml), "gradings_water": 1500,
             "water_boundary": "water evaporated on site, used to make the electricity and to make the chips",
             "wh": round(1500 * wh, 1), "gradings_energy": 1500,
             "energy_boundary": "running the model, a share of training and making the hardware, with data-centre overhead"}]
    for c in e["lifecycle"]["comparators"]:
        w, en, co2 = c.get("ml_water"), c.get("wh"), c.get("g_co2e")
        rows.append({"key": c["item"], "item": c["item"], "g_co2e": co2, "boundary": c.get("boundary"), "source": c["source"],
                     "gradings": round(co2 / g) if co2 else None, "ml_water": w, "gradings_water": round(w / ml) if w else None,
                     "water_boundary": c.get("water_boundary"), "wh": en, "gradings_energy": round(en / wh) if en else None,
                     "energy_boundary": c.get("energy_boundary")})
    return rows


def footprint_scale():
    e = _load("docs", "energy.json")
    if not e or "lifecycle" not in e:
        return []
    return [{"key": s["fact"], **s} for s in e["lifecycle"]["scale"]]


def setups():
    """setups/out/setups.json: whether a guard sentence or high reasoning effort removes a model's flag."""
    d = _load("setups", "out", "setups.json")
    if not d:
        return []
    rows = []
    for v in d["verdicts"]:
        rows.append({"key": f"{v['model']}:{v['condition']}", "model": name(v["model"]), "model_id": v["model"],
                     "setup": {"guard": "Guard sentence", "effort": "High reasoning effort"}[v["condition"]],
                     "gaming_default": v["gaming_worst_default"], "gaming": v["gaming_worst"], "vouched": v["vouched_worst"],
                     "blank_credited": v["blank_credited_worst"], "qwk_default": v["qwk_mean_default"], "qwk": v["qwk_mean"],
                     "verdict": v["verdict"]})
    return rows


def hosting():
    """hosting/out/hosting.json: the same open model served at 8-bit or 4-bit precision."""
    d = _load("hosting", "out", "hosting.json")
    if not d:
        return []
    comp = {(c["model"], c["task"]): c for c in d["comparisons"]}
    rows = []
    for r in d["rows"]:
        c = comp.get((r["model"], r["task"]), {})
        rows.append({"key": f"{r['model']}:{r['task']}:{r['arm']}", "model": name(r["model"]), "model_id": r["model"],
                     "task": TASKS.get(r["task"], r["task"]), "precision": {"fp8": "8-bit", "fp4": "4-bit"}[r["arm"]],
                     "qwk": r["qwk"], "injection": r["injection"], "forged": r["forged"], "vouched": r["vouched"],
                     "blank_credited": r["blank_credited"], "verdict": c.get("verdict")})
    return rows


def paraphrase():
    """paraphrase/out/paraphrase.json: marks under six rewordings of the prompt against asking again."""
    d = _load("paraphrase", "out", "paraphrase.json")
    if not d or not d.get("models"):
        return []
    rows = []
    for m, v in d["models"].items():
        tr = [r for r in d["rows"] if r["model"] == m]
        rows.append({"key": m, "model": name(m), "model_id": m,
                     "reask_changed": sum(r["retest_flip"] for r in tr) / len(tr),
                     "paraphrase_changed": sum(r["paraphrase_flip"] for r in tr) / len(tr),
                     "excess": v["excess"]["estimate"], "excess_lo": v["excess"]["ci95"][0], "excess_hi": v["excess"]["ci95"][1],
                     "qwk_spread_max": max(r["qwk_spread"] for r in tr), "verdict": v["verdict"]})
    return rows


def essays_finetune():
    """essays-finetune/out/essays-finetune.json: fine-tuned scorers against prompted models on 1,000 essays."""
    d = _load("essays-finetune", "out", "essays-finetune.json")
    if not d:
        return []
    label = {"deberta same-prompt": "DeBERTa, fine-tuned, same prompts", "deberta cross-prompt": "DeBERTa, fine-tuned, unseen prompt",
             "qwen same-prompt": "Qwen3 4B, fine-tuned, same prompts", "qwen cross-prompt": "Qwen3 4B, fine-tuned, unseen prompt"}
    rows = []
    for arm, v in d["arms"].items():
        if arm not in label:
            m, cond = arm.rsplit(" ", 1)
            label[arm] = {"claude-haiku-5.5": "Claude Haiku 5.5", "glm-5.3-flash": "GLM 5.3 Flash",
                          "claude-opus-5.5": "Claude Opus 5.5"}.get(m, m) + (", six marked examples" if cond == "anchored" else ", zero-shot")
        rows.append({"key": arm, "arm": label[arm], "qwk": v["estimate"], "qwk_lo": v["ci95"][0], "qwk_hi": v["ci95"][1], "essays": v["n"]})
    return sorted(rows, key=lambda r: -r["qwk"])


def length_partial():
    """out/length_partial.json: each model's agreement with the essay experts once length is set aside."""
    d = _load("out", "length_partial.json")
    if not d:
        return []
    return [{"key": f"{r['model']}:{r['task']}", "model": name(r["model"]), "model_id": r["model"], "task": TASKS.get(r["task"], r["task"]),
             "r": r["r"], "partial_r": r["partial_r"], "partial_lo": r["ci95"][0], "partial_hi": r["ci95"][1],
             "share_beyond_length": r["share_beyond_length"], "verdict": r["verdict"]} for r in d["rows"] if r["task"] == "asap2"]


def main(out):
    os.makedirs(out, exist_ok=True)
    for nm, fn in (("leaderboard", leaderboard), ("halo", halo), ("fairness", fairness),
                   ("feedback_checks", feedback_checks), ("drift", drift), ("floor", floor),
                   ("overall", overall), ("weights", weights), ("feedback_board", feedback_board),
                   ("speech", lambda: modality("speech", "Speech (pronunciation)", "speech")),
                   ("images", images_pooled), ("video", video), ("video_length", video_length),
                   ("maths", maths), ("pushback", pushback), ("baselines", baselines), ("agreement_flags", agreement_flags),
                   ("pushback_split", pushback_split), ("length_check", length_check), ("per_prompt", per_prompt),
                   ("multiplicity", multiplicity), ("corrections", corrections), ("energy", energy), ("models", models), ("contamination", contamination), ("energy_tasks", energy_tasks),
                   ("energy_measured", energy_measured), ("setups", setups), ("hosting", hosting), ("paraphrase", paraphrase),
                   ("essays_finetune", essays_finetune), ("length_partial", length_partial),
                   ("scoring", scoring), ("lifecycle_tasks", lifecycle_tasks), ("lifecycle_compare", lifecycle_compare), ("footprint_scale", footprint_scale)):
        rows = fn()
        json.dump(rows, open(os.path.join(out, f"{nm}.json"), "w"), indent=0)
        print(f"{nm}: {len(rows)} rows")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "public"))
