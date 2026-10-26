# A floor for the recording-quality probes

Pre-registered in `floor.py` (2026-10-26). Outputs: `out/simulate.json` (step 1), `out/control.json` (step 2).

**Question.** The speech and video tasks probe recording quality: noise and a telephone channel for speech, a
low-resolution copy and a second camera for video. Their results were reported but not ranked, because nothing
showed the instrument could see an effect if there were one.

## Step 1: simulated floor (no calls)

Each existing media run's own base and retest marks are resampled. A planted shift of 0%, 5% or 10% of the scale
is added, in 200 worlds per size.
- **CHANGE 1:** the first run's false alarms were 10-40%, because a resampled world kept the run's own observed
  base-to-retest gap. Each case's two gradings are now swapped at random. The first run is kept in
  `out/simulate-run1-failed.json`.

| verdict | runs |
|---|---|
| CAN SEE 5% | 14: five speech graders, and every video run but MiMo and Nova |
| CAN SEE 10% | 1: MiMo v2.6 Flash, video |
| CANNOT SEE | 2: Meta Muse Spark, speech (70 usable recordings; noisy marks), and Nova 2 Lite, video (no retest marks) |

So for 15 of 17 runs, a recording-quality probe that reads "no change" is a measured null at that size, not a
blind one. The earlier finding that most speech graders hold their marks under 10 dB noise now stands as a result.

## Step 2: speech positive control

The six speech graders graded the same recordings under added noise: 10 dB (from the original run), 0 dB and
-10 dB SNR. At -10 dB the noise is louder than the speech. The control passes if at least four of six models mark
the -10 dB recordings lower. Output: `out/control.json`; cost $2.20 of the $8 cap.

**Result: the control PASSES (5 of 6 respond).** Change in mark against the clean recording, as a share of the
scale, with 95% intervals (negative = marked lower under noise):

| model | 10 dB | 0 dB | -10 dB | verdict |
|---|---|---|---|---|
| Perceptron Mk1.5 | -0.086 [-0.123, -0.051] | -0.242 [-0.297, -0.191] | -0.590 [-0.648, -0.531] | responds |
| Meta Muse Spark | +0.006 [-0.086, +0.111] | -0.215 [-0.317, -0.105] | -0.562 [-0.670, -0.453] | responds |
| MiMo v2.6 Flash | -0.006 [-0.035, +0.023] | -0.027 [-0.060, +0.005] | -0.245 [-0.294, -0.194] | responds |
| Gemini 4 Argon | -0.003 [-0.024, +0.019] | -0.000 [-0.033, +0.035] | -0.091 [-0.143, -0.033] | responds |
| Voxtral Small 24B | +0.000 [-0.011, +0.011] | -0.013 [-0.026, +0.000] | -0.026 [-0.037, -0.014] | responds |
| Gemini 3.8 Flash | -0.008 [-0.026, +0.011] | -0.016 [-0.037, +0.005] | +0.004 [-0.034, +0.040] | **does not respond** |

What this means:
- **The noise probe can see a quality effect when there is one.** Five of six graders mark speech lower once it is
  buried in noise. So the step-1 finding stands: most graders hold their marks at 10 dB, the noise a real
  classroom recording might carry.
- **Gemini 3.8 Flash does not lower its marks even when the noise is louder than the speech.** It hears the
  noise: its reasons say so ("easily understood despite the heavy background noise") while giving 8 or 10 out of
  10. For pronunciation scoring, a grader that rates unintelligible audio as clear is not reading the recording.
- **Voxtral and Gemini 4 Argon respond, but only slightly** (3 and 9 points of the scale at -10 dB). Two models
  start dropping marks at 0 dB; for the rest, any effect appears only at -10 dB.
- **Unmarked gradings.** Gemini 4 Argon and Muse Spark each returned no mark on 45 of 300 calls (15%):
  - Argon returned garbled text.
  - Muse Spark said it cannot hear audio attachments. Muse Spark answered from several hosts, so this is most
    likely a host that does not pass audio through; it was also the run step 1 could not measure.
  - Their changes are computed on the marked gradings only.

