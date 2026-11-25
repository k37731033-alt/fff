# 11/25 가설 연구원: 장부 124~128번. 자료 = Twelve Data 일봉(분할 조정, ; 구분 CSV) + FRED 원본 CSV
# 쓰는 법: python3 t_h124_128.py <자료 폴더>
import sys, numpy as np, pandas as pd
D = sys.argv[1]; rng = np.random.default_rng(1125)
def ld(s):
    d = pd.read_csv(f'{D}/{s}.csv', parse_dates=['datetime']).set_index('datetime').sort_index()
    return d[~d.index.duplicated()]
def ci(x, n=5000):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    if len(x) < 2: return (np.nan, np.nan)
    m = rng.choice(x, (n, len(x))).mean(1); return tuple(np.percentile(m, [5, 95]))
def dci(a, b, n=5000):
    a = np.asarray(a, float); b = np.asarray(b, float); a = a[~np.isnan(a)]; b = b[~np.isnan(b)]
    bb = b if len(b) < 20000 else rng.choice(b, 20000, replace=False)
    m = rng.choice(a, (n, len(a))).mean(1) - np.array([rng.choice(bb, len(bb)).mean() for _ in range(300)]).mean()
    # 기준선 표본 오차는 사건 표본보다 훨씬 작아 평균만 반영
    return tuple(np.percentile(m, [5, 95]))
def desc(name, x, base=None):
    x = pd.Series(x).dropna(); n = len(x)
    if n == 0: print(name, 'n=0'); return
    lo, hi = ci(x.values); k = max(1, int(round(n * 0.3)))
    s = f'{name}: n={n} 평균 {100*x.mean():+.2f}% 중간 {100*x.median():+.2f}% 오름 {100*(x>0).mean():.0f}% 최악 {100*x.min():+.1f}% 범위[{100*lo:+.2f},{100*hi:+.2f}] 최근30%({k}) {100*x.iloc[-k:].mean():+.2f}% 좋은2빼면 {100*x.sort_values().iloc[:-2].mean():+.2f}%'
    if base is not None:
        b = pd.Series(base).dropna(); l2, h2 = dci(x.values, b.values)
        s += f' | 기준 {100*b.mean():+.2f}%(오름 {100*(b>0).mean():.0f}%) 차이 {100*(x.mean()-b.mean()):+.2f}%p 범위[{100*l2:+.2f},{100*h2:+.2f}]'
    print(s)
def dedupe(idx_pos, gap):
    out = []; last = -10**9
    for i in idx_pos:
        if i - last > gap: out.append(i); last = i
    return out

sx = pd.concat([ld('SOXX_old'), ld('SOXX')]); sx = sx[~sx.index.duplicated()].sort_index()
sp = pd.concat([ld('SPY_old'), ld('SPY')]); sp = sp[~sp.index.duplicated()].sort_index()
qq = ld('QQQ')
c = sx.close; r = c.pct_change(); sma200 = c.rolling(200).mean()
print('SOXX', c.index[0].date(), c.index[-1].date(), len(c), '| 11/24 종가', c.iloc[-1], '수익', round(100*r.iloc[-1], 2), '| SPY 11/24', round(100*sp.close.pct_change().iloc[-1], 2), 'QQQ', round(100*qq.close.pct_change().iloc[-1], 2))

print('\n===== 124: 한 종목만 급락한 날 뒤 =====')
T = ['AMAT','AMD','AVGO','INTC','KLAC','LRCX','META','MRVL','MU','NVDA','ON','QCOM','TSLA','TSM']
C = pd.DataFrame({t: ld(t).close for t in T}); C = C[C.index >= '2007-01-11']
sxc = c.reindex(C.index); qc = qq.close.reindex(C.index)
R = C.pct_change(); rs = sxc.pct_change(); rq = qc.pct_change()
rows = []; base = {1: [], 5: [], 20: []}
for t in T:
    rt = R[t]; avg = rt.abs().rolling(20).mean().shift(1)
    for h in base: base[h].append((C[t].shift(-h) / C[t] - 1).dropna())
    cond = (rt <= -3 * avg) & ((rt - rs) <= -0.03) & (rq >= -0.01)
    for d in rt.index[cond.fillna(False)]:
        i = C.index.get_loc(d)
        o = {'t': t, 'd': d, 'r0': rt.loc[d]}
        for h in (1, 5, 20): o[f'f{h}'] = C[t].iloc[i + h] / C[t].iloc[i] - 1 if i + h < len(C) else np.nan
        rows.append(o)
