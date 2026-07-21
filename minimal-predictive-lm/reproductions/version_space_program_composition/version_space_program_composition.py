from __future__ import annotations
import argparse, itertools, json, random, resource, time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
import numpy as np

VALUES_A = ["赤","青","緑","白"]
VALUES_B = ["朱","藍","翠","雪"]
OPS_A = ["回転","交換","反射","保持"]
OPS_B = ["巡回","転置","鏡映","維持"]
ALL_FUNCTIONS = [tuple(p) for p in itertools.product(range(4), repeat=4)]

def hidden_functions():
    return {0:(1,2,3,0),1:(1,0,3,2),2:(3,2,1,0),3:(0,1,2,3)}

def apply_chain(start, ops, funcs):
    x=start
    for op in ops:x=funcs[op][x]
    return x

def make_episode(rng, renamed=False, chain_len=2, demos_per_op=4, noisy=False, context_dependent=False):
    vals=VALUES_B if renamed else VALUES_A;ops=OPS_B if renamed else OPS_A;funcs=hidden_functions();seq=["<bos>"]
    for oi,op in enumerate(ops):
        inputs=list(range(4));rng.shuffle(inputs)
        for j,x in enumerate(inputs[:demos_per_op]):
            y=funcs[oi][x]
            if context_dependent and oi==1 and j>=1:y=funcs[0][x]
            if noisy and oi==2 and j==0:y=(y+1)%4
            seq += ["例","入力",vals[x],"操作",op,"出力",vals[y],"。"]
    start=rng.randrange(4);chain=[rng.randrange(4) for _ in range(chain_len)];ans=apply_chain(start,chain,funcs)
    seq += ["質問","開始",vals[start]]
    for oi in chain:seq += ["操作",ops[oi]]
    seq += ["回答",vals[ans],"<eos>"]
    return seq,vals[ans]

def clauses(seq):
    out=[];cur=[]
    for t in seq:
        cur.append(t)
        if t in {"。","<eos>"}:out.append(cur);cur=[]
    if cur:out.append(cur)
    return out

class VersionSpaceComposer:
    def __init__(self):self.schema_votes=Counter();self.schemas=[]
    def fit(self,seqs):
        for seq in seqs:
            for cl in clauses(seq):
                if "入力" in cl and "操作" in cl and "出力" in cl:
                    self.schema_votes[(cl.index("入力")+1,cl.index("操作")+1,cl.index("出力")+1,len(cl))]+=1
        self.schemas=[s for s,_ in self.schema_votes.most_common(8)]
    def parse(self,h):
        demos=[];query=None
        for cl in clauses(h):
            if "例" not in cl: continue
            for ip,opos,yp,L in self.schemas:
                if len(cl)==L and max(ip,opos,yp)<len(cl):demos.append((cl[ip],cl[opos],cl[yp]));break
        if "質問" in h and "開始" in h:
            qi=max(i for i,t in enumerate(h) if t=="質問");tail=h[qi:];start=tail[tail.index("開始")+1]
            ops=[tail[i+1] for i,t in enumerate(tail[:-1]) if t=="操作"]
            query=(start,ops)
        return demos,query
    def predict(self,h):
        demos,query=self.parse(h)
        if not query:return "<eos>",0,0,"no_query"
        atoms=[]
        for x,_,y in demos:
            if x not in atoms:atoms.append(x)
            if y not in atoms:atoms.append(y)
        start,ops=query
        if start not in atoms:atoms.append(start)
        if len(atoms)!=4:return "<eos>",0,0,"domain_not_identified"
        idx={v:i for i,v in enumerate(atoms)};byop={};inconsistent=False
        for x,o,y in demos:byop.setdefault(o,[]).append((idx[x],idx[y]))
        spaces={};reads=0
        for o in set(ops):
            cand=ALL_FUNCTIONS
            for x,y in byop.get(o,[]):cand=[f for f in cand if f[x]==y]
            for x in range(4):
                if len({y for xx,y in byop.get(o,[]) if xx==x})>1:inconsistent=True
            spaces[o]=cand;reads += len(ALL_FUNCTIONS)*max(1,len(byop.get(o,[])))
        if inconsistent or any(not spaces[o] for o in ops):return "<eos>",sum(len(spaces[o]) for o in set(ops)),reads,"inconsistent"
        possible={idx[start]}
        for o in ops:possible={f[x] for x in possible for f in spaces[o]}
        if len(possible)!=1:return "<eos>",sum(len(spaces[o]) for o in set(ops)),reads,"ambiguous"
        rev={i:v for v,i in idx.items()};return rev[next(iter(possible))],sum(len(spaces[o]) for o in set(ops)),reads,"resolved"
    def model_bytes(self):return len(json.dumps(self.schemas,ensure_ascii=False).encode())

class DirectBindingBaseline:
    def fit(self,seqs):pass
    def predict(self,h):
        demos=[]
        for cl in clauses(h):
            if all(x in cl for x in ("入力","操作","出力")):demos.append((cl[cl.index("入力")+1],cl[cl.index("操作")+1],cl[cl.index("出力")+1]))
        if "質問" not in h:return "<eos>",0,0,"no_query"
        tail=h[max(i for i,t in enumerate(h) if t=="質問"):]
        if "開始" not in tail:return "<eos>",0,len(demos),"no_query"
        start=tail[tail.index("開始")+1];ops=[tail[i+1] for i,t in enumerate(tail[:-1]) if t=="操作"]
        if len(ops)!=1:return "<eos>",0,len(demos),"cannot_compose"
        for x,o,y in reversed(demos):
            if x==start and o==ops[0]:return y,1,len(demos),"resolved"
        return "<eos>",0,len(demos),"missing"
    def model_bytes(self):return 2

