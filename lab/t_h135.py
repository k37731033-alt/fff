# h135: pre-registered gut calls, scored only (id, type, p, hit)
calls = [
 (1,'기타',0.60,0),(3,'기타',0.60,1),('4a','기타',0.60,0),
 (5,'⑤',0.60,0),(8,'④',0.60,0),(9,'①',0.60,1),(10,'①',0.60,1),
 (12,'⑤',0.60,1),(15,'①',0.55,0),(16,'⑤',0.60,0)]
from collections import defaultdict
g=defaultdict(list)
for c in calls: g[c[1]].append(c)
br=lambda p,o:(p-o)**2
for t,v in sorted(g.items()):
    print(t,len(v),sum(x[3] for x in v),round(sum(x[3] for x in v)/len(v),2),round(sum(br(x[2],x[3]) for x in v)/len(v),3))
alln=len(calls);h=sum(c[3] for c in calls);B=sum(br(c[2],c[3]) for c in calls)/alln
print('ALL',alln,h,h/alln,round(B,3))
# sensitivity: 8 as ① instead of ④
v=g['①']+[(8,'①',0.6,0)];print('① incl 8',len(v),sum(x[3] for x in v),round(sum(br(x[2],x[3]) for x in v)/len(v),3))
# hit rate needed at p=0.6 to beat 0.25: 0.36-0.2h<0.25 -> h>0.55
print('break-even hit at p=.6:',(0.36-0.25)/0.2)
# open-call check with given closes
print('13 NVDA 11/24 vs 11/23:',155.38/165.05-1,'(rule needs 11/27 close)')
print('7 SOXX 11/24 vs 141.85:',128.62/141.85-1,'(rule needs 12/17 close)')
print('11 SOXL 11/24 vs 11/23:',32.60/43.21-1,'(rule needs ~60 trading days)')
