# Does rewording the grading prompt change the grades?

Pre-registered in `study.py` (2026-10-26). Output: `out/paraphrase.json`. Spend $83.31 of the $128.38 cap ($8.38 for the first four models; $74.93 for the extension under CHANGE 4, including $0.58 of GPU time for Olmo).

**Question.** The board grades with one prompt; teachers will not use our wording. The 2026-10-23 literature
review ranked prompt paraphrase invariance second among what the board did not measure. Does a rewording that
keeps every instruction change marks more than simply asking again?

**Design.**
- **Prompts:** `prompts/default.txt` and six rewrites (`prompts/paraphrase/p1-p6.txt`), written before any call.
  Each keeps every placeholder and instruction and rewords the system line, the reply line or the scale line.
- **Models:** first Claude Haiku 5.5, GLM 5.3 Flash, GPT-5 Mini and Gemma 4 31B; then (CHANGE 4, under the
  maintainer's rule that every board model runs every task it can) every board model the cap allowed: 20 of 22.
  GPT-6 Astra and Claude Fable 5.1 are left out by the cap (estimates $56 and $137). Each runs on the board's 100
  cases for short answers, code and essays, through its board route (Olmo on our own GPU).
- **Reference:** the default prompt asked five more times per case.
- **Measure:** the share of a case's marks that move by more than 5% of the scale under a paraphrase, minus the
  same share under a plain re-ask (EXCESS). Pooled over the three tasks per model, 300 cases.

**The planted-effect check failed twice before it passed**, all before any call:
- Comparing against one retest per case detected a planted effect only 26% of the time.
- Five re-asks per case raised that to 63%.
- Pooling the tasks, and counting a change only above 5% of the scale, raised it to 96%, with a 2.5% false
  alarm rate.

The changes, and both failed checks, are kept in `out/`.

## Result

| model | grades changed by a re-ask | by a paraphrase | EXCESS [95%] | verdict |
|---|---|---|---|---|
| Gemma 3 4B | 15% | 34% | **+18.9 points** [+15.5, +22.5] | PROMPT-SENSITIVE |
| Gemini 3.5 Flash Lite | 15% | 29% | **+13.6 points** [+10.5, +16.7] | PROMPT-SENSITIVE |
| Ministral 8B | 16% | 29% | **+12.9 points** [+9.7, +16.0] | PROMPT-SENSITIVE |
| Gemma 4 26B A4B | 17% | 22% | **+5.5 points** [+3.1, +7.9] | PROMPT-SENSITIVE |
| Gemma 4 31B | 14% | 18% | **+4.4 points** [+2.4, +6.4] | PROMPT-SENSITIVE |
| Claude Haiku 5.5 | 19% | 23% | **+4.0 points** [+1.3, +6.9] | PROMPT-SENSITIVE |
| GLM 5.3 | 33% | 36% | **+3.7 points** [+0.7, +6.6] | PROMPT-SENSITIVE |
| Gemma 3 27B | 20% | 23% | **+3.3 points** [+0.6, +6.1] | PROMPT-SENSITIVE |
| Qwen3 235B | 17% | 20% | **+3.0 points** [+0.6, +5.2] | PROMPT-SENSITIVE |
| Claude Opus 5.5 | 12% | 15% | **+2.7 points** [+0.6, +4.9] | PROMPT-SENSITIVE |
| GPT-5.6 Luna | 21% | 23% | +2.3 points [-0.1, +4.7] | WITHIN RETEST NOISE |
| Phi-4 | 46% | 48% | +2.0 points [-0.9, +5.1] | WITHIN RETEST NOISE |
| Olmo 3.1 32B | 29% | 30% | +1.4 points [-1.3, +3.9] | WITHIN RETEST NOISE |
| DeepSeek V4 Pro | 49% | 50% | +1.3 points [-1.7, +4.3] | WITHIN RETEST NOISE |
| Llama 3.2 3B | 57% | 58% | +1.1 points [-1.7, +3.9] | WITHIN RETEST NOISE |
| DeepSeek V4.1 Flash | 25% | 26% | +0.9 points [-1.6, +3.4] | WITHIN RETEST NOISE |
| GPT-OSS 20B | 37% | 38% | +0.7 points [-1.8, +3.0] | WITHIN RETEST NOISE |
| GPT-5 Mini | 23% | 24% | +0.1 points [-2.1, +2.2] | WITHIN RETEST NOISE |
| GLM 5.3 Flash | 30% | 30% | +0.0 points [-2.7, +2.8] | WITHIN RETEST NOISE |
| DeepSeek V4.1 Flash (Oct 17 snapshot) | 24% | 24% | -0.4 points [-2.6, +1.9] | WITHIN RETEST NOISE |

(Shares averaged over the three tasks. EXCESS is how many more grades in 100 a paraphrase moves than a re-ask
does, pooled over about 300 cases per model; bold where the interval excludes zero. Cases where a model gave no readable
grade are dropped: 11 of 300 for GLM 5.3, 7 for Gemma 3 4B, and at most 3 for every other model.)

**Reading.**
- **Rewording matters for half the models.** For 10 of 20, a paraphrase that keeps every instruction moves more
  grades than asking again with the same wording: from 2.7 more in 100 (Claude Opus 5.5) to 18.9 more
  (Gemma 3 4B). For the other 10, rewording adds nothing the study can detect.
- **The three most sensitive are small models.** Gemma 3 4B, Gemini 3.5 Flash Lite and Ministral 8B move 13 to
  19 more grades in 100 under a rewording. Size is not the whole story: Llama 3.2 3B, the smallest model here,
  is not affected, and the large models that are affected (Opus 5.5, Qwen3 235B, GLM 5.3) move 2.7 to 3.7 more.
- **Asking again already moves many grades.** A plain re-ask changes 12% (Opus 5.5) to 57% (Llama 3.2 3B) of
  grades by more than 5% of the scale. For every model except Gemma 3 4B, that is more than rewording adds.
- **Steadier under rewording is not the same as better.** Several of the models least affected by wording are
  among the noisiest on a re-ask (DeepSeek V4 Pro 49%, Llama 3.2 3B 57%).
- **Agreement with the experts can move a lot.** Across the seven prompts a model's agreement on one task varies
  by 0.01 to 0.23 QWK (largest: Qwen3 235B on one task), and its mean grade by up to 7.7% of the scale
  (Gemma 3 4B). For the affected models, the board's figures hold for "this prompt or one like it".
- **Chance.** At the planted-effect check's false-alarm rate of 2.5%, about 0.5 of the 20 PROMPT-SENSITIVE calls
  would be expected by chance alone.
- **For the board:** results stand for this prompt; a submitter's own prompt is the bring-your-own-prompt track,
  with prompts-tried recorded.

**Limits.**
- Six paraphrases, all close to the original. A teacher's own rubric wording, or a different structure, may move
  grades more.
- 20 of the 22 board models; GPT-6 Astra and Claude Fable 5.1 are not yet run.
