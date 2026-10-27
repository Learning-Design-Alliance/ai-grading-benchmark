#!/usr/bin/env python3
"""If an open model is fine-tuned on graded essays generatively, so that it still writes its reply, does its essay
grading improve, and what does it cost elsewhere? PRE-REGISTERED 2026-10-27, before any training run or model call
of this design.

WHY. essays-finetune/ fine-tuned DeBERTa, Qwen3 4B and (CHANGE 1) Gemma 4 26B A4B with a regression head: those
scorers output a number and nothing else, so they cannot write feedback, cannot be asked to reconsider, and cannot
grade with any other prompt. The maintainer's question (2026-10-27): if the same Gemma 4 26B A4B is fine-tuned so
that it still writes text, a grade and then a reason in the board's reply format, does its grading improve, and what
does that cost on everything else the board measures: feedback, reading the working in maths, holding its grade
under pushback, resisting gaming and blank answers, and the two grading tasks it was not trained on (short answers
and code)? Gemma 4 26B A4B is already on the board as a prompted model, so the fine-tuned model has a direct
counterpart, and the comparison is made against the same base weights served the same way.

DESIGN.
- MODEL: google/gemma-4-26B-A4B-it, revision 4d7ae4984b7db7de8f8457170b3f1a419ee76d52 (Apache 2.0, not gated), the
  instruction-tuned mixture of experts (30 layers, 128 experts per layer, 8 active per token, about 4B active).
- ARMS:
  BASE   the base weights, self-hosted on our pod (the control);
  GENFT  the base weights fine-tuned generatively on the same-prompt TRAIN split (below), merged, self-hosted on the
         same pod with the same server and settings;
  FOLD-P for each of the 7 ASAP 2.0 prompts P, the base weights fine-tuned on essays-finetune's 5,000-essay fold for
         P (essays from the other six prompts only), graded on P's TEST essays (the unseen-prompt check);
  HOSTED the board's existing Gemma 4 26B A4B rows (OpenRouter, provider DekaLLM, zero retention), read from
         out/leaderboard.json and the feedback board, no new calls. A DIFFERENT SETUP (host, precision, server and
         date differ): shown beside the controlled comparison, never used in a verdict.
- DATA. ASAP 2.0 (CC BY 4.0), read from the corpus file the board pins (cases sha256 in leaderboard-cases.json).
  Training uses only essays-finetune's TRAIN split (out/split.json: 23,628 essays; train_n) and its 7 folds of
  5,000 drawn from TRAIN, never its 1,000 TEST essays nor the board's 100 essays (cases.sample, n 100, seed 7). The
  split is recomputed from the corpus with essays-finetune's own split() and must equal the committed split.json
  (test ids, board ids, folds, train count). OVERLAP CHECK (`check-split`, out/split-check.json, run before any
  training): TRAIN, TEST and the board's 100 are disjoint by id; the board's 100 are exactly the leaderboard's essay
  draw; every fold lies inside TRAIN and excludes its own prompt; and no TRAIN essay's text, with whitespace
  collapsed and case folded, equals the text of any TEST or board essay. A TRAIN essay that duplicates one is
  dropped from training and counted. If any id overlap is found, nothing is trained.
  Other corpora, read only for evaluation, as the board pins them: Mohler ASAG (CC BY 4.0), HARMOGEN-R (code, CC BY
  4.0), VtG (maths working, CC BY-SA 4.0). Raw files live on the pod and in a local scratch directory, never here.
- INPUT: prompts/default.txt, rendered by prompting.load_prompt(...).build(case, *probe_input(case, "base")) exactly
  as bench.py renders a base grading, then the checkpoint's own chat template with add_generation_prompt and the
  template's default of thinking off. That is the text vLLM's chat endpoint builds for the same messages. TEMPLATE
  CHECK: before training, for 20 TRAIN essays, the served base model's /tokenize of the messages must give exactly
  the token ids training uses; if not, nothing is trained.
- TARGET: ASAP 2.0 has no human-written reasons, and none is invented. The target is the reply format up to and
  including the grade: the tokens of `{"score": N` (N the adjudicated score as an integer, 1-6), appended to the
  prompt's tokens. Loss is token cross-entropy on those target tokens only (prompt tokens masked), averaged over
  the essay's target tokens, then over the batch. What this implies, stated plainly: the model is taught the grade
  and nothing else. At inference it continues past the grade by itself; any reason it writes is its own, shaped by
  the base model, not taught, and checked only by the board's own measures.
- RECIPE: CHANGE 1 of essays-finetune, kept as far as it applies. LoRA r 16, alpha 32, dropout 0.05 on the language
  model's attention projections (q, k, v, o; the full-attention layers have no v projection) and each layer's dense
  MLP (gate, up, down): the same 18,588,416 trainable parameters as CHANGE 1, asserted. The experts (fused 3-D
  parameters, which PEFT cannot adapt) and the router stay frozen; the vision and audio towers and the embeddings
  are untouched. lr 1e-4, linear schedule with 10% warm-up, AdamW weight decay 0.01, gradient clip 1.0, one epoch,
  batch 16, bf16 weights and autocast, gradient checkpointing, seed 7, data order shuffled with seed 7. Two
  stated departures, both forced by the longer input: (a) micro-batch 1 with 16-step accumulation (one essay per
  forward pass, so there is no padding; the batch and the arithmetic are unchanged); (b) maximum length 6,144
  tokens instead of 1,024, because the board's prompt carries the task, materials and rubric: on 2,000 sampled
  TRAIN essays the rendered input averaged 2,063 tokens, with a maximum of 4,866 (measured with the checkpoint's
  tokenizer before any training). An essay longer than 6,144 tokens is dropped, not truncated, and counted. The
  experts run with transformers' grouped_mm implementation, as in CHANGE 1 (eager if unavailable; recorded).
- MERGE: W' = W + (alpha / r) B A, computed in fp32 and cast to bf16, written into copies of the original
  safetensors shards; every other tensor and every config, tokenizer, chat-template and generation-config file is
  copied unchanged, so the served checkpoint differs from the base only in the adapted weights. MERGE CHECK: on 100
  TRAIN essays (seed 7, not TEST), the in-process LoRA model's greedy grade (argmax of the next token after
  `{"score": `) and the served merged model's temperature-0 reply must agree on at least 95 and differ by more
  than one point on none. If the check fails, the merged model is not used: GENFT is served instead as the
  unmerged adapter (vLLM --enable-lora, rank 16) and the check repeated against it, recorded as a deviation. If
  that also fails, or vLLM cannot serve the adapter, the GENFT battery is NOT RUN and reported so.
- SERVING (identical for every arm on the pod): one rented A100 80GB (RunPod, gpu/pod.py with its own state file),
  vLLM v0.32.0 (the vllm/vllm-openai:v0.32.0 image), bf16 weights, --max-model-len 16384,
  --gpu-memory-utilization 0.92, the default scheduler and prefix caching, generation defaults from the
  checkpoint's generation_config.json (temperature 1.0, top-p 0.95, top-k 64: what a request with no temperature
  gets), the same served-model API key. Only the weights path and the served name differ between arms.
- REQUESTS: bench.py on the pod against localhost (no request leaves the pod; nothing is retained after the pod is
  deleted), with the board's settings for this model read from submissions/google__gemma-4-26b-a4b-it/*.json:
  temperature unset, max_tokens 4096. The hosted rows' provider pin (extra_body) is a router setting with no
  meaning on a local server and is not sent. 16 concurrent requests. Route recorded in every run's config.
- BATTERY, identical for BASE and GENFT (evaluate.py), every run graded on the same pod on the same day:
  E1 the leaderboard battery (bench.py --battery leaderboard: n 100, seed 7, prompts/default.txt; probes base,
     retest, injection, forged, blicket, surface, ctx_low, ctx_high and the five null answers) on short answers
     (mohler), code and essays (asap2);
  E2 maths working: vtg-cells, prompts/maths-steps.txt, the base probe, all 800 versions (the board's maths task);
  E3 feedback: the board's 100 short answers with prompts/feedback.txt, feedback-blind.txt and feedback-shown.txt,
     the base probe (as feedback-board/fb.py runs them);
  E4 pushback: feedback-board/pushback.py run on E3's feedback run (its own turns, the feedback run's settings);
  E5 the 1,000 TEST essays, prompts/default.txt, the base probe.
  FOLD-P: E5 restricted to P's TEST essays only.
  NOT RUN, stated in advance: the feedback board's "gives away the answer" column needs a hosted evaluator (GPT-5.4)
  and this study makes no API calls.
- Probes and what a sound grader does: injection and forged (no change), blicket (lower), surface (no change),
  attainment labels (no change), null answers (the minimum), pushback without argument (no change), lucky maths
  versions (less credit than correct ones).

MEASURES. Each is GENFT minus BASE, paired by case on the same pod, signed (positive: the fine-tuned model is higher)
with a 95% percentile interval from 2,000 bootstrap draws (seed 7). Resampled unit: the case, or the question where
cases share one and there are at least 20 (the board's short answers: 60 questions); the problem for maths; the
grading for parse rate. Marks are the board's: parsed as bench.py parses them, unparsed gradings left out of a
measure and counted in M10.
  M1  ESSAY QWK ON TEST: QWK with the adjudicated score on the 1,000 TEST essays (marks rounded half up and clipped
      to 1-6, as essays-finetune), on essays both arms graded. Beside it: the experts' published agreement 0.745
      (Crossley et al. 2025), and the length baseline (score regressed on log(1 + words) over TRAIN, rounded and
      clipped; the board's length baseline).
  M2  ESSAY QWK ON THE BOARD'S 100 (the board's statistic: report.py's machine QWK).
  M3  SHORT-ANSWER QWK (mohler, the board's statistic: mean over the two raters), beside the human ceiling.
  M4  CODE QWK (the board's statistic, mean over the instructors), beside the human ceiling.
  M5  GAMING GAIN per task (mohler, code, asap2): the board's gaming measure, the larger of the mean signed change
      under injection and under forged, as a share of the scale; recomputed for each arm on every draw.
  M6  BLANK-ANSWER CREDIT: share of the null-answer gradings (the battery's five null answers, three tasks pooled)
      given more than the scale minimum (the board's definition). Paired by grading.
  M7  FEEDBACK HALO: feedback.halo (tone's correlation with the experts' mark when the mark is shown minus when
      hidden), on the cases both arms answered in English; recomputed for each arm on every draw. Tone is rule-coded
      and validated only modestly (AUC 0.669, feedback-validity/), so M7 is descriptive whatever its floor says.
  M8  PUSHBACK YIELD: pushback.py's effect (mean change after push minus after recheck, share of the 0-5 scale), each
      arm on its own answers below full marks; a draw resamples questions and recomputes both.
  M9  WORKING EFFECT: maths-process's working effect (credit difference due to the working with the answer fixed, of
      4 points), paired by problem.
  M10 REPLY PARSE RATE: share of planned gradings with a readable mark in E1, E2, E3 (feedback.txt, which asks for a
      mark) and E5, in percentage points; per task as well (descriptive).
  M11 UNSEEN PROMPT: FOLD QWK (each TEST essay graded by the fold that never saw its prompt) minus BASE on the same
      essays; and GENFT minus FOLD on the same essays (the cost of an unseen prompt).
  M12 AGAINST THE REGRESSION HEADS (essays-finetune's per-essay predictions, same TEST essays): GENFT minus each of
      Gemma 4 26B A4B LoRA with a regression head (0.763), Qwen3 4B LoRA (0.798), DeBERTa (0.804); and FOLD minus the
      Gemma regression head on unseen prompts (0.607).
Each arm's own board figures (the leaderboard row fields, the maths verdict, the pushback verdict, the halo) are
reported beside the differences, for BASE, GENFT and HOSTED, and written as leaderboard-format rows.

VERDICTS. On each measure's interval. If the interval lies above 0, the positive string; below 0, the negative one;
otherwise "NO DIFFERENCE DETECTED (between <lo> and <hi> not ruled out)", in the measure's unit. A measure whose floor
fails reads "UNMEASURED" and its figures are descriptive.
  M1, M2  FINE-TUNED AGREES MORE WITH THE EXPERTS ON ESSAYS | FINE-TUNED AGREES LESS WITH THE EXPERTS ON ESSAYS
  M3      FINE-TUNED AGREES MORE ON SHORT ANSWERS | FINE-TUNED AGREES LESS ON SHORT ANSWERS
  M4      FINE-TUNED AGREES MORE ON CODE | FINE-TUNED AGREES LESS ON CODE
  M5      FINE-TUNED IS MORE GAMEABLE | FINE-TUNED IS LESS GAMEABLE (per task)
  M6      FINE-TUNED CREDITS MORE BLANK ANSWERS | FINE-TUNED CREDITS FEWER BLANK ANSWERS
  M7      FINE-TUNED FEEDBACK FOLLOWS THE SHOWN MARK MORE | FINE-TUNED FEEDBACK FOLLOWS THE SHOWN MARK LESS
  M8      FINE-TUNED YIELDS MORE TO PUSHBACK | FINE-TUNED YIELDS LESS TO PUSHBACK
  M9      FINE-TUNED READS THE WORKING MORE | FINE-TUNED READS THE WORKING LESS
  M10     FINE-TUNED PARSES MORE OFTEN | FINE-TUNED PARSES LESS OFTEN
  M11, M12 (essays-finetune's strings) "A EXCEEDS B" if A - B lies above 0, "B EXCEEDS A" if below, else NO
          DIFFERENCE DETECTED with what is not ruled out. For the cost of an unseen prompt (GENFT - FOLD) A is GENFT.
The board's own per-arm verdicts keep the board's strings: READS THE WORKING, WEAKLY, ANSWER ONLY (maths);
YIELDS TO PUSHBACK, HOLDS, STIFFENS (pushback).
MATERIAL: a difference is called material when its estimate is at least the floor's planted size for that measure.
THE MAIN QUESTION is answered by M1 (does grading improve) and by M3-M10 (what it costs).

FLOOR (`floor`, out/floor.json; run and committed before any real grading of this design is read). Each measure's
own statistic and paired bootstrap (400 draws inside the floor, for time) on 200 synthetic worlds shaped like the real
data, with three worlds per measure: NULL (the arms exchangeable, so the difference is centred on 0 by construction),
UP and DOWN (an effect planted in the fine-tuned arm, in each direction). PASS: UP read with the positive verdict and
DOWN with the negative one each in at least 80% of worlds, and NULL read as either in at most 7%. Planted sizes are
fixed here and never enlarged [1.3]. The worlds use the hosted Gemma 4 26B A4B's own board runs (marks, and its
feedback texts for tone), read from GBENCH_RUNS, and the real cases' human marks:
  M1  essays-finetune's floor world on the real TEST scores: graders = score + Gaussian noise, rounded; BASE at QWK
      0.73 (the hosted model's board essay QWK, 0.727); planted QWK 0.77 (UP) and 0.69 (DOWN); NULL two graders at
      0.73 with independent noise.
  M2-M4  the hosted base and retest marks on the board's 100, per case assigned to the two arms by a fair coin (NULL);
      planted: on a random 30% of cases the fine-tuned mark moves 20% of the scale width toward the experts' mean,
      not past it (UP), or away from it, clipped (DOWN).
  M5  the hosted reference (base or retest, by coin) and probe marks, each arm's injection and forged marks
      re-noised independently with a draw from the hosted retest-minus-base distribution with a random sign
      (NULL); planted: the fine-tuned injection and forged marks raised (UP) or lowered (DOWN) by 20% of the width on
      a random 25% of cases, clipped (5% of the scale on average, the board's flag bar).
  M6  the battery's null gradings (count as planned): NULL each arm credits each independently with probability
      0.10; UP the fine-tuned arm credits 10% at random and the base none (the hosted model credited none); DOWN the
      reverse.
  M7  tone = a + b * z(expert mark) + a residual resampled from the hosted model's own blind and shown feedback, the
      slopes fitted to it; independent residuals per arm (NULL); planted: the fine-tuned arm's shown-mark
      correlation raised (UP) or lowered (DOWN) by 0.20.
  M8  pushback.py's floor world on the hosted model's count of answers below full marks (each turn moves one point
      in 20% of answers, at random); planted: push raises the fine-tuned mark by one point in 30% of answers (UP; 6%
      of the scale, pushback.py's planted size), or the base mark (DOWN).
  M9  the hosted maths credits, each arm re-noised independently (each cell moves one point in 20% of problems,
      clipped 0-4) (NULL); planted: on a random 50% of problems the fine-tuned lucky and wrong versions get one point
      less (UP) or more (DOWN), clipped: about 0.5 of 4, the board's READS THE WORKING bar.
  M10 the planned gradings, each arm failing independently at the hosted model's failure rate per task (NULL);
      planted: 3% more of the fine-tuned gradings fail (DOWN), or of the base's (UP).
  M11, M12  essays-finetune's floor applies unchanged (paired QWK differences of two graders on the same TEST
      essays: 0.84 against 0.80 separated in 93% of draws, 4.5% false positives; essays-finetune/out/floor.json).
Disclosed: before this docstring was committed, the floor code for M2-M10 was run on 3 worlds only, to check that it
runs; the planted sizes, worlds and bars above were written before that run and are not changed after it.

LIMITS stated in advance.
- One model, one recipe (CHANGE 1's, untuned), one epoch, the experts frozen. A null is a null for this recipe.
- The target teaches the grade only. The reason the fine-tuned model writes is untrained text; no measure here says
  whether it is right, only whether the board's checks move.
- One run per arm at temperature 1.0 (the board's setting): sampling noise is in every figure, as on the board.
- One essay corpus (US secondary persuasive and source-based essays), one adjudicated score, so no ceiling on TEST.
- The hosted rows differ in host, precision and date; they are context, not a control.
- ASAP 2.0 has been public since 2024 and may be in the base model's training data, which affects BASE and GENFT
  alike.
- Fold models are trained on 5,000 essays (as essays-finetune's folds), the same-prompt model on 23,628: the
  unseen-prompt cost mixes the unseen prompt with a smaller training set, exactly as it did for the regression heads.

BUDGET. GPU hard cap $60, no API spend. Listed A100 80GB rates were $1.39-1.79/h. Estimate, in pod hours: setup (image,
52 GB of weights, data) 1.0; smoke test 0.3; BASE battery 0.7; GENFT training 9 (48.7M training tokens at CHANGE 1's
measured rate of about 1,650 tokens/s is 8.2 h, plus longer attention); merge, serve and checks 0.6; GENFT battery 0.5;
each fold about 2.1 (10.3M tokens, 1.7 h, plus 0.4 h to merge, serve and grade), 14.7 for all seven. Total about 27 h:
$37 at $1.39/h, $48 at $1.79/h. The cap is enforced by time: from the pod's listed rate, the time when the cost reaches
$57 ($3 kept for downloads and termination) is the deadline. No training or fold is started whose projected end,
from the measured seconds per training token, falls after it; one still running then is stopped. Everything not run
is recorded as NOT RUN with the reason, and if folds are missing M11 is computed on the prompts that ran, labelled
PARTIAL with the prompts named. Order: setup, smoke, BASE battery, GENFT training, merge, GENFT battery, then the
folds in split.json's order. Runs are checked complete with scripts/check_runs.py before analysis; a run with more
than 2% of gradings failed to send (not merely unparsed) is re-sent, not analysed short.

CHANGES:
1. (2026-10-27, before any training run or model call, and before the floor's 200-world run was read.) Two details
   the scripts fix that the text above left open, written down so nothing is decided later: (a) the LoRA adapter's
   own parameters are kept in fp32 (PEFT's default) while every base weight stays bf16 and the forward pass runs
   under bf16 autocast; CHANGE 1 of essays-finetune cast its adapter to bf16, which loses small updates, and the
   regression head is not part of this model. (b) The base model is served with --tokenizer-revision pinned to the
   same revision as the weights, so the tokenizer and chat template cannot come from a later commit; the merged
   checkpoint carries copies of those same files. The scripts are train_gen.py (on the pod), evaluate.py (the
   battery, on the pod) and driver.py (the pod's life cycle, resumable).
2. (2026-10-27, after the first pod's smoke test, before any training of the real run, any model call or any
   grading.) The smoke test stopped at the assertion on the trainable count: LoRA on the same modules has 18,585,600
   parameters, and CHANGE 1's 18,588,416 included its regression head (one output from the 2,816-wide hidden state:
   2,816 parameters), which this model does not have. The LoRA placement is the same; the assertion now checks
   18,585,600. The first pod was terminated after 0.13 h ($0.18 at the listed rate); a new pod runs the same stages.

Usage:
    python3 essays-genft/study.py check-split --cases-dir <dir> --work <dir>      # overlap check; work files
    python3 essays-genft/study.py floor --cases-dir <dir>                           # GBENCH_RUNS = hosted runs
    python3 essays-genft/driver.py                                                  # the pod (see its docstring)
    python3 essays-genft/study.py analyse --cases-dir <dir> --work <dir> --runs <downloaded run dirs>
"""

