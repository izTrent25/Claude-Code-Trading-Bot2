# Order block indicator, TJR style (15 November 2026)

Second of three indicators for the new combined strategy. Pine v6 file:
`pvnt_bot/OrderBlock_Indicator.pine`. Compiles clean on TradingView's server, zero errors, zero
warnings. **Live on your BTCUSD 5-minute chart** as an unsaved "Untitled script" (the Basic plan's one
saved slot is taken). The repo file is the real copy; paste it into a new indicator and press
"Add to chart" if the editor loses it. Do not paste into a LuxAlgo script: those are read-only.

## Why not the LuxAlgo code

You pasted LuxAlgo's "Order Block Detector". It does not follow TJR's rule:

- It finds a block wherever **volume** makes a spike at a turning point, not where market
  structure shifts.
- Its box covers only **half of one candle** (from the middle to the low), not the leg.
- It keeps three blocks per side, not one per trend.
- Its licence (CC BY-NC-SA) forbids commercial use, which matters if the bot ever earns money.

So this is our own build to your definition and your two example pictures. Ideas kept from LuxAlgo:
a midpoint line, removing a block once price goes through it (close or wick), and alerts.

## The rule in plain words (bullish; bearish is the mirror)

1. **Swings.** A swing high is a candle with 3 lower highs on each side (setting "Swing length",
   default 3 since 15 Nov, was 5). A swing low is the mirror. A swing is only known 3 candles later, so
   nothing repaints.
2. **Structure break.** A candle **closes** above the last unbroken swing high.
   - If the trend was down (or unknown), that is a **shift**: the trend is now up.
   - If the trend was already up, it is a **continuation break (BOS)**. No new block (TJR: one per trend).
3. **Where price turned.** On a shift, find the lowest low of the down-trend being reversed: from
   where that down-trend began (or the broken swing high, whichever is older) up to the candle
   **before** the break. The breaking candle is the displacement, never the block.
4. **The order block** is the down leg into that low: the low candle plus the down-closing candles
   right before it (up to 10). Box = highest high of the leg to the lowest low. If the low candle
   itself already closes up (a reversal candle), it only adds its low, not its high.
5. **One per trend.** A new bullish block replaces the old bullish one. A bearish shift makes a
   bearish block the same way, from the up leg into the top.
6. **Return and invalidation.** Price coming back into the box fires the "returned" alert (TJR's
   "return to fill more orders"). A candle **closing** below a bullish box (above a bearish one)
   removes it. Setting: or any wick.

## Settings

| Group | Setting | Default | Meaning |
|---|---|---|---|
| Structure | Swing length | 3 | 3 reads shifts like the eye on 5m; 5 waits for bigger turns, about 40% fewer blocks |
| | Max candles in the leg | 10 | how far back the leg may reach from the turning candle |
| | Require a liquidity sweep | off | only make a block if the turning low took out the previous swing low |
| | Also make blocks on continuation breaks | off | off = one block per trend |
| Boxes | Box covers | Wick | or Body: top at the leg's highest candle body |
| | Invalidated when | Close | or Wick |
| | Blocks kept per direction | 1 | |
| | Extend past current bar | 20 | |
| | Midpoint line, Labels | on | |
| | Show structure breaks | off | dotted line at each broken swing, labelled Shift or BOS |
| Colors | Bullish / Bearish | purple / orange | purple like your BTC example |

## How it was checked

TradingView was not reachable, so the same rule was written in Python
(`research/ob_visual_check.py`) and drawn on NQ 5-minute and 15-minute bars for 2 to 3 November 2026.
Three fixes came out of looking at those charts:

1. The breaking candle was sometimes picked as the block when it also made the lowest low. Now
   excluded.
2. A big reversal candle stretched boxes too far. Now it adds only its extreme.
3. A small swing that formed after a top made the search miss the true top. Now the search covers
   the whole trend being reversed.

After the fixes every box sits on the leg into the turning point, like your GBPUSD and BTC examples,
with one block per trend. On the NQ 5-minute day: 5 shifts, 5 blocks, 1 still live.

**Chart check (15 Nov, BTCUSD 5m, 300 loaded candles).** The Python twin was run on exactly the
candles pulled from the chart. Both show the same two live blocks to the cent:

| Block | Starts | Bottom | Top |
|---|---|---|---|
| Bullish | Sun 10:10 CT | 64,254.08 | 64,663.63 |
| Bearish | Sun 16:55 CT | 65,101.09 | 65,460.90 |

