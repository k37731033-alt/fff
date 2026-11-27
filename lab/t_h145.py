"""H145 - 'Huge If True' (alphaXiv 2611.15747): are top-20% EPS surprises discounted?
Pre-registered test: next-day reaction to Top20 surprises (within-stock, past-only percentile)
is NOT larger than to Mid (40-80) surprises.
Data: Alpha Vantage EARNINGS (quarterly, transcribed to earn_<SYM>.txt), Twelve Data daily OHLC (px/<SYM>.csv, split-adjusted).
Run: python3 -I t_h145.py   (from this directory)
"""
import os, csv, numpy as np
from collections import defaultdict

D = os.path.dirname(os.path.abspath(__file__))
SYMS = ['MRVL', 'AVGO', 'MU', 'NVDA', 'AMD', 'CRDO', 'DELL', 'QCOM']
RNG = np.random.default_rng(145)
NB = 10000
N_TESTS = 0  # count of difference/slope tests run (variants)


def load_px(sym):
    rows = []
    with open(f'{D}/px/{sym}.csv') as f:
        r = csv.reader(f); next(r)
        for x in r:
            rows.append((x[0], float(x[1]), float(x[4])))
    rows.sort()
    return [r[0] for r in rows], np.array([r[1] for r in rows]), np.array([r[2] for r in rows])


def load_earn(sym):
    ev = []
    for line in open(f'{D}/earn_{sym}.txt'):
        if line.startswith('#') or not line.strip():
            continue
        p = line.split()
        date, t, sp = p[0], p[1], p[-1]
        ev.append((date, 'post' if t == 'a' else 'pre', None if sp == 'None' else float(sp)))
    ev.sort()
    return ev


def first_idx_ge(dates, d):
    import bisect
    return bisect.bisect_left(dates, d)


def first_idx_gt(dates, d):
    import bisect
    return bisect.bisect_right(dates, d)


# SOXX regime
sd, so, sc = load_px('SOXX')
sma200 = np.full(len(sc), np.nan)
cs = np.cumsum(sc)
for i in range(199, len(sc)):
    sma200[i] = (cs[i] - (cs[i - 200] if i >= 200 else 0)) / 200
soxx_below = {sd[i]: (sc[i] < sma200[i]) if not np.isnan(sma200[i]) else None for i in range(len(sd))}

def build(fix_labels=False):
  events = []
  oddity = []
  dropped = defaultdict(int)
  for sym in SYMS:
      dates, op, cl = load_px(sym)
      raw = load_earn(sym)
      pool = []
      for (rd, rt, sp) in raw:
          if fix_labels and sym in ('NVDA', 'AVGO') and rt == 'pre':
              rt = 'post'  # label fix: these labels fail the gap check (see output)
          if sp is None:
              dropped['missing_est'] += 1; continue
          if abs(sp) > 1000:
              dropped['abs_gt_1000'] += 1; continue
          past = np.array(pool)
          pool.append(sp)
          # reaction-day index
          if rt == 'post':
              ri = first_idx_gt(dates, rd)
          else:
              ri = first_idx_ge(dates, rd)
          # label check: gap on alternative day
          if 1 <= ri < len(dates) - 1:
              alt = ri + 1 if rt == 'pre' else ri - 1  # pre: next day; post: reportedDate itself
              g_lab = op[ri] / cl[ri - 1] - 1
              g_alt = op[alt] / cl[alt - 1] - 1 if alt >= 1 else np.nan
              oddity.append((sym, rd, rt, g_lab, g_alt))
          if len(past) < 8:
              dropped['lt8_past'] += 1; continue
          if ri < 1 or ri >= len(dates):
              dropped['no_price'] += 1; continue
          pc = cl[ri - 1]
          gap = op[ri] / pc - 1
          day = cl[ri] / pc - 1
          d5 = cl[ri + 4] / pc - 1 if ri + 4 < len(dates) else np.nan
          pct = (np.sum(past < sp) + 0.5 * np.sum(past == sp)) / len(past) * 100  # mid-rank
          pct_weak = np.sum(past <= sp) / len(past) * 100  # variant: ties counted as below
          events.append(dict(sym=sym, reportedDate=rd, reportTime=rt, react=dates[ri], prior=dates[ri - 1],
                             surprise=sp, n_past=len(past), pct=pct, pct_weak=pct_weak,
                             gap=gap, day=day, d5=d5, soxx_below=soxx_below.get(dates[ri - 1])))
  events.sort(key=lambda e: e['react'])
  return events, oddity, dropped


events, oddity, dropped = build()
events_fix, _, _ = build(True)

