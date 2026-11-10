# Roadmap

The step-by-step plan for the whole project, kept by the tracker chat. Each step says
what "done" looks like and which chat does the work. Boxes get ticked as steps finish,
with the date. Research chats write their results into `CONTINUE_HERE.md` and the
research log; this page only tracks the big picture.

**You are here:** Phase 1, step 2 done for seven candidates, step 3 waiting on your decision.
Latest (9 Nov 2026, evening): the Anchored-VWAP pullback indicator you pasted was turned into a
strategy and tested; it loses every year in every form, equals its coin-toss control and is a coin
flip before costs. Closed. Its Pine strategy version is ready for your chart if you want to watch it.
On 8–9 November 2026 the strategy chat ("Indicator/strat") tested six evidence-backed
candidates on 2010–2020 with honest costs and a random control each. Five carry real
information before costs, but a micro contract's costs (about $3.50 a trade) eat an edge of
$1.50 to $5 a trade, so they lose or barely break even. One, the turn of the month, passes
the frozen pass mark (profit factor 1.74, 8 of 11 years positive, above all eight random
seeds) and has earned the untouched 2021–2026 test. That test has not been run. Three
decisions are yours:

1. ~~Spend the 2021–2026 test on the turn of the month, or not.~~ **Decided 9 Nov 2026: not
   yet.** The turn of the month has earned the test and keeps that right; 2021–2026 stays
   untouched for now. It holds positions overnight, which a prop account cannot.
2. Yes or no on Strategy 5, the PVNT flow entry (`research/SPEC_pvnt_flow.md`). Expect little.
3. Whether to attack the noise-area momentum rule's cost line as its own logged hypothesis
   (fewer trades, limit entry): the strongest intraday signal found, 9 of 11 years before
   costs, 3 of 11 after.

## Phase 1: a strategy that is profitable in honest backtests

The bar for "profitable" is fixed now, before any result, so a lucky number cannot sneak
through. A rule passes Phase 1 when it:

1. beats its random control after real costs ($0.75 a side commission, 2 ticks slippage)
   on 2010–2020,
2. is positive in most of those 11 years,
3. is still positive on 2021–2026, which it never saw while it was being built,
4. gives the same picture in TradingView's own Strategy Tester,
5. paper-trades forward for at least four weeks without surprises.

Proposed numbers to call it "very profitable", for you to confirm or change: profit
factor 1.3 or better after costs, expectancy +0.15R or better per trade, positive in 8 of
11 development years and in 2021–2026, worst drawdown you could live through on your
account size. Nothing tested so far comes close; the sweep rule's best was profit factor
0.96 at 15 minutes.

Every strategy comes in two forms from its first test onward. The Python version runs the
honest backtest on 2010–2020 with costs and a random control; that is the verdict. The
Pine v6 version goes on your TradingView chart through the tradingview-mcp tool, so you
can see how it looks and watch how it trades the past with your own eyes. Both exist
before anything is called good. Only a rule that looks right on the chart and passes the
Python test goes on to 2021–2026.

