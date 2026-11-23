# 11/23 가설 연구원 — 장부 112~116번 (사전 등록: 56-4 문서 14:40 KST)
# 자료: Twelve Data 일봉(분할 조정, px/*.csv: date,open,high,low,close,volume) · FRED NASDAQCOM/NASDAQ100/SP500 · TWSE 가권
# 실행: python3 t_h112_116.py <px 폴더> [taiex csv]
import sys, pandas as pd, numpy as np
PX = sys.argv[1]; TW = sys.argv[2] if len(sys.argv) > 2 else None
rng = np.random.default_rng(1123)
def ci(x, n=5000):
    x = np.asarray(x, float)
    if len(x) < 3: return (np.nan, np.nan)
    m = rng.choice(x, (n, len(x))).mean(1); return np.percentile(m, [5, 95])
def dci(x, y, n=5000):
    x = np.asarray(x, float); y = np.asarray(y, float)
    d = rng.choice(x, (n, len(x))).mean(1) - rng.choice(y, (n, min(len(y), 3000))).mean(1); return np.percentile(d, [5, 95])
def line(name, g, base, col='oc'):
    x = g[col].dropna(); b = base[col].dropna()
    if len(x) < 3: print(f'  {name}: n={len(x)}'); return
    lo, hi = ci(x); dl, dh = dci(x, b)
    k = max(1, int(round(len(x) * .3))); rec = x.iloc[-k:].mean()
    xs = np.sort(x.values); ex2hi = xs[:-2].mean() if len(xs) > 4 else np.nan; ex2lo = xs[2:].mean() if len(xs) > 4 else np.nan
    print(f'  {name:34s} n={len(x):4d} 평균 {x.mean():+.2%} 중간 {x.median():+.2%} 오름 {(x>0).mean():.0%} 최악 {x.min():+.1%} | 90% {lo:+.2%}~{hi:+.2%} | 아무 날 {b.mean():+.2%} 차이 {x.mean()-b.mean():+.2%} ({dl:+.2%}~{dh:+.2%}) | 최근30% {rec:+.2%} | 위2개 뺌 {ex2hi:+.2%} 아래2개 뺌 {ex2lo:+.2%}')
def load(tk):
    d = pd.read_csv(f'{PX}/{tk}.csv', parse_dates=['date']).set_index('date').sort_index()
    d['pc'] = d.close.shift(1); d['gap'] = d.open / d.pc - 1; d['oc'] = d.close / d.open - 1
    d['prev'] = d.pc / d.close.shift(2) - 1
    d['ma50'] = d.close.rolling(50).mean().shift(1); d['ma200'] = d.close.rolling(200).mean().shift(1)
    d['o5'] = d.close.shift(-4) / d.open - 1          # 시가 → 5거래일째 종가
    d['c1'] = d.close / d.pc - 1
    return d.dropna(subset=['ma50'])
D = {tk: load(tk) for tk in ['SOXX', 'QQQ', 'NVDA', 'MU', 'AMD']}

print('■ 112 — 50일선 아래 + 갭 상승 → 시가→종가 (95번 긴 기간)')
for tk, d in D.items():
    print(f' [{tk}] {d.index[0].date()}~{d.index[-1].date()} {len(d)}일')
    below = d.pc < d.ma50
    line('갭≥+1%·50일선 아래(주 판정)', d[below & (d.gap >= .01)], d)
    if tk == 'SOXX':
        line('갭≥+1%·50일선 위', d[~below & (d.gap >= .01)], d)
        line('갭≥+2%·50일선 아래', d[below & (d.gap >= .02)], d)
        line('갭≥+1%·200일선 아래', d[(d.pc < d.ma200) & (d.gap >= .01)], d)
        for a, b in (('2001', '2009'), ('2010', '2019'), ('2020', '2026')):
            s = d[a:b]; line(f'갭≥+1%·50일선 아래 {a}~{b}', s[(s.pc < s.ma50) & (s.gap >= .01)], s)
        s = d['2024-11-20':]; line('갭≥+1%·아래 (95번 구간 2024-11~)', s[(s.pc < s.ma50) & (s.gap >= .01)], s)

