# Measured energy per grading, open-weight models

The design, the statistics and the verdicts are pre-registered in `energy.py`'s docstring, with two numbered
changes. CHANGE 1 came after the first runs, which took seconds, not minutes: 1-s polls and 20 windows. Its
first floor failed narrowly, and a t-interval replaced the percentile one. CHANGE 2 came after Llama's
figures: descriptive verdicts were added.

**Method.** Each model was served with vLLM v0.32.0 on one rented NVIDIA A100 80GB PCIe (RunPod) and given
the leaderboard battery (`bench.py --battery leaderboard`, `prompts/default.txt`, the canonical 100 cases per
task, max_tokens 4096), at 16 requests at a time. bench.py ran on the pod against localhost. The GPU's own
energy counter (NVML) and the count of finished gradings were read every second. The idle power is the mean of
60 s before and 60 s after the runs, with the model loaded. Each figure has a 95% interval from a block
bootstrap over 20 time windows of the run.

**Boundary.** NET is the GPU's energy above idle, per grading. GROSS includes idle. FULL-STACK is NET × 1.72,
from Google's split of a Gemini prompt's energy (active accelerators 58% of the total; Elsworth et al. 2025),
an assumption, not a measurement of this node. Not counted: this node's CPU, memory and network as measured,
cooling, the chips' manufacture, and loading the model.

**Self-check.**
- A simulation of the estimator (`floor`) recovers a planted energy per grading within 0.5% on average, and its
  interval covers it 91% of the time (bar 90%).
- On the pod, the counter agreed with the integral of the 1-s power readings within 1% for every model.
- **The eight board models all failed the idle check.** Idle power was 64-67 W before the runs and 73-81 W
  in the minute after (ratio 1.13-1.26; bar 1.10). A GPU idles higher while it is hot, so the bar was set too
  tight for a window taken straight after work. Under the pre-registered rule their verdicts are
  **UNMEASURED**, and their figures are shown labelled as such.
- **Olmo 3.1 32B passed it** (109 and 118 W, ratio 1.08). It ran on a second pod, because the first pod's host
  restarted the container five times. That pod had the same GPU model, but this card idles about 45 W higher.
  The NET figure removes idle, and the GROSS figures of the two pods do not compare. Which idle window is subtracted moves the NET figure
  by about 5-10%, shown as `net_wh_idle_range` in `out/energy.json`.

## Second run (2026-10-26, CHANGE 3): every model measured

