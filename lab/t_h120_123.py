# 장부 120~123번 (2026-11-24 가설 연구원) — Twelve Data 일봉(분할 조정) SOXX·QQQ·USD 2007~, SOXL 2010~
import json,glob,io,sys
import numpy as np, pandas as pd
D=sys.argv[1] if len(sys.argv)>1 else '.'
rng=np.random.default_rng(7)
def load(key):
    f=[x for x in glob.glob(D+'/mcp-Twelve_Data-get_time_series-*.txt') if key in x][0]
    df=pd.read_csv(io.StringIO(json.load(open(f))['result']),sep=';',parse_dates=['datetime']).sort_values('datetime').set_index('datetime')
    return df
S=load('yxsq7v'); Q=load('mqm2ey'); L=load('i7y185'); U=load('2ycewc')
def boot(x,n=5000):
    x=np.asarray(x,float); x=x[~np.isnan(x)]
    if len(x)<3: return (np.nan,np.nan)
    m=rng.choice(x,(n,len(x))).mean(1); return np.percentile(m,[5,95])
def bootdiff(a,b,n=3000):
    a=np.asarray(a,float);a=a[~np.isnan(a)];b=np.asarray(b,float);b=b[~np.isnan(b)]
    d=rng.choice(a,(n,len(a))).mean(1)-rng.choice(b,(n,len(b))).mean(1); return np.percentile(d,[5,95])
def desc(name,x,base=None):
    x=pd.Series(x).dropna()
    if len(x)==0: print(name,'n=0'); return
    lo,hi=boot(x); s=f"{name}: n={len(x)} 평균 {x.mean()*100:+.2f}% 중간 {x.median()*100:+.2f}% 오름 {(x>0).mean()*100:.0f}% 최악 {x.min()*100:+.1f}% 범위 {lo*100:+.2f}~{hi*100:+.2f}"
    k=int(np.ceil(len(x)*0.3)); s+=f" | 최근30%({k}) {x.iloc[-k:].mean()*100:+.2f}%"
    if len(x)>4: s+=f" | 좋은2 빼면 {x.sort_values().iloc[:-2].mean()*100:+.2f}%"
    if base is not None:
        b=pd.Series(base).dropna(); dl,dh=bootdiff(x,b); s+=f" | 아무 날 {b.mean()*100:+.2f}% 차이 {(x.mean()-b.mean())*100:+.2f}%p 범위 {dl*100:+.2f}~{dh*100:+.2f}"
    print(s)
def fwd(df,k): return df['close'].shift(-k)/df['close']-1
def dedup(idx,allidx,gap):
    out=[];last=-10**9
    pos={d:i for i,d in enumerate(allidx)}
    for d in idx:
        if pos[d]-last>=gap: out.append(d); last=pos[d]
    return out
for df in (S,Q,L,U):
    df['ret']=df['close'].pct_change(); df['ma200']=df['close'].rolling(200).mean(); df['ma50']=df['close'].rolling(50).mean()
    df['gapn']=df['open'].shift(-1)/df['close']-1          # 다음 날 밤사이 갭
    df['o2cn']=df['close'].shift(-1)/df['open'].shift(-1)-1 # 다음 날 시가→종가
    for k in (1,5,10,20,60): df[f'f{k}']=fwd(df,k)
