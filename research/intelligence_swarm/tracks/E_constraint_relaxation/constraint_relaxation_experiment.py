import random,time,pickle,resource,json,math,statistics
from collections import Counter

NAMES=['アルファ','ベータ','ガンマ','デルタ','シグマ','オメガ','ミライ','カナタ']
PLACES=['棚A','棚B','棚C','棚D','机上','入口','窓辺']
MOVE=['対象「{x}」を{d}へ移してください。','対象「{x}」の置き場所を{d}に変えてください。']

def state(x,p,l): return f'対象「{x}」は{p}にあり、照明は{l}。'
def ng(s,n=3): return Counter(s[i:i+n] for i in range(max(0,len(s)-n+1)))
def cos(a,b):
 d=(sum(v*v for v in a.values())*sum(v*v for v in b.values()))**.5
 return 0 if d==0 else sum(v*b.get(k,0) for k,v in a.items())/d

def event(r,para=False):
 x=r.choice(NAMES[:6]);p,d=r.sample(PLACES[:5],2);l=r.choice(['点灯','消灯'])
 return {'before':state(x,p,l),'cmd':MOVE[1 if para else 0].format(x=x,d=d),'after':state(x,d,l),'x':x}

def program(b,a):
 i=0
 while i<min(len(b),len(a)) and b[i]==a[i]: i+=1
 j=0
 while j<min(len(b)-i,len(a)-i) and b[-1-j]==a[-1-j]: j+=1
 return ((i,b[i:len(b)-j if j else len(b)],a[i:len(a)-j if j else len(a)]),)

def apply(b,p):
 s=b
 for i,o,n in p:
  if i<=len(s) and s[i:i+len(o)]==o:s=s[:i]+n+s[i+len(o):]
  elif o in s:s=s.replace(o,n,1)
 return s

class Model:
 def fit(self,es):self.items=[(ng(e['cmd']),program(e['before'],e['after']),e['cmd']) for e in es]
 def candidates(self,c,k=6):
  q=ng(c);z=[(cos(q,f),p,t) for f,p,t in self.items];z.sort(reverse=True,key=lambda x:x[0]);return z[:k]
 def greedy(self,b,c):
  z=self.candidates(c,1)[0];return apply(b,z[1])
 def relax(self,b,cmds,k=6,max_iter=12):
  cand=[self.candidates(c,k) for c in cmds];idx=[0]*len(cmds);prev=1e9
  def energy(sel):
   s=b;E=0
   for t,j in enumerate(sel):
    sim,p,_=cand[t][j];ns=apply(s,p)
    E+=(1-sim)+(0.8 if ns==s else 0)+0.25*abs(len(ns)-len(s))/max(1,len(s))
    if '対象「' not in ns or '照明は' not in ns:E+=2
    s=ns
   return E,s
  for it in range(1,max_iter+1):
   changed=False
   for t in range(len(cmds)):
    best=(1e9,idx[t])
    for j in range(len(cand[t])):
     q=idx[:];q[t]=j;E,_=energy(q)
     if E<best[0]-1e-12:best=(E,j)
    if best[1]!=idx[t]:idx[t]=best[1];changed=True
   E,s=energy(idx)
   if not changed or abs(prev-E)<1e-9:break
   prev=E
  alt=1e9
  for t in range(len(cmds)):
   for j in range(len(cand[t])):
    if j==idx[t]:continue
    q=idx[:];q[t]=j;alt=min(alt,energy(q)[0])
  return s,E,(alt-E if alt<1e9 else 0),it,sum(len(x) for x in cand)

def run(seed,n):
 r=random.Random(seed);m=Model();t=time.perf_counter();m.fit([event(r) for _ in range(n)]);train=time.perf_counter()-t
 g=rel=0;lat=[];its=[];reads=[]
 for i in range(80):
  rr=random.Random(seed*10000+i);x=rr.choice(NAMES[:6]);p,d1,d2=rr.sample(PLACES[:5],3);l=rr.choice(['点灯','消灯']);b=state(x,p,l)
  cs=[MOVE[0].format(x=x,d=d1),MOVE[0].format(x=x,d=d2)];target=state(x,d2,l)
  s=b
  for c in cs:s=m.greedy(s,c)
  g+=s==target
  st=time.perf_counter();s,E,ma,it,rd=m.relax(b,cs);lat.append((time.perf_counter()-st)*1000);rel+=s==target;its.append(it);reads.append(rd)
 para=rename=0
 for i in range(60):
  e=event(random.Random(seed*20000+i),True);para+=m.relax(e['before'],[e['cmd']])[0]==e['after']
  e=event(random.Random(seed*30000+i));new=NAMES[6+i%2]
  for z in ['before','cmd','after']:e[z]=e[z].replace(e['x'],new)
  rename+=m.relax(e['before'],[e['cmd']])[0]==e['after']
 abst=0
 for i in range(40):
  rr=random.Random(seed*40000+i);x=rr.choice(NAMES[:6]);p,d1,d2=rr.sample(PLACES[:5],3);b=state(x,p,'消灯')
  _,_,margin,_,_=m.relax(b,[MOVE[0].format(x=x,d=d1),MOVE[0].format(x=x,d=d2)]);abst+=margin<0.05
 return {'seed':seed,'n':n,'greedy_plan':g/80,'relax_plan':rel/80,'paraphrase':para/60,'rename':rename/60,'conflict_abstention':abst/40,'model_bytes':len(pickle.dumps(m)),'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'train_seconds':train,'inference_ms_plan':statistics.mean(lat),'iterations':statistics.mean(its),'active_candidates':statistics.mean(reads)}

rows=[run(s,n) for n in [32,128,512] for s in [1,7,19]]
agg={str(n):{k:statistics.mean(x[k] for x in rows if x['n']==n) for k in rows[0] if k not in ('seed','n')} for n in [32,128,512]}
out={'hypothesis':'Joint sparse constraint relaxation over candidate edit programs improves multi-step consistency beyond one-pass retrieval.','aggregate':agg,'runs':rows,'claim':{'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}}
open('results_cycle_001.json','w').write(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(agg,ensure_ascii=False,indent=2))
