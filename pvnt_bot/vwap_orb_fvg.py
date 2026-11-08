"""VWAP + 15-minute opening range + FVG/order-block pullback strategy. Research only.

Same interface as engine.Strategy: on_bar(bar) -> proposal dict or None. The exact rules are
written in research/SPEC_vwap_orb_fvg.md; keep the two in step. This module never places
orders; the Engine owns sizing, risk, fills and exits.
"""
from collections import deque
from zoneinfo import ZoneInfo


class VwapOrbFvgStrategy:
    def __init__(self, c):
        self.c = c; self.tz = ZoneInfo(c['timezone']); self.tick = c['tick_size']
        self.or_start = c.get('or_start', '08:30'); self.or_end = c.get('or_end', '08:45')
        self.zone_max_age = int(c.get('fvg_max_age_bars', 60)); self.zone_min_ticks = int(c.get('fvg_min_ticks', 2))
        # version 2 geometry (set all three to 0/false to reproduce version 1)
        self.gap_mult = float(c.get('fvg_min_range_mult', 0.3))      # gap >= this x average bar range
        self.floor_mult = float(c.get('stop_floor_range_mult', 1.0))  # stop at least this x average range from entry
        self.need_reclaim = bool(c.get('require_close_beyond_zone', True))  # pullback bar must close back beyond the zone
        self.ranges = deque(maxlen=20)
        # attributes the Engine touches on gaps/new days (kept for compatibility)
        self.bars = deque(maxlen=500); self.setup = None; self.building = {}; self.context = {15: None, 90: None}
        self.i = 0; self.day = None; self.last_utc = None; self.recent = deque(maxlen=3)
        self._reset_day()

    def _reset_day(self):
        self.or_high = None; self.or_low = None
        self.pv = 0.0; self.vol = 0.0; self.vwap = None
        self.breakout = 0; self.zones = []; self.recent = deque(maxlen=3); self.ranges = deque(maxlen=20)

    def _grid(self, price, side):
        """Snap a stop to the tick grid, always on the safe (further-away) side."""
        import math
        q = price / self.tick
        return (math.floor(q) if side == 1 else math.ceil(q)) * self.tick

    def on_bar(self, b):
        self.i += 1
        utc = b.dt(); local = utc.astimezone(self.tz); clock = local.strftime('%H:%M')
        if local.date() != self.day:
            self.day = local.date(); self._reset_day()
        if self.last_utc and (utc - self.last_utc).total_seconds() > 60:
            self.recent.clear()  # a three-bar pattern must be three consecutive minutes
        self.last_utc = utc
        signal = None
        if clock < self.or_start:          # overnight: not part of this strategy
            self.bars.append(b); return None
        # session VWAP anchored at the open
        tp = (b.high + b.low + b.close) / 3; self.pv += tp * b.volume; self.vol += b.volume
        self.vwap = self.pv / self.vol if self.vol > 0 else b.close
        self.ranges.append(b.high - b.low)
        avg = sum(self.ranges) / len(self.ranges) if len(self.ranges) >= 5 else None
        # opening range window
        if clock < self.or_end:
            self.or_high = b.high if self.or_high is None else max(self.or_high, b.high)
            self.or_low = b.low if self.or_low is None else min(self.or_low, b.low)
            self.recent.append(b); self.bars.append(b); return None
        if self.or_high is None:           # data began after the open: no range today
            self.recent.append(b); self.bars.append(b); return None
        # breakout state; a close beyond the opposite side flips it and clears zones
        if b.close > self.or_high and self.breakout != 1:
            self.breakout = 1; self.zones = []
        elif b.close < self.or_low and self.breakout != -1:
            self.breakout = -1; self.zones = []
        # fair value gap on bars A (i-2), B (i-1), C (current)
        if len(self.recent) >= 2 and self.breakout != 0 and avg is not None:
            a = self.recent[-2]
            min_gap = max(self.zone_min_ticks * self.tick, self.gap_mult * avg)
            if self.breakout == 1 and b.low - a.high >= min_gap:
                bottom, top = a.high, b.low
                ob_low = a.low if a.close < a.open else None
                stop = (min(bottom, ob_low) if ob_low is not None else bottom) - self.tick
                self.zones.append({'side': 1, 'top': top, 'bottom': bottom, 'stop': stop, 'born': self.i, 'used': False})
            elif self.breakout == -1 and a.low - b.high >= min_gap:
                bottom, top = b.high, a.low
                ob_high = a.high if a.close > a.open else None
                stop = (max(top, ob_high) if ob_high is not None else top) + self.tick
                self.zones.append({'side': -1, 'top': top, 'bottom': bottom, 'stop': stop, 'born': self.i, 'used': False})
        # expire, invalidate, consume
        live = []
        for z in self.zones:
            if z['used'] or self.i - z['born'] > self.zone_max_age: continue
            if z['side'] == 1 and b.close < z['bottom']: continue
            if z['side'] == -1 and b.close > z['top']: continue
            live.append(z)
        self.zones = live
        # entry: pullback into the newest live zone that holds, with VWAP agreeing
        slip = self.c['slippage_ticks'] * self.tick
        if self.breakout == 1 and b.close > self.vwap and avg is not None:
            for z in reversed(self.zones):
                held = b.close >= (z['top'] if self.need_reclaim else z['bottom'])
                if z['side'] == 1 and self.i > z['born'] and b.low <= z['top'] and held:
                    z['used'] = True
                    stop = z['stop']
                    if self.floor_mult > 0:
                        stop = min(stop, self._grid(b.close + slip - self.floor_mult * avg, 1))
                    signal = {'side': 1, 'stop': stop, 'signal_time': b.timestamp, 'reason': 'ORB up / above VWAP / FVG-OB pullback held'}
                    break
        elif self.breakout == -1 and b.close < self.vwap and avg is not None:
            for z in reversed(self.zones):
                held = b.close <= (z['bottom'] if self.need_reclaim else z['top'])
                if z['side'] == -1 and self.i > z['born'] and b.high >= z['bottom'] and held:
                    z['used'] = True
                    stop = z['stop']
                    if self.floor_mult > 0:
                        stop = max(stop, self._grid(b.close - slip + self.floor_mult * avg, -1))
                    signal = {'side': -1, 'stop': stop, 'signal_time': b.timestamp, 'reason': 'ORB down / below VWAP / FVG-OB pullback held'}
                    break
        self.recent.append(b); self.bars.append(b)
        return signal
