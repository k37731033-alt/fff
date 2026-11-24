# 장부 123-b: QQQ RSI<30 첫날 뒤 5일 — 표본 밖(1999-03~2006-12)
import json,glob,io,sys,numpy as np,pandas as pd
D=sys.argv[1]
def load(key):
    f=[x for x in glob.glob(D+'/*.txt') if key in x][0]
    return pd.read_csv(io.StringIO(json.load(open(f))['result']),sep=';',parse_dates=['datetime']).sort_values('datetime').reset_index(drop=True)
O=load('2b7f0u'); N=load('mqm2ey')
print('옛 구간',O.datetime.iloc[0].date(),'~',O.datetime.iloc[-1].date(),len(O))
A=pd.concat([O[O.datetime<N.datetime.iloc[0]],N]).reset_index(drop=True)
# 이음매 확인
j=A.index[A.datetime==N.datetime.iloc[0]][0]; print('이음매',A.datetime[j-1].date(),A.close[j-1],A.datetime[j].date(),A.close[j])
def rsi(c,n=14):
    d=c.diff();up=d.clip(lower=0).ewm(alpha=1/n,adjust=False).mean();dn=(-d.clip(upper=0)).ewm(alpha=1/n,adjust=False).mean();return 100-100/(1+up/dn)
A['rsi']=rsi(A.close); A['ma200']=A.close.rolling(200).mean()
for k in (1,5,10,20): A[f'f{k}']=A.close.shift(-k)/A.close-1
rng=np.random.default_rng(3)
def run(df,th=30,lab=''):
    ev=df.index[(df.rsi<th)&(df.rsi.shift(1)>=th)]; kp=[];last=-99
    for k in ev:
        if k-last>=20: kp.append(k);last=k
    for h in (5,20):
        x=df.loc[kp,f'f{h}'].dropna(); b=df[f'f{h}'].dropna()
        d=rng.choice(x.values,(5000,len(x))).mean(1)-rng.choice(b.values,(5000,len(b))).mean(1)
        print(f'{lab} RSI<{th} 뒤 {h}일: n={len(x)} 평균 {x.mean()*100:+.2f}% 중간 {x.median()*100:+.2f}% 오름 {(x>0).mean()*100:.0f}% 최악 {x.min()*100:+.1f}% | 아무 {h}일 {b.mean()*100:+.2f}% 차이 {(x.mean()-b.mean())*100:+.2f}%p 범위 {np.percentile(d,5)*100:+.2f}~{np.percentile(d,95)*100:+.2f} | 좋은2 빼면 {x.sort_values().iloc[:-2].mean()*100:+.2f}%')
    return kp
old=A[(A.datetime>='1999-03-01')&(A.datetime<'2007-01-01')].copy()
kp=run(old,30,'[표본 밖 1999~2006]'); print(' 사건:',[(str(old.datetime[k].date()),round(old.f5[k]*100,1)) for k in kp])
run(old,25,'[표본 밖 1999~2006]')
b=[k for k in kp if old.close[k]<old.ma200[k]]; x=old.loc[b,'f5']; print(' 200일선 아래만: n',len(x),'평균 %.2f%% 오름 %.0f%%'%(x.mean()*100,(x>0).mean()*100))
allp=run(A,30,'[전체 1999~2026]')
# 5일 안 최저(종가 대비)·저점까지
new=A[A.datetime>='2007-01-01']
x=[A.low[k+1:k+6].min()/A.close[k]-1 for k in allp if k+5<len(A)]; print('전체 사건: 5일 안 최저 평균 %.1f%% 중간 %.1f%% · -3%% 넘게 더 빠진 비율 %.0f%%'%(np.mean(x)*100,np.median(x)*100,(np.array(x)<-0.03).mean()*100))
# 200일선 아래/위 (전체)
for nm,cond in (('200일선 아래',lambda k:A.close[k]<A.ma200[k]),('200일선 위',lambda k:A.close[k]>=A.ma200[k])):
    kk=[k for k in allp if k+5<len(A) and not np.isnan(A.ma200[k]) and cond(k)]; x=A.loc[kk,'f5']; print(f' 전체·{nm}: n {len(x)} 5일 {x.mean()*100:+.2f}% 오름 {(x>0).mean()*100:.0f}% 최악 {x.min()*100:+.1f}%')
print('지금 QQQ RSI',round(A.rsi.iloc[-1],1),'· RSI 30이 되려면 필요한 하루 종가 대략:')
c=A.close.copy()
for drop in (0.03,0.05,0.07,0.09):
    c2=pd.concat([c,pd.Series([c.iloc[-1]*(1-drop)])],ignore_index=True); print('  하루 -%d%% → RSI %.1f'%(drop*100,rsi(c2).iloc[-1]))
