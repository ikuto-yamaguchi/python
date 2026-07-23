from __future__ import annotations
from dataclasses import dataclass, field
from collections import Counter
from functools import lru_cache
import argparse,json,math,pickle,random,resource,statistics,time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
UNSEEN=['測定器ゼータ','搬送台オメガ','記録紙ラムダ','検査枠シグマ']
RELS=['置き場所','状態','担当']
VALS={'置き場所':['棚A','棚B','棚C','棚D'],'状態':['待機','処理中','完了','保留'],'担当':['担当一','担当二','担当三','担当四']}
STATES=['{o}の置き場所は{loc}、状態は{status}、担当は{owner}です。','{o}について、保管先={loc}／進行={status}／受持={owner}。']
CMDS={'置き場所':['{o}を{v}へ移してください。','{o}の保管先を{v}へ変更します。','次から{o}は{v}で保管します。'],'状態':['{o}を{v}にしてください。','{o}の進行状態を{v}へ切り替えます。','次から{o}は{v}扱いです。'],'担当':['{o}を{v}の担当にしてください。','{o}の受け持ちを{v}へ変更します。','{o}は{v}へ引き継ぎます。']}
OMIT={'置き場所':'それを{v}へ移してください。','状態':'その対象を{v}にしてください。','担当':'担当は{v}へ変えてください。'}
QUERIES={'置き場所':['{o}の置き場所は？','{o}の保管先を教えて。','{o}は今どこ？'],'状態':['{o}の状態は？','{o}の進行状況を教えて。','現在の{o}はどういう段階？'],'担当':['{o}の担当は？','{o}の受け持ちは誰？','今の{o}を受け持つ人は？']}
DIST=['別件の資料を確認しました。','今日は気温が高いです。','この文章は更新とは無関係です。']
SEPS=set('、。！？「」『』（）()=：:／ 　\n')

def grams(s):
 s=''.join(s.split());return Counter(s[i:i+n] for n in (1,2,3) for i in range(max(0,len(s)-n+1)))
def cos(a,b):
 d=sum(v*b.get(k,0) for k,v in a.items());na=math.sqrt(sum(v*v for v in a.values()));nb=math.sqrt(sum(v*v for v in b.values()));return d/(na*nb+1e-12)
def diff(a,b):
 l=0
 while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
 r=0
 while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
 return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
@lru_cache(maxsize=4096)
def spans(t,mi=2,ma=12,cap=80):
 z=[]
 for i in range(len(t)):
  for j in range(i+mi,min(len(t),i+ma)+1):
   x=t[i:j]
   if not x.strip() or all(c in SEPS for c in x):continue
   bd=int(i==0 or t[i-1] in SEPS)+int(j==len(t) or t[j:j+1] in SEPS);z.append((bd,len(set(x))/len(x),-len(x),x))
 z.sort(reverse=True);seen=set();out=[]
 for *_,x in z:
  if x not in seen:seen.add(x);out.append(x)
  if len(out)>=cap:break
 return out
def common(texts,exclude=(),cap=8):
 z=[]
 for x in spans(min(texts,key=len),2,14,120):
  if any(e and (x in e or e in x) for e in exclude):continue
  n=sum(x in t for t in texts)
  if n>=2:z.append((n,-len(x),x))
 z.sort(reverse=True);return [x for _,_,x in z[:cap]]

@dataclass
class Episode: before:str;command:str;after:str;queries:list[str];obj:str;rel:str;value:str;session:int;focus:str
@dataclass
class Joint: obj:str;rel_sig:str;cmd_ctx:tuple[str,str];state_ctx:tuple[str,str]
@dataclass
class Endpoint: spans:Counter=field(default_factory=Counter);signature:Counter=field(default_factory=Counter);support:int=0
@dataclass
class Binding:
 oid:int;rid:int;vid:int;state_ctx:tuple[str,str];cmd_ctx:tuple[str,str];write_support:int=0;read_support:int=0;sessions:set=field(default_factory=set);damage:int=0
 def slow(self):return self.write_support>=2 and self.read_support>=1 and len(self.sessions)>=2 and self.damage==0

