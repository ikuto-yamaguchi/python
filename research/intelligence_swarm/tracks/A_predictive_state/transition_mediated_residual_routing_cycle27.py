from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
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
    def __init__(self,order=3): self.order=order; self.ctx=defaultdict(Counter); self.alpha=.25
    def fit(self,texts):
        for text in texts:
            s='^'*(self.order-1)+text+'$'
            for i in range(self.order-1,len(s)): self.ctx[s[i-self.order+1:i]][s[i]]+=1
    def nll(self,text):
        s='^'*(self.order-1)+text; vocab=max(16,len(set(text))); out=[]
        for i in range(self.order-1,len(s)):
            h=s[i-self.order+1:i]; c=s[i]; cnt=self.ctx.get(h,Counter()); tot=sum(cnt.values())
            out.append(-math.log((cnt.get(c,0)+self.alpha)/(tot+self.alpha*vocab)+1e-12))
        return out

def peaks(v):
    if not v:return [0]
    med=statistics.median(v); mad=statistics.median([abs(x-med) for x in v])+1e-6; th=med+.7*mad
    return sorted(set([0]+[i for i in range(1,len(v)-1) if v[i]>=th and v[i]>=v[i-1] and v[i]>=v[i+1]]+[len(v)]))

def intervals(text,score,cap=16):
    ps=peaks(score); z=[]
    for i,a in enumerate(ps[:-1]):
        for j in range(i+1,min(len(ps),i+5)):
            b=ps[j]
            if 1<=b-a<=16:
                x=text[a:b].strip(''.join(SEP))
                if x:z.append((a,b,x))
    out=[]; seen=set()
    for a,b,x in sorted(z,key=lambda q:(-sum(score[a:b])/max(1,b-a),len(q[2]))):
        if x not in seen: seen.add(x); out.append((a,b,x))
        if len(out)>=cap:break
    return out

def signal(x,text):
    if not x:return 0
    if x==text:return 1.
    if x in text:return .9
    if text in x:return .6
    return .35*sum((Counter(x)&Counter(text)).values())/max(1,len(x))

def make(rng,mode,canon):
    surf=ALIASES[canon] if mode=='rename' else canon
    old=rng.choice(VALUES); val=rng.choice([x for x in VALUES if x!=old]); form=1 if mode=='alternate' else 0
    before=STATE[form].format(o=surf,v=old); after=STATE[form].format(o=surf,v=val)
    if mode=='omitted': cmd=rng.choice(OMIT).format(v=val); truth='carry'
    elif mode in ('held','rename','nested','paragraph','plan'): cmd=rng.choice(HELD).format(o=surf,v=val); truth='switch'
    else: cmd=rng.choice(CMDS).format(o=surf,v=val); truth='switch'
    if mode=='nested': cmd='『'+rng.choice(DIST)+'』ただし、'+cmd
    if mode=='paragraph': cmd=' '.join(rng.choice(DIST) for _ in range(3))+'\n'+cmd
    if mode=='plan':
        alt=rng.choice([x for x in VALUES if x not in (old,val)])
        cmd=f'{surf}を{alt}へ変える案でした。{rng.choice(DIST)}最終的には'+cmd
    f1=f'次の観測でも{surf}は存在し、局所値は{val}、補助記録は維持。'
    f2=f'さらに後でも{surf}の値は{val}。他の対象には変更なし。'
    return Ex(before,cmd,after,f1,f2,surf,val,mode,truth)

def stream(seed,n,mode):
    rng=random.Random(seed); seq=[]; last=rng.choice(OBJECTS)
    for i in range(n):
        if mode=='omitted':
            if i%2==0: last=rng.choice(OBJECTS); e=make(rng,'seen',last)
            else: e=make(rng,'omitted',last)
        elif mode=='switch':
            if i%3==0: last=rng.choice([x for x in OBJECTS if x!=last]); e=make(rng,'seen',last)
            else:e=make(rng,'omitted',last)
        else:
            base=('seen','held','rename','alternate')[i%4] if mode=='train' else mode
            last=rng.choice(OBJECTS); e=make(rng,base,last)
        seq.append(e)
    return seq

