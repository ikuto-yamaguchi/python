from __future__ import annotations
import json, pickle, random, resource, statistics, time
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher

@dataclass
class Episode:
    before: str
    utterances: list[str]
    after: str
    followup: str
    op: str
    entity: str
    value: str

ENTITIES = ["試料A","試料B","青い箱","赤い容器","装置甲","装置乙","ポンプ一号","搬送機二号"]
VALUES = {
    "move": ["棚B","保管庫C","奥側区画","検査台D"],
    "temp": ["20度","25度","30度","低温域"],
    "mode": ["停止状態","待機状態","運転状態","検査モード"],
}
TRAIN_FORMS = {
    "move": ["{e}を{v}へ移して", "{e}は{v}に置いて", "{v}へ{e}を移動して"],
    "temp": ["{e}の温度を{v}に設定して", "{e}を{v}の温度にして", "温度は{v}、対象は{e}"],
    "mode": ["{e}を{v}に切り替えて", "{e}の状態を{v}へ変更して", "{v}にして、対象は{e}"],
}
HELD_ORDER = {
    "move": ["移動先は{v}、対象は{e}"],
    "temp": ["対象{e}について、設定温度は{v}"],
    "mode": ["対象{e}の新しい状態は{v}"],
}
HELD_SYNONYM = {
    "move": ["{e}を{v}まで運んで"],
    "temp": ["{e}の温度を{v}へ調整して"],
    "mode": ["{e}を{v}へ遷移させて"],
}
NONCE_E = ["ミラコフ","ネグサ粒子","未知体X7","ふわる対象","ケトラ装置","トルカ系","ペノラ体","ゾル機"]
NONCE_V = ["ゾル棚","42度域","未知工程Q","休止モード","ペノラ値","第九区画","中温域","観測状態Z"]

def state(e:str, op:str, v:str)->str:
    key={"move":"位置","temp":"温度","mode":"状態"}[op]
    return f"対象={e}；{key}={v}；記録=有効"

def episode(r:random.Random, op:str, forms:list[str], nonce=False)->Episode:
    es=NONCE_E if nonce else ENTITIES
    vs=NONCE_V if nonce else VALUES[op]
    e=r.choice(es); old=r.choice(vs); new=r.choice([x for x in vs if x!=old])
    utt=[f.format(e=e,v=new) for f in forms]
    return Episode(state(e,op,old),utt,state(e,op,new),f"更新後は{new}です",op,e,new)

def make_data(seed:int,n:int):
    r=random.Random(seed); train=[]
    for _ in range(n):
        op=r.choice(list(TRAIN_FORMS)); train.append(episode(r,op,TRAIN_FORMS[op],False))
    tests={k:[] for k in ("seen_view","held_order","held_synonym","rename","single_view","confound")}
    for _ in range(120):
        op=r.choice(list(TRAIN_FORMS))
        base=episode(r,op,TRAIN_FORMS[op],False)
        tests["seen_view"].append((base,r.choice(base.utterances)))
        eo=episode(r,op,HELD_ORDER[op],False);tests["held_order"].append((eo,eo.utterances[0]))
        es=episode(r,op,HELD_SYNONYM[op],False);tests["held_synonym"].append((es,es.utterances[0]))
        en=episode(r,op,TRAIN_FORMS[op],True);tests["rename"].append((en,r.choice(en.utterances)))
        sv=episode(r,op,[r.choice(TRAIN_FORMS[op])],False);tests["single_view"].append((sv,sv.utterances[0]))
        cf=episode(r,op,TRAIN_FORMS[op],False);cf.after=cf.before;tests["confound"].append((cf,r.choice(cf.utterances)))
    return train,tests

def ngrams(s,n=(2,3,4)):
    return Counter(g for k in n for g in (s[i:i+k] for i in range(max(0,len(s)-k+1))))

def cosine(a,b):
    if not a or not b:return 0.0
    dot=sum(v*b.get(k,0) for k,v in a.items());na=sum(v*v for v in a.values())**.5;nb=sum(v*v for v in b.values())**.5
    return dot/(na*nb) if na and nb else 0.0

def diff_signature(before,after):
    # maximal shared prefix/suffix quotient: episode-specific replacement is erased,
    # invariant boundary context is retained without semantic slot labels.
    p=0
    while p<min(len(before),len(after)) and before[p]==after[p]: p+=1
    q=0
    while q<min(len(before)-p,len(after)-p) and before[len(before)-1-q]==after[len(after)-1-q]: q+=1
    prefix=before[:p]
    segment=prefix.rsplit("；",1)[-1]
    boundary=segment.split("=",1)[0] if "=" in segment else segment[-4:]
    right=before[len(before)-q:len(before)-q+4] if q else ""
    return (("replace",boundary,right),)

