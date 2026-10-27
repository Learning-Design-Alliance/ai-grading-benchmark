# Do AI graders mark English learners' essays differently by economic status or race, beyond a second human rater?

**Asked:** the ASAP disability study (`../disability/`) matched groups on one released mark. If the
groups differ in true quality, that design reads a gap even for a perfect grader, because any second
noisy reader regresses toward each group's own mean. ELLIPSE (Crossley et al. 2023; CC BY-NC-SA 4.0)
releases both raters' marks. So: matched on rater 1, how large is a second human's own gap, and do
models show a gap beyond it?

**Design:** `gap2.py`'s docstring, pre-registered at 1e31612a before any machine grading. The essays
are matched exactly on rater 1's 1-5 holistic mark:

| contrast | A | B | n per group |
|---|---|---|---|
| C1 (primary) | economically disadvantaged | not economically disadvantaged | 1,000 |
| C2 | Black/African American | White | 465 |
| C3 | Hispanic/Latino | White | 469 |

The statistic is D = the model's gap (M) minus rater 2's gap (H) on the same essays, with a
4,000-draw bootstrap. Graders: Haiku 5.5, Gemini 3.5 Flash Lite, Qwen3 235B (DeepInfra) and GPT-5
Mini, default prompt, zero retention. Spend was $5.07.

**Floor passes** (`out/floor.json`): a planted −0.30 was detected in 94–100% of simulations, with no
false calls at 0, for every contrast and for graders both less noisy and noisier than a person.

## Came back (`out/result.json`)

| grader | C1 economic: D | C2 Black vs White: D | C3 Hispanic vs White: D |
|---|---|---|---|
| Haiku 5.5 | −0.005 [−0.061, +0.051] | −0.049 [−0.133, +0.037] | −0.108 [−0.190, −0.029] |
| Gemini 3.5 Flash Lite | −0.002 [−0.058, +0.052] | −0.078 [−0.164, +0.006] | −0.150 [−0.231, −0.066] |
| GPT-5 Mini | +0.005 [−0.055, +0.063] | −0.060 [−0.146, +0.026] | −0.109 [−0.196, −0.023] |
| Qwen3 235B | −0.020 [−0.075, +0.036] | −0.067 [−0.146, +0.015] | −0.126 [−0.207, −0.045] |
| verdicts | all four NO MORE THAN A SECOND HUMAN | three NO MORE THAN A SECOND HUMAN, Gemini INCONCLUSIVE | all four INCONCLUSIVE |
| H (rater 2's own gap) | +0.000 [−0.063, +0.060] | +0.030 [−0.060, +0.118] | +0.066 [−0.023, +0.160] |

All marks are on the 1-5 scale; negative means the grader marks group A lower. No grading failed in
more than 0.3% of either group.

- **Economic status (primary): no gap.** Every model marks economically disadvantaged and other
  English learners the same as a second human does, within ±0.06.
- **Hispanic vs White: a small gap against Hispanic learners, in all four models.** Every interval lies
  below zero (D −0.11 to −0.15). None lies wholly below the pre-registered −0.10, so the verdict is
  INCONCLUSIVE, not a finding. Four models from four vendors pointing the same way is worth a
  pre-registered replication on new essays. The second human leans the other way, +0.07, interval
  through 0, so the models' gap beyond a human is larger than their raw gap (M −0.04 to −0.08).
- **Black vs White:** no gap shown for three models; Gemini is inconclusive.
- **Matching artefact:** not shown in any contrast. In ELLIPSE the groups' mean marks differ by at
  most 0.13 (rater 1), so a regression artefact is expected to be small here. This does not show that
  the ASAP disability gap is free of it: where groups differ more, the artefact grows. That question
  still needs the individual ASAP/PERSUADE ratings.

No essay text or per-essay mark is committed.

## Replication of the Hispanic vs White signal (`rep.py`, pre-registered at d7216107; `out/rep-result.json`)

ELLIPSE holds only 469 White essays and C3 used all of them, so this replaces the Hispanic side with
1,407 essays C3 did not use (3:1 to the same White essays) and keeps the White side. It can show the
first result was not a fluke of the Hispanic sample; it cannot rule out one of the White sample. One
disclosed change before any grading: the floor failed at a guessed grader noise (k = 1.3) and was
judged at the graders' measured noise (k = 0.97–1.11; it passed at 1.11, 81%). Spend about $4.80 beyond
reused gradings, including runs cut short by a worker restart and resumed from their caches.

| grader | RA: matched on rater 1 (primary), D | RB: raters swapped, D |
|---|---|---|
| Haiku 5.5 | −0.043 [−0.113, +0.025] | +0.044 [−0.024, +0.108] |
| Gemini 3.5 Flash Lite | −0.085 [−0.154, −0.016] | −0.002 [−0.068, +0.063] |
| GPT-5 Mini | −0.040 [−0.112, +0.032] | +0.037 [−0.035, +0.109] |
| Qwen3 235B | −0.054 [−0.123, +0.014] | +0.021 [−0.046, +0.090] |
| DeepSeek V4.1 Flash (generality) | −0.055 [−0.120, +0.012] | +0.016 [−0.051, +0.080] |
| Gemma 4 31B (generality) | −0.067 [−0.131, −0.001] | −0.002 [−0.066, +0.059] |
| second human's own gap (H) | +0.002 [−0.075, +0.077] | −0.097 [−0.177, −0.020] |

**Pre-registered verdict: MIXED.** One of the four primary graders (Gemini) keeps an interval below 0;
three do not, and the rule for DOES NOT REPLICATE (three with intervals through 0 and estimates above
−0.05) is missed by Qwen's −0.054.

**Reading.** The first result does not hold up as a general model bias. With new Hispanic essays the
models' gap beyond a second human roughly halves (−0.04 to −0.09, against −0.11 to −0.15), and with
the raters' roles swapped it vanishes (−0.00 to +0.04). In that arm the human reference itself marks
Hispanic learners 0.10 lower at matched marks, and the models simply agree with it. What remains is
a possible small gap for Gemini, the model with the largest gap in both race contrasts here and in
the ASAP disability study. Because the White sample is shared, it cannot be separated from a property of those 469
essays. ELLIPSE cannot settle this further; a corpus with more White learners and two raters can.

## Added under the coverage rule (`gap2.py` CHANGE 1, `rep.py` CHANGE 2; 2026-10-26, after the results above were read)

Every other leaderboard model with a hosted zero-retention route, default prompt, each with its leaderboard
settings. GPT-6 Astra and Claude Fable 5.1 were added on 2026-10-27 by the maintainer's decision (`gap2.py` CHANGE 2,
`rep.py` CHANGE 3; $321 for both across the three fairness studies; Fable through the maintainers' own Anthropic key
under 30-day safety retention, as on the leaderboard). Claude Opus 5.5 (OpenRouter, zero retention) and Olmo 3.1 32B
(self-hosted: vLLM on a rented RunPod A100, bench.py on the pod against localhost, the pod deleted after) were added
the same day by the maintainer's decision (`gap2.py` CHANGE 3, `rep.py` CHANGE 4). Every board model has now run. The verdicts above are
unchanged; the replication's verdict still rests on its four primary graders (MIXED).

