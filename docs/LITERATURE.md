# Dimensions the benchmark does not yet measure: a literature review (2026-10-23)

A web review run by an agent for this benchmark. It read key abstracts and pages but did not open
most full texts, so some details rest on abstracts or secondary summaries; those are marked. Nothing
here has been independently checked yet, and it is not a precedence sweep in the sense of
`docs/specs/PUBLICATION-READINESS.md`.

## Ranked shortlist of additions

| # | dimension | measurement design | cost to add |
|---|---|---|---|
| 1 | Selective scoring (abstention) | grade each item k = 5 times; use the spread, or a conformal set, as confidence; report QWK against the share of items kept and the human workload saved at a fixed QWK | about 4 extra calls per case |
| 2 | Prompt and rubric paraphrase invariance | 6-9 meaning-preserving rewrites of the prompt; spread in QWK and the per-item flip rate, against the retest floor | one run per paraphrase |
| 3 | Master-key and null answers | blank, ".", "Thought process:", restated question, gibberish; rate of above-zero credit (up to 35% for GPT-4o and 60-90% for some open models, Zhao et al. 2025) | five calls per task |
| 4 | Version drift | frozen anchor set of 20-50 items re-scored each time the benchmark runs; shift against the same-version permutation null; an identity canary | small, repeated |
| 5 | Dialect and first-language counterfactual | rule-based rewrite (e.g. AAVE, learner English) with content fixed; signed shift against a control of the same size | needs careful, validated rewrite rules |
| 6 | Rationale faithfulness | delete the sentences the rationale cites and re-score, against deleting an equal number of random sentences | two extra calls per case |
| 7 | Score-blind vs score-informed feedback | feedback with the mark hidden and shown, both through feedback.py | one extra call per case |
| 8 | Inflation on AI-written answers | generated answers matched to human score bands; inflation, same-family vs cross-family | needs generation and, for a true score, human marks |

Also flagged:
- **Analytic per-criterion scoring and halo** needs trait-scored data (DREsS, ELLIPSE).
- **Human-in-the-loop decision quality** needs a human study (Goulas et al., PNAS Nexus 2026, seen via press coverage only).
- **External validity** needs new data.
- **Energy measured rather than assumed** is possible for open-weight models on metered hardware.
- **Generalisability theory** (Song et al. 2025) would give one dependability coefficient across run, prompt variant and model version, in place of separate retest checks.

## Sources

Peer-reviewed: Williamson, Xi and Breyer 2012 (EM:IP 31(1), seen via citing papers); AERA/APA/NCME
Standards 2014 (https://www.aera.net/Standards); Karim et al., EMNLP 2025
(https://arxiv.org/pdf/2509.15926); Korthals et al., MAKE 8(3):74, 2026; Kortemeyer and Nohl, PRPER
(https://arxiv.org/pdf/2410.19409); Corsi et al., EDM 2026
(https://educationaldatamining.org/edm2026/proceedings/2026.EDM.poster-demo-papers.391/index.html);
Hardy, AIME-Con 2026 (https://arxiv.org/abs/2603.04820); Zhao et al., NeurIPS 2025
(https://arxiv.org/pdf/2507.08794); AAVE math scoring, EDM 2025
(https://educationaldatamining.org/EDM2025/proceedings/2025.EDM.long-papers.195); Meng et al., AIME-Con
2025 WIP (https://aclanthology.org/2025.aimecon-wip.25); Kwako and Ormerod, BEA 2024
(https://aclanthology.org/2024.bea-1.7); Bueno et al., Findings of ACL 2026
(https://preview.aclanthology.org/ingest-acl/2026.findings-acl.375/); Bulut et al., AIME-Con 2026
(https://aclanthology.org/2026.aimecon-sessions.30.pdf); Chamieh, Zesch and Giebermann, BEA 2024
(https://aclanthology.org/2024.bea-1.25); Johnson, ETS RR-25-03
(https://www.ets.org/research/policy_research_reports/publications/report/2025/khni.html).

Preprints and grey literature: Casabianca et al. 2025 (https://arxiv.org/abs/2501.02334); SAS-Bench
(https://arxiv.org/abs/2505.07247); Sunkavalli 2026 (https://arxiv.org/abs/2608.29517); Song, Lee and
Jiao 2025 (https://arxiv.org/abs/2507.19980); Kucia et al. 2026 (https://arxiv.org/abs/2604.00259);
TOEFL L1 study (https://arxiv.org/pdf/2607.14605); Wataoka et al. (https://arxiv.org/pdf/2410.21819);
Hao et al. 2026 (https://arxiv.org/abs/2603.02353); Ofqual, January 2026
(https://ofqual.blog.gov.uk/2026/01/14/using-ai-in-marking-why-technical-capability-fairness-and-transparency-all-matter/);
ITC/ATP Guidelines for Technology-Based Assessment 2022; APA, responsible AI in assessment
(https://www.apa.org/science/programs/testing/responsible-ai-assessment); energy:
https://arxiv.org/pdf/2509.20241, https://arxiv.org/pdf/2601.22076v2.

Not reached or unverified: Goulas et al. (press coverage only); Zhong et al., ETS (repository listing
only); the NCME digital module (via a citing paper); College Board, Pearson, OECD and UNESCO guidance
pages were not opened.
