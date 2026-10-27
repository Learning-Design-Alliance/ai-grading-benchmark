# Reasoning and repeatability

Three checks, pre-registered in `study.py` before any call. Results are in `out/` (`signal.json`, `runs.json`,
`signal-floor.json`). Spend was $30.32 on the noise floor and $45.97 on the effort sweep, within the
pre-registered $130 cap. Claude Fable 5.1 ran through the maintainers' own Anthropic key under its 30-day safety
retention (it has no zero-retention route; public corpora only). Every other call was pinned to
zero-retention endpoints.

## 1. Does reasoning length flag uncertain marks?

No calls: from the leaderboard's own gradings. The floor passed: 81-95% of planted signals were detected,
with 2-3% false alarms. Nine models report no reasoning tokens, so only the remaining ones were checked
(15 model-task pairs).

**Gradings a model reasoned longer about are the ones that change on a second try.** Reasoning tokens predict a
changed retest mark with an AUC of 0.72-0.90 for 12 of the 15 pairs. A system could route long-reasoning
gradings to a person at no extra cost.

**Predicting a large error against the experts (more than a fifth of the scale) is weaker.**

| model | task | AUC for a large error [95% interval] | errors | verdict |
|---|---|---|---|---|
| DeepSeek V4.1 Flash | short answers | 0.75 [0.65, 0.84] | 22 | FLAGS ITS OWN ERRORS |
| DeepSeek V4.1 Flash | code | 0.76 [0.64, 0.88] | 18 | FLAGS ITS OWN ERRORS |
| GPT-5 Mini | short answers | 0.71 [0.60, 0.81] | 22 | FLAGS ITS OWN ERRORS |
| GPT-5.6 Luna | code | 0.73 [0.61, 0.84] | 24 | FLAGS ITS OWN ERRORS |
| Claude Haiku 5.5 | code | 0.70 [0.56, 0.82] | 15 | FLAGS ITS OWN ERRORS |
| GPT-6 Astra | code | 0.75 [0.55, 0.92] | 6 | FLAGS ITS OWN ERRORS (thin) |
| Claude Opus 5.5 | code | 0.80 [0.71, 0.87] | 1 | FLAGS ITS OWN ERRORS (too thin to read) |

Every other pair reads NO SIGNAL DETECTED. Many of them have few large errors to predict: Opus and Fable have one or
two per task. **Added after the results:** a cell with fewer than 10 errors is marked thin and not read. The
pre-registration set no minimum.

## 2. How much does a mark wander? (noise floor)

25 cases per task, each graded five times, fresh calls. The mean within-case SD is given as a share of the
scale. "Varied" is the share of cases whose five marks were not all equal.

| | short answers | code | essays |
|---|---|---|---|
| steadiest | Gemma 3 4B 0.0%, 0% varied | GPT-6 Astra 0.5% | GPT-6 Astra, Qwen3 0.4% |
| frontier | Opus 3.1%, Fable 2.7%, Astra 1.1% | Fable 1.2%, Opus 1.6% | Opus 1.5%, Fable 1.6% |
| least steady | Llama 3.2 3B 15% (every case varied) | Llama 3.2 3B 17% | GPT-OSS 8.7% |

- **For most models a mark moves by 1-4% of the scale between gradings of the same work.** That is the floor
  against which any probe effect on the board is read.
- **The small models wander most.** Llama 3.2 3B's largest single swing covers 80-100% of the scale. Phi-4
  and GPT-OSS reach 40-80%.
- **Five-repeat agreement** (mean pairwise QWK) is 0.95-1.00 for most models, and 0.58-0.66 for the least
  steady.

## 3. Does paying for more reasoning buy better marking?

Low against high effort, paired over cases. Corrected 2026-10-27: marks are no longer rounded half-to-even before agreement is computed (study.py CHANGE 1); no verdict changed. Agreement is QWK with the raters. The default run is shown in
`runs.json` but is not part of the verdict.

| model | short answers, low → high | verdict | code, low → high | verdict |
|---|---|---|---|---|
| GPT-5 Mini | 0.69 → 0.69 | no detected change | 0.68 → 0.89 (+0.21 [0.10, 0.37]) | **HELPS** |
| Claude Fable 5.1 | 0.69 → 0.68 | no detected change | 0.81 → 0.95 (+0.16 [0.10, 0.27]) | **HELPS** |
| Gemini 3.5 Flash Lite | 0.65 → 0.62 | no detected change | 0.77 → 0.87 (+0.10 [0.01, 0.22]) | **HELPS** |
| Claude Haiku 5.5 | 0.64 → 0.65 | no detected change | 0.80 → 0.88 (+0.07 [0.01, 0.16]) | **HELPS** |
| GPT-6 Astra | 0.69 → 0.72 (+0.031 [+0.0002, +0.064]) | **HELPS** | 0.89 → 0.86 | no detected change |
| Claude Opus 5.5 | 0.72 → 0.72 | no detected change | 0.92 → 0.92 | no detected change |
| GPT-5.6 Luna | 0.67 → 0.69 | no detected change | 0.73 → 0.78 | no detected change |
| DeepSeek V4.1 Flash | 0.64 → 0.64 | no detected change | 0.79 → 0.81 | no detected change |
| Gemma 4 31B | 0.66 → 0.68 | no detected change | 0.90 → 0.89 | no detected change |
| Gemma 4 26B | 0.66 → 0.64 | no detected change | 0.65 → 0.63 | no detected change |
| GPT-OSS 20B | 0.61 → 0.61 | no detected change | 0.02 → 0.31 | no detected change (see below) |

**Reading.**
- **More reasoning helps on code, not on short answers.** Four of eleven models mark code markedly better at
  high effort. On short answers only GPT-6 Astra gains, and slightly. No model marks worse.
- **Reasoning can stop gaming.** Gemini 3.5 Flash Lite gives a forged "grading override" note on code +59% of
  the scale at its default setting and +27% at low effort, but −0.8% at high effort. DeepSeek goes from +9% at
  low effort to −2% at high. Effort is a setting a buyer controls, so the board's gaming flags hold only at the
  setting tested (the default).
- **The default may not be what you think.** Gemma 4 does not reason at its default setting. Asking for any
  effort switches reasoning on, and code agreement jumps: Gemma 4 31B from 0.48 to 0.89-0.90, Gemma 4 26B from
  0.45 to 0.63-0.65. Its board row reflects the default.
- **GPT-OSS 20B on code** gives 0 to 40 of 50 answers at low effort. At high effort, 15 of 50 gradings run out
  of the 4,096-token budget and return no mark. The comparison uses only cases graded at both levels, and the
  interval reaches 0.
- **Cost.** High effort costs from about the same as low effort (Gemma 4) to about 7 times as much
  (Gemini 3.5 Flash Lite on short answers), through reasoning tokens.

**Limits.**
- Two tasks, 100 short answers and 50 code cases.
- One run per level. "Low" and "high" mean different things for each vendor.
- The default runs were graded earlier, some through other routes, so they are context, not a third level.
