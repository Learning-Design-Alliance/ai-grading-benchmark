# Feedback told a wrong grade

**Question.** Does a model's feedback follow the grade it is told, even when that grade contradicts the work? The
board's halo (`feedback-board/fb.py`) cannot tell this apart from a model that reads the teacher's grade as
information about the work, because the grade it shows is the right one. This study tells each model a grade that
disagrees with the work. Pre-registration, floor and changes: the docstring of `study.py`.

**Design.**
- The same 100 short answers as the board, from Mohler, Bunescu & Mihalcea (2011).
- The same feedback prompt (`prompts/feedback-shown.txt`), with each model's board settings.
- The teacher's grade m on 0–5 is replaced by its mirror, 5 − m: a 5 is told as 0, a 1.5 as 3.5.
- Each answer's feedback is paired with the board's feedback written with the true grade told.
- Tone is the validated tone rule (praise minus criticism phrases per 100 words).
- The told-grade slope S is the change in tone per point of told grade, with the work held fixed. Positive means
  tone follows the told grade.
- Intervals are 95%, bootstrapped over answers; BH correction is applied across models.

**Floor.** Passed. A shift of half the model's blind-tone SD across the scale was found in 86.5% of 400 worlds
shaped like the real data, and the null world was flagged in 7.0%.

**Result.** All 22 models: **TONE FOLLOWS THE TOLD GRADE**, every one significant after BH across the 22. "Shift" is S × 5,
the tone change across the whole 0–5 scale, in units of the model's own blind-tone SD.

| model | S, tone per grade point [95%] | shift / blind SD | board halo | verdict |
|---|---|---|---|---|
| Olmo 3.1 32B ¹ | +1.214 [+0.960, +1.468] | +1.84 | +0.278 | TONE FOLLOWS THE TOLD GRADE |
| Gemma 3 27B | +1.165 [+1.025, +1.310] | +2.47 | +0.361 | TONE FOLLOWS THE TOLD GRADE |
| GLM 5.3 | +1.039 [+0.870, +1.221] | +2.31 | +0.027 | TONE FOLLOWS THE TOLD GRADE |
| Qwen3 235B | +0.866 [+0.662, +1.069] | +2.11 | −0.095 | TONE FOLLOWS THE TOLD GRADE |
| GLM 5.3 Flash | +0.722 [+0.597, +0.839] | +1.67 | +0.035 | TONE FOLLOWS THE TOLD GRADE |
| Gemini 3.5 Flash Lite | +0.655 [+0.529, +0.766] | +1.60 | +0.338 | TONE FOLLOWS THE TOLD GRADE |
| DeepSeek V4 Pro | +0.607 [+0.461, +0.734] | +1.32 | +0.033 | TONE FOLLOWS THE TOLD GRADE |
| Gemma 4 31B | +0.607 [+0.470, +0.729] | +1.33 | +0.091 | TONE FOLLOWS THE TOLD GRADE |
| Ministral 8B | +0.602 [+0.455, +0.750] | +1.66 | +0.343 | TONE FOLLOWS THE TOLD GRADE |
| GPT-OSS 20B | +0.595 [+0.451, +0.731] | +1.48 | +0.334 | TONE FOLLOWS THE TOLD GRADE |
| Gemma 4 26B A4B | +0.584 [+0.469, +0.689] | +1.62 | +0.090 | TONE FOLLOWS THE TOLD GRADE |
| Claude Fable 5.1 | +0.508 [+0.415, +0.599] | +1.65 | +0.074 | TONE FOLLOWS THE TOLD GRADE |
| DeepSeek V4.1 Flash | +0.485 [+0.394, +0.577] | +1.27 | +0.083 | TONE FOLLOWS THE TOLD GRADE |
| Gemma 3 4B | +0.467 [+0.348, +0.591] | +1.56 | +0.058 | TONE FOLLOWS THE TOLD GRADE |
| Phi-4 | +0.435 [+0.275, +0.589] | +0.96 | +0.267 | TONE FOLLOWS THE TOLD GRADE |
| DeepSeek V4.1 Flash 1017 | +0.434 [+0.341, +0.530] | +1.26 | +0.071 | TONE FOLLOWS THE TOLD GRADE |
| Claude Haiku 5.5 | +0.414 [+0.310, +0.522] | +1.38 | +0.112 | TONE FOLLOWS THE TOLD GRADE |
| GPT-5.6 Luna | +0.390 [+0.267, +0.524] | +0.94 | +0.095 | TONE FOLLOWS THE TOLD GRADE |
| Claude Opus 5.5 | +0.353 [+0.269, +0.438] | +1.18 | +0.134 | TONE FOLLOWS THE TOLD GRADE |
| GPT-6 Astra | +0.326 [+0.236, +0.425] | +0.90 | +0.182 | TONE FOLLOWS THE TOLD GRADE |
| GPT-5 Mini | +0.252 [+0.158, +0.343] | +0.59 | −0.166 | TONE FOLLOWS THE TOLD GRADE |
| Llama 3.2 3B | +0.215 [+0.062, +0.349] | +0.48 | +0.208 | TONE FOLLOWS THE TOLD GRADE |

