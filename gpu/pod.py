#!/usr/bin/env python3
"""
Rent one RunPod GPU pod, drive it through gpu/controller.py, and terminate it. Standard library only.

    python3 gpu/pod.py create --gpu "NVIDIA A100 80GB PCIe" --name grading-bench
    python3 gpu/pod.py serve -- --model google/gemma-4-31B-it --revision <sha> ...   # restart vLLM
    python3 gpu/pod.py wait-up
    python3 gpu/pod.py exec "python3 bench.py run ..." --cwd /workspace/repo [--wait]
    python3 gpu/pod.py upload LOCAL REMOTE | download REMOTE LOCAL
    python3 gpu/pod.py terminate          # always, as soon as the work ends
    python3 gpu/pod.py spend              # account balance now, against the balance recorded at create

The RunPod key comes from RUNPOD_API_KEY in the environment and is never printed. The pod's controller token
is generated here and kept, with the pod id, in a state file outside the repository (GPU_POD_STATE, default
~/.gpu-pod.json, mode 600). Nothing is retained on the pod after termination; requests to the model never
leave it (bench.py runs on the pod against localhost).
"""
import argparse
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.request

STATE = os.environ.get("GPU_POD_STATE", os.path.expanduser("~/.gpu-pod.json"))
IMAGE = "vllm/vllm-openai:v0.32.0"
REST = "https://rest.runpod.io/v1"
UA = "grading-benchmark-gpu/1.0"


def key():
    k = os.environ.get("RUNPOD_API_KEY")
    if not k:
        sys.exit("RUNPOD_API_KEY is not set")
    return k


