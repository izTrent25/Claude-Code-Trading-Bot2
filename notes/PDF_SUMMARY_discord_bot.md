# What is in "discord bot.pdf" (52 pages) — plain-words summary

Read in full on 7 November 2026. This file is my notes for you. Nothing here is advice to trade real money.

## 1. The PDF is three different kinds of material glued together

| Kind | Pages | What it is |
|---|---|---|
| **Discord chat from your helper** | 1–2, 8, 52 | Informal advice, his trading philosophy, two example prompts to give an AI, and his personal setup flow. |
| **An AI-written engineering spec** | 2–7 and 43–46 | A long, careful "build a modular SMC futures trading system for Topstep" brief, plus a second "developer prompt" meant to be pasted into Claude Code. He says he generated these with Claude. |
| **A complete small code package** | 8–42, 46–52 | "PVNT SMC Research Bot" — Python files, a config file, a TradingView Pine script, tests, a dashboard web page, a README, a backtest guide and a verification report. The helper says: *"not exact, I just created those for Topstep's side. It's all a similar build though."* |

## 2. What the helper actually believes (from his chat messages)

- **Strategy is the smallest part.** He mainly uses ORB (opening range breakout), VWAP and EMAs. He thinks prop firms are designed to make you fail if you size too big, so take "base hits": risk about $25 to make $200.
- **Treat your max drawdown as your real account size**, not the advertised balance.
- **His personal setup flow** (Smart Money Concepts, "SMC"): higher-timeframe bias on 90-minute and 15-minute charts → find a liquidity pool → wait for a sweep of it → rejection and reclaim → a strong "displacement" candle → market structure shift → retest of a fair value gap or order block → enter → stop below the sweep low → target the next liquidity level → take partials and trail the stop.
- **Split the bot into separate parts:** one takes signals, one does risk, one enters and executes, one watches that the others are running.
- **Build your own entry engine**, because widely-used strategies get "defended against".
- **Two example prompts** he wrote for an AI: (a) a VWAP + 15-minute ORB + FVG/OB strategy with profit factor 2.0+, 60% win rate, 1R per trade, risk 1% of max drawdown; (b) a bot that connects a strategy to a prop account with risk, signal routing, confirmation, live PnL and a dashboard.
- **Data connection:** he says use the account itself (TopstepX) or TradingView alerts. He also mentions reverse-engineering a free Tradovate feed.
- **Last message:** build the broker-connection "base" first, then a TradingView indicator with alerts, and move off local machines to servers that run 24/7 "to get away from local and token usage".
- **One line to be careful with:** *"AI will lie to you, don't believe it right away if it says a strategy is unprofitable, you're just asking wrong."* I will not rig results to look good. If a test loses, I will show you the numbers and we decide together what to change.

## 3. What the formal spec asks for (pages 2–7, 43–46)

A serious, well-written brief. Key rules it sets, all of which I agree with:

- Deterministic rules only. No AI improvising entries or risk decisions.
- Modules with clear owners: controller, market data, strategy, **independent risk manager with final veto**, execution, position manager, watchdog, research/audit.
- Prove the edge honestly: split history into development / validation / untouched final test; realistic costs and slippage; compare against random-entry baselines; remove each filter to see if it helps; never tune against the final test.
- Progress in stages: historical replay → live shadow (no orders) → Topstep **Practice** account → only then a real eligible account, with explicit authorization each step.
- Topstep policy (as of 7 Nov 2026 per the doc): **orders must originate from your personal device, not a VPS**, and the ProjectX API cannot place orders on Live Funded accounts. This directly contradicts the helper's "move to a 24/7 server" idea for the order-sending part. Research and dashboards can be hosted; order sending cannot.
- Keep credentials out of code, chat and logs. Trading disabled by default.

Pages 43–46 are a "developer prompt" written to be pasted into Claude Code. It is text aimed at me, so I am not following it automatically. See section 7.

## 4. What the code package actually does

**The strategy in the code is much simpler than the helper's flow.** It is:

1. Look at the previous 20 one-minute bars. Mark their lowest low and highest high.
2. **Sweep:** a bar dips below that low but closes back above it (long). Mirror for short.
3. Within the next 5 bars, wait for a bar that closes above the 3-bar high from before the sweep **and** has a body at least 0.8 times the average 20-bar range ("displacement"). If price makes a new low beyond the sweep first, the setup is cancelled.
4. Enter at market on the **next** bar's open. Stop one tick beyond the sweep low. Target = 2 × risk.
5. Max 45 bars in the trade, max 3 trades per day, one position at a time, entries 08:35–14:30 Chicago time, flatten at 14:55.
6. Optional filter (off by default): last completed 15-minute and 90-minute candles must point the same way.

