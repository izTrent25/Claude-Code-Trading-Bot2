"""Overnight drift at the European open. Research only; rules in research/SPEC_overnight_drift.md.
Needs the engine's hold_overnight option; exits through check_exit at the end of the hour."""
import math, random
from collections import deque, Counter
from datetime import timedelta
from zoneinfo import ZoneInfo


def _minutes(clock):
    h, m = clock.split(':'); return int(h) * 60 + int(m)


class OvernightDriftStrategy:
    def __init__(self, c, random_hour_seed=None):
        self.c = c; self.tz = ZoneInfo(c['timezone']); self.tick = c['tick_size']
        self.bar_seconds = int(c.get('bar_seconds', 60))
        self.start = c.get('od_start', '01:00'); self.end = c.get('od_end', '02:00')
        self.hold = (_minutes(self.end) - _minutes(self.start)) % 1440
        self.after_down = bool(c.get('od_after_down_only', False))
        self.rng = random.Random(random_hour_seed) if random_hour_seed is not None else None
        self.candidates = [f'{h:02d}:{m:02d}' for h in list(range(17, 24)) + list(range(0, 7)) for m in (0, 30)
                           if not (h == 17 and m == 0) and f'{h:02d}:{m:02d}' != self.start]
        self.bars = deque(maxlen=500); self.setup = None; self.building = {}; self.context = {15: None, 90: None}
        self.day = None; self.prev_close = None; self.prev_prev_close = None; self.today_close = None
        self.start_today = self.start; self.done = False; self.exit_at = None
        self.stats = Counter()

    def on_bar(self, b):
        utc = b.dt(); local = utc.astimezone(self.tz); clock = local.strftime('%H:%M')
        close_clock = (local + timedelta(seconds=self.bar_seconds)).strftime('%H:%M')
        if local.date() != self.day:
            self.day = local.date()
            if self.today_close is not None: self.prev_prev_close = self.prev_close; self.prev_close = self.today_close
            self.today_close = None; self.done = False
            self.start_today = self.rng.choice(self.candidates) if self.rng else self.start
        self.bars.append(b)
        if '08:30' <= clock < '15:00': self.today_close = b.close
        if close_clock != self.start_today or self.done: return None
        self.done = True
        if self.after_down:
            if self.prev_close is None or self.prev_prev_close is None or self.prev_close >= self.prev_prev_close:
                self.stats['x not after a down day'] += 1; return None
        est = b.close + self.c['slippage_ticks'] * self.tick
        stop = math.floor(est * 0.995 / self.tick) * self.tick   # record only, never filled
        self.exit_at = utc + timedelta(seconds=self.bar_seconds) + timedelta(minutes=self.hold)
        self.stats['signal long'] += 1
        return {'side': 1, 'stop': stop, 'signal_time': b.timestamp, 'reason': f'overnight drift {self.start_today}'}

    def check_exit(self, position, b):
        if self.exit_at is None: return None
        return 'window end' if b.dt() + timedelta(seconds=self.bar_seconds) >= self.exit_at else None
