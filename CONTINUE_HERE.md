# Continue here

Read this first when picking the project back up. Tell Claude "continue" and it starts
from this page. Keep the "Where things stand" and "Next up" parts current at the end of
every working session.

## Where things stand (updated 8 November 2026, evening)

- **Goal:** a bot that sends trade notifications, or trades automatically, and is profitable.
  You have no prop-firm account yet and use TradingView only, so broker connections are on
  hold. Notifications would come from TradingView alerts on a Pine script.
- **Data:** 16 years of one-minute NQ, MNQ and ES bars in `data/futures/`. NQ stands in for
  MNQ before May 2019 (checked: same results on 2020).
- **Rules of the research:** 2010–2020 is the development window. **2021–2026 is untouched**
  and stays that way until a rule earns it. Every variant is logged in
  `research/research_log.md` before it runs. Losing results are kept, never hidden.
- **Strategy 1, the helper's sweep rule** (`pvnt_bot/engine.py`): loses every year
  2010–2020, −$36,039 on $50k, coin flip before costs, slightly better than random entries
  (+0.09R) but nowhere near enough. Full numbers in `research/REPORT_2010_2020.md`.
- **Strategy 2, VWAP + 15m ORB + FVG/OB** (`pvnt_bot/vwap_orb_fvg.py`, spec in
  `research/SPEC_vwap_orb_fvg.md`): loses every year in every variant, best profit factor
  0.58 against a wish of 2.0, direction call no better than a coin toss.
- **Lesson so far:** the problem is the one-minute timeframe and the cost-to-target ratio
  (about $5 of costs on trades aiming for ten points), not the specific pattern.
- **Slower bars (8 Nov):** confirmed. The sweep rule goes from −0.25R at 1m to −0.07R at
  15m (PF 0.96, 5 of 11 years positive) and beats random by ~0.1R at every bar size, but
  never clears costs. 30m+ bars run out of session before a 2R target. The VWAP/ORB/FVG
  rule is retired. The runner takes `--bars N`.
- **VWAP measurement (8 Nov):** being above or below session VWAP predicts nothing about
  the next hour. VWAP-bias filters are dead.
- **Package state:** `pvnt_bot/` is the helper's starter, rebuilt from the PDF; 35 tests
  pass; dashboard works at http://127.0.0.1:8765; it never places orders. The sweep rule's
  Pine script compiles clean in TradingView and has run in its Strategy Tester.
- **Git:** `main` only, on GitHub at `izTrent25/Claude-Code-Trading-Bot2`. Everything
  through the exit-rule experiments is committed and pushed (commit `50f1998`, 8 Nov 2026).
  GitHub matches the Mac.

- **TradingView tool:** connected and working as of 8 Nov 2026 (TradingView Desktop
  3.5.0 lives in `~/Desktop/Applications/`, not `/Applications`, so the launch script
  does not find it; launch by hand with
  `"/Users/trent/Desktop/Applications/TradingView.app/Contents/MacOS/TradingView" --remote-debugging-port=9222`).
  The sweep rule's Pine compiled clean; tester details in the report's "TradingView
  check" section. Basic plan: about one week of 1-minute history, one saved script.

- **TJR (8 Nov):** built to your write-up (`research/SPEC_tjr.md`, `pvnt_bot/tjr.py`,
  `pvnt_bot/TJR_Research.pine`), fired only a few times a year as strict rules, retired by
  your call. The TradingView chart has the sweep strategy ($500 budget) back on it.

- **Exit rules (8 Nov):** seven exits on the 15-minute sweep rule, all within noise of zero
  (PF 0.95–1.04). The sweep rule is closed. The engine now has `use_target`,
  `breakeven_r`, `trail_bars`, `max_consecutive_losses`, explicit `target` and `limit`
  proposals, all off by default and covered by tests (35 pass).

- **Strategy 3, the opening-range breakout on its own (8 Nov evening):** `research/SPEC_orb.md`,
  `pvnt_bot/orb.py`, research_log rows 50–72, report section "Strategy 3". Twelve variants,
  all lose in 10 or 11 of 11 years (best PF 0.89, −0.07R), none beats its coin-toss twin.
  **Closed.** The old Step 1 "+$42.9k" ORB does not survive honest costs. A Pine v6 version
  (`pvnt_bot/ORB_Research.pine`) is written but not compiled or loaded: you said not yet.
- **New house rule from the main chat (8 Nov):** every strategy also gets a Pine v6 version on
  the TradingView chart as a second opinion. The Python 2010–2020 result with its random
  control stays the verdict. Loading a script replaces the Pine editor contents, so ask first.