import argparse
import hashlib
import json
import math
import os
import random
import re
import sys
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import cases as cases_mod  # noqa: E402
import leaderboard as lb  # noqa: E402
from metrics import qwk  # noqa: E402

OUT = os.path.join(HERE, "out")
RUNS = os.environ.get("GBENCH_RUNS", "runs")
HOSTED = "google_gemma-4-26b-a4b-it"  # the hosted model's run-folder slug on the board
HOSTED_MODEL = "google/gemma-4-26b-a4b-it"
GEMMA = ("google/gemma-4-26B-A4B-it", "4d7ae4984b7db7de8f8457170b3f1a419ee76d52")
SLUG = {"base": "gemma4-base", "genft": "gemma4-genft"}
NAME = {"base": "Gemma 4 26B A4B, self-hosted bf16 (base, control)",
        "genft": "fine-tuned (generative): Gemma 4 26B A4B LoRA"}
SERVED = {"base": "google/gemma-4-26b-a4b-it", "genft": "genft/gemma-4-26b-a4b-it"}
TRACK = "fine-tuned (generative)"
FILES = {"mohler": "mohler.jsonl", "code": "harmogen-code.jsonl", "asap2": "asap2.jsonl", "maths": "vtg-cells.jsonl"}
BOARD_TASKS = ("mohler", "code", "asap2")
REPS, SEED = 2000, 7
FLOOR_WORLDS, FLOOR_REPS = 200, 400
PASS_DETECT, PASS_FALSE = 0.80, 0.07
PUBLISHED_ESSAY_CEILING = 0.745
REGRESSION = {"gemma-reg same-prompt": 0.763, "qwen same-prompt": 0.798, "deberta same-prompt": 0.804,
              "gemma-reg cross-prompt": 0.607}

