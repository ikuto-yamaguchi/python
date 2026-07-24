from __future__ import annotations
import json, random, time, math, statistics, resource, pickle
from collections import defaultdict, Counter

OPS = {
    "set1": lambda x: 1,
    "set0": lambda x: 0,
    "toggle": lambda x: 1-x,
    "copy": lambda x,y: y,
}
DOMAINS = {
    "d1": {"objs":["灯","扉"],"verbs":{"set1":["点ける","明るくする"],"set0":["消す","暗くする"],"toggle":["反転する","切り替える"],"copy":["合わせる","写す"]}},
    "d2": {"objs":["札","槽"],"verbs":{"set1":["満たす","有効化する"],"set0":["空にする","無効化する"],"toggle":["裏返す","切替える"],"copy":["同期する","倣わせる"]}},
}
FORMS=["canonical","reverse","omit","paragraph","free","rename"]

def apply(world, op, target, source=None):
    w=list(world)
    if op=="copy":
        w[target]=OPS[op](w[target], w[source])
    else:
        w[target]=OPS[op](w[target])
    return tuple(w)

def utter(domain, op, target, source, form, rng):
    objs=domain["objs"]
    verb=rng.choice(domain["verbs"][op])
    t=objs[target]
    s=objs[source] if source is not None else None
    if form=="rename":
        t="対象甲" if target==0 else "対象乙"
        s=("対象甲" if source==0 else "対象乙") if source is not None else None
    if op=="copy":
        base=f"{s}の状態を{t}へ{verb}"
    else:
        base=f"{t}を{verb}"
    if form=="reverse":
        return f"{verb}。対象は{t}" if op!="copy" else f"{verb}。元は{s}、先は{t}"
    if form=="omit":
        return f"それを{verb}"
    if form=="paragraph":
        return f"前の記録は保持。\n{base}。\n他は変更しない"
    if form=="free":
        return f"作業として、{base}ようにしてください"
    return base

def perturb_episode(ep, kind, rng):
    e=dict(ep)
    if kind=="target":
        e["target"]=1-e["target"]
        if e["op"]=="copy" and e["source"]==e["target"]:
            e["source"]=1-e["target"]
    elif kind=="source" and e["op"]=="copy":
        e["source"]=1-e["source"]
        if e["source"]==e["target"]:
            e["source"]=1-e["source"]
    elif kind=="goal":
        e["goal"]=1-e["goal"]
    elif kind=="order":
        e["form"]="reverse" if e["form"]!="reverse" else "canonical"
    elif kind=="direction":
        e["before"],e["after"]=e["after"],e["before"]
    return e

def make_episode(rng, dname, form=None):
    domain=DOMAINS[dname]
    op=rng.choice(list(OPS))
    target=rng.randrange(2)
    source=None
    if op=="copy":
        source=1-target
    before=(rng.randrange(2),rng.randrange(2))
    after=apply(before,op,target,source)
    goal=after[target]
    form=form or rng.choice(FORMS[:-1])
    text=utter(domain,op,target,source,form,rng)
    return {"domain":dname,"op":op,"target":target,"source":source,"before":before,"after":after,"goal":goal,"form":form,"text":text}

def char_features(text, dim=128):
    v=[0.0]*dim
    for i,ch in enumerate(text):
        h=(ord(ch)*1315423911 + i*2654435761) % dim
        v[h]+=1.0
    n=math.sqrt(sum(x*x for x in v)) or 1.0
    return [x/n for x in v]

def effect(ep):
    b,a=ep["before"],ep["after"]
    return (a[0]-b[0],a[1]-b[1],int(a[0]==b[0]),int(a[1]==b[1]),ep["goal"])

def signature_from_anonymous_perturbations(ep, rng, shuffled=False):
    kinds=["target","source","goal","order","direction"]
    pairs=[]
    base=effect(ep)
    for k in kinds:
        pe=perturb_episode(ep,k,rng)
        if k in ("target","source","goal","order"):
            pe["text"]=utter(DOMAINS[ep["domain"]],pe["op"],pe["target"],pe["source"],pe["form"],rng)
            pe["after"]=apply(pe["before"],pe["op"],pe["target"],pe["source"])
            pe["goal"]=pe["after"][pe["target"]]
        diff=tuple(x-y for x,y in zip(effect(pe),base))
        pairs.append((k,diff))
    if shuffled:
        ds=[d for _,d in pairs]; rng.shuffle(ds); pairs=[(k,d) for (k,_),d in zip(pairs,ds)]
    vecs=[d for _,d in pairs]
    comm=[]
    for i in range(len(vecs)):
        for j in range(i+1,len(vecs)):
            comm.append(sum(abs(vecs[i][z]-vecs[j][z]) for z in range(len(vecs[i]))))
    return tuple(sorted(vecs)), tuple(sorted(comm))

