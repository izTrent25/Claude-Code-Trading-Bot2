import copy,json,unittest,tempfile
from pathlib import Path
from engine import Engine,Bar,Strategy
from app import load_csv,demo
C=json.loads((Path(__file__).parent/'config.json').read_text())
def b(t,o=100,h=101,l=99,c=100):return Bar('2026-11-02T'+t+':00+00:00',o,h,l,c,10)
class Tests(unittest.TestCase):
    def engine(self):
        c=copy.deepcopy(C);c.update(entry_start='00:00',entry_end='23:58',flatten_time='23:59',risk_per_trade=100,max_contracts=1)
        return Engine(c)
    def enter(self,e):
        e.process(b('15:00'));e.pending={'side':1,'stop':95,'signal_time':e.last.timestamp,'reason':'test'}
        e.process(b('15:01',100,101,99,100));self.assertIsNotNone(e.position)
    def test_no_fill_on_signal_bar(self):
        e=self.engine();e.process(b('15:00'));e.pending={'side':1,'stop':95,'signal_time':e.last.timestamp,'reason':'test'}
        self.assertIsNone(e.position)
        e.process(b('15:01',102,103,101,102));self.assertEqual(e.position['entry'],102.5)
    def test_both_stop_target_is_stop(self):
        e=self.engine();self.enter(e);e.process(b('15:02',100,120,90,100));self.assertEqual(e.trades[-1]['reason'],'stop');self.assertLess(e.trades[-1]['net'],0)
    def test_gap_stop_fill(self):
        e=self.engine();self.enter(e);e.process(b('15:02',90,92,89,91));self.assertEqual(e.trades[-1]['exit'],89.5)
    def test_costs(self):
        e=self.engine();self.enter(e);e.close(100.5,'manual');t=e.trades[-1]
        self.assertAlmostEqual(t['net'],-2.5);self.assertAlmostEqual(e.balance-C['initial_balance'],t['net'])
    def test_size_rejected(self):
        e=self.engine();e.c['risk_per_trade']=1;e.process(b('15:00'));e.pending={'side':1,'stop':95,'signal_time':e.last.timestamp,'reason':'test'}
        e.process(b('15:01'));self.assertIsNone(e.position)
    def test_duplicate_bar_rejected(self):
        e=self.engine();e.process(b('15:00'))
        with self.assertRaises(ValueError):e.process(b('15:00'))
    def test_prefix_invariance(self):
        bars=demo()[:500];a=self.engine();z=self.engine()
        for x in bars[:300]:a.process(x)
        before=json.dumps(a.snapshot(),sort_keys=True)
        for x in bars[:300]:z.process(x)
        self.assertEqual(before,json.dumps(z.snapshot(),sort_keys=True))
        for x in bars[300:]:z.process(x)
        self.assertEqual(before,json.dumps(a.snapshot(),sort_keys=True))
    def test_sweep_then_structure(self):
        c=copy.deepcopy(C);c.update(lookback=3,displacement_multiple=.5)
        s=Strategy(c)
        for t in ('15:00','15:01','15:02'):self.assertIsNone(s.on_bar(b(t)))
        self.assertIsNone(s.on_bar(b('15:03',100,100.5,98,100)))
        signal=s.on_bar(b('15:04',100,103,99,102.5))
        self.assertEqual(signal['side'],1);self.assertEqual(signal['stop'],97.75)
    def test_target_requires_penetration(self):
        e=self.engine();self.enter(e);target=e.position['target']
        e.process(b('15:02',101,target,100,102));self.assertIsNotNone(e.position)
        e.process(b('15:03',102,target+.25,101,103));self.assertEqual(e.trades[-1]['reason'],'target')
    def test_daily_loss_halt(self):
        e=self.engine();self.enter(e);e.c['daily_loss']=10
        e.process(b('15:02',100,101,90,95));self.assertIsNone(e.position);self.assertTrue(e.daily_halted)
    def test_data_gap_cancels(self):
        e=self.engine();e.process(b('15:00'));e.pending={'side':1,'stop':95}
        e.process(b('15:05'));self.assertIsNone(e.position);self.assertIsNone(e.pending)
    def test_csv_timezone_required(self):
        with tempfile.NamedTemporaryFile('w',suffix='.csv') as f:
            f.write('timestamp,open,high,low,close\n2026-11-02T15:00:00,100,101,99,100\n');f.flush()
            with self.assertRaises(ValueError):load_csv(f.name)
    def test_whole_demo(self):
        e=self.engine()
        for x in demo():e.process(x)
        e.finish();self.assertIsNone(e.position);self.assertGreater(len(e.trades),0)
        self.assertAlmostEqual(e.balance-C['initial_balance'],sum(t['net'] for t in e.trades),places=6)

