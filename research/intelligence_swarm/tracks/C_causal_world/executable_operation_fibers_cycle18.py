"""Track C Cycle 018: Executable Operation Fibers with Conditional Commutator Algebra.

Learner input is raw Japanese before/command/after strings only.
Hidden object/relation/value labels are evaluator-only.
No external model, RAG, morphological analyzer, fixed ontology or hand-written slot parser.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末","大型端末":"大きい端末","北側の鍵":"北のキー","南側の鍵":"南のキー","試料甲":"サンプル甲","試料乙":"サンプル乙"}
FIELDS=["場所","状態","担当"]
VALS={"場所":["棚A","棚B","棚C"],"状態":["待機","処理中","完了"],"担当":["担当一","担当二","担当三"]}
STATE=["{o}の場所は{場所}、状態は{状態}、担当は{担当}です。","{o}：保管={場所}／進行={状態}／受持={担当}。","{o}について、{場所}にあり、{状態}で、{担当}が受け持つ。"]
CMD={"場所":["{o}を{v}へ移してください。","{o}の保管先を{v}へ変えます。"],"状態":["{o}を{v}にしてください。","{o}の進行を{v}へ切り替えます。"],"担当":["{o}を{v}の担当にしてください。","{o}の受持を{v}へ変更します。"]}
HELD={"場所":["次から{o}は{v}で保管。"],"状態":["以後{o}は{v}扱い。"],"担当":["{o}は{v}へ引き継ぎ。"]}
OMIT={"場所":["それを{v}へ移してください。"],"状態":["その対象を{v}にしてください。"],"担当":["担当は{v}へ変えてください。"]}
DIST=["別件の資料も確認しました。","これは変更と無関係です。","以前の案はいったん保留です。"]

def grams(s):
 s="".join(s.split()); return Counter(s[i:i+n] for n in (1,2,3) for i in range(max(0,len(s)-n+1)))
def cos(a,b):
 d=sum(v*b.get(k,0) for k,v in a.items()); na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values())); return d/(na*nb+1e-12)
def diff(a,b):
 l=0
 while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
 r=0
 while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
 return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def shape(s): return "".join("A" if c.isascii() and c.isalnum() else "J" if c.isalnum() else c for c in s)
def make_state(o,d,form): return STATE[form].format(o=o,**d)

@dataclass
class Ex:
 before:str; command:str; after:str; obj:str; field:str; value:str; mode:str; form:int; focus:str

def build(seed,n,mode):
 rng=random.Random(seed); world={}; out=[]; focus=""
 for _ in range(n):
  canonical=rng.choice(OBJECTS); surface=ALIASES[canonical] if mode=="rename" else canonical
  world.setdefault(canonical,{f:rng.choice(VALS[f]) for f in FIELDS})
  f=rng.choice(FIELDS); v=rng.choice([x for x in VALS[f] if x!=world[canonical][f]])
  form=1 if mode=="alternate" else (2 if mode=="freeform" else 0)
  before=make_state(surface,world[canonical],form)
  forms=OMIT[f] if mode=="omitted" else (HELD[f] if mode in ("held","paragraph","plan","rename","freeform") else CMD[f])
  command=rng.choice(forms).format(o=surface,v=v)
  if mode=="paragraph": command=" ".join(rng.choice(DIST) for _ in range(3))+"\n"+command
  if mode=="plan":
   oldv=rng.choice([x for x in VALS[f] if x not in (v,world[canonical][f])]); command=f"{surface}を{oldv}にする案でした。{rng.choice(DIST)} 最終的には"+command
  world[canonical][f]=v; after=make_state(surface,world[canonical],form)
  out.append(Ex(before,command,after,canonical,f,v,mode,form,focus));focus=surface
 return out

@dataclass
class Rule:
 sl:str; sr:str; cl:str; cr:str; delta_shape:str; preserve_shape:str; support:int=1; transport_ok:int=0; transport_fail:int=0

def context(text,token,r=7):
 i=text.find(token)
 if i<0:return None
 return text[max(0,i-r):i],text[i+len(token):i+len(token)+r]

class Model:
 def __init__(self,kind): self.kind=kind;self.rules=[];self.fibers=[];self.training_seconds=0
 def fit(self,eps):
  st=time.perf_counter()
  for e in eps:
   l,r,old,new=diff(e.before,e.after); c=context(e.command,new)
   if not new or not c:continue
   self.rules.append(Rule(e.before[:l],e.before[len(e.before)-r:] if r else "",c[0],c[1],shape(old)+"→"+shape(new),shape(e.before[:l])+shape(e.before[len(e.before)-r:] if r else "")))
   if len(self.rules)>=64:self.rules=self.rules[-64:]
  for r in self.rules:
   for e in eps[-48:]:
    out,ok=self._apply_rule(e.before,e.command,r)
    if ok:
     if out==e.after:r.transport_ok+=1
     else:r.transport_fail+=1
  if self.kind in ("fiber","conditional"):
   groups=defaultdict(list)
   for i,r in enumerate(self.rules):
    if r.transport_ok>0 and r.transport_fail==0:groups[(r.delta_shape,r.preserve_shape)].append(i)
   self.fibers=list(groups.values())
  self.training_seconds=time.perf_counter()-st
 def _extract(self,cmd,r):
  i=cmd.find(r.cl) if r.cl else 0
  if i<0:return None
  s=i+len(r.cl); e=cmd.find(r.cr,s) if r.cr else len(cmd)
  if e<s:return None
  x=cmd[s:e]; return x if 0<len(x)<=16 else None
 def _apply_rule(self,state,cmd,r):
  v=self._extract(cmd,r)
  if v is None:return state,False
  i=state.find(r.sl) if r.sl else 0
  if i<0:return state,False
  s=i+len(r.sl); e=state.find(r.sr,s) if r.sr else len(state)
  if e<s:return state,False
  return state[:s]+v+state[e:],True
 def predict(self,e):
  cand=[]; allowed=set(range(len(self.rules)))
  if self.kind in ("fiber","conditional"):allowed={i for g in self.fibers for i in g}
  for i,r in enumerate(self.rules):
   if i not in allowed:continue
   out,ok=self._apply_rule(e.before,e.command,r)
   if not ok:continue
   score=cos(grams(e.command),grams(r.cl+r.cr))+.25*cos(grams(e.before),grams(r.sl+r.sr))
   if self.kind in ("fiber","conditional"):score+=.2*(r.transport_ok/(r.transport_ok+r.transport_fail+1))
   cand.append((score,out,i))
  if not cand:return e.before,False,0
  cand.sort(reverse=True)
  if len(cand)>1 and cand[0][0]-cand[1][0]<.02:return e.before,False,len(cand)
  return cand[0][1],True,len(cand)
 def conditional_commutator(self,e1,e2):
  p1,ok1,_=self.predict(e1); p2,ok2,_=self.predict(e2)
  if not(ok1 and ok2):return None
  x=Ex(p1,e2.command,e2.after,e2.obj,e2.field,e2.value,e2.mode,e2.form,e2.focus); y=Ex(p2,e1.command,e1.after,e1.obj,e1.field,e1.value,e1.mode,e1.form,e1.focus)
  a,oka,_=self.predict(x); b,okb,_=self.predict(y)
  if not(oka and okb):return None
  return a==b

def evaluate(seed,n,mode):
 train=build(seed,n,"seen")+build(seed+1,n//2,"alternate")+build(seed+2,n//2,"rename"); test=build(seed+100,90,mode); out={}
 for kind in ("surface","transport","fiber","conditional"):
  m=Model(kind);m.fit(train);t=time.perf_counter();correct=commit=execs=0
  for e in test:
   p,ok,c=m.predict(e);correct+=int(p==e.after);commit+=int(ok);execs+=c
  pairs=cf_ok=0
  for a,b in zip(test[::2],test[1::2]):
   r=m.conditional_commutator(a,b)
   if r is not None:pairs+=1;cf_ok+=int(r==(a.field!=b.field))
  out[kind]={"accuracy":correct/len(test),"commit_rate":commit/len(test),"mean_executable_candidates":execs/len(test),"conditional_cf_accuracy":cf_ok/max(1,pairs),"conditional_cf_coverage":pairs/max(1,len(test)//2),"rules":len(m.rules),"fibers":len(m.fibers),"fiber_members":sum(map(len,m.fibers)),"model_bytes":len(pickle.dumps(m)),"training_seconds":m.training_seconds,"inference_ms":(time.perf_counter()-t)*1000/len(test)}
 return out

def summarize(raw):
 o={}
 for n,runs in raw.items():
  o[n]={}
  for mode in ("seen","held","alternate","rename","omitted","paragraph","plan","freeform"):
   o[n][mode]={}
   for kind in ("surface","transport","fiber","conditional"):
    keys=runs[0][mode][kind];o[n][mode][kind]={k:statistics.mean(r[mode][kind][k] for r in runs) for k in keys}
 return o

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--output",default="results_cycle_018.json");a=ap.parse_args();raw={}
 for n in (48,144,432):
  runs=[]
  for seed in (1,7,19):runs.append({m:evaluate(seed,n,m) for m in ("seen","held","alternate","rename","omitted","paragraph","plan","freeform")})
  raw[str(n)]=runs
 payload={"hypothesis":"Executable Operation Fibers with Conditional Commutator Algebra","seeds":[1,7,19],"sizes":[48,144,432],"raw":raw,"summary":summarize(raw),"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"estimated_complexity":"fit O(PN G), inference O(PG), conditional commutator O(PG); P<=64","hidden_labels_used_by_learner":False,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
 with open(a.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
 print(json.dumps(payload["summary"]["432"],ensure_ascii=False,indent=2))
if __name__=="__main__":main()
