# 11/25 오후 연구원: 장부 131(감 17 — 추수감사절 전날 수요일 하락 → 금요일 반등?) · 133(나스닥100 200일선 아래 급등 → 20일 안 급등 전 종가 이탈)
# 쓰는 법: python3 t_h131_133.py <자료 폴더>  (SOXX_old.csv·SOXX.csv = Twelve Data 일봉, NASDAQ100.csv·NASDAQSOX.csv = FRED 원본)
import sys, datetime as dt, numpy as np, pandas as pd
from math import log, sqrt, exp, erf
D = sys.argv[1]; rng = np.random.default_rng(1131)
def td(s):
    d = pd.read_csv(f'{D}/{s}.csv', parse_dates=['datetime']).set_index('datetime').sort_index(); return d[~d.index.duplicated()]
def fred(s):
    x = pd.read_csv(f'{D}/{s}.csv', parse_dates=['observation_date']).set_index('observation_date')[s]; return pd.to_numeric(x, errors='coerce').dropna()
def ci(x, n=5000):
    x = np.asarray(x, float); m = rng.choice(x, (n, len(x))).mean(1); return np.percentile(m, [5, 95])
sx = pd.concat([td('SOXX_old'), td('SOXX')]); sx = sx[~sx.index.duplicated()].sort_index()
S = {'SOXX': sx.close, 'NDX': fred('NASDAQ100'), 'SOX': fred('NASDAQSOX')}
def thanksgiving(y):
    d = dt.date(y, 11, 1); d += dt.timedelta((3 - d.weekday()) % 7); return d + dt.timedelta(21)
N_ = lambda x: 0.5 * (1 + erf(x / sqrt(2)))
def bs(S0, K, T, v, r=0.04):
    if T <= 1e-9: return max(S0 - K, 0.0)
    d1 = (log(S0 / K) + (r + v * v / 2) * T) / (v * sqrt(T)); return S0 * N_(d1) - K * exp(-r * T) * N_(d1 - v * sqrt(T))
print('===== 131: 추수감사절 수→금 =====')
for nm, c in S.items():
    r = c.pct_change(); sma = c.rolling(200).mean(); rv = r.rolling(20).std() * sqrt(252); rows = []
    for y in range(1986, 2026):
        tg = pd.Timestamp(thanksgiving(y)); w = tg - pd.Timedelta(days=1); f = tg + pd.Timedelta(days=1)
        if w not in c.index or f not in c.index: continue
        i = c.index.get_loc(w)
        if i < 1: continue
        # 수요일 종가 등가 콜, 금요일 만기, 금요일 종가 무렵 판다: 남은 기간 2/252 → 0 근처(금요일 마감 1시간 전 가정 0.2/252)
        rows.append({'y': y, 'wed': r.iloc[i], 'wf': c.loc[f] / c.loc[w] - 1, 'below200': bool(c.iloc[i] < sma.iloc[i]) if not np.isnan(sma.iloc[i]) else None, 'rv': rv.iloc[i],
                     'fri_gap_check': (f - w).days})
    E = pd.DataFrame(rows)
    if nm == 'SOX':  # FRED 지수 빠진 날·틀린 값(2008-11) 점검
        E = E[E.wf.abs() < 0.3]
    for m in (1.2, 1.5):
        E[f'call{m}'] = [ (bs(1+wf, 1, 0.2/252, rv*m) * (1-0.065)) / (bs(1, 1, 2/252, rv*m) * (1+0.065)) - 1 if not np.isnan(rv) else np.nan for wf, rv in zip(E.wf, E.rv)]
    def show(lab, X):
        if len(X) == 0: print(f'  {lab}: n=0'); return
        lo, hi = ci(X.wf.values) if len(X) > 1 else (np.nan, np.nan)
        print(f'  {lab}: n={len(X)} 수→금 평균 {100*X.wf.mean():+.2f}% 중간 {100*X.wf.median():+.2f}% 오름 {100*(X.wf>0).mean():.0f}% +3%이상 {int((X.wf>=0.03).sum())}번({100*(X.wf>=0.03).mean():.0f}%) 최악 {100*X.wf.min():+.1f}% 범위[{100*lo:+.2f},{100*hi:+.2f}] | 모델 콜(IV×1.2) 평균 {100*X["call1.2"].mean():+.0f}% 중간 {100*X["call1.2"].median():+.0f}% 이김 {100*(X["call1.2"]>0).mean():.0f}% · (IV×1.5) 평균 {100*X["call1.5"].mean():+.0f}%')
    print(nm, f'{int(E.y.min())}~{int(E.y.max())}')
    show('전체', E); show('수요일 하락', E[E.wed < 0]); show('수요일 상승', E[E.wed >= 0]); show('수요일 −1% 이하', E[E.wed <= -0.01]); show('수요일 −2% 이하', E[E.wed <= -0.02])
    show('200일선 아래 & 수요일 하락', E[(E.below200 == True) & (E.wed < 0)]); show('200일선 아래 전체', E[E.below200 == True])
    if nm == 'SOXX': print(E.assign(wed=(100*E.wed).round(2), wf=(100*E.wf).round(2)).drop(columns=['rv','fri_gap_check','call1.5']).round(2).to_string(index=False)); E.to_csv(f'{D}/h131_rows.csv', index=False)
    # 기준선: 아무 수요일 종가 → 이틀 뒤(금요일) 종가
    wd = c[c.index.weekday == 2]; base = (c.shift(-2) / c - 1).reindex(wd.index).dropna(); print(f'  기준선(모든 수→금, 이틀): 평균 {100*base.mean():+.2f}% 오름 {100*(base>0).mean():.0f}% +3%이상 {100*(base>=0.03).mean():.1f}%')
    bw = base[(c.pct_change().reindex(base.index) < 0)]; print(f'  기준선(수요일 하락한 모든 주): 평균 {100*bw.mean():+.2f}% 오름 {100*(bw>0).mean():.0f}% +3%이상 {100*(bw>=0.03).mean():.1f}% n={len(bw)}')

