"""Tests for the Anchored-VWAP pullback port (research/SPEC_avwap_pullback.md). Five-minute bars, tick 0.25,
constant volume, Chicago wall-clock times."""
import copy, json, unittest
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from engine import Engine, Bar
from avwap_pullback import AvwapPullbackStrategy
C = json.loads((Path(__file__).parent / 'config.json').read_text())
AV = {'bar_seconds': 300, 'risk_per_trade': 1e9, 'max_contracts': 1, 'daily_loss': 1e9, 'max_hold_bars': 60, 'max_trades_per_day': 50,
      'hold_overnight': True, 'intrabar_stop': True, 'loss_distance': 1e9}


def cfg(**over):
    c = copy.deepcopy(C); c.update(AV); c.update(over); return c


class Series:
    """A hand-built tape: quiet warm-up, a swing low, a ten-bar impulse, a two-bar pullback into the band, a reclaim bar."""
    def __init__(self):
        self.bars = []; self.t0 = datetime(2026, 11, 9, 2, 0, tzinfo=ZoneInfo('America/Chicago'))
    def add(self, o, h, l, c, vol=100):
        t = self.t0 + timedelta(minutes=5 * len(self.bars)); self.bars.append(Bar(t.isoformat(), o, h, l, c, vol)); return self.bars[-1]
    def setup(self):
        for _ in range(30): self.add(10000, 10001, 9999, 10000)       # bars 0-29: ATR about 2, equal highs and lows, so no pivots
        self.add(10000, 10001, 9990, 9998)                              # bar 30: the swing low at 9990
        px = 9998
        for _ in range(10): self.add(px, px + 2.25, px - 0.25, px + 1.5); px += 1.5   # bars 31-40: the impulse, confirmed at bar 40
        self.add(10013, 10013.25, 10008, 10009)                         # bar 41: into the band
        self.add(10009, 10010, 10006, 10007)                            # bar 42: deeper, pullback low 10006
        return self


