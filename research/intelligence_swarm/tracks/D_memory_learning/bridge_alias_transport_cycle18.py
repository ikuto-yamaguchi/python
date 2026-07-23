from __future__ import annotations
from dataclasses import dataclass, field
from collections import Counter
import json, random, time, pickle, resource, statistics, math, argparse
OBJECTS=['青い箱','赤い箱','小型端末','大型端末']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末'}
FIELDS=['場所','状態']; VALUES={'場所':['棚A','棚B','棚C'],'状態':['待機','処理中','完了']}
STATE=['{o}の場所は{場所}、状態は{状態}です。','{o}：保管先={場所}／進行={状態}。']
CMD={'場所':['{o}を{v}へ移してください。','{o}の保管先を{v}へ変更します。'],'状態':['{o}を{v}にしてください。','{o}の進行を{v}へ切り替えます。']}
HELD={'場所':'対象{o}、次から{v}で保管。','状態':'対象{o}は以後{v}扱い。'}
QUERY={'場所':'{o}の場所は？','状態':'{o}の状態は？'}
DIST=['別件を確認しました。','今日は暑いです。']
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
def varpair(a,b):
 l=0
 while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
 r=0
 while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
 x=a[l:len(a)-r if r else len(a)];y=b[l:len(b)-r if r else len(b)]
 return (x,y) if 2<=len(x)<=10 and 2<=len(y)<=10 else None
@dataclass
class Ep:
 before:str;cmd:str;after:str;query:str;obj:str;field:str;value:str;session:int
@dataclass
class Link:
 a:str;b:str;fw:int=0;rv:int=0;sessions:set=field(default_factory=set);damage:int=0
 def active(self,kind):
  if kind=='bidir':return self.fw>0 and self.rv>0
  if kind=='slow':return self.fw>=2 and self.rv>=2 and len(self.sessions)>=2 and self.damage==0
  return False

def mkstate(o,d,form):return STATE[form].format(o=o,**d)
def build(seed,n,mode):
 rng=random.Random(seed);world={};eps=[];sess=0
 for i in range(n):
  o=rng.choice(OBJECTS);a=ALIASES[o];world.setdefault(o,{f:rng.choice(VALUES[f]) for f in FIELDS});f=rng.choice(FIELDS);v=rng.choice([x for x in VALUES[f] if x!=world[o][f]])
  surf=a if mode in ('rename','combined') and rng.random()<.5 else o;form=1 if mode in ('alternate','combined') else 0
  before=mkstate(surf,world[o],form);cmd=(HELD[f] if mode=='held' else rng.choice(CMD[f])).format(o=surf,v=v);world[o][f]=v;after=mkstate(surf,world[o],form);q=QUERY[f].format(o=surf)
  eps.append(Ep(before,cmd,after,q,o,f,v,sess));sess+=1
  if mode in ('rename','combined') and rng.random()<.6:
   other=o if surf==a else a;eps.append(Ep(before.replace(surf,other),cmd.replace(surf,other),after.replace(surf,other),q.replace(surf,other),o,f,v,sess));sess+=1
 return eps,world
class Mem:
 def __init__(self,kind):self.kind=kind;self.eps=[];self.links={};self.fast=0
 def learn(self,e,hist):
  for h in hist[-2:]:
   ps=[]
   for x,y in ((h.before,e.before),(h.cmd,e.cmd),(h.after,e.after),(h.query,e.query)):
    p=varpair(x,y)
    if p:ps.append(p)
   for a,b in ps:
    key=tuple(sorted((a,b)));ln=self.links.setdefault(key,Link(*key));ht=(h.before,h.cmd,h.after,h.query);et=(e.before,e.cmd,e.after,e.query)
    fw=tuple(z.replace(a,b) for z in ht)==et;rv=tuple(z.replace(b,a) for z in et)==ht
    ln.fw+=fw;ln.rv+=rv
    if fw or rv:ln.sessions.update((h.session,e.session));self.fast+=1
  self.eps.append(e);self.eps=self.eps[-64:]
 def aset(self,x):
  out={x}
  for ln in self.links.values():
   if ln.active(self.kind):
    if ln.a in out:out.add(ln.b)
    if ln.b in out:out.add(ln.a)
  return out
 def write(self,before,cmd):
  best=None;bs=-1
  for e in self.eps:
   variants=[(e.before,e.cmd,e.after)]
   for ln in self.links.values():
    if ln.active(self.kind):
     variants.append((e.before.replace(ln.a,ln.b),e.cmd.replace(ln.a,ln.b),e.after.replace(ln.a,ln.b)))
     variants.append((e.before.replace(ln.b,ln.a),e.cmd.replace(ln.b,ln.a),e.after.replace(ln.b,ln.a)))
   for tb,tc,ta in variants:
    s=cos(grams(cmd),grams(tc))+.25*cos(grams(before),grams(tb))
    if s>bs:bs=s;best=(tb,tc,ta)
  if not best or bs<.6:return before,False
  tb,tc,ta=best;l,r,old,new=diff(tb,ta);_,_,_,cv=diff(tc,cmd);val=cv if 0<len(cv)<=8 else new
  return before[:l]+val+(before[len(before)-r:] if r else ''),True
 def read(self,q,states):
  best=None;bs=-1
  for st in states:
   s=cos(grams(q),grams(st))
   for ln in self.links.values():
    if ln.active(self.kind):s=max(s,cos(grams(q.replace(ln.a,ln.b)),grams(st)),cos(grams(q.replace(ln.b,ln.a)),grams(st)))
   if s>bs:bs=s;best=st
  return best if bs>.2 else None

