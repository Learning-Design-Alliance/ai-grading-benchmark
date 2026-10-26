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
