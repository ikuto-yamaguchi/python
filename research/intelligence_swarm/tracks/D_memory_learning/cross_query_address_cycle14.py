"""Track D Cycle 014: cross-query write/read address falsification probe."""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass,field
import argparse,json,math,pickle,random,resource,statistics,time
OBJECTS=["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵","試料甲","試料乙"]
FIELDS=["置き場所","状態","担当"]
VALUES={"置き場所":["棚A","棚B","棚C","棚D"],"状態":["待機","処理中","完了","保留"],"担当":["担当一","担当二","担当三","担当四"]}
STATE_FORMS=["{o}の置き場所は{loc}、状態は{status}、担当は{owner}です。","{o}について、保管先={loc}／進行={status}／受持={owner}。"]
CMD={"置き場所":["{o}を{v}へ移してください。","{o}の保管先を{v}へ変更します。"],"状態":["{o}を{v}にしてください。","{o}の進行状態を{v}へ切り替えます。"],"担当":["{o}を{v}の担当にしてください。","{o}の受け持ちを{v}へ変更します。"]}
HELD={"置き場所":["対象{o}、次から{v}で保管。","保管場所は{v}。対象は{o}。"],"状態":["対象{o}は以後{v}扱い。","進行を{v}へ。対象は{o}。"],"担当":["{o}は{v}へ引き継ぎ。","受持は{v}。対象は{o}。"]}
OMIT={"置き場所":["それを{v}へ移してください。"],"状態":["その対象を{v}にしてください。"],"担当":["担当は{v}へ変えてください。"]}
QUERIES={"置き場所":["{o}の置き場所は？","{o}の保管先を教えて。"],"状態":["{o}の状態は？","{o}の進行状況を教えて。"],"担当":["{o}の担当は？","{o}の受け持ちは誰？"]}
DISTRACT=["別件の資料を確認しました。","今日は気温が高いです。","更新とは無関係な話です。"]
def grams(s):
 s="".join(s.split());return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))
def cos(a,b):
 d=sum(v*b.get(k,0) for k,v in a.items());na=math.sqrt(sum(v*v for v in a.values()));nb=math.sqrt(sum(v*v for v in b.values()));return d/(na*nb+1e-12)
def diff(a,b):
 l=0
 while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
 r=0
 while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
 return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def around(text,token,radius=8):
 i=text.find(token)
 return None if i<0 else (text[max(0,i-radius):i],text[i+len(token):i+len(token)+radius])
@dataclass
class Ep:
 before:str;command:str;after:str;obj:str;field:str;value:str;event:int;focus:str|None=None
@dataclass
class Rule:
 cmd_l:str;cmd_r:str;state_l:str;state_r:str;support:int=0;query_gain:float=0.;nontarget_damage:float=0.;signatures:set=field(default_factory=set);successes:int=0;failures:int=0
 def score(self):return (self.query_gain+1)/(1+self.nontarget_damage)*(self.successes+1)/(self.successes+self.failures+2)
class SurfaceMemory:
 def __init__(self):self.eps=[]
 def learn(self,e):self.eps.append(e)
 def apply(self,state,cmd):
  if not self.eps:return state,False,0
  sim,e=max(((cos(grams(cmd),grams(x.command)),x) for x in self.eps),key=lambda z:z[0])
  if sim<.18:return state,False,1
  l,r,_,new=diff(e.before,e.after);sig=around(e.command,new)
  if not sig:return state,False,1
  a,b=sig;i=cmd.find(a) if a else 0
  if i<0:return state,False,1
  st=i+len(a);en=cmd.find(b,st) if b else len(cmd)
  if en<st:return state,False,1
  return state[:l]+cmd[st:en]+(state[len(state)-r:] if r else ""),True,1