with open(f'{D}/h145_events.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(events[0].keys()))
    w.writeheader(); [w.writerow(e) for e in events]


def grp(p, top=80):
    return 'Top' if p >= top else ('Mid' if p >= 40 else 'Low')


def stats(v):
    v = np.array([x for x in v if not np.isnan(x)])
    if len(v) == 0:
        return (0, np.nan, np.nan, np.nan)
    return (len(v), v.mean() * 100, np.median(v) * 100, (v > 0).mean() * 100)


def boot_diff(a, b):
    global N_TESTS
    N_TESTS += 1
    a = np.array([x for x in a if not np.isnan(x)]); b = np.array([x for x in b if not np.isnan(x)])
    if len(a) < 2 or len(b) < 2:
        return (np.nan, np.nan, np.nan, len(a), len(b))
    ia = RNG.integers(0, len(a), (NB, len(a))); ib = RNG.integers(0, len(b), (NB, len(b)))
    d = a[ia].mean(1) - b[ib].mean(1)
    return ((a.mean() - b.mean()) * 100, np.percentile(d, 5) * 100, np.percentile(d, 95) * 100, len(a), len(b))


METRICS = ['gap', 'day', 'd5']
out = []


def P(s=''):
    print(s); out.append(s)


def run(name, evs, pkey='pct', drop_best2=False):
    P(f'\n=== {name}  (events={len(evs)}) ===')
    for m in METRICS:
        g = defaultdict(list); g10 = []
        for e in evs:
            g[grp(e[pkey])].append(e[m])
            if e[pkey] >= 90: g10.append(e[m])
        line = f'{m:4s} '
        for k in ['Top', 'Mid', 'Low']:
            n, mu, md, pp = stats(g[k])
            line += f'| {k}20 n={n} mean={mu:+.2f} med={md:+.2f} pos={pp:.0f}% ' if k == 'Top' else f'| {k} n={n} mean={mu:+.2f} med={md:+.2f} pos={pp:.0f}% '
        n, mu, md, pp = stats(g10)
        line += f'| Top10 n={n} mean={mu:+.2f} med={md:+.2f} pos={pp:.0f}%'
        P(line)
        top = g['Top']
        if drop_best2:
            t = sorted([x for x in top if not np.isnan(x)])
            top = t[:-2]
        d = boot_diff(top, g['Mid'])
        P(f'     Top20-Mid = {d[0]:+.2f}pp  90%CI [{d[1]:+.2f}, {d[2]:+.2f}]  (n {d[3]} vs {d[4]})')
        if not drop_best2:
            d = boot_diff(g10, g['Mid'])
            P(f'     Top10-Mid = {d[0]:+.2f}pp  90%CI [{d[1]:+.2f}, {d[2]:+.2f}]  (n {d[3]} vs {d[4]})')


P(f'Dropped: {dict(dropped)}')
P('Events per stock: ' + ', '.join(f"{s}={sum(e['sym']==s for e in events)}" for s in SYMS))
P(f"Reaction-day range: {events[0]['react']} .. {events[-1]['react']}")

run('ALL', events)
run('2018+', [e for e in events if e['react'] >= '2018-01-01'])
run('SOXX below 200d SMA (prior day)', [e for e in events if e['soxx_below'] == True])
k = int(round(len(events) * 0.3))
run(f'Most recent 30% (last {k} events, from {events[-k]["react"]})', events[-k:])
run('ALL, Top20 minus its best 2 events (per metric)', events, drop_best2=True)
run('Variant: weak percentile (ties count as below)', events, pkey='pct_weak')
run('Variant: NVDA/AVGO pre-market labels treated as post-market', events_fix)
run('Label-fixed + SOXX below 200d SMA', [e for e in events_fix if e['soxx_below'] == True])

# OLS gap ~ percentile
def ols_slope(x, y):
    x = np.asarray(x); y = np.asarray(y)
    xm = x - x.mean()
    return (xm * (y - y.mean())).sum() / (xm ** 2).sum()


def ols_block(name, evs):
    global N_TESTS
    N_TESTS += 1
    x = np.array([e['pct'] for e in evs]); y = np.array([e['gap'] for e in evs])
    b = ols_slope(x, y)
    idx = RNG.integers(0, len(x), (NB, len(x)))
    bs = np.array([ols_slope(x[i], y[i]) for i in idx])
    P(f'OLS gap~pct [{name}] n={len(x)}: slope = {b*100*100:+.2f}pp gap per 100 pct-pts '
      f'(90%CI [{np.percentile(bs,5)*1e4:+.2f}, {np.percentile(bs,95)*1e4:+.2f}]), intercept={ (y.mean()-b*x.mean())*100:+.2f}pp')

P('\n=== OLS ===')
ols_block('ALL', events)
ols_block('2018+', [e for e in events if e['react'] >= '2018-01-01'])
ols_block('label-fixed ALL', events_fix)

# last 3 events per stock
P('\n=== Last 3 events: MRVL, CRDO, AVGO ===')
for s in ['MRVL', 'CRDO', 'AVGO']:
    for e in [e for e in events if e['sym'] == s][-3:]:
        P(f"{s} rep {e['reportedDate']} ({e['reportTime']}) react {e['react']}: surprise={e['surprise']:+.2f}% "
          f"pct={e['pct']:.0f} ({grp(e['pct'])}) gap={e['gap']*100:+.2f}% day={e['day']*100:+.2f}% d5={e['d5']*100:+.2f}%")

# reportTime label check
P('\n=== reportTime label check: |gap| on labelled reaction day vs alternative day ===')
agg = defaultdict(lambda: [0, 0])
for sym, rd, rt, gl, ga in oddity:
    if np.isnan(ga): continue
    key = (sym, rt, 'pre2014' if rd < '2014-01-01' else '2014+')
    agg[key][0] += 1
    if abs(ga) > abs(gl): agg[key][1] += 1
for k2 in sorted(agg):
    n, bad = agg[k2]
    P(f'{k2}: n={n}, alt day bigger |gap| in {bad} ({bad/n*100:.0f}%)')
P('NVDA pre-market-labelled sample (reportedDate gap vs next-day gap):')
for sym, rd, rt, gl, ga in oddity:
    if sym == 'NVDA' and rt == 'pre' and '2009-01-01' <= rd <= '2014-12-31':
        P(f'  {rd}: labelled-day gap {gl*100:+.2f}%  next-day gap {ga*100:+.2f}%')

P(f'\nTests (difference/slope variants) run: {N_TESTS}')
open(f'{D}/h145_output.txt', 'w').write('\n'.join(out))
