import random,re,time,pickle,resource,json,statistics
from collections import Counter,defaultdict

RELATIONS=[
  (["{e}の保管場所は{v}です。","{e}は{v}に置かれています。","{v}にあるのは{e}です。"],["{e}はどこですか？","{e}の置き場所は？","今どこにある？"]),
  (["{e}の担当者は{v}です。","{e}を担当する人は{v}。","{v}が{e}を受け持ちます。"],["{e}の担当は誰ですか？","{e}を担当する人は？","担当は誰？"]),
  (["{e}の合言葉は{v}です。","{e}では{v}を合言葉にします。","{v}が{e}の合言葉です。"],["{e}の合言葉を教えて。","{e}で使う合言葉は？","合言葉は？"]),
]
CHARS=list("甲乙丙丁戊己庚辛壬癸春夏秋冬東西南北天地海山川星月花鳥風雲")
def names(r,n,p):return [p+''.join(r.sample(CHARS,4))+str(i) for i in range(n)]
def norm(s):return re.sub(r"\s+","",s)

def anti_pair(a,b):
 import difflib
 blocks=[x for x in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks() if x.size>=4]
 vals=[]
 for x in sorted(blocks,key=lambda z:z.size,reverse=True):
  v=a[x.a:x.a+x.size]
  if v.strip("。、！？") and all(v not in y and y not in v for y in vals):vals.append(v)
  if len(vals)==2:break
 if len(vals)<2:return None
 vals=sorted(vals,key=a.index);clean=[]
 for x in vals:
  while len(x)>3 and x[0] in 'はがをにでへと':x=x[1:]
  while len(x)>3 and x[-1] in 'はがをにでへと':x=x[:-1]
  clean.append(x)
 pa,pb=a,b
 for k,x in enumerate(clean):
  pa=pa.replace(x,f"{{S{k}}}",1);pb=pb.replace(x,f"{{S{k}}}",1)
 return pa,pb,tuple(clean)

def compile_pat(pat):
 s=re.escape(pat)
 for k in range(3):s=s.replace(re.escape(f"{{S{k}}}"),f"(?P<S{k}>.+?)")
 return re.compile('^'+s+'$')

class CrossViewMemory:
 def __init__(self,min_support=2):
  self.min_support=min_support;self.views=[];self.query_links=[];self.bindings={};self.clock=0
 def fit_unlabeled(self,episodes):
  counts=Counter();q_examples=[]
  for s1,s2,q in episodes:
   z=anti_pair(norm(s1),norm(s2))
   if z:counts[(z[0],z[1])]+=1
   q_examples.append((norm(q),norm(s1),norm(s2)))
  self.views=[k for k,c in counts.items() if c>=self.min_support]
  votes=Counter()
  for q,s1,s2 in q_examples:
   for vi,(p1,p2) in enumerate(self.views):
    m1=compile_pat(p1).match(s1);m2=compile_pat(p2).match(s2)
    if not (m1 and m2):continue
    vals=[m1.group('S0'),m1.group('S1')]
    for slot,v in enumerate(vals):
     if v in q:votes[(q.replace(v,'{Q}',1),vi,slot)]+=1
  self.query_links=[k for k,c in votes.items() if c>=self.min_support]
 def observe(self,s):
  s=norm(s);self.clock+=1
  for vi,(p1,p2) in enumerate(self.views):
   for pat in (p1,p2):
    m=compile_pat(pat).match(s)
    if m:
     vals=(m.group('S0'),m.group('S1'))
     self.bindings[(vi,0,vals[0])]=(vals[1],self.clock)
     self.bindings[(vi,1,vals[1])]=(vals[0],self.clock)
     return True
  return False
 def query(self,q):
  q=norm(q);cands=[];reads=0
  for qp,vi,slot in self.query_links:
   reads+=1
   m=re.compile('^'+re.escape(qp).replace(re.escape('{Q}'),'(.+?)')+'$').match(q)
   if m:
    z=self.bindings.get((vi,slot,m.group(1)))
    if z:cands.append(z)
  return (max(cands,key=lambda x:x[1])[0],reads) if cands else (None,reads)
 def bytes(self):return len(pickle.dumps((self.views,self.query_links,self.bindings)))

class AnswerSupervised:
 def __init__(self):self.rows=[]
 def fit(self,episodes):
  for s1,s2,q in episodes:
   z=anti_pair(norm(s1),norm(s2))
   if z:self.rows.append((z[0],norm(q).replace(z[2][0],'{Q}',1)))
 def observe(self,s):
  s=norm(s)
  for i,row in enumerate(self.rows):
   m=compile_pat(row[0]).match(s)
   if m:self.rows[i]=(row[0],row[1],m.group('S0'),m.group('S1'));return True
  return False
 def query(self,q):
  q=norm(q)
  for row in reversed(self.rows):
   if len(row)==4 and row[1].replace('{Q}',row[2])==q:return row[3],len(self.rows)
  return None,len(self.rows)
 def bytes(self):return len(pickle.dumps(self.rows))

