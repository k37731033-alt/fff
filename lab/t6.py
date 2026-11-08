exec(open('tests.py').read())
# T6 카드 3번: 상승추세(SOXX 50>200)에서 아무 날 시가 2% 외가 콜 vs 풋(만기 3일), 종가 매도. 국면별
res={}
for s in ['SOXX','NVDA','MU']:
    d=X[s]; rows=[]
    for i in d.index[260::1]:
        if i not in reg.index: continue
        L=lab(i)
        if L is None or np.isnan(d.v.loc[i]) or not reg.up.loc[i]: continue
        c=opt_trade(d,i,1,0.02,3,1.2); p=opt_trade(d,i,-1,0.02,3,1.2)
        if c and p: rows.append({'reg':L,'date':i,'call':c[0],'put':p[0]})
    print('\nT6',s,'상승추세 아무 날 (시가→종가, 3일 만기 2% 외가)'); print(summ(rows,['call','put']).to_string())
    df=pd.DataFrame(rows); r=df[df.date>='2026-05-01']; print('  2026-05~:',round(r.call.mean()*100,1),round(r.put.mean()*100,1),len(r))
# T7 아래 갭 −3% 날 당일 만기 3%·5% 외가 풋 (시가 매수 → 종가 가치=내재가치), 상승추세 HH/H/N
print('\nT7 아래갭 −3% 날, 시가에 당일 만기 외가 풋 (종가=만기 가치)')
for s in ['SOXX','NVDA','MU']:
    d=X[s]; rows=[]
    for i in sx.index[sx.gap<=-0.03]:
        if i not in d.index or np.isnan(d.v.loc[i]): continue
        L=lab(i)
        if L is None: continue
        S0=d.open.loc[i]; v=d.v.loc[i]*1.4
        o={'reg':L,'date':i}
        for otm in (0.01,0.03):
            K=S0*(1-otm); p0=bs(S0,K,0.25/252,v,False)*1.08
            if p0<0.005*S0*0.01: p0=0.005*S0*0.01
            # 02:00 KST ≈ 장 시작 2.5시간 뒤 정리 vs 종가
            o[f'p{int(otm*100)}']=max(K-d.close.loc[i],0)/p0-1
            o[f'best{int(otm*100)}']=max(K-d.low.loc[i],0)*0.9/p0-1
        rows.append(o)
    print('\n',s); print(summ(rows,['p1','p3','best1']).to_string())
    df=pd.DataFrame(rows); r=df[df.date>='2026-05-01']; print('  2026-05~ p1/p3 평균·이긴:',round(r.p1.mean()*100),round((r.p1>0).mean()*100),round(r.p3.mean()*100),round((r.p3>0).mean()*100),len(r))
