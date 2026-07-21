"""Track E Cycle 010: Edge-Intervention Jacobian Factors.

Controlled falsification probe for local credit routing in sparse attractor graphs.
No pretrained model, parser, ontology, semantic dictionary, RAG, or external LLM.

Quoted spans are used only for the controlled candidate-recall condition. An
unmarked-Japanese split explicitly tests and falsifies open-form proposal.
"""
from __future__ import annotations
import argparse, json, math, pickle, random, resource, statistics, time
from dataclasses import dataclass
from itertools import product

ENTITIES=["箱甲","箱乙","端末青","端末赤","試料一","試料二","台車北","台車南"]
VALUES=["棚A","棚B","棚C","棚D","室内","廊下","保留","完了"]
COMMANDS=["「{e}」を「{v}」へ移してください。",
          "「{v}」へ「{e}」を移動します。",
          "対象「{e}」の行き先を「{v}」へ変更してください。"]
REVISION=["最初は「{e}」を「{v1}」へ。訂正して「{v2}」へ移してください。",
          "「{e}」は「{v1}」ではなく、最終的に「{v2}」へ移します。"]
UNMARKED=["{e}を{v}へ移してください。","対象{e}の行き先を{v}へ変更してください。"]

@dataclass(frozen=True)
class Graph:
    target:int
    value:int
    scope:int
    revision:int

def quoted(text:str)->list[str]:
    out=[]; pos=0
    while True:
        a=text.find("「",pos)
        if a<0: break
        b=text.find("」",a+1)
        if b<0: break
        out.append(text[a+1:b]); pos=b+1
    return out

def propose(text:str,max_candidates=32):
    spans=quoted(text)
    if len(spans)<2:
        return []
    cands=[]
    for t,v,s,r in product(range(len(spans)),range(len(spans)),(0,1),(0,1)):
        if t==v: continue
        cands.append(Graph(t,v,s,r))
        if len(cands)>=max_candidates: break
    return cands

def execute(g:Graph, spans:list[str], revision_case:bool):
    target=spans[g.target] if g.target<len(spans) else "?"
    value=spans[g.value] if g.value<len(spans) else "?"
    active_revision = int(revision_case and g.revision==1 and g.scope==1)
    final=(target,value,active_revision)
    inverse=(target,"RESTORED",active_revision)
    non_target=("OTHER","UNCHANGED",1)
    remove_first=(target,value,int(g.scope==1))
    remove_last=(target,value,int(g.scope==0))
    recall=(target,value)
    return (final,inverse,non_target,remove_first,remove_last,recall)

def edge_jacobian(g:Graph, spans:list[str], revision_case:bool):
    base=execute(g,spans,revision_case)
    variants=[]
    fields=("target","value","scope","revision")
    for field in fields:
        if field=="target":
            alt=Graph((g.target+1)%len(spans),g.value,g.scope,g.revision)
        elif field=="value":
            alt=Graph(g.target,(g.value+1)%len(spans),g.scope,g.revision)
        elif field=="scope":
            alt=Graph(g.target,g.value,1-g.scope,g.revision)
        else:
            alt=Graph(g.target,g.value,g.scope,1-g.revision)
        changed=execute(alt,spans,revision_case)
        variants.append(tuple(int(a!=b) for a,b in zip(base,changed)))
    return tuple(variants)

def mismatch(a,b):
    return sum(x!=y for x,y in zip(a,b))

def energy(g,spans,revision_case,observed,observed_jac,mode):
    out=execute(g,spans,revision_case)
    if mode=="final":
        return mismatch(out[:1],observed[:1])
    if mode=="outcome":
        return mismatch(out,observed)
    jac=edge_jacobian(g,spans,revision_case)
    e=mismatch(out,observed)
    for cj,oj in zip(jac,observed_jac):
        e += sum(abs(x-y) for x,y in zip(cj,oj))
    return e

def hypothesis_signature(g,spans,revision_case,mode):
    out=execute(g,spans,revision_case)
    if mode=="final":
        return out[:1]
    if mode=="outcome":
        return out
    return (out,edge_jacobian(g,spans,revision_case))

def relax(cands,spans,revision_case,observed,observed_jac,mode,max_sweeps=4):
    classes={}
    for g in cands:
        classes.setdefault(hypothesis_signature(g,spans,revision_case,mode),g)
    active=list(classes.values()); prev=None
    for sweep in range(1,max_sweeps+1):
        scored=sorted(((energy(g,spans,revision_case,observed,observed_jac,mode),g)
                       for g in active), key=lambda x:x[0])
        best=scored[0][0]
        active=[g for e,g in scored if e<=best+1]
        state=tuple(hypothesis_signature(g,spans,revision_case,mode) for g in active)
        if state==prev or len(active)<=1:
            break
        prev=state
    final=sorted(((energy(g,spans,revision_case,observed,observed_jac,mode),g)
                  for g in active), key=lambda x:x[0])
    margin=(final[1][0]-final[0][0]) if len(final)>1 else 1.0
    pred=final[0][1] if margin>0 else None
    return pred,sweep,len(active),margin,len(classes)

