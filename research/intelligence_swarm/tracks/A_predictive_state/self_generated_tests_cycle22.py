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
    before:str;command:str;after:str;future1:str;future2:str;obj:str;val:str;mode:str;focus:str

def make(rng,mode,focus=''):
    o=rng.choice(OBJECTS); surf=ALIASES[o] if mode=='rename' else o
    old=rng.choice(VALUES); v=rng.choice([x for x in VALUES if x!=old]); form=1 if mode=='alternate' else 0
    before=STATE[form].format(o=surf,v=old); after=STATE[form].format(o=surf,v=v)
    if mode=='omitted': cmd=rng.choice(OMIT).format(v=v)
    elif mode in ('held','rename','nested','paragraph','plan'): cmd=rng.choice(HELD).format(o=surf,v=v)
    else: cmd=rng.choice(CMDS).format(o=surf,v=v)
    if mode=='nested':cmd='『'+rng.choice(DIST)+'』ただし、'+cmd
    if mode=='paragraph':cmd=' '.join(rng.choice(DIST) for _ in range(3))+'\n'+cmd
    if mode=='plan':
        alt=rng.choice([x for x in VALUES if x not in (old,v)])
        cmd=f'{surf}を{alt}へ変える案でした。{rng.choice(DIST)}最終的には'+cmd
    f1=f'次の観測でも{surf}は存在し、局所値は{v}、補助記録は維持。'
    f2=f'さらに後でも{surf}の値は{v}。他の対象には変更なし。'
    return Ex(before,cmd,after,f1,f2,surf,v,mode,focus)

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

def intervals(text,score,cap=18):
    ps=peaks(score);z=[]
    for i,a in enumerate(ps[:-1]):
        for j in range(i+1,min(len(ps),i+4)):
            b=ps[j]
            if 1<=b-a<=14:
                x=text[a:b].strip(''.join(SEP))
                if x:z.append((a,b,x))
    seen=set();out=[]
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
    if x in text:return .82
    if text in x:return .58
    return .35*sum((Counter(x)&Counter(text)).values())/max(1,len(x))

STREAMS=('after','future1','future2','before')

class Model:
    def __init__(self,kind,max_tests=4):
        self.kind=kind;self.pred=CharPredictor();self.proto=[];self.max_tests=max_tests;self.train_s=0
    def fit(self,eps):
        t=time.perf_counter();texts=[]
        for e in eps:texts += [e.before,e.command,e.after,e.future1,e.future2]
        self.pred.fit(texts)
        for e in eps:
            sv=self.pred.surprise(e.command)
            for a,b,x in intervals(e.command,sv):
                if any(x in z for z in (e.before,e.after,e.future1,e.future2)):self.proto.append(profile(sv,a,b))
        self.proto=self.proto[:64];self.train_s=time.perf_counter()-t
    def propose(self,e):
        cv=self.pred.surprise(e.command); ci=intervals(e.command,cv)
        streams=[(e.before,self.pred.surprise(e.before)),(e.after,self.pred.surprise(e.after)),(e.future1,self.pred.surprise(e.future1)),(e.future2,self.pred.surprise(e.future2))]
        ps=[];cs=[]
        for a,b,x in ci:
            pc=profile(cv,a,b);sync=[]
            for text,sv in streams:
                for aa,bb,y in intervals(text,sv,12):sync.append(.58*signal(x,y)+.42*sim(pc,profile(sv,aa,bb)))
            learned=max([sim(pc,p) for p in self.proto] or [0])
            ps.append((max(sync,default=0)+.12*learned-.012*len(x),x))
            cs.append((.46*signal(x,e.after)+.42*max(signal(x,e.future1),signal(x,e.future2))-.28*signal(x,e.before)+.10*learned-.010*len(x),x))
        return sorted(ps,reverse=True)[:6],sorted(cs,reverse=True)[:6]
    def test_candidates(self,e,active):
        tests=[]
        for name in STREAMS:
            text=getattr(e,name);sv=self.pred.surprise(text)
            for a,b,x in intervals(text,sv,10):
                buckets=defaultdict(int)
                for p,c in active:
                    sig=(round(signal(p,x),1),round(signal(c,x),1),round(signal(p,text),1),round(signal(c,text),1))
                    buckets[sig]+=1
                n=len(active);gain=n*n-sum(v*v for v in buckets.values());tests.append((gain/(1+.08*len(x)),name,a,b,x))
        return sorted(tests,reverse=True)[:12]
    def candidate_outcome(self,pair,test,e):
        _,name,a,b,x=test;text=getattr(e,name);p,c=pair
        return (round(signal(p,x),1),round(signal(c,x),1),round(signal(p,text),1),round(signal(c,text),1))
    def observed_signature(self,e,test):
        _,name,a,b,x=test;text=getattr(e,name)
        return (round(signal(e.obj,x),1),round(signal(e.val,x),1),round(signal(e.obj,text),1),round(signal(e.val,text),1))
    def feedback_birth(self,e,test,active):
        x=test[4];cv=self.pred.surprise(e.command);new=[]
        for a,b,z in intervals(e.command,cv,24):
            if signal(z,x)>=.30:
                for p,c in active[:8]:new.extend([(z,c),(p,z)])
        return new[:16]
    def solve(self,e):
        ps,cs=self.propose(e);pairs=[(p,c) for _,p in ps[:4] for _,c in cs[:4]]
        objrec=int(any(x==e.obj for _,x in ps));valrec=int(any(x==e.val for _,x in cs));pairrec=int((e.obj,e.val) in pairs)
        active=list(dict.fromkeys(pairs));used=births=updates=0
        if self.kind!='passive':
            for _ in range(self.max_tests):
                if len(active)<=1:break
                tests=self.test_candidates(e,active)
                if not tests or tests[0][0]<=0:break
                test=tests[0];obs=self.observed_signature(e,test)
                nxt=[z for z in active if self.candidate_outcome(z,test,e)==obs];used+=1
                if self.kind.startswith('generated_feedback') and (not nxt or len(nxt)==len(active)):
                    born=self.feedback_birth(e,test,active);old=len(active);active=list(dict.fromkeys(active+born))[:24];births+=max(0,len(active)-old)
                    nxt=[z for z in active if self.candidate_outcome(z,test,e)==obs]
                if nxt and len(nxt)<len(active):active=nxt;updates+=1
                else:break
        pairrec2=int((e.obj,e.val) in active);chosen=active[0] if len(active)==1 else None
        if self.kind.endswith('null') and (chosen is None or not pairrec2):chosen=None
        return chosen,dict(object_recall=objrec,value_recall=valrec,pair_recall=pairrec,post_pair_recall=pairrec2,wrong=int(chosen is not None and chosen!=(e.obj,e.val)),null=int(chosen is None),tests=used,births=births,state_updates=updates,initial=len(pairs),final=len(active))

