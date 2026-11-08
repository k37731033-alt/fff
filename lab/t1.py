exec(open('tests.py').read())
print('=== T1 큰 갭 날(SOXX 시가 갭 |≥3%|), 시가에 갭 방향으로 타면? ===')
for s in ['SOXX','NVDA','MU','SOXL']:
    d=X[s]; rows=[]
    for i in sx.index[sx.gap.abs()>=0.03]:
        if i not in d.index: continue
        L=lab(i)
        if L is None or np.isnan(d.v.loc[i]): continue
        dirn=np.sign(sx.gap.loc[i]); o=d.open.loc[i]
        oc=dirn*(d.close.loc[i]/o-1)
        mfe=(d.high.loc[i]/o-1) if dirn>0 else (1-d.low.loc[i]/o)
        r={'reg':L,'oc':oc,'mfe':mfe,'down':dirn<0}
        if s!='SOXL':
            t=opt_trade(d,i,dirn,0.02,4)
            if t: r['opt_close'],r['opt_mix'],r['tp']=t
        rows.append(r)
    df=pd.DataFrame(rows)
    cols=['oc','mfe']+(['opt_close','opt_mix'] if s!='SOXL' else [])
    print('\n',s); print(summ(rows,cols).to_string())
    if s!='SOXL': print('  +100% 닿은 비율:',df.groupby('reg').tp.mean().round(2).to_dict())
    # 아래 갭만
    print('  아래 갭만 (oc 평균/이긴비율):',{k:(round(g.oc.mean()*100,1),round((g.oc>0).mean()*100),len(g)) for k,g in df[df.down].groupby('reg')})
    print('  위 갭만:',{k:(round(g.oc.mean()*100,1),round((g.oc>0).mean()*100),len(g)) for k,g in df[~df.down].groupby('reg')})