| # | Step | Done when | Chat | Status |
|---|---|---|---|---|
| 1 | Opening-range breakout on its own, 5m and 15m bars, random control, plus a Pine v6 version on your TradingView chart | Spec confirmed, rows logged, result in the report, verdict stated, script on the chart so you can watch it trade the past | Research: opening-range breakout | **closed** 8 Nov 2026: loses in 10 or 11 of 11 years in all twelve variants, breakout direction = coin toss (rows 50–72, report "Strategy 3"). Pine written, not loaded. |
| 2 | If it fails, the next idea from the `IDEAS.md` inbox (FVG retest entry, structure bias, partial exits, your own new ideas), one chat each, same eight steps | Each idea has a logged, controlled result and a Pine script you have seen trade on the chart | Research: `<idea name>` | in progress. SuperTrend from your chart: **closed** 8 Nov 2026, loses on 1m, 5m and 15m, flat with zero costs (rows 73–83, report "Strategy 4"). Six evidence-backed candidates tested 8–9 Nov 2026 (rows 85–120, report "The six evidence-backed candidates"), NQ 2010–2020, one contract, after costs: gap fade +$393 (5 of 11 years), last-half-hour momentum −$5,074, overnight drift −$5,388, first-candle ORB −$2,318, all **closed**; noise-area momentum +$3,596 but only 3 of 11 years, **fails the pass mark, parked** (9 of 11 years before costs, worth a cost-line attempt); **turn of the month +$5,731, PF 1.74, 8 of 11 years, beats all 8 random seeds: passes the pass mark** (121 trades, two thirds of the profit in 2020, holds overnight). No Pine script yet for any of the six, so the chart half of this step is still open for the survivor. Queued: the PVNT flow entry (Strategy 5, `research/SPEC_pvnt_flow.md`, needs your yes; its own scorecard says FLOW wins 20% of 325 trades, so expect little). Its Pine v6 script is already written by the fork chat at `pvnt_bot/PVNT_Flow_Research.pine` (compiles clean, for a 5-minute chart, not loaded on your chart, 9 Nov 2026). **Anchored-VWAP pullback** (PhenLabs' AVPT indicator, your paste, 9 Nov 2026): **closed**, 26,183 trades, −$263,489 on three micros, 0 of 11 years, identical to its random control, coin flip before costs; every profile, the day session, 1m and 15m lose (rows 121–138, report "Strategy 6"); Pine strategy `pvnt_bot/AVWAP_Pullback_Research.pine` compiles, not loaded. |
| 3 | First survivor goes to 2021–2026, once | Positive there and beats random there too. A fail sends it back to step 2; nothing is ever tuned on 2021–2026 | Research: `<idea>` out-of-sample | **held back by you, 9 Nov 2026**: the turn of the month has earned it under the frozen rule, and you chose not to spend 2021–2026 on it yet. Not run. Its right to the test stands until you say go. |
| 4 | The survivor's Pine strategy (on the chart since step 1 or 2) checked properly against the Python engine | Strategy Tester agrees with the Python engine on the bars both can see (Basic plan: about a week of 1-minute bars, more on 5m/15m) | TradingView: survivor check | waiting |
| 5 | Paper-trade forward with TradingView alerts to your phone; every alert and its outcome goes in a forward log | Four or more weeks logged and compared with the backtest's expectancy | Housekeeping: forward log | waiting |
| 6 | Verdict: is it very profitable by the numbers above? Written into the report | A written yes opens Phase 2 | Tracker (this chat) | waiting |

## Phase 2: chat-bot agents that look over the strategy

The source is [Jakeschincariol/trader-skill](https://github.com/Jakeschincariol/trader-skill),
checked 8 November 2026: 11 Claude Code skills by Jake Schincariol, MIT licence, plain
Python with no API keys, about 1,600 stars. It is built for US stocks: copy an investor's
13F filing, watch news and Congress trades, size positions to a budget, check risk, build an
order ticket, taxes, price alerts, rebalancing. Nothing in it places an order by itself;
every order needs your typed yes, and paper trading is its default. It is not built for
futures or day trading, so part of this phase is adapting the pieces that fit.

| Skill | Use here | Why |
|---|---|---|
| `trader-risk` | yes, adapt | Checks every proposed trade against limits before anything goes out: max loss per day, max contracts, blocked times. The "look over my strategy" agent. |
| `trader-broker` | yes, adapt | Turns an approved trade into a ticket and records your yes. The "never without your yes" gate. |
| `trader-budget` | maybe | Sizes positions to a budget. Ours is contracts from risk per trade, which is simpler, but its cash-buffer idea is good. |
| `trader-alerts` | maybe | Price-level alerts and a market clock. TradingView alerts may already cover this. |
| `trader-news` | maybe | Headline watch. Could flag high-impact days (CPI, FOMC, NFP) to skip. |
| `trader-copycat`, `trader-pelosi`, `trader-analyst`, `trader-screener`, `trader-tax`, `trader-rebalance` | no | Stock-picking and portfolio tools. Nothing to do with an intraday NQ rule. |

| # | Step | Done when | Chat | Status |
|---|---|---|---|---|
| 7 | Install trader-skill project-local (copy the `trader-*` folders into `.claude/skills/`), run its offline tests, read the four relevant `SKILL.md` files | Tests pass; a plain-words note on what each relevant skill reads and writes | Bot: install trader-skill | waiting on Phase 1 |
| 8 | Write the agent flow for our case: strategy signal → risk check → ticket → your yes → paper account. What each agent may see and do | A spec you have read and agreed to | Bot: agent flow spec | waiting |
| 9 | Adapt `trader-risk` to futures: MNQ contract, $2 a point, limits in dollars and contracts, daily loss stop, session hours only, blocked days | Tests pass; it blocks a bad trade and passes a good one in a demo | Bot: risk agent | waiting |
| 10 | Adapt `trader-broker` to the paper account that exists by then (none today: TradingView paper trading or a prop-firm demo). It still only writes a ticket and records your yes | A ticket for a demo trade, approved by you, recorded | Bot: broker ticket | waiting |
| 11 | Wire it up: signal (TradingView alert webhook, or the Python engine running live) → risk agent → ticket → you. Paper only | Runs for weeks on paper with every step logged | Bot: wire it up | waiting |
| 12 | A reviewer agent that reads the forward log weekly, compares it with the backtest, and flags drift | First weekly review written | Bot: reviewer agent | waiting |
| 13 | Live trading, only with a real account you chose and an explicit OK each session | Not planned yet | — | not started |

## Rules that never change

- 2010–2020 is for development. 2021–2026 is untouched until a rule earns it (step 3).
- Every variant is logged before it runs. Losing results are kept, never hidden.
- Nothing in this repo places orders. Any agent that could lead to an order needs your
  typed yes for that exact trade.
- Never ask for or paste API keys or passwords into a chat.
- `data/futures/` was paid for: never regenerate or delete it.

## Chat log

| Date | Chat | What it did | Result |
|---|---|---|---|
| 7 Nov 2026 | (first chat) | Reset the repo to the data store, summarised the helper's 52-page PDF | `notes/`, backup of the old project outside git |
| 8 Nov 2026 | (one long chat, now the tracker) | Rebuilt the helper's bot, tested the sweep rule, the VWAP/ORB/FVG rule, slower bars, VWAP tilt, TJR and seven exit rules; connected TradingView; wrote the pages and the chat convention | Everything loses after costs so far; research log rows 1–49 |
| 8 Nov 2026 | Research: opening-range breakout (now "Indicator/strat") | Step 1: ORB on 5m and 15m, twelve variants with random-direction controls, Pine written | Closed, loses every way (rows 50–72), committed `61f91a3` |
| 8 Nov 2026 | Indicator/strat | Step 2: your chart's SuperTrend script on 1m, 5m and 15m, two versions | Closed, costs are the whole loss (rows 73–83), not yet committed |
| 8 Nov 2026 | Tracker | Read the PVNT Academy guide, Perky's 7-second video and the gold screenshot: no rules in them, only a trade shape and the indicator's own scorecard (FLOW 20% win over 325 trades) | `notes/PVNT_ACADEMY_GUIDE.md`; trade shape sent to the strategy chat as Strategy 5 candidate |
| 9 Nov 2026 | Tracker | Wrote the Pine v6 version of Strategy 5 from its spec at your request, compiled clean in TradingView, handed to you to paste | `pvnt_bot/PVNT_Flow_Research.pine`; Python twin and backtest still waiting on your yes in the strategy chat |
| 8 Nov 2026 | Tracker | Roadmap written; rule added that every strategy gets a Pine script on the chart alongside the Python backtest | this page |
| 8–9 Nov 2026 | Indicator/strat | Step 2: six evidence-backed candidates (gap fade, last-half-hour momentum, overnight drift, turn of the month, noise-area momentum, first-candle ORB), each with a spec, code, a random control and a zero-cost run | Five are real before costs, costs eat them; the turn of the month passes the pass mark and has earned 2021–2026 (not run); rows 85–120, 62 tests pass, not committed |
| 9 Nov 2026 | Tracker | Logged the six-candidate verdicts; you decided not to spend the 2021–2026 test on the turn of the month yet | step 3 held back, 2021–2026 still untouched |
| 9 Nov 2026 | General (fork) | Wrote the Pine v6 strategy for the Strategy 5 PVNT flow entry and compiled it in TradingView | `pvnt_bot/PVNT_Flow_Research.pine`, ready to paste on a 5m chart, not loaded; Python test still waits on your yes |
| 9 Nov 2026 | General (fork) | Turned PhenLabs' Anchored-VWAP pullback indicator into a strategy at your request and tested it on NQ 2010–2020: 13 variants, 24 random controls, a Pine strategy version compiled; the engine gained the `breakeven_at` option (71 tests pass) | Closed: −$263,489, 0 of 11 years, equals random, coin flip before costs (rows 121–138, report "Strategy 6"); not committed |
