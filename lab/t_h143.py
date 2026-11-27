"""H143: CFTC TFF leveraged-funds net position in NASDAQ-100 futures -> QQQ/SOXX forward returns.
Pre-registered definitions (see task). Data: cftc_20974%2B.json (NASDAQ-100 Consolidated, CME, futures only),
qqq_daily.csv / soxx_daily.csv (Twelve Data 1day, split-adjusted close, price return, no dividends).
"""
import json, numpy as np, pandas as pd

rng = np.random.default_rng(143)
B = 10_000

# ---------- CFTC ----------
c = pd.DataFrame(json.load(open('cftc_20974%2B.json')))
c['report_date'] = pd.to_datetime(c.report_date_as_yyyy_mm_dd)
for k in ['open_interest_all', 'lev_money_positions_long', 'lev_money_positions_short']:
    c[k] = c[k].astype(float)
c = c.sort_values('report_date').reset_index(drop=True)
c['lev_net_pct'] = (c.lev_money_positions_long - c.lev_money_positions_short) / c.open_interest_all * 100
c['chg'] = c.lev_net_pct.diff()
c['release'] = c.report_date + pd.Timedelta(days=3)

# rolling past-only stats
prev_chg = c.chg.shift(1)
c['chg_mu52'] = prev_chg.rolling(52, min_periods=52).mean()
c['chg_sd52'] = prev_chg.rolling(52, min_periods=52).std()   # sample std (ddof=1)
prev_lvl = c.lev_net_pct.shift(1)
c['p10_156'] = prev_lvl.rolling(156, min_periods=156).quantile(0.10, interpolation='linear')
c['p20_156'] = prev_lvl.rolling(156, min_periods=156).quantile(0.20, interpolation='linear')
c['pctile_156'] = [  # percentile rank of current level vs previous 156 weeks (share of past <= current)
    (np.mean(c.lev_net_pct.values[i-156:i] <= c.lev_net_pct.values[i]) * 100) if i >= 156 else np.nan
    for i in range(len(c))]
c['chg_pctile_52'] = [
    (np.mean(c.chg.values[i-52:i] <= c.chg.values[i]) * 100) if i >= 53 else np.nan for i in range(len(c))]

c['sig_a20'] = c.chg >= c.chg_mu52 + 2.0 * c.chg_sd52
c['sig_a15'] = c.chg >= c.chg_mu52 + 1.5 * c.chg_sd52
c['sig_b10'] = c.lev_net_pct <= c.p10_156
c['sig_b20'] = c.lev_net_pct <= c.p20_156

# ---------- prices ----------
px = {}
for s in ['QQQ', 'SOXX']:
    d = pd.read_csv(f'{s.lower()}_daily.csv', parse_dates=['datetime']).sort_values('datetime').reset_index(drop=True)
    px[s] = d
dates = px['QQQ'].datetime.values
assert (dates == px['SOXX'].datetime.values).all()

c['entry_idx'] = np.searchsorted(dates, c.release.values, side='left')
c.loc[c.entry_idx >= len(dates), 'entry_idx'] = -1
c['entry_date'] = [pd.Timestamp(dates[i]) if i >= 0 else pd.NaT for i in c.entry_idx]
for s in ['QQQ', 'SOXX']:
    cl = px[s].close.values
    for h in [5, 20]:
        r = np.full(len(c), np.nan)
        for j, i in enumerate(c.entry_idx):
            if i >= 0 and i + h < len(cl):
                r[j] = (cl[i + h] / cl[i] - 1) * 100
        c[f'{s}_{h}'] = r

# approximate US-government-shutdown windows when CFTC releases were delayed (report_date+3 not actually public)
SHUT = [('2013-10-01', '2013-10-22'), ('2018-12-22', '2019-02-15'), ('2025-09-30', '2026-01-20')]
c['shutdown_delay'] = False
for a, b in SHUT:
    c.loc[(c.report_date >= a) & (c.report_date <= b), 'shutdown_delay'] = True


def dedup(mask):
    keep, last = [], -10**9
    for j in np.where(mask.values)[0]:
        i = c.entry_idx.iat[j]
        if i < 0:
            i = len(dates) + 1000  # not yet entered: still counts as a signal (kept if spaced)
        if i - last > 20:
            keep.append(j); last = i
    m = pd.Series(False, index=c.index); m.iloc[keep] = True
    return m


SIGS = {'a20': 'a short-cover 2.0sd (MAIN)', 'a15': 'a short-cover 1.5sd (variant)',
        'b10': 'b extreme-short p10 (MAIN)', 'b20': 'b extreme-short p20 (variant)'}
for k in SIGS:
    c[f'keep_{k}'] = dedup(c[f'sig_{k}'])


