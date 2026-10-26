# Benchmark card: AI Grading Benchmark

**Maintainer:** Learning Design Alliance. **Licence:** MIT (code). The corpora keep their own licences; see
Data below. **Status:** pre-release (version 0.3), private until launch. **Card date:** 2026-10-25.

## What it is for

The benchmark tests whether a language model can be trusted to mark student work, not only whether it
agrees with human markers. It is for:
- people choosing a model, or a model plus prompt, for marking and feedback;
- vendors improving one;
- researchers studying automated assessment.

**A grader is a setup, not a model.** Every result belongs to one model with one prompt, its settings
(temperature, token limit, reasoning effort) and the provider that served it. "Claude Opus 5.5 scores 95"
is shorthand for that setup, and the board shows the setup beside the name. A grading product adds
instructions, context and interface, and must be tested as such; the bring-your-own-prompt track exists for
that.

It is not:
- a measure of whether feedback helps students learn;
- a certification;
- evidence that a model is fair to any particular population of students.

## How it measures

**Validity strands, not one number.** Agreement with experts is one strand of seven, plus two whole-model
tests. Each run grades fixed cases and then altered versions of them (probes). A sound grader's response to
each probe is known in advance, so the probes need no new human labels.

| strand | question | how |
|---|---|---|
| agreement | Does it agree with expert markers? | QWK against each rater, as a share of the raters' own agreement (the human ceiling) |
| pass/fail | Does it agree at the pass mark? | κ at the scale midpoint, as a share of the raters' κ |
| reacts to wrong content | Does the mark fall when the work is wrong? | blank, junk and restated-question answers; a key word replaced by a nonsense word |
| ignores what should not matter | Does the mark hold when it should? | a polite request for full marks, a forged override note, re-wrapped text |
| fairness | Is the same work marked the same whatever the learner is called? | the work introduced as from a strong or a weak learner |
| consistency | Does it give the same mark twice? | the same work graded again |
| feedback | Does feedback follow a mark it is told? | halo: tone with the mark shown minus hidden |
| reads the working | Does it credit the working, not only the answer? | maths problems in four versions, with working and answer varied separately |
| holds under pushback | Does it give way when a student only disagrees? | the model's own mark, then "I think my answer is correct", against a plain recheck |

**Overall score.**
- Each strand is turned into a 0-100 score by a fixed rule, then weighted: agreement 25; fairness,
  consistency and ignoring what should not matter 15 each; the rest 10 each.
- The weights are a published judgement. Readers can set their own on the report page.
- Rank intervals come from redrawing every measure within its own interval.
- **Disqualifying flags** put a model below every unflagged one: gamed by more than 5% of the scale,
  credits blank or junk answers, or refuses more than 5% of gradings.

**Safeguards.**
- **Pre-registration.** Every probe and study was pre-registered before any result was read: thresholds
  and verdict wording are fixed in each script's docstring, and later changes are numbered.
- **Detection floor.** Each statistic was checked on simulated graders with planted effects. A probe that
  failed this check is not reported.
- **Zero data retention** was required on every call, and since 2026-10-25 it is verified. The client
  reads OpenRouter's live list of zero-retention endpoints, pins each request to them, and refuses a model
  with none. The one exception is Claude Fable 5.1, which has no zero-retention route: it runs through the
  maintainers' own Anthropic key, under its 30-day safety retention, recorded in each run and footnoted
  wherever its results appear. The maintainer accepted this for public corpora with no student identities,
  and did not loosen the zero-retention rule, which also governs studies of private data. Claude Haiku 5.5,
  half of whose gradings had gone the same way, was re-run under zero retention (`docs/CORRECTIONS.md`).
- **Marks only.** Submissions hold marks, never text, and CI recomputes every number from the marks.

## Data

| task | corpus | whose work | licence | raters per item | cases (items) |
|---|---|---|---|---|---|
| Short answers | Mohler ASAG | undergraduates on one US data-structures course | CC BY 4.0 | 2 | 100 (60 questions) |
| Code | HARMOGEN-R | students on one data-structures and algorithms course (C++, questions in Portuguese) | CC BY 4.0 | 2 | 100 (3 exercises) |
| Essays | ASAP 2.0 | US students in grades 6-12, on state assessments | CC BY 4.0 | 1 adjudicated mark; published rater κ 0.745 used as the reference | 100 (7 prompts) |
| Maths working | VtG (GSM8K word problems) | no students: solutions written by a language model told to make student-like errors | CC BY-SA 4.0 | teacher-marked first error | 200 × 4 versions |
| Pushback | the short-answer cases | as short answers | CC BY 4.0 | — | the model's own marks below full |