def run(seed,n,mode):
    rng=random.Random(seed);focus='';train=[]
    for i in range(n):
        m=('seen','held','rename','alternate')[i%4];e=make(rng,m,focus);train.append(e);focus=e.obj
    test=[];focus=''
    for _ in range(8):e=make(rng,mode,focus);test.append(e);focus=e.obj
    out={}
    for kind in ('passive','generated','generated_feedback','generated_feedback_null'):
        m=Model(kind);m.fit(train);t=time.perf_counter();acc=Counter()
        for e in test:
            ch,z=m.solve(e);acc['accuracy']+=int(ch==(e.obj,e.val))
            for k,v in z.items():acc[k]+=v
        out[kind]={k:acc[k]/len(test) for k in ['accuracy','object_recall','value_recall','pair_recall','post_pair_recall','wrong','null','tests','births','state_updates','initial','final']}
        out[kind].update(model_bytes=len(pickle.dumps(m)),training_seconds=m.train_s,inference_ms=(time.perf_counter()-t)*1000/len(test),predictive_states=len(m.proto))
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_022.json');a=ap.parse_args()
    modes=('seen','held','rename','alternate','nested','omitted','paragraph','plan');raw={}
    for n in (24,72):
        runs=[]
        for seed in (1,7,19):runs.append({mode:run(seed,n,mode) for mode in modes})
        raw[str(n)]=runs
    summary={}
    for n,runs in raw.items():
        summary[n]={}
        for mode in modes:
            summary[n][mode]={}
            for kind in ('passive','generated','generated_feedback','generated_feedback_null'):
                summary[n][mode][kind]={k:statistics.mean(r[mode][kind][k] for r in runs) for k in runs[0][mode][kind]}
    payload={'hypothesis':'Self-Generated Predictive Tests from Candidate Disagreement Residuals','seeds':[1,7,19],'sizes':[24,72],'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'char prediction O(NL), disagreement tests O(WH), feedback birth O(LH), recursive update O(QH), W<=40 H<=24 Q<=4','hidden_labels_used_by_learner':False,'environment_observation_uses_hidden_state_only_for_simulation':True,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary['72'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
