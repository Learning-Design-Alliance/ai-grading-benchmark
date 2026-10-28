# Research log

The benchmark's development record, moved from the research repository on 2026-10-24. Runs with a product's own grading prompt were made during development and are reported privately; their rows and paragraphs are left out here.


**Asked:** could the grader evaluation become a public benchmark? It would need to be independent of
any product, use whatever prompt the user brings, and run on data each user downloads themselves. It
should report what a decision to use AI marking turns on: validity, reliability, fairness and
sustainability (cost and energy).

**Came back (2026-10-23):** a standard-library Python package, version 0.1.0, and a first $35 test.
Five models were run on Mohler short answers and three on ASAP 2.0 essays with the benchmark's
default prompt. **Results are under "First runs" below.**

**The floor failed one criterion.** After five more probes were added, a planted +0.20 presence
effect was found in 14 of 20 seeds against a pre-registered 18. Every other effect passed. Presence
readings below their detectable size are therefore unresolved, not absent (`floor.py`, CHANGE 1 and 2).

## What it is

```
bench.py            prepare | run | score | compare   (the docstring is the user manual)
cases.py            the case format; loaders for Mohler and ASAP 2.0
prompting.py        bring-your-own prompt (template or Python), the nine probes, the mark parser
client.py           any OpenAI-compatible endpoint; disk cache; no silent fallback
report.py           the four sections; its docstring defines every number
metrics.py          QWK (half-up, as the research harness rounds), Pearson r, the bootstrap
floor.py            the detection floor (pre-registered at b36763c, before its first run)
prompts/default.txt the neutral reference prompt
out/floor.json      the floor's result
```

No product code is imported; the package scores whichever prompt it is given.

## What it measures

Each case is graded once per probe, through the user's own prompt:

| dimension | probes and numbers |
| --- | --- |
| **validity** | QWK and Pearson r against the humans, the human ceiling on the same cases, **share of the ceiling**, signed bias, spread, pass/fail agreement, failed gradings; padding appended, an injected request for full marks, work for a different task |
| **reliability** | the same call twice (retest QWK, identical share, mean change); the same work re-wrapped, read against the retest's change |
| **fairness** | 8/10 vs 3/10 prior attainment on identical work (same-length sentences), a neutral sentence vs none (the presence effect), penalty and reward; per demographic group, the grader's residual against the humans relative to the other groups, signed |
| **sustainability** | prompt, completion and reasoning tokens, latency, the model that actually answered; cost (reported, or from the prices passed); energy and carbon only from coefficients the user passes, with their source; human marking cost beside it |

`compare` gives paired B − A differences with intervals: the test of a user's own prompt against
the default.

Neither design choice is a style preference:
- **No energy default.** There is no public per-token energy figure for most hosted models, and the
  report will not print a guess as a measurement.
- **Group effects are signed per level** rather than reported as a widest gap. The widest gap among
  several groups is positive by construction, and its interval excludes zero on pure noise.

## Detection floor (`floor.py`, `out/floor.json`)

The floor uses a synthetic Mohler-shaped corpus: n = 200, two raters, and a fake grader that reads the
rendered prompts. Each world ran on 20 seeds. **FLOOR PASSES.**

| effect | planted | mean estimate | flagged (of 20) |
| --- | ---: | ---: | ---: |
| label (8/10 − 3/10) | +0.60 | +0.594 | 20 |
| presence | +0.20 | +0.197 | 19 |
| injection | +0.50 | +0.485 | 20 |
| group B vs A | −0.40 | −0.411 | 20 |
| padding, surface | 0 | −0.012, −0.008 | 1, 1 |
| NULL world, all six | 0 | −0.020 to +0.011 | 1–3 |

- **Ceiling:** 0.801 against the population's 0.801.
- **Resolution at n = 200:** the label effect's 95% half-width is 0.11 marks on a 0–5 scale. A
  smaller effect cannot be told from zero at the default size.
- **Positive control on real data:** Mohler's 1,727 kept rows give a ceiling of 0.5193 through the
  report's own code path, matching Paper VI's 0.519.