| grader | C1 economic: D | C2 Black vs White: D | C3 Hispanic vs White: D | replication RA: D |
|---|---|---|---|---|
| Claude Opus 5.5 | −0.008 [−0.058, +0.040] | −0.067 [−0.138, +0.008] | −0.136 [−0.207, −0.066] | −0.084 [−0.146, −0.025] |
| Claude Fable 5.1 | +0.014 [−0.037, +0.068] | −0.104 [−0.183, −0.025] | −0.164 [−0.239, −0.086] | −0.129 [−0.191, −0.065] |
| GPT-6 Astra | +0.024 [−0.027, +0.077] | −0.015 [−0.088, +0.062] | −0.083 [−0.164, −0.004] | −0.011 [−0.074, +0.050] |
| DeepSeek V4 Pro | +0.032 [−0.028, +0.094] | −0.088 [−0.178, +0.006] | −0.117 [−0.209, −0.026] | −0.103 [−0.181, −0.026] |
| DeepSeek V4.1 Flash | +0.041 [−0.015, +0.097] | −0.112 [−0.191, −0.030] | −0.115 [−0.196, −0.034] | −0.055 [−0.120, +0.012] |
| DeepSeek V4.1 Flash (Oct 17 snapshot) | +0.028 [−0.029, +0.084] | −0.110 [−0.189, −0.030] | −0.122 [−0.205, −0.041] | −0.100 [−0.167, −0.033] |
| GLM 5.3 | −0.033 [−0.090, +0.024] | −0.052 [−0.131, +0.028] | −0.094 [−0.173, −0.013] | −0.049 [−0.118, +0.018] |
| GLM 5.3 Flash | +0.049 [−0.006, +0.107] | −0.077 [−0.160, +0.003] | −0.110 [−0.192, −0.026] | −0.040 [−0.106, +0.024] |
| GPT-5.6 Luna | −0.007 [−0.065, +0.052] | −0.071 [−0.155, +0.011] | −0.072 [−0.156, +0.009] | −0.060 [−0.129, +0.010] |
| GPT-OSS 20B | +0.001 [−0.065, +0.065] | −0.060 [−0.153, +0.034] | −0.047 [−0.144, +0.051] | −0.011 [−0.092, +0.069] |
| Gemma 4 31B | +0.008 [−0.045, +0.061] | −0.062 [−0.140, +0.015] | −0.136 [−0.213, −0.060] | −0.067 [−0.131, −0.001] |
| Gemma 4 26B A4B | −0.016 [−0.069, +0.037] | −0.047 [−0.125, +0.032] | −0.115 [−0.198, −0.036] | −0.041 [−0.109, +0.027] |
| Gemma 3 27B | −0.021 [−0.079, +0.039] | −0.056 [−0.140, +0.030] | −0.117 [−0.205, −0.032] | −0.062 [−0.129, +0.005] |
| Gemma 3 4B | −0.025 [−0.085, +0.034] | −0.064 [−0.149, +0.025] | −0.119 [−0.203, −0.030] | −0.060 [−0.128, +0.015] |
| Ministral 8B | −0.036 [−0.092, +0.021] | −0.062 [−0.146, +0.026] | −0.124 [−0.207, −0.041] | −0.056 [−0.126, +0.012] |
| Phi-4 | −0.042 [−0.106, +0.024] | −0.060 [−0.155, +0.032] | −0.062 [−0.158, +0.032] | −0.035 [−0.118, +0.050] |
| Olmo 3.1 32B | −0.039 [−0.095, +0.020] | −0.103 [−0.185, −0.022] | −0.096 [−0.179, −0.013] | −0.055 [−0.126, +0.014] |
| Llama 3.2 3B | −0.072 [−0.145, −0.001] | −0.024 [−0.129, +0.082] | −0.030 [−0.132, +0.072] | −0.027 [−0.112, +0.058] |

