# Multimodal assessment fairness: skin tone, accent, language coverage

*Compiled 2026-10-26 by an agent from primary sources; each source is marked VERIFIED (page or abstract opened)
or UNVERIFIED. `scripts/check_citations.py` on this file: 27 OK, 3 unchecked (NIST, Vice, ETS pages it cannot
parse), 1 unresolved (Koenecke et al., PNAS: the page did not resolve for the checker), 1 flagged mismatch that is
not an error (Ardila et al.: LREC 2020, arXiv preprint 2019). Not a precedence sweep.*

Literature and dataset scan for extending the AI grading benchmark to video and speech. Compiled 2026-10-26.

**Verification key.** VERIFIED means the abstract or landing page (or the primary PDF) was opened during this
scan and states what is summarised here. UNVERIFIED means the claim comes only from secondary reporting or a
search-index snippet, or the primary page could not be opened. Numbers are quoted only where the opened page gave
them. Where the page gave no numbers, the entry says so. Do not cite anything from here without reopening it.

---

## 1. Skin tone and complexion (face detection, exposure, VLM descriptions)

### Classic audits

- **Buolamwini, J. & Gebru, T. (2018). "Gender Shades: Intersectional Accuracy Disparities in Commercial Gender
  Classification." Proc. FAT\* 2018, PMLR 81:77–91.** https://proceedings.mlr.press/v81/buolamwini18a.html
  Across three commercial gender classifiers, darker-skinned females had error rates of up to 34.7%, against a
  maximum of 0.8% for lighter-skinned males. Skin type was labelled on the Fitzpatrick scale. **VERIFIED**

- **Grother, P., Ngan, M. & Hanaoka, K. (2019). "Face Recognition Vendor Test (FRVT) Part 3: Demographic Effects."
  NISTIR 8280.** https://nvlpubs.nist.gov/nistpubs/ir/2019/NIST.IR.8280.pdf
  False-positive differentials are much larger than false-negative ones. Across demographic groups they "often
  vary by factors of 10 to beyond 100 times". On application photos, false positives were highest for West and
  East African and East Asian people. With some algorithms developed in China, East Asian faces showed low false
  positives instead. Women, the elderly and children also had higher false positives. **VERIFIED** (PDF text
  extracted)

- **Dooley, S., Wei, G. Z., Goldstein, T. & Dickerson, J. (2022). "Robustness Disparities in Face Detection."
  NeurIPS 2022 Datasets and Benchmarks.**
  https://proceedings.neurips.cc/paper_files/paper/2022/hash/f9faef4e1b4dbbd48ef60056ffe14c90-Abstract.html
  (preprint: Dooley, Goldstein & Dickerson, "Robustness Disparities in Commercial Face Detection", arXiv:2108.12508).
  This benchmark tests how commercial and academic face detectors hold up under noise. Photos of people who are
  "masculine presenting, older, have darker skin types, or are in dim lighting" are more susceptible to errors.
  Face detection is the step a video grader runs first. The abstract gives no numbers. **VERIFIED**

### Exposure, cameras and proctoring

- **Yoder-Himes, D. R., Asif, A., Kinney, K., Brandt, T. J., Cecil, R. E., Himes, P. R., Cashon, C., Hopp, R. M. P.
  & Ross, E. (2022). "Racial, skin tone, and sex disparities in automated proctoring software." Frontiers in
  Education 7:881449.** https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2022.881449/full
  - Setting: Respondus Monitor, about 357 students in four STEM courses at the University of Louisville in Fall
    2020. The authors coded 298 videos.
  - Face detection averaged about 78% for darker-skinned students, 87% for medium and 92% for lighter.
  - Flags per assessment averaged 6.07 for darker-skinned students, 1.91 for medium and 1.19 for lighter.
  - Darker-skinned students were 5.6 times more likely than lighter-skinned students to get a "low facial
    detection" flag.
  - Coded cheating behaviour did not differ by skin tone.
  - Caveat: skin-tone coding had low inter-rater reliability, so the authors merged categories.

  This is the most directly relevant educational evidence. **VERIFIED**

