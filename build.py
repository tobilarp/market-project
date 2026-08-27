#!/usr/bin/env python3
"""
build.py - Renders index.html from template.html.

Injects two things at build time:
  * history.json, as an inline fallback so the page still renders when opened
    as a local file (where fetch() of a sibling file is blocked). On GitHub
    Pages the page fetches history.json live and this copy goes unused.
  * commentary.md, the hand-written analyst note.
"""

import json
from pathlib import Path

here = Path(__file__).parent

history = json.loads((here / "history.json").read_text(encoding="utf-8"))
template = (here / "template.html").read_text(encoding="utf-8")

commentary_path = here / "commentary.md"
commentary = commentary_path.read_text(encoding="utf-8") if commentary_path.exists() else ""

subs = {
    "/*__HISTORY__*/null": json.dumps(history),
    '/*__COMMENTARY__*/""': json.dumps(commentary),
}

out = template
for marker, value in subs.items():
    if marker not in out:
        raise SystemExit(f"marker not found in template.html: {marker}")
    out = out.replace(marker, value)

(here / "index.html").write_text(out, encoding="utf-8")
print(f"Built index.html ({len(out):,} bytes, "
      f"{len(history['snapshots'])} snapshot(s), "
      f"{len(commentary.split())} words of commentary)")
