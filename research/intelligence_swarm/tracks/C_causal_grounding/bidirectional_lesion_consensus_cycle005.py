from __future__ import annotations
import importlib.util, json, pathlib, pickle, random, resource, statistics, time
import numpy as np

ROOT=pathlib.Path(__file__).resolve().parents[4]
BASE=ROOT/'research/intelligence_swarm/tracks/B_operation_goal/cross_lexicon_selective_consequence_cycle004.py'
spec=importlib.util.spec_from_file_location('base_cycle004',BASE); b=importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
SEEDS=(1,7,19); DOMAINS={'D':1,'E':2,'F':3}

def rename_dataset(seed,n,dom,scale):
    rng=random.Random(seed); rows=[]; L=b.LEX[dom]
    for _ in range(n):
        before=b.world(rng,scale); s=rng.randrange(4); m=rng.randrange(4); g=rng.randrange(2); t=b.target(before,s); after=b.move(before,t,m)
        text=f"{rng.choice(L['wrap'])}、対象規則『{rng.choice(L['sel'][s])}』に従うものへ、操作『{rng.choice(L['move'][m])}』を適用。達成基準は{L['goal'][g]}。"
        rows.append(dict(text=text,before=before,after=after,selector=s,move=m,goal=g,target=t,domain=dom,mode='rename'))
    return rows

def evaluate(rows,model,center,scale,mask):
    W,xc=model; joint=[]; inverse=[]; cycle=[]; start=time.perf_counter()
    for row in rows:
        x=b.lang(row['text'])-xc; q=x@W; q/=np.linalg.norm(q)+1e-8
        cand=[]
        for t in range(8):
            for m in range(4):
                trial=dict(row); trial['after']=b.move(row['before'],t,m)
                cand.append((float(q@b.effect(trial,center,scale,mask)),t,m))
        _,pt,pm=max(cand); joint.append(float(pt==row['target'] and pm==row['move']))
        choices=[(row['selector'],row['move'],row['goal'])]; cr=random.Random(b.stable_hash(row['text']))
        while len(choices)<8:
            z=(cr.randrange(4),cr.randrange(4),cr.randrange(2))
            if z not in choices: choices.append(z)
        y=b.effect(row,center,scale,mask); scores=[]
        for s,m,g in choices:
            x2=b.lang(b.render(cr,row['domain'],s,m,g,'seen'))-xc; p=x2@W; p/=np.linalg.norm(p)+1e-8; scores.append(float(p@y))
        inverse.append(float(np.argmax(scores)==0))
        xr=y@W.T; cycle.append(float((xr@x)/(np.linalg.norm(xr)*np.linalg.norm(x)+1e-8)))
    return dict(joint_accuracy=statistics.mean(joint),inverse_accuracy=statistics.mean(inverse),cycle_cosine=statistics.mean(cycle),inference_ms=(time.perf_counter()-start)*1000/len(rows))

def signature(train_rows,valid_rows,center,scale):
    full=np.ones(b.DIM_Y,np.float32); base=evaluate(valid_rows,b.train(train_rows,center,scale,full),center,scale,full); out=[]
    for ch in range(b.DIM_Y):
        mask=np.ones(b.DIM_Y,np.float32); mask[ch]=0; ev=evaluate(valid_rows,b.train(train_rows,center,scale,mask),center,scale,mask)
        out.append([base['joint_accuracy']-ev['joint_accuracy'],base['inverse_accuracy']-ev['inverse_accuracy'],base['cycle_cosine']-ev['cycle_cosine']])
    return np.asarray(out,np.float32)

def consensus(signatures,shuffled=False):
    ss=[x.copy() for x in signatures]
    if shuffled: ss[1]=ss[1][np.random.default_rng(77).permutation(len(ss[1]))]
    positive=np.stack([(x[:,0]>0)&(x[:,1]>0)&(x[:,2]>0) for x in ss]); strength=np.min(np.stack([np.maximum(x,0).sum(1) for x in ss]),axis=0)
    keep=np.all(positive,axis=0)
    if keep.sum()<3: keep[np.argsort(strength)[-3:]]=True
    return keep.astype(np.float32),dict(channels=int(keep.sum()),mean_strength=float(strength[keep].mean()))

def run_seed(seed):
    train={d:b.dataset(seed+100*i,48,d,('seen','word_order','paragraph','free'),sc) for i,(d,sc) in enumerate(DOMAINS.items())}; stats={d:b.fit_stats(x) for d,x in train.items()}
    valid={d:b.dataset(seed+500+i,8,d,('seen','word_order','free'),sc) for i,(d,sc) in enumerate(DOMAINS.items())}; sig=[signature(train[d],valid[d],*stats[d]) for d in DOMAINS]
    masks={}; masks['full']=np.ones(b.DIM_Y,np.float32); masks['bidirectional_consensus'],meta=consensus(sig); masks['shuffled_consensus'],smeta=consensus(sig,True)
    out={'meta':{'consensus':meta,'shuffled':smeta},'methods':{}}
    for name,mask in masks.items():
        out['methods'][name]={}
        for i,(d,sc) in enumerate(DOMAINS.items()):
            model=b.train(train[d],*stats[d],mask); shuf=b.train(train[d],*stats[d],mask,shuffle=True)
            tests={'held':b.dataset(seed+1000+i,8,d,('seen',),sc),'rename':rename_dataset(seed+1100+i,8,d,sc),'word_order':b.dataset(seed+1200+i,8,d,('word_order',),sc),'paragraph':b.dataset(seed+1300+i,8,d,('paragraph',),sc),'free':b.dataset(seed+1400+i,8,d,('free',),sc),'goal_change':b.dataset(seed+1500+i,8,d,('goal_change',),sc),'repair':b.dataset(seed+1600+i,8,d,('repair',),sc)}
            out['methods'][name][d]={'correct':{k:evaluate(v,model,*stats[d],mask) for k,v in tests.items()},'shuffle':{k:evaluate(v,shuf,*stats[d],mask) for k,v in tests.items()},'model_bytes':len(pickle.dumps((model,stats[d],mask)))}
    return out

def main():
    start=time.perf_counter(); raw={str(s):run_seed(s) for s in SEEDS}; strict=0
    for s in SEEDS:
        ok=True
        for d in DOMAINS:
            for c in ('free','goal_change','repair'):
                a=raw[str(s)]['methods']['bidirectional_consensus'][d]['correct'][c]; z=raw[str(s)]['methods']['bidirectional_consensus'][d]['shuffle'][c]
                ok &= a['joint_accuracy']-z['joint_accuracy']>=.10 and a['inverse_accuracy']-z['inverse_accuracy']>=.10
        strict+=int(ok)
    return dict(track='C_causal_grounding',cycle=5,hypothesis='Bidirectional Lesion-Consensus Causal Units from Cross-Lexicon Response Conservation',seeds=list(SEEDS),raw=raw,strict_seed_passes=strict,consensus_channels=statistics.mean(raw[str(s)]['meta']['consensus']['channels'] for s in SEEDS),peak_rss_kib_runtime_included=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,runtime_sec=time.perf_counter()-start,candidate_count=32,estimated_update_ops=b.DIM_X*b.DIM_Y,estimated_inference_ops=b.DIM_X*b.DIM_Y+32*b.DIM_Y*19,post_treatment_at_test=False,shared_lexicon_across_domains=False,fixed_ontology_or_handwritten_slot=False,highschool_level_passed=False,native_japanese_communication_passed=False,weak_smartphone_verified=False,completion=False)

if __name__=='__main__': print(json.dumps(main(),ensure_ascii=False,indent=2))
