"""Track A Cycle 013: survival-calibrated active probe programs.

Controlled falsification probe. Learner input is raw Japanese text plus generic
binary probe outcomes. Hidden target span is evaluator-only. No morphology,
ontology, dictionaries, RAG, external LLM, or Transformer attention is used.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
import argparse,json,math,pickle,random,resource,statistics,time,re

SEEN=["{a}について確認します。{x}を優先し、{y}は保留してください。","{a}の件です。今回は{x}を採用し、{y}には触れません。"]
PARA=["{a}を見直しました。先に進めるのは{x}で、{y}は後回しです。","{a}について、実行対象を{x}へ切り替え、{y}は据え置きます。"]
NESTED=["{a}の方針です。「{y}ではなく『{x}を先に』という案」を採用します。","{a}について（{y}を止めて、内側の「{x}」だけ進める）とします。"]
OMITTED=["{a}の件です。それを先に進め、もう一方は保留してください。","{a}について、前者を採用して後者は待機にします。"]
DISTRACT=["天気は晴れです","別件の資料があります","会議は午後です","雑談を続けます"]
WORDS=["北側案","南側案","高速案","安全案","試料甲","試料乙","処理A","処理B","棚A","棚B"]

def spans(text,cap=24):
    out=set()
    for m in re.finditer(r"[「『（(]?([^。、「」『』（）()]{2,14})[」』）)]?",text):
        s=m.group(1).strip()
        if 2<=len(s)<=14: out.add(s)
    chars="".join(text.split())
    for n in (2,3,4,5,6):
        for i in range(0,max(0,len(chars)-n+1),max(1,n//2)):
            z=chars[i:i+n]
            if not any(c in "。、" for c in z): out.add(z)
    return sorted(out,key=lambda z:(-len(set(z))/len(z),len(z)))[:cap]

PROBE_TYPES=("delete","swap_left","swap_right","reverse")
def signature(candidate,probe):
    h=sum((i+1)*ord(c) for i,c in enumerate(candidate))
    if probe=="delete": return (h%5)<2
    if probe=="swap_left": return ((h//3)%7)<3
    if probe=="swap_right": return ((h//5)%7)<3
    return (h%2)==0

@dataclass
class Example:
    text:str
    target:str|None
    mode:str

def make(seed,n,mode):
    rng=random.Random(seed); forms={"seen":SEEN,"paraphrase":PARA,"nested":NESTED,"omitted":OMITTED}; out=[]
    for i in range(n):
        a=f"案件{i%17}"; x,y=rng.sample(WORDS,2)
        if mode=="outset":
            text=rng.choice(PARA).format(a=a,x=x,y=y)+" "+rng.choice(DISTRACT); target="存在しない候補"
        else:
            text=rng.choice(forms[mode]).format(a=a,x=x,y=y)
            if rng.random()<0.45: text+=" "+rng.choice(DISTRACT)
            target=x
        out.append(Example(text,target,mode))
    return out

class Policy:
    def __init__(self,kind):
        self.kind=kind; self.stats={p:Counter() for p in PROBE_TYPES}; self.null_threshold=0.55
    def fit(self,examples):
        for ex in examples:
            cs=spans(ex.text); truth=[c==ex.target for c in cs]
            if not any(truth): continue
            for p in PROBE_TYPES:
                outcome=signature(ex.target,p); survivors=[signature(c,p)==outcome for c in cs]
                self.stats[p]["correct_survive"]+=int(any(t and s for t,s in zip(truth,survivors)))
                self.stats[p]["trials"]+=1
                self.stats[p]["false_removed"]+=sum((not t) and (not s) for t,s in zip(truth,survivors))
                self.stats[p]["false_total"]+=sum(not t for t in truth)
    def utility(self,p,current):
        st=self.stats[p]
        if self.kind=="entropy":
            yes=sum(signature(c,p) for c in current); return yes*(len(current)-yes)
        surv=(st["correct_survive"]+1)/(st["trials"]+2)
        elim=(st["false_removed"]+1)/(st["false_total"]+2)
        yes=sum(signature(c,p) for c in current); balance=yes*(len(current)-yes)/max(1,len(current)**2)
        return 2.2*surv+0.8*elim+0.3*balance
    def solve(self,ex,max_probes=4):
        cs=spans(ex.text); initial=len(cs)
        if not cs: return None,0,0,0
        current=list(cs); used=[]
        for _ in range(max_probes):
            if len(current)<=1: break
            remaining=[p for p in PROBE_TYPES if p not in used]
            if not remaining: break
            p=max(remaining,key=lambda q:self.utility(q,current)); used.append(p)
            outcome=(len(used)%2)==0 if ex.target not in cs else signature(ex.target,p)
            current=[c for c in current if signature(c,p)==outcome]
            if not current: break
        pred=current[0] if len(current)==1 else None
        if self.kind=="survival_null":
            survival_ratio=len(current)/max(1,initial)
            if pred is None or survival_ratio<0.03: return None,len(used),initial,1
            agreement=max((self.stats[p]["correct_survive"]+1)/(self.stats[p]["trials"]+2) for p in used) if used else 0
            if agreement<self.null_threshold: return None,len(used),initial,1
        return pred,len(used),initial,0

def evaluate(seed,train_n,test_n):
    train=make(seed,train_n,"seen")+make(seed+1,train_n//2,"paraphrase")
    methods={k:Policy(k) for k in ("entropy","survival","survival_null")}
    for m in methods.values(): m.fit(train)
    out={}
    for mode in ("seen","paraphrase","nested","omitted","outset"):
        tests=make(seed+100+len(mode),test_n,mode); out[mode]={}
        for name,m in methods.items():
            correct=wrong=null=probes=recall=cands=0; st=time.perf_counter()
            for ex in tests:
                cs=spans(ex.text); recall+=int(ex.target in cs); cands+=len(cs)
                pred,p,_,n=m.solve(ex); probes+=p; null+=n
                correct+=int(pred==ex.target); wrong+=int(pred is not None and pred!=ex.target)
            out[mode][name]={"accuracy":correct/len(tests),"wrong_commit":wrong/len(tests),"null_rate":null/len(tests),"candidate_recall":recall/len(tests),"mean_candidates":cands/len(tests),"mean_probes":probes/len(tests),"ms_per_example":(time.perf_counter()-st)*1000/len(tests),"model_bytes":len(pickle.dumps(m))}
    return out

def summarize(raw):
    out={}
    for n,runs in raw.items():
        out[n]={}
        for mode in ("seen","paraphrase","nested","omitted","outset"):
            out[n][mode]={}
            for method in ("entropy","survival","survival_null"):
                out[n][mode][method]={k:statistics.mean(r[mode][method][k] for r in runs) for k in runs[0][mode][method]}
        out[n]["policy_stats"]=runs[0]["policy_stats"]
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="results_cycle_013.json"); args=ap.parse_args(); raw={}
    for n in (64,256,1024):
        runs=[]
        for seed in (1,7,19):
            r=evaluate(seed,n,180); p=Policy("survival"); p.fit(make(seed,n,"seen")+make(seed+1,n//2,"paraphrase")); r["policy_stats"]={k:dict(v) for k,v in p.stats.items()}; runs.append(r)
        raw[str(n)]=runs
    payload={"hypothesis":"Survival-Calibrated Active Probe Programs with Coverage-Constrained Null States","seeds":[1,7,19],"train_sizes":[64,256,1024],"raw":raw,"summary":summarize(raw),"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"estimated_complexity":"proposal O(L^2), active O(PH), H<=24, P<=4","learner_hidden_target_access":False,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(args.output,"w",encoding="utf-8") as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload["summary"]["1024"],ensure_ascii=False,indent=2))
if __name__=="__main__": main()
