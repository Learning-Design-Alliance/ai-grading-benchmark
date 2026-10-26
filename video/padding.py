#!/usr/bin/env python3
"""Does a longer recording make an event harder to find? LASANA error labels, with the length varied and the
event held fixed. PRE-REGISTERED 2026-10-24, before any call of this design.

WHY. On LASANA's own recordings, length and skill are almost the same thing (faster is better), so grading
accuracy by length would compare good trainees with poor ones. Here the event is fixed and only the length
moves. The design follows needle-in-a-haystack tests of video models (TimeScope), with a grading question
("did this error happen?") in place of a retrieval one.

CASES. Every recording in LASANA's test split (205; `video/fetch_lasana.py --all-test`), left camera, one
discrete error per task, the corpus's own yes/no labels:
  PegTransfer       an object was dropped        object_dropped_within_fov OR object_dropped_outside_of_fov
  CircleCutting     the gauze came off a clip    gauze_detached
  BalloonResection  the inner balloon was opened balloon_opened
  SutureAndKnot     the needle was dropped       needle_dropped
Each recording is asked about at two lengths:
  x1  the recording itself;
  x4  the recording joined to three other test-split recordings of the same task in which the event did not happen.
The pads are drawn from the test split (never the recording itself), and the recording's position among them is
drawn at random (seed 7). So the event's presence is the same at every length, and the label holds for the
joined video: a pad never contains the event. Pads show other trainees doing the same task in the same box.
The question says the recording may show the task more than once, so a model is not misled by the repeats.

PROMPT. prompts/video-event.txt: the task, the event, and "1 if it happened anywhere in the recording, 0 if
not". The length is not given.

GRADERS. The video models of the video task that took the video and followed the format there: Gemini 3.5
Flash Lite, Gemini 3.8 Flash, Gemini 4 Argon, Perceptron mk1.5, Qwen3.8 27B. MiMo v2.6 Flash is left out
(it was charged for about 2,500 tokens a recording, so it does not see the video at this length), as is Nova
2 Lite (it described the video instead of answering on about nine in ten gradings). These exclusions rest on
input and format failures in the video task, not on its accuracy, and are stated here before any call.
Default settings, max_tokens 4096, zero data retention.

MEASURES, per model and length: sensitivity (share of event recordings answered 1), specificity (share of
event-free recordings answered 0), balanced accuracy, and failures (no answer). The effect of length is the
paired change from x1 to x4 in each, with a 95% interval by bootstrap over recordings
(stratified by task, 2,000 draws, seed 7).

VERDICTS (pre-registered), per model, on balanced accuracy x4 minus x1:
  LENGTH HURTS DETECTION      the interval lies below 0
  NO DETECTABLE EFFECT        the interval contains 0
  LENGTH HELPS DETECTION      the interval lies above 0
Sensitivity and specificity are reported with their own intervals. A model that answers 1 more often at x4
shows as higher sensitivity and lower specificity, which is why the verdict rests on balanced accuracy.

FLOOR (`floor`, run before any call). Simulated detectors on the real label counts: one whose sensitivity
falls from 0.80 to 0.55 at x4 with specificity 0.85 throughout must read LENGTH HURTS in at least 80% of
worlds, and one with no change must read it in at most 5%. The first design (the video task's 100 recordings,
37 with the event, three lengths) FAILED this floor: 56% of planted drops detected. With the whole test split
(205 recordings, 78 with the event) it passes; the 2x length was dropped to keep the cost down.

CHANGE 1 (2026-10-25, after O'Neill 2026 on low-powered nulls read as absence): a null verdict is never
printed alone. Beside it, `not_ruled_out` gives the largest effect in the direction of concern (a loss of balanced accuracy) that its 95%
interval still allows. The pre-registered verdict strings and thresholds are unchanged.

CHANGE 2 (2026-10-26, after the first five graders' results were read; written before any call for the graders
it adds): added under the maintainer's coverage rule (2026-10-26: every board model runs every task its inputs
allow), not because of any result. Every leaderboard model that can take video or images is added, as in the video
task:
  - sent the joined video (they take video): Gemma 4 31B, Gemma 4 26B A4B, GLM 5.3 Flash;
  - sent 16 evenly spaced frames of it (`bench.py --video-frames 16`; they take images, not video): Claude Opus
    5.5, Claude Haiku 5.5, Claude Fable 5.1, GPT-5 Mini, GPT-5.6 Luna, GPT-6 Astra, DeepSeek V4.1 Flash and its
    10-17 snapshot, Gemma 3 27B, Gemma 3 4B, Ministral 8B.
  Gemini 3.5 Flash Lite is already in. Cases, prompt, seed, base probe, max_tokens 4096, verdicts, thresholds and
  floor are unchanged. Each model keeps its leaderboard host pin and zero retention; Claude Fable 5.1, which has no
  zero-retention route, runs under the board's stated exception (the maintainers' own Anthropic key, 30-day
  safety retention, public corpora only), recorded in its run. A model that answers in no readable format is
  kept and its failures reported, not excluded after the fact.
  CAVEAT for the frames rows, stated before any call: 16 frames from a recording four times as long are four
  times as sparse, so a frames model's x4 change mixes length with sampling density. Those rows are labelled
  "16 frames" and read as what a frames-only grader would do with a long recording, not as the length effect alone.
  BUDGET: estimated at $60 (most of it Fable and Astra), within the coverage work's $300 cap, with a spend cap on
  each run.

    python3 video/padding.py build --root $LASANA_DIR
    python3 video/padding.py floor
    python3 video/padding.py analyse --runs <run dir> ... --out out/video/padding.json

Reads LASANA's annotation files and the fetched videos; writes the joined videos beside them and aggregates only.
"""
import argparse
import json
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import fetch_lasana as F  # noqa: E402

