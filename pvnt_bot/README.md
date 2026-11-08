# PVNT SMC research bot + dashboard

> Rebuilt on 7 November 2026 from the 52-page "discord bot.pdf" the Discord helper sent.
> The original zip (PVNT_Bot_Starter.zip) was not available. Python files came through the
> PDF intact; a few lines in the Pine script, the dashboard JavaScript and Start_Mac.command
> were garbled by the PDF converter and were reconstructed from context. See the research
> folder at the repo root for the historical backtests run on the owner's own 16-year data.

A runnable local paper-trading starter, with a separate Pine v6 research strategy. This is
new example strategy code, not your existing PVNT indicator and not a proven profitable
system.

## Run on your Mac

1. Open Terminal and run:

```
cd pvnt_bot
python3 --version
python3 app.py
```

Requires Python 3.10 or newer with standard timezone data. No pip packages, Docker, or
Node installation needed.

2. Open http://127.0.0.1:8765 in your browser.
3. Click **Start / resume**. Change speed to run faster. The demo ends automatically.
4. Inspect candles, paper equity, risk state, positions, events, and trade history. Click
   **Export trades** to download the full trade list.
5. Ctrl+C in Terminal stops the server. A restart creates a NEW run; it does not resume the
   prior paper account. Snapshots, processed bars, and all trades remain in
   `~/PVNTBotData/runs/*.sqlite` for audit. The dashboard shows the latest 200 trades and
   5,000 equity points; CSV includes every trade.

Start_Mac.command is an optional launcher after making it executable. Terminal is the
primary launch path. If port 8765 is occupied, run `python3 app.py --port 8766` and open
that port instead.

## Three data modes

| Mode | Source | Where fills happen | Needs credentials |
|---|---|---|---|
| Demo | Clearly labeled synthetic random candles | Local simulator | No |
| CSV | Your historical one-minute futures data | Local simulator | No |
| TopstepX data | Completed one-minute API bars, polled every 10 seconds | Local simulator | TopstepX API subscription/key |

This package never places, modifies, or cancels Topstep account orders. It does not connect
your TradingView alerts. It is not a Topstep Practice execution adapter, Trading Combine
executor, or Live Funded bot. Its API adapter allowlists authentication, contract search, and
historical bars only.

Demo data is artificial. Results generated from it only check software behavior, not market
profitability. The demo's default October 2026 dates are fixed for reproducibility.

## Historical CSV backtest

Use standard one-minute OHLC bars for a single actual futures contract, sorted oldest first.
Bar timestamps denote bar START and must contain a UTC offset. Required columns:

```
timestamp,open,high,low,close,volume
2026-11-02T14:35:00+00:00,21000.00,21004.00,20998.25,21002.50,120
2026-11-02T14:36:00+00:00,21002.50,21007.00,21001.00,21006.00,150
```

```
python3 app.py --mode csv --csv "/absolute/path/to/your_mnq_1m.csv"
```

Open the dashboard and click Start. Edit config.json before launching to change risk and
setup rules. Adjust symbol/tick economics for any instrument other than MNQ. Defaults for
costs are illustrative, not a quote of your Topstep fees. Replay inputs can contain session
gaps, but intervals under one minute and duplicate/out-of-order timestamps are rejected.
Gaps over one minute clear setup/context, cancel pending proposals, and flatten a paper
position at the next bar's open with slippage.

## Forward paper-test with TopstepX data

Get API access and generate a key through TopstepX following the official instructions
linked below. Do not paste your key into chat or source code.

```
python3 connect_topstep.py
```

Enter your platform username, then your API key at the hidden prompt. Select the exact
intended contract from the returned list. Contract tick size and tick value are loaded from
that metadata. Credentials are kept in the local process environment, not saved in files or
sent to this dashboard. The initial request warms the indicators using recent bars without
creating historical paper trades. Subsequent NEW completed bars drive paper trades. This
uses API historical bars as a slow polling feed, not a tick feed. It cannot validate
intraminute broker execution or protective-order behavior.

The advanced noninteractive path uses PROJECTX_USERNAME and PROJECTX_API_KEY,
`python3 app.py --list-contracts`, then `python3 app.py --mode projectx --contract
CONTRACT_ID`. Never store secrets in shell history.

## What the SMC rule actually does

