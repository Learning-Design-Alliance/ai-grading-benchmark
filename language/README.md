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

**Results.** Running.

Data: FLEURS dev split (CC BY 4.0), downloaded locally; no audio is committed.
