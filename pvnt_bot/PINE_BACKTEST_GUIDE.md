# Backtest the Pine strategy in TradingView

## 1. Load the right chart

Open TradingView Supercharts and select MNQ. Prefer the actual dated futures contract used
in your Python data when comparing systems. A continuous chart such as MNQ1! can be useful
for exploration, but roll adjustment and stitching may change sweep levels and fills. Do
not treat it as identical to one dated contract.

Select 1 minute, standard candles. Do not use Heikin Ashi, Renko, or synthetic candles.
Confirm the feed and historical data you can access. Your TradingView subscription/data
entitlements control available history; this package does not unlock additional bars or
Deep Backtesting.

## 2. Add the actual strategy

1. Open PVNT_SMC_Research.pine in a text editor.
2. Copy ALL code, starting with `//@version=6`.
3. Open TradingView's Pine Editor (its location may vary with the layout).
4. Create a new blank strategy/script, delete its template, and paste the code.
5. Save as PVNT SMC Research v0.1.
6. Click Add to chart or the current equivalent.
7. Resolve any compiler message before proceeding. This source was authored against Pine
   v6 documentation but could not be compiled in TradingView during delivery. Preserve the
   exact error text and line if asking your developer to fix it.

This is a strategy() script, not an indicator() script. It will produce simulated Strategy
Tester trades without webhooks or a connected broker. Do not create execution alerts from
this research script.

## 3. Set test inputs

Open the strategy's gear/settings and its Inputs tab:

- Liquidity lookback: 20.
- Maximum bars after sweep: 5.
- Displacement multiple: 0.8.
- Target: 2R.
- Risk budget: $50; maximum 2 contracts; 3 proposals/day.
- Maximum hold: 45 one-minute bars.
- Context filter: OFF for the first test.
- Timezone: America/Chicago.
- Entry start: 835; entry end: 1430; flatten: 1455. Values are HHMM, without a colon.
- Select an explicit Test begins and Test ends period.
- Research daily loss: $250; EOD loss distance: $2,000; safety buffer: $250. These are
  local research settings, not a certified Topstep rule implementation.

The date range filters entries; bars loaded before the start may still warm indicators.
With default next-bar execution, an end-of-range close can occur after the selected end if
no eligible bar arrives exactly at the boundary. Check timestamps in the trade list.

## 4. Match costs and fill settings

In Properties, verify:

- Initial capital: $50,000, USD.
- Pyramiding: 0.
- Commission: cash per contract, $0.75 per side as the example default. Replace with your
  actual all-in estimated costs. TradingView charges the configured commission on both
  entry and exit.
- Slippage: 2 ticks example default.
- Verify-price/limit fill assumption: 1 tick.
- Process orders on bar close: OFF.
- Recalculate on every tick: OFF.
- Recalculate after order fills: OFF.
- Margin: the supplied 1% setting is a research emulator setting, not Topstep margin or
  contract-cap rules.

The Inputs values labeled Sizing: commission and Sizing: slippage only estimate position
size. They do not set TradingView's Properties. Keep both sets consistent after changing
costs. The actual next-bar fill may still differ from the close-based sizing estimate.

If your account/UI offers Bar Magnifier, enable it for a second test. Newer interfaces may
label historical price detail as Bar detalization or similar; choose higher granularity
where available. It uses additional intrabar detail but cannot recreate queue priority,
exact latency or exchange matching. Record which setting you used rather than silently
mixing results.

TradingView documents next-tick fills, emulator assumptions, slippage, commission, and
historical detail here: https://www.tradingview.com/pine-script-docs/concepts/strategies/

## 5. Inspect Strategy Tester

Open Strategy Tester or the current strategy report panel. Review:

- Net profit AFTER commission and slippage.
- Number of trades and time coverage.
- Profit factor, win rate and average trade.
- Maximum drawdown and largest losses.
- Long/short results separately.
- Trade distribution and whether a few winners produce most profits.

Open the trade list. Inspect at least 15–20 entries and exits on the chart, including losing
trades, gaps, session endings and candles that touch both exit levels. Signal triangles show
confirmation, not guaranteed filled trades. A signal may be blocked by risk, session,
position or sizing rules.

If no trades appear, check that enough one-minute history exists, dates overlap loaded
bars, the Chicago entry window is represented, minimum contract risk fits the $50 budget,
and the strategy has not hit its research loss guard. Do not remove every constraint just
to make the report populate.

## 6. Use a development/validation/final-test split

Choose three chronological blocks of sufficient real history before tuning. As an
illustrative allocation only, use 60% development / 20% validation / 20% untouched test.
Develop on the first block. Check robustness on the second. Freeze rules, costs, settings
and acceptance criteria BEFORE opening the final block. If you tune after seeing the final
results, it becomes development data and you need a new untouched test.

Record every variant, including failed ones. Test higher slippage and fees, nearby settings,
separate months, long/short directions and volatility conditions. Export trades using the
report's export function if your plan supports it. Keep your settings and date windows with
each export.

## 7. Forward-test the Pine strategy

Keep the exact frozen strategy on the one-minute chart and observe newly completed bars
during market hours. Record signals and Strategy Tester simulated fills as they occur. This
is Pine's broker emulator; connecting TradingView Paper Trading does NOT automatically make
a Pine strategy execute through that account.

## 8. Compare Pine and Python honestly

| Item | Python starter | Pine starter |
|---|---|---|
| Core setup | Prior-N sweep, later displacement/structure break | Same definition |
| Entry | Next bar open plus slippage | TradingView next available tick, normally next open |
| Sizing | Uses simulated next-open entry | Uses signal-close entry estimate |
| Target | Based on simulated entry | Based on signal-close estimated entry |
| Both exits in one candle | Adverse/stop-first assumption | TradingView price-path/detail model |
| Target qualification | One-tick penetration | Emulator limit verification setting |
| Account guard | Conservative OHLC risk threshold plus close checks | Equity guard evaluated on script calculations, normally closes |
| HTF filter | Full UTC-epoch-aligned 15m/90m buckets | TradingView exchange/session-aligned completed HTF candles |
| Data gaps | Clears Python history/context; flattens next open | Clears setup; waits N bars; requests close at next observed calculation |
| Session reset | Chicago calendar-day approximation | Configured calendar-day approximation |
| Max proposals | Counts actual paper entries | Counts submitted entry proposals |
| Historical range | Exactly the CSV supplied | Available chart/plan history |
| Drawdown | Close-marked series | TradingView's own report calculation |

These differences can change individual trades and results. This is a shared core strategy,
not verified tick-for-tick parity. Disable context initially; compare identical contract/data
timestamps and SIGNALS first, then fills.

The [1] HTF offset with lookahead_on is intentional: it requests previously completed HTF
candles, not future values. Do not remove the offset.
https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/

## What is not included

No original PVNT SSM code, FVG retracement logic, order blocks, order-flow data,
learned/adaptive strategy, guaranteed profits, automatic parameter optimization, or account
execution alerts. Those require separate implementation and evidence.
