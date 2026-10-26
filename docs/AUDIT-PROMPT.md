# Independent audit prompt

Give this to an agent or person with no part in the work, before a card, report, README or paper leaves the
team, and after any wording sweep (`docs/METHODOLOGY.md` §5.3). First used 2026-10-26: 15 of about 95 claims in
the benchmark card failed.

---

Independent audit of <DOCUMENT>. Do not edit any file; report only.

Every number, verdict and factual claim in it should be traceable to a committed source in the repository: study
READMEs, `docs/`, and the JSON outputs (`out/`, each study's `out/`).

For each claim:
1. Find its source and check the number matches. It must be rounded once from the unrounded source: watch for
   double rounding (0.2948 to 0.295 to 0.30; 1.025 to 103%).
2. Check the direction and sign are stated correctly, and that a verdict label agrees with the sign of its number.
3. Check every count ("17 of 22") against the current data. A claim true of an earlier, smaller population may be
   stale.
4. Flag:
   - claims with no source;
   - claims contradicted elsewhere in the document or by `docs/CORRECTIONS.md`;
   - stale figures that a newer study supersedes;
   - shares given without their denominator;
   - wording that overstates a result: a null read as "no effect" or "ties", a descriptive figure presented as a
     verdict, a finding from one subset stated for all.

Out of scope: style, and whether the studies are well designed.

Report as a list, most serious first. For each: the document's exact text, what the source says (file and value),
and the fix you suggest. End with the number of claims checked and how many passed.
