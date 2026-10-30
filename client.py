"""
One model caller: any OpenAI-compatible chat-completions endpoint (OpenAI, OpenRouter, vLLM,
Ollama, LM Studio, most hosted open-weights providers). Standard library only.

Rules carried over from `shared/llm.py`, each learned on a real run:

- **The key comes from an environment variable or a `.env` file, never a command argument**, and
  only its source is reported, never its value. An exported key wins over `.env` here (the reverse of
  `shared/llm.py`, which has a reason specific to this repository's sandbox).
- **No silent fallback.** A failed call is recorded as failed. The model that actually answered
  (`model` in the reply, and `provider` where the router reports one) is recorded on every call, so a
  run whose arms were served by different backends says so in its own output.
- **Responses are cached on disk**, keyed by endpoint, request body and probe/repeat tag, so a run that
  dies at call 600 of 1,800 does not pay for the first 600 again, and the retest probe is never served
  from the base call's cache entry.
- **Transport errors are retried; replies are not.** 408/409/429/5xx and connection errors back off
  and retry. A completed reply with no readable mark is a failed grading, counted, not re-asked.

- **Zero data retention is checked, not assumed** (added 2026-10-25). On OpenRouter, a request must carry
  `provider.zdr: true`, and before the first call the client reads OpenRouter's live list of zero-retention
  endpoints (`/api/v1/endpoints/zdr`). It refuses a model with none there, and pins every request to the
  listed endpoints (`provider.only`). A reply served by a provider outside the list is recorded as a failed
  grading. Why: on 2026-10-25 the benchmark found 5,500 Claude Fable 5.1 and 11,300 Claude Haiku 5.5
  gradings served through the maintainers' own Anthropic key (bring-your-own-key), which carries 30-day
  safety retention and is not on that list. Anthropic's documentation says Fable 5.1 requires 30-day
  retention unless Anthropic authorises otherwise. The maintainer accepted that for public corpora; the
  check stops it from happening unnoticed. The pin is added when the request is sent, not to the cached body,
  so cached replies are still found.
- **A reply served on a stored provider key stops the run** (added 2026-10-30). OpenRouter sends a request
  through a provider key the account holder has stored with it, in preference to its own, even when the request
  requires zero retention and the provider is on the zero-retention list; the stored key's own terms then apply.
  The endpoint check above did not catch this: on 2026-10-28 a private study's 2,816 Claude Haiku 5.5 gradings
  went to Anthropic's listed endpoint through the maintainers' stored key, under its 30-day retention. The reply
  says so (`usage.is_byok`), but only after the request has been sent, so the client cannot prevent the first
  one: it discards that reply, refuses every later call in the run, and says why. A run under a stated
  `--retention-exception` is exempt. The real fix is on the account: store no provider key with the router.

Usage is read from the reply: prompt, completion and (where reported) reasoning tokens, and the
cost where the endpoint reports one (OpenRouter's `usage.cost`). Nothing is estimated here.
"""

import hashlib
import http.client
import json
import os
import random
import time
import urllib.error
import urllib.request

RETRY_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


def load_key(env_name):
    if os.environ.get(env_name):
        return os.environ[env_name], "environment"
    if os.path.exists(".env"):
        with open(".env", encoding="utf-8") as fh:
            for line in fh:
                k, _, v = line.strip().partition("=")
                if k.strip() == env_name and v.strip():
                    return v.strip().strip('"').strip("'"), ".env"
    return None, None


