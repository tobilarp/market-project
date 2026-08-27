#!/usr/bin/env python3
"""
collect.py - Market data collector.

Pulls a snapshot of quotes from Finnhub and appends it to history.json.
Designed to run once per day (e.g. via GitHub Actions) so that over time
the repo accumulates its own time series - which is what the anomaly
detection scores against.

Requires env var FINNHUB_KEY.
"""

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

FINNHUB_KEY = os.environ.get("FINNHUB_KEY")
if not FINNHUB_KEY:
    sys.exit("FINNHUB_KEY not set")

HISTORY = Path(__file__).parent / "history.json"

# Watchlist. Commodities and foreign indices are tracked via liquid ETF
# proxies because Finnhub's free tier does not expose futures or FX.
WATCHLIST = {
    # US indices
    "SPY": {"name": "S&P 500", "cls": "index"},
    "QQQ": {"name": "Nasdaq 100", "cls": "index"},
    "IWM": {"name": "Russell 2000", "cls": "index"},
    # International indices
    "EWU": {"name": "UK / FTSE", "cls": "index"},
    "EWG": {"name": "Germany / DAX", "cls": "index"},
    "EFA": {"name": "Developed ex-US", "cls": "index"},
    "EEM": {"name": "Emerging Markets", "cls": "index"},
    # Commodities (ETF proxies)
    "USO": {"name": "WTI Crude", "cls": "commodity"},
    "BNO": {"name": "Brent Crude", "cls": "commodity"},
    "GLD": {"name": "Gold", "cls": "commodity"},
    "SLV": {"name": "Silver", "cls": "commodity"},
    "UNG": {"name": "Natural Gas", "cls": "commodity"},
    "DBA": {"name": "Agriculture", "cls": "commodity"},
    # Currency / rates proxies
    "UUP": {"name": "US Dollar Index", "cls": "fx"},
    "FXE": {"name": "Euro", "cls": "fx"},
    "FXB": {"name": "British Pound", "cls": "fx"},
    "FXY": {"name": "Japanese Yen", "cls": "fx"},
    # Rate-sensitive
    "TLT": {"name": "20Y+ Treasuries", "cls": "rates"},
    # Sectors - used for rotation analysis
    "XLE": {"name": "Energy", "cls": "sector"},
    "XLK": {"name": "Technology", "cls": "sector"},
    "XLF": {"name": "Financials", "cls": "sector"},
    "XLU": {"name": "Utilities", "cls": "sector"},
    "XLV": {"name": "Healthcare", "cls": "sector"},
    "XLI": {"name": "Industrials", "cls": "sector"},
}


def fetch(url, retries=3):
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if attempt == retries - 1:
                print(f"  failed: {e}", file=sys.stderr)
                return None
            time.sleep(2)


def get_quote(symbol):
    data = fetch(
        f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_KEY}"
    )
    # Finnhub returns c=0 for an unknown or unavailable symbol
    if not data or not data.get("c"):
        return None
    return {
        "c": data["c"],    # current price
        "pc": data["pc"],  # previous close
        "dp": data["dp"],  # percent change
        "h": data["h"],    # day high
        "l": data["l"],    # day low
    }


def get_news(limit=40):
    data = fetch(
        f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_KEY}"
    )
    if not data:
        return []
    out = []
    for item in data[:limit]:
        out.append({
            "headline": item.get("headline", ""),
            "summary": (item.get("summary", "") or "")[:280],
            "source": item.get("source", ""),
            "url": item.get("url", ""),
            "datetime": item.get("datetime", 0),
        })
    return out


def load_history():
    if HISTORY.exists():
        try:
            return json.loads(HISTORY.read_text())
        except json.JSONDecodeError:
            print("history.json corrupt, starting fresh", file=sys.stderr)
    return {"meta": {}, "snapshots": []}


def main():
    hist = load_history()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Don't double-collect the same day; overwrite instead.
    hist["snapshots"] = [s for s in hist["snapshots"] if s["date"] != today]

    quotes = {}
    print(f"Collecting {len(WATCHLIST)} symbols for {today}...")
    for symbol in WATCHLIST:
        q = get_quote(symbol)
        if q:
            quotes[symbol] = q
            print(f"  {symbol:5} {q['c']:>10.2f}  {q['dp']:+.2f}%")
        else:
            print(f"  {symbol:5} -- no data")
        time.sleep(1.1)  # stay under 60 calls/min

    hist["snapshots"].append({
        "date": today,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "quotes": quotes,
    })
    hist["snapshots"].sort(key=lambda s: s["date"])

    # Keep a rolling window - 400 days is plenty for a 90-day baseline
    hist["snapshots"] = hist["snapshots"][-400:]

    hist["meta"] = {
        "watchlist": WATCHLIST,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "snapshot_count": len(hist["snapshots"]),
        "news": get_news(),
    }

    HISTORY.write_text(json.dumps(hist, indent=2))
    print(f"\nWrote {HISTORY} - {len(hist['snapshots'])} snapshot(s) on file")


if __name__ == "__main__":
    main()
