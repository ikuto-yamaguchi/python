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
QUERY={'場所':['{o}の場所は？','{o}の保管先を教えて。'],'状態':['{o}の状態は？','{o}の進行状況を教えて。'],'担当':['{o}の担当は？','{o}の受け持ちは誰？']}

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
 return (x,y) if 2<=len(x)<=12 and 2<=len(y)<=12 else None

@dataclass
class Ep:
 before:str;cmd:str;after:str;queries:list[str];obj:str;field:str;value:str;session:int
@dataclass
class Link:
 a:str;b:str;fw:int=0;rv:int=0;sessions:set=field(default_factory=set)
 positive:Counter=field(default_factory=Counter)
 damage:Counter=field(default_factory=Counter)
 nulls:Counter=field(default_factory=Counter)
 def bridge(self): return self.fw>0 and self.rv>0
 def selective(self):
  if not self.bridge() or not self.positive:return False
  total_pos=sum(self.positive.values());total_damage=sum(self.damage.values())
  supported=sum(1 for v in self.positive.values() if v>0)
  return total_pos>=3 and supported>=2 and total_damage==0
 def slow(self): return self.selective() and len(self.sessions)>=2 and sum(self.positive.values())>=5

def qsig(q,span):
 return tuple(sorted(grams(q.replace(span,'<X>')).items()))
def mkstate(o,d,form):return STATE[form].format(o=o,**d)
def build(seed,n,mode):
 rng=random.Random(seed);world={};eps=[];sess=0
 for _ in range(n):
  o=rng.choice(OBJECTS);a=ALIASES[o];world.setdefault(o,{f:rng.choice(VALUES[f]) for f in FIELDS})
  f=rng.choice(FIELDS);v=rng.choice([x for x in VALUES[f] if x!=world[o][f]])
  surf=a if mode in ('rename','combined') and rng.random()<.5 else o
  form=1 if mode in ('alternate','combined') else 0
  before=mkstate(surf,world[o],form);template=HELD[f] if mode=='held' else rng.choice(CMD[f])
  cmd=template.format(o=surf,v=v);world[o][f]=v;after=mkstate(surf,world[o],form)
  qs=[q.format(o=surf) for q in QUERY[f]]
  eps.append(Ep(before,cmd,after,qs,o,f,v,sess));sess+=1
  if mode in ('rename','combined') and rng.random()<.65:
   other=o if surf==a else a
   eps.append(Ep(before.replace(surf,other),cmd.replace(surf,other),after.replace(surf,other),[q.replace(surf,other) for q in qs],o,f,v,sess));sess+=1
 return eps,world

class Mem:
 def __init__(self,kind):
  self.kind=kind;self.eps=[];self.links={};self.fast=0;self.matrix_updates=0
 def active(self,ln):
  return ln.bridge() if self.kind=='bidir' else ln.selective() if self.kind=='selective' else ln.slow() if self.kind=='slow' else False
 def learn(self,e,hist):
  for h in hist[-3:]:
   pairs=[];views=[(h.before,e.before),(h.cmd,e.cmd),(h.after,e.after)]
   for hq,eq in zip(h.queries,e.queries):views.append((hq,eq))
   for x,y in views:
    p=varpair(x,y)
    if p:pairs.append(p)
   for a,b in pairs:
    key=tuple(sorted((a,b)));ln=self.links.setdefault(key,Link(*key))
    hv=(h.before,h.cmd,h.after,*h.queries);ev=(e.before,e.cmd,e.after,*e.queries)
    fw=tuple(z.replace(a,b) for z in hv)==ev;rv=tuple(z.replace(b,a) for z in ev)==hv
    ln.fw+=fw;ln.rv+=rv
    if fw or rv:ln.sessions.update((h.session,e.session));self.fast+=1
  self.eps.append(e);self.eps=self.eps[-64:]
  for ln in self.links.values():
   if not ln.bridge():continue
   for ep in self.eps[-6:]:
    for q in ep.queries:
     if ln.a not in q and ln.b not in q:continue
     src=ln.a if ln.a in q else ln.b;dst=ln.b if src==ln.a else ln.a
     tq=q.replace(src,dst);sig=qsig(q,src)
     candidates=[x.after for x in self.eps[-16:] if dst in x.after]
     if not candidates:
      ln.nulls[sig]+=1;continue
     best=max(candidates,key=lambda st:cos(grams(tq),grams(st)))
     masked_q=tq.replace(dst,'<X>');masked_st=best.replace(dst,'<X>')
     compat=cos(grams(masked_q),grams(masked_st))
     if dst in best and compat>.05:ln.positive[sig]+=1
     else:ln.damage[sig]+=1
     for other in self.links.values():
      if other is ln:continue
      if (other.a in best or other.b in best) and src not in best and dst not in best:ln.damage[sig]+=1
     self.matrix_updates+=1
 def variants(self,e):
  out=[(e.before,e.cmd,e.after)]
  for ln in self.links.values():
   if self.active(ln):
    out.append((e.before.replace(ln.a,ln.b),e.cmd.replace(ln.a,ln.b),e.after.replace(ln.a,ln.b)))
    out.append((e.before.replace(ln.b,ln.a),e.cmd.replace(ln.b,ln.a),e.after.replace(ln.b,ln.a)))
  return out
 def write(self,before,cmd):
  best=None;bs=-1
  for e in self.eps:
   for tb,tc,ta in self.variants(e):
    s=cos(grams(cmd),grams(tc))+.25*cos(grams(before),grams(tb))
    if s>bs:bs=s;best=(tb,tc,ta)
  if not best or bs<.6:return before,False
  tb,tc,ta=best;l,r,old,new=diff(tb,ta);_,_,_,cv=diff(tc,cmd);val=cv if 0<len(cv)<=10 else new
  return before[:l]+val+(before[len(before)-r:] if r else ''),True
 def read(self,q,states):
  best=None;bs=-1;qvars=[q]
  for ln in self.links.values():
   if self.active(ln):qvars.extend((q.replace(ln.a,ln.b),q.replace(ln.b,ln.a)))
  for st in states:
   s=max(cos(grams(v),grams(st)) for v in qvars)
   if s>bs:bs=s;best=st
  return best if bs>.2 else None

