"""
Fetch the leaderboard corpora, check them, and build the cases files the leaderboard pins.

All are public and open-licensed. Nothing here needs an account:

| task   | corpus                                   | source                                   |
|--------|------------------------------------------|------------------------------------------|
| mohler | Mohler ASAG (Mohler et al. 2011)         | Hugging Face nkazi/MohlerASAG, pinned commit |
| code   | HARMOGEN-R (Mendonca et al. 2026)        | Zenodo record 19534458                   |
| asap2  | ASAP 2.0 (Crossley et al. 2025)          | Kaggle lburleigh/asap-2-0, version 8     |
| maths  | VtG (Daheim et al. 2024), CC BY-SA 4.0   | GitHub eth-lre/verify-then-generate, pinned commit |

The pushback task reuses the short-answer cases (mohler).

    python3 fetch_data.py --dir data/

Every download is checked against its sha256 before use, and every cases file against the hash in
leaderboard-cases.json, so a leaderboard entry built from these files is comparable with every other.
The raw files stay in --dir; do not commit them.
Mohler's parquet needs pyarrow (`pip install pyarrow`).
"""

import argparse
import csv
import hashlib
import json
import os
import sys
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SOURCES = {
    "mohler": ("https://huggingface.co/datasets/nkazi/MohlerASAG/resolve/dac06732b42d01a5169f543f6d272f1476cced3e/data/cleaned-oe-00001.parquet",
               "mohler/cleaned-oe-00001.parquet", "f2aff37d7a3c6e6a7267afe0ab29ca4ebfbf90285b8eea77b08da9e1217376b0"),
    "code": ("https://zenodo.org/records/19534458/files/harmogenr_dataset_v2.zip?download=1",
             "harmogen/harmogenr_dataset_v2.zip", "d83ee9e6ee12adbfe127eed5f44fbacc996b2d3acdf013a9ec19ce0db26f0206"),
    "asap2": ("https://www.kaggle.com/api/v1/datasets/download/lburleigh/asap-2-0",
              "asap2/asap2.zip", "afef0d8b2b578ceff6bc0ef6286f37fd5d8da260d97ad2567c6b96cdd75cd964"),
    "maths": ("https://raw.githubusercontent.com/eth-lre/verify-then-generate/161019e6cc29968bb9a9ae7f261daf63f00e6fc7/dataset/dataset.json",
              "vtg/dataset.json", "335351285ae4b58176a671e6590d5ca29448df98f6b59c2ab8e5598cc8106cbf"),
}
OUT = {"mohler": "mohler.jsonl", "code": "harmogen-code.jsonl", "asap2": "asap2.jsonl", "maths": "vtg-cells.jsonl"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def get(url, path, want):
    if os.path.exists(path) and sha256(path) == want:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print(f"downloading {url}")
    urllib.request.urlretrieve(url, path + ".part")
    got = sha256(path + ".part")
    if got != want:
        sys.exit(f"{path}: sha256 {got} is not the pinned {want}; the source changed, so entries would not compare")
    os.replace(path + ".part", path)


def mohler_csv(parquet, out):
    import pyarrow.parquet as pq
    cols = ["id", "question", "instructor_answer", "student_answer", "score_grader_1", "score_grader_2", "score_avg"]
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in pq.read_table(parquet).to_pylist():
            w.writerow([r[c] for c in cols])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="data")
    ap.add_argument("--tasks", default="mohler,code,asap2,maths")
    a = ap.parse_args()
    import cases as cases_mod
    pins = json.load(open(os.path.join(HERE, "leaderboard-cases.json")))
    ok = True
    for task in a.tasks.split(","):
        url, rel, want = SOURCES[task]
        raw = os.path.join(a.dir, rel)
        get(url, raw, want)
        out = os.path.join(a.dir, OUT[task])
        if task == "maths":  # the four-version cells are built by the study's own (seeded) builder
            import importlib.util
            spec = importlib.util.spec_from_file_location("maths_process", os.path.join(HERE, "maths-process", "process.py"))
            mp = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mp)
            mp.cmd_build(argparse.Namespace(src=raw, out=out, n=200))
            got = sha256(out)
            match = got == pins.get(task)
            ok &= match
            print(f"{task}: -> {out}  {'matches the pinned file' if match else 'DOES NOT MATCH the pinned file ' + pins.get(task, '?')}")
            continue
        if task == "mohler":
            src = os.path.join(a.dir, "mohler", "mohler_en.csv")
            mohler_csv(raw, src)
            cs = cases_mod.from_mohler(src)
        elif task == "code":
            root = os.path.join(a.dir, "harmogen", "harmogenr_dataset_v2")
            if not os.path.exists(os.path.join(root, "csv", "tables")):
                zipfile.ZipFile(raw).extractall(os.path.join(a.dir, "harmogen"))
            cs = cases_mod.from_harmogen(root, "code")
        else:
            root = os.path.join(a.dir, "asap2")
            src = os.path.join(root, "ASAP2_train_sourcetexts.csv")
            if not os.path.exists(src):
                zipfile.ZipFile(raw).extractall(root)
            cs = cases_mod.from_asap2(src)
        cases_mod.write(cs, out)
        got = sha256(out)
        match = got == pins.get(task)
        ok &= match
        print(f"{task}: {len(cs)} cases -> {out}  {'matches the pinned file' if match else 'DOES NOT MATCH the pinned file ' + pins.get(task, '?')}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
