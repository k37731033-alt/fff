# 이틀 급등(2일 수익 ≥ 2σ·√2) 뒤 풋: 다음 날·이틀 뒤 결과, 장 온도별 (52종목)
import pandas as pd,numpy as np,glob,os
from math import sqrt
from tests import bs, reg, lab
fs=sorted(glob.glob('../data/daily/*.csv'))
skip={'SOXL','SOXX','QQQ'}
CPI=pd.to_datetime(['2025-12-18','2026-01-13','2026-02-13','2026-03-11','2026-04-10','2026-05-12',
 '2026-06-10','2026-07-14','2026-08-12','2026-09-11','2026-10-14'])   # 40 문서 3-1
rows=[];base=[]
for f in fs:
    s=os.path.basename(f)[:-4]
    if s in skip: continue
    d=pd.read_csv(f,parse_dates=['datetime']).set_index('datetime')
    r=d.close.pct_change()
    sig=np.log(d.close).diff().rolling(20).std().shift(2)          # 급등 이틀 전까지의 σ
    r2=d.close/d.close.shift(2)-1
    z2=r2/(sig*sqrt(2))
    f1=d.close.shift(-1)/d.close-1; f2=d.close.shift(-2)/d.close-1
    up=(d.close.rolling(50).mean()>d.close.rolling(200).mean())
    for i in range(220,len(d)-2):
        t=d.index[i]
        if t not in reg.index: continue
        L=lab(t)
        if L is None or np.isnan(z2.iloc[i]): continue
        v=sig.iloc[i]*sqrt(252)
        rec=dict(s=s,t=t,reg=L,z2=z2.iloc[i],f1=f1.iloc[i],f2=f2.iloc[i],sig=sig.iloc[i],up=up.iloc[i],
                 cpi_next=(d.index[i+1] in CPI))
        # 풋 모델: 종가에 4거래일 남은 풋 매수 → 다음 날/이틀 뒤 종가 매도. 호가 손해 ±8%
        S0=d.close.iloc[i]
        for nm,otm in (('atm',0.0),('o3',0.03)):
            for ivm in (1.2,1.5):
                K=S0*(1-otm); p0=bs(S0,K,4/252,v*ivm,False)*1.08
                for h,lbl in ((1,'1'),(2,'2')):
                    S1=d.close.iloc[i+h]; p1=bs(S1,K,(4-h)/252,v*ivm,False)*0.92
                    rec[f'{nm}_{ivm}_{lbl}']=p1/p0-1 if p0>0 else np.nan
        (rows if z2.iloc[i]>=2 else base).append(rec)
E=pd.DataFrame(rows); B=pd.DataFrame(base)
def tm(x):  # 상위 5% 뺀 평균
    x=x.dropna(); return x[x<=x.quantile(0.95)].mean()
def show(df,name):
    print(f'\n== {name} ==')
    for k in ['N','H','HH']:
        g=df[df.reg==k]
        if len(g)==0: continue
        print(f"{k:2s} n={len(g):5d} 다음날 하락 {100*(g.f1<0).mean():4.0f}% 평균 {100*g.f1.mean():+5.2f}% | 이틀 하락 {100*(g.f2<0).mean():4.0f}% 평균 {100*g.f2.mean():+5.2f}%"
              f" | 등가풋 1일(IV×1.2) 평균 {100*g['atm_1.2_1'].mean():+4.0f}% 절삭 {100*tm(g['atm_1.2_1']):+4.0f}% 이김 {100*(g['atm_1.2_1']>0).mean():3.0f}%"
              f" | ×1.5 {100*g['atm_1.5_1'].mean():+4.0f}% | 3%외가 1일 {100*g['o3_1.2_1'].mean():+4.0f}% 2배↑ {100*(g['o3_1.2_1']>=1).mean():3.0f}% | 등가 2일 {100*g['atm_1.2_2'].mean():+4.0f}%")
show(E,'이틀 급등(≥2σ) 뒤 — 전체 기간')
show(B,'비교: 아무 날')
for a,b in (('2006','2019'),('2020','2023'),('2024','2026')):
    show(E[(E.t>=a)&(E.t<=b+'-12-31')],f'이틀 급등 뒤 {a}~{b}')
show(E[E.t>='2026-05-01'],'이틀 급등 뒤 2026-05~ (지금과 비슷한 장)')
show(B[B.t>='2026-05-01'],'아무 날 2026-05~')
c=E[E.cpi_next]; cb=B[B.cpi_next]
print('\n== 다음 날이 CPI 날 (2025-12~2026-10, 11번) ==')
print('이틀 급등 뒤 CPI 날:',len(c),'건 다음날 하락',round(100*(c.f1<0).mean()) if len(c) else '-', '평균',round(100*c.f1.mean(),2) if len(c) else '-')
allc=pd.concat([c,cb]); print('CPI 날 전체(종목×날):',len(allc),'하락',round(100*(allc.f1<0).mean()),'% 평균',round(100*allc.f1.mean(),2),'% 등가풋1일',round(100*allc['atm_1.2_1'].mean()),'%')
print(c.groupby(c.t.dt.date).agg(n=('s','size'),down=('f1',lambda x:(x<0).mean()),avg=('f1','mean')))
E.to_pickle('/tmp/claude-0/-home-claude/c5d8715e-910b-5c3f-9687-e6b60606200c/scratchpad/surge2.pkl')