The eight board models were re-run with a cool-down before the post-run idle reading: power had to fall within 5%
of the pre-run idle (it took 63-97 s). One A100 80GB PCIe, secure cloud, idle about 97-108 W; Gemma 4 31B ran on
a fresh pod after the first could not start it (its disk was most likely full after seven models' weights). **All
eight passed every check** (idle ratio 1.02-1.03; counter against integrated power within 0.4%). Olmo is from the
first run, which it passed. `out/energy.json` holds these figures; the first run is kept as
`out/energy-run1-idle-failed.json`.

| model | short answer, NET mWh [95%] | essay | code | short answer, FULL-STACK | essay | code | full leaderboard run, NET | one at a time vs batched (short / essay) | verdict |
|---|---|---|---|---|---|---|---|---|---|
| Llama 3.2 3B | 0.8 [0.8-0.9] | 2.0 [1.8-2.1] | 10.1 [6.4-13.8] | 1.5 | 3.4 | 17.5 | 9 Wh | 13x / 8x | BELOW SMALL on all three |
| Gemma 3 4B | 1.2 [1.1-1.2] | 3.8 [3.4-4.2] | 3.5 [3.2-3.8] | 2.0 | 6.6 | 6.0 | 6 Wh | 13x / 11x | BELOW SMALL on all three |
| Ministral 8B | 2.1 [1.2-2.9] | 3.7 [3.4-4.0] | 7.9 [4.8-11.1] | 3.6 | 6.4 | 13.7 | 10 Wh | 9x / 7x | BELOW SMALL on all three |
| Phi-4 (14B) | 3.1 [3.0-3.2] | 7.0 [6.2-7.8] | 25.5 [21.7-29.4] | 5.4 | 12.1 | 44.0 | 24 Wh | 14x / 10x | BELOW SMALL on all three |
| GPT-OSS 20B | 7.7 [7.3-8.1] | 10.8 [10.2-11.5] | 19.3 [17.5-21.2] | 13.2 | 18.7 | 33.4 | 28 Wh | 7x / 6x | BELOW SMALL on all three |
| Gemma 4 26B A4B | 2.5 [2.3-2.6] | 4.9 [4.6-5.1] | 4.9 [4.7-5.1] | 4.2 | 8.4 | 8.4 | 9 Wh | 6x / 5x | BELOW SMALL on all three |
| Gemma 3 27B | 5.4 [5.2-5.6] | 12.1 [10.9-13.3] | 12.4 [11.6-13.1] | 9.3 | 20.9 | 21.3 | 22 Wh | 15x / 9x | BELOW SMALL on all three |
| Gemma 4 31B | 6.5 [6.2-6.8] | 16.8 [15.3-18.3] | 14.9 [14.1-15.8] | 11.2 | 28.9 | 25.8 | 29 Wh | 14x / 9x | BELOW SMALL on all three |
| Olmo 3.1 32B (first run) | 6.5 [4.9-8.1] | 13.6 [12.4-14.7] | 11.5 [10.8-12.3] | 11.2 | 23.4 | 19.9 | 24 Wh | 12x / 9x | BELOW SMALL on all three |

- **All 27 model-task figures are BELOW THE SMALL-MODEL ESTIMATE** (registered verdicts now, not descriptive), by
  a median factor of 4 (1.4 to 17), and 15 to 128 times below the mid-size estimate.
- **Batching:** one request at a time costs 5-15 times as much per grading.
- **The second run agrees with the first.** The NET figures moved by a few percent (a different card, and a
  different idle subtracted); every conclusion of the first run stands, now with its verdicts.

## First run (2026-10-25)

### Results

Wh are thousandths of a watt-hour here (mWh). One grading, batched at 16 at a time, one A100:

| model | short answer, NET mWh [95%] | essay | code | short answer, FULL-STACK | essay | code | full leaderboard run, 2,342 gradings, NET | one at a time vs batched (short answer / essay) |
|---|---|---|---|---|---|---|---|---|
| Llama 3.2 3B | 0.8 [0.8-0.9] | 2.3 [2.1-2.5] | 11.3 [6.4-16.2] | 1.5 | 3.9 | 19.5 | 10 Wh | 13x / 8x |
| Gemma 3 4B | 1.2 [1.1-1.2] | 4.2 [3.8-4.5] | 3.7 [3.5-4.0] | 2.0 | 7.2 | 6.5 | 7 Wh | 13x / 9x |
| Ministral 8B | 1.7 [1.6-1.7] | 4.8 [4.0-5.6] | 9.9 [6.2-13.7] | 2.9 | 8.3 | 17.1 | 12 Wh | 11x / 5x |
| Phi-4 (14B) | 3.7 [3.6-3.8] | 8.2 [7.3-9.1] | 29.4 [25.6-33.2] | 6.3 | 14.1 | 50.7 | 28 Wh | 15x / 10x |
| GPT-OSS 20B | 9.2 [8.6-9.9] | 12.9 [12.2-13.7] | 23.9 [21.3-26.5] | 15.9 | 22.3 | 41.2 | 34 Wh | 6x / 5x |
| Gemma 4 26B A4B | 2.7 [2.6-2.9] | 5.7 [5.4-6.0] | 5.6 [5.3-5.9] | 4.7 | 9.8 | 9.7 | 11 Wh | 5x / 4x |
| Gemma 3 27B | 6.3 [6.0-6.6] | 14.1 [12.7-15.5] | 14.2 [13.5-15.0] | 10.9 | 24.3 | 24.5 | 26 Wh | 16x / 10x |
| Gemma 4 31B | 7.3 [7.0-7.6] | 19.1 [17.3-20.8] | 16.8 [15.8-17.8] | 12.6 | 32.8 | 29.0 | 33 Wh | 14x / 9x |
| Olmo 3.1 32B (second pod) | 6.5 [4.9-8.1] | 13.6 [12.4-14.7] | 11.5 [10.8-12.3] | 11.2 | 23.4 | 19.9 | 24 Wh | 12x / 9x |

**Against the estimates** (docs/ENERGY.md's per-token model, at each model's own measured tokens; FULL-STACK
compared).
- **Olmo 3.1 32B, the one measured verdict: BELOW THE SMALL-MODEL ESTIMATE on all three tasks.** Measured /
  estimate is 0.74 for short answers, 0.41 for essays and 0.29 for code.
- The eight board models are UNMEASURED under the registered rule. Descriptively (CHANGE 2), with either idle
  window, or with nothing subtracted:
  - 23 of their 24 model-task figures are **below the small-model estimate** (Llama 3.1 8B in Jegham et al.), by
  a factor of 1.3 to 15 (measured / estimate 0.07-0.78; median factor 4).
  - The one exception is Gemma 4 31B's short answers. Taken GROSS, nothing subtracted, it lands just inside the
  estimates' range (16.9 against 16.1 mWh).
  - All are far below the mid-size estimate (GPT-4o), by 13 to 120 times.
So the published per-token model, fitted to API-inferred figures for hosted models with their overheads,
overstates what an open model up to 32B uses on one modern GPU in a batch, by a factor of about 2.5 to 7 for the middle half of figures.

**Reading.**
- **Batching is the largest lever, not model size.** The same model sending one request at a time used 4-16
  times the energy per grading. Gemma 3 27B goes from 6 to 98 mWh per short answer. A school sending its
  marking as a batch, or a vendor serving many schools at once, is near the batched figure; a single
  teacher's request on a dedicated GPU is near the other.
- **Output length drives the rest.** Code costs most for the models that write long replies (Phi-4 278
  tokens on average, GPT-OSS 562 with its reasoning, Llama 240), and about as much as an essay for models
  that reply briefly (Gemma, 50-100 tokens).
- **A sparse model is cheaper than its size suggests.** Gemma 4 26B A4B, which uses 3.8B parameters per
  token, costs about a third of the dense Gemma 4 31B per grading.
- **In everyday terms** (FULL-STACK, mid-size batched model, about 10-30 mWh): a teacher's term of 1,500
  gradings is 15-45 Wh, about 12-35 minutes of video streaming. The whole leaderboard battery for one model is
  7-34 Wh on the GPU.

**The served weights.** Gemma 3 and Llama 3.2 came from ungated copies (unsloth), whose hashes cannot be
checked against the gated originals. The self-hosted base marks agree with the board's about as well as the
board agrees with itself on a retest. For example, Gemma 3 27B scores 0.98, 0.92 and 0.96 against the board,
with board retests of 0.98, 0.92 and 0.96. That fits the same weights. Ministral 8B agrees less well than its
own retest (0.79 and 0.69 against 0.96 and 0.90), likely different serving defaults on Mistral's API. This does
not change its energy.

**Limits.**
- Olmo's figures come from a second card of the same model.
- One GPU model, one serving stack, one batch size (plus one at a time). Energy per grading falls with newer
  GPUs and larger batches, and rises with smaller ones.
- 100 cases per task.
- The idle check failed. Its consequence, which idle is subtracted, is small beside the gap to the estimates,
  but it is why only Olmo's verdict stands.
- Closed models cannot be measured this way.

Output: `out/energy.json` (per model and task: NET, GROSS and FULL-STACK figures, intervals, idle range,
tokens, estimates, the board-agreement check), `out/floor.json` and `out/floor-change1-percentile-failed.json`.
Run folders, which hold reply text, stay outside the repository.
