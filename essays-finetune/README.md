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
  stay at or above the expert raters' agreement (0.745).

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
- **Prompting a frontier model does not get there**, even the best one. Six marked examples close about a third
  of the gap, and they cost a teacher only six marked scripts.
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
