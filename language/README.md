# Language coverage: does an audio grader recognise a correct spoken answer as well in a less common language?

Pre-registered 2026-10-26 in `study.py`'s docstring, before any call. The design, verdicts and floor are there.

**What it asks.** FLEURS has the same sentences read aloud in 102 languages, so the content stays fixed and only
the language varies. For each of 18 languages (six high-, six mid- and six low-resource, tiered before any call),
30 recordings are each paired twice with an English model answer: once with their own sentence (should get 1) and
once with another sentence (should get 0). The gap is accuracy on the high-resource tier minus the low-resource
tier, signed, with a bootstrap over sentences. A model under 0.80 on English is "TASK NOT SUPPORTED".

**Floor** (`out/floor.json`, synthetic, before any call): false alarms 3.5% of 200 null worlds (limit 7%); a planted
10-point gap is detected in 94% (needs 80%). **Passes.**

**Budget.** CHANGE 1 (before any call) raised the cap from $15 to $65: FLEURS clips are 6.4 times longer than
the speech task's, and audio is billed by length.

**Graders.** The six audio models of the speech task, and Gemini 3.5 Flash Lite, added by CHANGE 2 (2026-10-26)
under the coverage rule after the other six models' results were read.

**Results** (`out/language.json`; accuracy is the share of the 60 gradings per language marked correctly).

| model | English | high tier | mid tier | low tier | gap, high minus low [95% interval] | verdict |
|---|---|---|---|---|---|---|
| Perceptron mk1.5 | 1.00 | 0.97 | 0.84 | 0.60 | +0.38 [+0.34, +0.41] | WORSE ON LOW-RESOURCE LANGUAGES |
| Voxtral Small 24B¹ | 0.95 | 0.94 | 0.87 | 0.57 | +0.36 [+0.32, +0.40] | WORSE ON LOW-RESOURCE LANGUAGES |
| MiMo v2.6 Flash | 0.98 | 0.98 | 0.85 | 0.66 | +0.32 [+0.25, +0.38] | WORSE ON LOW-RESOURCE LANGUAGES |
| Gemini 3.5 Flash Lite | 1.00 | 0.98 | 0.97 | 0.84 | +0.14 [+0.10, +0.18] | WORSE ON LOW-RESOURCE LANGUAGES |
| Gemini 3.8 Flash | 0.98 | 0.99 | 0.95 | 0.95 | +0.04 [+0.02, +0.07] | WORSE ON LOW-RESOURCE LANGUAGES |
| Gemini 4 Argon | 0.96 | 0.99 | 0.96 | 0.95 | +0.04 [+0.01, +0.06] | WORSE ON LOW-RESOURCE LANGUAGES |
| Muse Spark Open | 0.93 | 0.96 | 0.96 | 0.94 | +0.01 [−0.02, +0.05] | NO GAP DETECTED (a gap up to 0.05 not ruled out) |

Positive gaps mean worse on the low-resource tier. ¹ Voxtral's run is incomplete: 110 of 1,080 gradings failed.
Of 116 gradings that failed at first (`7a381d2`), an earlier re-send recovered 4; the 112 that remained were all transport failures (68 upstream rate limits, 44 on the API key's spending limit) and
were retried once under CHANGE 3 (committed 2026-10-28 23:12 UTC); 2 succeeded and 110 failed again on Mistral's upstream rate limit.
Failed gradings for the others, all completed replies with no readable mark, which the harness counts and does not
re-ask: Gemini 4 Argon 84 (59 with no mark in the text, 25 empty), Muse Spark 29, Gemini 3.8 Flash 13, MiMo 4.

- **Six of seven graders understand a correct spoken answer less well in a low-resource language.** Perceptron,
  Voxtral and MiMo lose 32-38 points between the high and low tiers, and score 0.50-0.59 (chance is 0.5) on
  their worst language (Yoruba, Amharic or Pashto). The Gemini models lose 4-14 points.
- **Gemini 3.5 Flash Lite is perfect in English and loses 14 points on the low tier.** It says it cannot
  understand a recording 12 times, all on low-resource languages (MiMo and Muse Spark 3 times each, also all low).
- Read speech by adults, with an English model answer: this tests cross-language understanding as well as hearing.

Data: FLEURS dev split (CC BY 4.0), downloaded locally; no audio is committed.
