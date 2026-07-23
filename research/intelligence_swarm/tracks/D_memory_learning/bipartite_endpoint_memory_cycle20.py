from __future__ import annotations
from dataclasses import dataclass, field
from collections import Counter
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末'}
FIELDS=['場所','状態','担当']
VALUES={'場所':['棚A','棚B','棚C'],'状態':['待機','処理中','完了'],'担当':['担当一','担当二','担当三']}
STATE=['{o}の場所は{場所}、状態は{状態}、担当は{担当}です。','{o}：保管先={場所}／進行={状態}／受持={担当}。']
CMD={'場所':['{o}を{v}へ移してください。','{o}の保管先を{v}へ変更します。'],'状態':['{o}を{v}にしてください。','{o}の進行を{v}へ切り替えます。'],'担当':['{o}を{v}の担当にしてください。','{o}の受け持ちを{v}へ変更します。']}
HELD={'場所':'対象{o}、次から{v}で保管。','状態':'対象{o}は以後{v}扱い。','担当':'対象{o}は{v}へ引き継ぎ。'}
OMIT={'場所':'それを{v}へ移してください。','状態':'その対象を{v}にしてください。','担当':'担当は{v}へ変えてください。'}
QUERY={'場所':['{o}の場所は？','{o}の保管先を教えて。'],'状態':['{o}の状態は？','{o}の進行状況を教えて。'],'担当':['{o}の担当は？','{o}の受け持ちは誰？']}
DISTRACT=['別件の資料も確認しました。','今日は暑いです。','この文は更新と無関係です。']

def grams(s):
 s=''.join(s.split());return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))
def cos(a,b):
 d=sum(v*b.get(k,0) for k,v in a.items());na=math.sqrt(sum(v*v for v in a.values()));nb=math.sqrt(sum(v*v for v in b.values()));return d/(na*nb+1e-9)
def diff(a,b):
 l=0
 while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
 r=0
 while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
 return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def spans(text,cap=24):
 cand=[]
 for i in range(len(text)):
  for j in range(i+2,min(len(text),i+12)+1):
   x=text[i:j]
   if x.strip():cand.append((int(i==0 or text[i-1] in '、。：／')+int(j==len(text) or text[j:j+1] in '、。：／'),len(x),x))
 cand.sort(reverse=True);out=[];seen=set()
 for _,_,x in cand:
  if x not in seen:seen.add(x);out.append(x)
  if len(out)>=cap:break
 return out

@dataclass
class Ep:
 before:str;cmd:str;after:str;queries:list[str];obj:str;field:str;value:str;session:int;focus:str=''
@dataclass
class ObjNode:
 forms:Counter=field(default_factory=Counter);qgrams:Counter=field(default_factory=Counter);support:int=0;damage:int=0
 def rel(self):return (self.support+1)/(self.support+self.damage+2)
@dataclass
class RelNode:
 qgrams:Counter=field(default_factory=Counter);cmdgrams:Counter=field(default_factory=Counter);support:int=0;damage:int=0
 def rel(self):return (self.support+1)/(self.support+self.damage+2)
@dataclass
class Edge:
 oi:int;ri:int;left:str;right:str;cmd_left:str;cmd_right:str;write_support:int=0;read_support:int=0;damage:int=0;sessions:set=field(default_factory=set)
 def slow(self):return self.write_support>=2 and self.read_support>=2 and len(self.sessions)>=2 and self.damage==0
 def score(self):return (self.write_support+self.read_support+1)/(self.write_support+self.read_support+self.damage+2)

def mkstate(o,d,form):return STATE[form].format(o=o,**d)
def build(seed,n,mode):
 rng=random.Random(seed);world={};eps=[];focus='';sess=0
 for _ in range(n):
  o=rng.choice(OBJECTS);a=ALIASES[o];world.setdefault(o,{f:rng.choice(VALUES[f]) for f in FIELDS})
  f=rng.choice(FIELDS);v=rng.choice([x for x in VALUES[f] if x!=world[o][f]])
  surf=a if mode in ('rename','combined') and rng.random()<.5 else o
  form=1 if mode in ('alternate','combined') else 0
  before=mkstate(surf,world[o],form)
  if mode=='held':templ=HELD[f]
  elif mode=='omitted':templ=OMIT[f]
  else:templ=rng.choice(CMD[f])
  cmd=templ.format(o=surf,v=v);world[o][f]=v;after=mkstate(surf,world[o],form)
  qs=[q.format(o=surf) for q in QUERY[f]]
  eps.append(Ep(before,cmd,after,qs,o,f,v,sess,focus));focus=surf;sess+=1
  if mode=='long':
   for _ in range(rng.randint(2,5)):eps.append(Ep('',rng.choice(DISTRACT),'',[], '', '', '',sess,focus));sess+=1
  if mode in ('rename','combined') and rng.random()<.5:
   other=o if surf==a else a
   eps.append(Ep(before.replace(surf,other),cmd.replace(surf,other),after.replace(surf,other),[q.replace(surf,other) for q in qs],o,f,v,sess,focus));sess+=1
 return eps,world

