"""Track D cycle 008: effect-grounded discourse-focus fast weights.

Controlled falsification probe for episodic coreference and continual memory.
The learner receives raw Japanese strings and quoted spans. It has no entity or
relation dictionary, tokenizer, morphology, fixed ontology, RAG, vector DB, or
external model.

Important limitation: delayed grounding contains an explicit entity mention.
Therefore delayed repair is evaluated separately from immediate coreference and
must not be reported as immediate language understanding.
"""
from __future__ import annotations
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
import argparse, json, math, pickle, random, resource, statistics, time

NAMES = ["装置甲","装置乙","試料赤","試料青","部品春","部品秋","箱ひとつ","箱ふたつ",
         "端末北","端末南","記録板A","記録板B"]
VALUES = ["棚A","棚B","棚C","棚D","区画東","区画西","保留","稼働","停止","点検中"]
INTRO = [
    "候補として「{a}」と「{b}」を確認します。",
    "話題には「{a}」、それから「{b}」があります。",
    "対象一覧は「{a}」および「{b}」です。",
]
TRAIN_FIRST = ["最初に挙げた方を中心にします。","先の対象について続けます。","前の候補を扱います。"]
TRAIN_SECOND = ["後から挙げた方を中心にします。","次の対象について続けます。","後の候補を扱います。"]
HELD_FIRST = ["冒頭側へ話を戻します。","一番手のものを見ます。","前段の対象が主題です。"]
HELD_SECOND = ["末尾側へ焦点を移します。","二番手のものを見ます。","後段の対象が主題です。"]
AMBIG = ["この件を続けます。","対象について更新します。","それを確認します。"]
PRON_UPDATE = ["それの状態は「{v}」です。","その対象を「{v}」として記録します。","続いて「{v}」へ更新します。"]
CONFIRM = [
    "後続の点検では「{e}」の更新内容と一致しました。",
    "操作ログ上、「{e}」への更新として整合しました。",
    "確認結果は「{e}」を対象とした処理でした。",
]
DISTRACT = ["天気の話をしました。","別件の資料を確認しました。","雑談を挟みました。","時計を見ました。"]
Q = ["「{e}」の現在値は？","現在の「{e}」について答えてください。","記憶上、「{e}」はどうなっていますか？"]

def ngrams(s: str) -> Counter[str]:
    compact = ''.join(s.split())
    return Counter(compact[i:i+n] for n in (2,3,4) for i in range(max(0,len(compact)-n+1)))

def cosine(a: Counter[str], b: Counter[str]) -> float:
    dot=sum(v*b.get(k,0) for k,v in a.items())
    na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return dot/(na*nb+1e-12)

def quoted(s: str) -> list[str]:
    out=[]; start=None
    for i,ch in enumerate(s):
        if ch=="「" and start is None: start=i+1
        elif ch=="」" and start is not None:
            if i>start: out.append(s[start:i])
            start=None
    return out

def cue_residue(s: str) -> str:
    out=s
    for q in quoted(s): out=out.replace(f"「{q}」","<Q>")
    return out

@dataclass
class FocusHypothesis:
    entity: str
    rank: int
    score: float

class RecencyMemory:
    def __init__(self):
        self.values={}
        self.recent=deque(maxlen=16)
    def introduce(self,a,b):
        self.recent.extend([a,b])
    def update(self,value):
        if self.recent: self.values[self.recent[-1]]=value
    def answer(self,e): return self.values.get(e)
    def size(self): return len(pickle.dumps(self))

