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
from tjr import TjrStrategy  # noqa: E402
from orb import OrbStrategy  # noqa: E402
from supertrend import SuperTrendStrategy  # noqa: E402
from gap_fade import GapFadeStrategy  # noqa: E402
from last_half_hour import LastHalfHourStrategy  # noqa: E402
from overnight_drift import OvernightDriftStrategy  # noqa: E402
from turn_of_month import TurnOfMonthStrategy  # noqa: E402
from noise_momentum import NoiseMomentumStrategy  # noqa: E402
from orb_candle import OrbCandleStrategy  # noqa: E402

# Settings the VWAP/ORB/FVG spec asks for (research/SPEC_vwap_orb_fvg.md); --set still overrides.
VOF_DEFAULTS = {'risk_per_trade': 20, 'reward_risk': 1.5, 'max_hold_bars': 60, 'entry_start': '08:45'}
# Settings the TJR spec asks for (research/SPEC_tjr.md): NY open window, out by 11 AM ET, 3/day, 2-loss stop.
TJR_DEFAULTS = {'entry_start': '08:35', 'entry_end': '09:30', 'flatten_time': '10:00', 'max_hold_bars': 120,
                'max_trades_per_day': 3, 'max_consecutive_losses': 2, 'risk_per_trade': 500, 'daily_loss': 5000}
# Settings the ORB spec asks for (research/SPEC_orb.md): research sizing, no time stop, entries from the open.
# entry_end is 11:01 so a fill at the 11:00 bar's open passes the engine's window check; the strategy itself
# requires the breakout bar to close by 11:00.
ORB_DEFAULTS = {'entry_start': '08:30', 'entry_end': '11:01', 'max_hold_bars': 1000, 'risk_per_trade': 500, 'daily_loss': 5000}
# Settings the SuperTrend spec asks for (research/SPEC_supertrend.md): one fixed contract, no stop fills between bars,
# no time stop, no day guard. Version A (supertrend) also holds overnight; version B (supertrend_day) keeps the session rules.
ST_COMMON = {'use_target': False, 'intrabar_stop': False, 'risk_per_trade': 1e9, 'max_contracts': 1, 'daily_loss': 1e9, 'max_hold_bars': 10**9, 'max_trades_per_day': 100}
ST_A_DEFAULTS = {**ST_COMMON, 'hold_overnight': True}
ST_B_DEFAULTS = {**ST_COMMON, 'entry_start': '08:30', 'entry_end': '14:30', 'flatten_time': '14:55'}
# The six evidence-backed candidates of 8 Nov 2026 (research/SPEC_gap_fade.md and friends): one fixed contract each.
FIXED1 = {'risk_per_trade': 1e9, 'max_contracts': 1, 'daily_loss': 1e9, 'max_hold_bars': 10**9, 'max_trades_per_day': 50, 'use_target': False}
GF_DEFAULTS = {**FIXED1, 'entry_start': '08:30', 'entry_end': '08:45', 'flatten_time': '10:30', 'intrabar_stop': True}
LH_DEFAULTS = {**FIXED1, 'entry_start': '14:20', 'entry_end': '14:35', 'flatten_time': '14:55', 'intrabar_stop': False}
OD_DEFAULTS = {**FIXED1, 'hold_overnight': True, 'intrabar_stop': False}
TM_DEFAULTS = {**FIXED1, 'hold_overnight': True, 'intrabar_stop': False}
NM_DEFAULTS = {**FIXED1, 'entry_start': '08:30', 'entry_end': '14:31', 'flatten_time': '14:55', 'intrabar_stop': False}
OC_DEFAULTS = {**FIXED1, 'entry_start': '08:30', 'entry_end': '08:40', 'flatten_time': '14:55', 'intrabar_stop': True}

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


def load_year(symbol, year, bars=1):
    import pandas as pd
    df = pd.read_parquet(ROOT / 'data' / 'futures' / symbol / f'{year}.parquet')
    if str(df.index.tz) != 'UTC':
        df.index = df.index.tz_convert('UTC')
    if bars > 1:  # build N-minute bars from the one-minute store; bins align to the clock (UTC, whole hours = Chicago)
        df = df.resample(f'{bars}min', label='left', closed='left').agg(
            {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}).dropna(subset=['open'])
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