- **Feathers, T. (2021, Apr 8). "Proctorio Is Using Racist Algorithms to Detect Faces." Vice/Motherboard.**
  https://www.vice.com/en/article/proctorio-is-using-racist-algorithms-to-detect-faces/
  Researcher Lucy Satheesan found that Proctorio's face detector matched OpenCV models. On about 11,000 FairFace
  images it failed to detect a face in 57% of images of Black faces, against 40% for white and 33% for Latinx.
  The article is VERIFIED to say this. It is journalism, not peer review, and Proctorio disputes whether FairFace is
  an appropriate test set. Use it as a lead, not as evidence.

- **Borek, M., Schwartz, A. & Spooner, A. (2024). "Evaluating Camera Performance in Face-Present Scenes With Diverse
  Skin Tones." Electronic Imaging 36 (IQSP XXI), 260-1–260-5. DOI 10.2352/EI.2024.36.9.IQSP-260.**
  https://library.imaging.org/ei/articles/36/9/IQSP-260
  The authors tested auto white balance, auto exposure and colour reproduction on webcams and phone cameras, using
  mannequins and synthetic faces spanning the Monk scale. "Color shifts, exposure errors, and reduced overall image
  fidelity are unfortunately common" for darker skin tones. This is the image-capture stage, before any model
  sees the video. The authors are from a camera-testing vendor, Imatest. **VERIFIED**

- **Roth, L. (2009). "Looking at Shirley, the Ultimate Norm: Colour Balance, Image Technologies, and Cognitive
  Equity." Canadian Journal of Communication 34(1).** A history of light-skin bias built into film emulsions,
  Kodak "Shirley" calibration cards and camera design. **UNVERIFIED** (seen only through secondary summaries; the
  primary page was not opened)

### Vision-language models and skin tone

- **Zhao, D., Wang, A. & Russakovsky, O. (2021). "Understanding and Evaluating Racial Biases in Image Captioning."
  ICCV 2021.** https://arxiv.org/abs/2106.08503
  The authors annotated perceived skin colour and gender for 28,315 people in COCO. Captioning performance,
  sentiment and word choice differed between images of lighter- and darker-skinned people, and the differences
  were larger in modern captioners than in older ones. **VERIFIED**

- **Malik, S., Abdullah, H. M., Saha, S. & Sheth, A. (2025/2026). "Ask Me Again Differently: GRAS for Measuring
  Bias in Vision Language Models on Gender, Race, Age, and Skin Tone." Findings of EACL 2026 (arXiv:2508.18989).**
  https://arxiv.org/abs/2508.18989
  A visual question answering bias benchmark over gender, race, age and skin tone, with skin-tone categories
  drawn from the Monk scale. Five state-of-the-art VLMs were tested. The least biased model scored "only 2 out of
  100" on the GRAS Bias Score. Answers changed when the same question was rephrased, so a bias evaluation needs
  several phrasings of each question. **VERIFIED** (abstract). A search summary claimed that darker MST tones
  (8–10) drew more negative traits. That detail is UNVERIFIED.

- **Gustafson, L., Rolland, C., Ravi, N., Duval, Q., Adcock, A., Fu, C.-Y., Hall, M. & Ross, C. (2023). "FACET:
  Fairness in Computer Vision Evaluation Benchmark." ICCV 2023 (arXiv:2309.00035).** https://arxiv.org/abs/2309.00035
  About 32k images with expert-annotated perceived skin tone, hair type, age and gender presentation. It covers
  classification, detection, segmentation and visual grounding. The models tested show performance disparities
  across these attributes and their intersections. The abstract does not name the skin-tone scale. FACET is for
  evaluation only. **VERIFIED** (abstract)

- **Schumann, C., Olanubi, G. O., Wright, A., Monk, E. Jr., Heldreth, C. & Ricco, S. (2023). "Consensus and
  Subjectivity of Skin Tone Annotation for ML Fairness." NeurIPS 2023 Datasets and Benchmarks (arXiv:2305.09073).**
  https://arxiv.org/abs/2305.09073
  - Annotators can match an expert's Monk Skin Tone (MST) labels reliably, even under challenging lighting.
  - Annotators from different regions apply the MST categories systematically differently.
  - The authors recommend diverse annotator pools and more annotations per image.
  - The paper releases MST-E: 1,515 images and 31 videos, intended for training annotators.

  This matters for the benchmark's ceiling: skin-tone labels have their own reliability. **VERIFIED**