EVENTS = {
    "PegTransfer": ("an object was dropped (a triangular object fell from the grasper, whether or not it was "
                    "picked up again)", ["object_dropped_within_fov", "object_dropped_outside_of_fov"]),
    "CircleCutting": ("the gauze came detached from one or more of the metal clips", ["gauze_detached"]),
    "BalloonResection": ("the inner balloon was opened, so that more than half of its water leaked out", ["balloon_opened"]),
    "SutureAndKnot": ("the suture needle was dropped", ["needle_dropped"]),
}
LENGTHS = (1, 4)


def labels(root):
    out = {}
    for t in F.TASKS:
        cols = EVENTS[t][1]
        for x in F.read(root, f"{t}.csv"):
            out[x["id"]] = (t, int(any(x[c] == "True" for c in cols)))
    return out


def test_split(root):
    return {t: sorted(x["id"] for x in F.read(root, f"{t}_split.csv") if x["split"] == "test") for t in F.TASKS}


def concat(paths, dst):
    lst = dst + ".txt"
    with open(lst, "w") as f:
        for p in paths:
            f.write(f"file '{p}'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    "-movflags", "+faststart", dst], check=True)
    os.remove(lst)


def cmd_build(a):
    sys.path.insert(0, os.path.dirname(HERE))
    from cases import LASANA_TASKS, normalise, write
    lab = labels(a.root)
    vids = os.path.join(a.root, "videos")
    sel = test_split(a.root)
    rng = random.Random(7)
    out_dir = os.path.join(vids, "padded")
    os.makedirs(out_dir, exist_ok=True)
    cases = []
    for t in F.TASKS:
        clean = [i for i in sel[t] if lab[i][1] == 0]
        event, _ = EVENTS[t]
        for rid in sel[t]:
            pool = [i for i in clean if i != rid]
            for k in LENGTHS:
                if k == 1:
                    path = os.path.join(vids, f"{rid}_left.mp4")
                else:
                    pads = rng.sample(pool, k - 1)
                    order = pads[:]
                    order.insert(rng.randrange(k), rid)
                    path = os.path.join(out_dir, f"{rid}_x{k}.mp4")
                    if not os.path.exists(path):
                        concat([os.path.join(vids, f"{i}_left.mp4") for i in order], path)
                cases.append(normalise({
                    "id": f"ev-{rid}-x{k}", "task": f"{t} x{k}", "question": LASANA_TASKS[t][0], "reference": "",
                    "rubric": f"Event: {event}.", "materials": "",
                    "response": "(the recording is attached; it may show the task being done more than once)",
                    "scale": [0, 1], "human": {"label": float(lab[rid][1])}, "groups": {"task": t, "length": f"x{k}"},
                    "media": [{"kind": "video", "path": path, "format": "mp4"}],
                }))
    write(cases, os.path.join(a.root, "lasana-events.jsonl"))
    n1 = [c for c in cases if c["id"].endswith("x1")]
    print(f"{len(cases)} cases ({len(n1)} recordings x {len(LENGTHS)} lengths); "
          f"{sum(c['human']['label'] for c in n1):.0f} with the event -> {os.path.join(a.root, 'lasana-events.jsonl')}")


def measures(units):
    """units: [(task, label, {1: answer, 2: answer, 4: answer})] -> {length: (sens, spec, bal)}"""
    out = {}
    for k in LENGTHS:
        pos = [u[2][k] for u in units if u[1] == 1 and u[2].get(k) is not None]
        neg = [u[2][k] for u in units if u[1] == 0 and u[2].get(k) is not None]
        sens = sum(pos) / len(pos) if pos else None
        spec = sum(1 - x for x in neg) / len(neg) if neg else None
        out[k] = (sens, spec, None if sens is None or spec is None else (sens + spec) / 2)
    return out


def boot(units, reps=2000, seed=7):
    by = {}
    for u in units:
        by.setdefault(u[0], []).append(u)
    rng = random.Random(seed)
    draws = {(k, j): [] for k in LENGTHS[1:] for j in range(3)}
    for _ in range(reps):
        s = [rng.choice(us) for us in by.values() for _ in us]
        m = measures(s)
        for k in LENGTHS[1:]:
            for j in range(3):
                if m[k][j] is not None and m[1][j] is not None:
                    draws[(k, j)].append(m[k][j] - m[1][j])
    ci = {}
    for key, v in draws.items():
        v.sort()
        ci[key] = [v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]] if v else None
    return ci


