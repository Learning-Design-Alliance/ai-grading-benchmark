#!/usr/bin/env python3
"""Drive essays-genft on one rented pod: setup, smoke, BASE battery, GENFT training, merge, GENFT battery, the folds.
Every long step runs as a job ON THE POD (gpu/controller.py), so this driver can be restarted (`--resume`) without
losing work: the stages done are kept in <work>/genft-progress.json, and a running job is re-attached by its id.

    GPU_POD_STATE=<own state file> GENFT_WORK=<dir holding genft-split.json> python3 essays-genft/driver.py [--resume]

The pod is terminated at the end, and on any failure of a stage. A failure to reach the pod's controller while
polling is retried, never treated as a failed job: the job itself is checked first. The cap (study.py BUDGET): from
the listed hourly rate, the deadline is the time the pod's cost reaches $57; no training is started whose projected
end passes it.
"""
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WORK = os.environ["GENFT_WORK"]
STATE = os.environ["GPU_POD_STATE"]
PROG = os.path.join(WORK, "genft-progress.json")
CAP, RESERVE = 60.0, 3.0
GPUS = (("NVIDIA A100-SXM4-80GB", "COMMUNITY"), ("NVIDIA A100 80GB PCIe", "COMMUNITY"),
        ("NVIDIA A100-SXM4-80GB", "SECURE"), ("NVIDIA A100 80GB PCIe", "SECURE"))
GEMMA = ("google/gemma-4-26B-A4B-it", "4d7ae4984b7db7de8f8457170b3f1a419ee76d52")
SERVE = ["--max-model-len", "16384", "--gpu-memory-utilization", "0.92"]
R = "/workspace/repo"
D = "/workspace/data"
RUNS = "/workspace/runs"
SPLIT = "/workspace/genft-split.json"
IDS = "/workspace/train-ids.jsonl"
COMMON = f"--corpus {D}/asap2.jsonl --split {SPLIT}"
LABEL = {"base": "Gemma 4 26B A4B, self-hosted bf16 (base, control)",
         "genft": "fine-tuned (generative): Gemma 4 26B A4B LoRA"}


def log(*a):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), *a, flush=True)


def pod(*args, check=True, quiet=False, tries=1):
    for t in range(tries):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "gpu", "pod.py"), *args], capture_output=True, text=True,
                           cwd=ROOT)
        out = (r.stdout + r.stderr).strip()
        if r.returncode == 0:
            break
        if t < tries - 1:
            time.sleep(30)
    if not quiet:
        log("pod", args[0], "|", out[-2000:])
    if check and r.returncode:
        raise RuntimeError(f"pod {args[0]} failed: {out[-500:]}")
    return out


def prog():
    return json.load(open(PROG)) if os.path.exists(PROG) else {"done": [], "jobs": {}, "notes": []}


def save(p):
    json.dump(p, open(PROG + ".tmp", "w"), indent=1)
    os.replace(PROG + ".tmp", PROG)


def job(p, name, cmd, until=None):
    """Run cmd on the pod as a job (re-attached on resume); return (rc, tail)."""
    jid = p["jobs"].get(name)
    if jid is None:
        out = pod("exec", cmd, tries=3)
        jid = int(re.search(r"job (\d+)", out).group(1))
        p["jobs"][name] = jid
        save(p)
    last, failing_since = 0, None
    while True:
        try:
            o = pod("job", str(jid), "--chars", "3000", check=True, quiet=True)
            failing_since = None
        except RuntimeError as e:  # the controller did not answer: retry, never read as a failed job
            failing_since = failing_since or time.time()
            log("poll failed, retrying:", str(e)[:200])
            if time.time() - failing_since > 7200:
                raise RuntimeError(f"the pod's controller has not answered for two hours (job {name})")
            time.sleep(60)
            continue
        m = re.search(r"done (True|False) rc (\S+)", o)
        if m and m.group(1) == "True":
            rc = int(m.group(2)) if m.group(2) not in ("None",) else None
            log(f"job {name} ({jid}) finished rc {rc} |", o[-2500:])
            return rc, o
        if time.time() - last > 900:
            log(f"job {name} ({jid}) running |", o[-600:])
            last = time.time()
        if until and time.time() > until + 3600:
            log(f"job {name} overran the deadline by an hour")
            return None, o
        time.sleep(60)


