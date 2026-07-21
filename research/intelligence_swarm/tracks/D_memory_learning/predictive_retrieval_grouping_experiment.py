import random,re,json,time,resource,pickle,statistics,math
from collections import defaultdict,Counter
ENT=['青葉','白波','黒羽','朝霧','夕凪','星見','月島','風祭','水瀬','森丘']
VAL=['棚A','棚B','棚C','棚D','箱1','箱2','東区','西区']
OBS=[lambda e,v:f'{e}の保管場所は{v}です。',lambda e,v:f'{e}は{v}に置かれています。',lambda e,v:f'{e}の置き場を{v}へ更新しました。']
Q=[lambda e:f'{e}はどこですか？',lambda e:f'{e}の保管先を教えて。',lambda e:f'さっき話した{e}について、結局どこ？']
PRON=['それ','その品','先ほどの物']
NOISE=['今日は晴れです。','装置は正常です。','次へ進みます。','休憩を取ります。']
def chunks(s): return [x for x in re.split(r'[、。？「」\s]+',s) if x]
def grams(s,n=2): return Counter(s[i:i+n] for i in range(max(0,len(s)-n+1)))
def cos(a,b):
 d=sum(v*b.get(k,0) for k,v in a.items());na=math.sqrt(sum(v*v for v in a.values()));nb=math.sqrt(sum(v*v for v in b.values()));return d/(na*nb+1e-12)
def shared_spans(a,b,minlen=2):
 out=set()
 for i in range(len(a)):
  for j in range(len(b)):
   k=0
   while i+k<len(a) and j+k<len(b) and a[i+k]==b[j+k]:k+=1
   if k>=minlen:out.add(a[i:i+k])
 vals=[x for x in out if re.search(r'[A-Za-z0-9一-龠ぁ-んァ-ン]',x)]
 vals=sorted(vals,key=len,reverse=True);kept=[]
 for x in vals:
  if not any(x in y for y in kept):kept.append(x)
 return kept
def skeleton_kv(text,key,value=None):
 out=text.replace(key,'<K>',1)
 if value is not None:out=out.replace(value,'<V>',1)
 return out
def common_suffix(strings):
 if not strings:return ''
 rev=[x[::-1] for x in strings];n=min(map(len,rev));i=0
 while i<n and len({x[i] for x in rev})==1:i+=1
 return rev[0][:i][::-1]
class SurfaceNearest:
 def __init__(self):self.obs=[]
 def observe(self,text):self.obs.append(text)
 def answer(self,q):
  if not self.obs:return None
  scored=sorted(((cos(grams(q),grams(o)),o) for o in self.obs),reverse=True)
  if not scored or scored[0][0]<.08:return None
  cand=[c for c in chunks(scored[0][1]) if c not in q and len(c)<=8]
  return cand[-1] if cand else None
class PredictiveGrouping:
 def __init__(self):
  self.fast=[];self.schemas=defaultdict(lambda:{'support':0.0,'harm':0.0,'answer_pos':Counter()});self.bindings={};self.last_entity=None;self.t=0;self.revoked=0;self.response_suffix=''
 def fit_suffix(self,responses):self.response_suffix=common_suffix(responses)
 def observe(self,text):
  self.t+=1;self.fast.append((self.t,text));self.fast=self.fast[-80:]
  if '？' not in text and not text.endswith('?'):
   cs=chunks(text)
   if cs:self.last_entity=cs[0][:12]
 def train_triple(self,obs,q,response,negative_questions):
  value=response[:-len(self.response_suffix)] if self.response_suffix and response.endswith(self.response_suffix) else response
  value=value.strip('「」 、。？')
  if not value or value not in obs:return
  common=shared_spans(obs,q,2)
  if not common:return
  key=common[0];sig=skeleton_kv(obs,key,value)+'||'+skeleton_kv(q,key)
  rec=self.schemas[sig];rec['support']+=1.0;rec['harm']+=sum(1 for nq in negative_questions if key in nq)/max(1,len(negative_questions))
  for i,p in enumerate(chunks(obs)):
   if value in p:rec['answer_pos'][i]+=1
  if rec['support']-2.0*rec['harm']>=2.0:self.bindings[(sig,key)]=(value,self.t)
 def ingest_one_shot(self,obs):
  candidates=[]
  for sig,rec in self.schemas.items():
   if rec['support']-2*rec['harm']<2:continue
   os,_=sig.split('||');pat=re.escape(os).replace(re.escape('<K>'),'(.+?)').replace(re.escape('<V>'),'(.+?)');m=re.fullmatch(pat,obs)
   if m and len(m.groups())>=2:candidates.append((sig,m.group(1),m.group(2)))
  uniq={(s,k,v) for s,k,v in candidates if k and v and k!=v}
  if len(uniq)==1:
   s,k,v=next(iter(uniq));self.t+=1;self.bindings[(s,k)]=(v,self.t);self.last_entity=k
  elif len(uniq)>1:self.revoked+=1
 def answer(self,q):
  cands=[]
  for (sig,key),(value,ts) in self.bindings.items():
   _,qs=sig.split('||');pat=re.escape(qs).replace(re.escape('<K>'),'(.+?)');m=re.fullmatch(pat,q)
   if m and m.group(1)==key:cands.append((ts,value))
  if not cands and any(p in q for p in PRON) and self.last_entity:
   for (sig,key),(value,ts) in self.bindings.items():
    if key==self.last_entity:cands.append((ts,value))
  if not cands:return None
  cands.sort(reverse=True)
  if len(cands)>1 and cands[0][0]==cands[1][0] and cands[0][1]!=cands[1][1]:self.revoked+=1;return None
  return cands[0][1]
