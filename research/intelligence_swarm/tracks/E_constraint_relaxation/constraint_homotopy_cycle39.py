from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','試料甲':'サンプル甲','試料乙':'サンプル乙'}
VALUES=['棚A','棚B','棚C','棚D','待機','処理中','完了','保留','担当一','担当二','担当三']
FILL=['補助記録は維持します。','別件は変更しません。','前段の設定はそのままです。']

@dataclass
class Ex:
    before:str; command:str; after:str; future:str; mode:str

def shape(s):
    return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、：／=\n 「」' else c for c in s)

def build(seed,n,mode):
    rng=random.Random(seed); out=[]
    for _ in range(n):
        canon=rng.choice(OBJECTS); obj=ALIASES[canon] if mode=='unknown' else canon
        old,new=rng.sample(VALUES,2); fill=rng.choice(FILL)
        before=f'{obj}の現在値は{old}です。{fill}'; cmd=f'{obj}の値を{new}へ変更してください。'
        if mode=='ambiguous':
            other=rng.choice([x for x in OBJECTS if x!=canon]); cmd=f'{obj}か{other}の値を{new}へ変更してください。'
        elif mode=='nested': cmd=f'依頼内容は「{cmd}」です。'
        elif mode=='omitted': cmd=f'それを{new}へ変更してください。'
        elif mode=='paragraph': cmd=f'{rng.choice(FILL)}\n{cmd}\n{rng.choice(FILL)}'
        elif mode=='plan':
            alt=rng.choice([v for v in VALUES if v not in (old,new)]); cmd=f'{obj}を{alt}にする案は撤回し、最終的には{new}へ変更してください。'
        elif mode=='counterfactual': cmd=f'もし変更しなければ{obj}は{old}のままです。実際には{cmd}'
        after=f'{obj}の現在値は{new}です。{fill}'; future=f'次の観測でも{obj}は{new}のままです。{fill}'
        out.append(Ex(before,cmd,after,future,mode))
    return out

def spans(text,lo=1,hi=10):
    return [(i,j,text[i:j]) for i in range(len(text)) for j in range(i+lo,min(len(text),i+hi)+1)
            if not any(c in text[i:j] for c in '\n「」')]

