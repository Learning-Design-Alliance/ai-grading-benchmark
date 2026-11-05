# %%
"""Grader agreement: does the model agree with expert raters as closely as they agree with each other?

AI Grading Benchmark (Learning Design Alliance): https://benchmark.learningdesignalliance.org

Each model grades 300 real student answers (100 computer-science short answers, 100 programs, 100 essays) with the
benchmark's plain marking prompt. Agreement is quadratic weighted kappa against each rater, as a share of the raters'
agreement with each other on the same answers (essays: their published agreement, 0.745), capped at 1 and averaged
over the three tasks.

Score: 0-1, higher is better, the leaderboard's own transform. Kaggle runs this task at its own model settings
(temperature 0) through its own model hosts, so a score can differ a little from the leaderboard's, which pins
hosts and uses each provider's default sampling. Data: the ai-grading-benchmark-board dataset (CC BY 4.0).
"""
import glob
import os
import sys

import kaggle_benchmarks as kbench

_data = os.environ.get("GBENCH_KAGGLE_DATA") or os.path.dirname(glob.glob("/kaggle/input/**/gradings.jsonl", recursive=True)[0])
sys.path.insert(0, os.path.join(_data, "gbench"))
import kaggle_scoring as ks  # noqa: E402

DATA = ks.find_data()


def grade(llm, rows):
    """Grade each row in its own chat; the benchmark's plain marking prompt, the mark parsed as the leaderboard does."""
    calls = []
    for r in rows:
        with kbench.chats.new(f"{r['task']} {r['id']} {r['probe']}", system_instructions=r["system"] or None):
            text = llm.prompt(r["user"])
        calls.append({"task": r["task"], "id": r["id"], "probe": r["probe"], "score": ks.parse(text, *r["scale"])})
    return calls

# %%
@kbench.task(name="grader-agreement")
def grader_agreement(llm) -> float:
    calls = grade(llm, ks.gradings(DATA, {"base"}))
    score, per_task = ks.agreement_score(DATA, calls)
    print("share of the raters' agreement by task:", per_task)
    return score


grader_agreement.run(kbench.llm)
