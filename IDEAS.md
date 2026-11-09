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
- Status: **tested and closed** 8 Nov 2026 (research_log rows 50–72; report section
  "Strategy 3"). Twelve variants on 5m and 15m bars, targets 1× and 2× the range height
  measured from the edge or from the entry, range stop or 0.10 × ATR stop, reversal allowed,
  zero costs: every one loses in 10 or 11 of 11 years (best PF 0.89, −0.07R) and none beats
  its random-direction twin. The old +$42.9k does not survive honest costs. Spec
  `research/SPEC_orb.md`, code `pvnt_bot/orb.py`, Pine `pvnt_bot/ORB_Research.pine` (written,
  not compiled or loaded at your request).

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
- Status: **folded into "Strategy 5: PVNT flow entry"** below (8 Nov 2026)

### Higher-timeframe bias from structure, not candle colour
- Source: Discord helper's flow ("HTF bias 90m / 15m")
- The idea: define bias from 15-minute swing highs and lows (higher highs and higher lows
  = long bias) rather than the last candle's colour, and only take trades with the bias.
- Status: inbox

### Partial exits and a trailing stop
- Source: Discord helper's flow
- The idea: take half at 1R, move the stop to break-even, trail the rest. Test as its own
  hypothesis; the spec warns never to assume this helps.
- Status: **folded into "Strategy 5: PVNT flow entry"** below (8 Nov 2026), as exits in thirds

### TradingView alerts from a Pine script
- Source: you (notifications are the goal)
- The idea: once any rule survives, maintain a Pine v6 version and set TradingView alerts
  to your phone or a Discord webhook. The sweep rule already has a Pine file
  (`pvnt_bot/PVNT_SMC_Research.pine`, compiles clean; a $500-budget copy ran in the
  Strategy Tester on 8 Nov 2026).
- Status: waiting for a rule worth alerting on

## From the TradingView hunt (8 November 2026)

Searched TradingView's public strategy library (Popular and Editors' picks, filtered to
strategies) for anything "very profitable". Honest finding first: TradingView does not rank
strategies by real profit, the Editors' picks reward code quality not edge, and a Strategy
Tester screenshot proves nothing (no slippage, tiny samples, repainting, curve-fitting on a few
months). Only one idea found there rests on independent, long-sample, cost-inclusive evidence.
Everything below is an inbox entry, not a result; each must pass the same 2010–2020 test with
a random control before it is believed.

### Noise-area intraday momentum (Zarattini, Aziz & Barbon 2024) — strongest candidate
- Source: the paper "Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF
  (SPY)", Swiss Finance Institute paper 24-97, revised 3 Feb 2025; found through two independent
  open-source NQ builds on TradingView ("$$$ INTRADAY MOMENTUM DIGGA $$$" by PINEDIGGA and
  "Xiznit Noise Band Momentum").
- The idea: most of the day the index just makes noise. Measure, for each half hour of the
  session, how far price typically moves from the open by that time (average over the last 14
  days). That gives a funnel-shaped "noise area" that is narrow at the open and wide by the
  close. Only when price is outside the funnel is there real buying or selling pressure; follow
  it until the close.
- Timeframe and market: checked only at HH:00 and HH:30 New York (so 5m or 15m bars work),
  09:30–16:00 New York, flat at the close. Paper is on SPY; the TradingView builds are on NQ/MNQ.
- Entry: at a half-hour mark, long if the close is above the upper band (and above session
  VWAP in the builds), short if below the lower band (and below VWAP). Upper band = max(today's
  open, yesterday's close) × (1 + average move to that time); lower band = min(open, yesterday's
  close) × (1 − average move). Fill at the next bar's open.
- Stop: trailing, the higher of the upper band and VWAP for longs (mirror for shorts), checked
  only at the half-hour marks. The base version uses the opposite band and reverses.
