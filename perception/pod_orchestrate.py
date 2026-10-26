#!/usr/bin/env python3
"""Drive the self-hosted run of perception/study.py (CHANGE 1) from the study machine.

For each batch of the sample: every video is read out of Meta's zip by range request (fetch_ccv2.py), uploaded
unmodified to our own RunPod pod, and deleted here at once; then each model is served on the pod in turn (vLLM,
bf16) and grades the batch with perception/pod_run.py against localhost; the screened records are downloaded and
joined here to the cells (the pod never sees a cell); finally the batch's videos are deleted from the pod. Every
fetch, upload and deletion is in DIR/manifest.jsonl. The pod is terminated by `gpu/pod.py terminate` (state file in
GPU_POD_STATE), after `wipe` deletes everything on it.

READS a licensed corpus (CCv2). The download links are read from `--links` at run time and never printed.

    GPU_POD_STATE=... python3 -I perception/pod_orchestrate.py --dir DIR --links LINKS.txt --ann CCv2.json \
        [--batch-size 640] [--models a,b,c] all
    GPU_POD_STATE=... python3 -I perception/pod_orchestrate.py --dir DIR wipe
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "gpu"))
import fetch_ccv2  # noqa: E402
import pod  # noqa: E402
import study  # noqa: E402

PODV = "/workspace/v"
VLLM = "v0.32.0"
SERVE = {  # served as the board's model id; the model's own video processor; bf16
    "google/gemma-4-31b-it": ["--max-model-len", "32768"],
    "google/gemma-4-26b-a4b-it": ["--max-model-len", "32768"],
    "qwen/qwen3.8-27b": ["--max-model-len", "65536", "--media-io-kwargs", '{"video": {"num_frames": -1}}'],
}


def log(d, **rec):
    fetch_ccv2.log(d, **rec)


def serve(m):
    repo, rev = study.SELF_HOSTED[m]
    tok = pod.load()["token"]
    args = [repo, "--revision", rev, "--dtype", "bfloat16", "--served-model-name", m, "--api-key", tok,
            "--allowed-local-media-path", PODV, "--limit-mm-per-prompt", '{"video": 1, "image": 0}',
            "--gpu-memory-utilization", "0.92", "--port", "8000"] + SERVE[m]
    pod.ctl("POST", "/serve", args)
    t0 = time.time()
    while time.time() - t0 < 2400:
        st = pod.ctl("GET", "/status")
        if st["up"]:
            print(f"{m} up after {time.time() - t0:.0f} s", flush=True)
            return
        if not st["running"]:
            print(st["log"][-3000:])
            raise SystemExit(f"vLLM exited for {m}")
        time.sleep(15)
    raise SystemExit(f"{m} not up in time")


def run_job(cmd, timeout=6 * 3600):
    j = pod.ctl("POST", "/exec", {"cmd": cmd, "cwd": "/workspace/repo"})
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = pod.ctl("GET", f"/job?id={j['id']}")
        if r["done"]:
            if r["rc"] != 0:
                print(r["tail"][-3000:])
                raise SystemExit(f"pod job failed: {cmd[:80]}")
            return r["tail"]
        time.sleep(15)
    raise SystemExit("pod job timed out")


def upload_batch(a, names, links, cd):
    """Fetch here, upload to the pod, delete here; one video at a time per worker."""
    have = set(run_job(f"ls {PODV}").split())
    todo = [n for n in names if n not in have]
    tmpd = os.path.join(a.dir, "videos")
    os.makedirs(tmpd, exist_ok=True)

    def one(n):
        part, member, off, csize, method = cd["videos"][n]
        p = os.path.join(tmpd, n)
        log(a.dir, file=f"videos/{n}", event="fetching")
        try:
            size = fetch_ccv2.remote_zip.fetch(links[part], (off, csize, method), p)
            log(a.dir, file=f"videos/{n}", event="fetched", bytes=size)
            for attempt in range(4):
                try:
                    pod.ctl("POST", "/upload?path=" + f"{PODV}/{n}", open(p, "rb").read(), timeout=900)
                    break
                except Exception:  # noqa: BLE001
                    if attempt == 3:
                        raise
                    time.sleep(10)
            log(a.dir, file=f"pod:{PODV}/{n}", event="uploaded", bytes=size)
        finally:
            if os.path.exists(p):
                os.remove(p)
                log(a.dir, file=f"videos/{n}", event="deleted")
        return n

    from concurrent.futures import ThreadPoolExecutor
    k = failed = 0
    with ThreadPoolExecutor(a.workers) as ex:
        futs = [ex.submit(one, n) for n in todo]
        for f in futs:
            try:
                f.result()
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"upload failed: {type(e).__name__}", flush=True)
            k += 1
            if k % 20 == 0 or k == len(todo):
                print(f"uploaded {k}/{len(todo)} ({failed} failed)", flush=True)


def grade(a, m, jobs, tag):
    jp = os.path.join(a.dir, f"jobs-{tag}.json")
    json.dump(jobs, open(jp, "w"))
    pod.ctl("POST", f"/upload?path=/workspace/jobs-{tag}.json", open(jp, "rb").read())
    out = f"/workspace/rec/{study.slug(m)}-{tag}.jsonl"
    label = f"{m}@bf16, self-hosted (vLLM {VLLM}, A100 80GB)"
    run_job(f"CTL_TOKEN=$CTL_TOKEN python3 perception/pod_run.py --jobs /workspace/jobs-{tag}.json --videos {PODV} "
            f"--model {m} --label '{label}' --out {out} --workers {a.pod_workers} 2>&1 | tail -3")
    data = pod.ctl("GET", "/download?path=" + out, raw=True, timeout=600)
    return [json.loads(l) for l in data.decode().splitlines() if l.strip()]


def store(a, m, recs, cells):
    rdir = os.path.join(a.dir, "runs")
    os.makedirs(rdir, exist_ok=True)
    with open(os.path.join(rdir, study.slug(m) + ".jsonl"), "a", encoding="utf-8") as fh:
        for r in recs:
            r = dict(r, **cells.get(r["id"], {}))
            fh.write(json.dumps(r) + "\n")


def recorded(a, m):
    p = os.path.join(a.dir, "runs", study.slug(m) + ".jsonl")
    if not os.path.exists(p):
        return set()
    return {json.loads(l)["id"] for l in open(p) if not json.loads(l).get("error")}


def cmd_all(a):
    links = fetch_ccv2.read_links(a.links)
    cd = json.load(open(os.path.join(a.dir, "cdmap.json")))
    ann = {r["video_name"]: r for r in study.load_ann(a.ann)}
    sample = study.read_sample(a.dir)
    cells = {v["video_name"]: {"subject_id": v["subject_id"], "group": v["group"], "stratum": v["stratum"]}
             for v in sample}
    models = a.models.split(",") if a.models else list(study.SELF_HOSTED)
    t0 = pod.balance()["clientBalance"]
    first = json.load(open(pod.STATE)).get("balance_at_create", t0)
    nb = (len(sample) + a.batch_size - 1) // a.batch_size
    current = None
    for b in range(nb if not a.max_batches else min(nb, a.max_batches)):
        batch = sample[b * a.batch_size:(b + 1) * a.batch_size]
        names = [v["video_name"] for v in batch]
        order = models if b % 2 == 0 else models[::-1]  # keep the served model across the batch boundary
        if all(set(names) <= recorded(a, m) for m in order):
            continue
        upload_batch(a, names, links, cd)
        jobs = [{"id": n, "file": n, "kind": "ccv2", "question": study.question_for(ann[n])} for n in names]
        for m in order:
            spent = first - pod.balance()["clientBalance"]
            if spent >= a.cap:
                raise SystemExit(f"GPU cap reached: ${spent:.2f} of ${a.cap:.0f}")
            if m != current:
                serve(m)
                current = m
            if not any(r.startswith("control:") for r in recorded(a, m)):
                ctrl = [{"id": f"control:black:{k}", "file": "control-black.mp4", "kind": "control",
                         "question": "Tell us how you usually spend your weekends."} for k in range(10)]
                store(a, m, grade(a, m, ctrl, "control"), {})
            todo = [j for j in jobs if j["id"] not in recorded(a, m)]
            if todo:
                recs = grade(a, m, todo, f"b{b}")
                store(a, m, recs, cells)
                ok = sum(not r.get("error") for r in recs)
                print(f"batch {b + 1}/{nb} {m}: {ok}/{len(todo)} graded; GPU spend so far "
                      f"${first - pod.balance()['clientBalance']:.2f}", flush=True)
        run_job(f"rm -f {' '.join(PODV + '/' + n for n in names)}; rm -f /workspace/jobs-b{b}.json")
        for n in names:
            log(a.dir, file=f"pod:{PODV}/{n}", event="deleted")
        print(f"batch {b + 1}/{nb} deleted from the pod", flush=True)


def cmd_wipe(a):
    """Delete every video, job and record on the pod (before terminating it)."""
    run_job("rm -rf /workspace/v /workspace/rec /workspace/jobs-*.json /workspace/repo /workspace/code.tgz; "
            "ls /workspace")
    log(a.dir, file="pod:/workspace (videos, jobs, records, code)", event="deleted")
    print("pod wiped", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["all", "wipe", "serve"])
    ap.add_argument("--dir", required=True)
    ap.add_argument("--links")
    ap.add_argument("--ann")
    ap.add_argument("--models", default="")
    ap.add_argument("--batch-size", type=int, default=640)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--pod-workers", type=int, default=8)
    ap.add_argument("--cap", type=float, default=80.0)
    ap.add_argument("--max-batches", type=int, default=0, help="stop after this many batches (a test)")
    a = ap.parse_args()
    if a.cmd == "serve":
        return serve(a.models)
    {"all": cmd_all, "wipe": cmd_wipe}[a.cmd](a)


if __name__ == "__main__":
    main()
