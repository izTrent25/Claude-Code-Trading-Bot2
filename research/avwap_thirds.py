#!/usr/bin/env python3
"""Add the three one-contract legs of an Anchored-VWAP pullback run into the three-contract strategy.

The legs (research/SPEC_avwap_pullback.md) propose identical entries, so the strategy's trade is the sum of
the same-entry trades of the TP1, TP2 and TP3 legs. Reads research/results/<tag>/ for each leg; with
--randdir it combines seed by seed from the random_seed<N>_trades.csv files instead.

  .venv/bin/python research/avwap_thirds.py --name av_bal_5m av_bal_5m_tp1 av_bal_5m_tp2 av_bal_5m_tp3
  .venv/bin/python research/avwap_thirds.py --name av_bal_5m_randdir --randdir av_bal_5m_tp1_randdir av_bal_5m_tp2_randdir av_bal_5m_tp3_randdir
"""
import argparse, csv, json, statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; RES = ROOT / 'research' / 'results'


def read_trades(path):
    with open(path, newline='') as f:
        return [{k: (float(v) if k in ('qty', 'entry', 'stop', 'target', 'exit', 'bars', 'initial_risk', 'net', 'r') and v != '' else v) for k, v in row.items()} for row in csv.DictReader(f)]


def combine(legs):
    """legs: list of trade lists. Returns the combined trades (one per signal) and a note on mismatches."""
    by_sig = [defaultdict(list) for _ in legs]
    for i, trades in enumerate(legs):
        for t in trades: by_sig[i][t['signal_time']].append(t)
    keys = [set(d) for d in by_sig]; common = set.intersection(*keys); union = set.union(*keys)
    out = []
    for k in sorted(common):
        parts = [d[k][0] for d in by_sig]
        net = sum(p['net'] for p in parts); risk = sum(p['initial_risk'] for p in parts)
        out.append({'signal_time': k, 'entry_time': parts[0]['entry_time'], 'side': parts[0]['side'], 'net': round(net, 2),
                    'r': round(net / risk, 4) if risk else 0.0, 'reasons': tuple(p['reason'] for p in parts), 'bars': max(p['bars'] for p in parts)})
    return out, {'common': len(common), 'only_in_some_legs': len(union - common)}


def metrics(trades, initial=50000.0):
    nets = [t['net'] for t in trades]; rs = [t['r'] for t in trades]
    gains = sum(x for x in nets if x > 0); losses = -sum(x for x in nets if x < 0)
    bal = initial; peak = bal; dd = 0.0
    for x in nets:
        bal += x; peak = max(peak, bal); dd = max(dd, peak - bal)
    by_year = defaultdict(float); n_year = Counter()
    for t in trades: by_year[t['entry_time'][:4]] += t['net']; n_year[t['entry_time'][:4]] += 1
    by_year = {y: {'net': round(v, 2), 'trades': n_year[y]} for y, v in sorted(by_year.items())}
    by_side = {}
    for s, name in (('1', 'long'), ('-1', 'short')):
        n_ = [t['net'] for t in trades if str(int(float(t['side']))) == s]
        by_side[name] = {'trades': len(n_), 'net': round(sum(n_), 2), 'win_rate': round(100 * sum(x > 0 for x in n_) / len(n_), 1) if n_ else None}
    return {'trades': len(nets), 'net_usd': round(sum(nets), 2), 'profit_factor': round(gains / losses, 3) if losses else None,
            'win_rate_pct': round(100 * sum(x > 0 for x in nets) / len(nets), 1) if nets else None,
            'expectancy_usd': round(statistics.mean(nets), 2) if nets else None, 'expectancy_r': round(statistics.mean(rs), 3) if rs else None,
            'avg_win_usd': round(statistics.mean([x for x in nets if x > 0]), 2) if gains else None,
            'avg_loss_usd': round(statistics.mean([x for x in nets if x < 0]), 2) if losses else None,
            'max_drawdown_closed_trades_usd': round(dd, 2), 'years_positive': sum(1 for v in by_year.values() if v['net'] > 0), 'years': len(by_year),
            'by_year': by_year, 'by_side': by_side, 'exit_mix': dict(Counter(' / '.join(t['reasons']) for t in trades).most_common(8))}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('tags', nargs=3, help='the TP1, TP2 and TP3 leg tags, in that order')
    ap.add_argument('--name', required=True); ap.add_argument('--randdir', action='store_true'); ap.add_argument('--seeds', type=int, default=8)
    a = ap.parse_args()
    if not a.randdir:
        legs = [read_trades(RES / t / 'smc_trades.csv') for t in a.tags]
        trades, note = combine(legs); m = metrics(trades); m['legs'] = {}
        for t in a.tags:
            s = json.loads((RES / t / 'smc_summary.json').read_text())['metrics']
            m['legs'][t] = {k: s[k] for k in ('trades', 'net_usd', 'profit_factor', 'win_rate_pct', 'expectancy_r', 'exit_reasons') if k in s}
            m['legs'][t]['by_year'] = {y: v['net'] for y, v in s['by_year'].items()}
        m['match'] = note
        out = RES / f'thirds_{a.name}.json'; out.write_text(json.dumps(m, indent=2)); print(json.dumps(m, indent=2)); return
    per_seed = []
    for seed in range(a.seeds):
        legs = [read_trades(RES / t / f'random_seed{seed}_trades.csv') for t in a.tags]
        trades, note = combine(legs); m = metrics(trades); m['seed'] = seed; m['match'] = note; per_seed.append(m)
        print(f"  seed {seed}: trades {m['trades']}, net ${m['net_usd']:,.0f}, PF {m['profit_factor']}, exp R {m['expectancy_r']}, years + {m['years_positive']}/{m['years']}, match {note}")
    def dist(key):
        v = [r[key] for r in per_seed if r[key] is not None]
        return {'min': min(v), 'median': statistics.median(v), 'max': max(v)} if v else None
    agg = {'seeds': len(per_seed), 'trades': dist('trades'), 'net_usd': dist('net_usd'), 'profit_factor': dist('profit_factor'),
           'expectancy_r': dist('expectancy_r'), 'win_rate_pct': dist('win_rate_pct'), 'seeds_profitable': sum(1 for r in per_seed if r['net_usd'] > 0)}
    out = RES / f'thirds_{a.name}.json'; out.write_text(json.dumps({'aggregate': agg, 'per_seed': per_seed}, indent=2)); print(json.dumps(agg, indent=2))


if __name__ == '__main__':
    main()
