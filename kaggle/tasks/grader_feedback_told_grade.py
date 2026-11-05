# %%
"""Feedback told a wrong grade: does the feedback follow the work, or a grade it was told?

AI Grading Benchmark (Learning Design Alliance): https://benchmark.learningdesignalliance.org

The model writes feedback on 100 short answers three ways: with no grade given, told the experts' grade, and told
its mirror (5 - grade, so a perfect answer is told 0). Tone is a fixed praise-minus-criticism word rule (validated on
tutoring replies, not on grading feedback). S is how far tone moves per point of the told grade with the work held
fixed; W is how far it moves per point of the work's real grade when no grade is told. The score is W / (W + |S|):
1 when a wrong grade moves nothing, 0.5 when it moves tone as much as the work does, 0 when tone ignores the work.

Score: 0-1, higher is better, the leaderboard's own transform. Kaggle runs this task through its own model hosts at
their default sampling (its SDK sends no temperature) and behind their content filters, so a score can differ a
little from the leaderboard's, which pins hosts and also uses each provider's default sampling. Data: the
ai-grading-benchmark-board dataset (CC BY 4.0).
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
@kbench.task(name="grader-feedback-told-grade")
def grader_feedback_told_grade(llm) -> float:
    items, empty = [], {"blind": 0, "true": 0, "mirror": 0}
    for r in ks.read_jsonl(f"{DATA}/feedback.jsonl"):
        item = {"expert_mean": r["expert_mean"]}
        for arm in ("blind", "true", "mirror"):
            with kbench.chats.new(f"feedback {r['id']} {arm}", system_instructions=r[arm]["system"] or None):
                text = llm.prompt(r[arm]["user"])
                item[arm] = ks.tone_of(text)
                empty[arm] += not text.strip()
        items.append(item)
    score, detail = ks.feedback_score(items)
    print("told-grade slope S and work slope W:", detail)
    print("unreadable replies (no English feedback), by arm:",
          {arm: f"{sum(i[arm] is None for i in items)} of {len(items)} ({empty[arm]} empty)"
           for arm in ("blind", "true", "mirror")})
    return score


grader_feedback_told_grade.run(kbench.llm)
