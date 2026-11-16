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

1. **Swings.** A swing high is a candle with 5 lower highs on each side (setting "Swing length").
   A swing low is the mirror. A swing is only known 5 candles later, so nothing repaints.
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
| Structure | Swing length | 5 | bigger = only major swings, fewer blocks |
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

## Open questions for the combined strategy

- Should a block require a liquidity sweep (TJR's full setup), or is any shift enough?
- Entry at the box edge, the midpoint, or a fair value gap inside the box?
- Does the block have to line up with a fair value gap from the first indicator?
