# Essays: fine-tuned encoder, fine-tuned small language model, or prompted frontier model?

Pre-registered in `study.py` (2026-10-26), before any call or training run. Output: `out/essays-finetune.json`;
the test split is in `out/split.json` (case ids only). Floor: the paired comparison on 1,000 essays separates a
grader at QWK 0.84 from one at 0.80 in 93% of simulated draws, with a 4.5% false-positive rate (`out/floor.json`).

**Question (the maintainer's).** DeBERTa fine-tuned on ASAP 2.0 scores the board's essays at QWK 0.81, above every
prompted model and above the two expert raters' own agreement (0.745). Can a frontier model, or a fine-tuned small
language model, match it?

**Design, in short.** ASAP 2.0 (24,728 essays, 7 prompts, one adjudicated score 1-6):
- **Test:** 1,000 held-out essays.
- **Same-prompt:** fine-tuned models trained on the other 23,628 essays.
- **Unseen-prompt:** for each prompt in turn, trained on 5,000 essays from the other six, then scored on that
  prompt's test essays.
- **Arms:**
  - DeBERTa-v3-base (the board's recipe);
  - Qwen3 4B Instruct, LoRA plus a regression head (Apache 2.0), on a rented A100;
  - Claude Haiku 5.5, GLM 5.3 Flash and Claude Opus 5.5 (Opus on 500 essays), prompted zero-shot and again with
    six marked example essays from the same prompt.
- **Board checks:** on the board's 100 essays, for the fine-tuned models.
- **Fairness:** for every arm.
- **Spend:** API $32, GPU $7.

**The vendor fine-tune was not run.** The maintainer chose to test one, accepting that a vendor fine-tune cannot
be zero-retention. OpenAI refused the job on 2026-10-26: it is winding down its fine-tuning platform (closed to
new users from 7 May 2026, to inactive ones from 2 July, to everyone on 6 January 2027) and gives no reason.
Google moved tuning out of its Gemini developer API in 2025; it remains on its enterprise cloud. We would not
recommend a hosted fine-tune for student work anyway: the training data and the tuned model are stored by the
vendor, which is not zero retention, and the service can be withdrawn under you.

## Results

| arm | QWK on 1,000 test essays [95%] |
|---|---|
| DeBERTa, same prompts | **0.804** [0.781, 0.827] |
| Qwen3 4B LoRA, same prompts | **0.798** [0.774, 0.820] |
| Qwen3 4B LoRA, unseen prompt | 0.755 [0.728, 0.782] |
| DeBERTa, unseen prompt | 0.741 [0.709, 0.770] |
| Claude Opus 5.5, six marked examples (500 essays) | 0.708 [0.665, 0.747] |
| GLM 5.3 Flash, six marked examples | 0.654 [0.616, 0.690] |
| Claude Opus 5.5, zero-shot (500 essays) | 0.625 [0.577, 0.670] |
| Claude Haiku 5.5, six marked examples | 0.589 [0.547, 0.626] |
| GLM 5.3 Flash, zero-shot | 0.564 [0.519, 0.604] |
| Claude Haiku 5.5, zero-shot | 0.514 [0.470, 0.556] |

Pre-registered comparisons, paired by essay:
- **C1. A fine-tuned small language model matches the encoder:** Qwen minus DeBERTa -0.006 [-0.023, +0.011], NO
  DIFFERENCE DETECTED.
- **C2. The best prompted arm does not:** Opus with examples minus DeBERTa -0.095 [-0.130, -0.059]; DeBERTa exceeds
  it.
- **C3. Six marked examples help every prompted model:** +0.075 (Haiku), +0.091 (GLM), +0.084 (Opus), each interval
  above 0.
- **C4. On an unseen prompt the two fine-tuned models tie:** Qwen minus DeBERTa +0.014 [-0.012, +0.040].
- **C5. Even on an unseen prompt, both beat prompting.** Against Opus zero-shot, DeBERTa exceeds it by 0.092 and Qwen
  by 0.120.
- **C6. An unseen prompt costs the fine-tuned models a little:** -0.063 for DeBERTa, -0.043 for Qwen. Both still
  stay near the expert raters' agreement (0.745): Qwen above it (0.755), DeBERTa just below (0.741), both
  intervals containing it.

**The board's checks on the fine-tuned models** (the board's 100 essays):

| model | QWK | polite request | forged override | vouched | padding | blank or junk credited |
|---|---|---|---|---|---|---|
| DeBERTa | 0.78 | +0.3% | +0.6% | +0.5% | +1.8% | 8% |
| Qwen3 4B LoRA | 0.83 | -4.5% | -4.7% | -5.5% | -3.3% | **29%** |

- **Neither can be gamed by a note.** The fine-tuned Qwen marks essays slightly lower when anything is
  appended: it reads a note as weaker writing, not as an instruction.
- **Both credit blank or junk answers, so both carry the board's flag.** A fine-tuned scorer has never seen a
  blank essay, and nothing tells it the lowest mark is right. Qwen gave above the minimum to 29% of them. A
  deployment would need a separate check for empty or non-attempt work.

**Fairness** (pre-registered; signed residuals against the adjudicated score). Each figure is the arm's mark
minus the human mark for the group, minus the same for everyone else, in marks on the 1-6 scale; only intervals
excluding 0 are listed.
- **English learners** (140 test essays):
  - GLM 5.3 Flash marks them *lower* than the humans did, relative to other students: -0.19 zero-shot, -0.15 with
    examples.
  - Haiku marks them *higher*: +0.19, +0.17.
  - The fine-tuned models on an unseen prompt mark them higher too: +0.15 (DeBERTa), +0.18 (Qwen).
- **Students identified with a disability:** GLM with examples -0.16; Qwen on an unseen prompt +0.15.
- **Economically disadvantaged students:** Haiku +0.13 (zero-shot) and +0.14 (with examples).
- **Hispanic or Latino students, on an unseen prompt:** DeBERTa +0.15, Qwen +0.13.
- **Black or African American students:** DeBERTa on the same prompts -0.10 [-0.19, -0.00], at the edge.
- **Opus** showed no difference in any group, on 500 essays.

These are 3-4% of the scale, in both directions. A positive figure narrows a gap the human raters had; a negative
one widens it. Same-prompt fine-tuning, which copies the raters most closely, departs from them least. The
pre-registered label for these was "WIDENS"; since it ignores the sign, each is reported with its direction instead.

## What it means

- **Fine-tuning a small model works, and it doesn't need to be large.** A 184M-parameter encoder and a
  4B-parameter language model reach the same agreement, about 0.80, above the experts' own agreement. They
  stay near it on a prompt they never saw.
- **Prompting a frontier model does not get there**, even the best one. Six marked examples close nearly half
  the gap (Opus: 0.625 to 0.708, against DeBERTa's 0.804), and they cost a teacher only six marked scripts.
- **The cost is elsewhere.** Fine-tuned scorers give no feedback, need thousands of marked essays, and credit
  blank work unless something else catches it.
- **Matching the raters more closely means copying their habits.** That includes rewarding length (see
  `../analyses/README.md`).

**Limits.**
- One corpus (US secondary persuasive and source-based essays) and one adjudicated score, so there is no ceiling
  on the test set.
- One recipe per fine-tuned model, untuned.
- ASAP 2.0 has been public since 2024; if the prompted models trained on it, that would favour them, and they
  still trail.

## CHANGE 1: a larger open model, Gemma 4 26B A4B, and the full board battery (2026-10-27)

Pre-registered as CHANGE 1 in `study.py`, after every result above had been read and before Gemma was trained or
scored. Output: `out/essays-finetune-change1.json` and `out/board_rows.json`; the results above are unchanged.

**Question (the maintainer's).** Does fine-tuning a larger, capable open model do better, especially on a prompt it
never saw? The second request was for the fine-tuned scorers' full leaderboard-battery results, so they can be
ranked beside prompted models and classic baselines.

**Design, in short.**
- **Model:** Gemma 4 26B A4B instruction-tuned (`google/gemma-4-26B-A4B-it`, pinned revision, Apache 2.0, not
  gated): a mixture of experts with 128 experts per layer, 8 active per token.
- **Recipe:** Qwen's: a regression head on the last token, LoRA r 16, lr 1e-4, one epoch, batch 16, 1,024 tokens,
  bf16, the same splits and seed.
- **One stated deviation:** the experts are stored as fused 3-D weights, which PEFT cannot adapt. LoRA therefore
  sits on attention and each layer's dense MLP (18.6M trainable parameters), and the experts stay frozen.
- **Hardware:** bf16 fitted on one A100 80GB (peak 50.4 GiB in training, 51.9 GiB over the folds), so no fallback
  to 4-bit was needed.
- **Retraining:** DeBERTa and Qwen were retrained on the same recipe for the battery, because their weights had
  been deleted with the first pod.
- **Spend:** GPU about $10 (7.17 h on one A100 at $1.39/h) of a $20 cap; no API spend.
- **One interruption:** after the same-prompt run, the first unseen-prompt fold ran out of memory while
  loading, because the previous model had not been freed. This was a code fault, not a precision limit. It was
  fixed, and the folds ran at the same micro-batch, before any Gemma prediction was read.

| arm | QWK on 1,000 test essays [95%] |
|---|---|
| DeBERTa, same prompts (above) | 0.804 [0.781, 0.827] |
| Qwen3 4B LoRA, same prompts (above) | 0.798 [0.774, 0.820] |
| **Gemma 4 26B A4B LoRA, same prompts** | **0.763** [0.737, 0.788] |
| Qwen3 4B LoRA, unseen prompt (above) | 0.755 [0.728, 0.782] |
| DeBERTa, unseen prompt (above) | 0.741 [0.709, 0.770] |
| **Gemma 4 26B A4B LoRA, unseen prompt** | **0.607** [0.565, 0.648] |

Pre-registered comparisons, paired by essay. The study's floor applies: these are paired comparisons on the same
1,000 essays, which it showed can separate 0.84 from 0.80.
- **C7. On the same prompts, the larger model does worse than the encoder.** Gemma minus DeBERTa is -0.041
  [-0.063, -0.019]: DeBERTa EXCEEDS Gemma.
- **C8. It also does worse than the 4B model.** Gemma minus Qwen is -0.035 [-0.054, -0.016]: Qwen EXCEEDS Gemma.
- **C9. On an unseen prompt, it does much worse than both.** Gemma minus DeBERTa is -0.134 [-0.170, -0.100], and
  Gemma minus Qwen is -0.148 [-0.186, -0.114]. Both exceed Gemma.
- **C10. An unseen prompt costs Gemma 0.156** [0.121, 0.193] (same minus unseen). That is about 2.5 times
  what it cost DeBERTa (0.063), and 3.7 times what it cost Qwen (0.043). It leaves Gemma well below the expert raters'
  agreement (0.745), and below Claude Opus 5.5 with six marked examples (0.708, on 500 essays, not paired here).

**So the answer is no: in this recipe, the larger model is worse, and worst where the maintainer hoped it would
help.** One recipe was tried, untuned, with its expert layers frozen. A different learning rate, more epochs, or
adapting the experts might change this, and none of them was tested. What the result rules out is that scale
alone, under the recipe that suited a 4B model, buys agreement or transfer.

**Reproduction.** The retrained models land within the pre-registered 0.02 of the originals: both REPRODUCED.
- **DeBERTa:** 0.801 [0.777, 0.824] against 0.804, a difference of -0.003 [-0.009, +0.003].
- **Qwen:** 0.811 [0.787, 0.833] against 0.798, a difference of +0.013 [-0.001, +0.026].

The software stack was newer than the first run's (torch 2.13, transformers 5.19, peft 0.21.2).

**Blank answers are not stable across retraining.** The study's own check scores the five null answers on all 100
board essays (500 gradings), and the retrained scorers did not match the originals:

| scorer | original | retrained or new |
|---|---|---|
| DeBERTa | 42 of 500 credited | 156 of 500 |
| Qwen | 144 of 500 | 100 of 500 |
| Gemma | — | 198 of 500 |

The recipe and seed were the same, and agreement on real essays held. What a fine-tuned scorer does with a
blank essay is an accident of training, not a property of the method. Every one of them carries the board's flag.

Gemma's study probes, as a share of the 1-6 scale on the board's 100 essays:
- polite request +2.0% [+0.7%, +3.2%];
- forged override +2.7% [+1.5%, +3.9%];
- vouched +0.4% [-0.8%, +1.5%];
- padding +2.0% [+0.9%, +3.0%].

Unlike Qwen, whose marks fell when anything was appended, Gemma's rise slightly, though all stay under the
board's 5% bar.

### The fine-tuned scorers on the full board battery

The board's 100 essays were scored under exactly the leaderboard battery, built as `baselines/baselines.py`
builds it. That is 813 gradings per scorer. Each mark was rounded to a whole score first, as the board does.
These rows are in `out/board_rows.json`, with track "fine-tuned". Gaming, blicket and surface are signed changes
as a share of the scale.

| scorer | QWK on the board's 100 [95%] | gaming (max of request, forged) | blicket | surface | blank or junk credited |
|---|---|---|---|---|---|
| fine-tuned: DeBERTa-v3-base | 0.784 [0.691, 0.849] | +0.0% [-0.6%, +0.6%] | -4.7% [-6.3%, -2.9%] | +0.0% [+0.0%, +0.0%] | 11 of 35 (31%) |
| fine-tuned: Qwen3 4B LoRA | 0.798 [0.713, 0.863] | -2.8% [-4.2%, -1.6%] | -1.1% [-2.0%, -0.2%] | -2.0% [-3.4%, -0.9%] | 7 of 35 (20%) |
| fine-tuned: Gemma 4 26B A4B LoRA | 0.797 [0.711, 0.859] | +1.6% [-0.4%, +3.4%] | -4.5% [-6.3%, -2.7%] | -0.9% [-2.5%, +0.7%] | 14 of 35 (40%) |

How to read the rows:
- **By construction**, each row states that retest agreement is 1 and the attainment-label effect is 0. A scorer
  that never sees the label, and scores each distinct input once, cannot do otherwise; these are not measurements.
- **The board's decision measure is empty for essays**, because ASAP 2.0 has no pass mark on the board.
- **The battery runs null answers on seven essays (35 gradings).** The study's 500-grading check above is the
  firmer figure.
- **All three resist gaming.** None gains more than 2% of the scale from a polite request or a forged
  override. Qwen's marks fall (-2.8%), and Gemma's rise slightly (+1.6%, interval up to +3.4%).
- **All three mark blicket essays lower.** These are essays with nonsense words swapped in.
- **On the board's 100 essays, the three scorers' agreement intervals overlap almost entirely.** The 1,000 test
  essays above separate them.

**Limits.**
- One recipe per model, untuned, with Gemma's expert layers frozen.
- One corpus, and no ceiling on the test set.
- The retrained DeBERTa and Qwen ran on a newer software stack than the originals.
- The blank-answer instability above was seen in three models, one retrain each.
- Fairness, which is descriptive: on an unseen prompt, Gemma marks some groups differently from the human raters,
  relative to other students:
  - English learners +0.25 marks [+0.10, +0.41];
  - students identified with a disability +0.24 [+0.07, +0.40];
  - Hispanic or Latino students +0.17 [+0.05, +0.29];
  - Asian or Pacific Islander students -0.25 [-0.47, -0.04] (56 essays).

  On the same prompts it showed no gap whose interval excluded 0.
