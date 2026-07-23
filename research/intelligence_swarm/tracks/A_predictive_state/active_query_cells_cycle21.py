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
        alt=rng.choice([x for x in VALUES if x not in (old,v)]);cmd=f'{surf}を{alt}へ変える案でした。{rng.choice(DIST)}最終的には'+cmd
    future1=f'次の観測でも{surf}は存在し、局所値は{v}、補助記録は維持。'
    future2=f'さらに後でも{surf}の値は{v}。他の対象には変更なし。'
    return Ex(before,cmd,after,future1,future2,surf,v,mode,focus)

class CharPredictor:
    def __init__(self,order=3):self.order=order;self.ctx=defaultdict(Counter);self.alpha=.25
    def fit(self,texts):
        for text in texts:
            s='^'*(self.order-1)+text+'$'
            for i in range(self.order-1,len(s)):self.ctx[s[i-self.order+1:i]][s[i]]+=1
    def surprise(self,text):
        s='^'*(self.order-1)+text;vals=[];vocab=max(16,len(set(text)))
        for i in range(self.order-1,len(s)):
            h=s[i-self.order+1:i];c=s[i];cnt=self.ctx.get(h,Counter());tot=sum(cnt.values());p=(cnt.get(c,0)+self.alpha)/(tot+self.alpha*vocab);vals.append(-math.log(p+1e-12))
        return vals

def peaks(v):
    if not v:return []
    med=statistics.median(v);mad=statistics.median([abs(x-med) for x in v])+1e-6;thr=med+.55*mad;out=[0]
    for i in range(1,len(v)-1):
        if v[i]>=thr and v[i]>=v[i-1] and v[i]>=v[i+1]:out.append(i)
    out.append(len(v));return sorted(set(out))

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
    out=[]
    for k in range(bins):
        lo=k*len(seg)//bins;hi=max(lo+1,(k+1)*len(seg)//bins);out.append(sum(seg[lo:hi])/max(1,hi-lo))
    base=sum(out)/len(out);return tuple(round(x-base,2) for x in out)

def simprof(a,b):
    na=math.sqrt(sum(x*x for x in a));nb=math.sqrt(sum(x*x for x in b));return sum(x*y for x,y in zip(a,b))/(na*nb+1e-9)

def token_signal(x,text):
    if x==text:return 1.0
    if x in text:return .82
    if text in x:return .58
    common=sum((Counter(x)&Counter(text)).values())/max(1,len(x))
    return .35*common

PROBES=('future1_presence','future2_presence','after_change','before_persistence','non_target_preservation')