- **Weak point:** NULL injection was flagged 3 of 20 times, which is the pre-registered limit.
  Percentile intervals on whole-number marks run a little narrow, so treat a flag that only just
  clears zero with care.

## Things found on the way

- **the maintainers' earlier grader-check script (private, not part of this repository) gives Mohler a ceiling of 0.503, not 0.519.** It pools
  both orders of each rater pair. The release counts one order per pair. This package follows the
  release. `grader_check.py` is unchanged, because the fix is a choice for the maintainer.
- **ASAP 2.0 releases one mark per essay** (adjudicated from two blind expert ratings; the individual
  ratings are not released), so the harness computes no ceiling. The data paper reports
  pre-adjudication weighted kappa .745 as a published reference. Its demographic groups are
  small at n = 200 (ELL yes about 26; race groups 1–40). Fairness work on it needs a larger n, or
  sampling stratified by group, which is not built yet.

## First runs (2026-10-23)

**Setup:**
- n = 200 per run, stratified on the human mark, with all 14 probes, through OpenRouter with
  zero-data-retention routing. Each model's own default settings were used.
- DeepSeek and Qwen were pinned to DeepInfra (see "Infrastructure" below).
- Spend was $34.96 in all, including a smoke test and two abandoned unpinned runs.
- Per-run aggregates are in `out/runs-2026-10-23/`. Reply text stays in scratch.
- **Floor caveat:** presence readings are below their detectable size and unresolved.

### Mohler (short answers, 0-5, two raters; ceiling 0.506 on this draw)

`*` = 95% interval excludes zero. Probe columns are mean change in marks, probe minus base.

| model | prompt | QWK | r | share of ceiling | bias | retest QWK | injection | forged | repeat | chimpanzee | label 8/10-3/10 | $/1k gradings |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Haiku 5.5 | default | 0.562 | 0.783 | 111% | -0.84* | 0.974 | +0.11* | +0.04 | -0.28* | -0.56* | +0.05 | 0.13 |
| Gemini 3.5 Flash Lite | default | 0.542 | 0.701 | 107% | -0.42* | 0.983 | +0.45* | +0.20* | -0.19* | -0.99* | +0.04 | 0.13 |
| GPT-5 Mini | default | 0.599 | 0.751 | 119% | -0.33* | 0.958 | +0.04 | +0.01 | -0.11 | -0.31* | +0.07 | 0.66 |
| DeepSeek V4.1 Flash | default | 0.579 | 0.765 | 115% | -0.58* | 0.963 | +0.25* | +0.03 | -0.17* | -0.32* | +0.10* | 0.17 |
| Qwen3 235B | default | 0.553 | 0.746 | 109% | -0.74* | 0.978 | +1.34* | +1.65* | -0.42* | -1.93* | +0.14* | 0.04 |

| model | QWK | attainment label effect |
|---|---|---|
| Haiku 5.5 | -0.089 [-0.133, -0.047] | +0.10 [+0.02, +0.19] |
| Gemini 3.5 Flash Lite | +0.024 [-0.017, +0.069] | +0.06 [-0.02, +0.14] |
| GPT-5 Mini | -0.087 [-0.139, -0.035] | +0.04 [-0.08, +0.14] |
| DeepSeek V4.1 Flash | -0.076 [-0.107, -0.045] | +0.08 [-0.01, +0.18] |
| Qwen3 235B | -0.136 [-0.182, -0.089] | +0.10 [+0.01, +0.20] |

### ASAP 2.0 (source-based essays, 1-6, one released mark per essay, so no computed ceiling)

| model | prompt | QWK | r | bias | retest QWK | forged | shuffled | chimpanzee | label | $/1k |
|---|---|---|---|---|---|---|---|---|---|---|
| Haiku 5.5 | default | 0.527 | 0.589 | -0.26* | 0.854 | +0.10* | -0.44* | -0.31*† | +0.12* | 0.50 |
| Gemini 3.5 Flash Lite | default | 0.605 | 0.717 | +0.64* | 0.957 | +2.33* | -0.98* | -0.81* | +0.12* | 0.76 |
| Qwen3 235B | default | 0.483 | 0.571 | +0.60* | 0.930 | +2.46* | -0.62* | -1.82* | +0.14* | 0.22 |

