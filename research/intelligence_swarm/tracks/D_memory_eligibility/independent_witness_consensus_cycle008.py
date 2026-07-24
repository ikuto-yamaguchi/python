#!/usr/bin/env python3
from __future__ import annotations
import itertools, random, statistics, json, time, resource
from collections import defaultdict

N=4
SEEDS=(1,7,19)
PERMS=tuple(itertools.permutations(range(N)))
WORLDS=tuple((a,b) for a in PERMS for b in PERMS)
QUERIES=tuple(itertools.product(range(N),range(N)))

def outcome(w,q): return w[0][q[0]], w[1][q[1]]
def filt(vs,q,o): return [w for w in vs if outcome(w,q)==o]
def exp_post(vs,q):
    buckets=defaultdict(int)
    for w in vs: buckets[outcome(w,q)]+=1
    return sum(size*size for size in buckets.values())/len(vs)
def choose(vs, forbidden=()):
    candidates=[q for q in QUERIES if q not in forbidden]
    best=min(exp_post(vs,q) for q in candidates)
    return sorted(q for q in candidates if exp_post(vs,q)==best)[0]
def acquire(true, forbidden=(), budget=3, corrupt_at=None, rng=None):
    vs=list(WORLDS); queries=[]; observations=[]
    for i in range(budget):
        query=choose(vs or WORLDS, tuple(forbidden)+tuple(queries))
        observed=outcome(true,query)
        if corrupt_at==i:
            donors=[outcome(true,item) for item in QUERIES if outcome(true,item)!=observed]
            observed=(rng or random).choice(donors)
        vs=filt(vs,query,observed)
        queries.append(query); observations.append(observed)
        if not vs: break
    return vs,queries,observations
def evaluate(vs,true):
    if len(vs)!=1: return {'joint':0.0,'inverse':0.0,'closed':0.0}
    predicted=vs[0]
    joint=sum(outcome(predicted,q)==outcome(true,q) for q in QUERIES)/len(QUERIES)
    inverse=0
    for latent_target,latent_operation in QUERIES:
        predicted_query=(predicted[0].index(latent_target),predicted[1].index(latent_operation))
        true_query=(true[0].index(latent_target),true[1].index(latent_operation))
        inverse += predicted_query==true_query
    inverse/=len(QUERIES)
    return {'joint':joint,'inverse':inverse,'closed':joint*inverse}
def run(seed):
    rng=random.Random(seed)
    true=(rng.choice(PERMS),rng.choice(PERMS))
    first,q1,o1=acquire(true,budget=3,rng=rng)
    second,q2,o2=acquire(true,forbidden=q1,budget=3,rng=rng)
    single_unique=len(first)==1
    dual_consensus=len(first)==1 and len(second)==1 and first[0]==second[0]
    merged=list(WORLDS)
    for query,observed in list(zip(q1,o1))+list(zip(q2,o2)):
        merged=filt(merged,query,observed)
    corrupted,qc,oc=acquire(true,budget=3,corrupt_at=1,rng=rng)
    merged_corrupt=list(WORLDS)
    for query,observed in list(zip(qc,oc))+list(zip(q2,o2)):
        merged_corrupt=filt(merged_corrupt,query,observed)
    conflict_detected=(len(merged_corrupt)==0 or (len(corrupted)==1 and len(second)==1 and corrupted[0]!=second[0]))
    retained=evaluate(second,true) if dual_consensus and conflict_detected else {'joint':0.0,'inverse':0.0,'closed':0.0}
    return {'single_remaining':len(first),'second_remaining':len(second),'merged_remaining':len(merged),'single_unique':float(single_unique),'dual_consensus':float(dual_consensus),'upper_bound_eligible':float(dual_consensus),'corrupt_first_remaining':len(corrupted),'merged_corrupt_remaining':len(merged_corrupt),'conflict_detected':float(conflict_detected),'retained_joint':retained['joint'],'retained_inverse':retained['inverse'],'retained_closed':retained['closed'],'witnesses_total':len(q1)+len(q2)}
def main():
    started=time.perf_counter()
    raw=[run(seed) for seed in SEEDS]
    mean={key:statistics.mean(item[key] for item in raw) for key in raw[0]}
    payload={'cycle':8,'track':'D_memory_eligibility','hypothesis':'Independent minimal witness-set consensus is required before memory eligibility; contradictory acquisition must be rejected rather than consolidated','seeds':list(SEEDS),'initial_worlds':len(WORLDS),'raw':raw,'mean':mean,'runtime_seconds':time.perf_counter()-started,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'model_bytes_upper_bound':9216,'estimated_probe_simulations_max':len(WORLDS)*len(QUERIES)*6,'answer_leakage':False,'final_test_outcome_used_for_selection':False,'oracle_limitations':['oracle token segmentation','known target-operation factorization','known unary arity','finite permutation world'],'g1_passed':False,'g2_passed':False,'formal_memory_eligibility_passed':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    print(json.dumps(payload,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
