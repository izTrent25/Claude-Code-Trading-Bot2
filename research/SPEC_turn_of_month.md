# Strategy spec: turn of the month, version 1

Written 8 November 2026, before any run. Sources: Lakonishok & Smidt 1988; McConnell & Xu 2008;
Etula, Rinne, Suominen & Vaittinen, "Dash for Cash", Journal of Finance 2020; Carcano &
Tornero on S&P 500 futures. Long only, a swing rule: **not something a prop day-trading account
can hold**, tested because you asked for the evidence-backed set. Times Chicago.

## Rules (primary = the classic window)
- **Trading days** = Chicago calendar days with a bar at 08:30 CT, read from the data itself
  (exchange holidays are published years ahead, so knowing them is not look-ahead on prices)
  **[grey: research shortcut]**. 2021 is never read.
- **Entry**: at the close of the bar ending 15:00 CT on the **second-to-last trading day of the
  month**, go long; filled at the next bar's open (15:00 CT) with 2 ticks slippage.
- **Exit**: at the close of the bar ending 15:00 CT on the **third trading day of the next
  month** (the strategy tells the engine; close with slippage). Held through nights and
  weekends (`hold_overnight`). Four sessions in total: the last day and the first three of the next month.
- **No stop, no target.** Record stop = entry × 0.97, never filled **[grey]**.
- Fixed 1 contract, standard costs, 12 trades a year.

## Variant
- **Etula window**: enter at the close of the **fourth-to-last** trading day, exit at the close
  of the **last** trading day (the "recovery" days −3 to 0 in that paper).

## Control
Same number of trades and the same four-session hold each month, but starting on a random
trading day that does not overlap the turn-of-month window, 8 seeds. If the turn of the month
is no better than a random five days, it is just a rising market.

## Expect
Since 1926 the window carried most of the equity return; 132 trades in our window is a small
sample, so one bad month moves the total a lot.

## Acceptance (frozen)
Beats the random-days control, PF above 1.0, positive in 6 of 11 years or more, after costs.

## Variants (rows 104–108)
104 sanity 2020 · 105 primary · 106 Etula window · 107 random-days control · 108 zero costs
