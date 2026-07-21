from __future__ import annotations
import argparse, json, pickle, random, resource, statistics, time
from pathlib import Path
from collections import defaultdict, Counter

ENTS=["装置A","装置B","箱α","箱β","部品甲","部品乙"]
VALS=["棚1","棚2","区画東","区画西","担当X","担当Y"]
SEEN=["{e}を{v}へ移動する","{v}へ{e}を移してください","{e}の行先を{v}に変える"]
HELD_ORDER=["最終的に{v}となるよう、対象の{e}を動かす"]
HELD_LEX=["{e}を{v}へ搬送せよ","{e}を{v}に収容する"]
NESTED=["安全確認後に、{e}を{v}へ移動する"]
OMIT=["それを{v}へ移してください"]
ALT_STATE=["{e}：現在地={v}"]

def state(e,v): return f"{e}の現在位置は{v}です。"
def effect(before,after):
    p=0
    while p<min(len(before),len(after)) and before[p]==after[p]: p+=1
    s=0
    while s<min(len(before)-p,len(after)-p) and before[-1-s]==after[-1-s]: s+=1
    return before[p:len(before)-s if s else len(before)], after[p:len(after)-s if s else len(after)], before[:p], before[len(before)-s:] if s else ""

def residue(cmd,before,after):
    old,new,_,_=effect(before,after)
    r=cmd
    for x in sorted({old,new},key=len,reverse=True):
        if x: r=r.replace(x,"<X>")
    return r

class Model:
    def __init__(self, execution_first=True):
        self.execution_first=execution_first
        self.programs=defaultdict(lambda: {"support":0,"surfaces":Counter()})
    def fit(self, rows):
        for b,c,a in rows:
            old,new,pre,suf=effect(b,a)
            if not old or not new: continue
            key=(pre,suf)
            executable=(b.replace(old,new,1)==a)
            if self.execution_first and not executable: continue
            self.programs[key]["support"]+=1
            self.programs[key]["surfaces"][residue(c,b,a)]+=1
        return self
    def predict(self,b,c):
        cand=[]
        for (pre,suf),meta in self.programs.items():
            if not (b.startswith(pre) and b.endswith(suf)): continue
            seen_new=set()
            for i in range(len(c)):
                for j in range(i+1,min(len(c),i+9)+1):
                    new=c[i:j]
                    if new in b or new in seen_new: continue
                    seen_new.add(new)
                    out=pre+new+suf
                    best_surface=max((count-abs(len(residue(c,b,out))-len(surf))*0.05 for surf,count in meta["surfaces"].items()), default=0)
                    cand.append(((best_surface,len(new)),out))
        if not cand: return None,0
        cand.sort(reverse=True)
        best=cand[0][0]
        outs={o for s,o in cand if s==best}
        return (next(iter(outs)),len(cand)) if len(outs)==1 else (None,len(cand))

def make(rng, n, forms):
    rows=[]
    for _ in range(n):
        e=rng.choice(ENTS); old,new=rng.sample(VALS,2); form=rng.choice(forms)
        rows.append((state(e,old),form.format(e=e,v=new),state(e,new)))
    return rows

def eval_one(seed,n):
    rng=random.Random(seed)
    train=make(rng,n,SEEN)
    models={"surface_mdl":Model(False).fit(train),"execution_first":Model(True).fit(train)}
    splits={"seen":make(rng,120,SEEN),"held_order":make(rng,120,HELD_ORDER),"held_lexeme":make(rng,120,HELD_LEX),"nested":make(rng,120,NESTED),"subject_omission":make(rng,120,OMIT),"alternate_state":make(rng,120,SEEN)}
    alt=[]
    for b,c,a in splits["alternate_state"]:
        e=next(x for x in ENTS if x in b); old=next(x for x in VALS if x in b); new=next(x for x in VALS if x in a)
        alt.append((ALT_STATE[0].format(e=e,v=old),c,ALT_STATE[0].format(e=e,v=new)))
    splits["alternate_state"]=alt
    out={}
    for name,m in models.items():
        mo={}
        for sn,rows in splits.items():
            t=time.perf_counter(); ok=reads=0
            for b,c,a in rows:
                p,r=m.predict(b,c); reads+=r; ok+=p==a
            mo[sn]={"accuracy":ok/len(rows),"ms":(time.perf_counter()-t)*1000/len(rows),"candidate_reads":reads/len(rows)}
        mo["model_bytes"]=len(pickle.dumps(dict(m.programs)))
        mo["programs"]=len(m.programs)
        out[name]=mo
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="results_cycle_009.json"); args=ap.parse_args()
    raw={str(n):[eval_one(s,n) for s in (1,7,19)] for n in (60,180,360)}
    summary={}
    for n,runs in raw.items():
        summary[n]={}
        for method in ("surface_mdl","execution_first"):
            d={}
            for split in ("seen","held_order","held_lexeme","nested","subject_omission","alternate_state"):
                d[split]={k:statistics.mean(x[method][split][k] for x in runs) for k in ("accuracy","ms","candidate_reads")}
            d["model_bytes"]=statistics.mean(x[method]["model_bytes"] for x in runs)
            d["programs"]=statistics.mean(x[method]["programs"] for x in runs)
            summary[n][method]=d
    payload={"hypothesis":"Execution-First Anti-Unification with MDL-Only Consolidation","raw":raw,"summary":summary,"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    Path(args.output).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(summary["360"],ensure_ascii=False,indent=2))
if __name__=="__main__": main()