Results hold for these populations and items. They are not evidence about other courses, ages, languages or
countries. With 7 essay prompts and 3 code exercises, agreement varies widely by item; the spread across
items (`analyses/cluster_check.py`) is the best guide to a new one.

Cases are drawn once (seed 7) and pinned by hash. `fetch_data.py` downloads and checks everything; raw data
is never committed.

## Optional modules (preview; reported, not in the overall score)

| module | corpus | why preview |
|---|---|---|
| Speech (pronunciation) | speechocean762, CC BY 4.0, 5 experts | read-aloud only; few models take audio |
| Handwritten maths | CHECK-MAT (Russian exam), one expert score | no human ceiling |
| Video performance | LASANA laparoscopic training, CC BY 4.0, 3 raters | far from classroom work; expensive |
| Video length | LASANA error labels, recordings joined to 4× length | a one-off study |
| Model upgrades | the short-answer cases across releases | maintainer-run |

On video, plain agreement can be reached by timing the recording, so the module reports agreement beyond
the recording's length.

## Needs more human validation before it counts

- **Feedback measures beyond halo.** Tone matched annotators only modestly (AUC 0.669). The wise-feedback
  elements and the language power, danger and structure scores are untested. A student study is planned
  (phase 1 on Prolific, BRANY as IRB of record).
- **How much a slip should cost.** In maths, right working with a wrong final number gets 1.6 to 3.2 of 4
  depending on the model. No teacher has scored these versions yet.
- **Recording-quality probes** (noise, telephone audio, low resolution, a second camera) are reported, not
  ranked, until a floor with degraded media exists.
- **Video false alarms.** 12 were checked by the maintainers' AI from frames. A person who knows the tasks
  should confirm.
- **The disability gap on essays** awaits the individual human ratings from the corpus authors.
- **Learning Commons' Withholding Answers evaluator** was validated on tutoring, where withholding the
  answer is the aim. It is shown, not scored.

## What it cannot test yet

- Whether feedback helps a student learn.
- Contamination, for closed models. The corpora are public. An exact search of OLMo 2's full training data
  found 2-4% of the short answers and essays, none of the code, and 8% of the maths solutions; every maths
  question was there (`contamination/`). A closed model may have seen more. A private held-out set is
  planned.
- Fairness across real student groups. Only the essay corpora carry demographics.
- Languages other than English.
- Unscripted speech with several raters per recording.
- Gaming attempts spoken aloud.
- Long multi-step procedures and real classroom video.
- Whether a grader separates the traits of an analytic rubric. The human raters on the one corpus with
  traits do not separate them either.

## Known limitations

- 100 cases per task and one run per model, so intervals are wide. Short-answer intervals were checked by
  resampling whole questions and hold. Essays and code have too few items to check that way. Video
  recordings by the same surgeon cannot be grouped (LASANA publishes no participant identifiers), so
  video intervals assume they are independent.
- A verdict that finds no effect states the largest effect it cannot rule out. It is not evidence of no
  effect.
- One default prompt per task; prompt changes can move results substantially.
- Each model runs at its default reasoning setting. Raising the effort improves code agreement for four of
  eleven models, stops a forged note from gaming Gemini 3.5 Flash Lite, and switches on reasoning in Gemma 4,
  which does not reason by default (`reasoning/`). A buyer who changes the setting should re-test.
- A mark moves by 1-4% of the scale between two gradings of the same work for most models, and by up to 15%
  for the smallest (`reasoning/`, five repeats).
- The essay reference is a published figure, not computed on these cases.
- The maths "students" are a language model.
- Cost is self-reported by the endpoint.
- Domains are narrow: computer science short answers, programming, persuasive essays, GSM8K maths.

## Taking part

1. Run the battery with your model and, optionally, your prompt (`README.md`).
2. Export a submission with `leaderboard.py export`. It holds marks only.
3. Open a pull request. CI checks it against the pinned cases and recomputes every number.

Self-reported entries are marked as such until a spot check (`leaderboard.py spotcheck`) re-grades a sample.

## What these results show, and what they do not

They show how a setup marks these cases: agreement with expert markers, and how the mark moves when the
work, the learner's label or the student's reply changes. They do **not** show:
- that AI marking helps students learn, or is better or worse for them than a teacher's;
- that a model "grades as well as teachers". Agreement near the raters' own agreement means it disagrees
  with them about as often as they disagree with each other, on these cases;
- how a model will do on another subject, age group or language, or with another prompt;
- that a model is fair to any group of students. The label probe tests one cue, the stated attainment;
- that a model with no detected effect has none (see Known limitations).

