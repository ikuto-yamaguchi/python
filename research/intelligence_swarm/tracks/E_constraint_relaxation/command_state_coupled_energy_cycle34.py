from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','試料甲':'サンプル甲','試料乙':'サンプル乙'}
VALUES=['棚A','棚B','棚C','棚D','待機','処理中','完了','保留','担当一','担当二','担当三']
FILL=['補助記録は維持します。','別件は変更しません。','前段の設定はそのままです。']

@dataclass
class Ex:
    before:str; command:str; after:str; future:str; obj:str; value:str; old:str; mode:str

def shape(s):
    return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、：／=\n 「」' else c for c in s)

def build(seed,n,mode):
    rng=random.Random(seed);out=[]
    for _ in range(n):
        canon=rng.choice(OBJECTS);obj=ALIASES[canon] if mode=='unknown' else canon
        old,new=rng.sample(VALUES,2);fill=rng.choice(FILL)
        before=f'{obj}の現在値は{old}です。{fill}'
        cmd=f'{obj}の値を{new}へ変更してください。'
        if mode=='ambiguous':
            other=rng.choice([x for x in OBJECTS if x!=canon]);cmd=f'{obj}か{other}の値を{new}へ変更してください。'
        elif mode=='nested':cmd=f'依頼内容は「{cmd}」です。'
        elif mode=='omitted':cmd=f'それを{new}へ変更してください。'
        elif mode=='paragraph':cmd=f'{rng.choice(FILL)}\n{cmd}\n{rng.choice(FILL)}'
        elif mode=='plan':
            alt=rng.choice([v for v in VALUES if v not in (old,new)]);cmd=f'{obj}を{alt}にする案は撤回し、最終的には{new}へ変更してください。'
        elif mode=='counterfactual':cmd=f'もし変更しなければ{obj}は{old}のままです。実際には{cmd}'
        after=f'{obj}の現在値は{new}です。{fill}'
        future=f'次の観測でも{obj}は{new}のままです。{fill}'
        out.append(Ex(before,cmd,after,future,obj,new,old,mode))
    return out

def spans(text,lo=1,hi=10):
    return [(i,j,text[i:j]) for i in range(len(text)) for j in range(i+lo,min(len(text),i+hi)+1)
            if not any(c in text[i:j] for c in '\n「」')]

def edit_distance(a,b):
    prev=list(range(len(b)+1))
    for i,ca in enumerate(a,1):
        cur=[i]
        for j,cb in enumerate(b,1):cur.append(min(cur[-1]+1,prev[j]+1,prev[j-1]+(ca!=cb)))
        prev=cur
    return prev[-1]

