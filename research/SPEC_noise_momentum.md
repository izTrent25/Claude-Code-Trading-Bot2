# Strategy spec: noise-area intraday momentum, version 1

Written 8 November 2026, before any run. Source: Zarattini, Aziz & Barbon (2024), "Beat the
Market: An Effective Intraday Momentum Strategy for S&P500 ETF (SPY)", Swiss Finance
Institute research paper 24-97, revised 3 February 2025 (sections 3 and 4 and the FAQ
appendix were read in full). Two open-source NQ builds exist on TradingView; the one by
PINEDIGGA publishes its NQ numbers year by year and was used as a cross-check on how the
rule behaves on our market. Neither build's code was copied; this is written from the paper.

Idea in one breath: most of the day the index only makes noise. For each half hour of the
session, measure how far price usually gets from the open by that time (average over the last
14 days). That gives a funnel, narrow at the open and wide by the close. Inside the funnel, do
nothing. When price is outside it at a half-hour mark, follow that direction with a trailing
stop and hold to the close.

Every judgement call is marked **[grey]** with the choice made. Times are Chicago (CT); New York
is one hour later, so the paper's 10:00 NY check is our 09:00 CT. All rules use completed bars.

## Session, bars and warm-up

- **Session** = 08:30 to 15:00 CT (09:30 to 16:00 New York, the cash-equity hours the paper
  uses). Overnight bars are ignored except to find yesterday's close.
- **Open** = the open of the first bar at 08:30 CT. **Yesterday's close** = the close of the
  bar ending at 15:00 CT on the previous session (the last close before 15:00 if that bar is
  missing).
- **Bars**: the runner feeds 5-minute bars (`--bars 5`) **[grey: the paper works on 1-minute
  prices but only acts on the half-hour; 5-minute bars give the same check prices and a
  near-identical VWAP, and run ten times faster. One run on 1-minute bars is logged as a
  check.]**
- **Check times** = the half-hour marks 09:00, 09:30, 10:00, ... 14:30 CT (12 checks; 10:00 to
  15:30 New York). A check uses the close of the bar that ends at that minute. Nothing happens
  between checks.
- **Warm-up**: 14 completed sessions with all 12 check prices. Sessions missing a check (half
  days, data gaps) are not stored and do not count toward the 14 **[grey]**. The first three
  weeks of the data therefore trade nothing. Counted.

## The noise area (the funnel), exactly as in the paper

For today t and each check time HH:MM:

1. For each of the last 14 stored sessions, the **move** to HH:MM = |close at HH:MM ÷ that
   session's open − 1|.
2. **σ(HH:MM)** = the plain average of those 14 moves.
3. **Upper band** = max(today's open, yesterday's close) × (1 + σ).
   **Lower band** = min(today's open, yesterday's close) × (1 − σ).
   Using yesterday's close as well as today's open is the paper's gap adjustment: after a gap
   down the upper band starts from yesterday's close, so the gap has to be overcome first.
4. **VWAP** = session volume-weighted average price from 08:30 CT, typical price
   (high+low+close)/3 × volume, cumulative, from the 5-minute bars.

## Entry

- At a check, if flat: **long** if the check close is above the upper band **and above VWAP**;
  **short** if below the lower band **and below VWAP**. Otherwise nothing.
  **[grey: the paper's entry text names only the band; VWAP is in its stop. But with the stop at
  max(band, VWAP), a long taken below VWAP is closed at the very next check, so the VWAP
  condition only removes trades that would last one half hour and lose the costs. The
  PINEDIGGA build has it too. The paper-literal entry without the VWAP condition is a logged
  variant.]**
- Fill at the **next bar's open with 2 ticks slippage** (the engine's market entry; on
  5-minute bars that is the price at the check minute).
- **Re-entries** are allowed at any later check the same day **[grey: the paper allows them
  and reverses; the NQ build measured re-entries as paying. A 2-trades-a-day cap is a possible
  later variant.]** Entries are allowed at every check through 14:30 CT **[grey: a 14:30 entry
  is a half-hour trade; the paper does not exclude it.]**

## Exit (the part the engine must learn)

