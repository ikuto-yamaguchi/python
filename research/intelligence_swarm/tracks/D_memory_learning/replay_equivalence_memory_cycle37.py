from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict, Counter
import argparse,json,pickle,random,resource,statistics,time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
FIELDS=['場所','状態','担当']
VALUES={'場所':['棚A','棚B','棚C','棚D'],'状態':['待機','処理中','完了','保留'],'担当':['担当一','担当二','担当三','担当四']}
S0='{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。'
S1='{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。'
Q={'場所':['{o}の場所はどこですか？','{o}はどこにありますか？'],'状態':['{o}の状態はどうなっていますか？','{o}はいまどういう状態ですか？'],'担当':['{o}の担当は誰ですか？','{o}を受け持つのは誰ですか？']}
CMD={'場所':['{o}を{v}へ移してください。','{o}の保管先を{v}へ変更します。'],'状態':['{o}を{v}にしてください。','{o}の進行状態を{v}へ切り替えます。'],'担当':['{o}を{v}の担当にしてください。','{o}の受け持ちを{v}へ変更します。']}

@dataclass
class Ep:
    before:str; command:str; after:str; future:str; query:str; answer:str; obj:str; session:int; mode:str
@dataclass
class Address:
    wb0:int; wb1:int; cv0:int; cv1:int; co0:int; co1:int; qo0:int; qo1:int
    old_shape:str; new_shape:str; obj_shape:str
    support:int=0; pos:int=0; neg:int=0; sessions:int=0; born:int=0; family:int=-1; slow:int=0

def shape(s): return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、：／=？\n ' else c for c in s)
def state(o,d,alt=False): return (S1 if alt else S0).format(o=o,loc=d['場所'],status=d['状態'],owner=d['担当'])
def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return l,len(a)-r,a[l:len(a)-r],b[l:len(b)-r]
def bucket(i,n): return max(0,min(24,round(24*i/max(1,n))))
def unbucket(b,n): return max(0,min(n,round(b*n/24)))
def spans(t,lo=1,hi=12):
    return [(i,j,t[i:j]) for i in range(len(t)) for j in range(i+lo,min(len(t),i+hi)+1) if not any(c in t[i:j] for c in '。、：／=？\n ')]
