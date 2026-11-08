import pandas as pd, numpy as np
df=pd.read_pickle('t52.pkl')
df=df.replace([np.inf,-np.inf],np.nan)
order=['N','H','HH']
def cell(g,col):
    x=g[col].dropna()
    if len(x)<5: return f'n{len(x)}'
    if col=='x':
        x=x.clip(-8,8); return f'{x.mean():+.2f}σ·{(x>0).mean()*100:.0f}%·n{len(x)}'
    xs=x.sort_values(); xt=xs.iloc[:max(1,int(len(xs)*0.95))]   # 가장 좋은 5% 빼고 평균(몇 번의 대박에 덜 끌리게)
    return f'평균{x.mean()*100:+.0f}%/상위5%빼면{xt.mean()*100:+.0f}% · 이김{(x>0).mean()*100:.0f}% · 2배↑{(x>=1).mean()*100:.0f}% · n{len(x)}'
def table(t,col,by='sec'):
    g=df[df.t==t]
    out={}
    for k,gg in g.groupby(by):
        row={r:cell(gg[gg.reg==r],col) for r in order}
        row['2026-05~']=cell(gg[gg.y26],col)
        out[k]=row
    allrow={r:cell(g[g.reg==r],col) for r in order}; allrow['2026-05~']=cell(g[g.y26],col)
    out['▶ 전체']=allrow
    return pd.DataFrame(out).T[order+['2026-05~']]
pd.set_option('display.width',250); pd.set_option('display.max_colwidth',60)
for t,col,title in [
 ('A_gap_down','x','A 아래 갭(1.5σ+) → 시가→종가 더 빠짐(+면 계속 하락)'),
 ('A_gap_down','opt','A 아래 갭 → 시가에 당일 만기 0.5σ 외가 풋'),
 ('A_gap_up','x','A 위 갭 → 시가→종가 더 오름'),
 ('A_gap_up','opt','A 위 갭 → 시가에 당일 만기 0.5σ 외가 콜'),
 ('B_chase_after_down','x','B 전날 −2σ → 오늘 또 빠짐(+면 추격 성공)'),
 ('B_chase_after_up','x','B 전날 +2σ → 오늘 또 오름(+면 추격 성공)'),
 ('C_D_rebound','opt','C D 반등 2주 등가 콜(5거래일)'),
 ('D_call_uptrend','opt','D 상승추세 아무 날 콜(0.5σ 외가, 3일 만기, 당일 종가)'),
 ('D_put_uptrend','opt','D 상승추세 아무 날 풋'),
 ('E_after_crash_d1','x','E −2.5σ 급락 다음 날'),
 ('E_after_crash_d5','x','E −2.5σ 급락 5일 뒤'),
 ('F_0dte_both','opt','F 당일 만기 콜+풋 양쪽(0.5σ 외가) 시가→만기'),
]:
    print('\n=== '+title+' ==='); print(table(t,col).to_string())