def random_direction(base):
    """Control: the real strategy's signals and distances, but the side is a coin toss. A flipped
    trade's stop, target and limit are mirrored around the signal bar's close so geometry is kept."""
    class RandomDirection(base):
        def __init__(self, c, seed):
            super().__init__(c); self.rng = random.Random(seed)
        def on_bar(self, b):
            s = super().on_bar(b)
            if s and self.rng.random() < 0.5:
                s = {**s, 'side': -s['side'], 'stop': b.close + (b.close - s['stop']), 'reason': 'random-direction control'}
                for k in ('target', 'limit'):
                    if s.get(k) is not None: s[k] = b.close + (b.close - s[k])
            return s
    return RandomDirection


# name -> (factory(c, seed), defaults, is_seeded_control). Seeded controls run through the multi-seed path.
REGISTRY = {
    'gap_fade': (lambda c, seed: GapFadeStrategy(c), GF_DEFAULTS, False),
    'gap_fade_randdir': (lambda c, seed: random_direction(GapFadeStrategy)(c, seed), GF_DEFAULTS, True),
    'last_half_hour': (lambda c, seed: LastHalfHourStrategy(c), LH_DEFAULTS, False),
    'last_half_hour_randdir': (lambda c, seed: random_direction(LastHalfHourStrategy)(c, seed), LH_DEFAULTS, True),
    'overnight_drift': (lambda c, seed: OvernightDriftStrategy(c), OD_DEFAULTS, False),
    'overnight_drift_randdir': (lambda c, seed: random_direction(OvernightDriftStrategy)(c, seed), OD_DEFAULTS, True),
    'overnight_drift_randhour': (lambda c, seed: OvernightDriftStrategy(c, random_hour_seed=seed), OD_DEFAULTS, True),
    'turn_of_month': (lambda c, seed: TurnOfMonthStrategy(c), TM_DEFAULTS, False),
    'turn_of_month_randdays': (lambda c, seed: TurnOfMonthStrategy(c, random_seed=seed), TM_DEFAULTS, True),
    'noise_momentum': (lambda c, seed: NoiseMomentumStrategy(c), NM_DEFAULTS, False),
    'noise_momentum_randdir': (lambda c, seed: random_direction(NoiseMomentumStrategy)(c, seed), NM_DEFAULTS, True),
    'orb_candle': (lambda c, seed: OrbCandleStrategy(c), OC_DEFAULTS, False),
    'orb_candle_randdir': (lambda c, seed: random_direction(OrbCandleStrategy)(c, seed), OC_DEFAULTS, True),
}


def trading_days(symbol, years):
    """ISO dates (Chicago) that have a bar at 08:30 CT, read from the store's index only. Never reads years outside `years`."""
    import pandas as pd
    days = set()
    for y in years:
        idx = pd.read_parquet(ROOT / 'data' / 'futures' / symbol / f'{y}.parquet', columns=['open']).index
        local = idx.tz_convert('America/Chicago')
        opens = local[(local.hour == 8) & (local.minute == 30)]
        days.update(d.isoformat() for d in opens.date)
    return sorted(days)


def build_config(args):
    c = json.loads((ROOT / 'pvnt_bot' / 'config.json').read_text())
    if args.strategy in ('vwap_orb_fvg', 'vof_randdir'):
        c.update(VOF_DEFAULTS)
    if args.strategy in ('tjr', 'tjr_randdir'):
        c.update(TJR_DEFAULTS)
    if args.strategy in ('orb', 'orb_randdir'):
        c.update(ORB_DEFAULTS)
    if args.strategy in ('supertrend', 'supertrend_randdir'):
        c.update(ST_A_DEFAULTS)
    if args.strategy in ('supertrend_day', 'supertrend_day_randdir'):
        c.update(ST_B_DEFAULTS)
    if args.strategy in REGISTRY:
        c.update(REGISTRY[args.strategy][1])
    if args.mode == 'research':
        c['loss_distance'] = 1e9  # disables the permanent account-failure halt; daily loss stop stays on
    if args.bars > 1:
        c['bar_seconds'] = args.bars * 60
    for kv in args.set or []:
        k, v = kv.split('=', 1)
        try: v = json.loads(v)
        except ValueError: pass
        c[k] = v
    return c


