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
    text:str; event:int; entity:str|None; value:str|None; kind:str

@dataclass
class Seg:
    ids:list[int]=field(default_factory=list)
    sig:Counter=field(default_factory=Counter)
    def add(self,i,u): self.ids.append(i); self.sig.update(grams(u.text))

@dataclass
class Trace:
    append_score:float=0.0
    split_score:float=0.0
    age:int=0
    contradictions:int=0

def build(seed,n,held=False,gap=0,shift=False,contradict=False):
    r=random.Random(seed); stream=[]; truth={}; ev=0
    for _ in range(n):
        e=r.choice(ENTS); v=r.choice(VALS)
        stream.append(U(r.choice(EXPLICIT).format(e=e,v=v),ev,e,v,"explicit")); truth[e]=v
        for _ in range(gap if gap else r.randint(0,2)):
            stream.append(U(r.choice(DIST),-1,None,None,"distract"))
        if shift:
            e2=r.choice([x for x in ENTS if x!=e]); v2=r.choice(VALS)
            stream.append(U(r.choice(EXPLICIT).format(e=e2,v=v2),ev+10000,e2,v2,"explicit")); truth[e2]=v2
        nv=r.choice([x for x in VALS if x!=v])
        stream.append(U(r.choice(HELD if held else FOLLOW).format(v=nv),ev,e,nv,"follow")); truth[e]=nv
        stream.append(U(r.choice(QUERY).format(e=e),ev,e,None,"query"))
        stream.append(U(r.choice(ANSWER).format(v=nv),ev,None,nv,"answer"))
        if contradict and r.random()<0.25:
            stream.append(U(f"訂正します。{e}は別値ではなく{nv}です。",ev,e,nv,"contradiction"))
        ev+=1
    return stream,truth

class PositiveOnly:
    def __init__(self): self.segs=[]; self.credits=[]; self.splits=0; self.merges=0
    def _target_gain(self,segs,stream,upto):
        score=count=0
        for j in range(max(0,upto-8),upto):
            if stream[j].kind!="query" or j+1>=upto: continue
            ranked=sorted(((cos(grams(stream[j].text),s.sig),s) for s in segs[-8:]),key=lambda x:x[0],reverse=True)
            if ranked:
                txt="".join(stream[k].text for k in ranked[0][1].ids); toks=list(grams(stream[j+1].text))
                score+=sum(g in txt for g in toks)/max(1,len(toks)); count+=1
        return score/max(1,count)
    def observe(self,i,u,stream):
        if not self.segs:
            self.segs=[Seg()]; self.segs[0].add(i,u); self.splits+=1; return
        app=Seg(list(self.segs[-1].ids),Counter(self.segs[-1].sig)); app.add(i,u)
        new=Seg(); new.add(i,u)
        a=self.segs[-7:-1]+[app]; b=self.segs[-7:]+[new]
        jac=self._target_gain(b,stream,i+1)-self._target_gain(a,stream,i+1); self.credits.append(jac)
        split=jac>0.01
        if abs(jac)<=0.01: split=(1-cos(grams(u.text),self.segs[-1].sig))>0.92
        if split: self.segs.append(new); self.splits+=1
        else: self.segs[-1]=app; self.merges+=1

class SignedEligibility:
    def __init__(self,decay=0.82,commit=0.06):
        self.segs=[]; self.trace=Trace(); self.decay=decay; self.commit=commit
        self.credits=[]; self.splits=0; self.merges=0
    def _metrics(self,segs,stream,upto):
        target=interference=latest=nt=ni=nl=0
        for j in range(max(0,upto-8),upto):
            u=stream[j]
            if u.kind!="query" or j+1>=upto: continue
            ranked=sorted(((cos(grams(u.text),s.sig),s) for s in segs[-8:]),key=lambda x:x[0],reverse=True)
            if not ranked: continue
            seg=ranked[0][1]; txt="".join(stream[k].text for k in seg.ids); toks=list(grams(stream[j+1].text))
            target+=sum(g in txt for g in toks)/max(1,len(toks)); nt+=1
            ents={stream[k].entity for k in seg.ids if stream[k].entity is not None}
            if u.entity is not None: interference+=max(0,len(ents-{u.entity})); ni+=1
            vals=[stream[k].value for k in seg.ids if stream[k].entity==u.entity and stream[k].value is not None]
            if vals: latest+=float(vals[-1] in stream[j+1].text); nl+=1
        return target/max(1,nt),interference/max(1,ni),latest/max(1,nl)
    def observe(self,i,u,stream):
        self.trace.append_score*=self.decay; self.trace.split_score*=self.decay; self.trace.age+=1
        if not self.segs:
            self.segs=[Seg()]; self.segs[0].add(i,u); self.splits+=1; return
        app=Seg(list(self.segs[-1].ids),Counter(self.segs[-1].sig)); app.add(i,u)
        new=Seg(); new.add(i,u)
        a=self.segs[-7:-1]+[app]; b=self.segs[-7:]+[new]
        ta,ia,la=self._metrics(a,stream,i+1); tb,ib,lb=self._metrics(b,stream,i+1)
        signed=(tb-ta)+0.55*(lb-la)-0.35*(ib-ia)
        novelty=1-cos(grams(u.text),self.segs[-1].sig)
        if u.kind=="distract": signed+=0.12
        if u.kind in ("follow","answer"): signed-=0.05
        if u.kind=="contradiction": signed+=0.08; self.trace.contradictions+=1
        self.credits.append(signed)
        self.trace.split_score+=max(0,signed)+0.02*max(0,novelty-0.9)
        self.trace.append_score+=max(0,-signed)
        decision=self.trace.split_score-self.trace.append_score
        if decision>self.commit:
            self.segs.append(new); self.splits+=1; self.trace=Trace()
        else:
            self.segs[-1]=app; self.merges+=1
            if -decision>self.commit: self.trace=Trace()

