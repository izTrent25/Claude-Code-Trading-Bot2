# Strategy spec: TJR liquidity sweep, version 5

Written 8 November 2026 before any run, from your write-up of TJR's method (sweep → shift →
retrace into the gap → lower-timeframe trigger → stop behind the sweep → target the opposite
pool). Versions 1–4 (4 November, in the backup folder) all lost; they used a moving-average
bias, a blind limit order in the gap and no 1-minute trigger. Version 5 follows your write-up
on exactly those points. Every grey area is marked **[grey]** with the choice I made; tell me
where your own trading differs and I'll make it a logged variant.

Times are Chicago (CT). New York time is one hour later. All rules use completed bars only.

## Sessions and levels

- **Trading session** = 17:00 CT to 16:00 CT next day (the CME day). Daily bars are built on
  that boundary. **PDH / PDL** = the previous completed session's high and low.
- **Asia** = 19:00–23:00 CT. **London** = 01:00–04:00 CT. **Pre-market** = 06:00–08:30 CT
  **[grey: pre-market start; 06:00 CT = 7 AM ET]**. Each gives a high and a low.
- **Lows that can be swept for a long:** PDL, Asia low, London low, pre-market low. Highs for
  a short: the mirror. A level counts once per day.
- **Not in v5 [grey]:** previous-week high/low, equal highs/lows, clean 15m–1H swings,
  weekly context, SMT divergence with ES, news avoidance. Each is a possible variant.

## Daily bias

- On completed daily session bars, a **swing high** is a bar whose high is above the highs of
  the bar before and the bar after (confirmed one bar later); swing low is the mirror.
- **Bullish bias** when the most recent structure event is a daily body close above the last
  confirmed swing high; **bearish** when it is a close below the last confirmed swing low.
  No event yet = no bias = no trades. **[grey: this is "higher highs and higher lows" reduced
  to the direction of the last break of structure.]**
- Bullish bias allows only sweeps of lows (longs); bearish only sweeps of highs (shorts).
  Counter-bias setups are skipped entirely in v5 **[grey: he sometimes takes them small]**.

## The setup, long side (shorts are the mirror)

1. **Sweep (5-minute).** A 5-minute bar from 08:30 CT on, opening above one of the eligible
   lows, trades below it and closes back above it. The sweep extreme is the lowest low from
   that bar until the shift. A later 5-minute close below the level is a breakout and cancels
   the setup. Sweeps are only watched 08:30–09:30 CT (9:30–10:30 ET) **[grey]**.
2. **Shift (5-minute, within 6 bars = 30 minutes of the sweep) [grey: window].** A 5-minute
   bar body-closes above the most recent confirmed 5-minute swing high (bars since 06:00 CT,
   fractal of one bar each side) **and** shows displacement: its body is at least 0.8 × the
   average range of the last 12 five-minute bars **[grey: threshold]**. If no shift comes in
   time, or price makes a new low below the sweep extreme first, the setup is dead.
3. **Zone.** The move from the sweep to the shift must leave a bullish 5-minute fair value gap
   (three bars where bar 3's low is above bar 1's high), formed on or after the sweep bar and
   no later than one bar after the shift. Zone = bar 1's high (bottom) to bar 3's low (top).
   No gap, no trade. Order block and equilibrium are not used in v5 **[grey]**.
4. **Retrace and 1-minute trigger.** After the shift, wait for a 1-minute bar whose low enters
   the zone. From then on, a 1-minute close below the zone bottom cancels the setup. The
   trigger is a 1-minute break of structure: a 1-minute bar closes above the most recent
   confirmed 1-minute swing high formed since price entered the zone. The inverse-FVG
   trigger is not in v5 **[grey]**. The trigger must come within 60 minutes of the shift and
   before 09:30 CT **[grey]**.
5. **Entry.** Market on the next 1-minute bar's open, with 2 ticks slippage (the engine's
   rule). The limit-at-50%-of-the-gap entry is the separately logged variant "v5-limit".
6. **Stop.** Sweep extreme minus the larger of 2 ticks and 0.1 × the average 5-minute range
   **[grey: "a few ticks"; his example is 5 points on a 15,000-point NQ]**.
7. **Target.** The nearest of PDH, Asia high, London high, pre-market high that is at least
   2R above the estimated entry (signal close plus slippage). If none qualifies, no trade.
   Single target; partials and runners are not in v5 **[grey]**.
8. **Management.** No break-even move, no trailing in v5 **[grey]**. Flat at 10:00 CT (11 AM
   ET) if still open. Entries allowed 08:35–09:30 CT.

## Risk and day rules

- Research runs use a $500 budget and a $5,000 daily stop so sizing never filters a signal;
  the $20 budget (1% of a $2,000 drawdown) is a logged variant.
- At most 3 entries per day. After 2 consecutive losing trades in a day, no more entries that
  day (new engine rule `max_consecutive_losses`).
- Costs as everywhere: $0.75 per side, 2 ticks slippage on market and stop fills.

## Acceptance (frozen before the run)

Worth keeping only if, on 2010–2020, it beats its random-direction control, is positive after
costs in most years, and its profit factor is above 1.0. Otherwise it is retired and we return
to the 15-minute sweep rule's exit experiments. 2021–2026 stays untouched.

## Pine version

`pvnt_bot/TJR_Research.pine` is the TradingView strategy, meant for a 5-minute chart. It
cannot run the 1-minute trigger on a 5-minute chart, so it uses the limit-at-50%-of-the-gap
entry and matches the Python "v5-limit" variant, not the primary. Daily bias and session
levels are computed inside the script. Differences from the Python model are listed in the
file header.
