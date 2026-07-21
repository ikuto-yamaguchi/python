import argparse,json,math,pickle,random,resource,statistics,time

class Model:
    def __init__(self,null=False,adaptive=False):
        self.null=null; self.adaptive=adaptive; self.threshold=.34
    def solve(self,candidates,evidence):
        active=list(range(len(candidates))); evals=0; sweeps=0
        energies=[sum(abs(a-b) for a,b in zip(c,evidence))/len(evidence) for c in candidates]
        while sweeps<4 and len(active)>1:
            sweeps+=1
            best=min(energies[i] for i in active)
            tied=[i for i in active if abs(energies[i]-best)<1e-9]
            if len(tied)==1:
                active=tied; break
            if not self.adaptive: break
            bestj=None; bestgain=0
            for j in range(len(evidence)):
                vals={candidates[i][j] for i in tied}; evals+=len(tied)
                if len(vals)>bestgain: bestgain=len(vals); bestj=j
            if bestj is None or bestgain<=1: break
            target=evidence[bestj]
            active=[i for i in tied if candidates[i][bestj]==target]
        minres=min(energies[i] for i in active) if active else 1.0
        if self.null and minres>self.threshold:
            return None,sweeps,evals,len(active),minres,True
        if len(active)==1:
            return active[0],sweeps,evals,1,minres,False
        return None,sweeps,evals,len(active),minres,False

def case(rng,mode,h=12,d=8):
    cand=[[rng.randint(0,1) for _ in range(d)] for _ in range(h)]
    if mode=='inset':
        gold=rng.randrange(h); ev=cand[gold][:]
        for i in range(h):
            if i!=gold: cand[i][:3]=ev[:3]
        return cand,ev,gold
    if mode=='outset':
        ev=[rng.randint(0,1) for _ in range(d)]
        while ev in cand: ev=[rng.randint(0,1) for _ in range(d)]
        return cand,ev,None
    if mode=='noisy':
        gold=rng.randrange(h); ev=cand[gold][:]
        for j in rng.sample(range(d),2): ev[j]^=1
        return cand,ev,gold
    base=[rng.randint(0,1) for _ in range(d)]
    return [base[:] for _ in range(h)],base[:],0

def run(seed,n):
    rng=random.Random(seed); out={}
    methods={'closed':Model(False,True),'null_fixed':Model(True,False),'null_adaptive':Model(True,True)}
    for name,m in methods.items():
        res={}
        for mode in ['inset','outset','noisy','collapse']:
            ok=wrong=null=conv=sweeps=evals=active=0; t=time.perf_counter()
            for _ in range(n):
                c,e,g=case(rng,mode); p,s,v,a,r,isnull=m.solve(c,e)
                sweeps+=s; evals+=v; active+=a; null+=isnull; conv+=p is not None or isnull
                if g is not None and p==g: ok+=1
                elif p is not None: wrong+=1
            dt=(time.perf_counter()-t)*1000/n
            res[mode]={'accuracy':ok/n,'wrong_commit':wrong/n,'null_rate':null/n,'convergence':conv/n,'sweeps':sweeps/n,'factor_evals':evals/n,'active':active/n,'ms':dt}
        res['model_bytes']=len(pickle.dumps(m)); out[name]=res
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',default='results_cycle_012.json'); a=ap.parse_args()
    raw={str(n):[run(s,n) for s in [1,7,19]] for n in [120,360,1080]}
    summary={}
    for n,runs in raw.items():
        summary[n]={}
        for meth in runs[0]:
            summary[n][meth]={}
            for mode in ['inset','outset','noisy','collapse']:
                summary[n][meth][mode]={k:statistics.mean(x[meth][mode][k] for x in runs) for k in runs[0][meth][mode]}
            summary[n][meth]['model_bytes']=statistics.mean(x[meth]['model_bytes'] for x in runs)
    payload={'hypothesis':'Open-Set Residual Energy with Null-Hypothesis Attractors','seeds':[1,7,19],'sizes':[120,360,1080],'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'complexity':'O(HF) worst-case, adaptive residual O(sum residual*remaining factors), H<=12,F=8,S<=4','highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary['1080'],ensure_ascii=False,indent=2))
if __name__=='__main__': main()