class Model:
    def __init__(self,kind): self.kind=kind; self.pred=CharPredictor(); self.commit_protos=[]; self.route_protos=[]; self.train_s=0
    def fit(self,eps):
        t=time.perf_counter(); self.pred.fit([x for e in eps for x in (e.before,e.command,e.after,e.future1,e.future2)])
        for e in eps:
            for text in (e.after,e.future1,e.future2):
                for _,_,x in intervals(text,self.pred.nll(text),10):
                    persistence=(signal(x,e.after)+signal(x,e.future1)+signal(x,e.future2))/3
                    if persistence>.68 and signal(x,e.before)>.35:self.commit_protos.append(x)
        self.commit_protos=list(dict.fromkeys(self.commit_protos))[:64]
        for prev,cur in zip(eps[:-1],eps[1:]):
            commits=self.commits(prev)
            target=cur.before+' '+cur.command
            residuals=intervals(target,self.pred.nll(target),12)
            for cs,c in commits:
                for a,b,r in residuals[:6]:
                    overlap=.55*signal(c,cur.before)+.45*signal(c,cur.command)
                    local=sum(self.pred.nll(target)[a:b])/max(1,b-a)
                    if overlap>.38 and local>1.0:self.route_protos.append((c,r,overlap,local))
        self.route_protos=self.route_protos[:32]; self.train_s=time.perf_counter()-t
    def commits(self,e):
        cand=[]
        for x in self.commit_protos:
            p=.45*signal(x,e.after)+.30*signal(x,e.future1)+.25*signal(x,e.future2)-.015*len(x)
            if p>.35:cand.append((p,x))
        return sorted(cand,reverse=True)[:6]
    def candidates(self,e):
        os=[];vs=[]
        for _,_,x in intervals(e.before,self.pred.nll(e.before),14): os.append((.65*signal(x,e.before)-.012*len(x),x))
        for _,_,x in intervals(e.command,self.pred.nll(e.command),14):
            vs.append((.58*signal(x,e.command)-.25*signal(x,e.before)-.01*len(x),x))
            if signal(x,e.before)>.55: os.append((.52*signal(x,e.before)-.01*len(x),x))
        return sorted(os,reverse=True)[:8],sorted(vs,reverse=True)[:8]
    def route_responsibility(self,e,commit):
        target=e.before+' '+e.command; residuals=intervals(target,self.pred.nll(target),12); out=[]
        for cs,c in commit:
            best=0; best_r=''
            for a,b,r in residuals[:6]:
                local_overlap=.55*signal(c,e.before)+.45*signal(c,e.command)
                proto=max([.5*signal(c,pc)+.5*signal(r,pr) for pc,pr,_,_ in self.route_protos] or [0])
                reduction=max(0,local_overlap+.35*proto-.75)
                if reduction>best: best=reduction; best_r=r
            out.append((best,c,best_r))
        return sorted(out,reverse=True)
    def solve(self,e,commit):
        os,vs=self.candidates(e); action='none'; routes=[]
        if self.kind=='unconditional': inject=commit; action='carry'
        elif self.kind in ('routed','routed_null'):
            routes=self.route_responsibility(e,commit); inject=[(r,x) for r,x,_ in routes if r>.02][:4]; action='carry' if inject else 'switch'
        else: inject=[]
        for rank,(score,x) in enumerate(inject): os.append((score+.14-.025*rank,x))
        os=sorted(os,reverse=True)[:8]; vs=sorted(vs,reverse=True)[:8]
        pairs=list(dict.fromkeys((o,v) for _,o in os for _,v in vs))[:48]
        ranked=[]
        for o,v in pairs:
            sc=.48*signal(o,e.before)+.28*signal(o,e.command)+.43*signal(v,e.command)-.16*signal(v,e.before)
            if action=='carry': sc+=.16*max([signal(o,x) for _,x in inject] or [0])
            ranked.append((sc,(o,v)))
        ranked.sort(reverse=True); chosen=ranked[0][1] if ranked else None
        pair_recall=int((e.obj,e.val) in pairs)
        if self.kind=='routed_null':
            margin=ranked[0][0]-(ranked[1][0] if len(ranked)>1 else 0) if ranked else 0
            if not(pair_recall and max([r for r,_,_ in routes] or [0])>.02 and margin>.03): chosen=None
        return chosen,{'object_recall':int(any(x==e.obj for _,x in os)),'value_recall':int(any(x==e.val for _,x in vs)),'pair_recall':pair_recall,'accuracy':int(chosen==(e.obj,e.val)),'wrong':int(chosen is not None and chosen!=(e.obj,e.val)),'null':int(chosen is None),'active_pairs':len(pairs),'carry':int(action=='carry'),'gate_correct':int(action==e.truth_action),'wrong_carry':int(action=='carry' and e.truth_action=='switch'),'continuation_recall':int(action=='carry' and e.truth_action=='carry'),'local_residual_reduction':max([r for r,_,_ in routes] or [0])}
    def run(self,test):
        commit=[];acc=Counter();t=time.perf_counter()
        for e in test:
            _,z=self.solve(e,commit)
            for k,v in z.items():acc[k]+=v
            commit=self.commits(e)
        n=len(test); out={k:acc[k]/n for k in acc}; out['inference_ms']=(time.perf_counter()-t)*1000/n; return out

def evaluate(seed,n):
    modes=['seen','held','rename','alternate','nested','omitted','switch','paragraph','plan']; train=stream(seed,n,'train'); out={}
    for kind in ('no_carry','unconditional','routed','routed_null'):
        m=Model(kind); m.fit(train); out[kind]={mode:m.run(stream(seed+1000,18,mode)) for mode in modes}
        out[kind]['model_bytes']=len(pickle.dumps(m)); out[kind]['training_seconds']=m.train_s; out[kind]['commit_prototypes']=len(m.commit_protos); out[kind]['route_prototypes']=len(m.route_protos)
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',default='results_cycle_027.json'); args=ap.parse_args()
    raw={str(seed):evaluate(seed,48) for seed in (1,7,19)}
    methods=('no_carry','unconditional','routed','routed_null'); modes=['seen','held','rename','alternate','nested','omitted','switch','paragraph','plan']; summary={}
    for method in methods:
        summary[method]={}
        for mode in modes:
            ks=raw['1'][method][mode].keys(); summary[method][mode]={k:statistics.mean(raw[str(seed)][method][mode][k] for seed in (1,7,19)) for k in ks}
        for k in ('model_bytes','training_seconds','commit_prototypes','route_prototypes'): summary[method][k]=statistics.mean(raw[str(seed)][method][k] for seed in (1,7,19))
    payload={'hypothesis':'Transition-Mediated Predictive Responsibility from Local Residual Routing','seeds':[1,7,19],'train_size':48,'test_size_per_split':18,'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'character prediction O(NL), interval proposal O(L), route matching O(KRW), sparse pairing O(KoKv)','hidden_labels_used_by_learner':False,'current_turn_after_future_used_for_selection':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(args.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)

if __name__=='__main__': main()
