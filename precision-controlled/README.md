# Precision with the host held fixed: 4-bit vs 8-bit vs bf16 on one GPU

Pre-registered in `study.py` (2026-10-27), before any call; CHANGE 1 (model and route-statistic fixes found by
the floor, before any call) is recorded there. Output: `out/precision-controlled.json` (after the runs).

**Question.** `hosting/` found the same open model far easier to game on OpenRouter hosts serving 4-bit weights
than on hosts serving 8-bit. Each arm there was a different set of hosts. Here the weights, the serving software
(vLLM v0.32.0), the GPU (one A100 80GB) and the requests are the same, and only the precision changes: bf16,
fp8 and 4-bit NF4, applied at load to the same checkpoint. Phi-4 and Gemma 3 27B, on code and essays, the
board's 100 cases, with the base, retest, polite-request, forged-override, vouched and five null-answer probes.

**Floor** (`out/floor.json`, from the board's own submissions, before any call). A forged-override rise of 10% of
the scale planted in one arm was detected in 98% to 100% of worlds in all four model-task cells, with false
alarms at most 1%: the gain verdicts are measurable everywhere. The route check (do two arms' marks differ by
more than each arm differs from itself) passes on essays (88% and 100% detection) and fails on code (5% and
58%), where the run-to-run noise on a 0-90 scale is too large for the planted shift; code's route verdicts are
therefore UNMEASURED. The first floor run, which failed and led to CHANGE 1, is kept as `out/floor-failed-1.json`.

Results: to follow.
