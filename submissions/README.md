# Submitting a result

1. Run the leaderboard battery on one or more tasks (see the top-level README).
2. Export each run:

       python3 leaderboard.py export runs/<run> --task <mohler|code|asap2> --submitter "<name>" \
           --out submissions/<model-slug>/<task>.json

   For your own prompt, the export includes the prompt's text: entries in the bring-your-own-prompt
   track must be rerunnable by anyone. Only text-template prompts are accepted there.
3. Check it locally: `python3 leaderboard.py verify submissions/<model-slug>/<task>.json --cases data/<task file>`.
4. Open a pull request that adds only files under `submissions/`.

**What CI checks** (`.github/workflows/leaderboard.yml`), and refuses on any failure:
- the file is the submission format, for the `leaderboard` battery;
- the cases file is the pinned one (`leaderboard-cases.json`), and the case IDs are the canonical draw;
- every planned grading is present once, and no other; every mark is on the task's scale;
- no grading carries text or any field outside the format;
- on the default track, the prompt is `prompts/default.txt`; on the other, the published prompt matches
  its hash.
CI then recomputes every leaderboard number from the marks. Your reported numbers are never used,
except cost, which is shown as self-reported.

**Verified badge.** A maintainer re-grades 25 random cases with the model, endpoint and settings you
declared (`leaderboard.py spotcheck`). The entry is VERIFIED when those marks agree with yours at
least as well as your run's own retest agreement minus 0.10. Until then it is shown as self-reported.

**Please include** the provider and region you used, and whether zero data retention was on, in the
pull request description. Hosted models can change under the same name; `served_models` in the export
records what the provider said it served.