- **TradingView hunt (8 Nov, late evening):** searched TradingView's public strategies for
  anything "very profitable". Four candidates are written up at the end of `IDEAS.md`; the
  strongest by far is the **noise-area intraday momentum** rule (Zarattini, Aziz & Barbon 2024,
  17 years of SPY evidence after costs, two open-source NQ builds). Nothing tested yet. The
  rest of what TradingView shows as "profitable" is unverifiable or already-closed ideas.
- **Strategy 4, SuperTrend (8 Nov, night):** the first script you brought from TradingView,
  rebuilt line for line (`pvnt_bot/supertrend.py`, `research/SPEC_supertrend.md`, rows 73–83,
  report section "Strategy 4"). Loses on 1m, 5m and 15m bars, as published and as a day-session
  version; coin-toss twins match it; flat with zero costs. **Closed.** The engine now has three
  more research options, all off by default: `hold_overnight`, `intrabar_stop=false` and a
  `check_exit(position, bar)` hook so a strategy can end a trade at a bar's close; 50 tests pass.
- **Working style now:** you bring strategies from TradingView, each gets the same pipeline (spec,
  log, code, sanity run, 2010–2020 with a coin-toss control, written up win or lose). The
  noise-area momentum spec (`research/SPEC_noise_momentum.md`) is written but unconfirmed, parked.
- **The six evidence-backed candidates (9 Nov, small hours):** gap fade, last-half-hour momentum,
  overnight drift, turn of the month, noise-area momentum, first-candle ORB. Rows 85–120, report
  section "The six evidence-backed candidates". Five carry real information (positive 7–10 of 11
  years before costs, beating every random seed); micro-contract costs of about $3.50 a trade eat
  edges of $1.50–$5. **Turn of the month passes the frozen pass mark** (121 trades, +$5,731,
  8 of 11 years) and has **earned the 2021–2026 test, not run**; 2020 is two thirds of it and it
  holds overnight. Noise-area momentum is the strongest intraday signal (+$11k before costs,
  +$3.6k after, 3 of 11 years). The rest are closed.
- **Strategy 5, PVNT flow entry:** spec written (`research/SPEC_pvnt_flow.md`), waiting for your yes.
- **Engine:** 62 tests pass; new research options `hold_overnight`, `intrabar_stop`, `check_exit`
  hook; the runner has a strategy registry (`REGISTRY` in `research/run_backtest.py`).
