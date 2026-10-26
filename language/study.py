#!/usr/bin/env python3
"""Does an audio grader recognise a correct spoken answer as well in a less common language?
PRE-REGISTERED 2026-10-26, before any call of this design.

WHY. A student may answer orally in their own language, and a grader that understands English, Spanish or Mandarin
well may fail on Amharic or Lao. The literature shows large per-language gaps in speech recognition (FLEURS, MMS),
but not for audio models used as graders (docs/LITERATURE-MEDIA-FAIRNESS.md). FLEURS reads the same sentences in
102 languages, so the content is held fixed and only the language varies (docs/DATA-ROADMAP.md, section 0).

DESIGN.
- Data: FLEURS dev split (CC BY 4.0; https://huggingface.co/datasets/google/fleurs). The audio is downloaded to a
  local directory and never committed.
- Languages: 18 in three tiers, assigned before any call. The tiers are the maintainers' judgement of how much
  text and speech in each language is on the web (a limit; no single published ranking covers all 18):
  - HIGH: en_us, es_419, fr_fr, de_de, cmn_hans_cn, ja_jp
  - MID: hi_in, sw_ke, vi_vn, tr_tr, id_id, pl_pl
  - LOW: yo_ng, am_et, ps_af, lo_la, ckb_iq, zu_za
- Items: 30 sentence ids present in every chosen language's dev split (seed 26), one recording each (the first
  listed).
  - MATCH: the recording of sentence i, with sentence i's English text as the model answer.
  - MISMATCH: the same recording, with the English text of another chosen sentence (a fixed derangement, seed 26).
  - 60 gradings per language and model.
- Prompt: prompts/spoken-meaning.txt. Mark 1 if the spoken answer says the same as the English model answer, else
  0; language, accent and pronunciation are to be ignored. Scale 0-1.
- Graders: the six audio models on the board's speech task (zero retention, default settings, max tokens 4096).

MEASURES, per model:
- Accuracy per language: the share of the 60 marked correctly.
- Tier accuracy: the mean over its six languages.
- The GAP: HIGH minus LOW accuracy, with a 95% bootstrap interval over the 30 sentence ids (cluster bootstrap:
  a sentence's 36 gradings, 18 languages by match and mismatch, move together; 2,000 draws, seed 7).
- Signed: positive means worse on low-resource languages. Also MID minus LOW, HIGH minus MID, and the share of
  replies that refuse or say they cannot understand, by tier.

VERDICT per model:
  WORSE ON LOW-RESOURCE LANGUAGES   GAP interval above 0
  NO GAP DETECTED                   interval contains 0 (its upper bound reported as what is not ruled out)
  BETTER ON LOW-RESOURCE LANGUAGES  interval below 0
  TASK NOT SUPPORTED                accuracy on en_us below 0.80: the model cannot do the task even in English,
                                    so its gap is not read

FLOOR (synthetic, before any call). Each grading is correct with a probability set by its tier, over 30 sentence
clusters by 18 languages by 2. Each sentence carries a random difficulty (sd 0.10 on the probability scale), so the
cluster bootstrap faces real clustering.
- Null: HIGH = LOW = 0.85. The verdict must read WORSE in at most 7% of 200 worlds.
- Planted: HIGH 0.90, LOW 0.80 (a 10-point gap). It must read WORSE in at least 80%.
If the floor fails, verdicts read UNMEASURED and the figures are descriptive.

LIMITS stated in advance:
- Read speech, not student answers.
- The model answer is in English, so this tests cross-language understanding as well as hearing.
- Tiers are a judgement.
- 30 sentences per language.
- FLEURS speakers are adults reading prepared text.

BUDGET. A cap of $15 (about 6,500 gradings).

Usage:
    python3 language/study.py prepare --dir <local dir>      # downloads the dev split for the 18 languages
    python3 language/study.py floor
    python3 language/study.py run --dir <local dir> [--go]
    python3 language/study.py analyse --dir <local dir>
"""

import argparse
import csv
import glob
import json
import os
import random
import subprocess
import sys
import tarfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

RUNS = os.environ.get("GBENCH_RUNS", "runs")
OUT = os.path.join(HERE, "out")
TIERS = {"HIGH": ["en_us", "es_419", "fr_fr", "de_de", "cmn_hans_cn", "ja_jp"],
         "MID": ["hi_in", "sw_ke", "vi_vn", "tr_tr", "id_id", "pl_pl"],
         "LOW": ["yo_ng", "am_et", "ps_af", "lo_la", "ckb_iq", "zu_za"]}
LANGS = [l for t in TIERS.values() for l in t]
TIER_OF = {l: t for t, ls in TIERS.items() for l in ls}
BASE = "https://huggingface.co/datasets/google/fleurs/resolve/main/data"
N_SENT, SEED, REPS = 30, 26, 2000
CAP = 15.0
REFUSE = ("cannot understand", "can't understand", "unable to understand", "not able to understand", "cannot hear",
          "can't hear", "unintelligible", "cannot determine", "can't determine", "unable to determine")


