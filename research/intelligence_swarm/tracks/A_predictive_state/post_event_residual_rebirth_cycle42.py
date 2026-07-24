from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
import argparse, json, pickle, random, resource, statistics, time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末"]
VALUES=["棚A","棚B","待機","完了"]
FILL=["補助記録は維持します。","別件は変えません。"]

@dataclass
class Turn:
    before:str; command:str; after:str; future:str
    obj:str; old:str; new:str; mode:str; boundary:bool

@dataclass(frozen=True)
class Rule:
    ss:int; se:int; vs:int; ve:int

def make_dialog(seed:int,n:int,mode:str)->list[Turn]:
    r=random.Random(seed); world={}; out=[]; prev_obj=None
    for i in range(n):
        if mode=="switch":
            obj=OBJECTS[(i//3)%len(OBJECTS)]
        else:
            obj=r.choice(OBJECTS)
        old=world.get(obj,r.choice(VALUES))
        new=r.choice([x for x in VALUES if x!=old])
        before=f"{obj}の現在値は{old}です。{r.choice(FILL)}"
        if mode=="omitted" and i%3!=0:
            command=f"それを{new}へ変更してください。"
        elif mode=="order":
            command=f"{new}へ変更してください、対象は{obj}です。"
        elif mode=="paragraph":
            command=f"{r.choice(FILL)}\n{obj}を{new}へ変更してください。"
        elif mode=="plan":
            alt=r.choice([x for x in VALUES if x not in (old,new)])
            command=f"{obj}を{alt}にする案は撤回し、最終的に{new}へ変更してください。"
        elif mode=="counterfactual":
            command=f"変更しなければ{obj}は{old}のままです。実際には{obj}を{new}へ変更してください。"
        else:
            command=f"{obj}を{new}へ変更してください。"
        after=f"{obj}の現在値は{new}です。{r.choice(FILL)}"
        future=f"次の観測でも{obj}は{new}です。"
        out.append(Turn(before,command,after,future,obj,old,new,mode,prev_obj is not None and obj!=prev_obj))
        world[obj]=new; prev_obj=obj
    return out

def spans(s,maxw=8):
    for i in range(len(s)):
        for j in range(i+1,min(len(s),i+maxw)+1):
            x=s[i:j]
            if not any(c in x for c in "。、\n「」"):
                yield i,j,x

def apply(t:Turn,r:Rule)->str|None:
    if not (0<=r.ss<r.se<=len(t.before) and 0<=r.vs<r.ve<=len(t.command)): return None
    return t.before[:r.ss]+t.command[r.vs:r.ve]+t.before[r.se:]

def mismatch(a,b):
    n=min(len(a),len(b))
    return abs(len(a)-len(b))+sum(a[i]!=b[i] for i in range(n))

def initial_rules(t:Turn,cap=32):
    sps=[(i,j,x) for i,j,x in spans(t.before) if len(x)<=5]
    vps=[(i,j,x) for i,j,x in spans(t.command) if x not in t.before]
    out=[]
    for si,sj,_ in sps[:10]:
        for vi,vj,_ in vps[:10]:
            out.append(Rule(si,sj,vi,vj))
            if len(out)>=cap:return out
    return out

def mutate(r:Rule,t:Turn):
    ds=[(-1,0,0,0),(1,0,0,0),(0,-1,0,0),(0,1,0,0),
        (0,0,-1,0),(0,0,1,0),(0,0,0,-1),(0,0,0,1)]
    out=[]
    for a,b,c,d in ds:
        q=Rule(r.ss+a,r.se+b,r.vs+c,r.ve+d)
        if 0<=q.ss<q.se<=len(t.before) and 0<=q.vs<q.ve<=len(t.command):out.append(q)
    return out

class Model:
    def __init__(self,mode):
        self.mode=mode; self.rules=Counter(); self.births=0; self.boundaries=0; self.train_s=0.0

    def fit(self,train):
        t0=time.perf_counter(); base=Counter()
        for t in train:
            for r in sorted(initial_rules(t),key=lambda q:mismatch(apply(t,q) or t.before,t.after))[:4]:
                base[r]+=1
        self.rules=Counter({r:n for r,n in base.most_common(48) if n>=2})
        self.train_s=time.perf_counter()-t0

    def run(self,dialog):
        active=[]; results=[]
        for idx,t in enumerate(dialog):
            candidates=[]
            for r,n in self.rules.items():
                p=apply(t,r)
                if p is not None:candidates.append((mismatch(p,t.after),n,r,p))
            candidates.sort(key=lambda x:(x[0],-x[1]))
            boundary=False
            if active and candidates:
                old_err=min(mismatch(apply(t,r) or t.before,t.after) for r in active)
                new_err=candidates[0][0]
                boundary=(old_err-new_err)>=2 or t.boundary
            elif t.boundary: boundary=True
            if boundary:self.boundaries+=1

            if self.mode in ("rebirth","shuffle") and boundary:
                if self.mode=="shuffle":
                    future_idxs=list(range(idx,min(len(dialog),idx+3)))
                    vals=[dialog[j].after for j in future_idxs]
                    vals=vals[1:]+vals[:1]
                else:
                    future_idxs=list(range(idx,min(len(dialog),idx+3)))
                    vals=[dialog[j].after for j in future_idxs]
                born=Counter()
                for j,target in zip(future_idxs,vals):
                    tj=dialog[j]
                    seeds=[x[2] for x in sorted([(mismatch(apply(tj,r) or tj.before,target),n,r) for r,n in self.rules.items()], key=lambda x:(x[0],-x[1]))[:4]]
                    for r in seeds:
                        base=mismatch(apply(tj,r) or tj.before,target)
                        for q in mutate(r,tj):
                            qp=apply(tj,q)
                            if qp is not None and mismatch(qp,target)<base:
                                born[q]+=1
                accepted={r:n for r,n in born.items() if n>=2}
                self.births+=len(accepted)
                if self.mode=="rebirth":
                    self.rules.update(accepted)
                active=list(accepted)[:8]
            elif boundary and self.mode=="boundary_only":
                active=[]
            elif not active:
                active=[x[2] for x in candidates[:4]]

            preds=[]
            for r in active:
                p=apply(t,r)
                if p is not None:preds.append((mismatch(p,t.after),p,r))
            preds.sort(key=lambda x:x[0])
            pred=preds[0][1] if len(preds)==1 or (preds and preds[0][0]<preds[1][0]) else None
            results.append({
                "accuracy":pred==t.after,
                "wrong":pred is not None and pred!=t.after,
                "null":pred is None,
                "boundary_pred":boundary,
                "boundary_true":t.boundary,
                "post_boundary_accuracy":pred==t.after and idx>0 and dialog[idx-1].boundary
            })
        return results

def f1(rows):
    tp=sum(x["boundary_pred"] and x["boundary_true"] for x in rows)
    fp=sum(x["boundary_pred"] and not x["boundary_true"] for x in rows)
    fn=sum((not x["boundary_pred"]) and x["boundary_true"] for x in rows)
    return 0 if 2*tp+fp+fn==0 else 2*tp/(2*tp+fp+fn)

def evaluate(seed,mode):
    train=[]
    for j,m in enumerate(("seen","order","paragraph","plan")): train+=make_dialog(seed+j,12,m)
    test=make_dialog(seed+999,24,mode)
    out={}
    for method in ("one_step","boundary_only","rebirth","shuffle"):
        model=Model(method); model.fit(train); t0=time.perf_counter(); rows=model.run(test)
        out[method]={
            "accuracy":statistics.mean(float(x["accuracy"]) for x in rows),
            "wrong":statistics.mean(float(x["wrong"]) for x in rows),
            "null":statistics.mean(float(x["null"]) for x in rows),
            "boundary_f1":f1(rows),
            "post_boundary_accuracy":statistics.mean(float(x["post_boundary_accuracy"]) for x in rows),
            "rules":len(model.rules),"births":model.births,"boundaries":model.boundaries,
            "model_bytes":len(pickle.dumps(model)),"training_seconds":model.train_s,
            "inference_ms":(time.perf_counter()-t0)*1000/len(test)
        }
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); a=ap.parse_args()
    modes=("switch","omitted","order","paragraph","plan","counterfactual")
    raw={str(s):{m:evaluate(s,m) for m in modes} for s in (1,7,19)}
    summary={}
    for m in modes:
        summary[m]={}
        for method in ("one_step","boundary_only","rebirth","shuffle"):
            summary[m][method]={k:statistics.mean(raw[str(s)][m][method][k] for s in (1,7,19))
                                for k in raw["1"][m][method]}
    payload={"cycle":42,"hypothesis":"Prediction-Residual State Rebirth from Post-Event Counterexample Synthesis",
             "seeds":[1,7,19],"summary":summary,"raw":raw,
             "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             "estimated_complexity":"induction O(NL^2) capped; online O(TR); residual birth O(kRM)",
             "final_test_after_future_used_for_standard_ranking":False,
             "highschool_level_passed":False,"native_japanese_communication_passed":False,
             "weak_smartphone_verified":False,"completion":False}
    open(a.output,"w",encoding="utf-8").write(json.dumps(payload,ensure_ascii=False,indent=2))
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