def stats(sig_mask, base_mask, col):
    x = c.loc[sig_mask, col].dropna().values
    base = c.loc[base_mask, col].dropna().values
    bm = base.mean()
    n = len(x)
    out = dict(n=n, base_n=len(base), base_mean=bm)
    if n == 0:
        return out
    out.update(mean=x.mean(), median=np.median(x), pos=(x > 0).mean() * 100, worst=x.min(), diff=x.mean() - bm)
    bs1 = rng.choice(x, (B, n)).mean(1) - bm
    bs2 = rng.choice(x, (B, n)).mean(1) - rng.choice(base, (B, len(base))).mean(1)
    out.update(ci1_lo=np.percentile(bs1, 5), ci1_hi=np.percentile(bs1, 95),
               ci2_lo=np.percentile(bs2, 5), ci2_hi=np.percentile(bs2, 95))
    k = int(np.ceil(0.3 * n))
    xr = x[-k:]  # rows are in date order
    out.update(recent_n=k, recent_mean=xr.mean(), recent_diff=xr.mean() - bm)
    out['mean_ex_best2'] = np.sort(x)[:-2].mean() if n > 2 else np.nan
    return out


rows = []
base_all = pd.Series(True, index=c.index)
for label, extra in [('all', base_all), ('ex_shutdown', ~c.shutdown_delay)]:
    for k, name in SIGS.items():
        for s in ['QQQ', 'SOXX']:
            for h in [5, 20]:
                st = stats(c[f'keep_{k}'] & extra, base_all & extra, f'{s}_{h}')
                rows.append(dict(sample=label, signal=k, desc=name, sym=s, h=h, **st))
res = pd.DataFrame(rows)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
cols = ['sample', 'signal', 'sym', 'h', 'n', 'mean', 'median', 'pos', 'worst', 'base_mean', 'diff',
        'ci1_lo', 'ci1_hi', 'ci2_lo', 'ci2_hi', 'recent_n', 'recent_mean', 'recent_diff', 'mean_ex_best2']
print('CFTC coverage:', c.report_date.min().date(), '->', c.report_date.max().date(), 'rows', len(c))
print('Price coverage:', pd.Timestamp(dates[0]).date(), '->', pd.Timestamp(dates[-1]).date(), 'days', len(dates))
print('raw signal counts:', {k: int(c[f'sig_{k}'].sum()) for k in SIGS}, 'dedup:', {k: int(c[f'keep_{k}'].sum()) for k in SIGS})
print(res[cols].round(2).to_string(index=False))
res.to_csv('h143_results.csv', index=False)

# signal rows csv
sr = []
for k in SIGS:
    for j in np.where(c[f'sig_{k}'])[0]:
        r = c.iloc[j]
        sr.append(dict(signal=k, report_date=r.report_date.date(), release=r.release.date(),
                       entry=(r.entry_date.date() if pd.notna(r.entry_date) else None), kept=bool(r[f'keep_{k}']),
                       lev_net_pct=round(r.lev_net_pct, 3), chg=round(r.chg, 3),
                       thr_a=round(r.chg_mu52 + (2.0 if k == 'a20' else 1.5) * r.chg_sd52, 3) if k[0] == 'a' else None,
                       thr_b=round(r.p10_156 if k == 'b10' else r.p20_156, 3) if k[0] == 'b' else None,
                       shutdown_delay=bool(r.shutdown_delay),
                       QQQ_5=r.QQQ_5, QQQ_20=r.QQQ_20, SOXX_5=r.SOXX_5, SOXX_20=r.SOXX_20))
sr = pd.DataFrame(sr)
sr.to_csv('h143_signal_rows.csv', index=False)

# case check: +-8 weeks around lows
print('\nCASE CHECK (report dates within +-56 days of low; all raw signals, kept flag)')
for low in ['2022-10-13', '2025-04-08']:
    L = pd.Timestamp(low)
    w = sr[(pd.to_datetime(sr.report_date) >= L - pd.Timedelta(days=56)) & (pd.to_datetime(sr.report_date) <= L + pd.Timedelta(days=56))]
    print(f'-- low {low}')
    print(w[['signal', 'report_date', 'release', 'entry', 'kept', 'lev_net_pct', 'chg', 'thr_a', 'thr_b', 'QQQ_20', 'SOXX_20']].round(2).to_string(index=False) if len(w) else '  none')
    ww = c[(c.report_date >= L - pd.Timedelta(days=56)) & (c.report_date <= L + pd.Timedelta(days=56))]
    print(ww[['report_date', 'lev_net_pct', 'chg', 'pctile_156', 'p10_156', 'p20_156']].round(2).to_string(index=False))

print('\nLATEST 6 REPORTS')
print(c[['report_date', 'release', 'open_interest_all', 'lev_money_positions_long', 'lev_money_positions_short', 'lev_net_pct', 'chg',
         'chg_mu52', 'chg_sd52', 'chg_pctile_52', 'pctile_156', 'p10_156', 'p20_156']].tail(6).round(3).to_string(index=False))
last = c.iloc[-1]
print('latest z of weekly change vs prev 52:', round((last.chg - last.chg_mu52) / last.chg_sd52, 2))
print('variants run: 4 signal defs (a2.0 main, a1.5, b10 main, b20) x 2 symbols x 2 horizons = 16 cells, '
      'x 2 samples (all, ex-shutdown robustness) = 32 cells')
