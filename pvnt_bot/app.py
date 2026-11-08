#!/usr/bin/env python3
"""PVNT local research terminal. Python 3.10+, standard library only."""
import argparse,csv,io,json,os,random,secrets,sqlite3,threading,time
from dataclasses import asdict
from datetime import datetime,timedelta,timezone
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo
from engine import Bar,Engine
from projectx import ProjectX

ROOT=Path(__file__).resolve().parent

def load_csv(path):
    with open(path,newline='',encoding='utf-8-sig') as f:
        rows=list(csv.DictReader(f))
    if not rows:raise ValueError('CSV is empty')
    required={'timestamp','open','high','low','close'}
    if not required.issubset(rows[0]):raise ValueError('CSV requires timestamp,open,high,low,close,volume(optional)')
    bars=[]
    for r in rows:
        b=Bar(r['timestamp'],*(float(r[k]) for k in ('open','high','low','close')),float(r.get('volume') or 0)); b.validate()
        if bars and (b.dt()-bars[-1].dt()).total_seconds()<60:raise ValueError('Use sorted, unique one-minute bars; timestamps need timezone offsets')
        bars.append(b)
    return bars

def demo():
    """Synthetic random market, deliberately not a historical performance claim."""
    rng=random.Random(41); bars=[]; price=21000.; tz=ZoneInfo('America/Chicago')
    for day in range(12):
        date=datetime(2026,10,12,tzinfo=tz)+timedelta(days=day)
        if date.weekday()>4:continue
        start=date.replace(hour=7,minute=0)
        for minute in range(480):
            o=price; c=round((o+rng.gauss(0,4))/0.25)*0.25
            h=round((max(o,c)+rng.uniform(0.25,5))/0.25)*0.25
            l=round((min(o,c)-rng.uniform(0.25,5))/0.25)*0.25
            bars.append(Bar((start+timedelta(minutes=minute)).astimezone(timezone.utc).isoformat(),o,h,l,c,rng.randint(20,800))); price=c
    return bars

class Runtime:
    def __init__(self,args,c):
        self.args=args; self.engine=Engine(c); self.lock=threading.RLock(); self.running=False
        self.done=False; self.error=''; self.index=0; self.speed=10; self.token=secrets.token_urlsafe(24)
        self.feed=args.mode; self.data=load_csv(args.csv) if args.mode=='csv' else (demo() if args.mode=='demo' else [])
        self.client=ProjectX() if args.mode=='projectx' else None
        self.last_poll=0; self.connection='Not connected' if self.client else 'Local replay'
        self.contract=args.contract; self.warmed=False; self.next_poll=0
        runs=Path(os.environ.get('PVNT_RUNS_DIR',str(Path.home()/'PVNTBotData'/'runs'))).expanduser(); runs.mkdir(parents=True,exist_ok=True)
        self.run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+secrets.token_hex(3)
        self.db_path=runs/(self.run_id+'.sqlite')
        self.db=sqlite3.connect(self.db_path,check_same_thread=False)
        self.db.executescript('CREATE TABLE bars (timestamp TEXT PRIMARY KEY, payload TEXT); CREATE TABLE snapshots (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT); CREATE TABLE trades (id INTEGER PRIMARY KEY, payload TEXT);')
        self.db.commit();self.db.close()
        self.saved_trades=0;self.unsaved_bars=[]
        self.engine.event('New independent simulation run; synthetic data' if self.feed=='demo' else 'New independent paper run')
    def persist(self,b=None):
        if b:self.unsaved_bars.append(b)
        if b and not self.client and len(self.unsaved_bars)<10:return
        # Short-lived connections also tolerate workspace file synchronization.
        db=sqlite3.connect(self.db_path)
        try:
            with db:
                db.executemany('INSERT OR IGNORE INTO bars VALUES (?,?)',[(x.timestamp,json.dumps(asdict(x))) for x in self.unsaved_bars])
                db.execute('INSERT OR REPLACE INTO snapshots VALUES (1,?)',(json.dumps(self.engine.snapshot()),))
                for i in range(self.saved_trades,len(self.engine.trades)):
                    db.execute('INSERT INTO trades VALUES (?,?)',(i,json.dumps(self.engine.trades[i])))
            self.unsaved_bars.clear();self.saved_trades=len(self.engine.trades)
        finally:db.close()
    def state(self):
        with self.lock:
            return {**self.engine.snapshot(),'mode':self.feed,'source_label':{'demo':'SYNTHETIC DEMO — not market results','csv':'CSV HISTORICAL REPLAY','projectx':'TOPSTEPX DATA / LOCAL PAPER FILLS'}[self.feed],
                    'running':self.running,'done':self.done,'error':self.error,'progress':self.index,'total':len(self.data),
                    'speed':self.speed,'connection':self.connection,'contract':self.contract,'run_id':self.run_id,
                    'last_poll':self.last_poll,'token':self.token}
    def control(self,action,body):
        with self.lock:
            if action=='start' and not self.done and not self.error:self.running=True
            elif action=='pause':self.running=False
            elif action=='step' and not self.client and not self.done and not self.running:self.advance()
            elif action=='speed':self.speed=max(1,min(1000,int(body.get('value',10))))
            elif action=='flatten':
                self.running=False; self.engine.pending=None
                if self.engine.position:self.engine.close(self.engine.last.close,'manual paper flatten')
                self.persist()
            elif action=='halt':
                self.running=False; self.engine.halted=True; self.engine.pending=None
                if self.engine.position:self.engine.close(self.engine.last.close,'manual paper kill switch')
                self.persist()
            elif action not in ('start','pause','step'):raise ValueError('Unknown action')
    def advance(self):
        if self.index<len(self.data):
            b=self.data[self.index]; self.engine.process(b); self.index+=1; self.persist(b)
        if self.index>=len(self.data):
            self.engine.finish(); self.done=True; self.running=False; self.persist()
    def poll(self):
        now=datetime.now(timezone.utc)
        bars=self.client.bars(self.contract,now-timedelta(hours=8) if not self.warmed else now-timedelta(minutes=10),now)
        self.last_poll=time.time(); self.connection='Connected; completed 1-minute bars, 10-second polling'
        if not self.warmed:
            # Warm indicators only. Never create paper historical trades on connect.
            for b in bars:self.engine.strategy.on_bar(b)
            if bars:self.engine.last=bars[-1]
            self.warmed=True; self.engine.event('Warmup complete; waiting for NEW completed bars'); return
        fresh=[b for b in bars if self.engine.last is None or b.dt()>self.engine.last.dt()]
        if fresh and (now-fresh[-1].dt()).total_seconds()>180:
            self.engine.pending=None; self.engine.event('Stale feed: new proposals disabled'); return
        for b in fresh:
            self.engine.process(b); self.persist(b)
        if not fresh and self.engine.last and (now-self.engine.last.dt()).total_seconds()>180:
            self.connection='STALE / market closed: paper positions await data; no real protection'
            self.engine.pending=None
    def worker(self):
        while True:
            try:
                with self.lock:
                    if self.running:
                        if self.client:
                            if time.monotonic()>=self.next_poll:
                                self.poll(); self.next_poll=time.monotonic()+10
                        else:
                            for _ in range(min(self.speed,100)):
                                if self.done:break
                                self.advance()
            except Exception as exc:
                with self.lock:
                    self.error=f'{type(exc).__name__}: {exc}'; self.running=False
                    self.engine.pending=None; self.engine.event('Stopped on error; restart creates new run')
            time.sleep(0.1 if self.client else 0.2)

