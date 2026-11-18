# 56 장부 83번 — 자기 실적 밤 양쪽(실제 옵션): 기존 39밤(self_earn_rows.csv) + 새 37밤(h83_rows.csv)
import pandas as pd, numpy as np
rng=np.random.default_rng(7)
def boot(x,n=5000):
    x=np.asarray(x,float); m=rng.choice(x,(n,len(x))).mean(1); return np.percentile(m,5),np.percentile(m,95)
def net(buy,sell,cost): # 1계약, 왕복 호가 비용 cost + 수수료 1.99달러×(다리 수×2)
    legs=buy.shape[1]; b=buy.sum(1); s=sell.sum(1)
    return (s*(1-cost)*100-1.99*2*legs)/(b*100)-1
def line(nm,r):
    r=np.asarray(r,float)
    if len(r)==0: print(nm,'n=0'); return
    lo,hi=boot(r) if len(r)>2 else (np.nan,np.nan)
    ex=np.sort(r)[:-2].mean() if len(r)>4 else np.nan
    print(f"{nm}: n={len(r)} mean={r.mean()*100:+.1f}% med={np.median(r)*100:+.1f}% win={np.mean(r>0)*100:.0f}% worst={r.min()*100:+.0f}% CI90=[{lo*100:+.1f},{hi*100:+.1f}] ex-top2={ex*100:+.1f}%")
new=pd.read_csv('h83_rows.csv'); new=new[~new.note.fillna('').str.contains('EXTRA')]
print('사전 등록 40밤 중 옵션 값 있는 밤:',new.call_c_D.notna().sum())
new=new[new.call_c_D.notna()&new.put_o_D1.notna()].copy()
new['prev']=new.prior_gaps.apply(lambda s: np.mean([abs(float(x)) for x in str(s).split(';')][:8])/100)
new['ag']=(new.S_open_D1/new.S_close_D-1).abs(); new['gap']=new.S_open_D1/new.S_close_D-1
N=pd.DataFrame(dict(t=new.ticker,eve=new.D,cC=new.call_c_D,cP=new.put_c_D,oC=new.call_o_D1,oP=new.put_o_D1,imp=(new.call_c_D+new.put_c_D)/new.S_close_D,ag=new.ag,gap=new.gap,prev=new.prev,src='new',note=new.note.fillna('')))
old=pd.read_csv('self_earn_rows.csv')
O=pd.DataFrame(dict(t=old.t,eve=old.eve,cC=old.c1C,cP=old.c1P,oC=old.o2C,oP=old.o2P,imp=old.imp,ag=old.ag,gap=np.nan,prev=old.prev,src='old',note=''))
A=pd.concat([O,N],ignore_index=True); A['ratio']=A.imp/A.prev; A=A.sort_values('eve').reset_index(drop=True)
for cost,lab in ((0.08,'비용 8%+수수료'),(0.05,'옛 5%+수수료')):
    A['st']=net(A[['cC','cP']].values,A[['oC','oP']].values,cost); A['rc']=net(A[['cC']].values,A[['oC']].values,cost); A['rp']=net(A[['cP']].values,A[['oP']].values,cost)
    print('\n#####',lab)
    for nm,D in (('새 37밤',A[A.src=='new']),('기존 39밤',A[A.src=='old']),('합계',A)):
        line(nm+' 양쪽',D.st); 
    line('합계 콜만',A.rc); line('합계 풋만',A.rp)
    if cost==0.08:
        k=int(round(len(A)*0.3)); line(f'합계 최근 30%({A.eve.iloc[-k]}~) 양쪽',A.st.iloc[-k:])
        R=A[A.ratio.notna()]
        print('값÷직전 갭 평균 비율을 아는 밤:',len(R),' 값(양쪽÷주가) 중간',round(A.imp.median()*100,1),'% 실제 갭 크기 중간',round(A.ag.median()*100,1),'%  갭>값인 밤',int((A.ag>A.imp).sum()),'/',len(A))
        for lo,hi in ((0,0.8),(0.8,1.0),(1.0,1.5),(1.5,99)): line(f' 비율 {lo}~{hi} 양쪽',R[(R.ratio>lo)&(R.ratio<=hi)].st)
        line(' 비율 ≤1.0 양쪽',R[R.ratio<=1.0].st); line(' 비율 >1.0 양쪽',R[R.ratio>1.0].st)
        print(R[R.ratio<=0.8][['t','eve','imp','prev','ratio','ag','st','src']].round(3).to_string())
        cl=A[(A.src=='old')|(~A.note.str.contains('timing check|preliminary'))]
        line('민감도: 시각 의심·예비 실적 8밤 뺀 합계 양쪽',cl.st); line('민감도: 새 밤 중 1일물만',A[(A.src=='new')&A.note.str.contains('1-day')].st); line('민감도: 새 밤 중 2일물 이상',A[(A.src=='new')&~A.note.str.contains('1-day')].st)
        nn=A[A.src=='new']; print('새 37밤: 갭 크기 평균',round(nn.ag.mean()*100,1),'% 중간',round(nn.ag.median()*100,1),'% / 값 중간',round(nn.imp.median()*100,1),'% / 갭 위로',int((nn.gap>0).sum()),'아래로',int((nn.gap<0).sum()))
        line('새 37밤 콜',nn.rc); line('새 37밤 풋',nn.rp)
        print(nn.sort_values('st')[['t','eve','imp','ag','st']].round(3).tail(6).to_string())
A.to_csv('h83_all_rows.csv',index=False)