def tsv(d, lang):
    rows = list(csv.reader(open(os.path.join(d, lang, "dev.tsv")), delimiter="\t"))
    out = {}
    for r in rows:
        out.setdefault(r[0], (r[1], r[2]))  # first recording per sentence id
    return out


def cmd_prepare(a):
    for lang in LANGS:
        ld = os.path.join(a.dir, lang)
        os.makedirs(ld, exist_ok=True)
        if not os.path.exists(os.path.join(ld, "dev.tsv")):
            urllib.request.urlretrieve(f"{BASE}/{lang}/dev.tsv", os.path.join(ld, "dev.tsv"))
        if not glob.glob(os.path.join(ld, "audio", "*.wav")):
            tgz = os.path.join(ld, "dev.tar.gz")
            urllib.request.urlretrieve(f"{BASE}/{lang}/audio/dev.tar.gz", tgz)
            os.makedirs(os.path.join(ld, "audio"), exist_ok=True)
            with tarfile.open(tgz) as t:
                for m in t.getmembers():
                    if m.isfile() and m.name.endswith(".wav"):
                        m.name = os.path.basename(m.name)
                        t.extract(m, os.path.join(ld, "audio"))
            os.remove(tgz)
        print(lang, len(glob.glob(os.path.join(ld, "audio", "*.wav"))), "recordings", flush=True)


def items(d):
    """The 30 shared sentence ids, their English texts, and a fixed derangement for the MISMATCH model answers."""
    per = {l: tsv(d, l) for l in LANGS}
    shared = sorted(set.intersection(*(set(v) for v in per.values())), key=int)
    ids = sorted(random.Random(SEED).sample(shared, N_SENT), key=int)
    rnd = random.Random(SEED)
    perm = ids[:]
    while any(x == y for x, y in zip(ids, perm)):
        rnd.shuffle(perm)
    wrong = dict(zip(ids, perm))
    english = {i: per["en_us"][i][1] for i in ids}
    return ids, english, wrong, per


def build_cases(d):
    ids, english, wrong, per = items(d)
    path = os.path.join(d, "cases.jsonl")
    with open(path, "w") as fh:
        for lang in LANGS:
            for i in ids:
                wav = os.path.join(d, lang, "audio", per[lang][i][0])
                for kind, ref in (("match", english[i]), ("mismatch", english[wrong[i]])):
                    fh.write(json.dumps({
                        "id": f"{lang}:{i}:{kind}", "task": "spoken meaning", "question": "Say this sentence in your own language.",
                        "reference": ref, "rubric": "", "materials": "", "response": "(the student's spoken answer is attached)",
                        "scale": [0, 1], "human": {"key": 1 if kind == "match" else 0},
                        "groups": {"language": lang, "tier": TIER_OF[lang], "kind": kind, "sentence": i},
                        "media": [{"kind": "audio", "path": wav, "format": "wav"}]}) + "\n")
    return path, len(LANGS) * len(ids) * 2


# ------------------------------------------------------------------ stats
def accuracy(marks, keys):
    return sum(int(round(marks[k]) == keys[k]) for k in marks) / len(marks) if marks else float("nan")


def gap_iv(rows, hi="HIGH", lo="LOW", reps=REPS, seed=7):
    """rows: [(sentence, tier, correct 0/1)]; cluster bootstrap over sentences."""
    by = {}
    for s, t, c in rows:
        by.setdefault(s, []).append((t, c))
    sents = sorted(by)

    def stat(ss):
        a = [c for s in ss for t, c in by[s] if t == hi]
        b = [c for s in ss for t, c in by[s] if t == lo]
        return (sum(a) / len(a) - sum(b) / len(b)) if a and b else float("nan")
    rnd = random.Random(seed)
    vals = sorted(v for v in (stat([rnd.choice(sents) for _ in sents]) for _ in range(reps)) if v == v)
    return {"estimate": stat(sents), "ci95": [vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]]}


def verdict(iv):
    lo, hi = iv["ci95"]
    return "WORSE ON LOW-RESOURCE LANGUAGES" if lo > 0 else "BETTER ON LOW-RESOURCE LANGUAGES" if hi < 0 else "NO GAP DETECTED"


def cmd_floor(a):
    def world(p_hi, p_lo, k):
        rnd = random.Random(k)
        rows = []
        for s in range(N_SENT):
            dif = rnd.gauss(0, 0.10)
            for t in TIERS:
                p = {"HIGH": p_hi, "MID": (p_hi + p_lo) / 2, "LOW": p_lo}[t] + dif
                for _ in range(len(TIERS[t]) * 2):
                    rows.append((s, t, int(rnd.random() < min(1, max(0, p)))))
        return rows
    fa = sum(verdict(gap_iv(world(0.85, 0.85, k), reps=500, seed=k)) == "WORSE ON LOW-RESOURCE LANGUAGES" for k in range(200)) / 200
    det = sum(verdict(gap_iv(world(0.90, 0.80, 1000 + k), reps=500, seed=k)) == "WORSE ON LOW-RESOURCE LANGUAGES" for k in range(200)) / 200
    res = {"false_alarm": fa, "detection_10pt": det, "passes": fa <= 0.07 and det >= 0.80}
    print(res)
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "floor.json"), "w"), indent=1)


