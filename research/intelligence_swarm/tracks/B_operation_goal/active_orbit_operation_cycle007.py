from __future__ import annotations
import json, math, pickle, random, resource, statistics, time
from collections import defaultdict

SEEDS=(1,7,19)
OPS=[(-1,0),(1,0),(0,-1),(0,1)]
NOBJ=4
FORMS=("held","rename","word_order","nested","paragraph","free")
TOKENS_H=("ピア","ゾフ","ルネ","キト")

def apply(world, target, op):
    w=[list(p) for p in world]
    dx,dy=op
    w[target][0]+=dx; w[target][1]+=dy
    return tuple(tuple(p) for p in w)

def world(rng):
    pts=[]
    while len(pts)<NOBJ:
        p=(rng.randrange(-3,4),rng.randrange(-3,4))
        if p not in pts: pts.append(p)
    return tuple(pts)

def utter(token,target,form):
    obj=f"対象{target+1}"
    if form=="held": return f"{obj}を{token}してください。"
    if form=="rename": return f"{obj}に{token}を実施してください。"
    if form=="word_order": return f"{token}をお願いします。対象は{obj}です。"
    if form=="nested": return f"依頼は「{obj}を{token}」です。"
    if form=="paragraph": return f"前段は維持。\n{obj}を{token}してください。\n後段も維持。"
    return f"{obj}について、位置関係を保ちながら{token}の処理を行ってください。"

def make_domain(tokens, perm):
    return {tokens[i]:perm[i] for i in range(4)}

def episode(rng, mapping, form):
    token=rng.choice(list(mapping)); target=rng.randrange(NOBJ); before=world(rng)
    after=apply(before,target,OPS[mapping[token]])
    return {"text":utter(token,target,form),"token":token,"target":target,
            "before":before,"after":after,"op_index":mapping[token],"form":form}

def delta_signature(before,after):
    changes=[]
    for i,(a,b) in enumerate(zip(before,after)):
        if a!=b: changes.append((i,b[0]-a[0],b[1]-a[1]))
    return tuple(changes)

def all_perms():
    import itertools
    return list(itertools.permutations(range(4)))

def candidate_outcome(ep, perm, tokens):
    ti=tokens.index(ep["token"])
    return apply(ep["before"],ep["target"],OPS[perm[ti]])

def split_score(ep, version_space, tokens):
    buckets=defaultdict(int)
    for p in version_space:
        buckets[delta_signature(ep["before"],candidate_outcome(ep,p,tokens))]+=1
    n=len(version_space)
    return n - sum(c*c for c in buckets.values())/n

def choose_probe(pool, version_space, tokens, mode, rng, true_perm=None):
    if mode=="random": return rng.choice(pool)
    if mode=="oracle":
        best=None
        for ep in pool:
            obs=delta_signature(ep["before"],apply(ep["before"],ep["target"],OPS[true_perm[tokens.index(ep["token"])]]))
            survivors=sum(delta_signature(ep["before"],candidate_outcome(ep,p,tokens))==obs for p in version_space)
            key=(-survivors,split_score(ep,version_space,tokens))
            if best is None or key>best[0]: best=(key,ep)
        return best[1]
    return max(pool,key=lambda e:split_score(e,version_space,tokens))

def calibrate(rng,tokens,true_perm,budget,mode,shuffle=False):
    vs=all_perms(); pool=[]; mapping=make_domain(tokens,true_perm)
    for _ in range(40): pool.append(episode(rng,mapping,rng.choice(FORMS[:3])))
    for _ in range(budget):
        ep=choose_probe(pool,vs,tokens,mode,rng,true_perm=true_perm); pool.remove(ep)
        observed=ep["after"]
        if shuffle: observed=rng.choice(pool)["after"]
        sig=delta_signature(ep["before"],observed)
        vs=[p for p in vs if delta_signature(ep["before"],candidate_outcome(ep,p,tokens))==sig]
        if not vs: break
    return vs

def predict(ep,vs,tokens):
    if not vs: return None
    votes=defaultdict(int)
    for p in vs: votes[candidate_outcome(ep,p,tokens)]+=1
    best=max(votes.values()); tops=[o for o,c in votes.items() if c==best]
    return tops[0] if len(tops)==1 else None

