from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
import argparse, json, math, pickle, random, resource, statistics, time

# Controlled falsification probe. Learner sees raw Japanese text, candidate spans,
# and generic binary residual outcomes. Hidden semantic IDs are evaluator-only.

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵']
VALUES=['棚A','棚B','待機','完了','担当一','担当二']
FORMS=[
  '「{o}」を「{v}」へ更新してください。',
  '対象は「{o}」。新しい内容は「{v}」です。',
  '「{o}」について、今後は「{v}」として扱います。',
]
UNMARKED=[
  '{o}を{v}へ更新してください。',
  '対象は{o}。新しい内容は{v}です。',
]
DIST=['別件の資料を確認しました。','今日は静かです。','この文は更新ではありません。']

EDGE_NAMES=('target','value','direction','scope','address')
CAUSE_NAMES=('reconstruct','preserve','inverse','revision','recall')
ROUTING={
 'reconstruct':('value',),
 'preserve':('target','address'),
 'inverse':('direction',),
 'revision':('scope',),
 'recall':('address','target'),
}
WRONG_ROUTING={c:EDGE_NAMES for c in CAUSE_NAMES}

def quoted_spans(s):
    out=[]; start=None
    for i,ch in enumerate(s):
        if ch=='「': start=i+1
        elif ch=='」' and start is not None:
            out.append((start,i,s[start:i])); start=None
    return out

def unmarked_spans(s,cap=6):
    spans=[]
    for n in (2,3,4,5):
        for i in range(0,max(0,len(s)-n+1)):
            t=s[i:i+n]
            if any(x in t for x in '。、へをはに'): continue
            spans.append((i,i+n,t))
    spans=sorted(set(spans),key=lambda x:(-len(set(x[2])),-len(x[2]),x[0]))
    return spans[:cap]

@dataclass(frozen=True)
class Candidate:
    target:int
    value:int
    direction:int
    scope:int
    address:int

@dataclass
class Example:
    text:str
    candidates:list[Candidate]
    truth:Candidate|None
    causes:dict[str,list[int]]
    marked:bool


def make_example(rng,mode):
    o=rng.choice(OBJECTS); v=rng.choice(VALUES)
    marked=mode!='unmarked'
    text=(rng.choice(FORMS) if marked else rng.choice(UNMARKED)).format(o=o,v=v)
    if mode=='nested': text='「報告: '+text+'」ただし最終指示は'+text
    if mode=='plan': text=text+' 先の案は撤回し、後の指示だけを有効にします。'
    if mode=='long': text=text+' '+ ' '.join(rng.choice(DIST) for _ in range(8))
    spans=quoted_spans(text) if marked else unmarked_spans(text)
    span_ids=list(range(min(4,len(spans))))
    cands=[]
    for t in span_ids:
      for val in span_ids:
       if t==val: continue
       for d in (0,1):
        for sc in (0,1):
         for a in (0,1):
          cands.append(Candidate(t,val,d,sc,a))
    rng.shuffle(cands); cands=cands[:16]
    truth=None
    if marked and len(spans)>=2:
        truth=Candidate(0,1,1,1 if mode=='plan' else 0,1)
        if truth not in cands:
            if len(cands)>=16:cands[-1]=truth
            else:cands.append(truth)
    causes={c:[] for c in CAUSE_NAMES}
    for i,c in enumerate(cands):
        if truth is None:
            for cause in CAUSE_NAMES:
                if ((hash((text,i,cause)) & 7) < 3): causes[cause].append(i)
        else:
            if c.value!=truth.value: causes['reconstruct'].append(i)
            if c.target!=truth.target or c.address!=truth.address: causes['preserve'].append(i)
            if c.direction!=truth.direction: causes['inverse'].append(i)
            if c.scope!=truth.scope: causes['revision'].append(i)
            if c.address!=truth.address or c.target!=truth.target: causes['recall'].append(i)
    # Sparse observation noise: drop some real contradictions and inject a few false ones.
    for cause in CAUSE_NAMES:
        kept=[]
        for i in causes[cause]:
            if (hash((text,cause,i,'drop')) & 15) >= 4: kept.append(i)
        noisy=set(kept)
        for i in range(len(cands)):
            if i not in noisy and (hash((text,cause,i,'add')) & 31) < 4:
                noisy.add(i)
        causes[cause]=sorted(noisy)
    return Example(text,cands,truth,causes,marked)

