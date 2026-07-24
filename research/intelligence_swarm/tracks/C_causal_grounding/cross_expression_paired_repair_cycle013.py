from __future__ import annotations
import random, math, time, json, resource, statistics, pickle
from collections import Counter, defaultdict

SEEDS=(1,7,19)
DOMAINS=("d1","d2")
FORMS=("canonical","reverse","omitted","paragraph","free")
OPS=("id","toggle","set1","set0")
TARGETS=(0,1)

LEX={
"d1":{
 "obj":{0:["ラ","ミ"],1:["ソ","ナ"]},
 "op":{"id":["ケ","ホ"],"toggle":["ギ","プ"],"set1":["ワ","ト"],"set0":["カ","ネ"]},
 "noise":["ふわり","静かに","ここで","そのまま"]
},
"d2":{
 "obj":{0:["ゼ","ル"],1:["ボ","マ"]},
 "op":{"id":["シ","ヌ"],"toggle":["ガ","ペ"],"set1":["ヨ","テ"],"set0":["ク","レ"]},
 "noise":["ゆっくり","今度は","そっと","続けて"]
}}

def apply(before,op,t):
    w=list(before)
    if op=="toggle": w[t]=1-w[t]
    elif op=="set1": w[t]=1
    elif op=="set0": w[t]=0
    return tuple(w)

