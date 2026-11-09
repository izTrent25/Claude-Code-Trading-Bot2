"""First-five-minute-candle ORB with an ATR stop (Zarattini & Aziz 2023; Step 1's orb5_atr).
Research only; rules in research/SPEC_orb_candle.md. Five-minute bars."""
import math
from collections import deque, Counter
from datetime import timedelta
from zoneinfo import ZoneInfo


class OrbCandleStrategy:
    def __init__(self, c):
        self.c = c; self.tz = ZoneInfo(c['timezone']); self.tick = c['tick_size']
        self.bar_seconds = int(c.get('bar_seconds', 60))
        self.candle_start = c.get('oc_candle_start', '08:30'); self.candle_close = c.get('oc_candle_close', '08:35')
        self.atr_mult = float(c.get('oc_atr_mult', 0.10)); self.atr_sessions = int(c.get('oc_atr_sessions', 14))
        self.bars = deque(maxlen=500); self.setup = None; self.building = {}; self.context = {15: None, 90: None}
        self.session_key = None; self.sess = None; self.prev_close = None; self.trs = deque(maxlen=self.atr_sessions)
        self.day = None; self.done = False
        self.stats = Counter()

    def atr(self):
        return sum(self.trs) / len(self.trs) if len(self.trs) >= self.atr_sessions else None

    def _session_update(self, b, local):
        key = (local + timedelta(days=1)).date() if local.hour >= 17 else local.date()
        if key != self.session_key:
            if self.sess is not None:
                h, l, c_ = self.sess
                tr = h - l if self.prev_close is None else max(h - l, abs(h - self.prev_close), abs(l - self.prev_close))
                self.trs.append(tr); self.prev_close = c_
            self.session_key = key; self.sess = [b.high, b.low, b.close]
        else:
            s = self.sess; s[0] = max(s[0], b.high); s[1] = min(s[1], b.low); s[2] = b.close

    def on_bar(self, b):
        local = b.dt().astimezone(self.tz); clock = local.strftime('%H:%M')
        close_clock = (local + timedelta(seconds=self.bar_seconds)).strftime('%H:%M')
        if local.date() != self.day: self.day = local.date(); self.done = False
        self._session_update(b, local); self.bars.append(b)
        if clock != self.candle_start or close_clock != self.candle_close or self.done: return None
        self.done = True
        atr = self.atr()
        if atr is None: self.stats['x no ATR yet'] += 1; return None
        if b.close == b.open: self.stats['x doji'] += 1; return None
        side = 1 if b.close > b.open else -1
        est = b.close + side * self.c['slippage_ticks'] * self.tick
        raw = est - side * self.atr_mult * atr; q = raw / self.tick
        stop = (math.floor(q) if side == 1 else math.ceil(q)) * self.tick
        if side * (est - stop) <= 0: self.stats['x stop beyond entry'] += 1; return None
        self.stats['signal long' if side == 1 else 'signal short'] += 1
        return {'side': side, 'stop': stop, 'signal_time': b.timestamp, 'reason': f"first candle {'up' if side == 1 else 'down'}, stop {self.atr_mult} x ATR14"}