class SignalTests(unittest.TestCase):
    def run_to_reclaim(self, **over):
        s = AvwapPullbackStrategy(cfg(**over)); tape = Series().setup()
        sigs = [s.on_bar(b) for b in tape.bars]
        self.assertTrue(all(x is None for x in sigs), 'no signal before the reclaim bar')
        self.assertIsNotNone(s.bull, 'the swing low at 9990 seeds a long anchor'); self.assertEqual(s.bull['price'], 9990)
        self.assertTrue(s.bull['armed']); self.assertEqual(s.bull['imp'], 10013.75)
        self.assertTrue(s.engs[0].bull_zone); self.assertEqual(s.engs[0].bull_pb_low, 10006)
        sig = s.on_bar(tape.add(10007, 10011, 10006.5, 10010.5))      # bar 43: the reclaim (up bar, above VWAP, near the prior high)
        return s, tape, sig

    def test_reclaim_bar_proposes_a_long_with_the_indicators_levels(self):
        s, tape, sig = self.run_to_reclaim(av_leg='tp2')
        self.assertIsNotNone(sig); self.assertEqual(sig['side'], 1); self.assertEqual(sig['intended_side'], 1)
        plan = s.engs[0].plan; risk = plan['risk']; entry = 10010.5
        self.assertEqual(plan['entry'], entry); self.assertEqual(plan['status'], 0); self.assertIsNone(plan['magnet'])
        self.assertAlmostEqual(sig['stop'], entry - risk, delta=0.13)                   # tick-rounded
        self.assertAlmostEqual(sig['tp1'], entry + risk, delta=0.13); self.assertAlmostEqual(sig['tp2'], entry + 2 * risk, delta=0.13)
        self.assertAlmostEqual(sig['tp3'], entry + 3 * risk, delta=0.13)
        self.assertEqual(sig['target'], sig['tp2']); self.assertEqual(sig['breakeven_at'], sig['tp1'] + 0.25)
        self.assertEqual(s.engs[0].bull_used, 1); self.assertFalse(s.engs[0].bull_zone)
        self.assertEqual(s.stats['signal long'], 1)
        for x in (sig['stop'], sig['tp1'], sig['tp2'], sig['tp3']): self.assertAlmostEqual(x / 0.25, round(x / 0.25))   # on the tick grid

    def test_tp1_leg_has_no_break_even_and_the_ladder_mode_has_no_magnet(self):
        s, tape, sig = self.run_to_reclaim(av_leg='tp1', av_target_mode='ladder')
        self.assertEqual(sig['target'], sig['tp1']); self.assertIsNone(sig['breakeven_at'])

    def test_plan_moves_to_break_even_after_a_tick_through_tp1_and_ends_at_the_entry(self):
        s, tape, sig = self.run_to_reclaim()
        tp1 = sig['tp1']
        s.on_bar(tape.add(10010.5, tp1 + 0.25, 10010, tp1))           # bar 44: a tick through TP1
        plan = s.engs[0].plan; self.assertTrue(plan['tp1_hit']); self.assertEqual(plan['active_sl'], 10010.5)
        s.on_bar(tape.add(tp1, tp1 + 0.5, 10010.25, 10011))            # bar 45: back to the entry
        self.assertEqual(plan['status'], 2); self.assertEqual(s.stats['plan: break-even stop'], 1)

    def test_a_touch_of_tp1_is_not_enough(self):
        s, tape, sig = self.run_to_reclaim()
        s.on_bar(tape.add(10010.5, sig['tp1'], 10010, sig['tp1'] - 0.25))
        self.assertFalse(s.engs[0].plan['tp1_hit'])

    def test_break_even_off_keeps_the_original_stop(self):
        s, tape, sig = self.run_to_reclaim(av_breakeven=False)
        self.assertIsNone(sig['breakeven_at'])
        s.on_bar(tape.add(10010.5, sig['tp1'] + 0.25, 10010, sig['tp1']))
        self.assertTrue(s.engs[0].plan['tp1_hit']); self.assertEqual(s.engs[0].plan['active_sl'], sig['stop'])

    def test_check_exit_flips_only_on_an_opposite_signal(self):
        s = AvwapPullbackStrategy(cfg()); pos = {'side': 1, 'intended_side': 1}
        self.assertIsNone(s.check_exit(pos, None))
        s.last_side = 1; self.assertIsNone(s.check_exit(pos, None))
        s.last_side = -1; self.assertEqual(s.check_exit(pos, None), 'flip')
        self.assertEqual(s.check_exit({'side': -1, 'intended_side': 1}, None), 'flip')   # the control's flipped trade exits at the same bar

    def test_day_version_blocks_signals_outside_the_window(self):
        # the same tape, but version B with a window that excludes 05:35 CT (bar 43 is at 05:35)
        s, tape, sig = self.run_to_reclaim(av_session=True, entry_start='08:30', entry_end='14:31', flatten_time='14:55')
        self.assertIsNone(sig); self.assertIsNone(s.engs[0].plan)

    def test_engine_trades_the_plan_and_honours_the_break_even_level(self):
        c = cfg(av_leg='tp2'); e = Engine(c); e.strategy = AvwapPullbackStrategy(c); tape = Series().setup()
        for b in tape.bars: e.process(b)
        e.process(tape.add(10007, 10011, 10006.5, 10010.5)); self.assertIsNotNone(e.pending); self.assertIsNone(e.position)
        plan = e.strategy.engs[0].plan; tp1 = plan['tp1']
        e.process(tape.add(10010.5, tp1 + 0.25, 10010, tp1))           # entry at this bar's open plus slippage, TP1 passed within the bar
        p = e.position; self.assertIsNotNone(p); self.assertEqual(p['qty'], 1); self.assertEqual(p['entry'], 10011)
        self.assertEqual(p['stop'], p['entry'], 'stop moved to the entry once TP1 was passed'); self.assertEqual(p['target'], plan['tp2'])
        e.process(tape.add(tp1, tp1 + 0.5, 10010.25, 10011))
        self.assertIsNone(e.position); self.assertEqual(e.trades[-1]['reason'], 'stop'); self.assertAlmostEqual(e.trades[-1]['exit'], 10011 - 0.5)


if __name__ == '__main__':
    unittest.main()
