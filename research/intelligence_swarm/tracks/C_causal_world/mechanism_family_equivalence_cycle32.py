from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse,json,pickle,random,resource,statistics,time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
FIELDS=['場所','状態','担当']
VALUES={'場所':['棚A','棚B','棚C','棚D'],'状態':['待機','処理中','完了','保留'],'担当':['担当一','担当二','担当三','担当四']}
STATE0='{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。'
STATE1='{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。'
CMDS={'場所':['{o}を{v}へ移してください。','{o}の保管先を{v}へ変更してください。'],'状態':['{o}を{v}にしてください。','{o}の進行状態を{v}へ切り替えてください。'],'担当':['{o}を{v}の担当にしてください。','{o}の受け持ちを{v}へ変更してください。']}
HELD={'場所':['{v}へ移してください、対象は{o}です。'],'状態':['{v}扱いにしてください、対象は{o}です。'],'担当':['{v}へ引き継いでください、対象は{o}です。']}
LEX={'場所':['対象{o}は次から{v}で保管。'],'状態':['対象{o}は以後{v}として運用。'],'担当':['対象{o}の受持を{v}へ。']}
OMIT={'場所':['それを{v}へ移してください。'],'状態':['その対象を{v}にしてください。'],'担当':['担当は{v}へ変えてください。']}
DIST=['別件は変更しません。','前段の説明を維持します。','補助記録には触れません。']

@dataclass
class Ex:
    before:str; command:str; after:str; future:str
    obj:str; canonical:str; field:str; old:str; new:str; mode:str

@dataclass(frozen=True)
class OpSig:
    old_shape:str; new_shape:str; left_bucket:int; right_bucket:int
    old_len:int; new_len:int; delta:int

def state(o,d,alt=False):
    return (STATE1 if alt else STATE0).format(o=o,loc=d['場所'],status=d['状態'],owner=d['担当'])

def shape(s):
    return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、／=：:\n 「」' else c for c in s)

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

def spans(t,lo=1,hi=10):
    return [(i,j,t[i:j]) for i in range(len(t)) for j in range(i+lo,min(len(t),i+hi)+1) if not any(c in t[i:j] for c in '。、\n「」')]

def build(seed,n,mode):
    rng=random.Random(seed); world={}; out=[]; focus=None
    for k in range(n):
        continuation=mode=='omitted' and k>0
        canon=focus if continuation else rng.choice(OBJECTS)
        surf=ALIASES[canon] if mode=='rename' else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS})
        fld=rng.choice(FIELDS); old=world[canon][fld]
        new=rng.choice([v for v in VALUES[fld] if v!=old])
        alt=mode=='alternate'; before=state(surf,world[canon],alt)
        forms=HELD[fld] if mode=='order' else LEX[fld] if mode=='lexeme' else OMIT[fld] if mode=='omitted' else CMDS[fld]
        command=rng.choice(forms).format(o=surf,v=new)
        if mode=='nested': command=f'依頼内容は「{command}」です。'
        elif mode=='paragraph': command=' '.join(rng.choice(DIST) for _ in range(4))+'\n'+command
        elif mode=='plan':
            altv=rng.choice([v for v in VALUES[fld] if v not in (old,new)])
            command=f'{surf}を{altv}にする案は撤回します。最終的には{command}'
        elif mode=='counterfactual':
            command=f'もし変更しなければ{surf}は{old}のままです。実際には{command}'
        world[canon][fld]=new
        after=state(surf,world[canon],alt)
        future=f'次の観測でも{surf}の更新結果は{new}で、補助記録は維持されます。'
        out.append(Ex(before,command,after,future,surf,canon,fld,old,new,mode)); focus=canon
    return out

def bucket(pos,n): return min(7,int(8*pos/max(1,n)))
def signature(before,a,b,val):
    return OpSig(shape(before[a:b]),shape(val),bucket(a,len(before)),bucket(len(before)-b,len(before)),b-a,len(val),len(val)-(b-a))

def apply_sig(e,sig,val):
    candidates=[]
    for a,b,seg in spans(e.before,1,10):
        if shape(seg)!=sig.old_shape: continue
        distance=abs(bucket(a,len(e.before))-sig.left_bucket)+abs(bucket(len(e.before)-b,len(e.before))-sig.right_bucket)+abs((b-a)-sig.old_len)
        if distance<=2: candidates.append((distance,a,b))
    if not candidates: return []
    best=min(x[0] for x in candidates)
    return [(e.before[:a]+val+e.before[b:],a,b) for d,a,b in candidates if d==best]

def value_candidates(e,sig):
    raw=[x for _,_,x in spans(e.command,1,10) if x not in e.before and shape(x)==sig.new_shape]
    maximal=[x for x in raw if not any(x in y and x!=y for y in raw)]
    return sorted(set(maximal+raw),key=lambda x:(abs(len(x)-sig.new_len),-len(x),x))[:8]

