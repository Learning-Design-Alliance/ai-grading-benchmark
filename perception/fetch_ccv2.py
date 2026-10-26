#!/usr/bin/env python3
"""Fetch only the sampled Casual Conversations v2 videos, by HTTP range request, never a whole part.

CCv2 (Meta; Porgali et al. 2023) ships 26,467 one-minute videos in 80 zips of about 59.5 GB each. The disk this
runs on holds about 13 GB, and the study needs a few hundred videos, so, as `video/fetch_lasana.py` does for
LASANA, this reads each part's central directory from its tail (`video/remote_zip.py`'s parser), maps every
video name to its part and offset, and then fetches only the sampled members.

THE LINKS ARE SECRETS. Meta's download links are signed URLs that work like passwords until they expire. They
are read at run time from the tab-separated list Meta's page gives (file_name, cdn_link; `--links`), held in
memory, and never printed, logged, cached, written to any file or passed on a command line (requests are made
with urllib, not curl, so they never appear in a process list). Error messages are reduced to the HTTP status.
The cached map holds part file names and byte offsets only.

WHAT IS KEPT. Each video exactly as Meta ships it: the zip member's bytes, decompressed, nothing else. The licence
forbids derivative works (clause 6.1), so nothing is re-encoded, trimmed, scaled or cut into frames. Originals
average about 148 MB, so the run fetches a batch, grades it, and deletes it (`clean`) before the next one; the
disk never holds more than one batch. Everything stays in the local directory given (`--dir`), outside the
repository. Every file written is appended to `DIR/manifest.jsonl` (name, bytes, when fetched, when deleted), so
a deletion request from Meta (clauses 4 and 9) can be met and shown to be met: `clean` deletes every file the
manifest lists that is still on disk.

READS a licensed corpus (CCv2; see docs/DATA-SOURCES.md). Raw videos never enter the repository.

    python3 -I perception/fetch_ccv2.py --links LINKS.txt --dir DIR map          # central directories -> DIR/cdmap.json
    python3 -I perception/fetch_ccv2.py --links LINKS.txt --dir DIR fetch [--batch K] [--limit N] [--names a.mp4,...]
    python3 -I perception/fetch_ccv2.py --dir DIR clean                          # delete every fetched video
    python3 -I perception/fetch_ccv2.py --dir DIR purge                          # clean, then delete the sample,
                                                                                 # the map and every run record
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "video"))
import remote_zip  # noqa: E402

MANIFEST = "manifest.jsonl"


class FetchError(IOError):
    """An error that carries no part of the URL."""


def _open(url, headers):
    req = urllib.request.Request(url, headers=headers)
    try:
        return urllib.request.urlopen(req, timeout=120)
    except urllib.error.HTTPError as e:
        raise FetchError(f"HTTP {e.code}") from None
    except Exception as e:  # noqa: BLE001  (URLError, socket errors: report the type only)
        raise FetchError(type(e).__name__) from None


def _range(url, start, end):
    with _open(url, {"Range": f"bytes={start}-{end}"}) as r:
        out = r.read()
    if len(out) != end - start + 1:
        raise FetchError(f"short read {len(out)} of {end - start + 1} at {start}")
    return out


def _size(url):
    with _open(url, {"Range": "bytes=0-0"}) as r:
        cr = r.headers.get("Content-Range")
    if not cr:
        raise FetchError("no Content-Range: server does not answer byte ranges")
    return int(cr.split("/")[-1])


# remote_zip's parser, with its transport swapped for one that keeps the URL out of argv and error text.
remote_zip._range = _range
remote_zip._size = _size


def read_links(path):
    """{file_name: url}. Held in memory only."""
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) == 2 and parts[0].endswith(".zip") and parts[1].startswith("https://"):
                out[parts[0]] = parts[1]
    return out


def video_parts(links):
    return sorted((k for k in links if k.startswith("CCv2_part_")), key=lambda k: int(k.split("_")[-1].split(".")[0]))


def cmd_map(a, links):
    path = os.path.join(a.dir, "cdmap.json")
    cd = json.load(open(path)) if os.path.exists(path) else {"parts": {}, "videos": {}}
    for part in video_parts(links):
        if part in cd["parts"]:
            continue
        try:
            members = remote_zip.members(links[part])
        except FetchError as e:
            print(f"{part}: {e}", flush=True)
            continue
        n = 0
        for name, (off, csize, method) in members.items():
            base = os.path.basename(name)
            if base.endswith(".mp4"):
                cd["videos"][base] = [part, name, off, csize, method]
                n += 1
        cd["parts"][part] = n
        tmp = path + ".tmp"
        json.dump(cd, open(tmp, "w"))
        os.replace(tmp, path)  # atomic: a crash never leaves a half-written map [3.2]
        print(f"{part}: {n} videos", flush=True)
    print(f"{len(cd['parts'])} parts mapped, {len(cd['videos'])} videos", flush=True)


def log(d, **rec):
    with open(os.path.join(d, MANIFEST), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(rec, at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))) + "\n")


def cmd_fetch(a, links):
    cd = json.load(open(os.path.join(a.dir, "cdmap.json")))
    if a.names:
        names = a.names.split(",")
    else:
        names = [r["video_name"] for r in json.load(open(os.path.join(a.dir, "sample.json")))["videos"]]
        if a.batch is not None:  # the sample in batches of --batch-size, in its fixed order
            names = names[a.batch * a.batch_size:(a.batch + 1) * a.batch_size]
    if a.limit:
        names = names[:a.limit]
    vdir = os.path.join(a.dir, "videos")
    os.makedirs(vdir, exist_ok=True)
    missing = [n for n in names if n not in cd["videos"]]
    if missing:
        print(f"{len(missing)} sampled videos are in no mapped part (map every part first)", flush=True)
    todo = [n for n in names if n in cd["videos"] and not os.path.exists(os.path.join(vdir, n))]

    def one(name):
        part, member, off, csize, method = cd["videos"][name]
        dst = os.path.join(vdir, name)
        tmp = dst + ".part"
        log(a.dir, file=os.path.relpath(tmp, a.dir), event="fetching")
        try:
            n = remote_zip.fetch(links[part], (off, csize, method), tmp)
            os.replace(tmp, dst)  # the original bytes, unmodified (licence clause 6.1)
            log(a.dir, file=os.path.relpath(dst, a.dir), event="fetched", bytes=n)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
        return name

    from concurrent.futures import ThreadPoolExecutor
    done = failed = 0
    with ThreadPoolExecutor(a.workers) as ex:
        futs = [ex.submit(one, n) for n in todo]
        for f in futs:
            try:
                f.result()
                done += 1
            except (FetchError, OSError) as e:
                failed += 1
                print(f"failed: {type(e).__name__} {e if isinstance(e, FetchError) else ''}", flush=True)
            if (done + failed) % 10 == 0 or done + failed == len(todo):
                print(f"{done + failed}/{len(todo)} ({failed} failed)", flush=True)


def cmd_clean(a):
    """Delete every fetched video (and any partial download) the manifest lists, and anything else in videos/."""
    vdir = os.path.join(a.dir, "videos")
    n = 0
    for root, _, files in os.walk(vdir):
        for f in files:
            p = os.path.join(root, f)
            os.remove(p)
            log(a.dir, file=os.path.relpath(p, a.dir), event="deleted")
            n += 1
    print(f"{n} files deleted from the video directory", flush=True)


def cmd_purge(a):
    """Everything this study derived from CCv2 on this machine: videos, sample, map, run records."""
    cmd_clean(a)
    import shutil
    for name in ("sample.json", "cdmap.json", "dryrun.json"):
        p = os.path.join(a.dir, name)
        if os.path.exists(p):
            os.remove(p)
            log(a.dir, file=name, event="deleted")
    for sub in ("videos", "runs"):
        p = os.path.join(a.dir, sub)
        if os.path.isdir(p):
            shutil.rmtree(p)
            log(a.dir, file=sub + "/", event="deleted")
    print("purged; the manifest is kept as the record of what was held and when it was deleted", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["map", "fetch", "clean", "purge"])
    ap.add_argument("--dir", required=True, help="local working directory, outside the repository")
    ap.add_argument("--links", help="Meta's tab-separated download list (file_name, cdn_link); never printed")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--names", default="")
    ap.add_argument("--batch", type=int, default=None, help="fetch batch k of the sample (0, 1, ...)")
    ap.add_argument("--batch-size", type=int, default=40, help="videos per batch (40 x ~148 MB fits the disk)")
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    os.makedirs(a.dir, exist_ok=True)
    if a.cmd in ("clean", "purge"):
        return {"clean": cmd_clean, "purge": cmd_purge}[a.cmd](a)
    if not a.links:
        sys.exit("--links is required")
    links = read_links(a.links)
    {"map": cmd_map, "fetch": cmd_fetch}[a.cmd](a, links)


if __name__ == "__main__":
    main()