Limits: noise was added synthetically (white noise at a fixed SNR), not recorded in classrooms. No listener rated
the noisy recordings, so this shows that marks fall, not by how much they should.

## Step 3: video positive control and lighting

Pre-registered in `floor.py` (step 3, CHANGES 2 and 3), before any call of this step. Every video run graded the
same 100 LASANA recordings again, fresh, four ways: as recorded; with the brightness cut to a quarter (the work
clearly visible, as in a dim room); cut to a twentieth (barely visible); and cut to 16 x 9 blocks (nothing of the
skill visible). Output: `out/video_control.json`. Cost $13.72 of the $55 cap, on top of the first pass's spend
(the resume after CHANGE 3 re-used every cached grading).

**The control PASSES: 7 of the 10 measurable runs respond to an unreadable picture** (pre-registered bar: two
thirds). Nova 2 Lite is unmeasurable: it gave a grade on none of the base recordings. Change in grade as a share
of the 16-point scale, with 95% intervals (negative = graded lower):

| run | quarter brightness | a twentieth | 16 x 9 blocks | control | lighting |
|---|---|---|---|---|---|
| Perceptron Mk1.5 | -0.032 [-0.057, -0.004] | -0.505 [-0.546, -0.463] | -0.334 [-0.384, -0.285] | responds | **grades dim work lower** |
| GPT-5 Mini (16 frames) | -0.036 [-0.071, -0.003] | -0.332 [-0.398, -0.268] | -0.105 [-0.154, -0.056] | responds | **grades dim work lower** |
| Gemini 3.5 Flash Lite | -0.011 [-0.054, +0.033] | -0.259 [-0.326, -0.185] | -0.147 [-0.211, -0.082] | responds | no effect detected |
| MiMo v2.6 Flash | +0.003 [-0.036, +0.040] | -0.086 [-0.138, -0.037] | -0.150 [-0.210, -0.091] | responds | no effect detected |
| Claude Haiku 5.5 (16 frames) | -0.022 [-0.064, +0.017] | -0.146 [-0.197, -0.095] | -0.069 [-0.119, -0.021] | responds | no effect detected |
| Qwen3.8 27B | -0.018 [-0.045, +0.011] | -0.079 [-0.121, -0.039] | -0.060 [-0.094, -0.028] | responds | no effect detected |
| Claude Opus 5.5 (16 frames) | +0.011 [-0.013, +0.037] | -0.006 [-0.059, +0.045] | +0.009 [-0.049, +0.064] | responds (declines 52 of 100) | no effect detected |
| Gemini 3.8 Flash (video) | -0.012 [-0.035, +0.013] | -0.062 [-0.096, -0.029] | +0.021 [-0.007, +0.046] | **does not respond** | not read |
| Gemini 3.8 Flash (16 frames) | -0.011 [-0.034, +0.011] | -0.204 [-0.229, -0.177] | -0.011 [-0.034, +0.015] | **does not respond** | not read |
| Gemini 4 Argon | +0.026 [-0.005, +0.057] | +0.052 [+0.012, +0.089] | +0.049 [+0.011, +0.086] | **raises the grade** | not read |

What this means:
- **The video probes can see an effect when there is one**, for most graders. So the earlier "no change" results
  for low resolution and the second camera stand as results for those graders.
- **Claude Opus 5.5 is the only grader that says it cannot see.** It declines to grade 52 of the pixelated
  recordings and 63 of the near-black ones, and grades the rest about as before. Every other grader gives a grade
  to every degraded recording.
- **Gemini 3.8 Flash grades a recording cut to blocks the same as the original**, from video or from frames, and
  Gemini 4 Argon grades it *higher*. Neither is reading the skill from the picture.
- **Lighting.** At a quarter brightness, where the work is plainly visible, two graders give lower grades:
  Perceptron Mk1.5 and GPT-5 Mini, each by about 3 to 4% of the scale. For five others no effect was detected. No
  grader declined a dim recording, so the "I can't see you" failure did not occur at this level of darkness.

Limits: brightness was cut digitally (a dark room also adds noise and shifts colour); the work is hands and
instruments, not faces, so this measures lighting, not skin tone; the "by eye" checks of each condition were one
frame each, by the agent that wrote the design.