E = pd.DataFrame(rows).sort_values('d').reset_index(drop=True)
B = {h: pd.concat(base[h]) for h in base}
print('사건', len(E), '날짜 수', E.d.nunique(), '종목 수', E.t.nunique(), '그날 평균 %.1f%%' % (100 * E.r0.mean()))
print(E.t.value_counts().to_dict())
for h in (1, 5, 20): desc(f'전체 뒤 {h}일', E[f'f{h}'], B[h])
for lab, m in (('2017~', E.d >= '2017-01-01'), ('2025~', E.d >= '2025-01-01'), ('그날 −8% 이하', E.r0 <= -0.08), ('그날 −8%보다 얕음', E.r0 > -0.08)):
    desc(f'{lab} 뒤 5일', E[m].f5, B[5]); desc(f'{lab} 뒤 20일', E[m].f20, B[20])
E.to_csv(f'{D}/h124_rows.csv', index=False)

print('\n===== 125: 급등 뒤 지정가 =====')
o_, h_, l_ = sx.open, sx.high, sx.low; N = len(c)
ev = dedupe([i for i in range(1, N) if r.iloc[i] >= 0.06], 5)
print('SOXX +6% 이상(5일 안 중복 제외):', len(ev), '번', [str(c.index[i].date()) for i in ev][-12:])
def limit_test(ev, x, hold=60):
    out = []
    for i in ev:
        P = c.iloc[i]; L = P * (1 - x); fill = None; day = None
        for j in range(i + 1, min(i + 21, N)):
            if o_.iloc[j] <= L: fill = o_.iloc[j]; day = j - i; break
            if l_.iloc[j] <= L: fill = L; day = j - i; break
        filled = fill is not None
        if not filled:
            if i + 21 >= N: continue
            fill = c.iloc[i + 21]
        if i + hold >= N: continue
        out.append({'d': c.index[i], 'filled': filled, 'day': day, 'fill_vs_P': fill / P - 1, 'lim': c.iloc[i + hold] / fill - 1,
                    'next': c.iloc[i + hold] / c.iloc[i + 1] - 1, 'same': c.iloc[i + hold] / P - 1, 'below200': c.iloc[i] < sma200.iloc[i],
                    'min20': l_.iloc[i + 1:i + 21].min() / P - 1})
    return pd.DataFrame(out)
for x in (0.03, 0.05, 0.07):
    Q = limit_test(ev, x)
    d = Q.lim - Q.next; lo, hi = ci(d.values)
    print(f'지정가 −{int(100*x)}%: n={len(Q)} 체결 {100*Q.filled.mean():.0f}% 체결까지 중간 {Q.day.median()}일 | 미체결 {int((~Q.filled).sum())}번의 21일째 값 P 대비 {100*Q[~Q.filled].fill_vs_P.mean():+.1f}% | 60일 시점: 지정가 {100*Q.lim.mean():+.2f}%(중간 {100*Q.lim.median():+.2f}%) 다음날종가 {100*Q.next.mean():+.2f}%(중간 {100*Q.next.median():+.2f}%) 급등일종가 {100*Q.same.mean():+.2f}% | 차이(지정가−다음날) {100*d.mean():+.2f}%p 중간 {100*d.median():+.2f}%p 이긴비율 {100*(d>0).mean():.0f}% 범위[{100*lo:+.2f},{100*hi:+.2f}]')
    for lab, m in (('200일선 아래', Q.below200), ('2022~', Q.d >= '2022-01-01')):
        q = Q[m]; d2 = q.lim - q.next; lo, hi = ci(d2.values)
        print(f'   {lab}: n={len(q)} 체결 {100*q.filled.mean():.0f}% 차이 {100*d2.mean():+.2f}%p 범위[{100*lo:+.2f},{100*hi:+.2f}] 지정가 {100*q.lim.mean():+.2f}% 다음날 {100*q.next.mean():+.2f}%')
    if x == 0.05: Q.to_csv(f'{D}/h125_rows.csv', index=False); k = max(1, int(round(len(Q) * .3))); print('   최근30%% 차이 %+.2f%%p | 좋은 2개 빼면 %+.2f%%p' % (100 * d.iloc[-k:].mean(), 100 * d.sort_values().iloc[:-2].mean()))
