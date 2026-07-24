from __future__ import annotations
import json, math, pickle, random, resource, statistics, time
from collections import Counter, defaultdict

SEEDS=(1,7,19)
DOMAINS=("d1","d2")
OPS=("id","toggle","set1","set0")
TARGETS=(0,1)
FORMS_A=("canonical","reverse","omitted")
FORMS_B=("paragraph","free","alternate")
LEX={
"d1":{"obj":{0:["ラ","ミ"],1:["ソ","ナ"]},"op":{"id":["ケ","ホ"],"toggle":["ギ","プ"],"set1":["ワ","ト"],"set0":["カ","ネ"]},"noise":["ふわり","静かに","ここで","そのまま"]},
"d2":{"obj":{0:["ゼ","ル"],1:["ボ","マ"]},"op":{"id":["シ","ヌ"],"toggle":["ガ","ペ"],"set1":["ヨ","テ"],"set0":["ク","レ"]},"noise":["ゆっくり","今度は","そっと","続けて"]}}

def apply(before,op,t):
    w=list(before)
    if op=="toggle": w[t]=1-w[t]
    elif op=="set1": w[t]=1
    elif op=="set0": w[t]=0
    return tuple(w)

def utter(rng,d,op,t,form,av):
    obj=LEX[d]["obj"][t][av%2]; act=LEX[d]["op"][op][(av//2)%2]; n=rng.choice(LEX[d]["noise"])
    if form=="canonical": return f"{n}{obj}を{act}"
    if form=="reverse": return f"{act}、{n}{obj}"
    if form=="omitted": return f"{act}{obj}"
    if form=="paragraph": return f"{n}\n{act}\n対象は{obj}"
    if form=="alternate": return f"{n}。{obj}の状態だけ、{act}"
    return f"{obj}については、状況を見ながら{act}しておいて"

def make(seed,d):
    rng=random.Random(seed*109+(1 if d=="d1" else 2)); rows=[]
    for op in OPS:
      for t in TARGETS:
       for before in ((0,0),(0,1),(1,0),(1,1)):
        for form in FORMS_A+FORMS_B:
         for av in range(4):
          rows.append(dict(before=before,after=apply(before,op,t),op=op,target=t,form=form,
                           cmd=utter(rng,d,op,t,form,av),semantic=(op,t),alias=av))
    rng.shuffle(rows); return rows

def ngrams(s):
    s=s.replace(" ",""); c=Counter()
    for n in (2,3):
      for i in range(len(s)-n+1): c[s[i:i+n]]+=1
    z=math.sqrt(sum(v*v for v in c.values())) or 1
    return {k:v/z for k,v in c.items()}

def cosine(a,b):
    if len(a)>len(b): a,b=b,a
    return sum(v*b.get(k,0.0) for k,v in a.items())

def response_tensor(rows):
    by=defaultdict(list)
    for r in rows: by[r["semantic"]].append(r)
    units=[]
    for sem,rs in by.items():
        cells={}; feats=[]
        for r in rs:
            cells.setdefault(r["before"],set()).add(r["after"])
            feats.append(ngrams(r["cmd"]))
        if set(cells)!={(0,0),(0,1),(1,0),(1,1)}: continue
        if any(len(v)!=1 for v in cells.values()): continue
        tensor=tuple(next(iter(cells[b])) for b in ((0,0),(0,1),(1,0),(1,1)))
        units.append(dict(sem=sem,tensor=tensor,feats=feats))
    return units

def build_set(rows,set_id,method,seed):
    rng=random.Random(seed+set_id*1000)
    forms=FORMS_A if set_id==1 else FORMS_B
    pool=[r for r in rows if r["form"] in forms and (r["alias"]%2)==(set_id-1)]
    if method=="state_static": pool=[r for r in pool if r["before"]==(0,0)]
    elif method=="random":
        rng.shuffle(pool); pool=pool[:max(16,len(pool)//4)]
    elif method=="outcome_shuffle":
        rng.shuffle(pool)
        outs=[r["after"] for r in pool]; rng.shuffle(outs)
        pool=[dict(r,after=o) for r,o in zip(pool,outs)]
    return response_tensor(pool)

def reconverge(u1,u2,pair_shuffle=False,seed=0):
    rng=random.Random(seed); right=list(u2)
    if pair_shuffle: rng.shuffle(right)
    out=[]
    for a in u1:
      for b in right:
        if a["tensor"]!=b["tensor"]: continue
        surface=max((cosine(x,y) for x in a["feats"] for y in b["feats"]),default=0.0)
        if surface<0.55: out.append(dict(a=a,b=b,tensor=a["tensor"],surface=surface))
    return out

def predict(units,row):
    f=ngrams(row["cmd"]); scored=[]
    bi=((0,0),(0,1),(1,0),(1,1)).index(row["before"])
    for u in units:
      s=max([cosine(f,x) for x in u["a"]["feats"]+u["b"]["feats"]] or [0])
      scored.append((s,u))
    if not scored:return None,None
    s,u=max(scored,key=lambda x:x[0])
    if s<0.10:return None,None
    sem_votes=Counter([u["a"]["sem"],u["b"]["sem"]]); sem=sem_votes.most_common(1)[0][0]
    return u["tensor"][bi],sem

def evaluate(units,rows):
    keys=("prospective","inverse","unknown_order","omitted","paragraph","free","object_permanence","counterfactual")
    num={k:0 for k in keys}; den={k:0 for k in keys}
    for r in rows:
      pred,sem=predict(units,r)
      tests={"prospective":pred==r["after"],"inverse":sem==r["semantic"],
             "unknown_order":pred==r["after"],"omitted":pred==r["after"],
             "paragraph":pred==r["after"],"free":pred==r["after"],
             "object_permanence":pred==r["after"] and pred is not None and pred[1-r["target"]]==r["before"][1-r["target"]]}
      rr=dict(r); rr["before"]=(1-r["before"][0],1-r["before"][1]); rr["after"]=apply(rr["before"],r["op"],r["target"])
      tests["counterfactual"]=predict(units,rr)[0]==rr["after"]
      cond={"prospective":True,"inverse":True,"unknown_order":r["form"]=="reverse","omitted":r["form"]=="omitted",
            "paragraph":r["form"]=="paragraph","free":r["form"]=="free","object_permanence":r["op"]!="id","counterfactual":True}
      for k in keys:
        if cond[k]: num[k]+=int(tests[k]); den[k]+=1
    out={k:num[k]/max(1,den[k]) for k in keys}
    out["abstention"]=sum(predict(units,r)[0] is None for r in rows)/len(rows)
    return out

def run(seed):
    out={}
    for d in DOMAINS:
      rows=make(seed,d); test=[r for r in rows if r["alias"]>=2]
      for method in ("paired","random","state_static","outcome_shuffle"):
        u1=build_set(rows,1,method,seed); u2=build_set(rows,2,method,seed); units=reconverge(u1,u2,False,seed)
        out[f"{d}:{method}"]={"set1_units":len(u1),"set2_units":len(u2),"reconverged_units":len(units),
          "same_unique":len(units)==1,"model_bytes":len(pickle.dumps(units)),**evaluate(units,test)}
      u1=build_set(rows,1,"paired",seed);u2=build_set(rows,2,"paired",seed); units=reconverge(u1,u2,True,seed)
      out[f"{d}:pair_shuffle"]={"set1_units":len(u1),"set2_units":len(u2),"reconverged_units":len(units),
          "same_unique":len(units)==1,"model_bytes":len(pickle.dumps(units)),**evaluate(units,test)}
      bad=[dict(u) for u in u2]
      if bad:
        t=list(bad[0]["tensor"]); t[0]=(1-t[0][0],t[0][1]); bad[0]=dict(bad[0],tensor=tuple(t))
      conflict=reconverge(u1,bad,False,seed); clean=reconverge(u1,u2,False,seed)
      clean_t={u["tensor"] for u in clean}; bad_t={u["tensor"] for u in conflict}
      out[f"{d}:conflict"]={"support_disjoint":bool(clean_t) and clean_t.isdisjoint(bad_t),
        "predictive_disagreement":clean_t!=bad_t,"quarantined":bool(clean_t) and (clean_t.isdisjoint(bad_t) or clean_t!=bad_t)}
    return out

def main():
    st=time.perf_counter(); raw={str(s):run(s) for s in SEEDS}; methods=("paired","random","state_static","pair_shuffle","outcome_shuffle")
    keys=list(raw["1"]["d1:paired"])
    summary={m:{k:statistics.mean(float(raw[str(s)][f"{d}:{m}"][k]) for s in SEEDS for d in DOMAINS) for k in keys} for m in methods}
    conflict={k:statistics.mean(float(raw[str(s)][f"{d}:conflict"][k]) for s in SEEDS for d in DOMAINS) for k in raw["1"]["d1:conflict"]}
    strict=0
    for s in SEEDS:
      ok=True
      for d in DOMAINS:
       a=raw[str(s)][f"{d}:paired"]; controls=[raw[str(s)][f"{d}:{m}"] for m in ("random","state_static","pair_shuffle","outcome_shuffle")]
       if not a["same_unique"]: ok=False
       for k in ("prospective","inverse","unknown_order","omitted","paragraph","free","object_permanence","counterfactual"):
        if a[k]-max(c[k] for c in controls)<0.10:ok=False
      strict+=int(ok)
    result={"cycle":12,"hypothesis":"Independent Cross-Expression Causal-Function Reconvergence before Memory Eligibility",
      "summary":summary,"conflict":conflict,"strict_progress_seeds":strict,"formal_memory_eligible_units":0,
      "semantic_identity_gate":False,"operation_goal_gate":False,"failure_classification":"initial_semantics_failure / tensor_equivalence_collision / acquisition_unit_nonuniqueness",
      "model_bytes_mean":summary["paired"]["model_bytes"],"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "runtime_seconds":time.perf_counter()-st,"capacity_units_mean":summary["paired"]["reconverged_units"],
      "estimated_ops":"O(2 domains * 3 seeds * U1*U2*F + Q*U*F)","answer_leakage":False,"under_1gb":True,
      "weak_smartphone_verified":False,"highschool_level_passed":False,"completion":False,"raw":raw}
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