def make_case(rng,kind):
    e=rng.choice(ENTITIES); vals=rng.sample(VALUES,2)
    if kind=="revision":
        text=rng.choice(REVISION).format(e=e,v1=vals[0],v2=vals[1])
        spans=quoted(text); correct=Graph(0,2,1,1)
        revision_case=True
    elif kind=="unmarked":
        text=rng.choice(UNMARKED).format(e=e,v=vals[1])
        spans=[]; correct=None; revision_case=False
    else:
        text=rng.choice(COMMANDS).format(e=e,v=vals[1])
        spans=quoted(text)
        correct=Graph(spans.index(e),spans.index(vals[1]),1,0)
        revision_case=False
    return text,spans,correct,revision_case

def evaluate(seed,n):
    rng=random.Random(seed)
    modes=("final","outcome","jacobian")
    splits=("seen","held_revision","nested","counterfactual","unmarked")
    result={m:{} for m in modes}
    for mode in modes:
        for split in splits:
            correct_n=abstain=sweeps=active=processed=classes_total=0; margins=[]; candidate_recall=0
            st=time.perf_counter()
            for _ in range(n):
                kind="revision" if split=="held_revision" else ("unmarked" if split=="unmarked" else "seen")
                text,spans,correct,revision_case=make_case(rng,kind)
                cands=propose(text)
                candidate_recall += int(correct in cands if correct is not None else False)
                if not cands or correct is None:
                    abstain+=1; continue
                observed=execute(correct,spans,revision_case)
                observed_jac=edge_jacobian(correct,spans,revision_case)
                pred,sw,act,margin,nclasses=relax(cands,spans,revision_case,observed,observed_jac,mode)
                processed+=1; sweeps+=sw; active+=act; classes_total+=nclasses; margins.append(margin)
                if pred is None: abstain+=1
                else:
                    output_ok = execute(pred,spans,revision_case)==observed
                    causal_ok = edge_jacobian(pred,spans,revision_case)==observed_jac
                    require_causal = split in ("held_revision","nested","counterfactual")
                    correct_n += int(output_ok and (causal_ok if require_causal else True))
            elapsed=(time.perf_counter()-st)*1000/n
            result[mode][split]={
                "accuracy":correct_n/n,
                "abstention":abstain/n,
                "candidate_recall":candidate_recall/n,
                "mean_sweeps":sweeps/max(1,processed),
                "mean_active":active/max(1,processed),
                "mean_hypothesis_classes":classes_total/max(1,processed),
                "mean_margin":statistics.mean(margins) if margins else 0.0,
                "ms_per_query":elapsed,
            }
    model={"edge_types":["target","value","scope","revision"],"max_candidates":32,"max_sweeps":4}
    result["model_bytes"]=len(pickle.dumps(model))
    return result

def summarize(raw):
    out={}
    for size,runs in raw.items():
        out[size]={}
        for mode in ("final","outcome","jacobian"):
            out[size][mode]={}
            for split in ("seen","held_revision","nested","counterfactual","unmarked"):
                keys=runs[0][mode][split]
                out[size][mode][split]={k:statistics.mean(r[mode][split][k] for r in runs) for k in keys}
        out[size]["model_bytes"]=statistics.mean(r["model_bytes"] for r in runs)
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="results_cycle_010.json")
    args=ap.parse_args()
    raw={str(n):[evaluate(seed,n) for seed in (1,7,19)] for n in (60,180,540)}
    payload={
      "hypothesis":"Edge-Intervention Jacobian Factors with Sparse Causal Credit Routing",
      "seeds":[1,7,19],"examples_per_split":[60,180,540],
      "raw":raw,"summary":summarize(raw),
      "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "estimated_complexity":"proposal O(L^2), Jacobian O(E*O), relaxation O(S*H*E*O); E=4,O=6,H<=32,S<=4",
      "free_japanese_integrated_gate":0.0,
      "highschool_level_passed":False,
      "native_japanese_communication_passed":False,
      "weak_smartphone_verified":False,
      "completion":False
    }
    with open(args.output,"w",encoding="utf-8") as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload["summary"]["540"],ensure_ascii=False,indent=2))
if __name__=="__main__": main()
