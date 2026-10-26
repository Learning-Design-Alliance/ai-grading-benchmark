# Study template

Copy this docstring to the top of `<study>/study.py`, fill every section before the first call, commit, and run
`python3 scripts/check_study.py <study>`. The rules behind each section are in `docs/METHODOLOGY.md` (section
numbers in brackets).

```
"""<The question, in one line>? PRE-REGISTERED <YYYY-MM-DD>, before any call of this design.

WHY. What the board cannot yet show, and why it matters to someone using a grader.

DESIGN.
- Models (and why these): ...
- Cases: corpus, licence, the cases used (seed), how many.
- Conditions: each one, written out. All graded on the same days [1.6].
- Setup recorded for every grader: prompt, reasoning effort, host and precision (open models pinned with
  `provider.quantizations`, rows labelled) [2.1, 2.2], retention route [2.4].
- Probes, and what a sound grader does under each (raise, lower, no change) [1.8].

MEASURES. Each statistic, its unit (shares of the scale [1.7]), its sign convention [4.1], the unit resampled for
intervals [4.4], and the human ceiling or length baseline it sits beside [4.5].

VERDICT. The exact strings, and the rule for each [1.5]. Every null verdict reports what it does not rule out [4.2].
State the direction in the label, not only the sign of a number [4.1].

FLOOR. The planted effect, its size, the null world and how it is centred [1.4], the pass bars (detection, false
alarm), and what happens if it fails (UNMEASURED; figures descriptive) [1.2]. Written and run before any real
result is read. Never enlarged to pass [1.3].

LIMITS stated in advance.

BUDGET. A hard cap across the study; per-run caps from what is left. Check runs are complete before analysing
them (`scripts/check_runs.py`) [3.1].

CHANGES: (numbered, dated, with the reason and whether any result had been read; failed outputs kept)

Usage:
    python3 <study>/study.py ...
"""
```

**After the runs:**
- `scripts/check_runs.py <run dirs>`
- analyse
- write the README: question, design in short, result table, reading, limits
- add a CORRECTIONS row if any reported figure changed [5.4]
- run the independent audit (`docs/AUDIT-PROMPT.md`) before anything leaves the team [5.3]

**For a new modality,** also work through the checklist in `docs/METHODOLOGY.md` §7.