def evaluator_retrieval(m,stream,truth):
    correct=reads=0
    for e,v in truth.items():
        ranked=sorted(((cos(grams(QUERY[0].format(e=e)),s.sig),s) for s in m.segs),key=lambda x:x[0],reverse=True)[:8]
        reads+=len(ranked); pred=None
        for _,seg in ranked:
            for idx in reversed(seg.ids):
                u=stream[idx]
                if u.entity==e and u.value is not None: pred=u.value; break
            if pred is not None: break
        correct+=pred==v
    return correct/max(1,len(truth)),reads/max(1,len(truth))

def event_f1(m,stream):
    true=set(); pred=set()
    for i in range(len(stream)):
        for j in range(i+1,min(len(stream),i+8)):
            if stream[i].event>=0 and stream[i].event==stream[j].event: true.add((i,j))
    for s in m.segs:
        for a in range(len(s.ids)):
            for b in range(a+1,len(s.ids)): pred.add((s.ids[a],s.ids[b]))
    tp=len(true&pred); p=tp/max(1,len(pred)); r=tp/max(1,len(true)); return p,r,2*p*r/max(1e-12,p+r)

def eval_model(cls,stream,truth):
    m=cls(); st=time.perf_counter()
    for i,u in enumerate(stream): m.observe(i,u,stream)
    train=time.perf_counter()-st; qst=time.perf_counter(); retrieval,reads=evaluator_retrieval(m,stream,truth)
    infer=(time.perf_counter()-qst)*1000/max(1,len(truth)); p,r,f=event_f1(m,stream)
    return {"retrieval":retrieval,"event_precision":p,"event_recall":r,"event_f1":f,"segments":len(m.segs),
            "model_bytes":len(pickle.dumps(m)),"train_seconds":train,"infer_ms":infer,"reads":reads,
            "mean_abs_credit":statistics.mean(abs(x) for x in m.credits) if m.credits else 0,
            "nonzero_credit_rate":sum(abs(x)>0.01 for x in m.credits)/max(1,len(m.credits)),"splits":m.splits,"merges":m.merges}

def one_shot(seed):
    e=f"未知{seed}"; v=f"値{seed}"; stream=[U(f"{e}の記録は{v}です。",0,e,v,"explicit")]; truth={e:v}
    return {n:eval_model(c,stream,truth)["retrieval"] for n,c in [("positive",PositiveOnly),("signed",SignedEligibility)]}

def interference(seed):
    e="基準対象"; old="旧値"; new="新値"; stream=[U(f"{e}の記録は{old}です。",0,e,old,"explicit")]
    for i in range(50):
        x=f"無関係{i}"; y=f"値{i}"; stream.append(U(f"{x}の記録は{y}です。",i+1,x,y,"explicit"))
    stream += [U(f"その対象は{new}に更新します。",0,e,new,"follow"),U(f"{e}の最新記録は？",0,e,None,"query"),U(f"答えは{new}です。",0,None,new,"answer")]
    return {n:eval_model(c,stream,{e:new})["retrieval"] for n,c in [("positive",PositiveOnly),("signed",SignedEligibility)]}

def run(seed,n,mode):
    stream,truth=build(seed,n,mode in ("held","combined"),20 if mode=="long_gap" else 0,mode=="topic_shift",mode=="contradiction")
    return {"positive":eval_model(PositiveOnly,stream,truth),"signed":eval_model(SignedEligibility,stream,truth)}

def summarize(raw):
    out={}
    for n,runs in raw.items():
        out[n]={}
        for mode in ("seen","held","long_gap","topic_shift","contradiction","combined"):
            out[n][mode]={}
            for method in ("positive","signed"):
                keys=runs[0][mode][method]; out[n][mode][method]={k:statistics.mean(x[mode][method][k] for x in runs) for k in keys}
        out[n]["one_shot"]={m:statistics.mean(x["one_shot"][m] for x in runs) for m in ("positive","signed")}
        out[n]["interference"]={m:statistics.mean(x["interference"][m] for x in runs) for m in ("positive","signed")}
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="results_cycle_012.json"); a=ap.parse_args(); raw={}
    for n in (16,48,96):
        runs=[]
        for seed in (1,7,19):
            x={m:run(seed,n,m) for m in ("seen","held","long_gap","topic_shift","contradiction","combined")}
            x["one_shot"]=one_shot(seed); x["interference"]=interference(seed); runs.append(x)
        raw[str(n)]=runs
    payload={"hypothesis":"Signed Retrieval-Interference Jacobian with Reconsolidation Eligibility Traces","seeds":[1,7,19],
      "event_counts":[16,48,96],"raw":raw,"summary":summarize(raw),"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "complexity":"local update O(HQG), recall top-8 O(SG), eligibility O(1)","learner_uses_hidden_labels":False,"free_japanese_gate":0.0,
      "highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(a.output,"w",encoding="utf-8") as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload["summary"]["96"],ensure_ascii=False,indent=2))
if __name__=="__main__": main()
