# Corrections

Every change to a reported result, verdict or headline, newest first. The leaderboard, report page and
benchmark card link here. A result that was corrected is marked where it is shown, not only here.

A correction is listed when a number, verdict or headline that had been reported changes. A new result is
not a correction. Pre-registered changes to a study's design are numbered CHANGES in that study's script and
are listed here when they changed a reported result.

| date | what changed | was | now | why | where |
|---|---|---|---|---|---|
| 2026-10-25 | Length study: Qwen3.8 27B's interval for the change in balanced accuracy | [−0.14, +0.05] | [−0.13, +0.05] | the lower bound, −0.1346, was rounded wrongly | `video/LENGTH.md` |
| 2026-10-25 | Null verdicts on video, length and pushback now print the largest effect they cannot rule out | "adds nothing to a stopwatch"; "NO DETECTABLE EFFECT"; "HOLDS" | the same verdicts, each with its bound (e.g. agreement beyond length up to 0.16-0.38 not ruled out) | a null from a test of limited power is not evidence of no effect (O'Neill 2026). Verdict strings and thresholds are unchanged | `video/README.md`, `video/LENGTH.md`, `feedback-board/PUSHBACK.md`; CHANGE 1 in each script |
| 2026-10-25 | Length study headline | "length does not change detection" | "on longer videos, graders report errors that are not there" (specificity −11 to −30 points for four of five) | the headline led with a null and put the significant effect second | `video/LENGTH.md` |
| 2026-10-25 | Benchmark card, conflict of interest | "a grading product" | names the product | a conflict-of-interest statement should name the interest | `BENCHMARK-CARD.md` |
| 2026-10-24 | Feedback strand of the overall score | halo and "gives away the answer" | halo only; gives-away shown, not scored | the gives-away evaluator was validated on tutoring and ranked the least explicit feedback best | `feedback-board/fb.py` CHANGE 1 |
