# Speech task: pre-registration (2026-10-24)

Written before any full run. One smoke run (2 cases, Gemini 3.8 Flash, 18 gradings) was made to check the
audio reaches the model; it is not part of the result and is reported as such.

**Task.** speechocean762 (CC BY 4.0, OpenSLR 101): 5,000 English sentences read aloud by Mandarin-L1
speakers (2,440 children, 2,560 adults), each scored independently by five experts. Trait: sentence-level
pronunciation accuracy, 0-10. Cases: `bench.py prepare speechocean`; draw `bench.py` sample, n = 100, seed 7.
Prompt: `prompts/speech.txt` (the corpus's own rubric).

**Probes and what a sound grader does:**

| probe | what it is | expect |
|---|---|---|
| base, retest | the recording, graded twice | agreement with the five experts; consistency |
| ctx_low / ctx_high | the same recording described as from a weak or strong learner | no change |
| off_task | another speaker's recording of a different sentence | low marks |
| null_silence | silence of the same length | the minimum (0) |
| null_tone | a 440 Hz tone of the same length | the minimum (0) |
| noise_10db | white noise mixed in at 10 dB SNR | no change (the experts scored the clean recording) |
| phone_band | band-limited to a telephone channel (8 kHz, 300-3,400 Hz) | no change |

**Hallucination** is the share of silence and tone gradings given more than the minimum: a grader that
credits a recording with no speech in it is reporting speech it did not hear.

**Graders** (every zero-retention audio endpoint found on 2026-10-24): Gemini 3.8 Flash, Gemini 4 Argon,
Xiaomi MiMo v2.6 Flash, Meta Muse Spark Open, Perceptron mk1.5, Mistral Voxtral Small. Default settings,
max_tokens 4096.

**Reading.** Agreement is reported as a share of the experts' own agreement (mean pairwise QWK over the five).
Every probe effect is signed with a 95% bootstrap interval, as for the text tasks; the same planted-effect
floor covers these paired statistics (`floor.py`: surface, padding and the null answers). Recording-quality
probes are reported, not ranked, until a floor with degraded audio is built.

## CHANGE 1 (2026-10-26, after the six graders' results were read; before any call for the grader it adds)

Added under the maintainer's coverage rule (2026-10-26: every leaderboard model runs every task its inputs
allow), not because of any result: Gemini 3.5 Flash Lite, the one leaderboard model that takes audio (it has a
zero-retention endpoint; it was not among the graders chosen on 2026-10-24). Cases, prompt, probes, seed and
max_tokens 4096 unchanged; zero retention. Budget: about $1.
