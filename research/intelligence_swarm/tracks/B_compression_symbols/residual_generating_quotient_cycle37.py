from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse, json, pickle, random, resource, statistics, time

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
    before:str; command:str; after:str; future:str
    obj:str; field:str; old:str; new:str; mode:str

@dataclass(frozen=True)
class Production:
    sb:int; sw:int; vb:int; vw:int; ob:int; ow:int
    old_shape:str; new_shape:str; obj_shape:str

@dataclass
class Symbol:
    p:Production; support:int=0; wrong:int=0
    signature:tuple=(); residual_splits:int=0; born:bool=False

def shape(s):
    return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、／=：:\n 「」' else c for c in s)

def state(o,d,form):
    return (STATE1 if form else STATE0).format(o=o,loc=d['場所'],status=d['状態'],owner=d['担当'])

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

def bucket(pos,n,k=16): return min(k-1,max(0,int(k*pos/max(1,n))))

def span_from_bucket(text,b,w,k=16):
    a=round(len(text)*b/k); z=round(len(text)*min(k,b+w)/k)
    if z<=a: z=min(len(text),a+1)
    return a,z,text[a:z]

def build(seed,n,mode):
    rng=random.Random(seed); world={}; focus=None; out=[]
    for _ in range(n):
        canon=focus if mode=='omitted' and focus else rng.choice(OBJECTS)
        surf=ALIASES[canon] if mode=='rename' else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS})
        f=rng.choice(FIELDS); old=world[canon][f]; new=rng.choice([x for x in VALUES[f] if x!=old])
        form=1 if mode=='alternate' else 0; before=state(surf,world[canon],form)
        forms=ORDER[f] if mode=='order' else LEX[f] if mode=='lexeme' else OMIT[f] if mode=='omitted' else CMDS[f]
        command=rng.choice(forms).format(o=surf,v=new)
        if mode=='nested': command='依頼内容は「'+command+'」です。'
        if mode=='paragraph': command='前段の説明があります。別件は変更しません。\n'+command+'\n補助記録は維持してください。'
        world[canon][f]=new; after=state(surf,world[canon],form)
        future=f'次の観測でも{surf}の更新結果は{new}で、補助記録は維持されます。'
        out.append(Ex(before,command,after,future,surf,f,old,new,mode)); focus=canon
    return out

def induce(e):
    l,r,old,new=diff(e.before,e.after)
    vi=e.command.find(new); oi=e.command.find(e.obj)
    if not old or not new or vi<0 or oi<0:return None
    return Production(bucket(l,len(e.before)),max(1,bucket(l+len(old),len(e.before))-bucket(l,len(e.before))),bucket(vi,len(e.command)),max(1,bucket(vi+len(new),len(e.command))-bucket(vi,len(e.command))),bucket(oi,len(e.command)),max(1,bucket(oi+len(e.obj),len(e.command))-bucket(oi,len(e.command))),shape(old),shape(new),shape(e.obj))

def apply(e,p):
    sa,sb,s=span_from_bucket(e.before,p.sb,p.sw)
    va,vb,v=span_from_bucket(e.command,p.vb,p.vw)
    oa,ob,o=span_from_bucket(e.command,p.ob,p.ow)
    if shape(s)!=p.old_shape:return None
    return e.before[:sa]+v+e.before[sb:],o,v,(sa,sb),(va,vb),(oa,ob)

def local_trace(e,p,truth):
    out=apply(e,p)
    if not out:return ('N',0,0,0,0)
    pred,o,v,ss,vs,os=out
    correct=int(pred==truth)
    inv=int(pred[:ss[0]]+e.old+pred[ss[0]+len(v):]==e.before)
    preserve=int(('補助記録' in pred)==('補助記録' in e.before))
    return ('C' if correct else 'W',inv,preserve,shape(o)==p.obj_shape,shape(v)==p.new_shape)

