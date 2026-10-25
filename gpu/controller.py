#!/usr/bin/env python3
"""
Runs on a rented GPU pod (gpu/pod.py starts it): swaps the vLLM model, runs jobs, moves files and samples the
GPU's energy counter. Standard library only, so it runs in the stock vLLM image.

Every request must carry the header `X-Token: <CTL_TOKEN>` (a random token pod.py generates per pod and keeps
in memory). The pod is reached only through RunPod's HTTPS proxy and is terminated when its work ends.

    GET  /energy            {"t", "mj", "w"}: NVML total energy since driver load (mJ) and power (W), now
    GET  /samples?since=T   the 1-second samples taken after T
    POST /serve             JSON list of `vllm serve` arguments; stops the running server first ([] stops it)
    GET  /status            whether vLLM is up, and the tail of its log
    POST /exec              JSON {"cmd": "...", "cwd": "..."}: runs a shell command in the background -> {"id"}
    GET  /job?id=N          {"done", "rc", "tail"}
    POST /upload?path=P     writes the body to P
    GET  /download?path=P   the file at P
"""
import ctypes
import json
import os
import signal
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOKEN = os.environ["CTL_TOKEN"]
LOG = "/workspace/vllm.log"
SAMPLES, JOBS, STATE = [], {}, {"vllm": None}


class NVML:
    """nvmlDeviceGetTotalEnergyConsumption (Volta and later) and nvmlDeviceGetPowerUsage, GPU 0, via ctypes."""

    def __init__(self):
        self.lib = ctypes.CDLL("libnvidia-ml.so.1")
        assert self.lib.nvmlInit_v2() == 0
        self.h = ctypes.c_void_p()
        assert self.lib.nvmlDeviceGetHandleByIndex_v2(0, ctypes.byref(self.h)) == 0

    def read(self):
        mj, mw = ctypes.c_ulonglong(), ctypes.c_uint()
        self.lib.nvmlDeviceGetTotalEnergyConsumption(self.h, ctypes.byref(mj))
        self.lib.nvmlDeviceGetPowerUsage(self.h, ctypes.byref(mw))
        return {"t": time.time(), "mj": mj.value, "w": mw.value / 1000}


GPU = NVML()


def sampler():
    while True:
        SAMPLES.append(GPU.read())
        del SAMPLES[:-200000]
        time.sleep(1)


def stop_vllm():
    p = STATE["vllm"]
    if p and p.poll() is None:
        os.killpg(p.pid, signal.SIGTERM)
        try:
            p.wait(60)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
    STATE["vllm"] = None


def tail(path, n=4000):
    try:
        with open(path, "rb") as fh:
            fh.seek(max(0, os.path.getsize(path) - n))
            return fh.read().decode(errors="replace")
    except OSError:
        return ""


def vllm_up():
    try:
        urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=3)
        return True
    except Exception:
        return False


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def reply(self, obj, raw=None):
        body = raw if raw is not None else json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def ok(self):
        if self.headers.get("X-Token") != TOKEN:
            self.send_response(403)
            self.end_headers()
            return False
        return True

    def do_GET(self):
        if not self.ok():
            return
        u = urllib.parse.urlparse(self.path)
        q = dict(urllib.parse.parse_qsl(u.query))
        if u.path == "/energy":
            return self.reply(GPU.read())
        if u.path == "/samples":
            since = float(q.get("since", 0))
            return self.reply([s for s in SAMPLES if s["t"] > since])
        if u.path == "/status":
            p = STATE["vllm"]
            return self.reply({"running": bool(p and p.poll() is None), "up": vllm_up(), "log": tail(LOG)})
        if u.path == "/job":
            j = JOBS[int(q["id"])]
            return self.reply({"done": j["p"].poll() is not None, "rc": j["p"].poll(), "tail": tail(j["log"], 6000)})
        if u.path == "/download":
            with open(q["path"], "rb") as fh:
                return self.reply(None, fh.read())
        self.reply({"error": "unknown"})

    def do_POST(self):
        if not self.ok():
            return
        u = urllib.parse.urlparse(self.path)
        q = dict(urllib.parse.parse_qsl(u.query))
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if u.path == "/serve":
            stop_vllm()
            args = json.loads(body)
            if args:
                log = open(LOG, "ab")
                STATE["vllm"] = subprocess.Popen(["vllm", "serve", *args], stdout=log, stderr=subprocess.STDOUT,
                                                 start_new_session=True)
            return self.reply({"started": bool(args)})
        if u.path == "/exec":
            spec = json.loads(body)
            jid = len(JOBS)
            log = f"/workspace/job{jid}.log"
            p = subprocess.Popen(["bash", "-c", spec["cmd"]], cwd=spec.get("cwd", "/workspace"), stdout=open(log, "wb"),
                                 stderr=subprocess.STDOUT, start_new_session=True)
            JOBS[jid] = {"p": p, "log": log}
            return self.reply({"id": jid})
        if u.path == "/upload":
            os.makedirs(os.path.dirname(q["path"]) or ".", exist_ok=True)
            with open(q["path"], "wb") as fh:
                fh.write(body)
            return self.reply({"bytes": len(body)})
        self.reply({"error": "unknown"})


if __name__ == "__main__":
    os.makedirs("/workspace", exist_ok=True)
    threading.Thread(target=sampler, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", 8001), H).serve_forever()
