# Sources

Where the benchmark's datasets and methods come from. The site's Sources page is built from this file
(`site/build.py`), and its in-text citations point here by the key in square brackets. Every entry is checked
against its primary record before release: `python3 scripts/check_citations.py docs/SOURCES.md`.

One entry per line: `- [key] Authors YEAR. Title. Venue. URL — used for: what the benchmark uses it for.`
The full method and the wider literature are in the benchmark's research report.

## Student work

- [mohler] Mohler, Bunescu & Mihalcea 2011. Learning to grade short answer questions using semantic similarity measures and dependency graph alignments. ACL 2011. https://aclanthology.org/P11-1076 — used for: the short-answer task (computer science answers, each graded by two teachers).
- [harmogen] Mendonça, Quintal, Mendonça & Baras 2026. The HARMOGEN-R dataset of human and AI-generated rubric evaluations for formative programming assessment. Zenodo. https://doi.org/10.5281/zenodo.19534458 — used for: the code task (programming exercises, each graded by two teachers).
- [asap2] The Learning Agency 2024. ASAP 2.0 (Automated Student Assessment Prize essay corpus). Kaggle. https://www.kaggle.com/datasets/lburleigh/asap-2-0 — used for: the essay task, and the comparison of students identified with a disability.
- [ellipse] Crossley, Tian, Baffour et al. 2023. The English Language Learner Insight, Proficiency and Skills Evaluation (ELLIPSE) Corpus. International Journal of Learner Corpus Research. https://doi.org/10.1075/ijlcr.22026.cro — used for: the fairness comparison between groups of English learners.
- [speechocean] Zhang et al. 2021. speechocean762: An open-source non-native English speech corpus for pronunciation assessment. Interspeech 2021. https://arxiv.org/abs/2104.01378 — used for: the speech task (pronunciation graded by five experts).
- [fleurs] Conneau et al. 2022. FLEURS: Few-shot learning evaluation of universal representations of speech. https://arxiv.org/abs/2205.12446 — used for: the study of how well audio models understand speech in different languages.
- [checkmat] Khrulev 2025. CHECK-MAT: Probing the mathematical reasoning and rubric-alignment of vision-language models on handwritten solutions. MathNLP 2025. https://doi.org/10.18653/v1/2025.mathnlp-main.6 — used for: the handwritten-work task.
- [lasana] Funke et al. 2026. LASANA: a dataset of laparoscopic surgical training videos with skill ratings. https://arxiv.org/abs/2602.09927 — used for: the video tasks (skill ratings by three experts, and spotting a mistake).
- [vtg] Daheim et al. 2024. Stepwise verification and remediation of student reasoning errors with large language model tutors. EMNLP 2024. https://arxiv.org/abs/2407.09136 — used for: the math-working study (solutions with the first wrong step marked by teachers).
- [mathdial] Macina et al. 2023. MathDial: A dialogue tutoring dataset with rich pedagogical properties grounded in math reasoning problems. Findings of EMNLP 2023. https://arxiv.org/abs/2305.14536 — used for: the source of the math-working solutions.
- [gsm8k] Cobbe et al. 2021. Training verifiers to solve math word problems. https://arxiv.org/abs/2110.14168 — used for: the math word problems behind the math-working solutions.

## How results are measured

- [cohen] Cohen 1968. Weighted kappa: Nominal scale agreement with provision for scaled disagreement or partial credit. Psychological Bulletin. https://doi.org/10.1037/h0026256 — used for: agreement with teachers (quadratic weighted kappa).
- [williamson] Williamson, Xi & Breyer 2012. A framework for evaluation and use of automated scoring. Educational Measurement: Issues and Practice. https://doi.org/10.1111/j.1745-3992.2011.00223.x — used for: the three standard checks from automated scoring.
- [act] Wood, Yao, Haisfield & Lottridge 2021. Establishing standards of best practice in automated scoring. ACT. https://act.org/content/dam/act/unsecured/documents/R2100-auto-scoring-standards-2021-07.pdf — used for: the thresholds of the standard checks, as tabulated there.
- [bh] Benjamini & Hochberg 1995. Controlling the false discovery rate: A practical and powerful approach to multiple testing. Journal of the Royal Statistical Society, Series B. https://doi.org/10.1111/j.2517-6161.1995.tb02031.x — used for: the check on results that could be chance.

## Feedback measures

- [mrbench] Maurya et al. 2025. Unifying AI tutor evaluation: An evaluation taxonomy for pedagogical ability assessment of LLM-powered AI tutors. NAACL 2025. https://aclanthology.org/2025.naacl-long.57 — used for: MRBench, the 1,655 tutor replies labeled by trained people, on which every feedback measure was tested.
- [lc] Learning Commons 2025. Evaluators (open-source evaluators of AI tutoring and feedback). https://github.com/learning-commons-org/evaluators — used for: the Withholding Answers and Revision Actionability evaluators tested on MRBench.

## Trained grading methods

- [deberta] He, Gao & Chen 2021. DeBERTaV3: Improving DeBERTa using ELECTRA-style pre-training with gradient-disentangled embedding sharing. https://arxiv.org/abs/2111.09543 — used for: the fine-tuned DeBERTa scorer.
- [sbert] Reimers & Gurevych 2019. Sentence-BERT: Sentence embeddings using Siamese BERT-networks. EMNLP 2019. https://arxiv.org/abs/1908.10084 — used for: the sentence-embedding scorer.
- [minilm] Wang et al. 2020. MiniLM: Deep self-attention distillation for task-agnostic compression of pre-trained transformers. NeurIPS 2020. https://arxiv.org/abs/2002.10957 — used for: the small model behind the sentence-embedding scorer.

## Training data and transparency

- [infinigram] Liu et al. 2024. Infini-gram: Scaling unbounded n-gram language models to a trillion tokens. https://arxiv.org/abs/2401.17377 — used for: searching open training data for the student work.
- [dclm] Li et al. 2024. DataComp-LM: In search of the next generation of training sets for language models. https://arxiv.org/abs/2406.11794 — used for: one of the two training sets searched (its search failed our accuracy check, so it is not used).
- [fmti] Wan, Klyman, Kapoor et al. 2025. The 2025 Foundation Model Transparency Index. https://doi.org/10.70777/si.v2i4.17165 — used for: how much each company discloses.

## Energy

- [jegham] Jegham et al. 2025. How hungry is AI? Benchmarking energy, water, and carbon footprint of LLM inference. https://arxiv.org/abs/2505.09598 — used for: one of the published methods for estimating the energy of a request. The footprint page lists the source of each everyday comparison beside it.
