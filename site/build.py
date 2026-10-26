#!/usr/bin/env python3
"""Build the benchmark's public site: one self-contained page, site/dist/index.html, from site/src/ and the
committed public datasets in out/public/ (public_data.py). Nothing here computes a result: every number on the
page is read from out/public/, so rebuild that first (python3 public_data.py) and then this.

    python3 site/build.py [--out site/dist/index.html]

The page is in the Learning Design Alliance brand (site/src/site.css follows learning-research-reports
site/report/brand.css) and loads only Google Fonts; it works from any static host or from disk.
"""

import argparse
import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(HERE, "src")
# The LDA monogram, as on the reports site's footer (learning-research-reports site/lda-monogram.svg).
MONO = ('<svg aria-hidden="true" focusable="false" viewBox="35 40 157 68" fill="none" xmlns="http://www.w3.org/2000/svg">'
        '<path d="{d}" fill="currentColor"/></svg>')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.path.join(HERE, "dist", "index.html"))
    a = ap.parse_args()
    data = {os.path.basename(p)[:-5]: json.load(open(p)) for p in sorted(glob.glob(os.path.join(ROOT, "out", "public", "*.json")))}
    # The board's grading instructions and the six rewordings tested in paraphrase/, for the "What changes results" page.
    def instr(path):
        txt = open(path).read()
        # The system block is two paragraphs, the instruction then the reply format; both are reworded.
        system, reply = txt.split("### system", 1)[1].split("### user", 1)[0].strip().split("\n\n", 1)
        scale = next((l.strip() for l in txt.splitlines() if "{scale_min}" in l), "")
        return {"system": system, "reply": reply.split(":", 1)[0] + ".",
                "scale": scale.replace("{scale_min}", "[min]").replace("{scale_max}", "[max]")}
    data["paraphrase_prompts"] = [dict(name="Standard instructions (used for every result on this site)", **instr(os.path.join(ROOT, "prompts", "default.txt")))] + \
        [dict(name=f"Rewording {i}", **instr(os.path.join(ROOT, "prompts", "paraphrase", f"p{i}.txt"))) for i in range(1, 7)]
    # Where the datasets and methods come from: docs/SOURCES.md, one "- [key] reference URL — used for: ..." per line.
    data["sources"], sec = [], None
    for line in open(os.path.join(ROOT, "docs", "SOURCES.md"), encoding="utf-8"):
        if line.startswith("## "):
            sec = line[3:].strip()
        m = re.match(r"- \[(\w+)\] (.+?) (https?://\S+) — used for: (.+)", line.strip())
        if m:
            data["sources"].append({"key": m.group(1), "section": sec, "ref": m.group(2), "url": m.group(3), "used": m.group(4)})
    d = open(os.path.join(SRC, "monogram-path.txt")).read().strip()
    page = open(os.path.join(SRC, "index.html")).read()
    for k, v in (("{{HEAD}}", open(os.path.join(SRC, "head.html")).read().strip()),
                 ("{{CSS}}", open(os.path.join(SRC, "site.css")).read()),
                 ("{{JS}}", open(os.path.join(SRC, "site.js")).read()),
                 ("{{MONO}}", MONO.format(d=d)),
                 ("{{DATA}}", json.dumps(data, separators=(",", ":")).replace("</", "<\\/"))):
        assert k in page, k
        page = page.replace(k, v)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w").write(page)
    print(f"wrote {os.path.relpath(a.out, ROOT)}: {len(page) // 1024} KB, {len(data)} datasets")


if __name__ == "__main__":
    main()