def evalone(seed,n,mode):
 train,_=build(seed,n,mode);test,truth=build(seed+1000,max(12,n//2),mode);out={}
 for kind in ('none','bidir','slow'):
  m=Mem(kind);hist=[]
  t=time.perf_counter()
  for e in train:m.learn(e,hist);hist.append(e)
  tr=time.perf_counter()-t;states=[];wc=0;t=time.perf_counter()
  for e in test:
   p,_=m.write(e.before,e.cmd);states.append(p);wc+=p==e.after
  infer_write=time.perf_counter()-t;rc=wrong=tot=0;t=time.perf_counter()
  for o,d in truth.items():
   surf=ALIASES[o] if mode in ('rename','combined') else o
   for f in FIELDS:
    st=m.read(QUERY[f].format(o=surf),states);tot+=1
    if st and (surf in st or o in st) and d[f] in st:rc+=1
    elif st:wrong+=1
  read_ms=(time.perf_counter()-t)*1000/max(1,tot)
  out[kind]={'write_accuracy':wc/max(1,len(test)),'read_accuracy':rc/max(1,tot),'wrong_read':wrong/max(1,tot),'links':len(m.links),'slow_links':sum(x.active('slow') for x in m.links.values()),'model_bytes':len(pickle.dumps(m)),'training_seconds':tr,'inference_ms':(infer_write*1000/max(1,len(test)))+read_ms,'fast_updates':m.fast}
 return out

def one_shot(seed):
 eps,_=build(seed,1,'rename');r={}
 for k in ('none','bidir','slow'):
  m=Mem(k);h=[]
  for e in eps:m.learn(e,h);h.append(e)
  p,_=m.write(eps[-1].before,eps[-1].cmd);r[k]=float(p==eps[-1].after)
 return r

def interference(seed):
 eps,_=build(seed,10,'rename');noise,_=build(seed+50,24,'combined');r={}
 for k in ('none','bidir','slow'):
  m=Mem(k);h=[];states=[]
  for e in eps+noise:m.learn(e,h);h.append(e);p,_=m.write(e.before,e.cmd);states.append(p)
  ok=0
  for o,a in ALIASES.items():ok+=m.read(f'{a}の場所は？',states) is not None
  r[k]=ok/len(ALIASES)
 return r

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output');a=ap.parse_args();raw={}
 for n in (12,24,48):
  runs=[]
  for seed in (1,7,19):
   x={m:evalone(seed,n,m) for m in ('seen','held','rename','alternate','combined')};x['one_shot']=one_shot(seed);x['interference']=interference(seed);runs.append(x)
  raw[str(n)]=runs
 summary={}
 for n,runs in raw.items():
  summary[n]={}
  for mode in ('seen','held','rename','alternate','combined'):
   summary[n][mode]={}
   for k in ('none','bidir','slow'):
    summary[n][mode][k]={m:statistics.mean(x[mode][k][m] for x in runs) for m in runs[0][mode][k]}
  summary[n]['one_shot']={k:statistics.mean(x['one_shot'][k] for x in runs) for k in ('none','bidir','slow')};summary[n]['interference']={k:statistics.mean(x['interference'][k] for x in runs) for k in ('none','bidir','slow')}
 payload={'hypothesis':'Bridge-Episode Alias Equivalence by Reversible State-Trajectory Transport','seeds':[1,7,19],'sizes':[12,24,48],'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'bridge O(NWH), read/write O(EK G), E<=64','hidden_labels_used_by_learner':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
 open(a.output,'w',encoding='utf-8').write(json.dumps(payload,ensure_ascii=False,indent=2));print(json.dumps(summary['48'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
