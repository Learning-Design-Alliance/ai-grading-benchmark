# Corrections

Every change to a reported result, verdict or headline, newest first. The leaderboard, report page and
benchmark card link here. A result that was corrected is marked where it is shown, not only here.

A correction is listed when a number, verdict or headline that had been reported changes. A new result is
not a correction. Pre-registered changes to a study's design are numbered CHANGES in that study's script and
are listed here when they changed a reported result.

| date | what changed | was | now | why | where |
|---|---|---|---|---|---|
| 2026-10-25 | Claude Haiku 5.5, re-run under verified zero retention (all five tasks and feedback) | overall 91.0; pushback +3.5% [+1.4, +5.7]; working effect +1.91 | overall 91.4 (rank 3, interval 2-8 unchanged); pushback +3.1% [+0.9, +5.4]; working effect +1.86; halo +0.11; gives-away 98% | about half its earlier gradings went through the maintainers' own key with 30-day retention | `submissions/anthropic__claude-haiku-5.5/` |
| 2026-10-25 | Data retention for Claude Fable 5.1 and Claude Haiku 5.5 | every request asked for zero retention (`provider.zdr`) | Fable's gradings and about half of Haiku's (5,517 and 11,313 across all runs; 99% through the maintainers' own Anthropic key) went to Anthropic's endpoint under that key's 30-day safety retention. OpenRouter does not offer zero retention for that route, and Fable 5.1 requires 30-day retention. The maintainer accepted this for public corpora with no student identities, rather than loosen the organisation's zero-retention rule, which also governs studies of private data. Results are unchanged | the retention of the key's route had not been recorded | `client.py` now checks OpenRouter's live zero-retention list and refuses a model with none; `docs/MODELS.md` records each model's retention |
| 2026-10-25 | Length study: Qwen3.8 27B's interval for the change in balanced accuracy | [−0.14, +0.05] | [−0.13, +0.05] | the lower bound, −0.1346, was rounded wrongly | `video/LENGTH.md` |
| 2026-10-25 | Null verdicts on video, length and pushback now print the largest effect they cannot rule out | "adds nothing to a stopwatch"; "NO DETECTABLE EFFECT"; "HOLDS" | the same verdicts, each with its bound (e.g. agreement beyond length up to 0.16-0.38 not ruled out) | a null from a test of limited power is not evidence of no effect (O'Neill 2026). Verdict strings and thresholds are unchanged | `video/README.md`, `video/LENGTH.md`, `feedback-board/PUSHBACK.md`; CHANGE 1 in each script |
| 2026-10-25 | Length study headline | "length does not change detection" | "on longer videos, graders report errors that are not there" (specificity −11 to −30 points for four of five) | the headline led with a null and put the significant effect second | `video/LENGTH.md` |
| 2026-10-25 | Benchmark card, conflict of interest | "a grading product" | names the product | a conflict-of-interest statement should name the interest | `BENCHMARK-CARD.md` |
| 2026-10-24 | Feedback strand of the overall score | halo and "gives away the answer" | halo only; gives-away shown, not scored | the gives-away evaluator was validated on tutoring and ranked the least explicit feedback best | `feedback-board/fb.py` CHANGE 1 |
