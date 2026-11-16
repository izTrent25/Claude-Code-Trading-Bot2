# Python twin of pvnt_bot/OrderBlock_Indicator.pine (defaults), drawn as an SVG chart for a visual check.
# Usage: .venv/bin/python research/ob_visual_check.py 15min 3   (bar size, days back from the end of NQ 2026 data)
import sys, pandas as pd
L, MAXLEG, EXT, BARS = 5, 10, 20, sys.argv[1] if len(sys.argv) > 1 else "15min"
d = pd.read_parquet('/Users/trent/Claude-Code-Trading-Bot/data/futures/NQ/2026.parquet')
d = d.tz_convert('America/Chicago')
b = d.resample(BARS, label='left', closed='left').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna()
b = b[b.index >= b.index[-1] - pd.Timedelta(days=int(sys.argv[2]) if len(sys.argv) > 2 else 3)].reset_index()
o,h,l,c = b.open.values, b.high.values, b.low.values, b.close.values
n = len(b)
swHi=swLo=None; swHiIdx=swLoIdx=None; hiBroken=loBroken=True; trend=0; bullB=bearB=None
obs=[]; done=[]; breaks=[]
def leg(dirn, i, span):
    rng = range(i-max(span,1), i)  # exclude the breaking candle
    turn = min(rng, key=lambda k:(l[k], -k)) if dirn==1 else max(rng, key=lambda k:(h[k], k))
    # Pine scans newest->oldest keeping strictly better, so ties go to the newest bar
    start = turn
    for k in range(turn-1, max(i-span, turn-MAXLEG+1)-1, -1):
        if (dirn==1 and c[k]<o[k]) or (dirn==-1 and c[k]>o[k]): start=k
        else: break
    legc = (c[turn]<o[turn]) if dirn==1 else (c[turn]>o[turn])
    full = legc or start==turn
    ks = list(range(start, turn+1)); others = [k for k in ks if k!=turn]
    if dirn==1:
        bot = min(l[k] for k in ks); top = max(h[k] for k in (ks if full else others))
    else:
        top = max(h[k] for k in ks); bot = min(l[k] for k in (ks if full else others))
    return top, bot, start
for i in range(n):
    p = i - L
    if p >= L:
        if h[p] > max(h[p-L:p]) and h[p] >= max(h[p+1:p+L+1]): swHi, swHiIdx, hiBroken = h[p], p, False
        if l[p] < min(l[p-L:p]) and l[p] <= min(l[p+1:p+L+1]): swLo, swLoIdx, loBroken = l[p], p, False
    for ob in obs[:]:
        if (ob['dir']==1 and c[i] < ob['bot']) or (ob['dir']==-1 and c[i] > ob['top']):
            ob['end']=i; done.append(ob); obs.remove(ob)
    if not hiBroken and swHi is not None and c[i] > swHi:
        hiBroken=True; shift = trend!=1; trend=1; breaks.append((swHiIdx,i,swHi,1,shift))
        if shift:
            fr = min(swHiIdx, bearB) if bearB is not None else swHiIdx
            t,bt,s = leg(1,i,min(i-fr,500)); bullB=i
            for ob in [x for x in obs if x['dir']==1]: ob['end']=i; done.append(ob); obs.remove(ob)
            obs.append(dict(dir=1,top=t,bot=bt,left=s,born=i,end=None))
    if not loBroken and swLo is not None and c[i] < swLo:
        loBroken=True; shift = trend!=-1; trend=-1; breaks.append((swLoIdx,i,swLo,-1,shift))
        if shift:
            fr = min(swLoIdx, bullB) if bullB is not None else swLoIdx
            t,bt,s = leg(-1,i,min(i-fr,500)); bearB=i
            for ob in [x for x in obs if x['dir']==-1]: ob['end']=i; done.append(ob); obs.remove(ob)
            obs.append(dict(dir=-1,top=t,bot=bt,left=s,born=i,end=None))
