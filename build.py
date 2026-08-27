#!/usr/bin/env python3
"""
build.py - Injects the current history.json into index.html as an inline
fallback, so the dashboard renders even when opened as a local file
(where fetch() of a sibling file is blocked by the browser).

On GitHub Pages the page fetches history.json live; the inline copy is
only used if that fetch fails.
"""

import json
from pathlib import Path

here = Path(__file__).parent
history = json.loads((here / "history.json").read_text())
template = (here / "template.html").read_text()

marker = "/*__HISTORY__*/null"
if marker not in template:
    raise SystemExit("marker not found in template.html")

out = template.replace(marker, json.dumps(history))
(here / "index.html").write_text(out)
print(f"Built index.html ({len(out):,} bytes, "
      f"{len(history['snapshots'])} snapshot(s) embedded)")
