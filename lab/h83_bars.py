import json,re,datetime as dt
f="/root/.claude/projects/-home-claude-fff/eddc1285-d67b-5a15-a3ee-2916bc304b7e/subagents/agent-a13b44c80b2472240.jsonl"
uses={};res={}
def walk(o):
    if isinstance(o,dict):
        if o.get('type')=='tool_use' and 'id' in o: uses[o['id']]=o.get('input',{})
        if o.get('type')=='tool_result' and 'tool_use_id' in o: res[o['tool_use_id']]=json.dumps(o.get('content'))
        for v in o.values(): walk(v)
    elif isinstance(o,list):
        for v in o: walk(v)
for l in open(f,errors='ignore'):
    try: walk(json.loads(l))
    except Exception as e: pass
bars={}
for i,inp in uses.items():
    p=inp.get('path','') if isinstance(inp,dict) else ''
    m=re.match(r'/v2/aggs/ticker/(O:[A-Z]+\d{6}[CP]\d{8})/range/1/day/(\S+)/(\S+)',p)
    if not m or i not in res: continue
    r=res[i]
    if 'RATE_LIMIT' in r: continue
    rows=re.findall(r'([\d.e+-]+),([\d.e+-]+),([\d.e+-]+),([\d.e+-]+),([\d.e+-]+),([\d.e+-]+),(\d{13}),(\d+)',r)
    d={}
    for v,vw,o,c,h,lo,t,n in rows:
        day=str((dt.datetime(1970,1,1)+dt.timedelta(seconds=int(t)/1000+43200)).date())
        d[day]=dict(v=float(v),o=float(o),c=float(c),n=int(n))
    bars[m.group(1)]=dict(D=m.group(2),D1=m.group(3),bars=d,raw=r[:200] if not rows else '')
json.dump(bars,open('bars.json','w'),indent=0)
if __name__=='__main__':
    for k,v in bars.items(): print(k,v['D'],v['D1'],{d:(b['o'],b['c'],b['v'],b['n']) for d,b in v['bars'].items()},v['raw'])
