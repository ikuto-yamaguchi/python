from __future__ import annotations
import argparse, json, random, resource, time
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np

STRUCT={"<bos>","<eos>","。","？","は","の","を","なら","先に","次に","最後"}
OPS={"記録","更新","配置","移動","追加","質問","回答","反転","原因","結果","計画"}
ATTRS={"色","場所","数","手順"}
NAMES_A=["葵","蓮","凛","空"]; NAMES_B=["海","森","光","風"]
COLORS_A=["赤","青","緑","白"]; COLORS_B=["朱","藍","翠","雪"]
OBJECTS_A=["鍵","本","箱","石"]; OBJECTS_B=["札","冊","器","玉"]
PLACES_A=["机","棚","庭","部屋"]; PLACES_B=["台","庫","苑","室"]
SYMS_A=["A","B","C","D"]; SYMS_B=["甲","乙","丙","丁"]

def make_episode(rng,family,renamed=False,depth=4,unseen_answer=False):
    names=NAMES_B if renamed else NAMES_A
    colors=COLORS_B if renamed else COLORS_A
    objects=OBJECTS_B if renamed else OBJECTS_A
    places=PLACES_B if renamed else PLACES_A
    syms=SYMS_B if renamed else SYMS_A
    if family=="memory":
        ns=rng.sample(names,3); cs=rng.sample(colors,3); st=dict(zip(ns,cs)); seq=["<bos>"]
        for n in ns: seq += ["記録",n,"は",st[n],"。"]
        for _ in range(depth):
            n=rng.choice(ns); c=rng.choice(colors); st[n]=c; seq += ["更新",n,"は",c,"。"]
        q=rng.choice(ns); ans=("金" if renamed else "紫") if unseen_answer else st[q]
        seq += ["質問",q,"の","色","は","？","回答",ans,"<eos>"]
    elif family=="location":
        os=rng.sample(objects,3); ps=rng.sample(places,3); st=dict(zip(os,ps)); seq=["<bos>"]
        for o in os: seq += ["配置",o,"は",st[o],"。"]
        for _ in range(depth):
            o=rng.choice(os); p=rng.choice(places); st[o]=p; seq += ["移動",o,"は",p,"。"]
        q=rng.choice(os); ans=st[q]
        seq += ["質問",q,"の","場所","は","？","回答",ans,"<eos>"]
    elif family=="causal":
        a,b=rng.sample(syms,2); seq=["<bos>","原因",a,"結果",b,"。","質問",a,"の","結果","は","？","回答",b,"<eos>"]; ans=b
    elif family=="plan":
        a,b,c=rng.sample(syms,3); seq=["<bos>","計画",a,"先に",b,"次に",c,"最後","。","質問","手順","は","？","回答",a,"<eos>"]; ans=a
    elif family=="decoy":
        ns=rng.sample(names,3); cs=rng.sample(colors,3); st=dict(zip(ns,cs)); seq=["<bos>"]
        for n in ns: seq += ["記録",n,"は",st[n],"。"]
        q=rng.choice(ns); ans=colors[(colors.index(st[q])+1)%4]
        seq += ["反転",q,"。","質問",q,"の","色","は","？","回答",ans,"<eos>"]
    else: raise ValueError(family)
    return seq,ans

def clauses(seq):
    out=[]; start=0
    for i,t in enumerate(seq):
        if t in {"。","？","<eos>"}:
            out.append(seq[start:i+1]); start=i+1
    return out

def abstract_token(t):
    if t in STRUCT or t in OPS or t in ATTRS:return t
    return "$ATOM"

class ReversibleEpisodicBinder:
    def __init__(self):
        self.schema_votes=Counter(); self.schemas=[]; self.lex=defaultdict(Counter)
    def fit(self,seqs):
        for seq in seqs:
            for i in range(len(seq)-1):
                for n in range(1,7):
                    if i-n+1>=0:self.lex[tuple(seq[i-n+1:i+1])][seq[i+1]]+=1
            try: ai=seq.index("回答"); qi=max(i for i,t in enumerate(seq[:ai]) if t=="質問")
            except ValueError: continue
            ans=seq[ai+1]; qatom=seq[qi+1] if qi+1<ai else None
            for cl in clauses(seq[:qi]):
                for ep,e in enumerate(cl):
                    if e!=qatom: continue
                    for vp,v in enumerate(cl):
                        if v==ans:
                            shape=tuple(abstract_token(x) for x in cl)
                            self.schema_votes[(shape,ep,vp)] += 1
        self.schemas=[k for k,_ in self.schema_votes.most_common(32)]
    def lexical_predict(self,h):
        for n in range(min(6,len(h)),0,-1):
            k=tuple(h[-n:])
            if k in self.lex:return self.lex[k].most_common(1)[0][0],len(self.lex[k])
        return "<eos>",0
    def bind_predict(self,h):
        try: qi=max(i for i,t in enumerate(h) if t=="質問")
        except ValueError:return "<eos>",0,0
        qatom=h[qi+1] if qi+1<len(h) else None
        reads=0; prior=clauses(h[:qi])
        for shape,ep,vp in self.schemas:
            for cl in reversed(prior):
                reads+=1
                if len(cl)!=len(shape):continue
                if tuple(abstract_token(x) for x in cl)!=shape:continue
                if ep<len(cl) and vp<len(cl) and cl[ep]==qatom:return cl[vp],1,reads
        return "<eos>",0,reads
    def model_bytes(self):
        return len(json.dumps({"schemas":[[list(s),e,v] for s,e,v in self.schemas]},ensure_ascii=False).encode())

