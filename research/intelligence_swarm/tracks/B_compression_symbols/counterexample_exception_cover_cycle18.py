"""Track B Cycle 018: counterexample-coded program symbols by minimum exception cover.

Controlled falsification experiment. Learner receives only raw Japanese
before/command/after strings. Hidden object/field/value labels are evaluator-only.
No external LLM, RAG, morphology, fixed ontology, handwritten slots,
task-specific inference branches, or answer leakage.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
import argparse, json, math, pickle, random, resource, statistics, time

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
def split_clauses(text):
    cuts=[0]
    for i,ch in enumerate(text):
        if ch in '。\n／':cuts.append(i+1)
    if cuts[-1]!=len(text):cuts.append(len(text))
    return [(a,b,text[a:b]) for a,b in zip(cuts,cuts[1:]) if text[a:b].strip()][:12]
def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def contexts(text,token,radius=10):
    out=[];pos=0
    while token:
        i=text.find(token,pos)
        if i<0:break
        out.append((text[max(0,i-radius):i],text[i+len(token):i+len(token)+radius]));pos=i+1
    return out[:4]
def state(o,d,form=0):return STATE_FORMS[form].format(o=o,loc=d['置き場所'],status=d['状態'],owner=d['担当'])

@dataclass
class Episode:
    before:str;command:str;after:str;obj:str;field_name:str;value:str;focus:str|None
@dataclass
class Program:
    cmd_left:str;cmd_right:str;state_left:str;state_right:str;source:str
    support:int=1;success:tuple[int,...]=();wrong:tuple[int,...]=();noexec:tuple[int,...]=();exception_indices:tuple[int,...]=()
    def structural_bits(self):return 8*(len(self.cmd_left)+len(self.cmd_right)+len(self.state_left)+len(self.state_right)+8)

class Learner:
    def __init__(self,mode,cap=32):
        self.mode=mode;self.cap=cap;self.programs=[];self.raw=0;self.rejected=0;self.merges=0;self.exception_bits=0.;self.description_bits=0.;self.covered=0
    def extract(self,cmd,p):
        starts=[0] if not p.cmd_left else []
        if p.cmd_left:
            pos=0
            while True:
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
        matches=[];pos=0
        while True:
            i=st.find(p.state_left,pos) if p.state_left else pos
            if i<0:break
            a=i+len(p.state_left);b=st.find(p.state_right,a) if p.state_right else len(st)
            if b>=a:matches.append((a,b))
            pos=i+1
            if not p.state_left or pos>=len(st):break
        if len(matches)!=1:return st,False,len(matches)
        a,b=matches[0];return st[:a]+v+st[b:],True,1
    def propose(self,e):
        out=[]
        for _,_,bc in split_clauses(e.before):
            for _,_,ac in split_clauses(e.after):
                l,r,old,new=diff(bc,ac)
                if not new or len(new)>14 or bc==ac:continue
                for cl,cr in contexts(e.command,new):
                    out.append(Program(cl,cr,bc[:l],bc[len(bc)-r:] if r else '',bc))
                    if len(out)>=96:return out
        return out
    def behavior(self,p,episodes):
        suc=[];wrong=[];no=[]
        for i,e in enumerate(episodes):
            out,ok,amb=self.execute(e.before,e.command,p)
            if not ok or amb!=1:no.append(i)
            elif out==e.after:suc.append(i)
            else:wrong.append(i)
        p.success=tuple(suc);p.wrong=tuple(wrong);p.noexec=tuple(no);return p
    def source_candidates(self,episodes):
        unique={}
        for e in episodes:
            ps=self.propose(e);self.raw+=len(ps)
            for p in ps:
                out,ok,amb=self.execute(e.before,e.command,p)
                if not ok or amb!=1 or out!=e.after:self.rejected+=1;continue
                k=(p.cmd_left,p.cmd_right,p.state_left,p.state_right)
                if k not in unique:unique[k]=p
                else:unique[k].support+=1
        return sorted((self.behavior(p,episodes) for p in unique.values()),key=lambda p:(len(p.success),p.support,-p.structural_bits()),reverse=True)[:64]
    def mdl_cost(self,p,n,include_wrong):
        idx=math.ceil(math.log2(max(2,n)));return p.structural_bits()+idx*((len(p.wrong) if include_wrong else 0)+max(1,len(p.success)))+16
    def learn(self,episodes):
        candidates=self.source_candidates(episodes);n=len(episodes)
        if self.mode=='executable':self.programs=candidates[:self.cap]
        elif self.mode=='success_mdl':
            groups={}
            for p in candidates:
                cur=groups.get(p.success)
                if cur is None or self.mdl_cost(p,n,False)<self.mdl_cost(cur,n,False):
                    if cur is not None:self.merges+=1
                    groups[p.success]=p
                else:self.merges+=1
            self.programs=sorted(groups.values(),key=lambda p:(len(p.success),-self.mdl_cost(p,n,False)),reverse=True)[:self.cap]
        else:
            uncovered=set(range(n));selected=[];literal=[8*(len(e.before)+len(e.command)+len(e.after)+4) for e in episodes]
            while uncovered and len(selected)<self.cap:
                best=None;gain0=0
                for p in candidates:
                    cover=uncovered.intersection(p.success)
                    if not cover:continue
                    cost=self.mdl_cost(p,n,True);gain=sum(literal[i] for i in cover)-cost-math.ceil(math.log2(max(2,n)))*len(p.wrong)
                    if gain>gain0:gain0=gain;best=(p,cover)
                if best is None:break
                p,cover=best;p.exception_indices=p.wrong;selected.append(p);uncovered-=cover;candidates.remove(p)
            self.programs=selected;self.covered=n-len(uncovered);idx=math.ceil(math.log2(max(2,n)));self.exception_bits=sum(len(p.exception_indices)*idx for p in selected);self.description_bits=sum(self.mdl_cost(p,n,True) for p in selected)+sum(literal[i] for i in uncovered)
        if self.mode!='exception_mdl':
            self.covered=len(set(i for p in self.programs for i in p.success));self.description_bits=sum(self.mdl_cost(p,n,False) for p in self.programs)
    def infer(self,before,command):
        cand=[]
        for p in self.programs:
            out,ok,amb=self.execute(before,command,p)
            if ok and amb==1:
                precision=len(p.success)/max(1,len(p.success)+len(p.wrong));score=cosine(grams(command),grams(p.cmd_left+p.cmd_right))+0.12*precision+0.03*math.log1p(p.support);cand.append((score,out))
        if not cand:return before,False,0
        cand.sort(reverse=True,key=lambda x:x[0])
        if len(cand)>1 and cand[0][0]-cand[1][0]<1e-9:return before,False,len(cand)
        return cand[0][1],True,len(cand)

def build(seed,n,mode):
    rng=random.Random(seed);world={};eps=[];focus=None
    for _ in range(n):
        o=rng.choice(OBJECTS)
        if o not in world:world[o]={f:rng.choice(VALUES[f]) for f in FIELDS}
        f=rng.choice(FIELDS);v=rng.choice([x for x in VALUES[f] if x!=world[o][f]]);form=1 if mode=='alternate' else 0;before=state(o,world[o],form)
        forms=HELD_ORDER[f] if mode=='held_order' else HELD_LEXEME[f] if mode=='held_lexeme' else OMITTED[f] if mode=='omitted' else COMMANDS[f]
        cmd=rng.choice(forms).format(o=o,v=v);world[o][f]=v;after=state(o,world[o],form)
        if mode=='nested':cmd='確認ですが、「'+cmd+'」という依頼です。'
        if mode=='freeform':cmd='前段の説明を踏まえます。\n'+cmd+'\nただし他の記録は維持してください。'
        eps.append(Episode(before,cmd,after,o,f,v,focus));focus=o
    return eps

def evaluate(seed,n,mode):
    train=build(seed,n,'seen');test=build(seed+10000,120,mode);out={}
    for m in ('executable','success_mdl','exception_mdl'):
        L=Learner(m);t=time.perf_counter();L.learn(train);train_s=time.perf_counter()-t;correct=wrong=commit=reads=recall=0;t=time.perf_counter()
        for e in test:
            exact=False
            for p in L.programs:
                pred,ok,amb=L.execute(e.before,e.command,p);exact|=bool(ok and amb==1 and pred==e.after)
            recall+=int(exact);pred,did,r=L.infer(e.before,e.command);reads+=r;commit+=int(did);correct+=int(pred==e.after and did);wrong+=int(did and pred!=e.after)
        out[m]={'accuracy':correct/len(test),'wrong_commit':wrong/len(test),'commit_rate':commit/len(test),'candidate_execution_recall':recall/len(test),'model_bytes':len(pickle.dumps(L)),'training_seconds':train_s,'inference_ms':(time.perf_counter()-t)*1000/len(test),'programs':len(L.programs),'raw_candidates':L.raw,'rejected':L.rejected,'merges':L.merges,'covered_train':L.covered,'description_bits':L.description_bits,'exception_bits':L.exception_bits,'mean_read_candidates':reads/len(test)}
    return out

def summarize(raw):
    out={}
    for n,runs in raw.items():
        out[n]={}
        for mode in ('seen','held_order','held_lexeme','nested','omitted','alternate','freeform'):
            out[n][mode]={}
            for method in ('executable','success_mdl','exception_mdl'):
                out[n][mode][method]={k:statistics.mean(r[mode][method][k] for r in runs) for k in runs[0][mode][method]}
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_018.json');a=ap.parse_args();raw={}
    for n in (48,144,432):
        raw[str(n)]=[{mode:evaluate(seed,n,mode) for mode in ('seen','held_order','held_lexeme','nested','omitted','alternate','freeform')} for seed in (1,7,19)]
    payload={'hypothesis':'Counterexample-Coded Program Symbols by Minimum Exception Cover','seeds':[1,7,19],'sizes':[48,144,432],'raw':raw,'summary':summarize(raw),'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'proposal O(NC^2), behavior O(PN), greedy cover O(KPN), inference O(PL); P<=64,K<=32','hidden_labels_used_by_learner':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload['summary']['432'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
