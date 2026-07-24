from __future__ import annotations
import json, math, random, resource, statistics, time, pickle
from collections import defaultdict, Counter

SEEDS=(1,7,19)
DOMAINS=('d1','d2')
FORMS=('canonical','reverse','omitted','paragraph','free','rename')
OPS=('hold','toggle','set1')
GOALS=('keep','change')

LEX={
'd1': {'obj':['ネ','フ','ラ'], 'op':['ギ','モ','セ'], 'goal':['静','変'], 'noise':['を','して','あと','です']},
'd2': {'obj':['タ','ビ','コ'], 'op':['ヌ','レ','ハ'], 'goal':['保','換'], 'noise':['に','実行','そして','ください']},
}

def effect(before,target,op,goal):
    w=list(before)
    if op=='toggle': w[target]=1-w[target]
    elif op=='set1': w[target]=1
    if goal=='change' and op=='hold': w[target]=1-w[target]
    return tuple(w)

def render(domain,target,op,goal,form,rng,alias_shift=0):
    lx=LEX[domain]; o=lx['obj'][(target+alias_shift)%3]
    p=lx['op'][(OPS.index(op)+alias_shift)%3]
    g=lx['goal'][(GOALS.index(goal)+alias_shift)%2]
    n=lx['noise']
    if form=='canonical': return f'{o}{n[0]}{p}{n[1]}{g}'
    if form=='reverse': return f'{g}{n[2]}{o}{p}'
    if form=='omitted': return f'{p}{o}'
    if form=='paragraph': return f'{o}{n[0]}{p}\n{g}{n[3]}'
    if form=='rename': return f'{lx["obj"][(target+1)%3]}{n[0]}{lx["op"][(OPS.index(op)+1)%3]}{g}'
    return f'{n[3]}、{g}なら{p}を{o}へ{n[1]}'

def ngrams(s):
    t=''.join(ch for ch in s if not ch.isspace())
    out=[]
    for n in (1,2,3):
        out.extend(t[i:i+n] for i in range(len(t)-n+1))
    return out

def vec(s): return Counter(ngrams(s))
def cos(a,b):
    dot=sum(v*b.get(k,0) for k,v in a.items()); na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return dot/(na*nb) if na and nb else 0.0

def signature(row, axis):
    b=row['before']; t=row['target']; op=row['op']; g=row['goal']
    if axis=='target': alt=(t+1)%3; y0=effect(b,t,op,g); y1=effect(b,alt,op,g)
    elif axis=='state':
        bb=list(b); bb[t]=1-bb[t]; bb=tuple(bb); y0=effect(b,t,op,g); y1=effect(bb,t,op,g)
    elif axis=='goal':
        gg='change' if g=='keep' else 'keep'; y0=effect(b,t,op,g); y1=effect(b,t,op,gg)
    else:
        y0=effect(b,t,op,g); y1=effect(b,t,'toggle' if op!='toggle' else 'hold',g)
    delta=tuple(int(a!=c) for a,c in zip(y0,y1))
    preserved=tuple(int(a==c) for i,(a,c) in enumerate(zip(y0,y1)) if i!=t)
    return (delta,preserved)

def make(seed,domain):
    rng=random.Random(seed*100+sum(map(ord,domain)))
    rows=[]
    for i in range(180):
        target=rng.randrange(3); op=rng.choice(OPS); goal=rng.choice(GOALS); before=tuple(rng.randrange(2) for _ in range(3))
        form=FORMS[i%len(FORMS)]
        text=render(domain,target,op,goal,form,rng,alias_shift=0)
        rows.append({'text':text,'before':before,'target':target,'op':op,'goal':goal,'form':form,'after':effect(before,target,op,goal)})
    return rows

