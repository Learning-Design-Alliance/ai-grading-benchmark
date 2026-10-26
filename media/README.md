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

Running: the six speech graders under noise at 0 dB and -10 dB SNR. The control passes if at least four of six
mark speech drowned at -10 dB lower. Results follow here.
