# The PVNT AI Academy guide, Perky's 7-second video and the gold screenshot

Read on 8 November 2026 from `~/Downloads/PVNT_AI_Academy_Complete_Guide (1).pdf`,
`~/Downloads/IMG_2613.mov` and a chart screenshot pasted into the tracker chat. Plain words,
so nobody has to open them again.

## The guide (38 pages): a course outline, no strategy rules

"PVNT AI Academy, Complete Reference Guide, November 2026." Four tracks, 24 topics, one
page each: the core idea, how it works, an example, pitfalls, a reference prompt.

1. AI mastery: how models work, agents and permissions, dictating specs, keeping decisions
   in project files (README, REQUIREMENTS, DECISIONS, PROGRESS), research and verification.
2. Tools and MCPs: terminal, Git and GitHub, skills and MCP servers, a toolkit inventory,
   memory and multi-agent workflows, security and prompt injection.
3. Building and automation: Python and APIs, Discord webhooks, inbound webhook receiver,
   SQLite and dashboards, VPS deployment, testing.
4. Algorithmic trading: bot architecture (data → strategy → signal ID → independent risk →
   paper executor → dashboard), SMC/ICT terms turned into unambiguous rules (confirmed
   pivots, sweep penetration and reclaim, displacement relative to ATR, observable at
   decision time), Pine v6 strategies with documented costs, validation (expectancy, profit
   factor, drawdown, freeze parameters before an untouched test, compare with simple
   baselines), TradingView-to-executor webhook, forward testing.

What it says about trading is exactly what this project already does: honest costs, a
baseline to beat, untouched test data, no tuning on it, rules written before the run. The
only concrete rule mentioned is "a prior confirmed low is breached, price closes back above
it, then a defined structure shift triggers a long", which is strategy 1, the sweep rule,
already tested and closed.

It contains **no entry, stop, target or session rules** beyond that example, no indicator
logic, and no numbers. The "real TradingView screenshot" page is a QQQ swing-level example
with no trade on it. The last pages are links (Claude Code docs, MCP registry, Playwright,
Pine docs, TradingView webhooks, FastAPI, SQLite, Nginx) and a security reference.

## The video (7 seconds, phone recording of a laptop)

Perky's TradingView: **Micro Gold Futures (MGC1!) 5-minute**, with the PVNT indicator on,
8 November 2026 in the evening. Visible:

- Entry and stop labels: `FLOW ▲ 4075.8 SL 4053.0` and `FLOW ▲ 4079.1 SL 4052.4` (long
  entries about 23–27 points above their stops), a grey `FVG` box below price, small
  `L -0.1` and `L -7.3` labels on recent losing trades, and a position tool with
  retracement lines (0%, 23.6%, 38.2%, 50%, 61.8%, 100%) drawn on the last swing.
- A text panel: "DAY / 0DTE-style: none graded yet (after the opening window)", "PICK OF
  THE DAY: pending the opening window", "SWING (hold 1–10 days): none (dip check 10:55 ET)",
  "24H+ SWING: no daily trend flip up today", "DAILY TREND (24H) MGC1!: DOWN".
- **The indicator's own scorecard** for closed trades on the loaded history of that chart:
  `SSM 43 trades, 56% win, +1.57 pts` · `DIP 0 trades` · `24H+ 0 trades` ·
  `FLOW 325 trades, 20% win, ...` (the rest is cut off by the recording).

That last line is the most useful thing in the video. On the history Perky had loaded, the
FLOW signal won one trade in five, and the SSM signal was flat (+1.57 gold points over 43
trades, before any cost). That is the indicator grading itself.

## The screenshot (5 October 2026, Micro Gold 5-minute)

Perky's live long in gold with the PVNT dashboard:

- Dashboard: BULLISH, quality 20/100, confidence 7, Asia session off, "No KZ" (no kill
  zone), timeframe bias 5/15/30/60/D all neutral, PDH 4259 PDL 4153.8, PWH 4320 PWL 4143,
  FLOW BUYERS 21%, ADR 88, HTF 60 DOWN, ASI L 4170.8 (Asia low), RANGE 45%, "RUNWAY WAIT
  FOR REVERSAL", "GATE LONG leg fired, wait for flip".
- Structure labels on the chart: LH, HH, CH, HL. A label `LONG FVG ·8 @ 4163.0`.
- The trade: 3 contracts long from about 4162.3, +$63 open. Three sell-limit targets of one
  contract each at 4164.4, 4168.2 and 4182.8, and a 3-contract stop at 4143.5. In points:
  risk 18.8; targets +2.1, +5.9 and +20.5, so 0.1R, 0.3R and 1.1R. Two of the three exits
  are tiny compared with the stop.

## What is extractable, and what is not

Extractable: the **trade shape**. A structure shift (CH, then HL), a fair value gap left by
the move, a long from that gap, the stop under the swing low, and exits scaled in thirds at
nearby levels. That is the "FVG retest entry" idea already in `IDEAS.md`, plus partial exits.

Not extractable: the PVNT indicator's logic. Its bias, quality score, "flow", "runway" and
"gate" rules are not in any of the three files, and the dashboard values cannot be
recomputed from price alone. Only Perky can supply the rules or the Pine source.

Also: the materials are on gold. The data store has NQ, MNQ and ES only, so any test runs
on NQ.

## What was done with it

The trade shape was handed to the strategy chat on 8 November 2026 as candidate
"Strategy 5: PVNT flow entry" (spec first, your yes before code, logged, costs, random
control, Pine on the chart, like every other candidate). The guide's architecture pages
match Phase 2 of `ROADMAP.md` and need nothing new.
