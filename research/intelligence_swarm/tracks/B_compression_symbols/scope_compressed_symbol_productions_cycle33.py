from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse,json,pickle,random,resource,statistics,time,math

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末',
         '北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
FIELDS=['場所','状態','担当']
VALUES={'場所':['棚A','棚B','棚C','棚D'],'状態':['待機','処理中','完了','保留'],'担当':['担当一','担当二','担当三','担当四']}
STATE0='{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。'
STATE1='{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。'
CMDS={'場所':['{o}を{v}へ移してください。','{o}の保管先を{v}へ変更します。'],
      '状態':['{o}を{v}にしてください。','{o}の進行状態を{v}へ切り替えます。'],
      '担当':['{o}を{v}の担当にしてください。','{o}の受け持ちを{v}へ変更します。']}
ORDER={'場所':['{v}へ移してください、対象は{o}です。'],
       '状態':['{v}扱いにしてください、対象は{o}です。'],
       '担当':['{v}へ引き継いでください、対象は{o}です。']}
LEX={'場所':['対象{o}は次から{v}で保管。'],
     '状態':['対象{o}は以後{v}として運用。'],
     '担当':['対象{o}の受持を{v}へ。']}
OMIT={'場所':['それを{v}へ移してください。'],
      '状態':['その対象を{v}にしてください。'],
      '担当':['担当は{v}へ変えてください。']}

@dataclass
class Ex:
    before:str; command:str; after:str; future:str
    obj:str; field:str; old:str; new:str; mode:str
@dataclass
class Endpoint:
    sl:str; sr:str; old_shape:str; new_shape:str; support:int=0
@dataclass
class Program:
    obj_shape:str; val_shape:str; endpoint:int; support:int=0; wrong:int=0
@dataclass(frozen=True)
class Repair:
    target_left:int; target_right:int; value_left:int; value_right:int
@dataclass(frozen=True)
class ScopeCode:
    command_len_bucket:int
    before_len_bucket:int
    common_count_bucket:int
    novel_count_bucket:int
    prefix_shape:str
    suffix_shape:str

def state(o,d,form):
    return (STATE1 if form else STATE0).format(o=o,loc=d['場所'],status=d['状態'],owner=d['担当'])
def shape(s):
    return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、／=：:\n 「」' else c for c in s)
def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def spans(text,max_len=12):
    return {(i,j,text[i:j]) for i in range(len(text)) for j in range(i+1,min(len(text),i+max_len)+1)}
def build(seed,n,mode):
    rng=random.Random(seed);world={};out=[];focus=None
    for i in range(n):
        canon=focus if mode=='omitted' and focus is not None else rng.choice(OBJECTS)
        surf=ALIASES[canon] if mode=='rename' else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS})
        f=rng.choice(FIELDS);old=world[canon][f];new=rng.choice([x for x in VALUES[f] if x!=old])
        form=1 if mode=='alternate' else 0;before=state(surf,world[canon],form)
        forms=ORDER[f] if mode=='order' else LEX[f] if mode=='lexeme' else OMIT[f] if mode=='omitted' else CMDS[f]
        command=random.Random(seed*1000+i).choice(forms).format(o=surf,v=new)
        if mode=='nested':command='依頼内容は「'+command+'」です。'
        if mode=='paragraph':command='前段の説明があります。別件は変更しません。\n'+command+'\n補助記録は維持してください。'
        world[canon][f]=new;after=state(surf,world[canon],form)
        future=f'次の観測でも{surf}の更新結果は{new}で、補助記録は維持されます。'
        out.append(Ex(before,command,after,future,surf,f,old,new,mode));focus=canon
    return out

def apply_span(before,value,a,b):
    if not (0<=a<b<=len(before)):return None
    return before[:a]+value+before[b:]
def edit_distance(a,b):
    prev=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        cur=[i]
        for j,y in enumerate(b,1):
            cur.append(min(cur[-1]+1,prev[j]+1,prev[j-1]+(x!=y)))
        prev=cur
    return prev[-1]
def boundary_distance(a,b,ta,tb):
    return abs(a-ta)+abs(b-tb)