DeepSeek V4.1 Flash and Gemma 4 31B were already replication graders; their RA figures are those above.

- **Economic status: no gap for any of the 22 graders** (NO MORE THAN A SECOND HUMAN for all). Llama 3.2 3B's
  interval just excludes 0 (−0.072), within the ±0.15 band.
- **Hispanic vs White: the first draw's pattern holds across vendors.** 18 of the 22 graders have D's interval
  below 0 on C3 (estimates −0.08 to −0.16); none lies wholly below −0.10, so every one is INCONCLUSIVE or NO
  MORE THAN A SECOND HUMAN (GPT-OSS 20B and Llama 3.2 3B). On the replication's new Hispanic essays, five of
  the added graders keep an interval below 0 (Claude Fable 5.1, Claude Opus 5.5, DeepSeek V4 Pro, the DeepSeek
  V4.1 Flash Oct 17 snapshot, and Gemma 4 31B, as before); the rest pass through 0. The White-sample caveat above applies to all.
- **Claude Fable 5.1 has the largest gap against Hispanic learners of any grader**: −0.164 [−0.239, −0.086] on
  C3 and −0.129 [−0.191, −0.065] on the replication, and it is the only grader whose gap stays below 0 with the
  raters' roles swapped (RB −0.061 [−0.122, −0.003]). Its verdicts remain INCONCLUSIVE: no interval lies wholly
  below the pre-registered −0.10. GPT-6 Astra shows a smaller C3 gap (−0.083 [−0.164, −0.004]) that disappears on
  the replication (−0.011 [−0.074, +0.050]).
- **Black vs White:** four added graders (Claude Fable 5.1, Olmo 3.1 32B, DeepSeek V4.1 Flash and its Oct 17
  snapshot) have intervals below 0 (−0.10 to −0.11), INCONCLUSIVE under the thresholds; the rest pass through 0.
- **Claude Opus 5.5, first on the leaderboard,** shows the shared Hispanic-vs-White pattern: −0.136 [−0.207, −0.066]
  on C3 and −0.084 [−0.146, −0.025] on the replication, gone with the raters' roles swapped (−0.009). No gap on
  economic status or Black vs White.