def state(o,d,f):return STATES[f].format(o=o,loc=d['置き場所'],status=d['状態'],owner=d['担当'])
def build(seed,n,mode):
 r=random.Random(seed);world={};out=[];focus='';objs=UNSEEN if mode=='domain' else OBJECTS
 for t in range(n):
  canon=r.choice(objs);surf=ALIASES.get(canon,canon) if mode=='rename' and r.random()<.8 else canon
  world.setdefault(canon,{x:r.choice(VALS[x]) for x in RELS});rel=r.choice(RELS);new=r.choice([v for v in VALS[rel] if v!=world[canon][rel]])
  form=1 if mode=='alternate' else 0;before=state(surf,world[canon],form)
  cmd=OMIT[rel].format(v=new) if mode=='omitted' else CMDS[rel][2 if mode in ('paraphrase','combined','domain') else r.randrange(2)].format(o=surf,v=new)
  if mode in ('long','combined'):cmd=' '.join(r.choice(DIST) for _ in range(5))+'\n'+cmd
  world[canon][rel]=new;after=state(surf,world[canon],form);qs=[q.format(o=surf) for q in QUERIES[rel]]
  out.append(Episode(before,cmd,after,qs,canon,rel,new,t//4,focus));focus=surf
 return out,world

class Memory:
 def __init__(self,kind):self.kind=kind;self.joints=[];self.objects=[];self.relations=[];self.values=[];self.bindings=[];self.fast_updates=0;self.rejected=0
 def extract(self,e):
  l,r,old,new=diff(e.before,e.after)
  if not new or new not in e.command:return None
  i=e.command.find(new);cc=(e.command[max(0,i-8):i],e.command[i+len(new):i+len(new)+8]);sc=(e.before[:l],e.before[len(e.before)-r:] if r else '');q=' '.join(e.queries)
  oc=common([e.before,e.command,q],(old,new),6)
  if not oc and e.focus:oc=[e.focus]
  rc=common([e.before,q],tuple(oc)+(old,new),8);return new,cc,sc,oc,rc
 def endpoint(self,arr,span,sig,th=.72):
  g=grams(sig);best=None;bs=0
  for i,x in enumerate(arr):
   ss=max((cos(grams(span),grams(s)) for s in x.spans),default=0);score=.45*ss+.55*cos(g,x.signature)
   if score>bs:bs,best=score,i
  if best is None or bs<th:arr.append(Endpoint());best=len(arr)-1
  x=arr[best];x.spans[span]+=1;x.signature.update(g);x.support+=1;return best
 def learn(self,e):
  z=self.extract(e)
  if not z:self.rejected+=1;return
  new,cc,sc,oc,rc=z
  if not oc or not rc:self.rejected+=1;return
  if self.kind=='joint':
   for o in oc[:2]:
    for q in rc[:2]:self.joints.append(Joint(o,q,cc,sc))
   self.joints=self.joints[-64:];return
  oi=self.endpoint(self.objects,oc[0],e.before+' '+e.command+' '+' '.join(e.queries));ri=self.endpoint(self.relations,rc[0],' '.join(e.queries)+' '+sc[0][-10:]+sc[1][:10]);vi=self.endpoint(self.values,new,cc[0]+cc[1]+' '+new,.65)
  b=next((x for x in self.bindings if (x.oid,x.rid,x.vid)==(oi,ri,vi) and x.cmd_ctx==cc),None)
  if b is None:b=Binding(oi,ri,vi,sc,cc);self.bindings.append(b)
  b.write_support+=1;b.sessions.add(e.session);self.fast_updates+=1;qg=grams(' '.join(e.queries))
  if cos(qg,self.objects[oi].signature)>.15 and cos(qg,self.relations[ri].signature)>.15 and new in e.after:b.read_support+=1
  if self.apply(e.before,e.command,b)!=e.after:b.damage+=1
  if len(self.bindings)>96:self.bindings=sorted(self.bindings,key=lambda x:(x.slow(),x.write_support+x.read_support-x.damage),reverse=True)[:96]
 def val(self,cmd,b):
  a,z=b.cmd_ctx;i=cmd.find(a) if a else 0
  if i<0:return None
  st=i+len(a);en=cmd.find(z,st) if z else len(cmd);v=cmd[st:en] if en>=st else ''
  return v if 0<len(v)<=14 else None
 def apply(self,st,cmd,b):
  v=self.val(cmd,b)
  if v is None:return None
  a,z=b.state_ctx;i=st.find(a) if a else 0
  if i<0:return None
  p=i+len(a);q=st.find(z,p) if z else len(st)
  return st[:p]+v+st[q:] if q>=p else None
 def write(self,before,cmd,focus=''):
  cand=[]
  if self.kind=='joint':
   for j in self.joints:
    a,z=j.cmd_ctx;i=cmd.find(a) if a else 0
    if i<0:continue
    p=i+len(a);q=cmd.find(z,p) if z else len(cmd);v=cmd[p:q] if q>=p else ''
    sa,sz=j.state_ctx;k=before.find(sa) if sa else 0
    if k<0:continue
    x=k+len(sa);y=before.find(sz,x) if sz else len(before)
    if y>=x:cand.append((int(j.obj in cmd or j.obj==focus),before[:x]+v+before[y:]))
  else:
   for b in self.bindings:
    if self.kind=='slow' and not b.slow():continue
    out=self.apply(before,cmd,b)
    if out is None:continue
    o=self.objects[b.oid];r=self.relations[b.rid];os=max((int(s in cmd)+.5*int(s==focus) for s in o.spans),default=0);score=os+.35*cos(grams(cmd),r.signature)+.15*(b.write_support+b.read_support)-.4*b.damage;cand.append((score,out))
  if not cand:return before,False,0
  cand.sort(reverse=True)
  if self.kind!='joint' and len(cand)>1 and cand[0][0]-cand[1][0]<.05:return before,False,len(cand)
  return cand[0][1],True,len(cand)
 def read(self,q,states):
  cand=[];qg=grams(q)
  if self.kind=='joint':
   for j in self.joints:
    for s in states:cand.append((cos(qg,grams(j.obj+' '+j.rel_sig))+.2*int(j.obj in s),s))
  else:
   for b in self.bindings:
    if self.kind=='slow' and not b.slow():continue
    o=self.objects[b.oid];r=self.relations[b.rid];os=max((cos(qg,grams(s)) for s in o.spans),default=0);rs=cos(qg,r.signature)
    for st in reversed(states):
     if any(s in st for s in o.spans):cand.append((.55*os+.45*rs+.1*b.read_support-.1*b.damage,st));break
  if not cand:return None,0
  cand.sort(reverse=True)
  if self.kind!='joint' and len(cand)>1 and cand[0][0]-cand[1][0]<.03:return None,len(cand)
  return cand[0][1],len(cand)

def evaluate(seed,n,mode):
 eps,world=build(seed,n,mode);out={}
 for name in ('joint','tri','slow'):
  m=Memory(name);states=[];focus='';wc=0;t=time.perf_counter()
  for e in eps:m.learn(e);p,_,_=m.write(e.before,e.command,focus);wc+=p==e.after;states.append(p);focus=e.obj
  train=time.perf_counter()-t;total=ok=wrong=null=0;t=time.perf_counter()
  for canon,d in world.items():
   surf=ALIASES.get(canon,canon) if mode=='rename' else canon
   for rel in RELS:
    a,_=m.read(QUERIES[rel][-1].format(o=surf),states);total+=1
    if a is None:null+=1
    else:ok+=surf in a and d[rel] in a;wrong+=surf not in a or d[rel] not in a
  out[name]={'write_accuracy':wc/max(1,len(eps)),'read_accuracy':ok/max(1,total),'wrong_read':wrong/max(1,total),'null_rate':null/max(1,total),'model_bytes':len(pickle.dumps(m)),'training_seconds':train,'inference_ms':(time.perf_counter()-t)*1000/max(1,total),'object_nodes':len(m.objects),'relation_nodes':len(m.relations),'value_nodes':len(m.values),'bindings':len(m.bindings),'slow_bindings':sum(x.slow() for x in m.bindings),'fast_updates':m.fast_updates,'rejected':m.rejected}
 return out
def one(seed):
 e=build(seed,1,'seen')[0][0];out={}
 for k in ('joint','tri','slow'):m=Memory(k);m.learn(e);out[k]=int(m.write(e.before,e.command,e.focus)[0]==e.after)
 return out
def interference(seed):
 stream=[]
 for i in range(12):stream+=build(seed+i,1,'seen')[0]
 held,world=build(seed+999,6,'rename');stream+=held;out={}
 for k in ('joint','tri','slow'):
  m=Memory(k);states=[];focus=''
  for e in stream:m.learn(e);p,_,_=m.write(e.before,e.command,focus);states.append(p);focus=e.obj
  total=ok=0
  for canon,d in world.items():
   surf=ALIASES.get(canon,canon)
   for rel in RELS:a,_=m.read(QUERIES[rel][-1].format(o=surf),states);total+=1;ok+=a is not None and surf in a and d[rel] in a
  out[k]=ok/max(1,total)
 return out
def summary(raw):
 out={}
 for n,runs in raw.items():
  out[n]={}
  for mode in ('seen','paraphrase','rename','alternate','omitted','long','combined','domain'):
   out[n][mode]={}
   for method in ('joint','tri','slow'):
    out[n][mode][method]={k:statistics.mean(r[mode][method][k] for r in runs) for k in runs[0][mode][method]}
  out[n]['one_shot']={k:statistics.mean(r['one_shot'][k] for r in runs) for k in ('joint','tri','slow')};out[n]['interference']={k:statistics.mean(r['interference'][k] for r in runs) for k in ('joint','tri','slow')}
 return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='MEASUREMENTS_CYCLE_021.json');a=ap.parse_args();raw={}
 for n in (6,12):
  runs=[]
  for seed in (1,7,19):
   r={m:evaluate(seed,n,m) for m in ('seen','paraphrase','rename','alternate','omitted','long','combined','domain')};r['one_shot']=one(seed);r['interference']=interference(seed);runs.append(r)
  raw[str(n)]=runs
 payload={'hypothesis':'Tri-Factor Endpoint Memory with Independent Object, Relation, and Value Reconsolidation','seeds':[1,7,19],'sizes':[6,12],'raw':raw,'summary':summary(raw),'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'proposal O(L^2), endpoint matching O((O+R+V)G), sparse read/write O(kBG), B<=96','hidden_labels_used_by_learner':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
 with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
 print(json.dumps(payload['summary']['12'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
