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
CMDS={'場所':['{o}を{v}へ移してください。','{o}の保管先を{v}へ変更します。'],'状態':['{o}を{v}にしてください。','{o}の進行状態を{v}へ切り替えます。'],'担当':['{o}を{v}の担当にしてください。','{o}の受け持ちを{v}へ変更します。']}
ORDER={'場所':['{v}へ移してください、対象は{o}です。'],'状態':['{v}扱いにしてください、対象は{o}です。'],'担当':['{v}へ引き継いでください、対象は{o}です。']}
LEX={'場所':['対象{o}は次から{v}で保管。'],'状態':['対象{o}は以後{v}として運用。'],'担当':['対象{o}の受持を{v}へ。']}
OMIT={'場所':['それを{v}へ移してください。'],'状態':['その対象を{v}にしてください。'],'担当':['担当は{v}へ変えてください。']}

@dataclass
class Ex:
    before:str; command:str; after:str; future:str; obj:str; field:str; old:str; new:str; mode:str
@dataclass
class Endpoint:
    sl:str; sr:str; old_shape:str; new_shape:str; support:int=0
@dataclass
class Program:
    obj_shape:str; val_shape:str; endpoint:int; support:int=0; wrong:int=0
@dataclass(frozen=True)
class Repair:
    tl:int; tr:int; vl:int; vr:int
@dataclass(frozen=True)
class Predicate:
    feature:int; threshold:int; polarity:int

def state(o,d,form): return (STATE1 if form else STATE0).format(o=o,loc=d['場所'],status=d['状態'],owner=d['担当'])
def shape(s): return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、／=：:\n 「」' else c for c in s)
def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def spans(text,max_len=12): return {(i,j,text[i:j]) for i in range(len(text)) for j in range(i+1,min(len(text),i+max_len)+1)}
def build(seed,n,mode):
    rng=random.Random(seed);world={};out=[];focus=None
    for i in range(n):
        canon=focus if mode=='omitted' and focus is not None else rng.choice(OBJECTS);surf=ALIASES[canon] if mode=='rename' else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS});f=rng.choice(FIELDS);old=world[canon][f];new=rng.choice([x for x in VALUES[f] if x!=old])
        form=1 if mode=='alternate' else 0;before=state(surf,world[canon],form);forms=ORDER[f] if mode=='order' else LEX[f] if mode=='lexeme' else OMIT[f] if mode=='omitted' else CMDS[f]
        command=random.Random(seed*1000+i).choice(forms).format(o=surf,v=new)
        if mode=='nested':command='依頼内容は「'+command+'」です。'
        if mode=='paragraph':command='前段の説明があります。別件は変更しません。\n'+command+'\n補助記録は維持してください。'
        world[canon][f]=new;after=state(surf,world[canon],form);future=f'次の観測でも{surf}の更新結果は{new}で、補助記録は維持されます。'
        out.append(Ex(before,command,after,future,surf,f,old,new,mode));focus=canon
    return out
def edit_distance(a,b):
    m=min(len(a),len(b));return abs(len(a)-len(b))+sum(x!=y for x,y in zip(a[:m],b[:m]))
def apply_span(before,value,a,b): return before[:a]+value+before[b:] if 0<=a<b<=len(before) else None

