"""t_h132.py — pre-registered: B4 real option trades, SOXX day <= -3% vs rest.
usage: python t_h132.py <b4_csv_dir> <soxx_data_dir>
Return = os/cb - 1 (buy at signal-day close 'cb', sell at next open 'os'); gross, no cost column exists.
Main universe = semiconductor names incl. SOXL (M7 rows reported as sensitivity only).
"""
import sys, os, numpy as np, pandas as pd
B, D = sys.argv[1], sys.argv[2]
SEED, NB = 132, 5000
SEMI = {'MU', 'NVDA', 'AMD', 'MRVL', 'AVGO', 'TSM', 'SOXL'}

# ---- 1. trades, de-dup ----
fr = []
for fn, src in [('b4_real.csv', 'real'), ('b4_oos_real.csv', 'oos'), ('b4w_real.csv', 'wide'),
                ('b4_soxl_real.csv', 'soxl'), ('b4_all_exit.csv', 'all_exit')]:
    x = pd.read_csv(os.path.join(B, fn)); x['src'] = src
    print(f'{fn}: {len(x)} rows')
    fr.append(x[['t', 'a', 'cb', 'os', 'src']])
A = pd.concat(fr)
A['a'] = pd.to_datetime(A.a)
# conflicts: same (t,a) with different prices?
chk = A.groupby(['t', 'a']).agg(ncb=('cb', 'nunique'), nos=('os', 'nunique'), srcs=('src', lambda s: '+'.join(sorted(s))))
bad = chk[(chk.ncb > 1) | (chk.nos > 1)]
print('price conflicts among duplicates:', len(bad)); print(bad.to_string() if len(bad) else '')
print('source combos:\n', chk.srcs.value_counts().to_string())
T = A.drop_duplicates(['t', 'a']).reset_index(drop=True)
T['r'] = T.os / T.cb - 1
T['semi'] = T.t.isin(SEMI)
print(f'de-dup trades: {len(T)} (semi {T.semi.sum()}, M7 {(~T.semi).sum()}), {T.a.min().date()}..{T.a.max().date()}')

# ---- 2. SOXX ----
S = pd.concat([pd.read_csv(os.path.join(D, 'SOXX_old.csv')), pd.read_csv(os.path.join(D, 'SOXX.csv'))])
S['datetime'] = pd.to_datetime(S.datetime)
S = S.drop_duplicates('datetime').sort_values('datetime').set_index('datetime')
S['ret'] = S.close.pct_change(); S['sma200'] = S.close.rolling(200).mean()
miss = set(T.a) - set(S.index)
print('signal dates missing in SOXX:', sorted(d.date() for d in miss))
T = T.join(S[['ret', 'close', 'sma200']], on='a').rename(columns={'ret': 'sx'})
T['below'] = T.close < T.sma200
T['wd'] = T.a.dt.dayofweek

# ---- 3. stats ----
rng = np.random.default_rng(SEED)
def boot_means(g):
    """cluster bootstrap by night: resample nights, mean over all trades in them"""
    nights = [v.values for _, v in g.groupby('a').r]
    if not nights: return np.array([np.nan] * NB)
    s = np.array([v.sum() for v in nights]); c = np.array([len(v) for v in nights])
    idx = rng.integers(0, len(nights), (NB, len(nights)))
    return s[idx].sum(1) / c[idx].sum(1)
def stats(g, name):
    r = g.r.values
    if len(r) == 0: return dict(group=name, n=0, mean=np.nan), np.full(NB, np.nan)
    bm = boot_means(g)
    ex2 = np.sort(r)[:-2].mean() if len(r) > 2 else np.nan
    return dict(group=name, n=len(r), nights=g.a.nunique(), mean=r.mean(), median=np.median(r),
                win=(r > 0).mean(), worst=r.min(), lo=np.percentile(bm, 5), hi=np.percentile(bm, 95), ex_best2=ex2), bm
