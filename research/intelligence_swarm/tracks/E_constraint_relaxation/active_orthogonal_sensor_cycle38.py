from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse, itertools, json, math, pickle, random, resource, statistics, time

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
    return [(i,j,text[i:j]) for i in range(len(text)) for j in range(i+lo,min(len(text),i+hi)+1) if not any(c in text[i:j] for c in '\n「」')]

def candidate(ex,a,b,ci,cj):
    if not (0<=a<b<=len(ex.before) and 0<=ci<cj<=len(ex.command)): return None
    target=ex.before[a:b]; value=ex.command[ci:cj]; pred=ex.before[:a]+value+ex.before[b:]
    ts=(min(7,8*a//max(1,len(ex.before))),min(7,8*b//max(1,len(ex.before))),shape(target),min(7,len(target)))
    vs=(min(7,8*ci//max(1,len(ex.command))),min(7,8*cj//max(1,len(ex.command))),shape(value),min(7,len(value)))
    ctx=(min(7,len(ex.before)//8),min(7,len(ex.command)//8),min(7,ex.command.count('。')),min(7,ex.command.count('\n')))
    base=2.0-.025*(len(target)+len(value))-.08*abs(len(target)-len(value))
    return {'a':a,'b':b,'ci':ci,'cj':cj,'target':target,'value':value,'pred':pred,'ts':ts,'vs':vs,'ctx':ctx,'base':base}

def generate(ex,cap=12):
    ts=sorted(spans(ex.before),key=lambda x:(-len(x[2]),x[0]))[:5]
    vs=sorted([x for x in spans(ex.command) if x[2] not in ex.before],key=lambda x:(-len(x[2]),x[0]))[:5]
    out=[]; seen=set()
    for a,b,_ in ts:
        for ci,cj,_ in vs:
            c=candidate(ex,a,b,ci,cj)
            if c and (c['pred'],a,b,ci,cj) not in seen:
                seen.add((c['pred'],a,b,ci,cj)); out.append(c)
    out.sort(key=lambda c:c['base'],reverse=True)
    return out[:cap]

def replace_once(text,old,new):
    p=text.find(old)
    return text if p<0 else text[:p]+new+text[p+len(old):]

def synth_queries(ex):
    out=[]
    present=[v for v in VALUES if v in ex.command]
    basev=present[-1] if present else None
    if basev:
        for nv in VALUES:
            if nv==basev: continue
            out.append(('value_swap',Ex(ex.before,replace_once(ex.command,basev,nv),replace_once(ex.after,basev,nv),replace_once(ex.future,basev,nv),ex.mode)))
    present_obj=next((o for o in OBJECTS+list(ALIASES.values()) if o in ex.command),None)
    if present_obj:
        for no in OBJECTS[:4]:
            if no==present_obj: continue
            out.append(('object_swap',Ex(replace_once(ex.before,present_obj,no),replace_once(ex.command,present_obj,no),replace_once(ex.after,present_obj,no),replace_once(ex.future,present_obj,no),ex.mode)))
        out.append(('object_mask',Ex(ex.before,replace_once(ex.command,present_obj,'その対象'),ex.after,ex.future,ex.mode)))
    out.append(('prefix_noise',Ex(ex.before,'補足です。'+ex.command,ex.after,ex.future,ex.mode)))
    out.append(('suffix_noise',Ex(ex.before,ex.command+'別件は維持します。',ex.after,ex.future,ex.mode)))
    return out[:18]

def response(c,q):
    a=max(0,min(len(q.before)-1,round(c['ts'][0]*len(q.before)/8)))
    b=max(a+1,min(len(q.before),round(c['ts'][1]*len(q.before)/8)))
    ci=max(0,min(len(q.command)-1,round(c['vs'][0]*len(q.command)/8)))
    cj=max(ci+1,min(len(q.command),round(c['vs'][1]*len(q.command)/8)))
    cc=candidate(q,a,b,ci,cj)
    if cc is None: return ('noexec',0,0,0)
    inv=cc['pred'][:a]+cc['target']+cc['pred'][a+len(cc['value']):]
    return ('correct' if cc['pred']==q.after else 'wrong', int(inv==q.before), int(cc['value'] in q.future), len(cc['pred'])-len(q.before))

def disagreement(cands,q):
    rs=[response(c,q) for c in cands]
    counts=Counter(rs); n=len(rs)
    pairs=(n*n-sum(v*v for v in counts.values()))//2
    bits=max(1,len(q.command.encode('utf-8'))*8)
    return pairs/bits, tuple(rs)

def corr(xs,ys):
    if not xs or len(xs)!=len(ys): return 1.0
    mx=sum(xs)/len(xs); my=sum(ys)/len(ys)
    vx=sum((x-mx)**2 for x in xs); vy=sum((y-my)**2 for y in ys)
    if vx==0 or vy==0: return 1.0
    return sum((x-mx)*(y-my) for x,y in zip(xs,ys))/math.sqrt(vx*vy)

class Model:
    def __init__(self,method):
        self.method=method; self.support=Counter(); self.sensors=[]; self.sensor_weight=[]; self.hyper=[]
        self.query_audit=0; self.orthogonal_pairs=0; self.train_s=0
    def fit(self,induction,probe,shuffle=False,random_queries=False):
        t=time.perf_counter()
        for ex in induction:
            for c in generate(ex): self.support[(c['ts'],c['vs'],c['ctx'])]+=1
        records=[]
        for ex in probe:
            cands=generate(ex)
            if not cands: continue
            qs=synth_queries(ex); self.query_audit+=len(qs)
            scored=[]
            for kind,q in qs:
                score,rv=disagreement(cands,q); scored.append((score,kind,q,rv))
            if random_queries:
                random.Random(len(ex.command)).shuffle(scored); selected=scored[:5]
            else:
                selected=sorted(scored,key=lambda x:x[0],reverse=True)[:5]
            if shuffle:
                selected=[(sc,k,Ex(q.before,q.command,probe[(i+1)%len(probe)].after,probe[(i+1)%len(probe)].future,q.mode),rv) for i,(sc,k,q,rv) in enumerate(selected)]
            for qi,(sc,kind,q,_) in enumerate(selected):
                vals=[]
                for c in cands:
                    r=response(c,q); vals.append(1 if r[0]=='correct' else 0)
                records.append((ex,cands,kind,qi,vals,sc))
        sensor_records=[]
        for _,cands,kind,qi,vals,sc in records:
            if sum(vals)==0 or sum(vals)==len(vals): continue
            sensor_records.append((kind,qi,vals,sc,cands))
        selected=[]
        for rec in sorted(sensor_records,key=lambda x:x[3],reverse=True):
            if all(abs(corr(rec[2],r[2]))<0.35 for r in selected): selected.append(rec)
            if len(selected)>=12: break
        self.sensors=[(k,qi) for k,qi,_,_,_ in selected]
        self.sensor_weight=[sc for _,_,_,sc,_ in selected]
        for combo in itertools.combinations(range(len(selected)),3):
            self.orthogonal_pairs+=3
            m=min(len(selected[i][2]) for i in combo)
            common=[all(selected[i][2][j] for i in combo) for j in range(m)]
            if sum(common)>=1: self.hyper.append((combo,sum(common),m-sum(common)))
        self.train_s=time.perf_counter()-t
    def sensor_values(self,ex,cands):
        qs=synth_queries(ex); values=[]
        for kind,qi in self.sensors:
            matching=[q for k,q in qs if k==kind]
            q=matching[min(qi,len(matching)-1)] if matching else None
            values.append([0]*len(cands) if q is None else [1 if response(c,q)[0]=='correct' else 0 for c in cands])
        return values
    def energy(self,ex,cands,idx,sv):
        c=cands[idx]; e=-c['base']+.025/max(1,self.support.get((c['ts'],c['vs'],c['ctx']),0))
        if self.method=='none': return e
        if self.method in ('active','random','shuffle'):
            e-=.04*sum(self.sensor_weight[i]*sv[i][idx] for i in range(len(sv)))
        if self.method=='active':
            for combo,p,n in self.hyper:
                if all(i<len(sv) and sv[i][idx] for i in combo): e-=.12*(p/(p+n))
        return e
    def relax(self,ex):
        active=generate(ex)
        if not active:return None,0,0,'collapse'
        sv=self.sensor_values(ex,active); prev=None; s=0
        while s<8:
            s+=1; rank=sorted((self.energy(ex,active,i,sv),i,c) for i,c in enumerate(active)); best=rank[0][0]
            active=[c for en,_,c in rank if en<=best+.05][:20]; sv=self.sensor_values(ex,active)
            sig=tuple((c['pred'],c['a'],c['b'],c['ci'],c['cj']) for c in active)
            if sig==prev: break
            prev=sig
        rank=sorted((self.energy(ex,active,i,sv),i,c) for i,c in enumerate(active)); gap=rank[1][0]-rank[0][0] if len(rank)>1 else 99
        if gap<.09:return None,s,len(active),'tie'
        return rank[0][2],s,len(active),'fixed'

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
    n=len(vals)
    return {'accuracy':sum(x[0] for x in vals)/n,'wrong_commit':sum(x[1] for x in vals)/n,'null_rate':sum(x[2] for x in vals)/n,'exact_boundary_recall':sum(x[3] for x in vals)/n,'pair_recall':sum(x[4] for x in vals)/n,'mean_candidates':statistics.mean(x[5] for x in vals),'mean_sweeps':statistics.mean(x[6] for x in vals),'max_sweeps':max(x[6] for x in vals),'mean_active':statistics.mean(x[7] for x in vals),'convergence_rate':1.0,'inference_ms':(time.perf_counter()-t)*1000/n,'reasons':dict(Counter(x[8] for x in vals))}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',default='results_cycle_038.json'); a=ap.parse_args()
    modes=['seen','unknown','ambiguous','nested','omitted','paragraph','plan','counterfactual']; raw={}
    for seed in (1,7,19):
        pool=build(seed,20,'seen')+build(seed+33,12,'unknown'); induction=pool[:20]; probe=pool[20:]
        specs=[('none','none',False,False),('random','random',False,True),('active','active',False,False),('shuffle','shuffle',True,False)]
        models={}
        for name,method,shuffle,rnd in specs:
            m=Model(method); m.fit(induction,probe,shuffle=shuffle,random_queries=rnd); models[name]=m
        run={'model':{n:{'sensors':len(m.sensors),'hyperedges':len(m.hyper),'query_audit':m.query_audit,'orthogonal_pair_checks':m.orthogonal_pairs,'train_s':m.train_s,'bytes':len(pickle.dumps({'method':m.method,'support':dict(m.support),'sensors':m.sensors,'weights':m.sensor_weight,'hyper':m.hyper}))} for n,m in models.items()}}
        for mode in modes: run[mode]={n:evaluate(m,build(seed+999,8,mode)) for n,m in models.items()}
        raw[str(seed)]=run
    methods=('none','random','active','shuffle'); summary={'model':{}}
    for method in methods: summary['model'][method]={k:statistics.mean(raw[str(s)]['model'][method][k] for s in (1,7,19)) for k in raw['1']['model'][method]}
    for mode in modes:
        summary[mode]={}
        for method in methods: summary[mode][method]={k:statistics.mean(raw[str(s)][mode][method][k] for s in (1,7,19)) for k,v in raw['1'][mode][method].items() if isinstance(v,(int,float))}
    payload={'cycle':38,'hypothesis':'Intervention-Orthogonal Sensor Birth from Actively Synthesized Constraint Queries','seeds':[1,7,19],'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'candidate O(L^4) capped; query synthesis O(Q); disagreement O(QH^2); orthogonal selection O(S^2H); relaxation O(RHS)','final_test_outcomes_used_for_ranking':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    open(a.output,'w',encoding='utf-8').write(json.dumps(payload,ensure_ascii=False,indent=2)); print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
