"""Tests for the six evidence-backed candidates of 8 Nov 2026 (research/SPEC_gap_fade.md and friends).
Chicago wall-clock times; 5-minute bars unless a test says otherwise."""
import copy, json, unittest
from pathlib import Path
from engine import Engine, Bar
from gap_fade import GapFadeStrategy
from last_half_hour import LastHalfHourStrategy
from overnight_drift import OvernightDriftStrategy
from turn_of_month import TurnOfMonthStrategy
from noise_momentum import NoiseMomentumStrategy
from orb_candle import OrbCandleStrategy
C = json.loads((Path(__file__).parent / 'config.json').read_text())


def bar(t, o, h, l, c, day='2026-11-09', vol=100):
    """A bar at Chicago wall-clock time `t` on `day`; the real timezone handles daylight saving."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    y, mo, d = (int(x) for x in day.split('-')); hh, mm = (int(x) for x in t.split(':'))
    return Bar(datetime(y, mo, d, hh, mm, tzinfo=ZoneInfo('America/Chicago')).isoformat(), o, h, l, c, vol)


def cfg(**over):
    c = copy.deepcopy(C); c.update(bar_seconds=300); c.update(over); return c


def feed_close(s, day, px):
    """A cash close for `day`: one bar inside the session and the bar that ends at 15:00."""
    s.on_bar(bar('10:00', px, px + 1, px - 1, px, day)); s.on_bar(bar('14:55', px, px + 1, px - 1, px, day))


class GapFadeTests(unittest.TestCase):
    def test_gap_up_is_faded_with_one_gap_stop_and_the_close_as_target(self):
        s = GapFadeStrategy(cfg()); feed_close(s, '2026-11-06', 10000)
        sig = s.on_bar(bar('08:30', 10050, 10060, 10040, 10045))          # gap +0.5%
        self.assertEqual(sig['side'], -1); self.assertEqual(sig['stop'], 10100); self.assertEqual(sig['target'], 10000)
        self.assertIsNone(s.on_bar(bar('08:35', 10045, 10050, 10030, 10035)))   # one trade a day
    def test_small_gap_is_skipped(self):
        s = GapFadeStrategy(cfg()); feed_close(s, '2026-11-06', 10000)
        self.assertIsNone(s.on_bar(bar('08:30', 10010, 10020, 10000, 10015))); self.assertEqual(s.stats['x gap too small'], 1)
    def test_guard_when_the_first_bar_already_filled_the_gap(self):
        s = GapFadeStrategy(cfg()); feed_close(s, '2026-11-06', 10000)
        self.assertIsNone(s.on_bar(bar('08:30', 10050, 10055, 9990, 9995))); self.assertEqual(s.stats['x already past the target'], 1)


class LastHalfHourTests(unittest.TestCase):
    def test_direction_follows_the_day_move_at_1430(self):
        s = LastHalfHourStrategy(cfg()); feed_close(s, '2026-11-06', 10000)
        self.assertIsNone(s.on_bar(bar('09:00', 10000, 10080, 9990, 10070)))
        sig = s.on_bar(bar('14:25', 10090, 10100, 10085, 10095))            # the bar ending 14:30, day up
        self.assertEqual(sig['side'], 1); self.assertEqual(sig['stop'], 9990)   # record stop = the session low
    def test_first_half_hour_mode(self):
        s = LastHalfHourStrategy(cfg(lh_mode='first30')); feed_close(s, '2026-11-06', 10000)
        s.on_bar(bar('08:55', 9995, 9999, 9900, 9950))                       # the bar ending 09:00: first half hour down
        sig = s.on_bar(bar('14:25', 10090, 10100, 10085, 10095))            # day is up, but the rule follows the first half hour
        self.assertEqual(sig['side'], -1)
    def test_big_move_filter_needs_history(self):
        s = LastHalfHourStrategy(cfg(lh_min_move_rank=0.5)); feed_close(s, '2026-11-06', 10000)
        self.assertIsNone(s.on_bar(bar('14:25', 10090, 10100, 10085, 10095))); self.assertEqual(s.stats['x move below threshold'], 1)


class OvernightDriftTests(unittest.TestCase):
    def test_long_at_one_and_out_at_two(self):
        c = cfg(hold_overnight=True, intrabar_stop=False, use_target=False, risk_per_trade=1e9, max_contracts=1, daily_loss=1e9, max_hold_bars=10**9)
        e = Engine(c); e.strategy = OvernightDriftStrategy(c)
        e.process(bar('00:50', 100, 101, 99, 100)); e.process(bar('00:55', 100, 101, 99, 100))   # the bar ending 01:00 signals
        self.assertIsNotNone(e.pending)
        e.process(bar('01:00', 100, 101, 99, 100)); self.assertEqual(e.position['entry'], 100.5)
        for t in ('01:05', '01:10', '01:50'): e.process(bar(t, 100, 101, 99, 100)); self.assertIsNotNone(e.position)
        e.process(bar('01:55', 100, 102, 99, 101)); self.assertEqual(e.trades[-1]['reason'], 'window end'); self.assertEqual(e.trades[-1]['exit'], 100.5)
    def test_after_down_filter_and_random_hour(self):
        s = OvernightDriftStrategy(cfg(od_after_down_only=True))
        feed_close(s, '2026-11-05', 10000); feed_close(s, '2026-11-06', 10100)       # yesterday was an up day
        self.assertIsNone(s.on_bar(bar('00:55', 100, 101, 99, 100))); self.assertEqual(s.stats['x not after a down day'], 1)
        r = OvernightDriftStrategy(cfg(), random_hour_seed=3); r.on_bar(bar('17:30', 100, 101, 99, 100))
        self.assertNotEqual(r.start_today, '01:00'); self.assertIn(r.start_today, r.candidates)


class TurnOfMonthTests(unittest.TestCase):
    DAYS = ['2026-10-27', '2026-10-28', '2026-10-29', '2026-10-30', '2026-11-02', '2026-11-03', '2026-11-04', '2026-11-05', '2026-11-06',
            '2026-11-09', '2026-11-10', '2026-11-24', '2026-11-25', '2026-11-27', '2026-11-30', '2026-12-01', '2026-12-02', '2026-12-03', '2026-12-04']
    def test_classic_window_enters_two_days_before_month_end_and_exits_on_the_third_day(self):
        s = TurnOfMonthStrategy(cfg(tom_trading_days=self.DAYS))
        self.assertEqual(s.entries, {'2026-10-29': '2026-11-04', '2026-11-27': '2026-12-03', '2026-12-03': None})   # December's exit is beyond the data
        self.assertIsNone(s.on_bar(bar('14:55', 100, 101, 99, 100, '2026-10-28')))
        sig = s.on_bar(bar('14:55', 100, 101, 99, 100, '2026-10-29')); self.assertEqual(sig['side'], 1)
        pos = {'side': 1, 'entry': 100.5}
        self.assertIsNone(s.check_exit(pos, bar('14:50', 100, 101, 99, 100, '2026-11-04')))
        self.assertEqual(s.check_exit(pos, bar('14:55', 100, 101, 99, 100, '2026-11-04')), 'window end')
    def test_etula_window_and_random_control_avoid_the_window(self):
        s = TurnOfMonthStrategy(cfg(tom_trading_days=self.DAYS, tom_entry_before=4, tom_exit_after=0))
        self.assertEqual(s.entries, {'2026-10-27': '2026-10-30', '2026-11-24': '2026-11-30', '2026-12-01': '2026-12-04'})
        r = TurnOfMonthStrategy(cfg(tom_trading_days=self.DAYS), random_seed=1)
        for e, x in r.entries.items():
            self.assertNotIn(e, ('2026-10-29', '2026-10-30', '2026-11-02', '2026-11-03', '2026-11-04'))
            self.assertEqual(self.DAYS.index(x) - self.DAYS.index(e), 4)   # the same four-session hold


class NoiseMomentumTests(unittest.TestCase):
    def warm(self, s, days):
        """14 sessions: open 100, every half-hour check closes at 101 or 99 (alternating days) => sigma 1% at every check."""
        for i, d in enumerate(days):
            px = 101 if i % 2 == 0 else 99
            s.on_bar(bar('08:30', 100, 100.5, 99.5, 100, d))
            for chk in s.checks:                                   # the bar that ends at the check starts five minutes earlier
                h, m = chk.split(':'); start = int(h) * 60 + int(m) - 5
                s.on_bar(bar(f'{start // 60:02d}:{start % 60:02d}', px, px + .5, px - .5, px, d))
            s.on_bar(bar('14:55', 100, 100.5, 99.5, 100, d))     # cash close 100
    def test_bands_entry_and_mirrored_exit(self):
        s = NoiseMomentumStrategy(cfg())
        days = [f'2026-10-{d:02d}' for d in range(1, 15)]; self.warm(s, days)
        s.on_bar(bar('08:30', 100, 100.5, 99.5, 100, '2026-10-15')); self.assertEqual(len(s.sessions), 14)   # the 14th session is stored at the day change
        sig = s.on_bar(bar('08:55', 100, 102.5, 100, 102, '2026-10-15'))   # the bar ending 09:00: close 102 > band 101 and > VWAP
        self.assertEqual(sig['side'], 1); self.assertAlmostEqual(s.cur['ub'], 101.0); self.assertAlmostEqual(s.cur['lb'], 99.0)
        self.assertAlmostEqual(sig['stop'], 99.0)
        pos = {**sig, 'entry': 102.5}
        s.on_bar(bar('09:25', 102, 102.5, 101.5, 102, '2026-10-15')); self.assertIsNone(s.check_exit(pos, None))   # still above band and VWAP
        s.on_bar(bar('09:55', 102, 102, 100.5, 100.8, '2026-10-15')); self.assertEqual(s.check_exit(pos, None), 'trailing exit')  # below VWAP
        flipped = {**sig, 'side': -1, 'entry': 101.5}                       # the control flipped it: mirrored level around the signal close 102
        s.on_bar(bar('10:25', 101, 103.5, 101, 103.3, '2026-10-15'))      # natural level ~ max(101, vwap~101.6); mirror ~ 102.4; close 103.3 above it
        self.assertEqual(s.check_exit(flipped, None), 'trailing exit (mirrored)')


class OrbCandleTests(unittest.TestCase):
    def test_follows_the_first_candle_with_a_tenth_of_atr_stop(self):
        import datetime
        s = OrbCandleStrategy(cfg()); s.trs.extend([50.0] * 14); s.session_key = datetime.date(2026, 11, 9); s.sess = [100, 99, 100]
        sig = s.on_bar(bar('08:30', 100, 103, 99.5, 102))
        self.assertEqual(sig['side'], 1); self.assertEqual(sig['stop'], 97.5)    # est 102.5 minus 5
        self.assertIsNone(s.on_bar(bar('08:35', 102, 104, 101, 103)))
        t = OrbCandleStrategy(cfg()); t.trs.extend([50.0] * 14); t.session_key = datetime.date(2026, 11, 9); t.sess = [100, 99, 100]
        self.assertIsNone(t.on_bar(bar('08:30', 100, 101, 99, 100))); self.assertEqual(t.stats['x doji'], 1)


if __name__ == '__main__': unittest.main()