- Target / exit: none; hold to the close or the trailing stop. Re-entries allowed the same day.
- Why it might work: the time-of-day-adaptive band is the structurally new ingredient (nothing
  we have tested adapts to the clock), the hold-to-close exit lets the few big trend days pay,
  and the evidence is unusually good for a public idea: on SPY 2007–2024 after $0.0035/share
  commission and $0.001 slippage the paper reports Sharpe 0.61 for the base version, 1.24 with
  the VWAP trailing stop, 1.33 with volatility-targeted sizing (19.6% a year, 25% max drawdown,
  43% daily hit rate, about 1.8 trades a day), only two losing years in seventeen (2016 −12.8%,
  2017 −6.9%) and a profit in all ten of the S&P's worst quarters.
- Red flags to carry into the test: the PINEDIGGA NQ build, run by its author on CME NQ 1-minute
  data with a 1.5-point cost per trade, shows 2010–2017 flat to negative, profit from 2018 on
  (2018 +1,695 pt, 2019 −209, 2020 +1,084, 2021 +1,208, 2022 +2,481, 2023 +1,886, 2024 +1,922),
  profit factor 1.27 over 2010–2026 with 36% winners, and "without the 5 best trades of each year,
  every tested period is negative". So on our 2010–2020 window it may come out marginal, and the
  MNQ cost drag is larger than the paper's. The paper's headline number also leans on 4× leverage
  sizing, which we would not use.
- Status: **inbox, recommended first test**. Spec would need: band lookback 14 days, half-hour
  grid, VWAP filter on/off, stop variant (opposite band vs current band+VWAP), re-entries
  allowed, flat at 15:00 Chicago, fixed 1–2 MNQ, our usual costs, random-direction control.

