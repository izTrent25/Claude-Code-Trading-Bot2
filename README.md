# Claude-Code-Trading-Bot

A workbench for building and honestly testing day-trading rules on Nasdaq-100 futures
(NQ / MNQ), with the goal of a bot that sends notifications or trades automatically once a
rule has proven itself. Backtests run on 16 years of one-minute data in `data/futures/`.

Two pages drive the work:

## 1. I have a new idea

Open [IDEAS.md](IDEAS.md). Write the idea in the template, or tell Claude "new idea: ...".
That page also lists the fixed steps every idea goes through before it counts: spec, log,
code, one-year sanity run, full 2010–2020 run with a random control, written result.

## 2. I want to continue what I was doing

Open [CONTINUE_HERE.md](CONTINUE_HERE.md), or tell Claude "continue". It holds the current
state of the project, the next steps in order, and the exact commands to run things.

## Ground rules

- 2010–2020 is for development. 2021–2026 is untouched until a rule earns it.
- Every variant is logged before it runs, and losing results are never deleted.
- Nothing in this repo places orders. Broker work waits for a real account and an explicit OK.
- The data store was paid for: never regenerate or delete `data/futures/`.
