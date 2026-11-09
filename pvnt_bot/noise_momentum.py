"""Noise-area intraday momentum (Zarattini, Aziz & Barbon 2024). Research only; rules in
research/SPEC_noise_momentum.md. Half-hour checks on Chicago time; exits through check_exit, which
also mirrors the exit level for a trade the random-direction control flipped."""
from collections import deque, Counter
from datetime import timedelta
from zoneinfo import ZoneInfo


class NoiseMomentumStrategy:
    def __init__(self, c):
        self.c = c; self.tz = ZoneInfo(c['timezone']); self.tick = c['tick_size']
        self.bar_seconds = int(c.get('bar_seconds', 60))
        self.lookback = int(c.get('nm_lookback', 14)); self.vwap_filter = bool(c.get('nm_vwap_filter', True))
        self.stop_mode = c.get('nm_stop', 'vwap')   # 'vwap' = max(band, VWAP) trailing (primary); 'band' = opposite band, reverse (base)
        self.checks = [f'{h:02d}:{m:02d}' for h in range(9, 15) for m in (0, 30)]          # 09:00 ... 14:30 Chicago
        self.checks = [c_ for c_ in self.checks if c_ <= c.get('nm_last_entry', '14:30')]
        self.sessions = deque(maxlen=self.lookback)   # dicts check -> |move from open|, complete sessions only
        self.bars = deque(maxlen=500); self.setup = None; self.building = {}; self.context = {15: None, 90: None}
        self.day = None; self.prev_close = None; self.today_close = None; self._reset_day()
        self.stats = Counter()

    def _reset_day(self):
        self.open_930 = None; self.pv = 0.0; self.vol = 0.0; self.vwap = None; self.today_moves = {}
        self.at_check = False; self.cur = None

    def on_bar(self, b):
        local = b.dt().astimezone(self.tz); clock = local.strftime('%H:%M')
        close_clock = (local + timedelta(seconds=self.bar_seconds)).strftime('%H:%M')
        if local.date() != self.day:
            if self.day is not None and len(self.today_moves) == len(self.checks): self.sessions.append(dict(self.today_moves))
            if self.today_close is not None: self.prev_close = self.today_close
            self.day = local.date(); self.today_close = None; self._reset_day()
        self.bars.append(b); self.at_check = False
        if clock < '08:30' or clock >= '15:00': return None
        if self.open_930 is None and clock == '08:30': self.open_930 = b.open
        self.today_close = b.close
        tp = (b.high + b.low + b.close) / 3; self.pv += tp * b.volume; self.vol += b.volume
        self.vwap = self.pv / self.vol if self.vol > 0 else b.close
        if self.open_930 is None or close_clock not in self.checks: return None
        self.today_moves[close_clock] = abs(b.close / self.open_930 - 1)
        if len(self.sessions) < self.lookback or self.prev_close is None: self.stats['x warm-up'] += 1; return None
        sigma = sum(s[close_clock] for s in self.sessions) / len(self.sessions)
        ub = max(self.open_930, self.prev_close) * (1 + sigma); lb = min(self.open_930, self.prev_close) * (1 - sigma)
        self.cur = {'ub': ub, 'lb': lb, 'vwap': self.vwap, 'close': b.close}; self.at_check = True
        self.stats['checks'] += 1
        side = 0
        if b.close > ub and (not self.vwap_filter or b.close > self.vwap): side = 1
        elif b.close < lb and (not self.vwap_filter or b.close < self.vwap): side = -1
        if side == 0: return None
        est = b.close + side * self.c['slippage_ticks'] * self.tick
        stop = lb if side == 1 else ub   # the opposite band: record only, unless the hard-stop variant turns intrabar stops on
        if side * (est - stop) <= 0: self.stats['x band beyond entry'] += 1; return None
        self.stats['signal long' if side == 1 else 'signal short'] += 1
        return {'side': side, 'stop': stop, 'signal_time': b.timestamp, 'intended_side': side, 'signal_close': b.close,
                'reason': f"noise area {'up' if side == 1 else 'down'} at {close_clock}"}

    def check_exit(self, position, b):
        if not self.at_check or self.cur is None: return None
        s0 = position.get('intended_side', position['side']); s = position['side']; cur = self.cur
        if s0 == 1:
            level = max(cur['ub'], cur['vwap']) if self.stop_mode == 'vwap' else cur['lb']; natural = cur['close'] < level
        else:
            level = min(cur['lb'], cur['vwap']) if self.stop_mode == 'vwap' else cur['ub']; natural = cur['close'] > level
        if s == s0: return 'trailing exit' if natural else None
        c0 = position.get('signal_close', position['entry']); mirrored = 2 * c0 - level   # the control flipped this trade
        flipped_exit = cur['close'] > mirrored if s0 == 1 else cur['close'] < mirrored
        return 'trailing exit (mirrored)' if flipped_exit else None
