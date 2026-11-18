# The setup (your 8-step plan), drawn by the combined indicator (18 Nov 2026)

`pvnt_bot/Combined_Strategy.pine`, section "THE SETUP". No time-of-day filter (you said to leave time out).

| Step | Your plan | What the indicator does |
|---|---|---|
| 1 Sweep | price runs through a marked level and closes back inside on 5m/15m | wick through a part 3 liquidity level (or the previous day's high/low), close back inside on that candle or within 3 candles. A later sweep only replaces it if it goes further |
| 2 Shift | 5m body closes through the last opposing swing (CHoCH) with displacement | within 20 candles, a body close through the most recent small 3-candle swing on the other side; the candle body is at least 1 x ATR(14) or the move left an FVG |
| 3 Zone | displacement FVG, order block (leg before the sweep), equilibrium of sweep-to-BOS swing | all three drawn; "Confluence n/3" counts how many overlap |
| 4 1m trigger | 1m BOS or IFVG in the zone | **not built yet** |
| 5 Entry | limit at the FVG edge or 50% | limit at the FVG 50%; equilibrium if there is no FVG |
| 6 Stop | a few ticks beyond the sweep wick | 4 ticks beyond the sweep's extreme |
| 7 Target | opposite liquidity pool, min 2R | first pool (part 3 level or previous day high/low) giving at least 2R; the next pool is the runner |
| 8 Manage | BE / trail after a new BOS; out by 11 AM | **not built yet** |

The setup is dropped if a candle closes back beyond the swept extreme, if price reaches the target without
retracing to the entry ("Missed: no retrace"), or if the entry does not fill within 30 candles.

Check on MNQ 5m, 17 Nov evening (your pink-line example): Sweep 27,609.25 (17:05, closed back inside on the
15m), CHoCH at 27,433.5 (17:50 close below the 17:25 low), entry FVG 50% 27,474.25, stop 27,610.25,
target 26,841.25 (4.7R). Not backtested.