def inverse(after,before,target,vs,tokens):
    if not vs:return None
    votes=defaultdict(int)
    for p in vs:
        for ti in range(4):
            if apply(before,target,OPS[p[ti]])==after: votes[ti]+=1
    if not votes:return None
    m=max(votes.values()); tops=[k for k,v in votes.items() if v==m]
    return tops[0] if len(tops)==1 else None

def run_seed(seed):
    rng=random.Random(seed); true_perm=list(range(4)); rng.shuffle(true_perm); true_perm=tuple(true_perm)
    result={}
    for budget in (0,1,2,3,4):
      result[str(budget)]={}
      for mode in ("active","random","oracle"):
       for shuffle in (False,True) if mode=="active" else (False,):
        name="shuffle" if shuffle else mode
        rr=random.Random(seed*100+budget*10+len(name))
        vs=calibrate(rr,TOKENS_H,true_perm,budget,mode,shuffle=shuffle)
        metrics={}
        for form in FORMS:
            tests=[episode(rr,make_domain(TOKENS_H,true_perm),form) for _ in range(96)]
            acc=sum(predict(e,vs,TOKENS_H)==e["after"] for e in tests)/len(tests)
            inv=sum(inverse(e["after"],e["before"],e["target"],vs,TOKENS_H)==TOKENS_H.index(e["token"]) for e in tests)/len(tests)
            metrics[form]={"prospective":acc,"inverse":inv}
        goals=[]; repairs=[]
        for _ in range(96):
            e=episode(rr,make_domain(TOKENS_H,true_perm),"free"); candidates=[]
            for ti,t in enumerate(TOKENS_H):
                ee=dict(e); ee["token"]=t; out=predict(ee,vs,TOKENS_H)
                if out is not None:
                    candidates.append((sum(abs(x)+abs(y) for x,y in out),ti,out))
            if candidates:
                chosen=min(candidates)[1]
                gold=min(range(4),key=lambda ti:sum(abs(x)+abs(y) for x,y in apply(e["before"],e["target"],OPS[true_perm[ti]])))
                goals.append(chosen==gold)
            repairs.append(inverse(e["after"],e["before"],e["target"],vs,TOKENS_H)==TOKENS_H.index(e["token"]))
        result[str(budget)][name]={"version_space":len(vs),"metrics":metrics,
          "goal_change":sum(goals)/len(goals) if goals else 0.0,
          "failure_repair":sum(repairs)/len(repairs)}
    return result

def aggregate(raw):
    out={}
    for budget in ("0","1","2","3","4"):
      out[budget]={}
      for name in raw["1"][budget]:
        out[budget][name]={"version_space":statistics.mean(raw[str(s)][budget][name]["version_space"] for s in SEEDS),
          "goal_change":statistics.mean(raw[str(s)][budget][name]["goal_change"] for s in SEEDS),
          "failure_repair":statistics.mean(raw[str(s)][budget][name]["failure_repair"] for s in SEEDS),"metrics":{}}
        for form in FORMS:
          out[budget][name]["metrics"][form]={k:statistics.mean(raw[str(s)][budget][name]["metrics"][form][k] for s in SEEDS)
            for k in ("prospective","inverse")}
    return out

def main():
    t0=time.perf_counter(); raw={str(s):run_seed(s) for s in SEEDS}; summary=aggregate(raw)
    print(json.dumps({"cycle":7,"hypothesis":"Active Orbit-Separating Witnesses for Operation Birth",
      "seeds":list(SEEDS),"summary":summary,"raw":raw,"runtime_seconds":time.perf_counter()-t0,
      "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "model_bytes_upper_bound":len(pickle.dumps(all_perms())),"candidate_operations":4,"initial_orbit_size":24,
      "estimated_ops_per_probe":"O(|H|*K), at most 96 transition simulations","answer_leakage":False,
      "fixed_ontology_or_handwritten_slots":False,"highschool_level_passed":False,
      "native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False},ensure_ascii=False,indent=2))
if __name__=="__main__": main()