def residual_ops(e,p,truth):
    out=apply(e,p)
    if not out:return []
    pred,o,v,ss,vs,os=out
    l,r,_,_=diff(pred,truth); target_b=bucket(l,len(e.before))
    value_pos=e.command.find(e.new); object_pos=e.command.find(e.obj); candidates=[]
    for ds in (-2,-1,0,1,2):
        for dw in (-1,0,1):
            candidates.append(Production(max(0,min(15,p.sb+ds)),max(1,min(8,p.sw+dw)),p.vb,p.vw,p.ob,p.ow,p.old_shape,p.new_shape,p.obj_shape))
    if value_pos>=0:
        vb=bucket(value_pos,len(e.command)); vw=max(1,bucket(value_pos+len(e.new),len(e.command))-vb)
        for dv in (-1,0,1):
            candidates.append(Production(p.sb,p.sw,max(0,min(15,vb+dv)),vw,p.ob,p.ow,p.old_shape,shape(e.new),p.obj_shape))
    if object_pos>=0:
        ob=bucket(object_pos,len(e.command)); ow=max(1,bucket(object_pos+len(e.obj),len(e.command))-ob)
        for do in (-1,0,1):
            candidates.append(Production(p.sb,p.sw,p.vb,p.vw,max(0,min(15,ob+do)),ow,p.old_shape,p.new_shape,shape(e.obj)))
    candidates.append(Production(target_b,p.sw,p.vb,p.vw,p.ob,p.ow,p.old_shape,p.new_shape,p.obj_shape))
    return list(dict.fromkeys(candidates))

class Model:
    def __init__(self,mode):
        self.mode=mode; self.symbols=[]; self.quotients={}; self.born=0
        self.trace_audits=0; self.birth_trials=0; self.bits=0; self.train_s=0
    def fit(self,ind,probe,shuffle=False):
        t=time.perf_counter(); cnt=Counter()
        for e in ind:
            p=induce(e)
            if p:cnt[p]+=1
        syms=[Symbol(p,support=n) for p,n in cnt.items() if n>=2]
        truths=[e.after for e in probe]
        if shuffle:truths=truths[1:]+truths[:1]
        groups=defaultdict(list)
        for i,s in enumerate(syms):
            sig=[]
            for e,tr in zip(probe,truths):
                z=local_trace(e,s.p,tr); self.trace_audits+=1; sig.append(z)
                if z[0]=='C':s.support+=1
                elif z[0]=='W':s.wrong+=1
            s.signature=tuple(Counter(sig).most_common())
            groups[(s.p.old_shape,s.p.new_shape,s.p.obj_shape,s.signature)].append(i)
        born_counter=Counter()
        if self.mode in ('birth','mdl'):
            for members in groups.values():
                if len(members)<2:continue
                member_syms=[syms[i] for i in members]
                for e,tr in zip(probe,truths):
                    outcomes=[local_trace(e,s.p,tr)[0] for s in member_syms]
                    if 'C' not in outcomes or 'W' not in outcomes:continue
                    for s,outcome in zip(member_syms,outcomes):
                        if outcome!='W':continue
                        for np in residual_ops(e,s.p,tr):
                            self.birth_trials+=1; no=apply(e,np)
                            if no and no[0]==tr:born_counter[np]+=1
                            elif no:born_counter[np]-=1
            for p,score in born_counter.items():
                if score>=2:
                    syms.append(Symbol(p,support=score,residual_splits=score,born=True)); self.born+=1
        for s in syms:
            if s.born:
                for e,tr in zip(probe,truths):
                    z=local_trace(e,s.p,tr); self.trace_audits+=1
                    if z[0]=='C':s.support+=1
                    elif z[0]=='W':s.wrong+=1
        self.symbols=sorted([s for s in syms if s.support>=2],key=lambda s:(s.support-s.wrong,s.residual_splits,-s.p.sw),reverse=True)[:64]
        q=defaultdict(list)
        for i,s in enumerate(self.symbols):q[(s.p.old_shape,s.p.new_shape,s.p.obj_shape,s.signature)].append(i)
        self.quotients={k:v for k,v in q.items() if len(v)>=2}
        literal=sum(8*(len(e.before)+len(e.command)+len(e.after)+len(e.future)) for e in ind+probe)
        grammar=len(self.symbols)*120+len(self.quotients)*64+self.born*48
        residual=sum(max(0,s.wrong-s.support)*16 for s in self.symbols)
        self.bits=literal if self.mode=='factorized' else grammar+residual
        self.train_s=time.perf_counter()-t
    def predict(self,e):
        qmember={i for v in self.quotients.values() for i in v}; cand=[]
        for i,s in enumerate(self.symbols):
            out=apply(e,s.p)
            if not out:continue
            pred,o,v,*_=out; score=s.support-s.wrong
            if self.mode in ('quotient','birth','mdl') and i in qmember:score+=1
            if self.mode in ('birth','mdl') and s.born:score+=s.residual_splits
            cand.append((score,pred,o,v))
        best={}
        for z in cand:
            if z[1] not in best or z[0]>best[z[1]][0]:best[z[1]]=z
        ranked=sorted(best.values(),reverse=True)[:64]
        if not ranked:return None,0,[]
        if len(ranked)>1 and ranked[0][0]-ranked[1][0]<1:return None,len(ranked),[(x[2],x[3]) for x in ranked]
        return ranked[0][1],len(ranked),[(x[2],x[3]) for x in ranked]

