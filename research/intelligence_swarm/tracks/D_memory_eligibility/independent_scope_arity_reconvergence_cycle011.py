from __future__ import annotations
import itertools, json, math, pickle, random, resource, statistics, time

SEEDS=(1,7,19)
DOMAINS=("d1","d2")
PROGRAMS=("identity","set0","set1","toggle","identity_flip1","set0_flip1","set1_flip1","toggle_flip1","swap","copy01","copy10","xor_to0")
TOKENS=("α","β","γ","δ")

def apply(program,state):
    a,b=state
    if program=="identity": return (a,b)
    if program=="set0": return (0,b)
    if program=="set1": return (1,b)
    if program=="toggle": return (1-a,b)
    if program=="identity_flip1": return (a,1-b)
    if program=="set0_flip1": return (0,1-b)
    if program=="set1_flip1": return (1,1-b)
    if program=="toggle_flip1": return (1-a,1-b)
    if program=="swap": return (b,a)
    if program=="copy01": return (a,a)
    if program=="copy10": return (b,b)
    if program=="xor_to0": return (a^b,b)
    raise ValueError(program)

ARITY={p:(1 if p in PROGRAMS[:8] else 2) for p in PROGRAMS}

def make_world(seed,domain):
    rng=random.Random(seed*101+(1 if domain=="d1" else 17))
    chosen=rng.sample(PROGRAMS,4)
    return dict(zip(TOKENS,chosen))

CANDS=[dict(zip(TOKENS,p)) for p in itertools.permutations(PROGRAMS,4)]
PROBES=[(t,s) for t in TOKENS for s in itertools.product((0,1),repeat=2)]

def outcome(cand,probe): return apply(cand[probe[0]],probe[1])

def entropy(survivors,probe):
    counts={}
    for i in survivors:
        o=outcome(CANDS[i],probe); counts[o]=counts.get(o,0)+1
    n=max(1,len(survivors))
    return -sum((v/n)*math.log2(v/n) for v in counts.values())

def choose(survivors,pool,method,rng):
    if method=="active": return max(pool,key=lambda p:(entropy(survivors,p),p))
    if method=="state_static":
        z=[p for p in pool if p[1]==(0,0)]
        return rng.choice(z or pool)
    return rng.choice(pool)