def api(method, path, body=None):
    req = urllib.request.Request(REST + path, method=method, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + key(), "Content-Type": "application/json", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            t = r.read().decode()
            return json.loads(t) if t.strip() else {}
    except urllib.error.HTTPError as e:
        sys.exit(f"RunPod {method} {path}: HTTP {e.code} {e.read().decode(errors='replace')[:500]}")


def balance():
    req = urllib.request.Request("https://api.runpod.io/graphql", method="POST",
                                 data=json.dumps({"query": "query { myself { clientBalance currentSpendPerHr } }"}).encode(),
                                 headers={"Authorization": "Bearer " + key(), "Content-Type": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["data"]["myself"]


def load():
    return json.load(open(STATE)) if os.path.exists(STATE) else {}


def save(s):
    with open(os.open(STATE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w") as fh:
        json.dump(s, fh, indent=1)


def ctl(method, path, body=None, raw=False, timeout=120):
    s = load()
    url = f"https://{s['pod']}-8001.proxy.runpod.net{path}"
    data = body if isinstance(body, (bytes, type(None))) else json.dumps(body).encode()
    req = urllib.request.Request(url, method=method, data=data, headers={"X-Token": s["token"], "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        b = r.read()
    return b if raw else json.loads(b)


def cmd_create(a):
    s = load()
    if s.get("pod"):
        sys.exit(f"a pod is already recorded ({s['pod']}); terminate it first")
    token = secrets.token_urlsafe(24)
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "controller.py")).read()
    import base64
    start = "echo \"$CTL_SRC\" | base64 -d > /ctl.py && exec python3 /ctl.py"
    body = {"name": a.name, "imageName": IMAGE, "gpuTypeIds": [a.gpu], "gpuCount": 1, "cloudType": a.cloud,
            "containerDiskInGb": a.disk, "volumeInGb": 0, "ports": ["8000/http", "8001/http"],
            "dockerEntrypoint": ["bash", "-c"], "dockerStartCmd": [start],
            "env": {"CTL_TOKEN": token, "CTL_SRC": base64.b64encode(src.encode()).decode(), "HF_HUB_ENABLE_HF_TRANSFER": "0"}}
    b0 = balance()["clientBalance"]
    pod = api("POST", "/pods", body)
    save({"pod": pod["id"], "token": token, "created": time.time(), "balance_at_create": b0, "gpu": a.gpu,
          "cost_per_hr": pod.get("costPerHr"), "cloud": a.cloud})
    print(f"pod {pod['id']} {a.gpu} {a.cloud} ${pod.get('costPerHr')}/h; balance before ${b0:.2f}")


def cmd_wait_ctl(a):
    t0 = time.time()
    while time.time() - t0 < a.timeout:
        try:
            print(json.dumps(ctl("GET", "/energy")))
            return
        except Exception:
            time.sleep(10)
    sys.exit("controller not reachable")


def cmd_serve(a):
    print(ctl("POST", "/serve", a.args))


def cmd_wait_up(a):
    t0 = time.time()
    while time.time() - t0 < a.timeout:
        st = ctl("GET", "/status")
        if st["up"]:
            print("vLLM up after", round(time.time() - t0), "s")
            return
        if not st["running"]:
            print(st["log"][-3000:])
            sys.exit("vLLM exited")
        time.sleep(15)
    print(ctl("GET", "/status")["log"][-3000:])
    sys.exit("vLLM not up in time")


def cmd_status(a):
    st = ctl("GET", "/status")
    print("running", st["running"], "up", st["up"])
    print(st["log"][-a.chars:])


def cmd_exec(a):
    j = ctl("POST", "/exec", {"cmd": a.command, "cwd": a.cwd})
    print("job", j["id"])
    if a.wait:
        wait_job(j["id"], a.timeout)


def wait_job(jid, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        j = ctl("GET", f"/job?id={jid}")
        if j["done"]:
            print(j["tail"][-4000:])
            print("rc", j["rc"])
            return j["rc"]
        time.sleep(10)
    print(ctl("GET", f"/job?id={jid}")["tail"][-2000:])
    print("still running after", timeout, "s")


def cmd_job(a):
    if a.wait:
        wait_job(a.id, a.timeout)
    else:
        j = ctl("GET", f"/job?id={a.id}")
        print(j["tail"][-a.chars:])
        print("done", j["done"], "rc", j["rc"])


def cmd_upload(a):
    print(ctl("POST", "/upload?path=" + urllib.request.quote(a.remote), open(a.local, "rb").read(), timeout=600))


def cmd_download(a):
    data = ctl("GET", "/download?path=" + urllib.request.quote(a.remote), raw=True, timeout=600)
    os.makedirs(os.path.dirname(os.path.abspath(a.local)), exist_ok=True)
    open(a.local, "wb").write(data)
    print(len(data), "bytes ->", a.local)


def cmd_terminate(a):
    s = load()
    if not s.get("pod"):
        print("no pod recorded")
    else:
        api("DELETE", f"/pods/{s['pod']}")
        hours = (time.time() - s["created"]) / 3600
        print(f"terminated {s['pod']} after {hours:.2f} h (about ${hours * (s.get('cost_per_hr') or 0):.2f} at the listed rate)")
        log = load_log()
        log.append({"pod": s["pod"], "gpu": s["gpu"], "hours": hours, "cost_per_hr": s.get("cost_per_hr"),
                    "balance_at_create": s["balance_at_create"]})
        json.dump(log, open(STATE + ".log", "w"), indent=1)
        save({"first_balance": s.get("first_balance", s["balance_at_create"])})
    pods = api("GET", "/pods")
    print("pods still on the account:", [p["id"] for p in pods] if isinstance(pods, list) else pods)


def load_log():
    return json.load(open(STATE + ".log")) if os.path.exists(STATE + ".log") else []


def cmd_spend(a):
    log = load_log()
    first = log[0]["balance_at_create"] if log else load().get("balance_at_create")
    now = balance()
    print(f"balance ${now['clientBalance']:.2f}, spending ${now['currentSpendPerHr']}/h now; "
          + (f"spent since the first pod ${first - now['clientBalance']:.2f}" if first else ""))
    for p in log:
        print(f"  {p['pod']} {p['gpu']} {p['hours']:.2f} h at ${p['cost_per_hr']}/h")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("create"); p.add_argument("--gpu", required=True); p.add_argument("--name", default="grading-bench")
    p.add_argument("--cloud", default="COMMUNITY", choices=["COMMUNITY", "SECURE"]); p.add_argument("--disk", type=int, default=200)
    p = sub.add_parser("wait-ctl"); p.add_argument("--timeout", type=int, default=1200)
    p = sub.add_parser("serve"); p.add_argument("args", nargs=argparse.REMAINDER)
    p = sub.add_parser("wait-up"); p.add_argument("--timeout", type=int, default=1800)
    p = sub.add_parser("status"); p.add_argument("--chars", type=int, default=3000)
    p = sub.add_parser("exec"); p.add_argument("command"); p.add_argument("--cwd", default="/workspace")
    p.add_argument("--wait", action="store_true"); p.add_argument("--timeout", type=int, default=3600)
    p = sub.add_parser("job"); p.add_argument("id", type=int); p.add_argument("--wait", action="store_true")
    p.add_argument("--timeout", type=int, default=3600); p.add_argument("--chars", type=int, default=3000)
    p = sub.add_parser("upload"); p.add_argument("local"); p.add_argument("remote")
    p = sub.add_parser("download"); p.add_argument("remote"); p.add_argument("local")
    sub.add_parser("terminate"); sub.add_parser("spend")
    a = ap.parse_args()
    if a.cmd == "serve" and a.args[:1] == ["--"]:
        a.args = a.args[1:]
    {"create": cmd_create, "wait-ctl": cmd_wait_ctl, "serve": cmd_serve, "wait-up": cmd_wait_up, "status": cmd_status,
     "exec": cmd_exec, "job": cmd_job, "upload": cmd_upload, "download": cmd_download, "terminate": cmd_terminate,
     "spend": cmd_spend}[a.cmd](a)


if __name__ == "__main__":
    main()
