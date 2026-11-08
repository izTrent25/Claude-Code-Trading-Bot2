# Research log

Rule: log every variant before or as it is tested, never delete a row, count versions.
Development window is 2010–2020 (NQ bars as MNQ proxy). 2021+ is untouched.

| # | Date | Variant | Why | Command / tag | Result (net, PF, expectancy R, years positive) | Verdict |
|---|---|---|---|---|---|---|
| 1 | 2026-11-07 | Package rebuild sanity: NQ 2020 only, research mode | Timing run and first look | `timing_2020` | 461 trades, −$1,396, PF 0.86, −0.11R | one year, loses |
| 2 | 2026-11-07 | Same rule on real MNQ 2020 | Check NQ is a fair stand-in for MNQ | `proxy_mnq_2020` | 467 trades, −$1,670, PF 0.84, −0.11R | proxy is fair |
| 3 | 2026-11-07 | Package defaults, account mode (permanent halt on), 2010–2020 | How the shipped package behaves | `smc_account_2010_2020` | halted 2010-11-09 after 233 trades, −$1,676, PF 0.45 | fails in 5 months |
| 4 | 2026-11-07 | Package defaults, research mode, 2010–2020 | Full-history statistics | `smc_research_2010_2020` | 5,670 trades, −$36,039, PF 0.62, −0.25R, 0 of 11 years | loser every year |
| 5 | 2026-11-07 | Zero commission and slippage, research mode | Does the signal have any raw edge? | `smc_zerocost_2010_2020` | 5,723 trades, −$2,363, PF 0.97, −0.03R, 3 of 11 | coin flip before costs |
| 6 | 2026-11-07 | use_context=true (15m + 90m candle direction filter) | The package's one optional filter | `smc_context_2010_2020` | 738 trades, −$4,517, PF 0.63, −0.23R, 2 of 11 | fewer trades, same quality |
| 7 | 2026-11-07 | Random entries, same stop/target/session/risk, 12 seeds, matched to 5,670 trades | Baseline: is the rule better than chance? | `random_research_2010_2020` | median 4,746 trades, −$30,242, PF 0.53, −0.34R, 0 of 12 seeds profitable | rule beats random by ~0.09R/trade but both lose |

| 8 | 2026-11-08 | VWAP + 15m ORB + FVG/OB pullback, v1 per `SPEC_vwap_orb_fvg.md`: target 1.5R, risk $20 (1% of $2,000 DD), 60-bar hold, entries 08:45–14:30 | The helper's page-one prompt, built as written | `vof_rr15_risk20` | pending | pending |
| 9 | 2026-11-08 | Same, target 1.0R | "at least 1R" read literally | `vof_rr10_risk20` | pending | pending |
| 10 | 2026-11-08 | Same, target 2.0R | nearby target | `vof_rr20_risk20` | pending | pending |
| 11 | 2026-11-08 | Same as row 8 but risk $50 | How much does the $20 budget reject? | `vof_rr15_risk50` | pending | pending |
| 12 | 2026-11-08 | Random-direction control of row 8: identical signals and stop distance, side flipped by coin toss, 8 seeds | Does the VWAP/ORB direction call add anything? | `vof_randdir_rr15_risk20` | superseded by row 18 (v2) | not run on v1 |
| 13 | 2026-11-08 | v1 sanity run, NQ 2020 only | Check the rule behaves before the long run | `vof_sanity_2020` | 11,163 signals, 767 trades, 2.2 bars/trade, −$3,559, PF 0.53, −0.35R | geometry too tight; led to v2 |
| 14 | 2026-11-08 | v1 full run 2010–2020 (rows 9–11 dropped; v1 is superseded) | Keep the v1 record honest | `vof_v1_rr15_risk20` | 90,804 signals, 8,045 trades, −$42,996, PF 0.42, −0.42R, 31% wins, 0 of 11 years | tick-sized geometry; dead |
| 15 | 2026-11-08 | **v2** per spec: gap ≥ 0.3× avg range, stop floor 1.0× avg range, close-beyond-zone; target 1.5R, risk $20 | Volatility-aware geometry | `vof_v2_rr15_risk20` | 66,798 signals, 7,663 trades, −$37,696, PF 0.49, −0.34R, 33.5% wins, 11 bars/trade, DD $37,721, 0 of 11 years | loses; primary |
| 16 | 2026-11-08 | v2, target 1.0R | "at least 1R" read literally | `vof_v2_rr10_risk20` | 66,798 signals, 7,674 trades, −$36,862, PF 0.44, −0.33R, 41.6% wins, 8 bars/trade, 0 of 11 years | loses |
| 17 | 2026-11-08 | v2, target 2.0R | nearby target | `vof_v2_rr20_risk20` | 66,798 signals, 7,644 trades, −$37,555, PF 0.53, −0.34R, 28.6% wins, 13.5 bars/trade, 0 of 11 years | loses |
| 18 | 2026-11-08 | v2, risk $50 | How much does the $20 budget reject? | `vof_v2_rr15_risk50` | 7,991 trades, −$48,707, PF 0.58, −0.33R, 1.92 contracts avg, 0 of 11 years | bigger size, bigger loss; budget was not the problem |
| 19 | 2026-11-08 | v2 random-direction control, 8 seeds | Does the VWAP/ORB direction call add anything? | `vof_v2_randdir` | 8 seeds (first run hung, relaunched): median −$40,834, PF 0.46, −0.37R, 32% wins, 0 of 8 profitable | real rule −0.34R: direction call worth ~0.03R, i.e. nothing |

