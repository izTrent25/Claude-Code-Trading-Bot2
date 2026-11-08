#!/usr/bin/env python3
"""Does being above or below the session VWAP predict the next 30/60 minutes?

For every trading day: VWAP anchored at 08:30 Chicago (typical price x volume, cumulative).
At fixed checkpoints (bar start times), record whether the close is above VWAP and the
forward move in points over the next 30 and 60 minutes. Compare above vs below, with a
day-resampled bootstrap on the difference. No strategy, no costs: a pure measurement.

Usage: .venv/bin/python research/vwap_measure.py [--symbol NQ] [--years 2010-2020] [--draws 3000]
"""
import argparse, json, random, statistics
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINTS = ['09:00', '10:00', '11:00', '13:00']
HORIZONS = (30, 60)


def parse_years(s):
    a, b = s.split('-'); return list(range(int(a), int(b) + 1))


def samples_for_year(symbol, year):
    df = pd.read_parquet(ROOT / 'data' / 'futures' / symbol / f'{year}.parquet')
    df = df.tz_convert('America/Chicago')
    df = df[df.index.strftime('%H:%M') >= '08:30']           # regular session only
    df = df[df.index.strftime('%H:%M') < '15:00']
    out = []
    for day, g in df.groupby(df.index.date):
        if len(g) < 120: continue                              # skip holidays / broken days
        tp = (g['high'] + g['low'] + g['close']) / 3
        vwap = (tp * g['volume']).cumsum() / g['volume'].cumsum().replace(0, float('nan'))
        avg_range = float((g['high'] - g['low']).mean())
        clocks = g.index.strftime('%H:%M')
        for cp in CHECKPOINTS:
            hit = g.index[clocks == cp]
            if len(hit) == 0: continue
            t = hit[0]; c0 = float(g.at[t, 'close']); v = float(vwap.at[t])
            if pd.isna(v): continue
            rec = {'day': str(day), 'cp': cp, 'above': c0 > v, 'dist_pts': c0 - v, 'avg_range': avg_range}
            for h in HORIZONS:
                c1 = g['close'].asof(t + pd.Timedelta(minutes=h))
                rec[f'fwd{h}'] = float(c1 - c0) if pd.notna(c1) else None
            out.append(rec)
    return out


def summarize(samples, cp, h, draws, seed=11):
    rows = [s for s in samples if s['cp'] == cp and s[f'fwd{h}'] is not None]
    above = [s for s in rows if s['above']]; below = [s for s in rows if not s['above']]
    def stats(xs):
        f = [x[f'fwd{h}'] for x in xs]; r = [x[f'fwd{h}'] / x['avg_range'] for x in xs]
        return {'n': len(f), 'mean_pts': round(statistics.mean(f), 3), 'mean_in_avg_ranges': round(statistics.mean(r), 3),
                'pct_up': round(100 * sum(x > 0 for x in f) / len(f), 1)} if f else None
    a, b = stats(above), stats(below)
    # bootstrap the difference (above mean - below mean, in avg-range units) by resampling days
    by_day = {}
    for s in rows: by_day.setdefault(s['day'], []).append(s)
    days = list(by_day.values()); rng = random.Random(seed); diffs = []
    for _ in range(draws):
        pick = [days[rng.randrange(len(days))] for _ in range(len(days))]
        fa = [s[f'fwd{h}'] / s['avg_range'] for d in pick for s in d if s['above']]
        fb = [s[f'fwd{h}'] / s['avg_range'] for d in pick for s in d if not s['above']]
        if fa and fb: diffs.append(statistics.mean(fa) - statistics.mean(fb))
    diffs.sort(); q = lambda p: round(diffs[min(len(diffs) - 1, int(p * len(diffs)))], 3)
    # per-year sign of the difference
    years = sorted({s['day'][:4] for s in rows}); yr = {}
    for y in years:
        fa = [s[f'fwd{h}'] for s in rows if s['day'].startswith(y) and s['above']]
        fb = [s[f'fwd{h}'] for s in rows if s['day'].startswith(y) and not s['above']]
        yr[y] = round(statistics.mean(fa) - statistics.mean(fb), 2) if fa and fb else None
    return {'checkpoint': cp, 'horizon_min': h, 'above': a, 'below': b,
            'diff_above_minus_below_in_avg_ranges': {'p5': q(.05), 'p50': q(.5), 'p95': q(.95)},
            'years_where_above_beats_below': sum(1 for v in yr.values() if v is not None and v > 0), 'years': len(yr), 'by_year_diff_pts': yr}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--symbol', default='NQ'); ap.add_argument('--years', default='2010-2020'); ap.add_argument('--draws', type=int, default=3000)
    a = ap.parse_args(); years = parse_years(a.years)
    samples = []
    for y in years:
        s = samples_for_year(a.symbol, y); samples += s; print(f'  {y}: {len(s)} checkpoint samples', flush=True)
    results = [summarize(samples, cp, h, a.draws) for cp in CHECKPOINTS for h in HORIZONS]
    out = ROOT / 'research' / 'results' / 'vwap_measure'; out.mkdir(parents=True, exist_ok=True)
    (out / 'summary.json').write_text(json.dumps({'symbol': a.symbol, 'years': a.years, 'samples': len(samples), 'results': results}, indent=2))
    pd.DataFrame(samples).to_csv(out / 'samples.csv', index=False)
    print('\n| Checkpoint | Next | Above VWAP: n, mean pts, % up | Below VWAP: n, mean pts, % up | Above minus below (avg-range units, 90% range) | Years above beats below |')
    print('|---|---|---|---|---|---|')
    for r in results:
        A, B, d = r['above'], r['below'], r['diff_above_minus_below_in_avg_ranges']
        print(f"| {r['checkpoint']} | {r['horizon_min']}m | {A['n']}, {A['mean_pts']:+.2f}, {A['pct_up']}% | {B['n']}, {B['mean_pts']:+.2f}, {B['pct_up']}% | {d['p50']:+.3f} ({d['p5']:+.3f} to {d['p95']:+.3f}) | {r['years_where_above_beats_below']} of {r['years']} |")


if __name__ == '__main__':
    main()