def build(seed,n,mode,start=0):
    rng=random.Random(seed);world={};out=[];focus=None
    for i in range(n):
        canon=focus if mode=='omitted' and focus else rng.choice(OBJECTS);o=ALIASES[canon] if mode=='rename' else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS});f=rng.choice(FIELDS);old=world[canon][f];new=rng.choice([x for x in VALUES[f] if x!=old])
        before=state(o,world[canon],mode=='alternate');cmd=rng.choice(CMD[f]).format(o=o,v=new)
        if mode=='held':cmd={'場所':f'対象{o}は次から{new}で保管。','状態':f'対象{o}は以後{new}として運用。','担当':f'対象{o}の受持を{new}へ。'}[f]
        elif mode=='omitted':cmd={'場所':f'それを{new}へ移してください。','状態':f'その対象を{new}にしてください。','担当':f'担当は{new}へ変えてください。'}[f]
        elif mode=='paragraph':cmd='長い前置きがあります。別件は変更しません。\n'+cmd+'\n補助情報は維持してください。'
        elif mode=='free':cmd={'場所':f'{o}は今後{new}に置こう。','状態':f'{o}はこれから{new}扱いで。','担当':f'{o}は{new}に任せる。'}[f]
        world[canon][f]=new;after=state(o,world[canon],mode=='alternate');query=rng.choice(Q[f]).format(o=o)
        if mode=='free':query={'場所':f'{o}を探すならどこ？','状態':f'{o}はいまどんな具合？','担当':f'{o}を見ている人は？'}[f]
        out.append(Ep(before,cmd,after,f'次の観測でも{o}の更新内容は{new}です。',query,new,o,start+i//6,mode));focus=canon
    return out

def locate(t,s):
    i=t.find(s);return None if i<0 else (bucket(i,len(t)),bucket(i+len(s),len(t)))
def induce(ep):
    l,r,old,new=diff(ep.before,ep.after);out=[]
    if not old or not new:return out
    vals=[(i,j,s) for i,j,s in spans(ep.command,1,10) if s==new]
    objs=[(i,j,s) for i,j,s in spans(ep.command,2,12) if s in ep.before and s in ep.query]
    objs=sorted(objs,key=lambda x:-len(x[2]))[:4]
    for vi,vj,v in vals[:4]:
      for oi,oj,o in objs:
        q=locate(ep.query,o)
        if q:out.append(Address(bucket(l,len(ep.before)),bucket(r,len(ep.before)),bucket(vi,len(ep.command)),bucket(vj,len(ep.command)),bucket(oi,len(ep.command)),bucket(oj,len(ep.command)),*q,shape(old),shape(v),shape(o)))
    return out

def apply(ep,p):
    a,b=unbucket(p.wb0,len(ep.before)),unbucket(p.wb1,len(ep.before));c,d=unbucket(p.cv0,len(ep.command)),unbucket(p.cv1,len(ep.command));e,f=unbucket(p.co0,len(ep.command)),unbucket(p.co1,len(ep.command));g,h=unbucket(p.qo0,len(ep.query)),unbucket(p.qo1,len(ep.query))
    if not (a<b and c<d and e<f and g<h):return None
    old,val,obj,qobj=ep.before[a:b],ep.command[c:d],ep.command[e:f],ep.query[g:h]
    if shape(old)!=p.old_shape or shape(val)!=p.new_shape or shape(obj)!=p.obj_shape or shape(qobj)!=p.obj_shape:return None
    if obj not in ep.before:return None
    return val,ep.before[:a]+val+ep.before[b:]

def key(p):return tuple(getattr(p,k) for k in ('wb0','wb1','cv0','cv1','co0','co1','qo0','qo1','old_shape','new_shape','obj_shape'))
def mutate_all(p):
    out=[]
    for attr in ('wb0','wb1','cv0','cv1','co0','co1','qo0','qo1'):
      for step in (-1,1):
        q=Address(**{k:getattr(p,k) for k in ('wb0','wb1','cv0','cv1','co0','co1','qo0','qo1','old_shape','new_shape','obj_shape')},support=p.support,born=1)
        setattr(q,attr,max(0,min(24,getattr(q,attr)+step)))
        if q.wb0<q.wb1 and q.cv0<q.cv1 and q.co0<q.co1 and q.qo0<q.qo1:out.append(q)
    return out

def response(ep,p,target,answer):
    g=apply(ep,p)
    if g is None:return (0,0,0)
    val,pred=g
    correct=int(val==answer and pred==target)
    wrong=int(not correct)
    l,r,_,_=diff(ep.before,target)
    damage=int(pred[:l]!=target[:l] or pred[r:]!=target[r:])
    return (2 if correct else 1,wrong,damage)

class Memory:
  def __init__(self,mode):
    self.mode=mode;self.addresses=[];self.audit=0;self.mutations=0;self.families=0;self.family_members=0;self.unique_witness=0;self.train_s=0
  def fit(self,train,probe,shuffle=False):
    t=time.perf_counter();tab=defaultdict(lambda:[0,set()])
    for ep in train:
      for p in induce(ep):tab[key(p)][0]+=1;tab[key(p)][1].add(ep.session)
    base=[Address(*k,support=n,sessions=len(s)) for k,(n,s) in sorted(tab.items(),key=lambda z:z[1][0],reverse=True)[:64]]
    candidates={key(p):p for p in base}
    for p in base:
      for q in mutate_all(p):candidates.setdefault(key(q),q);self.mutations+=1
    targets=[x.after for x in probe];answers=[x.answer for x in probe]
    if shuffle:targets=targets[1:]+targets[:1];answers=answers[1:]+answers[:1]
    vectors=defaultdict(list);stats={}
    for p in candidates.values():
      vec=[];pos=neg=0;sessions=set()
      for ep,target,answer in zip(probe,targets,answers):
        self.audit+=1;r=response(ep,p,target,answer);vec.append(r)
        if r[0]==2:pos+=1;sessions.add(ep.session)
        elif r[0]==1:neg+=1
      stats[key(p)]=(pos,neg,len(sessions))
      vectors[tuple(vec)].append(p)
    selected=[];fid=0
    for vec,members in vectors.items():
      pos=sum(1 for r in vec if r[0]==2);wrong=sum(1 for r in vec if r[0]==1);nonzero=sum(1 for r in vec if r[0]>0)
      if len(members)>=2 and pos>=2 and pos>wrong and nonzero>=pos:
        witnesses=0
        for i,r in enumerate(vec):
          if r[0]!=2:continue
          competing=sum(1 for ov in vectors if ov!=vec and ov[i][0]==2)
          if competing==0:witnesses+=1
        if witnesses==0:continue
        self.families+=1;self.unique_witness+=witnesses
        for p in members[:8]:
          p.pos=pos;p.neg=wrong;p.family=fid;p.slow=int(stats[key(p)][2]>=2 and witnesses>=1);selected.append(p);self.family_members+=1
        fid+=1
    if self.mode=='base':self.addresses=base
    elif self.mode=='family':self.addresses=selected
    elif self.mode=='slow':self.addresses=[p for p in selected if p.slow]
    elif self.mode=='shuffle':self.addresses=selected
    self.train_s=time.perf_counter()-t
  def rw(self,ep):
    cand=[]
    for p in self.addresses:
      g=apply(ep,p)
      if g:cand.append((4*p.pos-3*p.neg+.05*p.support+1.0*p.born+0.5*p.slow,*g,p.family))
    cand.sort(reverse=True)
    if not cand or (len(cand)>1 and cand[0][0]-cand[1][0]<.5):return None,None
    return cand[0][1],cand[0][2]

def evalm(m,test):
  t=time.perf_counter();ra=wa=cl=wr=ww=null=0
  for e in test:
    r,w=m.rw(e);ra+=r==e.answer;wa+=w==e.after;cl+=r==e.answer and w==e.after;wr+=r is not None and r!=e.answer;ww+=w is not None and w!=e.after;null+=r is None
  n=len(test);return dict(read_accuracy=ra/n,write_accuracy=wa/n,closed_cycle=cl/n,wrong_read=wr/n,wrong_write=ww/n,null_rate=null/n,inference_ms=(time.perf_counter()-t)*1000/n)

def run(seed):
  train=build(seed,72,'seen',0)+build(seed+11,36,'held',20);probe=build(seed+101,48,'seen',50);out={}
  for name,mode,sh in [('base','base',False),('family','family',False),('slow','slow',False),('shuffle','shuffle',True)]:
    m=Memory(mode);m.fit(train,probe,sh);r={'addresses':len(m.addresses),'mutations':m.mutations,'families':m.families,'family_members':m.family_members,'unique_witness':m.unique_witness,'audit':m.audit,'model_bytes':len(pickle.dumps(m)),'training_seconds':m.train_s}
    for md in ('seen','held','rename','alternate','omitted','paragraph','free'):r[md]=evalm(m,build(seed+999,24,md,100))
    one=build(seed+500,1,'free',200)[0];fast=Memory(mode);fast.fit(train+[one],probe,sh);rr,ww=fast.rw(one);r['one_shot_closed']=int(rr==one.answer and ww==one.after)
    seq=build(seed+700,30,'seen',300);a=Memory(mode);a.fit(train+seq[:15],probe,sh);pre=sum(a.rw(x)[0]==x.answer for x in seq[:15])/15;b=Memory(mode);b.fit(train+seq,probe,sh);post=sum(b.rw(x)[0]==x.answer for x in seq[:15])/15;latest=sum(b.rw(x)[0]==x.answer for x in seq[15:])/15
    r.update(interference_before=pre,interference_after=post,latest_recall=latest);out[name]=r
  return out

def main():
  ap=argparse.ArgumentParser();ap.add_argument('--output',default='MEASUREMENTS_CYCLE_037.json');a=ap.parse_args();raw={str(s):run(s) for s in (1,7,19)};summary={}
  for method in ('base','family','slow','shuffle'):
    summary[method]={};scalar=[k for k,v in raw['1'][method].items() if isinstance(v,(int,float))]
    for k in scalar:summary[method][k]=statistics.mean(raw[str(s)][method][k] for s in (1,7,19))
    for md in ('seen','held','rename','alternate','omitted','paragraph','free'):summary[method][md]={k:statistics.mean(raw[str(s)][method][md][k] for s in (1,7,19)) for k in raw['1'][method][md]}
  payload={'cycle':37,'hypothesis':'Replay-Response Equivalence Address Birth from Cross-Episode Residual Transport','seeds':[1,7,19],'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'induction O(NL^2), mutation O(P), replay response O(QP), quotient O(PQ log P), inference O(PL), P<=1088','final_test_outcome_used_for_retrieval_or_ranking':False,'fixed_ontology_or_slots_used_by_model':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
  with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
  print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
