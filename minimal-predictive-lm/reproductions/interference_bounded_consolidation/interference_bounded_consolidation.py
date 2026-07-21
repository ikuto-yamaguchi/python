from __future__ import annotations
import argparse, hashlib, json, math, random, resource, time
from functools import lru_cache
from dataclasses import asdict, dataclass
from pathlib import Path
import numpy as np

TOKENS = [
    "<bos>","<eos>","記録","更新","質問","回答","は","の","色","数","原因","結果","計画","手順","説明",
    "もし","なら","ため","。","？","葵","蓮","凛","空","赤","青","緑","白","0","1","2","3","A","B","C","D",
    "こんにちは","教えて","覚えて","追加","減少","先に","次に","最後","違う","新しい"
]
T2I = {t:i for i,t in enumerate(TOKENS)}
V = len(TOKENS)
NAMES = ["葵","蓮","凛","空"]
COLORS = ["赤","青","緑","白"]

def stable_hash(text: str) -> int:
    return int.from_bytes(hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest(), "little")

@lru_cache(maxsize=200000)
def _feat_cached(history: tuple[str, ...], dim: int = 64) -> bytes:
    x = np.zeros(dim, np.float32)
    start = max(0, len(history)-12)
    for n in (1,2,3,4):
        for i in range(start, len(history)-n+1):
            token_string = "\x1f".join(history[i:i+n])
            h = stable_hash(f"{n}:{token_string}")
            x[h % dim] += 1.0 if ((h >> 9) & 1) else -1.0
    norm = np.linalg.norm(x)
    x = x / (norm + 1e-6)
    return x.tobytes()

def feat(history: list[str], dim: int = 64) -> np.ndarray:
    return np.frombuffer(_feat_cached(tuple(history[-12:]), dim), dtype=np.float32).copy()

def episode(rng: random.Random, family: str, depth: int, counter: bool=False) -> list[str]:
    if family == "memory":
        names = rng.sample(NAMES, 4); colors = rng.sample(COLORS, 4)
        state = dict(zip(names, colors)); seq = ["<bos>"]
        for n in names: seq += ["記録", n, "は", state[n], "。"]
        for _ in range(depth):
            n = rng.choice(names); c = rng.choice(COLORS); state[n] = c
            seq += ["更新", n, "は", c, "。"]
        q = rng.choice(names)
        seq += ["質問", q, "の", "色", "は", "？", "回答", state[q], "<eos>"]
    elif family == "arithmetic":
        value = rng.randrange(4); seq = ["<bos>", "記録", "数", "は", str(value), "。"]
        for _ in range(depth):
            delta = rng.choice((1,2,3)); value = (value + delta) % 4
            seq += ["追加", str(delta), "。"]
        seq += ["質問", "数", "は", "？", "回答", str(value), "<eos>"]
    elif family == "causal":
        cause, effect = rng.sample(["A","B","C","D"], 2)
        seq = ["<bos>", "原因", cause, "結果", effect, "。", "もし", cause, "なら", "？", "回答", effect, "<eos>"]
    elif family == "plan":
        a,b,c = rng.sample(["A","B","C","D"], 3)
        seq = ["<bos>", "計画", a, "先に", b, "次に", c, "最後", "。", "質問", "手順", "は", "？", "回答", a, "<eos>"]
    else:
        raise ValueError(family)
    if counter:
        swap = {"葵":"空","空":"葵","蓮":"凛","凛":"蓮","赤":"白","白":"赤","青":"緑","緑":"青",
                "A":"D","D":"A","B":"C","C":"B","0":"3","3":"0","1":"2","2":"1"}
        seq = [swap.get(t,t) for t in seq]
    return seq

def free_gate() -> list[list[str]]:
    return [
        ["<bos>","こんにちは","<eos>"],
        ["<bos>","説明","手順","教えて","<eos>"],
        ["<bos>","もし","A","なら","B","違う","なら","C","<eos>"],
        ["<bos>","新しい","A","覚えて","質問","A","<eos>"],
        ["<bos>","原因","A","結果","B","説明","<eos>"],
        ["<bos>","計画","A","ため","B","手順","<eos>"],
        ["<bos>","記録","葵","は","赤","。","更新","葵","は","青","。","質問","葵","の","色","は","？","回答","青","<eos>"],
        ["<bos>","説明","原因","結果","<eos>"],
        ["<bos>","新しい","手順","覚えて","<eos>"],
    ]

@dataclass
class Metrics:
    method: str; seed: int; examples: int
    mixed_accuracy: float; counter_accuracy: float; reverse_order_accuracy: float; free_gate: float
    model_bytes: int; peak_rss_kib: int; train_seconds: float; inference_ms: float
    candidates: int; reads: int; proposed: int; accepted: int; rejected: int; protected_replay: int