def make(seed,n):
 r=random.Random(seed);ents=[e+str(i) for i,e in enumerate(ENT)];truth={};triples=[];stream=[]
 for _ in range(n):
  e=r.choice(ents);v=r.choice(VAL);truth[e]=v;obs=r.choice(OBS[:2])(e,v);q=r.choice(Q[:2])(e);resp=f'{v}です。';neg=[r.choice(Q[:2])(x) for x in r.sample([z for z in ents if z!=e],3)];triples.append((obs,q,resp,neg));stream.append(('obs',obs,None));stream.append(('q',q,v))
  if r.random()<.25:stream.append(('obs',r.choice(NOISE),None))
  if r.random()<.20:
   nv=r.choice([x for x in VAL if x!=v]);truth[e]=nv;obs2=OBS[2](e,nv);q2=Q[1](e);triples.append((obs2,q2,f'{nv}です。',neg));stream.append(('obs',obs2,None));stream.append(('q',q2,nv))
 ev=[]
 for _ in range(160):
  e=r.choice(ents);v=truth[e];k=r.choice(['direct','pronoun','variant','distractor','unseen'])
  q=Q[0](e) if k=='direct' else r.choice(PRON)+'はどこですか？' if k=='pronoun' else Q[0](e+'品') if k=='variant' else Q[2](e) if k=='distractor' else e+'を見つけるには、どの場所を探せばよい？';ev.append((k,q,v))
 one=[]
 for i in range(60):
  e='新規'+str(i);v=r.choice(VAL);one.append((r.choice(OBS[:2])(e,v),r.choice(Q[:2])(e),v))
 return triples,stream,ev,one
def run(seed,n):
 triples,stream,ev,one=make(seed,n);out={};s=SurfaceNearest();t=time.perf_counter()
 for typ,text,a in stream:
  if typ=='obs':s.observe(text)
 train=time.perf_counter()-t;by=defaultdict(list);t=time.perf_counter()
 for k,q,a in ev:by[k].append(s.answer(q)==a)
 inf=(time.perf_counter()-t)/len(ev)*1000;out['surface']={k:sum(v)/len(v) for k,v in by.items()};out['surface'].update(train_s=train,inference_ms=inf,model_bytes=len(pickle.dumps(s)),reads=len(s.obs),revoked=0,one_shot=0.0)
 m=PredictiveGrouping();t=time.perf_counter();m.fit_suffix([x[2] for x in triples])
 for obs,q,resp,neg in triples:m.train_triple(obs,q,resp,neg)
 for typ,text,a in stream:
  if typ=='obs':m.observe(text);m.ingest_one_shot(text)
 train=time.perf_counter()-t;by=defaultdict(list);t=time.perf_counter()
 for k,q,a in ev:by[k].append(m.answer(q)==a)
 inf=(time.perf_counter()-t)/len(ev)*1000;one_acc=[]
 for obs,q,a in one:m.observe(obs);m.ingest_one_shot(obs);one_acc.append(m.answer(q)==a)
 serial={'schemas':{k:{'support':v['support'],'harm':v['harm'],'answer_pos':dict(v['answer_pos'])} for k,v in m.schemas.items()},'bindings':{str(k):v for k,v in m.bindings.items()}}
 out['predictive_grouping']={k:sum(v)/len(v) for k,v in by.items()};out['predictive_grouping'].update(train_s=train,inference_ms=inf,model_bytes=len(json.dumps(serial,ensure_ascii=False).encode()),reads=len(m.schemas),revoked=m.revoked,one_shot=sum(one_acc)/len(one_acc),schemas=len(m.schemas),bindings=len(m.bindings));return out
runs=[]
for n in [48,180,540]:
 for seed in [1,7,19]:runs.append({'n':n,'seed':seed,'metrics':run(seed,n)})
summary={}
for n in [48,180,540]:
 summary[str(n)]={}
 for model in ['surface','predictive_grouping']:
  keys=runs[0]['metrics'][model].keys();summary[str(n)][model]={k:statistics.mean(r['metrics'][model][k] for r in runs if r['n']==n) for k in keys}
summary['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
print(json.dumps({'hypothesis':'Predictive Retrieval Gain Grouping with Negative Evidence','seeds':[1,7,19],'train_sizes':[48,180,540],'runs':runs,'summary':summary,'free_japanese_integrated_gate':0.0,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False},ensure_ascii=False,indent=2))