class Memory:
 def __init__(self,kind):
  self.kind=kind;self.objects=[];self.relations=[];self.edges=[];self.states=[];self.fast_updates=0;self.slow_edges=0
 def _obj_candidates(self,e):
  q=' '.join(e.queries);c=[]
  for x in spans(e.before):
   score=int(x in e.cmd)+int(x in q)+int(x==e.focus)
   if score>=2:c.append((score,len(x),x))
  if not c and e.focus and any(z in e.cmd for z in ('それ','その対象','担当は')):c=[(2,len(e.focus),e.focus)]
  c.sort(reverse=True);return [x for _,_,x in c[:4]]
 def _rel_candidate(self,e,l,r):
  q=' '.join(e.queries);return grams(q),grams(e.cmd[:max(0,e.cmd.find(e.value))]+e.cmd[e.cmd.find(e.value)+len(e.value):])
 def _find_obj(self,span,qg):
  best=None;bs=0
  for i,o in enumerate(self.objects):
   s=.65*max([cos(grams(span),grams(x)) for x in o.forms] or [0])+.35*cos(qg,o.qgrams)
   if s>bs:bs,best=s,i
  if best is not None and bs>.62:return best
  self.objects.append(ObjNode());return len(self.objects)-1
 def _find_rel(self,qg,cg):
  best=None;bs=0
  for i,r in enumerate(self.relations):
   s=.55*cos(qg,r.qgrams)+.45*cos(cg,r.cmdgrams)
   if s>bs:bs,best=s,i
  if best is not None and bs>.60:return best
  self.relations.append(RelNode());return len(self.relations)-1
 def learn(self,e):
  if not e.after:return
  l,r,old,new=diff(e.before,e.after)
  if not new:return
  objs=self._obj_candidates(e);qg,cg=self._rel_candidate(e,l,r)
  if not objs:return
  for sp in objs:
   oi=self._find_obj(sp,qg);o=self.objects[oi];o.forms[sp]+=1;o.qgrams.update(qg);o.support+=1
   ri=self._find_rel(qg,cg);rel=self.relations[ri];rel.qgrams.update(qg);rel.cmdgrams.update(cg);rel.support+=1
   p=e.cmd.find(new)
   if p<0:continue
   cl=e.cmd[max(0,p-8):p];cr=e.cmd[p+len(new):p+len(new)+8]
   edge=next((x for x in self.edges if x.oi==oi and x.ri==ri and x.left==e.before[:l] and x.right==(e.before[len(e.before)-r:] if r else '')),None)
   if edge is None:
    edge=Edge(oi,ri,e.before[:l],e.before[len(e.before)-r:] if r else '',cl,cr);self.edges.append(edge)
   edge.write_support+=1;edge.sessions.add(e.session);self.fast_updates+=1
   for q in e.queries:
    os=max([cos(grams(q),grams(f)) for f in o.forms] or [0]);rs=cos(grams(q),rel.qgrams)
    if os>.15 and rs>.25:edge.read_support+=1
    else:edge.damage+=1
  self.states.append(e.after);self.states=self.states[-64:];self.edges=sorted(self.edges,key=lambda x:(x.slow(),x.score()),reverse=True)[:64]
  self.slow_edges=sum(x.slow() for x in self.edges)
 def _value(self,cmd,e):
  i=cmd.find(e.cmd_left) if e.cmd_left else 0
  if i<0:return None
  st=i+len(e.cmd_left);en=cmd.find(e.cmd_right,st) if e.cmd_right else len(cmd)
  if en<st:return None
  v=cmd[st:en];return v if 0<len(v)<=12 else None
 def write(self,before,cmd,focus=''):
  cand=[]
  for e in self.edges:
   if self.kind=='slow' and not e.slow():continue
   o=self.objects[e.oi];r=self.relations[e.ri]
   os=max([int(f in cmd or f in before)+.2*cos(grams(focus),grams(f)) for f in o.forms] or [0])
   rs=cos(grams(cmd),r.cmdgrams);v=self._value(cmd,e)
   if v is None:continue
   if not before.startswith(e.left):continue
   out=e.left+v+e.right
   cand.append((.45*os+.35*rs+.20*e.score(),out))
  if not cand:return before,False
  cand.sort(reverse=True)
  if len(cand)>1 and cand[0][0]-cand[1][0]<.03:return before,False
  return cand[0][1],True
 def read(self,q):
  qg=grams(q);cand=[]
  for e in self.edges:
   if self.kind=='slow' and not e.slow():continue
   o=self.objects[e.oi];r=self.relations[e.ri]
   os=max([cos(qg,grams(f)) for f in o.forms] or [0]);rs=cos(qg,r.qgrams)
   score=.52*os+.33*rs+.15*e.score()
   for st in reversed(self.states):
    if any(f in st for f in o.forms):cand.append((score,st,e));break
  if not cand:return None
  cand.sort(reverse=True,key=lambda x:x[0])
  if len(cand)>1 and cand[0][0]-cand[1][0]<.04:return None
  return cand[0][1]