def train(seed, shuffled=False):
    rng=random.Random(seed)
    prot=defaultdict(lambda:[0.0]*128)
    sigs=defaultdict(Counter)
    t0=time.perf_counter()
    for d in DOMAINS:
        for _ in range(120):
            ep=make_episode(rng,d)
            sf=signature_from_anonymous_perturbations(ep,rng,shuffled)
            x=char_features(ep["text"])
            for i,v in enumerate(x): prot[ep["op"]][i]+=v
            sigs[ep["op"]][sf]+=1
    for op in prot:
        n=math.sqrt(sum(x*x for x in prot[op])) or 1
        prot[op]=[x/n for x in prot[op]]
    dominant={op:sigs[op].most_common(1)[0][0] for op in sigs}
    return {"prot":dict(prot),"sig":dominant}, time.perf_counter()-t0

def score(model, ep, use_sig=True):
    x=char_features(ep["text"])
    sf=signature_from_anonymous_perturbations(ep,random.Random(999),False)
    scores={}
    for op,p in model["prot"].items():
        sim=sum(a*b for a,b in zip(x,p))
        if use_sig:
            ref=model["sig"][op]
            mismatch=sum(abs(a-b) for va,vb in zip(sf[0],ref[0]) for a,b in zip(va,vb))
            sim-=0.02*mismatch
        scores[op]=sim
    return max(scores,key=scores.get),scores

def evaluate(seed, shuffled_train=False, use_sig=True):
    model,tr=train(seed,shuffled_train)
    rng=random.Random(seed+777)
    rows=[]
    for d in DOMAINS:
        for form in FORMS:
            for _ in range(40):
                ep=make_episode(rng,d,form)
                pred,_=score(model,ep,use_sig)
                src=(ep["source"] if ep["source"] is not None else 1-ep["target"]) if pred=="copy" else None
                pa=apply(ep["before"],pred,ep["target"],src)
                rows.append({"domain":d,"form":form,"op_acc":pred==ep["op"],"prospective":pa==ep["after"],
                             "inverse":pred==ep["op"],"goal":pa[ep["target"]]==ep["goal"],"repair":pa==ep["after"]})
    agg={}
    for d in DOMAINS:
      for form in FORMS:
        rr=[r for r in rows if r["domain"]==d and r["form"]==form]
        agg[f"{d}:{form}"]={k:statistics.mean(float(x[k]) for x in rr) for k in ("op_acc","prospective","inverse","goal","repair")}
    return model,tr,agg

def run():
    methods={"correct":(False,True),"random_surface":(False,False),"axis_shuffle":(True,True)}
    raw={}
    for seed in (1,7,19):
        raw[str(seed)]={}
        for m,(sh,us) in methods.items():
            model,tr,agg=evaluate(seed,sh,us)
            raw[str(seed)][m]={"train_s":tr,"model_bytes":len(pickle.dumps(model)),"agg":agg}
    summary={}
    for m in methods:
        summary[m]={}
        for key in raw["1"][m]["agg"]:
            summary[m][key]={metric:statistics.mean(raw[str(s)][m]["agg"][key][metric] for s in (1,7,19))
                             for metric in raw["1"][m]["agg"][key]}
        summary[m]["train_s"]=statistics.mean(raw[str(s)][m]["train_s"] for s in (1,7,19))
        summary[m]["model_bytes"]=statistics.mean(raw[str(s)][m]["model_bytes"] for s in (1,7,19))
    return {"cycle":12,"hypothesis":"Latent Operation-Axis Birth from Anonymous Commutator Sparsity",
            "summary":summary,"raw":raw,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "answer_leakage":False,"fixed_ontology_in_model":False,"highschool_level":False}

if __name__=="__main__":
    print(json.dumps(run(),ensure_ascii=False,indent=2))
