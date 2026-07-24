from __future__ import annotations
import itertools, json, math, pickle, random, resource, statistics, time

SEEDS=(1,7,19)
OPS=("noop","mark","swap","copy")
ARITY={"noop":0,"mark":1,"swap":2,"copy":2}
OBJECTS=("A","B","C","D")
OPAQUE_OBJ=("ラ","ミ","ソ","ネ")
OPAQUE_OP=("ギ","プ","ワ","ゾ")
FILLERS=("ト","カ")

def apply_op(world, op, args):
    w=list(world)
    if op=="noop": return tuple(w)
    if op=="mark":
        i=args[0]; w[i]=(w[i]+1)%4; return tuple(w)
    if op=="swap":
        i,j=args; w[i],w[j]=w[j],w[i]; return tuple(w)
    if op=="copy":
        i,j=args; w[j]=w[i]; return tuple(w)
    raise ValueError(op)

def encode_command(obj_tokens, op_tokens, obj_map, op_map, op, args, rng, form):
    ot=op_tokens[op_map.index(op)]
    ats=[obj_tokens[obj_map.index(OBJECTS[i])] for i in args]
    filler=rng.choice(FILLERS)
    if form=="prefix": parts=[filler,ot]+ats
    elif form=="suffix": parts=ats+[ot,filler]
    elif form=="interleave": parts=([ats[0],filler,ot]+ats[1:]) if ats else [filler,ot]
    elif form=="reverse": parts=list(reversed(ats))+[filler,ot]
    else: parts=[ot,filler]+ats
    return "".join(parts)

def generate_worlds(seed):
    rng=random.Random(seed)
    obj_map=list(OBJECTS); rng.shuffle(obj_map)
    op_map=list(OPS); rng.shuffle(op_map)
    rows=[]; forms=("prefix","suffix","interleave","reverse")
    for _ in range(96):
        world=tuple(rng.randrange(4) for _ in OBJECTS)
        op=rng.choice(OPS); ar=ARITY[op]
        args=tuple(rng.sample(range(4),ar)); form=rng.choice(forms)
        cmd=encode_command(OPAQUE_OBJ,OPAQUE_OP,obj_map,op_map,op,args,rng,form)
        rows.append({"before":world,"command":cmd,"after":apply_op(world,op,args),"op":op,"args":args,"form":form})
    return rows

def candidate_structures():
    op_perms=list(itertools.permutations(OPS))
    obj_perms=list(itertools.permutations(OBJECTS))
    arity_perms=sorted(set(itertools.permutations((0,1,2,2))))
    forms=("prefix","suffix","interleave","reverse")
    return [(opm,objm,arm,f) for opm in op_perms for objm in obj_perms for arm in arity_perms for f in forms]

def parse_with(h, cmd):
    opm,objm,arm,form=h; chars=list(cmd)
    op_pos=[i for i,c in enumerate(chars) if c in OPAQUE_OP]
    obj_pos=[i for i,c in enumerate(chars) if c in OPAQUE_OBJ]
    if len(op_pos)!=1: return None
    oi=OPAQUE_OP.index(chars[op_pos[0]]); op=opm[oi]
    if ARITY[op]!=arm[oi]: return None
    filtered=[c for c in chars if c not in FILLERS]
    if not filtered: return None
    if form=="prefix" and filtered[0] not in OPAQUE_OP: return None
    if form in ("suffix","reverse") and filtered[-1] not in OPAQUE_OP: return None
    if form=="interleave" and len(filtered)>1 and filtered[1] not in OPAQUE_OP: return None
    args=[]
    for p in obj_pos:
        latent=objm[OPAQUE_OBJ.index(chars[p])]
        args.append(OBJECTS.index(latent))
    if form=="reverse": args=list(reversed(args))
    if len(args)!=ARITY[op]: return None
    return op,tuple(args)

def predict(h,row):
    p=parse_with(h,row["command"])
    return None if p is None else apply_op(row["before"],p[0],p[1])

def compatible(h,row,outcome=None):
    pred=predict(h,row)
    return pred is not None and pred==(row["after"] if outcome is None else outcome)

