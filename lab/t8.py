exec(open('tests.py').read())
# HH 아래갭 날: 당일 만기 1% 외가 풋, 시가 매수 → 지정가 +50%/+100% 닿으면 그 값, 아니면 종가 가치. 장중 최저 시각 모름 → 낙관적
for s in ['SOXX','NVDA','MU']:
    d=X[s]; out={}
    for tgt in (0.5,1.0,2.0):
        res=[]
        for i in sx.index[sx.gap<=-0.03]:
            if i not in d.index or lab(i)!='HH' or np.isnan(d.v.loc[i]): continue
            S0=d.open.loc[i]; v=d.v.loc[i]*1.4; K=S0*0.99
            p0=bs(S0,K,0.25/252,v,False)*1.08
            # 장중 최저에서의 가치(남은 시간 절반 가정)
            pl=bs(d.low.loc[i],K,0.12/252,v,False)*0.92
            hit=pl>=p0*(1+tgt)
            res.append(tgt if hit else max(K-d.close.loc[i],0)/p0-1)
        r=np.array(res); out[tgt]=(round(r.mean()*100),round(np.median(r)*100),round((r>0).mean()*100),len(r))
    print(s,'지정가 +50% / +100% / +200% → (평균, 중간, 이긴%, n):',out)
