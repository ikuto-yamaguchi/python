from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse, json, pickle, random, resource, statistics, time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','試料甲':'サンプル甲','試料乙':'サンプル乙'}
VALUES=['棚A','棚B','棚C','棚D','待機','処理中','完了','保留','担当一','担当二']
FILLERS=['補助記録は維持します。','別系統の設定は変更しません。','監査用メモはそのままです。']

@dataclass
class Ex:
    before:str; command:str; after:str; future:str
    obj:str; old:str; new:str; mode:str

@dataclass(frozen=True)
class BoundarySig:
    pos_bucket:int
    width:int
    old_shape:str
    left_shape:str
    right_shape:str

@dataclass
class Fiber:
    sig:BoundarySig
    values:set[str]
    support:int=0
    wrong:int=0
    invariant:int=0
    reversible:int=0
    credit:float=0.0

def shape(s:str)->str:
    return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、：／=\n 「」' else c for c in s)

def make_state(obj:str,value:str,form:int,filler:str)->str:
    if form==0:return f'{obj}の現在値は{value}です。{filler}'
    if form==1:return f'{obj}：設定={value}／補助=維持。{filler}'
    return f'対象{obj}について、記録上の値は「{value}」。{filler}'

def build_bundle(seed:int,bundles:int,mode:str,values_per_bundle:int=4)->list[Ex]:
    rng=random.Random(seed); out=[]
    for _ in range(bundles):
        canon=rng.choice(OBJECTS); surf=ALIASES[canon] if mode=='rename' else canon
        old=rng.choice(VALUES); choices=rng.sample([v for v in VALUES if v!=old],values_per_bundle)
        form=1 if mode=='alternate' else 2 if mode=='alternate2' else 0; filler=rng.choice(FILLERS)
        before=make_state(surf,old,form,filler)
        for new in choices:
            cmd=f'{surf}の値を{new}へ変更してください。'
            if mode=='order':cmd=f'{new}へ変更してください。対象は{surf}です。'
            elif mode=='lexeme':cmd=f'対象{surf}は以後{new}扱いにします。'
            elif mode=='nested':cmd=f'依頼内容は「{surf}の値を{new}へ変更してください」です。'
            elif mode=='omitted':cmd=f'それを{new}へ変更してください。'
            elif mode=='paragraph':cmd=f'前段説明。{rng.choice(FILLERS)}\n{cmd}\n後段注記。'
            elif mode=='plan':
                alt=rng.choice([v for v in VALUES if v not in (old,new)]); cmd=f'{surf}を{alt}にする案は撤回します。最終的には{new}へ変更してください。'
            elif mode=='counterfactual':cmd=f'もし変更しなければ{surf}は{old}のままです。実際には{surf}を{new}へ変更してください。'
            after=make_state(surf,new,form,filler); future=f'次の観測でも{surf}は{new}であり、変更対象外は維持されます。'
            out.append(Ex(before,cmd,after,future,surf,old,new,mode))
    return out

def diff_span(a:str,b:str):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return l,len(a)-r if r else len(a),a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

def true_span(e:Ex):
    i=e.before.find(e.old); return i,i+len(e.old)

def boundary_sig(before:str,a:int,b:int)->BoundarySig:
    return BoundarySig(round(16*a/max(1,len(before))),b-a,shape(before[a:b]),shape(before[max(0,a-6):a]),shape(before[b:b+6]))

def candidate_values(e:Ex,new_shapes:set[str],learned_values:set[str]|None=None)->list[str]:
    vals=[]
    if learned_values:vals.extend(v for v in learned_values if v in e.command and v not in e.before)
    for i in range(len(e.command)):
        for j in range(i+1,min(len(e.command),i+11)+1):
            x=e.command[i:j]
            if x not in e.before and shape(x) in new_shapes:vals.append(x)
    return sorted(set(vals),key=lambda x:(-len(x),x))[:16]

def outside_signature(text:str,a:int,b:int)->str:return text[:a]+'<X>'+text[b:]

def apply(e:Ex,sig:BoundarySig,value:str):
    target=round(sig.pos_bucket*len(e.before)/16); out=[]
    for a in range(max(0,target-3),min(len(e.before),target+4)):
        for w in range(max(1,sig.width-2),min(14,sig.width+3)):
            b=a+w
            if b>len(e.before) or shape(e.before[a:b])!=sig.old_shape:continue
            if shape(e.before[max(0,a-6):a])!=sig.left_shape or shape(e.before[b:b+6])!=sig.right_shape:continue
            out.append((e.before[:a]+value+e.before[b:],a,b,value))
    return out