### What it says

1. **On short answers every model already reaches the human ceiling with a plain prompt**
   (107-119%), as Paper VI found for its models.
2. **The construct-validity probes mostly pass.** Every model penalises work for another task (it
   scores 0-6% of the scale), the chimpanzee swap and, on essays, shuffled sentences. Writing each sentence twice is penalised in 15 of 16 runs; the harness found it barely penalised
   on DREsS essays (-9% on content).

### Infrastructure findings (the benchmark caught these about itself)

- **A model name is not a model.** OpenRouter served DeepSeek V4.1 Flash from 23 backends, mixing
  fp4 and fp8, and chose one per call. The report now flags mixed backends, and DeepSeek and Qwen
  were re-run pinned.
- **Content filters bias probes.** See † above. The chimpanzee probe should not ship in a public
  benchmark as written. Replacing "the" with an ape name in essays by named, demographically labelled
  students produces demeaning text, which is also why a filter refuses it. A neutral non-word
  ("blicket") tests the same thing.
- **The harness graded ASAP without its source texts.** Here both prompts get them, which is why
  the ASAP prompts are about 2,100-4,700 tokens.

### Beside the harness's own tests

| test | research harness (Paper VI era) | this benchmark |
|---|---|---|
| ceiling-relative agreement | yes, 9 corpora | yes; reproduces Mohler 0.519 |
| retest / pooling | yes | retest only |
| surface edits | 7 (whitespace, bullets, lowercase, punctuation, typos...) | 2 (re-wrap, typos) |
| injection | 5 escalating payloads, the product prompt only | 2 (polite note, forged rubric), any prompt |
| babel (shuffled, chimera, chimpanzee, padded) | DREsS essays, 4 criteria | shuffled, off-task (= chimera at whole-response level), chimpanzee, repeat |
| attainment and history context | yes, with swapped-label and neutral arms | high/low/neutral, any prompt with a context slot |
| group residuals | ASAP ELL and others | every attribute the cases carry, signed per level |
| rubric ladder, calibration, exemplars, feedback quality, segmenting | yes | not yet |
| cost, latency, served backend | partly | yes, per run |
| a floor with planted effects | per study | built in (`floor.py`) |

## Second round (2026-10-23): blicket, a frontier model, code, and the disability gap

Spend across both rounds: $187.02. All aggregates are in `out/runs-2026-10-23/`.

### Chimpanzee becomes blicket

The chimpanzee figures in the first-round tables above are kept as recorded. The probe is now
`blicket` (every "the" becomes the non-word "blicket"), re-sent for all 16 first-round runs.

- Every model penalises it, and every interval excludes zero. Short answers: -0.15 to -1.26.
  Essays: -0.13 to -0.81.
- Google-hosted Haiku's content filter refused 0-2 of 200 essays, against 53-61 for chimpanzee.
- Penalties are smaller than chimpanzee's (Qwen on Mohler -1.26 vs -1.93; Gemini -0.56 vs -0.99).
  The ape's name drew a reaction of its own on top of the broken language.

### A frontier model: Claude Opus 5.5 (pinned to Google's endpoint)

| task | prompt | QWK | share of ceiling | polite request | forged override | label 8/10-3/10 | $/1k |
|---|---|---|---|---|---|---|---|
| Mohler | default | 0.641 | 127% | -0.04 | -0.08* | +0.03 | 3.97 |
| code | default | 0.941 | 103% | +0.02 | +0.02 | +0.04 | 24.58 |

† 34 cases failed on OpenRouter's in-flight credit limit and were not re-sent, to stay inside the budget.

### Code: HARMOGEN-R (C++ in Portuguese, 0-90, four instructors; ceiling about 0.91)

129 open code responses to 3 questions, with the instructors' own rubric.

