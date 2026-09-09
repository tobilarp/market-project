#!/usr/bin/env python3
"""
build.py - Renders index.html from template.html.

Injects two things at build time:
  * history.json, as an inline fallback so the page still renders when opened
    as a local file (where fetch() of a sibling file is blocked). On GitHub
    Pages the page fetches history.json live and this copy goes unused.
  * commentary.md, the hand-written analyst notes, split into dated entries.
"""

import json
import re
from pathlib import Path

here = Path(__file__).parent

history = json.loads((here / "history.json").read_text(encoding="utf-8"))
template = (here / "template.html").read_text(encoding="utf-8")

def parse_commentary(text):
    """Split commentary.md into entries, in the order they appear in the file.

    An entry begins with a markdown h2 - "## 8 September 2026 - title". The
    file is written newest-first, and the page renders it in that order, so
    adding a note means typing a new heading at the top. Any text before the
    first heading is kept as an untitled entry rather than silently dropped.
    """
    parts = re.split(r"^##[ \t]+(.+?)[ \t]*$", text, flags=re.M)
    entries = []
    lead = re.sub(r"<!--.*?-->", "", parts[0], flags=re.S).strip()
    if lead:
        entries.append({"heading": "", "body": lead})
    for heading, body in zip(parts[1::2], parts[2::2]):
        body = body.strip()
        if heading.strip() or body:
            entries.append({"heading": heading.strip(), "body": body})
    return entries


commentary_path = here / "commentary.md"
raw = commentary_path.read_text(encoding="utf-8") if commentary_path.exists() else ""
entries = parse_commentary(raw)

def inject(value):
    """JSON, safe to embed inside an inline <script> block.

    The browser looks for the literal "</script>" while reading the tag and
    does not care that it sits inside a JavaScript string, so one appearing
    in the data - a Finnhub headline, a commentary heading - would close the
    script element early and blank the whole page. Escaping "<" as \\u003c is
    still valid JSON and parses back to exactly the same string, so nothing
    in the data can break out of the tag.
    """
    return json.dumps(value).replace("<", "\\u003c")


subs = {
    "/*__HISTORY__*/null": inject(history),
    "/*__COMMENTARY__*/[]": inject(entries),
}

out = template
for marker, value in subs.items():
    if marker not in out:
        raise SystemExit(f"marker not found in template.html: {marker}")
    out = out.replace(marker, value)

(here / "index.html").write_text(out, encoding="utf-8")
print(f"Built index.html ({len(out):,} bytes, "
      f"{len(history['snapshots'])} snapshot(s), "
      f"{len(entries)} commentary entr{'y' if len(entries) == 1 else 'ies'}, "
      f"{len(raw.split())} words)")
for e in entries:
    print(f"  - {e['heading'] or '(untitled)'}")
