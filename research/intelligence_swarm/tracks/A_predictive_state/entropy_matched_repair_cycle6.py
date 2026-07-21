"""Series A Cycle 006: entropy-matched multi-turn predictive repair.

Candidate futures are assumed to exist. The probe asks surface-derived yes/no
questions that maximize expected entropy reduction. No semantic slots,
ontology, pretrained model, RAG, or external LLM are used.
"""
from collections import Counter, defaultdict
import argparse, json, math, pickle, random, resource, statistics, time

KNOWN_YES=["はい","そうです","その側です","含まれます"]
KNOWN_NO=["いいえ","違います","その側ではありません","含まれません"]
HELD_YES=["ええ、そのまとまりです","そちらに入っています","肯定です"]
HELD_NO=["いや、反対側です","そちらには入りません","否定です"]
OTHER=["了解しました","確認しました","続けてください","考え中です"]
TOKENS=["棚","箱","部屋","机","廊下","東","西","上","下","A","B","C","D","一","二","三","四"]

def grams(s):
    return Counter(s[i:i+n] for n in (1,2,3) for i in range(max(0,len(s)-n+1)))

def cosine(a,b):
    dot=sum(v*b.get(k,0) for k,v in a.items())
    na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return dot/(na*nb+1e-12)

class FeedbackActs:
    def __init__(self): self.patterns=defaultdict(Counter)
    def fit(self,rng,n):
        for _ in range(n):
            self.patterns[rng.choice(KNOWN_YES)]["yes"]+=1
            self.patterns[rng.choice(KNOWN_NO)]["no"]+=1
            self.patterns[rng.choice(OTHER)]["other"]+=1
        return self
    def parse(self,u):
        q=grams(u); scored=[]
        for p,counts in self.patterns.items():
            sim=cosine(q,grams(p)); total=sum(counts.values())
            scored += [(sim*c/total,a) for a,c in counts.items()]
        scored.sort(reverse=True)
        if not scored: return None
        top=scored[0]; second=scored[1] if len(scored)>1 else (0,None)
        if top[0]<0.16 or top[0]-second[0]<0.02 or top[1]=="other": return None
        return top[1]

def entropy(n): return math.log2(n) if n else 0.0

def features(v):
    return {v[i:i+n] for n in (1,2) for i in range(len(v)-n+1)}

def best_partition(values,active):
    h0=entropy(len(active)); best=None
    for f in set().union(*(features(values[i]) for i in active)):
        yes={i for i in active if f in values[i]}; no=set(active)-yes
        if not yes or not no: continue
        rem=len(yes)/len(active)*entropy(len(yes))+len(no)/len(active)*entropy(len(no))
        key=(h0-rem,-abs(len(yes)-len(no)),-len(f),f)
        if best is None or key>best[0]: best=(key,yes,no,h0-rem)
    if best: return best[1:]
    order=sorted(active,key=lambda i:values[i]); m=len(order)//2
    yes=set(order[:m]); no=set(order[m:])
    return yes,no,h0-(len(yes)/len(active)*entropy(len(yes))+len(no)/len(active)*entropy(len(no)))

def make_value(rng,i): return rng.choice(TOKENS[:9])+rng.choice(TOKENS[9:])+str(i)

class Agent:
    def __init__(self,feedback): self.feedback=feedback
    def run(self,values,target,mode,rng,max_turns=8,cost=0.0):
        active=set(range(len(values))); turns=0; bits=0.0
        while len(active)>1 and turns<max_turns:
            yes,no,gain=best_partition(values,active)
            if gain<=cost: break
            truth="yes" if target in yes else "no"
            if mode=="known": u=rng.choice(KNOWN_YES if truth=="yes" else KNOWN_NO)
            elif mode=="held": u=rng.choice(HELD_YES if truth=="yes" else HELD_NO)
            elif mode=="uninformative": u=rng.choice(OTHER)
            else:
                if rng.random()<0.2: u=rng.choice(OTHER)
                else: u=rng.choice((KNOWN_YES+HELD_YES) if truth=="yes" else (KNOWN_NO+HELD_NO))
            act=self.feedback.parse(u); before=len(active)
            if act=="yes": active &= yes
            elif act=="no": active &= no
            bits += max(0,entropy(before)-entropy(len(active))); turns+=1
            if act is None: break
        pred=next(iter(active)) if len(active)==1 else None
        return pred==target,pred is None,turns,bits,len(active)

def evaluate(seed,n):
    rng=random.Random(seed); acts=FeedbackActs().fit(rng,n); agent=Agent(acts); out={}
    for k in (2,3,4,5,6,8):
        for mode in ("known","held","uninformative","mixed"):
            rows=[]; t=time.perf_counter()
            for rep in range(180):
                vals=[make_value(rng,rep*k+i) for i in range(k)]
                rows.append(agent.run(vals,rng.randrange(k),mode,rng,math.ceil(math.log2(k))+2))
            out[f"k{k}_{mode}"]={"accuracy":statistics.mean(x[0] for x in rows),"abstention":statistics.mean(x[1] for x in rows),"turns":statistics.mean(x[2] for x in rows),"acquired_bits":statistics.mean(x[3] for x in rows),"remaining":statistics.mean(x[4] for x in rows),"ms_per_dialogue":(time.perf_counter()-t)*1000/len(rows),"ideal_bits":math.log2(k)}
    for label,limit,cost in (("one_shot",1,0.0),("cost_aware",8,0.65)):
        rows=[]
        for rep in range(360):
            k=rng.choice((2,3,4,5,6,8)); vals=[make_value(rng,10000+rep*k+i) for i in range(k)]
            rows.append(agent.run(vals,rng.randrange(k),"known",rng,limit,cost))
        out[label]={"accuracy":statistics.mean(x[0] for x in rows),"abstention":statistics.mean(x[1] for x in rows),"turns":statistics.mean(x[2] for x in rows),"acquired_bits":statistics.mean(x[3] for x in rows)}
    out["model_bytes"]=len(pickle.dumps(acts)); out["feedback_patterns"]=len(acts.patterns)
    return out

def summarize(runs):
    out={}
    for key in runs[0]:
        if isinstance(runs[0][key],dict): out[key]={m:statistics.mean(r[key][m] for r in runs) for m in runs[0][key]}
        else: out[key]=statistics.mean(r[key] for r in runs)
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="results_cycle_006.json"); a=ap.parse_args()
    raw={str(n):[evaluate(s,n) for s in (1,7,19)] for n in (32,128,512)}
    payload={"hypothesis":"Entropy-Matched Multi-Turn Predictive Repair Programs","seeds":[1,7,19],"train_sizes":[32,128,512],"summary":{n:summarize(v) for n,v in raw.items()},"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"candidate_futures_given":True,"fixed_semantic_slots":False,"external_model":False,"free_japanese_integrated_gate":0.0,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(a.output,"w",encoding="utf-8") as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload["summary"]["512"],ensure_ascii=False,indent=2))
if __name__=="__main__": main()
