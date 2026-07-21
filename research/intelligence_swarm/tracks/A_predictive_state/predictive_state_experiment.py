from __future__ import annotations
import argparse, hashlib, json, random, re, resource, statistics, time
from pathlib import Path
import numpy as np

NAMES=["葵","蓮","凛","空","遥","湊"]
ITEMS=["鍵","本","箱","傘","写真","薬"]
PLACES=["机","棚","玄関","鞄","引き出し","窓辺"]
OBS=["{n}は{i}を{p}に置いた。","{n}が{i}を{p}へ移した。","{i}は{n}によって{p}に置かれた。"]
CHG=["その後、{n}は{i}を{p}へ移した。","続いて{i}の場所を{p}に変えた。","{i}は最終的に{p}へ移された。"]
ASK=["{i}はどこにありますか？","{i}の場所を教えて。","今、{i}はどこ？"]
ANS=["{i}は{p}にあります。","{p}にあります。","現在地は{p}です。"]

def make_dialog(rng: random.Random, mode: str="train") -> list[str]:
    n=rng.choice(NAMES); item=rng.choice(ITEMS); p1,p2=rng.sample(PLACES,2)
    form=2 if mode=="paraphrase" else rng.randrange(2)
    if mode=="rename":
        n=f"人物{rng.randrange(1000,9999)}"
        item=f"物体{rng.randrange(1000,9999)}"
        p1=f"場所{rng.randrange(1000,9999)}"
        p2=f"場所{rng.randrange(1000,9999)}"
    turns=[OBS[form].format(n=n,i=item,p=p1)]
    if mode!="no_change":
        turns.append(CHG[form].format(n=n,i=item,p=p2)); final=p2
    else:
        final=p1
    turns.extend([ASK[form].format(i=item),ANS[form].format(i=item,p=final)])
    return turns

def grams(text: str,n: int)->list[str]:
    text=re.sub(r"\s+","",text)
    return [text[i:i+n] for i in range(max(0,len(text)-n+1))]

def vector(text: str,dim: int=192)->np.ndarray:
    x=np.zeros(dim,np.float32)
    for n in (2,3,4):
        for g in grams(text,n):
            h=int.from_bytes(hashlib.blake2b(g.encode("utf-8"),digest_size=8).digest(),"little")
            x[h%dim]+=1.0 if (h>>8)&1 else -1.0
    return x/(np.linalg.norm(x)+1e-6)

def jaccard(a: str,b: str)->float:
    A=set(grams(a,2)); B=set(grams(b,2))
    return len(A&B)/max(1,len(A|B))

def pairs(dialogs: list[list[str]])->list[tuple[str,str]]:
    out=[]
    for dialog in dialogs:
        hist=[]
        for turn in dialog:
            if hist:
                out.append(("\n".join(hist[-3:]),turn))
            hist.append(turn)
    return out

class LexicalHistory:
    def fit(self, examples):
        self.examples=examples
        self.contexts=[vector(c) for c,_ in examples]
    def predict(self, context):
        x=vector(context)
        idx=int(np.argmax([float(x@y) for y in self.contexts]))
        return self.examples[idx][1],len(self.examples)
    def bytes(self):
        return sum(x.nbytes for x in self.contexts)+sum(len((c+f).encode()) for c,f in self.examples)

class PredictiveStatePartition:
    def __init__(self, future_similarity=.70):
        self.future_similarity=future_similarity
    def fit(self, examples):
        states=[]
        for context,future in examples:
            fv=vector(future); cv=vector(context)
            sims=[float(fv@s["future"]) for s in states]
            if not sims or max(sims)<self.future_similarity:
                states.append({"future":fv,"contexts":[cv],"outputs":[future]})
            else:
                idx=int(np.argmax(sims))
                state=states[idx]
                state["contexts"].append(cv); state["outputs"].append(future)
                q=np.mean([vector(o) for o in state["outputs"]],axis=0)
                state["future"]=q/(np.linalg.norm(q)+1e-6)
        self.states=states
        for state in self.states:
            q=np.mean(state["contexts"],axis=0)
            state["context"]=q/(np.linalg.norm(q)+1e-6)
            scores=[sum(jaccard(o,z) for z in state["outputs"]) for o in state["outputs"]]
            state["representative"]=state["outputs"][int(np.argmax(scores))]
    def predict(self, context):
        x=vector(context)
        idx=int(np.argmax([float(x@s["context"]) for s in self.states]))
        return self.states[idx]["representative"],len(self.states)
    def bytes(self):
        return sum(s["context"].nbytes+s["future"].nbytes+len(s["representative"].encode()) for s in self.states)

def evaluate(model,dialogs):
    scores=[]; reads=[]
    for dialog in dialogs:
        hist=[]
        for turn in dialog:
            if hist:
                pred,r=model.predict("\n".join(hist[-3:]))
                scores.append(jaccard(pred,turn)); reads.append(r)
            hist.append(turn)
    return float(np.mean(scores)),float(np.mean(reads))

def one_run(seed: int,ntrain: int)->list[dict]:
    rng=random.Random(seed)
    train=[make_dialog(rng) for _ in range(ntrain)]
    tests={k:[make_dialog(rng,k) for _ in range(60)] for k in ("train","paraphrase","rename","no_change")}
    shuffled=[d[:] for d in tests["train"]]
    for d in shuffled: rng.shuffle(d)
    rows=[]
    for name,model in (("lexical_history",LexicalHistory()),("predictive_state",PredictiveStatePartition())):
        start=time.perf_counter(); model.fit(pairs(train)); train_s=time.perf_counter()-start
        metrics={k:evaluate(model,v)[0] for k,v in tests.items()}
        metrics["shuffled_order"]=evaluate(model,shuffled)[0]
        start=time.perf_counter()
        for _ in range(300):
            model.predict("葵は鍵を机に置いた。\n鍵はどこ？")
        latency=(time.perf_counter()-start)*1000/300
        rows.append({
          "method":name,"seed":seed,"train_dialogs":ntrain,**metrics,
          "train_seconds":train_s,"latency_ms":latency,
          "candidate_reads":evaluate(model,tests["train"])[1],
          "states":len(getattr(model,"states",[])),
          "model_bytes":model.bytes(),
          "peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "free_japanese_gate":0.0
        })
    return rows

def run(output: Path):
    rows=[]
    for n in (32,128,512):
        for seed in (1,7,19):
            rows.extend(one_run(seed,n))
    aggregate={}
    for n in (32,128,512):
        aggregate[str(n)]={}
        for method in ("lexical_history","predictive_state"):
            rs=[r for r in rows if r["train_dialogs"]==n and r["method"]==method]
            aggregate[str(n)][method]={k:statistics.mean(r[k] for r in rs) for k in (
              "train","paraphrase","rename","no_change","shuffled_order","train_seconds",
              "latency_ms","candidate_reads","states","model_bytes","peak_rss_kib","free_japanese_gate")}
    report={
      "hypothesis":"Histories should be compressed into predictive-equivalence states defined by future distributions, not lexical similarity.",
      "verdict":"falsified_as_general_intelligence_path",
      "aggregate":aggregate,
      "runs":rows,
      "claim":{"highschool_level_passed":False,"native_japanese_communication_passed":False,
               "weak_smartphone_verified":False,"completion":False}
    }
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    return report

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,default=Path("results_cycle_001.json"))
    args=ap.parse_args()
    report=run(args.output)
    print(json.dumps(report["aggregate"],ensure_ascii=False,indent=2))
