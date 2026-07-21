import difflib,json,random,time,resource,pickle,statistics,math
from collections import defaultdict,Counter
NAMES=['アルファ','ベータ','ガンマ','デルタ','シグマ','オメガ','ミライ','カナタ']
PLACES=['棚A','棚B','棚C','棚D','机上','入口','窓辺']
MOVE=['{x}を{dst}へ移してください。','{x}を{dst}に動かしてください。','{x}の置き場所を{dst}へ変えてください。']
ON=['ランプを点けてください。','照明をオンにしてください。','明かりを点灯してください。']
OFF=['ランプを消してください。','照明をオフにしてください。','明かりを消灯してください。']
def state(x,p,l): return f'対象「{x}」は{p}にあり、ランプは{l}。'
def gen(r,para=False,conf=False):
 x=r.choice(NAMES[:6]); src,dst=r.sample(PLACES[:5],2); typ=r.choice(['move','on','off']); lamp=r.choice(['点灯','消灯']); b=state(x,src,lamp)
 if typ=='move': c=r.choice(MOVE[1:] if para else MOVE[:1]).format(x=f'対象「{x}」',dst=dst); a=state(x,dst,lamp)
 elif typ=='on': c=r.choice(ON[1:] if para else ON[:1]); a=state(x,src,'点灯')
 else: c=r.choice(OFF[1:] if para else OFF[:1]); a=state(x,src,'消灯')
 if conf and r.random()<.5:
  a=b if typ=='move' else state(x,src,'消灯' if typ=='on' else '点灯')
 return {'before':b,'command':c,'after':a,'type':typ,'name':x}
def prog(b,a):
 sm=difflib.SequenceMatcher(a=b,b=a,autojunk=False); out=[]
 for tag,i1,i2,j1,j2 in sm.get_opcodes():
  if tag!='equal': out.append((tag,i1,i2,b[i1:i2],a[j1:j2]))
 return tuple(out)
def ng(s,n=3): return Counter(s[i:i+n] for i in range(max(0,len(s)-n+1)))
def cos(a,b):
 if not a or not b:return 0
 return sum(v*b.get(k,0) for k,v in a.items())/(math.sqrt(sum(v*v for v in a.values()))*math.sqrt(sum(v*v for v in b.values()))+1e-9)
def apply(b,p):
 s=b
 for _,i1,i2,old,new in sorted(p,key=lambda x:x[1],reverse=True):
  if s[i1:i2]==old:s=s[:i1]+new+s[i2:]
  elif old in s:s=s.replace(old,new,1)
 return s
class M:
 def __init__(self,m):self.m=m;self.es=[];self.cs=[];self.rej=0
 def fit(self,es):
  self.es=list(es); groups=defaultdict(list)
  for e in es:
   p=prog(e['before'],e['after']); shape=tuple((t,i2-i1,len(n)) for t,i1,i2,o,n in p); groups[shape].append((e,p))
  for shape,xs in groups.items():
   ps=[p for e,p in xs]; pc=Counter(ps); stable=pc.most_common(1)[0][1]/len(ps)
   self.cs.append({'shape':shape,'ps':ps,'cmds':[e['command'] for e,p in xs],'stable':stable})
 def predict(self,b,c):
  if self.m=='lexical':
   e=max(self.es,key=lambda e:cos(ng(c),ng(e['command']))); return apply(b,prog(e['before'],e['after'])),1,len(self.es)
  scored=[]
  for x in self.cs: scored.append((max(cos(ng(c),ng(z)) for z in x['cmds']),x))
  scored.sort(key=lambda z:z[0],reverse=True)
  if not scored:return b,0,0
  x=scored[0][1]
  if self.m=='intervention' and x['stable']<.8:self.rej+=1;return b,0,len(scored)
  p=Counter(x['ps']).most_common(1)[0][0]; out=apply(b,p)
  dst=[q for q in PLACES if q in c]
  if dst and p:
   new=p[0][4]
   for q in PLACES:
    if q in new and q in out and q!=dst[0]:out=out.replace(q,dst[0],1);break
  return out,1,len(scored)
def ev(m,es):
 ok=reads=ab=0;t=time.perf_counter()
 for e in es:
  p,a,r=m.predict(e['before'],e['command']);ok+=p==e['after'];reads+=r;ab+=a==0
 return ok/len(es),(time.perf_counter()-t)*1000/len(es),reads/len(es),ab/len(es)
def run(seed,n,method):
 r=random.Random(seed);tr=[gen(r) for _ in range(n)];m=M(method);t=time.perf_counter();m.fit(tr);ts=time.perf_counter()-t
 normal=[gen(random.Random(seed*10000+i)) for i in range(30)]; nacc,lat,reads,_=ev(m,normal)
 ren=[]
 for i in range(40):
  e=gen(random.Random(seed*20000+i));new=NAMES[6+i%2]
  for k in ['before','command','after']:e[k]=e[k].replace(e['name'],new)
  ren.append(e)
 racc,_,_,_=ev(m,ren)
 para=[gen(random.Random(seed*30000+i),True) for i in range(40)];pacc,_,_,_=ev(m,para)
 conf=[gen(random.Random(seed*40000+i),False,True) for i in range(40)];cacc,_,_,cab=ev(m,conf)
 planok=0
 for i in range(30):
  rr=random.Random(seed*50000+i);x=rr.choice(NAMES[6:]);src,d1,d2=rr.sample(PLACES,3);l=rr.choice(['点灯','消灯']);b=state(x,src,l)
  c1=MOVE[0].format(x=f'対象「{x}」',dst=d1);c2=MOVE[0].format(x=f'対象「{x}」',dst=d2);p1,_,_=m.predict(b,c1);p2,_,_=m.predict(p1,c2);planok+=p2==state(x,d2,l)
 omit=[]
 for i in range(30):
  e=gen(random.Random(seed*60000+i));e['command']=e['command'].replace(f'対象「{e["name"]}」を','それを');omit.append(e)
 oacc,_,_,_=ev(m,omit)
 return {'seed':seed,'ntrain':n,'method':method,'normal':nacc,'rename':racc,'paraphrase':pacc,'confounded_accuracy':cacc,'confounded_abstention':cab,'plan':planok/30,'omission':oacc,'free_gate':0.0,'model_bytes':len(pickle.dumps(m)),'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'train_seconds':ts,'inference_ms':lat,'candidate_reads':reads,'graph_nodes':len(m.cs),'graph_edges':sum(len(x['ps']) for x in m.cs),'rejected':m.rej}
rows=[run(s,n,m) for n in [32,128,512] for s in [1,7,19] for m in ['lexical','residual','intervention']]
agg={}
for m in ['lexical','residual','intervention']:
 agg[m]={}
 for n in [32,128,512]:
  rr=[x for x in rows if x['method']==m and x['ntrain']==n]
  agg[m][str(n)]={k:statistics.mean(x[k] for x in rr) for k in ['normal','rename','paraphrase','confounded_accuracy','confounded_abstention','plan','omission','free_gate','model_bytes','peak_rss_kib','train_seconds','inference_ms','candidate_reads','graph_nodes','graph_edges','rejected']}
out={'hypothesis':'Intervention-stable residual event programs should be accepted only when the same utterance family induces a consistent sparse state transition across diverse objects and contexts.','aggregate':agg,'runs':rows,'claim':{'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}}
open('results_cycle_001.json','w').write(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(agg,ensure_ascii=False,indent=2))