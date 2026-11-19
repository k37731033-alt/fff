# 56 장부 94·95번 (2026-11-19 가설 연구원)
# 94: 개장 직후 눌린 날 10:00에 사면 종가가 더 높은가(SOXX)  /  95: 하락 추세의 갭 상승은 장중에 팔리나
# 자료: Massive SOXX 30분봉·일봉(분할 조정) 2024-11-19~2026-11-18 → h94_soxx_days.csv (날짜별 요약, SQL로 뽑음)
#       Massive QQQ·NVDA·MU·AMD 일봉 → h95_4tickers_days.csv (갭·시가→종가는 bp, b: 1=전날 종가<50일선, 0=위, 9=50일 미만)
#       FRED NASDAQSOX(200일선 판정용)
import pandas as pd, numpy as np, math
from scipy.stats import norm
rng=np.random.default_rng(20261119)
d=pd.read_csv('h94_soxx_days.csv',parse_dates=['date']).set_index('date')
sox=pd.read_csv('fred_20261118/NASDAQSOX.csv',parse_dates=['observation_date']).set_index('observation_date')['NASDAQSOX']
sox=pd.to_numeric(sox,errors='coerce').dropna()
below200=(sox<sox.rolling(200).mean()).shift(1)          # 전날 종가 기준
d['b200']=below200.reindex(d.index).ffill()
cl=pd.concat([pd.Series([d.pc.iloc[0]],index=[d.index[0]-pd.Timedelta(days=1)]),d.c])
d['ma50']=d.pc.rolling(50).mean()                          # pc = 전날 종가 → 전날까지의 50일 평균
d['b50']=np.where(d.ma50.isna(),np.nan,(d.pc<d.ma50)*1.0)
lr=np.log(d.pc).diff(); d['rv20']=lr.rolling(20).std()*np.sqrt(252)   # 전날까지 20일 변동성
def bm(a,n=10000):
    a=np.asarray(a,float); return np.percentile([rng.choice(a,len(a)).mean() for _ in range(n)],[5,95])
def bd(a,b,n=10000):
    a,b=np.asarray(a,float),np.asarray(b,float)
    return np.percentile([rng.choice(a,len(a)).mean()-rng.choice(b,len(b)).mean() for _ in range(n)],[5,95])
def line(lab,a,base=None,drop='top'):
    a=pd.Series(a).dropna()
    if len(a)<3: print(f'  {lab}: {len(a)}건 — 너무 적음'); return
    lo,hi=bm(a); s=f'  {lab}: {len(a)}건 평균 {a.mean():+.2f}% · 중간값 {a.median():+.2f}% · 이김 {100*(a>0).mean():.0f}% · 최악 {a.min():+.1f}% · 90% {lo:+.2f}~{hi:+.2f}'
    if base is not None:
        l2,h2=bd(a,base); s+=f' | 기준 {np.mean(base):+.2f}% · 차이 {a.mean()-np.mean(base):+.2f}%p(90% {l2:+.2f}~{h2:+.2f})'
    k=int(len(a)*0.7); s+=f' | 최근 30%({len(a)-k}건) {a.iloc[k:].mean():+.2f}%'
    x=a.sort_values(); x=x.iloc[:-2] if drop=='top' else x.iloc[2:]
    s+=f' | {"가장 좋은" if drop=="top" else "가장 나쁜"} 2건 빼면 {x.mean():+.2f}%'
    print(s)

