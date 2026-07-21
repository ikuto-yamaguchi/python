import random,time,json,pickle,resource,statistics,re
from collections import Counter
from dataclasses import dataclass

TEMPLATES=[
("{e}の保管場所は{v}です。","{e}はどこにありますか？"),
("{e}の担当者は{v}です。","{e}の担当は誰ですか？"),
("{e}の合言葉は{v}です。","{e}の合言葉を教えて。")]
PARAPHRASE=[
("{e}は{v}に保管されています。","{e}の置き場所は？"),
("{e}を担当するのは{v}です。","{e}を担当している人は？"),
("{e}では{v}を合言葉にします。","{e}で使う合言葉は？")]

def make_names(rng,n,prefix):
    chars=list("甲乙丙丁戊己庚辛壬癸春夏秋冬東西南北")
    return [prefix+''.join(rng.sample(chars,3))+str(i) for i in range(n)]

@dataclass(frozen=True)
class Schema:
    stmt_pattern:str
    q_pattern:str
    support:int

def pattern_from_example(statement,question,answer):
    # 言語辞書を使わず、statement/question間の最長共通部分をepisode entity候補とする。
    best=""
    for i in range(len(statement)):
        for j in range(i+1,len(statement)+1):
            x=statement[i:j]
            if len(x)>len(best) and x in question and x not in answer:
                best=x
    if not best or answer not in statement:
        return None
    return statement.replace(best,"{E}",1).replace(answer,"{V}",1), question.replace(best,"{E}",1)

def compile_pattern(pat):
    s=re.escape(pat).replace(re.escape("{E}"),"(?P<E>.+?)").replace(re.escape("{V}"),"(?P<V>.+?)")
    return re.compile("^"+s+"$")

class StructuralRebindingMemory:
    def __init__(self,consolidate=True):
        self.examples=[]
        self.schemas=[]
        self.bindings={}
        self.consolidate=consolidate
    def fit_example(self,s,q,a):
        self.examples.append((s,q,a))
    def sleep(self):
        if not self.consolidate:
            return
        counts=Counter(pattern_from_example(*x) for x in self.examples)
        self.schemas=[Schema(k[0],k[1],v) for k,v in counts.items() if k and v>=2]
    def observe_unlabeled(self,s):
        for idx,sc in enumerate(self.schemas):
            m=compile_pattern(sc.stmt_pattern).match(s)
            if m:
                self.bindings[(idx,m.group("E"))]=m.group("V")
                return True
        return False
    def query(self,q):
        for idx,sc in enumerate(self.schemas):
            m=compile_pattern(sc.q_pattern).match(q)
            if m:
                return self.bindings.get((idx,m.group("E")))
        return None

class RawEpisodicMemory:
    def __init__(self): self.raw=[]
    def fit_example(self,s,q,a): self.raw.append((s,q,a))
    def sleep(self): pass
    def observe_unlabeled(self,s): self.raw.append((s,"",None)); return True
    def query(self,q): return None

def run(seed=1,n_train=120,n_test=120):
    rng=random.Random(seed)
    entities=make_names(rng,n_train+n_test+50,"対象")
    values=make_names(rng,n_train+n_test+100,"値")
    train=[]
    for i in range(n_train):
        k=i%3; s,q=TEMPLATES[k]
        train.append((s.format(e=entities[i],v=values[i]),q.format(e=entities[i]),values[i]))
    models={"raw_episode":RawEpisodicMemory(),"rebinding":StructuralRebindingMemory(True),"no_consolidation":StructuralRebindingMemory(False)}
    t0=time.perf_counter()
    for x in train:
        for m in models.values(): m.fit_example(*x)
    for m in models.values(): m.sleep()
    train_sec=time.perf_counter()-t0
    out={}
    for name,m in models.items():
        one=[]; para=[]; lat=[]; updates=[]
        for i in range(n_train,n_train+n_test):
            k=i%3; s,q=TEMPLATES[k]
            st=s.format(e=entities[i],v=values[i]); qu=q.format(e=entities[i])
            m.observe_unlabeled(st)
            t=time.perf_counter(); pred=m.query(qu); lat.append((time.perf_counter()-t)*1000)
            one.append(pred==values[i])
        for i in range(n_train,n_train+n_test//2):
            k=i%3; s,q=PARAPHRASE[k]
            st=s.format(e=entities[i],v=values[i]); qu=q.format(e=entities[i])
            m.observe_unlabeled(st); para.append(m.query(qu)==values[i])
        for j in range(30):
            k=j%3; s,q=TEMPLATES[k]; e=entities[j]
            v1=values[-1-j]; v2=values[-40-j]
            m.observe_unlabeled(s.format(e=e,v=v1)); m.observe_unlabeled(s.format(e=e,v=v2))
            updates.append(m.query(q.format(e=e))==v2)
        out[name]={"oneshot":sum(one)/len(one),"paraphrase":sum(para)/len(para),"interference_latest":sum(updates)/len(updates),"latency_ms":statistics.mean(lat),"model_bytes":len(pickle.dumps(m)),"schemas":len(getattr(m,"schemas",[])),"bindings":len(getattr(m,"bindings",{}))}
    return {"seed":seed,"train_seconds":train_sec,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"results":out}

if __name__=="__main__":
    print(json.dumps([run(s) for s in (1,7,19)],ensure_ascii=False,indent=2))
