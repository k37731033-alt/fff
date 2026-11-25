# 11/25 저녁 채팅(사용자 "요즘 장 흐름·심리로 금요일 만기?") 숫자 — 장부 136(2026년 큰 하락 날 다음 날)·137(재난 아닌 '실적 좋은데 빠진' 구간 낙폭)
# 쓰는 법: python3 t_h136_137.py <자료 폴더>  (SOXX_old.csv·SOXX.csv·NVDA.csv = Twelve Data 일봉)
import sys, pandas as pd, numpy as np
from math import log, sqrt, exp, erf
D = sys.argv[1]
c = pd.concat([pd.read_csv(f'{D}/SOXX_old.csv'), pd.read_csv(f'{D}/SOXX.csv')]).drop_duplicates('datetime')
c['datetime'] = pd.to_datetime(c.datetime); c = c.set_index('datetime').close.sort_index()
nv = pd.read_csv(f'{D}/NVDA.csv', parse_dates=['datetime']).set_index('datetime').close
r = c.pct_change(); rv = r.rolling(20).std() * sqrt(252); f1 = c.shift(-1) / c - 1
N = lambda x: 0.5 * (1 + erf(x / sqrt(2)))
def bs(S, K, T, v):
    if T <= 0: return max(S - K, 0)
    d1 = (log(S / K) + (0.04 + v * v / 2) * T) / (v * sqrt(T)); return S * N(d1) - K * exp(-0.04 * T) * N(d1 - v * sqrt(T))
print('== 136: 큰 하락 날 → 다음 날 (SOXX) ==')
for lab, start in (('2026년', '2026-01-01'), ('2025~', '2025-01-01'), ('2020~', '2020-01-01')):
    for th in (-0.03, -0.05):
        m = (r <= th) & (c.index >= start) & f1.notna(); x = f1[m]
        cl = pd.Series([(bs(1 + a, 1, 0.2 / 252, v * 1.3) * (1 - .065)) / (bs(1, 1, 2 / 252, v * 1.3) * (1 + .065)) - 1 for a, v in zip(x, rv[m])])
        print(f'{lab} ≤{100*th:.0f}%: {len(x)}번 다음 날 평균 {100*x.mean():+.2f}% 중간 {100*x.median():+.2f}% 오름 {100*(x>0).mean():.0f}% +2.2%↑ {int((x>=.022).sum())}번 +3%↑ {int((x>=.03).sum())}번 | 이틀짜리 등가 콜(모델, IV=20일 변동성×1.3, 왕복 13%) 평균 {100*cl.mean():+.0f}% 중간 {100*cl.median():+.0f}% 이김 {100*(cl>0).mean():.0f}% 2배↑ {int((cl>=1).sum())}번')
print('2026 ≤−5% 날:', [(str(d.date()), round(100 * r[d], 1), round(100 * f1[d], 1)) for d in r[(r <= -0.05) & (c.index >= '2026-01-01') & f1.notna()].index])
print('지금 SOXX 20일 변동성(연):', round(100 * rv.iloc[-1]))
print('\n== 137: 재난(전쟁·전염병) 아닌 하락 구간 낙폭 ==')
for a, b, why in (('2018-03-01', '2018-12-31', '무역전쟁·금리'), ('2021-11-01', '2022-10-31', '금리 인상'), ('2024-06-15', '2024-08-31', '엔 캐리 청산'), ('2025-01-01', '2025-04-30', '관세'), ('2026-06-01', '2026-11-24', '지금')):
    x = c[a:b]; hi = x.idxmax(); lo = x[hi:].idxmin(); y = nv[a:b]; hy = y.idxmax(); ly = y[hy:].idxmin()
    after = c[lo:].iloc[:121]; a120 = after.iloc[-1] / after.iloc[0] - 1 if len(after) > 120 else np.nan
    print(f'{a[:7]} {why}: SOXX {hi.date()}→{lo.date()} {100*(x[lo]/x[hi]-1):.0f}% · NVDA {hy.date()}→{ly.date()} {100*(y[ly]/y[hy]-1):.0f}% · SOXX 저점 뒤 120거래일 {100*a120:+.0f}%')