class Model:
    def __init__(self,method):
        self.method=method; self.sigs=[]; self.families=[]
        self.family_credit=Counter(); self.probe_audits=0; self.train_seconds=0

    def fit(self,induction,probe,shuffle=False):
        started=time.perf_counter(); counts=Counter()
        for e in induction:
            l,r,old,new=diff(e.before,e.after)
            if not old or not new or new not in e.command: continue
            for dl in (-1,0,1):
                for dr in (-1,0,1):
                    a=max(0,l+dl); b=min(len(e.before),len(e.before)-r+dr if r else len(e.before)+dr)
                    if a>=b or any(c in e.before[a:b] for c in '。、\n'): continue
                    counts[signature(e.before,a,b,new)]+=1
        self.sigs=[s for s,n in counts.most_common(24) if n>=2]
        observed=[e.after for e in probe]
        if shuffle and observed: observed=observed[1:]+observed[:1]
        responses={s:[] for s in self.sigs}; damage={s:0 for s in self.sigs}; inverse_ok={s:0 for s in self.sigs}
        for e,obs in zip(probe,observed):
            for sig in self.sigs:
                predictions=[]
                for value in value_candidates(e,sig):
                    predictions += [(p,a,b,value) for p,a,b in apply_sig(e,sig,value)]
                self.probe_audits+=len(predictions)
                correct=[x for x in predictions if x[0]==obs]
                if correct:
                    responses[sig].append(1)
                    inverse_ok[sig]+=sum(1 for p,a,b,v in correct if p[:a]+e.before[a:b]+p[a+len(v):]==e.before)
                elif predictions:
                    responses[sig].append(-1)
                    damage[sig]+=sum(1 for p,_,_,_ in predictions if ('補助' in p)!=('補助' in e.before))
                else:
                    responses[sig].append(0)
        groups=defaultdict(list)
        for sig,vector in responses.items(): groups[tuple(vector)].append(sig)
        for vector,members in groups.items():
            positive=sum(v==1 for v in vector); wrong=sum(v==-1 for v in vector)
            if len(members)>=2 and positive>=2 and wrong<=positive:
                self.families.append((tuple(members),vector,positive,wrong))
                for sig in members:
                    self.family_credit[sig]=2*positive-wrong-damage[sig]*.2+inverse_ok[sig]*.1
        self.train_seconds=time.perf_counter()-started

    def generate(self,e):
        active=self.sigs if self.method=='surface' else [s for family,_,_,_ in self.families for s in family]
        output=[]
        for sig in active:
            for value in value_candidates(e,sig):
                for predicted,a,b in apply_sig(e,sig,value):
                    inverse=int(predicted[:a]+e.before[a:b]+predicted[a+len(value):]==e.before)
                    preserved=int(('補助' in predicted)==('補助' in e.before))
                    score=inverse+preserved+int(value in e.command)
                    if self.method in ('family','graph'): score+=.25*self.family_credit[sig]
                    output.append({'pred':predicted,'a':a,'b':b,'v':value,'s':sig,'score':score})
        best={}
        for candidate in output:
            key=candidate['pred']
            if key not in best or candidate['score']>best[key]['score']: best[key]=candidate
        return sorted(best.values(),key=lambda x:x['score'],reverse=True)[:24]

    def predict(self,e):
        candidates=self.generate(e)
        if not candidates: return None,0,'collapse'
        if self.method=='graph':
            votes=Counter(c['pred'] for c in candidates)
            for c in candidates: c['score']+=.4*votes[c['pred']]
            candidates.sort(key=lambda x:x['score'],reverse=True)
        if len(candidates)>1 and candidates[0]['score']-candidates[1]['score']<.5:
            return None,len(candidates),'tie'
        return candidates[0],len(candidates),'commit'

def evaluate(model,test):
    started=time.perf_counter(); correct=wrong=null=exact=0; counts=[]; reasons=Counter()
    for e in test:
        prediction,n,reason=model.predict(e); counts.append(n); reasons[reason]+=1
        if prediction is None: null+=1
        elif prediction['pred']==e.after: correct+=1
        else: wrong+=1
        if prediction is not None:
            exact+=int(prediction['v']==e.new and e.before[prediction['a']:prediction['b']]==e.old)
    size=len(test)
    return {'accuracy':correct/size,'wrong_commit':wrong/size,'null_rate':null/size,'exact_target_value_recall':exact/size,'mean_candidates':statistics.mean(counts),'signatures':len(model.sigs),'families':len(model.families),'family_members':sum(len(x[0]) for x in model.families),'probe_audits':model.probe_audits,'model_bytes':len(pickle.dumps(model)),'training_seconds':model.train_seconds,'inference_ms':(time.perf_counter()-started)*1000/size,'reasons':dict(reasons)}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output',default='MEASUREMENTS_CYCLE_032.json'); args=parser.parse_args()
    modes=['seen','order','lexeme','rename','alternate','nested','omitted','paragraph','plan','counterfactual']; raw={}
    for seed in (1,7,19):
        data=build(seed,72,'seen'); induction,probe=data[:48],data[48:72]; models={}
        for method in ('surface','family','graph','shuffle'):
            model=Model('family' if method=='shuffle' else method)
            model.fit(induction,probe,shuffle=method=='shuffle'); models[method]=model
        raw[str(seed)]={mode:{name:evaluate(model,build(seed+999,12,mode)) for name,model in models.items()} for mode in modes}
    summary={}
    for mode in modes:
        summary[mode]={}
        for method in ('surface','family','graph','shuffle'):
            numeric=[k for k,v in raw['1'][mode][method].items() if isinstance(v,(int,float))]
            summary[mode][method]={k:statistics.mean(raw[str(seed)][mode][method][k] for seed in (1,7,19)) for k in numeric}
    payload={'cycle':32,'hypothesis':'Mechanism-Family Birth from Cross-Input Intervention Equivalence Classes','seeds':[1,7,19],'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'signature birth O(NL), probe response O(QSVL), family partition O(SQ log S), inference O(SVL)','final_test_outcomes_used_for_selection':False,'fixed_ontology_or_handwritten_slots_used_by_model':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(args.output,'w',encoding='utf-8') as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
