from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse, json, pickle, random, resource, statistics, time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末",
         "大型端末":"大きい端末","北側の鍵":"北のキー","南側の鍵":"南のキー"}
VALUES=["棚A","棚B","棚C","棚D","待機","処理中","完了","保留"]
FILL=["補助記録は維持します。","別件の設定は変えません。","前段の注意事項はそのままです。"]

@dataclass
class Turn:
    before:str; command:str; after:str; future:str
    obj:str; canon:str; old:str; new:str; mode:str

@dataclass(frozen=True)
class Cell:
    sb:int; sw:int
    vb:int; vw:int
    ob:int; ow:int
    oldshape:str; newshape:str; objshape:str

def shape(s):
    return "".join("A" if c.isascii() and c.isalnum() else
                   "J" if c not in "。、：／=\n 「」" else c for c in s)

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

def spans(text,lo=1,hi=12):
    return [(i,j,text[i:j]) for i in range(len(text))
            for j in range(i+lo,min(len(text),i+hi)+1)
            if not any(c in text[i:j] for c in "。、\n「」")]

def make(seed,n,mode):
    rng=random.Random(seed); world={}; focus=None; rows=[]
    for i in range(n):
        continuation=mode in ("omitted","switchmix") and i>0 and (mode=="omitted" or i%2==1)
        canon=focus if continuation else rng.choice(OBJECTS)
        obj=ALIASES[canon] if mode=="rename" else canon
        old=world.get(canon,rng.choice(VALUES))
        new=rng.choice([v for v in VALUES if v!=old])
        before=f"{obj}の現在値は{old}です。{rng.choice(FILL)}"
        if mode=="omitted" and i>0:
            cmd=f"それを{new}へ変更してください。"
        elif mode=="switchmix" and i>0 and i%2:
            cmd=f"その対象を{new}へ変更してください。"
        elif mode=="order":
            cmd=f"{new}へ変更してください、対象は{obj}です。"
        elif mode=="lexeme":
            cmd=f"対象{obj}は次から{new}扱いにします。"
        elif mode=="nested":
            cmd=f"依頼内容は「{obj}を{new}へ変更してください。」です。"
        elif mode=="paragraph":
            cmd=f"{rng.choice(FILL)}\n{obj}を{new}へ変更してください。\n{rng.choice(FILL)}"
        elif mode=="plan":
            alt=rng.choice([v for v in VALUES if v not in (old,new)])
            cmd=f"{obj}を{alt}にする案は撤回し、最終的には{new}へ変更してください。"
        elif mode=="counterfactual":
            cmd=f"もし変更しなければ{obj}は{old}のままです。実際には{obj}を{new}へ変更してください。"
        else:
            cmd=f"{obj}を{new}へ変更してください。"
        after=f"{obj}の現在値は{new}です。{rng.choice(FILL)}"
        future=f"次の観測でも{obj}は{new}のままです。"
        rows.append(Turn(before,cmd,after,future,obj,canon,old,new,mode))
        world[canon]=new; focus=canon
    return rows

def locate(text, token):
    p=text.find(token)
    return None if p<0 else (p,len(token))

def bucket(pos,length):
    return round(12*pos/max(1,length))

def unbucket(b,length):
    return max(0,min(length,round(b*length/12)))

def apply(before,value,cell):
    s=unbucket(cell.sb,len(before)); e=min(len(before),s+cell.sw)
    if shape(before[s:e])!=cell.oldshape: return None
    return before[:s]+value+before[e:]

def extract_joint(turn):
    l,r,old,new=diff(turn.before,turn.after)
    vp=locate(turn.command,new)
    op=locate(turn.command,turn.obj)
    if not old or vp is None or op is None: return None
    return Cell(bucket(l,len(turn.before)),len(old),
                bucket(vp[0],len(turn.command)),vp[1],
                bucket(op[0],len(turn.command)),op[1],
                shape(old),shape(new),shape(turn.obj))

def command_value(turn,cell):
    s=unbucket(cell.vb,len(turn.command)); e=min(len(turn.command),s+cell.vw)
    x=turn.command[s:e]
    return x if shape(x)==cell.newshape else None

def command_object(turn,cell):
    s=unbucket(cell.ob,len(turn.command)); e=min(len(turn.command),s+cell.ow)
    x=turn.command[s:e]
    return x if shape(x)==cell.objshape else None

def synthetic_target(turn,value):
    l,r,old,new=diff(turn.before,turn.after)
    if not old: return None
    return turn.before[:l]+value+turn.before[len(turn.before)-r if r else len(turn.before):]

