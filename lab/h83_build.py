import json,csv,subprocess,sys
subprocess.run([sys.executable,'bars.py'],stdout=subprocess.DEVNULL)
bars=json.load(open('bars.json')); nights=json.load(open('nights.json'))
st=list(csv.DictReader(open('stock.csv')))
earn=[r for r in csv.DictReader(open('earn.csv'))]
K={('LRCX','2026-10-21'):260,('AMAT','2026-11-12'):380,('KLAC','2026-10-28'):160,('QCOM','2026-11-04'):172.5,('INTC','2026-10-29'):92,('ORCL','2026-09-10'):152.5,('DELL','2026-09-01'):425,('CRWV','2026-11-10'):48.5,('META','2026-10-21'):697.5,('MSFT','2026-10-28'):530,('GOOGL','2026-10-28'):325,('AMZN','2026-10-29'):245,('AAPL','2026-11-02'):337.5,('TSLA','2026-10-21'):387.5,('SNDK','2026-10-29'):1330,('CRDO','2026-09-01'):207.5,('ALAB','2026-11-03'):232.5,('ANET','2026-11-03'):170,('SMCI','2026-11-03'):31.5,
('LRCX','2026-07-29'):252.5,('AMAT','2026-08-13'):535,('QCOM','2026-07-29'):155,('INTC','2026-07-23'):100,('MRVL','2026-08-27'):242.5,('ORCL','2026-06-10'):202.5,('DELL','2026-05-28'):317.5,('CRWV','2026-08-11'):90,('META','2026-07-29'):585,('MSFT','2026-07-29'):390,('GOOGL','2026-07-22'):342.5,('AMZN','2026-07-30'):235,('AAPL','2026-07-30'):332.5,('SNDK','2026-08-05'):1350,('CRDO','2026-06-01'):225,('ANET','2026-08-04'):190,('SMCI','2026-10-20'):32.5,('TSLA','2026-07-22'):375}
try: K.update({tuple(k.split('|')):v for k,v in json.load(open('kextra.json')).items()})
except Exception: pass
try: NOTES={tuple(k.split('|')):v for k,v in json.load(open('notes.json')).items()}
except Exception: NOTES={}
def tk(t,exp,cp,k): return "O:%s%s%s%08d"%(t,exp[2:].replace('-',''),cp,round(k*1000))
def f(x): return '' if x is None else (str(int(x)) if float(x)==int(x) else repr(round(float(x),4)))
rows=[]
for nn in sorted(nights,key=lambda x:(x['rank'],)):
    t,d,d1=nn['t'],nn['d'],nn['d1']
    timing='AMC' if nn['tm']=='post-market' else 'BMO'
    # prior gaps
    pri=[]
    for r in st:
        if r['ticker']!=t or r['d']>=d: continue
        e=[x for x in earn if x['t']==t and x['d']==r['d']][0]
        if e['tm']!='post-market': continue
        pri.append((r['d'],(float(r['o1'])/float(r['c'])-1)*100))
    pri.sort(reverse=True)
    pg=';'.join('%.2f'%g for _,g in pri[:8])
    note=[]
    row=dict(ticker=t,D=d,D1=d1,timing=timing,S_close_D=f(nn['S']),S_open_D1=f(nn['o1']),expiry='',strike='',call_c_D='',call_o_D1='',call_v_D='',call_n_D='',put_c_D='',put_o_D1='',put_v_D='',put_n_D='',replaced='',prior_gaps=pg,n_prior=len(pri))
    if timing=='BMO':
        note.append('BMO per t_earn_dates; options skipped')
    else:
        row['expiry']=nn['exp']
        if nn['exp']==d1: note.append('D1 is expiry day (1-day option)')
        k=K.get((t,d))
        if k is None: note.append('strike not resolved / not collected')
        else:
            row['strike']=f(k); row['replaced']=0
            for cp,nm in (('C','call'),('P','put')):
                b=bars.get(tk(t,nn['exp'],cp,k))
                if b is None: note.append(nm+' bars not fetched'); continue
                bd=b['bars'].get(d); b1=b['bars'].get(d1)
                if bd: row[nm+'_c_D']=f(bd['c']); row[nm+'_v_D']=f(bd['v']); row[nm+'_n_D']=bd['n']
                else: note.append(nm+' no bar on D')
                if b1: row[nm+'_o_D1']=f(b1['o'])
                else: note.append(nm+' no bar on D1')
                if bd and bd['n']<5: note.append(nm+' thin n<5')
    a=[abs(nn['gprev']),abs(nn['g']),abs(nn['gnext'])]
    if timing=='AMC' and a[1]<max(a[0],a[2]): note.append('timing check: night gap %.2f%% smaller than adjacent gap (prev open gap %.2f%%, next %.2f%%)'%(nn['g'],nn['gprev'],nn['gnext']))
    if (t,d) in NOTES: note.append(NOTES[(t,d)])
    row['note']=' | '.join(note)
    rows.append(row)
H="ticker,D,D1,timing,S_close_D,S_open_D1,expiry,strike,call_c_D,call_o_D1,call_v_D,call_n_D,put_c_D,put_o_D1,put_v_D,put_n_D,replaced,prior_gaps,n_prior,note".split(',')
w=csv.DictWriter(open('/home/claude/fff/_w/h83_rows.csv','w',newline=''),fieldnames=H); w.writeheader(); w.writerows(rows)
comp=sum(1 for r in rows if all(r[x]!='' for x in ['call_c_D','call_o_D1','put_c_D','put_o_D1']))
print('rows',len(rows),'complete',comp)
for r in rows: print(','.join(str(r[h]) for h in H))
