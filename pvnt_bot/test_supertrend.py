"""Tests for the SuperTrend strategy (research/SPEC_supertrend.md) and the three engine research options
it needs: hold_overnight, intrabar_stop=false and the strategy exit hook."""
import copy, json, unittest
from pathlib import Path
from engine import Engine, Bar
from supertrend import SuperTrendStrategy
C = json.loads((Path(__file__).parent / 'config.json').read_text())


def bar(t, o, h, l, c, day='2026-11-09'):
    return Bar(f'{day}T{t}:00-06:00', o, h, l, c, 100)


class SuperTrendTests(unittest.TestCase):
    def test_hand_computed_flips_with_period_two(self):
        c = copy.deepcopy(C); c.update(st_period=2, st_mult=1.0); s = SuperTrendStrategy(c)
        quiet = bar('09:00', 100, 101, 99, 100)
        self.assertIsNone(s.on_bar(quiet)); self.assertIsNone(s.on_bar(bar('09:01', 100, 101, 99, 100)))
        self.assertEqual(s.atr, 2); self.assertEqual((s.up, s.dn, s.trend), (98, 102, 1))
        self.assertIsNone(s.on_bar(bar('09:02', 100, 101, 99, 100)))
        sig = s.on_bar(bar('09:03', 100, 100, 94, 95))        # tr 6, atr 4, close 95 < previous up band 98: flip down
        self.assertEqual(sig['side'], -1); self.assertEqual(sig['stop'], 101); self.assertTrue(s.flipped)
        self.assertEqual(s.up, 98)                              # the up band ratchets: it may not fall while the previous close was above it
        self.assertIsNone(s.on_bar(bar('09:04', 95, 96, 94, 95))); self.assertFalse(s.flipped)
        self.assertEqual((s.atr, s.up, s.dn), (3, 92, 98))
        sig = s.on_bar(bar('09:05', 95, 104, 95, 103))         # close 103 > previous down band 98: flip up
        self.assertEqual(sig['side'], 1); self.assertEqual(sig['stop'], 93.5)

    def test_indicator_runs_through_a_session_break(self):
        c = copy.deepcopy(C); c.update(st_period=2, st_mult=1.0); s = SuperTrendStrategy(c)
        for t in ('14:58', '14:59'): s.on_bar(bar(t, 100, 101, 99, 100))
        atr_before = s.atr; s.on_bar(bar('17:00', 100, 101, 99, 100))      # the 16:00-17:00 break is not a reset
        self.assertEqual(s.atr, atr_before); self.assertEqual(s.trend, 1)


class EngineOptionTests(unittest.TestCase):
    def make(self, **over):
        c = copy.deepcopy(C); c.update(entry_start='00:00', entry_end='23:58', flatten_time='23:59', risk_per_trade=100, max_contracts=1); c.update(over)
        return Engine(c)
    def open_long(self, e, t_sig='15:00', t_in='15:01'):
        e.process(bar(t_sig, 100, 101, 99, 100)); e.pending = {'side': 1, 'stop': 95, 'signal_time': e.last.timestamp, 'reason': 'test'}
        e.process(bar(t_in, 100, 101, 99, 100)); self.assertIsNotNone(e.position)

    def test_intrabar_stop_off_keeps_the_trade(self):
        e = self.make(intrabar_stop=False); self.open_long(e)
        e.process(bar('15:02', 100, 100, 90, 99)); self.assertIsNotNone(e.position)       # low 90 is through the 95 stop
        f = self.make(); self.open_long(f); f.process(bar('15:02', 100, 100, 90, 99)); self.assertEqual(f.trades[-1]['reason'], 'stop')

    def test_hold_overnight_survives_day_change_gap_and_flatten(self):
        e = self.make(hold_overnight=True, flatten_time='15:03'); self.open_long(e)
        e.process(bar('15:03', 100, 101, 99, 100)); self.assertIsNotNone(e.position)      # no session flatten
        e.process(bar('17:00', 100, 101, 99, 100)); self.assertIsNotNone(e.position)      # a two-hour gap: no data-gap flatten
        e.process(bar('09:00', 100, 101, 99, 100, day='2026-11-10')); self.assertIsNotNone(e.position)   # new day: no session-gap flatten
        g = self.make(hold_overnight=True); g.process(bar('23:45', 100, 101, 99, 100))
        g.pending = {'side': -1, 'stop': 110, 'signal_time': g.last.timestamp, 'reason': 'late flip'}
        g.process(bar('00:00', 100, 101, 99, 100, day='2026-11-10'))
        self.assertEqual(g.position['side'], -1); self.assertEqual(g.position['entry'], 99.5)   # a proposal made before midnight fills after it
        f = self.make(); self.open_long(f); f.process(bar('17:00', 100, 101, 99, 100)); self.assertEqual(f.trades[-1]['reason'], 'data gap flatten')

    def test_exit_hook_closes_at_the_close_and_the_same_bar_can_reverse(self):
        e = self.make()
        class Flipper:
            bars = []; setup = None; building = {}; context = {}
            def __init__(self): self.fire = False
            def on_bar(self, b): return {'side': -1, 'stop': 110, 'signal_time': b.timestamp, 'reason': 'flip'} if self.fire else None
            def check_exit(self, position, b): return 'flip' if self.fire else None
        e.strategy = Flipper(); self.open_long(e)
        e.strategy.fire = True; e.process(bar('15:02', 100, 102, 99, 101))
        self.assertEqual(e.trades[-1]['reason'], 'flip'); self.assertEqual(e.trades[-1]['exit'], 100.5)   # close 101 minus 2 ticks slippage
        self.assertIsNotNone(e.pending); self.assertEqual(e.pending['side'], -1)                          # the reversal waits for the next open
        e.strategy.fire = False; e.process(bar('15:03', 101, 102, 100, 101)); self.assertEqual(e.position['side'], -1); self.assertEqual(e.position['entry'], 100.5)


if __name__ == '__main__': unittest.main()