| 20 | 2026-11-08 | TradingView Strategy Tester, sweep rule Pine script as shipped ($50 budget), MNQ1! 1-minute, Basic plan history 2–6 Nov 2026 | First TradingView-side run via the tradingview-mcp tool | TradingView, no tag | compiled clean, 0 trades | $50 budget rejects almost every 2026 trade at MNQ ≈ 27,000 |
| 21 | 2026-11-08 | Python engine on MNQ 2026 (Jan–4 Nov) at $50 and $500 budgets | Explain row 20 | `diag_mnq2026_risk50`, `diag_mnq2026_risk500` | $50: 3,783 signals, 159 trades, +$90, PF 1.02; $500: 460 trades, −$7,542, PF 0.80 | confirms the budget explanation; 2026 is still a loser at size |
| 22 | 2026-11-08 | TradingView Strategy Tester, same Pine with $500 budget, 2–6 Nov 2026 | Does the tester produce trades once sized? | TradingView, no tag | 13 trades, +$990, PF 1.98, 54% wins, max DD $615 | pipeline works; 13 trades in 5 days is not evidence of anything |

| 23 | 2026-11-08 | VWAP measurement: at 09:00, 10:00, 11:00, 13:00 Chicago, is close above or below the session VWAP (anchored 08:30), and what is the move over the next 30 and 60 minutes? NQ 2010–2020, day-bootstrapped | Is a VWAP bias filter worth anything? | `research/vwap_measure.py` → `results/vwap_measure/` | 21,500 checkpoints; above-minus-below next-hour move is +0.01 to +0.18 average-bar-ranges, every 90% range straddles zero, 5–8 of 11 years agree | no usable tilt; VWAP side is not a direction signal |
| 24 | 2026-11-08 | Sweep rule on 5-minute bars, research mode, $500 risk / $5,000 daily so sizing never filters signals, other settings unchanged (20-bar lookback, 5-bar confirm, 2R, 45-bar hold) | Was it the timeframe, not the pattern? | `smc_5m_2010_2020` | 2,006 trades, −$9,437, PF 0.89, −0.13R, 38% wins, 2 of 11 years | better than 1m, still loses |
| 25 | 2026-11-08 | Sweep rule on 15-minute bars, same | same | `smc_15m_2010_2020` | 934 trades, −$1,952, PF 0.96, −0.07R, 43% wins, 5 of 11 years | near break-even; least bad so far |
| 26 | 2026-11-08 | Random-entry control for row 24 (5m), 12 seeds | baseline | `random_5m_2010_2020` | 12 seeds, median 1,599 trades, −$10,445, PF 0.79, −0.21R, 0 profitable | rule beats random by ~0.09R at 5m |
| 27 | 2026-11-08 | Sweep rule 5m, zero costs | raw signal on 5m | `smc_5m_zerocost` | 2,011 trades, +$3,721, PF 1.05, −0.01R, 5 of 11 years | zero edge before costs, same as 1m |
| 28 | 2026-11-08 | VWAP/ORB/FVG v2 on 5-minute bars, $500 risk / $5,000 daily, other settings unchanged | same question for strategy 2 | `vof_5m_2010_2020` | 4,532 trades, −$30,087, PF 0.76, −0.22R, 0 of 11 years | loses |
| 29 | 2026-11-08 | VWAP/ORB/FVG v2 on 15-minute bars | same | `vof_15m_2010_2020` | 1,260 trades, −$4,999, PF 0.88, −0.12R, 2 of 11 years | loses less, still loses |
| 30 | 2026-11-08 | Random-direction control for row 28 (5m), 8 seeds | baseline | `vof_5m_randdir` | 8 seeds, median −$32,162, PF 0.74, −0.23R, 0 profitable | direction call still worth nothing |

| 31 | 2026-11-08 | Sweep rule on 30-minute bars, same settings as row 24 | Does the 1m→5m→15m improvement continue? | `smc_30m_2010_2020` | 658 trades, −$3,094, PF 0.90, −0.03R; 501 of 658 exits were the 14:55 session flatten | day too short for a 2R target on 30m bars |
| 32 | 2026-11-08 | Sweep rule on 60-minute bars, same | same | `smc_60m_2010_2020` | 209 trades, −$1,509, PF 0.76, −0.04R; 183 of 209 session flattens | same; not a pattern test |
| 33 | 2026-11-08 | Random-entry control for row 25 (15m), 12 seeds | Does the near-break-even 15m result beat chance? | `random_15m_2010_2020` | 12 seeds, median 795 trades, −$7,244, PF 0.75, −0.18R, 0 profitable | rule beats random by ~0.11R at 15m |

