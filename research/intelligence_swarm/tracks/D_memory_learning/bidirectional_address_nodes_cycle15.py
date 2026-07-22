"""Track D Cycle 015: bidirectional query-write address nodes.

Learner inputs are raw Japanese before/command/after/query strings and temporal order.
Hidden object/relation/value labels are evaluator-only.

This controlled probe tests whether local span co-activation and bidirectional
write/read consistency can create reusable memory addresses without a fixed ontology.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass, field
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵","試料甲","試料乙"]
FIELDS=["置き場所","状態","担当"]
VALUES={"置き場所":["棚A","棚B","棚C","棚D"],"状態":["待機","処理中","完了","保留"],"担当":["担当一","担当二","担当三","担当四"]}
STATE_FORMS=["{o}の置き場所は{loc}、状態は{status}、担当は{owner}です。","{o}について、保管先={loc}／進行={status}／受持={owner}。","{o}：場所{loc}、進捗{status}、受け持ち{owner}。"]
CMD_SEEN={"置き場所":["{o}を{v}へ移してください。","{o}の保管先を{v}へ変更します。"],"状態":["{o}を{v}にしてください。","{o}の進行状態を{v}へ切り替えます。"],"担当":["{o}を{v}の担当にしてください。","{o}の受け持ちを{v}へ変更します。"]}
CMD_HELD={"置き場所":["対象{o}、次から{v}で保管。","保管場所は{v}。対象は{o}。"],"状態":["対象{o}は以後{v}扱い。","進行を{v}へ。対象は{o}。"],"担当":["{o}は{v}へ引き継ぎ。","受持は{v}。対象は{o}。"]}
CMD_OMIT={"置き場所":["それを{v}へ移してください。"],"状態":["その対象を{v}にしてください。"],"担当":["担当は{v}へ変えてください。"]}
QUERY_SEEN={"置き場所":["{o}の置き場所は？","{o}の保管先を教えて。"],"状態":["{o}の状態は？","{o}の進行状況を教えて。"],"担当":["{o}の担当は？","{o}の受け持ちは誰？"]}
QUERY_HELD={"置き場所":["{o}を今どこに置く？"],"状態":["現在の{o}はどういう段階？"],"担当":["今の{o}を受け持つ人は？"]}
DISTRACT=["別件の資料を確認しました。","今日は気温が高いです。","更新とは無関係な話です。"]

def grams(s):
 s="".join(s.split());return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))
def cosine(a,b):
 d=sum(v*b.get(k,0) for k,v in a.items());na=math.sqrt(sum(v*v for v in a.values()));nb=math.sqrt(sum(v*v for v in b.values()));return d/(na*nb+1e-12)
def diff(a,b):
 l=0
 while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
 r=0
 while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
 return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def spans(text,min_len=2,max_len=12,cap=48):
 out=[]
 for i in range(len(text)):
  for j in range(i+min_len,min(len(text),i+max_len)+1):
   x=text[i:j]
   if x.strip() and not all(c in "、。？／=：" for c in x):
    score=(text.count(x)-1)*2+int(i==0 or text[i-1] in "、。／=：")+int(j==len(text) or text[j:j+1] in "、。／=：");out.append((score,len(x),i,j,x))
 out.sort(reverse=True);seen=set();ret=[]
 for z in out:
  if z[-1] not in seen:seen.add(z[-1]);ret.append(z)
  if len(ret)>=cap:break
 return ret
def contexts(text,token,radius=7):
 i=text.find(token);return None if i<0 else (text[max(0,i-radius):i],text[i+len(token):i+len(token)+radius])

@dataclass
class Episode:
 before:str;command:str;after:str;queries:list[str];obj:str;field_name:str;value:str;event:int
@dataclass
class Node:
 object_span:str;relation_span:str;cmd_left:str;cmd_right:str;state_left:str;state_right:str
 query_patterns:Counter=field(default_factory=Counter);support:int=0;write_success:int=0;read_success:int=0;wrong_object:int=0;wrong_relation:int=0;aliases:set=field(default_factory=set);last_t:int=0
 def reliability(self):return (self.write_success+self.read_success+1)/(self.write_success+self.read_success+self.wrong_object+self.wrong_relation+2)

class EpisodicReplay:
 def __init__(self):self.items=[]
 def learn(self,e,t):self.items.append(e)
 def write(self,state,cmd):
  if not self.items:return state,False,0
  sim,e=max(((cosine(grams(cmd),grams(x.command)),x) for x in self.items),key=lambda z:z[0])
  if sim<.18:return state,False,1
  l,r,_,new=diff(e.before,e.after);ctx=contexts(e.command,new)
  if not ctx:return state,False,1
  a,b=ctx;i=cmd.find(a) if a else 0
  if i<0:return state,False,1
  st=i+len(a);en=cmd.find(b,st) if b else len(cmd)
  if en<st:return state,False,1
  return state[:l]+cmd[st:en]+(state[len(state)-r:] if r else ""),True,1
 def read(self,q,states):return (None,0) if not states else (max(states,key=lambda s:cosine(grams(q),grams(s))),len(states))

class AddressNodes:
 def __init__(self,bidirectional=True,competition=True):self.nodes=[];self.bidirectional=bidirectional;self.competition=competition;self.rejected=0;self.fast_updates=0
 def _propose(self,e):
  l,r,old,new=diff(e.before,e.after);cctx=contexts(e.command,new)
  if not new or not cctx:return []
  qtext=" ".join(e.queries);obj=[];rel=[]
  for _,ln,_,_,x in spans(e.before,2,12,48):
   if x in e.command and x in qtext:obj.append((ln,x))
  for _,ln,_,_,x in spans(qtext,2,10,48):
   if x in e.before and x not in new and x not in old:rel.append((ln,x))
  if not rel:rel=[(0,"")]
  return [Node(o,rr,cctx[0],cctx[1],e.before[:l],e.before[len(e.before)-r:] if r else "") for _,o in obj[:6] for _,rr in rel[:6]][:24]
 def _extract(self,cmd,n):
  i=cmd.find(n.cmd_left) if n.cmd_left else 0
  if i<0:return None
  st=i+len(n.cmd_left);en=cmd.find(n.cmd_right,st) if n.cmd_right else len(cmd);v=cmd[st:en] if en>=st else ""
  return v if 0<len(v)<=12 else None
 def _execute(self,state,cmd,n):
  v=self._extract(cmd,n)
  if v is None:return state,False
  i=state.find(n.state_left) if n.state_left else 0
  if i<0:return state,False
  st=i+len(n.state_left);en=state.find(n.state_right,st) if n.state_right else len(state)
  return (state[:st]+v+state[en:],True) if en>=st else (state,False)
 def learn(self,e,t,contrast_states):
  props=self._propose(e)
  if not props:self.rejected+=1;return
  accepted=[]
  for p in props:
   out,ok=self._execute(e.before,e.command,p)
   if not ok or out!=e.after:continue
   qhits=sum(int(p.object_span in q and (not p.relation_span or p.relation_span in q)) for q in e.queries)
   if self.bidirectional and qhits==0:continue
   damage=sum(int(worked and out2!=st and p.object_span not in st) for st in contrast_states[-8:] for out2,worked in [self._execute(st,e.command,p)])
   p.support=1;p.write_success=1;p.read_success=qhits;p.wrong_object=damage;p.last_t=t;p.query_patterns.update(grams(" ".join(e.queries)));p.aliases.add((p.object_span,p.relation_span,p.cmd_left,p.cmd_right));accepted.append(p)
  if not accepted:self.rejected+=1;return
  for p in accepted:
   best=None;bs=0
   for n in self.nodes:
    ws=(cosine(grams(p.cmd_left+p.cmd_right),grams(n.cmd_left+n.cmd_right))+cosine(grams(p.state_left+p.state_right),grams(n.state_left+n.state_right)))/2;rs=cosine(p.query_patterns,n.query_patterns);os=cosine(grams(p.object_span),grams(n.object_span));score=.40*ws+.35*rs+.25*os
    if score>bs:bs,best=score,n
   if best is not None and bs>=.68:best.support+=1;best.write_success+=p.write_success;best.read_success+=p.read_success;best.wrong_object+=p.wrong_object;best.query_patterns.update(p.query_patterns);best.aliases.update(p.aliases);best.last_t=t
   else:self.nodes.append(p)
  self.fast_updates+=len(accepted)
 def write(self,state,cmd):
  cand=[]
  for n in self.nodes:
   out,ok=self._execute(state,cmd,n)
   if ok:cand.append((.55*cosine(grams(cmd),grams(n.cmd_left+n.cmd_right))+.25*int(n.object_span in cmd)+.20*n.reliability(),n,out))
  if not cand:return state,False,0
  cand.sort(reverse=True,key=lambda x:x[0])
  if self.competition and len(cand)>1 and cand[0][0]-cand[1][0]<.06:return state,False,len(cand)
  if cand[0][0]<.10:return state,False,len(cand)
  return cand[0][2],True,len(cand)
 def read(self,q,states):
  ranked=[(.45*cosine(grams(q),n.query_patterns)+.35*int(n.object_span in q)+.20*int(n.relation_span and n.relation_span in q),n) for n in self.nodes];ranked.sort(reverse=True,key=lambda x:x[0])
  if not ranked:return None,0
  if self.competition and len(ranked)>1 and ranked[0][0]-ranked[1][0]<.05:return None,len(ranked)
  n=ranked[0][1];matching=[st for st in states if n.object_span in st]
  return (matching[-1],len(ranked)) if matching else (None,len(ranked))

def make_state(o,d,form=0):return STATE_FORMS[form].format(o=o,loc=d["置き場所"],status=d["状態"],owner=d["担当"])
def build(seed,n,mode):
 rng=random.Random(seed);world={};eps=[]
 for t in range(n):
  o=rng.choice(OBJECTS);world.setdefault(o,{f:rng.choice(VALUES[f]) for f in FIELDS});f=rng.choice(FIELDS);nv=rng.choice([v for v in VALUES[f] if v!=world[o][f]]);form=1 if mode=="alternate" else 0;before=make_state(o,world[o],form);forms=CMD_OMIT[f] if mode=="omitted" else (CMD_HELD[f] if mode in ("held","combined") else CMD_SEEN[f]);cmd=rng.choice(forms).format(o=o,v=nv);world[o][f]=nv;after=make_state(o,world[o],form);qforms=QUERY_HELD[f] if mode in ("held","combined") else QUERY_SEEN[f];eps.append(Episode(before,cmd,after,[x.format(o=o) for x in qforms],o,f,nv,t))
  if mode=="long":eps.extend(Episode("",rng.choice(DISTRACT),"",[],"","","",-1) for _ in range(rng.randint(3,8)))
 return eps,world

def evaluate(seed,n,mode):
 eps,truth=build(seed,n,mode);methods={"episodic":EpisodicReplay(),"write_only":AddressNodes(False,True),"bidirectional":AddressNodes(True,True),"no_competition":AddressNodes(True,False)};out={}
 for name,m in methods.items():
  states=[];contrasts=[];writes=read_ops=write_correct=0;start=time.perf_counter()
  for e in eps:
   if e.event<0:continue
   m.learn(e,e.event,contrasts) if isinstance(m,AddressNodes) else m.learn(e,e.event);pred,_,r=m.write(e.before,e.command);writes+=1;write_correct+=int(pred==e.after);states.append(pred);contrasts.append(e.before)
  train=time.perf_counter()-start;qstart=time.perf_counter();read_correct=wrong_obj=abstain=total=0
  for o,d in truth.items():
   for f in FIELDS:
    qforms=QUERY_HELD[f] if mode in ("held","combined") else QUERY_SEEN[f];q=random.Random(seed+len(o)+len(f)).choice(qforms).format(o=o);selected,r=m.read(q,states);read_ops+=r;total+=1
    if selected is None:abstain+=1;continue
    read_correct+=int(o in selected and d[f] in selected);wrong_obj+=int(o not in selected)
  out[name]={"write_accuracy":write_correct/max(1,writes),"read_accuracy":read_correct/max(1,total),"wrong_object_rate":wrong_obj/max(1,total),"abstain_rate":abstain/max(1,total),"model_bytes":len(pickle.dumps(m)),"training_seconds":train,"inference_ms":(time.perf_counter()-qstart)*1000/max(1,total),"units":len(getattr(m,"nodes",getattr(m,"items",[]))),"mean_write_candidates":0 if not isinstance(m,AddressNodes) else m.fast_updates/max(1,writes),"mean_read_candidates":read_ops/max(1,total),"rejected":getattr(m,"rejected",0)}
 return out

def one_shot(seed):
 e=build(seed,1,"seen")[0][0];out={}
 for name,m in (("episodic",EpisodicReplay()),("write_only",AddressNodes(False,True)),("bidirectional",AddressNodes(True,True)),("no_competition",AddressNodes(True,False))):
  m.learn(e,0,[]) if isinstance(m,AddressNodes) else m.learn(e,0);out[name]=float(m.write(e.before,e.command)[0]==e.after)
 return out

def interference(seed):
 target=build(seed,1,"seen")[0][0];train=[target]
 for i in range(50):train+=build(seed+100+i,1,"seen")[0]
 out={}
 for name,m in (("episodic",EpisodicReplay()),("write_only",AddressNodes(False,True)),("bidirectional",AddressNodes(True,True)),("no_competition",AddressNodes(True,False))):
  states=[];contrasts=[]
  for e in train:
   m.learn(e,e.event,contrasts) if isinstance(m,AddressNodes) else m.learn(e,e.event);states.append(m.write(e.before,e.command)[0]);contrasts.append(e.before)
  selected,_=m.read(QUERY_SEEN[target.field_name][0].format(o=target.obj),states);out[name]=float(selected is not None and target.obj in selected and target.value in selected)
 return out

def summarize(raw):
 s={}
 for n,runs in raw.items():
  s[n]={}
  for mode in ("seen","held","alternate","omitted","long","combined"):
   s[n][mode]={m:{k:statistics.mean(r[mode][m][k] for r in runs) for k in runs[0][mode][m]} for m in ("episodic","write_only","bidirectional","no_competition")}
  for p in ("one_shot","interference"):s[n][p]={m:statistics.mean(r[p][m] for r in runs) for m in ("episodic","write_only","bidirectional","no_competition")}
 return s

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--output",default="results_cycle_015.json");a=ap.parse_args();raw={}
 for n in (24,72,216):
  raw[str(n)]=[]
  for seed in (1,7,19):
   r={mode:evaluate(seed,n,mode) for mode in ("seen","held","alternate","omitted","long","combined")};r["one_shot"]=one_shot(seed);r["interference"]=interference(seed);raw[str(n)].append(r)
 payload={"hypothesis":"Bidirectional Query-Write Address Nodes with Local Binding Competition","seeds":[1,7,19],"sizes":[24,72,216],"raw":raw,"summary":summarize(raw),"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"estimated_complexity":"proposal O(L^2), learn O(NHG), write/read O(HG), H<=24 per episode before consolidation","learner_hidden_labels":False,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
 with open(a.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
 print(json.dumps(payload["summary"]["216"],ensure_ascii=False,indent=2))
if __name__=="__main__":main()
