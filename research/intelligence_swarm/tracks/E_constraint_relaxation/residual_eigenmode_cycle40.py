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

def edit_distance(a,b):
    prev=list(range(len(b)+1))
    for i,ca in enumerate(a,1):
        cur=[i]
        for j,cb in enumerate(b,1): cur.append(min(cur[-1]+1,prev[j]+1,prev[j-1]+(ca!=cb)))
        prev=cur
    return prev[-1]

def candidate(ex,a,b,ci,cj):
    if not (0<=a<b<=len(ex.before) and 0<=ci<cj<=len(ex.command)): return None
    target=ex.before[a:b]; value=ex.command[ci:cj]; pred=ex.before[:a]+value+ex.before[b:]
    ts=(min(7,8*a//max(1,len(ex.before))),min(7,8*b//max(1,len(ex.before))),shape(target),min(7,len(target)))
    vs=(min(7,8*ci//max(1,len(ex.command))),min(7,8*cj//max(1,len(ex.command))),shape(value),min(7,len(value)))
    ctx=(min(7,len(ex.before)//8),min(7,len(ex.command)//8),min(7,ex.command.count('。')),min(7,ex.command.count('\n')))
    base=2.0-.025*(len(target)+len(value))-.08*abs(len(target)-len(value))
    return {'a':a,'b':b,'ci':ci,'cj':cj,'target':target,'value':value,'pred':pred,'ts':ts,'vs':vs,'ctx':ctx,'sig':(ts,vs,ctx),'base':base}

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

def residual_components(ex,c):
    a,b=c['a'],c['b']; val=c['value']
    inv=c['pred'][:a]+c['target']+c['pred'][a+len(val):]
    return [
        edit_distance(c['pred'],ex.after)/max(1,len(ex.after)),
        float(inv!=ex.before),
        float(val not in ex.command),
        float(val not in ex.future),
        abs(len(c['target'])-len(val))/10.0,
        abs(a/max(1,len(ex.before))-c['ci']/max(1,len(ex.command))),
    ]

def surface_features(c):
    return [1.0,c['a']/20.0,c['b']/20.0,c['ci']/20.0,c['cj']/20.0,len(c['target'])/10.0,len(c['value'])/10.0]

def dot(a,b): return sum(x*y for x,y in zip(a,b))
def norm(a): return math.sqrt(max(1e-12,dot(a,a)))
def normalize(a):
    n=norm(a); return [x/n for x in a]

def gram_schmidt(v,basis):
    out=v[:]
    for b in basis:
        k=dot(out,b); out=[x-k*y for x,y in zip(out,b)]
    return normalize(out)

def matvec(m,v): return [dot(row,v) for row in m]

def power_modes(cov,k=3,iters=40):
    n=len(cov); modes=[]
    for z in range(min(k,n)):
        v=[math.sin((i+1)*(z+1)*1.37)+.1 for i in range(n)]; v=gram_schmidt(v,modes)
        for _ in range(iters):
            nv=gram_schmidt(matvec(cov,v),modes)
            if norm([a-b for a,b in zip(nv,v)])<1e-8: break
            v=nv
        eig=dot(v,matvec(cov,v))
        if eig<1e-8: break
        modes.append(v)
    return modes

class Model:
    def __init__(self,method):
        self.method=method; self.support=Counter(); self.mode_weight={}; self.modes=[]; self.train_s=0
        self.probe_candidates=0; self.surface_removed_energy=0.0
    def fit(self,induction,probe,shuffle=False):
        t=time.perf_counter()
        for ex in induction:
            for c in generate(ex): self.support[c['sig']]+=1
        rows=[]; sigs=[]; surf=[]; correct=[]
        for i,ex in enumerate(probe):
            target=probe[(i+1)%len(probe)] if shuffle else ex
            for c in generate(ex):
                rows.append(residual_components(target,c)); sigs.append(c['sig']); surf.append(surface_features(c)); correct.append(1.0 if c['pred']==target.after else 0.0)
        self.probe_candidates=len(rows)
        if not rows: self.train_s=time.perf_counter()-t; return
        agg=defaultdict(lambda:[[],[],[]])
        for r,sf,sg,y in zip(rows,surf,sigs,correct): agg[sg][0].append(r); agg[sg][1].append(sf); agg[sg][2].append(y)
        keys=list(agg)[:64]
        X=[]; S=[]; Y=[]
        for k in keys:
            X.append([statistics.mean(v[j] for v in agg[k][0]) for j in range(len(rows[0]))])
            S.append([statistics.mean(v[j] for v in agg[k][1]) for j in range(len(surf[0]))])
            Y.append(statistics.mean(agg[k][2]))
        for j in range(len(X[0])):
            mu=statistics.mean(r[j] for r in X)
            for r in X: r[j]-=mu
        if self.method!='no_surface':
            basis=[]
            for j in range(len(S[0])):
                v=[r[j] for r in S]; v=gram_schmidt(v,basis)
                if norm(v)>1e-6: basis.append(v)
            before=sum(dot([r[j] for r in X],[r[j] for r in X]) for j in range(len(X[0])))
            for j in range(len(X[0])):
                col=[r[j] for r in X]
                for b in basis:
                    q=dot(col,b); col=[x-q*y for x,y in zip(col,b)]
                for i,x in enumerate(col): X[i][j]=x
            after=sum(dot([r[j] for r in X],[r[j] for r in X]) for j in range(len(X[0])))
            self.surface_removed_energy=max(0.0,before-after)
        cov=[[dot(X[i],X[j]) for j in range(len(keys))] for i in range(len(keys))]
        modes=power_modes(cov,3)
        for mode in modes:
            sparse=[x if abs(x)>=0.20*max(abs(z) for z in mode) else 0.0 for x in mode]
            sparse=normalize(sparse)
            corr=dot(sparse,Y)
            if corr<0: sparse=[-x for x in sparse]
            self.modes.append(sparse)
        for idx,k in enumerate(keys):
            self.mode_weight[k]=sum(m[idx]*dot(m,Y) for m in self.modes)
        self.train_s=time.perf_counter()-t
    def energy(self,c):
        e=-c['base']+.05/max(1,self.support.get(c['sig'],0))
        if self.method in ('eigen','no_surface','shuffle'):
            e-=1.5*self.mode_weight.get(c['sig'],0.0)
        elif self.method=='fixed':
            e+=.2*abs(len(c['target'])-len(c['value']))+.1*(c['value'] not in c['pred'])
        return e
    def relax(self,ex):
        active=generate(ex)
        if not active:return None,0,0,'collapse'
        prev=None
        for sweep in range(1,9):
            rank=sorted((self.energy(c),i,c) for i,c in enumerate(active)); best=rank[0][0]
            active=[c for en,_,c in rank if en<=best+.045][:12]
            sig=tuple((c['pred'],c['a'],c['b'],c['ci'],c['cj']) for c in active)
            if sig==prev: break
            prev=sig
        rank=sorted((self.energy(c),i,c) for i,c in enumerate(active)); gap=rank[1][0]-rank[0][0] if len(rank)>1 else 99
        if gap<.08:return None,sweep,len(active),'tie'
        return rank[0][2],sweep,len(active),'fixed'

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
    induction=build(seed,48,'seen'); probe=build(seed+101,24,'seen')
    modes=['seen','unknown','ambiguous','nested','omitted','paragraph','plan','counterfactual']
    methods=['none','fixed','eigen','no_surface','shuffle']; out={}
    for method in methods:
        m=Model(method); m.fit(induction,probe,shuffle=method=='shuffle')
        out[method]={'model_bytes':len(pickle.dumps(m)),'training_seconds':m.train_s,'mode_count':len(m.modes),'field_count':len(m.mode_weight),'probe_candidates':m.probe_candidates,'surface_removed_energy':m.surface_removed_energy,'tests':{}}
        for mode in modes: out[method]['tests'][mode]=evaluate(m,build(seed+1000,24,mode))
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); args=ap.parse_args(); seeds=[1,7,19]
    raw={str(s):run(s) for s in seeds}; modes=['seen','unknown','ambiguous','nested','omitted','paragraph','plan','counterfactual']; methods=['none','fixed','eigen','no_surface','shuffle']; summary={}
    for method in methods:
        summary[method]={k:statistics.mean(raw[str(s)][method][k] for s in seeds) for k in ['model_bytes','training_seconds','mode_count','field_count','probe_candidates','surface_removed_energy']}; summary[method]['tests']={}
        for mode in modes:
            ks=raw[str(seeds[0])][method]['tests'][mode].keys(); summary[method]['tests'][mode]={k:statistics.mean(raw[str(s)][method]['tests'][mode][k] for s in seeds) for k in ks}
    payload={'cycle':40,'hypothesis':'Constraint-Field Birth from Counterexample-Separating Residual Eigenmodes','seeds':seeds,'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'candidate O(L^4) capped 16; residual matrix O(QH); surface projection O(PQH); covariance/power iteration O(H^2D + KH^2); relaxation O(SH), H<=16,K<=3,S<=8','highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(args.output,'w',encoding='utf-8') as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