---

## 2. Accent, dialect and non-native speech

### ASR disparities

- **Koenecke, A., Nam, A., Lake, E., Nudell, J., Quartey, M., Mengesha, Z., Toups, C., Rickford, J. R., Jurafsky, D.
  & Goel, S. (2020). "Racial disparities in automated speech recognition." PNAS 117(14):7684–7689.**
  https://www.pnas.org/doi/10.1073/pnas.1915768117
  Five commercial ASR systems (Amazon, Apple, Google, IBM, Microsoft) were tested on interviews with 73 Black and
  42 white speakers. Average WER was 0.35 for Black speakers and 0.19 for white speakers. The authors trace the
  gap to the acoustic models. **VERIFIED** (abstract via Europe PMC; the PNAS page returned 403)

- **Martin, J. L. & Tang, K. (2020). "Understanding Racial Disparities in Automatic Speech Recognition: The Case of
  Habitual 'be'." Interspeech 2020, 626–630.** https://www.isca-archive.org/interspeech_2020/martin20_interspeech.html
  Using over 100 hours of African American English, the authors tested DeepSpeech and Google Cloud Speech. Habitual
  "be" and the words around it produced more errors than non-habitual "be", after controls for context, noise and
  speech rate. So dialect grammar, not only acoustics, drives error. **VERIFIED**

- **DiChristofano, A., Shuster, H., Chandra, S. & Patwari, N. (2022). "Global Performance Disparities Between
  English-Language Accents in Automatic Speech Recognition." arXiv:2208.01157.** https://arxiv.org/abs/2208.01157
  An audit of several commercial ASR services on the Speech Accent Archive (over 2,700 speakers born in 171
  countries). After linguistic controls, performance was significantly related to how politically aligned the
  speaker's birth country is with the US, for every service tested. The abstract gives no numbers. **VERIFIED**

- **Sanabria, R., Bogoychev, N., Markl, N., Carmantini, A., Klejch, O. & Bell, P. (2023). "The Edinburgh
  International Accents of English Corpus: Towards the Democratization of English ASR." ICASSP 2023
  (arXiv:2303.18110).** https://arxiv.org/abs/2303.18110
  About 40 hours of dyadic video-call conversations across L1 and L2 varieties of English, released under
  CC BY-SA. The best model averaged 19.7% WER on this corpus, against 2.7% on US English read speech. All models
  degraded on Indian, Jamaican and Nigerian English. The video-call recording conditions are close to student
  submissions. **VERIFIED**

- **Veliche, I.-E., Huang, Z., Kochaniyan, V. A., Peng, F., Kalinli, O. & Seltzer, M. L. (2024). "Towards measuring
  fairness in speech recognition: Fair-Speech dataset." arXiv:2408.12734.** https://arxiv.org/abs/2408.12734
  About 26.5k voice-command utterances from 593 US speakers. Each speaker self-reported age, gender, ethnicity,
  region and whether they are a native English speaker. The abstract gives no numbers. **VERIFIED**

### Audio LLMs and LLM decoders

- **Ginjala, S., Fosler-Lussier, E., Myers, C. W. & Parthasarathy, S. (2026). "Do LLM Decoders Listen Fairly?
  Benchmarking How Language Model Priors Shape Bias in Speech Recognition." arXiv:2604.21276.**
  https://arxiv.org/abs/2604.21276
  - Setup: nine ASR models on about 43k utterances from Common Voice 24 and Fair-Speech, across five demographic
    axes.
  - On clean audio, LLM decoders did not amplify racial bias. Granite-8B had the best max/min WER ratio across
    ethnicities, 2.28.
  - Whisper large-v3 hallucinated on Indian-accented speech, with insertion rates up to 9.62%. Injected silence
    amplified Whisper's accent bias by up to 4.64 times.
  - Audio-encoder compression predicted accent fairness better than LLM scale did.
  - Severe acoustic degradation compressed the fairness gaps, because every group converged on high WER.

  **VERIFIED** (abstract; preprint, not peer reviewed)

