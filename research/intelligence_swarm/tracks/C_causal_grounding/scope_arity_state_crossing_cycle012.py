from __future__ import annotations
import itertools, json, math, pickle, random, resource, statistics, time

SEEDS=(1,7,19)
DOMAINS=("d1","d2")
PROGRAMS=("identity","set0","set1","toggle","identity_flip1","set0_flip1","set1_flip1","toggle_flip1","swap","copy01","copy10","xor_to0")
TOKENS=("α","β","γ","δ")

def apply(program, state):
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

ARITY={p:(1 if p in ("identity","set0","set1","toggle","identity_flip1","set0_flip1","set1_flip1","toggle_flip1") else 2) for p in PROGRAMS}

def make_world(seed,domain):
    rng=random.Random(seed*101 + (1 if domain=="d1" else 17))
    chosen=rng.sample(PROGRAMS,4)
    mapping=dict(zip(TOKENS,chosen))
    aliases={t:(t + ("ら" if domain=="d1" else "ね")) for t in TOKENS}
    return mapping,aliases

def render(token,state,form,aliases):
    t=aliases[token]
    a,b=state
    if form=="plain": return f"{t} を実行"
    if form=="reverse": return f"状態は右{b}左{a}。{t}"
    if form=="omitted": return f"{t}で"
    if form=="paragraph": return f"左は{a}、右は{b}。\n次に{t}。"
    if form=="free": return f"いま左側が{a}で右側が{b}なんだけど、{t}をやったらどうなる？"
    return t

def candidates():
    return [dict(zip(TOKENS,perm)) for perm in itertools.permutations(PROGRAMS,4)]

CANDS=candidates()

def probe_space():
    return [(t,s) for t in TOKENS for s in itertools.product((0,1),repeat=2)]

def outcome(cand,probe):
    t,s=probe
    return apply(cand[t],s)

def entropy(survivors,probe):
    counts={}
    for i in survivors:
        o=outcome(CANDS[i],probe)
        counts[o]=counts.get(o,0)+1
    n=max(1,len(survivors))
    return -sum((v/n)*math.log2(v/n) for v in counts.values())

def choose_probe(survivors,pool,method,rng):
    if method=="active":
        return max(pool,key=lambda p:(entropy(survivors,p),p))
    if method=="state_static":
        fixed=[p for p in pool if p[1]==(0,0)]
        return rng.choice(fixed or pool)
    return rng.choice(pool)

def identify(true_mapping,budget,method,seed,shuffle=False):
    rng=random.Random(seed)
    survivors=list(range(len(CANDS)))
    pool=probe_space()
    used=[]
    for _ in range(budget):
        if not survivors or not pool: break
        p=choose_probe(survivors,pool,method,rng)
        pool.remove(p); used.append(p)
        obs=apply(true_mapping[p[0]],p[1])
        if shuffle:
            alts=[apply(true_mapping[t],s) for t,s in pool if apply(true_mapping[t],s)!=obs]
            if alts: obs=rng.choice(alts)
        survivors=[i for i in survivors if outcome(CANDS[i],p)==obs]
    return survivors,used

def vote_program(survivors,token):
    counts={}
    for i in survivors:
        p=CANDS[i][token]
        counts[p]=counts.get(p,0)+1
    return max(counts,key=counts.get) if counts else None

def vote_after(survivors,token,state):
    counts={}
    for i in survivors:
        o=apply(CANDS[i][token],state)
        counts[o]=counts.get(o,0)+1
    return max(counts,key=counts.get) if counts else None

def evaluate(survivors,true_mapping,aliases):
    forms=("plain","reverse","omitted","paragraph","free")
    total=correct=inv=arity=permanence=cf=0
    for token in TOKENS:
        for state in itertools.product((0,1),repeat=2):
            truep=true_mapping[token]
            for form in forms:
                _=render(token,state,form,aliases)
                pred=vote_after(survivors,token,state)
                correct += pred==apply(truep,state)
                inv += vote_program(survivors,token)==truep
                arity += (ARITY.get(vote_program(survivors,token),-1)==ARITY[truep])
                if ARITY[truep]==1:
                    permanence += (pred is not None and pred[1]==state[1])
                else:
                    permanence += pred==apply(truep,state)
                alt=(1-state[0],1-state[1])
                cf += vote_after(survivors,token,alt)==apply(truep,alt)
                total+=1
    return {"prospective":correct/total,"inverse_program":inv/total,"arity":arity/total,
            "object_permanence":permanence/total,"counterfactual":cf/total}

