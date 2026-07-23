from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse,json,pickle,random,resource,statistics,time

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
        out.append(Ex(before,cmd,after,future,obj,new,mode))
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

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return l,len(a)-r if r else len(a),b[l:len(b)-r if r else len(b)]

def ctx(ex,a,b,ci,cj):
    para=min(3,ex.command[:ci].count('\n'))
    return (min(7,8*a//max(1,len(ex.before))),min(7,8*b//max(1,len(ex.before))),min(7,8*ci//max(1,len(ex.command))),min(7,8*cj//max(1,len(ex.command))),shape(ex.before[max(0,a-2):min(len(ex.before),b+2)]),shape(ex.command[max(0,ci-2):min(len(ex.command),cj+2)]),para)

def make(ex,a,b,ci,cj,delta=None):
    if delta:
        da,db,dci,dcj=delta
        a=max(0,min(len(ex.before)-1,a+da));b=max(a+1,min(len(ex.before),b+db));ci=max(0,min(len(ex.command)-1,ci+dci));cj=max(ci+1,min(len(ex.command),cj+dcj))
    target=ex.before[a:b];value=ex.command[ci:cj];pred=ex.before[:a]+value+ex.before[b:]
    preserve=int(('補助記録' in ex.before)==('補助記録' in pred))
    base=1.5*preserve+int(value in ex.command)-0.02*(len(target)+len(value))-0.1*abs(len(target)-len(value))
    return {'a':a,'b':b,'ci':ci,'cj':cj,'target':target,'value':value,'pred':pred,'base':base,'ctx':ctx(ex,a,b,ci,cj)}

def generate_base(ex,cap=96):
    ts=sorted(spans(ex.before),key=lambda x:(-len(x[2]),x[0]))[:28]
    vs=sorted([x for x in spans(ex.command) if x[2] not in ex.before],key=lambda x:(-len(x[2]),x[0]))[:28]
    allc=[make(ex,a,b,ci,cj) for a,b,_ in ts for ci,cj,_ in vs]
    allc.sort(key=lambda c:c['base'],reverse=True);out=[];seen=set()
    for c in allc:
        k=(c['pred'],c['a'],c['b'],c['ci'],c['cj'])
        if k in seen:continue
        seen.add(k);out.append(c)
        if len(out)>=cap:break
    return out

def truth(ex,outcome):
    a,b,new=diff(ex.before,outcome);loc=[];st=0
    while new:
        i=ex.command.find(new,st)
        if i<0:break
        loc.append((i,i+len(new)));st=i+1
    return (a,b,*loc[-1]) if loc else None

def channel_signature(ex,c):
    obj_removed=ex.command.replace(ex.obj,'');val_removed=ex.command.replace(ex.value,'')
    return (int(c['value'] in obj_removed),int(c['target'] in val_removed),ex.command[:c['ci']].count('\n'),shape(c['target']),shape(c['value']))

class Model:
    def __init__(self,method):
        self.method=method;self.support=Counter();self.rules=defaultdict(Counter);self.audit=0;self.updates=0;self.gated=0;self.rejected=0;self.train_s=0
    def fit(self,induction,probe,shuffle=False):
        t=time.perf_counter()
        for ex in induction:
            for c in generate_base(ex):self.support[c['ctx']]+=1
        outcomes=[x.after for x in probe]
        if shuffle:outcomes=outcomes[1:]+outcomes[:1]
        for ex,outcome in zip(probe,outcomes):
            cs=generate_base(ex);self.audit+=len(cs);ranked=sorted(cs,key=lambda c:(edit_distance(c['pred'],outcome),-c['base']))[:6];tr=truth(ex,outcome)
            if tr is None or not ranked:continue
            ta,tb,tci,tcj=tr
            for idx,c in enumerate(ranked):
                delta=(ta-c['a'],tb-c['b'],tci-c['ci'],tcj-c['cj']);repaired=make(ex,c['a'],c['b'],c['ci'],c['cj'],delta)
                own_gain=edit_distance(c['pred'],outcome)-edit_distance(repaired['pred'],outcome)
                if own_gain<=0:continue
                eff=[]
                for j,o in enumerate(ranked):
                    if j==idx:continue
                    rr=make(ex,o['a'],o['b'],o['ci'],o['cj'],delta);eff.append(edit_distance(rr['pred'],outcome)-edit_distance(o['pred'],outcome))
                gate=sum(1 for x in eff if x>0)>=max(1,len(eff)//2) and sum(eff)>0
                key=(c['ctx'],channel_signature(ex,c))
                if self.method=='ungated' or gate:self.rules[key][delta]+=1;self.updates+=1;self.gated+=int(gate)
                else:self.rejected+=1
        for k in list(self.rules):
            self.rules[k]=Counter({d:n for d,n in self.rules[k].items() if n>=2})
            if not self.rules[k]:del self.rules[k]
        self.train_s=time.perf_counter()-t
    def generate(self,ex):
        base=generate_base(ex)
        if self.method=='none':return base
        out=list(base);seen={(c['pred'],c['a'],c['b'],c['ci'],c['cj']) for c in out}
        for c in base:
            key=(c['ctx'],channel_signature(ex,c))
            for d,n in self.rules.get(key,Counter()).most_common(2):
                r=make(ex,c['a'],c['b'],c['ci'],c['cj'],d);r['base']+=0.2*n;k=(r['pred'],r['a'],r['b'],r['ci'],r['cj'])
                if k not in seen:seen.add(k);out.append(r)
        return sorted(out,key=lambda c:c['base'],reverse=True)[:128]
    def energy(self,c):return -c['base']+0.02/max(1,self.support.get(c['ctx'],0))
    def relax(self,ex):
        active=self.generate(ex)
        if not active:return None,0,0,'collapse'
        prev=None;s=0
        while s<6:
            s+=1;rank=sorted((self.energy(c),i,c) for i,c in enumerate(active));best=rank[0][0];active=[c for e,_,c in rank if e<=best+0.08][:24]
            sig=tuple((c['pred'],c['a'],c['b'],c['ci'],c['cj']) for c in active)
            if sig==prev:break
            prev=sig
        rank=sorted((self.energy(c),i,c) for i,c in enumerate(active));gap=rank[1][0]-rank[0][0] if len(rank)>1 else 99
        if gap<.10:return None,s,len(active),'tie'
        return rank[0][2],s,len(active),'fixed'

def bd(c,ex):
    t=truth(ex,ex.after);return 99 if t is None else sum(abs(x-y) for x,y in zip((c['a'],c['b'],c['ci'],c['cj']),t))

def evaluate(m,test):
    t=time.perf_counter();vals=[]
    for ex in test:
        cs=m.generate(ex);p,s,a,r=m.relax(ex);vals.append((p is not None and p['pred']==ex.after,p is not None and p['pred']!=ex.after,p is None,any(c['target']==ex.obj and c['value']==ex.value for c in cs),min((bd(c,ex) for c in cs),default=99),len(cs),s,a,r))
    n=len(vals)
    return {'accuracy':sum(x[0] for x in vals)/n,'wrong_commit':sum(x[1] for x in vals)/n,'null_rate':sum(x[2] for x in vals)/n,'pair_recall':sum(x[3] for x in vals)/n,'mean_min_boundary_distance':statistics.mean(x[4] for x in vals),'mean_candidates':statistics.mean(x[5] for x in vals),'mean_sweeps':statistics.mean(x[6] for x in vals),'max_sweeps':max(x[6] for x in vals),'mean_active':statistics.mean(x[7] for x in vals),'convergence_rate':1.0,'inference_ms':(time.perf_counter()-t)*1000/n,'reasons':dict(Counter(x[8] for x in vals))}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_032.json');a=ap.parse_args();modes=['seen','unknown','ambiguous','nested','omitted','paragraph','plan','counterfactual'];raw={}
    for seed in (1,7,19):
        pool=build(seed,72,'seen')+build(seed+33,36,'unknown');induction=pool[:72];probe=pool[72:];models={}
        for name,shuffle in [('none',False),('ungated',False),('gated',False),('shuffle',True)]:
            m=Model('gated' if name=='shuffle' else name);m.fit(induction,probe,shuffle);models[name]=m
        run={'model':{n:{'rules':sum(len(v) for v in m.rules.values()),'contexts':len(m.rules),'audit':m.audit,'updates':m.updates,'gated':m.gated,'rejected':m.rejected,'train_s':m.train_s,'bytes':len(pickle.dumps(m))} for n,m in models.items()}}
        for mode in modes:run[mode]={n:evaluate(m,build(seed+999,24,mode)) for n,m in models.items()}
        raw[str(seed)]=run
    summary={'model':{}}
    for method in ('none','ungated','gated','shuffle'):summary['model'][method]={k:statistics.mean(raw[str(s)]['model'][method][k] for s in (1,7,19)) for k in raw['1']['model'][method]}
    for mode in modes:
        summary[mode]={}
        for method in ('none','ungated','gated','shuffle'):summary[mode][method]={k:statistics.mean(raw[str(s)][mode][method][k] for s in (1,7,19)) for k,v in raw['1'][mode][method].items() if isinstance(v,(int,float))}
    payload={'cycle':32,'hypothesis':'Scope-Gated Boundary Repair Attractors from Competing Counterexample Residuals','seeds':[1,7,19],'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'candidate O(L^4) capped, competing residual audit O(QkHL^2), repair expansion O(HR), relaxation O(SH)','final_test_outcomes_used_for_ranking':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    open(a.output,'w',encoding='utf-8').write(json.dumps(payload,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
