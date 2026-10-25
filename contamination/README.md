# Are the student texts in open training data?

The design, controls and verdicts are pre-registered in `search.py`'s docstring. CHANGE 1 there fixed the
span selection after the first run failed its own check; that run is kept as `out/search-run1.json`.

**Method.** Two random 13-word spans from each case's student text were searched for exactly in two open
training sets with infini-gram. A case counts as found if either span occurs.

**Self-check.** Spans copied from the training set itself must be found at least 90% of the time. Spans
from this repository's October 2026 documents, which cannot be in a 2024 crawl, must be found at most 5%.
- **OLMo 2 32B Instruct's full training data:** 90% and 0%. It passes, at the bar.
- **DCLM-baseline:** 88% and 0%. It fails narrowly, so its results are UNMEASURED, as pre-registered.

**Result, OLMo 2's training data:**

| task | answers found | 95% interval | cases searchable | questions found | verdict |
|---|---|---|---|---|---|
| short answers | 1 of 57 (2%) | 0-9% | 57 of 100 | 1 of 11 | NOT DETECTED |
| essays | 4 of 100 (4%) | 2-10% | 100 | 0 of 7 | NOT DETECTED |
| code | 0 of 34 | 0-10% | 34 of 100 | 0 of 3 | NOT DETECTED |
| maths (student-like solutions) | 15 of 200 (8%) | 5-12% | 200 | 178 of 178 | NOT DETECTED (lower bound 4.6%, below the 5% bar) |

**Reading.**
- **The students' own words are rarely in this training set.** At most about a tenth of short answers,
  essays or code answers occur verbatim, so agreement on these tasks is unlikely to come from memorised
  answers, for this model at least.
- **The maths problems are.** Every question is in OLMo 2's data, as GSM8K is widely used in training, and
  about one solution in twelve. The maths task tests whether graders read working, not whether they can
  solve the problem, so a memorised question matters less. A model that recognises the problem could
  still check the final answer against a remembered one.
- **The limits.**
  - A miss here does not clear a closed model, which may have trained on more, including these corpora
    directly.
  - Only exact 13-word matches are found, not paraphrases.
  - Short answers and code are often too short or too fragmented to search: 43 and 66 of 100 had no line of
    14 words.
  - No index of Olmo 3's data is offered, so the board's candidate model is not covered.

Output: `out/search.json`.
