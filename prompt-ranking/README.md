# Does rewording the grading prompt reorder the models?

Pre-registered in `study.py` (2026-10-27) before any result was read. Output: `out/ranking.json`; the floor is
`out/floor.json`. No calls: a reanalysis of the rewording study's runs (`paraphrase/`). Suggested by the
literature review (analysis 3; Mizrahi et al. 2024, Sclar et al. 2024).

**Question.** The rewording study found 11 of the 22 models PROMPT-SENSITIVE: rewording moves their own marks
more than asking again. Would the *order* of the models survive a different, equally reasonable wording?

**Design.**
- **Rankings:** the 22 models ordered by agreement with the human raters (QWK, the mean over short answers, code
  and essays), once under each of the seven prompts (the default and six rewrites), and once under each of six
  re-asks of the default prompt.
- **Cases:** the 270 cases every model graded under all 12 conditions (96 short answers, 84 programs, 90 essays
  of the board's 100 each).
- **Measure:** D = the mean rank correlation (Spearman) between pairs of prompt rankings, minus the same between
  pairs of re-ask rankings. Negative means rewording reorders the models more than asking again. The interval
  resamples cases within each task (2,000 draws).
- **Floor:** with 22 simulated graders on the board's real cases, a planted model-by-wording interaction was
  called in 100% of worlds and a null one in 0% (pass: at least 80% and at most 5%).

## Result: RANKING WITHIN RE-ASK NOISE, at the edge

| | mean rank correlation |
|---|---|
| between the seven prompts | 0.945 |
| between the six re-asks | 0.964 |
| D (prompts minus re-asks) | **−0.019** [−0.069, +0.00001] |

- **The interval reaches 0 by a hair.** The pre-registered verdict is RANKING WITHIN RE-ASK NOISE, but the
  rankings across wordings agree slightly less than across re-asks, and a reordering of up to 0.069 in mean
  rank correlation is not ruled out.
- **The top two hold.** Claude Opus 5.5 is first under five of the seven prompts and Claude Fable 5.1 under the
  other two; neither leaves the top two. The bottom three (GPT-OSS 20B, Llama 3.2 3B, Gemma 3 4B) stay in the
  bottom three under every prompt.
- **The middle moves, but mostly as much as it does on a re-ask.** Claude Haiku 5.5 ranks 4th under the default
  prompt and 9th to 13th under every rewrite. Its rank also ranges from 4th to 11th over the six re-asks of the
  default prompt, so the 4th was itself a favorable draw. The clearer wording effects are Gemini 3.5 Flash Lite
  (5th to 11th over prompts, 10th to 11th over re-asks) and Ministral 8B (11th to 18th against 15th to 18th),
  both PROMPT-SENSITIVE in the rewording study.
- **Rank intervals.** Drawing one of the seven prompts at random alongside the case bootstrap widens 13 of the 22
  models' 95% rank intervals (`out/ranking.json`, `rank_ci95_any_prompt` against `rank_ci95_default_prompt`).

**Reading.** At the level a buyer reads a leaderboard (who is near the top, who is near the bottom), the
ranking was not shown to depend on our wording more than on a re-ask; a small reordering is not ruled out. Positions 3 to 19 are not stable to within a few places under either a
rewording or a re-ask, so neighboring ranks in the middle of the board should not be read as a difference.

**Limits.** This is the agreement ranking only (the rewording runs hold base gradings, not the probes the
overall score needs). Seven wordings, all written by the benchmark. 270 cases. The default prompt's base grading
belongs to both sets.

CHANGE 1 (after the result was read; descriptive only): each model's rank range over the six re-asks was added
beside its range over the prompts.
