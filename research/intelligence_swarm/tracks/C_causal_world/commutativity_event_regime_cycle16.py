"""Series C Cycle 016
Event-Regime Discovery from Intervention Commutativity Breaks.

Learner input: raw Japanese before/command/after strings and sequence order only.
Hidden object/field/regime labels are evaluator-only.
No external model, morphology, ontology, or hand-written semantic slots.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=["青い箱","赤い箱","端末甲","端末乙","試料A","試料B"]
FIELDS=["場所","状態","担当"]
VALUES={"場所":["棚A","棚B","棚C","棚D"],"状態":["待機","処理中","完了","保留"],"担当":["担当一","担当二","担当三","担当四"]}
STATE_FORMS=["{o}の場所は{loc}、状態は{status}、担当は{owner}。","{o}について、保管={loc}／進行={status}／受持={owner}。"]
CMD_FORMS={"場所":["{o}を{v}へ移してください。","{o}の保管先を{v}へ変えます。"],"状態":["{o}を{v}にしてください。","{o}の進行を{v}へ変えます。"],"担当":["{o}を{v}の担当にしてください。","{o}の受持を{v}へ変えます。"]}
OMIT={"場所":["それを{v}へ移してください。"],"状態":["その対象を{v}にしてください。"],"担当":["担当は{v}へ変えてください。"]}
PLAN=["ただし、先ほどの変更は取り消し、{o}を{v}にしてください。","予定を変更します。最終的に{o}は{v}です。"]
DISTRACT=["別件の資料を確認しました。","今日は気温が高いです。","この発話は状態更新ではありません。"]

def grams(s):
    s="".join(s.split())
    return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))
def cosine(a,b):
    d=sum(v*b.get(k,0) for k,v in a.items())
    na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return d/(na*nb+1e-12)
def diff_window(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def state(o,d,form=0):
    return STATE_FORMS[form].format(o=o,loc=d["場所"],status=d["状態"],owner=d["担当"])

@dataclass
class Step:
    before:str; command:str; after:str
    boundary:int; event:int; obj:str; field:str; value:str
    regime:int; form:int

@dataclass
class Edit:
    l:int; r:int; old:str; new:str; cmd_ctx:str; support:int=1
    sig:object=None
    def __post_init__(self):
        if self.sig is None:self.sig=grams(self.cmd_ctx)
    def apply(self,s):
        if self.l>len(s) or self.r>len(s)-self.l:return None
        old=s[self.l:len(s)-self.r if self.r else len(s)]
        if old!=self.old:return None
        return s[:self.l]+self.new+(s[len(s)-self.r:] if self.r else "")

def build(seed,events=36,steps_per_event=4,mode="seen"):
    rng=random.Random(seed); world={}; seq=[]
    for ev in range(events):
        regime=rng.randrange(3); obj=rng.choice(OBJECTS)
        if obj not in world: world[obj]={f:rng.choice(VALUES[f]) for f in FIELDS}
        for j in range(steps_per_event):
            f=FIELDS[(regime+j)%3]
            nv=rng.choice([v for v in VALUES[f] if v!=world[obj][f]])
            form=1 if mode=="alternate" else 0
            before=state(obj,world[obj],form)
            if mode=="omitted" and j>0: cmd=rng.choice(OMIT[f]).format(v=nv)
            else: cmd=rng.choice(CMD_FORMS[f]).format(o=obj,v=nv)
            if mode=="paragraph": cmd=rng.choice(DISTRACT)+"\n"+cmd
            world[obj][f]=nv; after=state(obj,world[obj],form)
            seq.append(Step(before,cmd,after,int(j==0),ev,obj,f,nv,regime,form))
        if mode=="plan":
            f=rng.choice(FIELDS);nv=rng.choice([v for v in VALUES[f] if v!=world[obj][f]])
            before=state(obj,world[obj],0);cmd=rng.choice(PLAN).format(o=obj,v=nv)
            world[obj][f]=nv;after=state(obj,world[obj],0)
            seq.append(Step(before,cmd,after,0,ev,obj,f,nv,regime,0))
    return seq

class SurfaceBoundary:
    def __init__(self):self.prev=None;self.edits=[]
    def fit_step(self,x):
        l,r,o,n=diff_window(x.before,x.after);self.edits.append(Edit(l,r,o,n,x.command))
        score=1.0 if self.prev is None else 1-cosine(grams(self.prev.command),grams(x.command))
        self.prev=x; return score>.72
    def predict(self,before,cmd):
        if not self.edits:return before
        cmd_sig=grams(cmd); e=max(self.edits[-64:],key=lambda z:cosine(cmd_sig,z.sig))
        return e.apply(before) or before

class RegimeCommutativity:
    def __init__(self,use_comm=True,use_support=True):
        self.use_comm=use_comm;self.use_support=use_support;self.regimes=[[]];self.prev_edit=None;self.boundary_scores=[];self.library=[]
    def _edit(self,x):
        l,r,o,n=diff_window(x.before,x.after); return Edit(l,r,o,n,x.command)
    def _comm_break(self,a,b,state):
        if a is None:return 0.0
        ab=a.apply(state)
        if ab is not None:ab=b.apply(ab)
        ba=b.apply(state)
        if ba is not None:ba=a.apply(ba)
        if ab is None and ba is None:return 0.0
        return float(ab!=ba)
    def fit_step(self,x):
        e=self._edit(x)
        novelty=0 if self.prev_edit is None else 1-cosine(self.prev_edit.sig,e.sig)
        comm=self._comm_break(self.prev_edit,e,x.before) if self.use_comm else 0.0
        support=sum(cosine(q.sig,e.sig)>.62 for q in self.library[-64:])
        score=.62*comm+.38*novelty
        boundary=(self.prev_edit is None) or (score>.58 and (not self.use_support or support>=1))
        if boundary and self.regimes[-1]:self.regimes.append([])
        self.regimes[-1].append(e);self.library.append(e);self.prev_edit=e;self.boundary_scores.append(score)
        return boundary
    def predict(self,before,cmd):
        cmd_sig=grams(cmd);pool=self.regimes[-1] if self.regimes and self.regimes[-1] else self.library
        ranked=sorted(((cosine(cmd_sig,e.sig),e) for e in pool[-64:]),reverse=True,key=lambda z:z[0])
        if not ranked or ranked[0][0]<.18:return before
        out=ranked[0][1].apply(before)
        if out is not None:return out
        ranked=sorted(((cosine(cmd_sig,e.sig),e) for e in self.library[-64:]),reverse=True,key=lambda z:z[0])
        for _,e in ranked[:8]:
            out=e.apply(before)
            if out is not None:return out
        return before

def f1(pred,gold):
    tp=sum(p and g for p,g in zip(pred,gold));fp=sum(p and not g for p,g in zip(pred,gold));fn=sum((not p) and g for p,g in zip(pred,gold))
    return 2*tp/(2*tp+fp+fn+1e-12)

def order_counterfactual(model,steps,rng):
    ok=0;n=0
    for i in range(0,len(steps)-1,2):
        a,b=steps[i],steps[i+1]
        if a.obj!=b.obj:continue
        ea=Edit(*diff_window(a.before,a.after),a.command); eb=Edit(*diff_window(b.before,b.after),b.command)
        gold=eb.apply(a.before)
        if gold is not None:gold=ea.apply(gold)
        pred=model.predict(a.before,b.command);pred=model.predict(pred,a.command)
        if gold is not None:ok+=int(pred==gold);n+=1
    return ok/max(1,n)

def run(seed,events,mode):
    seq=build(seed,events,4,mode)
    methods={"surface":SurfaceBoundary(),"regime_no_comm":RegimeCommutativity(False,True),"regime_comm":RegimeCommutativity(True,True),"regime_no_support":RegimeCommutativity(True,False)}
    out={}
    for name,m in methods.items():
        pred_b=[];gold_b=[];correct=0;t=time.perf_counter()
        for x in seq:
            pred=m.fit_step(x);pred_b.append(bool(pred));gold_b.append(bool(x.boundary));correct+=int(m.predict(x.before,x.command)==x.after)
        train=time.perf_counter()-t
        q=time.perf_counter();oc=order_counterfactual(m,seq,random.Random(seed));qms=(time.perf_counter()-q)*1000/max(1,len(seq))
        out[name]={"boundary_f1":f1(pred_b,gold_b),"next_state_accuracy":correct/len(seq),"order_counterfactual_accuracy":oc,"model_bytes":len(pickle.dumps(m)),"training_seconds":train,"inference_ms":qms,"regime_count":len(getattr(m,"regimes",[])) if hasattr(m,"regimes") else sum(pred_b),"edges":len(getattr(m,"library",getattr(m,"edits",[]))),"mean_boundary_score":statistics.mean(getattr(m,"boundary_scores",[0]))}
    return out

def summarize(raw):
    ans={}
    for n,runs in raw.items():
        ans[n]={}
        for mode in ("seen","alternate","omitted","paragraph","plan"):
            ans[n][mode]={}
            for m in runs[0][mode]:ans[n][mode][m]={k:statistics.mean(r[mode][m][k] for r in runs) for k in runs[0][mode][m]}
    return ans

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="results_cycle_016.json");a=ap.parse_args();raw={}
    for n in (8,16,24):
        runs=[]
        for seed in (1,7,19):runs.append({mode:run(seed,n,mode) for mode in ("seen","alternate","omitted","paragraph","plan")})
        raw[str(n)]=runs
    payload={"hypothesis":"Event-Regime Discovery from Intervention Commutativity Breaks","seeds":[1,7,19],"event_counts":[8,16,24],"raw":raw,"summary":summarize(raw),"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"estimated_complexity":"learn O(NK G), infer O(KG), counterfactual O(NK); K bounded by 64 local edits","learner_hidden_labels":False,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(a.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload["summary"]["24"],ensure_ascii=False,indent=2))
if __name__=="__main__":main()
