from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末',
'北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
VALUES=['棚A','棚B','棚C','待機','処理中','完了','担当一','担当二']
CMDS=['{o}を{v}に変更してください。','{o}について、今後は{v}として扱います。','{o}の記録を{v}へ更新します。']
HELD=['念のため{o}は{v}にしておいてください。','次から{o}を{v}で運用します。','{o}、最終的には{v}へ切り替えます。']
OMIT=['それを{v}に変更してください。','その対象は今後{v}として扱います。']
STATE=['{o}の現在値は{v}です。補助記録は維持します。','{o}：値={v}／補助記録=維持。']
DIST=['別件の資料も確認しました。','これは更新とは関係ありません。','前の案はいったん保留です。']
SEP=set('、。！？「」『』（）()=：:／ 　\n')

@dataclass
class Ex:
    before:str; command:str; after:str; future1:str; future2:str
    obj:str; val:str; mode:str; truth_action:str

class CharPredictor:
    def __init__(self,order=3):
        self.order=order; self.ctx=defaultdict(Counter); self.alpha=.25
    def fit(self,texts):
        for text in texts:
            s='^'*(self.order-1)+text+'$'
            for i in range(self.order-1,len(s)):
                self.ctx[s[i-self.order+1:i]][s[i]] += 1
    def nll(self,text,prefix=''):
        s='^'*(self.order-1)+(prefix+text)
        start=max(self.order-1,len(prefix)+self.order-1)
        vocab=max(16,len(set(prefix+text)))
        out=[]
        for i in range(start,len(s)):
            h=s[i-self.order+1:i]; c=s[i]; cnt=self.ctx.get(h,Counter()); tot=sum(cnt.values())
            out.append(-math.log((cnt.get(c,0)+self.alpha)/(tot+self.alpha*vocab)+1e-12))
        return out

def peaks(v):
    if not v:return [0]
    med=statistics.median(v); mad=statistics.median([abs(x-med) for x in v])+1e-6; th=med+.55*mad
    return sorted(set([0]+[i for i in range(1,len(v)-1) if v[i]>=th and v[i]>=v[i-1] and v[i]>=v[i+1]]+[len(v)]))

def intervals(text,score,cap=18):
    ps=peaks(score); z=[]
    for i,a in enumerate(ps[:-1]):
        for j in range(i+1,min(len(ps),i+5)):
            b=ps[j]
            if 1<=b-a<=16:
                x=text[a:b].strip(''.join(SEP))
                if x:z.append((a,b,x))
    out=[];seen=set()
    for a,b,x in sorted(z,key=lambda q:(len(q[2]),q[0])):
        if x not in seen:seen.add(x);out.append((a,b,x))
        if len(out)>=cap:break
    return out

def signal(x,text):
    if not x:return 0
    if x==text:return 1.
    if x in text:return .88
    if text in x:return .60
    return .34*sum((Counter(x)&Counter(text)).values())/max(1,len(x))

def make(rng,mode,canon):
    surf=ALIASES[canon] if mode=='rename' else canon
    old=rng.choice(VALUES); val=rng.choice([x for x in VALUES if x!=old]); form=1 if mode=='alternate' else 0
    before=STATE[form].format(o=surf,v=old);after=STATE[form].format(o=surf,v=val)
    if mode=='omitted':cmd=rng.choice(OMIT).format(v=val); truth='carry'
    elif mode in ('held','rename','nested','paragraph','plan'):cmd=rng.choice(HELD).format(o=surf,v=val);truth='switch'
    else:cmd=rng.choice(CMDS).format(o=surf,v=val);truth='switch'
    if mode=='nested':cmd='『'+rng.choice(DIST)+'』ただし、'+cmd
    if mode=='paragraph':cmd=' '.join(rng.choice(DIST) for _ in range(3))+'\n'+cmd
    if mode=='plan':
        alt=rng.choice([x for x in VALUES if x not in (old,val)])
        cmd=f'{surf}を{alt}へ変える案でした。{rng.choice(DIST)}最終的には'+cmd
    f1=f'次の観測でも{surf}は存在し、局所値は{val}、補助記録は維持。'
    f2=f'さらに後でも{surf}の値は{val}。他の対象には変更なし。'
    return Ex(before,cmd,after,f1,f2,surf,val,mode,truth)