def train(rows, mode, seed):
    rng=random.Random(seed)
    axes=('target','state','goal','operation')
    prot=defaultdict(Counter); counts=Counter()
    calibration=[r for r in rows if r['form'] in ('canonical','paragraph')]
    for r in calibration:
        true_axis=rng.choice(axes)
        key=(true_axis, signature(r,true_axis))
        if mode=='axis_shuffle': key=(rng.choice(axes), key[1])
        elif mode=='signature_shuffle': key=(key[0], signature(r,rng.choice(axes)))
        elif mode=='random':
            if rng.random()<0.5: key=(rng.choice(axes), signature(r,rng.choice(axes)))
        for g,v in vec(r['text']).items(): prot[key][g]+=v
        counts[key]+=1
    for k in list(prot):
        c=max(1,counts[k]); prot[k]=Counter({g:v/c for g,v in prot[k].items()})
    return prot

def predict(prot,row):
    x=vec(row['text'])
    scores=defaultdict(float)
    for (axis,sig),p in prot.items(): scores[(axis,sig)]=cos(x,p)
    if not scores: return None
    return max(scores,key=scores.get)

def evaluate(prot,rows):
    metrics=Counter(); den=Counter()
    for r in rows:
        pred=predict(prot,r)
        if pred is None: continue
        axis,sig=pred
        truths={a:signature(r,a) for a in ('target','state','goal','operation')}
        correct = sig==truths.get(axis)
        metrics['prospective']+=correct; den['prospective']+=1
        metrics['inverse']+=correct and axis in ('target','operation'); den['inverse']+=1
        metrics['identity_hold']+=correct and sig[1]==truths[axis][1]; den['identity_hold']+=1
        metrics['counterfactual']+=correct; den['counterfactual']+=1
        formkey={'reverse':'unknown_order','omitted':'subject_omission','paragraph':'paragraph','free':'free','rename':'rename'}.get(r['form'])
        if formkey:
            metrics[formkey]+=correct; den[formkey]+=1
    return {k:metrics[k]/max(1,den[k]) for k in ('prospective','inverse','identity_hold','counterfactual','rename','unknown_order','subject_omission','paragraph','free')}

def run():
    start=time.perf_counter(); raw={}
    for seed in SEEDS:
        raw[str(seed)]={}
        for d in DOMAINS:
            rows=make(seed,d); trainrows=rows[:120]; test=rows[120:]
            raw[str(seed)][d]={}
            for mode in ('correct','random','axis_shuffle','signature_shuffle'):
                p=train(trainrows,mode,seed+len(d)); raw[str(seed)][d][mode]=evaluate(p,test)
                raw[str(seed)][d][mode]['model_bytes']=len(pickle.dumps(p))
    summary={}
    for mode in ('correct','random','axis_shuffle','signature_shuffle'):
        summary[mode]={}
        for k in raw['1']['d1'][mode]:
            summary[mode][k]=statistics.mean(raw[str(s)][d][mode][k] for s in SEEDS for d in DOMAINS)
    strict=0
    for s in SEEDS:
        ok=True
        for d in DOMAINS:
            c=raw[str(s)][d]['correct']
            for k in ('prospective','inverse','identity_hold','counterfactual','free'):
                ctrl=max(raw[str(s)][d][m][k] for m in ('random','axis_shuffle','signature_shuffle'))
                ok &= c[k]-ctrl>=0.10
        strict+=int(ok)
    out={'cycle':13,'hypothesis':'Cross-Expression Transformation-Indexed Identity from Selective Equivariance Signatures',
         'seeds':SEEDS,'domains':DOMAINS,'summary':summary,'strict_progress_seeds':strict,
         'semantic_identity_gate':False,'model_bytes_mean':summary['correct']['model_bytes'],
         'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         'runtime_seconds':time.perf_counter()-start,'estimated_ops':'O(N * |axes| * sparse_ngrams)',
         'answer_leakage':False,'fixed_ontology':False,'rag':False,'external_llm':False,
         'weak_smartphone_verified':False,'highschool_level_passed':False,'completion':False,'raw':raw}
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': run()
