exec(open('tests.py').read())
def show(rows,cols,title):
    print('\n'+title); print(summ(rows,cols).to_string())
    df=pd.DataFrame(rows); r26=df[df.date>=pd.Timestamp('2026-05-01')]
    if len(r26): print('  2026-05~:',{c:(round(r26[c].mean()*100,1),round((r26[c]>0).mean()*100),len(r26)) for c in cols})
# T3 D 반등: 그 종목 상승추세(50>200) + 3일 하락 ≤ -1.5×평소 → 다음 날 시가 매수, 5거래일 뒤 종가. 2주 등가 콜 모델
for s in ['MU','NVDA','SOXL','SOXX']:
    d=X[s]; rows=[]; last=-99
    ix=d.index
    for k in range(203,len(ix)-6):
        i=ix[k]
        if not d.sma50.iloc[k]>d.sma200.iloc[k]: continue
        r3=d.close.iloc[k]/d.close.iloc[k-3]-1; v=d.v.iloc[k]
        if np.isnan(v) or r3> -1.5*v*sqrt(3/252): continue
        if k-last<5: continue
        last=k; j=ix[k+1]; L=lab(j)
        if L is None: continue
        ret5=d.close.iloc[k+6]/d.open.iloc[k+1]-1
        S0=d.open.iloc[k+1]; vv=d.v.iloc[k+1]*1.2
        p0=bs(S0,S0,10/252,vv,True)*1.05; p1=bs(d.close.iloc[k+6],S0,4.75/252,vv,True)*0.95
        rows.append({'reg':L,'date':j,'ret5':ret5,'call':p1/p0-1})
    show(rows,['ret5','call'],f'T3 D 반등 {s} (5거래일 현물 / 2주 등가 콜)')
# T4 금요일 SOXX −4% 이하 → 월요일
rows=[]
ix=sx.index
for k in range(1,len(ix)-1):
    i=ix[k]
    if i.weekday()!=4 or sx.ret.iloc[k]>-0.04: continue
    j=ix[k+1]; L=lab(j)
    if L is None: continue
    rows.append({'reg':L,'date':j,'mon_open':sx.open.iloc[k+1]/sx.close.iloc[k]-1,'mon_close':sx.close.iloc[k+1]/sx.close.iloc[k]-1,'mon_high':sx.high.iloc[k+1]/sx.close.iloc[k]-1})
show(rows,['mon_open','mon_close','mon_high'],'T4 금요일 SOXX −4% → 월요일 (금 종가 대비)')
# T5 SOXX −5% 하루 급락 → 1/5/20일 (눌림 사기)
rows=[]
for k in range(1,len(ix)-21):
    if sx.ret.iloc[k]>-0.05: continue
    j=ix[k]; L=lab(j)
    if L is None: continue
    c=sx.close
    rows.append({'reg':L,'date':j,'d1':c.iloc[k+1]/c.iloc[k]-1,'d5':c.iloc[k+5]/c.iloc[k]-1,'d20':c.iloc[k+20]/c.iloc[k]-1})
show(rows,['d1','d5','d20'],'T5 SOXX 하루 −5% → 1·5·20거래일 뒤')
# T5b +5% 급등일 → 
rows=[]
for k in range(1,len(ix)-21):
    if sx.ret.iloc[k]<0.05: continue
    j=ix[k]; L=lab(j)
    if L is None: continue
    c=sx.close
    rows.append({'reg':L,'date':j,'d1':c.iloc[k+1]/c.iloc[k]-1,'d5':c.iloc[k+5]/c.iloc[k]-1,'d20':c.iloc[k+20]/c.iloc[k]-1})
show(rows,['d1','d5','d20'],'T5b SOXX 하루 +5% → 1·5·20거래일 뒤')
