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
    happen, so the second would mean label errors. Checking which needs a person to look at a sample of
    false alarms.
- **For a grader this matters more than the overall figure.** A model that marks students down for errors
  they did not make, more often on longer work, is a fairness problem even when its accuracy holds.
- **Perceptron leans the other way:** it says "no" almost always, and more so on long videos.
- **Only Argon and Gemini 3.8 Flash detect errors well above chance** (0.69-0.70 as recorded). The others
  are near 0.5 at either length.

**Limits.**
- One length step (4x, about 3 to 40 minutes).
- The joined recordings show other trainees doing the same task, which a model may notice.
- The error labels are LASANA's own. No second labeller, so there is no human reference for detection.
- Qwen3.8 27B ran out of its 4,096-token budget on 153 gradings, as the pre-registered settings allow.

Detail is in `../out/video/padding.json`.