@dataclass
class Row:
    method:str;seed:int;examples:int;single:float;composition2:float;composition4:float;renamed:float;ambiguous_abstain:float;noisy_reject:float;context_reject:float;free_gate:float;model_bytes:int;peak_rss_kib:int;train_seconds:float;inference_ms:float;candidates_mean:float;reads_mean:float;resolved_rate:float

def evaluate(m,seed,kind,n=96):
    rng=random.Random(seed);ok=0;cs=[];rs=[];resolved=0
    for _ in range(n):
        if kind=="single":seq,ans=make_episode(rng,False,1,4)
        elif kind=="composition2":seq,ans=make_episode(rng,False,2,4)
        elif kind=="composition4":seq,ans=make_episode(rng,False,4,4)
        elif kind=="renamed":seq,ans=make_episode(rng,True,3,4)
        elif kind=="ambiguous":seq,ans=make_episode(rng,True,3,1)
        elif kind=="noisy":seq,ans=make_episode(rng,True,3,4,noisy=True)
        elif kind=="context":seq,ans=make_episode(rng,True,3,4,context_dependent=True)
        pos=seq.index("回答");pred,c,r,status=m.predict(seq[:pos+1])
        if kind=="ambiguous":ok += status=="ambiguous"
        elif kind in ("noisy","context"):ok += status in ("inconsistent","ambiguous")
        else:ok += pred==ans
        cs.append(c);rs.append(r);resolved += status=="resolved"
    return ok/n,float(np.mean(cs)),float(np.mean(rs)),resolved/n

def free_gate(m):
    cases=[(["<bos>","こんにちは","回答"],"こんにちは"),(["<bos>","説明","手順","回答"],"先に"),(["<bos>","もし","A","なら","回答"],"B"),(["<bos>","計画","A","ため","回答"],"A"),(["<bos>","原因","A","結果","回答"],"B"),(["<bos>","文章","読んで","質問","回答"],"説明"),(["<bos>","前の","訂正","覚えて","回答"],"新しい"),(["<bos>","自由","記述","回答"],"説明"),(["<bos>","新しい","規則","覚えて","回答"],"A")]
    return sum(m.predict(h)[0]==target for h,target in cases)/9

def run_one(method,seed,examples):
    rng=random.Random(seed);seqs=[make_episode(rng,i%3==0,1+(i%4),4)[0] for i in range(examples)]
    m=DirectBindingBaseline() if method=="direct_binding" else VersionSpaceComposer();t=time.perf_counter();m.fit(seqs);train=time.perf_counter()-t
    vals={k:evaluate(m,seed+1000+len(k),k) for k in ("single","composition2","composition4","renamed","ambiguous","noisy","context")}
    rr=random.Random(seed+77);hs=[]
    for _ in range(500):
        seq,_=make_episode(rr,True,4,4);hs.append(seq[:seq.index("回答")+1])
    t=time.perf_counter()
    for h in hs:m.predict(h)
    inf=(time.perf_counter()-t)*1000/len(hs);normal=("single","composition2","composition4","renamed")
    return Row(method,seed,examples,vals["single"][0],vals["composition2"][0],vals["composition4"][0],vals["renamed"][0],vals["ambiguous"][0],vals["noisy"][0],vals["context"][0],free_gate(m),m.model_bytes(),resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,train,inf,float(np.mean([vals[k][1] for k in vals])),float(np.mean([vals[k][2] for k in vals])),float(np.mean([vals[k][3] for k in normal])))

def run(out):
    rows=[]
    for ex in (32,128,512):
        for seed in (1,7,19):
            for method in ("direct_binding","version_space_composer"):rows.append(run_one(method,seed,ex))
    metrics=("single","composition2","composition4","renamed","ambiguous_abstain","noisy_reject","context_reject","free_gate","train_seconds","inference_ms","candidates_mean","reads_mean","resolved_rate")
    agg={}
    for method in ("direct_binding","version_space_composer"):
        agg[method]={}
        for ex in (32,128,512):
            rr=[r for r in rows if r.method==method and r.examples==ex]
            agg[method][str(ex)]={k:float(np.mean([getattr(r,k) for r in rr])) for k in metrics}
            agg[method][str(ex)].update(model_bytes_max=max(r.model_bytes for r in rr),peak_rss_kib_max=max(r.peak_rss_kib for r in rr))
    report={"hypothesis":"Infer per-episode operator version spaces from demonstrations; compose them only when every consistent latent program agrees on the output.","claim":{"completion":False,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False},"aggregate":agg,"runs":[asdict(r) for r in rows]}
    Path(out).parent.mkdir(parents=True,exist_ok=True);Path(out).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8");return report

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",default="artifacts/version_space_program_composition_report.json");a=p.parse_args();print(json.dumps(run(a.output)["aggregate"],ensure_ascii=False,indent=2))