print('===== 94번: 개장 직후 눌린 날 10:00 매수 → 종가 (SOXX) =====')
f=d[d.nb==13].copy()                                       # 반장 제외
f['r10']=(f.c/f.c930-1)*100; f['r1030']=(f.c/f.c1000-1)*100; f['r10_12']=(f.c1200/f.c930-1)*100
f['dip30']=f.l930/f.pc-1; f['dip60']=np.minimum(f.l930,f.l1000)/f.pc-1; f['gap']=f.o/f.pc-1
print(f'전체 {len(f)}일 · 기간 {f.index[0].date()}~{f.index[-1].date()} · SOX 200일선 아래였던 날 {int(f.b200.sum())}일')
print(f'  의심 봉(09:30 봉 저가가 10:00 가격보다 2% 넘게 낮음): {int(((f.c930/f.l930-1)>0.02).sum())}일')
for th in (-0.01,-0.02):
    print(f'-- 문턱 {th*100:.0f}%')
    line('[주 판정] 30분 저가 기준·10:00 매수→종가' if th==-0.01 else '30분 저가 기준·10:00 매수→종가', f.r10[f.dip30<=th], f.r10)
    line('  └ 10:00→12:00', f.r10_12[f.dip30<=th], f.r10_12)
    line('첫 1시간 저가 기준·10:30 매수→종가', f.r1030[f.dip60<=th], f.r1030)
    line('(확인) 10:00 가격 자체가 문턱 아래일 때만', f.r10[(f.c930/f.pc-1)<=th], f.r10)
e=f[f.dip30<=-0.01]
line('문턱 −1% · SOX 200일선 아래', e.r10[e.b200==1], f.r10[f.b200==1]); line('문턱 −1% · SOX 200일선 위', e.r10[e.b200==0], f.r10[f.b200==0])
line('문턱 −1% · 갭 하락으로 연 날(시가 ≤ −1%)', e.r10[e.gap<=-0.01], f.r10); line('문턱 −1% · 시가는 멀쩡했다가 눌린 날(시가 > −1%)', e.r10[e.gap>-0.01], f.r10)
# 옵션 모델: 그 주 금요일 만기 등가 콜(금요일이면 다음 주 금요일), IV = rv20×1.2, 10:00 매수 → 당일 종가 매도, 왕복 8% + 수수료 1.99달러×2
def bs(S,K,T,v,r=0.04):
    if T<=0: return max(S-K,0)
    d1=(math.log(S/K)+(r+v*v/2)*T)/(v*math.sqrt(T)); return S*norm.cdf(d1)-K*math.exp(-r*T)*norm.cdf(d1-v*math.sqrt(T))
def optret(row):
    if not np.isfinite(row.rv20): return np.nan
    wd=row.name.weekday(); days=(4-wd) if wd<4 else 7
    v=row.rv20*1.2; K=row.c930
    b=bs(row.c930,K,(days+6/24)/365,v)*1.04; s=bs(row.c,K,days/365,v)*0.96
    return ((s*100-1.99)/(b*100+1.99)-1)*100
f['opt']=f.apply(optret,axis=1)
line('[모델] 눌린 날(−1%) 등가 콜 10:00→종가', f.opt[f.dip30<=-0.01], f.opt.dropna()); line('[모델] 아무 날 등가 콜 10:00→종가', f.opt)

print('\n===== 95번: 하락 추세의 갭 상승 → 시가→종가 =====')
d['gap']=(d.o/d.pc-1)*100; d['oc']=(d.c/d.o-1)*100
g=d.dropna(subset=['b50'])
print(f'SOXX {len(g)}일(50일선 계산 가능, {g.index[0].date()}~) · 50일선 아래 {int(g.b50.sum())}일 · 아무 날 시가→종가 {g.oc.mean():+.2f}%')
for th in (1,2):
    line(f'[주 판정] SOXX 갭 ≥ +{th}% · 50일선 아래' if th==1 else f'SOXX 갭 ≥ +{th}% · 50일선 아래', g.oc[(g.gap>=th)&(g.b50==1)], g.oc, 'bot')
    line(f'SOXX 갭 ≥ +{th}% · 50일선 위', g.oc[(g.gap>=th)&(g.b50==0)], g.oc, 'bot')
