# Discriminant validity: do graders tell analytic traits apart?

**Asked:** when an AI grader scores six traits of an essay (ELLIPSE: cohesion, syntax, vocabulary,
phraseology, grammar, conventions), does it distinguish them as well as a second human rater, or give one
overall impression six times? Design: `mtmm.py`'s docstring, pre-registered at 272871a.

**Came back: UNANSWERABLE ON ELLIPSE. No model was run.** The floor failed (`out/floor.json`): a simulated
halo grader, one score copied to every trait, read BLURS in 0 of 200 simulations, against a required 90%.
The cause is the reference, not the grader. ELLIPSE's own raters barely separate the traits: matched
against rater 2, rater 1's convergent-minus-discriminant correlation is +0.053 on the draw, and +0.022 to
+0.082 for every pair of traits on all 6,466 essays. A grader that gives one overall impression sits only
about 0.05 below the humans, inside the interval at any affordable sample size.

So the six ELLIPSE traits, as these raters scored them, behave as one proficiency judgement. That is a
finding about the corpus, and a caution for any benchmark that reports per-trait agreement on it: per-trait
QWK there is mostly overall-quality QWK.

**What would answer it:** a corpus whose raters do distinguish traits. The original 2012 ASAP essay sets 7
and 8 carry trait scores from two raters each (ideas, organisation, style, conventions); their terms of use
need checking before they are used here.
