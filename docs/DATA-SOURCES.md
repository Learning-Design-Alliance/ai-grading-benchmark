# Data sources

Raw data never enters this repository: every study reads a corpus from a local directory and commits
aggregates only. The three leaderboard corpora are fetched and hash-checked by `fetch_data.py`; the others
are needed only to re-run a study.

| corpus | used by | licence | where to get it |
|---|---|---|---|
| PERSUADE 2.0 and ELLIPSE essay corpora (`persuade-ellipse`) | PERSUADE runs; `fairness-ellipse/` | CC BY-NC-SA 4.0 | https://github.com/scrosseye/persuade_corpus_2.0 |
| Menagerie (`menagerie-grades`) | Menagerie runs | CC BY 4.0 | https://osf.io/q8jbt |
| HARMOGEN-R (`harmogen-r`) | leaderboard (code) | CC BY 4.0 | https://zenodo.org/records/19534458/files/harmogenr_dataset_v2.zip?download=1 |
| Mohler ASAG (Mohler, Bunescu and Mihalcea 2011), Hugging Face conversion nkazi/MohlerASAG (`mohler-asag`) | leaderboard (short answers) | CC BY 4.0 | https://huggingface.co/datasets/nkazi/MohlerASAG/resolve/dac06732b42d01a5169f543f6d272f1476cced3e/data/cleaned-oe-00001.parquet |
| ASAP 2.0 (`asap2`) | leaderboard (essays); `disability/` | CC BY 4.0 | https://www.kaggle.com/api/v1/datasets/download/lburleigh/asap-2-0 |
| MRBench (`mrbench`) | `feedback-validity/` | CC BY-SA 4.0 | https://github.com/kaushal0494/UnifyingAITutorEvaluation |
| speechocean762 (Zhang et al. 2021; OpenSLR 101) | `speech/` | CC BY 4.0 | https://www.openslr.org/101/ |
| FLEURS (Conneau et al. 2022), dev split of 18 languages | `language/` | CC BY 4.0 | https://huggingface.co/datasets/google/fleurs: `data/<lang>/dev.tsv` and `data/<lang>/audio/dev.tar.gz`, fetched by `python3 language/study.py prepare --dir DIR` |
| CHECK-MAT / EGE Math Solutions Assessment Benchmark (Karifannaa 2025) | `images/` | MIT per the paper; "other" on the dataset card | https://huggingface.co/datasets/Karifannaa/EGE_Math_Solutions_Assessment_Benchmark |
| VtG: stepwise maths solutions with the teacher-marked first wrong step (Daheim et al. 2024), from MathDial | `maths-process/` | CC BY-SA 4.0 (the README also shows a CC BY 4.0 badge; the stricter is followed) | https://github.com/eth-lre/verify-then-generate, `dataset/dataset.json` at commit 161019e (MD5 3aa4f6bf8b0185e26fe859b749165b13) |
| LASANA laparoscopic skill videos (TU Dresden; DOI 10.25532/OPARA-1046) | `video/` | CC BY 4.0 | https://opara.zih.tu-dresden.de/handle/123456789/1907: Annotation.zip (MD5 2339e7cd12ba6291e9162119ba068439), then `python3 video/fetch_lasana.py --root DIR`, which reads 100 test-split recordings out of the video zips by range request |
| Casual Conversations v2 (Meta; Porgali et al. 2023): 26,467 consented videos of 5,567 people, with Monk and Fitzpatrick skin tone, lighting, setup and self-reported language and disability labels | `perception/` | Limited licence: evaluation of models on the labels permitted (clause 1(b)); training on most labels not; no derivative works (6.1); no disclosure to third parties outside 1(b) (6.2, 6.9); deletion on request (4, 9) | Sign in on Meta's dataset page (ai.meta.com/datasets/casual-conversations-v2-dataset) and accept the licence; Meta then gives signed download links, which are personal and expire and are never shared or committed. CCv2_annotations.zip (MD5 81e412575d7f0b9ffe2f0ef8f64d6351); `python3 -I perception/fetch_ccv2.py` reads only the sampled videos out of the video zips by range request |

**ELLIPSE** (in `persuade-ellipse`): the two-rater file is a password-protected zip in
https://github.com/scrosseye/ellipse-corpus; the password is in that repository's README. `bench.py prepare ellipse`
reads the extracted raw-rater CSV and the final corpus's train and test CSVs from one directory.

**Learning Commons evaluators** (`feedback-validity/lc_mrbench.py`): https://github.com/learning-commons-org/evaluators
(code MIT, prompts CC BY 4.0), cloned at b9d4789; set `LC_EVALUATORS_DIR`.
