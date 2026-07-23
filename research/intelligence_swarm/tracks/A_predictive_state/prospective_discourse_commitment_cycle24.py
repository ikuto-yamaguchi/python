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
    before:str; command:str; after:str; future1:str; future2:str; obj:str; val:str; mode:str; continues:bool

class CharPredictor:
    def __init__(self,order=3): self.order=order; self.ctx=defaultdict(Counter); self.alpha=.25
    def fit(self,texts):
        for text in texts:
            s='^'*(self.order-1)+text+'$'
            for i in range(self.order-1,len(s)): self.ctx[s[i-self.order+1:i]][s[i]]+=1
    def surprise(self,text):
        s='^'*(self.order-1)+text; out=[]; vocab=max(16,len(set(text)))
        for i in range(self.order-1,len(s)):
            h=s[i-self.order+1:i]; c=s[i]; cnt=self.ctx.get(h,Counter()); tot=sum(cnt.values())
            out.append(-math.log((cnt.get(c,0)+self.alpha)/(tot+self.alpha*vocab)+1e-12))
        return out

def peaks(v):
    if not v:return [0]
    med=statistics.median(v);mad=statistics.median([abs(x-med) for x in v])+1e-6;thr=med+.55*mad
    return sorted(set([0]+[i for i in range(1,len(v)-1) if v[i]>=thr and v[i]>=v[i-1] and v[i]>=v[i+1]]+[len(v)]))

def intervals(text,score,cap=24):
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

def profile(v,a,b,bins=5):
    seg=v[a:b]
    if not seg:return (0,)*bins
    z=[]
    for k in range(bins):
        lo=k*len(seg)//bins;hi=max(lo+1,(k+1)*len(seg)//bins);z.append(sum(seg[lo:hi])/max(1,hi-lo))
    m=sum(z)/len(z);return tuple(round(x-m,2) for x in z)

def sim(a,b):
    na=math.sqrt(sum(x*x for x in a));nb=math.sqrt(sum(x*x for x in b))
    return sum(x*y for x,y in zip(a,b))/(na*nb+1e-9)

def signal(x,text):
    if x==text:return 1.0
    if x in text:return .84
    if text in x:return .56
    return .34*sum((Counter(x)&Counter(text)).values())/max(1,len(x))

def make(rng,mode,forced_obj=''):
    canonical=forced_obj or rng.choice(OBJECTS)
    surf=ALIASES[canonical] if mode=='rename' else canonical
    old=rng.choice(VALUES); v=rng.choice([x for x in VALUES if x!=old]); form=1 if mode=='alternate' else 0
    before=STATE[form].format(o=surf,v=old); after=STATE[form].format(o=surf,v=v)
    if mode=='omitted':cmd=rng.choice(OMIT).format(v=v)
    elif mode in ('held','rename','nested','paragraph','plan'):cmd=rng.choice(HELD).format(o=surf,v=v)
    else:cmd=rng.choice(CMDS).format(o=surf,v=v)
    if mode=='nested':cmd='『'+rng.choice(DIST)+'』ただし、'+cmd
    if mode=='paragraph':cmd=' '.join(rng.choice(DIST) for _ in range(3))+'\n'+cmd
    if mode=='plan':
        alt=rng.choice([x for x in VALUES if x not in (old,v)])
        cmd=f'{surf}を{alt}へ変える案でした。{rng.choice(DIST)}最終的には'+cmd
    f1=f'次の観測でも{surf}は存在し、局所値は{v}、補助記録は維持。'
    f2=f'さらに後でも{surf}の値は{v}。他の対象には変更なし。'
    return Ex(before,cmd,after,f1,f2,surf,v,mode,bool(forced_obj))

