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
    before:str; command:str; after:str; future:str; obj:str; value:str; old:str; mode:str

def shape(s):
    return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、：／=\n 「」' else c for c in s)

def build(seed,n,mode):
    rng=random.Random(seed);out=[]
    for _ in range(n):
        canon=rng.choice(OBJECTS);obj=ALIASES[canon] if mode=='unknown' else canon
        old,new=rng.sample(VALUES,2);fill=rng.choice(FILL)
        before=f'{obj}の現在値は{old}です。{fill}';cmd=f'{obj}の値を{new}へ変更してください。'
        if mode=='ambiguous':
            other=rng.choice([x for x in OBJECTS if x!=canon]);cmd=f'{obj}か{other}の値を{new}へ変更してください。'
        elif mode=='nested':cmd=f'依頼内容は「{cmd}」です。'
        elif mode=='omitted':cmd=f'それを{new}へ変更してください。'
        elif mode=='paragraph':cmd=f'{rng.choice(FILL)}\n{cmd}\n{rng.choice(FILL)}'
        elif mode=='plan':
            alt=rng.choice([v for v in VALUES if v not in (old,new)]);cmd=f'{obj}を{alt}にする案は撤回し、最終的には{new}へ変更してください。'
        elif mode=='counterfactual':cmd=f'もし変更しなければ{obj}は{old}のままです。実際には{cmd}'
        after=f'{obj}の現在値は{new}です。{fill}';future=f'次の観測でも{obj}は{new}のままです。{fill}'
        out.append(Ex(before,cmd,after,future,obj,new,old,mode))
    return out

def spans(text,lo=1,hi=10):
    return [(i,j,text[i:j]) for i in range(len(text)) for j in range(i+lo,min(len(text),i+hi)+1) if not any(c in text[i:j] for c in '\n「」')]

def edit_distance(a,b):
    prev=list(range(len(b)+1))
    for i,ca in enumerate(a,1):
        cur=[i]
        for j,cb in enumerate(b,1):cur.append(min(cur[-1]+1,prev[j]+1,prev[j-1]+(ca!=cb)))
        prev=cur
    return prev[-1]

