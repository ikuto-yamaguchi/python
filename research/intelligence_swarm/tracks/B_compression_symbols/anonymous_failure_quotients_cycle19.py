"""Track B Cycle 019: anonymous failure-cause quotients.

Learner input is raw Japanese before/command/after text only. Hidden object,
field and value labels are evaluator-only. No external model, RAG, morphology,
fixed ontology, handwritten slot parser, task branch or answer leakage.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
import argparse,json,math,pickle,random,resource,statistics,time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵","試料甲","試料乙"]
FIELDS=["置き場所","状態","担当"]
VALUES={"置き場所":["棚A","棚B","棚C","棚D"],"状態":["待機","処理中","完了","保留"],"担当":["担当一","担当二","担当三","担当四"]}
STATE_FORMS=["{o}の置き場所は{loc}。{o}の状態は{status}。{o}の担当は{owner}。","{o}について、保管先={loc}／進行={status}／受持={owner}。"]
COMMANDS={"置き場所":["{o}を{v}へ移してください。","{o}の保管先を{v}へ変更します。"],"状態":["{o}を{v}にしてください。","{o}の進行状態を{v}へ切り替えます。"],"担当":["{o}を{v}の担当にしてください。","{o}の受け持ちを{v}へ変更します。"]}
HELD_ORDER={"置き場所":["{v}へ移してください、対象は{o}です。"],"状態":["{v}扱いにしてください、対象は{o}です。"],"担当":["{v}へ引き継いでください、対象は{o}です。"]}
HELD_LEXEME={"置き場所":["対象{o}は次から{v}で保管。"],"状態":["対象{o}は以後{v}として運用。"],"担当":["対象{o}の受持を{v}へ。"]}
OMITTED={"置き場所":["それを{v}へ移してください。"],"状態":["その対象を{v}にしてください。"],"担当":["担当は{v}へ変えてください。"]}

def grams(s):
    s=''.join(s.split());return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))
def cosine(a,b):
    d=sum(v*b.get(k,0) for k,v in a.items());na=math.sqrt(sum(v*v for v in a.values()));nb=math.sqrt(sum(v*v for v in b.values()));return d/(na*nb+1e-12)
def clauses(t):
    c=[0]
    for i,x in enumerate(t):
        if x in '。\n／':c.append(i+1)
    if c[-1]!=len(t):c.append(len(t))
    return [t[a:b] for a,b in zip(c,c[1:]) if t[a:b].strip()][:12]
def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def contexts(t,x,radius=10):
    out=[];p=0
    while x:
        i=t.find(x,p)
        if i<0:break
        out.append((t[max(0,i-radius):i],t[i+len(x):i+len(x)+radius]));p=i+1
    return out[:4]
def state(o,d,form=0):return STATE_FORMS[form].format(o=o,loc=d['置き場所'],status=d['状態'],owner=d['担当'])

@dataclass
class Episode:
    before:str;command:str;after:str;obj:str;field_name:str;value:str;focus:str|None
@dataclass
class Program:
    cmd_left:str;cmd_right:str;state_left:str;state_right:str;source:str
    support:int=1;success:tuple[int,...]=();wrong:tuple[int,...]=();noexec:tuple[int,...]=();causes:tuple[tuple,...]=()
    def bits(self):return 8*(len(self.cmd_left)+len(self.cmd_right)+len(self.state_left)+len(self.state_right)+8)

class Learner:
    def __init__(self,mode,cap=32):
        self.mode=mode;self.cap=cap;self.programs=[];self.raw=0;self.rejected=0;self.description_bits=0.;self.cause_bits=0.;self.cause_count=0;self.merges=0
    def extract(self,cmd,p):
        starts=[0] if not p.cmd_left else [];pos=0
        while p.cmd_left:
            i=cmd.find(p.cmd_left,pos)
            if i<0:break
            starts.append(i+len(p.cmd_left));pos=i+1
        vals=[]
        for st in starts:
            en=cmd.find(p.cmd_right,st) if p.cmd_right else len(cmd)
            if en>=st and 0<en-st<=14:vals.append(cmd[st:en])
        return min(vals,key=len) if vals else None
    def execute(self,st,cmd,p):
        v=self.extract(cmd,p)
        if v is None:return st,False,0
        m=[];pos=0
        while True:
            i=st.find(p.state_left,pos) if p.state_left else pos
            if i<0:break
            a=i+len(p.state_left);b=st.find(p.state_right,a) if p.state_right else len(st)
            if b>=a:m.append((a,b))
            pos=i+1
            if not p.state_left or pos>=len(st):break
        if len(m)!=1:return st,False,len(m)
        a,b=m[0];return st[:a]+v+st[b:],True,1
    def propose(self,e):
        out=[]
        for bc in clauses(e.before):
            for ac in clauses(e.after):
                l,r,old,new=diff(bc,ac)
                if not new or len(new)>14 or bc==ac:continue
                for cl,cr in contexts(e.command,new):
                    out.append(Program(cl,cr,bc[:l],bc[len(bc)-r:] if r else '',bc))
                    if len(out)>=96:return out
        return out
    def vector(self,p,e):
        out,ok,amb=self.execute(e.before,e.command,p);old,new=diff(e.before,e.after)[2:];po,pn=diff(e.before,out)[2:]
        return (int(ok),min(3,amb),min(4,e.command.count(p.cmd_left) if p.cmd_left else 0),min(4,e.before.count(p.state_left) if p.state_left else 0),min(4,len(po)//4),min(4,len(pn)//4),min(4,abs(len(out)-len(e.after))//4),int(out==e.before),int(old==po),int(new==pn),int(cosine(grams(out),grams(e.after))>=.8))
    def behavior(self,p,episodes):
        s=[];w=[];n=[]
        for i,e in enumerate(episodes):
            out,ok,amb=self.execute(e.before,e.command,p)
            (n if not ok or amb!=1 else s if out==e.after else w).append(i)
        p.success=tuple(s);p.wrong=tuple(w);p.noexec=tuple(n);return p
    def candidates(self,episodes):
        u={}
        for e in episodes:
            ps=self.propose(e);self.raw+=len(ps)
            for p in ps:
                out,ok,amb=self.execute(e.before,e.command,p)
                if not ok or amb!=1 or out!=e.after:self.rejected+=1;continue
                k=(p.cmd_left,p.cmd_right,p.state_left,p.state_right)
                if k not in u:u[k]=p
                else:u[k].support+=1
        return sorted((self.behavior(p,episodes) for p in u.values()),key=lambda p:(len(p.success),p.support,-p.bits()),reverse=True)[:64]
    def causes(self,p,episodes):
        wrong=set(p.wrong)
        if not wrong:return ()
        vec={i:self.vector(p,episodes[i]) for i in wrong};succ=[self.vector(p,episodes[i]) for i in p.success];pred=[]
        for d in range(len(next(iter(vec.values())))):
            for val in sorted(set(v[d] for v in vec.values())):
                hit={i for i,v in vec.items() if v[d]==val}
                if hit and not any(v[d]==val for v in succ):pred.append(((d,val),hit))
        left=set(wrong);chosen=[]
        while left and len(chosen)<8:
            best=max(pred,key=lambda x:len(x[1]&left)/(1+.25*len(x[1])),default=None)
            if best is None or not best[1]&left:break
            chosen.append(best[0]);left-=best[1];pred=[x for x in pred if x[0]!=best[0]]
        return tuple(chosen) if not left else ()
    def cost(self,p,n,episode=False):
        idx=math.ceil(math.log2(max(2,n)));base=p.bits()+idx*max(1,len(p.success))+16
        return base+idx*len(p.wrong) if episode else base+14*len(p.causes)
    def learn(self,episodes):
        c=self.candidates(episodes);n=len(episodes)
        if self.mode in ('executable','episode_exception'):self.programs=c[:self.cap]
        else:
            for p in c:p.causes=self.causes(p,episodes)
            valid=[p for p in c if not p.wrong or p.causes];groups={}
            for p in valid:
                k=(p.success,p.causes);q=groups.get(k)
                if q is None or self.cost(p,n)<self.cost(q,n):
                    if q is not None:self.merges+=1
                    groups[k]=p
                else:self.merges+=1
            self.programs=sorted(groups.values(),key=lambda p:(len(p.success),-self.cost(p,n)),reverse=True)[:self.cap]
            self.cause_count=sum(len(p.causes) for p in self.programs);self.cause_bits=14*self.cause_count
        if self.mode=='executable':self.description_bits=sum(p.bits()+16 for p in self.programs)
        elif self.mode=='episode_exception':self.description_bits=sum(self.cost(p,n,True) for p in self.programs)
        else:self.description_bits=sum(self.cost(p,n) for p in self.programs)
    def infer(self,before,command):
        cand=[]
        for p in self.programs:
            out,ok,amb=self.execute(before,command,p)
            if not ok or amb!=1:continue
            pseudo=Episode(before,command,out,'','','',None);v=self.vector(p,pseudo)
            if self.mode=='anonymous_quotient' and any(v[d]==x for d,x in p.causes):continue
            precision=len(p.success)/max(1,len(p.success)+len(p.wrong));score=cosine(grams(command),grams(p.cmd_left+p.cmd_right))+.12*precision+.03*math.log1p(p.support);cand.append((score,out))
        if not cand:return before,False,0
        cand.sort(reverse=True,key=lambda x:x[0])
        if len(cand)>1 and abs(cand[0][0]-cand[1][0])<1e-9:return before,False,len(cand)
        return cand[0][1],True,len(cand)

def build(seed,n,mode):
    rng=random.Random(seed);world={};eps=[];focus=None
    for _ in range(n):
        o=rng.choice(OBJECTS);world.setdefault(o,{f:rng.choice(VALUES[f]) for f in FIELDS});f=rng.choice(FIELDS);v=rng.choice([x for x in VALUES[f] if x!=world[o][f]]);form=1 if mode=='alternate' else 0;before=state(o,world[o],form)
        forms=HELD_ORDER[f] if mode=='held_order' else HELD_LEXEME[f] if mode=='held_lexeme' else OMITTED[f] if mode=='omitted' else COMMANDS[f]
        cmd=rng.choice(forms).format(o=o,v=v);world[o][f]=v;after=state(o,world[o],form)
        if mode=='nested':cmd='確認ですが、「'+cmd+'」という依頼です。'
        if mode=='freeform':cmd='前段の説明を踏まえます。\n'+cmd+'\nただし他の記録は維持してください。'
        eps.append(Episode(before,cmd,after,o,f,v,focus));focus=o
    return eps

def evaluate(seed,n,mode):
    train=build(seed,n,'seen');test=build(seed+10000,120,mode);res={}
    for m in ('executable','episode_exception','anonymous_quotient'):
        L=Learner(m);t=time.perf_counter();L.learn(train);train_s=time.perf_counter()-t;correct=wrong=commit=reads=recall=0;t=time.perf_counter()
        for e in test:
            recall+=int(any(L.execute(e.before,e.command,p)[1] and L.execute(e.before,e.command,p)[2]==1 and L.execute(e.before,e.command,p)[0]==e.after for p in L.programs));pred,did,r=L.infer(e.before,e.command);reads+=r;commit+=int(did);correct+=int(did and pred==e.after);wrong+=int(did and pred!=e.after)
        res[m]={'accuracy':correct/len(test),'wrong_commit':wrong/len(test),'commit_rate':commit/len(test),'candidate_execution_recall':recall/len(test),'model_bytes':len(pickle.dumps(L)),'training_seconds':train_s,'inference_ms':(time.perf_counter()-t)*1000/len(test),'programs':len(L.programs),'raw_candidates':L.raw,'rejected':L.rejected,'merges':L.merges,'description_bits':L.description_bits,'cause_bits':L.cause_bits,'cause_count':L.cause_count,'mean_read_candidates':reads/len(test)}
    return res

def summarize(raw):
    out={}
    for n,runs in raw.items():
        out[n]={}
        for mode in ('seen','held_order','held_lexeme','nested','omitted','alternate','freeform'):
            out[n][mode]={}
            for method in ('executable','episode_exception','anonymous_quotient'):
                out[n][mode][method]={k:statistics.mean(r[mode][method][k] for r in runs) for k in runs[0][mode][method]}
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_019.json');a=ap.parse_args();raw={}
    for n in (48,144,432):raw[str(n)]=[{mode:evaluate(seed,n,mode) for mode in ('seen','held_order','held_lexeme','nested','omitted','alternate','freeform')} for seed in (1,7,19)]
    payload={'hypothesis':'Anonymous Failure-Cause Quotients from Minimal Counterexample Hitting Sets','seeds':[1,7,19],'sizes':[48,144,432],'raw':raw,'summary':summarize(raw),'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'proposal O(NC^2), behavior O(PN), predicate induction O(PND), greedy hitting O(PKW), inference O(PL)','hidden_labels_used_by_learner':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload['summary']['432'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
