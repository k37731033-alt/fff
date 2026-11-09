# 지금(11/9 장중) 52종목: 이틀 등락(σ), 추세, 풋 모델값 — q1109.csv 필요
import pandas as pd,numpy as np,sys
from math import sqrt
from tests import bs
SP='/tmp/claude-0/-home-claude/c5d8715e-910b-5c3f-9687-e6b60606200c/scratchpad/'
q=pd.read_csv('../data/quotes_2026-11-09_1320ET.csv').drop_duplicates('s',keep='last').set_index('s')
fx=float(sys.argv[1]) if len(sys.argv)>1 else np.nan
c8=pd.read_csv(SP+'cpi8.csv').set_index('s')
rows=[]
for s,x in q.iterrows():
    d=pd.read_csv(f'../data/daily/{s}.csv',parse_dates=['datetime']).set_index('datetime')
    c5=d.close.loc['2026-11-05']; c6=d.close.loc['2026-11-06']
    sig=np.log(d.close.loc[:'2026-11-05']).diff().tail(20).std()
    r2=x['last']/c5-1; z2=r2/(sig*sqrt(2))
    s50=d.close.tail(50).mean(); s200=d.close.tail(200).mean()
    v=np.log(d.close).diff().tail(20).std()*sqrt(252)
    T=4.1/252   # 11/13(금) 만기까지 약 4거래일
    S=x['last']
    atm=bs(S,round(S),T,v*1.2,False); o3=bs(S,S*0.97,T,v*1.2,False)
    # 다음 날(CPI) 종가에 -1σ / 0 / +1σ 일 때 등가 풋 값 변화 (IV 그대로, 호가 손해 ±8%)
    sd=sig
    def pnl(m): return bs(S*(1+m),round(S),3.1/252,v*1.2,False)*0.92/(atm*1.08)-1
    rows.append(dict(s=s,today=100*(S/x.prev-1),d2=100*r2,z2=z2,trend='상승' if s50>s200 else '하락',
        rv20=100*v,atm_put=atm,atm_pct=100*atm/S,o3_put=o3,
        krw_atm=atm*100*fx,krw_o3=o3*100*fx,
        dn1=100*pnl(-sd),flat=100*pnl(0),up1=100*pnl(sd),
        cpi8=c8.loc[s,'cpi8'] if s in c8.index else np.nan,
        strad_1d_model=100*(bs(S,round(S),1/252,v*1.2,True)+bs(S,round(S),1/252,v*1.2,False))/S))
o=pd.DataFrame(rows).set_index('s').sort_values('z2',ascending=False).round(2)
pd.set_option('display.width',250)
print(o.to_string())
o.to_csv(SP+'now_put.csv')
