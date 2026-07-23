from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass
import json, math, pickle, random, resource, statistics, time, argparse

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
    before:str;command:str;after:str;future:str;obj:str;val:str;mode:str;focus:str

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
    future=f'次の観測でも{surf}は存在し、局所値は{v}、補助記録は維持。'
    return Ex(before,cmd,after,future,surf,v,mode,focus)

def changed(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

class CharPredictor:
    def __init__(self,order=3):self.order=order;self.ctx=defaultdict(Counter);self.alpha=.25
    def fit(self,texts):
        for text in texts:
            s='^'*(self.order-1)+text+'$'
            for i in range(self.order-1,len(s)):
                self.ctx[s[i-self.order+1:i]][s[i]]+=1
    def surprise(self,text):
        s='^'*(self.order-1)+text
        vals=[]
        vocab=max(16,len({c for c in ''.join(text)}))
        for i in range(self.order-1,len(s)):
            c=s[i]; h=s[i-self.order+1:i]; cnt=self.ctx.get(h,Counter()); total=sum(cnt.values())
            p=(cnt.get(c,0)+self.alpha)/(total+self.alpha*vocab)
            vals.append(-math.log(p+1e-12))
        return vals

def peaks(v):
    if not v:return []
    med=statistics.median(v); mad=statistics.median([abs(x-med) for x in v])+1e-6;thr=med+.55*mad
    out=[0]
    for i in range(1,len(v)-1):
        if v[i]>=thr and v[i]>=v[i-1] and v[i]>=v[i+1]:out.append(i)
    out.append(len(v))
    return sorted(set(out))

def intervals(text,score,cap=18):
    ps=peaks(score); z=[]
    for a,b in zip(ps,ps[1:]):
        if 1<=b-a<=14:
            x=text[a:b].strip(''.join(SEP))
            if len(x)>=1:z.append((a,b,x))
    for i in range(len(ps)-1):
        for j in range(i+2,min(len(ps),i+4)):
            a,b=ps[i],ps[j]
            if 1<=b-a<=12:
                x=text[a:b].strip(''.join(SEP))
                if len(x)>=1:z.append((a,b,x))
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
        lo=k*len(seg)//bins;hi=max(lo+1,(k+1)*len(seg)//bins)
        out.append(round(sum(seg[lo:hi])/max(1,hi-lo),2))
    base=sum(out)/len(out)
    return tuple(round(x-base,2) for x in out)

def simprof(a,b):
    na=math.sqrt(sum(x*x for x in a));nb=math.sqrt(sum(x*x for x in b))
    return sum(x*y for x,y in zip(a,b))/(na*nb+1e-9)

class Model:
    def __init__(self,kind):self.kind=kind;self.pred=CharPredictor();self.proto=[];self.train_s=0
    def fit(self,eps):
        t=time.perf_counter();texts=[]
        for e in eps:texts.extend([e.before,e.command,e.after,e.future])
        self.pred.fit(texts)
        if self.kind=='sync_learned':
            feats=[]
            for e in eps:
                cv=self.pred.surprise(e.command)
                for a,b,x in intervals(e.command,cv):
                    if x in e.before or x in e.after or x in e.future:feats.append(profile(cv,a,b))
            self.proto=feats[:64]
        self.train_s=time.perf_counter()-t
    def propose(self,e):
        cv=self.pred.surprise(e.command);bv=self.pred.surprise(e.before);av=self.pred.surprise(e.after);fv=self.pred.surprise(e.future)
        ci=intervals(e.command,cv); bi=intervals(e.before,bv); ai=intervals(e.after,av); fi=intervals(e.future,fv)
        persist=[];change=[]
        for a,b,x in ci:
            pc=profile(cv,a,b); state_matches=[]
            for aa,bb,y in bi+fi:
                lexical=1.0 if x==y else (0.5 if x in y or y in x else 0)
                state_matches.append(.65*lexical+.35*simprof(pc,profile(bv if (aa,bb,y) in bi else fv,aa,bb)))
            best=max(state_matches,default=0);learned=max([simprof(pc,p) for p in self.proto] or [0])
            persist.append((best+.15*learned-.015*len(x),x))
            after_match=max([.7*(x==y)+.3*simprof(pc,profile(av,aa,bb)) for aa,bb,y in ai],default=0)
            before_match=max([1.0 if x==y else 0.4 if x in y or y in x else 0 for _,_,y in bi],default=0)
            change.append((after_match-.45*before_match+.15*learned-.012*len(x),x))
        return sorted(persist,reverse=True)[:6],sorted(change,reverse=True)[:6]
    def solve(self,e):
        ps,cs=self.propose(e);pr=int(any(x==e.obj for _,x in ps));cr=int(any(x==e.val for _,x in cs));pairs=[(p,c) for _,p in ps[:4] for _,c in cs[:4]];pair=int((e.obj,e.val) in pairs)
        if self.kind.endswith('null') and not pair:return None,(pr,cr,pair,len(ps),len(cs),len(pairs),0)
        if not pairs:return None,(pr,cr,pair,len(ps),len(cs),0,0)
        chosen=pairs[0]
        return chosen,(pr,cr,pair,len(ps),len(cs),len(pairs),int(chosen!=(e.obj,e.val)))

def run(seed,n,mode):
    rng=random.Random(seed);focus='';train=[]
    for i in range(n):
        m=('seen','held','rename','alternate')[i%4];e=make(rng,m,focus);train.append(e);focus=e.obj
    test=[];focus=''
    for _ in range(16):e=make(rng,mode,focus);test.append(e);focus=e.obj
    out={}
    for kind in ('sync','sync_null','sync_learned','sync_learned_null'):
        m=Model(kind);m.fit(train);t=time.perf_counter();acc=pr=cr=pair=wrong=null=np=nc=npa=0
        for e in test:
            ch,z=m.solve(e);a,b,c,d,f,g,w=z;pr+=a;cr+=b;pair+=c;np+=d;nc+=f;npa+=g;wrong+=w;null+=int(ch is None);acc+=int(ch==(e.obj,e.val))
        out[kind]={'accuracy':acc/16,'object_recall':pr/16,'value_recall':cr/16,'pair_recall':pair/16,'wrong_commit':wrong/16,'null_rate':null/16,'persistence_candidates':np/16,'change_candidates':nc/16,'pair_candidates':npa/16,'model_bytes':len(pickle.dumps(m)),'training_seconds':m.train_s,'inference_ms':(time.perf_counter()-t)*1000/16,'predictive_states':len(m.proto)}
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_020.json');a=ap.parse_args();raw={}
    for n in (24,72,144):
        runs=[]
        for seed in (1,7,19):runs.append({mode:run(seed,n,mode) for mode in ('seen','held','rename','alternate','nested','omitted','paragraph','plan')})
        raw[str(n)]=runs
    summary={}
    for n,runs in raw.items():
        summary[n]={}
        for mode in runs[0]:
            summary[n][mode]={}
            for kind in ('sync','sync_null','sync_learned','sync_learned_null'):
                summary[n][mode][kind]={k:statistics.mean(r[mode][kind][k] for r in runs) for k in runs[0][mode][kind]}
    payload={'hypothesis':'Cross-Stream Surprise Phase Locking for Minimal Predictive Roles','seeds':[1,7,19],'sizes':[24,72,144],'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'char model O(NL), phase cells O(L), alignment O(Hc(Hb+Ha+Hf)), pair O(KpKc)','hidden_labels_used_by_learner':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary['144'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
