from __future__ import annotations
import argparse, json, math, pickle, random, resource, statistics, time
from dataclasses import dataclass

@dataclass(frozen=True)
class Candidate:
    target:int; value:int; scope:int; revision:int

def make_case(rng, mode):
    # Controlled candidate graph. Labels are evaluator-only.
    target=rng.randrange(3); value=rng.randrange(3); scope=rng.randrange(2); revision=rng.randrange(2)
    gold=Candidate(target,value,scope,revision)
    cands=[]
    for t in range(3):
      for v in range(3):
       for s in range(2):
        for r in range(2):
         cands.append(Candidate(t,v,s,r))
    if mode=='unmarked':
      # open-form proposal failure: correct graph unavailable
      cands=[c for c in cands if c!=gold][:24]
    else:
      rng.shuffle(cands); cands=cands[:31]
      if gold not in cands: cands.append(gold)
    return gold,cands

def whole_factor(c):
    # Deliberately aliases target/scope and value/revision.
    return (c.target%2, c.value%2)

def probes(c):
    return {
      'target_swap':c.target,
      'value_swap':c.value,
      'scope_remove':c.scope,
      'revision_remove':c.revision,
      'inverse':(c.target+c.value)%3,
      'future_recall':(c.scope<<1)|c.revision,
    }

def choose(gold,cands,method,max_sweeps=4):
    active=list(cands); acquired=[]; evals=0
    base=whole_factor(gold)
    active=[c for c in active if whole_factor(c)==base]
    evals+=len(cands)
    if method=='whole':
      return (active[0] if len(active)==1 else None),len(active),0,evals,1
    all_names=list(probes(gold))
    if method=='full':
      selected=all_names
    else:
      selected=[]
      remaining=all_names[:]
      # Greedy residual equivalence splitting: acquire only informative probe.
      while len(active)>1 and remaining and len(selected)<max_sweeps:
        best=None
        for name in remaining:
          groups={}
          for c in active: groups.setdefault(probes(c)[name],0); groups[probes(c)[name]]+=1
          gain=len(active)-max(groups.values())
          evals+=len(active)
          if best is None or gain>best[0]: best=(gain,name)
        gain,name=best
        if gain<=0: break
        selected.append(name); remaining.remove(name)
        gv=probes(gold)[name]
        active=[c for c in active if probes(c)[name]==gv]
    if method=='full':
      for name in selected:
        gv=probes(gold)[name]; active=[c for c in active if probes(c)[name]==gv]; evals+=len(cands)
    return (active[0] if len(active)==1 else None),len(active),len(selected),evals,max(1,len(selected))

def run(seed,n):
 rng=random.Random(seed+n); modes=['seen','ambiguous','nested','counterfactual','revision','unmarked']
 out={}
 for mode in modes:
  rows=[]
  for _ in range(n): rows.append(make_case(rng,mode))
  out[mode]={}
  for method in ['whole','full','adaptive']:
   st=time.perf_counter(); correct=conv=0; residual=[]; acquired=[]; evals=[]; sweeps=[]
   for gold,cands in rows:
    pred,res,k,e,sw=choose(gold,cands,method)
    correct+=pred==gold; conv+=pred is not None; residual.append(res); acquired.append(k); evals.append(e); sweeps.append(sw)
   out[mode][method]={
    'accuracy':correct/n,'convergence_rate':conv/n,'mean_residual':statistics.mean(residual),
    'mean_factors':statistics.mean(acquired),'mean_factor_evals':statistics.mean(evals),
    'mean_sweeps':statistics.mean(sweeps),'active_candidates':statistics.mean([len(c) for _,c in rows]),
    'ms_per_query':(time.perf_counter()-st)*1000/n}
 return out

def summarize(raw):
 s={}
 for n,runs in raw.items():
  s[n]={}
  for mode in runs[0]:
   s[n][mode]={}
   for method in runs[0][mode]:
    s[n][mode][method]={k:statistics.mean(r[mode][method][k] for r in runs) for k in runs[0][mode][method]}
 return s

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_011.json');a=ap.parse_args()
 raw={str(n):[run(seed,n) for seed in (1,7,19)] for n in (60,180,540)}
 model={'factor_pool':['target_swap','value_swap','scope_remove','revision_remove','inverse','future_recall'],'max_sweeps':4}
 payload={'hypothesis':'Adaptive Factor Acquisition by Residual Equivalence Splitting','seeds':[1,7,19],'sizes':[60,180,540],
 'raw':raw,'summary':summarize(raw),'model_bytes':len(pickle.dumps(model)),
 'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
 'complexity':'whole O(H); full O(HF); adaptive O(H + sum residual*remaining factors), F=6, sweeps<=4',
 'free_japanese_integrated_gate':0.0,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
 open(a.output,'w',encoding='utf8').write(json.dumps(payload,ensure_ascii=False,indent=2))
 print(json.dumps(payload['summary']['540'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
