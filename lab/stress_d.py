# D 반등 '과장 의심' 스트레스 테스트: 급락 뒤 실제 IV가 모델보다 비싸다고 가정
# 사는 날 IV = 20일 변동성 × a, 파는 날 IV = × b (급락 뒤 IV가 내려오는 '변동성 하락' 반영), 호가 손해 c
import pandas as pd, numpy as np, os
from math import sqrt
exec(open('t52.py',encoding='utf-8').read().split("rows=[]")[0])
ev=[]
for sec,tks in SECT.items():
    for s in tks:
        f=f'../data/daily/{s}.csv'
        if not os.path.exists(f): continue
        d=pd.read_csv(f,parse_dates=['datetime']).set_index('datetime'); d=d[~d.index.duplicated()]; d=d[(d.close>=1)&(d.volume>0)]
        lr=np.log(d.close).diff(); d['sd']=lr.rolling(20).std().shift(1)
        d['s50']=d.close.rolling(50).mean().shift(1); d['s200']=d.close.rolling(200).mean().shift(1)
        last=-99
        for k in range(203,len(d)-6):
            sd=d.sd.iloc[k]
            if np.isnan(sd) or sd<0.004 or not d.s50.iloc[k]>d.s200.iloc[k]: continue
            if d.close.iloc[k]/d.close.iloc[k-3]-1>-1.5*sd*sqrt(3) or k-last<5: continue
            last=k; L=lab(d.index[k])
            if L is None: continue
            ev.append(dict(sec=sec,reg=L,y26=d.index[k]>=pd.Timestamp('2026-05-01'),S0=d.open.iloc[k+1],S1=d.close.iloc[k+6],v=max(sd*sqrt(252),0.15)))
E=pd.DataFrame(ev)
def run(g,a,b,c):
    r=[]
    for _,x in g.iterrows():
        p0=bs(x.S0,x.S0,10/252,x.v*a,True)*(1+c); p1=bs(x.S1,x.S0,4.75/252,x.v*b,True)*(1-c); r.append(p1/p0-1)
    r=pd.Series(r).sort_values(); t=r.iloc[:int(len(r)*0.95)].mean()
    return f'평균{r.mean()*100:+.0f}% 상위5%빼면{t*100:+.0f}% 이김{(r>0).mean()*100:.0f}%'
print('사건 수:',E.reg.value_counts().to_dict(),'2026-05~:',int(E.y26.sum()))
for a,b,c,name in [(1.2,1.2,0.05,'기존 모델'),(1.5,1.3,0.08,'급락 뒤 IV 25% 비쌈 + 호가 8%'),(1.8,1.4,0.10,'IV 50% 비쌈 + 호가 10%'),(2.2,1.6,0.12,'IV 83% 비쌈 + 호가 12% (아주 가혹)')]:
    print(f'\n[{name}] 사는 날 IV×{a}, 파는 날 ×{b}, 호가 ±{int(c*100)}%')
    for lbl,g in [('🙂N',E[E.reg=='N']),('🔥H',E[E.reg=='H']),('🔥🔥HH',E[E.reg=='HH']),('2026-05~',E[E.y26])]:
        print(f'  {lbl:9s} n{len(g):4d}  {run(g,a,b,c)}')