class Model:
    def __init__(self,mode,topk=4):
        self.mode=mode;self.topk=topk;self.endpoints=[];self.programs=[];self.repairs=Counter();self.rules=defaultdict(list);self.stats=Counter();self.bits=0;self.train_s=0
    def apply_endpoint(self,before,value,p):
        hits=[];q=0
        while True:
            i=before.find(p.sl,q) if p.sl else q
            if i<0:break
            a=i+len(p.sl);b=before.find(p.sr,a) if p.sr else len(before)
            if b>=a and shape(before[a:b])==p.old_shape:hits.append((a,b))
            q=i+1
            if not p.sl or q>=len(before):break
        if len(hits)!=1:return None
        a,b=hits[0];return before[:a]+value+before[b:]
    def candidate_parts(self,e):
        es={x for _,_,x in spans(e.command)};bs={x for _,_,x in spans(e.before)}
        return [s for s in es&bs if 2<=len(s)<=12],[s for s in es if s not in e.before and 1<=len(s)<=10]
    def generate_base(self,e):
        common,novel=self.candidate_parts(e);out=[]
        for ti,t in enumerate(self.programs):
            p=self.endpoints[t.endpoint]
            for o in [x for x in common if shape(x)==t.obj_shape][:4]:
                for v in [x for x in novel if shape(x)==t.val_shape][:8]:
                    pred=self.apply_endpoint(e.before,v,p)
                    if pred is not None:
                        l,r,_,_=diff(e.before,pred);out.append((t.support-t.wrong,pred,ti,o,v,l,len(e.before)-r))
        best={}
        for z in out:
            if z[1] not in best or z[0]>best[z[1]][0]:best[z[1]]=z
        return list(best.values())[:48]
    def consequence_features(self,e,z,rep):
        _,pred,_,o,v,ta,tb=z;va=e.command.find(v);vb=va+len(v);na=max(0,min(len(e.before)-1,ta+rep.tl));nb=max(na+1,min(len(e.before),tb+rep.tr));nva=max(0,min(len(e.command)-1,va+rep.vl));nvb=max(nva+1,min(len(e.command),vb+rep.vr));rv=e.command[nva:nvb];rp=apply_span(e.before,rv,na,nb)
        if rp is None:return None
        inv=apply_span(rp,e.before[na:nb],na,na+len(rv));non_target=int(e.before[:na]==rp[:na] and e.before[nb:]==rp[na+len(rv):])
        return rp,(int(rv in e.command),int(o in e.before),int(o in e.command),int(inv==e.before),non_target,min(7,abs(len(rv)-(nb-na))),min(7,edit_distance(pred,rp)//2),min(7,len(rv)//2))
    def generate_repairs(self,e,reps):
        out=list(self.generate_base(e))
        for z in list(out):
            for rep in reps:
                cf=self.consequence_features(e,z,rep)
                if cf:out.append((z[0]+.2,cf[0],z[2],z[3],z[4],0,1))
        best={}
        for z in out:
            if z[1] not in best or z[0]>best[z[1]][0]:best[z[1]]=z
        return list(best.values())[:48]
    def fit_predicates(self,examples):
        candidates=[]
        for f in range(8):
            for th in range(8):
                for pol in (-1,1):
                    p=Predicate(f,th,pol);hit=lambda x,p=p:(x[p.feature]<=p.threshold) if p.polarity<0 else (x[p.feature]>=p.threshold)
                    tp=sum(y==1 and hit(x) for x,y in examples);fp=sum(y!=1 and hit(x) for x,y in examples);fn=sum(y==1 and not hit(x) for x,y in examples);gain=3*tp-4*fp-fn-6
                    if gain>0:candidates.append((gain,(p,)))
        for i,(_,r1) in enumerate(candidates[:24]):
            for _,r2 in candidates[i+1:24]:
                rr=r1+r2;hit=lambda x:all((x[p.feature]<=p.threshold) if p.polarity<0 else (x[p.feature]>=p.threshold) for p in rr)
                tp=sum(y==1 and hit(x) for x,y in examples);fp=sum(y!=1 and hit(x) for x,y in examples);fn=sum(y==1 and not hit(x) for x,y in examples);gain=3*tp-4*fp-fn-10
                if gain>0:candidates.append((gain,rr))
        return max(candidates,key=lambda z:z[0])[1] if candidates else ()
    def fit(self,ind,pool,shuffle=False):
        t=time.perf_counter();epc=Counter();records=[]
        for e in ind:
            l,r,old,new=diff(e.before,e.after)
            if not old or not new:continue
            ep=(e.before[max(0,l-8):l],e.before[len(e.before)-r:len(e.before)-r+8] if r else '',shape(old),shape(new));epc[ep]+=1
            cmd={s for _,_,s in spans(e.command)};bef={s for _,_,s in spans(e.before)};aft={s for _,_,s in spans(e.after)};fut={s for _,_,s in spans(e.future)}
            records.append((e,ep,sorted([s for s in cmd&bef&aft&fut if 2<=len(s)<=12],key=len,reverse=True)[:4],sorted([s for s in cmd&aft&fut if s not in e.before and len(s)<=10],key=len,reverse=True)[:4]))
        self.endpoints=[Endpoint(*k,n) for k,n in epc.most_common(32)];epi={(p.sl,p.sr,p.old_shape,p.new_shape):i for i,p in enumerate(self.endpoints)};st=defaultdict(lambda:[0,0])
        for e,ep,os,vs in records:
            if ep not in epi:continue
            for o in os:
                for v in vs:
                    pr=self.apply_endpoint(e.before,v,self.endpoints[epi[ep]]);key=(shape(o),shape(v),epi[ep]);st[key][0 if pr==e.after and o in e.before and o in e.command else 1]+=1
        self.programs=sorted([Program(*k,a,b) for k,(a,b) in st.items() if a>=2 and b<=a],key=lambda p:p.support-p.wrong,reverse=True)[:32]
        truths=[e.after for e in pool]
        if shuffle:truths=truths[1:]+truths[:1]
        rex=[]
        for e,truth in zip(pool,truths):
            g=self.generate_base(e)
            if not g:continue
            tl,tr,_,new=diff(e.before,truth);tb=len(e.before)-tr;cv=e.command.find(new)
            if cv<0:continue
            for z in sorted(g,key=lambda z:edit_distance(z[1],truth))[:6]:
                va=e.command.find(z[4])
                if va<0:continue
                rep=Repair(max(-3,min(3,tl-z[5])),max(-3,min(3,tb-z[6])),max(-3,min(3,cv-va)),max(-3,min(3,cv+len(new)-(va+len(z[4])))));self.repairs[rep]+=1;rex.append((e,truth,z,rep))
        self.repairs=Counter({r:n for r,n in self.repairs.items() if n>=2});byrep=defaultdict(list)
        for e,truth,z,rep in rex:
            if rep not in self.repairs:continue
            cf=self.consequence_features(e,z,rep)
            if cf:byrep[rep].append((cf[1],1 if cf[0]==truth else -1))
        for rep,examples in byrep.items():
            rule=self.fit_predicates(examples)
            if rule:self.rules[rep]=list(rule)
        literal=sum(8*(len(e.before)+len(e.command)+len(e.after)+len(e.future)) for e in ind+pool);graph=len(self.programs)*128+sum(64+8*(len(p.sl)+len(p.sr)) for p in self.endpoints)
        self.bits=literal if self.mode=='graph' else graph+len(self.repairs)*24+sum(18*len(r) for r in self.rules.values());self.stats.update(programs=len(self.programs),repairs=len(self.repairs),rules=len(self.rules),predicates=sum(len(x) for x in self.rules.values()),examples=sum(map(len,byrep.values())));self.train_s=time.perf_counter()-t
    def applicable(self,e):
        if self.mode=='global':return list(self.repairs)[:self.topk]
        if self.mode not in ('executable','shuffle'):return []
        g=self.generate_base(e);rank=[]
        for rep,rule in self.rules.items():
            votes=0
            for z in g[:16]:
                cf=self.consequence_features(e,z,rep)
                if cf and all((cf[1][p.feature]<=p.threshold) if p.polarity<0 else (cf[1][p.feature]>=p.threshold) for p in rule):votes+=1
            if votes:rank.append((votes*self.repairs[rep]/max(1,len(rule)),rep))
        return [r for _,r in sorted(rank,key=lambda z:z[0],reverse=True)[:self.topk]]
    def predict(self,e):
        reps=self.applicable(e);g=self.generate_repairs(e,reps)
        if not g:return e.before,False,0,[],len(reps)
        ranked=sorted(g,reverse=True)
        if len(ranked)>1 and ranked[0][0]-ranked[1][0]<.5:return e.before,False,len(ranked),[(x[3],x[4]) for x in ranked],len(reps)
        x=ranked[0];return x[1],True,len(ranked),[(z[3],z[4]) for z in ranked],len(reps)

def evalm(m,test):
    t=time.perf_counter();c=w=k=rec=ca=rr=0
    for e in test:
        p,d,n,pairs,r=m.predict(e);c+=d and p==e.after;w+=d and p!=e.after;k+=d;rec+=any(o==e.obj and v==e.new for o,v in pairs);ca+=n;rr+=r
    n=len(test);return {'accuracy':c/n,'wrong_commit':w/n,'commit_rate':k/n,'pair_recall':rec/n,'mean_candidates':ca/n,'mean_repairs':rr/n,'programs':m.stats['programs'],'repairs':m.stats['repairs'],'rules':m.stats['rules'],'predicates':m.stats['predicates'],'scope_examples':m.stats['examples'],'description_bits':m.bits,'model_bytes':len(pickle.dumps(m)),'training_seconds':m.train_s,'inference_ms':(time.perf_counter()-t)*1000/n}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='MEASUREMENTS_CYCLE_034.json');a=ap.parse_args();modes=['seen','order','lexeme','rename','alternate','nested','omitted','paragraph'];methods=('graph','global','executable','shuffle');raw={}
    for seed in (1,7,19):
        tr=build(seed,60,'seen');ind,pool=tr[:40],tr[40:];mods={}
        for mode in methods:
            x=Model(mode);x.fit(ind,pool,shuffle=(mode=='shuffle'));mods[mode]=x
        raw[str(seed)]={mode:{k:evalm(v,build(seed+999,10,mode)) for k,v in mods.items()} for mode in modes}
    summary={mode:{method:{k:statistics.mean(raw[str(seed)][mode][method][k] for seed in (1,7,19)) for k in raw['1'][mode][method]} for method in methods} for mode in modes}
    payload={'cycle':34,'hypothesis':'Executable Scope Programs from Repair-Induced Probe Consequence Predictions','raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'induction O(NKoKv), repair O(VHL), predicate DAG O(RF^2V), inference O(TL^2+topk*TRF)','final_test_outcome_used':False,'probe_pool_independent':True,'fixed_ontology_or_handwritten_slots_used_by_model':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
