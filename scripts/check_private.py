"""Fail if the repository holds anything that must never be published.

Run in CI on every push and pull request, and before the repository is made public with --publish, which
also refuses machine-local paths and references to private repositories that are tolerated while the
work is private, and scans every line ever added in git history, not only the current files. A committed
file stays in git history, so this runs before anything is pushed.

The product's name is allowed in one place only: the conflict-of-interest line of the benchmark card,
which names it so readers can weigh the maintainers' interest (decided 2026-10-25). Its prompt, results
and any other mention are still refused.

    python3 scripts/check_private.py [--publish]
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALWAYS = [r"(?i)laz" + r"uli", r"sk-or-v1-[0-9a-f]{8,}", r"sk-ant-[A-Za-z0-9_-]{8,}", r"(?i)api[_-]?key\s*=\s*['\"][A-Za-z0-9_-]{16,}"]
# (file, text the line must contain) where the product name is allowed
NAME_ALLOWED = [("BENCHMARK-CARD.md", "**Conflict of interest:**")]
NAME_PATTERN = ALWAYS[0]
# Built from pieces, so this file never contains the strings it refuses (a history rewrite matching them
# would otherwise rewrite the check itself).
PUBLISH = [r"/home/" + r"user", r"/tmp/" + r"claude", r"\.\./grader" + r"-eval", r"(?i)learning-" + r"engineering-research",
           r"\.\./\.\./\.\./prod" + r"ucers"]


def allowed(f, p, line_text):
    return p == NAME_PATTERN and any(f == af and key in line_text for af, key in NAME_ALLOWED)


def scan(f, text, pats, hits):
    lines = text.split("\n")
    for p in pats:
        for m in re.finditer(p, text):
            n = text.count("\n", 0, m.start())
            if not allowed(f, p, lines[n]):
                hits.append(f"{f}:{n + 1}: matches {p!r}")


def history(pats, hits):
    """Every line ever added, in any commit on any branch."""
    log = subprocess.run(["git", "log", "--all", "-p", "--no-color", "--format=commit %h"], cwd=ROOT,
                         capture_output=True, text=True, errors="replace").stdout
    commit = f = None
    for line in log.split("\n"):
        if line.startswith("commit "):
            commit = line.split()[1]
        elif line.startswith("+++ "):
            f = line[6:] if line.startswith("+++ b/") else None
        elif line.startswith("+") and f and f != "scripts/check_private.py":
            for p in pats:
                if re.search(p, line[1:]) and not allowed(f, p, line[1:]):
                    hits.append(f"history {commit} {f}: matches {p!r}")


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
        scan(f, text, pats, hits)
    if "--publish" in sys.argv:
        history(ALWAYS, hits)
    if hits:
        print(f"{len(hits)} problem(s):\n  " + "\n  ".join(hits[:60]))
        sys.exit(1)
    print(f"{len(files)} tracked files clean" + (" for publication" if "--publish" in sys.argv else ""))


if __name__ == "__main__":
    main()
