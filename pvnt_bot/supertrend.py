"""SuperTrend strategy, KivancOzbilgic's Pine v4 script rebuilt line for line. Research only.

Same interface as engine.Strategy: on_bar(bar) -> proposal dict or None, plus check_exit(position, bar)
so the Engine (research option) closes the trade at the bar that flips the trend. The exact rules are
written in research/SPEC_supertrend.md; keep the two in step. The indicator runs straight through
session breaks and weekends, as on a TradingView chart. This module never places orders.

Settings (optional, from the config dict):
  st_period      ATR length (10)      st_mult    band multiplier (3.0)
  st_wilder      true = Wilder's smoothed ATR, the script's default; false = plain average of true range
"""
from collections import deque, Counter


class SuperTrendStrategy:
    def __init__(self, c):
        self.c = c; self.tick = c['tick_size']
        self.period = int(c.get('st_period', 10)); self.mult = float(c.get('st_mult', 3.0))
        self.wilder = bool(c.get('st_wilder', True))
        # attributes the Engine touches on gaps/new days (compatibility only; the indicator state lives below)
        self.bars = deque(maxlen=500); self.setup = None; self.building = {}; self.context = {15: None, 90: None}
        self.prev_close = None; self.trs = deque(maxlen=self.period); self.atr = None
        self.up = None; self.dn = None; self.trend = 1; self.flipped = False; self.i = 0
        self.stats = Counter()  # read by the research runner

    def _update_atr(self, b):
        tr = b.high - b.low if self.prev_close is None else max(b.high - b.low, abs(b.high - self.prev_close), abs(b.low - self.prev_close))
        if self.wilder:
            if self.atr is None:
                self.trs.append(tr)
                if len(self.trs) == self.period: self.atr = sum(self.trs) / self.period   # seeded like Pine's rma()
            else:
                self.atr = (self.atr * (self.period - 1) + tr) / self.period
        else:
            self.trs.append(tr)
            if len(self.trs) == self.period: self.atr = sum(self.trs) / self.period

    def on_bar(self, b):
        self.i += 1; self.bars.append(b); self.flipped = False
        self._update_atr(b)
        signal = None
        if self.atr is not None:
            src = (b.high + b.low) / 2
            up = src - self.mult * self.atr; up1 = self.up if self.up is not None else up
            if self.prev_close is not None and self.prev_close > up1: up = max(up, up1)
            dn = src + self.mult * self.atr; dn1 = self.dn if self.dn is not None else dn
            if self.prev_close is not None and self.prev_close < dn1: dn = min(dn, dn1)
            trend = self.trend
            if trend == -1 and b.close > dn1: trend = 1
            elif trend == 1 and b.close < up1: trend = -1
            self.flipped = trend != self.trend
            self.up, self.dn, self.trend = up, dn, trend
            if self.flipped:
                side = trend
                stop = up if side == 1 else dn   # the band itself: where the trend would flip back (record only, never filled intrabar)
                if side * (b.close - stop) > 0:
                    self.stats['flip long' if side == 1 else 'flip short'] += 1
                    signal = {'side': side, 'stop': stop, 'signal_time': b.timestamp,
                              'reason': 'SuperTrend flip ' + ('up' if side == 1 else 'down')}
                else:  # a huge flip bar can leave the new band on the wrong side of the close; no record stop, so no trade until the next flip
                    self.stats['x flip skipped: band beyond close'] += 1
        self.prev_close = b.close
        return signal

    def check_exit(self, position, b):
        """Called by the Engine after on_bar while a trade is open: the trend flipped on this bar, so leave
        at its close. Side-agnostic on purpose, so the random-direction control exits at the same bars."""
        return 'supertrend flip' if self.flipped else None
