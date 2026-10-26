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