def evaluate(m,test):
    t=time.perf_counter(); correct=wrong=null=pair=cands=0
    for e in test:
        p,n,pairs=m.predict(e); cands+=n; null+=p is None; correct+=p==e.after
        wrong+=p is not None and p!=e.after; pair+=any(o==e.obj and v==e.new for o,v in pairs)
    n=len(test)
    return {'accuracy':correct/n,'wrong_commit':wrong/n,'null_rate':null/n,'pair_recall':pair/n,'mean_candidates':cands/n,'symbols':len(m.symbols),'quotient_classes':len(m.quotients),'born_productions':m.born,'birth_trials':m.birth_trials,'trace_audits':m.trace_audits,'description_bits':m.bits,'model_bytes':len(pickle.dumps(m)),'training_seconds':m.train_s,'inference_ms':(time.perf_counter()-t)*1000/n}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',default='MEASUREMENTS_CYCLE_037.json'); a=ap.parse_args()
    modes=['seen','order','lexeme','rename','alternate','nested','omitted','paragraph']; raw={}
    for seed in (1,7,19):
        train=build(seed,60,'seen'); ind=train[:40]; probe=train[40:]; models={}
        for mode in ('factorized','quotient','birth','mdl'):
            m=Model(mode); m.fit(ind,probe,False); models[mode]=m
        sh=Model('birth'); sh.fit(ind,probe,True); models['shuffle']=sh
        raw[str(seed)]={mode:{name:evaluate(m,build(seed+999,30,mode)) for name,m in models.items()} for mode in modes}
    summary={}
    for mode in modes:
        summary[mode]={}
        for name in ('factorized','quotient','birth','mdl','shuffle'):
            keys=[k for k,v in raw['1'][mode][name].items() if isinstance(v,(int,float))]
            summary[mode][name]={k:statistics.mean(raw[str(seed)][mode][name][k] for seed in (1,7,19)) for k in keys}
    payload={'cycle':37,'hypothesis':'Residual-Generating Quotient Productions from Counterexample Trace Splits','seeds':[1,7,19],'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'induction O(NL), trace audit O(QP), residual birth O(QPR), quotient partition O(P log P), inference O(PL)','final_test_after_future_used_for_selection':False,'fixed_ontology_or_handwritten_slots_used_by_model':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