### UT Bot (ATR trailing line) as a strategy
- Source: QuantNomad's open-source "UT Bot Alerts", the most reused signal engine on
  TradingView; several open-source strategy wrappers (e.g. "UT Bot Strategy with Risk
  Management [TradeIQ]").
- The idea: an ATR-based trailing line (key value × ATR(period)) follows price; a close above the
  line is a buy, a close below is a sell; the position flips on the opposite signal.
- Timeframe and market: any; for us 5m or 15m NQ during the session with a flatten at the close.
- Entry: close crosses the trailing line. Stop: the line itself (or an ATR multiple).
  Target: none, exit on the opposite signal or the close.
- Why it might work: pure trend-following with an adaptive stop; it is what thousands of people
  actually trade, so it deserves an honest number.
- Red flags: no published long-sample test anywhere; on intraday NQ it is close to a moving-average
  cross, which the old Step 1 log found to lose. Expect a coin flip; test because it is cheap.
- Status: inbox

### VWAP-band mean reversion with a volume spike (NQ Phantom Scalper Pro)
- Source: open-source TradingView strategy by TradeManager_PRO, July 2025, built for NQ.
- The idea: fade touches of a VWAP standard-deviation band when volume spikes, during
  09:30–12:00 and 14:00–16:00 New York, exit back at VWAP or at a fixed target, ATR stop.
- Why it might work: it is the opposite bet to everything we have tested (fading, not following),
  and the VWAP measurement in row 23 only ruled out VWAP as a direction filter, not as a
  mean-reversion anchor.
- Red flags: no numbers published at all, many tunable knobs (band multiplier, volume multiplier,
  ATR multiple), and "scalping" on 1–5 minute bars is exactly the cost regime that killed
  strategies 1 and 2. Would need a 15m version and the random control.
- Status: inbox

### One Percent A Week (TASC, March 2026) — different horizon
- Source: Dion Kurczek, TASC "Trading Snapbacks in a Leveraged ETF"; open-source Pine by
  PineCodersTASC (an Editors' pick). Written for TQQQ, a 3× Nasdaq-100 fund.
- The idea: note Monday's open; buy a 1% dip from it with a limit order; from the next day sell
  at +1% from the fill; if the trade is ever 0.5% under water, exit at break-even instead; flat at
  Friday's close. Long only, one trade a week.
- Why it might work: Nasdaq-100 pullbacks inside uptrends tend to snap back; tiny rule set, hard
  to over-fit.
- Red flags: it is a swing rule, not day trading, so it needs multi-day holds that our engine does
  not have (it flattens every session); on NQ the 1% figures would need scaling; the article
  itself says it may not beat buy-and-hold. Keep for later, when the engine can hold overnight.
- Status: inbox, parked

### SuperTrend strategy (KivancOzbilgic), pasted by you
- Source: you, 8 Nov 2026, the Pine v4 "SuperTrend STRATEGY" from TradingView (the most-used one)
- The idea: an ATR × 3 band trails price; a close through the band flips the trend and the
  position; always in the market, no stop, no target.
- Timeframe and market: you asked for 1m, 5m and 15m NQ (MNQ costs), 2010–2020
- Status: **tested and closed** 8 Nov 2026 (research_log rows 73–83; report section
  "Strategy 4"). As published and as a day-session version, on all three bar sizes: every run
  loses (15m −$25.6k, 5m −$62k, 1m −$414k for one contract), the coin-toss twins match the real
  rule, and with zero costs it is flat (PF 0.99). Spec `research/SPEC_supertrend.md`, code
  `pvnt_bot/supertrend.py`. The engine gained `hold_overnight`, `intrabar_stop` and a strategy
  exit hook for it.

### Looked at and skipped
- ORB variants ("Crazy ORB V2.1 NQ", "EP001 15m Opening Range Audit", "Quick Flip Scalper"):
  the plain ORB is closed (rows 50–72); filters on a zero-edge signal are not a new idea.
- Liquidity-sweep and structure variants ("Magnet Structure", "Heat Sweep", "Sweep + FVG
  Reversal"): the sweep family is closed (rows 1–49).
- "Swing Exhaustion Fade | Learned Odds": the rule is learned from the chart it is loaded on,
  so its tester results are fitted by construction.
- "Midnight Express", "Overnight MNQ Synapse Scalper": proprietary rules and martingale sizing.
  Not testable, and martingale is how accounts die.
- Editors' picks for strategies are mostly templates and tools (trailing-stop examples, report
  generators, 3Commas bot wrappers), not edges.

## Five evidence-backed candidates (8 November 2026, at your request)

You asked for five strategies that were profitable in 2010–2020 and are not coincidence. Honest
framing first: no website publishes a verified NQ 2010–2020 winner with costs. The best filter
for "not coincidence" is a long academic sample plus a real economic reason the pattern exists,
so these five were chosen on that basis, each structurally different from the others and from
everything closed so far. The old Step 1 folder (4 Nov) also ran its own random checks on 1 NQ
contract with looser costs; where it tested a cousin of an idea, the number is given as a hint,
not as evidence. Every one of these still has to pass our 2010–2020 test with the coin-toss
control before it is believed. Rows start at 85.

### 1. Overnight drift at the European open
- Source: Boyarchenko, Larsen & Whelan, "The Overnight Drift", Review of Financial Studies
  36(9), 2023 (NY Fed Staff Report 917). Cousin tested in Step 1 as `european_open_drift`.
- The idea: S&P 500 futures earn most of their overnight return in the hour before Europe
  opens, 02:00–03:00 New York = **01:00–02:00 Chicago**. Long at 01:00, flat at 02:00, every
  weekday. Mechanism: dealers who absorbed selling during the US day unload inventory when
  European liquidity arrives; the drift is strongest after down days.
- Evidence: 1998–2018 S&P futures, about 3.6% a year gross from that one hour, highly
  significant. Step 1's 02:00–06:00 NY version: +$30,396 on 1 NQ, 6 of 11 years, passed its
  random check (0.0% of random runs beat it), **but 2020 alone was +$33,929**.
- Red flags: the NY Fed itself reported in July 2026 that the drift was **flat in 2021–2025**; the
  edge is about 1.4 basis points a night, and MNQ costs are about 1.75 points, roughly the same
  size at NQ 10,000, so after costs on a micro it may be nothing; without 2020 the Step 1 cousin
  was negative. Long only, so partly just owning a rising market.
- Fit: flat within the Globex session, so a prop account that allows overnight-session trading
  could run it. Engine: entry window 01:00–02:00 CT, flatten 02:00; control = the same one-hour
  long at random other hours of the night.
- Status: **tested and closed** 9 Nov 2026 (rows 97–103). The hour is real: +$4,066 and 10 of 11
  years before costs, $2,700 better than a random hour. After costs −$5,388: 0.75 point a night
  against 1.75 points of costs.

### 2. Last-half-hour momentum from hedging flows
- Source: Baltussen, Da, Lammers & Martens, "Hedging Demand and Market Intraday Momentum",
  Journal of Financial Economics 142(1), 2021; Gao, Han, Li & Zhou, "Market Intraday Momentum",
  JFE 129(2), 2018. Cousin tested in Step 1 as `last_half_hour_momentum`.
- The idea: at **14:30 Chicago** (15:30 New York), go with the day's direction, measured from
  yesterday's close, and exit at the 15:00 close. Mechanism: leveraged ETFs (TQQQ and SQQQ are
  enormous on the Nasdaq) and option market makers must trade with the day's move into the
  close to rebalance; the effect is strongest when they are short gamma.
- Evidence: 60+ futures markets, 1974–2020, "economically and statistically highly significant",
  stronger on big-move days; the 2018 paper on SPY 1993–2013 found the same with an
  out-of-sample R² of about 1.2%.
- Red flags: a small effect per day; Step 1's version (first half-hour and 15:00–15:30 both
  agreeing) made +$8,507 on 1 NQ but was positive only in 2018 and 2020; costs of 1.75 points
  against a typical 30-minute move of 10–20 points is a tight fit on a micro.
