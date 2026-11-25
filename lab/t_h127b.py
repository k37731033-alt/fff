# 11/25 장부 127번 보강: '업종만 빠진 날' 뒤 5일 — SOXL·USD 주가와 모델 등가 콜(비용 뒤). 쓰는 법: python3 t_h127b.py <자료 폴더>
import sys, numpy as np, pandas as pd
from math import log, sqrt, exp, erf
D = sys.argv[1]; rng = np.random.default_rng(7)
def ld(s):
    d = pd.read_csv(f'{D}/{s}.csv', parse_dates=['datetime']).set_index('datetime').sort_index(); return d[~d.index.duplicated()]
N_ = lambda x: 0.5 * (1 + erf(x / sqrt(2)))
def bs(S, K, T, v, r=0.04):
    if T <= 0: return max(S - K, 0)
    d1 = (log(S / K) + (r + v * v / 2) * T) / (v * sqrt(T)); return S * N_(d1) - K * exp(-r * T) * N_(d1 - v * sqrt(T))
sx = pd.concat([ld('SOXX_old'), ld('SOXX')]); sx = sx[~sx.index.duplicated()].sort_index(); sp = pd.concat([ld('SPY_old'), ld('SPY')]); sp = sp[~sp.index.duplicated()].sort_index()
c = sx.close; r = c.pct_change(); rsp = sp.close.pct_change().reindex(c.index); rv = r.rolling(20).std() * sqrt(252)
def ev(mask):
    out = []; last = -99
    for i in np.where(mask.values)[0]:
        if i - last > 5: out.append(i); last = i
    return out
def opt(idx, hold=5, exp_days=9, mult=1.2, cost=0.08):
    res = []
    for i in idx:
        if i + hold >= len(c) or np.isnan(rv.iloc[i]): continue
        S0 = c.iloc[i]; v = rv.iloc[i] * mult; p0 = bs(S0, S0, exp_days / 252, v); v1 = rv.iloc[i + hold] * mult
        p1 = bs(c.iloc[i + hold], S0, (exp_days - hold) / 252, v1)
        fee = 2 * 1.99 / (p0 * 100) if S0 > 20 else 0  # 옛 가격은 분할 조정으로 작아 수수료 비율이 왜곡됨 → 20달러 위에서만
        res.append(p1 * (1 - cost / 2) / (p0 * (1 + cost / 2)) - 1 - fee)
    return pd.Series(res)
def show(n, x):
    x = x.dropna(); m = rng.choice(x.values, (5000, len(x))).mean(1); lo, hi = np.percentile(m, [5, 95]); k = max(1, round(len(x) * .3))
    print(f'{n}: n={len(x)} 평균 {100*x.mean():+.1f}% 중간 {100*x.median():+.1f}% 이김 {100*(x>0).mean():.0f}% 범위[{100*lo:+.1f},{100*hi:+.1f}] 최근30% {100*x.iloc[-k:].mean():+.1f}% 좋은2빼면 {100*x.sort_values().iloc[:-2].mean():+.1f}%')
A = ev((r <= -0.04) & (rsp >= -0.01)); B = ev((r <= -0.04) & (rsp <= -0.02)); R = list(range(250, len(c) - 6, 5))
for m in (1.2, 1.5):
    print(f'-- 모델 등가 콜(만기 9거래일, 5일 뒤 팜, IV = 20일 변동성 × {m}, 왕복 8% + 수수료)')
    show('  업종만 빠진 날', opt(A, mult=m)); show('  시장 전체 급락 날', opt(B, mult=m)); show('  아무 날(5일마다)', opt(R, mult=m))
for s in ('SOXL', 'USD'):
    x = ld(s).close; f5 = x.shift(-5) / x - 1; d = [c.index[i] for i in A if c.index[i] in x.index]
    show(f'{s} 주가 5일(업종만 빠진 날)', f5.reindex(d)); print('   아무 5일 %+.2f%%' % (100 * f5.mean()))
f5 = c.shift(-5) / c - 1
for a, b in (('2001', '2009'), ('2010', '2019'), ('2020', '2026')):
    d = [c.index[i] for i in A if a <= str(c.index[i].year) <= b]; x = f5.reindex(d).dropna(); print(a, b, 'n', len(x), '5일 %+.2f%%' % (100 * x.mean()), '오름 %.0f%%' % (100 * (x > 0).mean()))
x = f5.reindex([c.index[i] for i in A]).dropna(); print('t =', round((x.mean() - f5.mean()) / (x.std() / sqrt(len(x))), 2), '| 2026년 사건', sum(1 for i in A if c.index[i].year == 2026), '번, 그 5일 평균 %+.2f%%' % (100 * f5.reindex([c.index[i] for i in A if c.index[i].year == 2026]).mean()))
# 그날 낙폭이 더 큰 쪽(오늘 = −8.3%)
for th in (-0.05, -0.06): 
    d = [c.index[i] for i in ev((r <= th) & (rsp >= -0.01))]; print(th, [(str(t.date()), round(100 * r[t], 1), None if np.isnan(f5.get(t, np.nan)) else round(100 * f5[t], 1)) for t in d])