A=g.oc[(g.gap>=1)&(g.b50==1)]; B=g.oc[(g.gap>=1)&(g.b50==0)]; l,h=bd(A,B); print(f'  아래 − 위 차이 {A.mean()-B.mean():+.2f}%p (90% {l:+.2f}~{h:+.2f})')
line('SOXX 갭 ≥ +1% · SOX 200일선 아래(2년 전체)', d.oc[(d.gap>=1)&(d.b200==1)], d.oc, 'bot'); line('SOXX 갭 ≥ +1% · SOX 200일선 위', d.oc[(d.gap>=1)&(d.b200==0)], d.oc, 'bot')
line('비교: SOXX 갭 ≤ −1% · 50일선 아래', g.oc[(g.gap<=-1)&(g.b50==1)], g.oc)
ee=d[(d.gap>=1)&(d.nb==13)]; print(f'  갭 ≥ +1% 날({len(ee)}) 첫 30분(시가→10:00) 평균 {((ee.c930/ee.o-1)*100).mean():+.2f}% · 10:00→종가 {((ee.c/ee.c930-1)*100).mean():+.2f}% · 종가 < 시가 비율 {100*(ee.c<ee.o).mean():.0f}%')
# 5종목 합침(날짜 묶음 부트스트랩)
w=pd.read_csv('h95_4tickers_days.csv'); w['date']=pd.to_datetime('20'+w.date); w=w.set_index('date')
rows=[]
for k in 'qnma':
    t=pd.DataFrame({'gap':w[f'{k}_gap']/100,'oc':w[f'{k}_oc']/100,'b':w[f'{k}_b'],'tk':k}); rows.append(t[t.b!=9])
t=g[['gap','oc']].copy(); t['b']=g.b50; t['tk']='s'; rows.append(t)
P=pd.concat(rows).reset_index().rename(columns={'index':'date'})
def cl_boot(E,Ball,n=5000):
    # 날짜 단위로 다시 뽑아 사건 평균 − 전체 평균
    days=Ball.date.unique(); gE=E.groupby('date').oc.agg(['sum','count']).reindex(days).fillna(0); gB=Ball.groupby('date').oc.agg(['sum','count']).reindex(days)
    out=[]
    for _ in range(n):
        i=rng.integers(0,len(days),len(days)); se,ce=gE['sum'].values[i].sum(),gE['count'].values[i].sum()
        if ce==0: continue
        out.append(se/ce-gB['sum'].values[i].sum()/gB['count'].values[i].sum())
    return np.percentile(out,[5,95])
names={'q':'QQQ','n':'NVDA','m':'MU','a':'AMD','s':'SOXX'}
for th in (1,2):
    for b,lab in ((1,'50일선 아래'),(0,'50일선 위')):
        E=P[(P.gap>=th)&(P.b==b)]; l,h=cl_boot(E,P)
        print(f'  5종목 합침 갭 ≥ +{th}% · {lab}: {len(E)}건({E.date.nunique()}일) 평균 {E.oc.mean():+.2f}% · 중간값 {E.oc.median():+.2f}% · 종가<시가 {100*(E.oc<0).mean():.0f}% | 아무 날 {P.oc.mean():+.2f}% · 차이 {E.oc.mean()-P.oc.mean():+.2f}%p (날짜 묶음 90% {l:+.2f}~{h:+.2f})')
for k in 'sqnma':
    E=P[(P.tk==k)&(P.gap>=1)&(P.b==1)]; F=P[(P.tk==k)&(P.gap>=1)&(P.b==0)]; al=P[P.tk==k]
    print(f'   {names[k]}: 아래 {len(E)}건 {E.oc.mean():+.2f}%(종가<시가 {100*(E.oc<0).mean():.0f}%) / 위 {len(F)}건 {F.oc.mean():+.2f}%({100*(F.oc<0).mean():.0f}%) / 아무 날 {al.oc.mean():+.2f}%')
E=P[(P.gap>=1)&(P.b==1)].sort_values('date'); dd=sorted(E.date.unique()); cut=dd[int(len(dd)*0.7)]
print(f'  5종목 아래·갭≥+1% 최근 30% 날짜({cut.date()}~): {E[E.date>=cut].oc.mean():+.2f}% ({len(E[E.date>=cut])}건) / 그 전: {E[E.date<cut].oc.mean():+.2f}%')
x=E.groupby('date').oc.mean().sort_values(); print(f'  날짜 평균으로: {len(x)}일 평균 {x.mean():+.2f}% · 가장 나쁜 2일 빼면 {x.iloc[2:].mean():+.2f}% · 90% {bm(x)[0]:+.2f}~{bm(x)[1]:+.2f}')
print('  최근 사건 날:', ', '.join(f'{a.date()}({b:+.1f})' for a,b in x.sort_index().tail(8).items()))