class Model:
    def __init__(self,kind,max_probe=4):
        self.kind=kind;self.pred=CharPredictor();self.proto=[];self.max_probe=max_probe;self.train_s=0
    def fit(self,eps):
        t=time.perf_counter();texts=[]
        for e in eps:texts += [e.before,e.command,e.after,e.future1,e.future2]
        self.pred.fit(texts)
        feats=[]
        for e in eps:
            cv=self.pred.surprise(e.command)
            for a,b,x in intervals(e.command,cv):
                if any(x in z for z in (e.before,e.after,e.future1,e.future2)):feats.append(profile(cv,a,b))
        self.proto=feats[:64];self.train_s=time.perf_counter()-t
    def propose(self,e):
        cv=self.pred.surprise(e.command);ci=intervals(e.command,cv)
        streams=[(e.before,self.pred.surprise(e.before)),(e.after,self.pred.surprise(e.after)),(e.future1,self.pred.surprise(e.future1)),(e.future2,self.pred.surprise(e.future2))]
        persist=[];change=[]
        for a,b,x in ci:
            pc=profile(cv,a,b);sync=[]
            for text,sv in streams:
                for aa,bb,y in intervals(text,sv,12):
                    sync.append(.58*token_signal(x,y)+.42*simprof(pc,profile(sv,aa,bb)))
            learned=max([simprof(pc,p) for p in self.proto] or [0])
            pscore=max(sync,default=0)+.12*learned-.012*len(x)
            after=token_signal(x,e.after);before=token_signal(x,e.before);fut=max(token_signal(x,e.future1),token_signal(x,e.future2))
            cscore=.46*after+.42*fut-.28*before+.10*learned-.010*len(x)
            persist.append((pscore,x));change.append((cscore,x))
        return sorted(persist,reverse=True)[:6],sorted(change,reverse=True)[:6]
    def outcome(self,e,pair,probe):
        p,c=pair
        if probe=='future1_presence': return (round(token_signal(p,e.future1),1),round(token_signal(c,e.future1),1))
        if probe=='future2_presence': return (round(token_signal(p,e.future2),1),round(token_signal(c,e.future2),1))
        if probe=='after_change': return (round(token_signal(p,e.after),1),round(token_signal(c,e.after),1))
        if probe=='before_persistence': return (round(token_signal(p,e.before),1),round(token_signal(c,e.before),1))
        return (int('補助記録' in e.after and '維持' in e.after),int(p in e.after or p in e.before))
    def oracle_outcome(self,e,probe):
        return self.outcome(e,(e.obj,e.val),probe)
    def solve(self,e):
        ps,cs=self.propose(e);pairs=[(p,c) for _,p in ps[:4] for _,c in cs[:4]]
        pr=int(any(x==e.obj for _,x in ps));cr=int(any(x==e.val for _,x in cs));pairrec=int((e.obj,e.val) in pairs)
        active=pairs[:];used=0;state_updates=0
        if self.kind!='passive':
            for _ in range(self.max_probe):
                if len(active)<=1:break
                best=None
                for q in PROBES:
                    buckets=defaultdict(int)
                    for z in active:buckets[self.outcome(e,z,q)]+=1
                    n=len(active);gain=n*n-sum(v*v for v in buckets.values())
                    if q=='non_target_preservation':gain*=.7
                    if best is None or gain>best[0]:best=(gain,q)
                if not best or best[0]<=0:break
                q=best[1];obs=self.oracle_outcome(e,q);nxt=[z for z in active if self.outcome(e,z,q)==obs]
                used+=1
                if nxt and len(nxt)<len(active):active=nxt;state_updates+=1
                else:break
        chosen=active[0] if len(active)==1 else None
        if self.kind.endswith('null') and (not pairrec or chosen is None):chosen=None
        wrong=int(chosen is not None and chosen!=(e.obj,e.val))
        return chosen,dict(object_recall=pr,value_recall=cr,pair_recall=pairrec,wrong=wrong,null=int(chosen is None),probes=used,state_updates=state_updates,initial=len(pairs),final=len(active))

def run(seed,n,mode):
    rng=random.Random(seed);focus='';train=[]
    for i in range(n):
        m=('seen','held','rename','alternate')[i%4];e=make(rng,m,focus);train.append(e);focus=e.obj
    test=[];focus=''
    for _ in range(24):e=make(rng,mode,focus);test.append(e);focus=e.obj
    out={}
    for kind in ('passive','active','active_null'):
        m=Model(kind);m.fit(train);t=time.perf_counter();acc=Counter();
        for e in test:
            ch,z=m.solve(e);acc['accuracy']+=int(ch==(e.obj,e.val))
            for k,v in z.items():acc[k]+=v
        out[kind]={k:acc[k]/len(test) for k in ['accuracy','object_recall','value_recall','pair_recall','wrong','null','probes','state_updates','initial','final']}
        out[kind].update(model_bytes=len(pickle.dumps(m)),training_seconds=m.train_s,inference_ms=(time.perf_counter()-t)*1000/len(test),predictive_states=len(m.proto))
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_021.json');a=ap.parse_args();raw={}
    modes=('seen','held','rename','alternate','nested','omitted','paragraph','plan')
    for n in (24,72,144):
        runs=[]
        for seed in (1,7,19):runs.append({mode:run(seed,n,mode) for mode in modes})
        raw[str(n)]=runs
    summary={}
    for n,runs in raw.items():
        summary[n]={}
        for mode in modes:
            summary[n][mode]={}
            for kind in ('passive','active','active_null'):
                summary[n][mode][kind]={k:statistics.mean(r[mode][kind][k] for r in runs) for k in runs[0][mode][kind]}
    payload={'hypothesis':'Active Query Disambiguation over Surprise-Synchronized Predictive Cells','seeds':[1,7,19],'sizes':[24,72,144],'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'char prediction O(NL), cell alignment O(Hc(Hb+Ha+Hf)), active query O(QH), Q<=5 H<=16','hidden_labels_used_by_learner':False,'oracle_used_only_as_environment_observation':True,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary['144'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
