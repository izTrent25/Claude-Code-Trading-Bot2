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
- **Package state:** `pvnt_bot/` is the helper's starter, rebuilt from the PDF; 27 tests
  pass; dashboard works at http://127.0.0.1:8765; it never places orders. The Pine script
  has not been compiled in TradingView.
- **Git:** `main` only. Last push had the data store and notes. Everything in `pvnt_bot/`,
  `research/`, `IDEAS.md`, this file and `.gitignore` is **not committed yet**.

## Next up (in order)

1. Commit and push the current work so GitHub matches the Mac.
2. Paste `pvnt_bot/PVNT_SMC_Research.pine` into TradingView's Pine Editor and report any
   compile error (only you can do this).
3. Run the cheap VWAP measurement from `IDEAS.md` ("Does above VWAP predict anything?").
4. Build the slower-bars experiment (5m and 15m) for both existing rules.
5. Then the opening-range breakout on its own.

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
| `pvnt_bot/vwap_orb_fvg.py` | Strategy 2. New strategies go next to it. |
| `research/run_backtest.py` | Headless backtester over the data store. |
| `research/research_log.md` | Every variant ever tested, numbered. |
| `research/REPORT_2010_2020.md` | The written results, both strategies. |
| `research/SPEC_*.md` | Exact rules for each strategy. |
| `IDEAS.md` | Inbox for new ideas and the steps to integrate one. |
| `notes/` | Plain-words summary of the helper's 52-page PDF. |
| `~/Claude-Code-Trading-Bot-backup-2026-11-07/` | The old Step 1/2/3 project, kept outside git. |
