# Does a longer video hide an error?

The design, verdicts and floor are pre-registered in `padding.py`'s docstring.

**Design.** All 205 recordings in LASANA's test split, each asked one yes-or-no question: did this
recording's labelled error happen? The errors are a dropped object, gauze off a clip, the inner balloon
opened, and a dropped needle; 78 recordings have the error. Each recording is asked about twice:
- as recorded;
- joined to three recordings of the same task in which that error did not happen, so four times as long.

The error and its label are the same at both lengths; only the length changes. The floor passed before any
call: 84% of planted drops were detected, with 2% false detections. The spend was $51.25 for 2,050
gradings, at zero data retention.

| model | balanced accuracy, as recorded → 4x | change [95% interval] | errors caught | clean videos cleared | no answer | verdict (pre-registered NO DETECTABLE EFFECT) |
|---|---|---|---|---|---|---|
| Gemini 4 Argon | 0.70 → 0.71 | +0.01 [−0.06, +0.09] | 46% → 68% (+22) | 94% → 75% (−19) | 0 | not detected; a loss up to 0.06 not ruled out |
| Gemini 3.8 Flash | 0.69 → 0.63 | −0.06 [−0.13, +0.00] | 66% → 83% (+17) | 73% → 43% (−30) | 10 | not detected; a loss up to 0.13 not ruled out |
| Qwen3.8 27B | 0.57 → 0.52 | −0.04 [−0.13, +0.05] | 58% → 61% | 55% → 44% (−11) | 153 | not detected; a loss up to 0.13 not ruled out |
| Gemini 3.5 Flash Lite | 0.56 → 0.53 | −0.02 [−0.10, +0.05] | 25% → 31% | 87% → 75% (−11) | 3 | not detected; a loss up to 0.10 not ruled out |
| Perceptron mk1.5 | 0.51 → 0.51 | −0.00 [−0.05, +0.04] | 14% → 4% (−10) | 88% → 98% (+10) | 0 | not detected; a loss up to 0.05 not ruled out |

Changes in brackets are those whose 95% interval excludes 0. A balanced accuracy of 0.5 is chance.

**Added under the coverage rule** (`padding.py` CHANGE 2, 2026-10-26, after the five results above were read):
every other leaderboard model that takes video or images. Same cases, prompt and verdicts; $48.76 for 5,330
gradings. Claude Fable 5.1 ran through the maintainers' own Anthropic key under 30-day safety retention, as on
the leaderboard; every other call at zero data retention.

| model | sees | balanced accuracy, as recorded → 4x | change [95% interval] | errors caught | clean videos cleared | no answer | verdict |
|---|---|---|---|---|---|---|---|
| GPT-6 Astra | 16 frames | 0.73 → 0.62 | −0.11 [−0.19, −0.03] | 49% → 39% | 96% → 84% (−12) | 10 | LENGTH HURTS DETECTION |
| Claude Fable 5.1 | 16 frames | 0.65 → 0.55 | −0.09 [−0.18, −0.002] | 69% → 73% | 60% → 38% (−22) | 0 | LENGTH HURTS DETECTION |
| Claude Opus 5.5 | 16 frames | 0.63 → 0.50 | −0.13 [−0.20, −0.05] | 37% → 35% | 89% → 66% (−23) | 0 | LENGTH HURTS DETECTION |
| GPT-5 Mini | 16 frames | 0.61 → 0.48 | −0.14 [−0.22, −0.04] | 62% → 46% (−16) | 60% → 50% | 6 | LENGTH HURTS DETECTION |
| Claude Haiku 5.5 | 16 frames | 0.59 → 0.49 | −0.10 [−0.18, −0.02] | 49% → 37% | 70% → 61% | 0 | LENGTH HURTS DETECTION |
| GLM 5.3 Flash | video | 0.59 → 0.54 | −0.05 [−0.14, +0.03] | 80% → 77% | 39% → 31% | 74 | not detected; a loss up to 0.14 not ruled out |
| GPT-5.6 Luna | 16 frames | 0.55 → 0.49 | −0.06 [−0.14, +0.01] | 31% → 16% (−15) | 79% → 82% | 6 | not detected; a loss up to 0.14 not ruled out |
| DeepSeek V4.1 Flash (Oct 17 snapshot) | 16 frames | 0.53 → 0.54 | +0.01 [−0.08, +0.09] | 35% → 38% | 72% → 70% | 30 | not detected; a loss up to 0.08 not ruled out |
| Gemma 4 26B A4B | video¹ | 0.53 → 0.52 | −0.00 [−0.06, +0.06] | 19% → 18% | 86% → 87% | 0 | not detected; a loss up to 0.06 not ruled out |
| DeepSeek V4.1 Flash | 16 frames | 0.51 → 0.51 | −0.01 [−0.09, +0.08] | 27% → 28% | 76% → 74% | 10 | not detected; a loss up to 0.09 not ruled out |
| Gemma 4 31B | video¹ | 0.50 → 0.52 | +0.02 [−0.02, +0.06] | 6% → 6% | 93% → 97% | 0 | not detected; a loss up to 0.02 not ruled out |
| Gemma 3 27B | 16 frames | 0.50 → 0.45 | −0.05 [−0.12, +0.02] | 62% → 62% | 39% → 28% (−10) | 0 | not detected; a loss up to 0.12 not ruled out |
| Gemma 3 4B | 16 frames | 0.46 → 0.45 | −0.00 [−0.06, +0.05] | 75% → 74% | 16% → 17% | 5 | not detected; a loss up to 0.06 not ruled out |

