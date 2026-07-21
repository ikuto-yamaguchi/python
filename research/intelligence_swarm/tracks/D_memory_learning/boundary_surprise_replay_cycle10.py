from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import argparse, json, math, pickle, random, resource, statistics, time

ENTS=["青箱","赤箱","端末甲","端末乙","試料一","試料二","台車A","台車B"]
VALS=["棚A","棚B","棚C","保留","完了","担当一","担当二","廊下"]
EXPL=["{e}の記録は{v}です。","{e}について{v}と記録します。","{e}は現在{v}です。"]
FOLLOW_SEEN=["その対象は{v}に更新します。","同じものを{v}へ変更します。"]
FOLLOW_HELD=["先ほどの品は{v}になりました。","話題中のもの、今は{v}です。"]
DIST=["今日は静かです。","別件を確認しました。","休憩します。","窓を閉めました。"]
QUERY=["{e}の最新記録は？","{e}は今どうなっていますか。"]

def grams(s):
 s=''.join(s.split()); return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))
def cos(a,b):
 d=sum(v*b.get(k,0) for k,v in a.items()); na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
 return d/(na*nb+1e-12)

@dataclass
class U:
 text:str; eid:int; ent:str|None; val:str|None; kind:str
@dataclass
class Seg:
 ids:list[int]=field(default_factory=list); sig:Counter=field(default_factory=Counter)
 def add(self,u,t): self.ids.append(t); self.sig.update(grams(u.text))

class Temporal:
 def __init__(self): self.segs=[]; self.prev_kind=None
 def observe(self,u,t):
  if not self.segs or u.kind=="explicit": self.segs.append(Seg())
  self.segs[-1].add(u,t); self.prev_kind=u.kind

class SurpriseReplay:
 def __init__(self,max_h=2):
  self.segs=[]; self.fast=[]; self.transition=defaultdict(Counter); self.max_h=max_h
  self.rejected=0; self.replay_merges=0; self.peak_fast=0
 def _surprise(self,u,seg):
  if not seg.ids: return 1.0
  sim=cos(grams(u.text),seg.sig)
  return 1-sim
 def _future_score(self,u,attach_new):
  g=grams(u.text)
  start=sum(self.transition["START"][k] for k in g)
  cont=sum(self.transition["CONT"][k] for k in g)
  total=start+cont
  if total==0: return 0.0
  pstart=start/total
  return pstart if attach_new else 1-pstart
 def observe(self,u,t):
  if not self.segs:
   self.segs.append(Seg()); self.segs[0].add(u,t)
   for g in grams(u.text): self.transition["START"][g]+=1
   return
  old=self.segs[-1]
  s_append=0.45*(1-self._surprise(u,old))+0.55*self._future_score(u,False)
  s_new=0.45*self._surprise(u,old)+0.55*self._future_score(u,True)
  self.fast=[("append",s_append),("new",s_new)]; self.peak_fast=max(self.peak_fast,len(self.fast))
  if abs(s_append-s_new)<0.05:
   choice="new" if self._surprise(u,old)>0.72 else "append"; self.rejected+=1
  else: choice=max(self.fast,key=lambda x:x[1])[0]
  if choice=="new": self.segs.append(Seg()); label="START"
  else: label="CONT"
  self.segs[-1].add(u,t)
  for g in grams(u.text): self.transition[label][g]+=1
  self.fast=[]
 def compress(self,stream):
  out=[]; i=0
  while i<len(self.segs):
   if i+1<len(self.segs):
    a,b=self.segs[i],self.segs[i+1]
    separate=len(a.sig)+len(b.sig)
    merged=a.sig+b.sig
    gain=separate-len(merged)
    if gain>2 and len(a.ids)+len(b.ids)<=4:
     c=Seg(a.ids+b.ids,merged); out.append(c); self.replay_merges+=1; i+=2; continue
   out.append(self.segs[i]); i+=1
  self.segs=out

def build(seed,n,held=False,gap=False,shift=False):
 r=random.Random(seed); stream=[]; truth={}; eid=0
 for _ in range(n):
  e=r.choice(ENTS); v=r.choice(VALS); stream.append(U(r.choice(EXPL).format(e=e,v=v),eid,e,v,"explicit")); truth[e]=v
  if gap:
   for _ in range(20): stream.append(U(r.choice(DIST),-1,None,None,"dist"))
  elif shift:
   e2=r.choice([x for x in ENTS if x!=e]); v2=r.choice(VALS); stream.append(U(r.choice(EXPL).format(e=e2,v=v2),eid+10000,e2,v2,"explicit")); truth[e2]=v2
  else:
   for _ in range(r.randint(0,2)): stream.append(U(r.choice(DIST),-1,None,None,"dist"))
  nv=r.choice([x for x in VALS if x!=v]); f=r.choice(FOLLOW_HELD if held else FOLLOW_SEEN)
  stream.append(U(f.format(v=nv),eid,e,nv,"follow")); truth[e]=nv; eid+=1
 return stream,truth

