# Essays: generative fine-tuning of Gemma 4 26B A4B

Pre-registered in `study.py` (2026-10-27), before any training run or model call of this design.

**Question (the maintainer's).** If an open model is fine-tuned on graded essays generatively, so that it still writes
its reply (a grade and then a reason, in the board's format), does its essay grading improve, and what does it cost on
everything else the board measures?

**Status.** Pre-registered; the overlap check has run (`out/split-check.json`: no TRAIN essay is a TEST or board
essay, by id or by text). Results follow here when the runs are complete.
