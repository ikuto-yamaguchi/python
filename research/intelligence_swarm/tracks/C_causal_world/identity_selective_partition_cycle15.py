from __future__ import annotations
import argparse,json,math,pickle,random,resource,statistics,time
from collections import Counter
from dataclasses import dataclass
OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵']
FIELDS=['置き場所','状態','担当']
VALUES={'置き場所':['棚A','棚B','棚C','棚D'],'状態':['待機','処理中','完了','保留'],'担当':['担当一','担当二','担当三','担当四']}
STATE_FORMS=['{o}の置き場所は{loc}。{o}の状態は{status}。{o}の担当は{owner}。','{o}について、保管先={loc}。進行={status}。受持={owner}。']
CMD={'置き場所':['{o}を{v}へ移してください。','{o}の保管先を{v}へ変更します。'],'状態':['{o}を{v}にしてください。','{o}の進行を{v}へ切り替えます。'],'担当':['{o}を{v}の担当にしてください。','{o}の受持を{v}へ変更します。']}
HELD={'置き場所':['対象{o}、次から{v}で保管。'],'状態':['対象{o}は以後{v}扱い。'],'担当':['{o}は{v}へ引き継ぎ。']}
OMIT={'置き場所':['それを{v}へ移してください。'],'状態':['その対象を{v}にしてください。'],'担当':['担当は{v}へ変えてください。']}
DIST=['別件の資料を確認しました。','今日は気温が高いです。','これは更新とは無関係です。']
def grams(s):
 s=''.join(s.split());return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))
def cos(a,b):
 d=sum(v*b.get(k,0) for k,v in a.items());na=math.sqrt(sum(v*v for v in a.values()));nb=math.sqrt(sum(v*v for v in b.values()));return d/(na*nb+1e-12)
def cls(s):return [x+'。' for x in s.split('。') if x]
def changed(b,a):
 bc,ac=cls(b),cls(a);return [(i,x,y) for i,(x,y) in enumerate(zip(bc,ac)) if x!=y]
def common(a,b):
 best=''
 for i in range(len(a)):
  for j in range(i+2,len(a)+1):
   x=a[i:j]
   if len(x)>len(best) and x in b:best=x
 return best
def around(s,t,r=7):
 i=s.find(t)
 return None if i<0 else (s[max(0,i-r):i],s[i+len(t):i+len(t)+r])
def diffparts(a,b):
 l=0
 while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
 r=0
 while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
 return a[:l],a[len(a)-r:] if r else '',b[l:len(b)-r if r else len(b)]
@dataclass
class Ep: before:str;cmd:str;after:str;obj:str;field:str;value:str;focus:str|None
@dataclass
class Node: obj_anchor:str;cmd_l:str;cmd_r:str;cl_l:str;cl_r:str;support:int=1;damage:float=0.0
class Model:
 def __init__(self,selective=True,use_null=True):self.nodes=[];self.selective=selective;self.use_null=use_null;self.nulls=0
 def learn(self,e,contrast):
  d=changed(e.before,e.after)
  if len(d)!=1:return
  _,old,new=d[0];ol,orr,nv=diffparts(old,new);cc=around(e.cmd,nv)
  if not cc:return
  oa=common(e.cmd,old)
  if not oa and e.focus and e.focus in old:oa=e.focus
  if not oa:return
  n=Node(oa,cc[0],cc[1],ol,orr)
  if self.selective:
   for st in contrast[-12:]:
    for c in cls(st):
     if n.cl_l in c and n.cl_r in c and n.obj_anchor not in c:n.damage+=1
  for q in self.nodes:
   if q.cmd_l==n.cmd_l and q.cmd_r==n.cmd_r and q.cl_l==n.cl_l and q.cl_r==n.cl_r and cos(grams(q.obj_anchor),grams(n.obj_anchor))>.6:
    q.support+=1;q.damage+=n.damage;return
  self.nodes.append(n)
 def infer(self,e):
  cs=cls(e.before);cands=[]
  for n in self.nodes:
   i=e.cmd.find(n.cmd_l) if n.cmd_l else 0
   if i<0:continue
   st=i+len(n.cmd_l);en=e.cmd.find(n.cmd_r,st) if n.cmd_r else len(e.cmd)
   if en<st:continue
   v=e.cmd[st:en]
   if not (0<len(v)<=12):continue
   for j,c in enumerate(cs):
    oi=c.find(n.obj_anchor);li=c.find(n.cl_l)
    if li<0:continue
    stc=li+len(n.cl_l);enc=c.find(n.cl_r,stc) if n.cl_r else len(c)
    if enc<stc:continue
    nc=c[:stc]+v+c[enc:];world=''.join(cs[:j]+[nc]+cs[j+1:])
    score=cos(grams(e.cmd),grams(n.obj_anchor+n.cmd_l+n.cmd_r))+0.03*math.log1p(n.support)
    if self.selective:score-=0.05*n.damage/max(1,n.support)
    if oi>=0:score+=0.4
    if e.focus and n.obj_anchor==e.focus:score+=0.15
    cands.append((score,world,n,j))
  cands.sort(reverse=True,key=lambda x:x[0])
  if not cands:self.nulls+=1;return e.before,0,True
  top=cands[0];tie=sum(abs(x[0]-top[0])<1e-9 for x in cands)
  if self.use_null and (top[0]<.28 or tie>1):self.nulls+=1;return e.before,len(cands),True
  return top[1],len(cands),False