class RawSearch:
 def __init__(self):self.raw=[]
 def fit(self,episodes):pass
 def observe(self,s):self.raw.append(norm(s));return True
 def query(self,q):return None,len(self.raw)
 def bytes(self):return len(pickle.dumps(self.raw))

def make(seed,ntrain):
 r=random.Random(seed);E=names(r,ntrain+500,'対象');V=names(r,ntrain+700,'値');train=[]
 for i in range(ntrain):
  forms,qs=RELATIONS[i%3];e,v=E[i],V[i]
  train.append((forms[0].format(e=e,v=v),forms[1].format(e=e,v=v),qs[i%2].format(e=e)))
 return E,V,train

def run(seed,ntrain):
 E,V,tr=make(seed,ntrain)
 models={'raw':RawSearch(),'answer_supervised':AnswerSupervised(),'cross_view':CrossViewMemory()}
 t0=time.perf_counter()
 for name,m in models.items():m.fit_unlabeled(tr) if name=='cross_view' else m.fit(tr)
 train_sec=time.perf_counter()-t0;out={}
 for name,m in models.items():
  ok=[];lat=[];reads=[]
  for j in range(120):
   i=ntrain+j;forms,qs=RELATIONS[i%3];e,v=E[i],V[i]
   m.observe(forms[0].format(e=e,v=v));t=time.perf_counter();p,rd=m.query(qs[0].format(e=e));lat.append((time.perf_counter()-t)*1000);reads.append(rd);ok.append(p==v)
  metrics={'oneshot':sum(ok)/len(ok)};ok=[]
  for j in range(90):
   i=ntrain+130+j;forms,qs=RELATIONS[i%3];e,v=E[i],V[i]
   m.observe(forms[1].format(e=e,v=v));p,_=m.query(qs[1].format(e=e));ok.append(p==v)
  metrics['paraphrase']=sum(ok)/len(ok);ok=[]
  for j in range(90):
   i=ntrain+230+j;forms,qs=RELATIONS[i%3];e,v=E[i],V[i]
   m.observe(forms[2].format(e=e,v=v));p,_=m.query(qs[0].format(e=e));ok.append(p==v)
  metrics['unseen_syntax']=sum(ok)/len(ok);abst=[]
  for j in range(60):
   i=ntrain+330+j;forms,qs=RELATIONS[i%3];e,v=E[i],V[i]
   m.observe(forms[0].format(e=e,v=v));p,_=m.query(qs[2]);abst.append(p is None)
  metrics['omission_abstain']=sum(abst)/len(abst);ok=[]
  for j in range(40):
   i=ntrain+400+j;forms,qs=RELATIONS[i%3];e=E[i];v1=V[i];v2=V[i+200]
   m.observe(forms[0].format(e=e,v=v1))
   for z in range(30):
    ff,_=RELATIONS[z%3];m.observe(ff[0].format(e=E[(i+z+1)%len(E)],v=V[(i+z+1)%len(V)]))
   m.observe(forms[1].format(e=e,v=v2));p,_=m.query(qs[0].format(e=e));ok.append(p==v2)
  metrics['latest_after_interference']=sum(ok)/len(ok)
  metrics.update(model_bytes=m.bytes(),latency_ms=statistics.mean(lat),candidate_reads=statistics.mean(reads),views=len(getattr(m,'views',[])),query_links=len(getattr(m,'query_links',[])),bindings=len(getattr(m,'bindings',{})))
  out[name]=metrics
 return {'seed':seed,'ntrain':ntrain,'train_seconds_all':train_sec,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'results':out}

rows=[run(s,n) for n in (48,180,540) for s in (1,7,19)];agg={}
for n in (48,180,540):
 agg[str(n)]={}
 for name in ('raw','answer_supervised','cross_view'):
  rr=[x['results'][name] for x in rows if x['ntrain']==n]
  agg[str(n)][name]={k:statistics.mean(z[k] for z in rr) for k in rr[0]}
out={'hypothesis':'Answer-free cross-view predictive rebinding can induce anonymous entity/value bindings from repeated co-referring descriptions and use them as one-shot fast memory.','aggregate':agg,'runs':rows,'claim':{'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}}
open('results_cycle_002.json','w').write(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(agg['540'],ensure_ascii=False,indent=2))
