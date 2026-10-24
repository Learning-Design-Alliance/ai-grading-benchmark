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

## Rules

- **Nothing from any product's own prompt or product results enters this repository**, not even while it is
  private: a committed file stays in git history. `scripts/check_private.py` enforces it in CI. Product
  comparisons live in the private research repository.
- **Raw data never enters it.** Corpora live in local directories; only aggregates are committed. A study
  that reads a corpus says so in its docstring and in `docs/DATA-SOURCES.md`.
- **Pre-register before reading results.** Thresholds and verdict strings go in the script's docstring and
  are committed before any call; changes after that are numbered CHANGES with their reason.
- **Check the detection floor before reading any real number**, and state the human ceiling beside any
  agreement figure. Sign every effect: say which direction it points.
- **Every request requires zero data retention.** Credentials come from the environment, never a command
  line or a committed file.
- **Never hand-edit a generated file** (`out/leaderboard.json`, `out/public/`): rebuild it.
- Before the repository is made public: `python3 scripts/check_private.py --publish` must pass, working files
  are cleaned up, and the vendor-facing write-up and the results go out together.
