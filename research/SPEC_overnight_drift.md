# Strategy spec: overnight drift at the European open, version 1

Written 8 November 2026, before any run. Source: Boyarchenko, Larsen & Whelan, "The Overnight
Drift", Review of Financial Studies 2023 (NY Fed Staff Report 917): S&P 500 futures 1998–2018
earn about 3.6% a year gross in the hour before European markets open, 02:00–03:00 New York.
The NY Fed reported in July 2026 that the drift was flat in 2021–2025. Step 1's cousin
(02:00–06:00 NY, ATR stop) made +$30,396 on 1 NQ, 6 of 11 years, with 2020 alone +$33,929.
Times Chicago: the paper's hour is **01:00–02:00 CT**.

## Rules
- **Long** at the open of the 01:00 CT bar (signal at the close of the bar ending 01:00), every
  night that has that bar (Monday to Friday mornings; weekends have no bar).
- **Exit** at the close of the bar ending **02:00 CT** (the strategy tells the engine; the engine
  closes at that bar's close with 2 ticks slippage). The position is held through nothing else:
  no day change, no gap flatten (engine `hold_overnight`).
- **No stop, no target** (as in the paper). Record stop for sizing = entry × 0.995, never filled
  **[grey]**.
- Fixed 1 contract, standard costs. One trade a night.

## Variants
- **After down days only [grey]**: trade only when yesterday's cash close was below the day
  before's (the paper finds the drift strongest after selling).
- **Step 1's window**: 01:00 to 05:00 CT (02:00–06:00 New York), no stop.

## Controls
- **Random hour** (the one that matters): the same one-hour long each night at a random
  half-hour start between 17:30 and 06:30 CT, never 01:00, 8 seeds. If 01:00 is no better than
  a random hour, there is no drift, only a rising market.
- Random direction at 01:00, 8 seeds, for completeness.

## Expect
The published edge is about 1.4 basis points a night; micro costs are about 1.75 points, the
same size at NQ 10,000. After costs on one micro this may be nothing even if the drift is real.

## Acceptance (frozen)
Beats the random-hour control, PF above 1.0, positive in 6 of 11 years or more, after costs.

## Variants (rows 97–103)
97 sanity 2020 · 98 primary · 99 after down days · 100 01:00–05:00 · 101 random hour · 102 random direction · 103 zero costs
