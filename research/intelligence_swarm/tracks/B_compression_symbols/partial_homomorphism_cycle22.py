from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
import argparse,json,math,pickle,random,resource,statistics,time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
FIELDS=['置き場所','状態','担当']
VALUES={'置き場所':['棚A','棚B','棚C','棚D'],'状態':['待機','処理中','完了','保留'],'担当':['担当一','担当二','担当三','担当四']}
STATE_FORMS=['{o}の置き場所は{loc}。{o}の状態は{status}。{o}の担当は{owner}。','{o}について、保管先={loc}／進行={status}／受持={owner}。']
COMMANDS={'置き場所':['{o}を{v}へ移してください。','{o}の保管先を{v}へ変更します。'],'状態':['{o}を{v}にしてください。','{o}の進行状態を{v}へ切り替えます。'],'担当':['{o}を{v}の担当にしてください。','{o}の受け持ちを{v}へ変更します。']}
HELD_ORDER={'置き場所':['{v}へ移してください、対象は{o}です。'],'状態':['{v}扱いにしてください、対象は{o}です。'],'担当':['{v}へ引き継いでください、対象は{o}です。']}
HELD_LEXEME={'置き場所':['対象{o}は次から{v}で保管。'],'状態':['対象{o}は以後{v}として運用。'],'担当':['対象{o}の受持を{v}へ。']}
OMITTED={'置き場所':['それを{v}へ移してください。'],'状態':['その対象を{v}にしてください。'],'担当':['担当は{v}へ変えてください。']}

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

def clauses(t):
    out=[];s=0
    for i,c in enumerate(t):
        if c in '。\n／':
            if i+1>s: out.append(t[s:i+1])
            s=i+1
    if s<len(t): out.append(t[s:])
    return [x for x in out if x.strip()][:12]

def contexts(t,x,r=10):
    out=[];p=0
    while x:
        i=t.find(x,p)
        if i<0: break
        out.append((t[max(0,i-r):i],t[i+len(x):i+len(x)+r]));p=i+1
    return out[:4]

def shape(s):
    return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、／=\n ' else c for c in s)

def state(o,d,form=0): return STATE_FORMS[form].format(o=o,loc=d['置き場所'],status=d['状態'],owner=d['担当'])

@dataclass
class Episode:
    before:str;command:str;after:str;obj:str;field_name:str;value:str;focus:str|None

@dataclass
class Program:
    cl:str;cr:str;sl:str;sr:str;support:int=1
    success:tuple=();wrong:tuple=();noexec:tuple=();fillers:tuple=()
    def bits(self): return 8*(len(self.cl)+len(self.cr)+len(self.sl)+len(self.sr)+8)

@dataclass
class Relation:
    source:tuple;target:tuple;shared_success:int;heldout_score:float;wrong_rate:float;support:int;filler_map:tuple
    def bits(self): return 96+sum(8*len(x) for x in self.source+self.target)+sum(8*(len(a)+len(b)) for a,b in self.filler_map)