Q = limit_test(ev, 0.05); print('20일 안 장중 최저(P 대비): 평균 %.1f%% 중간 %.1f%%' % (100 * Q.min20.mean(), 100 * Q.min20.median()))

print('\n===== 126: 하루짜리 랠리 → 급등 전 종가 이탈 =====')
def retest(th, win, below=True):
    out = []
    for i in dedupe([i for i in range(200, N) if r.iloc[i] >= th], 5):
        if below and not (c.iloc[i] < sma200.iloc[i]): continue
        if i + 2 >= N: continue
        gain = c.iloc[i] - c.iloc[i - 1]; gb = c.iloc[i + 1] <= c.iloc[i] - 0.5 * gain
        full = i + win < N
        seg = c.iloc[i + 1:i + 1 + win]
        out.append({'d': c.index[i], 'r': r.iloc[i], 'next': r.iloc[i + 1], 'gb': gb, 'full': full, 'under': bool(seg.min() < c.iloc[i - 1]),
                    'f20': c.iloc[i + 1 + 20] / c.iloc[i + 1] - 1 if i + 21 < N else np.nan, 'min': seg.min() / c.iloc[i - 1] - 1})
    return pd.DataFrame(out)
for th, win, below in ((0.06, 20, True), (0.05, 20, True), (0.08, 20, True), (0.06, 10, True), (0.06, 40, True), (0.06, 20, False), (0.05, 20, False)):
    W = retest(th, win, below); Wf = W[W.full]
    a = Wf[Wf.gb]; b = Wf[~Wf.gb]
    # 비율 차이 부트스트랩
    if len(a) > 1 and len(b) > 1:
        dd = rng.choice(a.under.values.astype(float), (5000, len(a))).mean(1) - rng.choice(b.under.values.astype(float), (5000, len(b))).mean(1); lo, hi = np.percentile(dd, [5, 95])
    else: lo = hi = np.nan
    print(f'+{int(100*th)}% {"200일선 아래" if below else "전체"} {win}일: 전체 n={len(Wf)} 이탈 {100*Wf.under.mean():.0f}% | 절반 넘게 반납 n={len(a)} 이탈 {100*a.under.mean() if len(a) else float("nan"):.0f}% | 반납 안 함 n={len(b)} 이탈 {100*b.under.mean() if len(b) else float("nan"):.0f}% | 차이 범위[{100*lo:+.0f},{100*hi:+.0f}]%p')
    if (th, win, below) == (0.06, 20, True):
        print(W.assign(d=W.d.dt.date).round(3).to_string(index=False)); W.to_csv(f'{D}/h126_rows.csv', index=False)
        desc('   반납 그룹: 반납한 날 종가 → 20일', a.f20, (c.shift(-20) / c - 1)[c < sma200]); desc('   반납 안 한 그룹: 다음 날 종가 → 20일', b.f20, (c.shift(-20) / c - 1)[c < sma200])

