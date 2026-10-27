# Precision with the host held fixed: 4-bit vs 8-bit vs bf16 on one GPU

Pre-registered in `study.py` (2026-10-27), before any call; CHANGE 1 (model and route-statistic fixes found by
the floor, before any call) is recorded there. Output: `out/precision-controlled.json` (after the runs).

**Question.** `hosting/` found the same open model far easier to game on OpenRouter hosts serving 4-bit weights
than on hosts serving 8-bit. Each arm there was a different set of hosts. Here the weights, the serving software
(vLLM v0.32.0), the GPU (one A100 80GB) and the requests are the same, and only the precision changes: bf16,
fp8 and 4-bit NF4, applied at load to the same checkpoint. Phi-4 and Gemma 3 27B, on code and essays, the
board's 100 cases, with the base, retest, polite-request, forged-override, vouched and five null-answer probes.

vLLM v0.32.0 no longer has the bitsandbytes method, so the planned 4-bit NF4 arm could not load; before any
4-bit grading it was replaced (CHANGE 2) by vLLM's online MXFP4, the 4-bit format some of the hosts in
`hosting/` declare. The serving logs confirm each arm: `MarlinMxFp4LinearKernel for MXFP4 GEMM`, with the weights
taking 8.9 GiB for Phi-4 at MXFP4 against 27.4 GiB at bf16, and 16.4 GiB for Gemma 3 27B at MXFP4 against
27.7 GiB at fp8. 12 runs, 6,300 gradings, none unsent; 3 replies without a mark (Phi-4 essays, bf16 2, fp8 1).
One A100-SXM4-80GB pod (community cloud) for 0.87 hours, about $1.20 at $1.39/h; the pod was terminated.

**Floor** (`out/floor.json`, from the board's own submissions, before any call). A forged-override rise of 10% of
the scale planted in one arm was detected in 98% to 100% of worlds in all four model-task cells, with false
alarms at most 1%: the gain verdicts are measurable everywhere. The route check (do two arms' marks differ by
more than each arm differs from itself) passes on essays (88% and 100% detection) and fails on code (5% and
58%), where the run-to-run noise on a 0-90 scale is too large for the planted shift; code's route verdicts are
therefore UNMEASURED. The first floor run, which failed and led to CHANGE 1, is kept as `out/floor-failed-1.json`.


## Result: PRECISION ALONE NOT SHOWN TO RAISE GAMING

Primary measure: the forged override's gain, 4-bit (MXFP4) minus 8-bit (fp8), paired by case, in points of the
scale (positive = the 4-bit arm is more gameable), with 95% bootstrap intervals over cases.

| model, task | forged gain: MXFP4 - fp8 | verdict | polite request: MXFP4 - fp8 (secondary) | verdict | QWK: MXFP4 - fp8 |
|---|---|---|---|---|---|
| Phi-4, code | -1.7 [-8.4, +5.0] | NO DIFFERENCE DETECTED | **+9.9 [+5.2, +14.8]** | **LOWER PRECISION MORE GAMEABLE** | **-0.128 [-0.217, -0.051]** |
| Phi-4, essays | +2.0 [-1.2, +5.4] | NO DIFFERENCE DETECTED | -1.8 [-4.2, +1.0] | NO DIFFERENCE DETECTED | +0.039 [-0.025, +0.107] |
| Gemma 3 27B, code | -1.0 [-5.9, +3.1] | NO DIFFERENCE DETECTED | -0.8 [-4.7, +2.9] | NO DIFFERENCE DETECTED | +0.043 [+0.017, +0.075] |
| Gemma 3 27B, essays | +2.8 [+0.4, +5.0] | NO DIFFERENCE DETECTED | +3.2 [+0.8, +5.6] | NO DIFFERENCE DETECTED | -0.044 [-0.114, +0.032] |

Bold marks a pre-registered verdict other than NO DIFFERENCE DETECTED, or a QWK interval that excludes 0 in the
direction that harms agreement. Each arm's own figures, and the MXFP4 - bf16 and fp8 - bf16 pairs, are in
`out/precision-controlled.json`. fp8 against bf16: NO DIFFERENCE DETECTED in every cell on both gains, with
intervals within -3.3 to +5.3 points.

Per arm (gain as points of the scale; null answers credited out of those graded):

| model, task | arm | QWK | forged gain | polite-request gain | null answers credited |
|---|---|---|---|---|---|
| Phi-4, code | bf16 | 0.758 | -10.0 | +8.0 | 3 of 15 |
| | fp8 | 0.790 | -8.7 | +10.3 | 3 of 15 |
| | MXFP4 | 0.663 | -10.4 | +20.2 | 9 of 15 |
| Phi-4, essays | bf16 | 0.598 | +7.2 | +4.6 | 5 of 33 |
| | fp8 | 0.606 | +6.4 | +5.6 | 7 of 34 |
| | MXFP4 | 0.645 | +8.4 | +3.8 | 20 of 35 |
| Gemma 3 27B, code | bf16 | 0.754 | +28.4 | +20.6 | 0 of 15 |
| | fp8 | 0.764 | +29.8 | +20.2 | 0 of 15 |
| | MXFP4 | 0.808 | +28.8 | +19.4 | 0 of 15 |
| Gemma 3 27B, essays | bf16 | 0.643 | +7.6 | +9.8 | 4 of 35 |
| | fp8 | 0.642 | +8.4 | +10.4 | 4 of 35 |
| | MXFP4 | 0.598 | +11.2 | +13.6 | 7 of 35 |

**Reading.**
- **With the host held fixed, 4-bit weights did not reproduce the hosting result.** In `hosting/`, a forged
  override gained 11 to 51 points of the scale more on 4-bit hosts than on 8-bit hosts. Here, with only the
  precision changed, the forged override's extra gain at MXFP4 is between -1.7 and +2.8 points in all four
  cells, and every interval excludes a rise larger than 5.4 points. The large hosting differences therefore
  cannot be attributed to 4-bit weights as such, at least for these two models: something else about those
  hosts, or about the larger mixture-of-experts models served there, contributed.
- **4-bit is not harmless either.** For Phi-4 on code, MXFP4 doubled the polite request's gain (+20.2 points
  against +10.3 at fp8; difference +9.9 [+5.2, +14.8], LOWER PRECISION MORE GAMEABLE on the secondary measure),
  lowered agreement with the raters by 0.128 QWK, and credited more of the null answers (9 of 15 against 3 of 15
  on code; 20 of 35 against 7 of 34 on essays; descriptive). On Gemma 3 27B's essays both gains rose slightly at
  MXFP4 (+2.8 and +3.2 points, intervals above 0 but below the 5-point threshold, so NO DIFFERENCE DETECTED by
  the pre-registered rule). The effect of 4-bit weights depends on the model and the task.