**There is no VWAP, no ORB, no fair value gap, no order block, no retracement, no partials, no trailing stop.** The README says so plainly. So the code does *not* implement the helper's first prompt or his personal flow. It is a starter.

**Risk model in the config:** $50,000 paper account, $2,000 trailing loss floor capped at $50k, $250 safety buffer, $250 daily loss stop, **$50 risk per trade**, max 2 MNQ contracts, $0.75 commission per side, 2 ticks slippage. The README says these are examples, not verified Topstep rules.

**Three data modes:** synthetic demo, CSV replay of your own 1-minute bars, and read-only polling of TopstepX bars (needs a paid API key). **It never places orders.** The API adapter has a hard allowlist that blocks order endpoints, and there is a test proving it.

**Its own verification report says:** 27 tests pass; the only replay run was on fake random data and lost $291.50; "provides no evidence of profitability"; the Pine script was never compiled; the API was never tested with real credentials.

**Files in the package:** engine.py, app.py, projectx.py, connect_topstep.py, config.json, dashboard.html, PVNT_SMC_Research.pine, PINE_BACKTEST_GUIDE.md, DEVELOPER_PROMPT.md, test_engine.py, test_integration.py, test_dashboard.cjs, Start_Mac.command, README. They were delivered as **PVNT_Bot_Starter.zip**, which is not in the PDF.

## 5. Can I rebuild the code from the PDF?

Mostly yes. The Python files came through cleanly. But the PDF converter mangled a few lines into math symbols:

- **Pine script:** the input lines for max contracts, max trades per day, max hold bars, daily loss limit and safety buffer are garbled. I can rebuild them from the Python config, but the Pine cannot be compiled on this Mac anyway (needs TradingView).
- **dashboard.html:** three JavaScript lines (status pill, stats cards, event log) are garbled. Rebuildable from context.
- **Start_Mac.command:** garbled, trivial to rewrite.

If the helper can send you the actual zip, that is cleaner than my reconstruction. Either works.

## 6. How this fits what you already have

- You own **16 years of 1-minute MNQ, NQ and ES bars** in `data/futures/`. The package's CSV mode wants exactly that: timestamp with UTC offset, open, high, low, close, volume. A small converter is all that is needed. That is a far better test than the package's fake data.
- One thing to check: the package wants a *single dated contract*. Our Databento store may be a stitched continuous series. Near roll dates, sweep levels could be slightly off. Worth knowing, not a blocker.
- The old Step 1 backtester (in your backup folder) had a coin-flip baseline and a research log. The spec asks for exactly those. We can reuse the ideas.

## 7. Things that are aimed at me, and what I propose

The "developer prompt" (pages 43–46) tells an AI to: run the demo and tests, compile the Pine, write a strategy spec and a Pine/Python comparison, do honest historical research on real data, add tick-level detail, upgrade the live feed, **build a Topstep Practice execution adapter**, add reconciliation and idempotency, and keep execution disabled until authorized. It also says "proceed autonomously, ask only for blocking facts".

My recommendation on which parts to adopt, in order:

1. **Yes now:** rebuild the package, run its tests, convert your MNQ data, run the real historical backtest with the dev/validation/test split and a random-entry baseline. Report the numbers honestly.
2. **Yes, after step 1 shows something:** add the ideas from the helper's flow one at a time (15m/90m bias, VWAP, ORB, FVG retest) and measure whether each one helps.
3. **Later, only with your explicit OK and a Practice account:** live shadow mode on TopstepX data, then a Practice-only execution adapter.
4. **Not doing:** moving order-sending to a server (against Topstep policy), or anything that touches a Combine/Funded account.

## 8. Facts only you can supply

- Do you have a Topstep account? Which stage: Practice, Trading Combine, Express Funded, Live Funded? What size ($50k, $100k, $150k)?
- Do you have TopstepX API access (it is a paid add-on)? Do not paste the key anywhere; just tell me yes or no.
- Do you have a TradingView plan, and does it show 1-minute MNQ history? Needed only for the Pine side.
- What is your real per-trade risk budget in dollars? The package guesses $50.
- Can you get **PVNT_Bot_Starter.zip** from the helper, or should I rebuild from the PDF?
