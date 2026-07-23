from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse, itertools, json, pickle, random, resource, statistics, time
OBJECTS=['青い箱','赤い箱','小型端末','大型端末','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','試料甲':'サンプル甲','試料乙':'サンプル乙'}
VALUES=['棚A','棚B','棚C','棚D','待機','処理中','完了','保留','担当一','担当二','担当三']
FILL=['補助記録は維持します。','別件は変更しません。','前段の設定はそのままです。']
SENSORS=('command_value','inverse','non_target','future_trace','shared_anchor')
@dataclass
class Ex:
    before:str; command:str; after:str; future:str; mode:str
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
        out.append(Ex(before,cmd,after,future,mode))
    return out
def spans(text,lo=1,hi=10):
    return [(i,j,text[i:j]) for i in range(len(text)) for j in range(i+lo,min(len(text),i+hi)+1) if not any(c in text[i:j] for c in '\n「」')]
def anchors(ex):
    common={s for _,_,s in spans(ex.before,2,10)} & {s for _,_,s in spans(ex.command,2,10)}
    return sorted(common,key=lambda x:(-len(x),x))[:6]
def candidate(ex,a,b,ci,cj):
    if not (0<=a<b<=len(ex.before) and 0<=ci<cj<=len(ex.command)):return None
    target=ex.before[a:b];value=ex.command[ci:cj];pred=ex.before[:a]+value+ex.before[b:];damage=0
    ts=(min(7,8*a//max(1,len(ex.before))),min(7,8*b//max(1,len(ex.before))),shape(target),min(7,len(target)))
    vs=(min(7,8*ci//max(1,len(ex.command))),min(7,8*cj//max(1,len(ex.command))),shape(value),min(7,len(value)))
    ctx=(min(7,len(ex.before)//8),min(7,len(ex.command)//8),min(7,ex.command.count('。')),min(7,ex.command.count('\n')))
    base=2.0-.025*(len(target)+len(value))-.08*abs(len(target)-len(value))-int(damage>0)
    return {'a':a,'b':b,'ci':ci,'cj':cj,'target':target,'value':value,'pred':pred,'ts':ts,'vs':vs,'ctx':ctx,'base':base,'damage':damage}
def generate(ex,cap=12):
    ts=sorted(spans(ex.before),key=lambda x:(-len(x[2]),x[0]))[:5]
    vs=sorted([x for x in spans(ex.command) if x[2] not in ex.before],key=lambda x:(-len(x[2]),x[0]))[:5]
    out=[];seen=set()
    for a,b,_ in ts:
        for ci,cj,_ in vs:
            c=candidate(ex,a,b,ci,cj)
            if c is None:continue
            key=(c['pred'],a,b,ci,cj)
            if key not in seen:seen.add(key);out.append(c)
    out.sort(key=lambda c:c['base'],reverse=True);return out[:cap]
def sensor_vector(ex,c,future=None):
    future=ex.future if future is None else future
    inv=c['pred'][:c['a']]+c['target']+c['pred'][c['a']+len(c['value']):];anc=anchors(ex)
    return {'command_value':int(c['value'] in ex.command and c['value'] not in ex.before),'inverse':int(inv==ex.before),'non_target':int(c['damage']==0),'future_trace':int(c['value'] in future),'shared_anchor':int(any(a in c['pred'] and a in future for a in anc))}
class Model:
    def __init__(self,method,lesion=None):
        self.method=method;self.lesion=lesion;self.support=Counter();self.single=defaultdict(lambda:[0,0]);self.synergy={};self.audit=0;self.train_s=0
    def fit(self,induction,probe,shuffle=False,channel_shuffle=False):
        t=time.perf_counter()
        for ex in induction:
            for c in generate(ex):self.support[(c['ts'],c['vs'],c['ctx'])]+=1
        outcomes=[e.after for e in probe];futures=[e.future for e in probe]
        if shuffle:outcomes=outcomes[1:]+outcomes[:1];futures=futures[1:]+futures[:1]
        records=[]
        for idx,(ex,outcome,future) in enumerate(zip(probe,outcomes,futures)):
            for c in generate(ex):
                self.audit+=1;correct=int(c['pred']==outcome);sv=sensor_vector(ex,c,future)
                if channel_shuffle:
                    rotated={}
                    for k_i,k in enumerate(SENSORS):
                        other=probe[(idx+k_i+1)%len(probe)];oc=generate(other)
                        rotated[k]=sensor_vector(other,oc[0],futures[(idx+k_i+1)%len(probe)])[k] if oc else 0
                    sv=rotated
                records.append((c,sv,correct))
                for s,v in sv.items():
                    if v:self.single[(c['ts'],c['vs'],s)][correct]+=1
        combos=list(itertools.combinations(SENSORS,3))+list(itertools.combinations(SENSORS,4));stats=defaultdict(lambda:[0,0])
        for c,sv,correct in records:
            for combo in combos:
                if all(sv[s] for s in combo):stats[(c['ts'],c['vs'],combo)][correct]+=1
        for key,(pos,neg) in stats.items():
            if pos+neg<2:continue
            ts,vs,combo=key;joint=pos/(pos+neg);singles=[]
            for s in combo:
                p,n=self.single.get((ts,vs,s),(0,0));singles.append(p/(p+n) if p+n else 0)
            synergy=joint-max(singles)
            if pos>neg and synergy>0.02:self.synergy[key]=(pos,neg,synergy)
        self.train_s=time.perf_counter()-t
    def energy(self,ex,c):
        e=-c['base']+.025/max(1,self.support.get((c['ts'],c['vs'],c['ctx']),0))
        if self.method=='none':return e
        sv=sensor_vector(ex,c)
        if self.method=='additive':
            for s,v in sv.items():
                if self.lesion==s or not v:continue
                p,n=self.single.get((c['ts'],c['vs'],s),(0,0));e-=.08*(p-n)/max(1,p+n)
            return e
        vals=[]
        for (ts,vs,combo),(p,n,sy) in self.synergy.items():
            if ts!=c['ts'] or vs!=c['vs'] or (self.lesion and self.lesion in combo):continue
            if all(sv[s] for s in combo):vals.append(.35*sy+.08*(p-n)/max(1,p+n))
        return e-(max(vals) if vals else 0)
    def relax(self,ex):
        active=generate(ex)
        if not active:return None,0,0,'collapse'
        prev=None;s=0
        while s<8:
            s+=1;rank=sorted((self.energy(ex,c),i,c) for i,c in enumerate(active));best=rank[0][0]
            active=[c for en,_,c in rank if en<=best+.05][:20]
            sig=tuple((c['pred'],c['a'],c['b'],c['ci'],c['cj']) for c in active)
            if sig==prev:break
            prev=sig
        rank=sorted((self.energy(ex,c),i,c) for i,c in enumerate(active));gap=rank[1][0]-rank[0][0] if len(rank)>1 else 99
        if gap<.09:return None,s,len(active),'tie'
        return rank[0][2],s,len(active),'fixed'
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
        cs=generate(ex);p,s,a,r=m.relax(ex);tr=truth(ex)
        exact=bool(tr and any((c['a'],c['b'],c['ci'],c['cj'])==tr for c in cs));pair=any(c['target'] in ex.before and c['value'] in ex.after and c['pred']==ex.after for c in cs)
        vals.append((p is not None and p['pred']==ex.after,p is not None and p['pred']!=ex.after,p is None,exact,pair,len(cs),s,a,r))
    n=len(vals)
    return {'accuracy':sum(x[0] for x in vals)/n,'wrong_commit':sum(x[1] for x in vals)/n,'null_rate':sum(x[2] for x in vals)/n,'exact_boundary_recall':sum(x[3] for x in vals)/n,'pair_recall':sum(x[4] for x in vals)/n,'mean_candidates':statistics.mean(x[5] for x in vals),'mean_sweeps':statistics.mean(x[6] for x in vals),'max_sweeps':max(x[6] for x in vals),'mean_active':statistics.mean(x[7] for x in vals),'convergence_rate':1.0,'inference_ms':(time.perf_counter()-t)*1000/n,'reasons':dict(Counter(x[8] for x in vals))}
