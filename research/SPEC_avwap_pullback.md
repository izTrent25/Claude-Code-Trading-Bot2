# Strategy spec: Anchored-VWAP pullback (PhenLabs' "AVPT" indicator turned into a strategy)

Written 9 November 2026, before any run. Source: the Pine v6 **indicator** "Anchored VWAP Pullback &
Target Zones [PhenLabs]" that you pasted, kept unchanged at `pvnt_bot/AVPT_PhenLabs_indicator.pine`
(Mozilla Public License 2.0). It draws trade plans and keeps a scorecard but places no orders, so
"backtest it" means: turn its plans into real orders, charge real costs, and run it on NQ 2010–2020
with a random control. Five-minute bars, Chicago time, completed bars only, the indicator's own
default settings. **[grey]** marks a judgement call where the indicator itself does not say.

## What the indicator does, in plain words

1. It waits for a **swing low** (a bar whose low is below the 10 bars either side, confirmed 10 bars
   later) and anchors a **volume-weighted average price (VWAP)** at it, together with a standard
   deviation band. It also tracks the highest high since the anchor, the **impulse high**.
2. The anchor is **armed** once the impulse high is at least 1.4 ATR(14) above the swing low.
3. A **pullback** is price dipping into the band (low at or below VWAP + 1.0σ for the Balanced
   profile) while staying above the anchor and below the impulse high.
4. The **entry signal** is the first bar in the pullback that closes back above the VWAP, is an up
   bar, and closes within 0.2 ATR of the previous bar's high (a "reclaim"), provided the filters pass:
   Kaufman trend efficiency over 10 bars ≥ 26 %, a "quality score" (close position in the bar, trend
   efficiency and relative volume blended) ≥ 52, pullback depth between 12 % and 85 % of the impulse,
   and no five-bar crash of more than 3.6 ATR against the trade.
5. The **plan**: entry at the signal bar's close; stop at the lower of the pullback low and VWAP − 1.0σ,
   less 0.2 ATR, with the risk clamped between 0.35 and 3.0 ATR; targets at 1R, 2R and 3R, where in the
   default "hybrid" mode the impulse high replaces 2R if it sits 1.3–2.4 R away, or 3R if 2.4–4.5 R
   away. After TP1 is reached the stop moves to the entry. The plan ends at the stop, at TP3, after
   60 bars, or when a signal in the opposite direction arrives (a flip). At most 2 plans per anchor.
6. Shorts are the mirror from a swing high. Six preset **profiles** (Balanced, Conservative,
   Aggressive, Shallow, Deep Value, Volume Climax) differ only in band width, outer band, minimum
   trend efficiency, minimum quality, stop scale, minimum risk and minimum relative volume. The
   anchors are shared; the "2 plans per anchor" replacement test reads the Balanced profile's counter
   for every profile, as the indicator does.
7. **"Auto-Optimize"** picks, on every bar, whichever profile has had the best past "TP1+ win rate" on
   the chart. That is a choice made with hindsight on the same bars it is then scored on, and the
   win rate it uses counts a trade that reached TP1 and then stopped at the entry as a win. It is
   not a tradeable rule, so it is **not tested**; each profile is tested on its own (row 138 reports
   which profile the selector would have picked at the end of 2020 and whether that was the
   profitable one).

## From indicator to strategy: what had to change

- **Entry at the next bar's open**, not at the signal bar's close (nobody can buy a closed bar). The
  stop and targets stay where the indicator put them, measured from the signal close.
- **Three contracts, one per target.** The indicator's scorecard mixes "half out at TP1" with "all
  out at TP3". The honest reading of a 1R/2R/3R ladder is thirds: one contract to TP1, one to TP2,
  one to TP3, with the stop on the last two moved to the entry once TP1 is passed. The engine trades
  one target per run, so each run is one **leg** (`av_leg` = `tp1`, `tp2`, `tp3`) and the strategy's
  result is the three legs added trade by trade (`research/avwap_thirds.py`). The legs share every
  entry: the module tracks the plan's lifetime itself, exactly as the indicator does, and an entry
  is proposed only when the indicator would spawn a plan. The legs are also reported on their own.
- **A target counts when price trades one tick through it** (the fill rule the engine and the
  TradingView tester share, `backtest_fill_limits_assumption = 1`); the indicator counts a touch.
  The stop fills on a touch, with slippage, as before. The break-even move follows the first tick
  through TP1 and applies from the next bar, as in the indicator.
- **Pivots** need the centre bar strictly above (below) all 10 bars on each side **[grey: what
  `ta.pivothigh` does on equal highs is undocumented; the Pine strategy uses the same explicit rule,
  so the two versions agree]**.
- **Levels are rounded to the tick** when the plan is made, as TradingView does with order prices.
- **Flip**: an opposite signal closes the open trade at that bar's close and the new trade enters at
  the next open, as the indicator's plan does. A same-direction signal while a trade is open cannot
  happen (the indicator blocks it); if the engine is still in a trade the indicator's plan has
  already ended (a rare gap case), the new signal is dropped.
- **Hours**: version A, as published, trades at any hour and holds through session breaks and
  weekends, with the 60-bar expiry as its only clock. Version B **[grey]** is the day-trader's
  reading: signals only 08:30–14:30 CT, everything flat at 14:55, the plan ends at the flatten; the
  indicator's anchors and zones still run on every bar.
- **Costs**: $0.75 per side per contract and 2 ticks of slippage on market and stop fills; the
  indicator and TradingView's tester default to zero.
- **Profile** is a setting (default Balanced, the indicator's first profile and the one its anchor
  rule reads). Custom thresholds are available but not run.

## Control

Same signals, same stop, targets and break-even level mirrored around the signal close, direction by
coin toss, 8 seeds (the `random_direction` wrapper, extended to mirror `breakeven_at`); the flip and
expiry happen on the same bars. Each seed is the sum of its three legs, as the strategy is.

## Acceptance (frozen, the same pass mark as the six candidates)

Beats every one of its eight random-direction seeds, profit factor above 1.0, positive in 6 of 11
years or more, after costs. Only that earns 2021–2026, which is not run here. "Very profitable" by the
roadmap's proposed bar means profit factor 1.3 or better, +0.15R or better a trade, 8 of 11 years.

## Planned variants (rows 121–138 in `research/research_log.md`, logged before running)

sanity NQ 2020 (TP3 leg) · Balanced legs TP1, TP2, TP3 and their sum, 5m, 2010–2020, version A ·
random-direction control, 8 seeds · zero costs · fixed R ladder (no impulse magnet) · break-even off ·
the five other profiles · version B day session · 1-minute and 15-minute bars · the Auto-Optimize
hindsight check.

## TradingView

`pvnt_bot/AVWAP_Pullback_Research.pine` is the indicator rewritten as a `strategy()`: the same seven
profile engines and state machine, drawing code removed, orders added for the chosen profile (three
contracts, one exit per target, stop to entry when the first third fills, 60-bar time stop, flip,
costs set). It is written for any chart timeframe, as the indicator is; the Python verdict is on 5m.
