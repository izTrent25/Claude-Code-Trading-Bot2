# Continue here

Read this first when picking the project back up. Tell Claude "continue" and it starts
from this page. Keep the "Where things stand" and "Next up" parts current at the end of
every working session.

## Where things stand (updated 8 November 2026)

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

## Next up (in order)

1. The opening-range breakout on its own, on 5m and 15m bars, with a random control. The
   old Step 1 log had an ORB rule as its best idea; this time it gets the honest test.
   Log it in `research/research_log.md` (row 50 onwards) before the first run.
2. Decide whether to keep the $500-budget copy of the sweep script as your one saved
   TradingView script (it is in the editor, unsaved, and on the MNQ1! 1-minute chart) or
   discard it.
3. Any idea in `IDEAS.md` you want to move ahead of the queue.

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
| `research/run_backtest.py` | Headless backtester over the data store (`--strategy`, `--bars`, `--set`). |
| `research/vwap_measure.py` | The VWAP-tilt measurement (found no tilt). |
| `research/research_log.md` | Every variant ever tested, numbered. |
| `research/REPORT_2010_2020.md` | The written results, both strategies. |
| `research/SPEC_*.md` | Exact rules for each strategy. |
| `IDEAS.md` | Inbox for new ideas and the steps to integrate one. |
| `notes/` | Plain-words summary of the helper's 52-page PDF. |
| `tools/tradingview-mcp/` | Drives TradingView Desktop for compiling and testing Pine scripts; registered in `.mcp.json`. See `tools/README.md`. |
| `~/Claude-Code-Trading-Bot-backup-2026-11-07/` | The old Step 1/2/3 project, kept outside git. |
