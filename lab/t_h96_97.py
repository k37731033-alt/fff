# 56 장부 96·97번 (2026-11-19 가설 연구원)
# 96: 월물 만기(셋째 금요일) 다음 주는 더 크게 움직이나  /  97: 초대형 상장 첫 거래일 전후 지수
# 자료: FRED NASDAQ100(1986~)·NASDAQSOX(2004~) 일별 종가 (lab/fred_20261118/)
import pandas as pd, numpy as np, datetime as dt
rng=np.random.default_rng(20261119)
def load(n):
    s=pd.read_csv(f'fred_20261118/{n}.csv',parse_dates=['observation_date']).set_index('observation_date')[n]
    return pd.to_numeric(s,errors='coerce').dropna()
ndx,sox=load('NASDAQ100'),load('NASDAQSOX')
print('자료 끝:',ndx.index[-1].date(),sox.index[-1].date(),'시작:',ndx.index[0].date(),sox.index[0].date())
def boot_diff(a,b,n=10000,f=np.mean):
    a,b=np.asarray(a),np.asarray(b)
    d=[f(rng.choice(a,len(a)))-f(rng.choice(b,len(b))) for _ in range(n)]
    return np.percentile(d,[5,95])
def boot_mean(a,n=10000):
    a=np.asarray(a); return np.percentile([rng.choice(a,len(a)).mean() for _ in range(n)],[5,95])

print('\n===== 96번: 만기 다음 주 =====')
def third_friday(y,m):
    d=dt.date(y,m,1); d+=dt.timedelta((4-d.weekday())%7); return d+dt.timedelta(14)
def weekly(s):
    w=s.resample('W-FRI').last().dropna(); r=w.pct_change().dropna()*100
    return r
def run96(s,name,start=None):
    r=weekly(s)
    if start: r=r[r.index>=start]
    tf={pd.Timestamp(third_friday(y,m)) for y in range(1986,2027) for m in range(1,13)}
    is_opex=r.index.isin(tf)
    post=np.roll(is_opex,1); post[0]=False
    A=r[post]; B=r[~post]
    lo,hi=boot_diff(A.abs(),B.abs()); lo2,hi2=boot_diff(A,B)
    k=int(len(A)*0.7); Ar=A.iloc[k:]; 
    print(f'{name} 만기 다음 주 {len(A)}주: |수익| 평균 {A.abs().mean():.2f}% vs 다른 주 {B.abs().mean():.2f}% (차이 {A.abs().mean()-B.abs().mean():+.2f}%p, 90% {lo:+.2f}~{hi:+.2f}) · 중간값 {A.abs().median():.2f} vs {B.abs().median():.2f}')
    print(f'   방향: 평균 {A.mean():+.2f}% vs {B.mean():+.2f}% (차이 {A.mean()-B.mean():+.2f}%p, 90% {lo2:+.2f}~{hi2:+.2f}) · 오른 주 {100*(A>0).mean():.0f}% vs {100*(B>0).mean():.0f}% · 최악 {A.min():.1f}%')
    print(f'   최근 30%({len(Ar)}주): |수익| {Ar.abs().mean():.2f}% · 방향 {Ar.mean():+.2f}%')
    # 만기 주 자체, 만기 주가 내린 경우의 다음 주
    O=r[is_opex]; print(f'   참고 만기 주 자체 {len(O)}주: |수익| {O.abs().mean():.2f}% · 방향 {O.mean():+.2f}%')
    prev=r.shift(1); C=r[post&(prev<0).values]; D=r[post&(prev>=0).values]
    lo3,hi3=boot_diff(C,B)
    print(f'   만기 주가 내린 뒤 다음 주 {len(C)}주: {C.mean():+.2f}%·오른 주 {100*(C>0).mean():.0f}% (다른 주 대비 90% {lo3:+.2f}~{hi3:+.2f}) / 오른 뒤 {len(D)}주: {D.mean():+.2f}%')
    # 큰 2개 빼기(방향)
    A2=A.sort_values().iloc[:-2]; print(f'   가장 좋은 2주 뺀 방향 평균 {A2.mean():+.2f}%')
    return A
run96(sox,'SOX 2004~'); run96(ndx,'나스닥100 1986~'); run96(sox,'SOX 2020~','2020-01-01'); run96(ndx,'나스닥100 2020~','2020-01-01')
# 11월만(= 추수감사절 주와 겹침)
r=weekly(sox); tf={pd.Timestamp(third_friday(y,11)) for y in range(2004,2026)}; post=np.roll(r.index.isin(tf),1)
print('SOX 11월 만기 다음 주(=대부분 추수감사절 주)',int(post.sum()),'번 평균',round(r[post].mean(),2),'|수익|',round(r[post].abs().mean(),2))

