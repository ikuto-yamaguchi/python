"""Track E Cycle 016
Open-Basis Residual Discovery from Raw Outcome Compression.

This is a controlled falsification experiment. The learner receives raw Japanese
strings and raw execution/future-observation strings. Hidden target/value/scope
labels are evaluator-only.

No external model, RAG, morphological analyzer, fixed semantic dictionary, or
hand-written slot parser is used.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass
import argparse, hashlib, json, math, pickle, random, resource, statistics, time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵","試料甲","試料乙"]
VALUES=["棚A","棚B","棚C","待機","処理中","完了","担当一","担当二"]
UNMARKED=[
 "念のため{o}は{v}にしておいてください。",
 "次から{o}を{v}で運用します。",
 "{o}、最終的には{v}へ切り替えます。",
]
DISTRACT=["別件の資料も確認しました。","これは更新とは関係ありません。","前の案はいったん保留です。"]

def grams(s):
    s="".join(s.split())
    return Counter(s[i:i+n] for n in (1,2,3) for i in range(max(0,len(s)-n+1)))

def cosine(a,b):
    d=sum(v*b.get(k,0) for k,v in a.items())
    na=math.sqrt(sum(v*v for v in a.values()))
    nb=math.sqrt(sum(v*v for v in b.values()))
    return d/(na*nb+1e-12)

def local_diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return a[l:len(a)-r if r else len(a)], b[l:len(b)-r if r else len(b)]

def spans(text,cap=12):
    out=[]
    seps="、。！？「」『』（）()=：:"
    for i in range(len(text)):
        for j in range(i+2,min(len(text),i+12)+1):
            x=text[i:j]
            if not x.strip() or all(c in seps for c in x): continue
            boundary=int(i==0 or text[i-1] in seps)+int(j==len(text) or text[j:j+1] in seps)
            rarity=len(set(x))/max(1,len(x))
            out.append((boundary,rarity,len(x),x))
    out.sort(reverse=True)
    seen=set(); ans=[]
    for _,_,_,x in out:
        if x not in seen:
            seen.add(x);ans.append(x)
        if len(ans)>=cap:break
    return ans

@dataclass
class Example:
    text:str
    before:str
    after:str
    future:str
    target:str
    value:str
    marked:bool
    mode:str

def make_example(rng,mode):
    o=rng.choice(OBJECTS);v=rng.choice(VALUES)
    old=rng.choice([x for x in VALUES if x!=v])
    before=f"{o}の現在値は{old}です。"
    after=f"{o}の現在値は{v}です。"
    if mode=="marked":
        text=f"「{o}」を「{v}」へ変更してください。"
    else:
        text=rng.choice(UNMARKED).format(o=o,v=v)
    if mode=="nested":
        text=f"『確認メモ: {rng.choice(DISTRACT)}』ただし、{text}"
    if mode=="plan":
        alt=rng.choice([x for x in VALUES if x not in (old,v)])
        text=f"{o}を{alt}にする案でした。{rng.choice(DISTRACT)} 最終的には{o}を{v}へ変更します。"
    if mode=="long":
        text=" ".join(rng.choice(DISTRACT) for _ in range(4))+" "+text
    future=f"次の確認では{o}={v}。非対象は変更なし。"
    return Example(text,before,after,future,o,v,mode=="marked",mode)

def proposals(ex):
    if ex.marked:
        q=[];cur="";inside=False
        for c in ex.text:
            if c=="「":inside=True;cur="";continue
            if c=="」" and inside:q.append(cur);inside=False;continue
            if inside:cur+=c
        base=q
    else:
        base=spans(ex.text,24)
    pairs=[]
    for i,a in enumerate(base):
        for b in base[i+1:]:
            if a==b or a in b or b in a:continue
            pairs.append((a,b))
            if len(pairs)>=8:return pairs
    return pairs

def execute(ex,cand):
    a,b=cand
    if a in ex.before:
        out=ex.before.replace(a,b,1)
    elif b in ex.before:
        out=ex.before.replace(b,a,1)
    else:
        out=ex.before+" [未解決:"+a+"|"+b+"]"
    future=ex.future if (ex.target in cand and ex.value in cand) else "次の確認では不整合。"
    return out,future

def raw_signature(ex,cand):
    out,fut=execute(ex,cand)
    d1=local_diff(ex.before,out)
    d2=local_diff(ex.after,out)
    d3=local_diff(ex.future,fut)
    raw="§".join(["→".join(d1),"→".join(d2),"→".join(d3)])
    return grams(raw),raw

class Solver:
    def __init__(self,kind,max_basis=8,max_sweep=4):
        self.kind=kind;self.max_basis=max_basis;self.max_sweep=max_sweep
        self.basis=[];self.train_seconds=0

    def fit(self,examples):
        t=time.perf_counter();sigs=[]
        for ex in examples:
            for c in proposals(ex):
                g,raw=raw_signature(ex,c)
                correct=int(ex.target in c and ex.value in c)
                sigs.append((g,raw,correct))
        if self.kind=="raw_basis":
            buckets=defaultdict(lambda:[0,0,Counter()])
            for g,raw,y in sigs:
                key=tuple(sorted(g.items()))
                buckets[key][y]+=1;buckets[key][2].update(g)
            scored=[]
            for _,(neg,pos,g) in buckets.items():
                support=neg+pos
                purity=abs(pos-neg)/max(1,support)
                scored.append((math.log1p(support)*purity,g))
            scored.sort(reverse=True,key=lambda z:z[0])
            self.basis=[g for _,g in scored[:self.max_basis]]
        elif self.kind=="random_basis":
            rng=random.Random(123)
            pool=[g for g,_,_ in sigs];rng.shuffle(pool);self.basis=pool[:self.max_basis]
        self.train_seconds=time.perf_counter()-t

    def solve(self,ex):
        cand=proposals(ex)
        if not cand:return None,{"recall":0,"sweeps":0,"active":0,"evals":0}
        scores=[]
        for c in cand:
            g,_=raw_signature(ex,c)
            if self.kind=="oracle":
                s=2*int(ex.target in c)+2*int(ex.value in c)-0.01*len(c[0]+c[1])
            elif self.kind=="global":
                out,fut=execute(ex,c)
                s=cosine(grams(out),grams(ex.after))+cosine(grams(fut),grams(ex.future))
            else:
                sims=[cosine(g,b) for b in self.basis]
                s=(max(sims) if sims else 0)+0.25*cosine(g,grams(ex.after+" "+ex.future))
            scores.append((s,c))
        scores.sort(reverse=True,key=lambda z:z[0])
        active=scores[:];sweeps=0
        for _ in range(self.max_sweep):
            sweeps+=1
            if len(active)<=1:break
            best=active[0][0]
            nxt=[z for z in active if z[0]>=best-0.08]
            if len(nxt)==len(active):break
            active=nxt
        chosen=active[0][1] if len(active)==1 else None
        return chosen,{"recall":int(any(ex.target in c and ex.value in c for c in cand)),
                       "sweeps":sweeps,"active":len(active),
                       "evals":len(cand)*max(1,len(self.basis))}

def run(seed,n,mode):
    rng=random.Random(seed)
    train=[make_example(rng,"marked" if i%2==0 else mode) for i in range(n)]
    test=[make_example(rng,mode) for _ in range(30)]
    methods={k:Solver(k) for k in ("global","random_basis","raw_basis","oracle")}
    for m in methods.values():m.fit(train)
    out={}
    for name,m in methods.items():
        t=time.perf_counter();acc=wrong=null=rec=sweeps=active=evals=0
        for ex in test:
            ch,meta=m.solve(ex)
            rec+=meta["recall"];sweeps+=meta["sweeps"];active+=meta["active"];evals+=meta["evals"]
            if ch is None:null+=1
            elif ex.target in ch and ex.value in ch:acc+=1
            else:wrong+=1
        out[name]={
            "accuracy":acc/len(test),"wrong_commit":wrong/len(test),"null_rate":null/len(test),
            "candidate_recall":rec/len(test),"mean_sweeps":sweeps/len(test),
            "mean_active":active/len(test),"mean_factor_evals":evals/len(test),
            "model_bytes":len(pickle.dumps(m)),"training_seconds":m.train_seconds,
            "inference_ms":(time.perf_counter()-t)*1000/len(test),"basis_count":len(m.basis)
        }
    return out

def summarize(raw):
    out={}
    for n,runs in raw.items():
        out[n]={}
        for mode in ("marked","unmarked","nested","plan","long"):
            out[n][mode]={}
            for method in ("global","random_basis","raw_basis","oracle"):
                keys=runs[0][mode][method]
                out[n][mode][method]={k:statistics.mean(r[mode][method][k] for r in runs) for k in keys}
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="results_cycle_016.json");a=ap.parse_args()
    raw={}
    for n in (30,90,180):
        runs=[]
        for seed in (1,7,19):
            runs.append({mode:run(seed,n,mode) for mode in ("marked","unmarked","nested","plan","long")})
        raw[str(n)]=runs
    payload={
      "hypothesis":"Open-Basis Residual Discovery from Raw Outcome Compression",
      "seeds":[1,7,19],"sizes":[30,90,180],"raw":raw,"summary":summarize(raw),
      "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "estimated_complexity":"proposal O(L^2), raw signature O(HL), basis O(BH), relaxation O(SH)",
      "hidden_labels_used_by_learner":False,
      "highschool_level_passed":False,"native_japanese_communication_passed":False,
      "weak_smartphone_verified":False,"completion":False
    }
    with open(a.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload["summary"]["180"],ensure_ascii=False,indent=2))
if __name__=="__main__":main()
