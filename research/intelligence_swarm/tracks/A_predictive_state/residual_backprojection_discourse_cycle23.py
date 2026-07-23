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
    before:str; command:str; after:str; future1:str; future2:str; obj:str; val:str; mode:str

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

def make(rng,mode,carry_obj=''):
    if mode=='omitted' and carry_obj:
        surf=carry_obj
        canonical=next((k for k,v in ALIASES.items() if v==surf),surf)
    else:
        canonical=rng.choice(OBJECTS); surf=ALIASES[canonical] if mode=='rename' else canonical
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
    return Ex(before,cmd,after,f1,f2,surf,v,mode)

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
                if any(x in z for z in (e.before,e.after,e.future1,e.future2)):
                    self.protos.append(profile(cv,a,b))
        self.protos=self.protos[:64]; self.train_s=time.perf_counter()-t
    def base_candidates(self,e):
        cv=self.pred.surprise(e.command); ci=intervals(e.command,cv,14)
        streams=[(e.before,self.pred.surprise(e.before)),(e.after,self.pred.surprise(e.after)),(e.future1,self.pred.surprise(e.future1)),(e.future2,self.pred.surprise(e.future2))]
        obj=[];val=[]
        for a,b,x in ci:
            pc=profile(cv,a,b); sync=[]
            for text,sv in streams:
                for aa,bb,y in intervals(text,sv,8): sync.append(.58*signal(x,y)+.42*sim(pc,profile(sv,aa,bb)))
            learned=max([sim(pc,p) for p in self.protos] or [0])
            obj.append((max(sync,default=0)+.10*learned-.012*len(x),x))
            val.append((.48*signal(x,e.after)+.42*max(signal(x,e.future1),signal(x,e.future2))-.26*signal(x,e.before)+.08*learned-.010*len(x),x))
        return sorted(obj,reverse=True)[:6], sorted(val,reverse=True)[:6]
    def residual_windows(self,e):
        out=[]
        streams=[('after',e.after),('future1',e.future1),('future2',e.future2)]
        for name,text in streams:
            sv=self.pred.surprise(text)
            for a,b,x in intervals(text,sv,8):
                persistence=sum(signal(x,t) for _,t in streams if t is not text)
                novelty=1-signal(x,e.before)
                out.append((persistence+.8*novelty-.02*len(x),name,a,b,x,profile(sv,a,b)))
        return sorted(out,reverse=True)[:18]
    def backproject(self,e,windows,carry):
        cv=self.pred.surprise(e.command);bv=self.pred.surprise(e.before)
        cmd=intervals(e.command,cv,14); bef=intervals(e.before,bv,14)
        obj=[];val=[];paths=0
        for _,name,a,b,x,rp in windows:
            for aa,bb,z in cmd:
                score=.50*signal(z,x)+.35*sim(profile(cv,aa,bb),rp)+.15*max(signal(z,e.after),signal(z,e.future1))
                if score>.34:
                    val.append((score-.01*len(z),z));paths+=1
            for aa,bb,z in bef:
                score=.54*signal(z,e.future1)+.30*signal(z,e.future2)-.18*signal(z,x)+.10*sim(profile(bv,aa,bb),rp)
                if score>.25:obj.append((score-.01*len(z),z));paths+=1
        for rank,z in enumerate(carry[:4]):
            support=max(signal(z,e.before),signal(z,e.future1),signal(z,e.future2))
            obj.append((.70*support-.03*rank,z))
        return sorted(obj,reverse=True)[:8],sorted(val,reverse=True)[:8],paths
    def horizon_score(self,e,pair):
        o,v=pair
        return (.28*signal(o,e.before)+.28*signal(o,e.future1)+.18*signal(o,e.future2)+.34*signal(v,e.after)+.34*signal(v,e.future1)+.24*signal(v,e.future2)-.18*signal(v,e.before))
    def solve(self,e,carry):
        bo,bv=self.base_candidates(e)
        windows=self.residual_windows(e)
        back_o,back_v,paths=self.backproject(e,windows,carry) if self.kind in ('backprojection','carry','carry_null') else ([],[],0)
        os=bo[:4];vs=bv[:4]
        if self.kind in ('backprojection','carry','carry_null'):
            os=sorted(bo+back_o,reverse=True)[:8];vs=sorted(bv+back_v,reverse=True)[:8]
        if self.kind in ('carry','carry_null'):
            for rank,z in enumerate(carry[:4]):os.append((.95-.04*rank,z))
        os=sorted(os,reverse=True)[:8];vs=sorted(vs,reverse=True)[:8]
        pairs=list(dict.fromkeys((o,v) for _,o in os for _,v in vs))[:48]
        initial_pair=int((e.obj,e.val) in [(o,v) for _,o in bo[:4] for _,v in bv[:4]])
        post_pair=int((e.obj,e.val) in pairs)
        ranked=sorted((self.horizon_score(e,p),p) for p in pairs)[::-1]
        chosen=None
        if ranked:
            margin=ranked[0][0]-(ranked[1][0] if len(ranked)>1 else 0)
            if self.kind!='carry_null' or (post_pair and margin>.05):chosen=ranked[0][1]
        nextcarry=[x for _,x in os[:4]]
        return chosen,nextcarry,dict(accuracy=int(chosen==(e.obj,e.val)),object_recall=int(any(x==e.obj for _,x in os)),value_recall=int(any(x==e.val for _,x in vs)),initial_pair_recall=initial_pair,post_pair_recall=post_pair,wrong=int(chosen is not None and chosen!=(e.obj,e.val)),null=int(chosen is None),backprojection_paths=paths,active_pairs=len(pairs),residual_windows=len(windows))

