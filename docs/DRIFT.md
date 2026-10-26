# Watching a grader drift

Providers update hosted models without changing their names, and an AI grader whose marks move
without anyone noticing is the failure a school would least expect. The benchmark watches for it in
two ways.

## 1. The same model over time (monitoring)

Run the anchor battery when you adopt a model and again on a schedule, for example monthly or
whenever the provider announces an update:

    python3 bench.py run --battery anchor --cases <cases.jsonl> --model <m> --base-url ... --out runs/<m>-<date> --go
    python3 bench.py drift runs/<m>-<first date> runs/<m>-<today>

The anchor battery is 30 fixed cases (stratified on the human mark, so the same cases every time for
the same file), each graded three times. `drift` reports:
- the mean shift in marks, B minus A, with a 95% bootstrap interval; DRIFT means the interval excludes 0;
- QWK between the two dates beside QWK between two calls on the same date. Marks that agree less
  across dates than within one date have changed even if their mean has not;
- the model id each provider reported serving, as an identity canary: a different id under the
  same name is itself a finding.

A single anchor run costs cents on most models. Pin the provider (`provider.order` with fallbacks
off on OpenRouter), or a backend switch will look like drift.

## 2. Older releases of the same family (improvement over time)

Run the core battery on the same cases for each release still served. `bench.py compare A B` gives
paired differences in agreement and in the attainment effect, and `drift A B` the mean shift. The
first lineage runs (2026-10-23) cover GPT-4o-mini, GPT-4.1-mini, GPT-5-mini and GPT-5.6 Luna; Claude
Haiku 4.5 and 5.5; Gemini 2.5 and 3.5 Flash Lite; Qwen 2.5 72B and Qwen3 235B; DeepSeek V3 and V4.1
Flash, all on Mohler short answers.

What this cannot do is recover a model version that is no longer served. A drift history starts on
the day the first anchor run is kept, so keep the run folders (they hold no student work beyond
what the cases file already has; keep them out of version control anyway).

## First lineage results (2026-10-23, `out/lineage-2026-10-23/`)

Core battery, default prompt, the same 100 Mohler cases for every model (human ceiling 0.573 [0.374, 0.734] on this draw; with an interval that wide, no model here is shown to beat the humans).
Gemini 2.5 Flash Lite has no zero-retention endpoint and is not included. The Fable API row ran through OpenRouter with a bring-your-own
Anthropic key (zero retention). The agent-pilot row (`out/agent-pilot-2026-10-23/`) graded the same
cases as prompt-only subagent batches and agreed with the API almost exactly (QWK 0.632 against
0.631); it differed on blicket (+0.05 against −0.31). Fable's content filter refused all 30 gibberish
answers; a refusal is not credit.

| model | QWK | share of ceiling | polite request | forged override | blicket | label 8 vs 3 | $/1k |
|---|---|---|---|---|---|---|---|
| Claude Haiku 4.5 | 0.675 | 118% | **+0.79** | −0.54 | −0.78 | +0.09 | 0.46 |
| GPT-5.6 Luna | 0.644 | 112% | +0.25 | +0.03 | −0.06 | +0.05 | 0.13 |
| DeepSeek V4.1 Flash | 0.643 | 112% | +0.24 | +0.07 | −0.19 | +0.17 | 0.15 |
| Fable 5.1 (API, BYOK) | 0.631 | 110% | −0.11 | −0.16 | −0.31 | +0.03 | 6.76 |
| Fable (agent pilot) | 0.632 | 110% | +0.13 | +0.08 | +0.05 | — | — |
| GPT-5 Mini | 0.630 | 110% | +0.09 | +0.13 | −0.05 | +0.11 | 0.58 |
| Qwen 2.5 72B | 0.617 | 108% | **+1.28** | **+1.48** | −0.95 | +0.15 | 0.07 |
| Claude Haiku 5.5 | 0.603 | 105% | +0.02 | +0.03 | −0.31 | +0.04 | 0.11 |
| Qwen3 235B | 0.602 | 105% | **+1.27** | **+1.52** | −1.33 | +0.20 | 0.04 |
| GPT-4.1 mini | 0.585 | 102% | +0.33 | +0.78 | −0.86 | +0.09 | 0.13 |
| DeepSeek V3 | 0.573 | 100% | **+1.10** | +0.40 | −0.80 | +0.03 | 0.08 |
| Gemini 3.5 Flash Lite | 0.547 | 96% | +0.44 | +0.34 | −0.39 | −0.06 | 0.13 |
| GPT-4o mini | 0.531 | 93% | +0.47 | +0.67 | −0.97 | +0.02 | 0.04 |