class ExtendedTests(unittest.TestCase):
    def make(self):
        c=copy.deepcopy(C);c.update(entry_start='00:00',entry_end='23:58',flatten_time='23:59',risk_per_trade=100,max_contracts=1)
        return Engine(c)
    def test_short_stop_adverse_slippage(self):
        e=self.make();e.process(b('15:00'));e.pending={'side':-1,'stop':105,'signal_time':e.last.timestamp,'reason':'short'}
        e.process(b('15:01',100,101,99,100));self.assertEqual(e.position['entry'],99.5)
        e.process(b('15:02',110,111,109,110));self.assertEqual(e.trades[-1]['exit'],110.5)
    def test_account_halt_on_gap(self):
        e=self.make();e.process(b('15:00'));e.pending={'side':1,'stop':95,'signal_time':e.last.timestamp,'reason':'test'}
        e.process(b('15:01'));e.floor=e.balance-1;e.process(b('15:02',90,91,89,90))
        self.assertTrue(e.halted);self.assertIsNone(e.position);self.assertIsNone(e.pending)
    def test_day_trail_and_cap(self):
        e=self.make();e.process(b('15:00'));e.balance=53000
        x=Bar('2026-11-03T15:00:00+00:00',100,101,99,100)
        e.process(x);self.assertEqual(e.floor,50000);self.assertEqual(e.day_start,53000)
    def test_daily_reset(self):
        e=self.make();e.process(b('15:00'));e.daily_halted=True;e.day_trades=3
        e.process(Bar('2026-11-03T15:00:00+00:00',100,101,99,100))
        self.assertFalse(e.daily_halted);self.assertEqual(e.day_trades,0)
    def test_invalid_ohlc(self):
        with self.assertRaises(ValueError):self.make().process(b('15:00',100,99,98,100))
    def test_nan_rejected(self):
        with self.assertRaises(ValueError):self.make().process(b('15:00',float('nan')))
    def test_partial_htf_not_published(self):
        s=Strategy(copy.deepcopy(C));s.on_bar(b('15:14'));s.on_bar(b('15:15'))
        self.assertIsNone(s.context[15])
    def test_complete_htf_published_after_close(self):
        s=Strategy(copy.deepcopy(C))
        for i in range(15):s.on_bar(b(f'15:{i:02d}',100,102,99,101))
        self.assertIsNone(s.context[15]);s.on_bar(b('15:15'))
        self.assertEqual(s.context[15],1)
    def test_no_entry_outside_session(self):
        e=self.make();e.c['entry_start']='16:00';e.process(b('15:00'))
        e.pending={'side':1,'stop':95,'signal_time':e.last.timestamp,'reason':'test'};e.process(b('15:01'))
        self.assertIsNone(e.position)
    def test_finish_flatten_and_accounting(self):
        e=self.make();e.process(b('15:00'));e.pending={'side':1,'stop':95,'signal_time':e.last.timestamp,'reason':'test'};e.process(b('15:01'))
        e.finish();self.assertIsNone(e.position);self.assertIsNone(e.pending)
        self.assertAlmostEqual(e.balance-C['initial_balance'],sum(t['net'] for t in e.trades))
    def test_projectx_endpoint_allowlist(self):
        from projectx import ProjectX
        with self.assertRaises(RuntimeError):ProjectX().post('/api/Order/place',{})
    def test_projectx_bar_sort_partial_filter(self):
        from projectx import ProjectX
        from datetime import datetime,timedelta,timezone
        from unittest.mock import patch
        x=ProjectX();now=datetime.now(timezone.utc)
        old=(now-timedelta(minutes=3)).isoformat();new=(now-timedelta(minutes=2)).isoformat();partial=now.isoformat()
        response={'bars':[{'t':t,'o':100,'h':101,'l':99,'c':100,'v':10} for t in [new,partial,old]]}
        with patch.object(x,'ready'),patch.object(x,'post',return_value=response):
            bars=x.bars('TEST',now-timedelta(hours=1),now)
        self.assertEqual([z.timestamp for z in bars],[old,new])
    def test_projectx_missing_credentials(self):
        from projectx import ProjectX
        from unittest.mock import patch
        with patch.dict('os.environ',{},clear=True):
            with self.assertRaises(RuntimeError):ProjectX().login()
    def test_projectx_body_failure_rejected(self):
        from projectx import ProjectX
        from unittest.mock import patch,MagicMock
        import io
        response=MagicMock();response.__enter__.return_value=io.BytesIO(b'{"success":false,"errorCode":3}')
        with patch('urllib.request.urlopen',return_value=response):
            with self.assertRaisesRegex(RuntimeError,'error code 3'):ProjectX().post('/api/Contract/search',{})

if __name__=='__main__':unittest.main()
