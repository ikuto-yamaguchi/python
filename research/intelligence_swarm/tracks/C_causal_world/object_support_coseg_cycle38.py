from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
import argparse, json, pickle, random, resource, statistics, time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
VALUES=['棚A','棚B','棚C','棚D','待機','処理中','完了','保留','担当一','担当二','担当三','担当四']
FILL=['補助記録は維持します。','監査情報は変更しません。','別件の設定はそのままです。']

@dataclass
class Ex:
    before:str; command:str; after:str; future:str
    obj:str; other:str; old:str; new:str; mode:str

@dataclass
class Proposal:
    obj_shape:str; obj_bucket:int; state_bucket:int; width:int; value_shape:str
    support:int=0; wrong:int=0; noexec:int=0; paired_support:int=0


def shape(s):
    return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、：／=\n「」 ' else c for c in s)

def spans(text,lo=1,hi=12):
    return [(i,j,text[i:j]) for i in range(len(text)) for j in range(i+lo,min(len(text),i+hi)+1)
            if not any(c in text[i:j] for c in '。、\n「」')]

def make(seed,n,mode):
    rng=random.Random(seed); out=[]
    for _ in range(n):
        a,b=rng.sample(OBJECTS,2); target=rng.choice([a,b]); other=b if target==a else a
        sa=ALIASES[a] if mode=='rename' else a; sb=ALIASES[b] if mode=='rename' else b
        st={a:rng.choice(VALUES),b:rng.choice(VALUES)}
        new=rng.choice([v for v in VALUES if v!=st[target]])
        before=f'{sa}の現在値は{st[a]}です。{sb}の現在値は{st[b]}です。{rng.choice(FILL)}'
        ts=ALIASES[target] if mode=='rename' else target
        if mode=='order': cmd=f'{new}へ変更してください、対象は{ts}です。'
        elif mode=='lexeme': cmd=f'対象{ts}は次から{new}扱いにします。'
        elif mode=='nested': cmd=f'依頼内容は「{ts}の値を{new}へ変更してください。」です。'
        elif mode=='omitted': cmd=f'その対象を{new}へ変更してください。'
        elif mode=='paragraph': cmd=f'{rng.choice(FILL)}\n{ts}の値を{new}へ変更してください。\n{rng.choice(FILL)}'
        elif mode=='plan':
            alt=rng.choice([v for v in VALUES if v not in (st[target],new)])
            cmd=f'{ts}を{alt}にする案は撤回し、最終的には{new}へ変更してください。'
        elif mode=='counterfactual': cmd=f'もし変更しなければ{ts}は{st[target]}のままです。実際には{ts}を{new}へ変更してください。'
        elif mode=='alternate':
            before=f'{sa}：値={st[a]}／{sb}：値={st[b]}／補助=維持。'; cmd=f'{ts}を{new}へ切り替えます。'
        else: cmd=f'{ts}の値を{new}へ変更してください。'
        old=st[target]; st[target]=new
        after=(f'{sa}の現在値は{st[a]}です。{sb}の現在値は{st[b]}です。{rng.choice(FILL)}'
               if mode!='alternate' else f'{sa}：値={st[a]}／{sb}：値={st[b]}／補助=維持。')
        future=f'次の観測でも{ts}は{new}で、もう一方の対象は変化しません。'
        out.append(Ex(before,cmd,after,future,ts,ALIASES[other] if mode=='rename' else other,old,new,mode))
    return out

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l, len(a)-r, a[l:len(a)-r if r else len(a)], b[l:len(b)-r if r else len(b)]

def bucket(i,n,k=16): return min(k-1,int(k*i/max(1,n)))

def value_candidates(e):
    xs=[s for _,_,s in spans(e.command,1,10) if s not in e.before]
    return sorted(set(xs),key=lambda x:(-len(x),x))[:12]

def object_candidates(e):
    xs=[s for _,_,s in spans(e.command,2,12) if s in e.before]
    return sorted(set(xs),key=lambda x:(-len(x),x))[:12]

def apply(e,p,obj,val):
    oi=e.before.find(obj)
    if oi<0: return None
    target_bucket=(bucket(oi,len(e.before))+p.state_bucket-p.obj_bucket)%16
    center=int((target_bucket+.5)*len(e.before)/16)
    candidates=[]
    for a in range(max(0,center-10),min(len(e.before),center+11)):
        b=a+p.width
        if b<=len(e.before): candidates.append((abs(bucket(a,len(e.before))-target_bucket),a,b))
    if not candidates:return None
    _,a,b=min(candidates)
    return e.before[:a]+val+e.before[b:],(a,b)

