from __future__ import annotations
from dataclasses import dataclass, field
from collections import Counter
import argparse, json, math, pickle, random, resource, statistics, time

ENTS=["青箱","赤箱","端末甲","端末乙","鍵北","鍵南","試料一","試料二"]
VALS=["棚A","棚B","棚C","完了","保留","担当甲","担当乙","廊下"]
EXPLICIT=["{e}の記録は{v}です。","{e}について{v}と記録します。","{e}は今{v}です。"]
FOLLOW=["その対象は{v}に更新します。","続きですが{v}です。","こちらは{v}になりました。"]
HELD=["先ほどのものは{v}へ変わりました。","例の対象は{v}です。","話題中の品は{v}になりました。"]
DIST=["天気は晴れです。","別件を確認しました。","休憩します。","窓を閉めました。"]
QUERY=["{e}の最新記録は？","{e}は今どうなっていますか。"]
ANSWER=["答えは{v}です。","最新値は{v}です。"]

def grams(s):
    s="".join(s.split())
    return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))
def cos(a,b):
    d=sum(v*b.get(k,0) for k,v in a.items())
    na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return d/(na*nb+1e-12)

@dataclass
class U:
    text:str
    event:int
    entity:str|None
    value:str|None
    kind:str

@dataclass
class Seg:
    ids:list[int]=field(default_factory=list)
    sig:Counter=field(default_factory=Counter)
    def add(self,i,u):
        self.ids.append(i); self.sig.update(grams(u.text))

def build(seed,n,held=False,gap=0,shift=False):
    r=random.Random(seed); stream=[]; truth={}; ev=0
    for _ in range(n):
        e=r.choice(ENTS); v=r.choice(VALS)
        stream.append(U(r.choice(EXPLICIT).format(e=e,v=v),ev,e,v,"explicit"))
        truth[e]=v
        for _ in range(gap if gap else r.randint(0,2)):
            stream.append(U(r.choice(DIST),-1,None,None,"distract"))
        if shift:
            e2=r.choice([x for x in ENTS if x!=e]); v2=r.choice(VALS)
            stream.append(U(r.choice(EXPLICIT).format(e=e2,v=v2),ev+10000,e2,v2,"explicit")); truth[e2]=v2
        nv=r.choice([x for x in VALS if x!=v])
        stream.append(U(r.choice(HELD if held else FOLLOW).format(v=nv),ev,e,nv,"follow")); truth[e]=nv
        stream.append(U(r.choice(QUERY).format(e=e),ev,e,None,"query"))
        stream.append(U(r.choice(ANSWER).format(v=nv),ev,None,nv,"answer"))
        ev+=1
    return stream,truth

class Surprise:
    def __init__(self): self.segs=[]; self.boundaries=0
    def observe(self,i,u):
        if not self.segs or cos(grams(u.text),self.segs[-1].sig)<0.08:
            self.segs.append(Seg()); self.boundaries+=1
        self.segs[-1].add(i,u)

class RetrievalJacobian:
    def __init__(self,max_recent=6):
        self.segs=[]; self.max_recent=max_recent; self.credits=[]; self.merges=0; self.splits=0
    def _retrieval_score(self,segs,stream,upto):
        score=0; count=0
        for j in range(max(0,upto-10),upto):
            if not stream[j].text.rstrip().endswith("？") or j+1>=upto: continue
            qg=grams(stream[j].text)
            ranked=sorted(((cos(qg,s.sig),s) for s in segs[-8:]),key=lambda x:x[0],reverse=True)
            if ranked:
                txt="".join(stream[k].text for k in ranked[0][1].ids)
                ans=stream[j+1].text
                toks=[g for g in grams(ans) if len(g)>=2]
                score += sum(g in txt for g in toks)/max(1,len(toks))
                count+=1
        return score/max(1,count)
    def observe(self,i,u,stream):
        if not self.segs:
            self.segs=[Seg()]; self.segs[0].add(i,u); self.splits+=1; return
        appended=Seg(list(self.segs[-1].ids),Counter(self.segs[-1].sig))
        appended.add(i,u)
        newseg=Seg(); newseg.add(i,u)
        a_tail=self.segs[-7:-1]+[appended]
        b_tail=self.segs[-7:]+[newseg]
        sa=self._retrieval_score(a_tail,stream,i+1)
        sb=self._retrieval_score(b_tail,stream,i+1)
        jac=sb-sa
        self.credits.append(jac)
        split = jac>0.01
        if abs(jac)<=0.01:
            novelty=1-cos(grams(u.text),self.segs[-1].sig)
            split=novelty>0.92
        if split:
            self.segs.append(newseg); self.splits+=1
        else:
            self.segs[-1]=appended; self.merges+=1

def sparse_replay_copy(m):
    import copy
    c=copy.deepcopy(m)
    for seg in c.segs:
        seg.sig=Counter(dict(seg.sig.most_common(48)))
        seg.ids=seg.ids[-8:]
    return c

def evaluator_retrieval(m,stream,truth):
    correct=0; reads=0
    for e,v in truth.items():
        q=QUERY[0].format(e=e); qg=grams(q)
        ranked=sorted(((cos(qg,s.sig),s) for s in m.segs),key=lambda x:x[0],reverse=True)[:8]
        reads+=len(ranked); pred=None
        for _,seg in ranked:
            for idx in reversed(seg.ids):
                u=stream[idx]
                if u.entity==e and u.value is not None: pred=u.value; break
            if pred is not None: break
        correct+=pred==v
    return correct/max(1,len(truth)), reads/max(1,len(truth))

