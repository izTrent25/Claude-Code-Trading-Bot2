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

Ideas not yet tested (log them here before running):

- Opening-range breakout alone, VWAP rule alone (helper's own favourites).
- FVG retest entry instead of next-bar market entry.
- Higher-timeframe bias from structure (swing highs/lows), not candle colour.
- Partial exit + trailing stop instead of fixed 2R.
- 5-minute bars to reduce cost drag.