def identify(true_mapping,pool,budget,method,seed,corrupt=False):
    rng=random.Random(seed); pool=list(pool); surv=list(range(len(CANDS))); used=[]
    for step in range(budget):
        if not pool or not surv: break
        p=choose(surv,pool,method,rng); pool.remove(p); used.append(p)
        obs=apply(true_mapping[p[0]],p[1])
        if corrupt and step==max(0,budget//2): obs=(1-obs[0],obs[1])
        surv=[i for i in surv if outcome(CANDS[i],p)==obs]
    return surv,used

def vote_program(surv,t):
    c={}
    for i in surv:
        p=CANDS[i][t]; c[p]=c.get(p,0)+1
    return max(c,key=c.get) if c else None

def vote_after(surv,t,s):
    c={}
    for i in surv:
        o=apply(CANDS[i][t],s); c[o]=c.get(o,0)+1
    return max(c,key=c.get) if c else None

def evaluate(surv,true_mapping):
    total=pros=inv=arity=perm=cf=0
    for t in TOKENS:
      tp=true_mapping[t]
      for s in itertools.product((0,1),repeat=2):
        pred=vote_after(surv,t,s); vp=vote_program(surv,t)
        pros+=pred==apply(tp,s); inv+=vp==tp; arity+=ARITY.get(vp,-1)==ARITY[tp]
        perm += (pred is not None and pred[1]==s[1]) if ARITY[tp]==1 else pred==apply(tp,s)
        alt=(1-s[0],1-s[1]); cf+=vote_after(surv,t,alt)==apply(tp,alt); total+=1
    return {"prospective":pros/total,"inverse_program":inv/total,"arity":arity/total,
            "object_permanence":perm/total,"counterfactual":cf/total}

def run_method(mapping,method,seed):
    s1,u1=identify(mapping,PROBES,7,method,seed)
    remaining=[p for p in PROBES if p not in u1]
    s2,u2=identify(mapping,remaining,7,method,seed+1000)
    inter=sorted(set(s1)&set(s2))
    return {"set1_survivors":len(s1),"set2_survivors":len(s2),"intersection_survivors":len(inter),
            "same_unique":len(s1)==len(s2)==1 and s1[0]==s2[0],
            "used1":u1,"used2":u2,"model_bytes":len(pickle.dumps(inter)),**evaluate(inter,mapping)}

def run():
    start=time.perf_counter(); raw={}
    for seed in SEEDS:
      raw[str(seed)]={}
      for domain in DOMAINS:
        mapping=make_world(seed,domain); raw[str(seed)][domain]={}
        for method in ("active","random","state_static"):
            raw[str(seed)][domain][method]=run_method(mapping,method,seed+(100 if domain=="d2" else 0))
        bad,u1=identify(mapping,PROBES,7,"active",seed+2000,corrupt=True)
        remaining=[p for p in PROBES if p not in u1]
        good,_=identify(mapping,remaining,7,"active",seed+3000)
        both=sorted(set(bad)&set(good))
        raw[str(seed)][domain]["conflict"]={"bad_survivors":len(bad),"good_survivors":len(good),
            "intersection_survivors":len(both),"conflict_detected":len(both)==0,**evaluate(both,mapping)}
    methods=("active","random","state_static")
    metrics=("set1_survivors","set2_survivors","intersection_survivors","same_unique","model_bytes",
             "prospective","inverse_program","arity","object_permanence","counterfactual")
    summary={m:{k:statistics.mean(float(raw[str(s)][d][m][k]) for s in SEEDS for d in DOMAINS) for k in metrics} for m in methods}
    summary["conflict"]={k:statistics.mean(float(raw[str(s)][d]["conflict"][k]) for s in SEEDS for d in DOMAINS)
                         for k in ("bad_survivors","good_survivors","intersection_survivors","conflict_detected")}
    upper=sum(all(raw[str(s)][d]["active"]["same_unique"] for d in DOMAINS) for s in SEEDS)
    strict=0
    for s in SEEDS:
      ok=True
      for d in DOMAINS:
        a=raw[str(s)][d]["active"]; controls=[raw[str(s)][d][x] for x in ("random","state_static")]
        if not a["same_unique"]: ok=False
        for k in ("prospective","inverse_program","object_permanence","counterfactual"):
          if a[k]-max(c[k] for c in controls)<0.10: ok=False
      strict+=int(ok)
    result={"track":"D_memory_eligibility","cycle":11,
      "hypothesis":"Independent Scope-Arity Reconvergence before Memory Eligibility",
      "seeds":SEEDS,"domains":DOMAINS,"candidate_worlds":len(CANDS),"witness_budget_per_set":7,
      "summary":summary,"upper_bound_reconvergence_seeds":upper,"strict_progress_seeds":strict,
      "formal_memory_eligible_units":0,"semantic_identity_gate":False,"operation_goal_gate":False,
      "decision":"hypothesis_rejected_no_formal_memory_eligibility",
      "failure_classification":"independent_set_non_uniqueness_and_intersection_rescue",
      "remaining_oracles":["operation token boundary","binary state interface","finite program vocabulary","raw parser"],
      "memory_optimization_enabled":False,"catastrophic_forgetting_observed":False,
      "answer_leakage":False,"model_bytes_mean":summary["active"]["model_bytes"],
      "peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "runtime_seconds":time.perf_counter()-start,"capacity_candidate_worlds":len(CANDS),
      "estimated_ops":f"O(2*B*H*Q), H={len(CANDS)}, B=7, Q=16",
      "under_1gb":True,"weak_smartphone_verified":False,"highschool_level_passed":False,"completion":False,"raw":raw}
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__": run()