print('자료 끝',S.index[-1].date(),'SOXX 시작',S.index[0].date(),'SOXL',L.index[0].date(),'USD',U.index[0].date())
print('\n===== 120: SOXX 급등 날 뒤 =====')
for th in (0.05,0.06,0.08):
    ev=S.index[S['ret']>=th]
    ev=[d for d in ev if d<S.index[-1]]
    print(f'--- 문턱 +{th*100:.0f}% 사건 {len(ev)}번 (독립: 5일 안 중복 제외 {len(dedup(ev,list(S.index),5))}번)')
    for col,nm in (('f1','다음날 종→종'),('gapn','다음날 밤사이 갭'),('o2cn','다음날 시→종'),('f5','5일'),('f20','20일')):
        desc(f'  SOXX {nm}',S.loc[ev,col],S[col])
    if th==0.06:
        print('  사건 날짜:',[str(d.date()) for d in ev])
        b=[d for d in ev if S.loc[d,'close']<S.loc[d,'ma200']]
        desc('  [200일선 아래] 다음날 종→종',S.loc[b,'f1'],S['f1']); desc('  [200일선 아래] 밤사이 갭',S.loc[b,'gapn'],S['gapn']); desc('  [200일선 아래] 20일',S.loc[b,'f20'],S['f20'])
        for nm,X in (('USD',U),('SOXL',L)):
            e2=[d for d in ev if d in X.index]
            desc(f'  {nm} 다음날 종→종',X.loc[e2,'f1'],X['f1']); desc(f'  {nm} 5일',X.loc[e2,'f5'],X['f5']); desc(f'  {nm} 20일',X.loc[e2,'f20'],X['f20'])
        # 20일 안 최저(종가 대비)
        mn=[S['low'].iloc[S.index.get_loc(d)+1:S.index.get_loc(d)+21].min()/S.loc[d,'close']-1 for d in ev if S.index.get_loc(d)+20<len(S)]
        print('  20일 안 최저(급등 날 종가 대비) 평균 %.1f%% 중간 %.1f%%'%(np.mean(mn)*100,np.median(mn)*100))
# 70 문서 9절 B 재현: +8%
ev8=[d for d in S.index[S['ret']>=0.08] if d<S.index[-1]]
print('  +8% 날짜:',[str(d.date()) for d in ev8])
print('\n===== 121: 확인 신호(200일선 아래 +1.5% & 거래량 증가) =====')
def test121(df,nm,th,volrule,ks=(5,20,60)):
    below=df['close']<df['ma200']
    if volrule=='prev': v=df['volume']>df['volume'].shift(1)
    else: v=df['volume']>df['volume'].rolling(50).mean().shift(1)
    sig=df.index[below&(df['ret']>=th)&v]
    sig=dedup(list(sig),list(df.index),10)
    for k in ks:
        desc(f'  {nm} +{th*100:.1f}% vol>{volrule} 뒤 {k}일',df.loc[sig,f'f{k}'],df.loc[below,f'f{k}'])
    return sig
sig=test121(S,'SOXX',0.015,'prev')
print('  (참고) 200일선 아래 +1.5% 이상인데 거래량이 전날보다 적은 날:')
below=S['close']<S['ma200']; nv=dedup(list(S.index[below&(S['ret']>=0.015)&(S['volume']<=S['volume'].shift(1))]),list(S.index),10)
desc('   SOXX 뒤 20일',S.loc[nv,'f20'],S.loc[below,'f20'])
for th in (0.02,0.03): test121(S,'SOXX',th,'prev',(20,))
test121(S,'SOXX',0.015,'ma50',(20,)); test121(Q,'QQQ',0.015,'prev',(20,60))
# IBD식: 저점(20일 최저 종가) 뒤 4~10일째에 +1.5% & 거래량 증가
lowday=S['close']==S['close'].rolling(20).min()
since=pd.Series(np.nan,index=S.index); c=np.nan
for i,d in enumerate(S.index):
    if lowday.iloc[i]: c=0
    elif not np.isnan(c): c+=1
    since.iloc[i]=c