class Learner:
    def __init__(self,mode,cap=32):
        self.mode=mode;self.cap=cap;self.programs=[];self.relations=[];self.raw=0;self.rejected=0;self.merges=0;self.description_bits=0
    def extract(self,cmd,l,r):
        starts=[0] if not l else [];p=0
        while l:
            i=cmd.find(l,p)
            if i<0: break
            starts.append(i+len(l));p=i+1
        vals=[]
        for st in starts:
            en=cmd.find(r,st) if r else len(cmd)
            if en>=st and 0<en-st<=14: vals.append(cmd[st:en])
        return min(vals,key=len) if vals else None
    def execute_ctx(self,st,cmd,cl,cr,sl,sr):
        v=self.extract(cmd,cl,cr)
        if v is None:return st,False,0,None
        hits=[];p=0
        while True:
            i=st.find(sl,p) if sl else p
            if i<0:break
            a=i+len(sl);b=st.find(sr,a) if sr else len(st)
            if b>=a:hits.append((a,b))
            p=i+1
            if not sl or p>=len(st):break
        if len(hits)!=1:return st,False,len(hits),v
        a,b=hits[0];return st[:a]+v+st[b:],True,1,v
    def execute(self,e,p):return self.execute_ctx(e.before,e.command,p.cl,p.cr,p.sl,p.sr)
    def propose(self,e):
        out=[]
        for bc in clauses(e.before):
            for ac in clauses(e.after):
                l,r,old,new=diff(bc,ac)
                if not new or bc==ac or len(new)>14:continue
                for cl,cr in contexts(e.command,new):
                    out.append(Program(cl,cr,bc[:l],bc[len(bc)-r:] if r else ''))
                    if len(out)>=96:return out
        return out
    def behavior(self,p,eps):
        s=[];w=[];n=[];f=[]
        for i,e in enumerate(eps):
            out,ok,amb,v=self.execute(e,p)
            if ok and amb==1:f.append(v)
            (n if not ok or amb!=1 else s if out==e.after else w).append(i)
        p.success=tuple(s);p.wrong=tuple(w);p.noexec=tuple(n);p.fillers=tuple(sorted(set(x for x in f if x)));return p
    def candidates(self,eps):
        u={}
        for e in eps:
            ps=self.propose(e);self.raw+=len(ps)
            for p in ps:
                out,ok,amb,_=self.execute(e,p)
                if not ok or amb!=1 or out!=e.after:self.rejected+=1;continue
                k=(p.cl,p.cr,p.sl,p.sr)
                if k in u:u[k].support+=1
                else:u[k]=p
        return sorted((self.behavior(p,eps) for p in u.values()),key=lambda p:(len(p.success),p.support,-p.bits()),reverse=True)[:64]
    def relation_candidate(self,a,b,eps):
        both=[i for i in range(len(eps)) if i not in a.noexec and i not in b.noexec]
        if len(both)<2:return None
        shared=sum(i in a.success and i in b.success for i in both)
        wrong=sum((i in a.wrong) or (i in b.wrong) for i in both)
        odd=[i for i in both if i%2];even=[i for i in both if i%2==0]
        if not odd or not even:return None
        os=sum((i in a.success)==(i in b.success) for i in odd)/len(odd)
        es=sum((i in a.success)==(i in b.success) for i in even)/len(even)
        held=min(os,es);wr=wrong/len(both)
        compatible=(shape(a.sl),shape(a.sr))==(shape(b.sl),shape(b.sr))
        if shared<2 or held<.65 or wr>.35 or not compatible:return None
        fmap=tuple(sorted(set(zip(a.fillers,b.fillers))))[:8]
        return Relation((a.cl,a.cr,a.sl,a.sr),(b.cl,b.cr,b.sl,b.sr),shared,held,wr,len(both),fmap)
    def learn(self,eps):
        ps=self.candidates(eps)
        if self.mode=='executable':self.programs=ps[:self.cap]
        elif self.mode=='strict':
            buckets=defaultdict(list)
            for p in ps:buckets[(p.success,p.wrong,p.noexec,shape(p.sl),shape(p.sr))].append(p)
            self.merges=sum(max(0,len(g)-1) for g in buckets.values());self.programs=ps[:self.cap]
        else:
            rel=[]
            for i,a in enumerate(ps):
                for b in ps[i+1:]:
                    r=self.relation_candidate(a,b,eps)
                    if r:rel.append(r)
            rel.sort(key=lambda r:(r.heldout_score,r.shared_success,-r.wrong_rate,r.support),reverse=True)
            self.relations=rel[:self.cap];self.programs=ps[:self.cap]
        self.description_bits=sum(p.bits()+16 for p in self.programs)+sum(r.bits() for r in self.relations)
    def infer(self,before,command):
        cand=[]
        for p in self.programs:
            out,ok,amb,_=self.execute_ctx(before,command,p.cl,p.cr,p.sl,p.sr)
            if ok and amb==1:cand.append((p.support,out))
        if self.mode=='partial':
            for r in self.relations:
                for ctx in (r.source,r.target):
                    out,ok,amb,_=self.execute_ctx(before,command,*ctx)
                    if ok and amb==1:cand.append((r.shared_success+2*r.heldout_score-2*r.wrong_rate,out))
        if not cand:return before,False,0
        by=defaultdict(float)
        for score,out in cand:by[out]=max(by[out],score)
        ranked=sorted(((score,out) for out,score in by.items()),reverse=True)
        if len(ranked)>1 and abs(ranked[0][0]-ranked[1][0])<1e-9:return before,False,len(ranked)
        return ranked[0][1],True,len(ranked)

