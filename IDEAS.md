# Ideas inbox

Drop new trading ideas here, in your own words, before anything is built. One idea per
block. Nothing is deleted; when an idea has been tested, its status changes and the result
links to the research log.

To add one, either edit this file or just tell Claude "new idea: ..." and it gets added here
in the template below.

## How an idea becomes part of the bot

1. **Write it down here** using the template. Rough is fine.
2. **Spec it.** Claude turns it into exact, testable rules in `research/SPEC_<name>.md`:
   what the signal is, where the stop goes, what the target is, when it is allowed to trade.
   You read the spec and say whether that is what you meant.
3. **Log it** as a numbered row in `research/research_log.md` before any run.
4. **Code it** as a strategy class in `pvnt_bot/` with the same `on_bar` interface as the
   others, and register it in `research/run_backtest.py` under `--strategy`.
5. **Sanity-run one year** to catch broken geometry (version 1 of the VWAP idea failed
   here: trades lasted two bars).
6. **Full run on 2010–2020** with the package's costs, plus a random control with the same
   stop, target and session rules.
7. **Write the result** into `research/REPORT_2010_2020.md`, good or bad, and update the
   status below.
8. **Only a survivor** (beats its random control, positive in most years, after costs) goes
   on to the untouched 2021–2026 test. Nothing is tuned against those years.

## Template

```
### <short name>
- Source: (you / Discord helper / a video / a book)
- The idea in one or two sentences:
- Timeframe and market: (e.g. 5-minute MNQ)
- Entry:
- Stop:
- Target / exit:
- Why it might work:
- Status: inbox | spec written | logged | tested — see research_log row N
```

## Backlog

### TradingView MCP tools for backtesting indicators and strategies
- Source: you, 8 November 2026 — https://github.com/tradesdontlie/tradingview-mcp
- The idea: bring the tradingview-mcp toolset into this project and connect it to your
  TradingView account so Claude can run and read backtests of indicators and strategies
  directly in TradingView, instead of only the local Python runner.
- Timeframe and market: whatever the chart is set to
- Why it might work: TradingView's Strategy Tester is a second, independent engine; it
  would let the Pine scripts be compiled and tested without hand-pasting
- Status: **working**. Installed in `tools/tradingview-mcp/`, registered in `.mcp.json`,
  connected to TradingView Desktop 3.5.0 on 8 Nov 2026. First use: the sweep rule's Pine
  script compiled clean and ran in the Strategy Tester (research_log rows 20–22). Known
  Basic-plan limits: one saved script, about one week of one-minute bars, an upgrade popup
  on Save. The tool's own compile button detection picks Save; the icon-only
  Add to chart / Update on chart buttons are clicked by position instead. See
  `tools/README.md` for the network caveat.

### Same ideas on slower bars
- Source: Claude, from the 2010–2020 results
- The idea: both one-minute rules were coin flips before costs. Re-run the sweep rule and
  the VWAP/ORB/FVG rule on 5-minute and 15-minute bars so a win is worth 50–100 points and
  $5 of costs stops mattering.
- Timeframe and market: 5m and 15m NQ (MNQ economics)
- Entry / stop / target: unchanged, bars resampled
- Why it might work: the loss so far is explained by cost-to-target ratio, not the pattern
- Status: **tested** 8 Nov 2026 (research_log rows 24–33). Bigger bars shrink the loss
  (sweep rule −0.25R at 1m → −0.07R at 15m, PF 0.96, 5 of 11 years positive) and the rule
  beats random by ~0.1R at every size, but nothing crosses break-even after costs. 30m and
  60m bars run out of session before a 2R target. The VWAP/ORB/FVG rule is worse at every
  size and is retired. The runner now has `--bars N`.

### TJR liquidity sweep (your own paper-traded method)
- Source: you, 8 Nov 2026, from a detailed write-up of TJR's method
- Spec: `research/SPEC_tjr.md`; code: `pvnt_bot/tjr.py` (Python, 1-minute trigger) and
  `pvnt_bot/TJR_Research.pine` (TradingView, 5-minute chart, limit entry; compiles clean)
- Status: **retired** 8 Nov 2026 by your call. Written as strict rules the method almost
  never fires: a handful of trades a year across every variant, far too few to prove or
  disprove an edge (research_log rows 34–42). The files stay for the record.

### Exit rules for the 15-minute sweep rule
- Source: Claude, from the slower-bars result
- The idea: the fixed 2R target is reached only 14–20% of the time at any bar size, and on
  30m+ bars most trades die at the 14:55 flatten. Test, as separate hypotheses: 1R target,
  a trailing stop, a partial at 1R, and exiting at the session close by design.
- Timeframe and market: 15m NQ (MNQ economics)
- Status: **tested** 8 Nov 2026, research_log rows 43–49. Seven exits, all within noise of
  zero (PF 0.95–1.04). The exit was never the problem. The sweep rule is closed.

### Opening-range breakout on its own
- Source: Discord helper ("I mainly stick with ORB, VWAP, EMAs"); also the old Step 1 work
  in the backup folder, where an ORB-with-ATR-stop rule was the best of 32 ideas on
  2010–2020 (+$42.9k on one NQ contract, 7 of 11 years) but was never checked against a
  random control or honest MNQ costs.
- The idea: trade the first close beyond the 15-minute opening range, stop at the other
  side of the range (or an ATR multiple), target one or two range heights. No FVG, no VWAP.
- Timeframe and market: 5m and 15m NQ
- Why it might work: simplest version of what the helper says he actually trades, and the
  only idea in the old log with a multi-year positive result
- Status: inbox, **next up**

### Does "above VWAP" predict anything?
- Source: Claude
- The idea: not a strategy, a measurement. For every bar at 09:00, 10:00, 11:00 Chicago,
  record whether price is above or below session VWAP and what it does over the next
  30 and 60 minutes. If there is no tilt, VWAP bias filters are dead for day trades.
- Status: **tested** 8 Nov 2026 (research_log row 23, `research/vwap_measure.py`). No tilt
  at any checkpoint or horizon; every bootstrap range straddles zero. VWAP-bias filters are
  dead for day trades.

### FVG retest entry instead of a market entry (for the sweep rule)
- Source: Discord helper's flow
- The idea: after the sweep and displacement, wait for price to come back into the fair
  value gap the displacement left, and enter there with a tighter stop.
- Status: inbox

### Higher-timeframe bias from structure, not candle colour
- Source: Discord helper's flow ("HTF bias 90m / 15m")
- The idea: define bias from 15-minute swing highs and lows (higher highs and higher lows
  = long bias) rather than the last candle's colour, and only take trades with the bias.
- Status: inbox

### Partial exits and a trailing stop
- Source: Discord helper's flow
- The idea: take half at 1R, move the stop to break-even, trail the rest. Test as its own
  hypothesis; the spec warns never to assume this helps.
- Status: inbox

### TradingView alerts from a Pine script
- Source: you (notifications are the goal)
- The idea: once any rule survives, maintain a Pine v6 version and set TradingView alerts
  to your phone or a Discord webhook. The sweep rule already has a Pine file
  (`pvnt_bot/PVNT_SMC_Research.pine`, uncompiled).
- Status: waiting for a rule worth alerting on
