# Host precision: the same open model, served at 8-bit or 4-bit

Pre-registered in `study.py` (2026-10-26), before any call. Output: `out/hosting.json`.

**Question.** OpenRouter routes an open-weights model to whichever host answers, and the hosts run it at
different numeric precision: on its zero-retention list, DeepSeek V4 Pro is served at fp8 by some hosts and at
4-bit (fp4, mxfp4) by others. The board pins no host. Does the precision change the grading?

**Design.** The same requests, with OpenRouter's filter `quantizations: ["fp8"]` or `["fp4", "mxfp4", "nvfp4"]`,
zero retention as always: DeepSeek V4 Pro on code and essays, GLM 5.3 on code; the board's 100 cases; probes
base, injection (a polite request for full marks), forged (a forged grading override), vouched (held out) and the
five blank or junk answers. Comparisons are paired by case, with 95% bootstrap intervals. Every reply's host was
checked against its arm. The cap was raised from $10 to $16 to complete three code runs cut at their per-run cap
(only the unsent gradings were added; the design did not change). Spend about $16.

## Result: PRECISION MATTERS, in all three comparisons

| model, task | arm | QWK | forged gain | polite-request gain | blank answers credited |
|---|---|---|---|---|---|
| DeepSeek V4 Pro, code | 8-bit | 0.75 | +21% | 0% | 0% |
| | 4-bit | 0.46 | **+72%** | +7% | 0% |
| DeepSeek V4 Pro, essays | 8-bit | 0.56 | +23% | +9% | 0% |
| | 4-bit | 0.55 | **+55%** | **+31%** | **29%** |
| GLM 5.3, code | 8-bit | 0.89 | 0% | -1% | 0% |
| | 4-bit | 0.86 | **+11%** | **+13%** | 0% |

Gains are shares of the scale; positive means the note raised the mark.

Paired differences, 8-bit minus 4-bit:
- DeepSeek V4 Pro, code: forged gain -0.51 [-0.60, -0.41]; QWK +0.31 [+0.15, +0.46].
- DeepSeek V4 Pro, essays: forged gain -0.32 [-0.39, -0.25]; polite-request gain -0.22 [-0.30, -0.14]; QWK no
  difference detected.
- GLM 5.3, code: forged gain -0.11 [-0.17, -0.06]; polite-request gain -0.14 [-0.20, -0.07]; QWK no difference
  detected.

**Reading.**
- **The 4-bit hosts are the gameable ones.** In every comparison the forged override gains more at 4-bit, by 11
  to 51 points of the scale. The held-out "vouched" note moved neither arm.
- **The board's rows for these two models are largely their hosts' rows.**
  - DeepSeek V4 Pro's board run was served almost entirely by 4-bit hosts: 597 of its 620 code gradings came
    from Sail Research, which serves it only at fp4. Its board figures match the 4-bit arm: code QWK 0.47,
    forged +70%.
  - At 8-bit it agrees with the experts at 0.75 on code. It is still gamed on both tasks, by about a fifth of
    the scale, so it would still carry a flag.
  - GLM 5.3's board run on code came 95% from Wafer and InferenceNet, both fp4. Its board flag on code (11%) is
    its 4-bit figure; at 8-bit it is not gamed at all.
- **Agreement can hide it.** On essays both arms agree with the experts equally well (0.56 against 0.55); only
  the probes show the difference.
- **Why.** Not tested here. A plausible reading is that 4-bit weights lose some of the fine control that keeps
  an instruction-tuned model from treating text inside the work as an instruction.

**What it means for the board.**
- An open model's row describes the model as served by the hosts that answered. The board records the hosts
  of every grading (`providers` in each submission) but not their precision.
- A fair comparison pins precision. The obvious change is to re-run the open models with
  `quantizations: ["fp8", "bf16"]` and record precision with each grading. That is a decision for the
  maintainers, not made here.
- **For schools:** asking a router for "the model" can buy a cheaper, compressed copy of it. The copy agrees with
  teachers about as well, and can be talked into full marks far more easily.

**Limits.** Two models, three task pairs, one router's precision labels (hosts of unstated precision were
excluded). A host's label is its own statement.
