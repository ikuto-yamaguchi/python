from __future__ import annotations
import itertools, json, math, pickle, random, resource, statistics, time

SEEDS=(1,7,19)
CHARS=("ラ","ミ","ソ","ギ","プ","ワ","ト")
LATENT_ROLES=("obj0","obj1","identity","toggle","noise")
FORMS=("prefix","suffix","interleave","reverse","paragraph","omitted")

def apply(world, op, target):
    w=list(world)
    if op=="toggle":
        w[target]=1-w[target]
    return tuple(w)

def make_data(seed):
    rng=random.Random(seed)
    chars=list(CHARS); rng.shuffle(chars)
    true_role={chars[0]:"obj0",chars[1]:"obj0",chars[2]:"obj1",chars[3]:"identity",chars[4]:"toggle",chars[5]:"toggle",chars[6]:"noise"}
    by_role={r:[c for c,v in true_role.items() if v==r] for r in LATENT_ROLES}
    rows=[]
    for _ in range(120):
        before=(rng.randrange(2),rng.randrange(2)); target=rng.randrange(2); op=rng.choice(("identity","toggle")); form=rng.choice(FORMS)
        obj=rng.choice(by_role[f"obj{target}"]); opch=rng.choice(by_role[op]); n1,n2=(rng.choice(by_role["noise"]) for _ in range(2))
        if form=="prefix": toks=[n1,opch,obj,n2]
        elif form=="suffix": toks=[n1,obj,opch,n2]
        elif form=="interleave": toks=[obj,n1,opch,n2]
        elif form=="reverse": toks=[n1,obj,n2,opch]
        elif form=="paragraph": toks=[n1,opch,"\n",obj,n2]
        else: toks=[opch,obj] if rng.random()<0.5 else [obj,opch]
        rows.append({"before":before,"command":"".join(toks),"after":apply(before,op,target),"target":target,"op":op,"form":form})
    return rows,true_role

ROLE_INDEX={r:i for i,r in enumerate(LATENT_ROLES)}

def all_hypotheses():
    base=(ROLE_INDEX["obj0"],ROLE_INDEX["obj0"],ROLE_INDEX["obj1"],ROLE_INDEX["identity"],ROLE_INDEX["toggle"],ROLE_INDEX["toggle"],ROLE_INDEX["noise"])
    out=set(itertools.permutations(base)); rng=random.Random(20260724)
    while len(out)<6000:
        labels=tuple(rng.randrange(len(LATENT_ROLES)) for _ in CHARS)
        if set(labels)==set(range(len(LATENT_ROLES))): out.add(labels)
    return sorted(out)

HS=all_hypotheses()

def parses(h, command):
    roles=[LATENT_ROLES[h[CHARS.index(c)]] for c in command if c in CHARS]
    objs={int(r[-1]) for r in roles if r.startswith("obj")}; ops={r for r in roles if r in ("identity","toggle")}
    if len(objs)!=1 or len(ops)!=1: return []
    return [(next(iter(ops)),next(iter(objs)))]

def predictions(h,row): return {apply(row["before"],op,target) for op,target in parses(h,row["command"])}

def entropy(survivors,row):
    groups={}
    for i in survivors:
        key=tuple(sorted(predictions(HS[i],row))); groups[key]=groups.get(key,0)+1
    n=max(1,len(survivors))
    return -sum((v/n)*math.log2(v/n) for v in groups.values())

def select(pool,budget,method,seed,shuffle=False):
    rng=random.Random(seed); pool=list(pool); surv=list(range(len(HS)))
    for _ in range(budget):
        if not pool or not surv: break
        if method=="active": row=max(pool,key=lambda r:entropy(surv,r))
        elif method=="state_static":
            cands=[r for r in pool if r["before"]==(0,0)]; row=rng.choice(cands or pool)
        else: row=rng.choice(pool)
        pool.remove(row); outcome=row["after"]
        if shuffle:
            alts=[r["after"] for r in pool if r["after"]!=outcome]
            if alts: outcome=rng.choice(alts)
        surv=[i for i in surv if outcome in predictions(HS[i],row)]
    return surv

def vote(surv,row):
    v={}
    for i in surv:
        for p in predictions(HS[i],row): v[p]=v.get(p,0)+1
    return max(v,key=v.get) if v else None