class DiscourseFocusMemory:
    def __init__(self, max_candidates=4):
        self.max_candidates=max_candidates
        self.values={}
        self.recent=deque(maxlen=16)
        self.cue_rank: dict[str,Counter[int]]=defaultdict(Counter)
        self.fast_hypotheses: list[FocusHypothesis]=[]
        self.pending: tuple[str,list[FocusHypothesis],str]|None=None
        self.revocations=0
        self.consolidations=0
        self.fast_updates=0
        self.reads=0

    def train_cue(self,cue,a,b,confirmed):
        rank=0 if confirmed==a else 1
        self.cue_rank[cue_residue(cue)][rank]+=1

    def introduce(self,a,b):
        self.recent.extend([a,b])

    def propose_focus(self,cue,a,b):
        q=ngrams(cue_residue(cue))
        scored=[]
        for pattern,counts in self.cue_rank.items():
            sim=cosine(q,ngrams(pattern))
            total=sum(counts.values())
            for rank,count in counts.items():
                scored.append((sim*count/total,rank))
        byrank={0:0.0,1:0.0}
        for s,r in scored: byrank[r]=max(byrank[r],s)
        hs=[FocusHypothesis(a,0,byrank[0]),FocusHypothesis(b,1,byrank[1])]
        hs.sort(key=lambda h:h.score,reverse=True)
        self.fast_hypotheses=hs[:self.max_candidates]
        self.reads += min(5,len(self.cue_rank))
        return self.fast_hypotheses

    def update_pronoun(self,cue,a,b,value):
        hs=self.propose_focus(cue,a,b)
        if not hs: return
        margin=hs[0].score-(hs[1].score if len(hs)>1 else 0)
        self.pending=(value,hs,cue_residue(cue))
        self.fast_updates += len(hs)
        if hs[0].score>0.15 and margin>0.035:
            self.values[hs[0].entity]=value

    def ground(self,confirmation):
        vals=quoted(confirmation)
        if not vals or self.pending is None: return
        confirmed=vals[0]
        value,hs,pattern=self.pending
        matching=[h for h in hs if h.entity==confirmed]
        if not matching:
            self.revocations += 1
            self.pending=None
            return
        for h in hs:
            if h.entity!=confirmed and self.values.get(h.entity)==value:
                del self.values[h.entity]
                self.revocations += 1
        self.values[confirmed]=value
        rank=matching[0].rank
        self.cue_rank[pattern][rank]+=1
        self.consolidations += 1
        self.pending=None

    def answer(self,e): return self.values.get(e)
    def size(self): return len(pickle.dumps(self))

