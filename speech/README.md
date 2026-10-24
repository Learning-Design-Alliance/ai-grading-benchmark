# Speech: can AI grade pronunciation from a recording?

Design: `PREREG.md` (written before any full run). speechocean762: 100 English sentences read aloud by
Mandarin-L1 children and adults, each scored for pronunciation accuracy (0-10) by five experts; the experts'
mean pairwise QWK is the ceiling (0.614). Six audio models with zero-retention endpoints. Aggregates:
`../out/speech/`.

| model | share of expert ceiling | same recording twice (QWK) | credits silence | credits a tone | another speaker's sentence | strong vs weak label | noise 10 dB | telephone band | $ / 1,000 |
|---|---|---|---|---|---|---|---|---|---|
| Gemini 3.8 Flash | 106% | 0.90 | **100%** | **97%** | 1% | +8.6% | −0.8% | −0.7% | 1.16 |
| Perceptron mk1.5 | 96% | 0.97 | **97%** | 7% | 14% | **+22%** | −8.6% | −2.4% | 0.10 |
| Gemini 4 Argon | 83% | 0.93 | **100%** | 8% | 3% | +10% | −0.3% | +0.8% | — |
| MiMo v2.6 Flash | 76% | 0.74 | **90%** | 41% | 22% | +11% | −0.6% | −0.4% | 0.05 |
| Voxtral Small 24B | 39% | 0.89 | **100%** | **100%** | **71%** | **+36%** | 0.0% | −0.4% | 0.38 |
| Muse Spark Open | 38% | 0.41 | 5% | 0% | 3% | −0.3% | +0.6% | −7.6% | 5.60 |

Effects are marks as a percentage of the 0-10 scale. Gemini 4 Argon left 19 of 760 gradings without a mark
and Muse 16; both reported no cost.

**What it says**
- **Every capable audio model hallucinates.** Five of six give marks to a silent recording, four of them to
  90-100% of silences. Gemini 3.8 Flash, the most accurate, gives 10/10 to silence and to a plain tone and
  describes "accurate pronunciation, natural rhythm". The one model that does not (Muse Spark) is barely
  above chance and inconsistent. An audio grader must be checked for this before it is trusted with a
  recording that might be empty, cut off or the wrong file.
- **When the recording carries little, the label carries a lot.** Being told the learner is strong raises
  marks by 9-36% of the scale, far more than on text (where most models move under 5%). Voxtral scores
  another speaker's different sentence at 71% of the scale: it marks the description, not the recording.
- **Recording quality matters for one model.** Perceptron marks noisy audio 8.6% lower; the others hold.
  Accent is not tested as a nuisance here: every speaker is Mandarin-L1, and pronunciation scoring is meant
  to respond to accent.
- **The best grader reaches the experts.** Gemini 3.8 Flash agrees with them as well as they agree with
  each other (106%), and Perceptron nearly does (96%) at a twelfth of the price.
