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
    obj_shape:str; val_shape:str; endpoint:int
    support:int=0; wrong:int=0; noexec:int=0
@dataclass(frozen=True)
class Repair:
    target_left:int; target_right:int; value_left:int; value_right:int


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

def boundary_distance(a,b,ta,tb):
    return abs(a-ta)+abs(b-tb)

class Model:
    def __init__(self,mode,budget=16):
        self.mode=mode;self.budget=budget;self.endpoints=[];self.programs=[]
        self.probes=[];self.repairs=Counter();self.symbol_of={};self.symbol_members=defaultdict(list)
        self.repair_by_symbol=defaultdict(Counter);self.stats=Counter();self.bits=0;self.train_s=0

    def fit(self,induction,pool,shuffle=False):
        t0=time.perf_counter(); epc=Counter(); records=[]
        for e in induction:
            l,r,old,new=diff(e.before,e.after)
            if not old or not new:continue
            ep=(e.before[max(0,l-8):l],e.before[len(e.before)-r:len(e.before)-r+8] if r else '',shape(old),shape(new));epc[ep]+=1
            cmd={s for _,_,s in spans(e.command)};bef={s for _,_,s in spans(e.before)};aft={s for _,_,s in spans(e.after)};fut={s for _,_,s in spans(e.future)}
            common=[s for s in cmd&bef&aft&fut if 2<=len(s)<=12]
            novel=[s for s in cmd&aft&fut if s not in e.before and 1<=len(s)<=10]
            oc=sorted(common,key=lambda x:(-len(x),x))[:4];vc=sorted(novel,key=lambda x:(-len(x),x))[:4]
            records.append((e,ep,oc,vc,old))
        self.endpoints=[Endpoint(*k,support=n) for k,n in epc.most_common(32)]
        epi={(p.sl,p.sr,p.old_shape,p.new_shape):i for i,p in enumerate(self.endpoints)}
        st=defaultdict(lambda:[0,0,0])
        for e,ep,ocs,vcs,old in records:
            pi=epi.get(ep)
            if pi is None:continue
            for o in ocs:
                for v in vcs:
                    p=self.endpoints[pi];pred=self.apply_endpoint(e.before,v,p);key=(shape(o),shape(v),pi)
                    ok=pred==e.after and o in e.command and o in e.before
                    if pred is None:st[key][2]+=1
                    elif ok:st[key][0]+=1
                    else:st[key][1]+=1
        for (osh,vsh,pi),(pos,wrong,noexec) in st.items():
            if pos>=3 and wrong<=pos:self.programs.append(Program(osh,vsh,pi,pos,wrong,noexec))
        self.programs=sorted(self.programs,key=lambda z:(z.support-z.wrong,-z.noexec),reverse=True)[:64]

        tri_resp={i:[] for i in range(len(self.programs))};probe_records=[]
        outcomes=[e.after for e in pool]
        if shuffle and outcomes: outcomes=outcomes[1:]+outcomes[:1]
        for idx,e in enumerate(pool):
            generated=self.generate(e,repair=False)
            by={ti:pred for _,pred,ti,_,_,_,_ in generated}
            truth=outcomes[idx]
            pairs=[]
            for a in sorted(by):
                for b in sorted(by):
                    if a>=b or by[a]==by[b]:continue
                    ca=by[a]==truth;cb=by[b]==truth
                    if ca!=cb:pairs.append((a,b) if ca else (b,a))
            for ti in tri_resp:tri_resp[ti].append(1 if by.get(ti)==truth else -1 if ti in by else 0)
            if pairs:
                desc=8*(len(e.before)+len(e.command));probe_records.append((len(set(pairs))/max(1,desc),idx,e,pairs))
        chosen=sorted(probe_records,reverse=True)[:self.budget];chosen_idx={x[1] for x in chosen}
        self.probes=[x[1] for x in chosen]
        sigs=defaultdict(list);ordered=sorted(chosen_idx)
        for ti in range(len(self.programs)):
            ep=self.endpoints[self.programs[ti].endpoint]
            sig=(ep.old_shape,ep.new_shape,tuple(tri_resp[ti][i] for i in ordered))
            sigs[sig].append(ti)
        sid=0
        for _,members in sorted(sigs.items(),key=lambda kv:-len(kv[1])):
            if len(members)<2:continue
            for ti in members:self.symbol_of[ti]=sid
            self.symbol_members[sid]=members;sid+=1

        for _,idx,e,_ in chosen:
            generated=self.generate(e,repair=False)
            if not generated:continue
            ranked=sorted(generated,key=lambda g:self.edit_distance(g[1],e.after))[:12]
            tl,tr,_,new=diff(e.before,e.after)
            cv=e.command.find(new)
            if cv<0:continue
            for _,pred,ti,o,v,ta,tb in ranked:
                if self.edit_distance(pred,e.after)==0:continue
                va=e.command.find(v)
                if va<0:continue
                rep=Repair(max(-3,min(3,tl-ta)),max(-3,min(3,tr-tb)),max(-3,min(3,cv-va)),max(-3,min(3,(cv+len(new))-(va+len(v)))))
                self.repairs[rep]+=1
                sid=self.symbol_of.get(ti)
                if sid is not None:self.repair_by_symbol[sid][rep]+=1
        self.repairs=Counter({r:n for r,n in self.repairs.items() if n>=2})
        for sid,c in list(self.repair_by_symbol.items()):
            self.repair_by_symbol[sid]=Counter({r:n for r,n in c.items() if n>=2})

        literal=sum(8*(len(e.before)+len(e.command)+len(e.after)+len(e.future)) for e in induction+pool)
        graph=sum(64+8*(len(p.sl)+len(p.sr)) for p in self.endpoints)+len(self.programs)*128
        probe_bits=sum(8*(len(pool[i].before)+len(pool[i].command)) for i in self.probes)
        symbol_bits=len(self.symbol_members)*64+sum(6*len(v) for v in self.symbol_members.values())
        repair_bits=len(self.repairs)*24+sum(len(c)*12 for c in self.repair_by_symbol.values())
        self.bits=literal if self.mode=='graph' else graph+probe_bits+symbol_bits+(repair_bits if self.mode in ('repair','shuffle_repair') else 0)
        self.stats.update(programs=len(self.programs),probes=len(self.probes),symbols=len(self.symbol_members),symbol_members=sum(map(len,self.symbol_members.values())),repairs=len(self.repairs),repair_rules=sum(len(c) for c in self.repair_by_symbol.values()))
        self.train_s=time.perf_counter()-t0

    @staticmethod
    def edit_distance(a,b):
        prev=list(range(len(b)+1))
        for i,x in enumerate(a,1):
            cur=[i]
            for j,y in enumerate(b,1):cur.append(min(cur[-1]+1,prev[j]+1,prev[j-1]+(x!=y)))
            prev=cur
        return prev[-1]

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

    def generate(self,e,repair=False):
        common=[(e.command.find(s),e.command.find(s)+len(s),s) for s in ({x for _,_,x in spans(e.command)} & {x for _,_,x in spans(e.before)}) if 2<=len(s)<=12]
        novel=[(e.command.find(s),e.command.find(s)+len(s),s) for s in {x for _,_,x in spans(e.command,10)} if s not in e.before and 1<=len(s)<=10]
        out=[]
        for ti,t in enumerate(self.programs):
            p=self.endpoints[t.endpoint]
            osh={t.obj_shape};vsh={t.val_shape}
            if ti in self.symbol_of:
                mem=self.symbol_members[self.symbol_of[ti]];osh={self.programs[m].obj_shape for m in mem};vsh={self.programs[m].val_shape for m in mem}
            os=[x for x in common if shape(x[2]) in osh][:4];vs=[x for x in novel if shape(x[2]) in vsh][:8]
            for oi,oj,o in os:
                for vi,vj,v in vs:
                    pred=self.apply_endpoint(e.before,v,p)
                    if pred is not None:
                        l,r,_,_=diff(e.before,pred);out.append((t.support-t.wrong,pred,ti,o,v,l,len(e.before)-r))
                    if repair:
                        sid=self.symbol_of.get(ti);rules=list(self.repair_by_symbol.get(sid,{}))[:6]
                        if not rules: rules=list(self.repairs)[:6]
                        base_l,base_r,_,_=diff(e.before,pred) if pred is not None else (0,0,'','')
                        base_b=len(e.before)-base_r
                        for rep in rules:
                            ta=max(0,min(len(e.before)-1,base_l+rep.target_left))
                            tb=max(ta+1,min(len(e.before),base_b+rep.target_right))
                            va=max(0,min(len(e.command)-1,vi+rep.value_left));vb=max(va+1,min(len(e.command),vj+rep.value_right))
                            rv=e.command[va:vb]
                            rpred=apply_span(e.before,rv,ta,tb)
                            if rpred is not None:out.append((t.support-t.wrong+.25,rpred,ti,o,rv,ta,tb))
        best={}
        for z in out:
            if z[1] not in best or z[0]>best[z[1]][0]:best[z[1]]=z
        return list(best.values())[:128]

    def predict(self,e):
        repair=self.mode in ('repair','shuffle_repair')
        g=self.generate(e,repair=repair)
        if not g:return e.before,False,0,[],999
        best={}
        for base,pred,ti,o,v,ta,tb in g:
            score=base+.05*len(self.symbol_members.get(self.symbol_of.get(ti,-1),[]))
            if pred not in best or score>best[pred][0]:best[pred]=(score,ti,o,v,ta,tb)
        r=sorted(((sc,pred,ti,o,v,ta,tb) for pred,(sc,ti,o,v,ta,tb) in best.items()),reverse=True)
        tl,tr,_,_=diff(e.before,e.after);true_b=len(e.before)-tr
        md=min((boundary_distance(x[5],x[6],tl,true_b) for x in r),default=999)
        if len(r)>1 and r[0][0]-r[1][0]<.5:return e.before,False,len(r),[(x[3],x[4]) for x in r],md
        return r[0][1],True,len(r),[(x[3],x[4]) for x in r],md

