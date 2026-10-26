# AI grading benchmark

The home of all benchmark work (moved from the Learning Design Alliance research repository on
2026-10-24). **Private until the maintainer makes it public**; the package at the root is what ships.

## Layout

- Root: the package people run (`bench.py`, `leaderboard.py`, `fetch_data.py`, `floor.py`, the harness modules,
  `prompts/`), its front page (`README.md`), CI (`.github/workflows/`).
- `submissions/`: leaderboard entries, marks only, no text. `out/`: committed aggregates (study results, the
  floor, the built leaderboard, the public report's data in `out/public/`).
- `disability/`, `fairness-ellipse/`, `feedback-validity/`: studies, each with its script (the docstring is
  the pre-registration and the record of changes), a README and `out/`.
- `docs/`: the research log, drift, the literature review, data sources. `scripts/`: repository checks.

## Methodology

Read `docs/METHODOLOGY.md` before designing or reporting anything: every rule there was learned from a mistake,
with the incident and how it is enforced. A new study starts from `docs/STUDY-TEMPLATE.md` and must pass
`python3 scripts/check_study.py` (CI runs it). Before analysing runs: `python3 scripts/check_runs.py <run dirs>`.
Before anything leaves the team: the independent audit in `docs/AUDIT-PROMPT.md`, and
`python3 scripts/check_numbers.py <document>` to list every number for checking. A new modality (presentations,
screen recordings, speech, video) works through the checklist in `docs/METHODOLOGY.md` section 7.

## Rules

- **Nothing from any product's own prompt or product results enters this repository**, not even while it is
  private: a committed file stays in git history. `scripts/check_private.py` enforces it in CI; the product is named only in the benchmark card's conflict-of-interest line. Product
  comparisons live in the private research repository.
- **Raw data never enters it.** Corpora live in local directories; only aggregates are committed. A study
  that reads a corpus says so in its docstring and in `docs/DATA-SOURCES.md`.
- **Pre-register before reading results.** Thresholds and verdict strings go in the script's docstring and
  are committed before any call; changes after that are numbered CHANGES with their reason.
- **Check the detection floor before reading any real number**, and state the human ceiling beside any
  agreement figure. Sign every effect: say which direction it points.
- **Every request requires zero data retention.** Credentials come from the environment, never a command
  line or a committed file.
- **Cite where a dataset or method comes from.** Add it to `docs/SOURCES.md` (the site's Sources page is built from
  it) and cite it in the site's text with `<cite data-ref="key"></cite>`.
- **Never hand-edit a generated file** (`out/leaderboard.json`, `out/public/`): rebuild it.
- Before the repository is made public: `python3 scripts/check_private.py --publish` and
  `python3 scripts/check_citations.py docs/LITERATURE.md` and `docs/SOURCES.md` must pass, working files
  are cleaned up, and the vendor-facing write-up and the results go out together.
