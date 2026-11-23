# 116번 — DELL 실적 밤 양쪽(발표일 마지막 체결가 → 다음 날 첫 체결가, Massive 옵션 일봉). 비용: 왕복 8%(살 때 +4%, 팔 때 −4%) + 수수료 1.99달러×2(계약당)
import pandas as pd, numpy as np
d = pd.read_csv('h116_dell_rows.csv'); rng = np.random.default_rng(116)
def net(b, s): return ((s*0.96*100 - 1.99) - (b*1.04*100 + 1.99)) / (b*1.04*100 + 1.99)
d['call'] = net(d.call_buy, d.call_sell); d['put'] = net(d.put_buy, d.put_sell)
cost = (d.call_buy + d.put_buy)*1.04*100 + 3.98; proceeds = (d.call_sell + d.put_sell)*0.96*100 - 3.98
d['both'] = proceeds/cost - 1; d['price_pct'] = (d.call_buy + d.put_buy)/d.S_close; d['absgap'] = d.gap.abs()
print(d[['earn_date','price_pct','absgap','call','put','both']].round(3).to_string())
for c in ('both','call','put'):
    x = d[c].values; m = rng.choice(x,(5000,len(x))).mean(1)
    print(f'{c}: 평균 {x.mean():+.1%} 중간 {np.median(x):+.1%} 이김 {(x>0).sum()}/{len(x)} 최악 {x.min():+.0%} 90% {np.percentile(m,5):+.0%}~{np.percentile(m,95):+.0%} 위2개 뺌 {np.sort(x)[:-2].mean():+.1%} 최근3번 {x[-3:].mean():+.1%}')
print(f'값÷주가 중간 {d.price_pct.median():.1%} 평균 {d.price_pct.mean():.1%} / 실제 갭 중간 {d.absgap.median():.1%} 평균 {d.absgap.mean():.1%} / 갭이 값을 넘은 밤 {(d.absgap>d.price_pct).sum()}/8')
