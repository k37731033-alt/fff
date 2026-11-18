import glob,os,re,csv,datetime as dt,json
f="/root/.claude/projects/-home-claude-fff/eddc1285-d67b-5a15-a3ee-2916bc304b7e/subagents/agent-a13b44c80b2472240.jsonl"
txt=open(f,errors='ignore').read()
i=txt.find('ticker,d,pc,o,c,d1,o1,c1,o2\\\\nAAPL')
seg=txt[i:i+40000]
seg=seg.replace('\\\\n','\n').replace('\\n','\n')
rows=[l for l in seg.split('\n') if re.match(r'^[A-Z]+,20\d\d-\d\d-\d\d,[\d.]+,[\d.]+,[\d.]+,20\d\d-\d\d-\d\d,[\d.]+,[\d.]+,[\d.]+$',l)]
print(len(rows))
open('stock.csv','w').write('ticker,d,pc,o,c,d1,o1,c1,o2\n'+'\n'.join(rows)+'\n')
st={(r['ticker'],r['d']):r for r in csv.DictReader(open('stock.csv'))}
T="LRCX AMAT KLAC QCOM INTC MRVL ORCL DELL CRWV META MSFT GOOGL AMZN AAPL TSLA SNDK CRDO ALAB ANET SMCI".split()
earn=[r for r in csv.DictReader(open('earn.csv')) if r['t'] in T and '2024-11-19'<=r['d']<='2026-11-13']
nights=[]
for rank in (0,1):
  for t in T:
    e=[r for r in earn if r['t']==t]
    r=e[-1-rank]; nights.append((t,r['d'],r['tm'],rank))
nights.append(('TSLA','2026-07-22','post-market',2))
out=[]
for t,d,tm,rank in nights:
    s=st[(t,d)]; d1=dt.date.fromisoformat(s['d1']); 
    exp=d1+dt.timedelta((4-d1.weekday())%7)
    S=float(s['c'])
    out.append(dict(t=t,d=d,tm=tm,rank=rank,d1=s['d1'],exp=str(exp),S=S,o1=float(s['o1']),lo=round(S*0.97,2),hi=round(S*1.03,2),
      gprev=round((float(s['o'])/float(s['pc'])-1)*100,2),g=round((float(s['o1'])/S-1)*100,2),gnext=round((float(s['o2'])/float(s['c1'])-1)*100,2)))
json.dump(out,open('nights.json','w'))
for k,o in enumerate(out): print(k,o['t'],o['d'],o['tm'][:3],o['d1'],o['exp'],o['S'],o['lo'],o['hi'],o['gprev'],o['g'],o['gnext'])