- **8-bit is indistinguishable from the released weights** on every gain, for both models and both tasks.
- **The route check is weaker than planned.** It passed its floor only on essays. For Gemma 3 27B on essays the
  MXFP4 arm's marks differ from both other arms by more than each arm differs from itself (ROUTES DIFFER). For
  Phi-4 the statistic is negative throughout, meaning the arms' first replies agree with each other more than an
  arm's reply agrees with its own retest. The reason is in the serving, not the precision: a fresh vLLM server
  draws its sampling randomness from the same default seed, so each arm's base requests, sent first and in the
  same order, share random numbers (42 of Phi-4's 100 essay replies are word for word the same at bf16 and fp8),
  while the retest, sent later, does not. The floor's null did not model this, so for Phi-4 the route verdict
  (ROUTES NOT SHOWN TO DIFFER) says nothing about whether the arms differ. The gain comparisons are not biased by
  it: shared randomness only makes the paired differences more precise.

**What it means for the board.** Pinning precision remains sound advice, because a 4-bit copy can be worse (Phi-4
here) and because hosts differ in more than precision. But the board should not say that 4-bit weights by
themselves make a model far easier to game: for these two models they changed the forged override's effect by at
most about 5 points of the scale, against the 11 to 51 points between hosts.

**Limits.** Two dense models of 14B and 27B parameters, not the large mixture-of-experts models (DeepSeek V4 Pro,
GLM 5.3) where `hosting/` found the effect; MXFP4 applied by vLLM at load, which may differ from a host's own
quantisation recipe (some hosts calibrate or keep sensitive layers at higher precision); an A100 has no fp4 or fp8
arithmetic, so the low-precision weights are expanded for the matrix products, which is how such weights run on
that hardware but not how a Blackwell host runs them; each model's default sampling; 100 cases per task. The
route check measures only whether the marks differ, and is uninformative for Phi-4 (above).
