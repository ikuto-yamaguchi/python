from __future__ import annotations
import argparse, json, math, pickle, random, resource, statistics, time
from collections import Counter, defaultdict
from dataclasses import dataclass

OBJECTS=['青い箱','赤い箱','試料甲','試料乙','端末一','端末二']
FIELDS=['場所','状態','担当']
VALUES={'場所':['棚A','棚B','棚C','棚D'],'状態':['待機','実行中','完了','保留'],'担当':['佐藤','鈴木','田中','高橋']}
STATE_FORMS=[lambda o,d:f"{o}：場所={d['場所']}、状態={d['状態']}、担当={d['担当']}。",lambda o,d:f"{o}の記録は、担当が{d['担当']}、場所が{d['場所']}、状態が{d['状態']}です。"]
COMMANDS={'場所':["{o}を{v}へ移してください。","{o}の置き先を{v}に変更。","{v}へ{o}を移す。"],'状態':["{o}を{v}にしてください。","{o}の状態を{v}へ更新。","{v}として{o}を扱う。"],'担当':["{o}の担当を{v}に替えてください。","{o}は{v}が担当します。","{v}へ{o}を引き継ぐ。"]}

def norm(s): return ''.join(s.split()).replace('。','').replace('、','')
def render(world,form): return '\n'.join(STATE_FORMS[form](o,world[o]) for o in sorted(world))
def diff_chunks(a,b):
 p=0
 while p<min(len(a),len(b)) and a[p]==b[p]: p+=1
 s=0
 while s<min(len(a)-p,len(b)-p) and a[-1-s]==b[-1-s]: s+=1
 return a[p:len(a)-s if s else len(a)],b[p:len(b)-s if s else len(b)],p,s

@dataclass(frozen=True)
class Program:
 command_anchor:str; before_anchor:str; after_anchor:str; delta_old:str; delta_new:str; span_left:int; span_right:int; support:int=1

class Learner:
 def __init__(self,adversarial=False,mdl=True):
  self.adversarial=adversarial; self.mdl=mdl; self.programs=[]; self.raw=0; self.rejected=0
 def propose(self,before,cmd,after):
  old,new,p,s=diff_chunks(before,after)
  if not old or not new:return []
  nc,nb=norm(cmd),norm(before); common=[]
  for L in range(2,min(12,len(nc))+1):
   for i in range(len(nc)-L+1):
    x=nc[i:i+L]
    if x in nb:common.append(x)
  common=sorted(set(common),key=lambda x:(-len(x),x))[:12] or ['']
  ba=norm(before[max(0,p-8):p]); aa=norm(after[max(0,p-8):p]); out=[]
  for c in common:
   for l in (0,1):
    for r in (0,1):out.append(Program(c,ba,aa,old,new,l,r))
  self.raw+=len(out); return out
 def fit(self,episodes):
  buckets=defaultdict(list)
  for b,c,a in episodes:
   for p in self.propose(b,c,a):buckets[(p.command_anchor,p.before_anchor,p.after_anchor)].append(p)
  kept=[]
  for key,ps in buckets.items():
   counts=Counter((p.delta_old,p.delta_new,p.span_left,p.span_right) for p in ps)
   for sig,n in counts.items():
    p=Program(*key,*sig,support=n)
    if n<2:self.rejected+=1;continue
    if self.adversarial:
     distinct_old=len({q.delta_old for q in ps}); distinct_new=len({q.delta_new for q in ps})
     risk=max(0,5-len(p.command_anchor))+max(0,4-len(p.before_anchor))
     if distinct_old<2 or distinct_new<2 or risk>=5:self.rejected+=1;continue
    kept.append(p)
  if self.mdl:kept.sort(key=lambda p:(-(p.support*max(1,len(p.command_anchor))),len(p.delta_old)+len(p.delta_new)))
  self.programs=kept[:64]
 def predict(self,before,cmd):
  nc=norm(cmd); cand=[]
  for p in self.programs:
   if p.command_anchor and p.command_anchor not in nc:continue
   score=len(p.command_anchor)*1.5+len(p.before_anchor)*.5+math.log1p(p.support)
   if before.count(p.delta_old)==1:cand.append((score,before.replace(p.delta_old,p.delta_new,1)))
  if not cand:return None,0
  cand.sort(reverse=True,key=lambda x:x[0]);return cand[0][1],len(cand)

def episode(rng,form=0,cmd_variant=0,omit=False,nested=False):
 objs=rng.sample(OBJECTS,3); world={o:{f:rng.choice(VALUES[f]) for f in FIELDS} for o in objs}
 target=rng.choice(objs); field=rng.choice(FIELDS); new=rng.choice([v for v in VALUES[field] if v!=world[target][field]])
 before=render(world,form); afterw={o:d.copy() for o,d in world.items()}; afterw[target][field]=new; after=render(afterw,form)
 if omit:cmd=f"それを{new}に更新してください。"
 else:cmd=COMMANDS[field][cmd_variant%3].format(o=target,v=new)
 if nested:cmd=f"『確認だけですが「{cmd}」という指示を実行してください』"
 return before,cmd,after

def run(seed,n,mode,method):
 rng=random.Random(seed); train=[episode(rng,0,0) for _ in range(n)]; learner=Learner(method=='adversarial',True)
 st=time.perf_counter();learner.fit(train);train_s=time.perf_counter()-st;tests=[]
 for _ in range(120):
  if mode=='seen':tests.append(episode(rng,0,0))
  elif mode=='held_order':tests.append(episode(rng,0,2))
  elif mode=='held_lexeme':tests.append(episode(rng,0,1))
  elif mode=='nested':tests.append(episode(rng,0,0,nested=True))
  elif mode=='subject_omission':tests.append(episode(rng,0,0,omit=True))
  elif mode=='alternate_state':tests.append(episode(rng,1,0))
  elif mode=='combined':tests.append(episode(rng,1,2,nested=True))
 correct=reads=0;st=time.perf_counter()
 for b,c,a in tests:
  p,r=learner.predict(b,c);reads+=r;correct+=p==a
 return {'accuracy':correct/len(tests),'model_bytes':len(pickle.dumps(learner)),'programs':len(learner.programs),'raw_candidates':learner.raw,'rejected':learner.rejected,'train_seconds':train_s,'infer_ms':(time.perf_counter()-st)*1000/len(tests),'reads':reads/len(tests)}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_013.json');args=ap.parse_args();raw={}
 modes=('seen','held_order','held_lexeme','nested','subject_omission','alternate_state','combined')
 for n in (48,144,432):
  runs=[]
  for seed in (1,7,19):runs.append({m:{mode:run(seed,n,mode,m) for mode in modes} for m in ('execution_only','adversarial')})
  raw[str(n)]=runs
 summary={}
 for n,runs in raw.items():
  summary[n]={}
  for method in ('execution_only','adversarial'):
   summary[n][method]={mode:{k:statistics.mean(r[method][mode][k] for r in runs) for k in runs[0][method][mode]} for mode in modes}
 payload={'hypothesis':'Adversarial Misapplication Programs with Relation-Contrastive MDL','seeds':[1,7,19],'sizes':[48,144,432],'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'train O(NL^2+C), infer O(PL), P<=64','highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
 open(args.output,'w',encoding='utf-8').write(json.dumps(payload,ensure_ascii=False,indent=2));print(json.dumps(summary['432'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