def diff(g, mask, name):
    a, b = g[mask], g[~mask]
    sa, ba = stats(a, 'in'); sb, bb = stats(b, 'out')
    d = ba - bb
    return dict(test=name, n_in=len(a), n_out=len(b), mean_in=sa['mean'], mean_out=sb['mean'],
                diff=(a.r.mean() - b.r.mean()) if len(a) and len(b) else np.nan, lo=np.nanpercentile(d, 5), hi=np.nanpercentile(d, 95),
                pass_=bool(np.nanpercentile(d, 95) < 0) if len(a) and len(b) else False), sa, sb

pct = lambda v: f'{v*100:+.1f}%'
def show(rows):
    for s in rows:
        if s.get('n', 0) == 0: print(f"  {s['group']:38s} n=0"); continue
        print(f"  {s['group']:38s} n={s['n']:3d} nights={s['nights']:3d} mean {pct(s['mean'])} med {pct(s['median'])} "
              f"win {s['win']*100:.0f}% worst {pct(s['worst'])} 90%CI [{pct(s['lo'])},{pct(s['hi'])}] ex-best2 {pct(s['ex_best2'])}")

for uni_name, U in [('MAIN universe: semis incl SOXL', T[T.semi]),
                    ('sens: semis excl SOXL', T[T.semi & (T.t != 'SOXL')]),
                    ('sens: all incl M7', T)]:
    print(f'\n===== {uni_name} =====')
    tests = [('MAIN sx<=-3%', U.sx <= -0.03, U),
             ('var sx<=-2%', U.sx <= -0.02, U),
             ('var sx<=-3% & below200', (U.sx <= -0.03) & U.below, U),
             ('var Tue only, sx<=-3%', None, U[U.wd == 1]),
             ('var 2025-06+, sx<=-3%', None, U[U.a >= '2025-06-01'])]
    show([stats(U, 'ALL')[0]])
    for name, m, G in tests:
        if m is None: m = G.sx <= -0.03
        res, sa, sb = diff(G, m, name)
        show([sa | {'group': name + ' IN'}, sb | {'group': name + ' OUT'}])
        print(f"    -> diff {pct(res['diff'])} 90%CI [{pct(res['lo'])},{pct(res['hi'])}] "
              f"{'PASS' if res['pass_'] else 'FAIL'} (n_in={res['n_in']}, n_out={res['n_out']})")
    print('  extra: below200 alone ->', end=' ')
    r, a_, b_ = diff(U, U.below, 'below200')
    print(f"in n={r['n_in']} {pct(r['mean_in'])} vs out {pct(r['mean_out'])}, diff {pct(r['diff'])} CI [{pct(r['lo'])},{pct(r['hi'])}]")

M = T[T.semi & (T.sx <= -0.03)].sort_values('a')
print('\nMAIN group trades (semis, SOXX<=-3%):')
print(M.assign(sx=(M.sx*100).round(2), r=(M.r*100).round(1), below=M.below, wd=M.wd)[['a', 't', 'sx', 'below', 'wd', 'cb', 'os', 'r', 'src']].to_string(index=False))
M7m = T[~T.semi & (T.sx <= -0.03)]
print('\nM7 trades with SOXX<=-3%:', len(M7m)); print(M7m[['a', 't', 'sx', 'r']].to_string(index=False) if len(M7m) else '')
print('\nSOXX<=-3% trades by month:'); print(T[T.sx <= -0.03].groupby(T.a.dt.to_period('M')).size().to_string())
# robustness: drop the single biggest night of the IN group (cluster leave-one-out)
U = T[T.semi]
for drop in sorted(U[U.sx <= -0.03].a.unique()):
    V = U[U.a != drop]; m = V.sx <= -0.03
    print(f"  drop night {pd.Timestamp(drop).date()}: IN n={m.sum()} mean {pct(V[m].r.mean())} | OUT {pct(V[~m].r.mean())} | diff {pct(V[m].r.mean()-V[~m].r.mean())}")
T.to_csv(os.path.join(B, 'h132_trades.csv'), index=False)
