exec(open('t52.py').read().split("rows=[]")[0])
import os
SECT2={k:v for k,v in SECT.items()}
rows=[]
for sec,tks in SECT2.items():
    for s in tks:
        if not os.path.exists(f'../data/daily/{s}.csv'): continue
        d=pd.read_csv(f'../data/daily/{s}.csv',parse_dates=['datetime']).set_index('datetime')
        d=d[~d.index.duplicated()]; d=d[(d.close>=1)&(d.volume>0)]
        lr=np.log(d.close).diff(); d['sd']=lr.rolling(20).std().shift(1); d['v']=d.sd*sqrt(252)
        d['ret']=d.close/d.close.shift(1)-1
        ix=d.index
        for k in range(21,len(d)-6):
            sd=d.sd.iloc[k]
            if np.isnan(sd) or sd<0.004: continue
            r=d.ret.iloc[k]
            if abs(r)<2.5*sd: continue
            j=ix[k+1]; L=lab(j)
            if L is None: continue
            dirn=-np.sign(r)           # 되돌림 방향(급락이면 콜, 급등이면 풋)
            o1=d.open.iloc[k+1]; v=max(d.v.iloc[k],0.15)*1.3
            gapback=dirn*(o1/d.close.iloc[k]-1)/sd   # 밤사이 이미 되돌린 몫
            oc=dirn*(d.close.iloc[k+1]/o1-1)/sd      # 다음 날 시가→종가
            c5=dirn*(d.close.iloc[k+5]/o1-1)/sd
            call=dirn>0
            p0=bs(o1,o1,10/252,v,call)*1.05
            p1=bs(d.close.iloc[k+1],o1,9.75/252,v,call)*0.95; p5=bs(d.close.iloc[k+5],o1,5.75/252,v,call)*0.95
            rows.append({'sec':sec,'tk':s,'reg':L,'y26':j>=pd.Timestamp('2026-05-01'),'kind':'급락뒤콜' if dirn>0 else '급등뒤풋','gap':gapback,'oc':oc,'c5':c5,'o1':p1/p0-1,'o5':p5/p0-1})
df=pd.DataFrame(rows)
for kind in ['급락뒤콜','급등뒤풋']:
    g=df[df.kind==kind]
    print('\n===',kind,'(전날 ±2.5σ → 다음 날 시가에 2주 등가 옵션) ===')
    for name,gg in [('N',g[g.reg=='N']),('H',g[g.reg=='H']),('HH',g[g.reg=='HH']),('2026-05~',g[g.y26])]:
        if len(gg)<5: continue
        o5=gg.o5.sort_values(); tr=o5.iloc[:int(len(o5)*0.95)].mean()
        print(f'{name:9s} n{len(gg):4d} | 밤사이 되돌림 {gg.gap.mean():+.2f}σ | 다음날 시가→종가 {gg.oc.mean():+.2f}σ({(gg.oc>0).mean()*100:.0f}%) | 5일 {gg.c5.mean():+.2f}σ({(gg.c5>0).mean()*100:.0f}%) | 옵션 1일 {gg.o1.mean()*100:+.0f}% · 5일 {gg.o5.mean()*100:+.0f}%(상위5%빼면 {tr*100:+.0f}%) 이김 {(gg.o5>0).mean()*100:.0f}%')
    hh=g[g.reg=='HH']
    print('  HH 섹터별 옵션 5일 평균/이김/n:',{k:(round(x.o5.mean()*100),round((x.o5>0).mean()*100),len(x)) for k,x in hh.groupby('sec') if len(x)>=5})
# 빅테크 탄력성: 지금 변동성으로 당일 만기 0.5σ 외가 콜이 주가 +1%·+2%면 몇 %?
print('\n=== 빅테크 옵션 탄력성 (지금 20일 변동성, 당일 만기·남은 6시간, 0.5σ 외가 콜) ===')
for s in ['AAPL','MSFT','GOOGL','AMZN','META','TSLA','NVDA']:
    d=pd.read_csv(f'../data/daily/{s}.csv'); c=d.close.values; lr=np.diff(np.log(c[-21:])); sd=lr.std(); v=sd*sqrt(252)
    S=100; K=S*(1+0.5*sd); T=0.25/252; p=bs(S,K,T,v*1.2,True)
    out=[]
    for mv in (0.005,0.01,0.02):
        p2=bs(S*(1+mv),K,T*0.5,v*1.2,True); out.append(f'+{mv*100:.1f}%→{(p2/p-1)*100:+.0f}%')
    p0=bs(S,K,T*0.5,v*1.2,True)
    print(f'{s}: 하루σ {sd*100:.1f}% · IV가정 {v*1.2*100:.0f}% · 행사가 +{0.5*sd*100:.2f}% · 옵션값 주가의 {p/S*100:.2f}% | '+' '.join(out)+f' | 안 움직이면 3시간 뒤 {(p0/p-1)*100:+.0f}%')