# ------------------------------------------------------------------ runs
def speech_models():
    out = []
    for d in sorted(x for x in glob.glob(os.path.join(RUNS, "speech-*")) if os.path.isdir(x)):
        c = json.load(open(os.path.join(d, "config.json")))
        out.append(c)
    return out


def spent():
    return sum((json.loads(line).get("usage") or {}).get("cost_reported") or 0.0
               for p in glob.glob(os.path.join(RUNS, "lang-*", "calls.jsonl")) for line in open(p)
               if not json.loads(line).get("cached"))


def cmd_run(a):
    path, n = build_cases(a.dir)
    for c in speech_models():
        left = CAP - spent()
        if a.go and left <= 0.5:
            print("cap reached")
            return
        out = os.path.join(RUNS, "lang-" + c["model"].replace("/", "_"))
        cmd = [sys.executable, "bench.py", "run", "--cases", path, "--prompt", "prompts/spoken-meaning.txt",
               "--base-url", c["base_url"], "--model", c["model"], "--key-env", "OPENROUTER_API_KEY", "--n", str(n),
               "--seed", "7", "--probes", "base", "--max-tokens", str(c.get("max_tokens") or 4096),
               "--extra-body", json.dumps(c.get("extra_body") or {}), "--out", out, "--workers", "8",
               "--max-usd", str(min(4.0, left)), "--max-calls", str(n + 10)]
        if a.go:
            cmd.append("--go")
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        print(f"{c['model'][:34]:34s} | " + " | ".join((r.stdout + r.stderr).strip().splitlines()[-2:])[:180], flush=True)
    print(f"spent ${spent():.2f} of ${CAP:.0f}")


def cmd_analyse(a):
    floor = json.load(open(os.path.join(OUT, "floor.json")))
    res = {"design": "language/study.py docstring", "floor": floor, "models": []}
    for d in sorted(x for x in glob.glob(os.path.join(RUNS, "lang-*")) if os.path.isdir(x)):
        cfg = json.load(open(os.path.join(d, "config.json")))
        calls = [json.loads(line) for line in open(os.path.join(d, "calls.jsonl"))]
        rows, per_lang, refusals, failed = [], {}, {t: 0 for t in TIERS}, 0
        for r in calls:
            lang, sent, kind = r["id"].split(":")
            if r.get("score") is None:
                failed += 1
                continue
            correct = int(round(r["score"]) == (1 if kind == "match" else 0))
            rows.append((sent, TIER_OF[lang], correct))
            per_lang.setdefault(lang, []).append(correct)
            if any(k in (r.get("text") or "").lower() for k in REFUSE):
                refusals[TIER_OF[lang]] += 1
        acc = {l: sum(v) / len(v) for l, v in per_lang.items()}
        tier = {t: sum(acc[l] for l in ls if l in acc) / max(1, sum(1 for l in ls if l in acc)) for t, ls in TIERS.items()}
        iv = gap_iv(rows)
        v = ("TASK NOT SUPPORTED" if acc.get("en_us", 0) < 0.80 else verdict(iv) if floor["passes"] else "UNMEASURED")
        row = {"model": cfg["model"], "accuracy": acc, "tier_accuracy": tier, "gap_high_minus_low": iv,
               "gap_mid_minus_low": gap_iv(rows, "MID", "LOW"), "gap_high_minus_mid": gap_iv(rows, "HIGH", "MID"),
               "refusals_by_tier": refusals, "failed": failed, "verdict": v,
               "not_ruled_out": iv["ci95"][1] if v == "NO GAP DETECTED" else None}
        res["models"].append(row)
        print(f"{cfg['model'][:30]:30s} en {acc.get('en_us', float('nan')):.2f} | HIGH {tier['HIGH']:.2f} MID {tier['MID']:.2f} "
              f"LOW {tier['LOW']:.2f} | gap {iv['estimate']:+.3f} [{iv['ci95'][0]:+.3f}, {iv['ci95'][1]:+.3f}] | "
              f"refusals {refusals} failed {failed} -> {v}")
        print("    " + " ".join(f"{l} {acc[l]:.2f}" for l in LANGS if l in acc))
    json.dump(res, open(os.path.join(OUT, "language.json"), "w"), indent=1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare"); p.add_argument("--dir", required=True); p.set_defaults(fn=cmd_prepare)
    sub.add_parser("floor").set_defaults(fn=cmd_floor)
    p = sub.add_parser("run"); p.add_argument("--dir", required=True); p.add_argument("--go", action="store_true"); p.set_defaults(fn=cmd_run)
    p = sub.add_parser("analyse"); p.add_argument("--dir", required=True); p.set_defaults(fn=cmd_analyse)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
