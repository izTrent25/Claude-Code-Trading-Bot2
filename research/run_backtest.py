#!/usr/bin/env python3
"""Headless historical research runner for the pvnt_bot Engine on the Parquet futures store.

Runs the exact Engine/Strategy from pvnt_bot/engine.py over data/futures/<SYMBOL>/<YEAR>.parquet,
year by year, and writes trades + a summary. Nothing here places orders.

Examples
  .venv/bin/python research/run_backtest.py --symbol NQ --years 2010-2020 --tag smc_2010_2020
  .venv/bin/python research/run_backtest.py --symbol NQ --years 2010-2020 --strategy random \
      --seeds 20 --match-trades 1234 --tag random_2010_2020
"""
import argparse, json, sys, time, random, statistics, csv, math
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'pvnt_bot'))
from engine import Bar, Engine, Strategy  # noqa: E402
from vwap_orb_fvg import VwapOrbFvgStrategy  # noqa: E402

# Settings the VWAP/ORB/FVG spec asks for (research/SPEC_vwap_orb_fvg.md); --set still overrides.
VOF_DEFAULTS = {'risk_per_trade': 20, 'reward_risk': 1.5, 'max_hold_bars': 60, 'entry_start': '08:45'}

# --- speed patch: cache each bar's parsed datetime (the engine parses it ~6 times per bar).
_orig_dt = Bar.dt
def _cached_dt(self):
    d = self.__dict__.get('_dt')
    if d is None:
        d = _orig_dt(self); self.__dict__['_dt'] = d
    return d
Bar.dt = _cached_dt


def parse_years(s):
    if '-' in s:
        a, b = s.split('-'); return list(range(int(a), int(b) + 1))
    return [int(x) for x in s.split(',')]


def load_year(symbol, year):
    import pandas as pd
    df = pd.read_parquet(ROOT / 'data' / 'futures' / symbol / f'{year}.parquet')
    if str(df.index.tz) != 'UTC':
        df.index = df.index.tz_convert('UTC')
    ts = df.index.strftime('%Y-%m-%dT%H:%M:%S+00:00')
    cols = [df[c].astype(float).tolist() for c in ('open', 'high', 'low', 'close', 'volume')]
    return [Bar(t, o, h, l, c, v) for t, o, h, l, c, v in zip(ts, *cols)]


class RandomStrategy(Strategy):
    """Random-entry control with the same session, stop geometry, target, hold and risk rules.
    Fires a random long/short proposal with probability p per bar; stop sits one tick beyond
    the prior-N-bar extreme (the same structural anchor the SMC rule uses)."""
    def __init__(self, c, p, seed):
        super().__init__(c); self.p = p; self.rng = random.Random(seed)
    def on_bar(self, b):
        self.i += 1; self.update_context(b); signal = None
        past = list(self.bars); n = self.c['lookback']
        if len(past) >= n and self.rng.random() < self.p:
            side = 1 if self.rng.random() < 0.5 else -1
            lo = min(x.low for x in past[-n:]); hi = max(x.high for x in past[-n:])
            stop = min(lo, b.low) - self.c['tick_size'] if side == 1 else max(hi, b.high) + self.c['tick_size']
            signal = {'side': side, 'stop': stop, 'signal_time': b.timestamp, 'reason': 'random baseline'}
        self.bars.append(b)
        return signal


class RandomDirection(VwapOrbFvgStrategy):
    """Control: the real strategy's signals and stop distances, but the side is a coin toss.
    A flipped trade's stop is mirrored around the signal bar's close so the distance is kept."""
    def __init__(self, c, seed):
        super().__init__(c); self.rng = random.Random(seed)
    def on_bar(self, b):
        s = super().on_bar(b)
        if s and self.rng.random() < 0.5:
            s = {**s, 'side': -s['side'], 'stop': b.close + (b.close - s['stop']), 'reason': 'random-direction control'}
        return s


def build_config(args):
    c = json.loads((ROOT / 'pvnt_bot' / 'config.json').read_text())
    if args.strategy in ('vwap_orb_fvg', 'vof_randdir'):
        c.update(VOF_DEFAULTS)
    if args.mode == 'research':
        c['loss_distance'] = 1e9  # disables the permanent account-failure halt; daily loss stop stays on
    for kv in args.set or []:
        k, v = kv.split('=', 1)
        try: v = json.loads(v)
        except ValueError: pass
        c[k] = v
    return c