class AddressMemory:
 def __init__(self,invariance=True):self.rules=[];self.invariance=invariance;self.rejected=0
 def propose(self,e):
  l,r,_,new=diff(e.before,e.after);cs=around(e.command,new)
  return None if not new or not cs else Rule(cs[0],cs[1],e.before[:l],e.before[len(e.before)-r:] if r else "")
 def extract(self,cmd,q):
  i=cmd.find(q.cmd_l) if q.cmd_l else 0
  if i<0:return None
  st=i+len(q.cmd_l);en=cmd.find(q.cmd_r,st) if q.cmd_r else len(cmd);v=cmd[st:en] if en>=st else ""
  return v if 0<len(v)<=12 else None
 def execute(self,state,cmd,q):
  v=self.extract(cmd,q)
  if v is None:return state,False
  i=state.find(q.state_l) if q.state_l else 0
  if i<0:return state,False
  st=i+len(q.state_l);en=state.find(q.state_r,st) if q.state_r else len(state)
  return (state[:st]+v+state[en:],True) if en>=st else (state,False)
 def learn(self,e,contrast_states,contrast_queries):
  p=self.propose(e)
  if not p:self.rejected+=1;return
  pred,ok=self.execute(e.before,e.command,p)
  if not ok or pred!=e.after:self.rejected+=1;return
  p.query_gain=1.;p.nontarget_damage=0.
  if self.invariance:
   for st in contrast_states[-6:]:
    out,worked=self.execute(st,e.command,p);p.nontarget_damage+=int(worked and out!=st)
   for q,_ in contrast_queries[-6:]:p.query_gain+=max(0.,cos(grams(q),grams(e.after))-cos(grams(q),grams(e.before)))
  best=None;bs=0.
  for r in self.rules:
   s=(cos(grams(p.cmd_l+p.cmd_r),grams(r.cmd_l+r.cmd_r))+cos(grams(p.state_l+p.state_r),grams(r.state_l+r.state_r)))/2
   if self.invariance:s-=.08*abs(p.nontarget_damage-r.nontarget_damage)
   if s>bs:bs,best=s,r
  if best and bs>=.62:
   best.support+=1;best.query_gain+=p.query_gain;best.nontarget_damage+=p.nontarget_damage;best.signatures.add(p.cmd_l+"|"+p.cmd_r)
  else:p.support=1;p.signatures.add(p.cmd_l+"|"+p.cmd_r);self.rules.append(p)
 def apply(self,state,cmd):
  cand=[]
  for r in self.rules:
   out,ok=self.execute(state,cmd,r)
   if ok:
    s=cos(grams(cmd),grams(r.cmd_l+r.cmd_r))*r.score()/(1+.25*r.nontarget_damage if self.invariance else 1);cand.append((s,r,out))
  if not cand:return state,False,0
  cand.sort(reverse=True,key=lambda x:x[0])
  if cand[0][0]<.025:return state,False,len(cand)
  _,r,out=cand[0];r.successes+=1;return out,True,len(cand)
def state(o,d,form=0):return STATE_FORMS[form].format(o=o,loc=d["置き場所"],status=d["状態"],owner=d["担当"])
def build(seed,n,mode):
 rng=random.Random(seed);world={};eps=[];focus=None
 for t in range(n):
  o=rng.choice(OBJECTS);world.setdefault(o,{f:rng.choice(VALUES[f]) for f in FIELDS});f=rng.choice(FIELDS);nv=rng.choice([v for v in VALUES[f] if v!=world[o][f]])
  form=1 if mode=="alternate" else 0;before=state(o,world[o],form);forms=OMIT[f] if mode=="omitted" else (HELD[f] if mode in ("held","combined") else CMD[f]);cmd=rng.choice(forms).format(o=o,v=nv);world[o][f]=nv;after=state(o,world[o],form);eps.append(Ep(before,cmd,after,o,f,nv,t,focus));focus=o
  if mode=="long":eps.extend(Ep("",rng.choice(DISTRACT),"","","","",-1,focus) for _ in range(rng.randint(3,8)))
 return eps,world
