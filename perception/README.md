# Perception audit: does a video grader say it cannot see a student, by skin tone and lighting?

**Status: run, 2026-10-27.** Results are below. The pre-registration is the docstring of `study.py`; CHANGES 1-3
record the move to self-hosted models, the per-model floor for the rating, and how a refusal is counted.

**Question.** A teacher asks students to answer a question aloud, to camera, and a video model checks each
recording: can it see the speaker, can it hear them, how well did they deliver the answer (1-5), and one sentence of
feedback. How often does the model say it cannot see a speaker who is plainly on screen, or refuse? Does that
depend on the speaker's skin tone, and on whether the recording was made after dark? This was prompted by a video
grader that told a student "I can't see you."

**Design in short.**
- **Data.** Meta's Casual Conversations v2: consented, paid adults answering a set question to camera. Skin tone
  comes only from the dataset's Monk labels, pooled into 1-2, 3-4, 5, 6, 7-8 and 9-10.
- **Lighting.** From the dataset's label: daylight (sunny or cloudy) against after dark. "After dark" recordings
  are nearly all indoors under room light, so this is a label about when the recording was made, not a measured
  brightness.
- **Sample.** 1,280 recordings (seed 26), at most one per person per cell. Per lighting stratum: 130, 200, 120, 85,
  85 and 20 across the six tone groups. After dark, the two darkest groups hold nearly every eligible person.
- **Models.** The open-weight board models that take video and fit one GPU: Gemma 4 26B A4B, Gemma 4 31B and
  Qwen3.8 27B, each at bf16 on our own rented A100 (vLLM v0.32.0). Each video is sent unmodified to our own
  machine and read by the model there; no video goes to any third party (licence clause 6.2). The licence forbids
  derivative works (6.1), so no frames, dimming or trimming.
- **Hosted models are not in this study.** Their endpoints refuse most full-length videos as too large (a 102 MB
  and a 168 MB video were refused in a pilot; the sample's median is about 155 MB), and the licence does not allow
  sending a reduced copy. GLM 5.3 Flash is too large for one GPU, and MiMo v2.6 Flash and Muse Spark have no public
  weights.
- **Pilot (not a result).** Before the move to self-hosting, one hosted model, MiMo v2.6 Flash, was sent the 10 black,
  silent control clips and 4 recordings. On 7 of the 10 blank clips it said a speaker was visible and audible and
  rated their delivery 3 to 5; those 7 cost almost nothing, which suggests the clip never reached the model and it
  answered anyway.
- **No labelling of people.** The model is asked nothing about the person, and nothing it says about a person
  is used. Feedback text that mentions appearance is discarded, and only a flag is kept.
- **Measures.**
  - The share of replies that say the speaker cannot be seen, and the share that refuse.
  - The delivery mark.
  - The darker-minus-lighter gap (Monk 7-10 minus 1-4) within each lighting stratum, and how the gap changes after
    dark.
  - Intervals from a cluster bootstrap over people.
- **Control.** A synthetic black, silent clip, which holds no dataset content.

**Floor (run, `out/floor.json`).** On simulated graders shaped like this sample:
- **Passed.** A 10-point after-dark can't-see gap against darker-skinned speakers is detected 85% of the time, with
  6.5% false alarms. A 0.10-of-scale after-dark rating gap is detected 98% of the time, and its widening after dark
  86% of the time.
- **Failed.** The daylight gaps' false alarms (7-9%) and the can't-see widening after dark (detected 71%) did not
  pass, so those will be reported as descriptive figures, not verdicts.
- **Not changed.** The planted effects were not enlarged. The corpus holds no more darker-skinned speakers
  recorded after dark.

## Results

All three models graded 1,278 of the 1,280 recordings (2 failed to upload), and all three said "not visible" on all
10 black, silent control clips, so none is barred by the CANNOT REPORT NOT SEEING rule.

| model | said it could not see the speaker | refused | usable replies | verdict on the tone gaps |
|---|---|---|---|---|
| Gemma 4 26B A4B (bf16, self-hosted) | 0 of 1,278 | 0 | 100% | UNMEASURED (no failures to compare) |
| Gemma 4 31B (bf16, self-hosted) | 0 of 1,278 | 0 | 100% | UNMEASURED (no failures to compare) |
| Qwen3.8 27B (bf16, self-hosted) | 822 of 1,278 (not credible; below) | 270 | 79% | DID NOT DO THE TASK |

**Reading.**
- **Both Gemma models saw the speaker in every recording**, in every skin-tone group, by day and after dark. With no
  failures at all, there is no gap between groups to measure, so the pre-registered gap verdicts read UNMEASURED.
  What the data do show is how rare a failure could be: zero in 1,278 recordings puts the overall rate below 0.23%
  (one-sided 95% bound). By tone group the bound depends on the group's size: below 0.7% for Monk 3-4 (400
  recordings), below 1.7-1.8% for Monk 6 and 7-8 (169-170), and below 7.2% for Monk 9-10, the darkest, where the
  corpus holds only 40 eligible recordings.
- **Qwen3.8 27B did not do the task.** 21% of its replies had no usable answer (the pre-registered limit is 20%), and
  its "cannot see" replies are not credible: in 372 of them it also rated the speaker's delivery. Its numbers are
  not read for groups. Its reasoning ran long at the registered 2,048-token limit, which is the likely cause.
- **Delivery ratings are descriptive only.** None of the three models takes audio, so the Gemma models answered
  "not audible" and, as the prompt asks, withheld the rating (they rated 0-4% of recordings); no rating gap is read.
- **What this does not show.** These are three open models on one GPU setup, not the hosted models most schools use;
  the incident that prompted the study involved a hosted model, which this design could not test. "After dark" is the
  dataset's label for when a recording was made, mostly indoors under room light, not a measured brightness.
- **A note on the records.** While the run was being restarted, stray copies of the runner briefly ran at the same
  time, so 122 Qwen recordings were graded twice; the analysis keeps one reply per recording (the last written).

**GPU spend.** About $27.57 of the $80 cap, across all attempts (6.6 hours on the final pod).

**Data handling.**
- Nothing from the dataset is in this repository: no video, frame, image, name, subject ID or reply text. Only
  aggregates are kept.
- Videos are read out of Meta's zips by range request (`fetch_ccv2.py`), 40 at a time. Every model grades the
  batch, and then the batch is deleted.
- `DIR/manifest.jsonl` records every file fetched and deleted.
- **To purge everything held locally** (for example, if Meta asks for deletion):

      python3 -I perception/fetch_ccv2.py --dir DIR purge

  This deletes the videos, the sample, the zip map and every run record. The manifest is kept as the record of what
  was held and when it was deleted. Then delete Meta's link list and the unpacked annotations.

**Files.**
- `study.py`: the pre-registration, sampler, floor, dry run, estimate, gated runner and analysis.
- `fetch_ccv2.py`: the range-request fetcher.
- `../prompts/spoken-answer.txt`: the prompt.
- `out/`: the floor and its failed drafts, the sample's cell counts, the dry run's request shape and the cost
  estimate.
