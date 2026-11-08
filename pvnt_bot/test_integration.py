"""Run directly for HTTP/worker/persistence smoke test; no API credentials needed."""
import subprocess,sys,urllib.request,urllib.error,json,time,tempfile,sqlite3,os
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
    # A separate port avoids interfering with a user dashboard on the default port.
    port=18765;base=f'http://127.0.0.1:{port}'
    temp=tempfile.TemporaryDirectory(prefix='pvnt-test-');run_dir=Path(temp.name)
    env=dict(os.environ,PVNT_RUNS_DIR=str(run_dir))
    p=subprocess.Popen([sys.executable,str(ROOT/'app.py'),'--port',str(port)],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    def get(path):
        with urllib.request.urlopen(base+path,timeout=20) as r:return r.read()
    def post(action,body,token):
        req=urllib.request.Request(base+'/api/'+action,json.dumps(body).encode(),{'Content-Type':'application/json','X-Control-Token':token})
        with urllib.request.urlopen(req,timeout=20) as r:return json.load(r)
    try:
        for _ in range(100):
            try:s=json.loads(get('/api/state'));break
            except urllib.error.URLError:time.sleep(.1)
        else:raise AssertionError('Server did not start')
        assert s['mode']=='demo' and s['bars']==0
        assert b'SMC execution lab' in get('/')
        try:post('start',{},'wrong');raise AssertionError('Wrong control token accepted')
        except urllib.error.HTTPError as e:assert e.code==403
        post('step',{},s['token']);assert json.loads(get('/api/state'))['bars']==1
        post('speed',{'value':100},s['token']);post('start',{},s['token'])
        for _ in range(300):
            s=json.loads(get('/api/state'))
            assert not s['error'],s['error']
            if s['done']:break
            time.sleep(.1)
        assert s['done'],'Replay did not finish'
        assert s['stats']['trades']>0
        assert b'entry_time' in get('/api/trades.csv')
        post('pause',{},s['token']);post('flatten',{},s['token']);post('halt',{},s['token'])
        assert json.loads(get('/api/state'))['halted']
        with sqlite3.connect(run_dir/(s['run_id']+'.sqlite')) as db:
            assert db.execute('select count(*) from bars').fetchone()[0]==s['bars']
            assert db.execute('select count(*) from trades').fetchone()[0]==s['stats']['trades']
        (ROOT/'tested_snapshot.json').write_text(json.dumps(s))
        print(json.dumps({'http_routes':'passed','control_token':'passed','start_pause_step_speed_flatten_halt':'passed','full_replay':'passed','bars':s['bars'],'trades':s['stats']['trades'],'csv_export':'passed','sqlite_audit':'passed'}))
    finally:p.terminate();p.wait(timeout=10);temp.cleanup()
if __name__=='__main__':main()
