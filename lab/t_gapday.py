"""큰 갭 상승 날: 시가 뒤 더 가나 / 파는 법 비교 (52종목 일봉, 주가 기준 = 깊은 내가격 콜과 비슷)
(a) 시가 전량 매도 = 0  (b) 종가까지 = oc  (c) 절반 시가 + 절반 '시가+3% 지정가, 안 닿으면 종가'
"""
import pandas as pd, numpy as np, glob, os
reg = pd.read_csv('data/soxx_regime.csv') if os.path.exists('data/soxx_regime.csv') else None
rows=[]
for f in glob.glob('data/daily/*.csv'):
    t=os.path.basename(f)[:-4]
    d=pd.read_csv(f).sort_values('datetime').reset_index(drop=True)
    d['pc']=d.close.shift(1); d['gap']=d.open/d.pc-1; d['oc']=d.close/d.open-1
    d['oh']=d.high/d.open-1; d['ol']=d.low/d.open-1
    d['r3']=d.pc/d.close.shift(4)-1
    d['dd']=d.pc/d.close.rolling(20).max().shift(1)-1
    d['n1']=d.close.shift(-1)/d.close-1
    d['t']=t; rows.append(d[d.datetime>='2024-01-01'])
a=pd.concat(rows)
print('regime cols', None if reg is None else list(reg.columns)[:6])
def show(name,x):
    if len(x)<8: print(f'{name}: n={len(x)} (표본 적음)'); return
    c=0.5*np.where(x.oh>=0.03,0.03,x.oc)
    c5=0.5*np.where(x.oh>=0.05,0.05,x.oc)
    print(f'{name}: n={len(x)} | 종가>시가 {(x.oc>0).mean():.0%} | 시가→종가 평균 {x.oc.mean():+.2%} 중간 {x.oc.median():+.2%} | 장중 +3% {(x.oh>=.03).mean():.0%} +5% {(x.oh>=.05).mean():.0%} | 장중 −3% {(x.ol<=-.03).mean():.0%} | 절반+3%지정가 {c.mean():+.2%} 절반+5% {c5.mean():+.2%} | 다음날 {x.n1.mean():+.2%}')
for per in ['2024-01-01','2026-05-01']:
    p=a[a.datetime>=per]; print('\n== 기간',per,'~')
    for lo,hi in [(0.04,0.07),(0.07,0.12),(0.12,9)]:
        g=p[(p.gap>=lo)&(p.gap<hi)]
        show(f'갭 +{lo:.0%}~{hi:.0%} 전체',g)
        show('   급락 상태(20일 고점 −15%↓)',g[g.dd<=-0.15])
        show('   직전 3일 +8%↑(놓친 랠리)',g[g.r3>=0.08])
    show('참고: 아무 날',p)