@dataclass
class Row:
    method:str; seed:int; examples:int; in_domain:float; renamed:float; location:float; causal:float; plan:float; decoy:float; unseen_value:float; free_gate:float; model_bytes:int; peak_rss_kib:int; train_seconds:float; inference_ms:float; candidates_mean:float; reads_mean:float; schema_count:int

def eval_family(m,seed,fam,renamed,method,n=96,unseen=False):
    rng=random.Random(seed);ok=0;cs=[];rs=[]
    for _ in range(n):
        seq,ans=make_episode(rng,fam,renamed,5,unseen);pos=seq.index("回答");h=seq[:pos+1]
        if method=="lexical":pred,c=m.lexical_predict(h);r=6
        else:pred,c,r=m.bind_predict(h)
        ok+=pred==ans;cs.append(c);rs.append(r)
    return ok/n,float(np.mean(cs)),float(np.mean(rs))

def free_gate(m,method):
    cases=[(["<bos>","こんにちは"],"こんにちは"),(["<bos>","説明","手順","回答"],"先に"),(["<bos>","もし","A","なら","回答"],"B"),(["<bos>","計画","A","ため","回答"],"A"),(["<bos>","原因","A","結果","回答"],"B"),(["<bos>","文章","読んで","質問","回答"],"説明"),(["<bos>","前の","訂正","覚えて","回答"],"新しい"),(["<bos>","自由","記述","回答"],"説明"),(["<bos>","新しい","規則","覚えて","回答"],"A")]
    good=0
    for h,target in cases:
        pred=m.lexical_predict(h)[0] if method=="lexical" else m.bind_predict(h)[0]
        good+=pred==target
    return good/9

def run_one(method,seed,examples):
    rng=random.Random(seed);seqs=[];fams=("memory","location","causal","plan")
    for i in range(examples):seqs.append(make_episode(rng,fams[i%4],False,4)[0])
    m=ReversibleEpisodicBinder();t=time.perf_counter();m.fit(seqs);train_s=time.perf_counter()-t
    vals={}
    for fam,ren,key in [("memory",False,"in_domain"),("memory",True,"renamed"),("location",True,"location"),("causal",True,"causal"),("plan",True,"plan"),("decoy",True,"decoy")]:vals[key]=eval_family(m,seed+1000+len(key),fam,ren,method)
    unseen=eval_family(m,seed+9000,"memory",True,method,unseen=True)
    rr=random.Random(seed+77);hs=[]
    for _ in range(500):
        seq,_=make_episode(rr,"memory",True,5);hs.append(seq[:seq.index("回答")+1])
    t=time.perf_counter()
    for h in hs:(m.lexical_predict(h) if method=="lexical" else m.bind_predict(h))
    inf=(time.perf_counter()-t)*1000/len(hs)
    means=[vals[k][1] for k in vals]+[unseen[1]];reads=[vals[k][2] for k in vals]+[unseen[2]]
    return Row(method,seed,examples,vals['in_domain'][0],vals['renamed'][0],vals['location'][0],vals['causal'][0],vals['plan'][0],vals['decoy'][0],unseen[0],free_gate(m,method),m.model_bytes(),resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,train_s,inf,float(np.mean(means)),float(np.mean(reads)),len(m.schemas))

def run(out):
    rows=[]
    for ex in (96,384,1536):
        for seed in (1,7,19):
            for method in ('lexical','reversible_binding'):rows.append(run_one(method,seed,ex))
    agg={};metrics=('in_domain','renamed','location','causal','plan','decoy','unseen_value','free_gate','train_seconds','inference_ms','candidates_mean','reads_mean')
    for method in ('lexical','reversible_binding'):
        agg[method]={}
        for ex in (96,384,1536):
            rr=[r for r in rows if r.method==method and r.examples==ex]
            agg[method][str(ex)]={k:float(np.mean([getattr(r,k) for r in rr])) for k in metrics}
            agg[method][str(ex)].update({'model_bytes_max':max(r.model_bytes for r in rr),'peak_rss_kib_max':max(r.peak_rss_kib for r in rr),'schema_count_max':max(r.schema_count for r in rr)})
    rep={'hypothesis':'Learn only equality-preserving relation-position schemas; keep episode atoms in a reversible local binding channel.','claim':{'completion':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False},'aggregate':agg,'runs':[asdict(r) for r in rows]}
    Path(out).parent.mkdir(parents=True,exist_ok=True);Path(out).write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8');return rep

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='artifacts/reversible_episodic_binding_report.json');a=p.parse_args();print(json.dumps(run(a.output)['aggregate'],ensure_ascii=False,indent=2))
