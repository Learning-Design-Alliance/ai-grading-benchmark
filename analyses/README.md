# Standard automated-scoring checks and non-LLM baselines (2026-10-25)

These were added after the second literature review. Sources are listed in `docs/LITERATURE.md`. Both use only
data already held, so no new model calls were made.

## Agreement flags, pushback split, length (`standard_checks.py`, output `../out/standard_checks.json`)

**Agreement flags** follow Williamson, Xi and Breyer (2012):
- QWK at least 0.70;
- a drop of at most 0.10 from human-human agreement;
- |SMD| at most 0.15.

A flag reads INDETERMINATE when its 95% bootstrap interval spans the threshold.
- **No model passes all three on any task.**
- **Systematic harshness is the common failure.** On short answers and code, almost every model marks below
  the raters, with an SMD of about −0.2 to −0.8. That is the measurable version of "AI feedback feels harsh".
- **Code.** Fable, Opus, Astra, Haiku and GPT-5 Mini pass QWK and degradation. All but Fable fail SMD (too
  low); Fable's is indeterminate.
- **Essays.** With 100 cases most flags are indeterminate. Fable (SMD −0.04) and Opus (−0.02) are the least
  biased.
- **Short answers.** QWK is 0.38-0.67 against a human ceiling of about 0.56, so every model is near or above
  the raters. The 0.70 bar is unreachable for anyone, and degradation passes for most.

**Pushback split** follows SycEval (Fanous et al. 2025). A push that raises a mark set below the experts' mean
is a correction. One that raises a mark already at or above it is sycophancy.
- Haiku's raises are 13 of 15 corrections, and DeepSeek's 13 of 13.
- Gemini 3.5 Flash Lite's are 6 of 9 regressive.
- On answers the model had not under-marked, the push-minus-recheck effect is still above 0 for most models:
  Ministral +40% of the scale, Llama +30%, Gemma 3 27B +19%.
- Astra (+1%) and Gemma 3 4B (−1%) do not give way.

**Length beyond the human mark** is the standardised coefficient of log length in a regression of the mark
on the human mark plus log length. The raters' own reference is +0.05 on short answers and +0.07 on code.
- **Essays.** Most models reward length beyond what the raters gave. Ministral (+0.27), Fable (+0.24),
  Gemini Flash Lite (+0.23), Gemma 3 27B (+0.22) and DeepSeek (+0.19) have intervals above 0.
- **Short answers.** Most models mark longer answers down, beyond the raters: Haiku −0.21, Fable −0.18,
  Opus −0.15.

## Non-LLM baselines (`../baselines/baselines.py`, output `../out/baselines.json`)

The baselines were pre-registered before scoring. Each was trained on the corpus cases outside the canonical
100 and scored on exactly the leaderboard battery.

| task | baseline | QWK | share of ceiling | credits blank or junk | gaming |
|---|---|---|---|---|---|
| Essays | length only | 0.64 | 85% of published κ | no | +2.6% |
| Essays | TF-IDF ridge | 0.73 | 99% of published κ | no | +2.2% |
| Short answers | TF-IDF ridge (question + answer) | 0.41 | 72% | yes (all) | +0.8% |
| Short answers | similarity to the reference | 0.16 | 28% | yes | −3.6% |
| Short answers | length only | 0.01 | 2% | yes | +0.4% |
| Code (29 training cases) | all three | ≈ 0 | ≈ 0 | yes | ≈ 0 |

**Reading.**
- A classic trained essay scorer matches the best language models on agreement (Fable 0.71, Opus 0.70).
  Length alone beats 9 of 17 models.
- The baselines are hard to game, never move with the learner label, and never give way to pushback. All are
  deterministic.
- But they credit blank answers on short answers and code, because a regression never drops to its floor.
- They need hundreds of marked examples per item, and give no feedback or reasons.
- The case for an LLM grader is therefore not agreement on essays. It is no training data, new items,
  feedback, and tasks like code and maths working where these baselines cannot follow the reasoning.
