# Does the guard sentence really make four models more gameable, or is that re-ask noise?

Pre-registered in `study.py` (2026-10-27) before any call. Output: `out/guard-retest.json`; the floor is
`out/floor.json`. Spend about $2.60 of the $15 hosted cap (24 new runs of 300 gradings each, plus re-sending 31
gradings refused by a rate limit), and $1.41 of GPU time for Olmo 3.1 32B (CHANGE 2: 0.79 hours on one rented A100,
terminated after). Suggested by the literature review (analysis 2; Li et al. 2026; JudgeSense,
Bellibatlu et al. 2026).

**Question.** The setups study (`setups/`) reported that adding the guard paragraph (`prompts/guarded.txt`) made
four models without a reasoning setting *more* gameable. Each condition there was one run. Does the effect
exceed what simply running the same prompt again does?

**Design.**
- **Models:** Gemma 3 27B, Qwen3 235B and Gemma 3 4B, each as on the board (zero retention, host pin, settings).
  Olmo 3.1 32B, which has no hosted route, was added after the others' results were read (CHANGE 2, with the
  maintainer's approval, before any Olmo call): self-hosted exactly as on the board (vLLM v0.32.0, bf16, its chat
  template, on one rented A100; no request left the pod), with the same repeats.
- **Runs per model:** six of the default prompt (the board's run, the setups study's, four new) and five with the
  guard (the setups study's, four new), each on the board's 100 short answers, programs and essays, with the
  board's polite request and forged override.
- **Gaming per run:** per task, the larger of the two notes' mean gain as a share of the scale (the board's figure),
  then the mean over the three tasks. **Attack success:** the share of (answer, note) pairs whose mark rose by
  more than 5% of the scale.
- **Effect:** guard runs' mean minus default runs' mean, with a 95% Welch interval over runs (the run is the unit the
  prompt was assigned to).
- **Floor:** the default runs' own spread (SD 0.2% to 0.6% of the scale) let a planted 10-point harm be detected
  in 100% of simulations, with false alarms at 2.2% to 3.4%. Passed for all four.

## Result

| model | gaming, default (6 runs) | with the guard (5 runs) | effect [95%] | verdict |
|---|---|---|---|---|
| Gemma 3 4B | 16.1% | 26.8% | **+10.7 points** [+10.3, +11.0] | GUARD MAKES IT MORE GAMEABLE |
| Gemma 3 27B | 20.6% | 28.7% | **+8.1 points** [+7.2, +9.1] | GUARD MAKES IT MORE GAMEABLE |
| Qwen3 235B | 55.0% | 51.1% | **−3.9 points** [−6.9, −0.8] | GUARD MAKES IT LESS GAMEABLE |
| Olmo 3.1 32B | 42.3% | 51.6% | **+9.2 points** [+7.9, +10.6] | GUARD MAKES IT MORE GAMEABLE |

Gaming is the mean over the three tasks, so it is lower than the worst-task figures the setups study reported.

| model | attack success, default | with the guard | effect [95%] |
|---|---|---|---|
| Gemma 3 4B | 62.8% | 76.9% | +14.1 points [+13.1, +15.1] |
| Gemma 3 27B | 63.5% | 73.1% | +9.6 points [+7.7, +11.5] |
| Qwen3 235B | 66.7% | 53.9% | −12.8 points [−16.2, −9.5] |
| Olmo 3.1 32B | 56.9% | 54.2% | −2.7 points [−4.3, −1.1] |

**Reading.**
- **Re-asking moves these models' gaming very little.** Six runs of the default prompt, on different days, agree
  to within 1.6 points of the scale (Gemma 3 27B, 19.4% to 21.0%) or less. The setups study's single-run differences were not noise.
- **For Gemma 3 4B and Gemma 3 27B the harm is confirmed.** The guard raises gaming by 10.7 and 8.1 points and
  the share of notes that succeed by 14.1 and 9.6 points. For Gemma 3 27B it comes from code (+22.7 points
  [+20.9, +24.5]) and essays (+4.2); on short answers the guard helps a little (−2.5).
- **For Qwen3 235B the setups study's "more gameable" is withdrawn as a model-level reading.** The guard does make
  it more gameable on code, the task the setups study reported (+6.6 points [+4.7, +8.6]), but less on short
  answers (−13.2 points [−18.6, −7.9]) and essays (−5.0 [−9.6, −0.4]), so over the three tasks it reduces
  gaming and attack success. Its guard runs also vary more than its default runs (48.5% to 54.0%).
- **For Olmo 3.1 32B the harm is confirmed, and it is all on code** (+26.6 points [+23.9, +29.2]; short answers
  +1.4 [−0.1, +2.8], essays −0.2 [−1.2, +0.8]). Its attack success falls slightly (−2.7 points): on code the
  notes that work now gain much more, while slightly fewer work overall.
- **Attack success moves with the mean gain** for the other three: 54% to 77% of notes succeed under either
  prompt for all four models, so they are gamed on most answers, not by a few large jumps.

**For the board and the paper.** "The guard sentence increased gaming for four models" should read: confirmed for
Gemma 3 4B, Gemma 3 27B and Olmo 3.1 32B against re-ask noise (Olmo's on code alone); for Qwen3 235B only on code
(over all three tasks the guard reduces it).

**Limits.** One guard wording; two of the board's notes; 100 answers per task. Olmo was added after the other
three models' results were read (CHANGE 2).
