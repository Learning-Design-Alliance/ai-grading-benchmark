#!/usr/bin/env python3
"""Check that every work a document cites exists and is the work named.

Added 2026-10-25. O'Neill (2026) found fabricated references, probably written by a language model, in a
study six meta-analyses relied on. This repository's literature reviews were written by an agent, so every
citation is checked before anything is published.

For every URL in the file:
- arXiv: the abstract page is fetched; the cited first-author surname must be among the record's authors,
  and the cited year must be within one year of first submission (a preprint is often cited by the year of
  its final version).
- DOI (doi.org/...): Crossref's record, checked the same way.
- a landing page carrying citation_author metadata (ACL Anthology, most journals): checked the same way.
- anything else: the URL must resolve (HTTP status below 400).
The cited names and year are read from the text before the URL, back to the previous URL, semicolon or
list item; a citation matches when any cited name is among the record's authors ("Karjus et al.
2026, https://..."). A URL with no surname before it is checked for resolution only.

Verdicts per citation: OK, MISMATCH (resolves, but author or year do not match), UNRESOLVED (no record), and
UNCHECKED (resolved, no author given to compare). The script exits 1 if any citation is MISMATCH or
UNRESOLVED.

    python3 scripts/check_citations.py docs/LITERATURE.md [--out out/citation_check.json]
"""
import argparse
import html
import json
import re
import sys
import time
import urllib.request

URL = re.compile(r"https?://[^\s)\]>,;]+")
CITE = re.compile(r"([A-Z][A-Za-z'\-]+(?:\s(?:and|&)\s[A-Z][A-Za-z'\-]+)?)(?:\s+et al\.?)?,?\s*\(?((?:19|20)\d\d)")


def get(url, accept=None):
    req = urllib.request.Request(url, headers={"User-Agent": "citation-check/1 (benchmark maintainers)",
                                               **({"Accept": accept} if accept else {})})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            return e.code, ""
        except Exception:
            if attempt < 2:
                time.sleep(3)
                continue
            return None, ""
    return None, ""


def norm(s):
    return re.sub(r"[^a-z]", "", html.unescape(s).lower().replace("ü", "u").replace("é", "e").replace("ö", "o"))


def arxiv(aid):
    st, t = get(f"https://arxiv.org/abs/{aid}")
    if st != 200:
        return None
    authors = [html.unescape(a) for a in re.findall(r'<meta name="citation_author" content="(.*?)"', t)]
    title = re.search(r'<meta name="citation_title" content="(.*?)"', t)
    sub = re.search(r"\[Submitted on (\d+ \w+ (\d{4}))", t)
    withdrawn = "withdrawn" in t.lower()[:200000] and "This paper has been withdrawn" in t
    return {"title": html.unescape(title.group(1)) if title else None, "authors": authors,
            "year": int(sub.group(2)) if sub else None, "withdrawn": withdrawn}


def crossref(doi):
    st, t = get(f"https://api.crossref.org/works/{doi}")
    if st != 200:
        return None
    m = json.loads(t)["message"]
    year = (m.get("issued") or {}).get("date-parts", [[None]])[0][0]
    return {"title": (m.get("title") or [None])[0], "authors": [f"{a.get('family', '')}, {a.get('given', '')}" for a in m.get("author", [])],
            "year": year, "withdrawn": False}


