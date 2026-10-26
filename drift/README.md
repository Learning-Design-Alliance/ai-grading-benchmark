# Drift watch

The monthly drift watch (`monitor.py`; its docstring is the pre-registration, with two changes made before any
comparison). Results, and the history of model-version drift on this board, are in `../docs/DRIFT.md`. Month
files are in `out/<date>/` (marks only); the baseline month is 2026-10-26; the 30-case month kept apart is
`out/2026-10-26-anchor/`. Verdicts: DRIFT when the 95% interval of the mean shift excludes 0 (material at 2% of
the scale or more), otherwise NO DRIFT DETECTED, or UNDERPOWERED if the floor fails.
