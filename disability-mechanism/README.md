# Is the shared disability gap a measurement artifact, and do length and convention errors carry it?

Pre-registered in `study.py` (2026-10-27) before any result was computed. Output: `out/mechanism.json`; the floor
is `out/floor.json`. No calls: a reanalysis of the 22 default-prompt runs of `disability/gap.py` on its 3,000
ASAP 2.0 essays (1,500 by students identified with a disability, 1,500 not, matched on the human mark). Suggested
by the literature review (analysis 5; Johnson, Liu and McCaffrey 2022; Buzick et al. 2016; Kucia et al. 2026).
Reads the ASAP 2.0 corpus locally; only aggregates are committed.

**Question.** Twenty of the 22 models mark the identified group's essays lower than other essays with the same
human mark (SHARED GAP, `disability/README.md`). Is that (A) what measurement error alone would produce, or
(B) carried by essay length and convention errors?

## (A) Reverse regression: UNMEASURED

The test asks whether, at the same *machine* mark, the identified essays get higher human marks (the model
under-marks them) or lower ones (both measures agree the essays are weaker, as measurement error predicts).

**The floor failed, so every model reads UNMEASURED.** In simulations shaped like this corpus (each group's real
mark distribution, a model residual SD of 0.875 marks, gap.py's matched draw), a model biased against the group
by 0.30 marks was detected in 0% of 200 simulations, and one biased by 0.50 marks also in 0%. Measurement error
pushes the reverse coefficient so far below zero that a bias of the observed size cannot turn it positive. The design cannot separate a model bias of the size observed from measurement error.

The real coefficients are all negative (−0.08 to −0.59, `out/mechanism.json`), which is what both readings
predict. They are descriptive only. **What would settle (A)** is unchanged: the two pre-adjudication ratings per
essay, or new human ratings on a sample.

## (B) Surface features: they carry part of the gap for every model, not most of it

Two rule-coded features per essay, **proxies, not validated constructs** (no person or model coded them):
length, log(1 + words); and convention errors per 100 words (misspellings by pyspellchecker 0.8.1's English
dictionary, excluding words in the assignment's own prompt and sources; standalone lowercase "i"; sentences
opening in lowercase). The floor passed: a gap planted entirely through convention errors read MOST in 90.5% of
simulations; a gap planted with the features unused read PART or MOST in 2%.

**At the same human mark, the identified group's essays carry 0.95 more convention errors per 100 words** (4.43
against 3.48 overall) **and are 7.7 words shorter.** Every one of the 22 models gives less to an essay with more
convention errors at the same human mark (coefficients −0.016 to −0.078 marks per error per 100 words, every
interval below 0).

| model | gap (matched on the human mark) | gap at equal length and convention errors | share the features account for [95%] | verdict |
|---|---|---|---|---|
| Llama 3.2 3B | −0.214 | −0.144 | 0.32 [0.22, 0.50] | PART |
| DeepSeek V4 Pro | −0.275 | −0.217 | 0.21 [0.16, 0.28] | PART |
| Olmo 3.1 32B | −0.247 | −0.197 | 0.20 [0.15, 0.26] | PART |
| Qwen3 235B | −0.212 | −0.170 | 0.20 [0.13, 0.28] | PART |
| GPT-5.6 Luna | −0.202 | −0.163 | 0.19 [0.13, 0.27] | PART |
| Claude Fable 5.1 | −0.247 | −0.206 | 0.17 [0.13, 0.21] | PART |
| GPT-6 Astra | −0.217 | −0.182 | 0.16 [0.11, 0.22] | PART |
| GPT-5 Mini | −0.172 | −0.145 | 0.16 [0.10, 0.23] | PART |
| Gemma 3 27B | −0.247 | −0.212 | 0.14 [0.10, 0.20] | PART |
| Gemini 3.5 Flash Lite | −0.429 | −0.373 | 0.13 [0.10, 0.17] | PART |
| Phi-4 | −0.279 | −0.244 | 0.13 [0.09, 0.18] | PART |
| DeepSeek V4.1 Flash (Oct 17) | −0.270 | −0.236 | 0.13 [0.09, 0.18] | PART |
| Claude Opus 5.5 | −0.219 | −0.193 | 0.12 [0.08, 0.16] | PART |
| DeepSeek V4.1 Flash | −0.333 | −0.294 | 0.12 [0.08, 0.16] | PART |
| Gemma 4 26B A4B | −0.347 | −0.308 | 0.11 [0.08, 0.15] | PART |
| GPT-OSS 20B | −0.232 | −0.207 | 0.11 [0.07, 0.16] | PART |
| Claude Haiku 5.5 | −0.166 | −0.147 | 0.11 [0.07, 0.17] | PART |
| Gemma 4 31B | −0.235 | −0.213 | 0.10 [0.06, 0.15] | PART |
| GLM 5.3 Flash | −0.393 | −0.355 | 0.10 [0.07, 0.13] | PART |
| GLM 5.3 | −0.367 | −0.335 | 0.09 [0.06, 0.12] | PART |

PART = SURFACE FEATURES ACCOUNT FOR PART OF THE GAP. Gemma 3 4B and Ministral 8B have no replicated gap and are
not tested (shares 0.40 and 0.24, descriptive). The gap columns are machine marks, identified minus not, in
points of the 1-6 scale. The interval resamples essays within each group (2,000 draws).

**Reading.**
- **Every model penalizes convention errors more than the human raters did** at the same mark, and the
  identified group makes more of them. That carries 9% to 32% of each model's gap.
- **Most of the gap remains** at equal length and convention errors: from −0.14 (Llama 3.2 3B) to −0.37 (Gemini
  3.5 Flash Lite), every interval below 0 (`gap_B1` in `out/mechanism.json`).
- The features are crude proxies, so this is a lower bound on what surface features carry, not a measure of it:
  a better measure of conventions could account for more.
- Whether the remaining gap is a model bias or the human marks' measurement error is still open: part (A) could
  not test it.

**Limits.** One released mark per essay. Rule-coded features. One corpus.
