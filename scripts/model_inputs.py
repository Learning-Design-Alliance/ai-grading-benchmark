#!/usr/bin/env python3
"""Record what each model can take as input (text, image, video, audio), so the site can say why a model has no
result on a task: it cannot take the input, or it has not been run yet.

Source: OpenRouter's public model list (https://openrouter.ai/api/v1/models, `architecture.input_modalities`),
read on the date stored in the output. Covers every board model (docs/models.json) and every model run on a
media task (out/speech, out/images, out/public/video.json). A model OpenRouter does not list, or lists without
modalities, takes its entry from OVERRIDES with the reason.

    python3 scripts/model_inputs.py            # writes docs/model-inputs.json
"""

import datetime
import glob
import json
import os
import re
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "https://openrouter.ai/api/v1/models"
#: Models served outside OpenRouter, or listed there without modalities.
OVERRIDES = {
    "allenai/olmo-3.1-32b-instruct": (["text"], "run on the maintainers' own GPU; a text-only model per its card"),
}


#: Release dates for models OpenRouter does not list, with their source.
DATE_OVERRIDES = {"allenai/olmo-3.1-32b-instruct": "2025-12-01"}  # Olmo 3 technical report, arXiv 2512.13961 (December 2025)


def model_ids():
    ids = {m["model"] for m in json.load(open(os.path.join(ROOT, "docs", "models.json")))["models"]}
    for p in glob.glob(os.path.join(ROOT, "out", "speech", "*.json")) + glob.glob(os.path.join(ROOT, "out", "images", "*.json")):
        stem = re.sub(r"^(speech|image\d*)-", "", os.path.basename(p)[:-5])
        ids.add(stem.replace("_", "/", 1))
    vp = os.path.join(ROOT, "out", "public", "video.json")
    if os.path.exists(vp):
        for r in json.load(open(vp)):
            stem = re.sub(r"^video(16f)?-", "", r["key"])
            ids.add(stem.replace("_", "/", 1))
    return sorted(i for i in ids if "/" in i)  # drops reference rows such as the human raters


def main():
    listed = {m["id"]: m for m in json.load(urllib.request.urlopen(URL, timeout=60))["data"]}
    out = {"source": URL, "field": "architecture.input_modalities", "read": datetime.date.today().isoformat(),
           "note": "'file' (document upload) is dropped: no task here sends one.", "models": {}}
    for mid in model_ids():
        if mid in OVERRIDES:
            inputs, why = OVERRIDES[mid]
            out["models"][mid] = {"inputs": inputs, "from": "override", "why": why}
            continue
        mods = ((listed.get(mid) or {}).get("architecture") or {}).get("input_modalities")
        if mods is None:
            out["models"][mid] = {"inputs": None, "from": "not listed"}
            continue
        out["models"][mid] = {"inputs": [m for m in ("text", "image", "video", "audio") if m in mods], "from": "openrouter"}
    json.dump(out, open(os.path.join(ROOT, "docs", "model-inputs.json"), "w"), indent=1)
    # Release dates for the timeline: when OpenRouter listed each model (its `created` field), for the board, the
    # media models and the older releases in the lineage runs.
    lineage = [json.load(open(p))["config"]["model"] for p in glob.glob(os.path.join(ROOT, "out", "lineage-2026-10-23", "*.json"))]
    dates = {mid: datetime.date.fromtimestamp(listed[mid]["created"]).isoformat()
             for mid in sorted(set(model_ids()) | set(lineage)) if mid in listed and listed[mid].get("created")}
    dates.update(DATE_OVERRIDES)
    json.dump({"source": URL, "field": "created (when OpenRouter listed the model; a stand-in for the vendor's release date)",
               "read": out["read"], "models": dates}, open(os.path.join(ROOT, "docs", "model-dates.json"), "w"), indent=1)
    for k, v in out["models"].items():
        print(f"{k:45s} {v['inputs']} ({v['from']})")


if __name__ == "__main__":
    main()