print('\n===== 133: 나스닥100 200일선 아래 급등 → 20일 안 급등 전 종가 이탈 =====')
c = S['NDX']; r = c.pct_change(); sma = c.rolling(200).mean(); N = len(c)
def run(th, win):
    ev = []; last = -99
    for i in range(200, N):
        if r.iloc[i] >= th and i - last > 5:
            last = i
            if c.iloc[i] < sma.iloc[i] and i + win < N: ev.append(i)
    out = []
    for i in ev:
        gb = c.iloc[i + 1] <= c.iloc[i] - 0.5 * (c.iloc[i] - c.iloc[i - 1])
        out.append({'d': c.index[i], 'r': r.iloc[i], 'gb': gb, 'under': bool(c.iloc[i + 1:i + 1 + win].min() < c.iloc[i - 1])})
    return pd.DataFrame(out)
for th, win in ((0.04, 20), (0.03, 20), (0.05, 20), (0.04, 10), (0.04, 40)):
    W = run(th, win); a = W[W.gb]; b = W[~W.gb]
    dd = rng.choice(a.under.values.astype(float), (5000, len(a))).mean(1) - rng.choice(b.under.values.astype(float), (5000, len(b))).mean(1) if len(a) > 1 and len(b) > 1 else np.array([np.nan])
    e1 = W[W.d < '2004-01-01']; e2 = W[W.d >= '2004-01-01']
    print(f'+{int(100*th)}% {win}일: n={len(W)} 이탈 {100*W.under.mean():.0f}% | 반납 n={len(a)} {100*a.under.mean():.0f}% vs 안 함 n={len(b)} {100*b.under.mean():.0f}% 차이 범위[{100*np.nanpercentile(dd,5):+.0f},{100*np.nanpercentile(dd,95):+.0f}]%p | 1986~2003 n={len(e1)} {100*e1.under.mean():.0f}% · 2004~ n={len(e2)} {100*e2.under.mean():.0f}% (2009~ {100*W[W.d>="2009-01-01"].under.mean():.0f}%, n={int((W.d>="2009-01-01").sum())})')
    if (th, win) == (0.04, 20): W.to_csv(f'{D}/h133_rows.csv', index=False); print('  반납 그룹:', [(str(x.d.date()), x.under) for x in a.itertuples()]); print('  2009~ 사건:', [(str(x.d.date()), round(100*x.r,1), x.gb, x.under) for x in W[W.d>='2009-01-01'].itertuples()])
