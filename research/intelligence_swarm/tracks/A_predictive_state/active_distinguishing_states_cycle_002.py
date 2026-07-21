import random,time,json,resource,statistics,sys
from collections import defaultdict,Counter

NAMES=['葵','蓮','凛','空','海','陸']
COLORS=['赤','青','緑','白']
PLACES=['棚A','棚B','棚C','棚D']
ALIASES={'色':['色は','色については','見た目は'],'場所':['場所は','置き場は','どこかというと']}

def episode(rng):
    n=rng.choice(NAMES); c=rng.choice(COLORS); p=rng.choice(PLACES); style=rng.randrange(3)
    return n,c,p,f'{n}の{ALIASES["色"][style]}{c}です。',f'{n}の{ALIASES["場所"][style]}{p}です。'

def observations(ep,mode):
    if mode=='color_only': return [ep[3]]
    if mode=='place_only': return [ep[4]]
    if mode=='both': return [ep[3],ep[4]]
    return []

def parse_surface(text):
    hits=[]
    for n in NAMES:
        if n in text: hits.append(('id',n))
    for v in COLORS+PLACES:
        if v in text: hits.append(('value',v))
    return hits

class Passive:
    def infer(self,obs):
        vals=[]
        for t in obs: vals += [v for typ,v in parse_surface(t) if typ=='value']
        c=next((v for v in vals if v in COLORS),'赤'); p=next((v for v in vals if v in PLACES),'棚A')
        return c,p,1

class Active:
    def __init__(self,train):
        self.states={(e[1],e[2]) for e in train}; self.queries=['q0','q1']
    def candidates(self,obs):
        vals=[]
        for t in obs: vals += [v for typ,v in parse_surface(t) if typ=='value']
        cand=set(self.states)
        for v in vals:
            if v in COLORS: cand={s for s in cand if s[0]==v}
            if v in PLACES: cand={s for s in cand if s[1]==v}
        return cand
    def choose(self,cand):
        if len(cand)<=1:return None
        best=None; score_best=-1
        for q in self.queries:
            groups=defaultdict(int)
            for c,p in cand: groups[c if q=='q0' else p]+=1
            score=len(cand)-sum(v*v for v in groups.values())/len(cand)
            if score>score_best: best,score_best=q,score
        return best
    def infer(self,obs,true_state=None,allow_query=True):
        cand=self.candidates(obs); reads=len(cand); q=None
        if allow_query and len(cand)>1:
            q=self.choose(cand)
            if true_state is not None:
                ans=true_state[0] if q=='q0' else true_state[1]
                cand={s for s in cand if (s[0] if q=='q0' else s[1])==ans}; reads+=len(cand)
        if len(cand)==1:
            c,p=next(iter(cand)); return c,p,q,reads
        return None,None,q,reads

def run(seed,ntrain,ntest=240):
    rng=random.Random(seed); train=[episode(rng) for _ in range(ntrain)]; active=Active(train); passive=Passive()
    metrics={m:Counter() for m in ['passive','active_no_query','active']}; modes=['color_only','place_only','both','none']
    t0=time.perf_counter()
    for _ in range(ntest):
        ep=episode(rng); true=(ep[1],ep[2]); obs=observations(ep,rng.choice(modes))
        c,p,r=passive.infer(obs); metrics['passive']['ok']+=int((c,p)==true); metrics['passive']['reads']+=r
        c,p,q,r=active.infer(obs,true,True); metrics['active']['ok']+=int((c,p)==true); metrics['active']['reads']+=r; metrics['active']['queries']+=int(q is not None)
        c,p,q,r=active.infer(obs,true,False); metrics['active_no_query']['ok']+=int((c,p)==true); metrics['active_no_query']['reads']+=r
    dt=time.perf_counter()-t0
    inconsistent=0
    for _ in range(60):
        ep=episode(rng); cand=active.candidates(observations(ep,'color_only')); q=active.choose(cand)
        narrowed={s for s in cand if (s[0] if q=='q0' else s[1])=='不存在'}
        inconsistent+=int(not narrowed)
    return {'seed':seed,'train':ntrain,'states':len(active.states),'model_bytes':sys.getsizeof(active.states)+sum(sys.getsizeof(x) for x in active.states),'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'eval_seconds':dt,'counter_abstain':inconsistent/60,**{k:{'accuracy':v['ok']/ntest,'mean_reads':v['reads']/ntest,'query_rate':v['queries']/ntest} for k,v in metrics.items()}}

def main():
    rows=[run(s,n) for n in (32,128,512) for s in (1,7,19)]; agg={}
    for n in (32,128,512):
        rr=[r for r in rows if r['train']==n]; agg[str(n)]={}
        for m in ('passive','active_no_query','active'):
            agg[str(n)][m]={'accuracy':statistics.mean(r[m]['accuracy'] for r in rr),'reads':statistics.mean(r[m]['mean_reads'] for r in rr),'query_rate':statistics.mean(r[m]['query_rate'] for r in rr)}
        agg[str(n)].update({'states':statistics.mean(r['states'] for r in rr),'model_bytes':max(r['model_bytes'] for r in rr),'peak_rss_kib':max(r['peak_rss_kib'] for r in rr),'eval_seconds':statistics.mean(r['eval_seconds'] for r in rr),'counter_abstain':statistics.mean(r['counter_abstain'] for r in rr)})
    print(json.dumps({'aggregate':agg,'runs':rows},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
