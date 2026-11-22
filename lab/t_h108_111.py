# 11/22 가설 연구원: 108(주간 급락 뒤) 109(추수감사절 주×하락장) 110(추수감사절 전날·반장) 111(10년물 급락 뒤 SOX)
# 자료: FRED 원본 CSV (NASDAQSOX, NASDAQ100, DGS10). 사용: python t_h108_111.py <csv 폴더>
import sys, numpy as np, pandas as pd, datetime as dt
D = sys.argv[1] if len(sys.argv) > 1 else '.'
rng = np.random.default_rng(1122)
def load(i):
    s = pd.read_csv(f'{D}/{i}.csv', index_col=0, parse_dates=True).iloc[:, 0]
    return pd.to_numeric(s, errors='coerce').dropna()
sox, ndx, y10 = load('NASDAQSOX'), load('NASDAQ100'), load('DGS10')
def clean(s):  # 하루 ±25% 넘는 가짜 값 제거
    r = s.pct_change().abs()
    bad = r[r > .25].index
    return s.drop(bad)
sox, ndx = clean(sox), clean(ndx)
def boot_mean(x, n=5000):
    x = np.asarray(x, float)
    if len(x) < 3: return (np.nan, np.nan)
    m = rng.choice(x, (n, len(x))).mean(1)
    return np.percentile(m, [5, 95])
def boot_diff(a, b, n=5000):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 3: return (np.nan, np.nan)
    d = rng.choice(a, (n, len(a))).mean(1) - rng.choice(b, (n, len(b))).mean(1)
    return np.percentile(d, [5, 95])
def desc(tag, x, base=None):
    x = np.asarray(x, float); n = len(x)
    if n == 0: print(f'{tag}: n=0'); return
    lo, hi = boot_mean(x)
    s = f'{tag}: n={n} 평균 {x.mean()*100:+.2f}% 중간 {np.median(x)*100:+.2f}% 오름 {np.mean(x>0)*100:.0f}% 최악 {x.min()*100:+.1f}% 범위[{lo*100:+.2f},{hi*100:+.2f}]'
    if base is not None:
        dl, dh = boot_diff(x, base)
        s += f' | 기준 {np.mean(base)*100:+.2f}% 차이 {100*(x.mean()-np.mean(base)):+.2f}%p [{dl*100:+.2f},{dh*100:+.2f}]'
    if n >= 6:
        k = max(1, int(round(n*.3))); s += f' | 최근30%({k}) {x[-k:].mean()*100:+.2f}%'
        s += f' | 좋은2뺌 {np.sort(x)[:-2].mean()*100:+.2f}% 나쁜2뺌 {np.sort(x)[2:].mean()*100:+.2f}%'
    print(s)

# ---------- 108 주간 급락 뒤 ----------
print('=== 108 주간 급락 뒤 다음 주/4주 ===')
def weekly(s): return s.resample('W-FRI').last().dropna()
for name, s, ths in [('SOX', sox, [-.08, -.10, -.12]), ('NDX', ndx, [-.07, -.10])]:
    w = weekly(s); r = w.pct_change(); f1 = w.shift(-1)/w-1; f4 = w.shift(-4)/w-1
    if name == 'SOX': r[pd.Timestamp('2008-11-07')] = np.nan  # FRED 2008-11-03 수준 단절(가짜 -43%)이 낀 주는 뺀다
    ma = s.rolling(200).mean().reindex(w.index, method='ffill'); below = w < ma
    for th in ths:
        ev = r[r <= th].index
        print(name, th, [d.strftime('%Y-%m-%d') for d in ev])
        desc(f' {name} 주 {th:.0%}↓ 다음1주', f1[ev].dropna(), f1.dropna())
        desc(f' {name} 주 {th:.0%}↓ 다음4주', f4[ev].dropna(), f4.dropna())
        e2 = [d for d in ev if below.get(d, False)]
        desc(f' {name} 주 {th:.0%}↓ & 200일선 아래 다음1주', f1[e2].dropna(), f1.dropna())
        desc(f' {name} 주 {th:.0%}↓ & 200일선 아래 다음4주', f4[e2].dropna(), f4.dropna())
        # 2주 안에 더 낮은 주간 종가
        lower = [(w.shift(-1)[d] < w[d]) or (w.shift(-2)[d] < w[d]) for d in ev if d in f4.dropna().index]
        print(f'   2주 안 더 낮은 주간 종가 비율 {np.mean(lower)*100:.0f}% (n={len(lower)})')

