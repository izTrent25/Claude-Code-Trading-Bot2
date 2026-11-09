# Strategy spec: opening-range breakout on its own, version 1

Written 8 November 2026, before any run. Source: the Discord helper ("I mainly stick with
ORB, VWAP, EMAs") and your own words for this test: the first 15 minutes after the 08:30
Chicago open make a high and a low; buy on the first bar close above that range, sell on
the first close below it; stop on the other side of the range; target one or two range
heights. No fair value gap, no VWAP, no bias filter.

The old Step 1 project (backup folder, 4 November) had two ORB rules. The plain one lost on
1-minute bars; a 5-minute version with a tight ATR stop and no target made +$42.9k on one
NQ contract, 7 of 11 years, but it never had a random control or MNQ costs, so that number
is a reason to test, not evidence.

Every judgement call I had to make is marked **[grey]** with the choice made. Tell me where
you would trade it differently and it becomes a logged variant instead of a silent change.

Times are Chicago (CT). New York time is one hour later. All rules use completed bars only;
nothing looks ahead. A bar's time is the minute it starts (the 08:30 fifteen-minute bar runs
08:30:00 to 08:44:59).

## Bars

- The runner builds 5-minute and 15-minute bars from the 1-minute store (`--bars 5`,
  `--bars 15`). Both sizes are tested as separate variants.
- The range itself is the same on both sizes (a high is a high however you cut the minutes);
  the bar size only changes what counts as "a close beyond the range".

## Opening range

- **Range** = highest high and lowest low of all bars from 08:30 up to, not including, 08:45.
  On 15-minute bars that is the single 08:30 bar; on 5-minute bars the 08:30, 08:35 and
  08:40 bars.
- **Height (H)** = range high minus range low.
- If any of those bars is missing (data gap at the open), there is no range and no trade that
  day. Counted, not hidden.
- No minimum or maximum range size in version 1 **[grey: a possible later variant skips
  very narrow or very wide ranges]**.

## Entry

- From the 08:45 bar on, the **first** bar that **closes above the range high** gives a long
  signal; the first that **closes below the range low** gives a short signal. Whichever comes
  first wins. A bar's high poking above the range without a close above is not a signal.
- Signal at that bar's close; the engine enters **at market on the next bar's open** with
  2 ticks of slippage (the house rule for every strategy). On 15-minute bars a signal on the
  08:45 bar means an entry at 09:00.
- **Entry window [grey]:** the breakout bar must close by **11:00**, so the latest possible
  entry is the 11:00 bar's open. No breakout by then means no trade that day.
- **One trade per day** in version 1 **[grey]**. A second, opposite-direction trade after a
  stop-out (the "reversal") is a logged variant with a maximum of 2 per day.
- **Geometry guard:** if the breakout bar has already run so far that the estimated entry
  (signal close plus 2 ticks) is at or beyond the target, there is no trade; the move has
  already happened. Counted. **[grey: a stricter version skips any close more than half a
  range height beyond the edge; not in v1]**

## Stop

- Long: **range low minus one tick**. Short: **range high plus one tick**. The stop never
  moves (no break-even, no trailing) in version 1 **[grey]**.
- **ATR-stop variant [grey, logged separately]:** stop = estimated entry minus (for a long)
  0.10 × ATR14, where ATR14 is the average true range of the last 14 completed CME sessions
  (17:00 to 16:00 Chicago). 0.10 is the old Step 1 value, the only ORB stop with a prior
  positive result. Snapped to the tick grid on the safe side. Needs 14 completed sessions,
  so the first three weeks of the data have no ATR trade.

## Target

- Long: **range high plus N × H**. Short: **range low minus N × H**. N = 1 and N = 2 are the
  two logged variants. The target is measured from the edge of the range, not from the fill
  **[grey: the other reading is "N heights above my entry"; this one is the textbook measured
  move and is what the code does]**.
- The target fills at its price once a bar trades one tick through it (engine rule). When a
  bar touches both stop and target the stop is assumed to have hit first (engine rule).
- **No-target variant [grey, logged with the ATR stop]:** hold until the session flatten, the
  exit the old Step 1 rule used.

## Exit if neither hits

- **Session flatten:** the engine closes any open trade at the close of the first bar that
  starts at or after 14:55 Chicago. On 5-minute bars that is the 14:55 bar (closing 15:00);
  on 15-minute bars the 15:00 bar (closing 15:15). The flatten is part of every variant.