On the chart the bullish box covers the down leg into Sunday's low and price has since come back to
its top, the "return to the block" TJR describes.

## Swing length changed from 5 to 3 (15 Nov)

You drew a bearish block on MNQ 5m on the up leg into Sunday evening's 28,279 top. With swing length 5
the indicator drew nothing, because neither dip in that rally had 5 higher lows on each side (the
18:40 dip at 28,110.25 had only 4 candles before the 19:00 crash). The only confirmed swing low left was
Friday's 27,767.75, still unbroken, so by the rule the trend was still up.

With swing length 3 the 18:40 dip counts, the 19:00 candle closes below it at 28,048, and the block
appears at **28,147 to 28,279 from Sunday 17:20**, matching your drawing. Cost, same candles:

| Candles | Swing 5 | Swing 3 |
|---|---|---|
| MNQ chart, Thu to Sun | 9 blocks | 14 blocks |
| NQ, 2 to 3 Nov | 12 blocks | 21 blocks |

Only one block per direction stays on the chart, so the chart stays clean. Swing length is a choice
about how big a turn must be before it counts; the backtest can compare 3 and 5 later.

## Open questions for the combined strategy

- Should a block require a liquidity sweep (TJR's full setup), or is any shift enough?
- Entry at the box edge, the midpoint, or a fair value gap inside the box?
- Does the block have to line up with a fair value gap from the first indicator?

## Rule changed to match your hand-drawn blocks (17 Nov, MNQ 15m, combined script)

You drew two blocks on MNQ 15m and said the top one is bearish and the bottom one bullish:

| Block | Candles (CT) | Bottom | Top |
|---|---|---|---|
| Bearish | Mon 16 Nov 08:45 to 09:15 (3 red candles of the drop from the top) | 27,338.25 | 27,716.25 |
| Bullish | Tue 17 Nov 09:00 to 09:30 (3 red candles into the low) | 26,829.75 | 27,335.00 |

The combined script (`pvnt_bot/Combined_Strategy.pine`, part 2) now uses this rule:

- **Bullish block:** the red candles going into the lowest low before the break. If the lowest candle is a green
  reversal candle (Tuesday's long wick to 26,659), it is left out completely.
- **Bearish block:** the red candles of the drop from the highest high, starting at the top candle if it is red,
  otherwise the next one, through the breaking candle, and it keeps growing while candles stay red.
- **Continuation breaks also make blocks** (Monday's break was a continuation: the trend was already down).
- **A new block completely inside a live block of the same direction is skipped.**
- **Up to 3 blocks per direction**; a candle closing past the far side removes a block (as you asked).

Check: a Python run of the same rule on the 378 chart candles left exactly your two blocks live, to the tick,
and the chart after "Update on chart" shows the same two. The standalone `OrderBlock_Indicator.pine` still has
the old rule.

## Rule replaced by your written definition (17 Nov, later)

You clarified: strong displacement, a break of meaningful structure, and the zone is the **last opposing candle**
before the displacement; not every supply/demand area is an order block. The combined script now does that:

- Break: a close through a swing (swing length 3), trend turns or continues.
- Displacement: from the block candle's far edge to the breaking close must be at least 2 x ATR(14) (setting).
- Zone: the last red candle before a move up (bullish), the last green candle before a move down (bearish);
  the box is that one candle's high to low.
- Nested blocks skipped, 3 kept per side, removed on a close through the far side.

On the same MNQ 15m candles: the Monday bearish block is now the 08:30 green candle, **27,485 to 27,717**.
The Tuesday low gets no bullish block yet: the bounce has not broken a swing high with a 2-ATR move.

## Final rule: the leg before the liquidity sweep, one per trend (17 Nov, last change)

Your definition, combined with your clarification:

- **Order block = the leg of price immediately before the liquidity sweep.** The sweep is the turning extreme of
  the trend being reversed. The leg is the run of opposing candles into it: red candles into the low (bullish),
  green candles into the high (bearish). A reversal candle with a long wick is the sweep itself and is left out.
- **One per trend.** Only a shift (trend change) makes a block; continuation breaks (BOS) do not. 1 kept per side.
- **Strong displacement.** The move from the sweep to the breaking close must be at least 2 x ATR(14).
- **Return.** Price coming back into the block fires the "returned" alert. A close through the far side removes it.

On the MNQ 15m chart candles the live block is the Tuesday bullish one, **26,829.75 to 27,335.00** from 09:00,
exactly your drawn box. Monday's bearish box is not made: the trend was already down, so by "one per trend" that
break was a continuation, not a new block.