1. Use the preceding 20 bars to define liquidity high/low. The current bar is excluded.
2. A long candidate sweeps the prior low and closes back above it; short is the inverse. A
   bar sweeping/reclaiming both sides is ignored.
3. Freeze the preceding three-bar structure extreme at the sweep. Within five later bars,
   require a close through that structure and a directional candle body at least 0.8 times
   the preceding 20-bar average range. A new extension beyond the sweep extreme
   invalidates the setup first.
4. Optional context requires the most recent completed 15m and 90m candles to agree with
   direction. This simple candle-direction filter is OFF by default; it is not a
   sophisticated HTF SMC bias model.
5. Propose a market entry for the NEXT one-minute bar open. No same-bar hindsight entry.
   There is NO retracement, FVG, order-block, or order-flow logic in this starter.
6. Stop one tick beyond the sweep. Target 2R from the modeled entry. Maximum 45 holding
   bars, three entries per configured calendar day, one position at a time. Entries
   08:35–14:30 Chicago time; flatten from 14:55. These are conservative user settings, not a
   statement of Topstep's official cutoff.

R denominator includes modeled stop distance, round-trip commission and assumed stop
slippage. Dashboard P&L is net of modeled costs. Max drawdown is based on close-marked
equity and final exits, not a tick-by-tick worst excursion.

## Risk and fill model

Initial paper balance $50,000; initial loss floor $48,000; floor trails end-of-day realized
balance less $2,000 and caps at $50,000. A $250 safety buffer, $250 daily loss stop, $50
risk budget and two-contract maximum are example settings. They are **not verified
account-specific Topstep rules**. Calendar-day Chicago resets approximate sessions; exact
firm sessions, account stages, payouts, resets, consistency criteria and contract limits are
NOT modeled.

Positions are sized at next open using structural stop distance, estimated exit slippage and
round-trip commission. A position too expensive even at one contract is rejected. Gaps can
exceed modeled risk and breach the floor despite a guard. Stop/risk checks are applied
before profit targets when intrabar sequence is unknowable. Market and stop fills suffer
adverse slippage; targets require one tick of penetration and fill at the target. No queue
position, partial fills, order latency, margin engine, exchange halts, or depth-of-book
model. No spread term separate from slippage. This OHLC simulator is a research
approximation.

Dashboard controls bind to localhost and require a per-run control token. Do not expose the
server to the internet.

## Architecture

- `engine.py`: SMC Strategy and independent risk/fill/account Engine.
- `projectx.py`: allowlisted read-only API adapter.
- `app.py`: controller, replay/live-bar loop, SQLite audit, HTTP dashboard API.
- `dashboard.html`: local charts, positions, risk, trade export and controls.
- `connect_topstep.py`: interactive data-only connection.
- `config.json`: editable settings.
- `PVNT_SMC_Research.pine`: separate TradingView strategy.
- `PINE_BACKTEST_GUIDE.md`: step-by-step TradingView test instructions and differences.
- `DEVELOPER_PROMPT.md`: handoff prompt to extend this project.
- `test_engine.py`: meaningful scenario tests. Run with `python3 -m unittest -v`.
- `test_integration.py`: HTTP/worker/persistence smoke test.
- `test_dashboard.cjs`: Node mock-DOM test of the dashboard script.

## What must happen before Topstep Practice order execution

Build a separate explicitly allowlisted Practice-account adapter with broker order/fill
reconciliation, verified protective brackets, partial-fill handling, duplicate prevention,
ambiguous-response recovery, disconnect recovery and account/session rule verification.
Test with Practice before any paid evaluation or funded simulated account. Keep risk
authoritative and prevent simultaneous executors. Never simply replace a simulator function
with an order POST.

Topstep's published API policy (as read on 7 November 2026) requires order activity from
your personal device, excludes order triggers/relays from VPS servers, and says ProjectX
API execution is unavailable for Live Funded Accounts. Recheck current policy before
extending this starter.

Official references checked November 7, 2026:

- https://help.topstep.com/en/articles/11187768-topstepx-api-access
- https://gateway.docs.projectx.com/docs/getting-started/authenticate/authenticate-api-key/
- https://gateway.docs.projectx.com/docs/api-reference/market-data/search-contracts/
- https://gateway.docs.projectx.com/docs/api-reference/market-data/retrieve-bars/
- https://www.tradingview.com/pine-script-docs/concepts/strategies/
- https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/
