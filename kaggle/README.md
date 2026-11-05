# The benchmark on Kaggle Benchmarks

Five of the benchmark's checks as Kaggle Benchmarks tasks, so Kaggle runs them on new models as they are released.
The leaderboard on the benchmark's site stays the reference; the Kaggle page is an independent run of these checks.

| file | what it is |
| --- | --- |
| `build_dataset.py` | builds the Kaggle dataset: the board's prompts rendered by the benchmark's own code, the 300 cases with human marks, the pushback and feedback items, and the scoring modules |
| `kaggle_scoring.py` | the five 0-1 scores, from `report.build` and the leaderboard's own transforms (shipped in the dataset) |
| `DATASET.md` | the dataset's data card (shipped as its README) |
| `tasks/*.py` | the five tasks, in the `kaggle-benchmarks` SDK's percent format |
| `verify.py` | the checks run before publishing |

## Verified before publishing (2026-11-05)

- Scoring: every model's committed leaderboard grades, scored by `kaggle_scoring.py`, reproduce `out/leaderboard.json`
  for all 22 models: 220 values (agreement share, larger note gain and blank-answer credit per task, and the
  pushback effect), 0 mismatches. The dataset's cases are the leaderboard's.
- Task files: run end to end against a stand-in for the SDK that replays Claude Opus 5.5's recorded replies, they
  give agreement 0.9805, note gaming 0.9911, blank answers 1.0, pushback 0.9524 and feedback 0.5961, the
  leaderboard's values. (This replay caught one bug, a missing `usage` field, fixed in `a5f5e94`.)

## Publishing (needs the maintainer's Kaggle account and token)

```
python3 fetch_data.py --dir DATA                       # each cases file is checked against its pin
python3 kaggle/build_dataset.py --data DATA --out kg-dataset --owner <kaggle user or org>
python3 kaggle/verify.py --data kg-dataset             # 0 mismatches before anything is uploaded
kaggle datasets create -p kg-dataset                   # creates <owner>/ai-grading-benchmark-board

kaggle b init -y                                       # model-proxy credentials for local test runs
python3 kaggle/tasks/grader_blank_answers.py           # optional: one cheap task locally first
for t in agreement note_gaming blank_answers pushback feedback_told_grade; do
  kaggle b t push grader-${t//_/-} -f kaggle/tasks/grader_$t.py -d <owner>/ai-grading-benchmark-board --wait
done
kaggle b t run grader-blank-answers -m <model> --wait  # one task, one model, to check before running all
kaggle b t publish grader-agreement                    # and the other four
```

Then, in the Kaggle web interface: Benchmarks, Create benchmark, add the five tasks and the models to show. The
CLI manages tasks only; a benchmark (the collection) is made in the web interface.

Notes:
- Each task file must end with its `.run(...)` call, or the push succeeds and records nothing.
- Repeat `-d <owner>/ai-grading-benchmark-board` on every push; a push without it detaches the dataset.
- Every push also runs the whole task on Kaggle's default model (gemini-3.8-flash on 2026-11-05), which spends quota:
  about $0.94 for agreement, $2.99 for note gaming, $0.16 for blank answers, $0.69 for pushback and $0.68 for
  feedback on that model. A re-push spends it again.
- Each task prints how many replies were unreadable. The score leaves those out, so a high count means it rests on
  fewer answers. On the first Kaggle run, Kaggle's host returned an empty reply to every gibberish answer for
  claude-haiku-5-5 (40 of 200); that model's blank-answer score covers the other four kinds of master-key answer.
- Calls per model: agreement 300, note gaming 900, blank answers 200, pushback about 100 + 2 per answer marked
  below full marks, feedback 300. If a community account's quota is too small, Kaggle offers more compute for
  research benchmarks (kaggle-benchmarks@google.com).
- Kaggle runs the models through its own hosts at temperature 0, without this benchmark's zero-retention routing
  (the corpora are public); scores can differ a little from the leaderboard's for that reason.
