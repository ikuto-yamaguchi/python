from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
import argparse,json,pickle,random,resource,statistics,time
OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー'}
VALUES=['棚A','棚B','棚C','棚D','待機','処理中','完了','保留']
FILL=['補助記録は維持します。','別件の設定は変えません。','前段の注意事項はそのままです。']
@dataclass
class Turn: before:str;command:str;after:str;future:str;obj:str;canon:str;old:str;new:str;mode:str
@dataclass(frozen=True)
class Fiber: sb:int;sw:int;cb:int;cw:int;oldshape:str;newshape:str

def shape(s):return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、：／=\n 「」' else c for c in s)
def diff(a,b):
 l=0
 while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
 r=0
 while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
 return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def spans(t,lo=1,hi=10):return [t[i:j] for i in range(len(t)) for j in range(i+lo,min(len(t),i+hi)+1) if not any(c in t[i:j] for c in '。、\n「」')]
def make(seed,n,mode):
 r=random.Random(seed);world={};focus=None;out=[]
 for i in range(n):
  cont=mode in ('omitted','switchmix') and i>0 and (mode=='omitted' or i%2==1)
  canon=focus if cont else r.choice(OBJECTS);obj=ALIASES[canon] if mode=='rename' else canon
  old=world.get(canon,r.choice(VALUES));new=r.choice([v for v in VALUES if v!=old]);before=f'{obj}の現在値は{old}です。{r.choice(FILL)}'
  if mode=='omitted' and i>0:cmd=f'それを{new}へ変更してください。'
  elif mode=='switchmix' and i>0 and i%2:cmd=f'その対象を{new}へ変更してください。'
  elif mode=='order':cmd=f'{new}へ変更してください、対象は{obj}です。'
  elif mode=='lexeme':cmd=f'対象{obj}は次から{new}扱いにします。'
  elif mode=='nested':cmd=f'依頼内容は「{obj}を{new}へ変更してください。」です。'
  elif mode=='paragraph':cmd=f'{r.choice(FILL)}\n{obj}を{new}へ変更してください。\n{r.choice(FILL)}'
  elif mode=='plan':
   alt=r.choice([v for v in VALUES if v not in (old,new)]);cmd=f'{obj}を{alt}にする案は撤回し、最終的には{new}へ変更してください。'
  elif mode=='counterfactual':cmd=f'もし変更しなければ{obj}は{old}のままです。実際には{obj}を{new}へ変更してください。'
  else:cmd=f'{obj}を{new}へ変更してください。'
  after=f'{obj}の現在値は{new}です。{r.choice(FILL)}';future=f'次の観測でも{obj}は{new}のままです。'
  out.append(Turn(before,cmd,after,future,obj,canon,old,new,mode));world[canon]=new;focus=canon
 return out

def apply(before,val,f):
 s=max(0,min(len(before),round(f.sb*len(before)/8)));e=max(s,min(len(before),s+f.sw))
 if shape(before[s:e])!=f.oldshape:return None
 return before[:s]+val+before[e:]
def candidates(t,prev=None,carry=False):
 objs=sorted({x for x in spans(t.command,2,10) if x in t.before},key=lambda x:(-len(x),x))[:6]
 if carry and prev:objs+=sorted({x for x in spans(prev.future,2,10) if x in prev.after},key=lambda x:(-len(x),x))[:4]
 vals=sorted({x for x in spans(t.command,1,8) if x not in t.before},key=lambda x:(-len(x),x))[:8]
 return list(dict.fromkeys(objs)),vals