def make_dialogue(rng, cue_mode="seen", gap=0, topic_shift=False, ambiguous=False):
    a,b=rng.sample(NAMES,2); target_rank=rng.randrange(2); target=(a,b)[target_rank]
    v=rng.choice(VALUES)
    if ambiguous:
        cue=rng.choice(AMBIG)
    elif cue_mode=="seen":
        cue=rng.choice(TRAIN_FIRST if target_rank==0 else TRAIN_SECOND)
    else:
        cue=rng.choice(HELD_FIRST if target_rank==0 else HELD_SECOND)
    intro=rng.choice(INTRO).format(a=a,b=b)
    update=rng.choice(PRON_UPDATE).format(v=v)
    conf=rng.choice(CONFIRM).format(e=target)
    distract=[rng.choice(DISTRACT) for _ in range(gap)]
    if topic_shift:
        c=rng.choice([x for x in NAMES if x not in (a,b)])
        distract.insert(len(distract)//2,f"途中で「{c}」の別件を確認しました。")
    return dict(a=a,b=b,target=target,value=v,cue=cue,intro=intro,update=update,
                confirm=conf,distract=distract)

def train(seed,n):
    rng=random.Random(seed)
    mem=DiscourseFocusMemory()
    t0=time.perf_counter()
    for _ in range(n):
        d=make_dialogue(rng,"seen")
        mem.introduce(d["a"],d["b"])
        mem.train_cue(d["cue"],d["a"],d["b"],d["target"])
        mem.update_pronoun(d["cue"],d["a"],d["b"],d["value"])
        mem.ground(d["confirm"])
    return mem,time.perf_counter()-t0

def score_dialogues(model,baseline,dialogs,delayed=False):
    hit_m=hit_b=abst_m=0
    start=time.perf_counter()
    for d in dialogs:
        model.introduce(d["a"],d["b"]); baseline.introduce(d["a"],d["b"])
        baseline.update(d["value"])
        model.update_pronoun(d["cue"],d["a"],d["b"],d["value"])
        if delayed: model.ground(d["confirm"])
        pm=model.answer(d["target"]); pb=baseline.answer(d["target"])
        hit_m += pm==d["value"]; hit_b += pb==d["value"]; abst_m += pm is None
    elapsed=(time.perf_counter()-start)*1000/max(1,len(dialogs))
    return {"focus_accuracy":hit_m/len(dialogs),"recency_accuracy":hit_b/len(dialogs),
            "focus_abstention":abst_m/len(dialogs),"ms_per_dialogue":elapsed}

def eval_run(seed,n):
    rng=random.Random(seed+5000)
    trained,train_s=train(seed,n)
    result={}
    specs={
        "seen_immediate":("seen",0,False,False,False),
        "held_immediate":("held",0,False,False,False),
        "held_delayed":("held",0,False,False,True),
        "long_gap":("seen",20,False,False,False),
        "topic_shift":("seen",8,True,False,False),
        "ambiguous":("seen",0,False,True,False),
    }
    for name,(mode,gap,shift,ambig,delayed) in specs.items():
        dialogs=[make_dialogue(rng,mode,gap,shift,ambig) for _ in range(180)]
        model=pickle.loads(pickle.dumps(trained)); base=RecencyMemory()
        result[name]=score_dialogues(model,base,dialogs,delayed)

    bridge_hits=[]; base_hits=[]
    for _ in range(100):
        d1=make_dialogue(rng,"held")
        d2=make_dialogue(rng,"held")
        rank=0 if d1["target"]==d1["a"] else 1
        d2["cue"]=d1["cue"]
        d2["target"]=(d2["a"],d2["b"])[rank]
        model=pickle.loads(pickle.dumps(trained)); base=RecencyMemory()
        model.introduce(d1["a"],d1["b"]); model.update_pronoun(d1["cue"],d1["a"],d1["b"],d1["value"]); model.ground(d1["confirm"])
        model.introduce(d2["a"],d2["b"]); model.update_pronoun(d2["cue"],d2["a"],d2["b"],d2["value"])
        base.introduce(d2["a"],d2["b"]); base.update(d2["value"])
        bridge_hits.append(model.answer(d2["target"])==d2["value"])
        base_hits.append(base.answer(d2["target"])==d2["value"])
    result["one_shot_bridge"]={"focus_accuracy":sum(bridge_hits)/len(bridge_hits),
                               "recency_accuracy":sum(base_hits)/len(base_hits)}

    model=pickle.loads(pickle.dumps(trained)); base=RecencyMemory(); truth={}
    for i in range(80):
        d=make_dialogue(rng,"seen"); truth[d["target"]]=d["value"]
        model.introduce(d["a"],d["b"]); model.update_pronoun(d["cue"],d["a"],d["b"],d["value"]); model.ground(d["confirm"])
        base.introduce(d["a"],d["b"]); base.update(d["value"])
        for _ in range(10): rng.choice(DISTRACT)
    pairs=list(truth.items())
    result["continual_latest"]={
        "focus_accuracy":sum(model.answer(e)==v for e,v in pairs)/max(1,len(pairs)),
        "recency_accuracy":sum(base.answer(e)==v for e,v in pairs)/max(1,len(pairs)),
    }
    result.update(training_seconds=train_s,model_bytes=trained.size(),schema_count=len(trained.cue_rank),
                  fast_updates=trained.fast_updates,consolidations=trained.consolidations,
                  revocations=trained.revocations,local_reads=min(5,len(trained.cue_rank)))
    return result

def summarize(raw):
    out={}
    for n,runs in raw.items():
        out[n]={}
        for split in ("seen_immediate","held_immediate","held_delayed","long_gap","topic_shift","ambiguous"):
            out[n][split]={k:statistics.mean(r[split][k] for r in runs) for k in runs[0][split]}
        for split in ("one_shot_bridge","continual_latest"):
            out[n][split]={k:statistics.mean(r[split][k] for r in runs) for k in runs[0][split]}
        for k in ("training_seconds","model_bytes","schema_count","fast_updates","consolidations","revocations","local_reads"):
            out[n][k]=statistics.mean(r[k] for r in runs)
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="results_cycle_008.json"); args=ap.parse_args()
    raw={str(n):[eval_run(s,n) for s in (1,7,19)] for n in (48,192,768)}
    payload={
        "hypothesis":"Effect-Grounded Bidirectional Discourse-Focus Fast Weights",
        "seeds":[1,7,19],"train_sizes":[48,192,768],"raw":raw,"summary":summarize(raw),
        "delayed_grounding_explicitly_mentions_entity":True,
        "estimated_complexity":"train O(NG); propose O(PG) with top-5 reads; fast update O(H), H=2",
        "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "free_japanese_integrated_gate":0.0,"highschool_level_passed":False,
        "native_japanese_communication_passed":False,"weak_smartphone_verified":False,
        "completion":False,
    }
    with open(args.output,"w",encoding="utf-8") as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload["summary"]["768"],ensure_ascii=False,indent=2))
    print("peak_rss_kib",payload["peak_rss_kib_runtime_included"])
if __name__=="__main__": main()