class OpenAICompatible:
    def __init__(self, base_url, model, key_env, cache_dir, temperature=None, max_tokens=None,
                 extra=None, timeout=180, retries=6, retention_exception=None):
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.model, self.temperature, self.max_tokens = model, temperature, max_tokens
        self.extra = extra or {}
        self.timeout, self.retries, self.cache_dir = timeout, retries, cache_dir
        self.key, self.key_source = load_key(key_env) if key_env else (None, None)
        self.zdr = None  # (provider names, endpoint tags) from OpenRouter's live list, read before the first call
        # A model with no zero-retention endpoint runs only under a stated exception, recorded in the run's config
        # (e.g. Claude Fable 5.1 through the maintainers' own key, 30-day safety retention, public corpora only).
        self.retention_exception = retention_exception
        self.stored_key_seen = False  # set by the first reply served on a stored provider key; every later call refused
        os.makedirs(cache_dir, exist_ok=True)

    def zdr_endpoints(self):
        """OpenRouter only: the model's zero-retention endpoints, or refuse. Other endpoints are not checked."""
        if "openrouter.ai" not in self.url:
            return None
        if self.zdr is False:
            return None
        if self.zdr is None:
            if not (self.extra.get("provider") or {}).get("zdr"):
                raise RuntimeError("refused: every request must require zero data retention; "
                                   'add "provider": {"zdr": true} to the request (--extra-body)')
            with urllib.request.urlopen("https://openrouter.ai/api/v1/endpoints/zdr", timeout=60) as resp:
                eps = [e for e in json.loads(resp.read().decode())["data"] if e.get("model_id") == self.model]
            if not eps:
                if self.retention_exception:
                    self.zdr = False
                    return None
                raise RuntimeError(f"refused: OpenRouter lists no zero-retention endpoint for {self.model}; "
                                   "a run without one needs --retention-exception stating the route and its retention")
            self.zdr = ({e["provider_name"] for e in eps}, sorted({e["tag"] for e in eps if e.get("tag")}))
        return self.zdr

    def body(self, messages):
        b = {"model": self.model, "messages": messages}
        if self.temperature is not None:
            b["temperature"] = self.temperature
        if self.max_tokens is not None:
            b["max_tokens"] = self.max_tokens
        b.update(self.extra)
        return b

    def call(self, messages, tag, extra=None, cached_only=False):
        body = self.body(messages)
        if extra:
            body.update(extra)
        key = hashlib.sha256(json.dumps([self.url, body, tag], sort_keys=True).encode()).hexdigest()
        path = os.path.join(self.cache_dir, key + ".json")
        if cached_only and not os.path.exists(path):
            return {"text": None, "usage": {}, "latency_s": None, "served_model": None, "provider": None,
                    "error": "not sent: --cached-only and not in the cache", "cached": False}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                rec = json.load(fh)
            rec["cached"] = True
            return rec
        rec = self._send(body)
        if rec["error"] is None:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(rec, fh)
        rec["cached"] = False
        return rec

    def _send(self, body):
        if self.stored_key_seen:
            raise RuntimeError(STORED_KEY_REFUSAL)
        z = self.zdr_endpoints()
        if z:
            body = dict(body, provider=dict(body.get("provider") or {}, zdr=True, only=z[1]))
        data = json.dumps(body).encode()
        headers = {"Content-Type": "application/json"}
        if self.key:
            headers["Authorization"] = "Bearer " + self.key
        err = None
        for attempt in range(self.retries + 1):
            t0 = time.time()
            try:
                req = urllib.request.Request(self.url, data=data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    reply = json.loads(resp.read().decode())
                rec = record(reply, time.time() - t0)
                if z and rec["error"] is None and rec.get("provider") not in z[0]:
                    rec = dict(rec, text=None, error=f"served by {rec.get('provider')!r}, which is not on OpenRouter's "
                                                    "zero-retention list for this model; reply discarded")
                if ("openrouter.ai" in self.url and rec["usage"].get("byok") and not self.retention_exception):
                    self.stored_key_seen = True
                    raise RuntimeError(STORED_KEY_REFUSAL)
                return rec
            except urllib.error.HTTPError as e:
                detail = e.read().decode(errors="replace")[:300]
                err = f"HTTP {e.code}: {detail}"
                # OpenRouter answers 402 when the credit reserved by requests already in flight
                # (max_tokens each) would exceed what the key may hold, not only when credit is gone.
                # That one settles as requests finish, so it is waited out like a rate limit.
                in_flight = e.code == 402 and "in_flight" in detail
                if e.code not in RETRY_STATUS and not in_flight:
                    break
            except (urllib.error.URLError, http.client.HTTPException, OSError, ValueError) as e:
                err = f"{type(e).__name__}: {e}"
            time.sleep(min(60, 2 ** attempt) + random.random())
        return {"text": None, "usage": {}, "latency_s": None, "served_model": None, "provider": None, "error": err}


STORED_KEY_REFUSAL = ("refused: OpenRouter served a reply through a provider key stored on this account (bring-your-own-"
                      "key), whose own retention terms apply instead of zero retention. The reply was discarded and the "
                      "run stopped. Remove the stored key from the OpenRouter account, or run under a stated "
                      "--retention-exception.")


def record(reply, latency):
    if "error" in reply and not reply.get("choices"):
        return {"text": None, "usage": {}, "latency_s": latency, "served_model": None, "provider": None,
                "error": json.dumps(reply["error"])[:300]}
    choice = (reply.get("choices") or [{}])[0]
    u = reply.get("usage") or {}
    details = u.get("completion_tokens_details") or {}
    cost = u.get("cost")
    if u.get("is_byok"):
        # Bring-your-own-key: OpenRouter's `cost` is only its fee; the provider bills the rest to the
        # user's own key and OpenRouter reports it separately. Count both, or the spend cap never trips.
        upstream = (u.get("cost_details") or {}).get("upstream_inference_cost")
        cost = None if upstream is None else (cost or 0.0) + upstream
    usage = {"prompt_tokens": u.get("prompt_tokens"), "completion_tokens": u.get("completion_tokens"),
             "reasoning_tokens": details.get("reasoning_tokens"), "cost_reported": cost,
             "byok": bool(u.get("is_byok"))}
    return {"text": (choice.get("message") or {}).get("content"), "usage": usage, "latency_s": latency,
            "served_model": reply.get("model"), "provider": reply.get("provider"),
            "finish_reason": choice.get("finish_reason"), "error": None}


class Fake:
    """A stand-in for the floor: a function of the rendered messages, with made-up usage."""

    def __init__(self, fn):
        self.fn, self.model, self.key_source = fn, "fake", None

    def body(self, messages):
        return {"model": "fake"}

    def call(self, messages, tag, extra=None):
        text = self.fn(messages, tag)
        n_in = sum(len(m["content"]) for m in messages) // 4
        return {"text": text, "usage": {"prompt_tokens": n_in, "completion_tokens": 20, "reasoning_tokens": None,
                                        "cost_reported": None},
                "latency_s": 0.0, "served_model": "fake", "provider": None, "error": None, "cached": False}
