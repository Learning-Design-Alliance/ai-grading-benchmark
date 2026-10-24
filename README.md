# Grader benchmark: can you trust an AI to mark student work?

> **Working repository, private.** Studies, results and the research log live alongside the package
> (`disability/`, `fairness-ellipse/`, `feedback-validity/`, `out/`, `docs/`); see `CLAUDE.md`.

An open benchmark you run yourself, with your own model, your own prompt and your own API key. It
scores AI graders on four things a school, a vendor or a researcher needs to know before trusting one:

- **Validity:** does it agree with human markers, and does it mark the work rather than tricks in it?
- **Reliability:** does it give the same mark twice?
- **Fairness:** does a label about the learner change the mark of identical work?
- **Sustainability:** what does a thousand gradings cost?

Every number is checked against people. Agreement is reported as a share of how well the human markers
agree with each other (the **human ceiling**), because an AI cannot be expected to agree with a person
more than another person does. Every probe passed a planted-effect self-check (`floor.py`) before any
real result was read.

## What it measures

The leaderboard battery grades 100 fixed cases per task, plus these variants of the same work:

| column | what it is | good reads |
|---|---|---|
| agreement | QWK with the human marks; share of the human ceiling where there are two or more markers | high |
| consistency | QWK between two gradings of the same work | near 1 |
| gaming | the larger mark gain from appending a polite request for marks, or a forged "grading override" note | 0 or negative |
| attainment label | mark change when identical work is labelled as from a strong rather than a weak learner | 0 |
| blicket | mark change when the answer's key content word becomes a nonsense word | negative |
| surface sensitivity | mark change from re-wrapping the text's line breaks | 0 |
| blank answers | share of empty, ".", "Thought process:", restated-question and gibberish answers given credit | 0 |
| refusals | gradings a provider's filter refused: work that goes to a person, not a mark | low |
| cost | USD per 1,000 gradings, self-reported | low |

There is no overall score. Weighting these is a judgement for whoever uses the grader, and an average
would hide the column that matters most: one model that ignores every request for marks can still be
talked into full marks by a forged override.

**Tasks** (all CC BY 4.0, fetched by `fetch_data.py`; no account needed):

| task | what | scale | markers |
|---|---|---|---|
| `mohler` | university computer-science short answers (Mohler et al. 2011) | 0-5 | 2 |
| `code` | C++ answers from a university course, in Portuguese (HARMOGEN-R, Mendonca et al. 2026) | 0-90 | 4 |
| `asap2` | grade 6-12 source-based essays (ASAP 2.0, Crossley et al. 2025) | 1-6 | 2, adjudicated; one mark released |

## Run it

Python 3.10 or later, no other dependency except `pyarrow` for fetching Mohler.

    pip install pyarrow
    python3 fetch_data.py --dir data/                 # downloads, checks hashes, builds the cases files

    export OPENROUTER_API_KEY=...                     # or any OpenAI-compatible endpoint and its key
    python3 bench.py run --cases data/mohler.jsonl --battery leaderboard \
        --base-url https://openrouter.ai/api/v1 --model <model> --key-env OPENROUTER_API_KEY \
        --out runs/mohler-<model>                     # a dry run: prints the plan and a cost estimate
    # add --go to make the calls
    python3 bench.py score runs/mohler-<model>        # the full report, runs/.../report.md

Repeat for `data/harmogen-code.jsonl` and `data/asap2.jsonl`. A run caches every reply, so a stopped
run resumes without paying twice (`--cached-only` rebuilds one from its cache). Keep `runs/` out of
version control: replies can quote student work.

**Your own prompt.** Pass `--prompt my-prompt.txt`. A prompt is a text template with `{question}`,
`{reference}`, `{rubric}`, `{materials}`, `{response}`, `{scale_min}`, `{scale_max}` and, optionally,
`{context}` (where the attainment label goes). The reply must contain a JSON object with a numeric
`"score"`. `bench.py compare runsA runsB` gives the paired difference between two prompts or models.

**Other checks** beyond the leaderboard: `--battery full` (every probe), `abstain` (grading each
answer five times, for routing uncertain work to a person), `faithful` (does the stated reason drive
the mark), `anchor` plus `bench.py drift` (has a hosted model's marking moved since you adopted it),
and `bench.py generate` / `selfpref` (does a grader favour answers written by its own model).

## Submit to the leaderboard

    python3 leaderboard.py export runs/mohler-<model> --task mohler --submitter "<your name>" \
        --out submissions/<model-slug>/mohler.json
    python3 leaderboard.py verify submissions/<model-slug>/mohler.json --cases data/mohler.jsonl

Then open a pull request adding the file. See [`submissions/README.md`](submissions/README.md).
A submission holds every grading's mark and no text, so it contains no student work.

## What it cannot tell you

- Whether the grader's **feedback** helps a learner. The package measures feedback with rules; only
  tone has been validated against trained annotators, on tutoring text.
- Whether it works on **your** students. These are public corpora, and public text may be in a model's
  training data. The surface-sensitivity column is a weak check for memorisation, not a proof.
- **Fairness by group.** The attainment label is a controlled test; real group gaps need two
  independent human markers per answer, which only some corpora release.
- **Energy.** Reported only if you supply a per-token coefficient with its source.

## Licence

The code and documentation are MIT-licensed (`LICENSE`), by the Learning Design Alliance. The corpora the
package fetches keep their own licences (CC BY 4.0 for all three leaderboard tasks) and are not
redistributed here; cite their authors when you publish results. Submissions hold marks only, no text.