- **Trailing stop, primary (the paper's "current band + VWAP" version):** at every check while
  long, if the check close is **below max(upper band at that check, VWAP)**, exit at that bar's
  close with 2 ticks slippage. Mirror for shorts: exit if the close is **above
  min(lower band, VWAP)**. The level is recomputed at each check and may move either way.
- **Base version (variant):** exit only when the close crosses the **opposite** band, and
  reverse into the new direction at the same check.
- **Flat at the close:** the engine's session flatten at 14:55 CT closes anything still open at
  the close of the 14:55 bar, i.e. at 15:00 CT = 16:00 New York, the paper's close.
- **Between checks nothing is watched.** The paper says stops "can also be triggered only on
  semi-hourly intervals". So the engine's usual intrabar stop is **switched off** for the
  primary (new research option `intrabar_stop=false`). A variant keeps a hard stop order at the
  opposite band that can fill between checks, which is what a live bot with a resting stop
  order would do.
- No target, no time stop.

## Engine additions (research options, off by default, covered by tests)

1. `intrabar_stop` (default true): when false the engine never fills a stop between bars; the
   proposal's stop is kept only for sizing and the record.
2. A strategy exit hook: after the strategy sees a bar, if it has `check_exit(position, bar)`
   and that returns a reason, the engine closes at the bar's close with slippage. If the same
   bar also produced a new proposal, it is taken at the next bar's open (the paper's reversal).

## Sizing, costs and the meaning of R

- **Fixed 1 contract** every trade (NQ bars standing in for MNQ, $0.50 a tick, $2 a point),
  as the NQ build did. The paper's 100%-of-equity and volatility-targeted sizing with up to 4×
  leverage are not used; its headline numbers lean on that leverage and we are not reproducing
  them, only the signal **[grey]**.
- Costs as everywhere: $0.75 per side, 2 ticks slippage on every market fill (entry, check
  exit, flatten). That is about $3.50 a trade, or 1.75 points. The NQ build used 1.5 points.
- **R** in the log for this strategy = net profit divided by the dollar distance from the entry
  to the opposite band at entry time (the stop used for the record). Points per trade and
  dollars are the primary numbers; R is kept so the log columns line up.
- Research sizing settings: `risk_per_trade` very large and `max_contracts` 1 so exactly one
  contract trades; `daily_loss` $5,000; `max_trades_per_day` 12; research mode.

## Random control

Same checks, same band and VWAP levels, same fills, but the side is a coin toss and the exit
level is mirrored around the signal close for a flipped trade (the strategy knows the side it
intended, so a flipped long is run as a short with the mirrored trailing level). 8 seeds. If
the real rule is no better than its flipped twin, "outside the funnel" says nothing about the
rest of the day.

## What the evidence says to expect (written down before the run, so it cannot be bent after)

- Paper, SPY 2007–2024 after costs: Sharpe 0.61 for the base version, 1.24 with the VWAP
  trailing stop; 43% daily hit rate; about 1.8 trades a day; losing years 2016 and 2017 only.
- NQ build, 2010–2026, 1 contract, 1.5-point cost: profit factor 1.27, 36% winners, average win
  49 points against average loss 22; **2010–2017 flat to negative**, profit from 2018 on;
  without the five best trades of each year every period is negative.
- So on our 2010–2020 window a marginal result is the likely outcome, with 2018 and 2020
  carrying it. The pass mark does not move for that.

## Acceptance (frozen before the run)

Worth keeping only if, on NQ 2010–2020 after costs, it beats its random-direction control,
has a profit factor above 1.0 and is positive in most years (6 of 11 or better). Such a rule
has earned the untouched 2021–2026 test, which is **not** run in this chat. Anything less is
closed. Nothing is tuned on 2021–2026. The paper's lookback-insensitivity table (5 to 90 days
all give Sharpe 1.2–1.5) means we do not need to tune the 14 days either, and we will not.

## Planned variants (logged as rows 73–80 in `research/research_log.md` before any run)

| Row | What | Purpose |
|---|---|---|
| 73 | Sanity run, NQ 2020, 5m bars, primary | geometry, durations, check times, a few trades by hand |
| 74 | **Primary**: VWAP trailing stop, VWAP entry filter, half-hour exits only, 1 contract, 2010–2020 | the rule |
| 75 | Base version: exit and reverse at the opposite band, no VWAP | the paper's first model |
| 76 | Primary plus a resting hard stop at the opposite band (fills between checks) | what a live stop order does |
| 77 | Primary without the VWAP entry condition | the paper-literal entry |
| 78 | Random-direction control of row 74, 8 seeds | does the direction mean anything? |
| 79 | Primary with zero commission and slippage | raw edge before costs |
| 80 | Primary on 1-minute bars, 2010–2020 | bar-size check on VWAP and fills |

## TradingView version

Per the house rule added 8 November, a Pine v6 version (`pvnt_bot/NoiseMomentum_Research.pine`)
is written after the sanity run so the chart shows the tested rules. It is **not** compiled in
or loaded on your TradingView until you say so.

## Confirmation (8 November 2026, late)

Run as written after your "test them all"; the grey choices above stand unless you overrule
one. Fixed 1 contract. Rows renumbered to 109–116: 109 sanity 2020 5m · 110 primary · 111 base
(opposite band, reverse) · 112 hard stop at the opposite band · 113 no VWAP entry condition ·
114 random-direction control (mirrored exits) · 115 zero costs · 116 1-minute bars.
