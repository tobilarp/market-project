# Talking about this project

Notes for you, not for the application. Everything below is only usable if it's
actually true when you say it — so build the thing, watch it run for a few weeks,
and then these become real answers rather than a script.

---

## The one-line version

"It's a daily read on equities, sectors, commodities and currencies — and it flags
moves that are unusual for that particular asset, so a 2% day in gas isn't news but
a 2% day in Treasuries is."

That sentence does the work. It says what the thing is, then lands the actual
insight: volatility is asset-specific, so "big move" means nothing on its own.

---

## The story worth telling

The interesting part of this project is **not** the dashboard. It's the constraint.

You wanted historical data to measure "unusual" against. Finnhub's free tier doesn't
sell history. Alpha Vantage caps at 25 calls a day. Both dead ends.

So the project collects its own. A scheduled job records a snapshot every weekday and
commits it, and the dataset grows from nothing into the baseline the z-scores are
measured against.

That's a real engineering decision with real trade-offs, and it's the thing to lead
with. Anyone can wire up an API. Working out what to do when the API won't give you
what you need is the actual skill.

Second-order benefits worth mentioning if it comes up: it also means the page makes
zero API calls when someone opens it (so it doesn't fall over with visitors), and the
keys never reach the browser.

---

## Questions you should have an answer ready for

**"Why z-scores?"**
Because "big move" is meaningless without knowing what normal looks like for that
asset. Natural gas routinely moves 3%; TLT doing the same would be a serious event.
The z-score normalises for that. Two standard deviations is the conventional
threshold — arbitrary, but conventional for a reason.

**"What are the weaknesses?"**
Have these ready, because being asked and having nothing is much worse than having
a list:
- Daily closes only — intraday moves are invisible
- Z-scores assume roughly normal returns; real returns have fatter tails, so it
  over-flags relative to theory
- ETF proxies aren't the underlying — tracking error, and roll cost on the commodity funds
- A flag has no idea *why* something moved; earnings and geopolitics look identical to it

Naming your own project's limits unprompted is the single most credible thing you can
do in this conversation.

**"Is this a trading signal?"**
No, and say so firmly. It's a screen — it tells you where to look. Turning a flag into
a view means reading the news and forming a judgement, which is the part a script
can't do.

**"How much of this did you write?"**
Answer honestly: you used AI assistance to write the code, and you made the design
decisions — what to track, how to define an anomaly, how to handle the rate limits,
what the proxies should be. That's true and it's fine. Anyone in markets is using these
tools now. What would *not* be fine is claiming to have hand-written it, because a
follow-up question will find that out in about thirty seconds.

If you want to be able to answer this more strongly, spend an afternoon actually
reading `collect.py` and the scoring function in the page until you could re-derive
them. That's a real afternoon of work and it changes the answer.

---

## Before you show anyone

- [ ] Deploy it and let it collect for **at least three weeks** — a dashboard saying
      "1 day on file" undercuts the whole thing
- [ ] Watch what it flags. Find one flag you can explain properly (what moved, why,
      what the headlines said). One worked example beats any amount of description.
- [ ] Read the code until you understand it
- [ ] Add your own commentary section if you want — but write it yourself

---

## Where it could actually go

You mentioned wanting this to help people your age keep up with markets. That's a
plausible direction and worth saying, but keep the claim proportionate: say it's the
direction you're interested in, not that you have users. If you do get people using
it, that becomes a much stronger thing to talk about — but only once it's true.

The honest framing: "I built this to learn, it's collecting live, and if it turns out
to be useful to other people that's where I'd take it next."
