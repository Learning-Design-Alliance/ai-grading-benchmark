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
| CHECK-MAT / EGE Math Solutions Assessment Benchmark (Karifannaa 2025) | `images/` | MIT per the paper; "other" on the dataset card | https://huggingface.co/datasets/Karifannaa/EGE_Math_Solutions_Assessment_Benchmark |
| LASANA laparoscopic skill videos (TU Dresden; DOI 10.25532/OPARA-1046) | `video/` | CC BY 4.0 | https://opara.zih.tu-dresden.de/handle/123456789/1907: Annotation.zip (MD5 2339e7cd12ba6291e9162119ba068439), then `python3 video/fetch_lasana.py --root DIR`, which reads 100 test-split recordings out of the video zips by range request |

**ELLIPSE** (in `persuade-ellipse`): the two-rater file is a password-protected zip in
https://github.com/scrosseye/ellipse-corpus; the password is in that repository's README. `bench.py prepare ellipse`
reads the extracted raw-rater CSV and the final corpus's train and test CSVs from one directory.

**Learning Commons evaluators** (`feedback-validity/lc_mrbench.py`): https://github.com/learning-commons-org/evaluators
(code MIT, prompts CC BY 4.0), cloned at b9d4789; set `LC_EVALUATORS_DIR`.