- **No time stop.** The engine's 45-bar time stop is switched off for this strategy
  (`max_hold_bars` set to 1000) so the only exits are stop, target and flatten.
- Known limit: on early-close days (the day after Thanksgiving, Christmas Eve) there is no
  14:55 bar; the engine then closes the trade at the next session's first bar. A few days a
  year, same as every other strategy in this repo.

## Costs and sizing (same as every other row in the log)

- $0.75 commission per side, 2 ticks slippage on market and stop fills, target fills at the
  target price. NQ bars stand in for MNQ ($0.50 per tick) before May 2019.
- Research sizing: $500 risk budget, maximum 2 contracts, $5,000 daily loss stop, research
  mode (the permanent account halt is off). These are the settings used for the 15-minute
  sweep-rule rows (25, 43–49) so the dollar figures are comparable. Sizing never filters a
  signal at these settings.
- R is measured against the full risk including costs, as everywhere in the log.

## Random control

- Same bars, same signals, same stop and target distances, but the side is a coin toss and
  the stop and target are mirrored around the signal close (the `random_direction` wrapper
  already used for the VWAP and TJR rules). 8 seeds per variant. If the real rule is no better
  than its flipped twin, the direction of the breakout carries no information.

## Acceptance (frozen before the run)

Worth keeping only if, on NQ 2010–2020 after costs, it beats its random-direction control,
has a profit factor above 1.0 and is positive in most years (6 of 11 or better). Such a rule
has earned the untouched 2021–2026 test, which is **not** run in this chat. Anything less is
closed and the next idea in `IDEAS.md` comes up. Nothing is tuned on 2021–2026.

## Version 1b (8 November 2026, after the sanity run on 2020)

The sanity run (row 50) behaved as specified: 232 trades, entries 09:00–11:00, one a day,
flat at the close. But it showed what measuring the target from the range edge does on
15-minute bars: the breakout bar often closes well past the edge, so by the time we enter the
target is close and the stop is far. Median stop distance 73 points against a median target
distance of 41 points; the reward left at entry was 0.65 of the risk in the typical trade and
as little as 0.02 in the worst. That is the rule as written and it stays as version 1, but it
is not what a trader means by "target one range height", so a second reading is added rather
than a silent change:

- **Version 1b: the target is measured from the estimated entry** (signal close plus 2 ticks
  of slippage): long target = entry + N × H, short target = entry − N × H. Setting
  `orb_target_from=entry`. Everything else is identical to version 1.

Both readings run on both bar sizes with their own random-direction controls (rows 64–71).

## Planned variants (logged as rows 50–71 in `research/research_log.md` before any run)

| Row | Bars | Stop | Target | Trades/day | Note |
|---|---|---|---|---|---|
| 50 | 15m | range | 1×H | 1 | sanity run, NQ 2020 only, trades read by hand |
| 51 | 15m | range | 1×H | 1 | 2010–2020 |
| 52 | 15m | range | 2×H | 1 | 2010–2020 |
| 53 | 5m | range | 1×H | 1 | 2010–2020 |
| 54 | 5m | range | 2×H | 1 | 2010–2020 |
| 55–58 | as 51–54 | mirrored | mirrored | 1 | random-direction controls, 8 seeds each |
| 59 | 15m | 0.10 × ATR14 | 2×H | 1 | the old Step 1 stop |
| 60 | 15m | 0.10 × ATR14 | none, flatten | 1 | the old Step 1 exit |
| 61 | best of 51–54, 64–67 | range | same | 2 | reversal trade allowed after a stop-out |
| 62 | best of 51–54, 64–67 | range | same | 1 | zero costs: does the raw signal have any edge? |
| 63 | 59 or 60 | — | — | 1 | random-direction control, only if either is positive after costs |
| 64 | 15m | range | 1×H from entry | 1 | version 1b |
| 65 | 15m | range | 2×H from entry | 1 | version 1b |
| 66 | 5m | range | 1×H from entry | 1 | version 1b |
| 67 | 5m | range | 2×H from entry | 1 | version 1b |
| 68–71 | as 64–67 | mirrored | mirrored | 1 | random-direction controls, 8 seeds each |

"Best of" means the highest expectancy in R among the eight main runs (51–54, 64–67),
chosen after they run and named in the log row.
