"""Last-half-hour intraday momentum. Research only; rules in research/SPEC_last_half_hour.md."""
from collections import deque, Counter
from datetime import timedelta
from zoneinfo import ZoneInfo


class LastHalfHourStrategy:
    def __init__(self, c):
        self.c = c; self.tz = ZoneInfo(c['timezone']); self.tick = c['tick_size']
        self.bar_seconds = int(c.get('bar_seconds', 60))
        self.signal_close = c.get('lh_signal_close', '14:30'); self.first30_close = c.get('lh_first30_close', '09:00')
        self.mode = c.get('lh_mode', 'day')                      # 'day' = close-to-14:30 move (JFE 2021); 'first30' = first half hour (JFE 2018)
        self.min_rank = float(c.get('lh_min_move_rank', 0))      # 0 = every day; 0.5 = |move| at or above the median of the last 20 sessions
        self.hist = deque(maxlen=20)
        self.bars = deque(maxlen=500); self.setup = None; self.building = {}; self.context = {15: None, 90: None}
        self.day = None; self.prev_close = None; self.today_close = None; self.first30 = None
        self.sess_high = None; self.sess_low = None; self.done = False
        self.stats = Counter()

    def on_bar(self, b):
        local = b.dt().astimezone(self.tz); clock = local.strftime('%H:%M')
        close_clock = (local + timedelta(seconds=self.bar_seconds)).strftime('%H:%M')
        if local.date() != self.day:
            self.day = local.date()
            if self.today_close is not None: self.prev_close = self.today_close
            self.today_close = None; self.first30 = None; self.sess_high = None; self.sess_low = None; self.done = False
        self.bars.append(b)
        if '08:30' <= clock < '15:00':
            self.today_close = b.close
            self.sess_high = b.high if self.sess_high is None else max(self.sess_high, b.high)
            self.sess_low = b.low if self.sess_low is None else min(self.sess_low, b.low)
        if close_clock == self.first30_close: self.first30 = b.close
        if close_clock != self.signal_close or self.done: return None
        self.done = True
        if self.prev_close is None: self.stats['x no previous close'] += 1; return None
        ref = b.close if self.mode == 'day' else self.first30
        if ref is None: self.stats['x no first half hour'] += 1; return None
        move = ref - self.prev_close; rel = abs(move) / self.prev_close
        ok = True
        if self.min_rank > 0:
            if len(self.hist) >= 10:
                srt = sorted(self.hist); ok = rel >= srt[int(self.min_rank * (len(srt) - 1))]
            else: ok = False
        self.hist.append(rel)
        if move == 0: self.stats['x no move'] += 1; return None
        if not ok: self.stats['x move below threshold'] += 1; return None
        side = 1 if move > 0 else -1
        est = b.close + side * self.c['slippage_ticks'] * self.tick
        stop = self.sess_low if side == 1 else self.sess_high   # record only, never filled: the day's opposite extreme
        if stop is None or side * (est - stop) <= 0: stop = est - side * 0.0025 * est
        self.stats['signal long' if side == 1 else 'signal short'] += 1
        return {'side': side, 'stop': stop, 'signal_time': b.timestamp, 'reason': f'last half hour ({self.mode}) move {move:+.2f}'}