def candidate(ex,a,b,ci,cj):
    if not (0<=a<b<=len(ex.before) and 0<=ci<cj<=len(ex.command)): return None
    target=ex.before[a:b]; value=ex.command[ci:cj]; pred=ex.before[:a]+value+ex.before[b:]
    ts=(min(7,8*a//max(1,len(ex.before))),min(7,8*b//max(1,len(ex.before))),shape(target),min(7,len(target)))
    vs=(min(7,8*ci//max(1,len(ex.command))),min(7,8*cj//max(1,len(ex.command))),shape(value),min(7,len(value)))
    ctx=(min(7,len(ex.before)//8),min(7,len(ex.command)//8),min(7,ex.command.count('。')),min(7,ex.command.count('\n')))
    base=2.0-.025*(len(target)+len(value))-.08*abs(len(target)-len(value))
    return {'a':a,'b':b,'ci':ci,'cj':cj,'target':target,'value':value,'pred':pred,'ts':ts,'vs':vs,'ctx':ctx,'base':base}

def generate(ex,cap=16):
    ts=sorted(spans(ex.before),key=lambda x:(-len(x[2]),x[0]))[:6]
    vs=sorted([x for x in spans(ex.command) if x[2] not in ex.before],key=lambda x:(-len(x[2]),x[0]))[:6]
    out=[]; seen=set()
    for a,b,_ in ts:
        for ci,cj,_ in vs:
            c=candidate(ex,a,b,ci,cj)
            if c and (c['pred'],a,b,ci,cj) not in seen:
                seen.add((c['pred'],a,b,ci,cj)); out.append(c)
    out.sort(key=lambda c:c['base'],reverse=True)
    return out[:cap]

def edit_distance(a,b):
    prev=list(range(len(b)+1))
    for i,ca in enumerate(a,1):
        cur=[i]
        for j,cb in enumerate(b,1): cur.append(min(cur[-1]+1,prev[j]+1,prev[j-1]+(ca!=cb)))
        prev=cur
    return prev[-1]

def features(ex,c):
    a,b=c['a'],c['b']
    inv=c['pred'][:a]+c['target']+c['pred'][a+len(c['value']):]
    outside_ok=(ex.before[:a]==c['pred'][:a] and ex.before[b:]==c['pred'][a+len(c['value']):])
    return {'support':1.0,'command_value':float(c['value'] in ex.command),'inverse':float(inv==ex.before),'non_target':float(outside_ok),'future':float(c['value'] in ex.future),'anchor':float(any(s in ex.command and s in ex.before for _,_,s in spans(ex.command,2,8))),'residual':edit_distance(c['pred'],ex.after)/max(1,len(ex.after))}

class Model:
    def __init__(self,method):
        self.method=method; self.support=Counter(); self.weights={}; self.train_s=0; self.stage_accept=Counter()
    def fit(self,induction,probe,shuffle=False):
        t=time.perf_counter()
        for ex in induction:
            for c in generate(ex): self.support[(c['ts'],c['vs'],c['ctx'])]+=1
        names=['command_value','inverse','non_target','future','anchor']; score=Counter(); count=Counter()
        for i,ex in enumerate(probe):
            target=probe[(i+1)%len(probe)] if shuffle else ex
            for c in generate(ex):
                f=features(target,c); y=1.0 if c['pred']==target.after else -1.0
                for n in names: score[n]+=y*f[n]; count[n]+=f[n]
        self.weights={n:(score[n]/max(1,count[n])) for n in names}; self.train_s=time.perf_counter()-t
    def energy(self,ex,c,lambdas):
        f=features(ex,c); e=-c['base']+.04/max(1,self.support.get((c['ts'],c['vs'],c['ctx']),0))+.35*f['residual']
        for n,lam in lambdas.items(): e-=lam*self.weights.get(n,0)*f[n]
        return e
    def schedule(self):
        if self.method=='none': return [dict()]
        if self.method=='joint': return [{n:1.0 for n in self.weights}]
        order=['anchor','future','non_target','inverse','command_value'] if self.method=='reverse' else ['command_value','inverse','non_target','future','anchor']
        stages=[]; active={}
        for n in order: active=dict(active); active[n]=1.0; stages.append(active)
        return stages
    def relax(self,ex):
        active=generate(ex)
        if not active:return None,0,0,'collapse'
        total=0; prev=None
        for stage,lams in enumerate(self.schedule()):
            for _ in range(3):
                total+=1; rank=sorted((self.energy(ex,c,lams),i,c) for i,c in enumerate(active)); best=rank[0][0]
                active=[c for en,_,c in rank if en<=best+.045][:12]
                sig=tuple((c['pred'],c['a'],c['b'],c['ci'],c['cj']) for c in active)
                if sig==prev: break
                prev=sig
            self.stage_accept[stage]+=len(active)
        rank=sorted((self.energy(ex,c,self.schedule()[-1]),i,c) for i,c in enumerate(active)); gap=rank[1][0]-rank[0][0] if len(rank)>1 else 99
        if gap<.08:return None,total,len(active),'tie'
        return rank[0][2],total,len(active),'fixed'

def truth(ex):
    l=0
    while l<min(len(ex.before),len(ex.after)) and ex.before[l]==ex.after[l]:l+=1
    r=0
    while r<min(len(ex.before)-l,len(ex.after)-l) and ex.before[-1-r]==ex.after[-1-r]:r+=1
    new=ex.after[l:len(ex.after)-r if r else len(ex.after)]; p=ex.command.rfind(new)
    return None if p<0 else (l,len(ex.before)-r if r else len(ex.before),p,p+len(new))

def evaluate(m,test):
    t=time.perf_counter(); vals=[]
    for ex in test:
        cs=generate(ex); p,s,a,r=m.relax(ex); tr=truth(ex)
        exact=bool(tr and any((c['a'],c['b'],c['ci'],c['cj'])==tr for c in cs)); pair=any(c['pred']==ex.after for c in cs)
        vals.append((p is not None and p['pred']==ex.after,p is not None and p['pred']!=ex.after,p is None,exact,pair,len(cs),s,a,r))
    ms=(time.perf_counter()-t)*1000/len(test); n=len(vals)
    return {'accuracy':sum(x[0] for x in vals)/n,'wrong_commit':sum(x[1] for x in vals)/n,'null_rate':sum(x[2] for x in vals)/n,'exact_boundary_recall':sum(x[3] for x in vals)/n,'pair_recall':sum(x[4] for x in vals)/n,'mean_candidates':statistics.mean(x[5] for x in vals),'mean_sweeps':statistics.mean(x[6] for x in vals),'max_sweeps':max(x[6] for x in vals),'mean_active':statistics.mean(x[7] for x in vals),'inference_ms':ms}

def run(seed):
    induction=build(seed,48,'seen'); probe=build(seed+101,24,'seen'); modes=['seen','unknown','ambiguous','nested','omitted','paragraph','plan','counterfactual']; methods=['none','joint','homotopy','reverse','shuffle_homotopy']; out={}
    for method in methods:
        m=Model('homotopy' if method=='shuffle_homotopy' else method); m.fit(induction,probe,shuffle=method=='shuffle_homotopy')
        out[method]={'model_bytes':len(pickle.dumps(m)),'training_seconds':m.train_s,'weights':m.weights,'tests':{},'stage_accept':dict(m.stage_accept)}
        for mode in modes: out[method]['tests'][mode]=evaluate(m,build(seed+1000,24,mode))
        out[method]['stage_accept']=dict(m.stage_accept)
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); args=ap.parse_args(); seeds=[1,7,19]
    raw={str(s):run(s) for s in seeds}; modes=['seen','unknown','ambiguous','nested','omitted','paragraph','plan','counterfactual']; methods=['none','joint','homotopy','reverse','shuffle_homotopy']; summary={}
    for method in methods:
        summary[method]={'model_bytes':statistics.mean(raw[str(s)][method]['model_bytes'] for s in seeds),'training_seconds':statistics.mean(raw[str(s)][method]['training_seconds'] for s in seeds),'tests':{}}
        for mode in modes:
            ks=raw[str(seeds[0])][method]['tests'][mode].keys(); summary[method]['tests'][mode]={k:statistics.mean(raw[str(s)][method]['tests'][mode][k] for s in seeds) for k in ks}
    payload={'cycle':39,'hypothesis':'Constraint-Homotopy Attractor Tracking from Staged Local Consistency Fields','seeds':seeds,'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'candidate O(L^4) capped 16; staged relaxation O(KSH), K<=5,S<=3,H<=16','highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(args.output,'w',encoding='utf-8') as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
