from __future__ import annotations
import argparse, json, random, resource, time
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np

SPECIAL={"<bos>","<eos>","。","？","は","の"}
NAMES_A=["葵","蓮","凛","空"]; NAMES_B=["海","森","光","風"]
COLORS_A=["赤","青","緑","白"]; COLORS_B=["朱","藍","翠","雪"]
OBJECTS=["鍵","本","箱","石"]; PLACES=["机","棚","庭","部屋"]
OPS={"記録","更新","配置","移動","追加","質問","回答","反転"}
ATTRS={"色","場所","数"}

def make_episode(rng,family,renamed=False,depth=4):
    names=NAMES_B if renamed else NAMES_A; colors=COLORS_B if renamed else COLORS_A
    if family=="memory":
        ns=rng.sample(names,3); cs=rng.sample(colors,3); st=dict(zip(ns,cs)); seq=["<bos>"]
        for n in ns: seq += ["記録",n,"は",st[n],"。"]
        for _ in range(depth):
            n=rng.choice(ns); c=rng.choice(colors); st[n]=c; seq += ["更新",n,"は",c,"。"]
        q=rng.choice(ns); ans=st[q]; seq += ["質問",q,"の","色","は","？","回答",ans,"<eos>"]
    elif family=="location":
        os=rng.sample(OBJECTS,3); ps=rng.sample(PLACES,3); st=dict(zip(os,ps)); seq=["<bos>"]
        for o in os: seq += ["配置",o,"は",st[o],"。"]
        for _ in range(depth):
            o=rng.choice(os); p=rng.choice(PLACES); st[o]=p; seq += ["移動",o,"は",p,"。"]
        q=rng.choice(os); ans=st[q]; seq += ["質問",q,"の","場所","は","？","回答",ans,"<eos>"]
    elif family=="arithmetic":
        v=rng.randrange(4); seq=["<bos>","記録","数","は",str(v),"。"]
        for _ in range(depth):
            d=rng.randrange(1,4); v=(v+d)%4; seq += ["追加",str(d),"。"]
        ans=str(v); seq += ["質問","数","は","？","回答",ans,"<eos>"]
    elif family=="decoy":
        ns=rng.sample(names,3); cs=rng.sample(colors,3); st=dict(zip(ns,cs)); seq=["<bos>"]
        for n in ns: seq += ["記録",n,"は",st[n],"。"]
        q=rng.choice(ns); ans=colors[(colors.index(st[q])+1)%4]
        seq += ["反転",q,"。","質問",q,"の","色","は","？","回答",ans,"<eos>"]
    else: raise ValueError(family)
    return seq,ans

class RoleQuotient:
    def __init__(self,context=6):
        self.context=context; self.roles={}; self.counts=defaultdict(Counter); self.lex=defaultdict(Counter)
    def fit_roles(self,seqs):
        left=defaultdict(Counter); right=defaultdict(Counter); vocab=set()
        for seq in seqs:
            vocab.update(seq)
            for i,t in enumerate(seq):
                if i:left[t][seq[i-1]]+=1
                if i+1<len(seq):right[t][seq[i+1]]+=1
        def cat(t):
            if t in SPECIAL:return t
            if t in OPS:return "OP"
            if t in ATTRS:return "ATTR"
            return "ATOM"
        groups=defaultdict(list)
        for t in sorted(vocab):
            if t in SPECIAL or t in OPS or t in ATTRS:
                self.roles[t]=t; continue
            sig=(tuple(sorted(cat(k) for k in left[t])),tuple(sorted(cat(k) for k in right[t])))
            groups[sig].append(t)
        for i,(_,ts) in enumerate(sorted(groups.items(),key=lambda x:repr(x[0]))):
            for t in ts:self.roles[t]=f"R{i}"
    def transform(self,seq):return [self.roles.get(t,"<unk-role>") for t in seq]
    def train(self,seqs):
        self.fit_roles(seqs)
        for seq in seqs:
            r=self.transform(seq)
            for i in range(len(seq)-1):
                for n in range(1,self.context+1):
                    if i-n+1<0:continue
                    self.counts[tuple(r[i-n+1:i+1])][seq[i+1]]+=1
                    self.lex[tuple(seq[i-n+1:i+1])][seq[i+1]]+=1
    def predict(self,h,quotient):
        seq=self.transform(h) if quotient else h; tab=self.counts if quotient else self.lex
        for n in range(min(self.context,len(seq)),0,-1):
            k=tuple(seq[-n:])
            if k in tab:return tab[k].most_common(1)[0][0],len(tab[k])
        return "<eos>",0
    def bytes(self):
        return len(json.dumps({"r":self.roles,"c":{repr(k):dict(v) for k,v in self.counts.items()}},ensure_ascii=False).encode())