def serve(runtime,port):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def reply(self,code,payload,kind='application/json'):
            data=payload.encode() if isinstance(payload,str) else json.dumps(payload,allow_nan=False).encode()
            self.send_response(code); self.send_header('Content-Type',kind); self.send_header('Content-Length',str(len(data)))
            self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers(); self.wfile.write(data)
        def valid_host(self):return self.headers.get('Host') in (f'127.0.0.1:{port}',f'localhost:{port}')
        def do_GET(self):
            if not self.valid_host():return self.reply(403,{'error':'Invalid host'})
            if self.path=='/':return self.reply(200,(ROOT/'dashboard.html').read_text(),'text/html; charset=utf-8')
            if self.path=='/api/state':return self.reply(200,runtime.state())
            if self.path=='/api/trades.csv':
                with runtime.lock:
                    rows=runtime.engine.trades
                    out=io.StringIO(); fields=['signal_time','entry_time','exit_time','side','qty','entry','stop','target','exit','net','r','reason']
                    writer=csv.DictWriter(out,fields,extrasaction='ignore'); writer.writeheader();writer.writerows(rows)
                return self.reply(200,out.getvalue(),'text/csv')
            return self.reply(404,{'error':'Not found'})
        def do_POST(self):
            if not self.valid_host() or self.headers.get('X-Control-Token')!=runtime.token:return self.reply(403,{'error':'Invalid control token'})
            try:
                n=int(self.headers.get('Content-Length',0))
                if n>2048:raise ValueError('Request too large')
                body=json.loads(self.rfile.read(n) or b'{}')
                if not self.path.startswith('/api/'):raise ValueError('Unknown route')
                runtime.control(self.path[5:],body); self.reply(200,{'ok':True})
            except (ValueError,TypeError) as exc:self.reply(400,{'error':str(exc)})
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    threading.Thread(target=runtime.worker,daemon=True).start()
    print(f'PVNT dashboard: http://127.0.0.1:{port}\nMode: {runtime.feed}. ALL fills are LOCAL SIMULATIONS. Ctrl+C stops.\nRun: {runtime.run_id}',flush=True)
    server.serve_forever()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['demo','csv','projectx'],default='demo')
    parser.add_argument('--csv');parser.add_argument('--contract');parser.add_argument('--list-contracts',action='store_true')
    parser.add_argument('--config',default=str(ROOT/'config.json'));parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args();c=json.loads(Path(args.config).read_text())
    if args.list_contracts:
        print(json.dumps(ProjectX().contracts(c['symbol']),indent=2));return
    if args.mode=='csv' and not args.csv:parser.error('--csv PATH required')
    if args.mode=='projectx' and not args.contract:parser.error('--contract ID required; first use --list-contracts')
    runtime=Runtime(args,c)
    try:serve(runtime,args.port)
    except KeyboardInterrupt:
        with runtime.lock:runtime.persist();runtime.db.close()
        print('\nStopped. Snapshot saved; restarting creates a new paper run.')

if __name__=='__main__':main()