| model | prompt | QWK | share | polite request | **forged override** | label |
|---|---|---|---|---|---|---|
| Opus 5.5 | default | 0.941 | 103% | +0.0 | +0.0 | +0.0 |
| Haiku 5.5 | default | 0.909 | 100% | -2.0* | -0.9 | +1.8* |
| GPT-5 Mini | default | 0.908 | 99% | -0.1 | -0.4 | +0.7 |
| DeepSeek V4.1 Flash | default | 0.877 | 96% | -0.2 | +0.5 | 0.0 |
| Gemini 3.5 Flash Lite | default | 0.863 | 94% | **+40.3*** | **+46.1*** | +0.1 |
| Qwen3 235B | default | 0.752 | 82% | **+13.1*** | **+61.3*** | +1.7* |

‡ Scored from cache after a time limit: 113 of 129 graded. § Same: 122 of 129.

**Code is where the forged override bites hardest.** With the default prompt it is worth +46 of 90
for Gemini and +61 of 90 for Qwen. Four of the six models ignore it.

On agreement, every model is at 82-104% of the instructors' ceiling, and the two prompts do not
differ (paired QWK differences -0.002 to +0.010, all intervals include zero).

**The probes are not task-neutral.** typos, blicket, repeat, shuffled and surface are written for
English prose and were not run on Portuguese C++. surface would also change a program's meaning,
because a `//` comment swallows the lines re-wrapped into it. Code needs its own meaning-preserving
probes: renamed identifiers, re-indentation, comment-only changes, dead code.

### Disability gap: replicated, shared, not Gemini's alone

See `disability/README.md`. On 3,000 new essays matched on the human mark, every grader marks
students identified with a disability lower than the human mark did: Gemini -0.43, Haiku -0.17,
Qwen -0.21. All intervals lie below -0.10. The pre-registered reading is SHARED GAP: the gap belongs
to the human marks or to the essays, until the individual ratings say which (the mark is adjudicated
from two blind raters; see `disability/README.md`). Gemini's gap is about twice the others'.

### Infrastructure, second round

- OpenRouter's in-flight budget returns HTTP 402 when the credit reserved by open requests
  (`max_tokens` each) exceeds the key's allowance, even with credit left. The client now waits it out.
- `run --cached-only` rebuilds a run from its cache, so a run stopped by a time limit or a spend
  cap can be scored on what it already paid for.

## Third round (2026-10-23): new tasks, small models, older releases, feedback and four new probes

### Four new probes from the literature review (`LITERATURE.md`)

- **Blank and master-key answers** (empty, ".", "Thought process:", the question restated, gibberish;
  Zhao et al. 2025): no model credited any of them in any run that included them (the core battery:
  the lineage runs, PERSUADE and Menagerie). The small-model runs predate the probe and did not.
- **Selective scoring** (five gradings per answer; keep the most consistent share). Accuracy rises as
  the least consistent answers go to a person for four of five models: on Mohler, keeping the most
  consistent half takes DeepSeek V4.1 from QWK 0.589 to 0.717, GPT-5 Mini 0.591 to 0.641, Haiku 5.5
  0.554 to 0.638, Gemini 0.541 to 0.593; Qwen3 does not improve (0.549 to 0.539). **The floor fails
  this probe (F9):** on planted data the gain was too small and too variable to trust at n = 200, so
  these curves are reported, not ranked.
