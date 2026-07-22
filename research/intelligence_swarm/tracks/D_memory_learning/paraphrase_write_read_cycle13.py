"""Track D Cycle 013: paraphrase-invariant write/read program probe.

The learner sees only raw Japanese before/utterance/after/query strings.
Hidden object/field/value labels are evaluator-only and are never passed into
proposal, consolidation, write, or read logic.

This is a controlled falsification probe, not evidence of unrestricted
Japanese understanding.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass, field
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS = ["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵","試料甲","試料乙"]
FIELDS = ["置き場所","状態","担当"]
VALUES = {
    "置き場所":["棚A","棚B","棚C","棚D"],
    "状態":["待機","処理中","完了","保留"],
    "担当":["担当一","担当二","担当三","担当四"],
}
STATE_FORMS = [
    "{o}の置き場所は{loc}、状態は{status}、担当は{owner}です。",
    "{o}について、場所={loc}、状態={status}、担当={owner}。",
]
COMMAND_FORMS = {
    "置き場所":["{o}を{v}へ移してください。","{o}の置き場所を{v}に更新します。","{o}は今後{v}で保管します。"],
    "状態":["{o}を{v}にしてください。","{o}の状態を{v}へ変更します。","{o}はこれから{v}として扱います。"],
    "担当":["{o}を{v}の担当にしてください。","{o}の担当を{v}へ変更します。","{o}は今後{v}が受け持ちます。"],
}
HELD_COMMAND_FORMS = {
    "置き場所":["保管先を{v}へ。対象は{o}です。","{o}、次から{v}に置きます。"],
    "状態":["{o}については{v}へ切り替え。","{o}を以後{v}扱いに。"],
    "担当":["{o}は{v}へ引き継ぎます。","受け持ちは{v}、対象は{o}。"],
}
OMITTED_FORMS = {
    "置き場所":["それを{v}へ移してください。"],
    "状態":["その対象を{v}にしてください。"],
    "担当":["担当は{v}へ変えてください。"],
}
QUERY_FORMS = ["{o}の現在の記録を教えてください。","{o}について最新の情報は何ですか。"]
HELD_QUERY_FORMS = ["{o}の直近状態を確認したいです。","今の{o}はどうなっていますか。"]
DISTRACTORS = ["別件の資料を確認しました。","今日は気温が高いです。","この発話は更新ではありません。","少し休憩します。"]

def grams(s: str) -> Counter[str]:
    s = "".join(s.split())
    return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))

def cosine(a: Counter[str], b: Counter[str]) -> float:
    dot=sum(v*b.get(k,0) for k,v in a.items())
    na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return dot/(na*nb+1e-12)

def diff_window(a: str,b: str):
    left=0
    while left<min(len(a),len(b)) and a[left]==b[left]: left+=1
    right=0
    while right<min(len(a)-left,len(b)-left) and a[-1-right]==b[-1-right]: right+=1
    return left,right,a[left:len(a)-right if right else len(a)],b[left:len(b)-right if right else len(b)]

def context_signature(text: str, value: str):
    i=text.find(value)
    if i<0: return None
    return text[max(0,i-8):i], text[i+len(value):i+len(value)+8]

@dataclass
class Episode:
    before: str
    utterance: str
    after: str
    obj: str
    field: str
    new_value: str
    event_id: int

@dataclass
class Program:
    cmd_left: str
    cmd_right: str
    state_left: str
    state_right: str
    support: int = 0
    successes: int = 0
    failures: int = 0
    paraphrase_families: set[str] = field(default_factory=set)
    @property
    def eligibility(self):
        return (self.successes+1)/(self.successes+self.failures+2)

class SurfaceReplay:
    def __init__(self): self.episodes=[]
    def learn(self,ep): self.episodes.append(ep)
    def update(self,state,utterance):
        ug=grams(utterance)
        ranked=sorted(((cosine(ug,grams(e.utterance)),e) for e in self.episodes),reverse=True,key=lambda x:x[0])
        if not ranked or ranked[0][0]<0.20: return state,False,1
        e=ranked[0][1]; _,_,_,new=diff_window(e.before,e.after); sig=context_signature(e.utterance,new)
        if not sig: return state,False,1
        l,r=sig; li=utterance.find(l) if l else 0
        if li<0: return state,False,1
        start=li+len(l); end=utterance.find(r,start) if r else len(utterance)
        if end<start:return state,False,1
        value=utterance[start:end]; dl,dr,_,_=diff_window(e.before,e.after)
        return state[:dl]+value+(state[len(state)-dr:] if dr else ""),True,1

class ConsolidatedPrograms:
    def __init__(self, contrastive=True):
        self.contrastive=contrastive; self.programs=[]; self.focus_state=None; self.rejected=0
    def propose(self,ep):
        left,right,_,new=diff_window(ep.before,ep.after); sig=context_signature(ep.utterance,new)
        if not sig or not new:return None
        cl,cr=sig
        return Program(cl,cr,ep.before[:left],ep.before[len(ep.before)-right:] if right else "")
    def learn(self,ep):
        p=self.propose(ep)
        if p is None: self.rejected+=1; return
        best=None; bestscore=0
        for q in self.programs:
            score=(cosine(grams(p.cmd_left+p.cmd_right),grams(q.cmd_left+q.cmd_right))+cosine(grams(p.state_left+p.state_right),grams(q.state_left+q.state_right)))/2
            if score>bestscore: bestscore,best=score,q
        if best is not None and bestscore>=0.52:
            best.support+=1; best.paraphrase_families.add(p.cmd_left+"|"+p.cmd_right)
        else:
            p.support=1; p.paraphrase_families.add(p.cmd_left+"|"+p.cmd_right); self.programs.append(p)
    def _extract(self,u,p):
        li=u.find(p.cmd_left) if p.cmd_left else 0
        if li<0:return None
        st=li+len(p.cmd_left); en=u.find(p.cmd_right,st) if p.cmd_right else len(u)
        if en<st:return None
        v=u[st:en]
        return v if 0<len(v)<=12 else None
    def update(self,state,utterance):
        scored=[]
        for p in self.programs:
            v=self._extract(utterance,p)
            if v is None: continue
            score=cosine(grams(utterance),grams(p.cmd_left+p.cmd_right))*p.eligibility
            if self.contrastive: score*=min(1.0,len(p.paraphrase_families)/2)
            scored.append((score,p,v))
        scored.sort(reverse=True,key=lambda x:x[0])
        if not scored or scored[0][0]<0.08:return state,False,len(scored)
        _,p,v=scored[0]; li=state.find(p.state_left) if p.state_left else 0
        if li<0: p.failures+=1; return state,False,len(scored)
        st=li+len(p.state_left); en=state.find(p.state_right,st) if p.state_right else len(state)
        if en<st: p.failures+=1; return state,False,len(scored)
        candidate=state[:st]+v+state[en:]; p.successes+=1; self.focus_state=candidate
        return candidate,True,len(scored)

def make_state(o,vals,form):
    return STATE_FORMS[form].format(o=o,loc=vals["置き場所"],status=vals["状態"],owner=vals["担当"])

def build(seed,n,held=False,omitted=False,alternate=False,long_dialogue=False):
    rng=random.Random(seed); states={}; eps=[]; event=0
    for _ in range(n):
        o=rng.choice(OBJECTS)
        if o not in states: states[o]={f:rng.choice(VALUES[f]) for f in FIELDS}
        fld=rng.choice(FIELDS); nv=rng.choice([v for v in VALUES[fld] if v!=states[o][fld]])
        form=1 if alternate else 0; before=make_state(o,states[o],form)
        forms=OMITTED_FORMS[fld] if omitted else (HELD_COMMAND_FORMS[fld] if held else COMMAND_FORMS[fld])
        utter=rng.choice(forms).format(o=o,v=nv); states[o][fld]=nv; after=make_state(o,states[o],form)
        if long_dialogue:
            for _d in range(rng.randint(3,10)): eps.append(Episode("",rng.choice(DISTRACTORS),"","","","",-1))
        eps.append(Episode(before,utter,after,o,fld,nv,event)); event+=1
    return eps,states

def evaluate(seed,n,mode):
    held=mode in ("held","combined"); omitted=mode=="omitted"; alternate=mode=="alternate"; long_dialogue=mode=="long"
    eps,truth=build(seed,n,held,omitted,alternate,long_dialogue)
    methods={"surface":SurfaceReplay(),"program":ConsolidatedPrograms(False),"contrastive":ConsolidatedPrograms(True)}; outputs={}
    for name,m in methods.items():
        live={}; start=time.perf_counter(); update_ok=reads=total=0
        for ep in eps:
            if ep.event_id<0: continue
            if ep.obj not in live: live[ep.obj]=ep.before
            m.learn(ep); pred,_,r=m.update(live[ep.obj],ep.utterance); reads+=r; total+=1; update_ok+=int(pred==ep.after); live[ep.obj]=pred
        train=time.perf_counter()-start; qstart=time.perf_counter(); recall=0
        for o,vals in truth.items():
            query=random.Random(seed+len(o)).choice(HELD_QUERY_FORMS if held else QUERY_FORMS).format(o=o)
            best=max(live.values(),key=lambda st:cosine(grams(query),grams(st)))
            recall+=int(best==make_state(o,vals,1 if alternate else 0))
        qms=(time.perf_counter()-qstart)*1000/max(1,len(truth))
        outputs[name]={"write_accuracy":update_ok/max(1,total),"read_accuracy":recall/max(1,len(truth)),"model_bytes":len(pickle.dumps(m)),"training_seconds":train,"inference_ms":qms,"programs":len(getattr(m,"programs",getattr(m,"episodes",[]))),"mean_reads":reads/max(1,total),"rejected":getattr(m,"rejected",0)}
    return outputs

def one_shot(seed):
    eps,_=build(seed,1); out={}
    for name,m in (("surface",SurfaceReplay()),("program",ConsolidatedPrograms(False)),("contrastive",ConsolidatedPrograms(True))):
        ep=eps[0]; m.learn(ep); pred,_,_=m.update(ep.before,ep.utterance); out[name]=float(pred==ep.after)
    return out

def interference(seed):
    rng=random.Random(seed); base,_=build(seed,1); target=base[0]; stream=[target]
    for i in range(50): stream.extend(build(seed+100+i,1)[0])
    vals={f:rng.choice(VALUES[f]) for f in FIELDS}; vals[target.field]=target.new_value; before=target.after
    nv=rng.choice([v for v in VALUES[target.field] if v!=target.new_value]); after_vals=vals.copy(); after_vals[target.field]=nv
    final=Episode(before,HELD_COMMAND_FORMS[target.field][0].format(o=target.obj,v=nv),make_state(target.obj,after_vals,0),target.obj,target.field,nv,999); stream.append(final)
    out={}
    for name,m in (("surface",SurfaceReplay()),("program",ConsolidatedPrograms(False)),("contrastive",ConsolidatedPrograms(True))):
        live={}
        for ep in stream:
            if ep.obj not in live:live[ep.obj]=ep.before
            m.learn(ep); pred,_,_=m.update(live[ep.obj],ep.utterance); live[ep.obj]=pred
        out[name]=float(live[target.obj]==final.after)
    return out

def summarize(raw):
    out={}
    for n,runs in raw.items():
        out[n]={}
        for mode in ("seen","held","alternate","omitted","long","combined"):
            out[n][mode]={}
            for method in ("surface","program","contrastive"):
                keys=runs[0][mode][method].keys(); out[n][mode][method]={k:statistics.mean(r[mode][method][k] for r in runs) for k in keys}
        for probe in ("one_shot","interference"): out[n][probe]={m:statistics.mean(r[probe][m] for r in runs) for m in ("surface","program","contrastive")}
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="results_cycle_013.json"); args=ap.parse_args(); raw={}
    for n in (24,72,216):
        runs=[]
        for seed in (1,7,19):
            r={mode:evaluate(seed,n,mode) for mode in ("seen","held","alternate","omitted","long","combined")}; r["one_shot"]=one_shot(seed); r["interference"]=interference(seed); runs.append(r)
        raw[str(n)]=runs
    payload={"hypothesis":"Paraphrase-Invariant Write/Read Programs with Contrastive Eligibility Consolidation","seeds":[1,7,19],"sizes":[24,72,216],"raw":raw,"summary":summarize(raw),"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"estimated_complexity":"learn O(NPG), write O(PG), read O(MG)","learner_hidden_labels":False,"free_japanese_integrated_gate":0.0,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(args.output,"w",encoding="utf-8") as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload["summary"]["216"],ensure_ascii=False,indent=2))
if __name__=="__main__": main()
