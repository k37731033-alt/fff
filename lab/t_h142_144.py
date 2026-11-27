# 56-7 장부 142(12월 절세 매도) · 144(추수감사절 뒤 5일 SOX·USD·SOXL) — 2026-11-27 가설 연구원
import pandas as pd, numpy as np, datetime as dt
rng=np.random.default_rng(0)
def ld(s):
    d=pd.read_csv(f'px/{s}.csv',parse_dates=['datetime']).set_index('datetime').sort_index(); return d['close']
def boot(x,n=10000):
    x=np.asarray(x); m=[rng.choice(x,len(x)).mean() for _ in range(n)]; return np.percentile(m,[5,95])
# ---------- 144 ----------
sox=pd.read_csv('sox.csv',parse_dates=['observation_date']).set_index('observation_date')['NASDAQSOX']
sox=pd.to_numeric(sox,errors='coerce').dropna(); sox=sox[sox.diff()!=0]  # 빠진 날(값 반복) 제거
def thanks(y):
    d=dt.date(y,11,1); first_thu=d+dt.timedelta((3-d.weekday())%7); return pd.Timestamp(first_thu+dt.timedelta(21))
def bf5(s,years):
    out=[]
    for y in years:
        t=thanks(y); idx=s.index[s.index>t]
        if len(idx)<6: continue
        b=idx[0]; 
        if (b-t).days!=1: continue
        i=s.index.get_loc(b); out.append((y,s.iloc[i+5]/s.iloc[i]-1, s.iloc[i]/s.iloc[max(i-200,0):i].mean()-1, s.iloc[i]/s[(s.index>=pd.Timestamp(y,10,31))].iloc[0]-1))
    return pd.DataFrame(out,columns=['y','r5','vs200','nov'])
print('=== 144 ===')
for name,s,ys in [('SOX',sox,range(2004,2026)),('SOXX',ld('SOXX'),range(2007,2026)),('USD',ld('USD'),range(2007,2026)),('SOXL',ld('SOXL'),range(2010,2026))]:
    r=bf5(s,ys); base=(s.shift(-5)/s-1).dropna()
    lo,hi=boot(r.r5.values-base.mean())
    print(f"{name} n={len(r)} 평균 {r.r5.mean()*100:+.2f}% 중간 {r.r5.median()*100:+.2f}% 상승 {np.mean(r.r5>0)*100:.0f}% 최악 {r.r5.min()*100:+.1f}% | 아무5일 {base.mean()*100:+.2f}% {np.mean(base>0)*100:.0f}% | 차이 90% [{lo*100:+.2f},{hi*100:+.2f}] | 좋은2개뺀 {np.sort(r.r5.values)[:-2].mean()*100:+.2f}% | 200일선아래 {len(r[r.vs200<0])}해 {r[r.vs200<0].r5.mean()*100:+.2f}% | 11월-10%이하 {len(r[r.nov<-.10])}해 {r[r.nov<-.10].r5.mean()*100:+.2f}%")
    if name=='SOX': print(r.assign(r5=(r.r5*100).round(2),vs200=(r.vs200*100).round(1),nov=(r.nov*100).round(1)).to_string(index=False))
# ---------- 142 ----------
print('=== 142 ===')
q=ld('QQQ_h143')
names=['AMD','AVGO','MRVL','MU','NVDA','QCOM','INTC','AMAT','LRCX','TXN','SOXX']
px={n:ld(n) for n in names}
rows=[]
for y in range(2010,2026):
    nov=q.index[(q.index.year==y)&(q.index.month==11)][-1]
    dec=q.index[(q.index.year==y)&(q.index.month==12)]; d10=dec[9]
    jan=q.index[(q.index.year==y+1)&(q.index.month==1)]; j5=jan[4]
    qa=q[d10]/q[nov]-1; qb=q[j5]/q[d10]-1
    for n in names:
        s=px[n]
        if nov not in s.index or j5 not in s.index: continue
        hist=s[:nov].iloc[-252:]
        if len(hist)<200: continue
        dd=s[nov]/hist.max()-1
        rows.append((y,n,dd,s[d10]/s[nov]-1-qa,s[j5]/s[d10]-1-qb))
R=pd.DataFrame(rows,columns=['y','sym','dd','exA','exB'])
def yboot(g,col,n=10000):
    ys=g.y.unique(); m=[]
    for _ in range(n):
        pick=rng.choice(ys,len(ys)); m.append(pd.concat([g[g.y==k] for k in pick])[col].mean())
    return np.percentile(m,[5,95])
for th in [-0.30,-0.40,-0.50]:
    L=R[R.dd<=th]; O=R[R.dd>th]
    for col,lab in [('exA','(가)11월말→12월10일째'),('exB','(나)12월10일째→1월5일째')]:
        lo,hi=yboot(L,col,3000)
        print(f"문턱{int(th*100)}% {lab}: 손실주 {len(L)}건/{L.y.nunique()}해 평균 {L[col].mean()*100:+.2f}%p 중간 {L[col].median()*100:+.2f} QQQ이김 {np.mean(L[col]>0)*100:.0f}% 범위[{lo*100:+.2f},{hi*100:+.2f}] | 나머지 {len(O)}건 {O[col].mean()*100:+.2f}%p | 해평균 {L.groupby('y')[col].mean().mean()*100:+.2f}")
L=R[R.dd<=-0.40]
print('2018~ (가)',f"{L[L.y>=2018].exA.mean()*100:+.2f}",len(L[L.y>=2018]),'(나)',f"{L[L.y>=2018].exB.mean()*100:+.2f}")
print(L.groupby('y').agg(n=('sym','count'),exA=('exA','mean'),exB=('exB','mean')).mul([1,100,100]).round(2).to_string())
nowd={n:(px[n].iloc[-1]/px[n].iloc[-252:].max()-1)*100 for n in names}
print('지금(11/25 종가) 52주 고점 대비:',{k:round(v,1) for k,v in nowd.items()})
R.to_csv('h142_rows.csv',index=False)
# 덧붙임: 절대 수익률·(나) 차이 범위
print('=== 142 덧붙임 ===')
q2=q
ab=[]
for _,r in R[R.dd<=-0.40].iterrows():
    y=r.y; nov=q.index[(q.index.year==y)&(q.index.month==11)][-1]; d10=q.index[(q.index.year==y)&(q.index.month==12)][9]
    s=px[r.sym]; ab.append((y,r.sym,s[d10]/s[nov]-1))
A=pd.DataFrame(ab,columns=['y','sym','abs']); print('손실주 절대 (가) 평균 %+.2f%% 오른 비율 %.0f%%'%(A['abs'].mean()*100,np.mean(A['abs']>0)*100)); print(A.assign(abs=(A['abs']*100).round(1)).to_string(index=False))
diffs=[]
ys=R.y.unique()
for _ in range(3000):
    pick=rng.choice(ys,len(ys)); g=pd.concat([R[R.y==k] for k in pick]); L=g[g.dd<=-0.40]; O=g[g.dd>-0.40]
    if len(L): diffs.append((L.exA.mean()-O.exA.mean(), L.exB.mean()-O.exB.mean()))
d=np.array(diffs); print('손실주−나머지 (가) 90%%[%+.2f,%+.2f] (나) 90%%[%+.2f,%+.2f]'%tuple(np.r_[np.percentile(d[:,0],[5,95]),np.percentile(d[:,1],[5,95])]*100))