def meta(body, nm):
    """Values of <meta name=nm content=...> in either attribute order, quoted or not."""
    out = []
    for tag in re.findall(r"<meta\b[^>]*>", body):
        if re.search(r'name=["\']?' + nm + r'["\'\s>/]', tag):
            c = re.search(r'content="([^"]*)"', tag) or re.search(r"content='([^']*)'", tag)
            if c:
                out.append(html.unescape(c.group(1)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--out")
    a = ap.parse_args()
    text = open(a.file, encoding="utf-8").read()
    results, seen, last_end = [], set(), 0
    for m in URL.finditer(text):
        url = m.group(0).rstrip(".")
        if url in seen:
            last_end = m.end()
            continue
        seen.add(url)
        # the citing text: back to the previous URL, semicolon, blank line or list item, whichever is nearest
        prev = [text.rfind(";", 0, m.start()), text.rfind("\n\n", 0, m.start()), last_end - 1]
        prev += [x.start() for x in re.finditer(r"\n\s*(?:\d+\.|-)\s", text[:m.start()])][-1:]
        before = re.sub(r"\s+", " ", text[max(prev) + 1:m.start()])
        last_end = m.end()
        c = list(CITE.finditer(before))
        names = re.findall(r"([A-Z][A-Za-z'\-]+)(?=,| et al| and| &|\s+\(?(?:19|20)\d\d)", before)
        surname = names[0] if names else None
        years = re.findall(r"(?:19|20)\d\d", before)
        year = int(years[-1]) if years else None
        rec, kind = None, "url"
        ax = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", url)
        dx = re.search(r"doi\.org/(10\.[^\s]+)", url)
        if ax:
            kind, rec = "arxiv", arxiv(ax.group(1))
        elif dx:
            kind, rec = "doi", crossref(dx.group(1))
        else:
            st, body = get(url)
            rec = None
            if st and st < 400:
                au = meta(body, "citation_author")
                ti = (meta(body, "citation_title") or [None])[0]
                ds = meta(body, "citation_publication_date") + meta(body, "citation_date")
                yr = re.match(r"(?:19|20)\d\d", ds[0]) if ds else None
                rec = {"status": st}
                if au:  # a scholarly landing page (ACL Anthology, journals) carries its own record
                    kind = "page"
                    rec.update({"title": ti, "authors": au, "year": int(yr.group(0)) if yr else None, "withdrawn": False})
        r = {"url": url, "cited_as": before.strip()[-120:], "surname": surname, "year": year, "kind": kind}
        if rec is None:
            r["verdict"] = "UNRESOLVED"
        elif kind == "url":
            r["verdict"] = "UNCHECKED" if surname else "OK"
            r["note"] = "resolves; not a scholarly record, so author and year not compared"
        else:
            r.update({"record_title": rec["title"], "record_first_authors": rec["authors"][:3], "record_year": rec["year"]})
            if rec.get("withdrawn"):
                r["note"] = "the record says it was withdrawn"
            if not surname:
                r["verdict"] = "UNCHECKED"
            else:
                # "Surname, Given" (arXiv, Crossref) or "Given Surname Suffix" (landing pages): any name part counts
                parts = lambda x: [norm(w) for w in re.split(r"[\s,]+", x) if len(norm(w)) > 1]
                hit = [n for n in names if norm(n) and any(norm(n) in parts(x) for x in rec["authors"])]
                au = bool(hit)
                if hit:
                    r["surname"] = hit[0]
                yr = year is None or rec["year"] is None or abs(year - rec["year"]) <= 1
                r["verdict"] = "OK" if au and yr else "MISMATCH"
                if not au:
                    r["problem"] = f"{surname} is not among the record's authors"
                elif not yr:
                    r["problem"] = f"cited {year}, record {rec['year']}"
        results.append(r)
        print(f"{r['verdict']:10s} {surname or '—':14s} {year or '':5} {url}" + (f"  ({r.get('problem')})" if r.get("problem") else ""), flush=True)
        time.sleep(1)
    counts = {v: sum(r["verdict"] == v for r in results) for v in ("OK", "UNCHECKED", "MISMATCH", "UNRESOLVED")}
    print(counts)
    if a.out:
        json.dump({"file": a.file, "design": "scripts/check_citations.py docstring", "counts": counts, "citations": results},
                  open(a.out, "w"), indent=1)
    sys.exit(1 if counts["MISMATCH"] or counts["UNRESOLVED"] else 0)


if __name__ == "__main__":
    main()
