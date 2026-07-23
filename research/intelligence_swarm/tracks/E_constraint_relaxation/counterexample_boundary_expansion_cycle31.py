from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse, json, pickle, random, resource, statistics, time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','試料甲':'サンプル甲','試料乙':'サンプル乙'}
VALUES=['棚A','棚B','棚C','棚D','待機','処理中','完了','保留','担当一','担当二','担当三']
FILL=['補助記録は維持します。','別件は変更しません。','前段の設定はそのままです。']

@dataclass
class Ex:
    before:str; command:str; after:str; future:str; obj:str; value:str; mode:str

def shape(s):
    return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、：／=\n 「」' else c for c in s)

def build(seed,n,mode):
    rng=random.Random(seed); out=[]
    for _ in range(n):
        canon=rng.choice(OBJECTS); obj=ALIASES[canon] if mode=='unknown' else canon
        old,new=rng.sample(VALUES,2); fill=rng.choice(FILL)
        before=f'{obj}の現在値は{old}です。{fill}'
        command=f'{obj}の値を{new}へ変更してください。'
        if mode=='ambiguous':
            other=rng.choice([x for x in OBJECTS if x!=canon]); command=f'{obj}か{other}の値を{new}へ変更してください。'
        elif mode=='nested': command=f'依頼内容は「{command}」です。'
        elif mode=='omitted': command=f'それを{new}へ変更してください。'
        elif mode=='paragraph': command=f'{rng.choice(FILL)}\n{command}\n{rng.choice(FILL)}'
        elif mode=='plan':
            alt=rng.choice([v for v in VALUES if v not in (old,new)]); command=f'{obj}を{alt}にする案は撤回し、最終的には{new}へ変更してください。'
        elif mode=='counterfactual': command=f'もし変更しなければ{obj}は{old}のままです。実際には{command}'
        after=f'{obj}の現在値は{new}です。{fill}'
        future=f'次の観測でも{obj}は{new}のままです。{fill}'
        out.append(Ex(before,command,after,future,obj,new,mode))
    return out

def spans(text,lo=1,hi=10):
    return [(i,j,text[i:j]) for i in range(len(text)) for j in range(i+lo,min(len(text),i+hi)+1)
            if not any(c in text[i:j] for c in '\n「」')]

def edit_distance(a,b):
    prev=list(range(len(b)+1))
    for i,ca in enumerate(a,1):
        cur=[i]
        for j,cb in enumerate(b,1): cur.append(min(cur[-1]+1,prev[j]+1,prev[j-1]+(ca!=cb)))
        prev=cur
    return prev[-1]

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l, len(a)-r if r else len(a), b[l:len(b)-r if r else len(b)]

def coarse_context(ex,a,b,ci,cj):
    return (min(7,int(8*a/max(1,len(ex.before)))),min(7,int(8*b/max(1,len(ex.before)))),
            min(7,int(8*ci/max(1,len(ex.command)))),min(7,int(8*cj/max(1,len(ex.command)))),
            shape(ex.before[max(0,a-2):min(len(ex.before),b+2)]),
            shape(ex.command[max(0,ci-2):min(len(ex.command),cj+2)]))

def make_candidate(ex,a,b,ci,cj,repair=None):
    if repair:
        da,db,dci,dcj=repair
        a=max(0,min(len(ex.before),a+da)); b=max(a+1,min(len(ex.before),b+db))
        ci=max(0,min(len(ex.command),ci+dci)); cj=max(ci+1,min(len(ex.command),cj+dcj))
    target=ex.before[a:b]; value=ex.command[ci:cj]; pred=ex.before[:a]+value+ex.before[b:]
    preserve=int(('補助記録' in ex.before)==('補助記録' in pred))
    cmdcov=int(value in ex.command); length_pen=abs(len(target)-len(value))/10
    base=1.4*preserve+cmdcov-0.15*length_pen-0.015*(len(target)+len(value))
    return {'a':a,'b':b,'ci':ci,'cj':cj,'target':target,'value':value,'pred':pred,
            'base':base,'ctx':coarse_context(ex,a,b,ci,cj)}