¹ Both Gemma 4 models were charged about 2,570 input tokens a recording at either length, so their endpoint
sends them a fixed few frames, as MiMo in the video task: they do not see the footage at this length. Ministral
8B is not here: its endpoint refused all 410 requests (at most 8 images a request).

- **Every 16-frame grader that detects errors above chance loses detection at 4x**, the five leading rows,
  by 0.09 to 0.14. This is the caveat pre-registered for the frames rows: 16 frames from a recording four times
  as long are four times as sparse, so these rows show what a frames-only grader does with a long recording, not
  the length effect alone. Astra is the best detector at either length (0.73 as recorded).
- **The false-alarm pattern holds for the added graders:** Fable, Opus, Astra and Gemma 3 27B clear 10-23 points
  fewer clean videos at 4x.
- The other added graders are at or near chance (0.45-0.59) at both lengths.

**Reading.**
- **Headline: on longer videos, graders report errors that are not there.** Four of five clear fewer
  clean videos at four times the length, by 11 to 30 points, each interval excluding 0.
- **Overall detection: no change was detected, but none is ruled out.** The pre-registered verdict is NO
  DETECTABLE EFFECT for every grader. The floor shows a 0.125 loss in balanced accuracy is caught 84% of
  the time. The intervals still allow losses of up to 0.13 (Gemini 3.8 Flash, Qwen) and 0.05-0.10 for the
  others. Gemini 3.8 Flash's interval reaches 0. The two strongest (Argon, Gemini 3.8 Flash) also catch more real errors. On a long
  recording they report errors that are not there.
  - Either they read more footage as more chances for something to go wrong, or the joined recordings hold
    errors their labels missed. The extra recordings were chosen because their labels say the error did not
    happen, so the second would mean label errors. A check of 12 false alarms, below, points to the
    first.
- **For a grader this matters more than the overall figure.** A model that marks students down for errors
  they did not make, more often on longer work, is a fairness problem even when its accuracy holds.
- **Perceptron leans the other way:** it says "no" almost always, and more so on long videos.
- **Only Argon and Gemini 3.8 Flash detect errors well above chance** (0.69-0.70 as recorded). The others
  are near 0.5 at either length.

**Where the false alarms point (checked after the results; not pre-registered).** The two strongest models
named a time for most new false alarms, that is "error" at 4x where they had said "no error" for the
recording alone. Rebuilding each joined video's order (verified frame by frame) places the cited time:

| model | in an added clean recording | in the original recording | no time given |
|---|---|---|---|
| Gemini 4 Argon (27) | 22 (+1 citing both) | 4 | 0 |
| Gemini 3.8 Flash (40) | 26 | 8 | 6 |

For about half of the added-recording cases, the same model had said "no error" when shown that recording
alone: 14 of 22 for Argon and 8 of 26 for Gemini 3.8 Flash. So the long video changed the model's reading
of the same footage.

Twelve cases were checked against the original recordings (960 x 540, 3 frames a second, 4 seconds either
side of the cited time). Each group was sampled at seed 11 and balanced by model: four the model also
flagged when shown the added recording alone, four it did not, and four in the original recording.
- **8 show no error.** The models misread ordinary actions. In peg transfer, a mid-air hand-off between
  graspers was read as a drop. In circle cutting, lifting away the cut-out circle was read as gauze coming
  off a clip.
- **4 could not be called.** Three are needle drops too small to see in the frames. One is a gauze edge
  that may have come loose from its clip.
- **None is a clear error the labels missed.**

These readings were made by the AI that ran the study, from still frames. They are not a rater's
judgement, and the four undecided cases need someone who knows the tasks. On this sample, though, the rise
in false alarms with length is mostly the models seeing errors that are not there, not missing labels.

**Limits.**
- One length step (4x, about 3 to 40 minutes).
- The joined recordings show other trainees doing the same task, which a model may notice.
- The error labels are LASANA's own. No second labeller, so there is no human reference for detection.
- Qwen3.8 27B ran out of its 4,096-token budget on 153 gradings, as the pre-registered settings allow.

Detail is in `../out/video/padding.json`.