def evalone(seed,n,mode):
 train,_=build(seed,n,mode);test,truth=build(seed+1000,max(9,n//3),mode);out={}
 for kind in ('none','bidir','selective','slow'):
  m=Mem(kind);hist=[];t=time.perf_counter()
  for e in train:m.learn(e,hist);hist.append(e)
  tr=time.perf_counter()-t;states=[];wc=0;t=time.perf_counter()
  for e in test:
   p,_=m.write(e.before,e.cmd);states.append(p);wc+=p==e.after
  write_ms=(time.perf_counter()-t)*1000/max(1,len(test));rc=wrong=tot=0;t=time.perf_counter()
  for o,d in truth.items():
   surfaces=[o,ALIASES[o]] if mode in ('rename','combined') else [o]
   for surf in surfaces:
    for f in FIELDS:
     st=m.read(QUERY[f][0].format(o=surf),states);tot+=1
     if st and (o in st or ALIASES[o] in st) and d[f] in st:rc+=1
     elif st:wrong+=1
  read_ms=(time.perf_counter()-t)*1000/max(1,tot)
  out[kind]={'write_accuracy':wc/max(1,len(test)),'read_accuracy':rc/max(1,tot),'wrong_read':wrong/max(1,tot),'links':len(m.links),'active_links':sum(m.active(x) for x in m.links.values()),'selective_links':sum(x.selective() for x in m.links.values()),'slow_links':sum(x.slow() for x in m.links.values()),'model_bytes':len(pickle.dumps(m)),'training_seconds':tr,'inference_ms':write_ms+read_ms,'fast_updates':m.fast,'matrix_updates':m.matrix_updates}
 return out

def one_shot(seed):
 eps,_=build(seed,1,'rename');r={}
 for k in ('none','bidir','selective','slow'):
  m=Mem(k);h=[]
  for e in eps:m.learn(e,h);h.append(e)
  p,_=m.write(eps[-1].before,eps[-1].cmd);r[k]=float(p==eps[-1].after)
 return r

def interference(seed):
 base,_=build(seed,8,'rename');noise,_=build(seed+50,16,'combined');r={}
 for k in ('none','bidir','selective','slow'):
  m=Mem(k);h=[];states=[]
  for e in base+noise:m.learn(e,h);h.append(e);p,_=m.write(e.before,e.cmd);states.append(p)
  exact=tot=0;latest={}
  for e in base+noise:latest[(e.obj,e.field)]=e.value
  for o in OBJECTS:
   for surf in (o,ALIASES[o]):
    for f in FIELDS:
     st=m.read(QUERY[f][0].format(o=surf),states);tot+=1
     exact+=int(st is not None and latest.get((o,f),'__') in st and (o in st or ALIASES[o] in st))
  r[k]=exact/max(1,tot)
 return r

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();raw={}
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
   for k in ('none','bidir','selective','slow'):
    summary[n][mode][k]={m:statistics.mean(x[mode][k][m] for x in runs) for m in runs[0][mode][k]}
  summary[n]['one_shot']={k:statistics.mean(x['one_shot'][k] for x in runs) for k in ('none','bidir','selective','slow')}
  summary[n]['interference']={k:statistics.mean(x['interference'][k] for x in runs) for k in ('none','bidir','selective','slow')}
 payload={'hypothesis':'Relation-Selective Bridge Links by Cross-Query Consequence Matrices','seeds':[1,7,19],'sizes':[12,24,48],'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'bridge O(NWH), consequence O(LQE), read/write O(EKG), E<=64','hidden_labels_used_by_learner':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
 open(a.output,'w',encoding='utf-8').write(json.dumps(payload,ensure_ascii=False,indent=2));print(json.dumps(summary['48'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
