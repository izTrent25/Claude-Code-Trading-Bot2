# Strategy spec: PVNT flow entry (structure shift → gap retest → thirds), version 1

Written 8 November 2026, before any run and **before your yes**. Source: the trade shape in
Perky's gold screenshot (5 October 2026, Micro Gold 5-minute) and 7-second video, read into
`notes/PVNT_ACADEMY_GUIDE.md`. The PVNT indicator's own bias, quality, flow and gate logic is
proprietary and in none of the files, so this is the **closest testable reading of the shape**,
not the indicator. The materials are on gold; the data store has NQ, MNQ and ES only, so the
test runs on NQ as the MNQ proxy. No promise is made; the indicator's own scorecard in the
video, on the gold history Perky had loaded, reads **FLOW 325 trades, 20% win** and **SSM 43
trades, 56% win, +1.57 points**, before any cost. Expect little.

It folds in two `IDEAS.md` inbox items: "FVG retest entry" and "Partial exits and a trailing
stop". Five-minute bars, Chicago time, completed bars only. **[grey]** marks a judgement call.

## Structure (as `SPEC_tjr.md` defines it)
- **Swing high / low**: a 5-minute bar whose high (low) is above (below) the bars either side,
  confirmed one bar later. Tracked from 06:00 CT each day **[grey]**.
- **Shift up (long)**: a 5-minute bar body-closes above the most recent confirmed swing high,
  and that swing high was lower than the one before it (a lower high, so the close is a
  change of character), and the bar shows **displacement**: body ≥ 0.8 × the average range of
  the last 12 bars **[grey: TJR's value]**. Shift down is the mirror.
- The **swing low that started the shift** = the lowest confirmed swing low between the
  broken lower high and the shift bar.

## The gap and the entry
- The move from that swing low to the shift bar (allowing one bar after the shift) must leave
  a **bullish fair value gap**: three bars where bar 3's low is above bar 1's high by at least
  the larger of 2 ticks and 0.3 × the average range **[grey: VOF v2 value]**. Zone = bar 1's
  high (bottom) to bar 3's low (top). No gap, no trade.
- **Entry**: a resting **limit at the top of the gap** **[grey: alternative 50% of the gap]**,
  filled on a one-tick penetration at the limit price (engine rule), alive for **24 bars**
  (2 hours) **[grey]**, cancelled if the stop level trades first or the gap is closed through.
- **Stop**: one tick below the swing low that started the shift.
- Entries 08:30–11:00 CT; one trade per shift, at most 2 trades a day **[grey]**.
- **No bias filter in version 1 [grey]**: Perky's dashboard carries a bias we cannot recompute;
  the VWAP bias measured in row 23 is worthless; a 15-minute structure bias (direction of the
  last 15-minute break of structure) is the logged variant.

## Exits in thirds (new engine option `partials`, default off, with tests)
- **Size**: 3 contracts, so each third is one contract **[grey: fixed, as in the screenshot]**.
- **First third** at the nearer of **1R** and the nearest confirmed swing high above the entry
  **[grey]**. **Stop to break-even** (the entry) after it fills.
- **Second third** at **2R**.
- **Last third** at the next swing high beyond the first target, or the 14:55 flatten, whichever
  first **[grey]**.
- The screenshot's actual targets were 0.1R, 0.3R and 1.1R. They are **not** copied in version 1
  **[grey]**; a logged variant uses them exactly.
- Limit targets fill on a one-tick penetration; the stop fills intrabar with slippage; costs
  $0.75 per side per contract and 2 ticks slippage on market and stop fills.

## Control
Same shifts, same gap, same limit, stop and targets mirrored around the signal close, direction
by coin toss, 8 seeds (the `random_direction` wrapper, extended to mirror the list of partial
targets).

## Acceptance (frozen)
Beats its control, profit factor above 1.0, positive in 6 of 11 years or more, after costs.
Only that earns 2021–2026, which is not run in this chat.

## Planned variants (rows numbered when logged, after your yes)
sanity NQ 2020 · primary · screenshot targets (0.1R / 0.3R / 1.1R) · 15-minute structure bias
required · limit at 50% of the gap · single exit at 2R (no partials, to see what the thirds
cost or earn) · random-direction control · zero costs

## TradingView
A Pine v6 version goes on the chart only after the sanity run and only after you say so; your
Pine editor currently holds the unsaved sweep script and the chart is on 1 minute.

## Version 1 readings fixed by the Pine script (9 November 2026)

`pvnt_bot/PVNT_Flow_Research.pine` was written from this spec by the tracker chat and compiles
clean (0 errors, 0 warnings, checked server-side on 9 Nov; your chart and editor were not
touched). Where the spec was grey it had to choose; the Python twin uses the same readings unless
you change them:

- **Shift** = the first close through the level (the previous bar's close was not beyond it),
  with displacement body ≥ 0.8 × the average range of the previous 12 bars.
- **The swing that started the shift** = the lowest low (highest high for shorts) from the broken
  swing bar to the shift bar, not only confirmed swings.
- **The gap** is searched only inside that span, taking the most recent gap; one extra bar after
  the shift is allowed for it to form.
- **The limit** must still be a pullback: the shift bar's close must be beyond the limit price,
  otherwise no trade.
- **Third target** = the nearest swing level beyond 2R, else hold to the 14:55 flatten.
- **Break-even** is applied from the bar after the first third fills, as the engine's next-bar
  rule does.
- The script's Exits input offers Thirds (v1), the screenshot's 0.1R / 0.3R / 1.1R, and a single
  2R, matching the logged variants.