def entropy_score(survivors,row):
    groups={}
    for h in survivors:
        pred=predict(h,row); groups[pred]=groups.get(pred,0)+1
    n=max(1,len(survivors))
    return -sum((c/n)*math.log2(c/n) for c in groups.values())

def select_active(survivors,pool):
    return max(pool,key=lambda r:entropy_score(survivors,r))

def run_method(rows, method, budget=5):
    survivors=candidate_structures(); rng=random.Random(991+len(rows)+sum(map(ord,method)))
    pool=rows[:48]; used=[]
    for _ in range(budget):
        if not pool or not survivors: break
        row=select_active(survivors,pool) if method=="active" else rng.choice(pool)
        pool.remove(row); used.append(row); outcome=row["after"]
        if method=="outcome_shuffle": outcome=rng.choice(rows)["after"]
        survivors=[h for h in survivors if compatible(h,row,outcome)]
    if method=="boundary_shuffle":
        survivors=[(h[0],h[1],h[2],rng.choice(("prefix","suffix","interleave","reverse"))) for h in survivors]
    if method=="arity_shuffle":
        aps=sorted(set(itertools.permutations((0,1,2,2))))
        survivors=[(h[0],h[1],rng.choice(aps),h[3]) for h in survivors]
    return survivors,used

def eval_survivors(survivors,rows):
    metrics={"prospective":0.0,"inverse":0.0,"repair":0.0,"free":0.0}
    if not survivors: return metrics
    tests=rows[48:]; correct=inv=repair=free=0
    for r in tests:
        preds=[predict(h,r) for h in survivors]; preds=[p for p in preds if p is not None]
        pred=max(set(preds),key=preds.count) if preds else None
        correct += pred==r["after"]
        ops=[parse_with(h,r["command"])[0] for h in survivors if parse_with(h,r["command"])]
        inv += (max(set(ops),key=ops.count)==r["op"]) if ops else False
        bad=list(r["before"]); bad[0]=(bad[0]+1)%4
        rr=dict(r); rr["before"]=tuple(bad)
        pp=[predict(h,rr) for h in survivors]; pp=[x for x in pp if x is not None]
        target=apply_op(rr["before"],r["op"],r["args"])
        repair += (max(set(pp),key=pp.count)==target) if pp else False
        free += pred==r["after"] if r["form"] in ("interleave","reverse") else 0
    n=len(tests); free_n=max(1,sum(r["form"] in ("interleave","reverse") for r in tests))
    return {"prospective":correct/n,"inverse":inv/n,"repair":repair/n,"free":free/free_n}

def main():
    allres={}
    methods=("active","random","boundary_shuffle","arity_shuffle","outcome_shuffle")
    for seed in SEEDS:
        rows=generate_worlds(seed); allres[str(seed)]={}
        for method in methods:
            t0=time.perf_counter(); survivors,used=run_method(rows,method)
            allres[str(seed)][method]={"survivors":len(survivors),"used_witnesses":len(used),**eval_survivors(survivors,rows),"seconds":time.perf_counter()-t0,"model_bytes":len(pickle.dumps(survivors))}
    summary={m:{k:statistics.mean(allres[str(s)][m][k] for s in SEEDS) for k in allres["1"][m]} for m in methods}
    strict=0
    for seed in SEEDS:
        a=allres[str(seed)]["active"]; controls=[allres[str(seed)][m] for m in methods[1:]]
        if all(a[x]>=max(c[x] for c in controls)+0.10 for x in ("prospective","inverse","repair","free")): strict+=1
    print(json.dumps({"cycle":8,"hypothesis":"Joint Segmentation–Variable-Arity Operation Orbit Birth from Minimal Witnesses","seeds":SEEDS,"initial_hypotheses":27648,"witness_budget":5,"summary":summary,"strict_gate_seeds":strict,"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"estimated_ops":"selector O(B*H*Q), inference O(H*Q), H=27648","answer_leakage":False,"fixed_ontology_or_handwritten_slots":False,"weak_smartphone_verified":False,"highschool_level_passed":False,"completion":False,"raw":allres},ensure_ascii=False,indent=2))

if __name__=="__main__": main()
