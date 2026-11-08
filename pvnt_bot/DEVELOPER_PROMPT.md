# Developer handoff prompt (from the Discord helper's package)

> Kept here for reference. This is text written to be pasted into an AI assistant. It is
> not being followed automatically; the project owner decides which parts to adopt.

You are extending the attached PVNT SMC research bot and dashboard. Inspect every source
file and README before changing anything. This is an existing working local simulation
starter, not a blank project. Preserve its runnable demo and keep all external trading
disabled by default.

## GOAL

Develop a robust, testable SMC futures trading bot for eligible Topstep accounts, with one
master controller coordinating market data, strategy, independent risk management,
execution, position management, monitoring and research. Start with MNQ. Keep each
module's ownership explicit. Risk must have final veto power. Only the execution adapter
may transmit orders. Use deterministic trading rules; do not use an LLM to improvise
entries, risk approvals or account actions.

## CURRENT BASELINE

Read the exact strategy in engine.py. It detects a sweep of the prior N bars, then a later
displacement candle closing beyond the frozen three-bar pre-sweep structure. It proposes a
next-bar market entry, with a structural stop and fixed-R target. It has no FVG,
retracement, order-block or order-flow logic. Do not imply those features exist.

The current system includes a synthetic demo, CSV historical replay, optional read-only
TopstepX completed-bar polling into a LOCAL paper broker, SQLite audit, localhost dashboard
and a separate Pine v6 strategy. There is intentionally no Topstep order execution. Sample
risk rules approximate account behavior and are not account-specific verified rules.

## WORK ORDER

1. Run the demo and supplied tests. Identify deficiencies using concrete evidence. Preserve
   the dashboard's usable dark/gold design. Implement meaningful fixes and document changes.
2. Compile PVNT_SMC_Research.pine in TradingView if an authorized interface is available.
   Otherwise state that compilation remains unverified and provide the exact file. Do not
   claim a compile check from a Python linter.
3. Write an exact strategy specification and a Pine/Python comparison matrix. Test signal
   parity on matching timestamps and identical contract data before attempting fill parity.
   Resolve or disclose differences in HTF session alignment, warmup, gaps, sizing, targets
   and exit assumptions. Avoid lookahead and repainting.
4. Implement robust historical research with real futures data the user is entitled to
   access. Use conservative execution assumptions, realistic fees/slippage, chronological
   development/validation/final-test periods, a register of every variant, parameter
   robustness and component-removal tests. Benchmark against simple and randomized-entry
   controls with comparable risk/holding constraints. Do not assume more SMC filters means
   better trading.
5. Add tick/intrabar detail where tight stop geometry requires it. Record missed fills and
   uncertainty. Report net expectancy in dollars and R, median R, profit factor, drawdown,
   losing streaks, MAE/MFE, time in trade, concentration and performance by
   period/direction. Use dependent-data-aware uncertainty estimates. Evaluate exact Topstep
   rule breaches after verifying the applicable rules.
6. Upgrade the read-only feed to a documented robust real-time connection if needed; keep
   it separate from account order routing. Handle stale/out-of-order data, clock
   synchronization, exchange sessions, rollover and contract economics.
7. Build a SEPARATE Topstep Practice-account execution adapter only after verifying current
   official Topstep/ProjectX documentation and the target account. Use a strict account-ID
   allowlist. Never assume an account is Practice from its display name alone. Never
   silently use a Combine, Express Funded or Live account instead.
8. Implement account reconciliation, persistent idempotency, atomic risk reservations,
   protective bracket verification, partial fills, rejects, uncertain order
   acknowledgments, token refresh, rate limits, reconnects and startup recovery. Reconcile
   before retrying ambiguous order submissions. Verify actual supported broker order
   semantics; do not assume native OCO/brackets exist.
9. Treat manual broker orders as changes to authoritative account state. Reject new
   exposure if position/order state is unknown. Preserve position supervision during
   strategy pauses. Coordinate emergency orders through a single execution authority.
   Never promise stops eliminate gap or outage losses.
10. Keep account execution disabled until explicitly authorized for the allowlisted Practice
    account. First demonstrate it with tests/mocks and reviewable configuration. Never
    place external trades merely because this prompt asks you to build an adapter. Use
    Practice to test broker behavior before any paid evaluation deployment.

## PINE STRATEGY REQUIREMENTS

Maintain a real Pine v6 strategy() version of each approved deterministic strategy, not an
indicator that only plots labels. Include explicit entry/exit orders, session/date inputs,
costs/slippage assumptions and risk-sizing logic. Use completed information only; HTF
requests must not leak future values. Test on standard candles. Document unavoidable
differences from the Python execution model instead of claiming identical results.

Maintain PINE_BACKTEST_GUIDE.md with step-by-step instructions. Explain TradingView
plan/history limits and that strategy simulation is not an automatic connection to
TradingView Paper Trading or Topstep.

## RISK REQUIREMENTS

Risk budgets must depend on structural stop distance, contract tick economics, fees,
slippage allowance and remaining account loss capacity. Do not size solely from the
advertised account balance. Reject trades if the minimum contract exceeds risk. Reserve
approved exposure atomically. Include pending orders and correlated positions in total
exposure. No martingale, averaging down to avoid realizing losses, or automatic recovery
sizing. Never widen initial risk without a fresh approval.

Verify exact account-stage rules, session cutoffs, contract limits, trailing-loss behavior,
payouts/resets and applicable policies from official sources, with date checked. Do not
assume the starter configuration is Topstep-compliant.

## HOSTING AND ACCESS

Current Topstep policy says order activity must originate from the trader's personal device
and excludes remote order triggers/relays. Reverify it before design or deployment. Do not
route order activity through a VPS. Keep credentials outside code, logs, artifacts and
frontend responses. Read-only research hosting is a separate decision. ProjectX API
execution is currently unavailable for Live Funded accounts; never promise this bot can run
there without a verified supported route.

## ACCEPTANCE AND HANDOFF

Deliver working source, clear startup commands, configuration examples, meaningful failure
tests, research results with provenance, a trade journal, architecture ownership map and a
documented operating/recovery procedure. Declare what is implemented, locally tested,
externally verified, still unproven or blocked.

A profitable result cannot be guaranteed by architecture or prompting. If the tested
strategy fails to establish positive net expectancy and acceptable risk, say so and report
the evidence. Do not manufacture metrics, hide failed variants, optimize repeatedly against
the final test set or change rules after seeing results without versioning them. Never
request API secrets in chat.