Effects are in marks out of 5. No model credited any of the five blank or master-key answers.

**Newer is not uniformly better.** OpenAI's line improves at each step (0.531 → 0.585 → 0.630 →
0.644) and becomes much harder to game. DeepSeek's does too. Haiku 5.5 agrees with the humans
less than 4.5 did (0.603 against 0.675), but it no longer responds to a polite request for marks
(+0.02 against +0.79). Qwen's newer release is no better on either count.

**An upgrade moves marks by about half a mark** (`out/lineage-2026-10-23/drift.txt`):

| from → to | mean shift (B − A) | QWK across versions | QWK within A, asked twice |
|---|---|---|---|
| GPT-4o mini → GPT-4.1 mini | +0.24 [+0.09, +0.40] | 0.829 | 0.920 |
| GPT-4.1 mini → GPT-5 Mini | +0.34 [+0.14, +0.55] | 0.743 | 0.956 |
| GPT-5 Mini → GPT-5.6 Luna | −0.09 [−0.24, +0.04] | 0.895 | 0.970 |
| GPT-4o mini → GPT-5.6 Luna | +0.49 [+0.29, +0.70] | 0.728 | 0.920 |
| Haiku 4.5 → Haiku 5.5 | −0.49 [−0.66, −0.33] | 0.802 | 0.983 |
| Qwen 2.5 72B → Qwen3 235B | −0.04 [−0.19, +0.09] | 0.855 | 0.908 |
| DeepSeek V3 → V4.1 Flash | +0.13 [−0.06, +0.35] | 0.806 | 0.901 |

Every upgrade agrees with its predecessor less than the predecessor agrees with itself, including
the three with no significant mean shift. A school that switches model versions under the same
prompt should expect individual marks to change even where the average does not.

## A snapshot under a new name (2026-10-25)

DeepSeek published a 17 October snapshot of V4.1 Flash (`deepseek/deepseek-v4.1-flash-1017`) described only as a
"minor update". The board already held the 10 September release, graded on 24 October. The same 100 cases per
task, default prompt, base probe (`bench.py drift`):

| task | mean shift, 17 Oct − 10 Sep | QWK across versions | QWK within 10 Sep, asked twice |
|---|---|---|---|
| short answers (0-5) | −0.07 [−0.16, +0.02] | 0.962 | 0.963 |
| essays | −0.09 [−0.19, +0.01] | 0.831 | 0.821 |
| code (0-90) | **+1.69 [+0.67, +2.74]** | 0.957 | 0.947 |
| code, 17 Oct pinned to DeepInfra | **+1.79 [+0.63, +3.02]** | 0.948 | 0.947 |

- **The snapshot marks code about 2% of the scale higher.** The order of the work is unchanged: the two versions
  agree with each other as well as one version agrees with itself. Short answers and essays did not move.
- **It is the model, not the host.** The 10 September run was served by DeepInfra alone and the 17 October run
  by six hosts, so the 17 October code grading was repeated on DeepInfra alone ($0.07). The shift stayed.
- DeepSeek's own API serves the snapshot under the plain name `deepseek-flash` (OpenRouter's model page). A school
  calling that name changed versions with no notice beyond "minor update".

## Monthly watch (from 2026-11-01)

`drift/monitor.py` (pre-registered; its docstring holds the design and two changes) grades the board's 100 cases per
task, once, for every board model with a zero-retention route, on the 1st of each month. It keeps only the marks,
in `drift/out/<date>/`. Each month is compared with the baseline month (2026-10-26). DRIFT means the 95% interval of the
mean shift excludes 0; a shift of 2% of the scale or more is "material". The floor detects a planted 2% shift in
85-89% of draws. Claude Fable 5.1 and Olmo 3.1 32B have no hosted zero-retention route and are not watched. About
$13-15 a month (GPT-6 Astra alone about $7), capped at $20. Results are added below as they come.