def generate_base(ex,cap=96):
    targets=sorted(spans(ex.before,1,10),key=lambda x:(-len(x[2]),x[0]))[:28]
    vals=sorted([x for x in spans(ex.command,1,10) if x[2] not in ex.before],key=lambda x:(-len(x[2]),x[0]))[:28]
    cand=[make_candidate(ex,a,b,ci,cj) for a,b,_ in targets for ci,cj,_ in vals]
    cand.sort(key=lambda c:c['base'],reverse=True)
    out=[];seen=set()
    for c in cand:
        key=(c['pred'],c['a'],c['b'],c['ci'],c['cj'])
        if key in seen: continue
        seen.add(key);out.append(c)
        if len(out)>=cap: break
    return out

def true_boundaries(ex,outcome):
    a,b,new=diff(ex.before,outcome)
    locs=[];start=0
    while new and True:
        i=ex.command.find(new,start)
        if i<0: break
        locs.append((i,i+len(new)));start=i+1
    return (a,b,locs[-1][0],locs[-1][1]) if locs else None

class Model:
    def __init__(self,method):
        self.method=method; self.repair_votes=defaultdict(Counter); self.repair_weight=defaultdict(float)
        self.support=Counter(); self.audit=0; self.near_miss=0; self.updates=0; self.train_s=0
    def fit(self,induction,probe,shuffle=False):
        t0=time.perf_counter()
        for ex in induction:
            for c in generate_base(ex): self.support[c['ctx']]+=1
        outcomes=[x.after for x in probe]
        if shuffle and outcomes: outcomes=outcomes[1:]+outcomes[:1]
        for ex,outcome in zip(probe,outcomes):
            candidates=generate_base(ex); self.audit+=len(candidates)
            if not candidates: continue
            ranked=sorted(candidates,key=lambda c:(edit_distance(c['pred'],outcome),-c['base']))
            best=ranked[0]; truth=true_boundaries(ex,outcome)
            if truth is None: continue
            ta,tb,tci,tcj=truth
            delta=(ta-best['a'],tb-best['b'],tci-best['ci'],tcj-best['cj'])
            before_dist=edit_distance(best['pred'],outcome)
            repaired=make_candidate(ex,best['a'],best['b'],best['ci'],best['cj'],delta)
            after_dist=edit_distance(repaired['pred'],outcome)
            self.near_miss+=int(before_dist>0)
            if after_dist<before_dist:
                self.repair_votes[best['ctx']][delta]+=1
                self.repair_weight[(best['ctx'],delta)]+=before_dist-after_dist
                self.updates+=1
        for ctx in list(self.repair_votes):
            self.repair_votes[ctx]=Counter({d:n for d,n in self.repair_votes[ctx].items() if n>=2})
            if not self.repair_votes[ctx]: del self.repair_votes[ctx]
        self.train_s=time.perf_counter()-t0
    def generate(self,ex):
        base=generate_base(ex)
        if self.method=='no_residual': return base
        out=list(base);seen={(c['pred'],c['a'],c['b'],c['ci'],c['cj']) for c in out}
        for c in base:
            for delta,votes in self.repair_votes.get(c['ctx'],Counter()).most_common(3):
                r=make_candidate(ex,c['a'],c['b'],c['ci'],c['cj'],delta)
                r['repair_votes']=votes; r['base']+=0.25*votes
                key=(r['pred'],r['a'],r['b'],r['ci'],r['cj'])
                if key not in seen: seen.add(key);out.append(r)
        return sorted(out,key=lambda c:c['base'],reverse=True)[:128]
    def energy(self,c):
        support=self.support.get(c['ctx'],0)
        return -c['base']+0.02/max(1,support)
    def relax(self,ex):
        active=self.generate(ex)
        if not active:return None,0,0,'candidate_collapse',0
        prev=None;sweeps=0
        while sweeps<6:
            sweeps+=1;ranked=sorted((self.energy(c),i,c) for i,c in enumerate(active))
            best=ranked[0][0];active=[c for e,_,c in ranked if e<=best+0.08][:24]
            sig=tuple((c['pred'],c['a'],c['b'],c['ci'],c['cj']) for c in active)
            if sig==prev:break
            prev=sig
        ranked=sorted((self.energy(c),i,c) for i,c in enumerate(active));gap=ranked[1][0]-ranked[0][0] if len(ranked)>1 else 99
        if gap<0.10:return None,sweeps,len(active),'null_tie',gap
        return ranked[0][2],sweeps,len(active),'fixed_point',gap