- Fit: a pure day trade, one a day, 30 minutes long. Engine: signal at the 14:30 bar, flatten
  15:00; a size filter (only on days whose move so far is above the median) is the natural
  variant the papers suggest.
- Status: **tested and closed** 9 Nov 2026 (rows 91–96). Real but small: +$4,121 and 7 of 11 years
  before costs, beats all 8 seeds; −$5,074 after costs.

### 3. Opening gap fade
- Source: practitioner statistics (ES opening gaps fill during the day roughly 70–76% of the
  time, mypivots and TradeFlightPlan, small undocumented samples); no peer-reviewed paper found.
  Tested in Step 1 as `gap_fade` v9 and v16.
- The idea: if the 08:30 Chicago open is at least 0.2% away from yesterday's 15:00 close, trade
  back toward that close from the 08:31 bar; target the close, stop one gap-size beyond the open,
  flat by 10:30. Mechanism: the overnight Globex session is thin, so the opening price is often
  an overshoot that the real cash auction reverses.
- Evidence: Step 1, 2010–2020, 1 NQ: 1,764 trades, +$36,045, profit factor 1.10, **8 of 11 years
  positive**, passed its random check (0.2% of random runs beat it, 0.8% of direction-flipped
  ones). This is the only idea on this list with an NQ-specific multi-year result in our window.
- Red flags: 2018 and 2020 supplied about $33,000 of the $36,000 and 2019 lost $10,945; the top
  five trades were $23,000 of it; the Step 1 engine's fills and costs are not ours (1 NQ, not
  MNQ), so the honest number could be smaller or negative.
- Fit: a morning day trade. Engine: needs yesterday's 15:00 close, an absolute target and a
  10:30 flatten, all available; control = same days, direction flipped.
- Status: **tested and closed** 9 Nov 2026 (rows 85–90). Real: +$5,950 and 9 of 11 years before
  costs, beats all 8 seeds. After costs +$393 in eleven years, 5 of 11 years: fails.

### 4. Turn of the month
- Source: Lakonishok & Smidt (1988); McConnell & Xu (2008, holds 1987–2005 in the US and 30+
  countries); Etula, Rinne, Suominen & Vaittinen, "Dash for Cash", Journal of Finance 2020;
  Carcano & Tornero on S&P 500 futures, where it is the one calendar effect that stays
  significant. Open-source TradingView scripts exist ("Turn of the Month Strategy [Honestcowboy]").