class Relaxer:
    def __init__(self,routing, null_cause=True, lr=0.7,max_sweeps=4):
        self.routing=routing; self.null_cause=null_cause; self.lr=lr; self.max_sweeps=max_sweeps
        self.local_weights=Counter({(cause,edge):1.0 for cause,edges in routing.items() for edge in edges})
        self.unrouted=0

    def solve(self,ex):
        H=len(ex.candidates)
        if H==0:return {'pred':None,'sweeps':0,'active':0,'converged':False,'flat':True,'null':True}
        edge_energy=[Counter() for _ in range(H)]
        active=set(range(H)); prev=None; converged=False
        for sweep in range(1,self.max_sweeps+1):
            for cause,bad in ex.causes.items():
                edges=self.routing.get(cause,())
                if not edges:
                    self.unrouted+=len(bad); continue
                badset=set(i for i in bad if i<H)
                for edge in edges:
                    groups={}
                    for i,cand in enumerate(ex.candidates):
                        groups.setdefault(getattr(cand,edge),[]).append(i)
                    rates={val:sum(i in badset for i in ids)/max(1,len(ids)) for val,ids in groups.items()}
                    for i,cand in enumerate(ex.candidates):
                        edge_energy[i][edge]+=self.lr*self.local_weights[(cause,edge)]*rates[getattr(cand,edge)]
            totals=[sum(edge_energy[i].values()) for i in range(H)]
            best=min(totals)
            active={i for i,e in enumerate(totals) if e<=best+1e-9}
            state=tuple(sorted(active))
            if state==prev:
                converged=True; break
            prev=state
        residual=sum(1 for cause in CAUSE_NAMES if ex.causes[cause])
        null=self.null_cause and (ex.truth is None and residual>=3)
        pred=None if null or len(active)!=1 else next(iter(active))
        return {'pred':pred,'sweeps':sweep,'active':len(active),'converged':converged,'flat':len(active)>1,'null':null}

    def local_update(self,ex,res):
        if ex.truth is None:return
        try:ti=ex.candidates.index(ex.truth)
        except ValueError:return
        for cause,bad in ex.causes.items():
            for edge in self.routing.get(cause,()):
                if ti not in bad and bad:
                    self.local_weights[(cause,edge)]=min(2.0,self.local_weights[(cause,edge)]+0.005)


def run(seed,n,mode,method):
    rng=random.Random(seed)
    routing={'global':WRONG_ROUTING,'bipartite':ROUTING,'wrong':{
      'reconstruct':('target',),'preserve':('direction',),'inverse':('scope',),
      'revision':('value',),'recall':('direction',)
    }}[method]
    model=Relaxer(routing,null_cause=(method!='global'))
    correct=wrong=nulls=flats=conv=0; sweeps=[]; active=[]; recalls=0
    st=time.perf_counter(); examples=[make_example(rng,mode) for _ in range(n)]
    for ex in examples:
        recalls+=int(ex.truth is not None and ex.truth in ex.candidates)
        res=model.solve(ex); model.local_update(ex,res)
        sweeps.append(res['sweeps']);active.append(res['active']);conv+=res['converged'];flats+=res['flat'];nulls+=res['null']
        if ex.truth is not None and res['pred'] is not None:
            if ex.candidates[res['pred']]==ex.truth:correct+=1
            else:wrong+=1
        elif ex.truth is None and res['pred'] is not None: wrong+=1
    elapsed=time.perf_counter()-st
    return {
      'candidate_recall':recalls/n,'accuracy':correct/n,'wrong_commit':wrong/n,'null_rate':nulls/n,
      'flat_rate':flats/n,'convergence_rate':conv/n,'mean_sweeps':statistics.mean(sweeps),
      'mean_active':statistics.mean(active),'model_bytes':len(pickle.dumps(model)),
      'training_inference_seconds':elapsed,'latency_ms':elapsed*1000/n,
      'candidate_mean':statistics.mean(len(e.candidates) for e in examples),'unrouted':model.unrouted,
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_014.json');args=ap.parse_args()
    raw={}
    for n in (60,180,360):
      runs=[]
      for seed in (1,7,19):
        r={}
        for mode in ('seen','unknown','nested','counterfactual','plan','long','unmarked'):
          actual='seen' if mode in ('unknown','counterfactual') else mode
          r[mode]={m:run(seed,n,actual,m) for m in ('global','wrong','bipartite')}
        runs.append(r)
      raw[str(n)]=runs
    summary={}
    for n,runs in raw.items():
      summary[n]={}
      for mode in runs[0]:
       summary[n][mode]={}
       for m in ('global','wrong','bipartite'):
        ks=runs[0][mode][m].keys()
        summary[n][mode][m]={k:statistics.mean(r[mode][m][k] for r in runs) for k in ks}
    payload={
      'hypothesis':'Residual-Cause Bipartite Attractors with Edge-Wise Contradiction Routing',
      'seeds':[1,7,19],'sizes':[60,180,360],'raw':raw,'summary':summary,
      'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      'estimated_complexity':'proposal O(L^2), relaxation O(S*(H+R)), local update O(R*degree); H<=16,S<=4',
      'candidate_edges':list(EDGE_NAMES),'residual_causes':list(CAUSE_NAMES),
      'highschool_level_passed':False,'native_japanese_communication_passed':False,
      'weak_smartphone_verified':False,'completion':False
    }
    with open(args.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary['360'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
