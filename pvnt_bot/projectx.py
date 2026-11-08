"""Read-only ProjectX adapter. There is intentionally NO order-placement code."""
import os, json, time, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone
from engine import Bar

class ProjectX:
    BASE='https://api.topstepx.com'
    ALLOWED={'/api/Auth/loginKey','/api/Contract/search','/api/History/retrieveBars'}
    def __init__(self): self.token=None; self.issued=0
    def post(self,path,payload):
        if path not in self.ALLOWED: raise RuntimeError('Endpoint outside read-only allowlist')
        headers={'Content-Type':'application/json','Accept':'application/json'}
        if self.token:headers['Authorization']='Bearer '+self.token
        req=urllib.request.Request(self.BASE+path,json.dumps(payload).encode(),headers,method='POST')
        try:
            with urllib.request.urlopen(req,timeout=20) as response: result=json.load(response)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f'ProjectX HTTP {exc.code}; check subscription, authorization, or rate limit') from None
        except urllib.error.URLError:
            raise RuntimeError('ProjectX connection unavailable') from None
        if result.get('success') is not True:
            raise RuntimeError(f"ProjectX rejected request; error code {result.get('errorCode')}")
        return result
    def login(self):
        user=os.environ.get('PROJECTX_USERNAME'); key=os.environ.get('PROJECTX_API_KEY')
        if not user or not key: raise RuntimeError('Set PROJECTX_USERNAME and PROJECTX_API_KEY locally')
        self.token=None
        r=self.post('/api/Auth/loginKey',{'userName':user,'apiKey':key})
        self.token=r['token']; self.issued=time.monotonic()
    def ready(self):
        if not self.token or time.monotonic()-self.issued>23*3600:self.login()
    def contracts(self,symbol):
        self.ready()
        return self.post('/api/Contract/search',{'searchText':symbol,'live':False})['contracts']
    def bars(self,contract,start,end):
        self.ready()
        r=self.post('/api/History/retrieveBars',{'contractId':contract,'live':False,
             'startTime':start.isoformat(),'endTime':end.isoformat(),'unit':2,'unitNumber':1,
             'limit':20000,'includePartialBar':False})
        now=datetime.now(timezone.utc)
        bars=[Bar(x['t'],float(x['o']),float(x['h']),float(x['l']),float(x['c']),float(x.get('v',0))) for x in r['bars']]
        # Timestamp is interpreted as bar start. Require a fully elapsed minute.
        return sorted([b for b in bars if b.dt()+timedelta(minutes=1)<=now],key=lambda b:b.dt())
