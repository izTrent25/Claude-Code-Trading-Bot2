# Fair value gap indicator, rebuilt (9 to 10 November 2026)

First of three indicators for the new combined strategy. The original is "FVG/iFVG
(Nephew_Sam_)" on TradingView: closed source, so this is our own version. Version 1 was
built from screenshots and did not match. Version 2 was built to the written FVG spec you
pasted (TJR/ICT reading) but its defaults drew higher-timeframe and inverted gaps the original
does not show, so boxes looked wrong or too big. **Version 3 (10 Nov) keeps every spec feature
as a switch and sets the defaults to the original's look.** Checked box for box on your MNQ 5m
chart: identical.

Pine v6 file: `pvnt_bot/FVG_iFVG_Indicator.pine`. Compiles clean. Live on the MNQ1! 5m chart as
an **unsaved** script ("Untitled script" in the editor): your Basic plan's one saved slot is
taken by an old script called "SMC Algo", so TradingView refuses to save this one. The repo copy
is the real one. If the editor loses it, paste the file back in and press "Add to chart".

## What a fair value gap is

Look at any three candles in a row, numbered 1, 2, 3 in time order. If the wick of candle 1 and
the wick of candle 3 do not overlap at all, the middle candle moved so fast that it left a price
"hole". That hole is the fair value gap (FVG, also called an imbalance or liquidity void). The
colours of candles 1 and 3 do not matter; candle 2 just has to span the hole.

- **Bullish gap:** low of candle 3 is above the high of candle 1. The box runs from candle 1's
  high (bottom) to candle 3's low (top). It sits below price and acts as support. Green.
- **Bearish gap:** high of candle 3 is below the low of candle 1. The box runs from candle 3's
  high (bottom) to candle 1's low (top). It sits above price and acts as resistance. Red.
- **Midpoint (CE, consequent encroachment):** a dotted line at 50% of the box. TJR often puts
  his limit order here.

The box starts at candle 1 and extends right until it is removed (or for a fixed number of
bars, a setting). A label names it: "FVG", "15m FVG", "1h FVG", and so on.

## What happens when price comes back (the states)

| State | What happened | What the chart does |
|---|---|---|
| Fresh | price has not come back into the box | normal box |
| Partial | a wick entered the box | nothing visible, fires the "entered" alert |
| CE touched | a wick reached the midpoint | fires the "midpoint" alert |
| Filled | a wick reached the far edge (setting: or a candle closed through it) | deleted, or dimmed and frozen (setting) |
| Inverted (iFVG) | a candle **body** closed through the far edge | colour flips, dashed border, box stays. Old support is now resistance and the other way round. Removed when a body closes back through it |

Inversion wins over filled when both happen on the same candle. A close landing exactly on the
far edge counts as through it (that matched the original on one tiny gap).

## Settings

| Group | Setting | Default | Meaning |
|---|---|---|---|
| General | Filled means | Close | a candle has to close through the far edge; "Wick" fills on a wick touch |
| | When filled | Delete | or "Dim" to keep a faded, frozen box |
| | Show inverted gaps | off | the iFVG flip; turn on to see them |
| | Box length | Fixed, 20 bars from candle 1 | or "Until removed" to stretch to the current bar |
| | Midpoint line, Labels | on | |
| | Max bars back | 300 | only hunt for new gaps in the last 300 bars, for speed |
| | Max live gaps per direction | 30 | oldest out first |
| Filters | Minimum gap size, x ATR(14) | 0 (off) | 0.3 to 0.5 removes micro-gaps in chop |
| | Middle candle body, x ATR(14) | 0 (off) | enforces a real displacement candle |
| | Middle candle body, % of range | 0 (off) | 60 to 70 means a wide body with small wicks |
| | Session filter | off | only gaps formed inside 09:30 to 11:00 New York |
| Higher TFs | 15m, 1h, 4h, Daily | all off | turn on per timeframe; each only draws when above the chart's own |

All filters, higher timeframes and the inverted flip are off by default so the chart shows exactly
the original's raw 5-minute gaps. They exist so the combined strategy can be picky later.

## Checks against the original

**10 Nov, MNQ1! 5m, version 3 defaults.** The original showed 5 live boxes. Ours showed the same
5 at identical prices: 27,885 to 27,903.50; 27,829.75 to 27,850; 27,742 to 27,751; 27,692.25 to
27,694.75; 27,580.75 to 27,602.25. Labels, colours and widths look the same by eye.

**9 Nov, BTCUSDT 5m, version 2 defaults** (wick fill, higher timeframes and inverted on): 8 of the
original's 9 boxes matched to the cent; the 9th was filled by a wick in the live move during the
check; our 7 extras were exactly 5 higher-timeframe gaps and 2 inverted gaps. That is why the
defaults changed. The original's own higher-timeframe and inverted gaps never appeared as boxes
or lines during either check, so how it draws those is still unknown.

## Things to know

- **No repainting.** Gaps are only created and updated on closed candles. Higher-timeframe gaps use
  the last finished higher-timeframe bar, so a 1h gap appears when that hour closes.
- **Drawing limits.** TradingView allows 500 boxes, lines and labels each. The script keeps at most
  150 zones and 30 live per direction.
- **Alerts built in:** new bullish gap, new bearish gap, price entered a gap, price touched a
  midpoint, gap inverted. These are for the notification bot later.
- **Not a strategy yet.** It draws and nothing else. Trading rules come once all three indicators
  exist.
- **Session-open gaps:** the 08:30 CT futures open can make a giant candle 2. The session filter is
  how to include or exclude those; decide when the strategy is written.

## Open questions for the combined strategy

- Which of the three indicators sets the direction, and which time the entry?
- Does a trade need a chart-timeframe gap, a higher-timeframe gap, or an inverted one?
- Entry at the edge or at the midpoint? Stop beyond the far edge or a fixed multiple?
- Which filters (gap size, displacement, session, structure break) does TJR's "the FVG from the
  displacement that broke structure after a sweep" actually need?
