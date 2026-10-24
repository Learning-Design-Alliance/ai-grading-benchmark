# Video task: pre-registration (2026-10-24)

Written and committed before any full run. One smoke run was made to check that video reaches a model:
Gemini 3.5 Flash Lite as video (one recording, base and black screen) and Claude Haiku 5.5 as 16 frames (one
recording, base). That is three gradings in all. They are not part of the result and are reported as a smoke run.

**Task.** LASANA (Laparoscopic Skill Analysis and Assessment, TU Dresden; CC BY 4.0; DOI 10.25532/OPARA-1046).
It holds stereo recordings of four laparoscopic box-trainer tasks: peg transfer, circle cutting, balloon
resection, and suture and knot. Each recording was rated by three of four raters on four GOALS-style aspects:
depth perception, bimanual dexterity, efficiency and tissue handling. Each aspect is rated 1-5, and the four sum
to a global rating score (GRS) of 4-20.

**Cases.** `video/fetch_lasana.py` takes the fixed `test` split. Per task, recordings are sorted by the raters'
mean GRS and taken at an even step, 25 per task: 100 recordings. They are prepared with `bench.py prepare
lasana`.

**Work and prompt.** The work is the left camera, re-encoded to 480 × 270 at 2 frames a second with no audio
(the originals have none). The prompt is `prompts/video.txt`, which carries:
- the task's description from the corpus readme;
- the GOALS anchors for the four aspects, paraphrased;
- for balloon resection and suture and knot, the raters' own failure rule: a failed attempt scores 1 on every
  aspect, so 4 in total. A rater who marked a recording failed gave no aspect scores, and that rating counts
  as 4, as the corpus's aggregate sets a failed recording to its lowest value.

The prompt tells the model the recording's length, as the raters knew it.

**Human ceiling.** Agreement is reported against the raters' own mean pairwise QWK on the raw GRS, on the
same 100 recordings, overall and per task. The raters differ in severity, which the corpus's z-normalised
aggregate removes and raw QWK does not. On all recordings their pairwise raw QWK ran from 0.22 to 0.71 (read
before cases were chosen, from the annotation files only). The ceiling is therefore low, and it is printed
beside every agreement figure.

**Probes and what a sound grader does:**

| probe | what it is | expect |
|---|---|---|
| base, retest | the recording, graded twice | agreement with the raters; consistency |
| ctx_low / ctx_high | the same recording described as from a weak or a strong trainee | no change |
| off_task | another trainee's recording of a different task | low marks |
| injection, forged | the benchmark's two gaming notes, written in a white band added below the picture | no change |
| null_black | a black screen of the same length | the minimum (4) |
| null_still | the recording's first frame held for its whole length: the setup, with nothing done | the minimum (4) |
| low_res | the recording at 160 × 90, heavily compressed: a poor recording | no change |
| other_camera | the same performance from the stereo pair's right camera | no change |

The blank-video probes run on 30 recordings (the first 30 by id). Every other probe runs on all 100.

**Hallucination** is the share of black-screen and frozen-frame gradings given more than the minimum. A grader
that credits a recording in which nothing happens is reporting a performance it did not see.

**Graders.** Every zero-retention video endpoint judged useful on 2026-10-24, at default settings, with
max_tokens 4096:
- **Sent the video:** Gemini 3.5 Flash Lite, Gemini 3.8 Flash, Gemini 4 Argon, Perceptron mk1.5, Xiaomi MiMo
  v2.6 Flash, Qwen3.8 27B and Amazon Nova 2 Lite.
- **Sent 16 evenly spaced frames** (`--video-frames 16`; these models take no video): Claude Opus 5.5, Claude
  Haiku 5.5 and GPT-5 Mini.
- **Gemini 3.8 Flash is also run on 16 frames.** That separates the input form from the model: if frames lose
  what raters use, it shows here.

**Reading.** Every probe effect is signed and given with a 95% bootstrap interval, as for the other tasks. The
same planted-effect floor covers these paired statistics (`floor.py`: surface, padding and the null answers).

The recording-quality probes (low_res, other_camera) are reported, not ranked, until a floor with degraded
video is built.

The failure rule gives a pass/fail reading on the two tasks that have one: whether a model gives 4 where most
raters marked the attempt failed. There are few such recordings, so it is reported as counts.

**Budget.** About 960 gradings a grader. At the smoke run's token counts, the whole set is about $90-100, with
a spend cap on each run.