def run_one(symbol, years, c, strategy, p=0.0, seed=0, progress=False):
    e = Engine(c)
    if strategy == 'random':
        e.strategy = RandomStrategy(c, p, seed)
    elif strategy == 'vwap_orb_fvg':
        e.strategy = VwapOrbFvgStrategy(c)
    elif strategy == 'vof_randdir':
        e.strategy = RandomDirection(c, seed)
    # count every proposal the strategy makes, so blocked/rejected ones are visible, not hidden
    e.signals = 0; _on_bar = e.strategy.on_bar
    def counting_on_bar(b):
        s = _on_bar(b)
        if s: e.signals += 1
        return s
    e.strategy.on_bar = counting_on_bar
    session_bars = 0; tz = ZoneInfo(c['timezone']); t0 = time.time()
    for y in years:
        bars = load_year(symbol, y)
        for b in bars:
            e.process(b)
        # count bars inside the entry window (for calibrating the random control)
        for b in bars[::7]:  # sample every 7th bar for speed; scaled back below
            clock = b.dt().astimezone(tz).strftime('%H:%M')
            if c['entry_start'] <= clock < c['entry_end']: session_bars += 7
        if progress: print(f'  {symbol} {y}: {len(bars):,} bars, trades so far {len(e.trades):,}, {time.time()-t0:.0f}s', flush=True)
    e.finish()
    return e, session_bars


def metrics(e, c, years):
    t = e.trades; nets = [x['net'] for x in t]; rs = [x['r'] for x in t]
    gains = sum(x for x in nets if x > 0); losses = -sum(x for x in nets if x < 0)
    streak = worst = 0
    for x in nets:
        streak = streak + 1 if x < 0 else 0; worst = max(worst, streak)
    # drawdown of the closed-trade balance curve (independent of the engine's close-marked one)
    bal = c['initial_balance']; peak = bal; dd_closed = 0
    for x in nets:
        bal += x; peak = max(peak, bal); dd_closed = max(dd_closed, peak - bal)
    top5 = sorted(nets, reverse=True)[:5]
    by_year = {}
    for x in t:
        y = x['entry_time'][:4]; d = by_year.setdefault(y, {'trades': 0, 'net': 0.0})
        d['trades'] += 1; d['net'] = round(d['net'] + x['net'], 2)
    by_side = {}
    for s, name in ((1, 'long'), (-1, 'short')):
        n_ = [x['net'] for x in t if x['side'] == s]
        by_side[name] = {'trades': len(n_), 'net': round(sum(n_), 2), 'win_rate': round(100 * sum(x > 0 for x in n_) / len(n_), 1) if n_ else None}
    return {
        'years': f'{years[0]}-{years[-1]}', 'signals': getattr(e, 'signals', None), 'trades': len(t),
        'signals_not_traded': (getattr(e, 'signals', 0) - len(t)) if hasattr(e, 'signals') else None,
        'net_usd': round(sum(nets), 2),
        'net_pct_of_initial': round(100 * sum(nets) / c['initial_balance'], 2),
        'final_balance': round(e.balance, 2), 'win_rate_pct': round(100 * sum(x > 0 for x in nets) / len(nets), 1) if nets else None,
        'profit_factor': round(gains / losses, 3) if losses else None,
        'expectancy_usd': round(statistics.mean(nets), 2) if nets else None,
        'expectancy_r': round(statistics.mean(rs), 3) if rs else None,
        'median_r': round(statistics.median(rs), 3) if rs else None,
        'avg_win_usd': round(statistics.mean([x for x in nets if x > 0]), 2) if gains else None,
        'avg_loss_usd': round(statistics.mean([x for x in nets if x < 0]), 2) if losses else None,
        'max_losing_streak': worst,
        'max_drawdown_close_marked_usd': round(e.max_dd, 2), 'max_drawdown_closed_trades_usd': round(dd_closed, 2),
        'avg_bars_in_trade': round(statistics.mean([x['bars'] for x in t]), 1) if t else None,
        'avg_contracts': round(statistics.mean([x['qty'] for x in t]), 2) if t else None,
        'top5_trades_usd': [round(x, 2) for x in top5], 'net_without_top5_usd': round(sum(nets) - sum(top5), 2),
        'exit_reasons': dict(Counter(x['reason'] for x in t)),
        'by_year': by_year, 'by_side': by_side,
        'account_halted': e.halted, 'bars_processed': e.count,
    }