def evaluate(seed,n,mode):
 eps,truth=build(seed,n,mode);methods={"surface":SurfaceMemory(),"program":AddressMemory(False),"cross_query":AddressMemory(True)};out={}
 for name,m in methods.items():
  stored=[];contrasts=[];qhist=[];writes=reads=correct=0;st=time.perf_counter()
  for e in eps:
   if e.event<0:continue
   m.learn(e,contrasts,qhist) if isinstance(m,AddressMemory) else m.learn(e);pred,_,r=m.apply(e.before,e.command);reads+=r;writes+=1;correct+=int(pred==e.after);stored.append(pred);contrasts.append(e.before);qhist.append((random.Random(seed+e.event).choice(QUERIES[e.field]).format(o=e.obj),e.after))
  train=time.perf_counter()-st;qst=time.perf_counter();rc=wrong=0
  for o,d in truth.items():
   for f in FIELDS:
    q=random.Random(seed+len(o)+len(f)).choice(QUERIES[f]).format(o=o);ranked=sorted(((cos(grams(q),grams(s)),s) for s in stored),reverse=True,key=lambda x:x[0])
    if ranked:
     selected=ranked[0][1];rc+=int(o in selected and d[f] in selected);wrong+=int(o not in selected)
  total=max(1,len(truth)*len(FIELDS));out[name]={"write_accuracy":correct/max(1,writes),"address_read_accuracy":rc/total,"wrong_object_read_rate":wrong/total,"model_bytes":len(pickle.dumps(m)),"training_seconds":train,"inference_ms":(time.perf_counter()-qst)*1000/total,"units":len(getattr(m,"rules",getattr(m,"eps",[]))),"mean_reads":reads/max(1,writes),"rejected":getattr(m,"rejected",0)}
 return out
def one_shot(seed):
 e=build(seed,1,"seen")[0][0];out={}
 for name,m in (("surface",SurfaceMemory()),("program",AddressMemory(False)),("cross_query",AddressMemory(True))):
  m.learn(e,[],[]) if isinstance(m,AddressMemory) else m.learn(e);out[name]=float(m.apply(e.before,e.command)[0]==e.after)
 return out
def interference(seed):
 target=build(seed,1,"seen")[0][0];stream=[target]
 for i in range(50):stream+=build(seed+100+i,1,"seen")[0]
 h=build(seed+999,1,"held")[0][0];h=Ep(h.before.replace(h.obj,target.obj),h.command.replace(h.obj,target.obj),h.after.replace(h.obj,target.obj),target.obj,h.field,h.value,999,target.obj);out={}
 for name,m in (("surface",SurfaceMemory()),("program",AddressMemory(False)),("cross_query",AddressMemory(True))):
  cs=[];qs=[]
  for e in stream:
   m.learn(e,cs,qs) if isinstance(m,AddressMemory) else m.learn(e);cs.append(e.before);qs.append((QUERIES[e.field][0].format(o=e.obj),e.after))
  m.learn(h,cs,qs) if isinstance(m,AddressMemory) else m.learn(h);out[name]=float(m.apply(h.before,h.command)[0]==h.after)
 return out
def summarize(raw):
 s={}
 for n,runs in raw.items():
  s[n]={}
  for mode in ("seen","held","alternate","omitted","long","combined"):
   s[n][mode]={m:{k:statistics.mean(r[mode][m][k] for r in runs) for k in runs[0][mode][m]} for m in ("surface","program","cross_query")}
  for p in ("one_shot","interference"):s[n][p]={m:statistics.mean(r[p][m] for r in runs) for m in ("surface","program","cross_query")}
 return s
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--output",default="results_cycle_014.json");a=ap.parse_args();raw={}
 for n in (24,72,216):
  raw[str(n)]=[]
  for seed in (1,7,19):
   r={mode:evaluate(seed,n,mode) for mode in ("seen","held","alternate","omitted","long","combined")};r["one_shot"]=one_shot(seed);r["interference"]=interference(seed);raw[str(n)].append(r)
 payload={"hypothesis":"Object-Relation Address Discovery by Cross-Query Write/Read Invariance","seeds":[1,7,19],"sizes":[24,72,216],"raw":raw,"summary":summarize(raw),"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"estimated_complexity":"learn O(NPG + NQG), write O(PG), read O(MG)","learner_hidden_labels":False,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
 with open(a.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
 print(json.dumps(payload["summary"]["216"],ensure_ascii=False,indent=2))
if __name__=="__main__":main()
