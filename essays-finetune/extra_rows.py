#!/usr/bin/env python3
"""Write out/finetune_extra.json: the essay study's fine-tuned language models as extra rows for the scoring board.

The board's reference rows already carry DeBERTa-v3-base on every task (out/baselines.json), so the study's
retrained DeBERTa is left out here to avoid listing it twice; the two fine-tuned language models (Qwen3 4B and
Gemma 4 26B A4B, LoRA) are added.

    python3 essays-finetune/extra_rows.py
    python3 leaderboard.py scoring out/leaderboard.json --extra out/baselines.json out/finetune_extra.json
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = []
for r in json.load(open(os.path.join(ROOT, "essays-finetune", "out", "board_rows.json")))["rows"]:
    if "DeBERTa" in r["model"]:
        continue
    rows.append(r)  # leaderboard.py scoring puts n_train under the row's task
json.dump({"source": "essays-finetune/out/board_rows.json (DeBERTa omitted: already in out/baselines.json)", "rows": rows},
          open(os.path.join(ROOT, "out", "finetune_extra.json"), "w"), indent=1)
print(f"{len(rows)} rows: " + ", ".join(r["model"] for r in rows))