def serve(args):
    pod("serve", "--", *args, tries=3)
    pod("wait-up", "--timeout", "2700")


def deadline():
    st = json.load(open(STATE))
    return st["created"] + (CAP - RESERVE) / float(st["cost_per_hr"]) * 3600


def fetch(remote, local):
    try:
        pod("download", remote, local, check=False)
    except Exception as e:  # noqa: BLE001
        log("download failed", e)


def stage(p, name):
    return name in p["done"]


def mark(p, name):
    p["done"].append(name)
    save(p)


def pack_runs(p, tag):
    rc, _ = job(p, f"pack-{tag}", f"cd {RUNS} && tar czf /workspace/runs-{tag}.tgz --exclude=.cache */calls.jsonl */config.json "
                f"&& cd /workspace && tar czf /workspace/stats-{tag}.tgz stats-*.json checks-*.json adapters/*/adapter_config.json "
                f"2>/dev/null; ls -la /workspace/*.tgz")
    fetch(f"/workspace/runs-{tag}.tgz", os.path.join(WORK, f"runs-{tag}.tgz"))
    fetch(f"/workspace/stats-{tag}.tgz", os.path.join(WORK, f"stats-{tag}.tgz"))


def main():
    p = prog()
    resume = "--resume" in sys.argv
    if not resume and os.path.exists(STATE) and json.load(open(STATE)).get("pod"):
        sys.exit("a pod is already recorded in this state file; use --resume")
    ok = False
    try:
        if not stage(p, "create"):
            for gpu, cloud in GPUS:
                try:
                    pod("create", "--gpu", gpu, "--name", "grading-bench-essays-genft", "--cloud", cloud, "--disk", "250")
                    break
                except RuntimeError:
                    if os.path.exists(STATE) and json.load(open(STATE)).get("pod"):
                        raise
                    time.sleep(5)
            else:
                raise RuntimeError("no A100 80GB available")
            mark(p, "create")
        st = json.load(open(STATE))
        log(f"pod {st['pod']} {st['gpu']} ${st['cost_per_hr']}/h; deadline "
            f"{time.strftime('%Y-%m-%d %H:%M', time.localtime(deadline()))}")
        if not stage(p, "setup"):
            pod("wait-ctl", "--timeout", "1800")
            tgz = os.path.join(WORK, "repo.tgz")
            subprocess.run(["git", "archive", "--format=tar.gz", "-o", tgz, "HEAD"], cwd=ROOT, check=True)
            pod("upload", tgz, "/workspace/repo.tgz", tries=3)
            pod("upload", os.path.join(WORK, "genft-split.json"), SPLIT, tries=3)
            rc, o = job(p, "setup",
                        f"set -e; mkdir -p {R} {RUNS} /workspace/adapters && tar xzf /workspace/repo.tgz -C {R} && "
                        "pip install -q pyarrow 'peft==0.21.2' 2>&1 | tail -1; "
                        "python3 -c \"import torch, transformers, peft, vllm; print('versions', torch.__version__, "
                        "transformers.__version__, peft.__version__, vllm.__version__)\"; "
                        "nvidia-smi --query-gpu=name,memory.total --format=csv; free -g | head -2; df -h /workspace | tail -1; "
                        f"cd {R} && python3 fetch_data.py --dir {D} 2>&1 | tail -6; "
                        f"python3 -c \"from huggingface_hub import snapshot_download as s; print(s('{GEMMA[0]}', revision='{GEMMA[1]}'))\"; "
                        "du -sh /root/.cache/huggingface")
            if rc != 0:
                raise RuntimeError("setup failed")
            mark(p, "setup")
        if not stage(p, "smoke"):
            mark(p, "smoke")
        base_serve = ["--model", GEMMA[0], "--revision", GEMMA[1], "--tokenizer-revision", GEMMA[1], "--served-model-name", "google/gemma-4-26b-a4b-it",
                      *SERVE, "--api-key", st["token"]]
        if not stage(p, "ids"):
            serve(base_serve)
            rc, o = job(p, "tokenize", f"cd {R} && python3 essays-genft/train_gen.py tokenize-all {COMMON} "
                        f"--served google/gemma-4-26b-a4b-it --out {IDS}")
            if rc != 0:
                raise RuntimeError("tokenize-all failed")
            rc, o = job(p, "template", f"cd {R} && python3 essays-genft/train_gen.py template-check {COMMON} --ids {IDS} "
                        f"--served google/gemma-4-26b-a4b-it --out /workspace/checks-template.json")
            fetch("/workspace/checks-template.json", os.path.join(WORK, "checks-template.json"))
            if rc != 0:
                raise RuntimeError("TEMPLATE CHECK failed: nothing is trained")
            mark(p, "ids")
        if not stage(p, "smoke2"):
            pod("serve", "--", tries=3)
            rc, o = job(p, "smoke2", f"cd {R} && python3 essays-genft/train_gen.py train {COMMON} --ids {IDS} --fold same "
                        f"--limit 48 --adapter /workspace/adapters/smoke --stats /workspace/stats-smoke.json && "
                        f"python3 essays-genft/train_gen.py merge --adapter /workspace/adapters/smoke --dry")
            if rc != 0:
                raise RuntimeError("smoke failed")
            fetch("/workspace/stats-smoke.json", os.path.join(WORK, "stats-smoke.json"))
            mark(p, "smoke2")
        if not stage(p, "base"):
            serve(base_serve)
            rc, o = job(p, "battery-base", f"cd {R} && python3 essays-genft/evaluate.py battery --slug gemma4-base "
                        f"--served google/gemma-4-26b-a4b-it --label '{LABEL['base']}' --data {D} --runs {RUNS} {COMMON}")
            if rc != 0:
                raise RuntimeError("BASE battery failed")
            mark(p, "base")
            pack_runs(p, "base")
        if not stage(p, "train-same"):
            pod("serve", "--", tries=3)  # stop vLLM: the GPU is needed for training
            rc, o = job(p, "train-same", f"cd {R} && python3 essays-genft/train_gen.py train {COMMON} --fold same "
                        f"--ids {IDS} --adapter /workspace/adapters/same --stats /workspace/stats-same.json --deadline {deadline():.0f}",
                        until=deadline())
            fetch("/workspace/stats-same.json", os.path.join(WORK, "stats-same.json"))
            if rc != 0:
                raise RuntimeError(f"GENFT training failed or hit the cap (rc {rc})")
            mark(p, "train-same")
        if not stage(p, "genft"):
            served = serve_finetuned(p, "same", "genft/gemma-4-26b-a4b-it", st)
            if served:
                rc, o = job(p, "battery-genft", f"cd {R} && python3 essays-genft/evaluate.py battery --slug gemma4-genft "
                            f"--served {served} --label '{LABEL['genft']}' --data {D} --runs {RUNS} {COMMON} "
                            f"--route-note 'merged LoRA fine-tune of {GEMMA[0]}@{GEMMA[1][:8]} (essays-genft)'")
                if rc != 0:
                    raise RuntimeError("GENFT battery failed")
            else:
                p["notes"].append("GENFT battery NOT RUN: neither the merged model nor the adapter passed the merge check")
            mark(p, "genft")
            pack_runs(p, "genft")
        sp = json.load(open(os.path.join(WORK, "genft-split.json")))
        for k, prompt in enumerate(sp["folds"]):
            name = f"fold{k}"
            if stage(p, name):
                continue
            rate = (json.load(open(os.path.join(WORK, "stats-same.json"))).get("tokens_per_second")
                    if os.path.exists(os.path.join(WORK, "stats-same.json")) else None)
            spent_after = time.time() + (10.3e6 / rate if rate else 6200) + 1500
            if spent_after > deadline():
                p["notes"].append(f"{name} ({prompt}) NOT RUN: GPU cap (projected end after the deadline)")
                log(p["notes"][-1])
                mark(p, name)
                continue
            pod("serve", "--", tries=3)
            rc, o = job(p, f"train-{name}", f"cd {R} && python3 essays-genft/train_gen.py train {COMMON} --fold '{prompt}' "
                        f"--ids {IDS} --adapter /workspace/adapters/{name} --stats /workspace/stats-{name}.json --deadline {deadline():.0f}",
                        until=deadline())
            fetch(f"/workspace/stats-{name}.json", os.path.join(WORK, f"stats-{name}.json"))
            if rc != 0:
                p["notes"].append(f"{name} ({prompt}) NOT RUN: training rc {rc}")
                mark(p, name)
                continue
            served = serve_finetuned(p, name, f"genft/gemma-4-26b-a4b-it-{name}", st)
            if served:
                rc, o = job(p, f"eval-{name}", f"cd {R} && python3 essays-genft/evaluate.py fold --slug gemma4-genft-{name} "
                            f"--served {served} --label 'fine-tuned (generative), unseen prompt: Gemma 4 26B A4B LoRA' "
                            f"--prompt '{prompt}' --data {D} --runs {RUNS} {COMMON} "
                            f"--route-note 'merged LoRA fine-tune (fold for {prompt}), essays-genft'")
                if rc != 0:
                    p["notes"].append(f"{name} ({prompt}) grading failed rc {rc}")
            else:
                p["notes"].append(f"{name} ({prompt}) NOT RUN: merge check failed")
            mark(p, name)
            pack_runs(p, name)
        pack_runs(p, "final")
        ok = True
    except Exception as e:  # noqa: BLE001
        log("FAILED:", repr(e)[:800])
        p["notes"].append(f"failure: {repr(e)[:300]}")
        save(p)
    finally:
        try:
            if os.path.exists(STATE) and json.load(open(STATE)).get("pod"):
                pack_runs(p, "end")
        except Exception as e:  # noqa: BLE001
            log("final pack failed", e)
        st = json.load(open(STATE)) if os.path.exists(STATE) else {}
        if st.get("pod"):
            p["pod"] = {"id": st["pod"], "gpu": st.get("gpu"), "cloud": st.get("cloud"), "cost_per_hr": st.get("cost_per_hr"),
                        "hours": (time.time() - st["created"]) / 3600}
            p["pod"]["listed_cost_usd"] = p["pod"]["hours"] * float(st.get("cost_per_hr") or 0)
            save(p)
            json.dump(p["pod"] | {"notes": p["notes"], "done": p["done"]}, open(os.path.join(WORK, "pod-record.json"), "w"), indent=1)
        pod("terminate", check=False)
        pod("spend", check=False)
        log("DRIVER END", "ok" if ok else "with failure")