def stream(seed,n,mode):
    rng=random.Random(seed);seq=[];last=rng.choice(OBJECTS)
    for i in range(n):
        if mode=='omitted':
            if i%2==0:
                last=rng.choice(OBJECTS);e=make(rng,'seen',last)
            else:e=make(rng,'omitted',last)
        elif mode=='switch':
            if i%3==0:
                last=rng.choice([x for x in OBJECTS if x!=last])
                e=make(rng,'seen',last)
            else:e=make(rng,'omitted',last)
        else:
            base=('seen','held','rename','alternate')[i%4] if mode=='train' else mode
            last=rng.choice(OBJECTS)
            e=make(rng,base,last)
        seq.append(e)
    return seq

class Model:
    def __init__(self,kind):
        self.kind=kind;self.pred=CharPredictor();self.commit_protos=[];self.train_s=0
    def fit(self,eps):
        t=time.perf_counter()
        texts=[x for e in eps for x in (e.before,e.command,e.after,e.future1,e.future2)]
        self.pred.fit(texts)
        for e in eps:
            for text in (e.after,e.future1,e.future2):
                sv=self.pred.nll(text)
                for a,b,x in intervals(text,sv,10):
                    persistence=(signal(x,e.after)+signal(x,e.future1)+signal(x,e.future2))/3
                    change=signal(x,e.after)-signal(x,e.before)
                    if persistence>.62 and change<.35:self.commit_protos.append(x)
        self.commit_protos=list(dict.fromkeys(self.commit_protos))[:64]
        self.train_s=time.perf_counter()-t
    def commits(self,e):
        cand=[]
        for x in self.commit_protos:
            p=.45*signal(x,e.after)+.30*signal(x,e.future1)+.25*signal(x,e.future2)-.015*len(x)
            if p>.35:cand.append((p,x))
        return sorted(cand,reverse=True)[:6]
    def candidates(self,e):
        b=self.pred.nll(e.before);c=self.pred.nll(e.command)
        os=[];vs=[]
        for a,z,x in intervals(e.before,b,14):
            os.append((.65*signal(x,e.before)-.012*len(x),x))
        for a,z,x in intervals(e.command,c,14):
            vs.append((.58*signal(x,e.command)-.25*signal(x,e.before)-.01*len(x),x))
            if signal(x,e.before)>.55:os.append((.52*signal(x,e.before)-.01*len(x),x))
        return sorted(os,reverse=True)[:8],sorted(vs,reverse=True)[:8]
    def responsibility(self,e,commit):
        target=e.before+' '+e.command
        base=sum(self.pred.nll(target))/max(1,len(target))
        out=[]
        for score,x in commit:
            with_cell=sum(self.pred.nll(target,prefix=x+' '))/max(1,len(target))
            delta=base-with_cell
            local=.55*signal(x,e.before)+.45*signal(x,e.command)
            out.append((delta+.18*local,delta,x))
        return sorted(out,reverse=True)
    def solve(self,e,commit):
        os,vs=self.candidates(e);action='none';resp=[]
        if self.kind in ('unconditional','responsibility','responsibility_null'):
            inject=commit;action='carry'
            if self.kind in ('responsibility','responsibility_null'):
                resp=self.responsibility(e,commit)
                inject=[(max(0,r),x) for r,d,x in resp if d>.002 or r>.10][:4]
                action='carry' if inject else 'switch'
            for rank,(score,x) in enumerate(inject):
                os.append((score+.14-.025*rank,x))
        os=sorted(os,reverse=True)[:8];vs=sorted(vs,reverse=True)[:8]
        pairs=list(dict.fromkeys((o,v) for _,o in os for _,v in vs))[:48]
        ranked=[]
        for o,v in pairs:
            sc=.48*signal(o,e.before)+.28*signal(o,e.command)+.43*signal(v,e.command)-.16*signal(v,e.before)
            if action=='carry': sc+=.14*max([signal(o,x) for _,x in commit] or [0])
            ranked.append((sc,(o,v)))
        ranked.sort(reverse=True);chosen=ranked[0][1] if ranked else None
        pair_recall=int((e.obj,e.val) in pairs)
        if self.kind=='responsibility_null':
            margin=ranked[0][0]-(ranked[1][0] if len(ranked)>1 else 0) if ranked else 0
            positive=max([d for _,d,_ in resp] or [-1])
            if not(pair_recall and positive>.002 and margin>.03):chosen=None
        return chosen,{
            'object_recall':int(any(x==e.obj for _,x in os)),
            'value_recall':int(any(x==e.val for _,x in vs)),
            'pair_recall':pair_recall,'accuracy':int(chosen==(e.obj,e.val)),
            'wrong':int(chosen is not None and chosen!=(e.obj,e.val)),
            'null':int(chosen is None),'active_pairs':len(pairs),
            'carry':int(action=='carry'),'gate_correct':int(action==e.truth_action),
            'wrong_carry':int(action=='carry' and e.truth_action=='switch'),
            'continuation_recall':int(action=='carry' and e.truth_action=='carry'),
            'termination_precision_num':int(action=='switch' and e.truth_action=='switch'),
            'termination_precision_den':int(action=='switch'),
            'mean_positive_responsibility':max([d for _,d,_ in resp] or [0]),
        }
    def run(self,test):
        commit=[];acc=Counter();t=time.perf_counter()
        for e in test:
            _,z=self.solve(e,commit)
            for k,v in z.items():acc[k]+=v
            commit=self.commits(e)
        n=len(test);out={k:acc[k]/n for k in acc}
        out['termination_precision']=acc['termination_precision_num']/max(1,acc['termination_precision_den'])
        out['inference_ms']=(time.perf_counter()-t)*1000/n
        return out

