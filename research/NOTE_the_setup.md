# The setup: TJR sequence, graded (rebuilt 26 Nov 2026)

`pvnt_bot/Combined_Strategy.pine`, section "THE SETUP: TJR sequence, graded". Replaces the 18 Nov version.

## Why the 18 Nov version gave bad signals (review of the user's ES/BTC screenshots, 26 Nov)

1. No higher-timeframe bias: longs and shorts anywhere (ES 20 Nov counter-trend long, stopped out).
2. Longs and shorts could be live together (ES 25-26 Nov, BTC 26 Nov ranges).
3. Every chart swing counted as liquidity; levels not ranked.
4. A sweep could pair with an unrelated break up to 20 candles later.
5. Any break counted as the shift (continuation BOS too), and the swing could be minor.
6. Displacement passed on 1 x ATR body OR any gap anywhere after the sweep.
7. Zone was the newest gap, or the 50% line with no gap.
8. Entry filled on a touch; no 1-minute confirmation.
9. "Confluence n/3" counted labels; only sweep + break + 2R were mandatory.
10. Very wide stops were allowed.

## The rules now (the user's answers, 26 Nov)

| # | Mandatory for A | Rule in the code |
|---|---|---|
| M1 | Bias | last BOS/CHoCH (pivot 5, close beyond) on 4H and 1H both agree; both against = no setup; one = B |
| M2 | Meaningful liquidity | ranked untouched pools: 1 PDH/PDL, 2 PWH/PWL, 3 Asia (18:00-02:00), London (02:00-09:30, includes premarket), New York (09:30-16:00) high/low from part 5 sessions, 4 EQH/EQL (two pivots within 0.1 ATR), 5 4H/1H swing, 6 clean 15m swing. Wick through, close back inside within one 15-minute period |
| M3 | Displacement | breaking candle body >= 1 x ATR or move from sweep >= 2 x ATR, AND a fair value gap in the move (middle candle at or after the sweep). No gap = NO TRADE |
| M4 | CHoCH | body close through the 3-candle swing that started the leg into the sweep, within 12 candles |
| M5 | Zone | the displacement gap |
| M6 | Retrace | price must come back into the gap; target first = "Missed: no retrace"; close beyond the sweep = dead; 30 candles = expired |
| M7 | 1m confirmation | reads 1-minute candles: 1m BOS (close past a 1m 2-candle swing formed after the touch) or 1m iFVG |
| M8 | Stop / target | 4 ticks beyond the sweep wick; first ranked untouched pool beyond giving >= 2R; checked again at the actual entry |

Grades: A+ = mandatory + 2 of (OB overlaps the gap, gap in discount/premium, PDL/PDH/PWL/PWH swept, daily agrees).
A = mandatory. B = faded with the missing reason, no alerts (4H/1H don't both agree, stop wider than 3 x ATR).
One setup at a time; a new one the other way cancels a waiting one (never one already in a trade).
Bias table bottom right; ranked pools (ranks 1-4) drawn as dashed lines with names.

Not built: step 8 (trade management). Not backtested. Not yet checked on the chart (TradingView was not connected).