def metrics(model,stream,truth):
 true=set(); pred=set()
 for i in range(len(stream)):
  for j in range(i+1,min(len(stream),i+25)):
   if stream[i].eid>=0 and stream[i].eid==stream[j].eid: true.add((i,j))
 for seg in model.segs:
  for ai,a in enumerate(seg.ids):
   for b in seg.ids[ai+1:]: pred.add((a,b))
 tp=len(true&pred); prec=tp/max(1,len(pred)); rec=tp/max(1,len(true)); f1=2*prec*rec/max(1e-12,prec+rec)
 correct=0
 for e,v in truth.items():
  qg=grams(random.choice(QUERY).format(e=e))
  ranked=sorted(((cos(qg,s.sig),s) for s in model.segs),reverse=True,key=lambda x:x[0])[:8]
  pv=None
  for _,seg in ranked:
   for idx in reversed(seg.ids):
    u=stream[idx]
    if u.ent==e and u.val is not None: pv=u.val; break
   if pv is not None: break
  correct+=pv==v
 return {"retrieval":correct/max(1,len(truth)),"pair_precision":prec,"pair_recall":rec,"pair_f1":f1}

def eval_one(seed,n,mode):
 stream,truth=build(seed,n,held=mode in ("held","combined"),gap=mode=="gap",shift=mode=="shift")
 out={}
 for name,m in [("temporal",Temporal()),("surprise",SurpriseReplay())]:
  st=time.perf_counter()
  for t,u in enumerate(stream): m.observe(u,t)
  if isinstance(m,SurpriseReplay): m.compress(stream)
  train=time.perf_counter()-st
  qst=time.perf_counter(); mm=metrics(m,stream,truth); infer=(time.perf_counter()-qst)*1000/max(1,len(truth))
  mm.update({"segments":len(m.segs),"model_bytes":len(pickle.dumps(m)),"train_s":train,"infer_ms":infer,
             "peak_fast":getattr(m,"peak_fast",0),"rejected":getattr(m,"rejected",0),"replay_merges":getattr(m,"replay_merges",0)})
  out[name]=mm
 return out

def interference(seed):
 stream=[U("基準対象の記録は旧値です。",0,"基準対象","旧値","explicit")]
 for i in range(50): stream.append(U(f"無関係{i}は値{i}です。",i+1,f"無関係{i}",f"値{i}","explicit"))
 stream.append(U("その対象は新値に更新します。",0,"基準対象","新値","follow"))
 out={}
 for name,m in [("temporal",Temporal()),("surprise",SurpriseReplay())]:
  for t,u in enumerate(stream): m.observe(u,t)
  if isinstance(m,SurpriseReplay): m.compress(stream)
  mm=metrics(m,stream,{"基準対象":"新値"}); out[name]=mm["retrieval"]
 return out

def summarize(raw):
 z={}
 for n,runs in raw.items():
  z[n]={}
  for mode in ("seen","held","gap","shift","combined"):
   z[n][mode]={}
   for method in ("temporal","surprise"):
    keys=runs[0][mode][method]
    z[n][mode][method]={k:statistics.mean(x[mode][method][k] for x in runs) for k in keys}
  z[n]["interference"]={m:statistics.mean(x["interference"][m] for x in runs) for m in ("temporal","surprise")}
 return z

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--output",default="results_cycle_010.json"); a=ap.parse_args()
 raw={}
 for n in (48,192,768):
  runs=[]
  for seed in (1,7,19):
   d={mode:eval_one(seed,n,mode) for mode in ("seen","held","gap","shift","combined")}
   d["interference"]=interference(seed); runs.append(d)
  raw[str(n)]=runs
 payload={"hypothesis":"Boundary-Surprise Fast States with Counterfactual Replay Compression","seeds":[1,7,19],
 "sizes":[48,192,768],"raw":raw,"summary":summarize(raw),
 "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
 "complexity":"update O(G), two fast worlds; replay O(SG); retrieval top-8 O(SG)",
 "hidden_labels_used_by_learner":False,"free_japanese_integrated_gate":0.0,
 "highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
 open(a.output,"w",encoding="utf-8").write(json.dumps(payload,ensure_ascii=False,indent=2))
 print(json.dumps(payload["summary"]["768"],ensure_ascii=False,indent=2))
if __name__=="__main__": main()