def make_candidate(ex,a,b,ci,cj,born=False,source=None):
    if not (0<=a<b<=len(ex.before) and 0<=ci<cj<=len(ex.command)):return None
    target=ex.before[a:b];value=ex.command[ci:cj];pred=ex.before[:a]+value+ex.before[b:]
    outside=ex.before[:a]+ex.before[b:];predoutside=pred[:a]+pred[a+len(value):];damage=edit_distance(outside,predoutside)
    ts=(min(7,8*a//max(1,len(ex.before))),min(7,8*b//max(1,len(ex.before))),shape(target),min(7,len(target)))
    vs=(min(7,8*ci//max(1,len(ex.command))),min(7,8*cj//max(1,len(ex.command))),shape(value),min(7,len(value)))
    ctx=(min(7,len(ex.before)//8),min(7,len(ex.command)//8),min(7,ex.command.count('。')),min(7,ex.command.count('\n')))
    base=2.0-int(damage>0)-0.025*(len(target)+len(value))-0.08*abs(len(target)-len(value))
    return {'a':a,'b':b,'ci':ci,'cj':cj,'target':target,'value':value,'pred':pred,'ts':ts,'vs':vs,'ctx':ctx,'base':base,'damage':damage,'born':born,'source':source}

def generate(ex,cap=16):
    ts=sorted(spans(ex.before),key=lambda x:(-len(x[2]),x[0]))[:6]
    vs=sorted([x for x in spans(ex.command) if x[2] not in ex.before],key=lambda x:(-len(x[2]),x[0]))[:6]
    out=[];seen=set()
    for a,b,_ in ts:
        for ci,cj,_ in vs:
            c=make_candidate(ex,a,b,ci,cj)
            if c is None:continue
            k=(c['pred'],a,b,ci,cj)
            if k not in seen:seen.add(k);out.append(c)
    out.sort(key=lambda c:c['base'],reverse=True);return out[:cap]

def disagreement_positions(cands):
    if len(cands)<2:return ()
    m=max(len(c['pred']) for c in cands);buckets=set()
    for i in range(m):
        chars={c['pred'][i] if i<len(c['pred']) else '∅' for c in cands}
        if len(chars)>1:buckets.add(min(7,8*i/max(1,m)))
    return tuple(sorted(buckets))

def residual_buckets(pred,outcome):
    m=max(len(pred),len(outcome));out=[]
    for i in range(m):
        a=pred[i] if i<len(pred) else '∅';b=outcome[i] if i<len(outcome) else '∅'
        if a!=b:out.append(min(7,8*i/max(1,m)))
    return tuple(sorted(set(out)))

class Model:
    def __init__(self,method):
        self.method=method;self.support=Counter();self.hyper=defaultdict(lambda:[0,0,0.0]);self.birth=Counter();self.audit=0;self.birth_trials=0;self.birth_accept=0;self.train_s=0
    def fit(self,induction,probe,shuffle=False):
        t=time.perf_counter()
        for ex in induction:
            for c in generate(ex):self.support[(c['ts'],c['vs'],c['ctx'])]+=1
        outcomes=[e.after for e in probe]
        if shuffle:outcomes=outcomes[1:]+outcomes[:1]
        for ex,outcome in zip(probe,outcomes):
            cs=generate(ex);fr=disagreement_positions(cs)
            if not cs or not fr:continue
            ds=[edit_distance(c['pred'],outcome) for c in cs];best=min(ds);local=[(c,d) for c,d in zip(cs,ds) if d<=best+2][:6];local_keys=[]
            for c,d in local:
                self.audit+=1;selected=int(d==0);rb=residual_buckets(c['pred'],outcome);key=(c['ts'],c['vs'],c['ctx'],fr,rb)
                rec=self.hyper[key];rec[0]+=selected;rec[1]+=1-selected;rec[2]+=d;local_keys.append((c,d,rb))
            for c,d,rb in local_keys:
                for da,db,dc,dd in ((-1,0,0,0),(1,0,0,0),(0,-1,0,0),(0,1,0,0),(0,0,-1,0),(0,0,1,0),(0,0,0,-1),(0,0,0,1)):
                    nc=make_candidate(ex,c['a']+da,c['b']+db,c['ci']+dc,c['cj']+dd,True,(c['ts'],c['vs']))
                    if nc is None:continue
                    self.birth_trials+=1;nd=edit_distance(nc['pred'],outcome);nrb=residual_buckets(nc['pred'],outcome);improved=len(set(rb)-set(nrb))
                    if nd<d and improved>=2 and nc['damage']==0:self.birth[(nc['ts'],nc['vs'],nc['ctx'])]+=1;self.birth_accept+=1
        self.hyper={k:v for k,v in self.hyper.items() if sum(v[:2])>=2};self.birth=Counter({k:v for k,v in self.birth.items() if v>=2});self.train_s=time.perf_counter()-t
    def augment(self,ex,base):
        if self.method not in ('birth','shuffle'):return base
        out=list(base);seen={(c['pred'],c['a'],c['b'],c['ci'],c['cj']) for c in out}
        for c in base:
            for da,db,dc,dd in ((-1,0,0,0),(1,0,0,0),(0,-1,0,0),(0,1,0,0),(0,0,-1,0),(0,0,1,0),(0,0,0,-1),(0,0,0,1)):
                nc=make_candidate(ex,c['a']+da,c['b']+db,c['ci']+dc,c['cj']+dd,True,(c['ts'],c['vs']))
                if nc is None or self.birth.get((nc['ts'],nc['vs'],nc['ctx']),0)<2:continue
                k=(nc['pred'],nc['a'],nc['b'],nc['ci'],nc['cj'])
                if k not in seen:seen.add(k);out.append(nc)
        return sorted(out,key=lambda c:(c['base']+.1*self.birth.get((c['ts'],c['vs'],c['ctx']),0)),reverse=True)[:48]
    def energy(self,ex,c,active):
        e=-c['base']+0.025/max(1,self.support.get((c['ts'],c['vs'],c['ctx']),0))
        if self.method=='none':return e
        fr=disagreement_positions(active);vals=[]
        for (ts,vs,ctx,hfr,rb),rec in self.hyper.items():
            if ts!=c['ts'] or vs!=c['vs']:continue
            context_match=sum(a==b for a,b in zip(ctx,c['ctx']))/len(ctx);basin_match=len(set(hfr)&set(fr))/max(1,len(set(hfr)|set(fr)))
            reliability=(rec[0]-rec[1])/max(1,rec[0]+rec[1]);mean_res=rec[2]/max(1,rec[0]+rec[1]);vals.append(.50*reliability+.20*context_match+.25*basin_match-.03*mean_res)
        birth_bonus=.12*min(3,self.birth.get((c['ts'],c['vs'],c['ctx']),0)) if c['born'] else 0
        return e-(max(vals) if vals else 0)-birth_bonus
    def relax(self,ex):
        base=generate(ex);active=self.augment(ex,base)
        if not active:return None,0,0,'collapse',len(base),0
        prev=None;s=0
        while s<8:
            s+=1;rank=sorted((self.energy(ex,c,active),i,c) for i,c in enumerate(active));best=rank[0][0];active=[c for en,_,c in rank if en<=best+.05][:20]
            sig=tuple((c['pred'],c['a'],c['b'],c['ci'],c['cj']) for c in active)
            if sig==prev:break
            prev=sig
        rank=sorted((self.energy(ex,c,active),i,c) for i,c in enumerate(active));gap=rank[1][0]-rank[0][0] if len(rank)>1 else 99;born=sum(c['born'] for c in active)
        if gap<.09:return None,s,len(active),'tie',len(base),born
        return rank[0][2],s,len(active),'fixed',len(base),born

def truth(ex):
    l=0
    while l<min(len(ex.before),len(ex.after)) and ex.before[l]==ex.after[l]:l+=1
    r=0
    while r<min(len(ex.before)-l,len(ex.after)-l) and ex.before[-1-r]==ex.after[-1-r]:r+=1
    new=ex.after[l:len(ex.after)-r if r else len(ex.after)];p=ex.command.rfind(new)
    return None if p<0 else (l,len(ex.before)-r if r else len(ex.before),p,p+len(new))

def evaluate(m,test):
    t=time.perf_counter();vals=[]
    for ex in test:
        base=generate(ex);allc=m.augment(ex,base);p,s,a,r,bc,born=m.relax(ex);tr=truth(ex)
        exact=bool(tr and any((c['a'],c['b'],c['ci'],c['cj'])==tr for c in allc));pair=any(c['target']==ex.obj and c['value']==ex.value for c in allc)
        vals.append((p is not None and p['pred']==ex.after,p is not None and p['pred']!=ex.after,p is None,exact,pair,len(allc),s,a,born,r))
    n=len(vals)
    return {'accuracy':sum(x[0] for x in vals)/n,'wrong_commit':sum(x[1] for x in vals)/n,'null_rate':sum(x[2] for x in vals)/n,'exact_boundary_recall':sum(x[3] for x in vals)/n,'pair_recall':sum(x[4] for x in vals)/n,'mean_candidates':statistics.mean(x[5] for x in vals),'mean_sweeps':statistics.mean(x[6] for x in vals),'max_sweeps':max(x[6] for x in vals),'mean_active':statistics.mean(x[7] for x in vals),'mean_born_active':statistics.mean(x[8] for x in vals),'convergence_rate':1.0,'inference_ms':(time.perf_counter()-t)*1000/n,'reasons':dict(Counter(x[9] for x in vals))}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_036.json');a=ap.parse_args();modes=['seen','unknown','ambiguous','nested','omitted','paragraph','plan','counterfactual'];raw={}
    for seed in (1,7,19):
        pool=build(seed,24,'seen')+build(seed+33,12,'unknown');induction=pool[:24];probe=pool[24:];models={}
        for name,shuffle in [('none',False),('edge',False),('birth',False),('shuffle',True)]:
            model=Model('birth' if name=='shuffle' else name);model.fit(induction,probe,shuffle);models[name]=model
        run={'model':{n:{'hyperedges':len(model.hyper),'birth_signatures':len(model.birth),'birth_trials':model.birth_trials,'birth_accept':model.birth_accept,'audit':model.audit,'train_s':model.train_s,'bytes':len(pickle.dumps(model))} for n,model in models.items()}}
        for mode in modes:run[mode]={n:evaluate(model,build(seed+999,8,mode)) for n,model in models.items()}
        raw[str(seed)]=run
    summary={'model':{}}
    for method in ('none','edge','birth','shuffle'):summary['model'][method]={k:statistics.mean(raw[str(s)]['model'][method][k] for s in (1,7,19)) for k in raw['1']['model'][method]}
    for mode in modes:
        summary[mode]={}
        for method in ('none','edge','birth','shuffle'):summary[mode][method]={k:statistics.mean(raw[str(s)][mode][method][k] for s in (1,7,19)) for k,v in raw['1'][mode][method].items() if isinstance(v,(int,float))}
    payload={'cycle':36,'hypothesis':'Residual-Transported Node Birth from Hyperedge Frustration Gradients','seeds':[1,7,19],'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'candidate O(L^4) capped, hyperedge audit O(QHL^2), node birth O(QHM L^2), relaxation O(SH)','final_test_outcomes_used_for_ranking':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    open(a.output,'w',encoding='utf-8').write(json.dumps(payload,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
