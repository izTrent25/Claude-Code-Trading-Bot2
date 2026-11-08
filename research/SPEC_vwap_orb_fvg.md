# Strategy spec: VWAP + 15-minute opening range + FVG/order-block pullback

Written 8 November 2026, before any test was run. Version 1. Built from the Discord helper's
prompt: "a strategy using VWAP and 15m ORB and FVG/OB as support and resistance ... aiming
for at least 1R per trade, risking no more than 1% of my max drawdown per trade."

All rules use completed one-minute bars only. Nothing looks ahead. Times are Chicago.

## Session
- Regular session opens 08:30. Everything resets at the first bar of each Chicago calendar day.
- Overnight bars before 08:30 are ignored for this strategy.
- Entries allowed 08:45 to 14:30. Open positions are flattened from 14:55 by the engine.

## VWAP (bias and support/resistance)
- Volume-weighted average price anchored at 08:30, using typical price (high+low+close)/3
  times volume, cumulative through the day.
- Long trades only while the signal bar closes above VWAP. Short trades only while it closes
  below VWAP.

## 15-minute opening range (ORB)
- Opening range = highest high and lowest low of the fifteen one-minute bars 08:30–08:44.
- Breakout up = a bar from 08:45 onward closes above the range high. Breakout down = a bar
  closes below the range low. The breakout direction stands until a close beyond the opposite
  side flips it. Flipping clears any pending zones.

## Fair value gap (FVG) and order block (OB) zones
- Bullish FVG: three consecutive bars A, B, C where C's low is above A's high by at least 2
  ticks. Zone = A's high (bottom) to C's low (top). Only counted after an up-breakout.
- Bearish FVG: C's high is below A's low by at least 2 ticks. Zone = C's high (bottom) to A's
  low (top). Only counted after a down-breakout.
- Order block: if bar A (the origin bar) is opposite-coloured to the move (bearish before a
  bullish gap, bullish before a bearish gap), A's full range is treated as part of the zone
  for stop placement.
- A zone expires 60 bars after it forms, or as soon as a bar closes through it (close below a
  bullish zone's bottom, above a bearish zone's top), or once it has produced one trade.

## Entry (support/resistance test)
- Long: breakout is up, a later bar dips into a live bullish zone (low at or below the zone
  top) but closes at or above the zone bottom, and closes above VWAP. Signal at that bar's
  close; the engine enters at market on the next bar's open with 2 ticks slippage.
- Short: mirror image.
- The newest live zone is checked first. The bar that creates a zone cannot be its own entry.

## Stop and target
- Long stop = one tick below the zone bottom, or below the order block's low if there is one.
- Short stop = one tick above the zone top, or above the order block's high if there is one.
- Target = R multiple of the modeled stop distance. Primary 1.5R; 1.0R and 2.0R are logged
  variants. Time stop 60 bars. The engine's rules on both-hit bars (stop first) apply.

## Risk
- Risk budget per trade = 1% of a $2,000 max drawdown = $20, including round-trip
  commission ($0.75 per side) and 2 ticks slippage each way. If one micro contract costs more
  than $20 of risk, the trade is rejected and counted, not hidden.
- Max 2 contracts, max 3 entries per day, one position at a time, $250 daily loss stop.
- A $50 budget variant is logged so the effect of the tight budget is visible.

## Version 2 (8 November 2026, after the version 1 sanity run on 2020)

Version 1's sanity run on NQ 2020 fired 11,163 signals, traded 767, and the average trade
lasted 2.2 bars: with a 2-tick minimum gap the zones and stops were a point or two wide on
a 10,000-point market with 5–10 point bars, so noise hit the stop within minutes. Version 2
scales the geometry to current volatility. Version 1 stays reproducible by setting the three
new settings to 0 / 0 / false.

- **Average range** = mean high-minus-low of the last 20 session bars (needs at least 5).
- **Minimum gap** for a fair value gap = the larger of 2 ticks and 0.3 × average range.
- **Stop floor**: the stop is never closer to the estimated entry (signal close plus 2 ticks
  slippage) than 1.0 × average range. If the structural stop is tighter, it is widened to the
  floor and snapped to the tick grid on the safe side. Stops are never tightened.
- **Support held** now means the pullback bar closes back above the bullish zone's top
  (below the bearish zone's bottom), not merely inside it.
- Everything else is unchanged from version 1.

## Acceptance criteria (frozen before the run)
- The helper's wish is profit factor ≥ 2.0 and win rate ≥ 60%. Those are the bar to report
  against, not a promise. A rule that beats its random-direction control and is positive in
  most years would be worth taking to the 2021–2026 out-of-sample test; anything less is not.
- 2021 onward stays untouched.
