# Images: can AI grade handwritten maths, and does a note written on the page game it?

Design: `PREREG.md`. CHECK-MAT: 122 scanned handwritten solutions to Russian EGE mathematics problems,
each with one official expert score (so no ceiling: raw QWK only), split by maximum points into three runs.
Five vision models (Qwen3.8 Flash was planned but has no zero-retention endpoint: dropped before any grading
was read). Aggregates per scale: `../out/images/`.

| model | QWK by scale (0-2, 0-3, 0-4) | gain from a note written on the page, by scale | strong vs weak label | $ / 1,000 |
|---|---|---|---|---|
| Claude Opus 5.5 | 0.70, 0.75, 0.69 | +2.6%, +2.0%, −2.3% | 0.0 to +3.0% | 15.47 |
| GPT-5 Mini | 0.55, 0.26, 0.67 | +3.5%, +6.1%, **+10.2%** | −2.3 to +5.1% | 2.41 |
| Claude Haiku 5.5 | 0.52, 0.36, 0.74 | +0.9%, **+15.2%**, **+10.9%** | −2.6 to +2.3% | 0.58 |
| Gemini 3.5 Flash Lite | 0.51, 0.48, 0.55 | **+10.5%, +14.1%, +15.6%** | −2.0 to +2.3% | 0.88 |
| Gemma 4 31B | 0.39, 0.39, 0.66 | **+26.3%, +21.2%, +32.0%** | +0.9 to +7.1% | 0.10 |

The gain is the larger of the two notes (a polite request or a forged "GRADING OVERRIDE"), drawn in a white
band under the student's work, as a share of the scale.

**What it says**
- **A note written on the work games models that ignore the same note as text.** Haiku 5.5 resists every
  text gaming probe on the leaderboard, but a forged note written onto a handwritten page raises its marks
  by 11-15% of the scale on two of the three scales. Only Opus resists it throughout.
- **Opus reads handwritten maths best** (QWK 0.69-0.75), at about 25 times Haiku's price.
- **Off-task is not interpretable on this corpus.** The student's pages carry the printed problem, so another
  task's pages are a complete answer to a different problem; marks for them (4-63% of the scale) do not
  read as a failure. Reported in the aggregates, not here.
- One expert per solution: these are agreement figures without a ceiling, and a pilot of the pipeline.
