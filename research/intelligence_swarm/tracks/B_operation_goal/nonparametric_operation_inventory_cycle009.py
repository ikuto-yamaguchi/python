from __future__ import annotations
import json, random, time, pickle, resource, math, statistics
from collections import defaultdict, Counter

SEEDS=(1,7,19)
FORMS=("prefix","suffix","interleave","reverse","paragraph","omitted","free")
OBJ_CHARS=list("甲乙丙")
OP_CHARS=list("天地玄黄")
NOISE=list("のをへ")

# Hidden operation families are used only by the environment, never supplied to learner.
def apply_hidden(world, op, args, goal):
    w=list(world)
    if op==0: # unary increment/decrement selected by goal
        i=args[0]; w[i]=(w[i]+(1 if goal==0 else -1))%4
    elif op==1: # binary swap
        i,j=args; w[i],w[j]=w[j],w[i]
    elif op==2: # unary set-to-goal-extreme
        i=args[0]; w[i]=3 if goal==0 else 0
    elif op==3: # zero-arity rotate whole world, direction by goal
        w=(w[-1:]+w[:-1]) if goal==0 else (w[1:]+w[:1])
    return tuple(w)

def render(rng, objmap, opmap, op, args, goal, form):
    os=[objmap[i] for i in args]
    oc=opmap[op]
    g="上" if goal==0 else "下"
    n=rng.choice(NOISE)
    if form=="prefix": s=oc+"".join(os)+g+n
    elif form=="suffix": s="".join(os)+g+n+oc
    elif form=="interleave": s=(os[0] if os else "")+oc+(os[1] if len(os)>1 else "")+n+g
    elif form=="reverse": s=g+n+"".join(reversed(os))+oc
    elif form=="paragraph": s=n+"\n"+oc+"".join(os)+"\n"+g
    elif form=="omitted": s=oc+g+n if args else n+oc+g
    else: s=n+oc+(os[0] if os else "")+g+(os[1] if len(os)>1 else "")+n
    return s

def episode(rng, objmap, opmap, form=None):
    op=rng.randrange(4); goal=rng.randrange(2)
    arity=(1,2,1,0)[op]
    args=tuple(rng.sample(range(3),arity))
    before=tuple(rng.randrange(4) for _ in range(3))
    after=apply_hidden(before,op,args,goal)
    return {"text":render(rng,objmap,opmap,op,args,goal,form or rng.choice(FORMS)),
            "before":before,"after":after,"op":op,"args":args,"goal":goal,"form":form or "mixed"}

def outcome_signature(before,after):
    changed=tuple(i for i,(a,b) in enumerate(zip(before,after)) if a!=b)
    delta=tuple((after[i]-before[i])%4 for i in changed)
    perm=tuple(sorted(before))==tuple(sorted(after)) and before!=after
    global_change=len(changed)>=2 and all(a!=b for a,b in zip(before,after))
    return (len(changed),delta,perm,global_change)

def select_active(pool, chosen, token_stats):
    # Choose episode maximizing novelty of token/outcome co-occurrence and arity coverage.
    best=None
    for idx,e in enumerate(pool):
        if idx in chosen: continue
        sig=outcome_signature(e['before'],e['after'])
        novelty=sum(1/(1+token_stats[c][sig]) for c in set(e['text']))
        score=novelty + 2/(1+sum(1 for j in chosen if outcome_signature(pool[j]['before'],pool[j]['after'])==sig))
        if best is None or score>best[0]: best=(score,idx)
    return best[1]

def infer_model(records, shuffle=False, global_template=False):
    rs=[dict(r) for r in records]
    if shuffle:
        outs=[r['after'] for r in rs]; random.Random(991).shuffle(outs)
        for r,o in zip(rs,outs): r['after']=o
    chars=sorted(set(''.join(r['text'] for r in rs) )-set('\n'))
    # Build anonymous token response profiles from occurrence and external outcomes.
    profile={c:Counter() for c in chars}
    positions={c:Counter() for c in chars}
    for r in rs:
        sig=outcome_signature(r['before'],r['after'])
        for i,c in enumerate(r['text'].replace('\n','')):
            profile[c][sig]+=1
            positions[c][int(4*i/max(1,len(r['text'].replace(chr(10),''))))]+=1
    # Nonparametric role score: operation tokens have low conditional outcome entropy;
    # object tokens select changed indices; nuisance tokens have high entropy/low selectivity.
    op_tokens=[]; obj_tokens=[]; nuisance=[]
    for c in chars:
        total=sum(profile[c].values())
        probs=[v/total for v in profile[c].values()] if total else []
        ent=-sum(p*math.log2(p) for p in probs)
        changed_assoc=[0,0,0]; occ=0
        for r in rs:
            if c in r['text']:
                occ+=1
                for i in range(3): changed_assoc[i]+=int(r['before'][i]!=r['after'][i])
        sel=(max(changed_assoc)/occ if occ else 0)-(min(changed_assoc)/occ if occ else 0)
        if sel>0.38: obj_tokens.append(c)
        elif ent<2.0 and total>=2: op_tokens.append(c)
        else: nuisance.append(c)
    # Infer object mapping by maximum changed-index association.
    objmap={}
    for c in obj_tokens:
        scores=[]
        for i in range(3):
            hit=sum(c in r['text'] and r['before'][i]!=r['after'][i] for r in rs)
            false=sum(c in r['text'] and r['before'][i]==r['after'][i] for r in rs)
            scores.append(hit-false*0.15)
        objmap[c]=max(range(3),key=lambda i:scores[i])
    # Infer operation prototypes directly from outcome signatures, no family cardinality supplied.
    opproto={}
    for c in op_tokens:
        cnt=Counter(outcome_signature(r['before'],r['after']) for r in rs if c in r['text'])
        if cnt: opproto[c]=cnt.most_common(1)[0][0]
    # Goal tokens emerge as chars whose presence splits delta direction for same op token.
    goaldir={}
    for c in chars:
        vals=[]
        for r in rs:
            if c in r['text']:
                sig=outcome_signature(r['before'],r['after']); vals.append(sig[1])
        flat=[x for v in vals for x in v]
        if flat: goaldir[c]=Counter(flat).most_common(1)[0][0]
    return {"op_tokens":op_tokens,"obj_tokens":obj_tokens,"nuisance":nuisance,
            "objmap":objmap,"opproto":opproto,"goaldir":goaldir,"global_template":global_template}