def utter(rng,domain,op,t,form,alias_variant):
    obj=LEX[domain]["obj"][t][alias_variant%2]
    act=LEX[domain]["op"][op][(alias_variant//2)%2]
    n=rng.choice(LEX[domain]["noise"])
    if form=="canonical": return f"{n}{obj}を{act}"
    if form=="reverse": return f"{act}、{n}{obj}"
    if form=="omitted": return f"{act}{obj}"
    if form=="paragraph": return f"{n}\n{act}\n対象は{obj}"
    return f"{obj}については、状況を見ながら{act}しておいて"

def make(seed,domain):
    rng=random.Random(seed*101 + (1 if domain=="d1" else 2))
    rows=[]
    for op in OPS:
      for t in TARGETS:
       for s0 in (0,1):
        for s1 in (0,1):
         before=(s0,s1)
         for form in FORMS:
          av=rng.randrange(4)
          cmd=utter(rng,domain,op,t,form,av)
          rows.append(dict(before=before,after=apply(before,op,t),op=op,target=t,form=form,cmd=cmd,
                           semantic=(op,t)))
    rng.shuffle(rows)
    return rows

def ngrams(s):
    s=s.replace(" ","")
    c=Counter()
    for n in (2,3):
      for i in range(len(s)-n+1): c[s[i:i+n]]+=1
    z=math.sqrt(sum(v*v for v in c.values())) or 1
    return {k:v/z for k,v in c.items()}

def cosine(a,b):
    if len(a)>len(b): a,b=b,a
    return sum(v*b.get(k,0) for k,v in a.items())

def delta_signature(before,after):
    return tuple(after[i]-before[i] for i in range(2))

def build_pairs(rows,method,seed):
    rng=random.Random(seed)
    bysem=defaultdict(list)
    for r in rows: bysem[r["semantic"]].append(r)
    pairs=[]
    for sem,rs in bysem.items():
      if method=="paired":
        for a in rs:
          cand=[b for b in rs if b["form"]!=a["form"] and b["before"]!=a["before"]]
          if cand:
            b=max(cand,key=lambda x: sum(int(a["before"][i]!=x["before"][i]) for i in range(2)))
            pairs.append((a,b))
      elif method=="state_static":
        z=[r for r in rs if r["before"]==(0,0)]
        for i in range(0,len(z)-1,2): pairs.append((z[i],z[i+1]))
      else:
        rr=rs[:]; rng.shuffle(rr)
        for i in range(0,len(rr)-1,2): pairs.append((rr[i],rr[i+1]))
    if method=="pair_shuffle":
      rights=[b for _,b in pairs]; rng.shuffle(rights); pairs=[(a,b) for (a,_),b in zip(pairs,rights)]
    return pairs

def train(rows,method,seed,outcome_shuffle=False):
    pairs=build_pairs(rows,method,seed)
    rng=random.Random(seed+99)
    units=[]
    for a,b in pairs:
      sa=delta_signature(a["before"],a["after"])
      sb=delta_signature(b["before"],b["after"])
      if outcome_shuffle:
        sb=rng.choice([(-1,0),(0,-1),(0,0),(0,1),(1,0)])
      if sa!=sb: continue
      fa,fb=ngrams(a["cmd"]),ngrams(b["cmd"])
      overlap=cosine(fa,fb)
      if overlap<0.35:
        units.append(dict(fa=fa,fb=fb,sig=sa,sem=a["semantic"],overlap=overlap))
    return units,pairs

def predict(units,row):
    f=ngrams(row["cmd"])
    scores=[]
    for u in units:
      s=max(cosine(f,u["fa"]),cosine(f,u["fb"]))
      scores.append((s,u))
    if not scores: return None,None
    s,u=max(scores,key=lambda x:x[0])
    if s<0.10: return None,None
    after=tuple(row["before"][i]+u["sig"][i] for i in range(2))
    if any(x not in (0,1) for x in after): return None,None
    return after,u["sem"]

def eval_units(units,rows):
    out={}
    for name,cond in {
      "prospective":lambda r:True,
      "inverse":lambda r:True,
      "unknown_order":lambda r:r["form"]=="reverse",
      "omitted":lambda r:r["form"]=="omitted",
      "paragraph":lambda r:r["form"]=="paragraph",
      "free":lambda r:r["form"]=="free",
      "object_permanence":lambda r:r["op"]!="id",
      "counterfactual":lambda r:True,
    }.items():
      n=d=0
      for r in rows:
        if not cond(r): continue
        if name=="counterfactual":
          rr=dict(r); rr["before"]=(1-r["before"][0],1-r["before"][1])
          rr["after"]=apply(rr["before"],r["op"],r["target"])
          pred,sem=predict(units,rr); ok=pred==rr["after"]
        elif name=="inverse":
          pred,sem=predict(units,r); ok=sem==r["semantic"]
        elif name=="object_permanence":
          pred,sem=predict(units,r)
          if pred is None: ok=False
          else:
            nt=1-r["target"]; ok=(pred==r["after"] and pred[nt]==r["before"][nt])
        else:
          pred,sem=predict(units,r); ok=pred==r["after"]
        n+=int(ok); d+=1
      out[name]=n/max(1,d)
    out["abstention"]=sum(predict(units,r)[0] is None for r in rows)/len(rows)
    return out

def run_seed(seed):
    result={}
    for domain in DOMAINS:
      rows=make(seed,domain)
      train_rows=[r for r in rows if r["form"] in ("canonical","reverse","omitted")][:100]
      test_rows=[r for r in rows if r not in train_rows]
      for method in ("paired","random","state_static","pair_shuffle"):
        units,pairs=train(train_rows,method,seed)
        result[(domain,method)]={"units":len(units),"pairs":len(pairs),
                                 "model_bytes":len(pickle.dumps(units)),**eval_units(units,test_rows)}
      units,pairs=train(train_rows,"paired",seed,outcome_shuffle=True)
      result[(domain,"outcome_shuffle")]={"units":len(units),"pairs":len(pairs),
                                          "model_bytes":len(pickle.dumps(units)),**eval_units(units,test_rows)}
    return {f"{d}:{m}":v for (d,m),v in result.items()}

def main():
    st=time.perf_counter()
    raw={str(s):run_seed(s) for s in SEEDS}
    methods=("paired","random","state_static","pair_shuffle","outcome_shuffle")
    metrics=list(next(iter(raw.values())).values())[0].keys()
    summary={}
    for m in methods:
      summary[m]={}
      for k in metrics:
        vals=[raw[str(s)][f"{d}:{m}"][k] for s in SEEDS for d in DOMAINS]
        summary[m][k]=statistics.mean(vals)
    strict=0
    for s in SEEDS:
      good=True
      for d in DOMAINS:
        a=raw[str(s)][f"{d}:paired"]
        controls=[raw[str(s)][f"{d}:{m}"] for m in ("random","state_static","pair_shuffle","outcome_shuffle")]
        for k in ("prospective","inverse","unknown_order","omitted","paragraph","free","object_permanence","counterfactual"):
          if a[k]-max(c[k] for c in controls)<0.10: good=False
      strict+=int(good)
    out={
      "cycle":13,
      "hypothesis":"Cross-Expression Paired Intervention Equivalence from Mutual Predictive Repair",
      "summary":summary,"strict_progress_seeds":strict,
      "semantic_identity_gate":False,"operation_goal_gate":False,
      "model_bytes_mean":summary["paired"]["model_bytes"],
      "peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "runtime_seconds":time.perf_counter()-st,
      "estimated_ops":"O(P*L + U*Q*V), character 2/3-gram sparse cosine",
      "candidate_units_mean":summary["paired"]["units"],
      "graph_size":0,"answer_leakage":False,"under_1gb":True,
      "weak_smartphone_verified":False,"highschool_level_passed":False,"completion":False,
      "raw":raw
    }
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
