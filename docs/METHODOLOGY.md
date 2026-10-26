# Methodology: the rules this benchmark runs on, and where each came from

Every rule here was learned by getting something wrong, or nearly. Each gives the incident and how the rule is
enforced:
- **check** — a script refuses or warns.
- **template** — the study template asks for it.
- **review** — the independent audit looks for it.

A new study, task or modality (student presentations, screen recordings, anything else) starts from
`docs/STUDY-TEMPLATE.md` and runs `python3 scripts/check_study.py <dir>` before its first call.

## 1. Before any call

**1.1 Pre-register the design in the script's docstring.** State the thresholds, verdict strings, floor and budget.
Commit them before any call. A later change is numbered and dated, gives its reason, and says whether any
result had been read. Failed outputs are kept (`out/*-failed.json`), never overwritten.
- *Learned:* every study in this repository.
- *Enforced:* check (`check_study.py`: docstring sections, numbered changes); template.

**1.2 A floor first: plant a known effect and show the instrument finds it.** Do this on synthetic data shaped
like the real cases, before reading any real result. A null from an instrument that cannot see a planted effect
is not a finding. If the floor fails, the verdicts read UNMEASURED and the figures are descriptive.
- *Learned:* four floors failed on 2026-10-26 alone:
  - paraphrase, twice (detection 26%, then 63%);
  - the drift watch;
  - the media floor.

  Each failure exposed a design fault, not a model property.
- *Enforced:* check (a pre-registered study must name its floor and its output); template.

**1.3 Never enlarge the planted effect to make a floor pass.** Fix the design or the reading (more cases,
balanced comparisons, a scale-relative threshold), and record why.
- *Learned:* the paraphrase floor was fixed by pooling tasks and a 5%-of-scale change rule; its planted effect was
  left alone.
- *Enforced:* review.

**1.4 The floor's null world must be null.** Resampling real cases keeps their sample bias. A real base-to-retest
gap, for instance, makes "no planted effect" a world with an effect. Randomise which repeat plays which role.
- *Learned:* the media floor's first run had false alarms of 10-40% from exactly this.
- *Enforced:* template (the floor section asks how the null world is centred).

**1.5 A verdict rule must be one the floor can pass.** "Interval excludes 0 *and* estimate at least 2%" detects
a true 2% shift only about half the time. Use the interval for the verdict, and the size for "material".
- *Learned:* the drift watch.
- *Enforced:* template; the floor itself.

**1.6 Compare like with like.** Six paraphrases against a single retest is not a fair noise reference; five
re-asks against six paraphrases is. Every condition is graded on the same days, so a cached run from another
day is not a control.
- *Learned:* paraphrase CHANGE 1; the setups study's default arm re-run when its cache did not match.
- *Enforced:* template.

**1.7 Thresholds are shares of the scale.** A rule written in marks means different things on a 0-5 and a 0-90
scale. On code (0-90) nearly every re-ask moves by a point.
- *Learned:* paraphrase CHANGE 2.
- *Enforced:* template.

**1.8 A probe that should change nothing needs a positive control.** Show it would see a change where one is
deserved. "Holds under 10 dB noise" means little until the same instrument sees speech drowned at -10 dB.
- *Learned:* the media floor.
- *Enforced:* template (new modality checklist).

**1.9 Dry-run every launch and read the plan.** Check call counts, the estimated cost, and that the tool
accepts the probe list (bench.py refuses a run without the base probe).
- *Learned:* paraphrase re-asks refused; an orphaned test process.
- *Enforced:* bench.py dry run is the default (`--go` to spend).

## 2. What a grader is

**2.1 A grader is a setup, not a model.** Record:
- the prompt;
- the reasoning effort;
- the host;
- the numeric precision for open models;
- the retention route;
- the date.

High effort removed the flag for two models. A guard sentence fixed three, and made four others worse.
- *Learned:* `reasoning/`, `setups/`.
- *Enforced:* check (bench.py records the settings; `check_runs.py` reports them).

**2.2 Pin precision for open models.** A router serves whichever host answers. At 4-bit, the same open model was
gamed by 11 to 51 points of the scale more than at 8-bit, at the same agreement. Pin with
`provider.quantizations`, and label the row (`--label <model>@8bit`).
- *Learned:* `hosting/`; `precision/`.
- *Enforced:* check (bench.py warns when an open model on OpenRouter is unpinned).

**2.3 Hold the host fixed when testing for drift.** A model update and a change of host both move marks.
- *Learned:* the DeepSeek 17 October snapshot, re-run on one host.
- *Enforced:* template.

**2.4 Verify retention; do not assume it.** Pin to the router's live list of zero-retention endpoints. Refuse a
model with none unless an exception is stated, recorded and footnoted.
- *Learned:* 5,500 Fable and 11,300 Haiku gradings went through a bring-your-own-key route with 30-day
  retention.
- *Enforced:* check (`client.py`).

## 3. Running

**3.1 A spend cap that stops a run leaves it incomplete.** Check before any analysis. The unsent gradings are
recorded as "not sent: spend cap", and analysing such a run silently shrinks it.
- *Learned:* host-precision code runs cut to 55 paired cases.
- *Enforced:* check (`check_runs.py` exits non-zero on unsent or failed gradings above 2%).

**3.2 Check what produced a value.** Sentinels, exit codes, file names and resumed files are all claims.
- *Learned:*
  - a crash left a half-written month file, which the resumed run skipped as done and which was committed;
  - a grading with no host broke a sorted write;
  - a training loss looked like failure but was an average over one epoch.
- *Enforced:* check (outputs written atomically; `check_runs.py` parses every file it is given).

**3.3 Long jobs run detached, with a watch that alerts on failure as well as success.** Background tools have time
limits.
- *Learned:* several watches expired while the job was still running.
- *Enforced:* review.

