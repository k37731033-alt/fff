# 52종목 × 장 온도(SOXX 기준 🙂N/🔥H/🔥🔥HH) × 2026-05~ 재검증
# 각 종목의 '평소 하루 움직임(σ)'으로 크기를 맞춰서 빅테크와 양자주를 같은 잣대로 본다.
import pandas as pd, numpy as np, os, json, sys
from math import log, sqrt, erf
def Nf(x): return 0.5*(1+erf(x/sqrt(2)))
def bs(S,K,T,v,call):
    if T<=0 or v<=0: return max(S-K,0) if call else max(K-S,0)
    d1=(log(S/K)+0.5*v*v*T)/(v*sqrt(T)); d2=d1-v*sqrt(T)
    return S*Nf(d1)-K*Nf(d2) if call else K*Nf(-d2)-S*Nf(-d1)
R=pd.read_csv('../data/soxx_regime.csv',parse_dates=['datetime']).set_index('datetime')
reg=pd.DataFrame(index=R.index)
reg['v20']=R.v20.shift(1); reg['ratio']=R.ratio.shift(1)
def lab(i):
    if i not in reg.index: return None
    x=reg.loc[i]
    if pd.isna(x.ratio): return None
    return 'HH' if x.v20>=0.5 else ('H' if x.ratio>=1.3 else 'N')
SECT={'메모리':['MU','SNDK','SKHY'],'광통신·연결칩':['LITE','COHR','AAOI','MRVL','CRDO','ALAB','SMTC'],
'장비':['ASML','AMAT','LRCX','KLAC'],'칩설계·파운드리':['NVDA','AMD','INTC','QCOM','ARM','AVGO','TSM','SOXL'],
'서버·네트워크·전력':['DELL','SMCI','ANET','VRT'],'AI클라우드':['CRWV','IREN','APLD','ORCL'],
'빅테크':['AAPL','MSFT','GOOGL','AMZN','META','TSLA'],'보안·SW':['PANW','PLTR','DDOG','NOW'],
'원전':['CEG','OKLO'],'양자':['IONQ','RGTI'],'우주':['ASTS','RKLB','SPCX'],'크립토·핀테크':['COIN','MSTR','HOOD'],'바이오':['LLY','MRNA']}
rows=[]
for sec,tks in SECT.items():
    for s in tks:
        f=f'../data/daily/{s}.csv'
        if not os.path.exists(f): print('없음',s); continue
        d=pd.read_csv(f,parse_dates=['datetime']).set_index('datetime')
        d=d[~d.index.duplicated()]
        d=d[(d.close>=1)&(d.volume>0)]
        d['pc']=d.close.shift(1); lr=np.log(d.close).diff()
        d['sd']=lr.rolling(20).std().shift(1)            # 전날까지 하루 σ
        d['v']=d.sd*sqrt(252)
        d['s50']=d.close.rolling(50).mean().shift(1); d['s200']=d.close.rolling(200).mean().shift(1)
        d['up']=d.s50>d.s200
        d['gap']=d.open/d.pc-1; d['ret']=d.close/d.pc-1
        ix=d.index; n=len(d)
        for k in range(21,n-6):
            i=ix[k]; L=lab(i)
            if L is None or np.isnan(d.sd.iloc[k]): continue
            sd=d.sd.iloc[k]
            if sd<0.004: continue
            v=max(d.v.iloc[k],0.15); o=d.open.iloc[k]; c=d.close.iloc[k]; h=d.high.iloc[k]; lo=d.low.iloc[k]
            base={'sec':sec,'tk':s,'reg':L,'date':i,'y26':i>=pd.Timestamp('2026-05-01')}
            g=d.gap.iloc[k]
            # A 큰 갭(1.5σ 이상): 시가→종가 같은 방향, + 당일 만기 0.5σ 외가 옵션(시가 매수→만기)
            if abs(g)>=1.5*sd:
                dirn=np.sign(g); call=dirn>0
                K=o*(1+dirn*0.5*sd); p0=max(bs(o,K,0.27/252,v*1.5,call)*1.15,o*0.0005)
                pay=(max(c-K,0) if call else max(K-c,0))/p0-1 if p0>0 else np.nan
                rows.append({**base,'t':'A_gap_down' if dirn<0 else 'A_gap_up','x':dirn*(c/o-1)/sd,'opt':pay,'up':bool(d.up.iloc[k])})
            # B 전날 큰 움직임(2σ) → 오늘 같은 방향 추격(전날 종가→오늘 종가, σ 단위)
            r1=d.ret.iloc[k-1]; sd1=d.sd.iloc[k-1]
            if not np.isnan(sd1) and abs(r1)>=2*sd1:
                rows.append({**base,'t':'B_chase_after_down' if r1<0 else 'B_chase_after_up','x':np.sign(r1)*(c/d.close.iloc[k-1]-1)/sd,'opt':np.nan,'up':bool(d.up.iloc[k])})
            # C D 반등: 상승 추세 + 3일 하락 ≤ -1.5σ√3 → 다음 날 시가 매수, 5거래일 뒤 종가 (2주 등가 콜)
            if d.up.iloc[k] and k+6<n:
                r3=d.close.iloc[k]/d.close.iloc[k-3]-1
                if r3<=-1.5*sd*sqrt(3):
                    S0=d.open.iloc[k+1]; S1=d.close.iloc[k+6]
                    p0=bs(S0,S0,10/252,v*1.2,True)*1.05; p1=bs(S1,S0,4.75/252,v*1.2,True)*0.95
                    rows.append({**base,'t':'C_D_rebound','x':(S1/S0-1)/sd,'opt':p1/p0-1,'up':True})
            # D 상승 추세 아무 날: 시가 0.5σ 외가 콜 vs 풋(3일 만기) → 종가 매도
            if d.up.iloc[k] and k%3==0:
                for call,t in ((True,'D_call_uptrend'),(False,'D_put_uptrend')):
                    K=o*(1+0.5*sd) if call else o*(1-0.5*sd)
                    p0=bs(o,K,3/252,v*1.2,call)*1.05; p1=bs(c,K,2.75/252,v*1.2,call)*0.95
                    rows.append({**base,'t':t,'x':np.nan,'opt':p1/p0-1,'up':True})
            # E 하루 -2.5σ 급락 다음 1·5일
            if d.ret.iloc[k]<=-2.5*sd and k+5<n:
                rows.append({**base,'t':'E_after_crash_d1','x':(d.close.iloc[k+1]/c-1)/sd,'opt':np.nan,'up':bool(d.up.iloc[k])})
                rows.append({**base,'t':'E_after_crash_d5','x':(d.close.iloc[k+5]/c-1)/sd,'opt':np.nan,'up':bool(d.up.iloc[k])})
            # F 당일 콜+풋 양쪽(0.5σ 외가) 시가 매수 → 만기: '조금만 움직여도' 효과
            if k%2==0:
                Kc=o*(1+0.5*sd); Kp=o*(1-0.5*sd)
                pc=max(bs(o,Kc,0.27/252,v*1.5,True)*1.15,o*0.0005); pp=max(bs(o,Kp,0.27/252,v*1.5,False)*1.15,o*0.0005)
                pay=(max(c-Kc,0)+max(Kp-c,0))/(pc+pp)-1
                rows.append({**base,'t':'F_0dte_both','x':abs(c/o-1)/sd,'opt':pay,'up':bool(d.up.iloc[k])})
df=pd.DataFrame(rows); df.to_pickle('t52.pkl'); print('rows',len(df))
