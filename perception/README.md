# Perception audit: does a video grader say it cannot see a student, by skin tone and lighting?

**Status: not yet run.** The calls are waiting on the licence check: the maintainer's own confirmation that the
Casual Conversations v2 licence (clauses 1(b), 6.2 and 6.9) allows sending videos to hosted models, at zero
retention, for this evaluation. If it does not, the study runs only on models we host ourselves. The design, the
floor, the sample, the fetcher and the cost estimate are done. The pre-registration is the docstring of
`study.py`.

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
- **Models.** The 11 board models that take video. Each video is sent unmodified, once per model, at zero
  retention. The licence forbids derivative works, so no frames, dimming or trimming, and image-only models are
  not covered.
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

**Cost (estimated, nothing spent).** About $57, and up to about $125 if models that count tokens by pixels charge in
proportion to the full 1920 x 1080 resolution. The proposed hard cap is $140, with $40 per model
(`out/estimate.json`).

**Open items.**
- **The licence check above.**
- **Request size.** An unmodified video is about 100-150 MB, about 136 MB as a request for the dry-run video. Some
  endpoints will likely refuse that, and a file-upload API is ruled out because it keeps a copy.

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
