"""TJR liquidity-sweep strategy, version 5. Research only; the exact rules live in
research/SPEC_tjr.md and this file must stay in step with them.

Runs on ONE-MINUTE bars and builds everything else itself: CME session bars (17:00-16:00 CT)
for the daily bias and previous-day levels, Asia / London / pre-market highs and lows, and
five-minute bars for the sweep, shift and fair value gap. The 1-minute bars give the trigger.

Same interface as engine.Strategy: on_bar(bar) -> proposal dict or None. Proposals carry an
explicit 'target' (the opposite liquidity pool) and, in limit mode, a 'limit' price; the Engine
owns sizing, fills, stops and exits.
"""
import math
from collections import deque, Counter
from datetime import timedelta
from zoneinfo import ZoneInfo


class TjrStrategy:
    def __init__(self, c):
        self.c = c; self.tz = ZoneInfo(c['timezone']); self.tick = c['tick_size']
        self.entry_mode = c.get('tjr_entry', 'trigger')          # 'trigger' = 1m BOS, 'limit' = 50% of the gap
        self.use_bias = bool(c.get('tjr_use_bias', True))
        self.shift_window = int(c.get('tjr_shift_bars', 6))      # 5m bars allowed between sweep and shift
        self.disp_mult = float(c.get('tjr_displacement', 0.8))   # shift body >= this x avg 5m range
        self.trigger_minutes = int(c.get('tjr_trigger_minutes', 60))
        self.min_rr = float(c.get('tjr_min_rr', 2.0))
        self.sweep_start = c.get('tjr_sweep_start', '08:30'); self.sweep_end = c.get('tjr_sweep_end', '09:30')
        # what kills a setup while waiting in the zone: 'zone' = a 1m close through the gap (v5.0),
        # 'sweep' = price trading back beyond the swept extreme (v5.1, as the write-up says)
        self.zone_invalidation = c.get('tjr_zone_invalidation', 'zone')
        self.windows = {'asia': ('19:00', '23:00'), 'london': ('01:00', '04:00'), 'pre': ('06:00', '08:30')}
        # attributes the Engine touches (compatibility only)
        self.bars = deque(maxlen=500); self.setup = None; self.building = {}; self.context = {15: None, 90: None}
        # session / daily state
        self.session_key = None; self.cur = None; self.prev = None
        self.daily = []; self.swing_high = None; self.swing_low = None; self.bias = 0
        # intraday state
        self.day = None; self._reset_day()
        self.stats = Counter()  # how many setups reach each stage; read by the research runner

    # ------------------------------------------------------------------ helpers
    def _reset_day(self):
        self.m5 = []; self.m5_bucket = None; self.m5_cur = None; self.m5_swing_high = None; self.m5_swing_low = None
        self.state = 'idle'; self.sw = None; self.zone = None; self.used = set()
        self.m1_recent = deque(maxlen=3); self.m1_swing = None; self.in_zone = False

    def _grid(self, price, side):
        q = price / self.tick
        return (math.floor(q) if side == 1 else math.ceil(q)) * self.tick

    def _avg_range(self):
        last = self.m5[-12:]
        return sum(x['h'] - x['l'] for x in last) / len(last) if len(last) >= 6 else None

    # ------------------------------------------------------------------ session + daily bias
    def _session_update(self, b, local, clock):
        key = (local + timedelta(days=1)).date() if local.hour >= 17 else local.date()
        if key != self.session_key:
            if self.cur is not None:
                self.prev = self.cur
                self._daily_close(self.cur)
            self.cur = {'o': b.open, 'h': b.high, 'l': b.low, 'c': b.close, 'asia': None, 'london': None, 'pre': None}
            self.session_key = key
        s = self.cur
        s['h'] = max(s['h'], b.high); s['l'] = min(s['l'], b.low); s['c'] = b.close
        for name, (a, z) in self.windows.items():
            if a <= clock < z:
                if s[name] is None: s[name] = [b.high, b.low]
                else: s[name][0] = max(s[name][0], b.high); s[name][1] = min(s[name][1], b.low)

    def _daily_close(self, s):
        self.daily.append({'o': s['o'], 'h': s['h'], 'l': s['l'], 'c': s['c']})
        d = self.daily; i = len(d) - 1
        # break of structure against the swings known before this bar
        if self.swing_high is not None and d[i]['c'] > self.swing_high: self.bias = 1
        if self.swing_low is not None and d[i]['c'] < self.swing_low: self.bias = -1
        # bar i-1 becomes a confirmed swing once bar i is complete
        if i >= 2:
            if d[i-1]['h'] > d[i-2]['h'] and d[i-1]['h'] > d[i]['h']: self.swing_high = d[i-1]['h']
            if d[i-1]['l'] < d[i-2]['l'] and d[i-1]['l'] < d[i]['l']: self.swing_low = d[i-1]['l']

    def _pools(self, side):
        """Liquidity levels for today: lows to sweep / highs to target (long), mirrored for short."""
        s = self.cur; out = {}
        if self.prev: out['pdl'] = self.prev['l']; out['pdh'] = self.prev['h']
        for name in ('asia', 'london', 'pre'):
            if s and s.get(name): out[name + '_h'] = s[name][0]; out[name + '_l'] = s[name][1]
        lows = {k: v for k, v in out.items() if k.endswith('l')}; highs = {k: v for k, v in out.items() if k.endswith('h')}
        return (lows, highs) if side == 1 else (highs, lows)

    # ------------------------------------------------------------------ five-minute bars
    def _m5_update(self, b, local, clock):
        bucket = (local.hour * 60 + local.minute) // 5
        done = None
        if self.m5_bucket is not None and bucket != self.m5_bucket:
            done = self.m5_cur; self.m5_cur = None
        if self.m5_cur is None:
            self.m5_cur = {'o': b.open, 'h': b.high, 'l': b.low, 'c': b.close, 'clock': clock, 't': b.timestamp}
            self.m5_bucket = bucket
        else:
            m = self.m5_cur; m['h'] = max(m['h'], b.high); m['l'] = min(m['l'], b.low); m['c'] = b.close
        return done

    def _m5_close(self, m, local):
        if m['clock'] < '06:00': return
        self.m5.append(m); n = len(self.m5)
        if n >= 3:  # confirm swings one bar late
            a, mid, z = self.m5[-3], self.m5[-2], self.m5[-1]
            if mid['h'] > a['h'] and mid['h'] > z['h']: self.m5_swing_high = mid['h']
            if mid['l'] < a['l'] and mid['l'] < z['l']: self.m5_swing_low = mid['l']
        self._m5_logic(m, local)

    def _m5_logic(self, m, local):
        side_allowed = [1, -1] if not self.use_bias else ([self.bias] if self.bias else [])
        st = self.stats
        if self.state == 'idle':
            if not (self.sweep_start <= m['clock'] < self.sweep_end): return
            st['5m bars in sweep window'] += 1
            if not side_allowed: st['no bias yet'] += 1; return
            for side in side_allowed:
                sweep_lv, _ = self._pools(side)
                for name, lv in sweep_lv.items():
                    if name in self.used: continue
                    swept = (m['o'] > lv and m['l'] < lv and m['c'] > lv) if side == 1 else (m['o'] < lv and m['h'] > lv and m['c'] < lv)
                    if swept:
                        structure = self.m5_swing_high if side == 1 else self.m5_swing_low
                        self.used.add(name); st['1 sweep'] += 1
                        if structure is None: st['x sweep without 5m structure'] += 1; return
                        self.sw = {'side': side, 'level': lv, 'name': name, 'extreme': m['l'] if side == 1 else m['h'],
                                   'i5': len(self.m5) - 1, 'structure': structure}
                        self.state = 'swept'; return
        elif self.state in ('swept', 'shift_wait'):
            sw = self.sw; side = sw['side']; age = len(self.m5) - 1 - sw['i5']
            sw['extreme'] = min(sw['extreme'], m['l']) if side == 1 else max(sw['extreme'], m['h'])
            breakout = (m['c'] < sw['level']) if side == 1 else (m['c'] > sw['level'])
            if breakout: st['x breakout through level'] += 1; self.state = 'idle'; return
            if age > self.shift_window + 1: st['x no shift in time'] += 1; self.state = 'idle'; return
            if self.state == 'swept':
                broke = (m['c'] > sw['structure']) if side == 1 else (m['c'] < sw['structure'])
                avg = self._avg_range(); body = side * (m['c'] - m['o'])
                if not broke: return
                if not (avg and body >= self.disp_mult * avg): st['x break without displacement'] += 1; return
                st['2 shift'] += 1; sw['shift_i5'] = len(self.m5) - 1; sw['shift_time'] = local
            zone = self._find_gap(side, sw['i5'])
            if zone: st['3 zone (gap found)'] += 1; self.zone = zone; self.state = 'zone'; self.in_zone = False; self.m1_swing = None; self.m1_recent.clear()
            elif self.state == 'swept': self.state = 'shift_wait'  # one more 5m bar may complete the gap
            else: st['x shift without gap'] += 1; self.state = 'idle'

    def _find_gap(self, side, from_i5):
        m5 = self.m5; found = None
        for k in range(max(from_i5 + 2, 2), len(m5)):
            a, z = m5[k-2], m5[k]
            if side == 1 and z['l'] - a['h'] >= 2 * self.tick: found = (a['h'], z['l'])
            if side == -1 and a['l'] - z['h'] >= 2 * self.tick: found = (z['h'], a['l'])
        return found

    # ------------------------------------------------------------------ proposals
    def _proposal(self, b, side, est_entry, local, limit=None):
        sw = self.sw; avg = self._avg_range() or 0
        buf = max(2 * self.tick, 0.1 * avg)
        stop = self._grid(sw['extreme'] - buf, 1) if side == 1 else self._grid(sw['extreme'] + buf, -1)
        risk = side * (est_entry - stop)
        if risk <= 0: self.stats['x entry beyond stop'] += 1; return None
        _, targets = self._pools(side)
        cands = sorted(((v - est_entry) * side, v) for v in targets.values() if (v - est_entry) * side >= self.min_rr * risk)
        if not cands: self.stats['x no pool at >= min R'] += 1; return None
        self.stats['6 proposal'] += 1
        target = round(cands[0][1] / self.tick) * self.tick
        p = {'side': side, 'stop': stop, 'target': target, 'signal_time': b.timestamp,
             'reason': f"TJR v5: swept {sw['name']}, 5m shift, gap retest, {'1m BOS' if limit is None else 'limit 50%'}"}
        if limit is not None: p['limit'] = limit; p['expire_bars'] = self.trigger_minutes
        return p

    def on_bar(self, b):
        utc = b.dt(); local = utc.astimezone(self.tz); clock = local.strftime('%H:%M')
        if local.date() != self.day: self.day = local.date(); self._reset_day()
        self._session_update(b, local, clock)
        done = self._m5_update(b, local, clock)
        if done is not None: self._m5_close(done, local)
        signal = None
        if self.state == 'zone':
            side = self.sw['side']; bottom, top = self.zone
            if (local - self.sw['shift_time']).total_seconds() > self.trigger_minutes * 60 or clock >= self.c['entry_end']:
                self.stats['x zone timed out' if self.in_zone else 'x price never came back to zone'] += 1; self.state = 'idle'
            elif self.entry_mode == 'limit':
                mid = (bottom + top) / 2; limit = self._grid(mid, -side)  # buy limit rounds down, sell limit rounds up
                signal = self._proposal(b, side, limit, local, limit=limit); self.state = 'idle'
            else:
                entered = (b.low <= top) if side == 1 else (b.high >= bottom)
                if self.zone_invalidation == 'sweep':
                    failed = (b.low < self.sw['extreme']) if side == 1 else (b.high > self.sw['extreme'])
                else:
                    failed = (b.close < bottom) if side == 1 else (b.close > top)
                if not self.in_zone and entered: self.in_zone = True; self.m1_recent.clear(); self.m1_swing = None; self.stats['4 price entered zone'] += 1
                if self.in_zone and failed: self.stats['x zone failed (close through)'] += 1; self.state = 'idle'
                elif self.in_zone:
                    self.m1_recent.append(b)
                    if len(self.m1_recent) == 3:
                        a, mid, z = self.m1_recent
                        if side == 1 and mid.high > a.high and mid.high > z.high: self.m1_swing = mid.high
                        if side == -1 and mid.low < a.low and mid.low < z.low: self.m1_swing = mid.low
                    bos = self.m1_swing is not None and ((b.close > self.m1_swing) if side == 1 else (b.close < self.m1_swing))
                    if bos:
                        self.stats['5 1m BOS trigger'] += 1
                        est = b.close + side * self.c['slippage_ticks'] * self.tick
                        signal = self._proposal(b, side, est, local); self.state = 'idle'
        self.bars.append(b)
        return signal
