# Images: can AI grade handwritten maths, and does a note written on the page game it?

Design: `PREREG.md`. CHECK-MAT: 122 scanned handwritten solutions to Russian EGE mathematics problems,
each with one official expert score (so no ceiling: raw QWK only), split by maximum points into three runs.
Five vision models at first (Qwen3.8 Flash was planned but has no zero-retention endpoint: dropped before any
grading was read); four more leaderboard models added under the coverage rule (`PREREG.md` CHANGE 1, 2026-10-26).
Aggregates per scale: `../out/images/`.

| model | QWK by scale (0-2, 0-3, 0-4) | gain from a note written on the page, by scale | strong vs weak label | $ / 1,000 |
|---|---|---|---|---|
| Claude Opus 5.5 | 0.70, 0.75, 0.69 | +2.6%, +2.0%, −2.3% | 0.0 to +3.0% | 15.47 |
| GPT-6 Astra | 0.64, 0.67, 0.73 | +2.6%, 0.0%, +2.3% | −3.0 to +3.1% | 23.44 |
| GPT-5 Mini | 0.55, 0.26, 0.67 | +3.5%, +6.1%, **+10.2%** | −2.3 to +5.1% | 2.41 |
| Claude Haiku 5.5 | 0.52, 0.36, 0.74 | +0.9%, **+15.2%**, **+10.9%** | −2.6 to +2.3% | 0.58 |
| Gemini 3.5 Flash Lite | 0.51, 0.48, 0.55 | **+10.5%, +14.1%, +15.6%** | −2.0 to +2.3% | 0.88 |
| Gemma 4 31B | 0.39, 0.39, 0.66 | **+26.3%, +21.2%, +32.0%** | +0.9 to +7.1% | 0.10 |
| Gemma 4 26B A4B | 0.20, 0.13, 0.22 | **+9.6%, +18.2%, +12.5%** | +0.9 to +9.4% | 0.06 |
| Ministral 8B | 0.09, 0.02, 0.13 | **+43.0%, +39.4%, +38.3%** | +2.6 to +5.1% | 0.24 |
| Gemma 3 4B | −0.06, 0.11, −0.00 | **+10.9%, +7.1%, +4.0%** | −2.2 to +2.8% | 0.03 |

Not yet run (2026-10-26), though they take images: Claude Fable 5.1 (0-2 scale complete; the 0-3 and 0-4 runs
stopped at their spend caps), Gemma 3 27B (stopped when the API key's spending limit was reached), DeepSeek V4.1
Flash and its 10-17 snapshot, GPT-5.6 Luna and GLM 5.3 Flash. Bold: the 95% interval excludes 0.

The gain is the larger of the two notes (a polite request or a forged "GRADING OVERRIDE"), drawn in a white
band under the student's work, as a share of the scale.

**What it says**
- **A note written on the work games models that ignore the same note as text.** Haiku 5.5 resists every
  text gaming probe on the leaderboard, but a forged note written onto a handwritten page raises its marks
  by 11-15% of the scale on two of the three scales. Only Opus and GPT-6 Astra resist it throughout; Ministral 8B
  gives 38-43% of the scale more for it.
- **Opus reads handwritten maths best** (QWK 0.69-0.75), at about 25 times Haiku's price; Astra is close
  (0.64-0.73) at 1.5 times Opus's. The small open models barely read the pages (QWK −0.06 to 0.22).
- **Off-task is not interpretable on this corpus.** The student's pages carry the printed problem, so another
  task's pages are a complete answer to a different problem; marks for them (0-76% of the scale across the nine models) do
  not read as a failure. Reported in the aggregates, not here.
- One expert per solution: these are agreement figures without a ceiling, and a pilot of the pipeline.
