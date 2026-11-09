"""Turn of the month. Research only; rules in research/SPEC_turn_of_month.md.
The runner supplies c['tom_trading_days'], the sorted ISO dates with a cash session. Needs hold_overnight."""
import math, random
from collections import deque, Counter
from datetime import timedelta
from zoneinfo import ZoneInfo


class TurnOfMonthStrategy:
    def __init__(self, c, random_seed=None):
        self.c = c; self.tz = ZoneInfo(c['timezone']); self.tick = c['tick_size']
        self.bar_seconds = int(c.get('bar_seconds', 60))
        self.entry_before = int(c.get('tom_entry_before', 2))   # entry day counted from the month's end: 2 = second-to-last trading day
        self.exit_after = int(c.get('tom_exit_after', 3))       # trading day of the next month to exit on; 0 = the last day of this month
        days = list(c['tom_trading_days']); self.days = days; idx = {d: i for i, d in enumerate(days)}
        months = {}
        for d in days: months.setdefault(d[:7], []).append(d)
        keys = sorted(months); self.windows = []   # (entry_date, exit_date or None)
        for k_i, k in enumerate(keys):
            m = months[k]
            if len(m) < self.entry_before: continue
            entry = m[len(m) - self.entry_before]
            if self.exit_after == 0: exit_ = m[-1]
            else:
                nxt = months[keys[k_i + 1]] if k_i + 1 < len(keys) else []
                exit_ = nxt[self.exit_after - 1] if len(nxt) >= self.exit_after else None
            self.windows.append((entry, exit_))
        self.entries = {e: x for e, x in self.windows}
        if random_seed is not None:   # control: the same hold from a random start day that does not overlap any window
            rng = random.Random(random_seed); blocked = set()
            for e, x in self.windows:
                for i in range(idx[e], idx[x] + 1 if x else len(days)): blocked.add(i)
            rnd = {}
            for e, x in self.windows:
                if x is None: continue
                hold = idx[x] - idx[e]; month = e[:7]
                pool = [i for i in range(len(days)) if days[i][:7] == month and i + hold < len(days)
                        and not any(j in blocked for j in range(i, i + hold + 1))]
                if pool:
                    i = rng.choice(pool); rnd[days[i]] = days[i + hold]
            self.entries = rnd
        self.bars = deque(maxlen=500); self.setup = None; self.building = {}; self.context = {15: None, 90: None}
        self.day = None; self.done = False; self.exit_date = None
        self.stats = Counter()

    def on_bar(self, b):
        local = b.dt().astimezone(self.tz); date = local.date().isoformat()
        close_clock = (local + timedelta(seconds=self.bar_seconds)).strftime('%H:%M')
        if local.date() != self.day: self.day = local.date(); self.done = False
        self.bars.append(b)
        if close_clock != '15:00' or self.done or date not in self.entries: return None
        self.done = True; self.exit_date = self.entries[date]
        est = b.close + self.c['slippage_ticks'] * self.tick
        stop = math.floor(est * 0.97 / self.tick) * self.tick   # record only, never filled
        self.stats['signal long'] += 1
        return {'side': 1, 'stop': stop, 'signal_time': b.timestamp, 'reason': f'turn of month, out {self.exit_date}'}

    def check_exit(self, position, b):
        if self.exit_date is None: return None
        local = b.dt().astimezone(self.tz); date = local.date().isoformat()
        close_clock = (local + timedelta(seconds=self.bar_seconds)).strftime('%H:%M')
        if date > self.exit_date or (date == self.exit_date and close_clock >= '15:00'): return 'window end'
        return None