class Surface:
 def __init__(self):self.train=[]
 def learn(self,e,*_):self.train.append(e)
 def infer(self,e):
  if not self.train:return e.before,0,False
  _,r=max(((cos(grams(e.cmd),grams(x.cmd)),x) for x in self.train),key=lambda z:z[0]);d=changed(r.before,r.after)
  if not d:return e.before,1,False
  idx,old,new=d[0];_,_,nv=diffparts(old,new);cc=around(r.cmd,nv)
  if not cc:return e.before,1,False
  i=e.cmd.find(cc[0]) if cc[0] else 0
  if i<0:return e.before,1,False
  st=i+len(cc[0]);en=e.cmd.find(cc[1],st) if cc[1] else len(e.cmd);v=e.cmd[st:en]
  cs=cls(e.before)
  if idx>=len(cs):return e.before,1,False
  l,rr,_=diffparts(old,new);c=cs[idx];li=c.find(l)
  if li<0:return e.before,1,False
  stc=li+len(l);enc=c.find(rr,stc) if rr else len(c);cs[idx]=c[:stc]+v+c[enc:]
  return ''.join(cs),1,False
def mk(o,d,form):return STATE_FORMS[form].format(o=o,loc=d['置き場所'],status=d['状態'],owner=d['担当'])
def build(seed,n,mode):
 rng=random.Random(seed);world={};out=[];focus=None
 for _ in range(n):
  o=rng.choice(OBJECTS)
  if o not in world:world[o]={f:rng.choice(VALUES[f]) for f in FIELDS}
  f=rng.choice(FIELDS);v=rng.choice([x for x in VALUES[f] if x!=world[o][f]]);form=1 if mode=='alternate' else 0
  b=mk(o,world[o],form);forms=OMIT[f] if mode=='omitted' else (HELD[f] if mode in ('held','paragraph') else CMD[f]);cmd=rng.choice(forms).format(o=o,v=v)
  world[o][f]=v;a=mk(o,world[o],form)
  if mode=='paragraph':cmd=rng.choice(DIST)+'\n'+cmd
  if mode=='plan_change':
   v2=rng.choice([x for x in VALUES[f] if x!=v]);cmd+=' ただし最終的には'+v2+'に変更します。';world[o][f]=v2;a=mk(o,world[o],form)
  out.append(Ep(b,cmd,a,o,f,world[o][f],focus));focus=o
 return out
def evalone(seed,n,mode):
 train=build(seed,n,'seen');test=build(seed+10000,120,mode);methods={'surface':Surface(),'partition':Model(False,False),'selective':Model(True,False),'selective_null':Model(True,True)};out={}
 for name,m in methods.items():
  contrasts=[];st=time.perf_counter()
  for e in train:m.learn(e,contrasts);contrasts.append(e.before)
  train_s=time.perf_counter()-st;ok=reads=null=0;it=time.perf_counter()
  for e in test:
   p,r,nu=m.infer(e);ok+=p==e.after;reads+=r;null+=nu
  inf=time.perf_counter()-it
  out[name]={'accuracy':ok/len(test),'null_rate':null/len(test),'mean_candidates':reads/len(test),'nodes':len(getattr(m,'nodes',getattr(m,'train',[]))),'model_bytes':len(pickle.dumps(m)),'training_seconds':train_s,'inference_ms':inf*1000/len(test)}
 return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output');a=ap.parse_args();raw={}
 for n in (48,144,432):raw[str(n)]=[{m:evalone(seed,n,m) for m in ('seen','held','alternate','omitted','paragraph','plan_change')} for seed in (1,7,19)]
 summary={}
 for n,rs in raw.items():
  summary[n]={}
  for mode in rs[0]:
   summary[n][mode]={}
   for meth in rs[0][mode]:summary[n][mode][meth]={k:statistics.mean(r[mode][meth][k] for r in rs) for k in rs[0][mode][meth]}
 payload={'hypothesis':'Identity-Selective Intervention Partitions with Null Object Nodes','seeds':[1,7,19],'sizes':[48,144,432],'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'learn O(NQG), infer O(HCG), H=learned nodes, C<=3','learner_hidden_labels':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False};open(a.output,'w',encoding='utf-8').write(json.dumps(payload,ensure_ascii=False,indent=2));print(json.dumps(summary['432'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