| 34 | 2026-11-08 | **TJR v5** per `SPEC_tjr.md`: structure daily bias, 5m sweep of PDL/Asia/London/pre-market, 5m displacement shift, 5m FVG zone, 1m BOS trigger, stop behind sweep, nearest opposite pool ≥2R, 3/day, 2-loss stop; $500 risk | The user's own paper-traded method, built to their write-up | `tjr_v5_2010_2020` | 9 trades in 11 years, −$683, PF 0.24, −0.14R; 6 of 9 exits were the 11 AM flatten | almost never fires; retired |
| 35 | 2026-11-08 | TJR v5 with bias off (both directions allowed) | Does the daily bias add anything? | `tjr_v5_nobias` | 29 trades, −$544, PF 0.62, −0.09R, 3 of 11 years; 25 of 29 flattened at 11 AM | bias is not what limits it |
| 36 | 2026-11-08 | TJR v5-limit: same setup, entry by limit at 50% of the 5m gap instead of the 1m trigger (the entry the Pine version uses) | Compare entry methods; parity with TradingView | `tjr_v5_limit` | 145 proposals, 75 fills, −$1,098, PF 0.66, −0.06R, 5 of 11 years; targets hit 5 times | most trades, still loses |
| 37 | 2026-11-08 | TJR v5 random-direction control, 8 seeds | baseline | `tjr_v5_randdir` | 8 seeds on 9 trades: median −$41, −0.00R, 2 of 8 profitable | too few trades for a control to mean anything |
| 38 | 2026-11-08 | TJR v5 at the $20 budget (1% of $2,000) | What the real sizing does | `tjr_v5_risk20` | not run | moot: the rule barely fires |
| 39 | 2026-11-08 | TJR Pine strategy compiled in TradingView on MNQ1! 5-minute | Visibility on real charts; tester as second opinion | TradingView | compiled clean after 5 Pine fixes (tuple ternary, comma declarations, bit mask, indexed call, shadowed name); added to the chart, then removed at the user's request | retired with the rest |
| 40 | 2026-11-08 | TJR v5 funnel counts on NQ 2020 and 2015 (stage counters added to the strategy) | Why only 2 signals a year? | `tjr_funnel_2020`, `tjr_funnel_2015` | 191 sweeps → 50 shifts (124 fail displacement) → 34 gaps → 20 retraces → 6 triggers (12 die on a close through the gap) → 2 proposals | my "close through the gap" cancel is not TJR's rule; displacement threshold is the harshest grey filter |
| 41 | 2026-11-08 | **TJR v5.1**: zone invalidation = price trades back beyond the swept extreme (per the write-up), everything else as v5 | Correct my grey choice to his stated rule | `tjr_v51_2010_2020` | 34 trades, −$1,917, PF 0.25, −0.27R, 2 of 10 years; 21 flattened at 11 AM | loses |
| 42 | 2026-11-08 | TJR v5.1 with displacement 0.5 × avg range instead of 0.8 | Grey threshold sensitivity | `tjr_v51_disp05` | 37 trades, −$1,927, PF 0.25, −0.25R | threshold is not the issue |

| 43 | 2026-11-08 | 15m sweep rule, target 1.0R (base: row 25 settings, $500 risk, $5,000 daily) | Exit experiments: the 2R target is reached only 14–20% of the time | `smc_15m_rr10` | 949 trades, +$1,737, PF 1.04, −0.05R, 47.5% wins, 5 of 11 years | best of the set and still ~zero: $1.83 a trade |
| 44 | 2026-11-08 | 15m sweep rule, target 1.5R | same | `smc_15m_rr15` | 943 trades, −$298, PF 0.99, −0.06R | zero |
| 45 | 2026-11-08 | 15m sweep rule, target 3.0R | same | `smc_15m_rr30` | 933 trades, −$2,185, PF 0.95, −0.07R; target hit 27 times | zero |
| 46 | 2026-11-08 | 15m sweep rule, no target: stop, 45-bar time stop or 14:55 flatten only | same | `smc_15m_notarget` | 933 trades, −$1,662, PF 0.96, −0.07R, 6 of 11 years | zero |
| 47 | 2026-11-08 | 15m sweep rule, 2R target plus break-even: stop to entry once +1R has printed (applied from the next bar) | same | `smc_15m_be1` | 937 trades, −$1,055, PF 0.98, −0.06R, avg loss shrinks to −$74 | zero |
| 48 | 2026-11-08 | 15m sweep rule, no target, break-even at +1R then trail the stop behind the last 3 completed bars | same | `smc_15m_trail3` | 949 trades, +$529, PF 1.01, −0.06R | zero |
| 49 | 2026-11-08 | 15m sweep rule, 2R target plus the same break-even and trail | same | `smc_15m_rr20_trail3` | 949 trades, +$455, PF 1.01, −0.06R, 4 of 11 years | zero |

Ideas not yet tested (log them here before running):

- Opening-range breakout alone, VWAP rule alone (helper's own favourites).
- FVG retest entry instead of next-bar market entry.
- Higher-timeframe bias from structure (swing highs/lows), not candle colour.
- Partial exit + trailing stop instead of fixed 2R.
- 5-minute bars to reduce cost drag.