- **Li, K., Shen, C., Liu, Y., Han, J., Zheng, K., et al. (2025). "AudioTrust: Benchmarking the Multifaceted
  Trustworthiness of Audio Large Language Models." ICLR 2026 (arXiv:2505.16211).** https://arxiv.org/abs/2505.16211
  Fairness is one of six evaluation dimensions. The authors point to non-semantic cues ("timbre, accent, and
  background noise") as a source of risk. The abstract gives no accent-specific numbers. **VERIFIED** (abstract)

### Automated speech scoring (education)

- **Loukina, A., Madnani, N. & Zechner, K. (2019). "The many dimensions of algorithmic fairness in educational
  applications." BEA 2019 (ACL), 1–10.** https://aclanthology.org/W19-4401/
  Using simulated and operational English-proficiency speaking data, the authors show how test-takers' native
  language affects automated scores. Different fairness definitions conflict, and "total fairness may not be
  achievable". This is the key framing paper for subgroup analysis by L1. **VERIFIED** (abstract; no numbers in it)

- **Loukina, A. & Buzick, H. M. (2017). "Use of Automated Scoring in Spoken Language Assessments for Test Takers With
  Speech Impairments." ETS Research Report RR-17-42. DOI 10.1002/ets2.12170.**
  https://www.ets.org/research/policy_research_reports/publications/report/2017/jycv.html
  In TOEFL iBT speaking data, SpeechRater scores came out higher than human scores for test takers with speech
  impairments. In a subsample, ASR word error rate was also higher for these test takers. **UNVERIFIED** (the ETS
  page failed to load; content taken from a search-index summary of that page)

- **Kwako, A., Wan, Y., Zhao, J., Hansen, M., Chang, K.-W. & Cai, L. (2023). "Does BERT Exacerbate Gender or L1
  Biases in Automated English Speaking Assessment?" BEA 2023, 668–681.** https://aclanthology.org/2023.bea-1.54/
  The authors measured differential item functioning (DIF) by L1. It was moderate in grade band 9–12. BERT scoring
  increased DIF, but by an amount the authors call very small in practical terms. DIF was greater for longer items
  and older examinees, and BERT did not amplify that pattern. **VERIFIED** (abstract; no numbers in it)

- **Parikh, A. K., Tejedor-Garcia, C., Cucchiarini, C. & Strik, H. (2025). "Zero-Shot Speech LLMs for Multi-Aspect
  Evaluation of L2 Speech: Challenges and Opportunities." SLaTE 2025 (arXiv:2601.16230).**
  https://arxiv.org/abs/2601.16230
  Qwen2-Audio-7B-Instruct scored 5,000 speechocean762 utterances zero-shot for accuracy, fluency, prosody and
  completeness. Its scores agreed strongly with human ratings within ±2 points, especially for high-quality speech.
  It over-predicted scores for low-quality speech and detected errors imprecisely. The same over-scoring of weak
  responses would matter for grading. **VERIFIED** (abstract)

- **Ma, R., Qian, M., Tang, S., Bannò, S., Knill, K. M. & Gales, M. J. F. (2025). "Assessment of L2 Oral Proficiency
  using Speech Large Language Models." arXiv:2505.21148.** https://arxiv.org/abs/2505.21148
  Adapted speech LLMs outperform previous baselines on two datasets, according to the abstract, which gives no
  numbers. A search snippet reported PCC 0.954 and 0.938 for a Qwen2-Audio grader. That figure is UNVERIFIED.
  **VERIFIED** (abstract claim only)

- **Gayed, J. M. (2026). "Investigating first-language bias in LLM-based automated essay scoring: A cross-prompt
  evaluation of an open-weight AI-model on TOEFL essays." arXiv:2607.14605.** https://arxiv.org/abs/2607.14605
  This is written work, not speech, but it is the closest current L1-fairness result for an LLM grader.
  - Setup: LoRA-tuned Gemma-3-27B on 12,100 TOEFL11 essays from 11 L1s.
  - Accuracy: QWK 0.702, exact band agreement 77.79%.
  - Within every proficiency band, essays by writers from European-language backgrounds scored higher than essays
    by writers from East-Asian-language backgrounds.

  **VERIFIED** (abstract; preprint)

---

## 3. Language coverage (common vs low-resource) and non-English assessment

- **Conneau, A., Ma, M., Khanuja, S., Zhang, Y., Axelrod, V., Dalmia, S., Riesa, J., Rivera, C. & Bapna, A. (2022).
  "FLEURS: Few-shot Learning Evaluation of Universal Representations of Speech." arXiv:2205.12446 (IEEE SLT 2022).**
  https://arxiv.org/abs/2205.12446
  An n-way parallel speech benchmark in 102 languages, with about 12 hours per language, built on FLoRes-101 and
  released under CC BY 4.0. **VERIFIED** (abstract; the SLT venue is from memory and was not shown on the page)

- **Shi, J., Berrebbi, D., Chen, W., et al. (2023). "ML-SUPERB: Multilingual Speech Universal PERformance
  Benchmark." Interspeech 2023 (arXiv:2305.10615).** https://arxiv.org/abs/2305.10615
  An ASR and language-identification benchmark over 143 languages. Self-supervised features beat filterbank
  features, but multilingual models do not always beat monolingual ones. **VERIFIED**

- **Pratap, V., Tjandra, A., Shi, B., et al. (2023). "Scaling Speech Technology to 1,000+ Languages" (MMS).
  arXiv:2305.13516.** https://arxiv.org/abs/2305.13516
  ASR for 1,107 languages and language identification for 4,017. On 54 FLEURS languages, MMS cut Whisper's WER by
  more than half. This shows that a major general model has large per-language gaps. **VERIFIED**

- **Radford, A., Kim, J. W., Xu, T., Brockman, G., McLeavey, C. & Sutskever, I. (2022). "Robust Speech Recognition via
  Large-Scale Weak Supervision" (Whisper). arXiv:2212.04356 (ICML 2023).** https://arxiv.org/abs/2212.04356
  Trained on 680k hours of multilingual audio. The abstract says nothing about per-language results. The paper's
  appendix reports per-language FLEURS WER, which falls steeply with training hours per language; that point is
  from memory and **UNVERIFIED** here.

- **Olatunji, T., Afonja, T., Yadavalli, A., et al. (2023). "AfriSpeech-200: Pan-African Accented Speech Dataset for
  Clinical and General Domain ASR." TACL 2023 (arXiv:2310.00274).** https://arxiv.org/abs/2310.00274
  200 hours of English from 2,463 speakers, covering 120 African accents in 13 countries. Performance on minority
  accents "lags significantly". The abstract gives no numbers. **VERIFIED**

- **Ardila, R., Branson, M., Davis, K., et al. (2020). "Common Voice: A Massively-Multilingual Speech Corpus." LREC
  2020 (arXiv:1912.06670).** https://arxiv.org/abs/1912.06670
  The crowdsourced corpus as of the paper: 29 languages released, 38 collecting, about 2,500 hours. **VERIFIED**

### Automated assessment of non-English or multilingual student work

- **Ghazawi, R. & Simpson, E. (2025). "How well can LLMs Grade Essays in Arabic?" arXiv:2501.16516.**
  https://arxiv.org/abs/2501.16516
  On the AR-AES dataset, the best generative LLM (ACEGPT) reached QWK 0.67, and a smaller BERT model reached 0.88.
  **VERIFIED**

- **Aisyah, N., Al Kautsar, M. D., Hidayat, A., Chowdhury, R. & Koto, F. (2025). "Evaluating Vision-Language and Large
  Language Models for Automated Student Assessment in Indonesian Classrooms." AIED 2026 (arXiv:2506.04822).**
  https://arxiv.org/abs/2506.04822
  Over 14k handwritten grade-4 answers in Mathematics and English. The VLM struggled with handwriting recognition,
  and those errors propagated into the LLM grades. The abstract gives no numbers. **VERIFIED**

- **Henkel, O., Roberts, B., Jaffe, D. & Holt, L. (2025). "Seeing the Big Picture: Evaluating Multimodal LLMs' Ability
  to Interpret and Grade Handwritten Student Work." arXiv:2510.05538.** https://arxiv.org/abs/2510.05538
  - Arithmetic work by 288 Ghanaian middle-school students: about 95% accuracy, κ = 0.90.
  - Illustrations by 150 American elementary students: κ = 0.20 from the image alone, and κ = 0.47 when the model
    was given human-written descriptions. The authors say 0.47 is in line with human-to-human agreement.

  **VERIFIED**

---

## 4. Datasets

The "Use" column is a summary only. Read each licence in full before running a study. In particular, read whether
it allows evaluating third-party or commercial models, whether outputs may be published, and whether the data may
be retained.

| Dataset | What it holds | Size | Licence / terms | Access | Status |
|---|---|---|---|---|---|
| **Casual Conversations v1** (Hazirbas et al. 2021, arXiv:2104.02821) | Consented, paid participants answering unscripted questions on video. Labels: self-reported age and gender; Fitzpatrick type (annotated); low-light flag; human speech transcriptions | 3,011 people, 45,186 videos, ~1 min each; all US (five cities) | Meta data user agreement, summarised as "Limited". **Evaluation allowed; no training on the provided labels.** The landing page does not address commercial use | Open download from ai.meta.com/datasets/casual-conversations-dataset/ after accepting the agreement | VERIFIED (landing page and abstract) |
| **Casual Conversations v2** (Porgali et al. 2023, arXiv:2303.04838) | Self-reported: age, gender, **language/dialect**, disability, geo-location, adornments. Annotated: **Fitzpatrick and Monk skin tone**, voice timbre, recording setup, activity | 5,567 people, 26,467 videos; Brazil, India, Indonesia, Mexico, Philippines, US, Vietnam | Meta licence, "Limited": evaluation allowed, training only on certain labels. Commercial use is not stated on the page | Open download from ai.meta.com/datasets/casual-conversations-v2-dataset/ after accepting the licence | VERIFIED |
| **MST-E** (Schumann et al. 2023) | Images and video across all ten Monk tones, with expert labels and a lighting challenge set | 1,515 images, 31 videos | Dataset licence not found on the arXiv page | Released by Google (skintone.google) | VERIFIED size; licence UNVERIFIED |
| **FACET** (Gustafson et al. 2023) | Still images with perceived skin tone, age, gender presentation and hair | ~32k images | Evaluation only, no training | facet.metademolab.com | VERIFIED (abstract); "evaluation only" term from secondary source |
| **Fair-Speech** (Veliche et al. 2024) | US voice commands. Self-reported: age, gender, ethnicity, region, native-English status | 26.5k utterances, 593 speakers | Stated as "publicly released"; licence not found | via Meta (link not on the abstract page) | VERIFIED content; licence UNVERIFIED |
| **EdAcc** (Sanabria et al. 2023) | Video-call conversations across many L1 and L2 English accents | ~40 h | CC BY-SA | Open (University of Edinburgh) | VERIFIED |
| **L2-ARCTIC** (Zhao et al. 2018, Interspeech) | Read and unscripted English from 24 speakers (4 per L1: Hindi, Korean, Mandarin, Spanish, Arabic, Vietnamese). About 150 utterances per speaker are hand-annotated for phone errors | ~24 h | **CC BY-NC 4.0**; commercial use requires contacting TAMU | Web form; download link sent by email | VERIFIED |
| **speechocean762** (Zhang et al. 2021, Interspeech) | Non-native English (Mandarin L1) with expert scores at sentence, word and phone level (accuracy, fluency, prosody, completeness); half the speakers are children | 5,000 utterances, 250 speakers, 520 MB | **CC BY 4.0; commercial use allowed** | Open, OpenSLR 101 | VERIFIED |
| **Speak & Improve Corpus 2025** (Knill et al. 2024, arXiv:2412.11986) | Learner English speech (A2–C1) with holistic proficiency scores; a subset has transcripts and error annotations; speakers span many L1s | ~315 h (the abstract gives 340 h in one version) | **Non-commercial use** | ELiT website (sign-up) | VERIFIED |
| **TLT-school** (Gretter et al., LREC 2020) | Italian schoolchildren aged 9–16 speaking English and German as L2, scored by experts on proficiency indicators | Not confirmed | Part of the corpus is free to researchers | via FBK | UNVERIFIED details (search snippet only) |
| **Speech Accent Archive** (GMU, Weinberger) | One elicitation paragraph read by speakers of many L1s | >2,700 speakers born in 171 countries (per DiChristofano et al.) | **CC BY-NC-SA 4.0** | Open browse/download at accent.gmu.edu (site under renovation) | VERIFIED licence |
| **AfriSpeech-200** | African-accented English, clinical and general domains | 200 h, 2,463 speakers, 120 accents | **CC BY-NC-SA 4.0, "research purposes only"** | Hugging Face, gated (accept terms) | VERIFIED |
| **FLEURS** | Parallel read sentences | 102 languages, ~12 h each | **CC BY 4.0** | Open (Hugging Face google/fleurs) | VERIFIED (paper abstract) |
| **Common Voice** | Crowdsourced read speech (now also spontaneous speech); optional self-reported age, sex and **accent** | 100+ languages; tens of thousands of hours (the paper reports 2,500 h for 2019) | **CC0** | **Since Oct 2025 only via the Mozilla Data Collective** (account plus terms of service); old Hugging Face mirrors are emptied | VERIFIED move; MDC terms of service not read |
| **MERLIN** | Written learner texts in German, Italian and Czech, rated on the CEFR | 2,286 texts | **CC BY-SA 4.0** | Eurac CLARIN repository | VERIFIED |
| **SOPHIAS** (Becerra, Cobos & Daza 2026, arXiv:2601.07576) | Student oral presentations recorded with webcams and other sensors, plus evaluation data | 50 presentations, 65 students, ~12 h | Controlled access under a Data Usage Agreement (Science Data Bank) | Request | VERIFIED access terms; size from search snippet |
| **MLA'14 Oral Presentation Quality Corpus** | Student presentations with human scores for delivery and slides | Not confirmed | Not confirmed | Not confirmed | UNVERIFIED |

---

## 5. Gaps (what the literature does not yet answer)

1. **Graded student video by skin tone.** No published study found measures whether a multimodal LLM *grades* the
   same presentation differently by presenter skin tone or lighting. The existing evidence covers detection
   (Yoder-Himes 2022, Dooley 2022), capture (Borek 2024) and descriptions or VQA (Zhao 2021, GRAS 2025). Casual
   Conversations v2 supports a counterfactual design: the same rubric applied across Monk tones and lighting.
   However, its content is casual speech, not student work.
2. **Accent effects in audio LLM *scoring*, as opposed to transcription.** Zero-shot speech-LLM scoring
   (Parikh 2025) over-predicts weak speech. No study found measures score gaps by L1 *at fixed human score* for
   audio LLMs. The Loukina 2019 and Kwako 2023 DIF framing applies directly. speechocean762 is single-L1 (Mandarin),
   so cross-L1 comparison needs Speak & Improve, L2-ARCTIC or TLT-school.
3. **Pipeline attribution.** ASR errors propagate into grades (Loukina & Buzick 2017; Martin & Tang 2020), and so do
   handwriting-OCR errors (Aisyah 2025). A benchmark should report transcription error by group alongside score
   error by group, so a disparity can be traced to its stage.
4. **Non-English spoken student work with human scores** is scarce. TLT-school (Italian learners of English and
   German) is the main lead found. FLEURS and Common Voice give per-language recognition, not assessment.
5. **Ceilings.** Skin-tone labels are themselves unreliable and region-dependent (Schumann 2023; Yoder-Himes merged
   categories because of low inter-rater reliability). Any skin-tone analysis must report label agreement before
   reading a disparity.
6. **Licences.** Most of the accent and score corpora are non-commercial (L2-ARCTIC, Speak & Improve, AfriSpeech,
   Speech Accent Archive). Only speechocean762, FLEURS, EdAcc (share-alike) and Common Voice are open for
   commercial use. Meta's Casual Conversations licences allow evaluation, but the full text should be read before
   commercial models are tested on them or their outputs are published.