class Memory:
    def __init__(self, method: str, dim: int=64, lr: float=.4, replay_cap: int=24):
        self.method=method; self.dim=dim; self.lr=lr
        self.w=np.zeros((dim,V), np.float32); self.fast=np.zeros_like(self.w)
        self.ema=math.log(V); self.replay=[]; self.replay_cap=replay_cap
        self.proposed=self.accepted=self.rejected=0

    def logits(self,x, extra=None):
        return x @ (self.w+self.fast+(0 if extra is None else extra))

    def loss_prob(self,x,y,extra=None):
        z=self.logits(x,extra); z-=z.max(); p=np.exp(z); p/=p.sum()
        return -math.log(float(p[y])+1e-9), p

    def _diverse_add(self,x,y):
        if len(self.replay)<self.replay_cap:
            self.replay.append((x.copy(),y)); return
        sims=[abs(float(x@rx)) for rx,_ in self.replay]
        j=int(np.argmax(sims))
        if sims[j] > .92: self.replay[j]=(x.copy(),y)
        else: self.replay.pop(0); self.replay.append((x.copy(),y))

    def observe(self,x,y):
        loss,p=self.loss_prob(x,y); self.ema=.985*self.ema+.015*loss
        one=np.zeros(V,np.float32); one[y]=1
        cand=(self.lr*np.outer(x,one-p)).astype(np.float32); self.proposed+=1
        if self.method=="immediate":
            self.w += cand; self.accepted+=1
        elif self.method=="surprise":
            if loss > self.ema: self.w += cand; self.accepted+=1
            else: self.rejected+=1
        elif self.method=="interference_bounded":
            current_gain = loss - self.loss_prob(x,y,cand)[0]
            damage=0.0
            for rx,ry in self.replay[::max(1,len(self.replay)//2 or 1)]:
                damage += max(0.0, self.loss_prob(rx,ry,cand)[0]-self.loss_prob(rx,ry)[0])
            if current_gain > 1e-5 and damage <= max(1e-4, current_gain*.35):
                self.w += cand; self.accepted+=1
            else: self.rejected+=1
        else: raise ValueError(self.method)
        self._diverse_add(x,y)

def train_stream(method, seed, examples, order=("memory","arithmetic","causal","plan")):
    rng=random.Random(seed); m=Memory(method); started=time.perf_counter(); per=max(1,examples//len(order))
    for family in order:
        for _ in range(per):
            seq=episode(rng,family,depth=3,counter=False); hist=[]
            for i in range(len(seq)-1):
                x=feat(hist+[seq[i]]); y=T2I[seq[i+1]]; m.observe(x,y); hist.append(seq[i])
    return m,time.perf_counter()-started

def evaluate(m, seed, counter=False, depth=8, n=32):
    rng=random.Random(seed); correct=total=0
    for family in ("memory","arithmetic","causal","plan"):
        for _ in range(n//4):
            seq=episode(rng,family,depth if family in ("memory","arithmetic") else 1,counter); hist=[]
            for i in range(len(seq)-1):
                x=feat(hist+[seq[i]]); y=T2I[seq[i+1]]
                if seq[i]=="回答": correct += int(int(m.logits(x).argmax())==y); total+=1
                hist.append(seq[i])
    return correct/max(1,total)

def gate_score(m):
    passed=0
    for seq in free_gate():
        hist=[]; ok=True
        for i in range(len(seq)-1):
            x=feat(hist+[seq[i]])
            if int(m.logits(x).argmax()) != T2I[seq[i+1]]: ok=False
            hist.append(seq[i])
        passed += int(ok)
    return passed/9

def run_one(method,seed,examples):
    m,train_s=train_stream(method,seed,examples)
    mixed=evaluate(m,seed+1000,False); counter=evaluate(m,seed+2000,True)
    reverse,_=train_stream(method,seed,examples,order=("plan","causal","arithmetic","memory"))
    reverse_acc=evaluate(reverse,seed+3000,False)
    x=feat(["<bos>","質問","葵","の","色","は","？","回答"]); t=time.perf_counter()
    for _ in range(500): m.logits(x)
    infer=(time.perf_counter()-t)*1000/500
    return Metrics(method,seed,examples,mixed,counter,reverse_acc,gate_score(m),
        int(m.w.nbytes+m.fast.nbytes),resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        train_s,infer,V,int(2*m.dim*V),m.proposed,m.accepted,m.rejected,len(m.replay))

def run(output: Path):
    rows=[]
    for examples in (32,128,256):
        for seed in (1,7,19):
            for method in ("immediate","surprise","interference_bounded"):
                rows.append(run_one(method,seed,examples))
    agg={}
    for method in ("immediate","surprise","interference_bounded"):
        agg[method]={}
        for examples in (32,128,256):
            rr=[r for r in rows if r.method==method and r.examples==examples]
            agg[method][str(examples)]={
                "mixed_accuracy_mean":float(np.mean([r.mixed_accuracy for r in rr])),
                "counter_accuracy_mean":float(np.mean([r.counter_accuracy for r in rr])),
                "reverse_order_accuracy_mean":float(np.mean([r.reverse_order_accuracy for r in rr])),
                "free_gate_mean":float(np.mean([r.free_gate for r in rr])),
                "model_bytes_max":max(r.model_bytes for r in rr),
                "peak_rss_kib_max":max(r.peak_rss_kib for r in rr),
                "train_seconds_mean":float(np.mean([r.train_seconds for r in rr])),
                "inference_ms_mean":float(np.mean([r.inference_ms for r in rr])),
                "accepted_mean":float(np.mean([r.accepted for r in rr])),
                "rejected_mean":float(np.mean([r.rejected for r in rr])),
            }
    report={
        "hypothesis":"Accept updates only when present loss decreases without exceeding an interference budget on a diverse protected replay set.",
        "claim":{"completion":False,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False},
        "aggregate":agg,"runs":[asdict(r) for r in rows],
    }
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--output",type=Path,default=Path("artifacts/interference_report.json"))
    args=p.parse_args(); report=run(args.output); print(json.dumps(report["aggregate"],ensure_ascii=False,indent=2))