# ---- SVG
W,H,PAD = 1000, 1000, 50
lo, hi = l.min(), h.max()
xw = (W-2*PAD)/(n+EXT)
X = lambda i: PAD + i*xw
Y = lambda v: PAD + (hi-v)/(hi-lo)*(H-2*PAD)
out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"><rect width="100%" height="100%" fill="white"/>']
for k in range(6):
    v = lo + k*(hi-lo)/5
    out.append(f'<text x="{W-PAD+4}" y="{Y(v):.0f}" font-size="11" font-family="Helvetica">{v:,.0f}</text>')
for k in range(0,n,max(1,n//12)):
    out.append(f'<text x="{X(k):.0f}" y="{H-20}" font-size="11" font-family="Helvetica">{b.ts[k]:%a %H:%M}</text>')
for ob in done+obs:
    col = '#9c27b0' if ob['dir']==1 else '#ff9800'
    right = ob['end'] if ob['end'] is not None else n-1+EXT
    op = '0.10' if ob['end'] is not None else '0.25'
    out.append(f'<rect x="{X(ob["left"]):.1f}" y="{Y(ob["top"]):.1f}" width="{X(right)-X(ob["left"]):.1f}" height="{Y(ob["bot"])-Y(ob["top"]):.1f}" fill="{col}" fill-opacity="{op}" stroke="{col}" stroke-opacity="{float(op)*3}"/>')
    lab = ("Bull OB" if ob['dir']==1 else "Bear OB") + ("" if ob['end'] is None else " (gone)")
    out.append(f'<text x="{X(right)+3:.1f}" y="{Y((ob["top"]+ob["bot"])/2)+4:.1f}" font-size="12" fill="{col}" font-family="Helvetica">{lab}</text>')
for (a,z,lvl,dirn,shift) in breaks:
    col = '#9c27b0' if dirn==1 else '#ff9800'
    out.append(f'<line x1="{X(a):.1f}" y1="{Y(lvl):.1f}" x2="{X(z):.1f}" y2="{Y(lvl):.1f}" stroke="{col}" stroke-dasharray="3,3"/>')
    out.append(f'<text x="{(X(a)+X(z))/2:.1f}" y="{Y(lvl)+(-4 if dirn==1 else 13):.1f}" font-size="11" fill="{col}" font-family="Helvetica">{"Shift" if shift else "BOS"}</text>')
for i in range(n):
    up = c[i]>=o[i]; col = '#26a69a' if up else '#222'
    out.append(f'<line x1="{X(i)+xw/2:.1f}" y1="{Y(h[i]):.1f}" x2="{X(i)+xw/2:.1f}" y2="{Y(l[i]):.1f}" stroke="{col}"/>')
    t,bt = max(o[i],c[i]), min(o[i],c[i])
    out.append(f'<rect x="{X(i)+xw*0.15:.1f}" y="{Y(t):.1f}" width="{xw*0.7:.1f}" height="{max(1,Y(bt)-Y(t)):.1f}" fill="{col}"/>')
out.append(f'<text x="{PAD}" y="30" font-size="18" font-family="Helvetica">NQ {BARS} bars, Order Block rule (Python twin of the Pine), dotted = structure breaks</text></svg>')
fn = f'/Users/trent/Claude-Code-Trading-Bot/research/results/ob_{BARS}.svg'
open(fn,'w').write('\n'.join(out))
print(fn, "bars", n, "breaks", len(breaks), "shifts", sum(1 for x in breaks if x[4]), "blocks", len(done)+len(obs), "live", len(obs))
for ob in done+obs:
    print(("BULL" if ob['dir']==1 else "BEAR"), b.ts[ob['left']].strftime('%a %H:%M'), f"{ob['bot']:.2f}-{ob['top']:.2f}", "legbars", ob['born']-ob['left'] if False else None, "gone" if ob['end'] is not None else "live")
