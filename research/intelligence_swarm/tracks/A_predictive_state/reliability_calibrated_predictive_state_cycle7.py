"""Cycle A007: reliability-calibrated predictive states.

Controlled falsification probe. The learner receives raw Japanese feedback strings
and delayed generic interaction success/failure, never the hidden target value.
No pretrained model, morphology, semantic slots, fixed ontology, RAG, or LLM.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import argparse, json, math, pickle, random, resource, statistics, time

TRAIN_POS=["はい、その理解で大丈夫です","ええ、それで進めてください","合っています","その認識で問題ありません","そうです","その通りです"]
TRAIN_NEG=["いいえ、違います","その理解ではありません","誤っています","もう一方を検討してください","違うので戻してください","そうではないです"]
HELD_POS=["認識どおりで構いません","うん、それを採用して","正しく受け取れています","その線で続行してください"]
HELD_NEG=["解釈を反転してください","いや、選択を戻して","その読み方は外れです","別候補に切り替えてください"]
NONANSWER=["確認しました","少し考えます","続けてください","聞こえています","保留にします","なるほど"]
ADV_POS=["違いはありません","いいえ、ではなくはいです","そうではないとは限りません"]
ADV_NEG=["はい、でもその理解は違います","合ってはいません","そうだとは言っていません"]

def grams(text):
    text="".join(text.split()); out=Counter()
    for n in (2,3,4):
        for i in range(max(0,len(text)-n+1)): out[text[i:i+n]]+=1
    return out

def cosine(a,b):
    dot=sum(v*b.get(k,0) for k,v in a.items())
    return dot/(math.sqrt(sum(v*v for v in a.values()))*math.sqrt(sum(v*v for v in b.values()))+1e-12)

@dataclass
class Proto:
    text:str
    polarity:Counter=field(default_factory=Counter)
    success:int=0
    failure:int=0
    @property
    def support(self): return sum(self.polarity.values())
    @property
    def agreement(self): return max(self.polarity.values())/self.support if self.support else 0.0
    @property
    def reliability(self): return (self.success+1)/(self.success+self.failure+2)
    @property
    def label(self): return self.polarity.most_common(1)[0][0]

class Channel:
    def __init__(self,calibrated,min_conf=.30):
        self.calibrated=calibrated; self.min_conf=min_conf; self.protos=[]
    def observe(self,text,proposal_correct,downstream_success):
        p=next((x for x in self.protos if x.text==text),None)
        if p is None: p=Proto(text); self.protos.append(p)
        p.polarity[int(proposal_correct)]+=1
        if downstream_success:p.success+=1
        else:p.failure+=1
    def interpret(self,text):
        q=grams(text); scored=sorted(((cosine(q,grams(p.text)),p) for p in self.protos),reverse=True,key=lambda x:x[0])[:5]
        if not scored:return None,0.0,0
        votes=Counter(); total=0.0
        for sim,p in scored:
            w=sim*(p.reliability if self.calibrated else 1.0)*(p.agreement if self.calibrated else 1.0)
            votes[p.label]+=w; total+=w
        label,win=votes.most_common(1)[0]; runner=sum(votes.values())-win
        conf=scored[0][0]*(win-runner)/(total+1e-12)*min(1.0,sum(p.support for _,p in scored)/8)
        if self.calibrated and conf<self.min_conf:return None,conf,len(scored)
        return label,conf,len(scored)

@dataclass
class State:
    candidates:tuple
    ledger:list=field(default_factory=list)
    def update(self,yes_set,polarity,text):
        before=self.candidates
        self.candidates=tuple(c for c in before if (c in yes_set)==bool(polarity))
        self.ledger.append((text,before,polarity))
    def rollback(self):
        if self.ledger:self.candidates=self.ledger.pop()[1]

def train(seed,n,calibrated):
    rng=random.Random(seed); ch=Channel(calibrated)
    for _ in range(n):
        correct=rng.random()<.5; text=rng.choice(TRAIN_POS if correct else TRAIN_NEG)
        ch.observe(text,correct,rng.random()>=.08)
    return ch

def reply(rng,truth,mode,drift=False):
    if mode=="known": return rng.choice(TRAIN_POS if truth else TRAIN_NEG)
    if mode=="held": return rng.choice(HELD_POS if truth else HELD_NEG)
    if mode=="nonanswer": return rng.choice(NONANSWER)
    if mode=="adversarial": return rng.choice(ADV_POS if truth else ADV_NEG)
    if mode=="drift": return rng.choice(TRAIN_NEG if truth else TRAIN_POS) if drift else rng.choice(TRAIN_POS if truth else TRAIN_NEG)
    raise ValueError(mode)

def run_split(ch,seed,k,mode,count=240,drift=False,rollback=False):
    rng=random.Random(seed*1009+k*97+len(mode)); good=bad=abst=reads=turns=rolled=0; confs=[]
    start=time.perf_counter()
    for _ in range(count):
        target=rng.randrange(k); st=State(tuple(range(k)))
        for __ in range(math.ceil(math.log2(k))+2):
            if len(st.candidates)<=1:break
            ordered=list(st.candidates); yes=set(ordered[:max(1,len(ordered)//2)])
            text=reply(rng,target in yes,mode,drift); pol,conf,r=ch.interpret(text)
            reads+=r; turns+=1; confs.append(conf)
            if pol is None:break
            st.update(yes,pol,text)
        if len(st.candidates)==1:
            if st.candidates[0]==target:good+=1
            else:bad+=1
        else:abst+=1
        if rollback and st.ledger:
            expected=st.ledger[-1][1]; st.rollback(); rolled+=int(st.candidates==expected)
    elapsed=(time.perf_counter()-start)*1000/count; coverage=(good+bad)/count
    return {"accuracy_all":good/count,"coverage":coverage,"selective_accuracy":good/max(1,good+bad),"wrong_commit_rate":bad/count,"abstention_rate":abst/count,"mean_confidence":statistics.mean(confs) if confs else 0.0,"candidate_reads":reads/max(1,turns),"mean_turns":turns/count,"ms_per_dialogue":elapsed,"rollback_success":rolled/(count if rollback else 1)}

def evaluate(seed,n):
    out={}
    for name,cal in (("naive",False),("calibrated",True)):
        ch=train(seed,n,cal); m={}
        for k in (2,4,8):
            m[str(k)]={x:run_split(ch,seed,k,x,drift=(x=="drift")) for x in ("known","held","nonanswer","adversarial","drift")}
            m[str(k)]["reversible"]=run_split(ch,seed,k,"known",rollback=True)
        m["model_bytes"]=len(pickle.dumps(ch)); m["prototype_count"]=len(ch.protos); out[name]=m
    return out

def summarize(raw):
    out={}
    for n,runs in raw.items():
        out[n]={}
        for method in ("naive","calibrated"):
            m={}
            for k in ("2","4","8"):
                m[k]={}
                for mode in ("known","held","nonanswer","adversarial","drift","reversible"):
                    m[k][mode]={key:statistics.mean(r[method][k][mode][key] for r in runs) for key in runs[0][method][k][mode]}
            m["model_bytes"]=statistics.mean(r[method]["model_bytes"] for r in runs)
            m["prototype_count"]=statistics.mean(r[method]["prototype_count"] for r in runs)
            out[n][method]=m
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="results_cycle_007.json"); args=ap.parse_args()
    raw={str(n):[evaluate(seed,n) for seed in (1,7,19)] for n in (64,256,1024)}
    payload={"hypothesis":"Reliability-Calibrated Active Predictive States with Reversible Evidence Channels","seeds":[1,7,19],"train_sizes":[64,256,1024],"summary":summarize(raw),"delayed_evidence_contains_target_value":False,"estimated_complexity":"train O(NG); infer O(PG), top-5 sparse reads","peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"free_japanese_integrated_gate":0.0,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(args.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload["summary"]["1024"],ensure_ascii=False,indent=2))
if __name__=="__main__":main()
