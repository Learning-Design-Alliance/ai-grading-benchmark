# Baselines: what a grader that is not a language model does on the same cases

The design is pre-registered in `baselines.py`'s docstring. CHANGE 1 added a sentence-encoder baseline.
CHANGE 2 added a fine-tuned DeBERTa-v3-base, with one implementation fix made before any prediction: the
checkpoint loaded in fp16 and training went to NaN. Every baseline is trained on the corpus's cases outside the canonical 100
and scored on those 100 under the leaderboard's probes, like a submission. Baselines sit beside the board,
never in it.

| task | baseline | QWK [95%] | share of the human ceiling | gaming | blank answers credited | training cases |
|---|---|---|---|---|---|---|
| short answers | length | 0.01 | 2% | 0% | all | 1,627 |
| short answers | TF-IDF + ridge | 0.41 [0.19-0.62] | 72% | +1% | all | 1,627 |
| short answers | reference similarity | 0.16 | 28% | -4% | all | 1,627 |
| short answers | MiniLM + ridge | 0.32 [0.20-0.43] | 56% | +1% | all | 1,627 |
| short answers | **DeBERTa fine-tuned** | **0.36 [0.21-0.50]** | **62%** | **-10%** | **all** | 1,627 |
| essays | length | 0.64 | 85% of published | +3% | none | 24,628 |
| essays | TF-IDF + ridge | 0.73 [0.62-0.81] | 99% of published | +2% | none | 24,628 |
| essays | MiniLM + ridge | 0.48 [0.33-0.60] | 64% of published | 0% | 80% | 24,628 |
| essays | **DeBERTa fine-tuned** | **0.81 [0.73-0.87]** | **109% of published** | **+1%** | **14%** | 24,628 |
| code | every baseline, DeBERTa included | 0.00-0.05 | 0-6% | 0-2% | all | 29 |

**Against what was expected** (written before training):
- **Essays: as expected.** DeBERTa is above TF-IDF and MiniLM, though its interval overlaps TF-IDF's. At 0.81 it
  is above every language model on the board: the best are Gemma 4 26B at 0.73 and Claude Fable 5.1 at 0.71,
  graded with the default prompt and no training. That is not a like-for-like contest. DeBERTa learned from
  24,628 essays written to the same seven prompts and marked to the same rubric, which a school adopting a
  grader rarely has. A quarter of the training essays were cut at 512 word pieces.
- **Short answers: not as expected.** DeBERTa is between MiniLM and TF-IDF, not above TF-IDF. The board's
  language models all do better (QWK 0.38-0.68) with no training at all. 1,627 answers spread over about 80
  questions is about 20 per question, too few for a fine-tuned reader.
- **Code: as expected, weak.** 29 training cases.
- **Blank answers: credited, as expected**, on short answers and code, since a regression has no floor.
- **Gaming: as expected, no gain.** The polite request and the forged override do not raise DeBERTa's mark.
  On short answers they lower it by 10% of the scale.

**Reading.** A cheap reader trained on enough marked work from the same tasks can match or beat a prompted
language model on agreement, and it cannot be talked into a mark. Where the training data is thin, as for
short answers and code here, it falls well behind. And on short answers and code, like the other baselines,
it gives credit to an empty answer, so it needs a blank-answer rule in front of it.

Trained on one rented A100 (`gpu/pod.py`), in under an hour for all three tasks, on public corpora only.

    python3 baselines/baselines.py --cases-dir <dir> --out out/baselines.json [--kinds deberta-ft]

Output: `out/baselines.json` (the report reads it as `out/public/baselines.json`).
