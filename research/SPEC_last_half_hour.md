# Strategy spec: last-half-hour intraday momentum, version 1

Written 8 November 2026, before any run. Sources: Baltussen, Da, Lammers & Martens, "Hedging
Demand and Market Intraday Momentum", JFE 2021 (60+ futures, 1974–2020: the return from the
previous close to 30 minutes before the close predicts the last 30 minutes); Gao, Han, Li &
Zhou, "Market Intraday Momentum", JFE 2018 (SPY: the first half-hour predicts the last). Step 1
tested a version requiring both to agree: +$8,507, positive only 2018 and 2020. Times Chicago.

## Rules (primary = the 2021 paper)
- **Day move** = the close of the bar ending at **14:30 CT** minus **yesterday's cash close**
  (last bar ending at or before 15:00 CT the previous session).
- **Direction** = the sign of the day move. Zero move = no trade.
- **Signal** at the close of the bar ending 14:30 (the 14:25 bar on 5-minute bars, the only bar
  size run); **entry at the next bar's open** (14:30) with 2 ticks slippage.
- **Exit** at the cash close: the engine's flatten at the close of the 14:55 bar = 15:00 CT.
- **No stop, no target** (the papers have none). For sizing and the record the stop is the
  session's opposite extreme so far (the day's low for a long, high for a short), never filled
  **[grey]**.
- One trade a day, fixed 1 contract, standard costs.

## Variants
- **Big-move days only [grey threshold]**: trade only when |day move| ÷ yesterday's close is at
  or above the median of the last 20 sessions' values. The papers find the effect concentrated
  on large-move days.
- **First-half-hour version (Gao et al.)**: direction = the sign of (close of the bar ending
  09:00 CT minus yesterday's close), still entered at 14:30.

## Control
Same days, direction by coin toss, 8 seeds.

## Expect
A small effect per day (R² about 1–2% in the papers); 1.75 points of micro costs against a
typical 30-minute move of 10–20 points is a tight fit. Marginal or losing is the likely outcome.

## Acceptance (frozen)
Beats its control, PF above 1.0, positive in 6 of 11 years or more, after costs.

## Variants (rows 91–96)
91 sanity 2020 · 92 primary · 93 big-move days · 94 first-half-hour · 95 control · 96 zero costs
