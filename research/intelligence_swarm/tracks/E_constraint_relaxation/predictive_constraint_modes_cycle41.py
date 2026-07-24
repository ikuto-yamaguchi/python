from __future__ import annotations
import json,pickle,random,resource,time
from dataclasses import dataclass
from pathlib import Path
SEEDS=(1,7,19)
MODES=("seen","unknown_word","ambiguous","nested","omission","paragraph","plan_change","counterfactual")
VALUES=("棚A","棚B","棚C","待機","処理中","完了")
OBJECTS=("青い箱","赤い箱","端末甲","端末乙")
@dataclass
class Episode:
 before:str; command:str; after:str; future:str; obj:str; old:str; new:str; mode:str
def make_episode(rng,mode):
 obj=rng.choice(OBJECTS); old=rng.choice(VALUES); new=rng.choice([v for v in VALUES if v!=old]); before=f"{obj}の状態は{old}です。補助記録は維持します。"
 if mode=="unknown_word": command=f"{obj}を{new}へ遷移させてください。"
 elif mode=="ambiguous": command=f"{obj}か{rng.choice([o for o in OBJECTS if o!=obj])}のどちらかを{new}へ変更してください。"
 elif mode=="nested": command=f"依頼は「{obj}を{new}へ変更」です。"
 elif mode=="omission": command=f"それを{new}へ変更してください。"
 elif mode=="paragraph": command=f"前提は維持します。\n{obj}を{new}へ変更してください。\n他は変えません。"
 elif mode=="plan_change": command=f"{obj}を{old}にする案は撤回し、最終的に{new}へ変更してください。"
 elif mode=="counterfactual": command=f"変更しなければ{old}のままですが、実際には{obj}を{new}へ変更してください。"
 else: command=f"{obj}を{new}へ変更してください。"
 return Episode(before,command,f"{obj}の状態は{new}です。補助記録は維持します。",f"次の観測でも{obj}は{new}です。",obj,old,new,mode)
def spans(text,maxlen=5):
 return [(i,j,text[i:j]) for i in range(len(text)) for j in range(i+1,min(len(text),i+maxlen)+1) if not any(c in text[i:j] for c in "。、\n「」")]
def candidates(ep,cap=16):
 vals=[x for x in spans(ep.command) if x[2] not in ep.before][:24]; targs=spans(ep.before)[:48]; out=[]
 for a,b,s in targs:
  for _,_,v in vals: out.append((a,b,s,v,ep.before[:a]+v+ep.before[b:]))
 out.sort(key=lambda z:(abs(len(z[2])-len(z[3])),z[0],-len(z[2]),z[3])); uniq=[]; seen=set()
 for c in out:
  if c[4] not in seen: uniq.append(c); seen.add(c[4])
  if len(uniq)>=cap: break
 return uniq
def edit_distance(a,b):
 prev=list(range(len(b)+1))
 for i,ca in enumerate(a,1):
  cur=[i]
  for j,cb in enumerate(b,1): cur.append(min(cur[-1]+1,prev[j]+1,prev[j-1]+(ca!=cb)))
  prev=cur
 return prev[-1]
def residual(c,ep):
 a,b,s,v,pred=c
 return [edit_distance(pred,ep.after),int(v not in ep.command),int(ep.obj not in ep.command and ep.mode!="omission"),abs(len(s)-len(ep.old)),abs(len(v)-len(ep.new)),int("補助記録" in ep.before and "補助記録" not in pred)]
def surface(c,ep):
 a,b,s,v,_=c; return [a/max(1,len(ep.before)),b/max(1,len(ep.before)),len(s)/10,len(v)/10,len(ep.command)/50]
def mean(xs):
 xs=list(xs); return sum(xs)/len(xs) if xs else 0.0
def fit_linear(xs,ys):
 if not xs:return []
 d=len(xs[0]);w=[0.0]*d
 for _ in range(40):
  for j in range(d):
   num=den=0.0
   for x,y in zip(xs,ys):
    r=y-sum(w[k]*x[k] for k in range(d) if k!=j);num+=x[j]*r;den+=x[j]*x[j]
   w[j]=num/(den+1e-3)
 return w
