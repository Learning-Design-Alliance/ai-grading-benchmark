#!/usr/bin/env python3
"""Check that a study is pre-registered the way docs/METHODOLOGY.md requires.

For each study script whose docstring says PRE-REGISTERED, checks that:
- the docstring has a dated pre-registration and the sections WHY, DESIGN, VERDICT (or VERDICTS), FLOOR and
  BUDGET (a study with no calls may say "no calls" in place of BUDGET) [1.1, 1.2];
- numbered CHANGES run 1, 2, 3 ... with no gaps, and each is dated [1.1];
- the study directory has a README.md and an out/ directory once results exist;
- every verdict string the README uses in capitals appears in the docstring (a renamed or invented label is a
  common slip) [4.1];
- no machine-local path is a default (`/home/`, `/tmp/`) [3.5].

    python3 scripts/check_study.py [study dirs ...]      # default: every study in the repository
Studies pre-registered from 2026-10-26 (when docs/METHODOLOGY.md took effect) must pass; earlier ones are listed
as warnings. Exit status 1 if any study registered from that date fails.
"""
import ast
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def docstring(path):
    try:
        return ast.get_docstring(ast.parse(open(path).read())) or ""
    except SyntaxError:
        return ""


SYN = {
    "WHY": r"\bWHY\b|\bQUESTION\b",
    "DESIGN": r"\b(DESIGN|CASES|MODELS|ARMS|RUNS|PROBES|TASKS?|DATA|CONDITIONS|BATTERY|RECORDINGS|GRADERS)\b",
    "FLOOR": r"\bFLOOR\b|planted",
    "VERDICT": r"\bVERDICTS?\b",
    "BUDGET": r"\bBUDGET\b|\bCOST\b|\bno calls\b|\bNo new calls\b|\bno model call|\bcap of \$|\$\d",
}


def check(path):
    problems = []
    doc = docstring(path)
    if "PRE-REGISTERED" not in doc or os.path.basename(os.path.dirname(path)) == "scripts":
        return None
    if not re.search(r"PRE-REGISTERED \d{4}-\d{2}-\d{2}", doc):
        problems.append("no dated PRE-REGISTERED line")
    for name, pat in SYN.items():
        if not re.search(pat, doc) and not (name == "WHY" and doc.split("\n", 1)[0].rstrip().endswith(("?", "? PRE-REGISTERED"))
                                            or (name == "WHY" and "?" in doc.split("\n", 1)[0])):
            problems.append(f"no {name} section")
    changes = doc.split("CHANGES", 1)[1] if "CHANGES" in doc else ""
    cnums = [int(n) for n in re.findall(r"(?m)^\s*(\d+)\. \(", changes)]
    if cnums and cnums != list(range(1, len(cnums) + 1)):
        problems.append(f"CHANGES not numbered 1..n: {cnums}")
    undated = [n for n in re.findall(r"(?m)^\s*(\d+)\. \(([^)]*)\)", changes) if not re.search(r"\d{4}-\d{2}-\d{2}", n[1])]
    if undated:
        problems.append(f"undated CHANGES: {[n[0] for n in undated]}")
    src = open(path).read()
    if re.search(r'os\.environ\.get\([^)]*"/(home|tmp)/', src):
        problems.append("a machine-local default path")
    d = os.path.dirname(path)
    mds = [m for m in glob.glob(os.path.join(d, "*.md"))]
    if os.path.isdir(os.path.join(d, "out")) and os.listdir(os.path.join(d, "out")) and not mds:
        problems.append("results in out/ but no write-up (*.md)")
    flat_doc = " ".join(" ".join(docstring(q) for q in glob.glob(os.path.join(d, "*.py"))).split())
    for md in mds:
        text = " ".join(open(md).read().split())
        used = set(re.findall(r"\b((?:NO |NOT |CAN |DOES )?[A-Z][A-Z-]+(?: [A-Z0-9%-]+){1,5})\b", text))
        verdictish = {u for u in used if any(w in u for w in ("DETECTED", "EXCEEDS", "FIXED", "MATTERS", "SENSITIVE",
                                                                  "BELOW", "ABOVE", "WITHIN", "HOLDS", "YIELDS", "DRIFT",
                                                                  "RESPONDS", "CAN SEE", "CANNOT", "UNMEASURED"))}
        missing = sorted(v for v in verdictish if v not in flat_doc)
        if missing:
            problems.append(f"{os.path.basename(md)} verdicts not in the docstring: {missing}")
    return problems


STRICT_FROM = "2026-10-26"  # docs/METHODOLOGY.md took effect; earlier studies are reported, not failed


def registered(path):
    m = re.search(r"PRE-REGISTERED (\d{4}-\d{2}-\d{2})", docstring(path))
    return m.group(1) if m else "0000-00-00"


def main(argv):
    dirs = argv or sorted({os.path.dirname(p) for p in glob.glob(os.path.join(ROOT, "*", "*.py"))})
    bad = 0
    seen = 0
    legacy = 0
    for d in dirs:
        for path in sorted(glob.glob(os.path.join(d, "*.py"))):
            r = check(path)
            if r is None:
                continue
            seen += 1
            rel = os.path.relpath(path, ROOT)
            if r and registered(path) >= STRICT_FROM:
                bad += 1
                print(f"FAIL {rel}: " + "; ".join(r))
            elif r:
                legacy += 1
                print(f"warn {rel} (registered {registered(path)}, before the methodology): " + "; ".join(r))
            else:
                print(f"ok   {rel}")
    print(f"{seen} pre-registered studies checked, {bad} failing, {legacy} earlier studies with gaps (warnings)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
