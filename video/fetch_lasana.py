#!/usr/bin/env python3
"""Fetch the LASANA videos the video task uses, without downloading the whole corpus.

LASANA (Laparoscopic Skill Analysis and Assessment, TU Dresden; CC BY 4.0; DOI 10.25532/OPARA-1046): 1,270
stereo recordings of four laparoscopic training tasks, each rated by three of four raters on four aspects
(1-5) summed to a global rating score (GRS, 4-20). The videos ship as one 15-28 GB zip per task and camera;
this reads each zip's directory by HTTP range requests and fetches only the chosen recordings.

SELECTION. The fixed `test` split only. Per task, recordings are sorted by the mean of their raters' GRS
(a failed recording counts as 4, the minimum) and taken at an even step, 25 per task: 100 recordings. This is
how `cases.sample` stratifies, done per task so each task contributes equally.

WHAT IS KEPT. Each recording from both cameras, re-encoded small enough to send: 480 x 270, 2 frames a
second, H.264, no audio (the originals have none). The left camera is the work; the right camera is the
`other_camera` probe (the same performance from a second viewpoint). The original .mkv is deleted after
re-encoding. Raw videos stay outside the repository.

    python3 video/fetch_lasana.py --root $LASANA_DIR [--per-task 25]

`--root` must hold `Annotation/` from the corpus's Annotation.zip (MD5 2339e7cd12ba6291e9162119ba068439).
"""
import argparse
import csv
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import remote_zip  # noqa: E402

BASE = "https://opara.zih.tu-dresden.de/server/api/core/bitstreams/{}/content"
ZIPS = {  # OPARA bitstream ids (record 629966ba-4d11-475c-a689-9959204f3be4)
    ("PegTransfer", "left"): "f577d564-0745-45b9-ac88-f82e0b7fdbee",
    ("PegTransfer", "right"): "e9b58d48-2465-4ee2-a3ca-1bb8259b81da",
    ("CircleCutting", "left"): "da15f935-03bf-4483-aab2-10315f53cdc8",
    ("CircleCutting", "right"): "71209477-b015-442c-a3e9-b35957f37203",
    ("BalloonResection", "left"): "08bc523e-b123-47d2-82b6-564e6b6551b1",
    ("BalloonResection", "right"): "7f522ef6-dafc-4761-b614-1ef3d405f853",
    ("SutureAndKnot", "left"): "005bdc22-ca88-47d7-b998-22c70dc73f80",
    ("SutureAndKnot", "right"): "cc8e197b-c96e-440b-b813-9a6e39e738ab",
}
TASKS = ["PegTransfer", "CircleCutting", "BalloonResection", "SutureAndKnot"]
FAILED_GRS = 4.0


def read(root, name):
    return list(csv.DictReader(open(os.path.join(root, "Annotation", name), encoding="utf-8"), delimiter=";"))


def rater_grs(root, task):
    """{recording id: {rater: GRS}}; a rater who marked the recording failed (no aspect scores) gives 4."""
    out = {}
    for r in range(4):
        fn = os.path.join(root, "Annotation", f"{task}_rater{r}.csv")
        if not os.path.exists(fn):
            continue
        for x in read(root, f"{task}_rater{r}.csv"):
            failed = not (x.get("bimanual_dexterity") or "").strip()
            out.setdefault(x["id"], {})[f"rater{r}"] = FAILED_GRS if failed else float(x["GRS"])
    return out


def select(root, task, per_task):
    split = {x["id"]: x["split"] for x in read(root, f"{task}_split.csv")}
    grs = rater_grs(root, task)
    ids = [i for i in grs if split.get(i) == "test" and len(grs[i]) >= 2]
    ordered = sorted(ids, key=lambda i: (sum(grs[i].values()) / len(grs[i]), i))
    step = max(1, len(ordered) // per_task)
    return sorted([i for k, i in enumerate(ordered) if k % step == 0][:per_task])


def encode(src, dst):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", "scale=480:270,fps=2", "-an", "-c:v", "libx264",
                    "-preset", "veryfast", "-crf", "30", "-pix_fmt", "yuv420p", "-movflags", "+faststart", dst], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--per-task", type=int, default=25)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--all-test", action="store_true", help="every test-split recording, left camera (for video/padding.py)")
    a = ap.parse_args()
    out_dir = os.path.join(a.root, "videos")
    os.makedirs(out_dir, exist_ok=True)
    from concurrent.futures import ThreadPoolExecutor
    jobs = []
    for task in TASKS:
        ids = select(a.root, task, a.per_task)
        if a.all_test:  # video/padding.py: every test-split recording, left camera only
            ids = sorted(x["id"] for x in read(a.root, f"{task}_split.csv") if x["split"] == "test")
        for cam in (("left",) if a.all_test else ("left", "right")):
            todo = [i for i in ids if not os.path.exists(os.path.join(out_dir, f"{i}_{cam}.mp4"))]
            if todo:
                url = BASE.format(ZIPS[(task, cam)])
                m = remote_zip.members(url)
                jobs += [(url, m[f"{task}/{cam}/{i}.mkv"], i, cam) for i in todo]

    def one(job):
        url, entry, i, cam = job
        raw = os.path.join(out_dir, f"{i}_{cam}.mkv")
        remote_zip.fetch(url, entry, raw)
        encode(raw, os.path.join(out_dir, f"{i}_{cam}.mp4"))
        os.remove(raw)
        return i

    with ThreadPoolExecutor(a.workers) as ex:
        for k, _ in enumerate(ex.map(one, jobs), 1):
            if k % 20 == 0 or k == len(jobs):
                print(f"{k}/{len(jobs)} fetched", flush=True)
    if a.all_test:
        return
    with open(os.path.join(a.root, "selection.csv"), "w", encoding="utf-8") as f:
        f.write("task;id\n")
        for task in TASKS:
            for i in select(a.root, task, a.per_task):
                f.write(f"{task};{i}\n")


if __name__ == "__main__":
    main()
