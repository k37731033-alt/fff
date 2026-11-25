# H134: sector-only selloff (SOXX<=-4%, SPY>=-1%) -> buy ATM call at close, expiry = Friday of following week,
# sell at close 5 trading days later. SOXL main, NVDA secondary. Controls = event + 15 trading days.
# Data: Massive (Polygon) daily aggs, fetched 2026-11-25. Option closes hand-copied from API output into ROWS.
import numpy as np, pandas as pd

FEE_PCT = 0.04      # 4% each side (spread/slippage + fx assumption)
FEE_FIX = 1.99      # USD per contract per side
OUT = '/tmp/claude-0/-home-claude-fff/8d1e0b32-9975-5ea4-9b7c-6e00bf0bd753/scratchpad/h134_rows.csv'

# group, date, ticker, option, S0, entry, exit_date, exit_px, note
ROWS = [
 ('event','2026-01-30','SOXL','O:SOXL260206C00062000',61.79,3.68,'2026-02-06',0.06,'exit = expiry day'),
 ('event','2026-03-03','SOXL','O:SOXL260313C00053000',53.42,4.95,'2026-03-10',3.77,''),
 ('event','2026-03-30','SOXL','O:SOXL260410C00040500',40.62,3.40,'2026-04-07',14.89,'thin: 5 trades on exit day, close < intrinsic 16.05'),
 ('event','2026-06-16','SOXL','O:SOXL260626C00225000',226.19,30.45,'2026-06-24',30.00,'226 not listed (2.5 steps >200) -> 225'),
 ('event','2026-06-26','SOXL','O:SOXL260702C00215000',215.60,20.95,'2026-07-01',10.32,'expiry Thu 7/2 (7/3 holiday); exit moved to 7/1 (3 days held)'),
 ('event','2026-07-07','SOXL','O:SOXL260717C00165000',165.28,21.25,'2026-07-14',20.00,''),
 ('event','2026-07-16','SOXL','O:SOXL260724C00142000',142.48,16.50,'2026-07-23',14.70,''),
 ('event','2026-07-24','SOXL','O:SOXL260731C00137000',136.81,15.20,'2026-07-31',0.01,'exit = expiry day'),
 ('event','2026-08-18','SOXL','O:SOXL260828C00129000',129.10,10.00,'2026-08-25',1.67,''),
 ('event','2026-09-14','SOXL','O:SOXL260925C00101000',101.13,7.75,'2026-09-21',42.00,'thin: 6 trades on exit day'),
 ('event','2026-01-30','NVDA','O:NVDA260206C00190000',191.13,5.00,'2026-02-06',0.01,'exit = expiry day'),
 ('event','2026-03-03','NVDA','O:NVDA260313C00180000',180.05,5.65,'2026-03-10',6.17,''),
 ('event','2026-03-30','NVDA','O:NVDA260410C00165000',165.17,4.90,'2026-04-07',13.15,''),
 ('event','2026-06-16','NVDA','O:NVDA260626C00207500',207.41,4.90,'2026-06-24',0.38,''),
 ('event','2026-06-26','NVDA','O:NVDA260702C00192500',192.53,3.55,'2026-07-01',5.78,'expiry Thu 7/2; exit moved to 7/1'),
 ('event','2026-07-07','NVDA','O:NVDA260717C00197500',196.93,5.15,'2026-07-14',14.77,''),
 ('event','2026-07-16','NVDA','O:NVDA260724C00207500',207.40,5.10,'2026-07-23',2.43,''),
 ('event','2026-07-24','NVDA','O:NVDA260731C00207500',206.84,4.45,'2026-07-31',0.01,'exit = expiry day'),
 ('event','2026-08-18','NVDA','O:NVDA260828C00220000',219.74,6.95,'2026-08-25',3.70,'NVDA earnings inside option life (estimate)'),
 ('event','2026-09-14','NVDA','O:NVDA260925C00210000',210.96,5.55,'2026-09-21',17.75,''),
 ('control','2026-02-23','SOXL','O:SOXL260306C00066000',65.86,5.60,'2026-03-02',2.01,''),
 ('control','2026-03-24','SOXL','O:SOXL260402C00055000',54.96,4.22,'2026-03-31',0.16,'expiry Thu 4/2 (Good Friday)'),
 ('control','2026-04-21','SOXL','O:SOXL260501C00098000',98.09,9.40,'2026-04-28',11.18,''),
 ('control','2026-07-09','SOXL','O:SOXL260717C00192000',192.45,21.10,'2026-07-16',0.03,''),
 ('control','2026-07-20','SOXL','O:SOXL260731C00137000',136.81,21.50,'2026-07-27',8.25,'thin: 6 trades on entry day'),
 ('control','2026-07-28','SOXL','O:SOXL260807C00110000',109.54,13.00,'2026-08-04',33.85,''),
 ('control','2026-08-06','SOXL','O:SOXL260814C00132000',132.33,14.36,'2026-08-13',13.50,'thin: 9 trades on exit day'),
 ('control','2026-08-14','SOXL','O:SOXL260821C00145000',144.95,8.60,'2026-08-21',0.04,'exit = expiry day'),
 ('control','2026-09-09','SOXL','O:SOXL260918C00126000',125.87,8.73,'2026-09-16',0.09,''),
 ('control','2026-10-05','SOXL','O:SOXL261016C00164000',164.27,10.69,'2026-10-12',0.18,''),
 ('control','2026-02-23','NVDA','O:NVDA260306C00192500',191.55,7.27,'2026-03-02',0.43,'NVDA earnings 2/25 inside window'),
 ('control','2026-03-24','NVDA','O:NVDA260402C00175000',175.20,4.29,'2026-03-31',1.70,'expiry Thu 4/2'),
 ('control','2026-04-21','NVDA','O:NVDA260501C00200000',199.88,4.85,'2026-04-28',13.82,''),
 ('control','2026-07-09','NVDA','O:NVDA260717C00202500',202.78,4.75,'2026-07-16',5.45,''),
 ('control','2026-07-20','NVDA','O:NVDA260731C00202500',203.28,6.35,'2026-07-27',1.81,''),
 ('control','2026-07-28','NVDA','O:NVDA260807C00197500',197.01,5.50,'2026-08-04',14.80,''),
 ('control','2026-08-06','NVDA','O:NVDA260814C00220000',218.99,4.15,'2026-08-13',5.44,''),
 ('control','2026-08-14','NVDA','O:NVDA260821C00225000',225.16,3.80,'2026-08-21',0.01,'exit = expiry day'),
 ('control','2026-09-09','NVDA','O:NVDA260918C00222500',223.67,5.40,'2026-09-16',0.23,''),
 ('control','2026-10-05','NVDA','O:NVDA261016C00240000',238.90,4.40,'2026-10-12',0.20,''),
]
df = pd.DataFrame(ROWS, columns=['group','date','ticker','option','S0','entry','exit_date','exit_px','note'])
df['strike'] = df.option.str[-8:].astype(int)/1000
df['ret'] = (df.exit_px*(1-FEE_PCT))/(df.entry*(1+FEE_PCT)) - 1 - (2*FEE_FIX)/(df.entry*100)
df.to_csv(OUT, index=False)

rng = np.random.default_rng(134)
def summ(r):
    r = np.asarray(r); bs = rng.choice(r, (5000, len(r))).mean(1)
    return dict(n=len(r), mean=r.mean(), median=np.median(r), win=(r>0).mean(), best=r.max(), worst=r.min(),
                ci5=np.percentile(bs,5), ci95=np.percentile(bs,95))
pd.set_option('display.width',200)
print(df[['group','date','ticker','option','S0','entry','exit_date','exit_px','ret']].to_string(index=False, float_format=lambda x:f'{x:.3f}'))
print()
S = pd.DataFrame({f'{t} {g}': summ(df[(df.ticker==t)&(df.group==g)].ret) for t in ['SOXL','NVDA'] for g in ['event','control']}).T
print(S.to_string(float_format=lambda x:f'{x:+.1%}' if abs(x)<50 else f'{x:.0f}'))