- **Rationale deletion** (delete the sentence the grader's reason leans on, against a random
  sentence of the same length). On PERSUADE essays no model's mark depends on the sentence it cited
  more than on a random one: cited minus random, in marks, Haiku +0.02 [−0.05, +0.08], Gemini +0.01
  [−0.04, +0.06], GPT-5 Mini −0.03 [−0.08, +0.03], Qwen3 +0.07 [−0.01, +0.14], DeepSeek +0.04
  [−0.05, +0.12] (153–190 essays each; the floor's planted effect, +0.41, was found 20/20). On Mohler
  only about 10 answers per model have a sentence to delete, too few to read.
- **Feedback with the mark hidden and shown** (`bench.py halo`; Bulut et al. 2026's design). Tone is
  praise minus criticism phrases. A positive halo means feedback follows a mark it is told beyond
  what the work shows:

  | model | Mohler | PERSUADE |
  |---|---|---|
  | Claude Haiku 5.5 | −0.00 [−0.13, +0.13] | **+0.20** [+0.01, +0.39] |
  | Gemini 3.5 Flash Lite | **+0.26** [+0.17, +0.35] | **+0.38** [+0.23, +0.53] |
  | GPT-5 Mini | +0.12 [−0.00, +0.25] | **+0.40** [+0.16, +0.65] |
  | Qwen3 235B | +0.04 [−0.06, +0.15] | **+0.43** [+0.22, +0.63] |
  | DeepSeek V4.1 Flash | **+0.12** [+0.01, +0.22] | **+0.39** [+0.19, +0.59] |

  On essays every model's feedback copies the mark. A teacher who marks first and asks the AI for
  comments gets comments that agree with the mark rather than an independent read. The tone measure
  was later validated against trained annotators on tutoring responses (`feedback-validity/`, AUC
  0.67, beating length); its transfer to essay feedback is not shown.

### Feedback quality (`prompts/feedback.txt`, rule-coded, descriptive)

On short answers, Haiku's feedback reproduces five or more words of the model answer for 21% of
weak answers (Gemini and DeepSeek 14%, GPT-5 Mini and Qwen 0%). That measure has since failed
validation against trained annotators (`feedback-validity/`, AUC 0.52), so this counts copied phrasing,
not revealed answers. On essays, feedback for strong
and weak work hardly differs for any model (varied-by-quality 0.01 to 0.04), as the earlier harness
found ("specific without discriminating"). Gemini and Qwen aim the most phrases at the person rather
than the work (about 6 to 7 per 100 words on essays).

### New tasks

**PERSUADE 2.0** (argumentative essays, grades 6-12, 1-6, one released mark per essay, so no computed ceiling; 100 cases):

| model | QWK | polite request | forged override | blicket | label 8 vs 3 | $/1k |
|---|---|---|---|---|---|---|
| Gemini 3.5 Flash Lite | 0.690 | +0.66 | **+2.07** | −0.27 | +0.12 | 0.35 |
| Qwen3 235B | 0.563 | **+1.33** | **+1.91** | −0.97 | +0.23 | 0.10 |
| Claude Haiku 5.5 | 0.429 | −0.13 | −0.04 | −0.19 | +0.26 | 0.28 |
| GPT-5 Mini | 0.371 | +0.05 | +0.07 | −0.20 | +0.07 | 0.92 |

DeepSeek V4.1 Flash is still running on its pinned zero-retention host (very slow) and is not in this table.

The forged override is not a code problem. On essays it adds about two marks on a six-point scale
for the two models it also moved on code; the two models that resist it agree with the human least.

**Menagerie** (whole programs, four craft dimensions, 0-4, three to four markers; 100 cases). The
markers barely agree with each other (ceiling QWK 0.234 [0.053, 0.293]), so shares of the ceiling
are unstable:

| model | QWK | r | share of ceiling | polite request | forged override | $/1k |
|---|---|---|---|---|---|---|
| Qwen3 235B | 0.296 | 0.601 | 126% | +0.41 | +0.41 | 1.54 |
| Gemini 3.5 Flash Lite | 0.283 | 0.609 | 121% | +0.29 | +0.33 | 5.75 |
| GPT-5 Mini | 0.155 | 0.302 | 66% | +0.22 | +0.30 | 4.83 |
| Claude Haiku 5.5 | 0.104 | 0.328 | 44% | −0.09 | −0.07 | 3.07 |

DeepSeek V4.1 Flash: pending, as above.

### Small open models (hosted copies, pinned host, zero retention; n = 200 Mohler, 129 code)

| model | Mohler share | code share | code: forged override (of 90) | code: polite request | $/1k (code) |
|---|---|---|---|---|---|
| Gemma 4 31B | 120% | 84% | +10.4 | +2.7 | 0.25 |
| Gemma 4 26B A4B | 120% | 82% | +6.9 | −4.6 | 0.12 |
| Gemma 3 27B | 109% | 94% | **+19.9** | **+17.0** | 0.20 |
| GPT-OSS 20B | 104% | 71% | **+39.7** | −2.7 | 0.11 |
| Phi-4 | 102% | 91% | −1.3 | +11.0 | 0.21 |
| Ministral 8B | 94% | 92% | +1.9 | +3.5 | 0.08 |
| Gemma 3 4B | 78% | 51% | +11.5 | +14.5 | 0.08 |
| Llama 3.2 3B | 34% | 79% | −20.3 | +5.6 | 0.26 |

For comparison, GPT-5 Mini is 119% and 99% at $2.54/1k on code. Gemma 4 grades short answers as well
as any frontier model for about a hundredth of the price, but every small model can be talked into
marks on code by at least one of the two requests. Granite 4.2 8B returned no readable mark for 70%
of code answers and its host was too slow to finish Mohler; Gemma 3 12B had no zero-retention host
that would serve it. These are hosted weights; a laptop's quantised copy may differ.

### Expensive models

GPT-6 Astra (n = 200): Mohler 125% of the ceiling at $4.95/1k, code 101% at $34.28/1k, and no probe
moved it. Fable 5.1 ran through OpenRouter on a bring-your-own Anthropic key (BYOK,
zero retention): Mohler core battery QWK 0.631 (110%) at $6.76/1k, no request or forged override
raised its marks, blicket penalised (−0.31), and its content filter refused every gibberish answer.
Code (all 129 cases): QWK 0.943 (103%), level with Opus (0.941), forged override −0.55,
at $71.31/1k, the most expensive grader here because its reasons run to about 730 tokens. Before the
key was added, a labelled pilot graded the core battery's 100 Mohler cases and 40 code answers
(base and forged override only) as prompt-only subagent batches (`out/agent-pilot-2026-10-23/`): 110% and 102% of the
ceiling, the forged override had no effect, and blicket was not penalised (+0.05). The pilot is not
comparable on cost or serving conditions.

### Older releases and drift

See `DRIFT.md`: newer is not uniformly better (Haiku 4.5 agrees more than 5.5 but is easier to game),
and every upgrade agrees with its predecessor less than the predecessor agrees with itself.

### Self-preference

449 answers written by five models at three quality levels to 30 Mohler questions, graded by
those five and two more (`out/selfpref-2026-10-23/`): no grader over-marks its own model's or
family's answers (every residual within ±2.5% of the scale). The one interval that excludes zero
goes the other way: GPT-5 Mini marks GPT-5 Mini's answers 2.4% lower [−4.7, −0.2].

## The leaderboard (2026-10-24)

`leaderboard.py` defines it; `public/README.md` is the package's front page and `public/SUBMITTING.md` how
to submit. 48 entries are seeded from the maintainers' runs (`submissions/`; 17 models on short answers and
code, 14 on essays; Fable, Opus and Astra not run on essays) and built by the same verifier CI runs
(`out/leaderboard.json`, 0 refused). The public report's data is `out/public/` (`public_data.py`).

What it shows, briefly:
- **Short answers:** 16 of 17 models reach at least 91% of the human ceiling (Opus 5.5 119%); Llama 3.2
  3B reaches 66%.
- **Code:** the frontier models lead (Fable 5.1 and Opus 5.5 108%, Astra 103%); GPT-OSS 20B and Gemma 3
  4B reach about a third.
- **Gaming:** the forged override or polite request gains more than 5% of the scale for 9 of 17 models on
  code (Qwen3 83%, Gemini 3.5 Flash Lite 62%, GPT-OSS 20B 53%), and about half the scale on essays for
  Qwen3, Gemini and Gemma 4 26B.
- **Blank answers:** credited by Gemma 3 4B, Llama 3.2 3B, Phi-4, Ministral 8B and Gemma 3 27B; the other
  12 models credit none.
- **Refusals:** Fable 5.1 and Haiku 5.5 refuse about 30 of 909 short-answer gradings each, nearly all the
  gibberish answers. A refusal is work sent to a person, not credit.

## Pre-registered: measured energy, Olmo on the board, a fine-tuned encoder (2026-10-25)

Committed before any call or training run:
- `energy/energy.py`: GPU energy per grading for the eight open models on the board, and for Olmo 3.1 32B
  Instruct, measured on one rented A100 80GB (RunPod) with vLLM, against docs/ENERGY.md's per-token
  estimates. Its floor (a simulation of the estimator) passed: mean error 0.8%, interval coverage 92%.
- Olmo 3.1 32B Instruct on the board: the full battery on the same pod (`gpu/pod.py`, `gpu/controller.py`).
  The route is recorded in each run's config (`bench.py --route`, carried into the export).
- `baselines/baselines.py` CHANGE 2: DeBERTa-v3-base fine-tuned per task.

## Results: measured energy, Olmo on the board, the fine-tuned encoder (2026-10-25)

Two RunPod pods with one A100 80GB PCIe each, 4.8 GPU-hours, $6.49 in all; both terminated. The first pod's
host restarted the container five times, so Olmo and DeBERTa ran on a second pod.
- **Energy (`energy/`).** Batched 16 at a time, a grading used 0.8-9 mWh of GPU energy above idle for a short
  answer and up to 29 mWh for code. With a stated ×1.72 for the rest of the data centre, that is below the
  per-token estimate's small-model tier in all 27 model-task cases, by a median factor of 4. One request at a
  time costs 4-16 times as much. The eight board models failed the pre-registered idle check (idle 13-26% higher
  just after work; bar 10%), so their verdicts are UNMEASURED and the figures descriptive. Olmo passed it:
  BELOW THE SMALL-MODEL ESTIMATE on all three tasks. CHANGE 1 (1-s polls; t-interval after a narrow floor
  failure) and CHANGE 2 (descriptive verdicts) are in the script.
- **Olmo 3.1 32B on the board.** Overall 71.6, rank 16 of 18. 103% of the ceiling on short answers; gamed by
  55% of the scale on essays (the most on the board); credits blank answers; YIELDS TO PUSHBACK by 26% of the
  scale; reads the maths working. Other models' scores are unchanged.
- **DeBERTa baseline (CHANGE 2).** Essays: QWK 0.81, above every model on the board. Short answers: 0.36,
  below every model. Code: 0.01.

## Running it

Fetch Mohler or ASAP 2.0 yourself (`data/data-sources.json`: `mohler-asag`, `asap2`, both CC BY 4.0;
Mohler's parquet goes through a conversion script in the maintainers' private analysis repository). Then follow the usage in
`bench.py`'s docstring. `run` is a dry run until `--go` is passed. Keep `runs/` out of version
control, because reply text can quote student work.

## Not done yet

- **The individual pre-adjudication ratings for ASAP 2.0 and PERSUADE** (ask the authors), for the
  disability gap and for a computed ceiling on essays.
- **Selective scoring at a size the floor can see** (F9 fails at n = 200).
- **Code versions of the prose probes** (renamed variables, re-indentation, comment-only edits).
- **Opus and Astra on essays**, and the small models on essays.
- **A human reference sample for the feedback measures**, before any of them is used as a gate.
- **Vendor notice for the forged-override exploit**, then the patent gate and readiness before any
  packaging outside this repository.

## 2026-10-26: what changes a grader's results

Eight pre-registered studies; each docstring holds the design and its numbered changes, each README the result.
- **Setups** (`setups/`): the flag is fixable for 4 of 14 flagged models (Gemma 4 31B, Gemma 4 26B A4B, GLM 5.3,
  GPT-5.6 Luna). High reasoning effort cut gaming for every reasoning model; a guard sentence backfired on four
  non-reasoning models.
- **Host precision** (`hosting/`): PRECISION MATTERS in all three comparisons; 4-bit hosts were far more gameable
  (DeepSeek V4 Pro code: forged +72% against +21%, QWK 0.46 against 0.75). The board's DeepSeek V4 Pro and GLM 5.3
  rows were served mostly at 4-bit.
- **Paraphrase** (`paraphrase/`): the floor failed twice before any call and passed after two changes. Two of four
  models are PROMPT-SENSITIVE, by about 4 points beyond a re-ask.
- **Essays, fine-tuning** (`essays-finetune/`): fine-tuned Qwen3 4B ties DeBERTa (0.80); both beat the best prompted
  model (Opus with six marked examples, 0.71) even on an unseen prompt. The vendor arm could not run: OpenAI is
  withdrawing self-serve fine-tuning.
- **Length** (`analyses/length_partial.py`): every model agrees with the essay experts beyond length.
- **Energy re-run** (`energy/`, CHANGE 3): all eight board models pass after a cool-down; 27 of 27 figures below the
  small-model estimate.
- **Drift watch** (`drift/monitor.py`): the floor failed (a rule that needed the estimate above 2%), two changes
  before any comparison; baseline month done; monthly from 1 November.
- **Housekeeping:**
  - Olmo added to the setups study on a rented GPU.
  - `pushback.py` opened to any endpoint.
  - No machine-local paths in tracked files; git history rewritten to remove them (maintainer's decision).

## Essays fine-tuning, CHANGE 1: Gemma 4 26B A4B LoRA and the full board battery (2026-10-27)

**Asked (the maintainer):** does fine-tuning a larger open model, Gemma 4 26B A4B, do better than DeBERTa and Qwen3 4B,
especially on an unseen prompt? And what do the fine-tuned scorers score on the full leaderboard battery?

**Came back:** no; the larger model does worse.
- **Same prompts:** QWK 0.763 [0.737, 0.788]. DeBERTa and Qwen each exceed it, by 0.041 and 0.035.
- **Unseen prompt:** 0.607 [0.565, 0.648], which is 0.134 below DeBERTa and 0.148 below Qwen. That is a cost of
  0.156 for an unseen prompt, against 0.063 and 0.043 for the other two.
- **Recipe:** one, untuned, Qwen's. The expert layers stayed frozen, because PEFT cannot adapt fused experts.
- **Battery:** all three fine-tuned scorers now have full-battery rows (`essays-finetune/out/board_rows.json`).
  Board QWK is 0.78-0.80, and none is gameable by more than 2% of the scale. Every one credits blank answers.
- **Reproduction:** the retrained DeBERTa and Qwen reproduce their test QWK within 0.02. Their blank-answer
  crediting did not reproduce (DeBERTa 42 of 500 before, 156 after).
- **Spend:** GPU about $10.

## Essays, generative fine-tuning: Gemma 4 26B A4B against its own base on one server (2026-10-27/28)

**Asked (the maintainer):** if Gemma 4 26B A4B is fine-tuned so that it still writes its reply (a grade, then a
reason), does its essay grading improve, and what does it cost on the rest of the board? Pre-registered in
`essays-genft/study.py`, with four CHANGES, all before any grading was read.

**Design.**
- LoRA training on essays-finetune's 23,628 TRAIN essays, with the loss on the grade's tokens only (`{"score": N`).
  No reasons were taught: the reasons the model writes are its own.
- The control is the base model on the same pod, with the same vLLM, bf16 and settings, through the full battery.

**Came back** (fine-tuned minus base):
- **Essays:** QWK on 1,000 TEST essays rose from 0.620 to 0.781 (+0.162 [+0.129, +0.198]). It is descriptive: the
  floor for a 0.04 change failed.
- **Gaming on essays:** fell from 48% to 8% of the scale.
- **Short answers:** agreement fell, -0.198 QWK (from 112% to 77% of the ceiling), and gaming rose by 8% of the
  scale.
- **Maths:** it reads the working less (-0.33 of 4).
- **Unresolved or unchanged:** code, the halo and pushback were not resolved (their floors failed). Neither arm
  credits a blank answer.
- **Consistency:** retest agreement on essays fell from 0.97 to 0.74 (descriptive).
- **Against the regression heads:** level with the Gemma regression head and with Qwen; DeBERTa is 0.023 ahead.
- **Unseen prompt:**
  - the fold models reach 0.734, +0.114 over the base;
  - the cost of an unseen prompt is 0.047, against the regression head's 0.156;
  - +0.127 over the regression head on unseen prompts.
- **Spend:** GPU $37.21 (26.77 h), cap $60. All pods are terminated.
