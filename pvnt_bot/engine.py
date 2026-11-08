"""Deterministic, single-symbol OHLC research engine. No broker order endpoints."""
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from collections import deque
import math

@dataclass
class Bar:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0
    def dt(self):
        d = datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
        if d.tzinfo is None:
            raise ValueError('Timestamps must include a timezone')
        return d.astimezone(timezone.utc)
    def validate(self):
        self.dt()
        if not all(math.isfinite(x) and x > 0 for x in (self.open,self.high,self.low,self.close)):
            raise ValueError('Prices must be finite and positive')
        if self.low > min(self.open,self.close) or self.high < max(self.open,self.close) or self.low > self.high:
            raise ValueError('Invalid OHLC')
        if not math.isfinite(self.volume) or self.volume < 0:
            raise ValueError('Invalid volume')

class Strategy:
    """Sweep prior N bars; later close breaks pre-sweep 3-bar structure.
    Signal at close, market entry at NEXT bar open. No retracement/FVG claims.
    """
    def __init__(self, c):
        self.c=c; self.bars=deque(maxlen=500); self.setup=None; self.i=0
        self.context={15:None,90:None}; self.building={}
    def update_context(self,b):
        # UTC epoch-aligned buckets, only publish after a subsequent bucket starts.
        for n in (15,90):
            bucket=int(b.dt().timestamp())//(n*60)
            old=self.building.get(n)
            if old and old[0]!=bucket:
                if old[3]>=n:
                    self.context[n]=1 if old[2]>old[1] else (-1 if old[2]<old[1] else 0)
                old=None
            self.building[n]=(bucket, old[1] if old else b.open, b.close,old[3]+1 if old else 1)
    def on_bar(self,b):
        self.i+=1; self.update_context(b); signal=None
        past=list(self.bars); n=self.c['lookback']
        if len(past)>=n:
            ranges=[x.high-x.low for x in past[-n:]]
            avg=sum(ranges)/n
            s=self.setup
            if s:
                age=self.i-s['i']
                invalid=(b.low<s['extreme'] if s['side']==1 else b.high>s['extreme'])
                if age>self.c['confirmation_bars'] or invalid:
                    self.setup=None
                elif age>0:
                    side=s['side']
                    broke=b.close>s['structure'] if side==1 else b.close<s['structure']
                    displaced=side*(b.close-b.open)>=self.c['displacement_multiple']*avg
                    context_ok=not self.c['use_context'] or all(v==side for v in self.context.values())
                    if broke and displaced and context_ok:
                        signal={'side':side,'stop':s['extreme']-side*self.c['tick_size'],
                                'signal_time':b.timestamp,'reason':'Sweep / displacement / structure break'}
                        self.setup=None
            if signal is None and self.setup is None:
                lo=min(x.low for x in past[-n:]); hi=max(x.high for x in past[-n:])
                bull=b.low<lo and b.close>lo
                bear=b.high>hi and b.close<hi
                if bull != bear:
                    side=1 if bull else -1
                    self.setup={'side':side,'i':self.i,'extreme':b.low if bull else b.high,
                                'structure':max(x.high for x in past[-3:]) if bull else min(x.low for x in past[-3:])}
        self.bars.append(b)
        return signal

