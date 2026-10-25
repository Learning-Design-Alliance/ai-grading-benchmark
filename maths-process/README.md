# Do graders read the working, or only check the answer?

The design, verdicts and floor are pre-registered in `process.py`'s docstring.

**Data.** VtG word problems from GSM8K. The step-by-step student solutions were written by a language model
told to make student-like errors, and teachers marked the first wrong step.

**Design.** Each of 200 problems comes in four versions:
- **correct**: right working, right answer;
- **slip**: right working, wrong final answer;
- **lucky**: wrong working, right final answer;
- **wrong**: wrong working, wrong answer.

The numbers are the same within each problem. An answer checker gives correct and lucky 4, and slip and
wrong 0: it cannot see the working at all.

**Result.** Every model reads the working (pre-registered verdict READS THE WORKING: the working effect's
interval lies above 0.5 of 4). The spend was $6.30 for 5,600 gradings, at zero data retention.

| grader | working effect (of 4) | answer effect | correct | slip | lucky | wrong | lucky given full credit | first wrong step found* |
|---|---|---|---|---|---|---|---|---|
| answer checker (no model) | 0.00 | 4.00 | 4.00 | 0.00 | 4.00 | 0.00 | 100% | — |
| Gemini 3.5 Flash Lite | +2.76 [2.63, 2.88] | +0.48 | 3.98 | 3.19 | 0.91 | 0.74 | 2% | 69% |
| Gemma 4 31B | +2.16 [2.08, 2.23] | +0.64 | 3.98 | 2.82 | 1.30 | 1.19 | 2% | 73% |
| Claude Opus 5.5 | +2.00 [1.92, 2.09] | +1.16 | 3.83 | 1.88 | 1.04 | 0.66 | 0% | 72% |
| Claude Haiku 5.5 | +1.91 [1.81, 2.00] | +1.24 | 3.85 | 1.58 | 0.92 | 0.71 | 0% | 66% |
| DeepSeek V4.1 Flash | +1.76 [1.68, 1.85] | +0.61 | 3.93 | 2.94 | 1.79 | 1.56 | 1% | 72% |
| GPT-5 Mini | +1.75 [1.65, 1.83] | +0.56 | 3.94 | 2.99 | 1.80 | 1.62 | 0% | 69% |
| Qwen3 235B | +1.60 [1.51, 1.70] | +1.28 | 3.91 | 1.55 | 1.23 | 1.03 | 0% | 68% |

\* Exact agreement with the teacher's first wrong step, on the wrong versions. The lucky versions agree to
within a point. A correct solution is flagged as error-free 90-99.5% of the time.

**Reading.**
- **No model is fooled by a right answer with wrong working.** At most 2% of lucky solutions get full
  credit, against 100% from the answer checker. This is where an LLM grader earns its cost over a
  deterministic check.
- **Models disagree on a slip.** The same correct working ending in a wrong number gets 3.2 of 4 from
  Gemini 3.5 Flash Lite, but about 1.6-1.9 from Claude Haiku, Claude Opus and Qwen. No human scored these
  versions, so which is right is a rubric decision. The spread is the point: a student's mark for one slip
  depends on the grader by up to 1.6 points of 4. That is one concrete source of "harsh" AI marking.
- **Finding the first error** is about 70% for every model, close to the 2025 report that models struggle
  to locate it. Most models score lucky solutions only slightly above wrong ones, so the right answer buys
  little once the working is wrong.

**Extended to all 17 leaderboard models (2026-10-25).** The ten added models ran the same pinned cases and
prompt; the maths task is now part of the overall score as the "reads the working" strand. Two models, Gemma
3 4B (+0.51) and Llama 3.2 3B (+0.55), read the working only WEAKLY: their intervals reach below 0.5. The
other fifteen read it. The full table is in `out/process.json`.

**Limits.**
- The "students" are a language model. This tests whether graders read the working, not grading of real
  students' work.
- The correct solutions are a model's rephrasing of the reference solution. They may read more fluently
  than the student versions, which could inflate the working effect. The slip and lucky versions keep each
  source's own wording, so the effect partly reflects wording. It cannot be separated with this data.
- There is one run per model, with no human partial-credit marks.

Per-grader detail is in `out/process.json`.
