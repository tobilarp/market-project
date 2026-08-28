# Daily Market Monitor

A daily read on global equities, sectors, commodities and currencies. 24 instruments,
collected automatically every weekday, with unusual moves flagged against each asset's
own history.

**Live:** https://tobilarp.github.io/market-project/

---

## What it does

Most market dashboards answer "what moved?" and stop. This one also answers **"was that
move actually unusual?"** — because a 2% day in natural gas and a 2% day in long-dated
Treasuries are not the same event. One is a Tuesday; the other is a dislocation. Scoring
each asset against its own volatility is what makes them comparable.

| Section | What it shows |
|---|---|
| Session summary | One generated sentence on where the index, sectors and commodities finished |
| Benchmarks | S&P 500, Nasdaq, UK and German equity proxies |
| What moved today | Leading and lagging sectors, biggest commodity move, risk posture — with related headlines |
| Sector rotation | Each US sector's move relative to the S&P, as a diverging bar chart |
| All tracked instruments | All 24 funds grouped by exposure, with anything unusual lifted to the top |
| Commodities & FX | Oil, gold, gas, agriculture, major currencies, long Treasuries |
| Analyst note | Hand-written interpretation — the only part of the page that isn't mechanical |

### On the narrative sections

Everything the page says about the market is computed from the price data. It will tell
you that energy lagged the index by 1.4 points; it will never tell you *why*, because it
has no way to know. Headlines are keyword-matched to the day's movers and shown as
possible context, explicitly labelled as making no causal claim.

Interpretation lives in `commentary.md`, written by hand and rendered on the page under
"Analyst note". That separation — mechanical below, human above, clearly marked — is
deliberate.

---

## Architecture

```
collect.py   ──>  history.json  ──>  build.py  ──>  index.html
(daily, CI)       (accumulating       (inlines        (static page,
                   time series)        data)           GitHub Pages)
```

The design is driven by one constraint: **free-tier API limits.**

- **Finnhub free** gives real-time equity quotes and market news, but no futures, no FX,
  and no historical candles.
- **Alpha Vantage free** gives FX spot, but caps at 25 requests *per day* — which a
  page that fetches on load would exhaust after a couple of visitors.

So the dashboard does not call an API when you open it. Instead:

1. A GitHub Action runs `collect.py` once each weekday after the US close.
2. It appends that day's quotes to `history.json` and commits the result.
3. `build.py` regenerates the static page.
4. The page is pure HTML — it loads instantly, costs no API calls, and works for any
   number of visitors.

Two useful side effects:

- **The repo accumulates its own dataset.** Since the free tier won't sell history, the
  project builds it — every run adds a day. That accumulated series is what the anomaly
  z-scores are measured against.
- **API keys never reach the browser.** They live in GitHub Actions secrets and are only
  ever used server-side.

### Everything tracked is an ETF

Worth stating plainly, because it is easy to misread the tables: **no row in this
project is an index, a barrel of oil or a currency.** Every one is an exchange-traded
fund — an instrument that trades like a share and tracks one of those things. `SPY` is
not the S&P 500; it is a fund holding the index constituents. `XLK` is not "technology";
it is the Technology Select Sector SPDR Fund.

The tables label this as **Ticker** (what trades), **Tracks** (the exposure it gives)
and **Exposure** (what kind). Free-tier data has no futures or FX, so the macro
exposures are reached this way:

| Exposure | Proxy | Exposure | Proxy |
|---|---|---|---|
| WTI crude | `USO` | UK equities | `EWU` |
| Brent crude | `BNO` | German equities | `EWG` |
| Gold | `GLD` | Sterling | `FXB` |
| Silver | `SLV` | Euro | `FXE` |
| Natural gas | `UNG` | Yen | `FXY` |
| Agriculture | `DBA` | US dollar | `UUP` |

These carry tracking error, and the commodity funds carry roll cost, so they are
directional indicators rather than spot prices. That is a real limitation of the free
tier and is stated on the page itself.

---

## Methodology

For each symbol, the daily percentage change is scored against the distribution of its
own prior daily changes:

```
z = (today's % change − mean of prior changes) / standard deviation of prior changes
```

A reading of `|z| ≥ 2` is flagged. Scoring requires at least 10 prior observations; below
that the dashboard reports "insufficient data" rather than producing a meaningless number.

**What a flag is not.** It is a prompt to investigate, not a signal. An earnings date, an
index rebalance, and a genuine geopolitical dislocation all produce the same statistical
footprint. Separating them requires reading the news — which is why headlines appear on
the same page.

**Known limits.** Daily closes only, so intraday moves are invisible. The z-score assumes
returns are roughly normal, which is a convenient approximation and not a true one — real
return distributions have fatter tails, so `|z| ≥ 2` fires somewhat more often than the
textbook 5%.

---

## Running it

```bash
export FINNHUB_KEY=your_key_here
python collect.py    # appends today's snapshot to history.json
python build.py      # regenerates index.html
```

Then open `index.html`.

## Deploying

1. Push this repo to GitHub.
2. **Settings → Secrets and variables → Actions → New repository secret**
   Name `FINNHUB_KEY`, value your Finnhub key.
3. **Settings → Pages** → Source: `master` branch, root.
4. **Actions** tab → *Collect market data* → *Run workflow* to take the first snapshot.

The scheduled run then adds a day automatically each weekday.

---

## Status

The monitor is live and collecting. The anomaly screen stays in "baseline building"
mode until roughly 11 sessions are on file — until then it shows raw moves ranked by
size, and says so on the page rather than pretending to a confidence it hasn't earned.

## Possible extensions

- Cross-asset correlation breaks (e.g. oil and energy equities decoupling)
- Alerting when a flag fires
- Sector-relative z-scores, not just index-relative
- Longer baselines once enough history has accumulated

---

Data from [Finnhub](https://finnhub.io). Not investment advice.