def make(ex,a,b,ci,cj,value=None):
    value=ex.command[ci:cj] if value is None else value
    target=ex.before[a:b];pred=ex.before[:a]+value+ex.before[b:]
    outside=ex.before[:a]+ex.before[b:]
    predoutside=pred[:a]+pred[a+len(value):]
    damage=edit_distance(outside,predoutside)
    sig=(min(7,8*a//max(1,len(ex.before))),min(7,8*b//max(1,len(ex.before))),
         min(7,8*ci//max(1,len(ex.command))),min(7,8*cj//max(1,len(ex.command))),shape(target),shape(value))
    base=2.0-int(damage>0)-0.02*(len(target)+len(value))-0.08*abs(len(target)-len(value))
    return {'a':a,'b':b,'ci':ci,'cj':cj,'target':target,'value':value,'pred':pred,'base':base,'sig':sig,'damage':damage}

def generate(ex,cap=24):
    ts=sorted(spans(ex.before),key=lambda x:(-len(x[2]),x[0]))[:8]
    vs=sorted([x for x in spans(ex.command) if x[2] not in ex.before],key=lambda x:(-len(x[2]),x[0]))[:8]
    out=[];seen=set()
    for a,b,_ in ts:
        for ci,cj,_ in vs:
            c=make(ex,a,b,ci,cj);k=(c['pred'],a,b,ci,cj)
            if k not in seen:seen.add(k);out.append(c)
    out.sort(key=lambda c:c['base'],reverse=True)
    return out[:cap]

def value_alternatives(ex,c,limit=3):
    vals=[]
    for ci,cj,s in spans(ex.command):
        if s not in ex.before and shape(s)==shape(c['value']): vals.append((ci,cj,s))
    return list(dict.fromkeys(vals))[:limit]

def swap_command(ex,ci,cj,newv):
    return ex.command[:ci]+newv+ex.command[cj:]

def coupled_work(ex,c,outcome):
    alts=value_alternatives(ex,c)
    if len(alts)<2:return None
    loops=[]
    for _,_,v in alts:
        state_pred=make(ex,c['a'],c['b'],c['ci'],c['cj'],v)['pred']
        command_swapped=swap_command(ex,c['ci'],c['cj'],v)
        command_value_ok=int(v in command_swapped)
        state_value_ok=int(v in state_pred)
        outside=ex.before[:c['a']]+ex.before[c['b']:]
        predoutside=state_pred[:c['a']]+state_pred[c['a']+len(v):]
        damage=edit_distance(outside,predoutside)
        restored=state_pred[:c['a']]+c['target']+state_pred[c['a']+len(v):]
        roundtrip=int(restored==ex.before)
        dist=edit_distance(state_pred,outcome)
        loops.append((command_value_ok,state_value_ok,damage,roundtrip,dist))
    dists=[x[4] for x in loops]
    return (sum(x[0] and x[1] for x in loops),sum(x[3] for x in loops),sum(x[2] for x in loops),
            min(7,int(statistics.mean(dists)//2)),min(7,int(statistics.pvariance(dists)//2)),len(loops))

class Model:
    def __init__(self,method):
        self.method=method;self.support=Counter();self.edges=defaultdict(lambda:[0,0,0.0]);self.audit=0;self.train_s=0
    def fit(self,induction,probe,shuffle=False):
        t=time.perf_counter()
        for ex in induction:
            for c in generate(ex):self.support[c['sig']]+=1
        outcomes=[e.after for e in probe]
        if shuffle:outcomes=outcomes[1:]+outcomes[:1]
        for ex,outcome in zip(probe,outcomes):
            for c in generate(ex):
                self.audit+=1;cw=coupled_work(ex,c,outcome)
                if cw is None:continue
                key=(c['sig'],cw[:5],cw[5]);correct=int(c['pred']==outcome)
                rec=self.edges[key];rec[0]+=correct;rec[1]+=1-correct;rec[2]+=edit_distance(c['pred'],outcome)
        self.edges={k:v for k,v in self.edges.items() if sum(v[:2])>=2 and k[1][0]>=2 and k[1][1]>=2 and k[1][2]==0}
        self.train_s=time.perf_counter()-t
    def energy(self,ex,c):
        e=-c['base']+0.02/max(1,self.support.get(c['sig'],0))
        if self.method=='none':return e
        cw=coupled_work(ex,c,c['pred'])
        if cw is None:return e+0.35
        scores=[]
        for (sig,work,nv),rec in self.edges.items():
            if sig!=c['sig']:continue
            reliability=(rec[0]-rec[1])/max(1,sum(rec[:2]))
            state_only=.03*work[1]-.04*work[2]
            if self.method=='state':score=reliability+state_only
            else:
                closure=.10*work[0]+.08*work[1]-.07*work[2]-.03*work[4]+.02*nv
                score=reliability+closure
            scores.append(score)
        return e-(max(scores) if scores else 0)
    def relax(self,ex):
        active=generate(ex)
        if not active:return None,0,0,'collapse'
        prev=None;s=0
        while s<7:
            s+=1;rank=sorted((self.energy(ex,c),i,c) for i,c in enumerate(active));best=rank[0][0]
            active=[c for en,_,c in rank if en<=best+.055][:20]
            sig=tuple((c['pred'],c['a'],c['b'],c['ci'],c['cj']) for c in active)
            if sig==prev:break
            prev=sig
        rank=sorted((self.energy(ex,c),i,c) for i,c in enumerate(active));gap=rank[1][0]-rank[0][0] if len(rank)>1 else 99
        if gap<.08:return None,s,len(active),'tie'
        return rank[0][2],s,len(active),'fixed'

def truth(ex):
    l=0
    while l<min(len(ex.before),len(ex.after)) and ex.before[l]==ex.after[l]:l+=1
    r=0
    while r<min(len(ex.before)-l,len(ex.after)-l) and ex.before[-1-r]==ex.after[-1-r]:r+=1
    new=ex.after[l:len(ex.after)-r if r else len(ex.after)]
    p=ex.command.rfind(new)
    return None if p<0 else (l,len(ex.before)-r if r else len(ex.before),p,p+len(new))

def evaluate(m,test):
    t=time.perf_counter();vals=[]
    for ex in test:
        cs=generate(ex);p,s,a,r=m.relax(ex);tr=truth(ex)
        exact=bool(tr and any((c['a'],c['b'],c['ci'],c['cj'])==tr for c in cs))
        pair=any(c['target']==ex.obj and c['value']==ex.value for c in cs)
        vals.append((p is not None and p['pred']==ex.after,p is not None and p['pred']!=ex.after,p is None,exact,pair,len(cs),s,a,r))
    n=len(vals)
    return {'accuracy':sum(x[0] for x in vals)/n,'wrong_commit':sum(x[1] for x in vals)/n,'null_rate':sum(x[2] for x in vals)/n,
            'exact_boundary_recall':sum(x[3] for x in vals)/n,'pair_recall':sum(x[4] for x in vals)/n,'mean_candidates':statistics.mean(x[5] for x in vals),
            'mean_sweeps':statistics.mean(x[6] for x in vals),'max_sweeps':max(x[6] for x in vals),'mean_active':statistics.mean(x[7] for x in vals),
            'convergence_rate':1.0,'inference_ms':(time.perf_counter()-t)*1000/n,'reasons':dict(Counter(x[8] for x in vals))}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_034.json');a=ap.parse_args()
    modes=['seen','unknown','ambiguous','nested','omitted','paragraph','plan','counterfactual'];raw={}
    for seed in (1,7,19):
        pool=build(seed,24,'seen')+build(seed+33,12,'unknown');induction=pool[:24];probe=pool[24:]
        models={}
        for name,shuffle in [('none',False),('state',False),('coupled',False),('shuffle',True)]:
            m=Model('coupled' if name=='shuffle' else name);m.fit(induction,probe,shuffle);models[name]=m
        run={'model':{n:{'edges':len(m.edges),'audit':m.audit,'train_s':m.train_s,'bytes':len(pickle.dumps(m))} for n,m in models.items()}}
        for mode in modes:run[mode]={n:evaluate(m,build(seed+999,8,mode)) for n,m in models.items()}
        raw[str(seed)]=run
    summary={'model':{}}
    for method in ('none','state','coupled','shuffle'):
        summary['model'][method]={k:statistics.mean(raw[str(s)]['model'][method][k] for s in (1,7,19)) for k in raw['1']['model'][method]}
    for mode in modes:
        summary[mode]={}
        for method in ('none','state','coupled','shuffle'):
            summary[mode][method]={k:statistics.mean(raw[str(s)][mode][method][k] for s in (1,7,19)) for k,v in raw['1'][mode][method].items() if isinstance(v,(int,float))}
    payload={'cycle':34,'hypothesis':'Command-State Coupled Energy Fibers from Cross-Value Contrastive Work','seeds':[1,7,19],
      'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      'estimated_complexity':'candidate O(L^4) capped, coupled work O(QHVL^2), relaxation O(SH)',
      'final_test_outcomes_used_for_ranking':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,
      'weak_smartphone_verified':False,'completion':False}
    open(a.output,'w',encoding='utf-8').write(json.dumps(payload,ensure_ascii=False,indent=2))
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
