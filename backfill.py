#!/usr/bin/env python3
"""
backfill.py - One-off: loads the daily closes from BEFORE this dashboard
started collecting, so the unusual-move screen has a calm baseline.

Why this exists: collection began on 27 Aug 2026, when the Iran oil shock was
already under way. Every observation the screen had was a crisis observation,
so "oil jumping around and drifting up" was all it had ever seen - and it
could never call that unusual. Loading the months before fixes the baseline.

What it does:
  * Pulls up to ~100 trading days of daily closes per fund from Alpha Vantage
    (TIME_SERIES_DAILY, the free endpoint).
  * Keeps only closes from BEFORE that fund's first collected session, so
    nothing is double-counted with history.json.
  * Also keeps Alpha Vantage's closes for the first few overlapping sessions,
    purely as a check that the two sources agree on the same prices.
  * Saves everything to backfill.json. history.json is never touched.

Free tier allows 25 calls a day and 5 a minute, and there are 26 funds, so
this needs running on two days. It picks up where it left off: a fund already
in backfill.json is skipped.

Requires env var ALPHAVANTAGE_KEY.
"""

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

KEY = os.environ.get("ALPHAVANTAGE_KEY")
if not KEY:
    sys.exit("ALPHAVANTAGE_KEY not set")

here = Path(__file__).parent
HISTORY = here / "history.json"
BACKFILL = here / "backfill.json"

CALLS_PER_RUN = 24      # stay under the 25/day free limit
PAUSE = 13              # seconds between calls, under the 5/minute limit
CHECK_DAYS = 5          # overlapping closes kept to compare the two sources

history = json.loads(HISTORY.read_text(encoding="utf-8"))
watchlist = history.get("meta", {}).get("watchlist") or {}
snaps = [s for s in history["snapshots"] if s.get("final") is not False]

# First collected session for each fund - DIA and IEF started later (8 Sep).
first_collected = {}
for s in snaps:
    for sym in s["quotes"]:
        first_collected.setdefault(sym, s["date"])
symbols = list(watchlist) or list(first_collected)

if BACKFILL.exists():
    data = json.loads(BACKFILL.read_text(encoding="utf-8"))
else:
    data = {
        "source": "Alpha Vantage TIME_SERIES_DAILY, unadjusted daily close",
        "note": "Closes from before each fund's first collected session. "
                "Used only as extra baseline for the z-score; never shown "
                "as part of the collected history.",
        "series": {},
        "check": {},
    }

todo = [s for s in symbols if s not in data["series"]]
print(f"{len(symbols) - len(todo)} of {len(symbols)} funds already backfilled; "
      f"{len(todo)} to go, up to {CALLS_PER_RUN} this run.")

calls = 0
for sym in todo:
    if calls >= CALLS_PER_RUN:
        break
    if calls:
        time.sleep(PAUSE)
    calls += 1
    url = ("https://www.alphavantage.co/query?function=TIME_SERIES_DAILY"
           f"&symbol={sym}&outputsize=compact&apikey={KEY}")
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            body = json.loads(r.read().decode())
    except Exception as e:
        print(f"  {sym}: request failed ({e}) - will retry next run")
        continue

    ts = body.get("Time Series (Daily)")
    if not ts:
        # Rate-limit and premium messages come back as "Note"/"Information".
        msg = body.get("Note") or body.get("Information") or body.get("Error Message") or body
        print(f"  {sym}: no data - {str(msg)[:160]}")
        if "Note" in body or "Information" in body:
            print("  Daily limit reached - stopping. Run again tomorrow.")
            break
        continue

    start = first_collected.get(sym)
    closes = sorted((d, float(v["4. close"])) for d, v in ts.items())
    before = [[d, c] for d, c in closes if start is None or d < start]
    after = [[d, c] for d, c in closes if start is not None and d >= start][:CHECK_DAYS]
    data["series"][sym] = before
    data["check"][sym] = after
    print(f"  {sym}: {len(before)} closes before {start} "
          f"({before[0][0] if before else '-'} to {before[-1][0] if before else '-'})")

    # Save after every fund so a crash or limit never loses fetched data.
    BACKFILL.write_text(json.dumps(data, indent=1), encoding="utf-8")

left = [s for s in symbols if s not in data["series"]]
print(f"Done for now. {len(symbols) - len(left)} of {len(symbols)} funds backfilled."
      + (f" Still to fetch: {', '.join(left)} - run again tomorrow." if left else " Complete."))
