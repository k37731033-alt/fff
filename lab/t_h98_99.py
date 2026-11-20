# 56 장부 98·99번 (11/20 가설 연구원). 자료: FRED DGS10·NASDAQ100·NASDAQSOX·DFEDTAR·DFEDTARU CSV (curl -L "https://fred.stlouisfed.org/graph/fredgraph.csv?id=코드" -o 코드.csv)
import pandas as pd, numpy as np
rng=np.random.default_rng(0)
def load(s):
    d=pd.read_csv(s+'.csv'); d.columns=['date','v']; d['v']=pd.to_numeric(d.v,errors='coerce')
    return d.dropna().set_index(pd.to_datetime(d.dropna().date)).v
y=load('DGS10'); ndx=load('NASDAQ100'); sox=load('NASDAQSOX')
ft=pd.concat([load('DFEDTAR'),load('DFEDTARU')]).sort_index(); ft=ft[~ft.index.duplicated(keep='last')]
def boot(x,n=5000):
    x=np.asarray(x); m=[rng.choice(x,len(x)).mean() for _ in range(n)]; return np.percentile(m,[5,95])
def fwd(px,h): return px.shift(-h)/px-1
def summarize(name,px,dates,h,base=None):
    f=fwd(px,h)*100; ev=f.reindex(dates).dropna()
    allf=f.dropna() if base is None else base
    lo,hi=boot(ev.values); diff=ev.values[:,None]
    # diff CI: bootstrap ev mean minus base mean
    bm=[rng.choice(ev.values,len(ev)).mean()-rng.choice(allf.values,len(ev)*4).mean() for _ in range(3000)]
    k=int(len(ev)*0.7); rec=ev.iloc[k:]
    srt=np.sort(ev.values)
    print(f"{name} h{h}: n={len(ev)} mean {ev.mean():+.2f} med {ev.median():+.2f} up {100*(ev>0).mean():.0f}% worst {ev.min():+.1f} CI[{lo:+.2f},{hi:+.2f}] | base {allf.mean():+.2f} (up {100*(allf>0).mean():.0f}%) diff {ev.mean()-allf.mean():+.2f} CI[{np.percentile(bm,5):+.2f},{np.percentile(bm,95):+.2f}] | recent30% n={len(rec)} {rec.mean():+.2f} | drop-best2 {srt[:-2].mean():+.2f}")
    return ev
def thin(dates,gap):
    out=[];last=None
    idx=list(dates)
    for d in idx:
        if last is None or (d-last).days>gap*1.45: out.append(d); last=d
    return pd.DatetimeIndex(out)
print("=== H98: 10y >= 5% ===")
for px,nm in [(ndx,'NDX'),(sox,'SOX')]:
    yy=y.reindex(px.index).ffill()
    hi=yy[yy>=5.0].index; lo=yy[yy<5.0].index
    print(nm,'days >=5%:',len(hi), 'first',hi.min().date() if len(hi) else None,'last',hi.max().date() if len(hi) else None)
    f=fwd(px,20)*100
    base=f.reindex(lo).dropna()
    ev=summarize(nm+' 10y>=5 (thin20)',px,thin(hi,20),20,base)
    print('   by year blocks:', f.reindex(thin(hi,20)).dropna().groupby(lambda d:d.year).mean().round(2).to_dict())
    summarize(nm+' 10y>=5 (thin20) h60',px,thin(hi,60),60,(fwd(px,60)*100).reindex(lo).dropna())
print("=== H98b: 10y first 252d high (cooldown 20) ===")
roll=y.rolling(252).max()
newhi=y[(y>=roll)&(y.shift(1)<roll.shift(1))].index
for px,nm in [(ndx,'NDX'),(sox,'SOX')]:
    d=[x for x in newhi if x>=px.index[0]]
    d=pd.DatetimeIndex([px.index[px.index.searchsorted(x)] for x in d if px.index.searchsorted(x)<len(px)])
    d=thin(d,20)
    for h in (20,60): summarize(nm+' 10y new 1y high',px,d,h)
print("=== H99: Fed hikes ===")
ch=ft.diff(); hikes=ch[ch>0].index
hikes=hikes[hikes>='1986-06-01']
first=[d for d in hikes if ((hikes<d)&(hikes>=d-pd.Timedelta(days=365))).sum()==0]
print('hikes',len(hikes),'first-of-cycle',[str(x.date()) for x in first])
for px,nm in [(ndx,'NDX'),(sox,'SOX')]:
    hd=pd.DatetimeIndex([px.index[px.index.searchsorted(x)] for x in hikes if x>=px.index[0] and px.index.searchsorted(x)<len(px)])
    fd=pd.DatetimeIndex([px.index[px.index.searchsorted(x)] for x in first if x>=px.index[0] and px.index.searchsorted(x)<len(px)])
    for h in (20,60):
        summarize(nm+' all hikes',px,hd,h)
        e=summarize(nm+' first hikes',px,fd,h)
        if h==20: print('   first-hike rows', e.round(1).to_dict())
    hd2=hd[hd>='2000-01-01']; summarize(nm+' hikes 2000+',px,hd2,20)