# ---------- 109/110 추수감사절 ----------
print('=== 109 추수감사절 주 × 장 상태 / 110 전날·반장 ===')
def tg(y):
    d = dt.date(y, 11, 1); d += dt.timedelta((3 - d.weekday()) % 7); return pd.Timestamp(d + dt.timedelta(21))
def at(s, d):  # d 당일 또는 그 전 마지막 값
    x = s[:d]; return x.iloc[-1] if len(x) else np.nan
for name, s in [('NDX', ndx), ('SOX', sox)]:
    ma = s.rolling(200).mean(); dr = s.pct_change()
    rows = []
    for y in range(s.index[0].year + 1, 2026):
        t = tg(y); pf = t - pd.Timedelta(days=6); ppf = t - pd.Timedelta(days=13); wed = t - pd.Timedelta(days=1); fri = t + pd.Timedelta(days=1)
        if pf < s.index[200] or wed not in s.index or fri not in s.index: continue
        rows.append(dict(y=y, wk=at(s, fri)/at(s, pf)-1, prev=at(s, pf)/at(s, ppf)-1, below=at(s, pf) < at(ma, pf),
                         wed=s[wed]/at(s, wed - pd.Timedelta(days=1))-1, fri=s[fri]/s[wed]-1,
                         monwed=s[wed]/at(s, pf)-1))
    T = pd.DataFrame(rows)
    allw = weekly(s).pct_change().dropna()
    desc(f'{name} 추수감사절 주 전체', T.wk, allw)
    desc(f'{name}  200일선 아래 해', T[T.below].wk, T[~T.below].wk); print('   해:', T[T.below][['y', 'wk']].round(3).values.tolist())
    desc(f'{name}  200일선 위 해', T[~T.below].wk, allw)
    desc(f'{name}  직전 주 -3%↓ 해', T[T.prev <= -.03].wk, T[T.prev > -.03].wk); print('   해:', T[T.prev <= -.03][['y', 'prev', 'wk']].round(3).values.tolist())
    desc(f'{name} [110] 수요일 하루', T.wed, dr.dropna())
    desc(f'{name} [110] 금요일 반장(수 종가→금 종가)', T.fri, dr.dropna())
    desc(f'{name} [110] 수요일, 200일선 아래 해', T[T.below].wed, dr.dropna())
    desc(f'{name} [110] 금요일, 200일선 아래 해', T[T.below].fri, dr.dropna())
    desc(f'{name} [110] 월~수 3일(전 금→수)', T.monwed)

# ---------- 111 10년물 급락 뒤 ----------
print('=== 111 10년물 20일 -0.30%p 뒤 ===')
df = pd.concat([sox.rename('sox'), ndx.rename('ndx'), y10.rename('y')], axis=1, sort=True).dropna()
df['dy'] = df.y - df.y.shift(20)
for h in (20, 60):
    df[f's{h}'] = df.sox.shift(-h)/df.sox-1; df[f'n{h}'] = df.ndx.shift(-h)/df.ndx-1
df['s_past'] = df.sox/df.sox.shift(20)-1
def events(mask, gap=20):
    out, last = [], -10**9
    idx = np.where(mask.values)[0]
    for i in idx:
        if i - last > gap: out.append(i); last = i
    return df.index[out]
for th in (-.30, -.40):
    ev = events(df.dy <= th)
    print(th, len(ev), [d.strftime('%Y-%m-%d') for d in ev][-12:])
    for h in (20, 60):
        e = df.loc[ev].dropna(subset=[f's{h}'])
        desc(f' 10년물 {th}%p SOX 뒤 {h}일', e[f's{h}'], df[f's{h}'].dropna())
        desc(f' 10년물 {th}%p NDX 뒤 {h}일', e[f'n{h}'], df[f'n{h}'].dropna())
        desc(f' 10년물 {th}%p SOX-NDX 뒤 {h}일', e[f's{h}']-e[f'n{h}'], (df[f's{h}']-df[f'n{h}']).dropna())
        e2 = e[e.s_past < 0]
        desc(f' 〃 + SOX 20일 수익<0  SOX 뒤 {h}일', e2[f's{h}'], df[f's{h}'].dropna())
print('지금:', df[['y', 'dy']].tail(3).round(2).to_string())
print('SOX 마지막', sox.index[-1].date(), sox.iloc[-1], '200일선', round(sox.rolling(200).mean().iloc[-1], 1), '| NDX', ndx.iloc[-1], round(ndx.rolling(200).mean().iloc[-1], 1))
w = weekly(sox); print('SOX 최근 주간', w.pct_change().tail(4).round(4).to_string())
