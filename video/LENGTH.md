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

| model | balanced accuracy, as recorded → 4x | change [95% interval] | errors caught | clean videos cleared | no answer | verdict |
|---|---|---|---|---|---|---|
| Gemini 4 Argon | 0.70 → 0.71 | +0.01 [−0.06, +0.09] | 46% → 68% (+22) | 94% → 75% (−19) | 0 | NO DETECTABLE EFFECT |
| Gemini 3.8 Flash | 0.69 → 0.63 | −0.06 [−0.13, +0.00] | 66% → 83% (+17) | 73% → 43% (−30) | 10 | NO DETECTABLE EFFECT |
| Qwen3.8 27B | 0.57 → 0.52 | −0.04 [−0.14, +0.05] | 58% → 61% | 55% → 44% (−11) | 153 | NO DETECTABLE EFFECT |
| Gemini 3.5 Flash Lite | 0.56 → 0.53 | −0.02 [−0.10, +0.05] | 25% → 31% | 87% → 75% (−11) | 3 | NO DETECTABLE EFFECT |
| Perceptron mk1.5 | 0.51 → 0.51 | −0.00 [−0.05, +0.04] | 14% → 4% (−10) | 88% → 98% (+10) | 0 | NO DETECTABLE EFFECT |

Changes in brackets are those whose 95% interval excludes 0. A balanced accuracy of 0.5 is chance.

**Reading.**
- **Length does not change overall detection** for any grader, by the pre-registered verdict. Gemini 3.8
  Flash comes nearest to a loss, with an interval reaching 0.
- **Length makes graders say "yes" more.** Four of five clear fewer clean videos at four times the length,
  by 11 to 30 points. The two strongest (Argon, Gemini 3.8 Flash) also catch more real errors. On a long
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
