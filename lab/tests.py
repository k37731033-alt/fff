import pandas as pd,numpy as np
from math import log,sqrt,exp,erf
def N(x): return 0.5*(1+erf(x/sqrt(2)))
def bs(S,K,T,v,call):
    if T<=0: return max(S-K,0) if call else max(K-S,0)
    d1=(log(S/K)+0.5*v*v*T)/(v*sqrt(T)); d2=d1-v*sqrt(T)
    return S*N(d1)-K*N(d2) if call else K*N(-d2)-S*N(-d1)
R=pd.read_csv('../data/soxx_regime.csv',parse_dates=['datetime']).set_index('datetime')
reg=pd.DataFrame(index=R.index)
reg['ratio']=R.ratio.shift(1); reg['v20']=R.v20.shift(1)   # 전날까지 정보만
reg['up']=(R.sma50>R.sma200).shift(1)
def lab(i):
    x=reg.loc[i]
    if pd.isna(x.ratio): return None
    if x.v20>=0.5: return 'HH'
    return 'H' if x.ratio>=1.3 else 'N'
def load(s):
    d=pd.read_csv(f'../data/daily/{s}.csv',parse_dates=['datetime']).set_index('datetime')
    d['pc']=d.close.shift(1); d['v']=np.log(d.close).diff().rolling(20).std().shift(1)*sqrt(252)
    d['sma50']=d.close.rolling(50).mean(); d['sma200']=d.close.rolling(200).mean()
    return d
X={s:load(s) for s in ['SOXX','SOXL','NVDA','MU','QQQ']}
sx=X['SOXX']; sx['gap']=sx.open/sx.pc-1; sx['ret']=sx.close/sx.pc-1
def summ(rows,cols):
    df=pd.DataFrame(rows)
    out=[]
    for k,g in df.groupby('reg'):
        o={'reg':k,'n':len(g)}
        for c in cols:
            o[c+'_avg']=round(g[c].mean()*100,1); o[c+'_med']=round(g[c].median()*100,1); o[c+'_win']=round((g[c]>0).mean()*100)
        out.append(o)
    return pd.DataFrame(out).set_index('reg').reindex(['N','H','HH'])
def opt_trade(d,i,direction,otm,days,ivmult=1.2,exit_close_days=0):
    # 시가에 외가 옵션 매수 → 같은 날 종가(또는 n일 뒤 종가) 매도. 호가 손해 살 때 +5%, 팔 때 -5%
    S0=d.open.loc[i]; v=d.v.loc[i]*ivmult
    if np.isnan(v): return None
    call=direction>0
    K=S0*(1+otm) if call else S0*(1-otm)
    p0=bs(S0,K,days/252,v,call)*1.05
    if p0<=0: return None
    idx=d.index.get_loc(i); j=idx+exit_close_days
    if j>=len(d): return None
    S1=d.close.iloc[j]; p1=bs(S1,K,max(days-exit_close_days-0.25,0)/252,v,call)*0.95
    # 장중 최고 유리한 가격에서의 값(지정가 +100% 닿았나)
    Sx=d.high.loc[i] if call else d.low.loc[i]
    px=bs(Sx,K,(days-0.1)/252,v,call)*0.95
    tp=(1 if px>=2*p0 else 0)
    # 절반 +100%에 팔고 절반 종가: 
    mix=0.5*(1.0)+0.5*(p1/p0-1) if tp else p1/p0-1
    return p1/p0-1, mix, tp
