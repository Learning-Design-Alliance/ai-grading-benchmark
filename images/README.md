# Images: can AI grade handwritten math, and does a note written on the page game it?

Design: `PREREG.md`. CHECK-MAT: 122 scanned handwritten solutions to Russian EGE mathematics problems,
each with one official expert score (so no ceiling: raw QWK only), split by maximum points into three runs.
Five vision models at first (Qwen3.8 Flash was planned but has no zero-retention endpoint: dropped before any
grading was read); the other ten leaderboard models that take images added under the coverage rule (`PREREG.md` CHANGE 1, 2026-10-26).
Aggregates per scale: `../out/images/`.

| model | QWK by scale (0-2, 0-3, 0-4) | gain from a note written on the page, by scale | strong vs weak label | $ / 1,000 |
|---|---|---|---|---|
| Claude Opus 5.5 | 0.70, 0.75, 0.69 | +2.6%, +2.0%, −2.3% | 0.0 to +3.0% | 15.47 |
| Claude Fable 5.1¹ | 0.51, 0.73, 0.85 | −0.9%, +3.0%, +0.8% | +2.0 to +2.6% | 45.73 |
| GPT-6 Astra | 0.64, 0.67, 0.73 | +2.6%, 0.0%, +2.3% | −3.0 to +3.1% | 23.44 |
| DeepSeek V4.1 Flash (Oct 17 snapshot) | 0.61, 0.51, 0.71 | **+13.4%, +33.3%, +25.9%** | +3.6 to +6.6% | 1.15 |
| GLM 5.3 Flash² | 0.50, 0.53, 0.72 | **+11.8%, +40.0%, +31.8%** | 0.0 to +15.6% | 1.14 |
| GPT-5 Mini | 0.55, 0.26, 0.67 | +3.5%, +6.1%, **+10.2%** | −2.3 to +5.1% | 2.41 |
| Claude Haiku 5.5 | 0.52, 0.36, 0.74 | +0.9%, **+15.2%**, **+10.9%** | −2.6 to +2.3% | 0.58 |
| Gemini 3.5 Flash Lite | 0.51, 0.48, 0.55 | **+10.5%, +14.1%, +15.6%** | −2.0 to +2.3% | 0.88 |
| DeepSeek V4.1 Flash | 0.47, 0.51, 0.66 | **+12.5%, +42.7%, +35.9%** | −2.7 to +8.6% | 1.35 |
| GPT-5.6 Luna | 0.50, 0.42, 0.59 | **+18.4%, +33.3%, +31.2%** | 0.0 to +3.9% | 0.99 |
| Gemma 4 31B | 0.39, 0.39, 0.66 | **+26.3%, +21.2%, +32.0%** | +0.9 to +7.1% | 0.10 |
| Gemma 4 26B A4B | 0.20, 0.13, 0.22 | **+9.6%, +18.2%, +12.5%** | +0.9 to +9.4% | 0.06 |
| Gemma 3 27B | 0.06, −0.04, 0.26 | **+12.3%**, +5.1%, **+10.9%** | +2.6 to +5.1% | 0.07 |
| Ministral 8B | 0.09, 0.02, 0.13 | **+43.0%, +39.4%, +38.3%** | +2.6 to +5.1% | 0.24 |
| Gemma 3 4B | −0.06, 0.11, −0.00 | **+10.9%, +7.1%, +4.0%** | −2.2 to +2.8% | 0.03 |

Bold: the 95% interval excludes 0. Every leaderboard model that takes images has now run (2026-10-27).
¹ Fable has no zero-retention route: it ran through the maintainers' own Anthropic key under 30-day safety
retention (public corpus, no student identities), as on the leaderboard.
² GLM 5.3 Flash gave no readable mark on 17 of 399, 68 of 231 and 50 of 224 gradings (0-2, 0-3, 0-4), so its
agreement rests on 56, 20 and 24 solutions.

The gain is the larger of the two notes (a polite request or a forged "GRADING OVERRIDE"), drawn in a white
band under the student's work, as a share of the scale.

**What it says**
- **A note written on the work games models that ignore the same note as text.** Haiku 5.5 resists every
  text gaming probe on the leaderboard, but a forged note written onto a handwritten page raises its marks
  by 11-15% of the scale on two of the three scales. Only Opus, GPT-6 Astra and Fable resist it throughout. Twelve
  of fifteen models are raised by it on at least one scale, by up to 43% of the scale (Ministral 8B; DeepSeek
  V4.1 Flash and GLM 5.3 Flash 40-43% on the 0-3 scale).
- **Opus reads handwritten math most consistently** (QWK 0.69-0.75), at about 25 times Haiku's price. Fable
  ranges more widely (0.51-0.85, the best on the 0-4 scale) at three times Opus's price; Astra is close to Opus
  (0.64-0.73) at 1.5 times its price. The small open models barely read the pages (QWK −0.06 to 0.26).
- **Off-task is not interpretable on this corpus.** The student's pages carry the printed problem, so another
  task's pages are a complete answer to a different problem; marks for them (0-76% of the scale across the fifteen models) do
  not read as a failure. Reported in the aggregates, not here.
- One expert per solution: these are agreement figures without a ceiling, and a pilot of the pipeline.
