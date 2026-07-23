from __future__ import annotations
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import random,time,statistics,pickle,resource,json,argparse,math

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
VALUES=['棚A','棚B','棚C','棚D','待機','処理中','完了','保留','担当一','担当二','担当三','担当四']
FILL=['補助記録は維持します。','別件の設定は変えません。','前段の注意事項はそのままです。']
@dataclass
class Ex: before:str; command:str; after:str; future:str; obj:str; canon:str; old:str; new:str; mode:str
@dataclass
class Kernel:
    old_shape:str; new_shape:str; src_bucket:int; width:int; delta:int
    support:int=0; pos:int=0; neg:int=0; topology:int=1

def shape(s):
    return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、：／=\n 「」' else c for c in s)
def coarse(s):
    z=[]
    for c in shape(s):
        if not z or z[-1]!=c:z.append(c)
    return ''.join(z)
def build(seed,n,mode):
    rng=random.Random(seed); rows=[]; focus=None; world={}
    for t in range(n):
        cont=mode in ('omitted','switchmix') and t>0 and (mode=='omitted' or t%2==1)
        canon=focus if cont else rng.choice(OBJECTS); surf=ALIASES[canon] if mode=='rename' else canon
        old=world.get(canon,rng.choice(VALUES)); new=rng.choice([v for v in VALUES if v!=old]); filler=rng.choice(FILL)
        before=f'{surf}の現在値は{old}です。{filler}'
        if mode=='omitted' and t>0: cmd=f'それを{new}へ変更してください。'
        elif mode=='switchmix' and t>0 and t%2: cmd=f'その対象を{new}へ変更してください。'
        elif mode=='order': cmd=f'{new}へ変更してください、対象は{surf}です。'
        elif mode=='lexeme': cmd=f'対象{surf}は次から{new}扱いにします。'
        elif mode=='nested': cmd=f'依頼内容は「{surf}の値を{new}へ変更してください。」です。'
        elif mode=='paragraph': cmd=f'{rng.choice(FILL)}\n{surf}の値を{new}へ変更してください。\n{rng.choice(FILL)}'
        elif mode=='plan':
            alt=rng.choice([v for v in VALUES if v not in (old,new)]); cmd=f'{surf}を{alt}にする案は撤回し、最終的には{new}へ変更してください。'
        elif mode=='counterfactual': cmd=f'もし変更しなければ{surf}は{old}のままです。実際には{surf}を{new}へ変更してください。'
        else: cmd=f'{surf}の値を{new}へ変更してください。'
        after=f'{surf}の現在値は{new}です。{filler}'; future=f'次の観測でも{surf}は{new}のままです。'
        rows.append(Ex(before,cmd,after,future,surf,canon,old,new,mode)); world[canon]=new; focus=canon
    return rows

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def spans(text,lo=1,hi=10):
    return [(i,j,text[i:j]) for i in range(len(text)) for j in range(i+lo,min(len(text),i+hi)+1) if not any(c in text[i:j] for c in '。、\n「」')]
def vals(ex):
    xs=[s for _,_,s in spans(ex.command) if s not in ex.before]
    return sorted(set(xs),key=lambda x:(abs(len(x)-3),len(x),x))[:10]
def objs(ex,prev=None,carry=False):
    xs=[s for _,_,s in spans(ex.command,2,12) if s in ex.before]
    if carry and prev: xs += [s for _,_,s in spans(prev.after+' '+prev.future,2,12) if s in prev.after and s in prev.future]
    return sorted(set(xs),key=lambda x:(-len(x),x))[:10]
def apply(before,new,k):
    L=len(before); center=round(k.src_bucket*max(1,L-1)/7); hits=[]
    for a in range(max(0,center-3+k.delta),min(L,center+4+k.delta)):
        b=a+k.width
        if b<=L and coarse(before[a:b])==k.old_shape:hits.append((a,b))
    if len(hits)!=1:return None
    a,b=hits[0]; return before[:a]+new+before[b:]
def inverse(after,old,k,new):
    L=len(after); center=round(k.src_bucket*max(1,L-1)/7); hits=[]
    for a in range(max(0,center-3+k.delta),min(L,center+4+k.delta)):
        for w in range(1,11):
            b=a+w
            if b<=L and coarse(after[a:b])==coarse(new):hits.append((a,b))
    if len(hits)!=1:return None
    a,b=hits[0]; return after[:a]+old+after[b:]