**3.4 Rented GPUs:**
- terminate in a `finally`;
- give each pod its own state file;
- size the disk for every model it will load;
- let the GPU cool before an idle reading.
- *Learned:*
  - a full disk stopped one model;
  - post-run idle power was 13-26% high until a cool-down.
- *Enforced:* `gpu/pod.py`; review.

**3.5 No machine-local paths or private-repository names in tracked files.** Defaults come from environment
variables. History counts too.
- *Learned:* 60 such references, and a history rewrite.
- *Enforced:* check (`check_private.py`, `--publish` before release).

## 4. Measuring

**4.1 Sign every effect, and make the verdict label carry the direction.** "WIDENS" for a gap that narrowed is
wrong even when the interval is right.
- *Learned:* essay fairness labels; three sign errors in the research programme.
- *Enforced:* template; review.

**4.2 A null is never "no effect".** Report the largest effect the interval does not rule out. "Ties" becomes "no
difference detected (up to 0.02 not ruled out)".
- *Learned:* O'Neill 2026; the card audit.
- *Enforced:* check (verdict strings); review.

**4.3 Give the denominator.** "8% of the maths solutions" means 15 of 200 searchable. Short answers were 1 of 57,
not of 100.
- *Learned:* the card audit (contamination).
- *Enforced:* review.

**4.4 Pair by case, and resample the unit that was assigned.** Use a cluster bootstrap where cases share a
question. Correct for many flags at once (false discovery rate).
- *Learned:* `analyses/cluster_check.py`, `leaderboard.py multiplicity`.
- *Enforced:* code.

**4.5 Put the human ceiling beside any agreement figure, and the length baseline beside any essay figure.**
Length alone beat 16 of 22 models on essays, because the experts' marks follow length.
- *Learned:* `analyses/length_partial.py`.
- *Enforced:* template.

**4.6 Run the board's probes on every new kind of grader**, including fine-tuned and non-AI ones. Fine-tuned essay
scorers could not be gamed, but credited blank essays (8% and 29%).
- *Learned:* `essays-finetune/`.
- *Enforced:* template.

## 5. Reporting

**5.1 Round once, from the unrounded source; compute derived numbers from unrounded inputs.**
- *Learned:* the card audit found two double-rounding errors in one pass: 1.025 shown as 103%, and 0.0749 shown as
  0.08.
- *Enforced:* review; `scripts/check_numbers.py` lists every number in a document for checking against its
  source.

**5.2 When the population grows, re-check every claim made about it.** "No model is fooled" was true of seven
models and false of 22.
- *Learned:* the card audit (maths).
- *Enforced:* review (the audit re-checks every count).

**5.3 An independent audit before anything is shown outside the team.** The audit has no part in the work, checks
every number against its source, and lists unsourced claims. Any wording sweep is followed by an audit.
- *Learned:* 15 of about 95 claims failed on 2026-10-26.
- *Enforced:* review (`docs/AUDIT-PROMPT.md`).

**5.4 Every changed number, verdict or headline gets a dated row in `docs/CORRECTIONS.md`.** A row whose context
later changes is annotated "at the time", never rewritten.
- *Enforced:* review.

**5.5 Cite only what ships and public sources.** No private repository, path or unsourced detail.
- *Enforced:* check (`check_private.py`, `check_citations.py`).

## 6. Data and people

**6.1 No raw data in the repository.** Commit marks and aggregates, never student work or replies. Every corpus's
licence and source are listed.
- *Enforced:* check (`check_private.py`); `docs/DATA-SOURCES.md`.

**6.2 Zero retention for every call.** A vendor fine-tune cannot meet this, and the service can be withdrawn
(OpenAI's was, in 2026).
- *Enforced:* check (`client.py`).

**6.3 People who can be identified** (faces, voices, names) need consented data with terms that allow this use,
and no frame or clip is committed.
- *Enforced:* template (new modality checklist).

## 7. A new kind of assessment: the checklist

For presentations, screen recordings, spoken answers, video or any other new modality, the study must cover:

**Rubric and reference**
1. **Human reference.** At least two raters per item, so there is a ceiling. The rubric is the one the raters used.
2. **Same rubric, every grader.** The prompt carries the rubric; prompt wording is varied (paraphrase study) before
   results are compared across models.

**Gaming and nonsense input**
3. **Null inputs.** Black screen, frozen frame, silence, a tone, a blank slide. A sound grader gives the minimum.
4. **Off-task input.** Another person's or another task's work.
5. **Injection in the medium itself.** Text on a slide or screen saying "full marks", and the same spoken aloud.

**What should not change the mark**
6. **Quality.** Lighting, resolution, compression, noise, a phone microphone, a second camera. Use a floor
   (§1.2) and a positive control (§1.8).
7. **Length and pace.** Duration, words per minute, slide count. These are construct-irrelevant unless the rubric
   says otherwise (`video/LENGTH.md`).
8. **Input form.** Native video, sampled frames, or a transcript. Run the transcript-only control: if the grade
   survives without the video, the video is not being assessed.

**People**
9. **Appearance and voice fairness**, with consented, labelled data:
   - skin tone, crossed with lighting;
   - accent and first language;
   - the language spoken, common and less common;
   - age;
   - visible disability, and assistive formats such as captions or sign language.

   Signed gaps against the human reference, with the subgroup minimum stated in advance.
10. **"Cannot see or hear" replies.** Count refusals and "I can't see you" replies by group. A grader that cannot
    perceive a student must say so, never mark them down.
11. **Consent and retention.** Identifiable people are processed only under terms that allow it, with zero
    retention, and nothing identifiable is committed.

**Cost**
12. **Cost and energy per minute of media**, measured where the model is open.