def evalm(m,test):
    t=time.perf_counter();c=w=k=rec=cands=0;dists=[]
    for e in test:
        p,d,n,pairs,bd=m.predict(e);k+=d;c+=d and p==e.after;w+=d and p!=e.after;cands+=n;dists.append(bd)
        rec+=any(o==e.obj and v==e.new for o,v in pairs)
    n=len(test)
    return {'accuracy':c/n,'wrong_commit':w/n,'commit_rate':k/n,'pair_recall':rec/n,'mean_candidates':cands/n,
            'mean_boundary_distance':statistics.mean(dists),'programs':m.stats['programs'],'probes':m.stats['probes'],
            'symbols':m.stats['symbols'],'symbol_members':m.stats['symbol_members'],'repairs':m.stats['repairs'],
            'repair_rules':m.stats['repair_rules'],'description_bits':m.bits,'model_bytes':len(pickle.dumps(m)),
            'training_seconds':m.train_s,'inference_ms':(time.perf_counter()-t)*1000/n}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='MEASUREMENTS_CYCLE_032.json');a=ap.parse_args()
    modes=['seen','order','lexeme','rename','alternate','nested','omitted','paragraph'];raw={}
    for seed in (1,7,19):
        alltr=build(seed,288,'seen');ind=alltr[:190];pool=alltr[190:];models={}
        for mode in ('graph','symbol','repair','shuffle_repair'):
            m=Model(mode,16);m.fit(ind,pool,shuffle=(mode=='shuffle_repair'));models[mode]=m
        raw[str(seed)]={mode:{k:evalm(v,build(seed+999,24,mode)) for k,v in models.items()} for mode in modes}
    summary={mode:{method:{k:statistics.mean(raw[str(seed)][mode][method][k] for seed in (1,7,19)) for k in raw['1'][mode][method]}
                   for method in ('graph','symbol','repair','shuffle_repair')} for mode in modes}
    payload={'cycle':32,'hypothesis':'Probe-Driven Symbol Refinement by Counterexample Boundary Repair','raw':raw,'summary':summary,
      'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      'estimated_complexity':'program induction O(NKoKv), probe response O(VT), near-miss repair O(VHL^2), inference O(TL^2+TR)',
      'final_test_outcome_used':False,'probe_pool_independent':True,'fixed_ontology_or_handwritten_slots_used_by_model':False,
      'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
