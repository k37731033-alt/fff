import pandas as pd,numpy as np
s=pd.read_csv('../data/daily/SOXX.csv',parse_dates=['datetime']).set_index('datetime')
r=np.log(s.close).diff()
v20=r.rolling(20).std()*np.sqrt(252)
med=v20.rolling(252).median()
s['v20']=v20; s['ratio']=v20/med
s['sma50']=s.close.rolling(50).mean(); s['sma200']=s.close.rolling(200).mean()
s['pct']=v20.expanding(252).rank(pct=True)
print(s[['close','v20','ratio','pct','sma50','sma200']].tail(8).round(3))
H=(s.ratio>=1.3)
print('volatile-day share',H.mean().round(3))
# list volatile stretches
g=(H!=H.shift()).cumsum()
runs=s[H].groupby(g[H]).apply(lambda x:(x.index[0].date(),x.index[-1].date(),len(x),round(x.v20.max(),2)))
runs=[x for x in runs if x[2]>=15]
for x in runs: print(x)
s.to_csv('../data/soxx_regime.csv')