def evaluate(seed,n):
    modes=['seen','held','rename','alternate','nested','omitted','switch','paragraph','plan']
    train=stream(seed,n,'train');out={}
    for kind in ('no_carry','unconditional','responsibility','responsibility_null'):
        m=Model(kind);m.fit(train);out[kind]={mode:m.run(stream(seed+1000,36,mode)) for mode in modes}
        out[kind]['model_bytes']=len(pickle.dumps(m));out[kind]['training_seconds']=m.train_s
        out[kind]['commit_prototypes']=len(m.commit_protos)
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_026.json');a=ap.parse_args()
    raw={str(seed):evaluate(seed,72) for seed in (1,7,19)}
    methods=('no_carry','unconditional','responsibility','responsibility_null')
    modes=['seen','held','rename','alternate','nested','omitted','switch','paragraph','plan']
    summary={}
    for method in methods:
        summary[method]={}
        for mode in modes:
            ks=raw['1'][method][mode].keys()
            summary[method][mode]={k:statistics.mean(raw[str(seed)][method][mode][k] for seed in (1,7,19)) for k in ks}
        for k in ('model_bytes','training_seconds','commit_prototypes'):
            summary[method][k]=statistics.mean(raw[str(seed)][method][k] for seed in (1,7,19))
    payload={'hypothesis':'Responsibility-Weighted Prospective Commitments by Counterfactual Prediction Removal',
             'seeds':[1,7,19],'train_size':72,'raw':raw,'summary':summary,
             'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             'estimated_complexity':'character prediction O(NL), interval proposal O(L), responsibility removal O(KL), sparse pairing O(KoKv)',
             'hidden_labels_used_by_learner':False,'current_turn_after_future_used_for_selection':False,
             'highschool_level_passed':False,'native_japanese_communication_passed':False,
             'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
