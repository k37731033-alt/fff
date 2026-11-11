"""이벤트(선두 종목 실적) 전날 종가에 2차 종목 옵션을 사서 다음 날 시가에 파는 모델 손익.
선두: NVDA·AVGO·AMZN·ORCL·CRWV 실적(2024-01~). 옵션: 등가, 만기까지 3거래일, IV=RV20*k, 시가에 IV*0.95, 왕복 비용 8%."""
import json,glob,os,numpy as np,pandas as pd
from math import log,sqrt,erf
N=lambda x:0.5*(1+erf(x/sqrt(2)))
def bs(S,K,T,v,call):
    d1=(log(S/K)+v*v*T/2)/(v*sqrt(T));d2=d1-v*sqrt(T)
    return S*N(d1)-K*N(d2) if call else K*N(-d2)-S*N(-d1)
ev={}
p='/root/.claude/projects/-home-claude/c5d8715e-910b-5c3f-9687-e6b60606200c.jsonl'
def walk(x):
    if isinstance(x,str) and x.startswith('{\n  "symbol"') and 'quarterlyEarnings' in x:
        try:j=json.loads(x)
        except:return
        ev[j['symbol']]=[(q['reportedDate'],q['reportTime']) for q in j['quarterlyEarnings'] if q['reportedDate']>='2024-01-01']
    elif isinstance(x,dict):[walk(v) for v in x.values()]
    elif isinstance(x,list):[walk(v) for v in x]
for line in open(p):
    if 'quarterlyEarnings' in line:
        try:walk(json.loads(line))
        except:pass
print({k:len(v) for k,v in ev.items()})
D={}
for f in glob.glob('data/daily/*.csv'):
    d=pd.read_csv(f).sort_values('datetime').reset_index(drop=True)
    r=np.log(d.close).diff();d['rv']=r.rolling(20).std()*np.sqrt(252)
    d['dd']=d.close/d.close.rolling(20).max()-1
    D[os.path.basename(f)[:-4]]=d.set_index('datetime')
SEMI=['MU','SNDK','NVDA','AMD','AVGO','TSM','MRVL','AMAT','LRCX','KLAC','ASML','SOXL','LITE','COHR','ANET','VRT','SMCI','DELL','CRWV','IREN','APLD','ORCL','ALAB','CRDO','ARM','QCOM','INTC']
rows=[]
for lead,L in ev.items():
    if lead not in D:continue
    idx=list(D[lead].index)
    for date,tm in L:
        if date not in D[lead].index:continue
        i=idx.index(date); b=i if tm=='post-market' else i-1   # 사는 날(종가)
        if b+1>=len(idx) or b<0:continue
        bd,rd=idx[b],idx[b+1]
        lg=D[lead].open[rd]/D[lead].close[bd]-1
        for t in SEMI:
            if t==lead or t not in D or bd not in D[t].index or rd not in D[t].index:continue
            x=D[t];S=x.close[bd];O=x.open[rd];rv=x.rv[bd]
            if not rv>0:continue
            for k in(1.2,1.6):
                v=max(rv*k,.25)
                c0=bs(S,S,3/252,v,1);p0=bs(S,S,3/252,v,0)
                c1=bs(O,S,2.6/252,v*.95,1);p1=bs(O,S,2.6/252,v*.95,0)
                rows.append(dict(lead=lead,date=bd,t=t,k=k,lg=lg,gap=O/S-1,dd=x.dd[bd],call=c1*.96/(c0*1.04)-1,put=p1*.96/(p0*1.04)-1,strad=(c1+p1)*.96/((c0+p0)*1.04)-1,rvmove=abs(O/S-1)/(rv/np.sqrt(252))))
a=pd.DataFrame(rows);a.to_pickle('/tmp/claude-0/-home-claude/c5d8715e-910b-5c3f-9687-e6b60606200c/scratchpad/preevent.pkl')
def show(n,x):
    if len(x)<15:print(f'{n}: n={len(x)} 표본 적음');return
    print(f'{n}: n={len(x)} (이벤트 {x.date.nunique()}) | 갭 평균 {x.gap.mean():+.2%} 절대 {x.gap.abs().mean():.2%} | 콜 {x.call.mean():+.0%}(중간 {x.call.median():+.0%}, 이김 {(x.call>0).mean():.0%}) | 풋 {x.put.mean():+.0%}(이김 {(x.put>0).mean():.0%}) | 양쪽 {x.strad.mean():+.0%}(중간 {x.strad.median():+.0%}, 이김 {(x.strad>0).mean():.0%})')
for k in(1.2,1.6):
    b=a[a.k==k];print(f'\n=== IV = RV20 × {k}')
    show('전체',b)
    for l in ev:
        show(f'  선두 {l}',b[b.lead==l])
    show('  과낙폭(20일 고점 −15%↓)',b[b.dd<=-.15]); show('  과낙폭 아님',b[b.dd>-.15])
    show('  2026-05~',b[b.date>='2026-05-01']); show('  2026-05~ 과낙폭',b[(b.date>='2026-05-01')&(b.dd<=-.15)])
    show('  메모리(MU·SNDK)',b[b.t.isin(['MU','SNDK'])])
    show('  선두 갭 방향 = 위(사후)',b[b.lg>0.03]); show('  선두 갭 방향 = 아래(사후)',b[b.lg<-0.03])
