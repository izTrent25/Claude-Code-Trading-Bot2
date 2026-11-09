# Strategy spec: first-five-minute-candle ORB with an ATR stop, version 1

Written 8 November 2026, before any run. Source: Zarattini & Aziz 2023, "Can Day Trading Really
Be Profitable?" (QQQ/TQQQ 2016–2023), rebuilt in Step 1 as `orb5_atr` v28: +$42,903 on 1 NQ
2010–2020, 7 of 11 years, passed that folder's random check (0.2%). This is **not** the range
breakout closed in rows 50–72: the entry is the colour of the first five-minute candle. Times
Chicago.

## Rules
- **Signal** at the close of the **08:30–08:35 CT** five-minute bar: close above open → long;
  close below open → short; equal → no trade. **Entry at the 08:35 bar's open** with 2 ticks
  slippage. Five-minute bars only.
- **Stop** = estimated entry (signal close plus slippage) minus **0.10 × ATR14**, where ATR14 is
  the average true range of the last 14 completed CME sessions (17:00–16:00 CT), snapped to the
  tick grid on the safe side. A real stop: fills intrabar with slippage.
- **No target.** Hold to the cash close: the engine flattens at the close of the 14:55 bar
  (15:00 CT).
- One trade a day, fixed 1 contract, standard costs. The first 14 sessions of the data have no
  ATR and trade nothing.

## Control
Same days, same stop distance, direction by coin toss, 8 seeds.

## Expect
Step 1: 17.9% winners, median stop 5.3 points, 2018–2019 supplied most of it. With micro costs
and 80% of trades stopped, the honest number may be far smaller.

## Acceptance (frozen)
Beats its control, PF above 1.0, positive in 6 of 11 years or more, after costs.

## Variants (rows 117–120)
117 sanity 2020 · 118 primary · 119 control · 120 zero costs