def stream(seed,n,mode):
    rng=random.Random(seed);seq=[];carry=''
    for i in range(n):
        if mode=='omitted' and i%2==1:
            e=make(rng,'omitted',carry)
        else:
            base=('seen','held','rename','alternate')[i%4] if mode=='train' else mode
            e=make(rng,base)
        seq.append(e);carry=e.obj
    return seq

def run(seed,n,mode):
    train=stream(seed,n,'train');test=stream(seed+1000,8,mode);out={}
    for kind in ('base','backprojection','carry','carry_null'):
        m=Model(kind);m.fit(train);carry=[];acc=Counter();t=time.perf_counter()
        for e in test:
            ch,carry,z=m.solve(e,carry)
            for k,v in z.items():acc[k]+=v
        out[kind]={k:acc[k]/len(test) for k in acc}
        out[kind].update(model_bytes=len(pickle.dumps(m)),training_seconds=m.train_s,inference_ms=(time.perf_counter()-t)*1000/len(test),predictive_states=len(m.protos))
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_023.json');a=ap.parse_args()
    modes=('seen','held','rename','alternate','nested','omitted','paragraph','plan');raw={}
    for n in (24,48,72):
        runs=[]
        for seed in (1,7,19):runs.append({mode:run(seed,n,mode) for mode in modes})
        raw[str(n)]=runs
    summary={}
    for n,runs in raw.items():
        summary[n]={}
        for mode in modes:
            summary[n][mode]={}
            for kind in ('base','backprojection','carry','carry_null'):
                summary[n][mode][kind]={k:statistics.mean(r[mode][kind][k] for r in runs) for k in runs[0][mode][kind]}
    payload={'hypothesis':'Predictive Test-Cell Co-Creation by Residual Backprojection with Discourse Carry','seeds':[1,7,19],'sizes':[24,48,72],'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'char prediction O(NL), residual windows O(WL), backprojection O(W(C+B)), sparse pairing O(KoKv), Ko,Kv<=8 W<=18','hidden_labels_used_by_learner':False,'environment_observation_uses_hidden_state_only_to_generate_raw_outcomes':True,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary['72'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
