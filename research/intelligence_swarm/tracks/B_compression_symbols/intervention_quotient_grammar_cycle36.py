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
    before:str; command:str; after:str; future:str; obj:str; field:str; old:str; new:str; mode:str

@dataclass(frozen=True)
class Production:
    sb:int; sw:int; vb:int; vw:int; ob:int; ow:int; old_shape:str; new_shape:str; obj_shape:str

@dataclass
class Symbol:
    production:Production; support:int=0; wrong:int=0
    single_ok:int=0; single_wrong:int=0
    trace_ok:int=0; trace_wrong:int=0
    signature:tuple=()

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

def bucket(pos,n,k=16): return min(k-1,int(k*pos/max(1,n)))

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
    if not old or not new or vi<0 or oi<0: return None
    return Production(bucket(l,len(e.before)),max(1,bucket(l+len(old),len(e.before))-bucket(l,len(e.before))),
        bucket(vi,len(e.command)),max(1,bucket(vi+len(new),len(e.command))-bucket(vi,len(e.command))),
        bucket(oi,len(e.command)),max(1,bucket(oi+len(e.obj),len(e.command))-bucket(oi,len(e.command))),
        shape(old),shape(new),shape(e.obj))

def apply(e,p,value=None,obj=None,reverse_order=False):
    sa,sb,s=span_from_bucket(e.before,p.sb,p.sw)
    va,vb,v=span_from_bucket(e.command,p.vb,p.vw)
    oa,ob,o=span_from_bucket(e.command,p.ob,p.ow)
    if shape(s)!=p.old_shape: return None
    value=v if value is None else value; obj=o if obj is None else obj
    pred=e.before[:sa]+value+e.before[sb:]
    if reverse_order:
        cmd=e.command[va:vb]+' '+e.command[:va]+e.command[vb:]
    else: cmd=e.command
    return pred,value,obj,cmd,(sa,sb),(va,vb),(oa,ob)

def alt_value(base):
    vals=sum(VALUES.values(),[])
    return next((v for v in vals if v!=base and len(v)==len(base)),None)

def alt_object(base):
    return next((o for o in OBJECTS if o!=base and len(o)==len(base)),None)

def trace_signature(e,symbol,truth,shuffle_truth=None):
    p=symbol.production
    base=apply(e,p)
    if not base: return (0,)*8
    pred,v,o,_,_,_,_=base
    vals=[x for x in sum(VALUES.values(),[]) if x in e.command]
    basev=vals[0] if vals else v; av=alt_value(basev)
    ao=alt_object(e.obj)
    outcomes=[]
    outcomes.append(int(pred==(shuffle_truth if shuffle_truth is not None else truth)))
    if av:
        ev=Ex(e.before,e.command.replace(basev,av),e.after,e.future,e.obj,e.field,e.old,av,e.mode)
        ov=apply(ev,p,value=av)
        outcomes.append(int(bool(ov) and av in ov[0] and basev not in ov[0]))
    else: outcomes.append(0)
    if ao:
        eo=Ex(e.before.replace(e.obj,ao),e.command.replace(e.obj,ao),e.after.replace(e.obj,ao),e.future.replace(e.obj,ao),ao,e.field,e.old,e.new,e.mode)
        oo=apply(eo,p,obj=ao)
        outcomes.append(int(bool(oo) and ao in oo[0]))
    else: outcomes.append(0)
    oo=apply(e,p,reverse_order=True); outcomes.append(int(bool(oo) and oo[0]==pred))
    if av and ao:
        evo=Ex(e.before.replace(e.obj,ao),e.command.replace(basev,av).replace(e.obj,ao),e.after,e.future,ao,e.field,e.old,av,e.mode)
        p1=apply(evo,p,value=av,obj=ao)
        eov=Ex(e.before.replace(e.obj,ao),e.command.replace(e.obj,ao).replace(basev,av),e.after,e.future,ao,e.field,e.old,av,e.mode)
        p2=apply(eov,p,value=av,obj=ao)
        commute=int(bool(p1 and p2) and p1[0]==p2[0])
        outcomes.append(commute)
        outcomes.append(int(bool(p1) and av in p1[0]))
        outcomes.append(int(bool(p2) and ao in p2[0]))
    else: outcomes.extend([0,0,0])
    outcomes.append(int('補助記録' in pred)==int('補助記録' in e.before))
    return tuple(outcomes)

