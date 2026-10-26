# Does rewording the grading prompt change the marks?

Pre-registered in `study.py` (2026-10-26). Output: `out/paraphrase.json`. Spend $8.38.

**Question.** The board grades with one prompt; teachers will not use our wording. The 2026-10-23 literature
review ranked prompt paraphrase invariance second among what the board did not measure. Does a rewording that
keeps every instruction change marks more than simply asking again?

**Design.**
- **Prompts:** `prompts/default.txt` and six rewrites (`prompts/paraphrase/p1-p6.txt`), written before any call.
  Each keeps every placeholder and instruction and rewords the system line, the reply line or the scale line.
- **Models:** Claude Haiku 5.5, GLM 5.3 Flash, GPT-5 Mini and Gemma 4 31B, on the board's 100 cases for short
  answers, code and essays.
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

| model | marks changed by a re-ask | by a paraphrase | EXCESS [95%] | verdict |
|---|---|---|---|---|
| Claude Haiku 5.5 | 19% | 23% | **+4.0 points** [+1.3, +6.9] | PROMPT-SENSITIVE |
| Gemma 4 31B | 14% | 18% | **+4.4 points** [+2.4, +6.4] | PROMPT-SENSITIVE |
| GLM 5.3 Flash | 30% | 30% | +0.0 [-2.7, +2.8] | WITHIN RETEST NOISE |
| GPT-5 Mini | 23% | 24% | +0.1 [-2.1, +2.2] | WITHIN RETEST NOISE |

(Shares averaged over the three tasks.)

**Reading.**
- **Rewording matters, but less than chance does.**
  - For two of four models, a paraphrase moves about 4 more cases in 100 than asking again would.
  - For the other two, rewording adds nothing detectable: at most 2-3 points.
  - For every model, most of the movement is already there when the same prompt is asked twice. A re-ask
    changes 14-30% of marks by more than 5% of the scale.
- **The ranking does not hinge on our wording.**
  - Across the seven prompts, a model's agreement with the experts varies by 0.03 to 0.10 QWK on a task. That
    is within the board's own intervals on most tasks.
  - The mean mark moves by at most 3.6% of the scale under any paraphrase.
- **Which models are steadier is not which are better.** GLM 5.3 Flash is the least sensitive to wording, and
  also the noisiest on a plain re-ask.
- **For the board:** results stand for "this prompt or one like it". The card says so; a submitter's own prompt
  is the bring-your-own-prompt track, with prompts-tried recorded.

**Limits.**
- Six paraphrases, all close to the original. A teacher's own rubric wording, or a different structure, may move
  marks more.
- Four models.