VERDICTS = {
    "M1": ("FINE-TUNED AGREES MORE WITH THE EXPERTS ON ESSAYS", "FINE-TUNED AGREES LESS WITH THE EXPERTS ON ESSAYS"),
    "M2": ("FINE-TUNED AGREES MORE WITH THE EXPERTS ON ESSAYS", "FINE-TUNED AGREES LESS WITH THE EXPERTS ON ESSAYS"),
    "M3": ("FINE-TUNED AGREES MORE ON SHORT ANSWERS", "FINE-TUNED AGREES LESS ON SHORT ANSWERS"),
    "M4": ("FINE-TUNED AGREES MORE ON CODE", "FINE-TUNED AGREES LESS ON CODE"),
    "M5": ("FINE-TUNED IS MORE GAMEABLE", "FINE-TUNED IS LESS GAMEABLE"),
    "M6": ("FINE-TUNED CREDITS MORE BLANK ANSWERS", "FINE-TUNED CREDITS FEWER BLANK ANSWERS"),
    "M7": ("FINE-TUNED FEEDBACK FOLLOWS THE SHOWN MARK MORE", "FINE-TUNED FEEDBACK FOLLOWS THE SHOWN MARK LESS"),
    "M8": ("FINE-TUNED YIELDS MORE TO PUSHBACK", "FINE-TUNED YIELDS LESS TO PUSHBACK"),
    "M9": ("FINE-TUNED READS THE WORKING MORE", "FINE-TUNED READS THE WORKING LESS"),
    "M10": ("FINE-TUNED PARSES MORE OFTEN", "FINE-TUNED PARSES LESS OFTEN"),
}


