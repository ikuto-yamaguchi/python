"""Track E Cycle 009: Outcome-vector factor sufficiency probe.

No pretrained model, RAG, morphology, semantic slot dictionary, or fixed ontology.
Candidate graphs are generated from generic quoted spans and sentence boundaries.
This is a controlled factor-sufficiency probe, not evidence of free Japanese parsing.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
import argparse, json, math, pickle, random, resource, statistics, time

REV_TRAIN = ["訂正して", "やはり", "変更します", "先ほどの指示を取り消し"]
REV_HELD = ["考え直して", "前言を撤回し", "予定を改め", "最初の案はなしで"]
REV_UNKNOWN = ["翻意し", "既述を廃して", "方針転換により"]
ENTITIES = ["箱甲","箱乙","端末A","端末B","試料一","試料二"]
VALUES = ["棚A","棚B","棚C","棚D","室内","廊下","保留","完了"]

def grams(text):
    s="".join(text.split())
    return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))

def cosine(a,b):
    dot=sum(v*b.get(k,0) for k,v in a.items())
    na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return dot/(na*nb+1e-12)

def split_sentences(text):
    out=[]; cur=""
    for ch in text:
        cur+=ch
        if ch in "。！？\n":
            if cur.strip(): out.append(cur.strip())
            cur=""
    if cur.strip(): out.append(cur.strip())
    return out

def quoted(text):
    out=[]; start=None
    for i,ch in enumerate(text):
        if ch=="「": start=i+1
        elif ch=="」" and start is not None:
            out.append(text[start:i]); start=None
    return out

@dataclass(frozen=True)
class Candidate:
    command_index:int
    target:str
    dest:str
    branch:str
    feature:tuple

def build_example(rng, mode):
    e1,e2=rng.sample(ENTITIES,2)
    v0,v_other,v1,v2=rng.sample(VALUES,4)
    if mode=="seen":
        rev=rng.choice(REV_TRAIN); mode="plan_change"
    elif mode=="held":
        rev=rng.choice(REV_HELD); mode="plan_change"
    elif mode=="unknown":
        rev=rng.choice(REV_UNKNOWN); mode="plan_change"
    else:
        rev=""
    initial=f"「{e1}」は「{v0}」にあり、「{e2}」は「{v_other}」にある。"
    cmd1=f"まず「{e1}」を「{v1}」へ移す。"
    if mode=="no_revision":
        text=initial+cmd1
        chosen=0; final={e1:v1,e2:v_other}
    elif mode=="nested":
        text=initial+f"「{e1}」を「{v1}」へ移す案を検討したが、{rev}、条件が変わらなければ「{e1}」を「{v2}」へ移す。"
        chosen=1; final={e1:v2,e2:v_other}
    elif mode=="multi":
        text=initial+"\n"+cmd1+"\n"+f"{rev}、「{e1}」を「{v2}」へ移す。"
        chosen=1; final={e1:v2,e2:v_other}
    elif mode=="plan_change":
        text=initial+cmd1+f"{rev}、「{e1}」を「{v2}」へ移す。"
        chosen=1; final={e1:v2,e2:v_other}
    elif mode=="counterfactual":
        text=initial+cmd1+f"{rev}、「{e1}」を「{v2}」へ移す。もし訂正がなければ「{e1}」は「{v1}」だった。"
        chosen=1; final={e1:v2,e2:v_other}
    elif mode=="unmarked":
        text=f"{e1}は{v0}にあり、{e2}は{v_other}にある。まず{e1}を{v1}へ移す。{rev}、{e1}を{v2}へ移す。"
        chosen=1; final={e1:v2,e2:v_other}
    else:
        raise ValueError(mode)
    return {"text":text,"initial":{e1:v0,e2:v_other},"final":final,"target":e1,"chosen":chosen,
            "v1":v1,"v2":v2}

def propose(ex):
    sents=split_sentences(ex["text"])
    ops=[]
    for i,s in enumerate(sents):
        q=quoted(s)
        if len(q)>=2:
            for a in range(len(q)):
                for b in range(len(q)):
                    if a!=b:
                        ops.append((i,s,q[a],q[b]))
    cands=[]
    revg=grams(" ".join(REV_TRAIN))
    for oi,(si,s,t,d) in enumerate(ops):
        for branch in ("action","noop"):
            position=(si+1)/max(1,len(sents))
            revsim=cosine(grams(s),revg)
            changes=float(branch=="action" and ex["initial"].get(t)!=d)
            inverse=float(t in ex["initial"])
            non_target=float(t in ex["initial"])
            removal_impact=changes
            compose=float(branch=="action")
            feat=(1.0,position,revsim,changes,inverse,non_target,removal_impact,compose)
            cands.append(Candidate(oi,t,d,branch,feat))
    return cands[:32]

def execute(ex,c):
    world=dict(ex["initial"])
    if c.branch=="action" and c.target in world:
        world[c.target]=c.dest
    return world

def outcome_vector(ex,c):
    world=execute(ex,c)
    inverse_ok=float(c.target in ex["initial"] and ({**world,c.target:ex["initial"][c.target]}==ex["initial"]))
    non_target_ok=float(all(world.get(k)==v for k,v in ex["initial"].items() if k!=c.target))
    final_match=sum(world.get(k)==v for k,v in ex["final"].items())/max(1,len(ex["final"]))
    recall_match=float(world.get(ex["target"])==ex["final"].get(ex["target"]))
    removal_effect=float(c.branch=="action" and c.target==ex["target"] and c.dest==ex["final"].get(ex["target"]))
    return (final_match,inverse_ok,non_target_ok,removal_effect,recall_match)

class Attractor:
    def __init__(self,use_outcome):
        self.use_outcome=use_outcome
        self.w=[0.0]*8
        self.w[1]=0.05; self.w[2]=0.05
    def score(self,c):
        return sum(a*b for a,b in zip(self.w,c.feature))
    def fit(self,examples,epochs=2):
        for _ in range(epochs):
            for ex in examples:
                cs=propose(ex)
                if not cs: continue
                free=max(cs,key=self.score)
                if self.use_outcome:
                    nudged=max(cs,key=lambda c:(sum(outcome_vector(ex,c)),self.score(c)))
                else:
                    nudged=max(cs,key=lambda c:(outcome_vector(ex,c)[0],self.score(c)))
                if free!=nudged:
                    for i,(a,b) in enumerate(zip(nudged.feature,free.feature)):
                        self.w[i]+=0.08*(a-b)
        return self
    def infer(self,ex,max_sweeps=4):
        cs=propose(ex)
        if not cs:return None,0,0.0,0
        active=cs
        prev=None
        sweeps=0
        for sweeps in range(1,max_sweeps+1):
            ranked=sorted(active,key=self.score,reverse=True)
            sig=(ranked[0].target,ranked[0].dest,ranked[0].branch,ranked[0].command_index)
            if sig==prev:break
            prev=sig
            active=ranked[:max(2,len(ranked)//2)]
        ranked=sorted(cs,key=self.score,reverse=True)
        margin=self.score(ranked[0])-self.score(ranked[1]) if len(ranked)>1 else 1.0
        if margin<0.005:return None,sweeps,margin,len(cs)
        return ranked[0],sweeps,margin,len(cs)

def eval_run(seed,n):
    rng=random.Random(seed)
    train=[build_example(rng,rng.choice(["plan_change","multi","no_revision"])) for _ in range(n)]
    models={"final_only":Attractor(False).fit(train),"outcome_vector":Attractor(True).fit(train)}
    out={}
    for name,m in models.items():
        out[name]={"weights":m.w}
        for mode in ["seen","held","unknown","nested","multi","counterfactual","unmarked","no_revision"]:
            rows=[build_example(rng,mode) for _ in range(120)]
            ok=abst=sweeps=margin=active=recall=0
            st=time.perf_counter()
            for ex in rows:
                cs=propose(ex)
                recall += any(execute(ex,c)==ex["final"] for c in cs)
                pred,sw,ma,ac=m.infer(ex)
                sweeps+=sw;margin+=ma;active+=ac
                if pred is None:abst+=1
                else:ok+=execute(ex,pred)==ex["final"]
            ms=(time.perf_counter()-st)*1000/len(rows)
            out[name][mode]={"accuracy":ok/len(rows),"abstention":abst/len(rows),
                "candidate_recall":recall/len(rows),"sweeps":sweeps/len(rows),
                "margin":margin/len(rows),"active_candidates":active/len(rows),"ms":ms}
        out[name]["model_bytes"]=len(pickle.dumps(m))
    return out

def summarize(raw):
    out={}
    for n,runs in raw.items():
        out[n]={}
        for method in ("final_only","outcome_vector"):
            out[n][method]={}
            for mode in ["seen","held","unknown","nested","multi","counterfactual","unmarked","no_revision"]:
                out[n][method][mode]={k:statistics.mean(r[method][mode][k] for r in runs)
                    for k in runs[0][method][mode]}
            out[n][method]["model_bytes"]=statistics.mean(r[method]["model_bytes"] for r in runs)
            out[n][method]["weights"]=[statistics.mean(r[method]["weights"][i] for r in runs) for i in range(8)]
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="results_cycle_009.json")
    a=ap.parse_args()
    raw={str(n):[eval_run(s,n) for s in (1,7,19)] for n in (24,96,384)}
    payload={"hypothesis":"Outcome-Vector Factor Sufficiency with Revision-Causal Perturbations",
      "seeds":[1,7,19],"train_sizes":[24,96,384],"raw":raw,"summary":summarize(raw),
      "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "estimated_complexity":"proposal O(L^2), relaxation O(SH), H<=32, S<=4",
      "highschool_level_passed":False,"native_japanese_communication_passed":False,
      "weak_smartphone_verified":False,"completion":False}
    with open(a.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload["summary"]["384"],ensure_ascii=False,indent=2))
if __name__=="__main__":main()