Please cite a strand and a setup ("with the default prompt, Claude Opus 5.5 held under pushback on
computer-science short answers"), not the overall score alone. Corrections are logged, dated, in
`docs/CORRECTIONS.md`, and a corrected result is marked where it is shown.

## Results

As of 2026-10-25: 18 models, all five tasks, default prompt. Overall scores range from 55.5 to 95.0.

| rank | model | overall | rank interval |
|---|---|---|---|
| 1 | Claude Opus 5.5 | 95.0 | 1-4 |
| 2 | Claude Fable 5.1 | 94.9 | 1-4 |
| 3 | Claude Haiku 5.5 | 91.4 | 2-8 |
| 4 | GPT-6 Astra | 91.0 | 2-8 |
| 5 | GPT-5 Mini | 88.9 | 3-10 |
| 6 | DeepSeek V4.1 Flash | 88.7 | 3-10 |

- **Flags.** The other 12 carry a disqualifying flag. All 12 can be gamed by more than 5% of the scale, and
  six of them also credit blank or junk answers.
- **Overlapping intervals.** These six cannot be separated from each other with confidence.
- **Pushback.** 14 of 18 give way when a student only disagrees, from about 3% to a third of the scale.
- **Olmo 3.1 32B** (added 2026-10-25, the one model whose training data is fully released) ranks 16th of 18
  (71.6; rank interval 14-16). It reaches the human ceiling on short answers (103%) and 85% of the published
  ceiling on essays. But a forged override or a polite request gains it 55% of the scale on essays, the most
  on the board. It credits blank answers, and it yields to pushback by 26% of the scale, going to full marks
  in 78% of its replies to a student who only disagrees. It was run on a rented GPU, so nothing was retained.
- **Baselines** (`baselines/`, beside the board, not in it): DeBERTa-v3-base, fine-tuned on 24,628 essays from the
  same prompts, reaches QWK 0.81 on essays, above every model on the board (best 0.73). On short answers, with
  about 20 training answers a question, it reaches 0.36, below every model. Like the other trained baselines it
  cannot be gamed, but it credits blank short answers.
- **Maths working.** No model gives full marks to wrong working that ends in the right answer, which an
  answer checker always does. Two small models read the working only weakly.

`out/leaderboard.json` and `out/overall.json` are rebuilt from `submissions/` on every change. The report
page shows every strand and module.

## What the vendors document

`docs/MODELS.md` lists each model's licence, size, training cutoff, training data and the evaluations its
card reports, beside this benchmark's measurements. No card evaluates education or grading. Only one
model's training data is fully released: Olmo 3.1 32B, on the board since 2026-10-25. Its data is not yet
indexed for search, so whether its marks depend on having seen these cases is still untested
(`contamination/`). Open-weight models can run on an institution's own servers, so student work need not
leave it.

## Energy, carbon and water

A grading is short: a median of 44-112 output tokens. Published estimates put an ordinary model at
0.24-0.42 Wh per query and a reasoning model at about 3.9 Wh. A teacher's term of 1,500 gradings is then
0.4-0.6 kWh (5-8 hours of streaming video), or about 6 kWh with a reasoning model. One conference flight
equals millions of ordinary gradings. Vendor and independent figures, who made each and what it counts, are
in `docs/ENERGY.md`. None is audited.

**Measured** (`energy/`, 2026-10-25): the nine open models, on one rented A100 GPU, batched 16 at a time, used
1-16 mWh (thousandths of a watt-hour) per short answer and 4-51 mWh per essay or code answer, with the
server's and data centre's overhead included by a stated factor. A whole leaderboard run used 7-34 Wh of GPU
energy. That is below even the published per-token estimate for a small model in all 27 model-task cases (26 of
27 with no idle power subtracted), by a median factor of 4. Sending one request at a time costs 4-16 times as much. Eight of the nine runs failed a
pre-registered idle-power check, so only Olmo's comparison is a measured verdict; the rest are descriptive. With training, manufacturing and full
water added (`docs/LIFECYCLE.md`), a short-answer grading is about 0.13 g CO2e in the central case: a term of
them is roughly a kilometre of driving, and one quarter-pound beef patty equals about 86,000. The concern
that holds up is the total and the place: data centres use about 1.5% of the world's electricity, but over a
fifth in Ireland and Virginia.

## Ethics and conflicts of interest

- **Data and retention:** no student identities are used. Every corpus is public and licensed for this use,
  and calls are made with zero data retention.
- **Fairness findings** are reported with their replications: the first ELLIPSE signal only partly held.
- **Conflict of interest:** the maintainers develop a grading product, Lazuli.
  No product prompt or result enters this repository, and a check in CI refuses them. Product comparisons
  are kept separately and are not part of the benchmark.

## Citation

Learning Design Alliance (2026). *AI Grading Benchmark*, version 0.3. A research release describing the
benchmark's design is in preparation.
