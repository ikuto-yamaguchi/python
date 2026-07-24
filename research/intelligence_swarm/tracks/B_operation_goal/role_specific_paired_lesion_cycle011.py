from __future__ import annotations
import random, time, json, pickle, resource, statistics
from collections import defaultdict, Counter

SEEDS=(1,7,19)
FORMS=("seen","paraphrase","order","nested","paragraph","free")
OPS=("copy","swap","set0","set1")

def apply(w, op, a, b, goal):
    w=list(w)
    if op=="copy": w[a]=w[b]
    elif op=="swap": w[a],w[b]=w[b],w[a]
    elif op=="set0": w[a]=0
    elif op=="set1": w[a]=1
    return tuple(w)

def lexicon(seed, domain):
    rng=random.Random(seed*97+domain*1009)
    chars=list("亜伊宇江尾加幾久計己佐志須世曽")
    rng.shuffle(chars)
    return {"obj":chars[:3],"op":chars[3:7],"goal":chars[7:9],"noise":chars[9:]}

def utter(lex, opi,a,b,goal,form,rng):
    o1=lex["obj"][a]; o2=lex["obj"][b]; op=lex["op"][opi]; g=lex["goal"][goal]
    n1,n2=rng.sample(lex["noise"],2)
    forms={
      "seen":[n1,o1,op,o2,g,n2], "paraphrase":[g,n1,op,o1,n2,o2],
      "order":[o2,g,n2,o1,op,n1], "nested":[n1,n2,o1,g,op,o2],
      "paragraph":[o1,"\n",n1,op,"\n",o2,g,n2], "free":[n2,g,o2,n1,op,o1]}
    return "".join(forms[form])

def make(seed,domain,n=240):
    rng=random.Random(seed+domain*10000); lex=lexicon(seed,domain); rows=[]
    for _ in range(n):
        before=tuple(rng.randrange(2) for _ in range(3)); opi=rng.randrange(4); a=rng.randrange(3)
        b=rng.choice([x for x in range(3) if x!=a]); goal=rng.randrange(2); form=rng.choice(FORMS)
        rows.append({"before":before,"after":apply(before,OPS[opi],a,b,goal),
          "cmd":utter(lex,opi,a,b,goal,form,rng),"op":opi,"a":a,"b":b,"goal":goal,"form":form})
    return rows

def delta(before,after): return tuple(after[i]-before[i] for i in range(3))

def paired_role_candidates(rows, method, seed):
    rng=random.Random(seed); by=defaultdict(list)
    for r in rows: by[(r["before"],r["form"])].append(r)
    votes=defaultdict(Counter); trials=0
    for group in by.values():
      for i,x in enumerate(group):
       for y in group[i+1:]:
        diffs=sum([x["op"]!=y["op"],x["a"]!=y["a"],x["b"]!=y["b"],x["goal"]!=y["goal"]])
        if diffs!=1: continue
        changed=frozenset(set(x["cmd"].replace("\n",""))^set(y["cmd"].replace("\n","")))
        if not changed or len(changed)>4: continue
        dx=delta(x["before"],x["after"]); dy=delta(y["before"],y["after"])
        response=tuple(dy[k]-dx[k] for k in range(3))
        if method in ("pair_shuffle","outcome_shuffle"): response=tuple(rng.sample(list(response),3))
        factor=("op" if x["op"]!=y["op"] else "target" if x["a"]!=y["a"] else "source" if x["b"]!=y["b"] else "goal")
        votes[changed][(factor,response)]+=1; trials+=1
    cands=[]
    for tokset,c in votes.items():
        total=sum(c.values()); (fr,resp),support=c.most_common(1)[0]; purity=support/total
        if method=="random": purity*=rng.random()
        if method=="state_static": purity*=0.35
        if purity>=0.55 and support>=2:
            cands.append({"tokens":tuple(sorted(tokset)),"factor":fr,"response":resp,"support":support,"purity":purity})
    cands.sort(key=lambda z:(z["purity"],z["support"]),reverse=True)
    return cands[:128],trials

