# Do AI graders mark essays by students identified with a disability lower than the human rater?

**Asked:** the benchmark's first ASAP 2.0 run had a signal for Gemini 3.5 Flash Lite. On 27 essays, it
marked essays by students identified with a disability lower than the human rater did, relative to
other students: -0.60 with the default prompt. Haiku 5.5 and Qwen3 showed nothing
on the same essays. Does that replicate on new essays, and is it Gemini's?

**Design:** `gap.py`'s docstring, pre-registered on 2026-10-23 before any call. Two changes were made
before any real grading was read:
- CHANGE 1: a smaller simulation budget for the floor.
- CHANGE 2: 1,500 essays per group. At 500 per group the floor failed, 55.5% against 90%, because
  the essays sit near the bottom of the scale and a downward shift is clipped.

The final floor passes: 97.5% of simulations detect a planted -0.30, and none flag a planted 0 (`out/floor.json`).

The sample is 3,000 new ASAP 2.0 essays, excluding the first run's 200: 1,500 by students identified
with a disability and 1,500 not, matched exactly on the human mark. The grader's bunching of marks
toward the middle therefore cannot make a gap.

## Came back (2026-10-23)

| grader | gap, identified minus not (machine marks; human marks identical) | verdict |
|---|---|---|
| Gemini 3.5 Flash Lite, default prompt (primary) | -0.429 [-0.506, -0.349] | GAP REPLICATES |
| Haiku 5.5, default prompt | -0.166 [-0.210, -0.123] | GAP REPLICATES |
| Qwen3 235B (DeepInfra), default prompt | -0.212 [-0.276, -0.148] | GAP REPLICATES |

No grading failed in any of the runs. (A product-prompt arm, run with these, is kept in the private
research repository and is not part of this benchmark.)

**Pre-registered reading: SHARED GAP.** Gemini's gap replicates, but both comparators show it as well.
So the gap is not one model's. It belongs either to the human marks, which were relatively generous
to these essays, or to something in the essays that every model penalises. Gemini's gap is
about twice the comparators'. That is a model-specific excess on top of a shared gap; this design
did not pre-register it as a test.

The first run's "Haiku and Qwen show nothing" was a power problem at n = 27, not an absence.

**Exploratory, not pre-registered:** median length differs little between the groups at matched
marks (mark 1: 202 against 226 words; marks 2-4 within about 20 words in either direction). The
rate of a lowercase " i " barely differs (0.20 against 0.17 per 100 words). Neither obviously
explains the gap.

**Correction (2026-10-23, after the result):** this README first called ASAP 2.0's mark a single
rater's. It is not. The data paper (Crossley et al. 2025, Assessing Writing 65, 100954, section 3;
`data/data-sources.json`, `asap2`) describes double-blind expert rating with every essay adjudicated
(pre-adjudication weighted kappa .745). Only the adjudicated mark is released. "One rater was
generous" is therefore the less likely reading: two blind raters and an adjudicator would all have had
to lean the same way. The pre-registered verdict, SHARED GAP, stands, because the design cannot
separate a bias shared by the human panel from one shared by the models.

**What would settle it:** the two pre-adjudication ratings per essay (released by the authors, or
requested from them), or new human ratings on a sample. A gap the individual raters also show
belongs to the human marks; one they do not show belongs to the models.

The fairness section of the benchmark should say this about any corpus that releases one mark per
essay: a residual gap measures the grader against that mark, and here every grader shared the gap.

`out/result.json` holds the aggregates. No essay text or per-essay mark is committed.

## Added under the coverage rule (`gap.py` CHANGE 3, 2026-10-26, after the result above was read)

Every other leaderboard model with a hosted zero-retention route, default prompt, each with its leaderboard
settings, on the same 3,000 matched essays. GPT-6 Astra and Claude Fable 5.1 were added on 2026-10-27 by the
maintainer's decision (CHANGE 4; Fable through the maintainers' own Anthropic key under 30-day safety retention, as
on the leaderboard). Not run: Claude Opus 5.5 (not approved) and Olmo 3.1 32B (no hosted route).

| grader | gap, identified minus not (machine marks; human marks identical) | verdict |
|---|---|---|
| GLM 5.3 Flash | −0.393 [−0.451, −0.334] | GAP REPLICATES |
| GLM 5.3 | −0.367 [−0.422, −0.310] | GAP REPLICATES |
| Gemma 4 26B A4B | −0.347 [−0.410, −0.283] | GAP REPLICATES |
| DeepSeek V4.1 Flash | −0.333 [−0.397, −0.268] | GAP REPLICATES |
| Phi-4 | −0.279 [−0.340, −0.217] | GAP REPLICATES |
| DeepSeek V4 Pro | −0.275 [−0.336, −0.211] | GAP REPLICATES |
| DeepSeek V4.1 Flash (Oct 17 snapshot) | −0.270 [−0.330, −0.211] | GAP REPLICATES |
| Claude Fable 5.1 | −0.247 [−0.298, −0.196] | GAP REPLICATES |
| Gemma 3 27B | −0.247 [−0.301, −0.192] | GAP REPLICATES |
| Gemma 4 31B | −0.235 [−0.291, −0.178] | GAP REPLICATES |
| GPT-OSS 20B | −0.232 [−0.285, −0.177] | GAP REPLICATES |
| GPT-6 Astra | −0.217 [−0.268, −0.162] | GAP REPLICATES |
| Llama 3.2 3B | −0.213 [−0.288, −0.140] | GAP REPLICATES |
| GPT-5.6 Luna | −0.202 [−0.260, −0.143] | GAP REPLICATES |
| GPT-5 Mini | −0.172 [−0.223, −0.120] | GAP REPLICATES |
| Ministral 8B | −0.124 [−0.167, −0.082] | NO GAP OF 0.2 OR MORE |
| Gemma 3 4B | −0.086 [−0.141, −0.029] | NO GAP OF 0.2 OR MORE |

- **The gap is shared by nearly every model.** 15 of the 17 added graders read GAP REPLICATES, from −0.17
  (GPT-5 Mini) to −0.39 (GLM 5.3 Flash), so 18 of the 20 graders in all. The two that read NO GAP OF 0.2 OR MORE (Gemma
  3 4B, −0.09, and Ministral 8B, −0.12) still mark the identified group lower: their intervals lie below 0, inside
  the ±0.20 band.
- The SHARED GAP reading stands. Gemini 3.5 Flash Lite's −0.43 is still the largest.
