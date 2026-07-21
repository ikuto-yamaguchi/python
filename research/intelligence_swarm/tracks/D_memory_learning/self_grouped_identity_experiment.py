import random,json,time,resource,pickle,statistics,re
from collections import defaultdict
ENT=['青葉','白波','黒羽','朝霧','夕凪','星見','月島','風祭','水瀬','森丘']
VAL=['棚A','棚B','棚C','棚D','箱1','箱2','東区','西区']
FORMS=[lambda e,v:f'{e}の保管場所は{v}です。',lambda e,v:f'{e}は{v}に置かれています。',lambda e,v:f'{e}の置き場を{v}へ更新しました。']
Q=[lambda e:f'{e}はどこですか？',lambda e:f'{e}の保管先を教えて。']
PRON=['それ','その品','先ほどの物']
def grams(s,n=2): return {s[i:i+n] for i in range(max(0,len(s)-n+1))}
def jac(a,b):
 A,B=grams(a),grams(b); return len(A&B)/max(1,len(A|B))
def residual_chunks(s):
 return [x for x in re.split(r'[、。？「」 ]+',s) if 1<len(x)<=18]
class Exact:
 def __init__(self): self.obs=[]; self.last=None
 def observe(self,s): self.obs.append(s); self.last=s
 def answer(self,q):
  best=(0,None)
  for s in reversed(self.obs):
   sc=jac(q,s)
   if sc>best[0]: best=(sc,s)
  if best[0]<.12:return None
  m=re.findall(r'(棚[A-D]|箱[12]|[東西]区)',best[1])
  return m[-1] if m else None
class SelfGroup:
 def __init__(self): self.obs=[]; self.revoked=0
 def observe(self,s):
  self.obs.append((s,residual_chunks(s)))
  if len(self.obs)>1500:self.obs=self.obs[-1500:]
 def answer(self,q):
  scored=[]
  for age,(s,ch) in enumerate(reversed(self.obs)):
   sc=jac(q,s)+0.12*max([jac(x,q) for x in ch] or [0])-age*1e-5
   if sc>.08: scored.append((sc,s,ch))
  if not scored:return None
  scored.sort(reverse=True);cand=defaultdict(float)
  for rank,(sc,s,ch) in enumerate(scored[:12]):
   for c in ch:
    for k in (2,3,4):
     if len(c)>=k:
      r=c[-k:]
      if not any(r in x for x in residual_chunks(q)):cand[r]+=sc/(1+rank)
  if not cand:return None
  ordered=sorted(cand.items(),key=lambda z:(-z[1],len(z[0])))
  if len(ordered)>1 and ordered[0][1] < ordered[1][1]*1.08:
   self.revoked+=1; return None
  return ordered[0][0]
def make(seed,n):
 r=random.Random(seed);es=[e+str(i) for i,e in enumerate(ENT)];truth={};train=[]
 for _ in range(n):
  e=r.choice(es);v=r.choice(VAL);truth[e]=v;train.append(('o',r.choice(FORMS[:2])(e,v),None,e))
  if r.random()<.35:train.append(('o',r.choice(['今日は晴れです。','装置は正常です。','次へ進みます。']),None,None))
  q=r.choice(Q)(e) if r.random()<.65 else r.choice(PRON)+'はどこですか？';train.append(('q',q,v,e))
  if r.random()<.18:
   nv=r.choice([x for x in VAL if x!=v]);truth[e]=nv;train.append(('o',FORMS[2](e,nv),None,e));train.append(('q',Q[1](e),nv,e))
 ev=[]
 for _ in range(120):
  e=r.choice(es);v=truth[e];k=r.choice(['direct','pronoun','variant','distractor','unseen'])
  if k=='direct':q=Q[0](e)
  elif k=='pronoun':q=r.choice(PRON)+'はどこですか？'
  elif k=='variant':q=Q[0](e+'品')
  elif k=='distractor':q='さっき話した'+e+'について、結局どこ？'
  else:q=e+'を見つけるには、どの場所を探せばよい？'
  ev.append((k,q,v))
 return train,ev
def run(seed,n):
 tr,ev=make(seed,n);out={}
 for name,M in [('exact',Exact),('self_grouped',SelfGroup)]:
  m=M();online=[];t=time.perf_counter()
  for typ,s,a,e in tr:
   if typ=='o':m.observe(s)
   else:online.append(m.answer(s)==a);m.observe(s)
  train=time.perf_counter()-t;by=defaultdict(list);t=time.perf_counter()
  for k,q,a in ev:by[k].append(m.answer(q)==a)
  inf=(time.perf_counter()-t)/len(ev)*1000
  out[name]={k:sum(v)/len(v) for k,v in by.items()};out[name].update(online=sum(online)/len(online),train_s=train,inference_ms=inf,model_bytes=len(pickle.dumps(m)),reads=min(12,len(m.obs)),revoked=getattr(m,'revoked',0))
 return out
runs=[]
for n in [48,180,540]:
 for seed in [1,7,19]:runs.append({'n':n,'seed':seed,'metrics':run(seed,n)})
summary={}
for n in [48,180,540]:
 summary[str(n)]={}
 for model in ['exact','self_grouped']:
  keys=runs[0]['metrics'][model]
  summary[str(n)][model]={k:statistics.mean([r['metrics'][model][k] for r in runs if r['n']==n]) for k in keys}
summary['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
print(json.dumps({'runs':runs,'summary':summary},ensure_ascii=False,indent=2))