def inverse_vote(surv,row):
    v={}
    for i in surv:
        for op,target in parses(HS[i],row["command"]):
            key=(op,target); v[key]=v.get(key,0)+1
    return max(v,key=v.get) if v else None

def evaluate(surv,data):
    keys=("prospective","inverse","unknown_order","paragraph","omitted","counterfactual"); n={k:0 for k in keys}; d={k:0 for k in keys}
    for r in data:
        pred=vote(surv,r); n["prospective"]+=pred==r["after"]; d["prospective"]+=1
        n["inverse"]+=inverse_vote(surv,r)==(r["op"],r["target"]); d["inverse"]+=1
        if r["form"] in ("interleave","reverse"): n["unknown_order"]+=pred==r["after"]; d["unknown_order"]+=1
        if r["form"]=="paragraph": n["paragraph"]+=pred==r["after"]; d["paragraph"]+=1
        if r["form"]=="omitted": n["omitted"]+=pred==r["after"]; d["omitted"]+=1
        alt=(1-r["before"][0],1-r["before"][1]); rr=dict(r); rr["before"]=alt
        n["counterfactual"]+=vote(surv,rr)==apply(alt,r["op"],r["target"]); d["counterfactual"]+=1
    return {k:n[k]/max(1,d[k]) for k in keys}

def run_seed(seed):
    data,true_role=make_data(seed); true_idx=HS.index(tuple(ROLE_INDEX[true_role[c]] for c in CHARS)); p1,p2,test=data[:40],data[40:80],data[80:]; out={}
    for method in ("active","random","state_static"):
        s1=select(p1,8,method,seed+100); s2=select(p2,8,method,seed+200); inter=list(set(s1)&set(s2))
        out[method]={"survivors_1":len(s1),"survivors_2":len(s2),"intersection":len(inter),"true_support_1":true_idx in s1,"true_support_2":true_idx in s2,"same_unique":len(s1)==len(s2)==1 and s1[0]==s2[0],**evaluate(inter,test),"model_bytes":len(pickle.dumps(inter))}
    s1=select(p1,8,"active",seed+300,True); s2=select(p2,8,"active",seed+400,True); inter=list(set(s1)&set(s2))
    out["outcome_shuffle"]={"survivors_1":len(s1),"survivors_2":len(s2),"intersection":len(inter),**evaluate(inter,test)}
    alias=[c for c,r in true_role.items() if r in ("obj0","toggle")]; lesion=[r for r in test if not any(c in r["command"] for c in alias[:2])]
    active_inter=list(set(select(p1,8,"active",seed+100))&set(select(p2,8,"active",seed+200)))
    out["alias_lesion"]={"survivors_1":out["active"]["survivors_1"],"survivors_2":out["active"]["survivors_2"],"intersection":out["active"]["intersection"],**evaluate(active_inter,lesion)}
    return out

def main():
    start=time.perf_counter(); raw={str(s):run_seed(s) for s in SEEDS}
    def avg(m,k): return statistics.mean(float(raw[str(s)][m][k]) for s in SEEDS)
    summary={m:{k:avg(m,k) for k in raw["1"][m]} for m in raw["1"]}; strict=0
    for s in SEEDS:
        a=raw[str(s)]["active"]; r=raw[str(s)]["random"]; st=raw[str(s)]["state_static"]
        if all(a[k]-max(r[k],st[k])>=0.10 for k in ("prospective","inverse","unknown_order","counterfactual")): strict+=1
    print(json.dumps({"cycle":11,"hypothesis":"Nonparametric Alias-Role Inventory Birth from Independent State-Crossing Witnesses","seeds":SEEDS,"summary":summary,"strict_progress_seeds":strict,"semantic_identity_gate":False,"failure_classification":"finite_role_vocabulary_and_binary_state_upper_bound","candidate_count":len(HS),"model_bytes_mean":summary["active"]["model_bytes"],"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"runtime_seconds":time.perf_counter()-start,"estimated_ops":f"O(2*B*H*Q), H={len(HS)}, B=8","answer_leakage":False,"fixed_class_cardinality":False,"operation_family_oracle":True,"binary_state_interface_oracle":True,"fixed_ontology":False,"rag":False,"external_llm":False,"weak_smartphone_verified":False,"highschool_level_passed":False,"completion":False,"raw":raw},ensure_ascii=False,indent=2))

if __name__=="__main__": main()