def scope_code(e):
    cs={x for _,_,x in spans(e.command,10)}
    bs={x for _,_,x in spans(e.before,10)}
    common=sum(1 for x in cs if x in bs)
    novel=sum(1 for x in cs if x not in bs)
    return ScopeCode(min(7,len(e.command)//8),min(7,len(e.before)//8),
                     min(7,common//8),min(7,novel//8),
                     shape(e.command[:6]),shape(e.command[-6:]))

def scope_distance(a,b):
    return (abs(a.command_len_bucket-b.command_len_bucket)+
            abs(a.before_len_bucket-b.before_len_bucket)+
            abs(a.common_count_bucket-b.common_count_bucket)+
            abs(a.novel_count_bucket-b.novel_count_bucket)+
            (a.prefix_shape!=b.prefix_shape)+(a.suffix_shape!=b.suffix_shape))

class Model:
    def __init__(self,mode,budget=16,topk=4):
        self.mode=mode;self.budget=budget;self.topk=topk
        self.endpoints=[];self.programs=[];self.repairs=Counter()
        self.scope_stats=defaultdict(Counter)
        self.scope_rules=defaultdict(list)
        self.stats=Counter();self.bits=0;self.train_s=0

    def fit(self,induction,pool,shuffle=False):
        t0=time.perf_counter(); epc=Counter(); records=[]
        for e in induction:
            l,r,old,new=diff(e.before,e.after)
            if not old or not new:continue
            ep=(e.before[max(0,l-8):l],e.before[len(e.before)-r:len(e.before)-r+8] if r else '',shape(old),shape(new))
            epc[ep]+=1
            cmd={s for _,_,s in spans(e.command)};bef={s for _,_,s in spans(e.before)}
            aft={s for _,_,s in spans(e.after)};fut={s for _,_,s in spans(e.future)}
            oc=sorted([s for s in cmd&bef&aft&fut if 2<=len(s)<=12],key=lambda x:(-len(x),x))[:4]
            vc=sorted([s for s in cmd&aft&fut if s not in e.before and 1<=len(s)<=10],key=lambda x:(-len(x),x))[:4]
            records.append((e,ep,oc,vc))
        self.endpoints=[Endpoint(*k,support=n) for k,n in epc.most_common(32)]
        epi={(p.sl,p.sr,p.old_shape,p.new_shape):i for i,p in enumerate(self.endpoints)}
        st=defaultdict(lambda:[0,0])
        for e,ep,ocs,vcs in records:
            pi=epi.get(ep)
            if pi is None:continue
            for o in ocs:
                for v in vcs:
                    pred=self.apply_endpoint(e.before,v,self.endpoints[pi]);key=(shape(o),shape(v),pi)
                    if pred==e.after and o in e.before and o in e.command:st[key][0]+=1
                    elif pred is not None:st[key][1]+=1
        self.programs=[Program(*k,pos,wrong) for k,(pos,wrong) in st.items() if pos>=3 and wrong<=pos]
        self.programs=sorted(self.programs,key=lambda p:(p.support-p.wrong),reverse=True)[:64]

        outcomes=[e.after for e in pool]
        if shuffle and outcomes:outcomes=outcomes[1:]+outcomes[:1]
        probe_records=[]
        for idx,e in enumerate(pool):
            g=self.generate_base(e)
            by={ti:pred for _,pred,ti,_,_,_,_ in g}
            pairs=set()
            for a in by:
                for b in by:
                    if a>=b or by[a]==by[b]:continue
                    ca=by[a]==outcomes[idx];cb=by[b]==outcomes[idx]
                    if ca!=cb:pairs.add((a,b) if ca else (b,a))
            if pairs:
                bits=8*(len(e.before)+len(e.command))
                probe_records.append((len(pairs)/max(1,bits),idx,e))
        chosen=sorted(probe_records,reverse=True)[:self.budget]

        repair_examples=[]
        for _,idx,e in chosen:
            truth=outcomes[idx]
            g=self.generate_base(e)
            if not g:continue
            ranked=sorted(g,key=lambda z:edit_distance(z[1],truth))[:12]
            tl,tr,_,new=diff(e.before,truth);true_b=len(e.before)-tr
            cv=e.command.find(new)
            if cv<0:continue
            sc=scope_code(e)
            for _,pred,ti,o,v,ta,tb in ranked:
                if pred==truth:continue
                va=e.command.find(v)
                if va<0:continue
                rep=Repair(max(-3,min(3,tl-ta)),max(-3,min(3,true_b-tb)),
                           max(-3,min(3,cv-va)),max(-3,min(3,(cv+len(new))-(va+len(v)))))
                self.repairs[rep]+=1
                repair_examples.append((e,truth,rep,sc))
        self.repairs=Counter({r:n for r,n in self.repairs.items() if n>=2})

        for e,truth,rep,sc in repair_examples:
            if rep not in self.repairs:continue
            candidates=self.generate_with_repairs(e,[rep])
            matched=[pred for _,pred,_,_,_,_,_ in candidates]
            status=1 if truth in matched else -1 if matched else 0
            self.scope_stats[rep][(sc,status)]+=1

        for rep in self.repairs:
            code_scores=[]
            aggregated=defaultdict(lambda:[0,0,0])
            for (sc,status),n in self.scope_stats[rep].items():
                aggregated[sc][0 if status==1 else 1 if status==-1 else 2]+=n
            for sc,(succ,wrong,noexec) in aggregated.items():
                utility=2.5*succ-3.0*wrong-0.2*noexec-0.15*(6+sum(map(len,(sc.prefix_shape,sc.suffix_shape))))
                if utility>0 and succ>=1:
                    code_scores.append((utility,sc,succ,wrong,noexec))
            self.scope_rules[rep]=[(sc,succ,wrong,noexec) for _,sc,succ,wrong,noexec in sorted(code_scores,key=lambda x:x[0],reverse=True)[:8]]

        literal=sum(8*(len(e.before)+len(e.command)+len(e.after)+len(e.future)) for e in induction+pool)
        graph=sum(64+8*(len(p.sl)+len(p.sr)) for p in self.endpoints)+len(self.programs)*128
        repair_bits=len(self.repairs)*24
        scope_bits=sum(12+4*(len(sc.prefix_shape)+len(sc.suffix_shape)) for rules in self.scope_rules.values() for sc,_,_,_ in rules)
        residual_errors=sum(wrong+noexec for rules in self.scope_rules.values() for _,_,wrong,noexec in rules)*3
        self.bits=literal if self.mode=='graph' else graph+repair_bits+(scope_bits+residual_errors if self.mode in ('scoped','shuffle_scoped') else 0)
        self.stats.update(programs=len(self.programs),repairs=len(self.repairs),
                          scope_rules=sum(len(x) for x in self.scope_rules.values()),
                          repair_examples=len(repair_examples))
        self.train_s=time.perf_counter()-t0

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

    def candidates(self,e):
        es={x for _,_,x in spans(e.command)}
        bs={x for _,_,x in spans(e.before)}
        common=[(e.command.find(s),e.command.find(s)+len(s),s) for s in es&bs if 2<=len(s)<=12]
        novel=[(e.command.find(s),e.command.find(s)+len(s),s) for s in es if s not in e.before and 1<=len(s)<=10]
        return common,novel

    def generate_base(self,e):
        common,novel=self.candidates(e);out=[]
        for ti,t in enumerate(self.programs):
            p=self.endpoints[t.endpoint]
            os=[x for x in common if shape(x[2])==t.obj_shape][:4]
            vs=[x for x in novel if shape(x[2])==t.val_shape][:8]
            for _,_,o in os:
                for vi,vj,v in vs:
                    pred=self.apply_endpoint(e.before,v,p)
                    if pred is not None:
                        l,r,_,_=diff(e.before,pred);out.append((t.support-t.wrong,pred,ti,o,v,l,len(e.before)-r))
        best={}
        for z in out:
            if z[1] not in best or z[0]>best[z[1]][0]:best[z[1]]=z
        return list(best.values())[:128]

    def applicable_repairs(self,e):
        if self.mode=='global':
            return list(self.repairs)[:self.topk]
        if self.mode not in ('scoped','shuffle_scoped'):
            return []
        sc=scope_code(e);ranked=[]
        for rep,rules in self.scope_rules.items():
            if not rules:continue
            d,s,w,n=min((scope_distance(sc,rc),succ,wrong,noexec) for rc,succ,wrong,noexec in rules)
            score=(s+1)/(w+n+1)-0.35*d
            ranked.append((score,rep))
        return [r for score,r in sorted(ranked,key=lambda x:x[0],reverse=True)[:self.topk] if score>0]

    def generate_with_repairs(self,e,reps):
        base=self.generate_base(e)
        out=list(base)
        for score,pred,ti,o,v,ta,tb in base:
            va=e.command.find(v);vb=va+len(v)
            for rep in reps:
                na=max(0,min(len(e.before)-1,ta+rep.target_left))
                nb=max(na+1,min(len(e.before),tb+rep.target_right))
                nva=max(0,min(len(e.command)-1,va+rep.value_left))
                nvb=max(nva+1,min(len(e.command),vb+rep.value_right))
                rv=e.command[nva:nvb];rpred=apply_span(e.before,rv,na,nb)
                if rpred is not None:out.append((score+.2,rpred,ti,o,rv,na,nb))
        best={}
        for z in out:
            if z[1] not in best or z[0]>best[z[1]][0]:best[z[1]]=z
        return list(best.values())[:128]

    def predict(self,e):
        reps=self.applicable_repairs(e)
        g=self.generate_with_repairs(e,reps)
        if not g:return e.before,False,0,[],999,len(reps)
        ranked=sorted(g,reverse=True)
        tl,tr,_,_=diff(e.before,e.after);true_b=len(e.before)-tr
        md=min((boundary_distance(x[5],x[6],tl,true_b) for x in ranked),default=999)
        if len(ranked)>1 and ranked[0][0]-ranked[1][0]<.5:
            return e.before,False,len(ranked),[(x[3],x[4]) for x in ranked],md,len(reps)
        x=ranked[0]
        return x[1],True,len(ranked),[(z[3],z[4]) for z in ranked],md,len(reps)

def evalm(m,test):
    t=time.perf_counter();c=w=k=rec=cands=0;dists=[];expanded=0
    for e in test:
        p,d,n,pairs,bd,nrep=m.predict(e);k+=d;c+=d and p==e.after;w+=d and p!=e.after;cands+=n;dists.append(bd);expanded+=nrep
        rec+=any(o==e.obj and v==e.new for o,v in pairs)
    n=len(test)
    return {'accuracy':c/n,'wrong_commit':w/n,'commit_rate':k/n,'pair_recall':rec/n,
            'mean_candidates':cands/n,'mean_boundary_distance':statistics.mean(dists),
            'mean_expanded_repairs':expanded/n,'programs':m.stats['programs'],
            'repairs':m.stats['repairs'],'scope_rules':m.stats['scope_rules'],
            'repair_examples':m.stats['repair_examples'],'description_bits':m.bits,
            'model_bytes':len(pickle.dumps(m)),'training_seconds':m.train_s,
            'inference_ms':(time.perf_counter()-t)*1000/n}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='MEASUREMENTS_CYCLE_033.json');a=ap.parse_args()
    modes=['seen','order','lexeme','rename','alternate','nested','omitted','paragraph'];raw={}
    methods=('graph','global','scoped','shuffle_scoped')
    for seed in (1,7,19):
        alltr=build(seed,288,'seen');ind=alltr[:190];pool=alltr[190:];models={}
        for mode in methods:
            m=Model(mode,16,topk=4);m.fit(ind,pool,shuffle=(mode=='shuffle_scoped'));models[mode]=m
        raw[str(seed)]={mode:{k:evalm(v,build(seed+999,24,mode)) for k,v in models.items()} for mode in modes}
    summary={mode:{method:{k:statistics.mean(raw[str(seed)][mode][method][k] for seed in (1,7,19)) for k in raw['1'][mode][method]}
                   for method in methods} for mode in modes}
    payload={'cycle':33,'hypothesis':'Scope-Compressed Symbol Productions from Repair Applicability Codes',
      'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      'estimated_complexity':'program induction O(NKoKv), probe repair O(VHL^2), scope coding O(RV log V), inference O(TL^2+topk*TR)',
      'final_test_outcome_used':False,'probe_pool_independent':True,'fixed_ontology_or_handwritten_slots_used_by_model':False,
      'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
