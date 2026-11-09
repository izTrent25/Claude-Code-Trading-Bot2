"""Opening-range breakout on its own. Research only.

Same interface as engine.Strategy: on_bar(bar) -> proposal dict or None. The exact rules are
written in research/SPEC_orb.md; keep the two in step. Meant for 5- or 15-minute bars built by
the research runner (--bars N), which puts the bar size in c['bar_seconds']. This module never
places orders; the Engine owns sizing, risk, fills and exits.

Settings (all optional, read from the config dict):
  orb_range_start / orb_range_end  bars starting in [start, end) build the range (08:30-08:45)
  orb_last_close                   the breakout bar must close by this Chicago time (11:00)
  orb_target_mult                  target = N range heights; 0 = no target
  orb_target_from                  'edge' = measured from the range edge (v1); 'entry' = from the estimated entry (v1b)
  orb_stop                         'range' = one tick outside the range; 'atr' = k x ATR14
  orb_atr_mult / orb_atr_sessions  k and the number of completed CME sessions in the ATR
  orb_max_trades                   1 = first breakout only; 2 = one opposite trade allowed after it
"""
import math
from collections import deque, Counter
from datetime import timedelta
from zoneinfo import ZoneInfo


def _minutes(clock):
    h, m = clock.split(':'); return int(h) * 60 + int(m)


class OrbStrategy:
    def __init__(self, c):
        self.c = c; self.tz = ZoneInfo(c['timezone']); self.tick = c['tick_size']
        self.bar_seconds = int(c.get('bar_seconds', 60))
        self.range_start = c.get('orb_range_start', '08:30'); self.range_end = c.get('orb_range_end', '08:45')
        self.last_close = c.get('orb_last_close', '11:00')
        self.target_mult = float(c.get('orb_target_mult', 1.0)); self.target_from = c.get('orb_target_from', 'edge')
        self.stop_mode = c.get('orb_stop', 'range')
        self.atr_mult = float(c.get('orb_atr_mult', 0.10)); self.atr_sessions = int(c.get('orb_atr_sessions', 14))
        self.max_trades = int(c.get('orb_max_trades', 1))
        self.expected_bars = max(1, (_minutes(self.range_end) - _minutes(self.range_start)) * 60 // self.bar_seconds)
        # attributes the Engine touches on gaps/new days (compatibility only)
        self.bars = deque(maxlen=500); self.setup = None; self.building = {}; self.context = {15: None, 90: None}
        # ATR over completed CME sessions (17:00-16:00 Chicago): [high, low, close] of the running session
        self.session_key = None; self.sess = None; self.prev_close = None; self.trs = deque(maxlen=self.atr_sessions)
        self.day = None; self._reset_day()
        self.stats = Counter()  # how many days reach each stage; read by the research runner

    def _reset_day(self):
        self.or_high = None; self.or_low = None; self.or_bars = 0
        self.range_state = None   # None until the range window has passed, then 'ok' or 'missing'
        self.sides = []           # breakout directions seen today, in order
        self.cutoff_counted = False

    def _grid(self, price, side):
        """Snap a stop to the tick grid on the safe (further-away) side."""
        q = price / self.tick
        return (math.floor(q) if side == 1 else math.ceil(q)) * self.tick

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
        if local.date() != self.day:
            self.day = local.date(); self._reset_day()
        self._session_update(b, local); self.bars.append(b)
        if clock < self.range_start:
            return None
        if clock < self.range_end:  # building the opening range
            self.or_high = b.high if self.or_high is None else max(self.or_high, b.high)
            self.or_low = b.low if self.or_low is None else min(self.or_low, b.low)
            self.or_bars += 1
            return None
        if self.range_state is None:
            if self.or_high is not None and self.or_bars >= self.expected_bars:
                self.range_state = 'ok'; self.stats['days with range'] += 1
            else:  # a Sunday or holiday has evening bars only; a real gap at the open is the rarer case
                self.range_state = 'missing'
                self.stats['x no range (gap at the open)' if clock < '12:00' else 'x no morning bars (weekend or holiday)'] += 1
        if self.range_state != 'ok':
            return None
        # the breakout bar must start before the cutoff and close by it
        close_clock = (local + timedelta(seconds=self.bar_seconds)).strftime('%H:%M')
        if not (clock < self.last_close and close_clock <= self.last_close):
            if not self.sides and not self.cutoff_counted:
                self.stats['x no breakout by cutoff'] += 1; self.cutoff_counted = True
            return None
        if len(self.sides) >= self.max_trades:
            return None
        side = 1 if b.close > self.or_high else (-1 if b.close < self.or_low else 0)
        if side == 0 or (self.sides and side == self.sides[-1]):
            return None  # no breakout, or a repeat of today's direction (a second trade must be the reversal)
        self.sides.append(side)  # the day's breakout is set whether or not a trade results
        height = self.or_high - self.or_low
        est = b.close + side * self.c['slippage_ticks'] * self.tick  # where the market entry is expected to fill
        if self.stop_mode == 'atr':
            atr = self.atr()
            if atr is None:
                self.stats['x no ATR yet'] += 1; return None
            stop = self._grid(est - side * self.atr_mult * atr, side)
        else:
            stop = self.or_low - self.tick if side == 1 else self.or_high + self.tick
        target = None
        if self.target_mult > 0:
            base = est if self.target_from == 'entry' else (self.or_high if side == 1 else self.or_low)
            target = base + side * self.target_mult * height
            if side * (target - est) <= 0:
                self.stats['x entry already beyond target'] += 1; return None
        if side * (est - stop) <= 0:
            self.stats['x entry beyond stop'] += 1; return None
        self.stats['signal long' if side == 1 else 'signal short'] += 1
        sig = {'side': side, 'stop': stop, 'signal_time': b.timestamp,
               'reason': f"ORB {'up' if side == 1 else 'down'}: close beyond the {self.range_start}-{self.range_end} range"}
        if target is not None:
            sig['target'] = target
        return sig