ibd=dedup(list(S.index[below&(S['ret']>=0.015)&(S['volume']>S['volume'].shift(1))&(since>=4)&(since<=10)]),list(S.index),10)
desc('  SOXX IBD식(저점 뒤 4~10일째) 뒤 20일',S.loc[ibd,'f20'],S.loc[below,'f20'])
print('  가장 최근 신호 5개:',[str(d.date()) for d in sig[-5:]], '| 11/23은 신호인가:',S.index[-1] in set(S.index[below&(S['ret']>=0.015)&(S['volume']>S['volume'].shift(1))]), ' 11/23 거래량',S['volume'].iloc[-1],'11/20',S['volume'].iloc[-2])
print('\n===== 122: 200일선 아래에서 산 2배·3배의 감가 =====')
J=pd.DataFrame({'s':S['close'],'u':U['close'],'l':L['close'],'ma200':S['ma200']}).dropna()
J['vol20']=J['s'].pct_change().rolling(20).std()*np.sqrt(252)
for k in (60,20):
    R=pd.DataFrame({'s':J['s'].shift(-k)/J['s']-1,'u':J['u'].shift(-k)/J['u']-1,'l':J['l'].shift(-k)/J['l']-1,'below':J['s']<J['ma200'],'vol':J['vol20']}).dropna()
    R['gapL']=R['l']-3*R['s']; R['gapU']=R['u']-2*R['s']
    Rk=R.iloc[::k]  # 겹치지 않게
    b=Rk[Rk.below]; a=Rk[~Rk.below]
    print(f'--- {k}일 (겹치지 않는 시작일: 아래 {len(b)} · 위 {len(a)})')
    desc('  [아래] SOXL−3×SOXX',b.gapL,a.gapL); desc('  [위]   SOXL−3×SOXX',a.gapL)
    desc('  [아래] USD−2×SOXX',b.gapU,a.gapU); desc('  [위]   USD−2×SOXX',a.gapU)
    desc('  [아래] SOXX',b.s); desc('  [아래] USD',b.u); desc('  [아래] SOXL',b.l)
    desc('  [위] SOXX',a.s); desc('  [위] USD',a.u); desc('  [위] SOXL',a.l)
    hv=Rk[Rk.vol>=R.vol.quantile(2/3)]; desc('  [변동성 상위1/3] SOXL−3×SOXX',hv.gapL); desc('  [변동성 상위1/3] USD−2×SOXX',hv.gapU)
    # 모든 날(겹침) 기준 이긴 비율
    Rb=R[R.below]
    print('  [아래·모든 날] USD>SOXL 비율 %.0f%% · SOXL<0 비율 %.0f%% · SOXX<0 비율 %.0f%% · SOXX>0인데 SOXL<0 비율 %.0f%%'%((Rb.u>Rb.l).mean()*100,(Rb.l<0).mean()*100,(Rb.s<0).mean()*100,((Rb.s>0)&(Rb.l<0)).mean()*100))
# 6월 고점~11/20
for a_,b_ in (('2026-06-25','2026-11-20'),('2025-11-21','2026-11-20')):
    try:
        x=J.loc[a_:b_]; print(f'  {a_}→{b_}: SOXX {x.s.iloc[-1]/x.s.iloc[0]-1:+.0%} USD {x.u.iloc[-1]/x.u.iloc[0]-1:+.0%} SOXL {x.l.iloc[-1]/x.l.iloc[0]-1:+.0%}')
    except Exception as e: print(e)
print('\n===== 123: RSI 30 아래 첫날 =====')
def rsi(c,n=14):
    d=c.diff(); up=d.clip(lower=0).ewm(alpha=1/n,adjust=False).mean(); dn=(-d.clip(upper=0)).ewm(alpha=1/n,adjust=False).mean(); return 100-100/(1+up/dn)
for nm,df in (('QQQ',Q),('SOXX',S)):
    df['rsi']=rsi(df['close'])
    print(nm,'지금 RSI',round(df['rsi'].iloc[-1],1),'11/20 RSI',round(df['rsi'].iloc[-2],1),'최근 최저',round(df['rsi'].iloc[-30:].min(),1))
    for th in (30,25):
        ev=df.index[(df['rsi']<th)&(df['rsi'].shift(1)>=th)]; ev=dedup(list(ev),list(df.index),20)
        for k in (5,20,60): desc(f'  {nm} RSI<{th} 뒤 {k}일',df.loc[ev,f'f{k}'],df[f'f{k}'])
        if th==30:
            b=[d for d in ev if df.loc[d,'close']<df.loc[d,'ma200']]; desc(f'  {nm} RSI<30 & 200일선 아래 뒤 20일',df.loc[b,'f20'],df['f20'])
            print('   최근 사건:',[str(d.date()) for d in ev[-6:]])