def _job(a):
    symbol, years, c, strategy, p, seed = a
    e, sb = run_one(symbol, years, c, strategy, p, seed)
    return seed, metrics(e, c, years), e.trades, sb


def write_results(out, name, m, trades, c):
    out.mkdir(parents=True, exist_ok=True)
    (out / f'{name}_summary.json').write_text(json.dumps({'config': c, 'metrics': m}, indent=2))
    with open(out / f'{name}_trades.csv', 'w', newline='') as f:
        fields = ['signal_time', 'entry_time', 'exit_time', 'side', 'qty', 'entry', 'stop', 'target', 'exit', 'bars', 'initial_risk', 'net', 'r', 'reason']
        w = csv.DictWriter(f, fields, extrasaction='ignore'); w.writeheader(); w.writerows(trades)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--symbol', default='NQ'); ap.add_argument('--years', default='2010-2020')
    ap.add_argument('--strategy', choices=['smc', 'random', 'vwap_orb_fvg', 'vof_randdir'], default='smc')
    ap.add_argument('--mode', choices=['account', 'research'], default='research',
                    help='account = package defaults incl. permanent account-failure halt; research = that halt disabled')
    ap.add_argument('--set', action='append', help='override config, e.g. --set use_context=true')
    ap.add_argument('--tag', required=True); ap.add_argument('--seeds', type=int, default=1)
    ap.add_argument('--p', type=float, default=None, help='random: per-bar proposal probability')
    ap.add_argument('--match-trades', type=int, default=None, help='random: calibrate p to land near this trade count')
    ap.add_argument('--jobs', type=int, default=4)
    args = ap.parse_args()
    years = parse_years(args.years); c = build_config(args); out = ROOT / 'research' / 'results' / args.tag
    print(f'== {args.tag}: {args.strategy} on {args.symbol} {years[0]}-{years[-1]}, mode={args.mode}', flush=True)
    if args.strategy in ('smc', 'vwap_orb_fvg'):
        e, sb = run_one(args.symbol, years, c, args.strategy, progress=True)
        m = metrics(e, c, years); m['session_bars_est'] = sb
        write_results(out, 'smc', m, e.trades, c)
        print(json.dumps(m, indent=2)); return
    # random controls (random entries, or the real strategy with random direction)
    p = args.p
    if args.strategy == 'vof_randdir':
        p = 0.0
    elif p is None:
        if not args.match_trades: ap.error('random needs --p or --match-trades')
        # pilot run to calibrate: start from trades / session bars, then scale once
        e0, sb = run_one(args.symbol, years, c, 'random', p=0.0005, seed=12345)
        got = len(e0.trades); p = 0.0005 * args.match_trades / max(got, 1)
        print(f'calibration: p=0.0005 gave {got} trades; using p={p:.6f} to target {args.match_trades}', flush=True)
    jobs = [(args.symbol, years, c, args.strategy, p, s) for s in range(args.seeds)]
    results = []
    with ProcessPoolExecutor(max_workers=args.jobs) as ex:
        for seed, m, trades, sb in ex.map(_job, jobs):
            results.append(m); write_results(out, f'random_seed{seed}', m, trades, c)
            print(f'  seed {seed}: trades {m["trades"]}, net ${m["net_usd"]:,.0f}, PF {m["profit_factor"]}, exp R {m["expectancy_r"]}', flush=True)
    def dist(key):
        v = [r[key] for r in results if r[key] is not None]
        return {'min': min(v), 'median': statistics.median(v), 'max': max(v)} if v else None
    agg = {'seeds': len(results), 'p': p, 'trades': dist('trades'), 'net_usd': dist('net_usd'), 'profit_factor': dist('profit_factor'),
           'expectancy_r': dist('expectancy_r'), 'win_rate_pct': dist('win_rate_pct'), 'max_drawdown_closed_trades_usd': dist('max_drawdown_closed_trades_usd'),
           'seeds_profitable': sum(1 for r in results if r['net_usd'] > 0)}
    (out / 'random_aggregate.json').write_text(json.dumps({'config': c, 'aggregate': agg, 'per_seed': results}, indent=2))
    print(json.dumps(agg, indent=2))


if __name__ == '__main__':
    main()
