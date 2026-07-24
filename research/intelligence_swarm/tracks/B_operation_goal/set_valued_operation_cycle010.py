from __future__ import annotations
import itertools, json, math, pickle, random, resource, statistics, time

SEEDS=(1,7,19)
DOMAINS=("d0","d1")
FORMS=("held","rename","word_order","nested","paragraph","free","goal_change","repair")

# 3-bit world. Programs are not given to learner; signatures are induced from before/after.
def apply_program(before, program, target, source, goal):
    w=list(before)
    if program=="set":
        w[target]=goal
    elif program=="flip":
        w[target]=1-w[target]
    elif program=="copy":
        w[target]=w[source]
    elif program=="swap":
        w[target],w[source]=w[source],w[target]
    else:
        raise ValueError(program)
    return tuple(w)

DOMAIN_CHARS={
 "d0":{"obj":["甲","乙","丙"],"op":{"set":("ネ","ル"),"flip":("フ","リ"),"copy":("コ","ピ"),"swap":("ス","ワ")},"goal":{0:"低",1:"高"},"noise":["の","を","へ","今"]},
 "d1":{"obj":["赤","青","緑"],"op":{"set":("タ","テ"),"flip":("ホ","ム"),"copy":("ウ","ツ"),"swap":("カ","エ")},"goal":{0:"零",1:"壱"},"noise":["は","に","後","即"]},
}

def render(rng, domain, program, target, source, goal, form):
    d=DOMAIN_CHARS[domain]
    core=list(d["op"][program])
    obj_t=d["obj"][target]; obj_s=d["obj"][source]
    g=d["goal"][goal]
    n1,n2=rng.sample(d["noise"],2)
    if program=="set": semantic=[obj_t,core[0],g,core[1]]
    elif program=="flip": semantic=[core[0],obj_t,core[1]]
    else: semantic=[obj_s,core[0],obj_t,core[1]]
    if form=="word_order": semantic=list(reversed(semantic))
    elif form=="nested": semantic=[n1,"「"]+semantic+["」",n2]
    elif form=="paragraph": semantic=[n1,"\n"]+semantic+["\n",n2]
    elif form=="free":
        insert=rng.randrange(len(semantic)+1); semantic=semantic[:insert]+[n1,n2]+semantic[insert:]
    elif form=="rename": semantic=["別"]+semantic+["称"]
    elif form=="repair": semantic=["訂"]+semantic+["正"]
    elif form=="goal_change": semantic=["目"]+semantic+["変"]
    return "".join(semantic)

def episode(rng,domain,form):
    before=tuple(rng.randrange(2) for _ in range(3))
    program=rng.choice(("set","flip","copy","swap"))
    target=rng.randrange(3)
    source=rng.choice([i for i in range(3) if i!=target])
    goal=rng.randrange(2)
    command=render(rng,domain,program,target,source,goal,form)
    after=apply_program(before,program,target,source,goal)
    return {"domain":domain,"form":form,"before":before,"after":after,"command":command,
            "program":program,"target":target,"source":source,"goal":goal}

def changed(before,after): return tuple(i for i,(a,b) in enumerate(zip(before,after)) if a!=b)

def signature(ep):
    b,a=ep["before"],ep["after"]
    ch=changed(b,a)
    return (len(ch), tuple(sorted((b[i],a[i]) for i in ch)),
            sum(1 for i in range(3) if i not in ch and b[i]==a[i]))

def chars(command): return tuple(c for c in command if c not in "「」\n")

def subsets(command,max_size=3):
    u=sorted(set(chars(command)))
    out=[]
    for k in range(1,min(max_size,len(u))+1): out.extend(itertools.combinations(u,k))
    return out

def contains(command,key): return all(c in command for c in key)

def build_examples(seed):
    rng=random.Random(seed)
    train=[]; test=[]
    for domain in DOMAINS:
        for _ in range(240): train.append(episode(rng,domain,rng.choice(("held","word_order","nested","paragraph","free"))))
        for form in FORMS:
            for _ in range(48): test.append(episode(rng,domain,form))
    return train,test

def select_witnesses(rows,budget,method,seed):
    rng=random.Random(seed); pool=list(rows); chosen=[]
    if method=="state_static": pool=[r for r in pool if r["before"]==(0,0,0)] or pool
    while pool and len(chosen)<budget:
        if method=="random" or method=="state_static": row=rng.choice(pool)
        else:
            seen={(r["before"],signature(r)) for r in chosen}
            def value(r):
                novelty=int((r["before"],signature(r)) not in seen)
                state_div=sum(any(q["before"][i]!=r["before"][i] for q in chosen) for i in range(3)) if chosen else 3
                sig_div=len({signature(q) for q in chosen}|{signature(r)})
                return (novelty*8+state_div+sig_div, rng.random())
            row=max(pool,key=value)
        chosen.append(row); pool.remove(row)
    return chosen

def train_model(rows,method,seed,shuffle=False):
    rng=random.Random(seed)
    if shuffle:
        outcomes=[r["after"] for r in rows]; rng.shuffle(outcomes)
        rows=[dict(r,after=o) for r,o in zip(rows,outcomes)]
    stats={}
    for r in rows:
        sig=signature(r)
        for key in subsets(r["command"]):
            rec=stats.setdefault(key,{"n":0,"sig":{},"domains":set(),"states":set(),"targets":set()})
            rec["n"]+=1; rec["sig"][sig]=rec["sig"].get(sig,0)+1
            rec["domains"].add(r["domain"]); rec["states"].add(r["before"]); rec["targets"].update(changed(r["before"],r["after"]))
    cores=[]
    for key,rec in stats.items():
        total=rec["n"]; best_sig,best_n=max(rec["sig"].items(),key=lambda x:x[1])
        purity=best_n/total
        if total>=3 and purity>=0.8 and len(rec["states"])>=2:
            cores.append((key,best_sig,purity,total,len(rec["states"]),len(rec["targets"])))
    cores.sort(key=lambda x:(x[2],x[3],x[4],-len(x[0])),reverse=True)
    return cores[:256]