def anti_frame(texts):
    # common subsequence literals across views; gaps become anonymous variables
    if not texts:return ()
    cur=list(texts[0])
    for t in texts[1:]:
        sm=SequenceMatcher(None,cur,list(t),autojunk=False)
        nxt=[]
        for a,b,k in sm.get_matching_blocks():
            if k:nxt.extend(cur[a:a+k])
        cur=nxt
    return tuple(cur)

def mask_episode_values(text,e,v):
    return text.replace(e,"¤E¤").replace(v,"¤V¤")

class TextOnlyMDL:
    def __init__(self):self.protos=[]
    def fit(self,eps):
        uniq={}
        for ep in eps:
            for u in ep.utterances:
                m=mask_episode_values(u,ep.entity,ep.value);uniq[(m,diff_signature(ep.before,ep.after))]=(ngrams(m),diff_signature(ep.before,ep.after))
        self.protos=list(uniq.values())
        return self
    def predict(self,u):
        q=ngrams(u);sc=defaultdict(float)
        for p,sig in self.protos:sc[sig]=max(sc[sig],cosine(q,p))
        best=sorted(sc.items(),key=lambda x:-x[1])
        return (best[0][0],best[0][1]-(best[1][1] if len(best)>1 else 0),len(self.protos)) if best else (None,0,0)

class CrossViewQuotient:
    def __init__(self):
        self.classes={};self.frame_bank=defaultdict(list);self.transition_counts=Counter()
    def fit(self,eps):
        buckets=defaultdict(list)
        for ep in eps:buckets[diff_signature(ep.before,ep.after)].append(ep)
        for sid,(sig,group) in enumerate(sorted(buckets.items(), key=lambda x:-len(x[1]))):
            cid=f"Q{sid}"; self.classes[cid]={"signature":sig,"support":len(group)}
            self.transition_counts[cid]=len(group)
            for ep in group:
                for u in ep.utterances:
                    masked=mask_episode_values(u,ep.entity,ep.value)
                    self.frame_bank[cid].append(ngrams(masked))
        return self
    def predict(self,u):
        q=ngrams(u);scores=[]
        for cid,bank in self.frame_bank.items():
            sample=bank[::max(1,len(bank)//12)][:12]
            sim=max((cosine(q,p) for p in sample),default=0)
            support=self.transition_counts[cid]
            score=sim+0.015*(support**.5)
            scores.append((score,cid,len(sample)))
        scores.sort(reverse=True)
        if not scores:return None,0,0
        margin=scores[0][0]-(scores[1][0] if len(scores)>1 else 0)
        return self.classes[scores[0][1]]["signature"],margin,sum(x[2] for x in scores)

def evaluate(seed,n):
    train,tests=make_data(seed,n)
    t=time.perf_counter();base=TextOnlyMDL().fit(train);tb=time.perf_counter()-t
    t=time.perf_counter();cv=CrossViewQuotient().fit(train);tc=time.perf_counter()-t
    def score(ds,model,abstain=False):
        ok=[];lat=[];reads=[];marg=[];ab=[]
        for ep,u in ds:
            q=time.perf_counter_ns();pred,margin,r=model.predict(u);lat.append((time.perf_counter_ns()-q)/1e6);reads.append(r);marg.append(margin)
            if abstain:
                a=margin<0.04;ab.append(int(a));ok.append(int(a))
            else:ok.append(int(pred==diff_signature(ep.before,ep.after)))
        return {"accuracy":statistics.mean(ok),"latency_ms":statistics.mean(lat),"reads":statistics.mean(reads),"margin":statistics.mean(marg),"abstention":statistics.mean(ab) if ab else 0}
    out={"seed":seed,"n_train":n,"base_bytes":len(pickle.dumps(base)),"cross_view_bytes":len(pickle.dumps(cv)),"base_train_s":tb,"cross_view_train_s":tc,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"quotient_classes":len(cv.classes)}
    for k,ds in tests.items():
        out["base_"+k]=score(ds,base,k=="confound")
        out["cross_"+k]=score(ds,cv,k=="confound")
    return out

if __name__=="__main__":
    results=[evaluate(s,n) for n in (60,240,720) for s in (1,7,19)]
    print(json.dumps(results,ensure_ascii=False,indent=2))