- The idea: long from the close of the second-to-last trading day of the month to the close of
  the third trading day of the next, flat the rest of the time. Mechanism: pension and payroll
  money arrives at month end and gets invested; institutions sell before it to raise cash and the
  market recovers after.
- Evidence: since 1926 those few days carried most of the market's return; Quantpedia's
  indicative figure is 7.2% a year, Sharpe 1.04, with a fraction of the exposure.
- Red flags: 12 trades a year, so 132 in our window, a small sample; multi-day holds, so **not
  for a prop account**; long only in a decade that rose, so the control must be random 5-day
  holds at other times of the month.
- Fit: swing, not day trading. Engine: `hold_overnight` now exists, so it can be tested.
- Status: **tested, PASSES the frozen pass mark** 9 Nov 2026 (rows 104–108): 121 trades, +$5,731,
  PF 1.74, 8 of 11 years, above every random-days seed. Caveats: 2020 is two thirds of it, the
  edge over random four-day holds is about $3,300 in eleven years, and it holds overnight. **Has
  earned the 2021–2026 test; not run.** Your call.

### 5. Noise-area intraday momentum
- Source: Zarattini, Aziz & Barbon 2024, already written up above (TradingView hunt) and
  specced in `research/SPEC_noise_momentum.md`, unconfirmed.
- Evidence and red flags: 17 years of SPY after costs, two losing years; the public NQ build
  shows 2010–2017 flat and profit from 2018 on. The one idea here that adapts to the time of day.
- Fit: day trade, half-hour checks.
- Status: **tested** 9 Nov 2026 (rows 109–116). The strongest intraday signal: +$11,376 and 9 of 11
  years before costs, beats all 8 seeds by $6,000–$12,800. After costs +$3,596, PF 1.10, but only
  3 of 11 years positive: **fails the years test**. The one worth attacking on its cost line.

### A sixth, if you want it
The old Step 1's best result, `orb5_atr` v28 (+$42,903 on 1 NQ, 7 of 11 years, passed its random
check at 0.2%), is **not** the range breakout we closed in rows 50–72. It follows the colour of
the first 5-minute candle at 08:35 Chicago, stop one tenth of the 14-day average range, hold to
the close, from Zarattini & Aziz 2023 "Can Day Trading Really Be Profitable?" (QQQ/TQQQ
2016–2023). **Tested and closed** 9 Nov 2026 (rows 117–120): +$7,276 and 9 of 11 years before
costs, −$2,318 after; 81% of trades stopped.

## Strategy 5: PVNT flow entry (queued 8 November 2026)

- Source: you, via the tracker chat: Perky's gold screenshot (5 Oct 2026) and 7-second video,
  plus the PVNT Academy guide, all read into `notes/PVNT_ACADEMY_GUIDE.md`. The guide has no
  rules; the indicator's logic is proprietary and not in any file. What is extractable is the
  trade shape.
- The idea: a structure shift (a close through the last lower high, with displacement) leaves a
  fair value gap; enter on the first return into the gap with a resting limit, stop one tick
  beyond the swing that started the shift, exits in thirds (1R or the nearest level, 2R, the
  next level or the close), stop to break-even after the first third.
- Timeframe and market: 5-minute. The materials are Micro Gold; we only have NQ/MNQ/ES, so
  the test is on NQ.
- Evidence to carry in: the indicator's own scorecard in the video reads FLOW 325 trades, 20%
  win; SSM 43 trades, 56% win, +1.57 points, before costs. Expect little.
- Needs: a partial-exit option in the engine (default off, tested).
- Status: **spec written** (`research/SPEC_pvnt_flow.md`), **waiting for your yes**; runs after
  the six candidates finish. Folds in "FVG retest entry" and "Partial exits and a trailing stop".