class Engine:
    def __init__(self,c):
        self.c=c; self.validate_config(); self.strategy=Strategy(c)
        self.balance=float(c['initial_balance']); self.floor=self.balance-c['loss_distance']
        self.position=None; self.pending=None; self.last=None; self.day=None
        self.day_start=self.balance; self.day_trades=0; self.daily_halted=False
        self.halted=False; self.trades=[]; self.events=[]; self.equity=[]; self.peak=self.balance
        self.max_dd=0.; self.count=0
    def validate_config(self):
        for key in ('tick_size','tick_value','initial_balance','loss_distance','daily_loss','risk_per_trade','max_contracts','lookback','confirmation_bars','reward_risk','max_hold_bars','max_trades_per_day'):
            if not isinstance(self.c[key],(int,float)) or not math.isfinite(self.c[key]) or self.c[key]<=0:
                raise ValueError('Invalid positive setting: '+key)
        for key in ('safety_buffer','commission_per_side','slippage_ticks','displacement_multiple'):
            if not math.isfinite(self.c[key]) or self.c[key]<0: raise ValueError('Invalid setting: '+key)
        ZoneInfo(self.c['timezone'])
        for k in ('entry_start','entry_end','flatten_time'): datetime.strptime(self.c[k],'%H:%M')
    def event(self,msg):
        self.events.append({'time':self.last.timestamp if self.last else '', 'message':msg})
        self.events=self.events[-200:]
    def pnl(self,price):
        p=self.position
        return 0 if not p else (price-p['entry'])*p['side']/self.c['tick_size']*self.c['tick_value']*p['qty']
    def equity_at(self,price): return self.balance+self.pnl(price)
    def close(self,price,reason):
        p=self.position
        if not p:return
        # Adverse market/stop slippage; limit target fills do not get favorable improvement.
        fill=price if reason=='target' else price-p['side']*self.c['slippage_ticks']*self.c['tick_size']
        gross=self.pnl(fill); fee=self.c['commission_per_side']*p['qty']
        self.balance+=gross-fee
        net=gross-2*fee
        self.trades.append({**p,'exit_time':self.last.timestamp,'exit':fill,'net':round(net,2),
                            'r':round(net/p['initial_risk'],4),'reason':reason})
        self.event(f"EXIT {reason}: ${net:.2f}"); self.position=None
    def session(self,b):
        dt=b.dt().astimezone(ZoneInfo(self.c['timezone']))
        return dt.date().isoformat(),dt.strftime('%H:%M')
    def process(self,b):
        b.validate()
        if self.last and b.dt()<=self.last.dt():raise ValueError('Bars must be strictly increasing')
        old=self.last; self.last=b; self.count+=1
        day,clock=self.session(b)
        if day!=self.day:
            if self.position:self.close(b.open,'session gap flatten')
            if self.day is not None:
                self.floor=max(self.floor,min(self.c['floor_cap'],self.balance-self.c['loss_distance']))
            self.day=day; self.day_start=self.balance; self.day_trades=0; self.daily_halted=False
            self.pending=None; self.strategy.setup=None
        if old and (b.dt()-old.dt()).total_seconds()>60:
            self.pending=None; self.strategy.setup=None
            self.strategy.bars.clear(); self.strategy.building.clear(); self.strategy.context={15:None,90:None}
            if self.position:self.close(b.open,'data gap flatten')
            self.event('Gap: canceled proposal, cleared strategy context')
        if self.pending and not self.position:
            s=self.pending; self.pending=None
            if not self.halted and not self.daily_halted and self.c['entry_start']<=clock<self.c['entry_end']:
                side=s['side']; entry=b.open+side*self.c['slippage_ticks']*self.c['tick_size']
                dist=side*(entry-s['stop'])
                exit_cost=self.c['slippage_ticks']*self.c['tick_value']
                unit=dist/self.c['tick_size']*self.c['tick_value']+2*self.c['commission_per_side']+exit_cost
                room=min(self.c['risk_per_trade'],self.balance-self.floor-self.c['safety_buffer'],
                         self.c['daily_loss']+(self.balance-self.day_start))
                qty=min(int(self.c['max_contracts']),math.floor(max(0,room)/unit)) if dist>0 and unit>0 else 0
                if qty>0 and self.day_trades<self.c['max_trades_per_day']:
                    stop=s['stop']; target=entry+side*dist*self.c['reward_risk']
                    target=round(target/self.c['tick_size'])*self.c['tick_size']
                    self.position={**s,'entry_time':b.timestamp,'entry':entry,'stop':stop,'target':target,
                                   'qty':qty,'bars':0,'initial_risk':unit*qty}
                    self.balance-=self.c['commission_per_side']*qty; self.day_trades+=1
                    self.event(f"ENTRY {'LONG' if side==1 else 'SHORT'} x{qty} at {entry:.2f}")
                else:self.event('Risk rejected proposal: no available size / daily trade cap')
        p=self.position
        if p:
            p['bars']+=1; side=p['side']
            # Conservative path: adverse excursion first, account guard before target.
            cut=max(self.floor+self.c['safety_buffer'],self.day_start-self.c['daily_loss'])
            guard_price=p['entry']+(cut+self.c['commission_per_side']*p['qty']-self.balance)*side*self.c['tick_size']/(self.c['tick_value']*p['qty'])
            effective=max(p['stop'],guard_price) if side==1 else min(p['stop'],guard_price)
            triggered=(b.low<=effective if side==1 else b.high>=effective)
            if triggered:
                fill=min(b.open,effective) if side==1 else max(b.open,effective)
                self.close(fill,'risk guard' if effective!=p['stop'] else 'stop')
            elif (b.high>=p['target']+self.c['tick_size'] if side==1 else b.low<=p['target']-self.c['tick_size']):
                self.close(p['target'],'target')
            elif clock>=self.c['flatten_time'] or p['bars']>=self.c['max_hold_bars']:
                self.close(b.close,'session flatten' if clock>=self.c['flatten_time'] else 'time stop')
        eq=self.equity_at(b.close)
        if eq<=self.floor+self.c['safety_buffer']:
            self.halted=True; self.pending=None
            if self.position:self.close(b.close,'account guard')
        if self.equity_at(b.close)-self.day_start<=-self.c['daily_loss']:
            self.daily_halted=True; self.pending=None
            if self.position:self.close(b.close,'daily guard')
        signal=self.strategy.on_bar(b)
        if signal and not self.position and not self.halted and not self.daily_halted and self.c['entry_start']<=clock<self.c['entry_end']:
            self.pending=signal; self.event('Signal confirmed; next-bar market proposal')
        eq=self.equity_at(b.close); self.peak=max(self.peak,eq); self.max_dd=max(self.max_dd,self.peak-eq)
        self.equity.append({'time':b.timestamp,'value':round(eq,2)})
        self.equity=self.equity[-5000:]
    def finish(self):
        self.pending=None
        if self.position:self.close(self.last.close,'end of data')
        if self.last:
            self.max_dd=max(self.max_dd,self.peak-self.balance)
            self.equity.append({'time':self.last.timestamp,'value':round(self.balance,2)})
    def snapshot(self):
        nets=[t['net'] for t in self.trades]; gains=sum(x for x in nets if x>0); losses=-sum(x for x in nets if x<0)
        return {'balance':round(self.balance,2),'equity':round(self.equity_at(self.last.close) if self.last else self.balance,2),
                'floor':round(self.floor,2),'daily_pnl':round((self.equity_at(self.last.close) if self.last else self.balance)-self.day_start,2),
                'halted':self.halted,'daily_halted':self.daily_halted,'position':self.position,'pending':self.pending,
                'bars':self.count,'trades':self.trades[-200:],'events':self.events[-30:],'curve':self.equity,
                'candles':[asdict(b) for b in list(self.strategy.bars)[-100:]],
                'stats':{'trades':len(nets),'net':round(sum(nets),2),'win_rate':round(100*sum(x>0 for x in nets)/len(nets),1) if nets else 0,
                         'profit_factor':round(gains/losses,2) if losses else None,'expectancy':round(sum(nets)/len(nets),2) if nets else 0,'max_dd':round(self.max_dd,2)},
                'Context':self.strategy.context,'config':self.c}
