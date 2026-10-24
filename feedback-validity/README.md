# Do the benchmark's feedback measures agree with trained annotators?

**Asked:** `../feedback.py` scores the feedback a grader writes with word-list rules. They had no human
reference, so they could only be reported as descriptive. Do four of them agree with trained human
annotators' labels on MRBench (Maurya et al., NAACL 2025; CC BY-SA 4.0; 1,655 tutor responses from
seven LLM tutors and a human expert, to a student's maths mistake in 200 dialogues)?

**Design:** `validate.py`'s docstring, pre-registered at 1d22f184 before any annotation was read. Each
rule is applied unchanged. The statistic is a signed AUC with a bootstrap over dialogues, against a
content-free bar (response length). The reported annotator agreement, the ceiling for any automatic
measure, is average Cohen's κ 0.71 (paper) and Fleiss' κ 0.65 (BEA 2025 shared task). These figures
were read from search summaries, not from the papers.

One disclosed change was made before any AUC was computed (CHANGE 1). The README's label strings
("Yes (correct)") are not the file's ("Yes (and the answer is correct)"), so the leak pair first read
zero positives. The floor was re-run after the fix.

**Floor passes** (`out/floor.json`) for all four pairs:
- labels planted from the rule at AUC about 0.72 were recovered 50/50;
- labels planted from length alone were never called VALIDATED (0/50);
- labels deranged within each tutor were never called VALIDATED (0/50), with mean null AUCs of 0.47 to
  0.53, so the model-identity fallback did not trip.

## Came back (`out/result.json`)

| rule (feedback.py) | human label | AUC [95% CI] | length bar | verdict |
|---|---|---|---|---|
| tone (praise minus criticism) | Encouraging vs Neutral | **0.669** [0.639, 0.698] | 0.585 | **VALIDATED** |
| critical phrases per 100 words | Mistake identified: Yes vs No | 0.581 [0.538, 0.624] | 0.636 | INCONCLUSIVE |
| action phrases per 100 words | Actionable: Yes vs No | 0.513 [0.486, 0.540] | 0.565 | NOT VALIDATED |
| five-word overlap with the solution (`leaks_answer`) | Reveals the answer: Yes vs No | 0.517 [0.490, 0.547] | 0.781 | NOT VALIDATED |

- **Tone is validated** for tutoring-style responses: it beats length by +0.05 to +0.11. This is the
  measure the feedback-halo test uses (`../feedback.py`, `halo`), so the halo finding now rests on a
  validated tone measure, for this kind of text. Transfer to essay feedback is not shown.
- **`leaks_answer` does not work.** Tutors reveal an answer by stating it ("it's a pentagon", "so the
  answer is 18"), not by copying five words of a worked solution. The round-3 figures (Haiku leaking
  on 21% of weak short answers) are therefore withdrawn as evidence of answer leakage: they count
  copied phrasing, not revealed answers.
- **Action phrases do not track actionability.** The word list ("should", "try", "consider") is
  rarely how tutors give a next step; they ask a guiding question instead.
- **Critical phrases** are inconclusive, and below the length bar.

**Exploratory, not a verdict:** a different leak rule, "the response contains the solution's final
number", reaches AUC 0.830 on the dialogues that have a solution. It was chosen after the data were
seen, so it needs its own pre-registered test on new data before the benchmark adopts it.

**What this changes in the benchmark:** tone, and the halo built on it, may be reported as validated
against MRBench for tutoring-style feedback. Every other feedback measure stays descriptive, and
`leaks_answer` and `action_per100` should be replaced, not tuned.

Reads `$MRBENCH_DIR` (registry id `mrbench`). No response text or per-response label is committed.

## Learning Commons' Feedback evaluators on MRBench (`lc_mrbench.py`, pre-registered at 2671e71a; `out/lc-result.json`)

**Out of scope, and labelled so wherever it is cited.** Learning Commons scopes its Feedback evaluators
to Quill "because" completions in ELA writing (grades 6-12). MRBench is maths tutoring. A pass says
the construct travels; a failure would not be evidence against the evaluators in their own scope. This
fills part of what `(private pre-registration)` could not run.

Their own prompts, schema, model and temperature (GPT-5.4 at T = 1, served by Azure through OpenRouter
with zero retention), with the MRBench dialogue as `student_text` and the tutor's reply as
`feedback_text`. 600 responses each and 100 retests, $10.37. One disclosed change: their output schema's
definitions were inlined for OpenAI's strict mode, after a smoke call that returned an error and no
output. Floor passed for both.

| evaluator | MRBench label | AUC (balanced accuracy) [95% CI] | length bar | kappa | retest | verdict |
|---|---|---|---|---|---|---|
| Withholding Answers | Reveals the answer (No = meets) | **0.804** [0.775, 0.832] | 0.573 | 0.581 | 96% | **VALIDATED** |
| Revision Actionability | Actionable | 0.633 [0.592, 0.673] | 0.574 | 0.267 | 92% | INCONCLUSIVE |

Annotator agreement on MRBench, the ceiling: kappa 0.65–0.71.

- **Withholding Answers works on tutoring, near the annotators' own level** (kappa 0.58 against their
  0.65–0.71). It is strict: when a tutor revealed the answer it says so 98.5% of the time; when the
  tutor did not, it still flags 38% as revealing (sensitivity 0.62). It beats this benchmark's own
  word-overlap rule (0.52) and the exploratory final-number rule (0.83, on the dialogues that have a
  solution) is about as good, for free.
- **Revision Actionability is better than our word list (0.51) but not validated**: its lower bound,
  0.592, sits just under the 0.60 bar.
- **Tone Appropriateness: unanswerable here** (its construct counts neutral tone as meeting it, and
  MRBench has one offensive response).

**What it changes:** Withholding Answers is a candidate to replace `leaks_answer` in the benchmark's
feedback checks, for tutoring-style feedback, at about $0.008 a call; the final-number rule is the
free alternative and needs its own pre-registered test.
