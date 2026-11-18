# 가설 연구원 11/18 — 56 장부 80·81·82번. 자료: FRED(VIXCLS, NASDAQ100, NASDAQSOX), SEC submissions(NVDA 8-K Item 2.02)
import pandas as pd, numpy as np, json, sys, os
rng=np.random.default_rng(7)
def fred(i):
    d=pd.read_csv(f'fred/{i}.csv'); d.columns=['d','v']; d['d']=pd.to_datetime(d['d']); d['v']=pd.to_numeric(d['v'],errors='coerce')
    return d.dropna().set_index('d')['v']
vix,ndx,sox=fred('VIXCLS'),fred('NASDAQ100'),fred('NASDAQSOX')
def fwd(px,h): return px.shift(-h)/px-1
def mdd_fwd(px,h):
    a=px.values; out=np.full(len(a),np.nan)
    for i in range(len(a)-h): out[i]=a[i+1:i+h+1].min()/a[i]-1
    return pd.Series(out,index=px.index)
def boot(x,n=5000):
    x=np.asarray(x,float); x=x[~np.isnan(x)]
    if len(x)<3: return (np.nan,np.nan)
    m=rng.choice(x,(n,len(x))).mean(1); return (np.percentile(m,5),np.percentile(m,95))
def dedupe(dates,px,gap):
    pos=[px.index.get_loc(d) for d in dates if d in px.index]; keep=[]; last=-10**9
    for p in pos:
        if p-last>gap: keep.append(p); last=p
    return px.index[keep]
def report(name,ev,px,hs,start=None):
    px=px if start is None else px[px.index>=start]
    ev=[d for d in ev if d in px.index]
    for h in hs:
        f=fwd(px,h); base=f.dropna(); e=f.reindex(ev).dropna()
        if len(e)==0: continue
        lo,hi=boot(e.values); d=e.values-base.mean(); dlo,dhi=boot(d)
        k=max(1,int(round(len(e)*0.3))); rec=e.iloc[-k:]
        ex2=np.sort(e.values)[:-2].mean() if len(e)>4 else np.nan
        md=mdd_fwd(px,h).reindex(e.index)
        print(f"{name} h={h}: n={len(e)} mean={e.mean()*100:+.2f}% med={e.median()*100:+.2f}% win={np.mean(e>0)*100:.0f}% worst={e.min()*100:+.1f}% CI90=[{lo*100:+.2f},{hi*100:+.2f}] | base mean={base.mean()*100:+.2f}% win={np.mean(base>0)*100:.0f}% | diff={d.mean()*100:+.2f}%p CI90=[{dlo*100:+.2f},{dhi*100:+.2f}] | recent30%(n={k})={rec.mean()*100:+.2f}% | ex-top2={ex2*100:+.2f}% | path-min med={md.median()*100:+.1f}% worst={md.min()*100:+.1f}% (base med={mdd_fwd(px,h).median()*100:+.1f}%)")
which=sys.argv[1] if len(sys.argv)>1 else 'all'
if which in('80','all'):
    print('=== H80 VIX 하루 급등 ==='); r=vix.pct_change()
    print('최근 급등 상위:', (r[r.index>='2026-01-01'].nlargest(5)*100).round(1).to_dict())
    print('1990~ 상위 6:', (r.nlargest(6)*100).round(1).to_dict())
    for thr in (0.30,0.40,0.50):
        raw=r[r>=thr].index
        for nm,px in (('NDX',ndx),('SOX',sox)):
            ev=dedupe([d for d in raw if d>=px.index[0]],px,20)
            print(f'-- thr +{int(thr*100)}% {nm}: raw={sum(d>=px.index[0] for d in raw)} kept={len(ev)} last={[str(d.date()) for d in ev[-4:]]}')
            report(f'VIX+{int(thr*100)} {nm}',ev,px,(5,20,60),start=max(px.index[0],pd.Timestamp('1990-01-02')))
if which in('81','all'):
    print('=== H81 데드크로스 ===')
    for nm,px in (('SOX',sox),('NDX',ndx)):
        s50,s200=px.rolling(50).mean(),px.rolling(200).mean(); below=(s50<s200)&s200.notna()
        cross=below&(~below.shift(1,fill_value=False))&s200.shift(1).notna()
        ev=list(px.index[cross.values]); print(nm,'crosses',len(ev),[str(d.date()) for d in ev])
        report(f'DC {nm}',ev,px,(20,60,120),start=px.index[199])
        # 뒷북인가: 크로스 전 120일~뒤 250일 구간의 최저 종가가 크로스 전에 나왔나
        late=0; rows=[]
        for d in ev:
            i=px.index.get_loc(d); w=px.iloc[max(0,i-120):min(len(px),i+251)]
            lowd=w.idxmin(); before=lowd<=d; late+=before
            dd_from_high=px.iloc[i]/px.iloc[max(0,i-250):i+1].max()-1
            after=px.iloc[i+1:min(len(px),i+251)]
            rows.append((str(d.date()),f"{dd_from_high*100:+.0f}%",str(lowd.date()),'전' if before else '뒤',f"{(after.min()/px.iloc[i]-1)*100:+.0f}%" if len(after) else 'NA'))
        print(' 저점이 크로스 이전(뒷북):',late,'/',len(ev)); 
        for x in rows: print('  ',x)
        print(' 지금:',str(px.index[-1].date()),'종가',px.iloc[-1],'50일선',round(s50.iloc[-1],1),'200일선',round(s200.iloc[-1],1))
if which in('82','all'):
    print('=== H82 NVDA 실적 반응일 뒤 ===')
    ed=pd.to_datetime(pd.read_csv('nvda_earn_sec.csv')['filed'])
    rd=[]; 
    for d in sorted(ed):
        nx=sox.index[sox.index>d]
        if len(nx): rd.append(nx[0])
    rd=sorted(set(rd)); r0=sox.pct_change()
    for nm,px in (('SOX',sox),('NDX',ndx)):
        for cut in (0.0,0.01):
            up=[d for d in rd if r0.get(d,np.nan)>cut]; dn=[d for d in rd if r0.get(d,np.nan)<=0]
            print(f'-- {nm} 반응일 SOX>{cut*100:.0f}%: up n={len(up)} / down n={len(dn)} / all {len(rd)}')
            report(f'UP>{int(cut*100)} {nm}',up,px,(5,10),start=sox.index[0])
            if cut==0: 
                report(f'DOWN {nm}',dn,px,(5,10),start=sox.index[0])
                for h in (5,10):
                    f=fwd(px,h); a=f.reindex(up).dropna().values; b=f.reindex(dn).dropna().values
                    ds=[rng.choice(a,len(a)).mean()-rng.choice(b,len(b)).mean() for _ in range(5000)]
                    print(f'   up−down h={h}: {(a.mean()-b.mean())*100:+.2f}%p CI90=[{np.percentile(ds,5)*100:+.2f},{np.percentile(ds,95)*100:+.2f}]')
    print(' 반응일 SOX 평균',round(r0.reindex(rd).mean()*100,2),'% 오른 비율',round((r0.reindex(rd)>0).mean()*100),'%')