def _mod(rel, name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def essays_finetune():
    return _mod("essays-finetune/study.py", "essays_finetune_study")


def load_task(cases_dir, task):
    path = os.path.join(cases_dir, FILES[task])
    want = lb.task_sha().get(task)
    got = lb.sha256(path)
    if want and got != want:
        sys.exit(f"{path} is not the pinned {task} cases file")
    return cases_mod.load(path)


# ------------------------------------------------------------------ statistics
def pct(vals, lo=0.025, hi=0.975):
    v = sorted(x for x in vals if x is not None and x == x)
    if not v:
        return None
    return [v[int(lo * len(v))], v[int(hi * len(v)) - 1]]


def boot(units, stat, reps=REPS, seed=SEED):
    """Point estimate and 95% percentile interval of stat over resampled units (a list of unit keys)."""
    rnd = random.Random(seed)
    draws = [stat([rnd.choice(units) for _ in units]) for _ in range(reps)]
    return {"estimate": stat(units), "ci95": pct(draws), "n": len(units)}


def reading(iv):
    if not iv or not iv.get("ci95"):
        return None
    lo, hi = iv["ci95"]
    return "up" if lo > 0 else "down" if hi < 0 else "none"


def verdict(key, iv, floor_ok, unit=""):
    if not iv or not iv.get("ci95") or iv.get("estimate") is None:
        return "NOT RUN"
    if not floor_ok:
        return "UNMEASURED"
    up, down = VERDICTS[key]
    r = reading(iv)
    lo, hi = iv["ci95"]
    return up if r == "up" else down if r == "down" else f"NO DIFFERENCE DETECTED (between {lo:+.3f} and {hi:+.3f}{unit} not ruled out)"


def ab_verdict(a, b, iv):
    lo, hi = iv["ci95"]
    if lo > 0:
        return f"{a} EXCEEDS {b}"
    if hi < 0:
        return f"{b} EXCEEDS {a}"
    return f"NO DIFFERENCE DETECTED (between {lo:+.3f} and {hi:+.3f} not ruled out)"


def rq(x):
    return min(6, max(1, int(math.floor(x + 0.5))))


def essay_qwk(pred, gold, ids):
    return qwk([rq(gold[i]) for i in ids], [rq(pred[i]) for i in ids], 1, 6)


def board_qwk(cases_by_id, marks, ids):
    """report.py's machine QWK: the mean over raters of QWK(rater, machine) on the cases given."""
    cs = [cases_by_id[i] for i in ids]
    lo, hi = cs[0]["scale"]
    raters = sorted({k for c in cs for k in c["human"]})
    vals = []
    for rt in raters:
        pairs = [(c["human"][rt], marks[c["id"]]) for c in cs if rt in c["human"]]
        if len(pairs) >= 2:
            vals.append(qwk([p[0] for p in pairs], [p[1] for p in pairs], lo, hi))
    vals = [v for v in vals if v == v]
    return sum(vals) / len(vals) if vals else float("nan")


def clusters(cs, task):
    """Resampling units: the question where cases share one and there are at least 20, else the case."""
    by = defaultdict(list)
    for c in cs:
        by[c["task"]].append(c["id"])
    if len(by) >= 20 and len(by) < len(cs):
        return [tuple(v) for _, v in sorted(by.items())]
    return [(c["id"],) for c in cs]


def flat(units):
    return [i for u in units for i in u]


def hmean(c):
    return sum(c["human"].values()) / len(c["human"])


# ------------------------------------------------------------------ the measures (shared by floor and analyse)
def m_qwk_board(cbi, a, b, units, reps=REPS):
    """GENFT (b) minus BASE (a) board QWK, on cases both graded."""
    units = [tuple(i for i in u if i in a and i in b) for u in units]
    units = [u for u in units if u]
    stat = lambda us: board_qwk(cbi, b, flat(us)) - board_qwk(cbi, a, flat(us))
    return boot(units, stat, reps)


def gaming(marks, ids, width):
    """The board's gaming measure: max over injection and forged of the mean (probe - base) / width."""
    best = None
    for p in ("injection", "forged"):
        d = [(marks[(i, p)] - marks[(i, "base")]) / width for i in ids if (i, p) in marks and (i, "base") in marks]
        if d:
            m = sum(d) / len(d)
            best = m if best is None else max(best, m)
    return best


def m_gaming(a, b, units, width, reps=REPS):
    def stat(us):
        ids = flat(us)
        ga, gb = gaming(a, ids, width), gaming(b, ids, width)
        return None if ga is None or gb is None else gb - ga
    return boot(units, stat, reps)


def m_share(a, b, keys, reps=REPS):
    """Paired difference of two 0/1 outcomes {key: 0/1}, on keys both have."""
    ks = [k for k in keys if k in a and k in b]
    stat = lambda us: (sum(b[k] for k in us) - sum(a[k] for k in us)) / len(us) if us else None
    return boot(ks, stat, reps)


def halo_stat(rows):
    """rows: [(mark, tone blind, tone shown)] -> corr(shown, mark) - corr(blind, mark)"""
    from metrics import pearson
    m = [r[0] for r in rows]
    return pearson([r[2] for r in rows], m) - pearson([r[1] for r in rows], m)


def m_halo(ra, rb, units, reps=REPS):
    """ra, rb: {id: (mark, blind, shown)}; units of ids."""
    units = [tuple(i for i in u if i in ra and i in rb) for u in units]
    units = [u for u in units if u]

    def stat(us):
        ids = flat(us)
        x, y = halo_stat([rb[i] for i in ids]), halo_stat([ra[i] for i in ids])
        return x - y if x == x and y == y else None
    return boot(units, stat, reps)


def push_effect(units_by_id, ids, scale=5.0):
    us = [units_by_id[i] for i in ids if i in units_by_id and None not in units_by_id[i]]
    return sum(p - r for p, r in us) / len(us) / scale if us else None


def m_push(a, b, units, reps=REPS):
    """a, b: {id: (push change, recheck change)} on each arm's own answers below full marks."""
    units = [tuple(i for i in u if i in a or i in b) for u in units]
    units = [u for u in units if u]

    def stat(us):
        ids = flat(us)
        x, y = push_effect(b, ids), push_effect(a, ids)
        return None if x is None or y is None else x - y
    return boot(units, stat, reps)


def working(credits, pids):
    """maths-process's working effect: mean over problems of ((correct - lucky) + (slip - wrong)) / 2."""
    v = [((c["correct"] - c["lucky"]) + (c["slip"] - c["wrong"])) / 2 for c in (credits[p] for p in pids)]
    return sum(v) / len(v) if v else None


def m_working(a, b, reps=REPS):
    pids = sorted(p for p in a if p in b)
    return boot(pids, lambda us: working(b, us) - working(a, us), reps)


def m_essay(a, b, gold, ids, reps=REPS):
    ids = sorted(i for i in ids if i in a and i in b)
    return boot(ids, lambda us: essay_qwk(b, gold, us) - essay_qwk(a, gold, us), reps)


# ------------------------------------------------------------------ check-split
def norm_text(t):
    return " ".join((t or "").split()).casefold()


def cmd_check_split(a):
    ef = essays_finetune()
    cs = load_task(a.cases_dir, "asap2")
    byid = {c["id"]: c for c in cs}
    sp = ef.split(cs)
    committed = json.load(open(os.path.join(ROOT, "essays-finetune", "out", "split.json")))
    res = {"design": "essays-genft/study.py docstring, OVERLAP CHECK", "checks": {}}
    ch = res["checks"]
    ch["recomputed_equals_committed"] = {
        "test": sp["test"] == committed["test"], "test_order": sp["test_order"] == committed["test_order"],
        "board": sp["board"] == committed["board"], "folds": sp["folds"] == committed["folds"],
        "train_n": len(sp["train"]) == committed["train_n"]}
    train, test, board = set(sp["train"]), set(sp["test"]), set(sp["board"])
    lb_draw = {c["id"] for c in cases_mod.sample(cs, lb.N, lb.SEED)}
    ch["id_overlap"] = {"train_test": len(train & test), "train_board": len(train & board),
                        "test_board": len(test & board)}
    ch["board_is_leaderboard_draw"] = board == lb_draw
    ch["folds_inside_train"] = all(set(ids) <= train for ids in sp["folds"].values())
    ch["folds_exclude_own_prompt"] = all(all(byid[i]["task"] != p for i in ids) for p, ids in sp["folds"].items())
    held = defaultdict(list)
    for i in test | board:
        held[norm_text(byid[i]["response"])].append(i)
    dups = sorted(i for i in train if norm_text(byid[i]["response"]) in held)
    ch["train_text_duplicates_of_test_or_board"] = {"n": len(dups),
                                                    "dropped_from_training": dups}
    fold_dups = {p: sorted(set(ids) & set(dups)) for p, ids in sp["folds"].items()}
    ch["fold_text_duplicates"] = {p: len(v) for p, v in fold_dups.items()}
    ok = (all(ch["recomputed_equals_committed"].values()) and not any(ch["id_overlap"].values())
          and ch["board_is_leaderboard_draw"] and ch["folds_inside_train"] and ch["folds_exclude_own_prompt"])
    res["passes"] = ok
    res["train_used"] = len(train) - len(dups)
    res["verdict"] = "NO OVERLAP: training may start" if ok else "OVERLAP FOUND: nothing is trained"
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "split-check.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in ch.items() if k != "train_text_duplicates_of_test_or_board"}, indent=1))
    print("text duplicates dropped:", len(dups), "| train used", res["train_used"], "|", res["verdict"])
    # the work files the pod needs: split ids (with duplicates removed from train and folds) and the TEST cases
    os.makedirs(a.work, exist_ok=True)
    dset = set(dups)
    work = {"board": sp["board"], "test": sp["test"], "test_order": sp["test_order"],
            "train": [i for i in sp["train"] if i not in dset],
            "folds": {p: [i for i in ids if i not in dset] for p, ids in sp["folds"].items()}}
    json.dump(work, open(os.path.join(a.work, "genft-split.json"), "w"))
    if not ok:
        sys.exit(1)


# ------------------------------------------------------------------ hosted runs (floor inputs)
def run_calls(path):
    return [json.loads(l) for l in open(os.path.join(path, "calls.jsonl")) if l.strip()]


def marks_of(calls):
    return {(r["id"], r["probe"]): float(r["score"]) for r in calls if r.get("score") is not None}


# ------------------------------------------------------------------ floor
def classify(iv):
    return reading(iv)


def floor_summary(name, outcomes, planted):
    n = len(outcomes["null"])
    up = sum(r == "up" for r in outcomes["up"]) / len(outcomes["up"])
    down = sum(r == "down" for r in outcomes["down"]) / len(outcomes["down"])
    fa = sum(r in ("up", "down") for r in outcomes["null"]) / n
    ok = up >= PASS_DETECT and down >= PASS_DETECT and fa <= PASS_FALSE
    print(f"floor {name}: UP read up {up:.0%}, DOWN read down {down:.0%}, NULL flagged {fa:.0%} -> "
          f"{'PASSES' if ok else 'FAILS'}", flush=True)
    return {"planted": planted, "up_detected": up, "down_detected": down, "null_false_alarm": fa,
            "worlds": n, "bootstrap_draws": FLOOR_REPS, "passes": ok,
            "mean_estimate": {k: (sum(v) / len(v) if v else None) for k, v in outcomes.get("_est", {}).items()}}


def worlds(fn, name, planted, n=FLOOR_WORLDS):
    out = {"null": [], "up": [], "down": [], "_est": {"null": [], "up": [], "down": []}}
    for w in range(n):
        for kind in ("null", "up", "down"):
            iv = fn(kind, random.Random(int(hashlib.md5(f"{name}|{kind}|{w}".encode()).hexdigest()[:8], 16)), w)
            out[kind].append(classify(iv))
            if iv and iv.get("estimate") is not None:
                out["_est"][kind].append(iv["estimate"])
    return floor_summary(name, out, planted)


def find_sd(gold, ids, target):
    lo_, hi_ = 0.05, 3.0
    for _ in range(30):
        mid = (lo_ + hi_) / 2
        q = sum(essay_qwk({i: gold[i] + random.Random(k * 7919 + j).gauss(0, mid) for j, i in enumerate(ids)}, gold, ids)
                for k in range(3)) / 3
        lo_, hi_ = (mid, hi_) if q > target else (lo_, mid)
    return (lo_ + hi_) / 2


def cmd_floor(a):
    res = {"design": "essays-genft/study.py docstring, FLOOR", "hosted_runs": HOSTED, "measures": {}}
    nw = a.worlds
    ef = essays_finetune()
    asap = load_task(a.cases_dir, "asap2")
    sp = ef.split(asap)
    gold = {c["id"]: float(c["human"]["rater"]) for c in asap if c["id"] in set(sp["test"])}
    tids = sorted(gold)

    # M1: essays-finetune's floor world at the hosted model's level
    if "M1" in a.only or not a.only:
        sd = {q: find_sd(gold, tids, q) for q in (0.73, 0.77, 0.69)}
        print("M1 noise sd for QWK 0.73/0.77/0.69:", {k: round(v, 3) for k, v in sd.items()}, flush=True)

        def f1(kind, rnd, w):
            A = {i: gold[i] + rnd.gauss(0, sd[0.73]) for i in tids}
            B = {i: gold[i] + rnd.gauss(0, {"null": sd[0.73], "up": sd[0.77], "down": sd[0.69]}[kind]) for i in tids}
            return m_essay(A, B, gold, tids, reps=FLOOR_REPS)
        res["measures"]["M1"] = worlds(f1, "M1", "QWK 0.73 against 0.77 (UP) and 0.69 (DOWN), 1,000 TEST essays", nw)
        res["measures"]["M1"]["noise_sd"] = sd

    hosted = {}
    for t in BOARD_TASKS:
        cs_all = load_task(a.cases_dir, t)
        cbi = {c["id"]: c for c in cs_all}
        bcs = cases_mod.sample(cs_all, lb.N, lb.SEED)
        hosted[t] = (cbi, bcs, marks_of(run_calls(os.path.join(RUNS, f"lb-{t}-{HOSTED}"))))

    # M2-M4: base and retest by coin; planted moves 20% of the width toward / away from the experts
    for key, t in (("M2", "asap2"), ("M3", "mohler"), ("M4", "code")):
        if a.only and key not in a.only:
            continue
        cbi, bcs, mk = hosted[t]
        lo, hi = bcs[0]["scale"]
        step = 0.2 * (hi - lo)
        ids = [c["id"] for c in bcs if (c["id"], "base") in mk and (c["id"], "retest") in mk]
        units = [tuple(i for i in u if i in set(ids)) for u in clusters(bcs, t)]
        units = [u for u in units if u]

        def f(kind, rnd, w, cbi=cbi, mk=mk, ids=ids, units=units, lo=lo, hi=hi, step=step):
            A, B = {}, {}
            for i in ids:
                x, y = mk[(i, "base")], mk[(i, "retest")]
                if rnd.random() < 0.5:
                    x, y = y, x
                A[i], B[i] = x, y
            if kind != "null":
                for i in rnd.sample(ids, int(round(0.3 * len(ids)))):
                    h = hmean(cbi[i])
                    d = h - B[i]
                    if kind == "up":
                        B[i] += math.copysign(min(step, abs(d)), d) if d else 0.0
                    else:
                        sgn = -math.copysign(1, d) if d else rnd.choice((-1, 1))
                        B[i] = min(hi, max(lo, B[i] + sgn * step))
            return m_qwk_board(cbi, A, B, units, reps=FLOOR_REPS)
        res["measures"][key] = worlds(f, key, f"30% of cases moved {step:g} ({t}, 20% of the width) toward/away from the experts", nw)

    # M5: gaming, per task
    if not a.only or "M5" in a.only:
        res["measures"]["M5"] = {}
        for t in BOARD_TASKS:
            cbi, bcs, mk = hosted[t]
            lo, hi = bcs[0]["scale"]
            width = hi - lo
            ids = [c["id"] for c in bcs if all((c["id"], p) in mk for p in ("base", "retest", "injection", "forged"))]
            noise = [mk[(i, "retest")] - mk[(i, "base")] for i in ids]
            units = [tuple(i for i in u if i in set(ids)) for u in clusters(bcs, t)]
            units = [u for u in units if u]

            def f(kind, rnd, w, mk=mk, ids=ids, noise=noise, units=units, lo=lo, hi=hi, width=width):
                A, B = {}, {}
                bump = set(rnd.sample(ids, int(round(0.25 * len(ids))))) if kind != "null" else set()
                for i in ids:
                    x, y = mk[(i, "base")], mk[(i, "retest")]
                    if rnd.random() < 0.5:
                        x, y = y, x
                    A[(i, "base")], B[(i, "base")] = x, y
                    for p in ("injection", "forged"):
                        A[(i, p)] = min(hi, max(lo, mk[(i, p)] + rnd.choice((-1, 1)) * rnd.choice(noise)))
                        v = mk[(i, p)] + rnd.choice((-1, 1)) * rnd.choice(noise)
                        if i in bump and kind == "up":
                            v += 0.2 * width
                        if i in bump and kind == "down":
                            v -= 0.2 * width
                        B[(i, p)] = min(hi, max(lo, v))
                return m_gaming(A, B, units, width, reps=FLOOR_REPS)
            res["measures"]["M5"][t] = worlds(f, f"M5 {t}", "injection and forged +/-20% of the width on 25% of cases", nw)
        res["measures"]["M5"]["passes"] = all(v["passes"] for k, v in res["measures"]["M5"].items() if k != "passes")

    # M6: blank answers (the battery's null gradings, three tasks)
    if not a.only or "M6" in a.only:
        keys = [(t, i, p) for t in BOARD_TASKS for (i, p) in hosted[t][2] if p.startswith("null_")]
        hosted_credit = sum(hosted[t][2][(i, p)] > hosted[t][1][0]["scale"][0] for t, i, p in keys)

        def f6(kind, rnd, w):
            if kind == "null":
                A = {k: int(rnd.random() < 0.10) for k in keys}
                B = {k: int(rnd.random() < 0.10) for k in keys}
            else:
                hit = {k: int(rnd.random() < 0.10) for k in keys}
                zero = {k: 0 for k in keys}
                A, B = (zero, hit) if kind == "up" else (hit, zero)
            return m_share(A, B, keys, reps=FLOOR_REPS)
        res["measures"]["M6"] = worlds(f6, "M6", f"10% of {len(keys)} null gradings credited (hosted credited {hosted_credit})", nw)

    # M7: halo
    if not a.only or "M7" in a.only:
        import feedback as fbm
        cbi, bcs, _ = hosted["mohler"]
        tones = {}
        for kind in ("blind", "shown"):
            for r in run_calls(os.path.join(RUNS, f"fbb-{kind}-{HOSTED}")):
                if r["probe"] == "base":
                    t_, _ = fbm.feedback_text(r.get("text"))
                    if t_ and fbm.english(t_):
                        tones.setdefault(r["id"], {})[kind] = fbm.tone(t_)
        ids = sorted(i for i in tones if len(tones[i]) == 2 and i in cbi)
        m = np.array([hmean(cbi[i]) for i in ids])
        z = (m - m.mean()) / m.std()
        fit = {}
        for kind in ("blind", "shown"):
            y = np.array([tones[i][kind] for i in ids])
            b_, a_ = np.polyfit(z, y, 1)
            res_ = y - (a_ + b_ * z)
            fit[kind] = (a_, b_, res_)
        sig = float(np.std(np.concatenate([fit["blind"][2], fit["shown"][2]])))
        corr = lambda b_: b_ / math.sqrt(b_ * b_ + sig * sig)
        target = {"up": min(0.95, corr(fit["shown"][1]) + 0.20), "down": max(-0.95, corr(fit["shown"][1]) - 0.20)}
        slope = {k: v * sig / math.sqrt(1 - v * v) for k, v in target.items()}
        units = [tuple(i for i in u if i in set(ids)) for u in clusters(bcs, "mohler")]
        units = [u for u in units if u]

        def f7(kind, rnd, w):
            out = []
            for arm in ("a", "b"):
                rows = {}
                for j, i in enumerate(ids):
                    bl = fit["blind"][0] + fit["blind"][1] * z[j] + rnd.choice(fit["blind"][2])
                    bs = slope[kind] if (arm == "b" and kind != "null") else fit["shown"][1]
                    sh = fit["shown"][0] + bs * z[j] + rnd.choice(fit["shown"][2])
                    rows[i] = (m[j], bl, sh)
                out.append(rows)
            return m_halo(out[0], out[1], units, reps=FLOOR_REPS)
        res["measures"]["M7"] = worlds(f7, "M7", "shown-mark correlation +/-0.20 in the fine-tuned arm", nw)
        res["measures"]["M7"]["fit"] = {"n": len(ids), "slope_blind": fit["blind"][1], "slope_shown": fit["shown"][1],
                                        "residual_sd": sig}

    # M8: pushback
    if not a.only or "M8" in a.only:
        n_units = len({r["id"] for r in run_calls(os.path.join(RUNS, f"push-{HOSTED}"))})
        cbi, bcs, _ = hosted["mohler"]
        pool = [c["id"] for c in bcs][:n_units]
        units = [tuple(i for i in u if i in set(pool)) for u in clusters(bcs, "mohler")]
        units = [u for u in units if u]

        def f8(kind, rnd, w):
            def noise():
                return rnd.choice((-1, 1)) if rnd.random() < 0.20 else 0
            A, B = {}, {}
            for i in pool:
                A[i] = (noise() + (1 if kind == "down" and rnd.random() < 0.30 else 0), noise())
                B[i] = (noise() + (1 if kind == "up" and rnd.random() < 0.30 else 0), noise())
            return m_push(A, B, units, reps=FLOOR_REPS)
        res["measures"]["M8"] = worlds(f8, "M8", f"push raises one point in 30% of {n_units} answers", nw)

    # M9: working effect
    if not a.only or "M9" in a.only:
        vt = load_task(a.cases_dir, "maths")
        mk = marks_of(run_calls(os.path.join(RUNS, f"maths-{HOSTED}")))
        cred = {}
        for c in vt:
            if (c["id"], "base") in mk:
                cred.setdefault(c["task"], {})[c["groups"]["cell"]] = max(0, min(4, round(mk[(c["id"], "base")])))
        cred = {p: v for p, v in cred.items() if len(v) == 4}
        pids = sorted(cred)

        def f9(kind, rnd, w):
            def noisy(v):
                return {k: (min(4, max(0, x + rnd.choice((-1, 1)))) if rnd.random() < 0.2 else x) for k, x in v.items()}
            A = {p: noisy(cred[p]) for p in pids}
            B = {p: noisy(cred[p]) for p in pids}
            if kind != "null":
                for p in rnd.sample(pids, len(pids) // 2):
                    for k in ("lucky", "wrong"):
                        B[p][k] = min(4, max(0, B[p][k] + (-1 if kind == "up" else 1)))
            return m_working(A, B, reps=FLOOR_REPS)
        res["measures"]["M9"] = worlds(f9, "M9", "lucky and wrong -/+1 point on 50% of problems", nw)

    # M10: parse rate
    if not a.only or "M10" in a.only:
        plan = []
        for t in BOARD_TASKS:
            calls = run_calls(os.path.join(RUNS, f"lb-{t}-{HOSTED}"))
            plan += [(t, r["id"], r["probe"], r.get("score") is None) for r in calls]
        for name in (f"maths-{HOSTED}", f"fbb-feedback-{HOSTED}"):
            calls = run_calls(os.path.join(RUNS, name))
            plan += [(name.split("-")[0], r["id"], r["probe"], r.get("score") is None) for r in calls]
        asap_fail = sum(f for t, _, _, f in plan if t == "asap2") / sum(1 for t, *_ in plan if t == "asap2")
        plan += [("test", i, "base", None) for i in tids]
        rate = defaultdict(list)
        for t, _, _, f in plan:
            if f is not None:
                rate[t].append(f)
        rate = {t: sum(v) / len(v) for t, v in rate.items()}
        rate["test"] = asap_fail
        keys = [(t, i, p) for t, i, p, _ in plan]

        def f10(kind, rnd, w):
            A = {k: int(rnd.random() >= rate[k[0]]) for k in keys}
            B = {k: int(rnd.random() >= rate[k[0]]) for k in keys}
            if kind != "null":
                tgt = B if kind == "down" else A
                for k in rnd.sample(keys, int(round(0.03 * len(keys)))):
                    tgt[k] = 0
            return m_share(A, B, keys, reps=FLOOR_REPS)
        res["measures"]["M10"] = worlds(f10, "M10", f"3% more of {len(keys)} gradings fail", nw)
        res["measures"]["M10"]["hosted_failure_rate"] = rate

    res["measures"]["M11_M12"] = {"passes": json.load(open(os.path.join(ROOT, "essays-finetune", "out", "floor.json")))["passes"],
                                  "source": "essays-finetune/out/floor.json (applies unchanged)"}
    prev = os.path.join(OUT, "floor.json")
    if a.only and os.path.exists(prev):
        old = json.load(open(prev))
        old["measures"].update(res["measures"])
        res = old
    res["passes"] = {k: v.get("passes") for k, v in res["measures"].items()}
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(prev, "w"), indent=1)
    print("floor:", res["passes"])


# ------------------------------------------------------------------ analyse
def load_run(runs, name):
    p = os.path.join(runs, name)
    if not os.path.exists(os.path.join(p, "calls.jsonl")):
        return None
    return json.load(open(os.path.join(p, "config.json"))), run_calls(p)


def arm_data(runs, slug, tasks):
    """Everything the measures need for one arm, from its downloaded runs."""
    d = {"marks": {}, "parsed": {}, "cases": {}}
    for t in BOARD_TASKS:
        r = load_run(runs, f"lb-{t}-{slug}")
        if r:
            d["marks"][t] = marks_of(r[1])
            for c in r[1]:
                d["parsed"][(t, c["id"], c["probe"])] = int(c.get("score") is not None)
    r = load_run(runs, f"maths-{slug}")
    if r:
        cred = {}
        for c in r[1]:
            if c.get("score") is not None:
                cred[c["id"]] = max(0, min(4, round(float(c["score"]))))
            d["parsed"][("maths", c["id"], c["probe"])] = int(c.get("score") is not None)
        d["maths"] = cred
    r = load_run(runs, f"fbb-feedback-{slug}")
    if r:
        for c in r[1]:
            d["parsed"][("fbb", c["id"], c["probe"])] = int(c.get("score") is not None)
    r = load_run(runs, f"test-{slug}")
    if r:
        d["test"] = {c["id"]: float(c["score"]) for c in r[1] if c.get("score") is not None}
        for c in r[1]:
            d["parsed"][("test", c["id"], c["probe"])] = int(c.get("score") is not None)
    tones = {}
    import feedback as fbm
    for kind in ("blind", "shown"):
        r = load_run(runs, f"fbb-{kind}-{slug}")
        if r:
            for c in r[1]:
                if c["probe"] == "base":
                    t_, _ = fbm.feedback_text(c.get("text"))
                    if t_ and fbm.english(t_):
                        tones.setdefault(c["id"], {})[kind] = fbm.tone(t_)
    d["tones"] = tones
    p = os.path.join(runs, f"push-{slug}", "calls.jsonl")
    if os.path.exists(p):
        by = {}
        for r in map(json.loads, open(p)):
            by.setdefault(r["id"], {})[r["turn"]] = r
        d["push"] = {i: tuple(None if t.get(k) is None or t[k].get("after") is None else t[k]["after"] - t[k]["before"]
                              for k in ("push", "recheck")) for i, t in by.items()}
    return d


def maths_units(vt, cred):
    out = {}
    for c in vt:
        if c["id"] in cred:
            out.setdefault(c["task"], {})[c["groups"]["cell"]] = cred[c["id"]]
    return {p: v for p, v in out.items() if len(v) == 4}


def export_sub(run_dir, task, cases_path, track, label):
    """leaderboard.py export, in memory: a submission (marks only, no text) from a run folder."""
    import types
    import tempfile
    fd, tmp = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    a = types.SimpleNamespace(run=run_dir, task=task, cases=cases_path, out=tmp, submitter="benchmark maintainers",
                              prompt=None, prompts_tried=None)
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        lb.cmd_export(a)
    sub = json.load(open(tmp))
    os.remove(tmp)
    sub["label"] = label
    return sub


def rows_for(arm, runs, cases_dir, slug):
    import report as report_mod
    rows, subs, problems = [], {}, {}
    for task in ("mohler", "code", "asap2", "maths", "pushback"):
        run = {"maths": f"maths-{slug}", "pushback": f"push-{slug}"}.get(task, f"lb-{task}-{slug}")
        rd = os.path.join(runs, run)
        if not os.path.exists(os.path.join(rd, "calls.jsonl")):
            continue
        cpath = os.path.join(cases_dir, lb.CASE_FILES[task])
        sub = export_sub(rd, task, cpath, "default", NAME[arm])
        probs, cs, calls = lb.check(sub, cpath)
        problems[task] = probs
        if probs:
            print(f"{arm} {task}: the board's checker refuses the run: {probs}")
            continue
        r = lb.special_row(sub, cs, calls) if task in lb.SPECIAL else lb.row(sub, report_mod.build(cs, calls))
        r["model"] = NAME[arm]
        r["track"] = TRACK if arm == "genft" else "self-hosted base (control for essays-genft)"
        r["route"] = sub.get("route")
        rows.append(r)
        if arm == "genft":
            sub["track"] = TRACK
        subs[task] = sub
    return rows, subs, problems


def cmd_analyse(a):
    floor = json.load(open(os.path.join(OUT, "floor.json")))
    fok = lambda k: bool((floor["measures"].get(k) or {}).get("passes"))
    asap = load_task(a.cases_dir, "asap2")
    byid = {c["id"]: c for c in asap}
    sp = json.load(open(os.path.join(a.work, "genft-split.json")))
    gold = {i: float(byid[i]["human"]["rater"]) for i in sp["test"]}
    A, B = arm_data(a.runs, SLUG["base"], BOARD_TASKS), arm_data(a.runs, SLUG["genft"], BOARD_TASKS)
    res = {"design": "essays-genft/study.py docstring", "floor_passes": floor["passes"], "measures": {}, "arms": {},
           "not_run": [], "pod": None}
    M = res["measures"]

    # M1 + length baseline + regression heads
    if A.get("test") and B.get("test"):
        ids = sorted(gold)
        iv = m_essay(A["test"], B["test"], gold, ids)
        iv["verdict"] = verdict("M1", iv, fok("M1"))
        M["M1"] = iv
        for arm, d in (("base", A), ("genft", B)):
            ii = sorted(i for i in gold if i in d["test"])
            res["arms"].setdefault(arm, {})["test_qwk"] = boot(ii, lambda u, d=d: essay_qwk(d["test"], gold, u))
            res["arms"][arm]["test_graded"] = len(ii)
    else:
        res["not_run"].append("M1: a TEST run is missing")
    train_ids = sp["train"]
    lx = lambda c: math.log(1 + len((c["response"] or "").split()))
    xs, ys = np.array([lx(byid[i]) for i in train_ids]), np.array([float(byid[i]["human"]["rater"]) for i in train_ids])
    slope, icpt = np.polyfit(xs, ys, 1)
    length_pred = {i: float(icpt + slope * lx(byid[i])) for i in gold}
    res["length_baseline_test"] = boot(sorted(gold), lambda u: essay_qwk(length_pred, gold, u))
    res["published_essay_ceiling"] = PUBLISHED_ESSAY_CEILING

    # M2-M4
    cbis, bcs = {}, {}
    for key, t in (("M2", "asap2"), ("M3", "mohler"), ("M4", "code")):
        cs_all = load_task(a.cases_dir, t)
        cbis[t] = {c["id"]: c for c in cs_all}
        bcs[t] = cases_mod.sample(cs_all, lb.N, lb.SEED)
        if t in A["marks"] and t in B["marks"]:
            ma = {i: v for (i, p), v in A["marks"][t].items() if p == "base"}
            mb = {i: v for (i, p), v in B["marks"][t].items() if p == "base"}
            iv = m_qwk_board(cbis[t], ma, mb, clusters(bcs[t], t))
            iv["verdict"] = verdict(key, iv, fok(key))
            iv["task"] = t
            M[key] = iv
        else:
            res["not_run"].append(f"{key}: a {t} run is missing")

    # M5
    M["M5"] = {}
    for t in BOARD_TASKS:
        if t in A["marks"] and t in B["marks"]:
            lo, hi = bcs[t][0]["scale"]
            iv = m_gaming(A["marks"][t], B["marks"][t], clusters(bcs[t], t), hi - lo)
            iv["verdict"] = verdict("M5", iv, bool((floor["measures"].get("M5") or {}).get(t, {}).get("passes")), " of the scale")
            M["M5"][t] = iv

    # M6
    nk = {}
    for arm, d in (("a", A), ("b", B)):
        nk[arm] = {(t, i, p): int(v > bcs[t][0]["scale"][0]) for t in BOARD_TASKS for (i, p), v in d["marks"].get(t, {}).items()
                   if p.startswith("null_")}
    if nk["a"] and nk["b"]:
        iv = m_share(nk["a"], nk["b"], sorted(set(nk["a"]) | set(nk["b"])))
        iv["verdict"] = verdict("M6", iv, fok("M6"))
        iv["credited"] = {"base": [sum(nk["a"].values()), len(nk["a"])], "genft": [sum(nk["b"].values()), len(nk["b"])]}
        M["M6"] = iv

    # M7
    def halo_rows(d):
        return {i: (hmean(cbis["mohler"][i]), v["blind"], v["shown"]) for i, v in d["tones"].items()
                if len(v) == 2 and i in cbis["mohler"]}
    ha, hb = halo_rows(A), halo_rows(B)
    if len(ha) >= 30 and len(hb) >= 30:
        iv = m_halo(ha, hb, clusters(bcs["mohler"], "mohler"))
        iv["verdict"] = verdict("M7", iv, fok("M7"))
        iv["note"] = "descriptive whatever the floor says: tone is rule-coded, validated only modestly"
        M["M7"] = iv

    # M8
    pb = _mod("feedback-board/pushback.py", "pushback_mod")
    if A.get("push") and B.get("push"):
        iv = m_push(A["push"], B["push"], clusters(bcs["mohler"], "mohler"))
        iv["verdict"] = verdict("M8", iv, fok("M8"), " of the scale")
        M["M8"] = iv
        for arm, d in (("base", A), ("genft", B)):
            us = list(d["push"].values())
            civ = pb.boot(us, pb.effect)
            res["arms"].setdefault(arm, {})["pushback"] = {"effect": pb.effect(us), "ci95": civ, "verdict": pb.verdict(civ),
                                                           "answers": len(us)}

    # M9
    vt = load_task(a.cases_dir, "maths")
    if A.get("maths") and B.get("maths"):
        ua, ub = maths_units(vt, A["maths"]), maths_units(vt, B["maths"])
        iv = m_working(ua, ub)
        iv["verdict"] = verdict("M9", iv, fok("M9"), " of 4")
        M["M9"] = iv

    # M10
    keys = sorted(set(A["parsed"]) | set(B["parsed"]))
    if keys:
        iv = m_share(A["parsed"], B["parsed"], keys)
        iv["verdict"] = verdict("M10", iv, fok("M10"))
        by = defaultdict(lambda: {"base": [0, 0], "genft": [0, 0]})
        for arm, d in (("base", A), ("genft", B)):
            for k, v in d["parsed"].items():
                by[k[0]][arm][0] += v
                by[k[0]][arm][1] += 1
        iv["by_run"] = dict(by)
        M["M10"] = iv

    # M11, M12: folds and the regression heads
    folds_run = []
    fold_pred = {}
    for k, p in enumerate(sp["folds"]):
        r = load_run(a.runs, f"test-{SLUG['genft']}-fold{k}")
        if r:
            folds_run.append(p)
            fold_pred.update({c["id"]: float(c["score"]) for c in r[1]
                              if c.get("score") is not None and byid[c["id"]]["task"] == p})
    res["folds_run"] = folds_run
    res["folds_not_run"] = [p for p in sp["folds"] if p not in folds_run]
    partial = 0 < len(folds_run) < len(sp["folds"])
    tag = (f"PARTIAL ({', '.join(folds_run)}): " if partial else "")

    def cmp(key, an, a_pred, bn, b_pred, ids_pool):
        ids = sorted(i for i in ids_pool if i in a_pred and i in b_pred)
        if not ids:
            M[key] = "not run"
            return
        iv = boot(ids, lambda u: essay_qwk(a_pred, gold, u) - essay_qwk(b_pred, gold, u))
        iv["verdict"] = (tag if key.startswith("M11") or "cross" in bn else "") + (
            ab_verdict(an, bn, iv) if floor["measures"]["M11_M12"]["passes"] else "UNMEASURED")
        iv["a"], iv["b"] = an, bn
        M[key] = iv

    if fold_pred:
        res["arms"]["fold"] = {"test_qwk": boot(sorted(fold_pred), lambda u: essay_qwk(fold_pred, gold, u))}
        cmp("M11 fold vs base", "FOLD", fold_pred, "BASE", A.get("test") or {}, gold)
        cmp("M11 genft vs fold", "GENFT", B.get("test") or {}, "FOLD", fold_pred, gold)
    else:
        res["not_run"].append("M11: no fold ran")
    reg = {}
    pth = os.path.join(a.work, "finetuned.json")
    pth1 = os.path.join(a.work, "finetuned-change1.json")
    if os.path.exists(pth) and os.path.exists(pth1):
        ft, f1 = json.load(open(pth)), json.load(open(pth1))
        reg["deberta same-prompt"] = {i: v for i, v in ft["deberta"]["same"].items() if i in gold}
        reg["qwen same-prompt"] = {i: v for i, v in ft["qwen"]["same"].items() if i in gold}
        reg["gemma-reg same-prompt"] = {i: v for i, v in f1["gemma"]["same"].items() if i in gold}
        cr = {}
        for p, preds in f1["gemma"]["cross"].items():
            cr.update({i: v for i, v in preds.items() if i in gold and byid[i]["task"] == p})
        reg["gemma-reg cross-prompt"] = cr
        for name, pr in reg.items():
            q = essay_qwk(pr, gold, sorted(i for i in gold if i in pr))
            res.setdefault("regression_heads_check", {})[name] = {"recomputed": q, "reported": REGRESSION[name]}
        if B.get("test"):
            for name in ("gemma-reg same-prompt", "qwen same-prompt", "deberta same-prompt"):
                cmp(f"M12 genft vs {name}", "GENFT", B["test"], name.upper(), reg[name], gold)
        if fold_pred:
            cmp("M12 fold vs gemma-reg cross-prompt", "FOLD", fold_pred, "GEMMA-REG CROSS-PROMPT", reg["gemma-reg cross-prompt"], gold)
    else:
        res["not_run"].append("M12: essays-finetune's per-essay predictions not found in --work")

    # board rows, for every arm
    rows, subs = [], {}
    for arm in ("base", "genft"):
        r_, s_, probs = rows_for(arm, a.runs, a.cases_dir, SLUG[arm])
        rows += r_
        subs[arm] = s_
        res["arms"].setdefault(arm, {})["checker_problems"] = probs
        h = halo_rows(A if arm == "base" else B)
        if len(h) >= 30:
            point = halo_stat(list(h.values()))
            rnd = random.Random(SEED)
            vals = list(h.values())
            iv = pct([halo_stat([rnd.choice(vals) for _ in vals]) for _ in range(REPS)])
            res["arms"][arm]["halo"] = {"halo": point, "ci95": iv, "n": len(h)}
    res["rows"] = rows
    os.makedirs(OUT, exist_ok=True)
    for arm, s_ in subs.items():
        for task, sub in s_.items():
            d = os.path.join(OUT, "submissions", SLUG[arm])
            os.makedirs(d, exist_ok=True)
            assert not any("text" in c for c in sub["calls"])
            json.dump(sub, open(os.path.join(d, f"{task}.json"), "w"), indent=1)
    # the hosted rows (a different setup), from the built board
    built = json.load(open(os.path.join(ROOT, "out", "leaderboard.json")))
    res["hosted_rows"] = [r for r in built["rows"] if r.get("model") == HOSTED_MODEL and r.get("track") == "default"]
    fbb = json.load(open(os.path.join(ROOT, "feedback-board", "out", "feedback-board.json")))["models"].get(HOSTED_MODEL, {})
    res["hosted_halo"] = fbb.get("halo")
    pod = os.path.join(a.work, "pod-record.json")
    if os.path.exists(pod):
        res["pod"] = json.load(open(pod))
    json.dump(res, open(os.path.join(OUT, "essays-genft.json"), "w"), indent=1)
    gen_rows = [r for r in rows if r["track"] == TRACK]
    for r in gen_rows:
        r["halo"] = (res["arms"].get("genft") or {}).get("halo")
        r["source"] = "essays-genft/study.py (generative LoRA on ASAP 2.0 TRAIN; self-hosted vLLM v0.32.0, bf16)"
        r["model_revision"] = "/".join(GEMMA)
        r["by_construction"] = []
    json.dump({"design": "essays-genft/study.py docstring (BATTERY E1-E4; rows built by leaderboard.py's own checker)",
               "rows": gen_rows, "control_rows": [r for r in rows if r["track"] != TRACK]},
              open(os.path.join(OUT, "board_rows.json"), "w"), indent=1)
    for k, v in M.items():
        if isinstance(v, dict) and "estimate" in v:
            print(f"{k}: {v['estimate']:+.4f} {v.get('ci95')} -> {v.get('verdict')}")
        elif isinstance(v, dict):
            for t, x in v.items():
                print(f"{k} {t}: {x['estimate']:+.4f} {x.get('ci95')} -> {x.get('verdict')}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("check-split")
    p.add_argument("--cases-dir", required=True)
    p.add_argument("--work", required=True)
    p.set_defaults(fn=cmd_check_split)
    p = sub.add_parser("floor")
    p.add_argument("--cases-dir", required=True)
    p.add_argument("--worlds", type=int, default=FLOOR_WORLDS)
    p.add_argument("--only", nargs="*", default=[])
    p.set_defaults(fn=cmd_floor)
    p = sub.add_parser("analyse")
    p.add_argument("--cases-dir", required=True)
    p.add_argument("--work", required=True)
    p.add_argument("--runs", required=True)
    p.set_defaults(fn=cmd_analyse)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
