# Claude-Code-Trading-Bot

A workbench for building and honestly testing day-trading rules on Nasdaq-100 futures
(NQ / MNQ), with the goal of a bot that sends notifications or trades automatically once a
rule has proven itself. Backtests run on 16 years of one-minute data in `data/futures/`.

Last updated 9 November 2026. Where things stand, in one line: a dozen rules (the sweep
rule, VWAP/ORB/FVG, the opening-range breakout, SuperTrend, six evidence-backed candidates,
TJR, the Anchored-VWAP pullback) have been tested honestly on 2010–2020; only the turn of the
month passes the pass mark, and it holds overnight, which a prop account cannot; the next idea
is up. Details in [CONTINUE_HERE.md](CONTINUE_HERE.md).

Three pages drive the work, and [ROADMAP.md](ROADMAP.md) holds the whole plan: Phase 1 is
a strategy that passes an honest backtest, Phase 2 adds agents from trader-skill that
check every trade and never act without your yes.

## 1. I have a new idea

Open [IDEAS.md](IDEAS.md). Write the idea in the template, or tell Claude "new idea: ...".
That page also lists the fixed steps every idea goes through before it counts: spec, log,
code, one-year sanity run, full 2010–2020 run with a random control, written result.

## 2. I want to continue what I was doing

Open [CONTINUE_HERE.md](CONTINUE_HERE.md), or tell Claude "continue". It holds the current
state of the project, the next steps in order, and the exact commands to run things.

## 3. I am starting a new chat

One Claude Code chat per task, named by kind and purpose (`Research: ...`,
`TradingView: ...`, `Housekeeping: ...`, `Learn: ...`). A chat only remembers what is
written to files, so end each task with "write that to the log" or "update continue-here",
then "commit" and "push". The full convention is in
[CONTINUE_HERE.md](CONTINUE_HERE.md#how-to-work-with-claude-on-this-project).

## Ground rules

- 2010–2020 is for development. 2021–2026 is untouched until a rule earns it.
- Every variant is logged before it runs, and losing results are never deleted.
- Nothing in this repo places orders. Broker work waits for a real account and an explicit OK.
- The data store was paid for: never regenerate or delete `data/futures/`.
