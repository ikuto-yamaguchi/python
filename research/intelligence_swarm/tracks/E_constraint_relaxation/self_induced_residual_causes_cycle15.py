from __future__ import annotations
import argparse, json, math, pickle, random, resource, statistics, time, hashlib
from dataclasses import dataclass

EDGES=('target','value','direction','scope','address')
R=('reconstruct','preserve','inverse','revision','recall')
TRUE_MAP={'reconstruct':'value','preserve':'target','inverse':'direction','revision':'scope','recall':'address'}

@dataclass(frozen=True)
class Cand:
    vals: tuple[int,...]

def stable(*xs):
    h=hashlib.blake2b('|'.join(map(str,xs)).encode(),digest_size=8).digest()
    return int.from_bytes(h,'little')

def residual(c: Cand, truth: Cand, noise: float, rng: random.Random):
    out=[]
    for r in R:
        e=TRUE_MAP[r]; i=EDGES.index(e)
        v=float(c.vals[i]!=truth.vals[i])
        if rng.random()<noise: v=1.0-v
        out.append(v)
    return tuple(out)

def candidates(rng,n=16,marked=True):
    truth=Cand(tuple(rng.randrange(2) for _ in EDGES))
    pool=[]
    for bits in range(2**len(EDGES)):
        c=Cand(tuple((bits>>i)&1 for i in range(len(EDGES))))
        if c==truth or rng.random()<0.58: pool.append(c)
    rng.shuffle(pool);pool=pool[:n]
    if marked and truth not in pool: pool[-1]=truth
    if not marked and truth in pool: pool.remove(truth)
    return truth,pool

def induce_map(pool, truth, rng, noise=0.03):
    base=[residual(c,truth,noise,rng) for c in pool]
    sigs={e:[0.0]*len(R) for e in EDGES}; evals=0
    for ci,c in enumerate(pool):
        for ei,e in enumerate(EDGES):
            v=list(c.vals);v[ei]^=1; surg=Cand(tuple(v))
            rr=residual(surg,truth,noise,rng);evals+=1
            for j in range(len(R)): sigs[e][j]+=abs(rr[j]-base[ci][j])
    pairs=[]
    for e in EDGES:
        for j,r in enumerate(R): pairs.append((sigs[e][j],e,r))
    pairs.sort(reverse=True); emap={}; used_r=set();used_e=set()
    for score,e,r in pairs:
        if score<=0 or e in used_e or r in used_r: continue
        emap[r]=e;used_e.add(e);used_r.add(r)
    return emap,evals,sigs

def relax(pool,truth,mode,rng,noise=0.03,max_sweep=4):
    if not pool:return None,0,0,0,{},'null'
    obs=[residual(c,truth,noise,rng) for c in pool];evals=0
    if mode=='oracle': mp=TRUE_MAP.copy()
    elif mode=='self': mp,evals,_=induce_map(pool,truth,rng,noise)
    elif mode=='shuffled':
        es=list(EDGES);rng.shuffle(es);mp={r:e for r,e in zip(R,es)}
    else: mp={r:'ALL' for r in R}
    scores=[0.0]*len(pool); active=list(range(len(pool))); prev=None
    for sweep in range(1,max_sweep+1):
        for k in active:
            penalty=0.0
            for j,r in enumerate(R):
                if mode=='global': penalty+=obs[k][j]
                else:
                    e=mp.get(r)
                    if e is None: continue
                    ei=EDGES.index(e)
                    consensus=round(sum(c.vals[ei] for c in pool)/len(pool))
                    penalty+=obs[k][j]*(1.0+0.25*(pool[k].vals[ei]==consensus))
            scores[k]=-penalty
        best=max(scores[k] for k in active); new=[k for k in active if scores[k]>=best-1e-9]
        state=tuple(new)
        if state==prev:return (pool[new[0]] if len(new)==1 else None),sweep,len(new),evals,mp,('unique' if len(new)==1 else 'flat')
        prev=state;active=new
    return (pool[active[0]] if len(active)==1 else None),max_sweep,len(active),evals,mp,('unique' if len(active)==1 else 'diverge')

def run(seed,n,condition):
    rng=random.Random(seed*100000+n*17+stable(condition)%10000)
    marked=condition!='unmarked'; noise=.03 if condition not in ('noise','long') else (.14 if condition=='noise' else .07)
    rows=[]
    for _ in range(n):
        truth,pool=candidates(rng,16,marked)
        if condition=='ambiguous': pool=pool[:12]
        if condition=='nested': pool=pool[:14]
        if condition=='plan': pool=pool[:10]
        for mode in ('global','shuffled','oracle','self'):
            t=time.perf_counter(); pred,sw,act,ev,mp,status=relax(pool,truth,mode,rng,noise);dt=time.perf_counter()-t
            rows.append({'mode':mode,'correct':int(pred==truth),'wrong':int(pred is not None and pred!=truth),'null':int(pred is None),'sweeps':sw,'active':act,'factor_evals':ev,'seconds':dt,'map_exact':int(mp==TRUE_MAP)})
    out={}
    for mode in ('global','shuffled','oracle','self'):
        z=[x for x in rows if x['mode']==mode]
        out[mode]={k:statistics.mean(x[k] for x in z) for k in ('correct','wrong','null','sweeps','active','factor_evals','seconds','map_exact')}
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_015.json');a=ap.parse_args()
    raw={}; conditions=('seen','ambiguous','nested','counterfactual','plan','long','noise','unmarked')
    for n in (60,180,360):
        raw[str(n)]={}
        for seed in (1,7,19): raw[str(n)][str(seed)]={c:run(seed,n,c) for c in conditions}
    summary={}
    for n in raw:
        summary[n]={}
        for c in conditions:
            summary[n][c]={}
            for m in ('global','shuffled','oracle','self'):
                summary[n][c][m]={k:statistics.mean(raw[n][str(seed)][c][m][k] for seed in (1,7,19)) for k in raw[n]['1'][c][m]}
    payload={'hypothesis':'Self-Induced Residual Cause Nodes by Minimal Edge Surgery','seeds':[1,7,19],'sizes':[60,180,360],'summary':summary,'raw':raw,'model_bytes':len(pickle.dumps({'edges':EDGES,'residuals':R})),'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'proposal O(L^2); surgery O(HER); relaxation O(SHR); H<=16,E=5,R=5,S<=4','unmarked_candidate_recall':0.0,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary['360'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