- **Sweep rule revisited (9 Nov):** you want to go back to PVNT SMC Research v0.1. Its Pine script
  now accepts 1-, 5- and 15-minute charts (gap detection uses the chart's bar length); bar-count
  settings scale with the chart. The Python already ran on 5m/15m through `--bars` (rows 24–25, 43–49).

## Next up (in order)

1. **Turn of the month, 2021–2026 test: held back.** You decided on 9 November 2026 ("Not yet",
   relayed from the tracker chat) not to spend the untouched years on it yet. It keeps its earned
   right to that test until you say go. 2021–2026 stays untouched for everything.
2. **Your yes or no on Strategy 5, PVNT flow entry** (`research/SPEC_pvnt_flow.md`); the Pine
   version already exists (`pvnt_bot/PVNT_Flow_Research.pine`, compiles clean); the Python twin
   needs a partial-exit option in the engine. Expect little (the indicator's own scorecard: 20%
   wins).
3. **Noise-area momentum's cost line**, as its own logged hypothesis if wanted: the signal is real,
   the micro's $3.50 a trade is the problem. Candidates: fewer trades (first signal of the day only),
   a limit entry instead of market. Tuning risk: write the rule before looking at results. Rows
   start at 121.
4. Cheaper ideas from the TradingView hunt if wanted: UT Bot trailing line, VWAP-band mean
   reversion. Or paste the next TradingView script (its tester defaults to zero costs).
5. Decide whether to keep the $500-budget copy of the sweep script as your one saved TradingView
   script (it is in the editor, unsaved, and on the MNQ1! 1-minute chart) or discard it.
6. Any idea in `IDEAS.md` you want to move ahead of the queue.

## How to work with Claude on this project

One chat per task. A chat gets slow and forgetful as it grows, and when it is compacted
only a summary survives. The files in this repo are the real memory.

- Start a research chat with "continue"; Claude reads this page first.
- Start an idea chat with "new idea: ..."; it lands in `IDEAS.md`.
- Before a chat gets long, or when a task is done, say "write that to the log" or
  "update continue-here" so the result lands in a file. Then say "commit" and "push".
- Name chats by kind, then the one thing they are for, so the sidebar stays readable:
  - `Research: opening-range breakout`, `Research: FVG retest entry`
  - `TradingView: load sweep script on chart`, `TradingView: alerts setup`
  - `Bot: alert to Discord webhook` (later, once a rule survives)
  - `Housekeeping: commit and push`, `Housekeeping: update continue-here`
  - `Learn: what profit factor means` (throwaway question chats)

  Add the date when the same job repeats, for example `Research: ORB, 10 Nov`.
- Rules that hold in every chat: 2010–2020 only, log before running, never hide a loss,
  never touch `data/futures/`, no broker or API keys until there is an account and an
  explicit OK.

## How to run things

All commands from the project folder `/Users/trent/Claude-Code-Trading-Bot`. The research
runner needs the private toolbox in `.venv` (recreate with `python3 -m venv .venv` then
`.venv/bin/pip install pandas pyarrow`).

Run the package's own tests:

```bash
cd pvnt_bot && python3 -m unittest -v
```

Open the dashboard on the synthetic demo:

```bash
cd pvnt_bot && python3 app.py
```

Backtest the sweep rule on 2010–2020 (about 3 minutes):

```bash
.venv/bin/python research/run_backtest.py --symbol NQ --years 2010-2020 --mode research --tag smc_research_2010_2020
```

Same sweep rule on 15-minute bars (the runner resamples the 1-minute store):

```bash
.venv/bin/python research/run_backtest.py --symbol NQ --years 2010-2020 --mode research --bars 15 --tag smc_15m_research
```

Check the TradingView tool is talking to TradingView Desktop (launch it with the debug
port first, see above):

```bash
cd tools/tradingview-mcp && node src/cli/index.js status
```

Backtest the opening-range breakout (15-minute bars, 2-height target; about a minute):

```bash
.venv/bin/python research/run_backtest.py --symbol NQ --years 2010-2020 --strategy orb --bars 15 --set orb_target_mult=2 --tag orb_15m_t2
```

Backtest the SuperTrend script as published (holds overnight) on 15-minute bars:

```bash
.venv/bin/python research/run_backtest.py --symbol NQ --years 2010-2020 --strategy supertrend --bars 15 --tag st_a_15m
```

Backtest the VWAP/ORB/FVG rule:

```bash
.venv/bin/python research/run_backtest.py --symbol NQ --years 2010-2020 --strategy vwap_orb_fvg --tag vof_v2_rr15_risk20
```

Random control for either (random entries, or the VWAP rule with random direction):

```bash
.venv/bin/python research/run_backtest.py --symbol NQ --years 2010-2020 --strategy random --seeds 12 --match-trades 5670 --tag random_research_2010_2020
```

Change a setting without editing files, for example a 2R target:

```bash
.venv/bin/python research/run_backtest.py --symbol NQ --years 2010-2020 --strategy vwap_orb_fvg --set reward_risk=2.0 --tag vof_v2_rr20_risk20
```

Results land in `research/results/<tag>/` (ignored by git; re-creatable).

## Map of the project

| Where | What |
|---|---|
| `data/futures/` | The paid-for 16-year minute data. Never regenerate, never delete. |
| `pvnt_bot/` | The helper's research bot: engine, dashboard, Pine script, tests, docs. |
| `pvnt_bot/vwap_orb_fvg.py` | Strategy 2 (retired). New strategies go next to it. |
| `pvnt_bot/tjr.py`, `pvnt_bot/TJR_Research.pine` | TJR method as strict rules, retired 8 Nov 2026, kept for the record. |
| `pvnt_bot/orb.py`, `pvnt_bot/ORB_Research.pine`, `research/SPEC_orb.md` | Strategy 3, the opening-range breakout alone, closed 8 Nov 2026. Pine version not yet loaded. |
| `pvnt_bot/supertrend.py`, `research/SPEC_supertrend.md` | Strategy 4, SuperTrend from TradingView, closed 8 Nov 2026. |
| `pvnt_bot/{gap_fade,last_half_hour,overnight_drift,turn_of_month,noise_momentum,orb_candle}.py`, `research/SPEC_*.md` | The six evidence-backed candidates, tested 9 Nov 2026. |
| `research/SPEC_pvnt_flow.md` | Strategy 5, PVNT flow entry, spec only, awaiting your yes. |
| `research/run_backtest.py` | Headless backtester over the data store (`--strategy`, `--bars`, `--set`). |
| `research/vwap_measure.py` | The VWAP-tilt measurement (found no tilt). |
| `research/research_log.md` | Every variant ever tested, numbered. |
| `research/REPORT_2010_2020.md` | The written results, both strategies. |
| `research/SPEC_*.md` | Exact rules for each strategy. |
| `IDEAS.md` | Inbox for new ideas and the steps to integrate one. |
| `notes/` | Plain-words summary of the helper's 52-page PDF. |
| `tools/tradingview-mcp/` | Drives TradingView Desktop for compiling and testing Pine scripts; registered in `.mcp.json`. See `tools/README.md`. |
| `~/Claude-Code-Trading-Bot-backup-2026-11-07/` | The old Step 1/2/3 project, kept outside git. |
