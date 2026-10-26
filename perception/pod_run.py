#!/usr/bin/env python3
"""Runs ON our own rented GPU pod: grade the videos in a job file against the vLLM server on localhost.

Part of perception/study.py (CHANGE 1). The pod holds a batch of unmodified CCv2 videos, uploaded from the study
machine; vLLM reads each file from local disk (`file://`, `--allowed-local-media-path`) and decodes and samples it
as the model's own processor does. No request leaves the pod. The job file carries only video names and the
question each was asked; the pod never holds a skin-tone, lighting or any other personal label.

Each reply is screened in memory by study.screen() and only the kept fields are written (study.py, SCREEN); the
reply text is never written to disk.

    python3 perception/pod_run.py --jobs JOBS.json --videos DIR --model ID --label LABEL --out RECORDS.jsonl
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import study  # noqa: E402

URL = "http://127.0.0.1:8000/v1/chat/completions"


def messages(question, path):
    import prompting
    p = prompting.load_prompt(study.PROMPT)
    case = {"question": question, "reference": "", "rubric": "", "materials": "", "scale": list(study.SCALE)}
    msgs = p.build(case, "(The student's recorded answer is attached.)", "")
    # the unmodified file, read by the server from local disk
    msgs[-1]["content"] = [{"type": "text", "text": msgs[-1]["content"]},
                           {"type": "video_url", "video_url": {"url": "file://" + os.path.abspath(path)}}]
    return msgs


def call(model, msgs, token):
    body = json.dumps({"model": model, "messages": msgs, "max_tokens": study.MAX_TOKENS}).encode()
    req = urllib.request.Request(URL, data=body, method="POST",
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=900) as r:
            rep = json.loads(r.read())
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}", None, time.time() - t0
    except Exception as e:  # noqa: BLE001
        return None, type(e).__name__, None, time.time() - t0
    ch = (rep.get("choices") or [{}])[0]
    return (ch.get("message") or {}).get("content"), None, rep.get("usage") or {}, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--videos", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    token = os.environ.get("CTL_TOKEN", "")
    jobs = json.load(open(a.jobs))
    done = set()
    if os.path.exists(a.out):
        done = {json.loads(l)["id"] for l in open(a.out) if not json.loads(l).get("error")}
    todo = [j for j in jobs if j["id"] not in done and os.path.exists(os.path.join(a.videos, j["file"]))]

    def one(j):
        text, err, usage, secs = call(a.model, messages(j["question"], os.path.join(a.videos, j["file"])), token)
        rec = dict(study.screen(text) if text is not None else study.screen(""), id=j["id"], kind=j["kind"],
                   label=a.label, error=err, seconds=round(secs, 2),
                   prompt_tokens=(usage or {}).get("prompt_tokens"), completion_tokens=(usage or {}).get("completion_tokens"))
        if err:
            rec["refusal"] = False  # a failed call is not a refusal; it is counted as unsent
        return rec

    n = 0
    with ThreadPoolExecutor(a.workers) as ex, open(a.out, "a") as fh:
        for rec in ex.map(one, todo):
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            n += 1
            if n % 20 == 0 or n == len(todo):
                print(f"{n}/{len(todo)}", flush=True)


if __name__ == "__main__":
    main()