print('\n===== 127: 업종만 빠진 날 vs 시장 전체 =====')
rsp = sp.close.pct_change().reindex(c.index)
f = {h: c.shift(-h) / c - 1 for h in (1, 5, 20)}
def grp(th, lo_spy=None, hi_spy=None, start=None, gap=5):
    m = (r <= th)
    if lo_spy is not None: m &= (rsp >= lo_spy)
    if hi_spy is not None: m &= (rsp <= hi_spy)
    if start: m &= (c.index >= start)
    pos = dedupe([i for i in range(N) if bool(m.iloc[i])], gap); return c.index[pos]
for th, a_, lab in ((-0.04, -0.01, '주 판정'), (-0.03, -0.01, ''), (-0.05, -0.01, ''), (-0.04, -0.005, '')):
    A = grp(th, lo_spy=a_); Bm = grp(th, hi_spy=-0.02)
    print(f'-- SOXX ≤ {100*th:.0f}% / 업종만 = SPY ≥ {100*a_:.1f}% {lab}')
    for h in (1, 5, 20):
        desc(f'  업종만 뒤 {h}일', f[h].reindex(A), f[h]); 
    desc('  시장 전체(SPY ≤ −2%) 뒤 5일', f[5].reindex(Bm), f[5]); desc('  시장 전체 뒤 20일', f[20].reindex(Bm), f[20])
    xa = f[5].reindex(A).dropna().values; xb = f[5].reindex(Bm).dropna().values
    dd = rng.choice(xa, (5000, len(xa))).mean(1) - rng.choice(xb, (5000, len(xb))).mean(1); print('  업종만 − 시장 전체(5일): %+.2f%%p 범위[%+.2f,%+.2f]' % (100 * (xa.mean() - xb.mean()), *(100 * np.percentile(dd, [5, 95]))))
A = grp(-0.04, lo_spy=-0.01, start='2020-01-01'); desc('2020~ 업종만 뒤 5일', f[5].reindex(A), f[5][f[5].index >= '2020-01-01']); desc('2020~ 업종만 뒤 20일', f[20].reindex(A), f[20][f[20].index >= '2020-01-01'])
A = grp(-0.04, lo_spy=-0.01); print('업종만 사건 날짜(최근 15):', [str(d.date()) for d in A[-15:]])
A6 = grp(-0.06, lo_spy=-0.01); desc('SOXX ≤ −6% & SPY ≥ −1% 뒤 5일', f[5].reindex(A6), f[5]); print([str(d.date()) for d in A6])
pd.DataFrame({'d': A, 'f1': f[1].reindex(A).values, 'f5': f[5].reindex(A).values, 'f20': f[20].reindex(A).values}).to_csv(f'{D}/h127_rows.csv', index=False)

print('\n===== 128: 11월이 크게 빠진 해의 12월 =====')
for sid in ('NASDAQCOM', 'NASDAQSOX'):
    x = pd.read_csv(f'{D}/{sid}.csv', parse_dates=['observation_date']).set_index('observation_date')[sid]; x = pd.to_numeric(x, errors='coerce').dropna()
    me = x.groupby([x.index.year, x.index.month]).last(); mr = me.pct_change()
    yrs = sorted(set(y for y, m in mr.index if m == 12 and (y, 11) in mr.index and y < 2026))
    nov = pd.Series({y: mr[(y, 11)] for y in yrs}); dec = pd.Series({y: mr[(y, 12)] for y in yrs})
    jan = pd.Series({y: (me[(y + 1, 1)] / me[(y, 11)] - 1) if (y + 1, 1) in me.index else np.nan for y in yrs})
    print(sid, '해 수', len(yrs), '| 2026-11 지금까지 %.1f%%' % (100 * (x.iloc[-1] / me[(2026, 10)] - 1)))
    for th in (-0.05, -0.03):
        m = nov <= th; desc(f'  11월 ≤ {100*th:.0f}% 해의 12월', dec[m], dec); print('   ', {y: (round(100 * nov[y], 1), round(100 * dec[y], 1)) for y in nov.index[m]})
        desc(f'  11월 ≤ {100*th:.0f}% 해의 12월+1월', jan[m], jan)
