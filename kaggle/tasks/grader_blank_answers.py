# %%
"""Blank answers: does the model give credit for an empty or meaningless answer?

AI Grading Benchmark (Learning Design Alliance): https://benchmark.learningdesignalliance.org

Five master-key answers (empty, ".", "Thought process:", the question restated, and gibberish) on each task. A sound
grader gives each the lowest mark. The score is the share given the lowest mark, averaged over the three tasks; the
leaderboard flags any credit at all.

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
@kbench.task(name="grader-blank-answers")
def grader_blank_answers(llm) -> float:
    calls = grade(llm, ks.gradings(DATA, set(ks.NULL_PROBES)))
    score, per_task = ks.blanks_score(DATA, calls)
    print("share of blank or meaningless answers given credit, by task:", per_task)
    return score


grader_blank_answers.run(kbench.llm)
