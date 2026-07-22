"""Track C Cycle 017
Latent-State-Specific Operation Algebra from Cross-Context Commutator Signatures.

Learner sees only raw Japanese state/command/after strings and temporal order.
Hidden object/field/value labels are evaluator-only.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass
import argparse, hashlib, json, math, pickle, random, resource, statistics, time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵","試料甲","試料乙"]
FIELDS=["場所","状態","担当"]
VALUES={"場所":["棚A","棚B","棚C"],"状態":["待機","処理中","完了"],"担当":["担当一","担当二","担当三"]}
STATE_FORMS=[
 "{o}の場所は{loc}、状態は{status}、担当は{owner}です。",
 "{o}について、保管先={loc}／進行={status}／受持={owner}。",
]
COMMANDS={
 "場所":["{o}を{v}へ移してください。","{o}の保管先を{v}に変更します。"],
 "状態":["{o}を{v}にしてください。","{o}の進行状態を{v}へ切り替えます。"],
 "担当":["{o}の担当を{v}へ変更します。","{o}は今後{v}が受け持ちます。"],
}
HELD={
 "場所":["対象{o}、次から{v}で保管。"],"状態":["対象{o}は以後{v}扱い。"],"担当":["受持は{v}。対象は{o}。"]
}
OMIT={
 "場所":["それを{v}へ移してください。"],"状態":["その対象を{v}にしてください。"],"担当":["担当は{v}へ変えてください。"]
}
DISTRACT=["別件の資料を確認しました。","この文は更新ではありません。","前案はいったん保留です。"]

def grams(s):
 s="".join(s.split())
 return Counter(s[i:i+n] for n in (1,2,3) for i in range(max(0,len(s)-n+1)))
def cosine(a,b):
 d=sum(v*b.get(k,0) for k,v in a.items())
 na=math.sqrt(sum(v*v for v in a.values()));nb=math.sqrt(sum(v*v for v in b.values()))
 return d/(na*nb+1e-12)
def diff(a,b):
 l=0
 while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
 r=0
 while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
 return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def shape(s):
 return "".join("A" if c.isascii() and c.isalnum() else ("P" if c in "、。／=：" else "J") for c in s)
def state(o,d,form=0):
 return STATE_FORMS[form].format(o=o,loc=d["場所"],status=d["状態"],owner=d["担当"])

@dataclass
class Event:
 before:str;command:str;after:str;obj:str;field:str;value:str;event:int;focus:str

@dataclass
class Op:
 cl:str;cr:str;sl:str;sr:str;support:int=1
 def execute(self,s,cmd):
  i=cmd.find(self.cl) if self.cl else 0
  if i<0:return s,False
  st=i+len(self.cl);en=cmd.find(self.cr,st) if self.cr else len(cmd)
  if en<st:return s,False
  v=cmd[st:en]
  j=s.find(self.sl) if self.sl else 0
  if j<0:return s,False
  st2=j+len(self.sl);en2=s.find(self.sr,st2) if self.sr else len(s)
  if en2<st2:return s,False
  return s[:st2]+v+s[en2:],True

class Algebra:
 def __init__(self,kind):
  self.kind=kind;self.ops=[];self.families=[];self.training_seconds=0
 def fit(self,events):
  t=time.perf_counter()
  for e in events:
   l,r,old,new=diff(e.before,e.after)
   i=e.command.find(new)
   if i<0:continue
   op=Op(e.command[max(0,i-8):i],e.command[i+len(new):i+len(new)+8],e.before[:l],e.before[len(e.before)-r:] if r else "")
   self.ops.append(op)
  self.ops=self.ops[-64:]
  if self.kind=="surface":
   keys=[shape(o.cl+"|"+o.cr+"|"+o.sl+"|"+o.sr) for o in self.ops]
  else:
   keys=[]
   contexts=events[-24:]
   for idx,o in enumerate(self.ops):
    sig=[]
    for e in contexts:
     for j,p in enumerate(self.ops[:12]):
      if p is o:continue
      ab,ok1=o.execute(e.before,e.command)
      ab2,ok2=p.execute(ab,e.command) if ok1 else (ab,False)
      ba,ok3=p.execute(e.before,e.command)
      ba2,ok4=o.execute(ba,e.command) if ok3 else (ba,False)
      comm=int(ok1 and ok2 and ok3 and ok4 and ab2==ba2)
      changed=shape(diff(ab2,ba2)[3])[:8]
      if self.kind=="single":
       sig.append((comm,changed))
       break
      else:
       sig.append((comm,changed,shape(diff(e.before,ab2)[3])[:8],shape(diff(e.before,ba2)[3])[:8]))
    keys.append(tuple(sig))
  fam={}
  for i,k in enumerate(keys):
   fam.setdefault(str(k),[]).append(i)
  self.families=list(fam.values())
  self.training_seconds=time.perf_counter()-t

 def choose(self,s,cmd):
  cand=[]
  for fi,inds in enumerate(self.families):
   for i in inds:
    out,ok=self.ops[i].execute(s,cmd)
    if ok:
     score=cosine(grams(cmd),grams(self.ops[i].cl+self.ops[i].cr))
     cand.append((score,fi,out))
  if not cand:return s,False,0
  cand.sort(reverse=True,key=lambda z:z[0])
  return cand[0][2],True,len(cand)

def build(seed,n,mode):
 rng=random.Random(seed);world={};events=[];focus=""
 for t in range(n):
  o=rng.choice(OBJECTS);world.setdefault(o,{f:rng.choice(VALUES[f]) for f in FIELDS})
  f=rng.choice(FIELDS);v=rng.choice([x for x in VALUES[f] if x!=world[o][f]])
  form=1 if mode=="alternate" else 0
  before=state(o,world[o],form)
  forms=OMIT[f] if mode=="omitted" else (HELD[f] if mode in ("held","paragraph","plan") else COMMANDS[f])
  cmd=rng.choice(forms).format(o=o,v=v)
  if mode=="paragraph":cmd=" ".join(rng.choice(DISTRACT) for _ in range(3))+"\n"+cmd
  if mode=="plan":
   oldplan=rng.choice([x for x in VALUES[f] if x not in (world[o][f],v)])
   cmd=f"{o}を{oldplan}にする案でした。最終的には"+cmd
  world[o][f]=v;after=state(o,world[o],form)
  events.append(Event(before,cmd,after,o,f,v,t,focus));focus=o
 return events

def eval_mode(seed,n,mode):
 train=build(seed,n,"seen")
 test=build(seed+999,max(24,n//2),mode)
 out={}
 for kind in ("surface","single","cross_context"):
  m=Algebra(kind);m.fit(train)
  start=time.perf_counter();acc=0;cands=0
  for e in test:
   pred,_,c=m.choose(e.before,e.command);acc+=int(pred==e.after);cands+=c
  infer=(time.perf_counter()-start)*1000/len(test)
  cf=0;tot=0
  for a,b in zip(test[::2],test[1::2]):
   if a.obj!=b.obj:continue
   s=a.before
   p1,_,_=m.choose(s,a.command);p2,_,_=m.choose(p1,b.command)
   q1,_,_=m.choose(s,b.command);q2,_,_=m.choose(q1,a.command)
   truth_same=(a.field!=b.field)
   cf+=int((p2==q2)==truth_same);tot+=1
  out[kind]={
   "accuracy":acc/len(test),"counterfactual_order_accuracy":cf/max(1,tot),
   "families":len(m.families),"ops":len(m.ops),"model_bytes":len(pickle.dumps(m)),
   "training_seconds":m.training_seconds,"inference_ms":infer,"mean_candidates":cands/len(test)
  }
 return out

def summarize(raw):
 s={}
 for n,runs in raw.items():
  s[n]={}
  for mode in ("seen","held","alternate","omitted","paragraph","plan"):
   s[n][mode]={}
   for k in ("surface","single","cross_context"):
    keys=runs[0][mode][k]
    s[n][mode][k]={x:statistics.mean(r[mode][k][x] for r in runs) for x in keys}
 return s

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--output",default="results_cycle_017.json");a=ap.parse_args()
 raw={}
 for n in (48,144,432):
  runs=[]
  for seed in (1,7,19):
   runs.append({m:eval_mode(seed,n,m) for m in ("seen","held","alternate","omitted","paragraph","plan")})
  raw[str(n)]=runs
 payload={
  "hypothesis":"Latent-State-Specific Operation Algebra from Cross-Context Commutator Signatures",
  "seeds":[1,7,19],"sizes":[48,144,432],"raw":raw,"summary":summarize(raw),
  "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
  "estimated_complexity":"fit O(PKC G), inference O(PG), P<=64, K<=12, C<=24",
  "hidden_labels_used_by_learner":False,
  "highschool_level_passed":False,"native_japanese_communication_passed":False,
  "weak_smartphone_verified":False,"completion":False
 }
 with open(a.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
 print(json.dumps(payload["summary"]["432"],ensure_ascii=False,indent=2))
if __name__=="__main__":main()