def infer(cands,row):
    chars=set(row["cmd"].replace("\n","")); active=[c for c in cands if set(c["tokens"])<=chars]
    groups={r:sorted([c for c in active if c["factor"]==r],key=lambda x:(x["purity"],x["support"]),reverse=True)
            for r in ("op","target","source","goal")}
    if not groups["op"] or not groups["target"]: return None,None,None
    candidates=[]
    for opi in range(4):
     for a in range(3):
      for b in range(3):
       if a==b: continue
       for goal in range(2):
        aft=apply(row["before"],OPS[opi],a,b,goal); d=delta(row["before"],aft)
        score=-sum((d[i]-groups["op"][0]["response"][i])**2 for i in range(3))
        score+=0.01*(groups["op"][0]["support"]+groups["target"][0]["support"])
        candidates.append((score,aft,(opi,a,b,goal)))
    candidates.sort(reverse=True)
    if len(candidates)>1 and abs(candidates[0][0]-candidates[1][0])<1e-12: return None,None,None
    return candidates[0][1],candidates[0][2],len(candidates)

def evaluate(cands,rows):
    out=Counter(); candn=[]
    for r in rows:
        aft,inv,k=infer(cands,r); out["prospective"]+=aft==r["after"]
        out["inverse"]+=inv==(r["op"],r["a"],r["b"],r["goal"])
        out["goal"]+=(inv is not None and inv[0]==r["op"] and inv[3]==r["goal"])
        if inv is not None:
            out["repair"]+=apply(r["before"],OPS[inv[0]],inv[1],inv[2],1-r["goal"])==apply(r["before"],OPS[r["op"]],r["a"],r["b"],1-r["goal"])
        out["abstain"]+=aft is None
        if k: candn.append(k)
    n=max(1,len(rows))
    return {k:out[k]/n for k in ("prospective","inverse","goal","repair","abstain")}|{"candidate_rollouts":statistics.mean(candn) if candn else 0}

def run():
    t0=time.perf_counter(); raw={}; methods=("paired","random","state_static","pair_shuffle","outcome_shuffle")
    for seed in SEEDS:
      raw[str(seed)]={}
      for method in methods:
       domains=[]
       for domain in (0,1):
        rows=make(seed,domain); cands,trials=paired_role_candidates(rows[:150],method,seed+domain)
        domains.append({"candidates":len(cands),"trials":trials,"model_bytes":len(pickle.dumps(cands)),
          "forms":{form:evaluate(cands,[r for r in rows[150:] if r["form"]==form]) for form in FORMS}})
       raw[str(seed)][method]=domains
    summary={}
    for method in methods:
      summary[method]={"candidates":statistics.mean(raw[str(s)][method][d]["candidates"] for s in SEEDS for d in (0,1)),
       "model_bytes":statistics.mean(raw[str(s)][method][d]["model_bytes"] for s in SEEDS for d in (0,1)),
       "trials":statistics.mean(raw[str(s)][method][d]["trials"] for s in SEEDS for d in (0,1))}
      for form in FORMS:
       summary[method][form]={k:statistics.mean(raw[str(s)][method][d]["forms"][form][k] for s in SEEDS for d in (0,1))
        for k in raw["1"][method][0]["forms"][form]}
    return {"cycle":11,"hypothesis":"Role-Specific Paired Lesion Birth without Enumerated Programs","seeds":SEEDS,
     "summary":summary,"strict_progress_seeds":0,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
     "runtime_seconds":time.perf_counter()-t0,"estimated_complexity":"pair generation O(N^2 L), inference O(C*36)",
     "answer_leakage":False,"under_1gb":True,"weak_smartphone_verified":False,"semantic_identity_gate":False,
     "operation_goal_gate":False,"formal_operation_proposals":0,"highschool_level_passed":False,"completion":False,"raw":raw}

if __name__=="__main__": print(json.dumps(run(),ensure_ascii=False,indent=2))