class Model:
    def __init__(self,method): self.method=method; self.props=[]; self.train_seconds=0
    def fit(self,train,pairs):
        t=time.perf_counter(); counts=defaultdict(lambda:[0,0,0,0])
        for e in train:
            l,r,old,new=diff(e.before,e.after)
            if not old or not new: continue
            for obj in object_candidates(e)[:6]:
                oi=e.before.find(obj)
                if oi<0: continue
                key=(shape(obj),bucket(oi,len(e.before)),bucket(l,len(e.before)),len(old),shape(new))
                counts[key][0]+=1
        for e1,e2 in pairs:
            l1,_,o1,n1=diff(e1.before,e1.after); l2,_,o2,n2=diff(e2.before,e2.after)
            if not o1 or not o2: continue
            for a in object_candidates(e1)[:6]:
                for b in object_candidates(e2)[:6]:
                    if shape(a)!=shape(b): continue
                    ai=e1.before.find(a); bi=e2.before.find(b)
                    if ai<0 or bi<0: continue
                    rel1=(bucket(l1,len(e1.before))-bucket(ai,len(e1.before)))%16
                    rel2=(bucket(l2,len(e2.before))-bucket(bi,len(e2.before)))%16
                    if rel1==rel2:
                        key=(shape(a),bucket(ai,len(e1.before)),bucket(l1,len(e1.before)),len(o1),shape(n1))
                        counts[key][3]+=1
        ps=[]
        for k,v in counts.items():
            if v[0]>=2:
                ps.append(Proposal(*k,support=v[0],paired_support=v[3]))
        if self.method=='coseg': ps=[p for p in ps if p.paired_support>=1]
        if self.method=='strict': ps=[p for p in ps if p.paired_support>=2]
        self.props=sorted(ps,key=lambda p:(p.paired_support,p.support),reverse=True)[:32]
        self.train_seconds=time.perf_counter()-t
    def predict(self,e):
        outs=[]
        for p in self.props:
            for obj in object_candidates(e)[:4]:
                if shape(obj)!=p.obj_shape: continue
                for val in value_candidates(e)[:4]:
                    if shape(val)!=p.value_shape: continue
                    z=apply(e,p,obj,val)
                    if z is None: continue
                    pred,span=z
                    score=p.support+2*p.paired_support
                    outs.append((score,pred,obj,val,span))
        uniq={}
        for x in outs:
            if x[1] not in uniq or x[0]>uniq[x[1]][0]: uniq[x[1]]=x
        ranked=sorted(uniq.values(),reverse=True)
        if not ranked:return None,len(uniq),False
        if len(ranked)>1 and ranked[0][0]==ranked[1][0]: return None,len(uniq),False
        return ranked[0],len(uniq),True

def paired(seed,n,shuffle=False):
    pairs=[]
    for i in range(n):
        e1=make(seed+i,2,'seen')[0]
        candidates=make(seed+10000+i,16,'seen')
        e2=next((x for x in candidates if x.obj!=e1.obj and shape(x.new)==shape(e1.new)),candidates[0])
        pairs.append((e1,e2))
    if shuffle:
        right=[b for _,b in pairs]; right=right[1:]+right[:1]
        pairs=[(a,b) for (a,_),b in zip(pairs,right)]
    return pairs

def evaluate(seed,mode):
    train=make(seed,72,'seen'); good=paired(seed+100,18,False); bad=paired(seed+100,18,True)
    test=make(seed+999,18,mode); out={}
    for method,pairs in [('factorized',[]),('coseg',good),('strict',good),('shuffle',bad)]:
        m=Model(method if method!='shuffle' else 'coseg'); m.fit(train,pairs)
        t=time.perf_counter(); vals=[]
        for e in test:
            pred,n,commit=m.predict(e)
            ok=bool(commit and pred and pred[1]==e.after)
            wrong=bool(commit and pred and pred[1]!=e.after)
            exact=bool(pred and pred[4]==(e.before.find(e.old),e.before.find(e.old)+len(e.old)))
            pair=bool(pred and pred[2]==e.obj and pred[3]==e.new)
            vals.append((ok,wrong,not commit,exact,pair,n))
        ms=(time.perf_counter()-t)*1000/len(test)
        out[method]={
          'accuracy':statistics.mean(x[0] for x in vals),'wrong_commit':statistics.mean(x[1] for x in vals),
          'null':statistics.mean(x[2] for x in vals),'exact_boundary':statistics.mean(x[3] for x in vals),
          'object_value_pair':statistics.mean(x[4] for x in vals),'mean_candidates':statistics.mean(x[5] for x in vals),
          'proposal_count':len(m.props),'paired_support_sum':sum(p.paired_support for p in m.props),
          'model_bytes':len(pickle.dumps(m)),'training_seconds':m.train_seconds,'inference_ms':ms}
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',default='MEASUREMENTS_CYCLE_038.json'); a=ap.parse_args()
    modes=['seen','order','lexeme','rename','alternate','nested','omitted','paragraph','plan','counterfactual']
    raw={str(seed):{mode:evaluate(seed,mode) for mode in modes} for seed in (1,7,19)}
    summary={}
    for mode in modes:
        summary[mode]={}
        for method in ('factorized','coseg','strict','shuffle'):
            summary[mode][method]={k:statistics.mean(raw[str(seed)][mode][method][k] for seed in (1,7,19)) for k in raw['1'][mode][method]}
    payload={'cycle':38,'hypothesis':'Object-Centered Support Birth from Paired-World Co-Segmentation',
      'seeds':[1,7,19],'summary':summary,'raw':raw,
      'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      'estimated_complexity':'induction O(NL^2), paired co-segmentation O(QO^2L), inference O(POVL)',
      'final_test_outcome_used_for_selection':False,'fixed_ontology_or_handwritten_slots_used_by_model':False,
      'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
