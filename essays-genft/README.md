# Essays: generative fine-tuning of Gemma 4 26B A4B, against its own base on the same server

Pre-registered in `study.py` (2026-10-27), before any training run or model call; four numbered CHANGES, all made
before any grading was read. Outputs:
- `out/essays-genft.json`: every measure, arm figure and check;
- `out/board_rows.json`: leaderboard-format rows, track "fine-tuned (generative)", with the base control rows beside
  them;
- `out/submissions/`: both arms' battery marks in the submission format (marks only, no text);
- `out/floor.json`: the floor (the first, failed run is kept as `out/floor-failed-1.json`);
- `out/split-check.json`: the overlap check.

**Question (the maintainer's, 2026-10-27).** essays-finetune fine-tuned Gemma 4 26B A4B with a regression head, so
that model can only output a number. If the same model is instead fine-tuned *generatively*, so that it still writes
its reply (a grade, then a reason, in the board's format), does its essay grading improve? And what does that cost on
everything else the board measures?

## Design, in short

- **Model and arms.**
  - **BASE:** `google/gemma-4-26B-A4B-it` at a pinned revision, served on our own pod.
  - **GENFT:** the same weights fine-tuned, merged, and served on the same pod with the same vLLM v0.32.0, bf16 and
    settings.
  - **FOLD:** the unseen-prompt check, one fine-tune per ASAP 2.0 prompt that never saw that prompt.
  - **HOSTED:** the board's existing hosted Gemma row, shown beside the others. It is a different setup (host,
    precision, date), so no verdict rests on it.
- **Training data.** essays-finetune's TRAIN split: 23,628 ASAP 2.0 essays.
  - It never includes the 1,000 TEST essays or the board's 100 essays.
  - The overlap check found no shared id and no TRAIN essay whose text, whitespace collapsed and case folded, equals a
    TEST or board essay.
  - The recomputed split equals the committed one.
- **Input and target.**
  - The input is the board's default prompt, exactly as the server renders it. The token ids are taken from vLLM's
    own `/tokenize`; CHANGE 3 explains why.
  - The target is the reply format up to and including the grade: the tokens of `{"score": N`, with the loss on those
    tokens only.
  - ASAP 2.0 has no human-written reasons, and none was invented. **So the model was taught the grade and nothing
    else. Every reason it writes after the grade is its own, not taught.** It still writes one: all 1,000 TEST replies
    carry a reason, of 32 words on average (31 for the base).
- **Recipe.** essays-finetune CHANGE 1's recipe:
  - LoRA r 16 on attention and the dense MLP (18,585,600 parameters), with the experts frozen;
  - lr 1e-4, one epoch, batch 16, bf16;
  - micro-batch 1, so there is no padding, and up to 6,144 tokens (the prompt carries the task and materials). No
    essay was too long.
  - Training took 10.0 h on one A100 80GB (49.3M tokens, peak 52.4 GiB).
- **Merge and its checks.**
  - The adapter was merged into copies of the original weight files.
  - The served merged model gave the same temperature-0 grade as the in-process model on 100 of 100 TRAIN essays.
  - The template check gave the same token ids on 20 of 20 essays.
- **Battery, identical for both arms, on the same pod on the same day.** bench.py ran against localhost with the
  board's settings for this model (temperature unset, max_tokens 4096):
  - the leaderboard battery on short answers, code and essays;
  - maths working (800 versions);
  - feedback (three prompts) and pushback;
  - the 1,000 TEST essays.
- **Not run:** the feedback board's "gives away the answer" column. It needs a hosted evaluator, and this study made
  no API calls.

## Results: fine-tuned minus base

Each figure is GENFT minus BASE, paired by case, with a 95% bootstrap interval (2,000 draws). A positive figure means
the fine-tuned model is higher.

| measure | base | fine-tuned | difference [95%] | verdict |
|---|---|---|---|---|
| M1 essay QWK, 1,000 TEST essays | 0.620 | 0.781 | **+0.162** [+0.129, +0.198] | UNMEASURED (floor failed; see below) |
| M2 essay QWK, board's 100 | 0.721 | 0.753 | +0.032 [-0.064, +0.129] | NO DIFFERENCE DETECTED |
| M3 short-answer QWK (board's 100) | 0.640 | 0.442 | **-0.198** [-0.278, -0.115] | FINE-TUNED AGREES LESS ON SHORT ANSWERS |
| M4 code QWK (board's 100) | 0.465 | 0.592 | +0.127 [+0.051, +0.204] | UNMEASURED |
| M5 gaming gain, short answers (share of scale) | 3.9% | 11.9% | **+8.0%** [+4.2%, +11.5%] | FINE-TUNED IS MORE GAMEABLE |
| M5 gaming gain, code | 13.4% | 25.3% | +11.9% [+3.1%, +21.3%] | UNMEASURED |
| M5 gaming gain, essays | 48.4% | 8.2% | **-40.2%** [-46.4%, -33.6%] | FINE-TUNED IS LESS GAMEABLE |
| M6 blank answers credited | 0 of 180 | 0 of 194 | 0 | NO DIFFERENCE DETECTED |
| M7 feedback halo | +0.11 | +0.24 | +0.13 [-0.07, +0.34] | UNMEASURED (descriptive in any case) |
| M8 pushback yield (share of 0-5) | +7.2% | +5.1% | -2.1% [-6.0%, +1.9%] | UNMEASURED |
| M9 working effect (of 4 points) | 1.77 | 1.45 | **-0.33** [-0.41, -0.25] | FINE-TUNED READS THE WORKING LESS |
| M10 reply parse rate | 99.5% | 99.8% | +0.31 pp [+0.12, +0.52] | FINE-TUNED PARSES MORE OFTEN |

Where the reference points stand:
- **The TEST essays.** The experts' published agreement is 0.745. The length baseline (log words, fitted on TRAIN)
  reaches 0.652 [0.612, 0.688].
  - Base: 0.620 [0.579, 0.658], below length alone.
  - Fine-tuned: 0.781 [0.754, 0.806], above both.
- **Short answers, as a share of the human ceiling.** Base 112%, fine-tuned 77%.
- **Code, as a share of the human ceiling.** Base 57%, fine-tuned 73%.

**Against the regression heads of essays-finetune** (M12, the same 1,000 TEST essays, paired; essays-finetune's
floor applies):
- **Gemma 4 26B A4B with a regression head (0.763):** +0.018 [-0.009, +0.045], NO DIFFERENCE DETECTED.
- **Qwen3 4B LoRA (0.798):** -0.017 [-0.041, +0.008], NO DIFFERENCE DETECTED.
- **DeBERTa (0.804):** -0.023 [-0.046, -0.001]. Verdict B EXCEEDS A: DeBERTa exceeds the fine-tuned model, by
  little.

So writing its reply cost the fine-tuned model nothing in essay agreement against the regression head on the same
model, and it lands with the two best scorers.

**Unseen prompt (M11):** the seven fold models are training on the pod; this section is filled in when they finish.

## Reading

- **Essay grading improves a lot, and the gain is not in doubt in size, only in its pre-registered verdict.**
  - The fine-tuned model agrees with the experts at 0.78 on 1,000 held-out essays, against the base's 0.62.
  - The interval for the gain, +0.13 to +0.20, lies far from 0.
  - The verdict reads UNMEASURED by the pre-registered rule. M1's floor asked the instrument to detect a change of
    0.04 in both directions in 80% of worlds; it detected a rise 81% of the time and a fall 72%.
  - The observed gain is four times the planted one, so the figure stands as descriptive.
  - On the board's own 100 essays the same gain is too small for 100 cases to resolve (M2).
- **It stops being gamed on essays.**
  - The base model gained 48% of the scale from a polite request or a forged override on essays (the hosted row
    shows 49%).
  - The fine-tuned model gains 8%: still above the board's 5% bar, so it still carries the flag.
- **It costs short answers, and with them the board's other strengths.**
  - Agreement on short answers falls from 112% to 77% of the human ceiling.
  - Gaming on short answers rises from 4% to 12% of the scale.
  - It reads the maths working less. It gives a lucky solution (wrong working, right answer) 1.94 of 4 against
    1.36, and a wrong one 1.97 against 1.32. It still reads the working by the board's bar.
- **Code, the other untrained task, moved up** (+0.13 QWK, gaming +12%), but its floor failed, so both figures are
  descriptive.
- **Consistency fell** (descriptive, not a pre-registered measure). On essays, the base's retest agreement was 0.966
  and the fine-tuned model's 0.736. At the board's temperature of 1.0 the fine-tuned model samples a grade from a
  spread it learned, where the base nearly always gave the same one. Short answers fell from 0.990 to 0.904, code
  from 0.967 to 0.841.
- **Unchanged or unresolved.**
  - Neither arm credits a blank answer.
  - Both arms yield to pushback by the board's verdict: base +7.2% [+4.2%, +10.2%], fine-tuned +5.1% [+2.0%, +8.3%].
    The difference is not resolved: M8's floor failed.
  - The fine-tuned feedback's halo is +0.24 [+0.07, +0.42], against the base's +0.11 [-0.02, +0.23]. The difference
    is not resolved either (M7's floor failed), and tone is rule-coded in any case.

**The self-hosted base against the hosted row** (a different setup; descriptive):
- **Agreement:** close on every task. Essays 0.721 against 0.727, short answers 0.640 against 0.638, code 0.465
  against 0.487.
- **Gaming:** close as well. Essays 48% against 49%, short answers 4% against 3%.
- **Pushback:** the one difference. The self-hosted base YIELDS TO PUSHBACK (+7.2%) where the hosted row HOLDS
  (+2.2%, interval up to +5.1%).

That is why the controlled comparison matters: host and serving differences move some board figures by themselves.

## The floor

Pre-registered; every measure was planted UP, DOWN and NULL in 200 worlds built from the hosted model's own runs.
- **The first run failed for seven measures.** CHANGE 4 then fixed three design faults:
  - plants that the scale's ends or the experts' marks cut short;
  - 400 bootstrap draws against the analysis's 2,000;
  - M1's reference treated as error-free.

  The planted sizes and the bars were not changed. The first run is kept.
- **Passes:**
  - M2, M3 (a QWK change of about 0.11-0.21 on 100 cases);
  - M5 on short answers and essays (5% of the scale);
  - M6, M9 (0.5 of 4) and M10 (3 points).
- **Fails, so the verdict reads UNMEASURED:**
  - M1: a 0.04 change on 1,000 essays was seen 81% (up) and 72% (down) of the time;
  - M4: false alarm 8%;
  - M5 on code: DOWN seen 41%;
  - M7 and M8: under-powered.

## Limits

- One model, one recipe (CHANGE 1's, untuned), one epoch, the experts frozen.
- The target teaches the grade only. No measure here says whether the reasons are right.
- One run per arm at temperature 1.0, as on the board.
- One essay corpus with one adjudicated score, so there is no ceiling on TEST.
- The essay gain is measured on the prompts the model was trained on; the unseen-prompt check is above.
- The base model may have seen ASAP 2.0 in pre-training; that affects both arms alike.

## Spend

Reported when the pod is terminated.
