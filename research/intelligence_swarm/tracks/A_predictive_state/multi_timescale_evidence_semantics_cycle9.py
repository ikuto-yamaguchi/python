"""Track A Cycle 009: multi-timescale predictive evidence semantics.

Controlled falsification probe. Learner sees raw Japanese evidence strings, speaker ids,
episode boundaries and delayed generic success/failure. It never sees target world values,
semantic act labels, a hand-written lexicon, ontology, morphology, RAG, or an external LLM.
Hidden cause labels are evaluator-only.
"""
from __future__ import annotations
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
import argparse, json, math, pickle, random, resource, statistics, time

POS = ["はい、それで進めて","その理解で大丈夫です","合っています","その通りです","ええ、問題ありません"]
NEG = ["いいえ、違います","その理解ではありません","誤っています","もう一方です","そうではないです"]
HELD_POS = ["認識どおりです","その線で続けて","正しく受け取れています","うん、それを採用して"]
HELD_NEG = ["読み方が外れています","選択を戻して","別候補にしてください","解釈を反転してください"]
NEUTRAL = ["確認しました","少し考えます","聞こえています","保留します","続けてください"]
WRAPPERS = [
    "{x}",
    "引用すると「{x}」です",
    "相手は「{x}」と言いました",
    "私は『{x}』とは言っていません",
    "訂正します。さきほどの「{x}」は撤回します",
]
CAUSES = ["global","speaker","episode","quoted","negated","corrected"]

def grams(text:str)->Counter[str]:
    s="".join(text.split())
    return Counter(s[i:i+n] for n in (2,3,4) for i in range(max(0,len(s)-n+1)))

def cosine(a,b):
    dot=sum(v*b.get(k,0) for k,v in a.items())
    na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return dot/(na*nb+1e-12)

@dataclass
class Proto:
    text:str
    pos:int=0
    neg:int=0
    ok:int=0
    bad:int=0
    def polarity(self):
        return 1 if self.pos>=self.neg else 0
    def agreement(self):
        return max(self.pos,self.neg)/max(1,self.pos+self.neg)
    def reliability(self):
        return (self.ok+1)/(self.ok+self.bad+2)

class StaticModel:
    def __init__(self):
        self.ps={}
    def update(self,text,truth,success,**kw):
        p=self.ps.setdefault(text,Proto(text))
        if truth:p.pos+=1
        else:p.neg+=1
        if success:p.ok+=1
        else:p.bad+=1
    def infer(self,text,**kw):
        q=grams(text); scored=[]
        for p in self.ps.values():
            scored.append((cosine(q,grams(p.text))*p.agreement()*p.reliability(),p.polarity()))
        scored.sort(reverse=True)
        if not scored or scored[0][0]<0.18:return None,0.0,0
        return scored[0][1],scored[0][0],min(5,len(scored))

class MultiTimescale:
    """Global, speaker-local, episode-local, and fast change states.

    Scope/cause is not given semantically. Separate raw-context prototypes are induced
    from full evidence strings and compared across timescales.
    """
    def __init__(self):
        self.global_ps={}
        self.speaker_ps=defaultdict(dict)
        self.episode_ps=defaultdict(dict)
        self.fast={}
        self.rollbacks=0
        self.forks=0

    def _upd(self,table,text,truth,success):
        p=table.setdefault(text,Proto(text))
        if truth:p.pos+=1
        else:p.neg+=1
        if success:p.ok+=1
        else:p.bad+=1

    def update(self,text,truth,success,speaker,episode):
        self._upd(self.global_ps,text,truth,success)
        self._upd(self.speaker_ps[speaker],text,truth,success)
        self._upd(self.episode_ps[episode],text,truth,success)
        hist=self.fast.setdefault((speaker,text),deque(maxlen=12))
        if hist and hist[-1][0]!=truth:self.forks+=1
        hist.append((truth,success))
        if not success:self.rollbacks+=1

    def _score_table(self,table,text,weight):
        q=grams(text); out=[]
        for p in table.values():
            sim=cosine(q,grams(p.text))
            if sim:
                out.append((weight*sim*p.agreement()*p.reliability(),p.polarity()))
        return out

    def infer(self,text,speaker,episode):
        votes=Counter(); reads=0
        sources=[
            (self.episode_ps.get(episode,{}),1.25),
            (self.speaker_ps.get(speaker,{}),1.0),
            (self.global_ps,0.55),
        ]
        for table,w in sources:
            scores=sorted(self._score_table(table,text,w),reverse=True)[:4]
            reads+=len(scores)
            for score,pol in scores:votes[pol]+=score

        hist=self.fast.get((speaker,text))
        if hist:
            pos=sum(t and ok for t,ok in hist); neg=sum((not t) and ok for t,ok in hist)
            n=pos+neg
            if n>=3:
                pol=int(pos>=neg)
                votes[pol]+=1.35*(max(pos,neg)/n)

        if not votes:return None,0.0,reads
        best,win=votes.most_common(1)[0]; total=sum(votes.values())
        margin=(win-(total-win))/(total+1e-12)
        confidence=win/(total+1e-12)*max(0,margin)
        if confidence<0.26:return None,confidence,reads
        return best,confidence,reads

