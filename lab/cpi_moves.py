import pandas as pd,numpy as np,glob,os
CPI=pd.to_datetime(['2026-03-11','2026-04-10','2026-05-12','2026-06-10','2026-07-14','2026-08-12','2026-09-11','2026-10-14'])  # 40 문서, 직전 8번
out=[]
for f in sorted(glob.glob('../data/daily/*.csv')):
    s=os.path.basename(f)[:-4]
    d=pd.read_csv(f,parse_dates=['datetime']).set_index('datetime')
    r=d.close.pct_change()
    m=r.reindex(CPI).abs()
    rv=np.log(d.close).diff().tail(20).std()
    allabs=r['2026-03-01':].abs().mean()
    out.append(dict(s=s,cpi8=m.mean()*100,cpi_med=m.median()*100,n=m.notna().sum(),other=allabs*100,rv1d=rv*100*0.798))
o=pd.DataFrame(out).set_index('s').round(2)
o['ratio_cpi_vs_other']=(o.cpi8/o.other).round(2)
print(o.sort_values('ratio_cpi_vs_other',ascending=False).to_string())
o.to_csv('/tmp/claude-0/-home-claude/c5d8715e-910b-5c3f-9687-e6b60606200c/scratchpad/cpi8.csv')
