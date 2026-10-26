#!/usr/bin/env python3
"""List every number in a document, with its line, for checking against its source (docs/METHODOLOGY.md 5.1, 5.3).

It flags the patterns behind this benchmark's past slips:
- a percentage above 100 where a share is meant (a rounded-up share of the ceiling, e.g. 1.025 shown as 103%);
- a number with a trailing zero after rounding (0.30, 0.80) that may have been rounded twice;
- a range whose ends are equal or reversed;
- "N of M" counts, so each can be checked against the current population.

It does not decide whether a number is right; it makes sure none is skipped.

    python3 scripts/check_numbers.py <document.md> [--flags-only]
"""
import re
import sys

NUM = re.compile(r"(?<![\w.])[-+−]?\d[\d,]*(?:\.\d+)?%?")
OF = re.compile(r"\b(\d+) of (?:the )?(\d+)\b")
RANGE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s*(?:-|–|to)\s*(\d+(?:\.\d+)?)(%?)")


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    path, flags_only = argv[0], "--flags-only" in argv
    total = flagged = 0
    for n, line in enumerate(open(path), 1):
        nums = NUM.findall(line)
        flags = []
        for m in re.finditer(r"(?<![\w.])(\d{3,})%", line):
            if int(m.group(1)) > 100 and ("ceiling" in line.lower() or "share" in line.lower()):
                flags.append(f"share above 100%: {m.group(0)} (check rounding against the source)")
        for m in re.finditer(r"(?<![\w.])\d+\.\d*0(?!\d)", line):
            flags.append(f"trailing zero: {m.group(0)} (rounded once from the source?)")
        for a, b, _ in RANGE.findall(line):
            try:
                if float(a) >= float(b) and "-" not in a:
                    flags.append(f"range not increasing: {a}-{b}")
            except ValueError:
                pass
        for a, b in OF.findall(line):
            flags.append(f"count {a} of {b}: re-check against the current population")
        total += len(nums)
        if flags:
            flagged += 1
        if nums and (flags or not flags_only):
            print(f"{n:4d}: {line.strip()[:120]}")
            for f in flags:
                print(f"      ! {f}")
    print(f"{total} numbers; {flagged} lines with something to check")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
