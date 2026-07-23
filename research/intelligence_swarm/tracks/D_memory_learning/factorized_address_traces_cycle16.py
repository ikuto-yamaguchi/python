"""Track D Cycle 016
Factorized Object/Relation Address Traces from Independent Counterexample Axes.

Learner receives only raw Japanese before/command/after/query strings and order.
Hidden object/relation/value labels are evaluator-only.

This is a controlled falsification experiment, not evidence of unrestricted
Japanese language understanding.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass, field
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS = ["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵","試料甲","試料乙"]
ALIASES = {"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末","大型端末":"大きい端末","北側の鍵":"北のキー","南側の鍵":"南のキー","試料甲":"サンプル甲","試料乙":"サンプル乙"}
FIELDS = ["置き場所","状態","担当"]
VALUES = {"置き場所":["棚A","棚B","棚C","棚D"],"状態":["待機","処理中","完了","保留"],"担当":["担当一","担当二","担当三","担当四"]}
STATE_FORMS = ["{o}の置き場所は{loc}、状態は{status}、担当は{owner}です。","{o}について、保管先={loc}／進行={status}／受持={owner}。","{o}：場所{loc}、進捗{status}、受け持ち{owner}。"]
CMD_SEEN = {"置き場所":["{o}を{v}へ移してください。","{o}の保管先を{v}へ変更します。"],"状態":["{o}を{v}にしてください。","{o}の進行状態を{v}へ切り替えます。"],"担当":["{o}を{v}の担当にしてください。","{o}の受け持ちを{v}へ変更します。"]}
CMD_HELD = {"置き場所":["対象{o}、次から{v}で保管。","保管場所は{v}。対象は{o}。"],"状態":["対象{o}は以後{v}扱い。","進行を{v}へ。対象は{o}。"],"担当":["{o}は{v}へ引き継ぎ。","受持は{v}。対象は{o}。"]}
CMD_OMIT = {"置き場所":["それを{v}へ移してください。"],"状態":["その対象を{v}にしてください。"],"担当":["担当は{v}へ変えてください。"]}
QUERY_SEEN = {"置き場所":["{o}の置き場所は？","{o}の保管先を教えて。"],"状態":["{o}の状態は？","{o}の進行状況を教えて。"],"担当":["{o}の担当は？","{o}の受け持ちは誰？"]}
QUERY_HELD = {"置き場所":["{o}を今どこに置く？"],"状態":["現在の{o}はどういう段階？"],"担当":["今の{o}を受け持つ人は？"]}
DISTRACT = ["別件の資料を確認しました。","今日は気温が高いです。","更新とは無関係な話です。"]

def grams(s):
    s="".join(s.split()); return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))
def cosine(a,b):
    d=sum(v*b.get(k,0) for k,v in a.items()); na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values())); return d/(na*nb+1e-12)
def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def spans(text,min_len=2,max_len=12,cap=64):
    cand=[]
    for i in range(len(text)):
        for j in range(i+min_len,min(len(text),i+max_len)+1):
            x=text[i:j]
            if not x.strip() or all(c in "、。？／=：" for c in x): continue
            boundary=int(i==0 or text[i-1] in "、。／=：")+int(j==len(text) or text[j:j+1] in "、。／=：")
            cand.append((boundary,len(x),i,j,x))
    cand.sort(reverse=True); out=[]; seen=set()
    for z in cand:
        if z[-1] not in seen: seen.add(z[-1]); out.append(z)
        if len(out)>=cap: break
    return out
def context(text,token,radius=7):
    i=text.find(token); return None if i<0 else (text[max(0,i-radius):i],text[i+len(token):i+len(token)+radius])

@dataclass
class Episode:
    before:str; command:str; after:str; queries:list[str]; obj:str; field_name:str; value:str; event:int; focus_text:str
@dataclass
class JointNode:
    obj_span:str; rel_span:str; cmd_l:str; cmd_r:str; state_l:str; state_r:str; support:int=1; qgrams:Counter=field(default_factory=Counter)
@dataclass
class ObjectTrace:
    aliases:Counter=field(default_factory=Counter); query_grams:Counter=field(default_factory=Counter); temporal_support:int=0; wrong_object:int=0; last_seen:int=-1
    def reliability(self): return (self.temporal_support+1)/(self.temporal_support+self.wrong_object+2)
@dataclass
class RelationTrace:
    state_l:str=""; state_r:str=""; cmd_l:str=""; cmd_r:str=""; query_grams:Counter=field(default_factory=Counter); support:int=0; wrong_relation:int=0
    def reliability(self): return (self.support+1)/(self.support+self.wrong_relation+2)
@dataclass
class Address:
    object_id:int; relation_id:int; support:int=0; writes:int=0; reads:int=0; damage:int=0
    def reliability(self): return (self.writes+self.reads+1)/(self.writes+self.reads+self.damage+2)

class EpisodicReplay:
    def __init__(self): self.items=[]
    def learn(self,e,t,history): self.items.append(e)
    def write(self,state,cmd,focus=None):
        if not self.items:return state,False,0
        sim,e=max(((cosine(grams(cmd),grams(x.command)),x) for x in self.items),key=lambda z:z[0])
        if sim<.18:return state,False,1
        l,r,_,new=diff(e.before,e.after); ctx=context(e.command,new)
        if not ctx:return state,False,1
        a,b=ctx; i=cmd.find(a) if a else 0
        if i<0:return state,False,1
        st=i+len(a); en=cmd.find(b,st) if b else len(cmd)
        if en<st:return state,False,1
        return state[:l]+cmd[st:en]+(state[len(state)-r:] if r else ""),True,1
    def read(self,q,states): return (None,0) if not states else (max(states,key=lambda s:cosine(grams(q),grams(s))),len(states))

class JointAddress:
    def __init__(self): self.nodes=[]; self.rejected=0
    def learn(self,e,t,history):
        l,r,old,new=diff(e.before,e.after); c=context(e.command,new)
        if not new or not c:self.rejected+=1;return
        qtext=" ".join(e.queries); objs=[x for *_,x in spans(e.before) if x in e.command and x in qtext][:4]
        rels=[x for *_,x in spans(qtext,2,10,48) if x in e.before and x not in old and x not in new][:4] or [""]
        if not objs:self.rejected+=1;return
        for o in objs:
            for rel in rels:
                n=JointNode(o,rel,c[0],c[1],e.before[:l],e.before[len(e.before)-r:] if r else ""); n.qgrams.update(grams(qtext)); self.nodes.append(n)
        self.nodes=self.nodes[-64:]
    def _execute(self,state,cmd,n):
        i=cmd.find(n.cmd_l) if n.cmd_l else 0
        if i<0:return state,False
        st=i+len(n.cmd_l); en=cmd.find(n.cmd_r,st) if n.cmd_r else len(cmd)
        if en<st:return state,False
        v=cmd[st:en]; i2=state.find(n.state_l) if n.state_l else 0
        if i2<0:return state,False
        st2=i2+len(n.state_l); en2=state.find(n.state_r,st2) if n.state_r else len(state)
        return (state[:st2]+v+state[en2:],True) if en2>=st2 else (state,False)
    def write(self,state,cmd,focus=None):
        cand=[]
        for n in self.nodes:
            out,ok=self._execute(state,cmd,n)
            if ok:cand.append((cosine(grams(cmd),grams(n.cmd_l+n.cmd_r))+.2*int(n.obj_span in cmd),out))
        if not cand:return state,False,0
        cand.sort(reverse=True); return cand[0][1],True,len(cand)
    def read(self,q,states):
        if not self.nodes:return None,0
        n=max(self.nodes,key=lambda x:cosine(grams(q),x.qgrams)+.2*int(x.obj_span in q)); m=[s for s in states if n.obj_span in s]
        return (m[-1],len(self.nodes)) if m else (None,len(self.nodes))

class FactorizedMemory:
    def __init__(self,contrastive=True):
        self.objects=[]; self.relations=[]; self.addresses=[]; self.contrastive=contrastive; self.rejected=0; self.fast_updates=0
    def _object_candidates(self,e):
        qtext=" ".join(e.queries); c=[]
        for *_,x in spans(e.before,2,12,64):
            score=int(x in e.command)+int(x in qtext)+int(x==e.focus_text)
            if score>=2:c.append((score,len(x),x))
        if not c and e.focus_text and any(w in e.command for w in ("それ","その対象","担当は")): c.append((2,len(e.focus_text),e.focus_text))
        c.sort(reverse=True); return [x for _,_,x in c[:6]]
    def _relation_candidates(self,e,old,new):
        qtext=" ".join(e.queries); out=[]
        for *_,x in spans(qtext,2,10,64):
            if x in e.before and x not in old and x not in new and x not in e.command: out.append((len(x),x))
        if not out:
            l,r,_,_=diff(e.before,e.after); out=[(0,e.before[max(0,l-6):l]+"|"+(e.before[len(e.before)-r:][:6] if r else ""))]
        out.sort(reverse=True); return [x for _,x in out[:6]]
    def _find_object(self,span,qgrams,t):
        best=None; bs=0
        for i,o in enumerate(self.objects):
            alias=max((cosine(grams(span),grams(a)) for a in o.aliases),default=0); qs=cosine(qgrams,o.query_grams); temporal=1/(1+max(0,t-o.last_seen)); s=.45*alias+.35*qs+.20*temporal
            if s>bs:bs,best=s,i
        if best is not None and bs>=.58:return best
        self.objects.append(ObjectTrace()); return len(self.objects)-1
    def _find_relation(self,sl,sr,cl,cr,qgrams):
        best=None; bs=0
        for i,r in enumerate(self.relations):
            s=.40*cosine(grams(sl+sr),grams(r.state_l+r.state_r))+.30*cosine(grams(cl+cr),grams(r.cmd_l+r.cmd_r))+.30*cosine(qgrams,r.query_grams)
            if s>bs:bs,best=s,i
        if best is not None and bs>=.62:return best
        self.relations.append(RelationTrace(sl,sr,cl,cr)); return len(self.relations)-1
    def _extract(self,cmd,r):
        i=cmd.find(r.cmd_l) if r.cmd_l else 0
        if i<0:return None
        st=i+len(r.cmd_l); en=cmd.find(r.cmd_r,st) if r.cmd_r else len(cmd)
        if en<st:return None
        v=cmd[st:en]; return v if 0<len(v)<=12 else None
    def _execute(self,state,cmd,r):
        v=self._extract(cmd,r)
        if v is None:return state,False
        i=state.find(r.state_l) if r.state_l else 0
        if i<0:return state,False
        st=i+len(r.state_l); en=state.find(r.state_r,st) if r.state_r else len(state)
        return (state[:st]+v+state[en:],True) if en>=st else (state,False)
    def learn(self,e,t,history):
        l,r,old,new=diff(e.before,e.after); cc=context(e.command,new)
        if not new or not cc:self.rejected+=1;return
        objs=self._object_candidates(e); rels=self._relation_candidates(e,old,new)
        if not objs or not rels:self.rejected+=1;return
        qg=grams(" ".join(e.queries)); sl=e.before[:l]; sr=e.before[len(e.before)-r:] if r else ""; accepted=0
        for os in objs:
            oi=self._find_object(os,qg,t); ot=self.objects[oi]; ot.aliases[os]+=1; ot.query_grams.update(qg); ot.temporal_support+=1; ot.last_seen=t
            for _ in rels:
                ri=self._find_relation(sl,sr,cc[0],cc[1],qg); rt=self.relations[ri]; rt.query_grams.update(qg); rt.support+=1
                out,ok=self._execute(e.before,e.command,rt)
                if not ok or out!=e.after:continue
                damage=0
                if self.contrastive:
                    for h in history[-10:]:
                        if os not in h.before:
                            out2,worked=self._execute(h.before,e.command,rt); damage+=int(worked and out2!=h.before)
                        elif cosine(qg,grams(" ".join(h.queries)))<.25:
                            out2,worked=self._execute(h.before,e.command,rt); damage+=int(worked and out2!=h.before)
                ot.wrong_object+=damage; rt.wrong_relation+=damage
                a=next((a for a in self.addresses if a.object_id==oi and a.relation_id==ri),None)
                if a is None:a=Address(oi,ri);self.addresses.append(a)
                a.support+=1;a.writes+=1;a.damage+=damage;accepted+=1
        self.fast_updates+=accepted
        if not accepted:self.rejected+=1
        if len(self.addresses)>64:self.addresses=sorted(self.addresses,key=lambda a:(a.reliability(),a.support),reverse=True)[:64]
    def write(self,state,cmd,focus=None):
        cand=[]
        for a in self.addresses:
            o=self.objects[a.object_id]; r=self.relations[a.relation_id]; obj_score=max([int(alias in cmd) for alias in o.aliases] or [0])
            if not obj_score and focus:obj_score=max([cosine(grams(focus),grams(alias)) for alias in o.aliases] or [0])
            out,ok=self._execute(state,cmd,r)
            if ok:cand.append((.40*obj_score+.35*cosine(grams(cmd),grams(r.cmd_l+r.cmd_r))+.25*a.reliability(),a,out))
        if not cand:return state,False,0
        cand.sort(reverse=True,key=lambda x:x[0])
        if len(cand)>1 and cand[0][0]-cand[1][0]<.04:return state,False,len(cand)
        return cand[0][2],True,len(cand)
    def read(self,q,states):
        cand=[]; qg=grams(q)
        for a in self.addresses:
            o=self.objects[a.object_id]; r=self.relations[a.relation_id]; os=max([cosine(qg,grams(alias)) for alias in o.aliases] or [0]); rs=cosine(qg,r.query_grams); cand.append((.50*os+.35*rs+.15*a.reliability(),a))
        if not cand:return None,0
        cand.sort(reverse=True,key=lambda x:x[0])
        if len(cand)>1 and cand[0][0]-cand[1][0]<.035:return None,len(cand)
        a=cand[0][1]; aliases=list(self.objects[a.object_id].aliases); matching=[st for st in states if any(x in st for x in aliases)]
        return (matching[-1],len(cand)) if matching else (None,len(cand))

def make_state(o,d,form=0):return STATE_FORMS[form].format(o=o,loc=d["置き場所"],status=d["状態"],owner=d["担当"])
def build(seed,n,mode):
    rng=random.Random(seed);world={};eps=[];focus=""
    for t in range(n):
        canonical=rng.choice(OBJECTS); surface=ALIASES[canonical] if mode=="rename" and rng.random()<.6 else canonical; world.setdefault(canonical,{f:rng.choice(VALUES[f]) for f in FIELDS}); f=rng.choice(FIELDS); nv=rng.choice([v for v in VALUES[f] if v!=world[canonical][f]]); form=1 if mode=="alternate" else 0; before=make_state(surface,world[canonical],form); forms=CMD_OMIT[f] if mode=="omitted" else (CMD_HELD[f] if mode in ("held","combined","rename") else CMD_SEEN[f]); cmd=rng.choice(forms).format(o=surface,v=nv); world[canonical][f]=nv; after=make_state(surface,world[canonical],form); qforms=QUERY_HELD[f] if mode in ("held","combined","rename") else QUERY_SEEN[f]; queries=[x.format(o=surface) for x in qforms]; eps.append(Episode(before,cmd,after,queries,canonical,f,nv,t,focus)); focus=surface
        if mode=="long":eps.extend(Episode("",rng.choice(DISTRACT),"",[],"","","",-1,focus) for _ in range(rng.randint(3,8)))
    return eps,world

def evaluate(seed,n,mode):
    eps,truth=build(seed,n,mode); methods={"episodic":EpisodicReplay(),"joint":JointAddress(),"factorized":FactorizedMemory(False),"contrastive":FactorizedMemory(True)}; out={}
    for name,m in methods.items():
        states=[];history=[];writes=wc=read_ops=0;start=time.perf_counter();focus=""
        for e in eps:
            if e.event<0:continue
            m.learn(e,e.event,history); pred,_,r=m.write(e.before,e.command,focus); writes+=1; wc+=int(pred==e.after); states.append(pred); history.append(e); focus=e.focus_text or focus
        train=time.perf_counter()-start; qs=time.perf_counter();rc=wrong=abstain=total=0
        for canonical,d in truth.items():
            surface=ALIASES[canonical] if mode=="rename" else canonical
            for f in FIELDS:
                qforms=QUERY_HELD[f] if mode in ("held","combined","rename") else QUERY_SEEN[f]; q=random.Random(seed+len(canonical)+len(f)).choice(qforms).format(o=surface); selected,r=m.read(q,states);read_ops+=r;total+=1
                if selected is None:abstain+=1;continue
                rc+=int(surface in selected and d[f] in selected); wrong+=int(surface not in selected)
        out[name]={"write_accuracy":wc/max(1,writes),"read_accuracy":rc/max(1,total),"wrong_object_rate":wrong/max(1,total),"abstain_rate":abstain/max(1,total),"model_bytes":len(pickle.dumps(m)),"training_seconds":train,"inference_ms":(time.perf_counter()-qs)*1000/max(1,total),"object_traces":len(getattr(m,"objects",[])),"relation_traces":len(getattr(m,"relations",[])),"addresses":len(getattr(m,"addresses",getattr(m,"nodes",getattr(m,"items",[])))),"fast_updates":getattr(m,"fast_updates",0),"rejected":getattr(m,"rejected",0)}
    return out

def one_shot(seed):
    e=build(seed,1,"seen")[0][0];out={}
    for name,m in (("episodic",EpisodicReplay()),("joint",JointAddress()),("factorized",FactorizedMemory(False)),("contrastive",FactorizedMemory(True))):m.learn(e,0,[]);p,_,_=m.write(e.before,e.command,e.focus_text);out[name]=float(p==e.after)
    return out

def interference(seed):
    target=build(seed,1,"seen")[0][0];stream=[target]
    for i in range(50):stream.extend(build(seed+100+i,1,"seen")[0])
    h=build(seed+999,1,"held")[0][0];h=Episode(h.before.replace(h.obj,target.obj),h.command.replace(h.obj,target.obj),h.after.replace(h.obj,target.obj),[q.replace(h.obj,target.obj) for q in h.queries],target.obj,h.field_name,h.value,999,target.obj);out={}
    for name,m in (("episodic",EpisodicReplay()),("joint",JointAddress()),("factorized",FactorizedMemory(False)),("contrastive",FactorizedMemory(True))):
        hist=[]
        for e in stream:m.learn(e,e.event,hist);hist.append(e)
        m.learn(h,999,hist);p,_,_=m.write(h.before,h.command,target.obj);selected,_=m.read(h.queries[0],[p]);out[name]={"write":float(p==h.after),"read":float(selected is not None and h.value in selected)}
    return out

def summarize(raw):
    s={}
    for n,runs in raw.items():
        s[n]={}
        for mode in ("seen","held","rename","alternate","omitted","long","combined"):
            s[n][mode]={}
            for m in ("episodic","joint","factorized","contrastive"):
                keys=runs[0][mode][m];s[n][mode][m]={k:statistics.mean(r[mode][m][k] for r in runs) for k in keys}
        s[n]["one_shot"]={m:statistics.mean(r["one_shot"][m] for r in runs) for m in ("episodic","joint","factorized","contrastive")};s[n]["interference"]={m:{k:statistics.mean(r["interference"][m][k] for r in runs) for k in ("write","read")} for m in ("episodic","joint","factorized","contrastive")}
    return s

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="results_cycle_016.json");a=ap.parse_args();raw={}
    for n in (24,72,216):
        runs=[]
        for seed in (1,7,19):
            r={mode:evaluate(seed,n,mode) for mode in ("seen","held","rename","alternate","omitted","long","combined")};r["one_shot"]=one_shot(seed);r["interference"]=interference(seed);runs.append(r)
        raw[str(n)]=runs
    payload={"hypothesis":"Factorized Object/Relation Address Traces from Independent Counterexample Axes","seeds":[1,7,19],"sizes":[24,72,216],"raw":raw,"summary":summarize(raw),"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"estimated_complexity":"proposal O(L^2), learning O(N(Ho+Hr)G), sparse address O(A G), A<=64","learner_hidden_labels":False,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(a.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload["summary"]["216"],ensure_ascii=False,indent=2))
if __name__=="__main__":main()