¹ Olmo 3.1 32B was added by CHANGE 3, with the maintainer's approval, after the other 21 results had been read. Its
board feedback runs had not been kept, so all three of its arms (blind, true grade told, mirrored grade told) ran the
same day. They used one rented A100 80GB PCIe pod, served exactly as on the board: vLLM v0.32.0, the pinned
revision, bf16, max tokens 4096. bench.py ran on the pod against localhost, and the pod was wiped and deleted
afterwards. Its board-halo column is the feedback board's figure; its slope pairs its own same-day arms. Its work
slope W is 0.913 and S/W is 1.33. Neither is pre-registered with an interval. A descriptive bootstrap on the 98
paired answers gives W 0.95 [0.38, 1.68] and S/W 1.28 [0.72, 3.12]. Recomputing BH across 22 models changed no
other model's verdict or BH flag.

**Reading.**
- Every model's feedback follows the grade it is told when that grade is wrong.
- For 20 of the 22, the interval's lower end is above the floor's planted size, half the model's blind-tone SD
  across the scale. The exceptions are GPT-5 Mini (0.37 SD at its lower end) and Llama 3.2 3B (0.14 SD).
- The pre-registered reading applies: the board's halo is at least partly the told grade itself, not only use of
  information.
- The board's halo and this slope do not rank models the same way. GPT-5 Mini (halo −0.166) and Qwen3 235B
  (−0.095) have negative board halos, and GLM 5.3 (+0.027) one near zero, yet all three follow the wrong grade.
  GLM 5.3 shifts tone by 2.31 blind-tone SDs across the scale.
- The board's halo compares two correlations with the true grade. When the told grade and the work agree, a model
  can follow the told grade without changing that correlation much. A near-zero or negative board halo is
  therefore not evidence that feedback ignores the grade it is told.

**Limits.**
- Tone is a rule-coded measure validated on tutoring replies, with no human reference here.
- The true-grade arm was run up to three days earlier, on 2026-10-24 to 2026-10-26, except Olmo's, which ran the
  same day as its mirrored arm.
- The mirror is an extreme disagreement: a perfect answer is told 0. S says how tone responds across that range,
  not to a small grading error.
- One prompt, one corpus, English.
- Claude Fable 5.1 ran through the maintainers' own Anthropic key with 30-day safety retention (CHANGE 2), because
  OpenRouter no longer lists a zero-retention route for it. Mohler is public.

**Spend.** $4.03 against a $60 cap: $3.85 reported for the 21 hosted models and about $0.18 of GPU time for Olmo
(0.10 h at $1.79/h).

**Files.** `out/floor.json` (the floor), `out/discordant.json` (per-model aggregates: S, interval, p, BH flag,
the blind work slope W, mean tones, verdict). No feedback text is committed.