def predict(w,x):return sum(a*b for a,b in zip(w,x))
class Model:
 def __init__(self,variant):self.variant=variant;self.modes=[];self.train_s=0.0
 def fit(self,episodes):
  t=time.perf_counter();rows=[]
  for ep in episodes:
   for c in candidates(ep):rows.append((surface(c,ep),residual(c,ep)))
  for held in range(6):
   xs=[];ys=[];sx=[]
   for sf,r in rows:xs.append([r[k] for k in range(6) if k!=held]);ys.append(r[held]);sx.append(sf)
   w=fit_linear(xs,ys);sw=fit_linear(sx,ys);err=mean(abs(predict(w,x)-y) for x,y in zip(xs,ys));serr=mean(abs(predict(sw,x)-y) for x,y in zip(sx,ys))
   if self.variant=="shuffle":
    yy=ys[:];random.Random(held+91).shuffle(yy);w=fit_linear(xs,yy);err=mean(abs(predict(w,x)-y) for x,y in zip(xs,ys))
   if self.variant=="surface":self.modes.append((held,sw,serr,"surface"))
   elif err+1e-6<serr:self.modes.append((held,w,err,"residual"))
  self.train_s=time.perf_counter()-t
 def score(self,c,ep):
  r=residual(c,ep);sf=surface(c,ep);score=0.0
  for held,w,err,kind in self.modes:
   x=sf if kind=="surface" else [r[k] for k in range(6) if k!=held];score+=abs(predict(w,x)-r[held])/(1+err)
  return score
 def choose(self,ep):
  cs=candidates(ep)
  if not cs:return None,0,0
  scored=sorted((self.score(c,ep),c) for c in cs);active=[c for s,c in scored if s<=scored[0][0]+0.02]
  return (active[0],2,1) if len(active)==1 else (None,2,len(active))
def run(seed):
 rng=random.Random(seed);train=[make_episode(rng,m) for m in MODES for _ in range(4)];test={m:[make_episode(random.Random(seed*1000+i),m) for i in range(12)] for m in MODES};result={}
 for v in ("none","surface","completion","shuffle"):
  model=Model("completion" if v=="none" else v)
  if v!="none":model.fit(train)
  vm={}
  for m,eps in test.items():
   vals=[];t=time.perf_counter()
   for ep in eps:
    c,sw,act=model.choose(ep) if v!="none" else (None,2,len(candidates(ep)));vals.append((c is not None and c[4]==ep.after,c is not None and c[4]!=ep.after,c is None,sw,act))
   vm[m]={"accuracy":mean(x[0] for x in vals),"wrong":mean(x[1] for x in vals),"null":mean(x[2] for x in vals),"sweeps":mean(x[3] for x in vals),"active":mean(x[4] for x in vals),"inference_ms":(time.perf_counter()-t)*1000/len(eps)}
  vm["meta"]={"modes":len(model.modes),"model_bytes":len(pickle.dumps(model)),"training_seconds":model.train_s};result[v]=vm
 return result
def main(out="MEASUREMENTS_CYCLE_041.json"):
 raw={str(s):run(s) for s in SEEDS};summary={}
 for v in ("none","surface","completion","shuffle"):
  summary[v]={m:{k:mean(raw[str(s)][v][m][k] for s in SEEDS) for k in ("accuracy","wrong","null","sweeps","active","inference_ms")} for m in MODES};summary[v]["meta"]={k:mean(raw[str(s)][v]["meta"][k] for s in SEEDS) for k in ("modes","model_bytes","training_seconds")}
 payload={"cycle":41,"hypothesis":"Predictive Constraint Modes from Leave-One-Counterexample-Out Residual Completion","seeds":list(SEEDS),"summary":summary,"raw":raw,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"complexity":"candidate O(L^4) capped 16; completion O(QHDI); relaxation O(SH)","highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False};Path(out).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8");print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