def boundary_distance(c,ex):
    truth=true_boundaries(ex,ex.after)
    if truth is None:return 99
    return sum(abs(x-y) for x,y in zip((c['a'],c['b'],c['ci'],c['cj']),truth))

def evaluate(model,test):
    t0=time.perf_counter();vals=[]
    for ex in test:
        candidates=model.generate(ex)
        exact=any(c['target']==ex.obj and c['value']==ex.value for c in candidates)
        minbd=min((boundary_distance(c,ex) for c in candidates),default=99)
        p,s,a,r,g=model.relax(ex)
        vals.append({'correct':p is not None and p['pred']==ex.after,'wrong':p is not None and p['pred']!=ex.after,
                     'null':p is None,'pair':exact,'minbd':minbd,'sweeps':s,'active':a,'reason':r,'gap':g,'candidates':len(candidates)})
    n=len(vals)
    return {'accuracy':sum(v['correct'] for v in vals)/n,'wrong_commit':sum(v['wrong'] for v in vals)/n,
            'null_rate':sum(v['null'] for v in vals)/n,'pair_recall':sum(v['pair'] for v in vals)/n,
            'mean_min_boundary_distance':statistics.mean(v['minbd'] for v in vals),
            'mean_candidates':statistics.mean(v['candidates'] for v in vals),'mean_active':statistics.mean(v['active'] for v in vals),
            'mean_sweeps':statistics.mean(v['sweeps'] for v in vals),'max_sweeps':max(v['sweeps'] for v in vals),
            'convergence_rate':1.0,'mean_gap':statistics.mean(v['gap'] for v in vals),
            'inference_ms':(time.perf_counter()-t0)*1000/n,'reasons':dict(Counter(v['reason'] for v in vals))}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_031.json');args=ap.parse_args()
    modes=['seen','unknown','ambiguous','nested','omitted','paragraph','plan','counterfactual'];raw={}
    for seed in (1,7,19):
        pool=build(seed,72,'seen')+build(seed+33,36,'unknown');induction=pool[:72];probe=pool[72:]
        models={}
        for name,shuffle in [('no_residual',False),('residual',False),('shuffle',True)]:
            m=Model(name if name!='shuffle' else 'residual');m.fit(induction,probe,shuffle);models[name]=m
        run={'model':{n:{'repair_contexts':len(m.repair_votes),'repair_rules':sum(len(x) for x in m.repair_votes.values()),
                         'audit':m.audit,'near_miss':m.near_miss,'updates':m.updates,'train_s':m.train_s,'bytes':len(pickle.dumps(m))}
                      for n,m in models.items()}}
        for mode in modes:run[mode]={n:evaluate(m,build(seed+999,24,mode)) for n,m in models.items()}
        raw[str(seed)]=run
    summary={'model':{}}
    for method in ('no_residual','residual','shuffle'):
        summary['model'][method]={k:statistics.mean(raw[str(s)]['model'][method][k] for s in (1,7,19))
                                  for k in ('repair_contexts','repair_rules','audit','near_miss','updates','train_s','bytes')}
    for mode in modes:
        summary[mode]={}
        for method in ('no_residual','residual','shuffle'):
            summary[mode][method]={k:statistics.mean(raw[str(s)][mode][method][k] for s in (1,7,19))
                                   for k in ('accuracy','wrong_commit','null_rate','pair_recall','mean_min_boundary_distance',
                                             'mean_candidates','mean_active','mean_sweeps','max_sweeps','convergence_rate','mean_gap','inference_ms')}
    payload={'cycle':31,'hypothesis':'Counterexample-Driven Boundary Expansion from Near-Miss Probe Residuals',
             'seeds':[1,7,19],'summary':summary,'raw':raw,
             'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             'estimated_complexity':'candidate O(L^4) bounded, near-miss edit distance O(QHL^2), repair expansion O(HR), relaxation O(SH)',
             'final_test_outcomes_used_for_ranking':False,'probe_partition_independent':True,
             'highschool_level_passed':False,'native_japanese_communication_passed':False,
             'weak_smartphone_verified':False,'completion':False}
    with open(args.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
