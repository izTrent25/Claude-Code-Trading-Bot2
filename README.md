# Claude-Code-Trading-Bot

A workbench for building and honestly testing day-trading rules on Nasdaq-100 futures
(NQ / MNQ), with the goal of a bot that sends notifications or trades automatically once a
rule has proven itself. Backtests run on 16 years of one-minute data in `data/futures/`.

Last updated 8 November 2026. Where things stand, in one line: two strategies and the
TJR method have been tested honestly on 2010–2020 and none beats costs yet; the
opening-range breakout is next. Details in [CONTINUE_HERE.md](CONTINUE_HERE.md).

Three pages drive the work:

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
