"""系列A Cycle 030: operator-centered recurrent error cancellation.

固定ontology/手書きslotを使わず、局所edit operatorをforward・inverse・
idempotenceで監査し、反復緩和でpredictive stateを選択する最小実装。
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse, json, pickle, random, resource, statistics, time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末","大型端末":"大きい端末","北側の鍵":"北のキー","南側の鍵":"南のキー","試料甲":"サンプル甲","試料乙":"サンプル乙"}
VALUES=["棚A","棚B","棚C","棚D","待機","処理中","完了","保留","担当一","担当二","担当三","担当四"]
FILL=["補助記録は維持します。","別件の設定は変えません。","前段の注意事項はそのままです。"]

@dataclass
class Turn:
    before:str; command:str; after:str; future:str
    obj:str; canonical:str; value:str; old:str

@dataclass
class Operator:
    left:str; right:str; old_shape:str; new_shape:str
    support:int=0; wrong:int=0; noexec:int=0; credit:float=0.0

def shape(s):
    return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、：／=\n 「」' else c for c in s)

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

def spans(text,lo=1,hi=12):
    return [text[i:j] for i in range(len(text)) for j in range(i+lo,min(len(text),i+hi)+1)
            if not any(c in text[i:j] for c in '。、\n「」')]

def make_dialog(seed,n,mode):
    rng=random.Random(seed); rows=[]; focus=None; world={}
    for t in range(n):
        cont=mode in ('omitted','switchmix') and t>0 and (mode=='omitted' or t%2==1)
        obj=focus if cont else rng.choice(OBJECTS); surf=ALIASES[obj] if mode=='rename' else obj
        old=world.get(obj,rng.choice(VALUES)); new=rng.choice([v for v in VALUES if v!=old])
        before=f'{surf}の現在値は{old}です。{rng.choice(FILL)}'
        if mode=='omitted' and t>0: command=f'それを{new}へ変更してください。'
        elif mode=='switchmix' and t>0 and t%2==1: command=f'その対象を{new}へ変更してください。'
        elif mode=='order': command=f'{new}へ変更してください、対象は{surf}です。'
        elif mode=='lexeme': command=f'対象{surf}は次から{new}扱いにします。'
        elif mode=='nested': command=f'依頼内容は「{surf}の値を{new}へ変更してください。」です。'
        elif mode=='paragraph': command=f'{rng.choice(FILL)}\n{surf}の値を{new}へ変更してください。\n{rng.choice(FILL)}'
        elif mode=='plan':
            alt=rng.choice([v for v in VALUES if v not in (old,new)])
            command=f'{surf}を{alt}にする案は撤回し、最終的には{new}へ変更してください。'
        elif mode=='counterfactual': command=f'もし変更しなければ{surf}は{old}のままです。実際には{surf}を{new}へ変更してください。'
        else: command=f'{surf}の値を{new}へ変更してください。'
        after=f'{surf}の現在値は{new}です。{rng.choice(FILL)}'; future=f'次の観測でも{surf}は{new}のままです。'
        rows.append(Turn(before,command,after,future,surf,obj,new,old)); world[obj]=new; focus=obj
    return rows

def apply(before,value,op,new_shape=False):
    hits=[]; p=0; expected=op.new_shape if new_shape else op.old_shape
    while True:
        i=before.find(op.left,p) if op.left else p
        if i<0: break
        a=i+len(op.left); b=before.find(op.right,a) if op.right else len(before)
        if b>=a and shape(before[a:b])==expected: hits.append((a,b))
        p=i+1
        if not op.left or p>=len(before): break
    if len(hits)!=1: return None
    a,b=hits[0]; return before[:a]+value+before[b:]

class Model:
    def __init__(self,method): self.method=method; self.ops=[]
    def fit(self,dialogs):
        c=defaultdict(lambda:[0,0,0]); t0=time.perf_counter()
        for rows in dialogs:
            for x in rows:
                l,r,old,new=diff(x.before,x.after)
                if not old or not new: continue
                key=(x.before[max(0,l-8):l],x.before[len(x.before)-r:len(x.before)-r+8] if r else '',shape(old),shape(new))
                op=Operator(*key); pred=apply(x.before,new,op); inv=apply(x.after,old,op,True)
                idem=pred is not None and apply(pred,new,op,True)==pred
                if pred is None: c[key][2]+=1
                elif pred==x.after and inv==x.before and idem: c[key][0]+=1
                else: c[key][1]+=1
        for k,(pos,wrong,noexec) in c.items():
            if pos>=2: self.ops.append(Operator(*k,pos,wrong,noexec,(pos-wrong)/(pos+wrong+noexec)))
        self.ops=sorted(self.ops,key=lambda o:(o.credit,o.support,-o.wrong),reverse=True)[:64]
        self.train_seconds=time.perf_counter()-t0
    def candidates(self,cur,prev=None):
        common=[s for s in spans(cur.command,2,12) if s in cur.before]
        objects=sorted({x for x in common if not any(x in y and x!=y for y in common)},key=len,reverse=True)[:8]
        if self.method in ('carry','recurrent') and prev:
            objects+=sorted(set(spans(prev.after+' '+prev.future,2,12)),key=len,reverse=True)[:8]
        novel=[s for s in spans(cur.command,1,10) if s not in cur.before]
        values=sorted(set(novel),key=len,reverse=True)[:12]
        out=[]
        for o in objects or ['']:
            for v in values:
                for i,op in enumerate(self.ops):
                    pred=apply(cur.before,v,op)
                    if pred is None: continue
                    inv=apply(pred,cur.old,op,True); idem=apply(pred,v,op,True)==pred
                    score=op.support-op.wrong-2*int(inv!=cur.before)-2*int(not idem)
                    if self.method=='recurrent': score+=1.5*op.credit
                    out.append((score,pred,o,v,i))
        return out[:96]
    def infer(self,cur,prev=None):
        active=self.candidates(cur,prev)
        if not active: return None,0,0,'candidate_collapse'
        prior=None; sweeps=0
        while sweeps<6:
            sweeps+=1; active=sorted(active,reverse=True); best=active[0][0]
            active=[x for x in active if x[0]>=best-.25][:16]
            sig=tuple(active)
            if sig==prior: break
            prior=sig
        if len(active)>1 and active[0][0]-active[1][0]<.5: return None,sweeps,len(active),'tie'
        return active[0],sweeps,len(active),'fixed_point'

def evaluate(seed,mode):
    train=[make_dialog(seed+i,56,m) for i,m in enumerate(('seen','rename','switchmix','paragraph','plan'))]
    test=make_dialog(seed+999,28,mode); out={}
    for method in ('onepass','carry','recurrent'):
        m=Model(method); m.fit(train); vals=[]; t0=time.perf_counter()
        for prev,cur in zip(test[:-1],test[1:]):
            p,sw,act,reason=m.infer(cur,prev)
            vals.append({'accuracy':p is not None and p[1]==cur.after,'wrong_commit':p is not None and p[1]!=cur.after,
                         'null':p is None,'pair_recall':p is not None and p[2]==cur.obj and p[3]==cur.value,
                         'sweeps':sw,'active':act,'reason':reason})
        ms=(time.perf_counter()-t0)*1000/len(vals)
        z={k:statistics.mean(float(v[k]) for v in vals) for k in ('accuracy','wrong_commit','null','pair_recall','sweeps','active')}
        z.update({'max_sweeps':max(v['sweeps'] for v in vals),'operators':len(m.ops),'model_bytes':len(pickle.dumps(m)),
                  'training_seconds':m.train_seconds,'inference_ms':ms,'reasons':dict(Counter(v['reason'] for v in vals))})
        out[method]=z
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',default='MEASUREMENTS_CYCLE_030.json'); a=ap.parse_args()
    modes=('seen','order','lexeme','rename','nested','omitted','switchmix','paragraph','plan','counterfactual')
    raw={str(seed):{mode:evaluate(seed,mode) for mode in modes} for seed in (1,7,19)}; summary={}
    for mode in modes:
        summary[mode]={}
        for method in ('onepass','carry','recurrent'):
            keys=[k for k,v in raw['1'][mode][method].items() if isinstance(v,(int,float))]
            summary[mode][method]={k:statistics.mean(raw[str(seed)][mode][method][k] for seed in (1,7,19)) for k in keys}
    payload={'cycle':30,'hypothesis':'Operator-Centered Predictive State Birth from Recurrent Error-Cancellation Loops',
             'seeds':[1,7,19],'summary':summary,'raw':raw,
             'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             'estimated_complexity':'operator induction O(NL), proposal O(OVPL), recurrent relaxation O(SH)',
             'current_turn_after_future_used_for_selection':False,'fixed_ontology_or_handwritten_slots_used_by_model':False,
             'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f: json.dump(payload,f,ensure_ascii=False,indent=2)
if __name__=='__main__': main()