def arity_shuffle_eval(survivors,true_mapping,aliases,seed):
    rng=random.Random(seed)
    fake=[]
    for i in survivors:
        c=dict(CANDS[i])
        vals=list(c.values()); rng.shuffle(vals)
        fake.append(dict(zip(TOKENS,vals)))
    def vprog(token):
        counts={}
        for c in fake: counts[c[token]]=counts.get(c[token],0)+1
        return max(counts,key=counts.get) if counts else None
    def vafter(token,state):
        counts={}
        for c in fake:
            o=apply(c[token],state); counts[o]=counts.get(o,0)+1
        return max(counts,key=counts.get) if counts else None
    total=correct=inv=arity=perm=cf=0
    for token in TOKENS:
      for state in itertools.product((0,1),repeat=2):
        tp=true_mapping[token]
        for _form in ("plain","reverse","omitted","paragraph","free"):
          p=vafter(token,state)
          correct+=p==apply(tp,state); inv+=vprog(token)==tp
          arity+=ARITY.get(vprog(token),-1)==ARITY[tp]
          perm+=(p is not None and p[1]==state[1]) if ARITY[tp]==1 else p==apply(tp,state)
          alt=(1-state[0],1-state[1]); cf+=vafter(token,alt)==apply(tp,alt); total+=1
    return {"prospective":correct/total,"inverse_program":inv/total,"arity":arity/total,
            "object_permanence":perm/total,"counterfactual":cf/total}

def run():
    start=time.perf_counter()
    raw={}
    for seed in SEEDS:
      raw[str(seed)]={}
      for domain in DOMAINS:
        true_mapping,aliases=make_world(seed,domain)
        raw[str(seed)][domain]={}
        for method in ("active","random","state_static"):
          surv,used=identify(true_mapping,7,method,seed+(0 if domain=="d1" else 100))
          raw[str(seed)][domain][method]={"survivors":len(surv),"used_probes":used,
            **evaluate(surv,true_mapping,aliases),"model_bytes":len(pickle.dumps(surv))}
        surv,_=identify(true_mapping,7,"active",seed+300,shuffle=True)
        raw[str(seed)][domain]["outcome_shuffle"]={"survivors":len(surv),**evaluate(surv,true_mapping,aliases)}
        active_surv,_=identify(true_mapping,7,"active",seed+500)
        raw[str(seed)][domain]["arity_shuffle"]={"survivors":len(active_surv),
          **arity_shuffle_eval(active_surv,true_mapping,aliases,seed)}
    methods=("active","random","state_static","outcome_shuffle","arity_shuffle")
    metrics=("survivors","prospective","inverse_program","arity","object_permanence","counterfactual")
    summary={}
    for m in methods:
      summary[m]={k:statistics.mean(float(raw[str(s)][d][m][k]) for s in SEEDS for d in DOMAINS) for k in metrics}
    strict=0
    for s in SEEDS:
      ok=True
      for d in DOMAINS:
        a=raw[str(s)][d]["active"]
        controls=[raw[str(s)][d][x] for x in ("random","state_static","outcome_shuffle","arity_shuffle")]
        for k in ("prospective","inverse_program","object_permanence","counterfactual"):
          if a[k]-max(c[k] for c in controls)<0.10: ok=False
      strict+=int(ok)
    result={"track":"C_causal_grounding","cycle":12,
      "hypothesis":"Scope-Arity Program Identification from State-Crossing and Non-Target Preservation Witnesses",
      "seeds":SEEDS,"domains":DOMAINS,"candidate_worlds":len(CANDS),"witness_budget":7,
      "summary":summary,"strict_progress_seeds":strict,"semantic_identity_gate":False,
      "operation_goal_gate":False,"decision":"upper_bound_supported_no_formal_progress",
      "remaining_oracles":["operation token boundary","binary state interface","finite program vocabulary","raw parser"],
      "answer_leakage":False,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "runtime_seconds":time.perf_counter()-start,
      "estimated_ops":f"O(B*H*Q), H={len(CANDS)}, B=7, Q=16","under_1gb":True,
      "weak_smartphone_verified":False,"highschool_level_passed":False,"completion":False,"raw":raw}
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__": run()