print('\n===== 97번: 초대형 상장 =====')
# 르네상스 캐피털 'Largest US IPOs'(2026-11-19 확인): 공모가 확정일, 규모(십억 달러, 초과배정 제외)
ipos=[('SpaceX','2026-06-11',75.00),('SK hynix','2026-07-09',26.51),('Alibaba','2014-09-18',21.77),('Visa','2008-03-18',17.86),
('ENEL','1999-11-01',16.45),('Facebook','2012-05-17',16.01),('General Motors','2010-11-17',15.77),('Deutsche Telekom','1996-11-17',13.03),
('Rivian','2021-11-09',11.93),('AT&T Wireless','2000-04-26',10.62),('Kraft Foods','2001-06-12',8.68),('Uber','2019-05-09',8.10),
('France Telecom','1997-10-17',7.29),('Medline','2025-12-16',6.27),('Telstra','1997-11-17',5.65),('Swisscom','1998-10-04',5.58),
('Cerebras','2026-05-13',5.55),('UPS','1999-11-09',5.47),('Infineon','2000-03-12',5.23),('China Unicom','2000-06-16',4.92),
('Arm','2023-09-13',4.87),('CIT Group','2002-07-01',4.60),('Coupang','2021-03-10',4.55),('Lineage','2024-07-24',4.44),('DiDi','2021-06-29',4.44)]
def run97(s,name,minsize=0,show=False):
    idx=s.index; rows=[]
    for nm,d,sz in ipos:
        if sz<minsize: continue
        p=idx.searchsorted(pd.Timestamp(d),side='right')   # 공모가 확정일 다음 거래일 = 첫 거래일
        if p<6 or p+20>=len(idx) or pd.Timestamp(d)<idx[5]: 
            if p+5<len(idx) and p>=6: pass
            else: continue
        g=lambda a,b:(s.iloc[b]/s.iloc[a]-1)*100 if b<len(idx) else np.nan
        rows.append(dict(name=nm,first=idx[p].date(),size=sz,pre5=g(p-6,p-1),day=g(p-1,p),post5=g(p,p+5),post20=g(p,p+20)))
    E=pd.DataFrame(rows)
    base={ 'pre5':s.pct_change(5).dropna()*100,'day':s.pct_change().dropna()*100,'post5':s.pct_change(5).dropna()*100,'post20':s.pct_change(20).dropna()*100}
    if minsize==0 and name.startswith('SOX'): base={k:v for k,v in base.items()}
    print(f'--- {name} (규모 ≥ {minsize}십억 달러) {len(E)}건')
    for k,lab in [('pre5','앞 5일'),('day','첫 거래일'),('post5','뒤 5일'),('post20','뒤 20일')]:
        a=E[k].dropna(); b=base[k]
        b=b[b.index>=pd.Timestamp(E['first'].min())-pd.Timedelta(days=400)]
        lo,hi=boot_diff(a,b,5000)
        a2=a.sort_values().iloc[2:]  # 가설이 '낮다'이므로 가장 나쁜 2건을 뺌
        print(f'  {lab}: 평균 {a.mean():+.2f}% · 중간값 {a.median():+.2f}% · 오른 비율 {100*(a>0).mean():.0f}% · 최악 {a.min():+.1f}% ({len(a)}건) | 아무 날 {b.mean():+.2f}%·{100*(b>0).mean():.0f}% | 차이 {a.mean()-b.mean():+.2f}%p (90% {lo:+.2f}~{hi:+.2f}) | 가장 나쁜 2건 빼면 {a2.mean():+.2f}%')
    k=int(len(E)*0.7); Es=E.sort_values('first'); R=Es.iloc[k:]
    print(f'  최근 30%({len(R)}건, {R["first"].min()}~): 첫날 {R["day"].mean():+.2f}% · 뒤 5일 {R["post5"].mean():+.2f}% · 뒤 20일 {R["post20"].mean():+.2f}%')
    if show: print(Es.round(2).to_string(index=False))
    return E
E1=run97(ndx,'나스닥100',0,True); E2=run97(sox,'SOX',0,True); run97(ndx,'나스닥100',10); run97(sox,'SOX',10)
E1.to_csv('h97_rows_ndx.csv',index=False); E2.to_csv('h97_rows_sox.csv',index=False)
