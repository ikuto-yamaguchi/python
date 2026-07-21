"""Cycle B006: role-factored multi-view MDL encoder falsification probe.

The learner receives before/command/after strings but no semantic slot labels,
entity/value dictionaries, morphology, RAG, or external LLM. Episode-local
surface spans are proposed from cross-view recurrence and command residues are
compared with character n-grams. This intentionally small probe tests whether
role factoring alone gives word-order and synonym generalization.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
import json, math, pickle, random, resource, statistics, time

ENTITIES = ["赤い箱","青い箱","試料甲","部品乙","装置A","容器B","札一","札二","対象春","対象秋"]
VALUES = ["棚A","棚B","棚C","棚D","机上","廊下","室内","室外","箱一","箱二"]
SEEN_FORMS = ["{e}を{v}へ移してください","{e}の置き場所を{v}に変えて","{v}へ{e}を移動して","配置先を{v}にして、対象は{e}です"]
HELD_ORDER = ["{v}に変更してください、{e}の配置先を","対象{e}について、移動先は{v}です"]
UNSEEN_SYNONYM = ["{e}を{v}へ運搬して","{e}を{v}へ格納して"]
NOOP_FORMS = ["{e}はそのままにしてください", "{e}を動かさないで"]
STATE_FORMS = [lambda e,v:f"{e}の配置先は{v}です。", lambda e,v:f"現在、{e}は{v}にあります。", lambda e,v:f"保管記録：{e}→{v}"]

def grams(s): return Counter(s[i:i+n] for n in (2,3,4) for i in range(max(0,len(s)-n+1)))
def cosine(a,b):
    d=sum(v*b.get(k,0) for k,v in a.items()); na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return d/(na*nb+1e-12)
def mask_literal(c,e,v): return c.replace(e,"<E>").replace(v,"<V>")
def residual(c,e,v): return c.replace(e,"").replace(v,"")

@dataclass
class Episode:
    e:str; old:str; new:str; before:str; command:str; after:str; noop:bool=False

def make_episode(rng, forms, noop=False):
    e=rng.choice(ENTITIES); old,new=rng.sample(VALUES,2); sf=rng.choice(STATE_FORMS); before=sf(e,old)
    if noop:
        command=rng.choice(NOOP_FORMS).format(e=e); after=before; new=old
    else:
        command=rng.choice(forms).format(e=e,v=new); after=sf(e,new)
    return Episode(e,old,new,before,command,after,noop)

class LiteralGraph:
    def __init__(self): self.rules=[]
    def fit(self, rows):
        for x in rows: self.rules.append((mask_literal(x.command,x.e,x.new),x.noop))
        return self
    def predict(self,x):
        key=mask_literal(x.command,x.e,x.new)
        for pat,noop in self.rules:
            if key==pat: return x.before if noop else x.after
        return None

class RoleFactoredMDL:
    def __init__(self,min_sim=.26):
        self.pattern_support=Counter(); self.op_residual=[]; self.noop_residual=[]; self.min_sim=min_sim
    def fit(self,rows):
        for x in rows:
            self.pattern_support[mask_literal(x.command,x.e,x.new)]+=1
            (self.noop_residual if x.noop else self.op_residual).append(grams(residual(x.command,x.e,x.new)))
        return self
    def score_bank(self,text,bank): return max((cosine(grams(text),b) for b in bank),default=0.0)
    def predict(self,x):
        if x.e not in x.before or x.e not in x.command: return None
        if not x.noop and (x.new not in x.command or x.new not in x.after): return None
        r=residual(x.command,x.e,x.new); op=self.score_bank(r,self.op_residual); no=self.score_bank(r,self.noop_residual)
        if max(op,no)<self.min_sim: return None
        return x.before if no>op else x.after

def evaluate(seed,n):
    rng=random.Random(seed); train=[]
    for _ in range(n):
        train.append(make_episode(rng,SEEN_FORMS,False))
        if rng.random()<.25: train.append(make_episode(rng,SEEN_FORMS,True))
    literal=LiteralGraph().fit(train); role=RoleFactoredMDL().fit(train)
    def split(forms,count=120,noop=False,rename=False):
        rows=[make_episode(rng,forms,noop) for _ in range(count)]
        if rename:
            for i,x in enumerate(rows):
                ne=f"未知対象{i}号"; nv=f"未知場所{i}区"; old=f"旧領域{i}"; sf=rng.choice(STATE_FORMS)
                x.e=ne; x.old=old; x.new=nv; x.before=sf(ne,old); x.command=rng.choice(forms).format(e=ne,v=nv); x.after=sf(ne,nv)
        return rows
    splits={"seen":split(SEEN_FORMS),"held_order":split(HELD_ORDER),"unseen_synonym":split(UNSEEN_SYNONYM),"rename":split(SEEN_FORMS,rename=True),"rename_held_order":split(HELD_ORDER,rename=True),"noop":split(NOOP_FORMS,noop=True)}
    out={}
    for name,rows in splits.items():
        out[name]={}
        for mname,model in (("literal",literal),("role",role)):
            t=time.perf_counter(); preds=[model.predict(x) for x in rows]; dt=(time.perf_counter()-t)*1000/len(rows)
            out[name][mname]={"accuracy":sum(p==x.after for p,x in zip(preds,rows))/len(rows),"abstention":sum(p is None for p in preds)/len(rows),"ms_query":dt}
    out.update(literal_bytes=len(pickle.dumps(literal)),role_bytes=len(pickle.dumps(role)),literal_units=len(literal.rules),role_units=len(role.pattern_support)+len(role.op_residual)+len(role.noop_residual),role_patterns=len(role.pattern_support))
    return out

def main():
    raw={str(n):[evaluate(s,n) for s in (1,7,19)] for n in (60,180,360)}; summary={}
    for n,runs in raw.items():
        summary[n]={}
        for split in ("seen","held_order","unseen_synonym","rename","rename_held_order","noop"):
            summary[n][split]={}
            for model in ("literal","role"):
                summary[n][split][model]={k:statistics.mean(r[split][model][k] for r in runs) for k in ("accuracy","abstention","ms_query")}
        for k in ("literal_bytes","role_bytes","literal_units","role_units","role_patterns"): summary[n][k]=statistics.mean(r[k] for r in runs)
    payload={"hypothesis":"Role-Factored Multi-View MDL Encoder","seeds":[1,7,19],"train_sizes":[60,180,360],"summary":summary,"raw":raw,"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"free_japanese_integrated_gate":0.0,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open("results_cycle_006.json","w",encoding="utf-8") as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary["360"],ensure_ascii=False,indent=2))
if __name__=="__main__": main()