class Model:
    def __init__(self,mode):
        self.mode=mode
        self.cells=[]
        self.reactivation=Counter()
        self.swap_support=Counter()
        self.audit=0
        self.births=0
        self.train_s=0.0

    def fit(self,induction,probe):
        t0=time.perf_counter()
        raw=Counter(c for t in induction if (c:=extract_joint(t)) is not None)
        cells=[c for c,n in raw.most_common(48) if n>=2]
        if self.mode=="factorized":
            self.cells=cells
            self.train_s=time.perf_counter()-t0
            return

        targets=[t.after for t in probe]
        if self.mode=="shuffle":
            targets=targets[1:]+targets[:1]

        kept=[]
        for c in cells:
            base_ok=base_wrong=swap_ok=swap_wrong=react=0
            prior_by_canon={}
            for idx,(t,target) in enumerate(zip(probe,targets)):
                v=command_value(t,c); o=command_object(t,c)
                if v is None or o is None: continue
                pred=apply(t.before,v,c); self.audit+=1
                if pred==target: base_ok+=1
                elif pred is not None: base_wrong+=1

                donor=probe[(idx+1)%len(probe)]
                dv=donor.new
                swapped=synthetic_target(t,dv)
                sp=apply(t.before,dv,c); self.audit+=1
                if sp==swapped: swap_ok+=1
                elif sp is not None: swap_wrong+=1

                if t.canon in prior_by_canon and pred==target:
                    react+=1
                prior_by_canon[t.canon]=idx

            self.swap_support[c]=swap_ok-swap_wrong
            self.reactivation[c]=react
            if self.mode=="joint":
                if base_ok>=2 and base_ok>base_wrong and swap_ok>=2 and swap_ok>swap_wrong:
                    kept.append(c)
            elif self.mode=="state_only":
                if base_ok>=2 and base_ok>base_wrong:
                    kept.append(c)
            elif self.mode=="shuffle":
                if base_ok>=2 and base_ok>base_wrong and swap_ok>=2 and swap_ok>swap_wrong:
                    kept.append(c)

        self.cells=kept[:48]
        self.births=max(0,len(self.cells)-len([c for c,n in raw.items() if n>=3]))
        self.train_s=time.perf_counter()-t0

    def predict(self,turn,prev=None):
        props=[]
        for c in self.cells:
            v=command_value(turn,c)
            o=command_object(turn,c)
            if v is None: continue
            pred=apply(turn.before,v,c)
            if pred is None: continue
            score=1.0
            if o is not None: score+=0.5
            if self.mode in ("joint","shuffle"):
                score+=0.15*self.swap_support.get(c,0)+0.1*self.reactivation.get(c,0)
            if prev is not None and prev.canon==turn.canon:
                score+=0.2*self.reactivation.get(c,0)
            props.append((score,pred,o or "",v,c))
        if not props: return None,0,0
        props.sort(key=lambda x:x[0],reverse=True)
        best=props[0][0]
        active=[x for x in props if x[0]>=best-0.1][:16]
        if len(active)>1 and active[0][0]-active[1][0]<0.25:
            return None,2,len(active)
        return active[0],2,len(active)

def evaluate(seed,mode):
    train=[]
    for j,m in enumerate(("seen","rename","paragraph","switchmix","plan")):
        train += make(seed+j,30,m)
    cut=int(.7*len(train)); induction,probe=train[:cut],train[cut:]
    test=make(seed+999,24,mode)
    out={}
    for method in ("factorized","state_only","joint","shuffle"):
        model=Model(method); model.fit(induction,probe)
        rows=[]; t0=time.perf_counter()
        for i,t in enumerate(test):
            p,sw,a=model.predict(t,test[i-1] if i else None)
            rows.append({
                "accuracy":p is not None and p[1]==t.after,
                "wrong":p is not None and p[1]!=t.after,
                "null":p is None,
                "pair":p is not None and p[2]==t.obj and p[3]==t.new,
                "reactivated":p is not None and i>0 and test[i-1].canon==t.canon,
                "wrong_carry":p is not None and i>0 and test[i-1].canon!=t.canon,
                "sweeps":sw,"active":a
            })
        out[method]={
            "accuracy":statistics.mean(float(x["accuracy"]) for x in rows),
            "wrong":statistics.mean(float(x["wrong"]) for x in rows),
            "null":statistics.mean(float(x["null"]) for x in rows),
            "pair_recall":statistics.mean(float(x["pair"]) for x in rows),
            "reactivation_rate":statistics.mean(float(x["reactivated"]) for x in rows),
            "wrong_carry":statistics.mean(float(x["wrong_carry"]) for x in rows),
            "mean_sweeps":statistics.mean(x["sweeps"] for x in rows),
            "mean_active":statistics.mean(x["active"] for x in rows),
            "cells":len(model.cells),
            "reactivation_edges":sum(1 for v in model.reactivation.values() if v>0),
            "swap_supported_cells":sum(1 for v in model.swap_support.values() if v>0),
            "probe_audits":model.audit,
            "births":model.births,
            "model_bytes":len(pickle.dumps(model)),
            "training_seconds":model.train_s,
            "inference_ms":(time.perf_counter()-t0)*1000/len(test)
        }
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",default="MEASUREMENTS_CYCLE_035.json")
    args=ap.parse_args()
    modes=("seen","order","lexeme","rename","nested","omitted","switchmix","paragraph","plan","counterfactual")
    raw={str(seed):{mode:evaluate(seed,mode) for mode in modes} for seed in (1,7,19)}
    summary={}
    for mode in modes:
        summary[mode]={}
        for method in ("factorized","state_only","joint","shuffle"):
            summary[mode][method]={k:statistics.mean(raw[str(seed)][mode][method][k] for seed in (1,7,19))
                                   for k in raw["1"][mode][method]}
    payload={
        "cycle":35,
        "hypothesis":"Joint-Born Command-State Transition Cells from Cross-Turn Contrastive Swaps",
        "seeds":[1,7,19],
        "summary":summary,
        "raw":raw,
        "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "estimated_complexity":"induction O(NL), contrastive probe O(QC), inference O(C)",
        "final_test_outcome_used_for_ranking":False,
        "fixed_ontology_or_handwritten_slots_used_by_model":False,
        "highschool_level_passed":False,
        "native_japanese_communication_passed":False,
        "weak_smartphone_verified":False,
        "completion":False
    }
    with open(args.output,"w",encoding="utf-8") as f:
        json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