def verdict(iv):
    if iv is None:
        return None
    return "LENGTH HURTS DETECTION" if iv[1] < 0 else "LENGTH HELPS DETECTION" if iv[0] > 0 else "NO DETECTABLE EFFECT"


def cmd_floor(a):
    root = a.root
    lab = labels(root)
    sel = [(t, i) for t, ids in test_split(root).items() for i in ids]
    rng = random.Random(11)
    res = {}
    for name, sens4 in (("drop", 0.55), ("none", 0.80)):
        hits = 0
        for w in range(a.worlds):
            units = []
            for t, i in sel:
                y = lab[i][1]
                ans = {}
                for k in LENGTHS:
                    s = 0.80 if k == 1 else (0.80 + (sens4 - 0.80) * (k - 1) / 3)
                    ans[k] = int(rng.random() < s) if y else int(rng.random() > 0.85)
                units.append((t, y, ans))
            iv = boot(units, reps=400, seed=w)[(4, 2)]
            hits += verdict(iv) == "LENGTH HURTS DETECTION"
        res[name] = hits / a.worlds
    ok = res["drop"] >= 0.80 and res["none"] <= 0.05
    print(f"planted drop read as LENGTH HURTS in {res['drop']:.0%} of worlds; no change in {res['none']:.0%} -> "
          f"{'FLOOR PASSES' if ok else 'FLOOR FAILS'}")
    os.makedirs(os.path.join(os.path.dirname(HERE), "out", "video"), exist_ok=True)
    json.dump({"design": "padding.py floor", "worlds": a.worlds, "read_as_hurts": res, "passes": ok},
              open(os.path.join(os.path.dirname(HERE), "out", "video", "padding-floor.json"), "w"), indent=1)


def cmd_analyse(a):
    res = {"design": "video/padding.py docstring", "runs": {}}
    for run in a.runs:
        calls = [json.loads(l) for l in open(os.path.join(run, "calls.jsonl"))]
        cfg = json.load(open(os.path.join(run, "config.json")))
        cs = {json.loads(l)["id"]: json.loads(l) for l in open(cfg["cases"])}
        ans, fails = {}, {k: 0 for k in LENGTHS}
        for r in calls:
            if r["probe"] != "base":
                continue
            rid, k = r["id"][3:].rsplit("-x", 1)
            k = int(k)
            if r.get("score") is None:
                fails[k] += 1
                continue
            ans.setdefault(rid, {})[k] = int(r["score"] >= 0.5)
        units = []
        for cid, c in cs.items():
            if cid.endswith("-x1"):
                rid = cid[3:-3]
                units.append((c["groups"]["task"], int(c["human"]["label"]), ans.get(rid, {})))
        m, ci = measures(units), boot(units)
        row = {"model": cfg["model"], "failed": fails,
               "by_length": {f"x{k}": {"sensitivity": m[k][0], "specificity": m[k][1], "balanced": m[k][2]} for k in LENGTHS},
               "change": {f"x{k}-x1": {"sensitivity": (None if m[k][0] is None else m[k][0] - m[1][0], ci[(k, 0)]),
                                        "specificity": (None if m[k][1] is None else m[k][1] - m[1][1], ci[(k, 1)]),
                                        "balanced": (None if m[k][2] is None else m[k][2] - m[1][2], ci[(k, 2)])} for k in LENGTHS[1:]},
               "verdict": verdict(ci[(4, 2)]),
               "not_ruled_out": (None if ci[(4, 2)] is None or verdict(ci[(4, 2)]) != "NO DETECTABLE EFFECT"
                                 else {"balanced_accuracy_loss_up_to": max(0.0, -ci[(4, 2)][0])})}
        res["runs"][os.path.basename(run.rstrip("/"))] = row
        f = lambda v: "—" if v is None else f"{v:.2f}"
        print(f"{os.path.basename(run):40s} bal x1 {f(m[1][2])} x4 {f(m[4][2])} | sens {f(m[1][0])}->{f(m[4][0])} "
              f"spec {f(m[1][1])}->{f(m[4][1])} | fails {fails} -> {row['verdict']}")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("build"); p.add_argument("--root", required=True)
    p = sub.add_parser("floor"); p.add_argument("--root", required=True); p.add_argument("--worlds", type=int, default=200)
    p = sub.add_parser("analyse"); p.add_argument("--runs", nargs="+", required=True); p.add_argument("--out", required=True)
    a = ap.parse_args()
    {"build": cmd_build, "floor": cmd_floor, "analyse": cmd_analyse}[a.cmd](a)


if __name__ == "__main__":
    main()