class Model:
    def __init__(self,mode):
        self.mode=mode; self.symbols=[]; self.quotients={}; self.bits=0; self.train_s=0; self.trace_audits=0
    def fit(self,ind,probe,shuffle=False):
        t=time.perf_counter(); cnt=Counter()
        for e in ind:
            p=induce(e)
            if p: cnt[p]+=1
        syms=[Symbol(p,support=n) for p,n in cnt.items() if n>=2]
        truths=[e.after for e in probe]
        if shuffle: truths=truths[1:]+truths[:1]
        for s in syms:
            sigs=[]
            for e,truth in zip(probe,truths):
                out=apply(e,s.production)
                if out:
                    pred,*_=out
                    if pred==truth: s.support+=1
                    else: s.wrong+=1
                sig=trace_signature(e,s,truth,shuffle_truth=truth if shuffle else None)
                self.trace_audits+=1; sigs.append(sig)
                s.single_ok+=sig[1]; s.single_wrong+=1-sig[1]
                coherent=int(sig[1] and sig[2] and sig[3] and sig[4] and sig[7])
                s.trace_ok+=coherent; s.trace_wrong+=1-coherent
            hist=Counter(sigs)
            s.signature=tuple(sorted((k,min(3,v)) for k,v in hist.items()))
        self.symbols=sorted([s for s in syms if s.support>=2],key=lambda x:(x.trace_ok-x.trace_wrong,x.support-x.wrong),reverse=True)[:48]
        groups=defaultdict(list)
        for i,s in enumerate(self.symbols):
            key=(s.production.old_shape,s.production.new_shape,s.production.obj_shape,s.signature)
            groups[key].append(i)
        self.quotients={k:v for k,v in groups.items() if len(v)>=2}
        literal=sum(8*(len(e.before)+len(e.command)+len(e.after)+len(e.future)) for e in ind+probe)
        grammar=len(self.symbols)*112+sum(48+8*len(v)+8*len(k[3]) for k,v in self.quotients.items())
        self.bits=literal if self.mode=='factorized' else grammar
        self.train_s=time.perf_counter()-t
    def predict(self,e):
        c=[]
        member_to_q={i:q for q,m in enumerate(self.quotients.values()) for i in m}
        for i,s in enumerate(self.symbols):
            out=apply(e,s.production)
            if not out: continue
            pred,v,o,*_=out
            score=s.support-s.wrong
            if self.mode=='single': score+=s.single_ok-s.single_wrong
            if self.mode in ('quotient','mdl'):
                score+=2*(s.trace_ok-s.trace_wrong)
                if i in member_to_q: score+=2
            c.append((score,pred,o,v,i))
        best={}
        for z in c:
            if z[1] not in best or z[0]>best[z[1]][0]: best[z[1]]=z
        ranked=sorted(best.values(),reverse=True)[:64]
        if not ranked: return None,0,[]
        if len(ranked)>1 and ranked[0][0]-ranked[1][0]<1: return None,len(ranked),[(x[2],x[3]) for x in ranked]
        return ranked[0][1],len(ranked),[(x[2],x[3]) for x in ranked]

def eval_model(m,test):
    t=time.perf_counter();correct=wrong=null=pair=cands=0
    for e in test:
        p,n,ps=m.predict(e); cands+=n; null+=p is None; correct+=p==e.after; wrong+=p is not None and p!=e.after; pair+=any(o==e.obj and v==e.new for o,v in ps)
    N=len(test)
    return {'accuracy':correct/N,'wrong_commit':wrong/N,'null_rate':null/N,'pair_recall':pair/N,'mean_candidates':cands/N,
            'symbols':len(m.symbols),'quotient_classes':len(m.quotients),'trace_audits':m.trace_audits,'description_bits':m.bits,
            'model_bytes':len(pickle.dumps(m)),'training_seconds':m.train_s,'inference_ms':(time.perf_counter()-t)*1000/N}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',default='MEASUREMENTS_CYCLE_036.json'); a=ap.parse_args()
    modes=['seen','order','lexeme','rename','alternate','nested','omitted','paragraph']; raw={}
    for seed in (1,7,19):
        ind=build(seed,72,'seen'); probe=build(seed+101,36,'seen')
        models={}
        for mode in ('factorized','single','quotient','mdl','shuffle'):
            m=Model(mode); m.fit(ind,probe,shuffle=mode=='shuffle'); models[mode]=m
        raw[str(seed)]={mode:{k:eval_model(m,build(seed+999,30,mode)) for k,m in models.items()} for mode in modes}
    summary={}
    for mode in modes:
        summary[mode]={}
        for method in ('factorized','single','quotient','mdl','shuffle'):
            keys=raw['1'][mode][method]
            summary[mode][method]={k:statistics.mean(raw[str(s)][mode][method][k] for s in (1,7,19)) for k in keys}
    payload={'cycle':36,'hypothesis':'Trace-Bisimulation Quotient Grammar from Minimal Multi-Intervention Diagrams','seeds':[1,7,19],
             'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             'estimated_complexity':'induction O(NL), intervention traces O(QPI), quotient partition O(P log P), inference O(PL)',
             'final_test_outcomes_used_for_selection':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,
             'weak_smartphone_verified':False,'completion':False}
    open(a.output,'w',encoding='utf-8').write(json.dumps(payload,ensure_ascii=False,indent=2)); print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
