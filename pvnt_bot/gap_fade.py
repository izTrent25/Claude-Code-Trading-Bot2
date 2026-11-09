"""Opening gap fade. Research only; rules in research/SPEC_gap_fade.md. Same interface as engine.Strategy."""
from collections import deque, Counter
from zoneinfo import ZoneInfo


class GapFadeStrategy:
    def __init__(self, c):
        self.c = c; self.tz = ZoneInfo(c['timezone']); self.tick = c['tick_size']
        self.open_clock = c.get('gf_open', '08:30'); self.close_clock = c.get('gf_close', '15:00')
        self.min_gap = float(c.get('gf_min_gap_pct', 0.2))
        self.stop_gaps = float(c.get('gf_stop_gaps', 1.0)); self.target_gaps = float(c.get('gf_target_gaps', 1.0))
        self.bars = deque(maxlen=500); self.setup = None; self.building = {}; self.context = {15: None, 90: None}
        self.day = None; self.prev_close = None; self.today_close = None; self.done = False
        self.stats = Counter()

    def on_bar(self, b):
        local = b.dt().astimezone(self.tz); clock = local.strftime('%H:%M')
        if local.date() != self.day:
            self.day = local.date()
            if self.today_close is not None: self.prev_close = self.today_close
            self.today_close = None; self.done = False
        self.bars.append(b)
        if self.open_clock <= clock < self.close_clock: self.today_close = b.close  # the last one standing is the cash close
        if clock != self.open_clock or self.done: return None
        self.done = True
        if self.prev_close is None: self.stats['x no previous close'] += 1; return None
        gap = b.open - self.prev_close
        if abs(gap) / self.prev_close * 100 < self.min_gap: self.stats['x gap too small'] += 1; return None
        side = -1 if gap > 0 else 1
        stop = b.open + self.stop_gaps * gap       # beyond the open, on the gap's side
        target = b.open - self.target_gaps * gap   # back toward yesterday's close
        est = b.close + side * self.c['slippage_ticks'] * self.tick
        if side * (target - est) <= 0: self.stats['x already past the target'] += 1; return None
        if side * (est - stop) <= 0: self.stats['x already through the stop'] += 1; return None
        self.stats['signal long' if side == 1 else 'signal short'] += 1
        return {'side': side, 'stop': stop, 'target': target, 'signal_time': b.timestamp, 'reason': f'gap fade, gap {gap:+.2f}'}