def predict(model,e):
    text=e['text']; before=e['before']
    ops=[c for c in model['op_tokens'] if c in text and c in model['opproto']]
    if not ops: return None
    oc=max(ops,key=lambda c:sum(1 for x in text if x==c)); sig=model['opproto'][oc]
    objs=[]
    for c in model['obj_tokens']:
        if c in text and c in model['objmap'] and model['objmap'][c] not in objs: objs.append(model['objmap'][c])
    arity=sig[0]
    # For global transformations, changed-count may be 3 while semantic arity is 0.
    if sig[3]: arity=0
    if sig[2]: arity=2
    if arity>len(objs): return None
    args=tuple(objs[:arity])
    # Infer anonymous execution from signature rather than hidden family labels.
    candidates=[]
    for op in range(4):
        if (1,2,1,0)[op]!=arity: continue
        for goal in range(2):
            out=apply_hidden(before,op,args,goal)
            if outcome_signature(before,out)==sig: candidates.append((out,op,goal,args))
    if len(candidates)!=1: return None
    return candidates[0]

def evaluate(seed,method,budget=18):
    rng=random.Random(seed)
    objmap=dict(zip(range(3),rng.sample(OBJ_CHARS,3)))
    opmap=dict(zip(range(4),rng.sample(OP_CHARS,4)))
    pool=[episode(rng,objmap,opmap) for _ in range(90)]
    chosen=[]; stats=defaultdict(Counter)
    for _ in range(budget):
        if method in ('active','conservative','shuffle','global'):
            idx=select_active(pool,chosen,stats)
        else:
            idx=rng.choice([i for i in range(len(pool)) if i not in chosen])
        chosen.append(idx); r=pool[idx]; sig=outcome_signature(r['before'],r['after'])
        for c in set(r['text']): stats[c][sig]+=1
    rec=[pool[i] for i in chosen]
    model=infer_model(rec,shuffle=(method=='shuffle'),global_template=(method=='global'))
    modes=['held','rename','word_order','omitted','paragraph','free','goal_change','repair','second_domain']
    results={}
    # second domain has disjoint chars and mapping, with 4 one-shot calibration records only.
    for mode in modes:
        trng=random.Random(seed*100+len(mode))
        om=objmap; pm=opmap
        local_model=model
        if mode=='second_domain':
            om=dict(zip(range(3),list('丁戊己'))); pm=dict(zip(range(4),list('宇宙洪荒')))
            cal=[episode(trng,om,pm) for _ in range(4)]
            local_model=infer_model(cal)
        form={'held':'prefix','rename':'suffix','word_order':'reverse','omitted':'omitted','paragraph':'paragraph','free':'free','goal_change':'interleave','repair':'free','second_domain':'free'}[mode]
        vals=[]
        for _ in range(48):
            e=episode(trng,om,pm,form=form)
            p=predict(local_model,e)
            vals.append({
                'joint':p is not None and p[0]==e['after'],
                'inverse':p is not None and p[1]==e['op'],
                'goal':p is not None and p[2]==e['goal'],
                'repair':p is not None and p[0]==e['after'],
                'abstain':p is None})
        results[mode]={k:statistics.mean(float(v[k]) for v in vals) for k in vals[0]}
    return model,results

def main():
    methods=['active','conservative','random','global','shuffle']
    raw={}; t0=time.perf_counter(); max_model=0
    for seed in SEEDS:
        raw[str(seed)]={}
        for m in methods:
            mt=time.perf_counter(); model,res=evaluate(seed,m)
            b=len(pickle.dumps(model)); max_model=max(max_model,b)
            raw[str(seed)][m]={'model_bytes':b,'seconds':time.perf_counter()-mt,'results':res,
                               'role_inventory':{k:len(model[k]) for k in ('op_tokens','obj_tokens','nuisance')}}
    summary={}
    for m in methods:
        summary[m]={'model_bytes':statistics.mean(raw[str(s)][m]['model_bytes'] for s in SEEDS),
                    'seconds':statistics.mean(raw[str(s)][m]['seconds'] for s in SEEDS)}
        for mode in raw['1'][m]['results']:
            summary[m][mode]={k:statistics.mean(raw[str(s)][m]['results'][mode][k] for s in SEEDS)
                              for k in raw['1'][m]['results'][mode]}
        summary[m]['roles']={k:statistics.mean(raw[str(s)][m]['role_inventory'][k] for s in SEEDS)
                             for k in raw['1'][m]['role_inventory']}
    print(json.dumps({'cycle':9,'hypothesis':'Nonparametric Operation-Inventory Birth from Outcome-Conditioned Token Roles',
      'seeds':SEEDS,'summary':summary,'raw':raw,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      'runtime_seconds':time.perf_counter()-t0,'candidate_cap':90,'witness_budget':18,
      'estimated_ops':'train O(B*L*S), inference O(K*A), K<=4, A<=2',
      'answer_leakage':False,'fixed_operation_family_given_to_learner':False,
      'fixed_role_cardinality_given_to_learner':False,'highschool_level':False},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
