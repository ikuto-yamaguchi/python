"""Track B Cycle 017: reversible multi-view factor codes with held-out reconstruction.

Controlled falsification experiment. Learner receives only raw Japanese
before/command/after strings. Hidden object/field/value labels are evaluator-only.
No external LLM, RAG, morphology, fixed ontology, handwritten slots, or task branches.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵","試料甲","試料乙"]
FIELDS=["置き場所","状態","担当"]
VALUES={"置き場所":["棚A","棚B","棚C","棚D"],"状態":["待機","処理中","完了","保留"],"担当":["担当一","担当二","担当三","担当四"]}
STATE_FORMS=[
 "{o}の置き場所は{loc}。{o}の状態は{status}。{o}の担当は{owner}。",
 "{o}について、保管先={loc}／進行={status}／受持={owner}。",
]
COMMANDS={
 "置き場所":["{o}を{v}へ移してください。","{o}の保管先を{v}へ変更します。"],
 "状態":["{o}を{v}にしてください。","{o}の進行状態を{v}へ切り替えます。"],
 "担当":["{o}を{v}の担当にしてください。","{o}の受け持ちを{v}へ変更します。"],
}
HELD_ORDER={"置き場所":["{v}へ移してください、対象は{o}です。"],"状態":["{v}扱いにしてください、対象は{o}です。"],"担当":["{v}へ引き継いでください、対象は{o}です。"]}
HELD_LEXEME={"置き場所":["対象{o}は次から{v}で保管。"],"状態":["対象{o}は以後{v}として運用。"],"担当":["対象{o}の受持を{v}へ。"]}
OMITTED={"置き場所":["それを{v}へ移してください。"],"状態":["その対象を{v}にしてください。"],"担当":["担当は{v}へ変えてください。"]}


def grams(s):
    s=''.join(s.split())
    return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))

def cosine(a,b):
    d=sum(v*b.get(k,0) for k,v in a.items());na=math.sqrt(sum(v*v for v in a.values()));nb=math.sqrt(sum(v*v for v in b.values()))
    return d/(na*nb+1e-12)

def norm_shape(s):
    out=[]
    for c in s:
        if c.isdigit() or (c.isascii() and c.isalpha()):out.append('A')
        elif c in '。、「」／=：, ':out.append(c)
        else:out.append('J')
    return ''.join(out)

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

def state(o,d,form=0):
    return STATE_FORMS[form].format(o=o,loc=d['置き場所'],status=d['状態'],owner=d['担当'])

@dataclass
class Episode:
    before:str;command:str;after:str;obj:str;field_name:str;value:str;focus:str|None

@dataclass
class Program:
    cmd_left:str;cmd_right:str;state_left:str;state_right:str;source:str
    support:int=1;score:float=0.0;views:tuple=();aliases:set[str]=field(default_factory=set)
    def cost(self):return len(self.cmd_left)+len(self.cmd_right)+len(self.state_left)+len(self.state_right)+8

class Learner:
    def __init__(self,mode,cap=32):
        self.mode=mode;self.cap=cap;self.programs=[];self.raw=0;self.rejected=0;self.merges=0;self.factor_groups=0

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
        ms=[];pos=0
        while True:
            i=st.find(p.state_left,pos) if p.state_left else pos
            if i<0:break
            a=i+len(p.state_left);b=st.find(p.state_right,a) if p.state_right else len(st)
            if b>=a:ms.append((a,b))
            pos=i+1
            if not p.state_left or pos>=len(st):break
        if len(ms)!=1:return st,False,len(ms)
        a,b=ms[0];return st[:a]+v+st[b:],True,1

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

    def view_code(self,p,episodes):
        cmd_shape=(norm_shape(p.cmd_left[-8:]),norm_shape(p.cmd_right[:8]))
        state_shape=(norm_shape(p.state_left[-8:]),norm_shape(p.state_right[:8]))
        preserve=[];transport=[]
        for e in episodes[-24:]:
            out,ok,amb=self.execute(e.before,e.command,p)
            preserve.append((int(ok),int(amb==1),int(ok and len(out)==len(e.after))))
            transport.append((int(ok),int(out==e.after),round(cosine(grams(out),grams(e.after)),2)))
        pres=tuple(sum(x[i] for x in preserve) for i in range(3))
        trans=tuple(sum(x[i] for x in transport) if i<2 else round(sum(x[i] for x in transport),2) for i in range(3))
        return (cmd_shape,state_shape,pres,trans)

    def heldout_predictability(self,candidates):
        predictable=[defaultdict(set) for _ in range(4)]
        for p in candidates:
            for i in range(4):
                key=tuple(v for j,v in enumerate(p.views) if j!=i)
                predictable[i][key].add(p.views[i])
        scores={}
        for p in candidates:
            good=0
            for i in range(4):
                key=tuple(v for j,v in enumerate(p.views) if j!=i)
                good+=int(len(predictable[i][key])==1)
            scores[id(p)]=good/4
        return scores

    def learn(self,episodes):
        accepted=[]
        for e in episodes:
            ps=self.propose(e);self.raw+=len(ps)
            for p in ps:
                o,ok,amb=self.execute(e.before,e.command,p)
                if not ok or amb!=1 or o!=e.after:
                    self.rejected+=1;continue
                p.score=5-0.015*p.cost();p.aliases.add(p.cmd_left+'|'+p.cmd_right);accepted.append(p)
        unique={}
        for p in accepted:
            k=(p.cmd_left,p.cmd_right,p.state_left,p.state_right)
            if k not in unique:unique[k]=p
            else:unique[k].support+=1
        candidates=sorted(unique.values(),key=lambda p:(p.support,p.score),reverse=True)[:64]
        if self.mode=='executable':
            self.programs=candidates[:self.cap];return
        for p in candidates:p.views=self.view_code(p,episodes)
        if self.mode=='surface_mdl':
            groups={}
            for p in candidates:
                k=(p.views[0],p.views[1])
                cur=groups.get(k)
                if cur is None or p.cost()<cur.cost():groups[k]=p
                else:self.merges+=1
            self.programs=sorted(groups.values(),key=lambda p:(p.support,p.score),reverse=True)[:self.cap];return
        pred=self.heldout_predictability(candidates)
        groups={}
        for p in candidates:
            factor=(p.views[2],p.views[3])
            if pred[id(p)]<1.0:
                factor=('unresolved',id(p))
            cur=groups.get(factor)
            if cur is None:
                groups[factor]=p
            else:
                self.merges+=1
                cur.support+=p.support;cur.aliases|=p.aliases
                if p.cost()<cur.cost():groups[factor]=p
        self.factor_groups=len(groups)
        self.programs=sorted(groups.values(),key=lambda p:(p.support,p.score),reverse=True)[:self.cap]

    def infer(self,before,command):
        cand=[]
        for p in self.programs:
            o,ok,amb=self.execute(before,command,p)
            if ok and amb==1:
                s=cosine(grams(command),grams(p.cmd_left+p.cmd_right))+0.05*math.log1p(p.support)
                cand.append((s,o))
        if not cand:return before,False,0
        cand.sort(reverse=True,key=lambda x:x[0]);return cand[0][1],True,len(cand)

def build(seed,n,mode):
    rng=random.Random(seed);world={};eps=[];focus=None
    for _ in range(n):
        o=rng.choice(OBJECTS)
        if o not in world:world[o]={f:rng.choice(VALUES[f]) for f in FIELDS}
        f=rng.choice(FIELDS);v=rng.choice([x for x in VALUES[f] if x!=world[o][f]])
        form=1 if mode=='alternate' else 0;before=state(o,world[o],form)
        forms=HELD_ORDER[f] if mode=='held_order' else HELD_LEXEME[f] if mode=='held_lexeme' else OMITTED[f] if mode=='omitted' else COMMANDS[f]
        cmd=rng.choice(forms).format(o=o,v=v);world[o][f]=v;after=state(o,world[o],form)
        if mode=='nested':cmd='確認ですが、「'+cmd+'」という依頼です。'
        if mode=='freeform':cmd='前段の説明を踏まえます。\n'+cmd+'\nただし他の記録は維持してください。'
        eps.append(Episode(before,cmd,after,o,f,v,focus));focus=o
    return eps

def evaluate(seed,n,mode):
    train=build(seed,n,'seen');test=build(seed+10000,120,mode);out={}
    for m in ('executable','surface_mdl','multiview_factor'):
        L=Learner(m);t=time.perf_counter();L.learn(train);train_s=time.perf_counter()-t
        c=reads=0;t=time.perf_counter()
        for e in test:
            p,_,r=L.infer(e.before,e.command);reads+=r;c+=int(p==e.after)
        out[m]={
          'accuracy':c/len(test),'model_bytes':len(pickle.dumps(L)),'training_seconds':train_s,
          'inference_ms':(time.perf_counter()-t)*1000/len(test),'programs':len(L.programs),
          'raw_candidates':L.raw,'rejected':L.rejected,'merges':L.merges,'factor_groups':L.factor_groups,
          'mean_read_candidates':reads/len(test)
        }
    return out

def summarize(raw):
    out={}
    for n,runs in raw.items():
        out[n]={}
        for mode in ('seen','held_order','held_lexeme','nested','omitted','alternate','freeform'):
            out[n][mode]={}
            for method in ('executable','surface_mdl','multiview_factor'):
                keys=runs[0][mode][method]
                out[n][mode][method]={k:statistics.mean(r[mode][method][k] for r in runs) for k in keys}
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_017.json');a=ap.parse_args()
    raw={}
    for n in (48,144,432):
        runs=[]
        for seed in (1,7,19):
            runs.append({mode:evaluate(seed,n,mode) for mode in ('seen','held_order','held_lexeme','nested','omitted','alternate','freeform')})
        raw[str(n)]=runs
    payload={
      'hypothesis':'Reversible Multi-View Factor Codes by Held-Out Reconstruction',
      'seeds':[1,7,19],'sizes':[48,144,432],'raw':raw,'summary':summarize(raw),
      'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      'estimated_complexity':'proposal O(NC^2), view coding O(PW), held-out reconstruction O(PV), inference O(PL)',
      'hidden_labels_used_by_learner':False,'highschool_level_passed':False,
      'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False
    }
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload['summary']['432'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
