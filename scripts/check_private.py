"""Fail if the repository holds anything that must never be published.

Run in CI on every push and pull request, and before the repository is made public with --publish, which
also refuses machine-local paths and references to private repositories that are tolerated while the
work is private. A committed file stays in git history, so this runs before anything is pushed.

    python3 scripts/check_private.py [--publish]
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALWAYS = [r"(?i)laz" + r"uli", r"sk-or-v1-[0-9a-f]{8,}", r"sk-ant-[A-Za-z0-9_-]{8,}", r"(?i)api[_-]?key\s*=\s*['\"][A-Za-z0-9_-]{16,}"]
PUBLISH = [r"~", r"scratch", r"\.\./private-analysis-repository", r"(?i)private-research-repository", r"\.\./\.\./\.\./producers"]


def main():
    pats = ALWAYS + (PUBLISH if "--publish" in sys.argv else [])
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    hits = []
    for f in files:
        if f == "scripts/check_private.py":
            continue
        try:
            text = open(os.path.join(ROOT, f), encoding="utf-8").read()
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        for p in pats:
            for m in re.finditer(p, text):
                line = text.count("\n", 0, m.start()) + 1
                hits.append(f"{f}:{line}: matches {p!r}")
    if hits:
        print(f"{len(hits)} problem(s):\n  " + "\n  ".join(hits[:60]))
        sys.exit(1)
    print(f"{len(files)} tracked files clean" + (" for publication" if "--publish" in sys.argv else ""))


if __name__ == "__main__":
    main()