@dataclass
class Row:
    method:str;seed:int;examples:int;in_domain:float;renamed:float;decoy:float;arithmetic:float;free_gate:float;model_bytes:int;peak_rss_kib:int;train_seconds:float;inference_ms:float;candidates_mean:float;reads:int;role_count:int

def eval_family(m,seed,fam,renamed,quotient,n=96):
    rng=random.Random(seed);ok=0;cs=[]
    for _ in range(n):
        seq,ans=make_episode(rng,fam,renamed,5);pos=seq.index("回答");pred,c=m.predict(seq[:pos+1],quotient);ok+=pred==ans;cs.append(c)
    return ok/n,float(np.mean(cs))

def free_gate(m,q):
    cases=[
      (["<bos>","こんにちは"],"こんにちは"),
      (["<bos>","説明","手順","回答"],"先に"),
      (["<bos>","もし","A","なら","回答"],"B"),
      (["<bos>","計画","A","ため","回答"],"A"),
      (["<bos>","原因","A","結果","回答"],"B"),
      (["<bos>","文章","読んで","質問","回答"],"説明"),
      (["<bos>","前の","訂正","覚えて","回答"],"新しい"),
      (["<bos>","自由","記述","回答"],"説明"),
      (["<bos>","新しい","規則","覚えて","回答"],"A"),
    ]
    good=0
    for p,target in cases:
        pred,_=m.predict(p,q);good+=pred==target
    return good/9

def run_one(method,seed,examples):
    rng=random.Random(seed);seqs=[];fams=("memory","location","arithmetic")
    for i in range(examples):seqs.append(make_episode(rng,fams[i%3],False,4)[0])
    m=RoleQuotient();t=time.perf_counter();m.train(seqs);train_s=time.perf_counter()-t;q=method=="role_quotient"
    a,c1=eval_family(m,seed+1000,"memory",False,q);b,c2=eval_family(m,seed+2000,"memory",True,q);d,c3=eval_family(m,seed+3000,"decoy",True,q);e,c4=eval_family(m,seed+4000,"arithmetic",False,q)
    hs=[];rr=random.Random(seed+9)
    for _ in range(500):
        seq,_=make_episode(rr,"memory",True,5);hs.append(seq[:seq.index("回答")+1])
    t=time.perf_counter()
    for h in hs:m.predict(h,q)
    inf=(time.perf_counter()-t)*1000/len(hs)
    return Row(method,seed,examples,a,b,d,e,free_gate(m,q),m.bytes(),resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,train_s,inf,float(np.mean([c1,c2,c3,c4])),6,len(set(m.roles.values())))

def run(out):
    rows=[]
    for ex in (96,384,1536):
        for seed in (1,7,19):
            for method in ("lexical_causal_state","role_quotient"):rows.append(run_one(method,seed,ex))
    agg={}
    for method in ("lexical_causal_state","role_quotient"):
        agg[method]={}
        for ex in (96,384,1536):
            rr=[r for r in rows if r.method==method and r.examples==ex]
            agg[method][str(ex)]={k:float(np.mean([getattr(r,k) for r in rr])) for k in ("in_domain","renamed","decoy","arithmetic","free_gate","train_seconds","inference_ms","candidates_mean")}
            agg[method][str(ex)].update({"model_bytes_max":max(r.model_bytes for r in rr),"peak_rss_kib_max":max(r.peak_rss_kib for r in rr),"role_count_max":max(r.role_count for r in rr),"reads":6})
    rep={"hypothesis":"Relational-role quotienting can form predictive states invariant to entity renaming without task labels.","claim":{"completion":False,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False},"aggregate":agg,"runs":[asdict(r) for r in rows]}
    Path(out).write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding="utf-8");return rep

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",default="relational_role_quotient_report.json");a=p.parse_args();print(json.dumps(run(a.output)["aggregate"],ensure_ascii=False,indent=2))