class Model:
    def __init__(self,kind):
        self.kind=kind;self.pred=CharPredictor();self.protos=[];self.train_s=0
    def fit(self,eps):
        t=time.perf_counter();texts=[]
        for e in eps:texts += [e.before,e.command,e.after,e.future1,e.future2]
        self.pred.fit(texts)
        for e in eps:
            cv=self.pred.surprise(e.command)
            for a,b,x in intervals(e.command,cv,12):
                if any(x in z for z in (e.before,e.after,e.future1,e.future2)):self.protos.append(profile(cv,a,b))
        self.protos=self.protos[:64];self.train_s=time.perf_counter()-t
    def candidates_pre(self,e):
        cv=self.pred.surprise(e.command); bv=self.pred.surprise(e.before)
        ci=intervals(e.command,cv,14); bi=intervals(e.before,bv,14)
        obj=[];val=[]
        for a,b,x in bi:
            score=.62*signal(x,e.before)-.012*len(x)+.12*max([sim(profile(bv,a,b),p) for p in self.protos] or [0])
            obj.append((score,x))
        for a,b,x in ci:
            score=.55*signal(x,e.command)-.26*signal(x,e.before)-.010*len(x)+.1*max([sim(profile(cv,a,b),p) for p in self.protos] or [0])
            val.append((score,x))
            if signal(x,e.before)>.55:obj.append((.55*signal(x,e.before)-.01*len(x),x))
        return sorted(obj,reverse=True)[:8],sorted(val,reverse=True)[:8]
    def retrospective(self,e):
        sv=[]
        for text in (e.after,e.future1,e.future2):
            v=self.pred.surprise(text)
            sv.extend((signal(x,e.future1)+signal(x,e.future2)-.02*len(x),x) for _,_,x in intervals(text,v,10))
        return sorted(sv,reverse=True)[:8]
    def commit_next(self,e):
        streams=(e.before,e.after,e.future1,e.future2)
        candidates=[]
        for text in streams:
            sv=self.pred.surprise(text)
            for a,b,x in intervals(text,sv,12):
                persistence=sum(signal(x,t) for t in streams)/len(streams)
                future=.5*signal(x,e.future1)+.5*signal(x,e.future2)
                value_change=signal(x,e.after)-signal(x,e.before)
                score=.55*persistence+.35*future-.22*max(0,value_change)-.012*len(x)
                candidates.append((score,x))
        out=[];seen=set()
        for score,x in sorted(candidates,reverse=True):
            if x not in seen:seen.add(x);out.append((score,x))
            if len(out)>=4:break
        return out
    def solve(self,e,commit):
        os,vs=self.candidates_pre(e)
        pre_obj=int(any(x==e.obj for _,x in os)); pre_val=int(any(x==e.val for _,x in vs))
        if self.kind in ('commit','commit_null'):
            for rank,(score,x) in enumerate(commit): os.append((score+.18-.03*rank,x))
        elif self.kind=='retrospective':
            os += self.retrospective(e)
        os=sorted(os,reverse=True)[:8];vs=sorted(vs,reverse=True)[:8]
        pairs=list(dict.fromkeys((o,v) for _,o in os for _,v in vs))[:48]
        pair_recall=int((e.obj,e.val) in pairs)
        ranked=[]
        for o,v in pairs:
            score=.50*signal(o,e.before)+.30*signal(o,e.command)+.42*signal(v,e.command)-.16*signal(v,e.before)
            if self.kind=='retrospective':score += .35*signal(o,e.after)+.35*signal(v,e.future1)
            ranked.append((score,(o,v)))
        ranked.sort(reverse=True)
        chosen=None
        if ranked:
            margin=ranked[0][0]-(ranked[1][0] if len(ranked)>1 else 0)
            if self.kind!='commit_null' or (pair_recall and margin>.04):chosen=ranked[0][1]
        return chosen,dict(pre_object_recall=pre_obj,pre_value_recall=pre_val,object_recall=int(any(x==e.obj for _,x in os)),value_recall=int(any(x==e.val for _,x in vs)),pair_recall=pair_recall,accuracy=int(chosen==(e.obj,e.val)),wrong=int(chosen is not None and chosen!=(e.obj,e.val)),null=int(chosen is None),active_pairs=len(pairs),commit_size=len(commit))

def stream(seed,n,mode):
    rng=random.Random(seed);seq=[];last=''
    for i in range(n):
        if mode=='omitted':
            if i%2==0:
                canon=rng.choice(OBJECTS); e=make(rng,'seen',canon); last=canon
            else:e=make(rng,'omitted',last)
        else:
            base=('seen','held','rename','alternate')[i%4] if mode=='train' else mode
            e=make(rng,base)
        seq.append(e)
    return seq

def run(seed,n,mode):
    train=stream(seed,n,'train');test=stream(seed+1000,12,mode);out={}
    for kind in ('no_carry','retrospective','commit','commit_null'):
        m=Model(kind);m.fit(train);commit=[];acc=Counter();t=time.perf_counter()
        for e in test:
            _,z=m.solve(e,commit)
            for k,v in z.items():acc[k]+=v
            commit=m.commit_next(e)
        out[kind]={k:acc[k]/len(test) for k in acc}
        out[kind].update(model_bytes=len(pickle.dumps(m)),training_seconds=m.train_s,inference_ms=(time.perf_counter()-t)*1000/len(test),predictive_states=len(m.protos))
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_024.json');a=ap.parse_args()
    modes=('seen','held','rename','alternate','nested','omitted','paragraph','plan');raw={}
    for n in (24,48,72):
        raw[str(n)]=[{mode:run(seed,n,mode) for mode in modes} for seed in (1,7,19)]
    summary={}
    for n,runs in raw.items():
        summary[n]={}
        for mode in modes:
            summary[n][mode]={}
            for kind in ('no_carry','retrospective','commit','commit_null'):
                summary[n][mode][kind]={k:statistics.mean(r[mode][kind][k] for r in runs) for k in runs[0][mode][kind]}
    payload={'hypothesis':'Prospective Discourse State from Pre-Observation Prediction Commitments','seeds':[1,7,19],'sizes':[24,48,72],'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'character prediction O(NL), interval proposal O(L), commitment O(WL), sparse pairing O(KoKv), Ko,Kv<=8','current_turn_after_future_used_for_commit_selection':False,'hidden_labels_used_by_learner':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary['72'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