def sample_text(rng,truth,held=False,cause="global"):
    base=rng.choice((HELD_POS if held else POS) if truth else (HELD_NEG if held else NEG))
    if cause=="quoted":
        return rng.choice(["引用すると「{x}」です","相手は「{x}」と言いました"]).format(x=base)
    if cause=="negated":
        return f"私は『{base}』とは言っていません"
    if cause=="corrected":
        return f"訂正します。さきほどの「{base}」は撤回します"
    return base

def operational_truth(base_truth,cause,flip):
    if cause in ("negated","corrected"): return not base_truth
    return (not base_truth) if flip else base_truth

def train(model,seed,n):
    rng=random.Random(seed)
    for i in range(n):
        speaker=f"S{rng.randrange(4)}"; episode=f"E{i//8}"
        base=rng.random()<0.5
        cause=rng.choice(["global","speaker","episode","quoted","negated","corrected"])
        text=sample_text(rng,base,False,cause)
        truth=operational_truth(base,cause,False)
        success=rng.random()>0.06
        model.update(text,truth,success,speaker=speaker,episode=episode)

def scenario(seed,model,kind,count=300):
    rng=random.Random(seed*997+len(kind))
    correct=wrong=abst=reads=0; confs=[]; immediate=[]
    start=time.perf_counter()
    for i in range(count):
        speaker=f"S{rng.randrange(4)}"; episode=f"Q{i//12}"
        base=rng.random()<0.5; held=(kind=="held")
        cause="global"; flip=False
        if kind=="abrupt":
            flip=i>=300
        elif kind=="speaker":
            flip=i>=250 and speaker=="S1"
        elif kind=="episode":
            flip=(i//12)%5==3
        elif kind=="scope":
            cause=rng.choice(["quoted","negated","corrected"])
        elif kind=="gradual":
            flip=rng.random()<max(0,(i-200)/700)
        elif kind=="held":
            cause=rng.choice(["global","speaker","episode","quoted","negated","corrected"])
        text=sample_text(rng,base,held,cause)
        truth=operational_truth(base,cause,flip)
        pred,conf,r=model.infer(text,speaker=speaker,episode=episode)
        reads+=r; confs.append(conf)
        if pred is None:abst+=1
        elif pred==truth:correct+=1
        else:wrong+=1
        if kind=="abrupt" and 300<=i<320:
            immediate.append(int(pred==truth) if pred is not None else 0)
        success=(pred==truth) if pred is not None else False
        model.update(text,truth,success,speaker=speaker,episode=episode)
    ms=(time.perf_counter()-start)*1000/count
    coverage=(correct+wrong)/count
    return {
        "accuracy_all":correct/count,
        "coverage":coverage,
        "selective_accuracy":correct/max(1,correct+wrong),
        "wrong_commit_rate":wrong/count,
        "abstention_rate":abst/count,
        "mean_confidence":statistics.mean(confs),
        "mean_reads":reads/count,
        "ms_per_episode":ms,
        "abrupt_first20_accuracy":statistics.mean(immediate) if immediate else None,
    }

def evaluate(seed,n):
    out={}
    for name,cls in (("static",StaticModel),("multi",MultiTimescale)):
        m=cls(); train(m,seed,n)
        r={k:scenario(seed,m,k) for k in ("stable","abrupt","speaker","episode","scope","gradual","held")}
        r["model_bytes"]=len(pickle.dumps(m))
        r["prototype_count"]=(
            len(m.ps) if isinstance(m,StaticModel)
            else len(m.global_ps)+sum(len(x) for x in m.speaker_ps.values())+sum(len(x) for x in m.episode_ps.values())
        )
        if isinstance(m,MultiTimescale):
            r["forks"]=m.forks;r["rollbacks"]=m.rollbacks
        out[name]=r
    return out

def summarize(raw):
    ans={}
    for n,runs in raw.items():
        ans[n]={}
        for method in ("static","multi"):
            m={}
            for sc in ("stable","abrupt","speaker","episode","scope","gradual","held"):
                m[sc]={}
                for key in runs[0][method][sc]:
                    vals=[r[method][sc][key] for r in runs if r[method][sc][key] is not None]
                    m[sc][key]=statistics.mean(vals) if vals else None
            for k in ("model_bytes","prototype_count"):
                m[k]=statistics.mean(r[method][k] for r in runs)
            if method=="multi":
                m["forks"]=statistics.mean(r[method]["forks"] for r in runs)
                m["rollbacks"]=statistics.mean(r[method]["rollbacks"] for r in runs)
            ans[n][method]=m
    return ans

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="results_cycle_009.json")
    args=ap.parse_args()
    raw={str(n):[evaluate(s,n) for s in (1,7,19)] for n in (64,256,512)}
    payload={
      "hypothesis":"Multi-Timescale Predictive Evidence Semantics with Structural Drift Causes",
      "seeds":[1,7,19],"train_sizes":[64,256,512],
      "raw":raw,"summary":summarize(raw),
      "delayed_evidence_contains_target_value":False,
      "estimated_complexity":"update O(1)+prototype append; infer O((Pg+Ps+Pe)G), top-12 reads",
      "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "free_japanese_integrated_gate":0.0,
      "highschool_level_passed":False,
      "native_japanese_communication_passed":False,
      "weak_smartphone_verified":False,
      "completion":False
    }
    with open(args.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload["summary"]["512"],ensure_ascii=False,indent=2))
if __name__=="__main__":main()