def eval_model(cls,stream,truth):
    m=cls(); st=time.perf_counter()
    for i,u in enumerate(stream):
        if isinstance(m,RetrievalJacobian): m.observe(i,u,stream)
        else: m.observe(i,u)
    train=time.perf_counter()-st
    qst=time.perf_counter()
    retrieval, reads=evaluator_retrieval(m,stream,truth)
    inf=(time.perf_counter()-qst)*1000/max(1,len(truth))
    compressed=sparse_replay_copy(m)
    compressed_retrieval,_=evaluator_retrieval(compressed,stream,truth)
    true=set(); pred=set()
    for i in range(len(stream)):
        for j in range(i+1,min(len(stream),i+8)):
            if stream[i].event>=0 and stream[i].event==stream[j].event: true.add((i,j))
    for s in m.segs:
        for a in range(len(s.ids)):
            for b in range(a+1,len(s.ids)): pred.add((s.ids[a],s.ids[b]))
    tp=len(true&pred); p=tp/max(1,len(pred)); r=tp/max(1,len(true)); f=2*p*r/max(1e-12,p+r)
    return {"retrieval":retrieval,"event_precision":p,"event_recall":r,"event_f1":f,
            "segments":len(m.segs),"model_bytes":len(pickle.dumps(m)),
            "compressed_model_bytes":len(pickle.dumps(compressed)),
            "compressed_retrieval":compressed_retrieval,"train_seconds":train,
            "infer_ms":inf,"reads":reads,
            "mean_abs_credit":statistics.mean(abs(x) for x in getattr(m,"credits",[]) ) if getattr(m,"credits",[]) else 0,
            "nonzero_credit_rate":sum(abs(x)>0.01 for x in getattr(m,"credits",[]))/max(1,len(getattr(m,"credits",[])))}

def one_shot(seed):
    e=f"未知{seed}"; v=f"値{seed}"; stream=[U(f"{e}の記録は{v}です。",0,e,v,"explicit")]; truth={e:v}
    return {n:eval_model(c,stream,truth)["retrieval"] for n,c in [("surprise",Surprise),("jacobian",RetrievalJacobian)]}

def interference(seed):
    e="基準対象"; old="旧値"; new="新値"
    stream=[U(f"{e}の記録は{old}です。",0,e,old,"explicit")]
    for i in range(50):
        x=f"無関係{i}"; y=f"値{i}"
        stream.append(U(f"{x}の記録は{y}です。",i+1,x,y,"explicit"))
    stream.append(U(f"その対象は{new}に更新します。",0,e,new,"follow"))
    stream.append(U(f"{e}の最新記録は？",0,e,None,"query"))
    stream.append(U(f"答えは{new}です。",0,None,new,"answer"))
    truth={e:new}
    return {n:eval_model(c,stream,truth)["retrieval"] for n,c in [("surprise",Surprise),("jacobian",RetrievalJacobian)]}

def run(seed,n,mode):
    held=mode in ("held","combined"); gap=20 if mode=="long_gap" else 0; shift=mode=="topic_shift"
    stream,truth=build(seed,n,held,gap,shift)
    return {"surprise":eval_model(Surprise,stream,truth),"jacobian":eval_model(RetrievalJacobian,stream,truth)}

def summarize(raw):
    out={}
    for n,runs in raw.items():
        out[n]={}
        for mode in ("seen","held","long_gap","topic_shift","combined"):
            out[n][mode]={}
            for method in ("surprise","jacobian"):
                keys=runs[0][mode][method]
                out[n][mode][method]={k:statistics.mean(x[mode][method][k] for x in runs) for k in keys}
        out[n]["one_shot"]={m:statistics.mean(x["one_shot"][m] for x in runs) for m in ("surprise","jacobian")}
        out[n]["interference"]={m:statistics.mean(x["interference"][m] for x in runs) for m in ("surprise","jacobian")}
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="results_cycle_011.json"); a=ap.parse_args()
    raw={}
    for n in (48,192,384):
        runs=[]
        for seed in (1,7,19):
            x={m:run(seed,n,m) for m in ("seen","held","long_gap","topic_shift","combined")}
            x["one_shot"]=one_shot(seed); x["interference"]=interference(seed); runs.append(x)
        raw[str(n)]=runs
    payload={"hypothesis":"Retrieval-Jacobian Boundary Credit with Sparse Semantic Replay",
      "seeds":[1,7,19],"event_counts":[48,192,384],"raw":raw,"summary":summarize(raw),
      "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "complexity":"update O(HSQG) local-window self-supervised counterfactual retrieval; recall top-8 O(SG)",
      "learner_uses_hidden_labels":False,"free_japanese_gate":0.0,
      "highschool_level_passed":False,"native_japanese_communication_passed":False,
      "weak_smartphone_verified":False,"completion":False}
    with open(a.output,"w",encoding="utf-8") as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload["summary"]["384"],ensure_ascii=False,indent=2))
if __name__=="__main__": main()