def serve_finetuned(p, name, served, st):
    """Merge, serve, check; fall back to the unmerged adapter (study.py MERGE). Returns the served name or None."""
    if not stage(p, f"merge-{name}"):
        pod("serve", "--", tries=3)
        rc, o = job(p, f"merge-{name}", f"cd {R} && rm -rf /workspace/merged && python3 essays-genft/train_gen.py merge "
                    f"--adapter /workspace/adapters/{name} --out /workspace/merged && cp /workspace/merged/genft-merge.json "
                    f"/workspace/checks-merge-{name}.json")
        if rc != 0:
            raise RuntimeError(f"merge {name} failed")
        mark(p, f"merge-{name}")
    serve(["--model", "/workspace/merged", "--served-model-name", served, *SERVE, "--api-key", st["token"]])
    rc, o = job(p, f"template-{name}", f"cd {R} && python3 essays-genft/train_gen.py template-check {COMMON} --ids {IDS} "
                f"--served {served} --out /workspace/checks-template-{name}.json")
    if rc != 0:
        raise RuntimeError(f"TEMPLATE CHECK failed on the merged model {name}")
    rc, o = job(p, f"mcheck-{name}", f"cd {R} && python3 essays-genft/train_gen.py merge-check --corpus {D}/asap2.jsonl "
                f"--stats /workspace/stats-{name}.json --served {served} --out /workspace/checks-mergecheck-{name}.json")
    if rc == 0:
        return served
    p["notes"].append(f"{name}: merge check failed against the merged model; trying the unmerged adapter")
    log(p["notes"][-1])
    try:
        serve(["--model", GEMMA[0], "--revision", GEMMA[1], "--tokenizer-revision", GEMMA[1], "--served-model-name", "base", "--enable-lora",
               "--max-lora-rank", "16", "--lora-modules", f"{served}=/workspace/adapters/{name}", *SERVE, "--api-key", st["token"]])
    except RuntimeError as e:
        p["notes"].append(f"{name}: vLLM could not serve the adapter: {str(e)[:200]}")
        return None
    rc, o = job(p, f"mcheck-lora-{name}", f"cd {R} && python3 essays-genft/train_gen.py merge-check --corpus {D}/asap2.jsonl "
                f"--stats /workspace/stats-{name}.json --served {served} --out /workspace/checks-mergecheck-lora-{name}.json")
    if rc == 0:
        p["notes"].append(f"{name}: served as the unmerged adapter (deviation, study.py MERGE)")
        return served
    return None


if __name__ == "__main__":
    main()