class Model:
    def __init__(self,method,shuffle=False): self.method=method; self.shuffle=shuffle; self.kernels=[]; self.edges=set(); self.train_s=0; self.audit=0; self.rewire=0
    def fit(self,ind,probe):
        t=time.perf_counter(); stats=Counter()
        for e in ind:
            l,r,old,new=diff(e.before,e.after)
            if not old or not new:continue
            bucket=round(7*l/max(1,len(e.before)-1))
            for delta in (-2,-1,0,1,2):
                key=(coarse(old),coarse(new),bucket,len(old),delta); pred=apply(e.before,new,Kernel(*key))
                if pred==e.after: stats[key]+=1
        self.kernels=[Kernel(*k,support=n) for k,n in stats.most_common(64)]
        targets=[e.after for e in probe]
        if self.shuffle and targets: targets=targets[1:]+targets[:1]
        compat=defaultdict(list)
        for idx,k in enumerate(self.kernels):compat[(k.old_shape,k.new_shape)].append(idx)
        for e,target in zip(probe,targets):
            for i,k in enumerate(self.kernels):
                for v in vals(e):
                    if coarse(v)!=k.new_shape:continue
                    p=apply(e.before,v,k)
                    if p is None:continue
                    self.audit+=1
                    if p==target and inverse(p,e.old,k,v)==e.before:
                        k.pos+=1
                        for j in compat[(k.old_shape,k.new_shape)]:
                            if abs(self.kernels[j].src_bucket-k.src_bucket)<=1:
                                self.edges.add((i,j)); self.rewire+=1
                    else:
                        k.neg+=1
        if self.method=='plastic':
            self.kernels=[k for k in self.kernels if k.pos>k.neg]
            self.edges=set()
            for i,k in enumerate(self.kernels):
                for j,h in enumerate(self.kernels):
                    if i!=j and k.old_shape==h.old_shape and k.new_shape==h.new_shape and abs(k.src_bucket-h.src_bucket)<=1:self.edges.add((i,j))
        elif self.method=='shuffle':
            self.kernels=[k for k in self.kernels if k.pos>k.neg]
        self.train_s=time.perf_counter()-t
    def predict(self,e,prev=None):
        carry=self.method in ('carry','plastic','shuffle') and prev is not None
        ps=[]
        for i,k in enumerate(self.kernels):
            for v in vals(e):
                if coarse(v)!=k.new_shape:continue
                p=apply(e.before,v,k)
                if p is None:continue
                inv=int(inverse(p,e.old,k,v)!=e.before)
                degree=sum(1 for a,b in self.edges if a==i) if self.method=='plastic' else 0
                score=k.support+2*k.pos-1.5*k.neg-inv+0.25*degree
                for o in objs(e,prev,carry) or ['']:
                    ps.append((score,p,o,v,i))
        if not ps:return None,0,0,'collapse'
        active=ps; last=None
        for sweep in range(1,7):
            active=sorted(active,reverse=True); best=active[0][0]; active=[x for x in active if x[0]>=best-.25][:10]
            sig=tuple((x[1],x[2],x[3],x[4]) for x in active)
            if sig==last:break
            last=sig
        preds={x[1] for x in active}
        if len(preds)!=1:return None,sweep,len(active),'tie'
        return active[0],sweep,len(active),'fixed'

def eval_model(m,test):
    z=[]; t=time.perf_counter()
    for i,e in enumerate(test):z.append((m.predict(e,test[i-1] if i else None),e))
    n=len(z)
    return {'accuracy':sum(r[0] is not None and r[0][1]==e.after for r,e in z)/n,
      'wrong_commit':sum(r[0] is not None and r[0][1]!=e.after for r,e in z)/n,
      'null_rate':sum(r[0] is None for r,e in z)/n,
      'pair_recall':sum(r[0] is not None and r[0][2]==e.obj and r[0][3]==e.new for r,e in z)/n,
      'mean_sweeps':statistics.mean(r[1] for r,e in z),'mean_active':statistics.mean(r[2] for r,e in z),
      'kernels':len(m.kernels),'topology_edges':len(m.edges),'probe_audit':m.audit,'rewire_updates':m.rewire,
      'model_bytes':len(pickle.dumps(m)),'training_seconds':m.train_s,'inference_ms':(time.perf_counter()-t)*1000/n}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='MEASUREMENTS_CYCLE_032.json');a=ap.parse_args()
    modes=['seen','order','lexeme','rename','nested','omitted','switchmix','paragraph','plan','counterfactual']; raw={}
    for seed in (1,7,19):
        alltr=build(seed,32,'seen')+build(seed+20,16,'rename')+build(seed+40,16,'paragraph'); ind=alltr[:44];probe=alltr[44:]
        models={}
        for method,sh in [('family',False),('carry',False),('plastic',False),('shuffle',True)]:
            m=Model(method,sh);m.fit(ind,probe);models[method]=m
        raw[str(seed)]={mode:{k:eval_model(m,build(seed+999,12,mode)) for k,m in models.items()} for mode in modes}
    summary={}
    for mode in modes:
        summary[mode]={}
        for method in ('family','carry','plastic','shuffle'):
            keys=raw['1'][mode][method];summary[mode][method]={k:statistics.mean(raw[str(s)][mode][method][k] for s in (1,7,19)) for k in keys}
    payload={'cycle':32,'hypothesis':'Probe-Driven Transition-Kernel Plasticity for Operator-State Formation','seeds':[1,7,19],'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'induction O(NL), probe plasticity O(QKV), topology O(K^2), inference O(KOV+SH)','final_test_outcome_used_for_ranking':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    open(a.output,'w',encoding='utf-8').write(json.dumps(payload,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