def build(seed,n,mode):
    rng=random.Random(seed);world={};eps=[];focus=None
    for _ in range(n):
        o=rng.choice(OBJECTS);surf=ALIASES[o] if mode=='rename' else o
        world.setdefault(o,{f:rng.choice(VALUES[f]) for f in FIELDS})
        f=rng.choice(FIELDS);v=rng.choice([x for x in VALUES[f] if x!=world[o][f]]);form=1 if mode=='alternate' else 0
        before=state(surf,world[o],form)
        forms=HELD_ORDER[f] if mode=='held_order' else HELD_LEXEME[f] if mode in ('held_lexeme','rename') else OMITTED[f] if mode=='omitted' else COMMANDS[f]
        cmd=rng.choice(forms).format(o=surf,v=v);world[o][f]=v;after=state(surf,world[o],form)
        if mode=='nested':cmd='確認ですが、「'+cmd+'」という依頼です。'
        if mode=='freeform':cmd='前段の説明を踏まえます。\n'+cmd+'\nただし他の記録は維持してください。'
        eps.append(Episode(before,cmd,after,surf,f,v,focus));focus=surf
    return eps

def evaluate(seed,n,mode):
    train=build(seed,n,'seen');test=build(seed+10000,48,mode);res={}
    for m in ('executable','strict','partial'):
        L=Learner(m);t=time.perf_counter();L.learn(train);tr=time.perf_counter()-t
        correct=wrong=commit=recall=reads=0;t=time.perf_counter()
        for e in test:
            pred,did,r=L.infer(e.before,e.command);reads+=r;commit+=did
            correct+=int(did and pred==e.after);wrong+=int(did and pred!=e.after)
            recall+=int(any(L.execute(e,p)[1] and L.execute(e,p)[2]==1 and L.execute(e,p)[0]==e.after for p in L.programs))
        res[m]={'accuracy':correct/len(test),'wrong_commit':wrong/len(test),'commit_rate':commit/len(test),'candidate_execution_recall':recall/len(test),'model_bytes':len(pickle.dumps(L)),'training_seconds':tr,'inference_ms':(time.perf_counter()-t)*1000/len(test),'programs':len(L.programs),'relations':len(L.relations),'raw_candidates':L.raw,'rejected':L.rejected,'merges':L.merges,'description_bits':L.description_bits,'mean_read_candidates':reads/len(test)}
    return res

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_022.json');a=ap.parse_args()
    modes=['seen','held_order','held_lexeme','rename','nested','omitted','alternate','freeform'];raw={}
    for n in (48,144,288):raw[str(n)]=[{mode:evaluate(seed,n,mode) for mode in modes} for seed in (1,7,19)]
    summary={}
    for n,runs in raw.items():
        summary[n]={}
        for mode in modes:
            summary[n][mode]={}
            for method in ('executable','strict','partial'):
                keys=runs[0][mode][method];summary[n][mode][method]={k:statistics.mean(r[mode][method][k] for r in runs) for k in keys}
    payload={'hypothesis':'Open-Transport Context Relations from Partial Derivation Homomorphisms','seeds':[1,7,19],'sizes':[48,144,288],'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'proposal O(NC^2), behavior O(PN), relation O(P^2N), inference O((P+R)L)','hidden_labels_used_by_learner':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary['288'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
