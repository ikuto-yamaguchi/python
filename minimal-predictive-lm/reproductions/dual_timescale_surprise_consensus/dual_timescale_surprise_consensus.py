from __future__ import annotations
import argparse, hashlib, json, math, random, resource, time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable
import numpy as np

TOKENS = ["<bos>","<eos>","記録","更新","質問","回答","は","の","色","数","原因","結果","計画","ため","。","？",
          "葵","蓮","凛","空","赤","青","緑","白","0","1","2","3","A","B","C","D",
          "こんにちは","説明","手順","もし","なら","違う","新しい","覚えて"]
T2I={t:i for i,t in enumerate(TOKENS)}
V=len(TOKENS)
NAMES=["葵","蓮","凛","空"]; COLORS=["赤","青","緑","白"]

def _stable_hash(text):
    return int.from_bytes(hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest(), "little")

def feat(history, dim=64):
    x=np.zeros(dim,np.float32)
    for n in (1,2,3):
        for i in range(max(0,len(history)-8), len(history)-n+1):
            s="|".join(history[i:i+n])
            h=_stable_hash(f"{n}:{s}")
            x[h%dim]+=1.0 if (h>>8)&1 else -1.0
    norm=np.linalg.norm(x)
    return x/(norm+1e-6)

def make_episode(rng, depth=2, counter=False):
    names=rng.sample(NAMES,4); colors=rng.sample(COLORS,4)
    state=dict(zip(names,colors))
    seq=["<bos>"]
    for n in names: seq += ["記録",n,"は",state[n],"。"]
    for _ in range(depth):
        n=rng.choice(names); c=rng.choice(COLORS); state[n]=c
        seq += ["更新",n,"は",c,"。"]
    q=rng.choice(names)
    seq += ["質問",q,"の","色","は","？","回答",state[q],"<eos>"]
    if counter:
        swap={"葵":"空","空":"葵","蓮":"凛","凛":"蓮","赤":"白","白":"赤","青":"緑","緑":"青"}
        seq=[swap.get(t,t) for t in seq]
    return seq

def make_gate():
    return [
      ["<bos>","こんにちは","<eos>"],
      ["<bos>","説明","手順","<eos>"],
      ["<bos>","もし","A","なら","B","違う","なら","C","<eos>"],
      ["<bos>","新しい","A","覚えて","質問","A","<eos>"],
      ["<bos>","原因","A","結果","B","<eos>"],
      ["<bos>","計画","A","ため","B","<eos>"],
      ["<bos>","記録","葵","は","赤","。","更新","葵","は","青","。","質問","葵","の","色","は","？","回答","青","<eos>"],
      ["<bos>","説明","原因","結果","<eos>"],
      ["<bos>","新しい","手順","覚えて","<eos>"],
    ]

@dataclass
class Metrics:
    method:str; seed:int; examples:int; next_acc:float; counter_acc:float
    retention:float; gate:float; model_bytes:int; peak_rss_kib:int
    train_seconds:float; infer_ms:float; candidates:int; reads:int
    proposed:int; accepted:int; rejected:int

class Memory:
    def __init__(self, method, dim=64, lr=.35, fast_lr=.7):
        self.method=method; self.dim=dim; self.lr=lr; self.fast_lr=fast_lr
        self.slow=np.zeros((dim,V),np.float32)
        self.fast=np.zeros((dim,V),np.float32)
        self.ema=math.log(V); self.buffer=[]; self.proposed=self.accepted=self.rejected=0
    def logits(self,x): return x @ (self.slow+self.fast)
    def loss(self,x,y, extra=None):
        z=x @ (self.slow+self.fast+(0 if extra is None else extra)); z-=z.max()
        p=np.exp(z); p/=p.sum()
        return -math.log(float(p[y])+1e-9), p
    def observe(self,x,y,cf=None):
        loss,p=self.loss(x,y); self.ema=.98*self.ema+.02*loss
        one=np.zeros(V,np.float32); one[y]=1
        g=np.outer(x, one-p).astype(np.float32)
        self.buffer.append((x.copy(),y,cf))
        if len(self.buffer)>16:self.buffer.pop(0)
        if self.method=="immediate":
            self.slow += self.lr*g; return
        if loss > self.ema*0.95:
            cand=self.fast_lr*g; self.fast += cand; self.proposed+=1
            if self.method=="surprise": return
            if len(self.buffer)>=6:
                base=trial=0.0
                for bx,by,bcf in self.buffer[::5]:
                    base += self.loss(bx,by)[0]; trial += self.loss(bx,by,cand)[0]
                    if bcf is not None:
                        cx,cy=bcf; base += self.loss(cx,cy)[0]; trial += self.loss(cx,cy,cand)[0]
                if trial < base-1e-4:
                    self.slow += .5*cand; self.accepted+=1
                else:self.rejected+=1
                self.fast *= .5