print('\n■ 113 — 전날 급락 뒤 갭 상승 → 시가→종가')
d = D['SOXX']
line('SOXX 전날≤−5%·갭≥+1%(주 판정)', d[(d.prev <= -.05) & (d.gap >= .01)], d)
line('SOXX 전날≤−4%·갭≥+1%', d[(d.prev <= -.04) & (d.gap >= .01)], d)
line('SOXX 전날≤−7%·갭≥+1%', d[(d.prev <= -.07) & (d.gap >= .01)], d)
line('SOXX 전날≤−5%·갭≥+2%', d[(d.prev <= -.05) & (d.gap >= .02)], d)
line('SOXX 전날≤−4%·갭≥+2%', d[(d.prev <= -.04) & (d.gap >= .02)], d)
line('SOXX 전날≤−4%·갭≥+1%·200일선 아래', d[(d.prev <= -.04) & (d.gap >= .01) & (d.pc < d.ma200)], d)
line('SOXX 전날≤−4%·갭≥+1% → 시가→5일', d[(d.prev <= -.04) & (d.gap >= .01)], d, 'o5')
line('SOXX 전날≤−4%·갭<0 (비교)', d[(d.prev <= -.04) & (d.gap < 0)], d)
q = D['QQQ']
line('QQQ 전날≤−3%·갭≥+1%', q[(q.prev <= -.03) & (q.gap >= .01)], q)
line('QQQ 전날≤−3%·갭≥+1% → 시가→5일', q[(q.prev <= -.03) & (q.gap >= .01)], q, 'o5')
n = D['NVDA']
line('NVDA 전날≤−7%·갭≥+1%', n[(n.prev <= -.07) & (n.gap >= .01)], n)
s = d[(d.prev <= -.05) & (d.gap >= .01)]
print('  SOXX 주 판정 사건:', ', '.join(f"{i.date()} 전날{r.prev:+.1%} 갭{r.gap:+.1%} 장중{r.oc:+.1%}" for i, r in s.iterrows()))

print('\n■ 114 — 지수 연속 하락 뒤')
def fred(code):
    s = pd.read_csv(f'{PX}/{code}.csv'); s.columns = ['date', 'v']; s['v'] = pd.to_numeric(s.v, errors='coerce')
    s = s.dropna(); s['date'] = pd.to_datetime(s.date); return s.set_index('date').v
for code in ['NASDAQCOM', 'NASDAQ100', 'SP500']:
    v = fred(code); f = pd.DataFrame({'v': v}); f['r'] = f.v.pct_change()
    dn = (f.r < 0).astype(int); st = dn * (dn.groupby((dn != dn.shift()).cumsum()).cumcount() + 1); f['st'] = st
    f['f5'] = f.v.shift(-5) / f.v - 1; f['f20'] = f.v.shift(-20) / f.v - 1; f['f1'] = f.v.shift(-1) / f.v - 1
    f['ma200'] = f.v.rolling(200).mean()
    print(f' [{code}] {f.index[0].date()}~{f.index[-1].date()} · 지금 연속 하락 {int(f.st.iloc[-1])}일(11/19까지, 11/20 미포함)')
    for k in (6, 7, 8):
        e = f[f.st == k]
        line(f'{k}일째 → 뒤 5일' + ('(주 판정)' if (k == 7 and code == 'NASDAQCOM') else ''), e, f, 'f5')
    e = f[f.st == 7]
    line('7일째 → 뒤 1일', e, f, 'f1'); line('7일째 → 뒤 20일', e, f, 'f20')
    line('7일째·200일선 아래 → 뒤 5일', e[e.v < e.ma200], f, 'f5')
    line('7일째·200일선 위 → 뒤 5일', e[e.v >= e.ma200], f, 'f5')
    if code == 'NASDAQCOM':
        line('7일째 1971~1999 → 5일', e[:'1999'], f[:'1999'], 'f5'); line('7일째 2000~ → 5일', e['2000':], f['2000':], 'f5')
        print('  2000~ 사건:', ', '.join(f"{i.date()}({r.f5:+.1%})" for i, r in e['2000':].iterrows()))

if TW:
    print('\n■ 115 — 대만 가권 급락 날 밤 SOXX')
    tw = pd.read_csv(TW, parse_dates=['date']).set_index('date').sort_index(); tw['tr'] = tw.taiex.pct_change()
    gapdays = tw.index.to_series().diff().dt.days; tw.loc[gapdays > 20, 'tr'] = np.nan   # 자료가 빠진 구간 건너뜀
    d = D['SOXX']; j = d.join(tw.tr, how='inner').dropna(subset=['tr', 'gap', 'oc'])
    print(f' {j.index[0].date()}~{j.index[-1].date()} 겹친 날 {len(j)}')
    for th in (-.03, -.02, -.04):
        s = j[j.tr <= th]
        tag = '(주 판정)' if th == -.03 else ''
        line(f'가권≤{th:.0%}·SOXX 갭<0{tag}', s[s.gap < 0], j)
        line(f'가권≤{th:.0%}·SOXX 갭≥0', s[s.gap >= 0], j)
    s = j[(j.tr <= -.03)]; line('가권≤−3% 전체', s, j)
    s2 = j['2020':]; line('가권≤−3%·갭<0 2020~', s2[(s2.tr <= -.03) & (s2.gap < 0)], s2)
    line('가권≤−3%·갭<−2%', j[(j.tr <= -.03) & (j.gap < -.02)], j)
    s = j[(j.tr <= -.03)]
    print('  최근 사건:', ', '.join(f"{i.date()} 가권{r.tr:+.1%} 갭{r.gap:+.1%} 장중{r.oc:+.1%}" for i, r in s.tail(12).iterrows()))
