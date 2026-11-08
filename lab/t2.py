exec(open('tests.py').read())
def tab(rows,cols,title):
    print('\n'+title); print(summ(rows,cols).to_string())
    df=pd.DataFrame(rows)
    if 'date' in df: 
        r26=df[df.date>=pd.Timestamp('2026-05-01')]
        if len(r26): print('  2026-05~ (지금 같은 장):',{c:(round(r26[c].mean()*100,1),round((r26[c]>0).mean()*100),len(r26)) for c in cols})
# T2 다음 날 추격: SOXX 종가 |±4%| 다음 날 같은 방향(시가→종가), 그리고 반대
for s in ['SOXX','SOXL','NVDA','MU']:
    d=X[s]; rows=[]
    idx=sx.index
    for k in range(1,len(idx)-1):
        i=idx[k]
        if abs(sx.ret.loc[i])<0.04: continue
        j=idx[k+1]
        if j not in d.index: continue
        L=lab(j)
        if L is None: continue
        dirn=np.sign(sx.ret.loc[i])
        rows.append({'reg':L,'date':j,'same_oc':dirn*(d.close.loc[j]/d.open.loc[j]-1),'same_cc':dirn*(d.close.loc[j]/d.close.loc[i]-1),'gapfollow':dirn*(d.open.loc[j]/d.close.loc[i]-1)})
    tab(rows,['same_oc','same_cc'],f'T2 {s}: SOXX ±4% 다음 날 같은 방향 (oc=시가→종가, cc=전날 종가→종가)')