class Model:
    def __init__(self,mode:str):
        self.mode=mode; self.fibers=[]; self.raw_sigs=0; self.probe_audits=0; self.non_target_checks=0; self.training_seconds=0.0
    def fit(self,ind:list[Ex],probe:list[Ex],shuffle:bool=False):
        t=time.perf_counter(); sig_values=defaultdict(set); sig_support=Counter(); new_shapes=defaultdict(set)
        for e in ind:
            a,b,old,new=diff_span(e.before,e.after)
            if not old or not new:continue
            sig=boundary_sig(e.before,a,b); sig_values[sig].add(new); sig_support[sig]+=1; new_shapes[sig].add(shape(new))
        self.raw_sigs=len(sig_support); observations=[e.after for e in probe]
        if shuffle:observations=observations[1:]+observations[:1]
        fibers=[]
        for sig,support in sig_support.most_common(64):
            values=set(sig_values[sig]); pos=wrong=inv=rev=0; min_values=1 if self.mode=='single' else 3
            if len(values)<min_values:continue
            for e,obs in zip(probe,observations):
                for v in candidate_values(e,new_shapes[sig],values):
                    self.probe_audits+=1
                    for pred,a,b,_ in apply(e,sig,v):
                        if pred==obs:
                            pos+=1; invariant=outside_signature(e.before,a,b)==outside_signature(obs,a,a+len(v)); inv+=int(invariant); self.non_target_checks+=1
                            old=e.before[a:b]; rev+=int(obs[:a]+old+obs[a+len(v):]==e.before); values.add(v)
                        else:wrong+=1
            accept=pos>=2 and len(values)>=3 if self.mode=='no_invariance' else pos>=2 and len(values)>=min_values and inv>=pos and rev>=pos
            if accept:
                f=Fiber(sig,values,support,wrong,inv,rev); f.credit=(2*pos+inv+rev-wrong)/(1+pos+wrong); fibers.append(f)
        self.fibers=sorted(fibers,key=lambda f:(f.credit,f.invariant,f.support),reverse=True)[:32]; self.training_seconds=time.perf_counter()-t
    def predict(self,e:Ex):
        outputs=[]
        for fi,f in enumerate(self.fibers):
            for v in candidate_values(e,{shape(x) for x in f.values},f.values):
                for pred,a,b,_ in apply(e,f.sig,v):
                    score=f.credit+int(v in e.command)+int('維持' in pred)-.02*(b-a)+.1*len(f.values); outputs.append((score,pred,a,b,v,fi))
        if not outputs:return None,0
        outputs.sort(key=lambda x:(x[0],x[1],x[2],x[3],x[4]),reverse=True); best=outputs[0][0]; tops=[x for x in outputs if best-x[0]<.35]
        if len({x[1] for x in tops})>1:return None,len(outputs)
        return tops[0],len(outputs)

def evaluate(m:Model,test:list[Ex]):
    correct=wrong=null=exact=inv=0; counts=[]; st=time.perf_counter()
    for e in test:
        p,n=m.predict(e); counts.append(n)
        if p is None:null+=1; continue
        _,pred,a,b,v,_=p; correct+=int(pred==e.after); wrong+=int(pred!=e.after); ta,tb=true_span(e); exact+=int(a==ta and b==tb and v==e.new); inv+=int(outside_signature(e.before,a,b)==outside_signature(pred,a,a+len(v)))
    N=len(test)
    return {'accuracy':correct/N,'wrong_commit':wrong/N,'null_rate':null/N,'exact_boundary':exact/N,'non_target_invariance':inv/N,'mean_candidates':statistics.mean(counts),'fibers':len(m.fibers),'fiber_values':sum(len(f.values) for f in m.fibers),'raw_signatures':m.raw_sigs,'probe_audits':m.probe_audits,'non_target_checks':m.non_target_checks,'model_bytes':len(pickle.dumps(m)),'training_seconds':m.training_seconds,'inference_ms':(time.perf_counter()-st)*1000/N}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',default='MEASUREMENTS_CYCLE_034.json'); args=ap.parse_args()
    modes=['seen','order','lexeme','rename','alternate','alternate2','nested','omitted','paragraph','plan','counterfactual']; methods=['single','multi','no_invariance','shuffle']; raw={}
    for seed in (1,7,19):
        train=build_bundle(seed,18,'seen',4)+build_bundle(seed+1,10,'rename',4)+build_bundle(seed+2,10,'alternate',4); ind=train[:96]; probe=train[96:]; models={}
        for method in methods:
            m=Model(method); m.fit(ind,probe,shuffle=method=='shuffle'); models[method]=m
        raw[str(seed)]={mode:{method:evaluate(m,build_bundle(seed+999,6,mode,4)) for method,m in models.items()} for mode in modes}
    summary={}
    for mode in modes:
        summary[mode]={}
        for method in methods:
            keys=raw['1'][mode][method].keys(); summary[mode][method]={k:statistics.mean(raw[str(seed)][mode][method][k] for seed in (1,7,19)) for k in keys}
    payload={'cycle':34,'hypothesis':'Multi-Value Intervention Fibers from Non-Target Invariance Cross-Tests','seeds':[1,7,19],'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'signature O(NL), multi-value probe O(FQVL), inference O(FVL)','final_test_outcomes_used_for_ranking':False,'hidden_labels_used_only_for_evaluation':True,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(args.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
