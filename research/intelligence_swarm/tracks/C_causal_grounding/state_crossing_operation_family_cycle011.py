#!/usr/bin/env python3
import itertools, json, math, random, resource, statistics, time
from collections import Counter

FUNCS={"zero":lambda x:0,"one":lambda x:1,"identity":lambda x:x,"not":lambda x:1-x}
TOKENS=("p","q","r")
CANDIDATES=[dict(zip(TOKENS,p)) for p in itertools.permutations(FUNCS,3)]
SEEDS=(1,7,19)

def predict(c,e): return FUNCS[c[e["op"]]](e["before"])
def keep(cs,e): return [c for c in cs if predict(c,e)==e["after"]]
def entropy(cs,e):
    z=Counter(predict(c,e) for c in cs); n=len(cs)
    return -sum((v/n)*math.log(v/n) for v in z.values())
def choose_active(cs,pool,budget):
    rem=list(pool); chosen=[]
    for _ in range(budget):
        e=max(rem,key=lambda q:entropy(cs,q)); rem.remove(e); chosen.append(e); cs=keep(cs,e)
    return chosen,cs
def accuracy(cs,test):
    if not cs:return 0.0
    ok=0
    for e in test:
        v=Counter(predict(c,e) for c in cs).most_common()
        y=v[0][0] if len(v)==1 or v[0][1]>v[1][1] else None
        ok+=y==e["after"]
    return ok/len(test)
def one(seed,budget=5):
    rng=random.Random(seed); true=dict(zip(TOKENS,rng.sample(list(FUNCS),3)))
    pool=[{"op":o,"before":x,"after":FUNCS[true[o]](x),"form":f} for o in TOKENS for x in (0,1) for f in range(4)]
    _,ac=choose_active(CANDIDATES,pool,budget)
    rc=list(CANDIDATES)
    for e in rng.sample(pool,budget): rc=keep(rc,e)
    zc=list(CANDIDATES); zpool=[e for e in pool if e["before"]==0]
    for e in rng.sample(zpool,budget): zc=keep(zc,e)
    shuffled=list(CANDIDATES); outs=[e["after"] for e in pool]; rng.shuffle(outs)
    for e,y in zip(pool[:budget],outs[:budget]): shuffled=keep(shuffled,{**e,"after":y})
    test=[{"op":o,"before":x,"after":FUNCS[true[o]](x)} for o in TOKENS for x in (0,1)]
    return {"seed":seed,"active_survivors":len(ac),"random_survivors":len(rc),"state0_survivors":len(zc),"shuffle_survivors":len(shuffled),"active_prospective":accuracy(ac,test),"random_prospective":accuracy(rc,test),"state0_prospective":accuracy(zc,test),"shuffle_prospective":accuracy(shuffled,test)}
def main():
    t=time.perf_counter(); rows=[one(s) for s in SEEDS]
    keys=[k for k in rows[0] if k!="seed"]
    mean={k:statistics.mean(r[k] for r in rows) for k in keys}
    out={"hypothesis":"State-Crossing Witnesses Identify Nonparametric Unary Operation Families","seeds":rows,"mean":mean,"model_bytes_upper_bound":24*3*8,"candidate_worlds":24,"estimated_probe_evaluations":24*24*5,"runtime_sec":time.perf_counter()-t,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"strict_progress_gate":False,"high_school_level":False}
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