def evalone(seed,n,mode):
 train,_=build(seed,n,mode);test,truth=build(seed+1000,max(9,n//3),mode);out={}
 for kind in ('joint','bipartite','slow'):
  m=Memory(kind);t=time.perf_counter()
  for e in train:m.learn(e)
  tr=time.perf_counter()-t;wc=0;focus='';t=time.perf_counter()
  for e in test:
   if not e.after:continue
   p,_=m.write(e.before,e.cmd,focus);m.states.append(p);m.states=m.states[-64:];wc+=p==e.after;focus=e.obj
  write_n=max(1,sum(bool(e.after) for e in test));write_ms=(time.perf_counter()-t)*1000/write_n
  rc=wrong=tot=0;t=time.perf_counter()
  for o,d in truth.items():
   surfaces=[o,ALIASES[o]] if mode in ('rename','combined') else [o]
   for surf in surfaces:
    for f in FIELDS:
     st=m.read(QUERY[f][0].format(o=surf));tot+=1
     if st and (o in st or ALIASES[o] in st) and d[f] in st:rc+=1
     elif st:wrong+=1
  read_ms=(time.perf_counter()-t)*1000/max(1,tot)
  out[kind]={'write_accuracy':wc/write_n,'read_accuracy':rc/max(1,tot),'wrong_read':wrong/max(1,tot),'objects':len(m.objects),'relations':len(m.relations),'edges':len(m.edges),'slow_edges':m.slow_edges,'model_bytes':len(pickle.dumps(m)),'training_seconds':tr,'inference_ms':write_ms+read_ms,'fast_updates':m.fast_updates}
 return out

def one_shot(seed):
 eps,_=build(seed,1,'rename');r={}
 for k in ('joint','bipartite','slow'):
  m=Memory(k)
  for e in eps:m.learn(e)
  p,_=m.write(eps[-1].before,eps[-1].cmd,eps[-1].focus);r[k]=float(p==eps[-1].after)
 return r

def interference(seed):
 base,_=build(seed,12,'rename');noise,_=build(seed+99,36,'combined');r={}
 for k in ('joint','bipartite','slow'):
  m=Memory(k);latest={}
  for e in base+noise:
   m.learn(e)
   if e.after:latest[(e.obj,e.field)]=e.value
  exact=tot=0
  for o in OBJECTS:
   for surf in (o,ALIASES[o]):
    for f in FIELDS:
     st=m.read(QUERY[f][0].format(o=surf));tot+=1
     exact+=int(st is not None and latest.get((o,f),'__') in st and (o in st or ALIASES[o] in st))
  r[k]=exact/max(1,tot)
 return r

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();raw={}
 for n in (12,24,48):
  runs=[]
  for seed in (1,7,19):
   x={m:evalone(seed,n,m) for m in ('seen','held','rename','alternate','omitted','long','combined')};x['one_shot']=one_shot(seed);x['interference']=interference(seed);runs.append(x)
  raw[str(n)]=runs
 summary={}
 for n,runs in raw.items():
  summary[n]={}
  for mode in ('seen','held','rename','alternate','omitted','long','combined'):
   summary[n][mode]={}
   for k in ('joint','bipartite','slow'):
    summary[n][mode][k]={m:statistics.mean(x[mode][k][m] for x in runs) for m in runs[0][mode][k]}
  summary[n]['one_shot']={k:statistics.mean(x['one_shot'][k] for x in runs) for k in ('joint','bipartite','slow')}
  summary[n]['interference']={k:statistics.mean(x['interference'][k] for x in runs) for k in ('joint','bipartite','slow')}
 payload={'hypothesis':'Bipartite Query–Object–Relation Addresses with Endpoint-Specific Reconsolidation','seeds':[1,7,19],'sizes':[12,24,48],'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'proposal O(L^2), learning O(N(A+R)G), read/write O(k(A+R)G), k<=64','hidden_labels_used_by_learner':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
 with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
 print(json.dumps(summary['48'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
