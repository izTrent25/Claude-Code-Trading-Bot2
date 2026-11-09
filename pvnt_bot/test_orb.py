"""Tests for the opening-range breakout strategy (research/SPEC_orb.md). Times are Chicago
(CST in November 2026, so the -06:00 offset); bars are 15-minute unless a test says otherwise."""
import copy, json, unittest
from pathlib import Path
from engine import Engine, Bar
from orb import OrbStrategy
C = json.loads((Path(__file__).parent / 'config.json').read_text())


def bar(clock, o, h, l, c, day='2026-11-09'):
    return Bar(f'{day}T{clock}:00-06:00', o, h, l, c, 100)


def strat(**over):
    c = copy.deepcopy(C); c.update(bar_seconds=900); c.update(over); return OrbStrategy(c)


RANGE = bar('08:30', 100, 110, 100, 105)   # opening range 100-110, height 10


class OrbTests(unittest.TestCase):
    def test_long_breakout_geometry(self):
        s = strat(); self.assertIsNone(s.on_bar(RANGE))
        sig = s.on_bar(bar('08:45', 105, 113, 104, 112))
        self.assertEqual(sig['side'], 1); self.assertEqual(sig['stop'], 99.75); self.assertEqual(sig['target'], 120)
        s2 = strat(orb_target_mult=2); s2.on_bar(RANGE)
        self.assertEqual(s2.on_bar(bar('08:45', 105, 113, 104, 112))['target'], 130)
        s3 = strat(orb_target_from='entry'); s3.on_bar(RANGE)       # v1b: one height above the estimated entry 112.5
        self.assertEqual(s3.on_bar(bar('08:45', 105, 113, 104, 112))['target'], 122.5)

    def test_wick_through_the_range_is_not_a_breakout(self):
        s = strat(); s.on_bar(RANGE)
        self.assertIsNone(s.on_bar(bar('08:45', 105, 115, 104, 108)))      # high above 110, close inside
        self.assertEqual(s.on_bar(bar('09:00', 108, 112, 107, 111))['side'], 1)

    def test_one_trade_per_day_and_the_reversal_variant(self):
        s = strat(); s.on_bar(RANGE); s.on_bar(bar('08:45', 105, 113, 104, 112))
        self.assertIsNone(s.on_bar(bar('09:00', 112, 116, 111, 115)))      # a repeat close above: nothing
        self.assertIsNone(s.on_bar(bar('09:15', 115, 115, 95, 97)))        # close below the low: nothing with 1 trade/day
        r = strat(orb_max_trades=2); r.on_bar(RANGE); r.on_bar(bar('08:45', 105, 113, 104, 112))
        self.assertIsNone(r.on_bar(bar('09:00', 112, 116, 111, 115)))
        sig = r.on_bar(bar('09:15', 115, 115, 95, 97))
        self.assertEqual(sig['side'], -1); self.assertEqual(sig['stop'], 110.25); self.assertEqual(sig['target'], 90)
        self.assertIsNone(r.on_bar(bar('09:30', 97, 112, 96, 111)))        # third trade never allowed

    def test_breakout_must_close_by_eleven(self):
        quiet = [bar(t, 105, 108, 102, 105) for t in ('08:45', '09:00', '09:15', '09:30', '09:45', '10:00', '10:15', '10:30')]
        s = strat(); s.on_bar(RANGE)
        for q in quiet: self.assertIsNone(s.on_bar(q))
        self.assertEqual(s.on_bar(bar('10:45', 105, 113, 104, 112))['side'], 1)   # closes at 11:00: allowed
        s2 = strat(); s2.on_bar(RANGE)
        for q in quiet + [bar('10:45', 105, 108, 102, 105)]: s2.on_bar(q)
        self.assertIsNone(s2.on_bar(bar('11:00', 105, 113, 104, 112)))            # closes at 11:15: too late
        self.assertEqual(s2.stats['x no breakout by cutoff'], 1)

    def test_no_trade_when_the_breakout_bar_already_passed_the_target(self):
        s = strat(); s.on_bar(RANGE)
        self.assertIsNone(s.on_bar(bar('08:45', 105, 125, 104, 121)))      # target would be 120; close 121
        self.assertEqual(s.stats['x entry already beyond target'], 1)
        self.assertIsNone(s.on_bar(bar('09:00', 121, 126, 120, 125)))      # the day's breakout is spent

    def test_short_on_five_minute_bars(self):
        s = strat(bar_seconds=300)
        for t, hi, lo in (('08:30', 108, 100), ('08:35', 110, 103), ('08:40', 107, 101)):
            self.assertIsNone(s.on_bar(bar(t, 104, hi, lo, 104)))
        sig = s.on_bar(bar('08:45', 103, 104, 97, 98))
        self.assertEqual(sig['side'], -1); self.assertEqual(sig['stop'], 110.25); self.assertEqual(sig['target'], 90)

    def test_missing_range_bar_means_no_trade(self):
        s = strat(bar_seconds=300)
        s.on_bar(bar('08:30', 104, 108, 100, 104)); s.on_bar(bar('08:40', 104, 107, 101, 104))   # 08:35 missing
        self.assertIsNone(s.on_bar(bar('08:45', 104, 114, 103, 113)))
        self.assertEqual(s.stats['x no range (gap at the open)'], 1)
        w = strat(); w.on_bar(bar('17:00', 104, 108, 100, 104, day='2026-11-08'))                  # a Sunday evening
        self.assertEqual(w.stats['x no morning bars (weekend or holiday)'], 1); self.assertEqual(w.stats['x no range (gap at the open)'], 0)

    def test_atr_stop_needs_fourteen_sessions_then_uses_them(self):
        s = strat(orb_stop='atr', orb_target_mult=2); s.on_bar(RANGE)
        self.assertIsNone(s.on_bar(bar('08:45', 105, 113, 104, 112))); self.assertEqual(s.stats['x no ATR yet'], 1)
        t = strat(orb_stop='atr', orb_target_mult=2); t.trs.extend([50.0] * 14); t.on_bar(RANGE)
        sig = t.on_bar(bar('08:45', 105, 113, 104, 112))
        self.assertEqual(sig['stop'], 107.5)       # estimated entry 112.5 minus 0.10 x 50, on the grid
        self.assertEqual(sig['target'], 130)

    def test_session_true_range_rolls_at_five_pm(self):
        s = strat()
        s.on_bar(bar('08:30', 100, 110, 100, 105)); s.on_bar(bar('15:00', 105, 112, 98, 104))      # session 1: 98-112
        s.on_bar(bar('17:00', 120, 125, 119, 122))                                                # session 2 opens with a gap
        self.assertEqual(list(s.trs), [14.0])                                                     # session 1 closed: 112-98
        s.on_bar(bar('17:00', 122, 123, 121, 122, day='2026-11-10'))
        self.assertEqual(list(s.trs), [14.0, 21.0])                                               # max(6, 125-104, |119-104|)

    def test_engine_round_trip_on_fifteen_minute_bars(self):
        c = copy.deepcopy(C); c.update(bar_seconds=900, entry_start='08:30', entry_end='11:01', max_hold_bars=1000,
                                       risk_per_trade=500, daily_loss=5000, loss_distance=1e9)
        e = Engine(c); e.strategy = OrbStrategy(c)
        e.process(RANGE); e.process(bar('08:45', 105, 113, 104, 112)); self.assertIsNotNone(e.pending)
        e.process(bar('09:00', 112, 114, 111, 113))
        self.assertEqual(e.position['entry'], 112.5); self.assertEqual(e.position['target'], 120); self.assertEqual(e.position['qty'], 2)
        e.process(bar('09:15', 113, 121, 112, 119))
        self.assertEqual(e.trades[-1]['reason'], 'target'); self.assertAlmostEqual(e.trades[-1]['net'], 27.0)


if __name__ == '__main__': unittest.main()