def run_one(symbol, years, c, strategy, p=0.0, seed=0, progress=False):
    bars = max(1, int(c.get('bar_seconds', 60)) // 60)
    e = Engine(c)
    if strategy == 'random':
        e.strategy = RandomStrategy(c, p, seed)
    elif strategy == 'vwap_orb_fvg':
        e.strategy = VwapOrbFvgStrategy(c)
    elif strategy == 'vof_randdir':
        e.strategy = random_direction(VwapOrbFvgStrategy)(c, seed)
    elif strategy == 'tjr':
        e.strategy = TjrStrategy(c)
    elif strategy == 'tjr_randdir':
        e.strategy = random_direction(TjrStrategy)(c, seed)
    elif strategy == 'orb':
        e.strategy = OrbStrategy(c)
    elif strategy == 'orb_randdir':
        e.strategy = random_direction(OrbStrategy)(c, seed)
    elif strategy in ('supertrend', 'supertrend_day'):
        e.strategy = SuperTrendStrategy(c)
    elif strategy in ('supertrend_randdir', 'supertrend_day_randdir'):
        e.strategy = random_direction(SuperTrendStrategy)(c, seed)
    elif strategy in REGISTRY:
        e.strategy = REGISTRY[strategy][0](c, seed)
    # count every proposal the strategy makes, so blocked/rejected ones are visible, not hidden
    e.signals = 0; _on_bar = e.strategy.on_bar
    def counting_on_bar(b):
        s = _on_bar(b)
        if s: e.signals += 1
        return s
    e.strategy.on_bar = counting_on_bar
    session_bars = 0; tz = ZoneInfo(c['timezone']); t0 = time.time()
    for y in years:
        ybars = load_year(symbol, y, bars)
        for b in ybars:
            e.process(b)
        # count bars inside the entry window (for calibrating the random control)
        for b in ybars[::7]:  # sample every 7th bar for speed; scaled back below
            clock = b.dt().astimezone(tz).strftime('%H:%M')
            if c['entry_start'] <= clock < c['entry_end']: session_bars += 7
        if progress: print(f'  {symbol} {y}: {len(ybars):,} bars of {bars}m, trades so far {len(e.trades):,}, {time.time()-t0:.0f}s', flush=True)
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
        'strategy_stats': dict(sorted(getattr(e.strategy, 'stats', {}).items())),
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
    ap.add_argument('--strategy', choices=['smc', 'random', 'vwap_orb_fvg', 'vof_randdir', 'tjr', 'tjr_randdir', 'orb', 'orb_randdir', 'supertrend', 'supertrend_day', 'supertrend_randdir', 'supertrend_day_randdir'] + sorted(REGISTRY), default='smc')
    ap.add_argument('--mode', choices=['account', 'research'], default='research',
                    help='account = package defaults incl. permanent account-failure halt; research = that halt disabled')
    ap.add_argument('--set', action='append', help='override config, e.g. --set use_context=true')
    ap.add_argument('--bars', type=int, default=1, help='bar size in minutes; >1 resamples the one-minute store (default 1)')
    ap.add_argument('--tag', required=True); ap.add_argument('--seeds', type=int, default=1)
    ap.add_argument('--p', type=float, default=None, help='random: per-bar proposal probability')
    ap.add_argument('--match-trades', type=int, default=None, help='random: calibrate p to land near this trade count')
    ap.add_argument('--jobs', type=int, default=4)
    args = ap.parse_args()
    years = parse_years(args.years); c = build_config(args); out = ROOT / 'research' / 'results' / args.tag
    if args.strategy.startswith('turn_of_month'):
        c['tom_trading_days'] = trading_days(args.symbol, years)
    print(f'== {args.tag}: {args.strategy} on {args.symbol} {years[0]}-{years[-1]}, mode={args.mode}', flush=True)
    if args.strategy in ('smc', 'vwap_orb_fvg', 'tjr', 'orb', 'supertrend', 'supertrend_day') or (args.strategy in REGISTRY and not REGISTRY[args.strategy][2]):
        e, sb = run_one(args.symbol, years, c, args.strategy, progress=True)
        m = metrics(e, c, years); m['session_bars_est'] = sb
        write_results(out, 'smc', m, e.trades, c)
        print(json.dumps(m, indent=2)); return
    # random controls (random entries, or the real strategy with random direction)
    p = args.p
    if args.strategy in ('vof_randdir', 'tjr_randdir', 'orb_randdir', 'supertrend_randdir', 'supertrend_day_randdir') or args.strategy in REGISTRY:
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
