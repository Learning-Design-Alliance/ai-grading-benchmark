# Video task: rating a recorded performance (LASANA)

The design is pre-registered in `PREREG.md`, the statistics in `analyse.py`, and the length study in
`LENGTH.md`.

**Task.** 100 recordings from LASANA's test split, 25 for each of four laparoscopic box-trainer tasks. Each
was rated by three raters on four GOALS-style aspects summed to a total of 4-20. Models were sent either the
video itself (480 × 270, 2 frames a second) or, for models without video input, 16 evenly spaced frames.

**Why plain agreement is not enough here.** A recording's length predicts the raters' mean score (Spearman
0.46-0.96 by task), and the prompt gives the length, as the raters knew it. A planted grader that only times
the recording reaches QWK 0.57, the raters' own agreement. So the pre-registered measure is **agreement
beyond length**: the partial Spearman correlation of the model's mark with the raters' mean, controlling for
length, within task. A model WATCHES THE RECORDING if its 95% interval lies above 0. The raters reach 0.58
on this measure, one against the others. Spend was $113.84, at zero data retention.

| grader | sees | beyond length [95% interval] | QWK | prompt alone | credits black screen | credits frozen frame | note on screen, % of scale | strong vs weak label, % of scale | low resolution, % of scale | retest QWK | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Raters, one against the others | video | 0.58 | 0.57 | | | | | | | | reference |
| Gemini 4 Argon | video | +0.46 [+0.21, +0.63] | 0.53 | 0.27 | 53% | 3% | −6.3 | +7.4 | −0.9 | 0.88 | WATCHES |
| Gemini 3.8 Flash | video | +0.33 [+0.06, +0.54] | 0.29 | 0.29 | 100% | 100% | +7.1 | +11.1 | +0.2 | 0.71 | WATCHES |
| Gemini 3.8 Flash | 16 frames | +0.25 [+0.04, +0.44] | 0.13 | 0.22 | 100% | 100% | +7.8 | +10.4 | +0.4 | 0.71 | WATCHES |
| GPT-5 Mini | 16 frames | +0.14 [−0.10, +0.38] | −0.03 | −0.01 | 0% | 70% | +27.0 | +4.0 | +2.2 | 0.77 | not shown |
| Gemini 3.5 Flash Lite | video | +0.09 [−0.12, +0.31] | 0.01 | 0.01 | 80% | 53% | +37.4 | +17.0 | −8.4 | 0.88 | not shown |
| Claude Opus 5.5 | 16 frames | +0.08 [−0.12, +0.29] | 0.21 | declined | 0% (declined all) | 13% | +1.6 | +7.6 | +4.8 | 0.74 | not shown |
| Perceptron mk1.5 | video | +0.08 [−0.14, +0.30] | −0.01 | 0.01 | 0% | 0% | +29.3 | +16.9 | −3.2 | 0.83 | not shown |
| Claude Haiku 5.5 | 16 frames | +0.04 [−0.17, +0.23] | 0.04 | declined | 3% | 70% | +7.9 | +6.8 | +5.8 | 0.52 | not shown |
| MiMo v2.6 Flash | video | −0.04 [−0.25, +0.17] | 0.13 | 0.06 | 97% | 90% | +37.2 | +25.3 | +5.9 | 0.52 | not shown |
| Qwen3.8 27B | video | −0.09 [−0.30, +0.16] | 0.13 | −0.08 | 0% | 27% | +19.8 | +11.8 | −3.6 | 0.59 | not shown |
| Nova 2 Lite | video | — | — | −0.07 | 23% | 0% | — | — | — | — | did not rate |

"Not shown" is the pre-registered ADDS NOTHING TO THE STOPWATCH: the interval reaches 0. It does not
show that the model ignores the footage. Every such interval still allows agreement beyond length of 0.16-0.38,
up to two-thirds of the raters' 0.58. The data cannot tell those models apart from a stopwatch.

The black-screen and frozen-frame columns are the share of all such gradings given more than the minimum, so
a model that declined to rate counts as not crediting. The gaming column takes the larger of the two notes;
positive means the note raised the mark.

**Reading.**
- **Three of eleven runs watch the recording**: Gemini 4 Argon, and Gemini 3.8 Flash from both video and 16
  frames. Argon comes closest to the raters, at four-fifths of their agreement beyond length. For the other
  models, 100 recordings cannot separate them from a stopwatch. Their intervals run from about 0 to
  0.16-0.38, so a modest ability to watch is not ruled out.
- **Plain agreement misleads.**
  - Gemini 3.8 Flash's QWK is 0.29 with the video and 0.29 from the prompt alone, which carries the length.
  - Claude Opus reaches QWK 0.21 from frames with no agreement beyond length.
  - Agreement beyond length is the number to read for any timed performance.
- **Hallucination is the norm.**
  - Gemini 3.8 Flash rates every black screen and every frozen frame above the minimum, though it watches
    real footage.
  - Argon credits half the black screens, presumably rating from the length it is told.
  - Only Claude Opus, Perceptron and Qwen never credit a black screen. Opus declines to rate it and says
    why.
- **Video against frames, the same model:** Gemini 3.8 Flash scores a little lower from 16 frames (+0.25
  against +0.33), with overlapping intervals. Frames lose little for this model; the frames-only models'
  weakness is the models, not only the input.
- **Gaming and labels.**
  - A note shown on screen raises the mark by 27-37% of the scale for GPT-5 Mini, Gemini Flash Lite,
    Perceptron and MiMo.
  - Argon marks it down instead (−6.3%).
  - Every model gives a strong-labelled trainee more than a weak-labelled one, by 4-25% of the scale.
- **Input that never arrived.**
  - Nova 2 Lite described the video instead of rating it on nearly every grading.
  - MiMo was charged about 2,500 input tokens a recording, so it likely saw only a few frames.
  - Qwen ran out of its 4,096-token budget on 130 of 1,060 gradings.

**Limits.**
- Laparoscopic training is far from classroom work.
- The raters' raw-scale agreement is modest (0.57), and they differed in severity.
- One prompt; one run per model.
- Blank-video probes ran on 30 recordings.
- Recording-quality probes are reported, not ranked, until a floor with degraded video exists.

Per-run reports are in `../out/video/`, the extras in `../out/video/extras.json`.
