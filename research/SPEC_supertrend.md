# Strategy spec: SuperTrend strategy (KivancOzbilgic), version 1

Written 8 November 2026, before any run, from the Pine v4 source you pasted ("SuperTrend
STRATEGY" by KivancOzbilgic, Mozilla Public License 2.0; the most-used SuperTrend script on
TradingView). The rules below are the script's defaults, untouched: nothing is tuned.

Idea in one breath: a volatility band (ATR × 3) trails below price in an uptrend and above it in
a downtrend. When price closes through the band, the trend flips and so does the position. It
is always in the market: long until a flip to short, short until a flip to long.

Every judgement call is marked **[grey]** with the choice made. Times are Chicago (CT).

## The indicator, exactly as the script computes it

- **Source** = (high + low) / 2 of the bar. **ATR** = Wilder's smoothed average true range over
  10 bars (the script's `atr()` with "Change ATR Calculation Method" = true, its default; the
  plain 10-bar average of true range is the alternative, not used). **Multiplier** = 3.0.
- **Up band** = source − 3 × ATR, but while the previous close was above the previous up band
  the up band may only rise (max of new and previous).
- **Down band** = source + 3 × ATR, but while the previous close was below the previous down
  band it may only fall (min of new and previous).
- **Trend** starts at +1. It flips to +1 when the trend is −1 and the close is above the
  previous down band; it flips to −1 when the trend is +1 and the close is below the previous
  up band. Everything is computed on completed bars; nothing looks ahead.
- **Buy signal** = the bar on which the trend flips to +1. **Sell signal** = the bar on which it
  flips to −1. The script enters on those bars only, so it is flat until the first flip and then
  always in.
- The bars run straight through overnight breaks and weekends, as they do on a TradingView
  chart: the ATR and bands are not reset by gaps.

## Version A: as published (holds overnight)

- Signal at the flip bar's close. **Entry at the next bar's open with 2 ticks slippage.**
- **Exit** at the next opposite flip: closed at that bar's close with 2 ticks slippage, and the
  new position in the other direction is opened at the following bar's open (the script does
  both at the next bar's open; the difference is one bar's open-to-close on the exit, which we
  accept rather than invent a fill the engine does not have).
- No stop, no target, no time stop, **positions are held overnight and over weekends**, no
  session window. Three new engine research options make this possible: `hold_overnight`
  (no flatten at the day change, at data gaps or at 14:55), `intrabar_stop=false` (the
  proposal's stop is kept for the record only) and a strategy exit hook (the strategy tells the
  engine to exit at a bar's close). All default off and covered by tests.
- **Stop for the record** = the current up band for a long (down band for a short) at signal
  time, which is also where the trend would flip. It is never filled between bars; R in the log
  is net profit over that distance. Points per contract and dollars are the primary numbers.
- **Bar sizes:** you asked for 1-minute, 5-minute and 15-minute bars, all three, 2010–2020.
  The 15-minute runs anchor the random controls; a third control is run on whichever bar size
  does best if that is not 15 minutes.

## Version B: day-session only

- Same indicator and flips, but a flip is acted on only when the flip bar closes between 08:30
  and 14:30 CT **[grey]**, and any open position is closed by the engine's session flatten at the
  close of the 14:55 bar (15:00 CT). Nothing is held overnight. A flip overnight sets the trend
  but opens nothing; the next in-session flip does.
- This is not the script as published. It is the version that matches your goal of a
  day-trading bot on a prop account, which cannot hold overnight.

## Costs and sizing

- **Fixed 1 contract** every trade, as the script's default quantity.
- $0.75 commission per side and 2 ticks slippage on every market fill, as everywhere in the
  log. **The script's own backtest has zero commission and zero slippage**, so its tester will
  always look better than this test; that gap is real money.
- NQ bars stand in for MNQ ($0.50 a tick, $2 a point) before May 2019.
- Research settings: `risk_per_trade` very large and `max_contracts` 1 so exactly one contract
  trades; `daily_loss` very large so no day guard interferes (version A); research mode.

## Random control

Same flip times, same bands, same fills, but the direction taken at each flip is a coin toss
(the `random_direction` wrapper; the exit still happens at the next flip regardless of the side
held). 8 seeds. If the real rule is no better than the coin-toss twin, "the band flipped" says
nothing about which way price goes next.

## What to expect (written before the run)

Always-in trend followers on 5- to 60-minute index bars flip often and most flips are
whipsaws; the classic result after costs is a profit factor near 1.0 with a few trending years
carrying the rest. The old Step 1 log found moving-average crosses lose on 1-minute NQ. A
marginal or losing result is the likely outcome; the pass mark does not move for that.

## Acceptance (frozen before the run)

Worth keeping only if, on NQ 2010–2020 after costs, it beats its random-direction control, has
a profit factor above 1.0 and is positive in most years (6 of 11 or better). Such a rule has
earned the untouched 2021–2026 test, which is **not** run in this chat. Anything less is closed.
Nothing is tuned on 2021–2026. The ATR period and multiplier stay at 10 and 3.

## Planned variants (logged as rows 73–83 in `research/research_log.md` before any run)

| Row | What | Purpose |
|---|---|---|
| 73 | Sanity run, NQ 2020, version A on 15m bars | flips, durations, a few trades by hand |
| 74 | **Version A, 15m, 2010–2020** | the script as published |
| 75 | Version A, 5m | same, faster flips |
| 76 | Version A, 1m | same, fastest |
| 77 | **Version B, 15m** | the day-session version |
| 78 | Version B, 5m | same, faster |
| 79 | Version B, 1m | same, fastest |
| 80 | Random-direction control of row 74, 8 seeds | does the flip direction mean anything? |
| 81 | Random-direction control of row 77, 8 seeds | same for the day version |
| 82 | Version A, 15m, zero commission and slippage | raw edge before costs |
| 83 | Random-direction control of the best of rows 74–79, if it is not 74 or 77 | the best run needs its own control |

## TradingView version

The script you pasted is the TradingView version; nothing new needs writing. It is not loaded
on your chart in this chat.