class Model:
 def __init__(self,mode):self.mode=mode;self.fibers=[];self.reactivation=Counter();self.audit=0;self.train_s=0
 def fit(self,ind,probe):
  st=time.perf_counter();c=Counter()
  for t in ind:
   l,r,o,n=diff(t.before,t.after);p=t.command.find(n)
   if o and p>=0:c[Fiber(round(8*l/max(1,len(t.before))),len(o),round(8*p/max(1,len(t.command))),len(n),shape(o),shape(n))]+=1
  raw=[f for f,n in c.most_common(32) if n>=2];targets=[x.after for x in probe]
  if self.mode=='shuffle':targets=targets[1:]+targets[:1]
  kept=[]
  for f in raw:
   values=set();ok=wrong=react=0;lastcanon=None
   for t,target in zip(probe,targets):
    _,vs=candidates(t)
    for v in vs:
     p=apply(t.before,v,f);self.audit+=1
     if p is None:continue
     if p==target:values.add(v);ok+=1
     else:wrong+=1
    if lastcanon==t.canon and ok>0:react+=1
    lastcanon=t.canon
   if self.mode in ('multi','shuffle'):
    if len(values)>=3 and ok>wrong:kept.append(f);self.reactivation[f]=react
   elif self.mode=='single':
    if len(values)>=1 and ok>wrong:kept.append(f)
   else:kept=raw
  self.fibers=kept[:32];self.train_s=time.perf_counter()-st
 def predict(self,t,prev=None):
  os,vs=candidates(t,prev,self.mode in ('multi','shuffle'));props=[]
  for f in self.fibers:
   for o in os or ['']:
    for v in vs:
     p=apply(t.before,v,f)
     if p is None:continue
     non_target=int(('補助記録' in t.before)==('補助記録' in p));score=non_target+self.reactivation.get(f,0)*.2
     props.append((score,p,o,v,f))
  if not props:return None,0,0
  props.sort(reverse=True,key=lambda x:x[0]);best=props[0][0];active=[x for x in props if x[0]>=best-.1][:12]
  if len(active)>1 and active[0][0]-active[1][0]<.3:return None,2,len(active)
  return active[0],2,len(active)
def run(seed,mode):
 train=[]
 for j,m in enumerate(('seen','rename','paragraph','switchmix','plan')):train+=make(seed+j,24,m)
 cut=int(.7*len(train));ind,probe=train[:cut],train[cut:];test=make(seed+999,18,mode);out={}
 for method in ('raw','single','multi','shuffle'):
  M=Model(method);M.fit(ind,probe);rs=[];st=time.perf_counter()
  for i,t in enumerate(test):
   p,sw,a=M.predict(t,test[i-1] if i else None);rs.append((p is not None and p[1]==t.after,p is not None and p[1]!=t.after,p is None,p is not None and p[2]==t.obj and p[3]==t.new,sw,a))
  out[method]={'accuracy':statistics.mean(x[0] for x in rs),'wrong':statistics.mean(x[1] for x in rs),'null':statistics.mean(x[2] for x in rs),'pair_recall':statistics.mean(x[3] for x in rs),'mean_sweeps':statistics.mean(x[4] for x in rs),'mean_active':statistics.mean(x[5] for x in rs),'fibers':len(M.fibers),'reactivation_edges':sum(1 for v in M.reactivation.values() if v>0),'probe_audits':M.audit,'model_bytes':len(pickle.dumps(M)),'training_seconds':M.train_s,'inference_ms':(time.perf_counter()-st)*1000/len(test)}
 return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='MEASUREMENTS_CYCLE_034.json');a=ap.parse_args();modes=('seen','order','lexeme','rename','nested','omitted','switchmix','paragraph','plan','counterfactual')
 raw={str(s):{m:run(s,m) for m in modes} for s in (1,7,19)};summary={m:{q:{k:statistics.mean(raw[str(s)][m][q][k] for s in (1,7,19)) for k in raw['1'][m][q]} for q in ('raw','single','multi','shuffle')} for m in modes}
 payload={'cycle':34,'hypothesis':'Multi-Value Temporal Transition Fibers with Cross-Turn Reactivation','seeds':[1,7,19],'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'complexity':'induction O(NL), multi-value probe O(QFVL), inference O(FOV)','final_test_outcome_used_for_ranking':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
 open(a.output,'w',encoding='utf8').write(json.dumps(payload,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