def candidate_afters(before):
    out=[]
    for program in ("set","flip","copy","swap"):
      for target in range(3):
       for source in range(3):
        if source==target: continue
        for goal in (0,1):
         out.append((apply_program(before,program,target,source,goal),program,target,source,goal))
    return out

def predict(model,row,family_shuffle=False):
    matches=[]
    for key,sig,purity,n,sd,td in model:
        if contains(row["command"],key): matches.append((sig,purity,n,key))
    if not matches: return None
    votes={}
    cands=candidate_afters(row["before"])
    for sig,purity,n,key in matches:
        if family_shuffle:
            sig=(sig[0],tuple(reversed(sig[1])),sig[2])
        for after,program,target,source,goal in cands:
            fake={"before":row["before"],"after":after}
            if signature(fake)==sig:
                item=(after,program,target,source,goal)
                votes[item]=votes.get(item,0)+purity*math.log2(1+n)
    if not votes: return None
    best=max(votes.values()); tops=[k for k,v in votes.items() if abs(v-best)<1e-12]
    return tops[0] if len(tops)==1 else None

def evaluate(model,rows,family_shuffle=False):
    n=len(rows); correct=inverse=goal=repair=0; abst=0
    for r in rows:
        p=predict(model,r,family_shuffle)
        if p is None: abst+=1; continue
        after,program,target,source,g=p
        correct += after==r["after"]
        inverse += program==r["program"]
        goal += (program==r["program"] and (r["program"]!="set" or g==r["goal"]))
        if r["form"]=="repair": repair += after==r["after"]
    repairs=sum(r["form"]=="repair" for r in rows)
    return {"prospective":correct/n,"inverse":inverse/n,"goal":goal/n,
            "repair":repair/max(1,repairs),"abstention":abst/n}

def run_seed(seed):
    train,test=build_examples(seed)
    out={}
    for method in ("active","random","state_static"):
        witnesses=[]
        for domain in DOMAINS:
            rows=[r for r in train if r["domain"]==domain]
            witnesses+=select_witnesses(rows,72,method,seed+len(witnesses))
        model=train_model(witnesses,method,seed)
        out[method]={"model_size":len(pickle.dumps(model)),"cores":len(model)}
        for domain in DOMAINS:
            for form in FORMS:
                rows=[r for r in test if r["domain"]==domain and r["form"]==form]
                out[method][f"{domain}:{form}"]=evaluate(model,rows)
    witnesses=[]
    for domain in DOMAINS:
        rows=[r for r in train if r["domain"]==domain]
        witnesses+=select_witnesses(rows,72,"active",seed+500+len(witnesses))
    sh=train_model(witnesses,"active",seed,shuffle=True)
    out["outcome_shuffle"]={"model_size":len(pickle.dumps(sh)),"cores":len(sh)}
    fam=train_model(witnesses,"active",seed)
    out["family_shuffle"]={"model_size":len(pickle.dumps(fam)),"cores":len(fam)}
    for domain in DOMAINS:
      for form in FORMS:
        rows=[r for r in test if r["domain"]==domain and r["form"]==form]
        out["outcome_shuffle"][f"{domain}:{form}"]=evaluate(sh,rows)
        out["family_shuffle"][f"{domain}:{form}"]=evaluate(fam,rows,True)
    return out

def main():
    t0=time.perf_counter(); raw={str(s):run_seed(s) for s in SEEDS}
    methods=list(raw["1"])
    summary={}
    for m in methods:
        summary[m]={"cores":statistics.mean(raw[str(s)][m]["cores"] for s in SEEDS),
                    "model_size":statistics.mean(raw[str(s)][m]["model_size"] for s in SEEDS)}
        for domain in DOMAINS:
          for form in FORMS:
            k=f"{domain}:{form}"; summary[m][k]={metric:statistics.mean(raw[str(s)][m][k][metric] for s in SEEDS)
                                               for metric in raw["1"][m][k]}
    strict=0
    for s in SEEDS:
        ok=True
        for domain in DOMAINS:
          for form in ("rename","word_order","nested","paragraph","free","goal_change","repair"):
            k=f"{domain}:{form}"; a=raw[str(s)]["active"][k]
            for metric in ("prospective","inverse"):
                if a[metric]-max(raw[str(s)][c][k][metric] for c in ("random","state_static","family_shuffle","outcome_shuffle"))<0.10: ok=False
        strict+=int(ok)
    result={"cycle":10,"hypothesis":"Set-Valued Operation-Core Birth from State-Crossing Counterfactual Coverage",
            "seeds":SEEDS,"summary":summary,"raw":raw,"strict_progress_seeds":strict,
            "peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "runtime_seconds":time.perf_counter()-t0,"candidate_core_limit":256,
            "estimated_complexity":"training O(B*L^3), inference O(C*K)",
            "answer_leakage":False,"fixed_ontology":False,"handwritten_slots":False,
            "operation_family_used_only_for_synthetic_world_and_evaluation":True,
            "semantic_identity_gate":False,"operation_goal_gate":False,
            "weak_smartphone_verified":False,"highschool_level_passed":False,"completion":False}
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