def train_eval(method, seed, examples):
    rng=random.Random(seed)
    m=Memory(method)
    started=time.perf_counter()
    for _ in range(examples):
        seq=make_episode(rng,6,False); cseq=make_episode(random.Random(rng.randrange(1<<30)),6,True)
        hist=[]
        for i in range(len(seq)-1):
            x=feat(hist+[seq[i]]); y=T2I[seq[i+1]]
            ci=min(i+1,len(cseq)-1); cf=(feat(cseq[:ci]), T2I[cseq[ci]])
            m.observe(x,y,cf); hist.append(seq[i])
    train_s=time.perf_counter()-started
    def acc(counter=False, depth=2, n=16):
        rr=random.Random(seed+9000+int(counter)*17+depth)
        ok=tot=0
        for _ in range(n):
            seq=make_episode(rr,depth,counter); hist=[]
            for i in range(len(seq)-1):
                x=feat(hist+[seq[i]]); y=T2I[seq[i+1]]
                if seq[i]=="回答":
                    ok += int(m.logits(x).argmax()==y); tot+=1
                hist.append(seq[i])
        return ok/max(1,tot)
    a=acc(False); ca=acc(True)
    before=acc(False,depth=12)
    rr=random.Random(seed+12345)
    for _ in range(examples//4):
        seq=make_episode(rr,10,True); hist=[]
        for i in range(len(seq)-1):
            x=feat(hist+[seq[i]]); m.observe(x,T2I[seq[i+1]],None); hist.append(seq[i])
    after=acc(False,depth=12)
    retention=after/max(before,1e-6) if before>0 else 0.0
    gate_ok=0
    for seq in make_gate():
        hist=[]; good=0
        for i in range(len(seq)-1):
            x=feat(hist+[seq[i]])
            good += int(m.logits(x).argmax()==T2I[seq[i+1]])
            hist.append(seq[i])
        gate_ok += int(good==len(seq)-1)
    gate=gate_ok/9
    x=feat(["<bos>","質問","葵","の","色","は","？","回答"])
    t=time.perf_counter()
    for _ in range(1000):m.logits(x)
    infer=(time.perf_counter()-t)*1000/1000
    return Metrics(method,seed,examples,a,ca,retention,gate,
      int(m.slow.nbytes+m.fast.nbytes),resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      train_s,infer,V,int(2*m.dim*V),m.proposed,m.accepted,m.rejected)

def run(output):
    rows=[]
    for ex in (16,64,256):
      for seed in (1,7,19):
       for method in ("immediate","surprise","delayed_consensus"):
        rows.append(train_eval(method,seed,ex))
    agg={}
    for method in ("immediate","surprise","delayed_consensus"):
      agg[method]={}
      for ex in (16,64,256):
       r=[x for x in rows if x.method==method and x.examples==ex]
       agg[method][str(ex)]={k:float(np.mean([getattr(x,k) for x in r])) for k in
         ("next_acc","counter_acc","retention","gate","model_bytes","peak_rss_kib","train_seconds","infer_ms","proposed","accepted","rejected")}
    report={"hypothesis":"dual-timescale surprise consensus","aggregate":agg,
      "claim":{"completion":False,"highschool_level_passed":False,"native_japanese_communication_passed":False,
      "weak_smartphone_verified":False},
      "runs":[asdict(x) for x in rows]}
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(report,ensure_ascii=False,indent=2))
    return report

def main(argv:Iterable[str]|None=None):
    p=argparse.ArgumentParser(); p.add_argument("--output",type=Path,default=Path("artifacts/report.json"))
    a=p.parse_args(argv); r=run(a.output); print(json.dumps(r["aggregate"],ensure_ascii=False,indent=2))
if __name__=="__main__":main()
