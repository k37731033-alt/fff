exec(open('tests.py').read())
print('=== HH(변동성 50%↑) 아래 갭 −3% 날 상세 ===')
rows=[]
for i in sx.index[(sx.gap<=-0.03)]:
    if lab(i)!='HH': continue
    r={'date':i.date(),'gap':round(sx.gap.loc[i]*100,1),'up':bool(reg.up.loc[i])}
    for s in ['SOXX','NVDA','MU','SOXL']:
        d=X[s]
        if i not in d.index or np.isnan(d.v.loc[i]): r[s]=None; continue
        r[s]=round(-(d.close.loc[i]/d.open.loc[i]-1)*100,1)
        if s in('SOXX','NVDA','MU'):
            for otm in (0.02,0.05):
                t=opt_trade(d,i,-1,otm,4,1.3)
                r[f'{s}p{int(otm*100)}']=round(t[0]*100) if t else None
    rows.append(r)
df=pd.DataFrame(rows); print(df.to_string())
for c in ['SOXXp2','SOXXp5','NVDAp2','NVDAp5','MUp2','MUp5']:
    x=df[c].dropna(); print(c,'평균',round(x.mean()),'중간',round(x.median()),'이긴',round((x>0).mean()*100),'n',len(x))
print('\n상승추세(50>200)인 HH 아래갭:'); print(df[df.up][['date','gap','SOXX','SOXL','SOXXp2','NVDAp2','MUp2']].to_string())
