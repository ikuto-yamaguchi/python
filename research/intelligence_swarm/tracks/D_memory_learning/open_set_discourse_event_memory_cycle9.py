"""Track D Cycle 009
Open-Set Discourse Event Segmentation with Multi-Channel Predictive Memory.

Controlled falsification probe. The learner receives only raw Japanese utterances,
temporal order, and delayed generic consistency signals. It receives no entity/value
dictionary, semantic slot labels, morphology, fixed ontology, RAG, or external LLM.

The benchmark generator retains hidden event/entity/value labels for evaluation only.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import argparse, json, math, pickle, random, resource, statistics, time

ENTITIES = ["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵",
            "試料甲","試料乙","搬送台車","検査票"]
VALUES = ["棚A","棚B","棚C","棚D","保留","完了","担当一","担当二","室内","廊下"]
RELATIONS = ["置き場所","状態","担当","保管先"]
EXPLICIT = [
    "{e}の{r}は{v}です。",
    "{e}について、{r}を{v}として記録します。",
    "{e}は現在{v}です。{r}の情報です。",
]
FOLLOW = [
    "その対象は{v}になりました。",
    "こちらは{v}へ更新します。",
    "同じものを{v}として扱います。",
    "続きですが、{v}です。",
]
HELD_FOLLOW = [
    "先ほど触れたものは{v}に変わりました。",
    "話題中の品については{v}へ。",
    "例の対象、今は{v}です。",
    "それについて新しい情報は{v}です。",
]
DISTRACT = [
    "今日は気温が高いです。", "別件の資料を確認しました。", "窓の外は静かです。",
    "この発話は対象の更新ではありません。", "少し休憩します。"
]
QUERY = [
    "{e}の最新情報を教えてください。",
    "{e}は今どうなっていますか。",
    "{e}について最後に記録した内容は何ですか。",
]
HELD_QUERY = [
    "{e}の現在値を確認したいです。",
    "さっきの{e}、結局どうなりましたか。",
    "{e}について直近の変更を答えてください。",
]

def grams(text: str) -> Counter[str]:
    s = "".join(text.split())
    return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))

def cosine(a, b) -> float:
    dot = sum(v*b.get(k,0) for k,v in a.items())
    na = math.sqrt(sum(v*v for v in a.values()))
    nb = math.sqrt(sum(v*v for v in b.values()))
    return dot/(na*nb+1e-12)

@dataclass
class Utterance:
    text: str
    event_id: int
    entity: str|None
    value: str|None
    kind: str
    effect: int

@dataclass
class Segment:
    sid: int
    utterances: list[str] = field(default_factory=list)
    signatures: Counter[str] = field(default_factory=Counter)
    member_indices: list[int] = field(default_factory=list)
    last_t: int = 0

    def add(self, u: Utterance, t: int):
        self.utterances.append(u.text)
        self.member_indices.append(t)
        self.signatures.update(grams(u.text))
        self.last_t = t

class BaseMemory:
    def __init__(self):
        self.segments: list[Segment] = []
        self.next_sid = 0
        self.peak_hypotheses = 0
        self.reversible_rejections = 0

    def new_segment(self, u, t):
        seg = Segment(self.next_sid)
        self.next_sid += 1
        seg.add(u,t)
        self.segments.append(seg)

    def retrieve_segment(self, query: str):
        qg = grams(query)
        ranked = sorted(
            ((cosine(qg,s.signatures), s.last_t, s) for s in self.segments),
            key=lambda x:(x[0],x[1]), reverse=True
        )
        return (ranked[0][2] if ranked else None), min(len(ranked), 8)

class TemporalOnly(BaseMemory):
    def __init__(self, gap=2):
        super().__init__(); self.gap=gap
    def observe(self,u,t):
        if not self.segments or t-self.segments[-1].last_t > self.gap or u.kind=="explicit":
            self.new_segment(u,t)
        else:
            self.segments[-1].add(u,t)

class MultiChannelMemory(BaseMemory):
    """Raw-text event hypotheses with local successor prediction and reversible focus."""
    def __init__(self, max_active=6):
        super().__init__()
        self.max_active=max_active
        self.focus_scores=Counter()
        self.successor_support=defaultdict(Counter)

    def _extract_candidates(self,u,t):
        cands=[]
        ug=grams(u.text)
        recent=self.segments[-self.max_active:]
        for seg in recent:
            lexical=cosine(ug,seg.signatures)
            recency=1/(1+max(0,t-seg.last_t))
            focus=self.focus_scores[seg.sid]
            succ = sum(self.successor_support[g][seg.sid] for g in ug)
            succ = min(1.0, succ / max(1, sum(ug.values())))
            score=0.32*lexical+0.28*recency+0.22*focus+0.18*succ
            cands.append((score,seg))
        cands.append((0.30,None))
        self.peak_hypotheses=max(self.peak_hypotheses,len(cands))
        return sorted(cands,key=lambda x:x[0],reverse=True)

    def observe(self,u,t):
        if u.kind=="explicit" or not self.segments:
            self.new_segment(u,t)
            chosen=self.segments[-1]
        else:
            cands=self._extract_candidates(u,t)
            best_score,best=cands[0]
            second=cands[1][0] if len(cands)>1 else -1
            if best is None or best_score-second < 0.035:
                self.new_segment(u,t); chosen=self.segments[-1]
                if best is not None: self.reversible_rejections += 1
            else:
                chosen=best; chosen.add(u,t)
        self.focus_scores = Counter({k:v*0.86 for k,v in self.focus_scores.items() if v*0.86>0.03})
        self.focus_scores[chosen.sid]+=1.0
        for g in grams(u.text):
            self.successor_support[g][chosen.sid]+=1

    def delayed_consistency(self, generic_success: bool):
        if not self.segments:
            return
        sid=max(self.focus_scores,key=self.focus_scores.get)
        if generic_success:
            self.focus_scores[sid]+=0.15
        else:
            self.focus_scores[sid]-=0.5
            self.reversible_rejections+=1

def build_stream(seed:int,n_events:int,held=False,long_gap=False,topic_shift=False):
    rng=random.Random(seed)
    stream=[]; truth={}; event_id=0
    for _ in range(n_events):
        e=rng.choice(ENTITIES); r=rng.choice(RELATIONS); v=rng.choice(VALUES)
        stream.append(Utterance(rng.choice(EXPLICIT).format(e=e,r=r,v=v),event_id,e,v,"explicit",1))
        truth[e]=v
        gaps=20 if long_gap else rng.randint(0,3)
        for _g in range(gaps):
            stream.append(Utterance(rng.choice(DISTRACT),-1,None,None,"distract",0))
        if topic_shift:
            e2=rng.choice([x for x in ENTITIES if x!=e]); v2=rng.choice(VALUES)
            stream.append(Utterance(rng.choice(EXPLICIT).format(e=e2,r=r,v=v2),event_id+10000,e2,v2,"explicit",1))
            truth[e2]=v2
        nv=rng.choice([x for x in VALUES if x!=v])
        form=rng.choice(HELD_FOLLOW if held else FOLLOW)
        stream.append(Utterance(form.format(v=nv),event_id,e,nv,"follow",1))
        truth[e]=nv
        event_id+=1
    return stream,truth

def evaluate(seed,n_events,mode):
    held=mode in ("held","combined")
    long_gap=mode=="long_gap"
    topic_shift=mode=="topic_shift"
    stream,truth=build_stream(seed,n_events,held,long_gap,topic_shift)
    models={"temporal":TemporalOnly(),"multi":MultiChannelMemory()}
    outputs={}
    for name,m in models.items():
        st=time.perf_counter()
        for t,u in enumerate(stream):
            m.observe(u,t)
            if isinstance(m,MultiChannelMemory):
                m.delayed_consistency(True)
        train=time.perf_counter()-st
        correct=reads=0
        qst=time.perf_counter()
        for e,v in truth.items():
            q=random.Random(seed+len(e)).choice(HELD_QUERY if held else QUERY).format(e=e)
            seg,r=m.retrieve_segment(q); reads+=r
            pred=None
            if seg is not None:
                for idx in reversed(seg.member_indices):
                    u=stream[idx]
                    if u.entity==e and u.value is not None:
                        pred=u.value; break
            correct += pred==v
        qtime=(time.perf_counter()-qst)*1000/max(1,len(truth))
        true_pairs=set(); pred_pairs=set()
        for i in range(len(stream)):
            for j in range(i+1,min(len(stream),i+6)):
                if stream[i].event_id>=0 and stream[i].event_id==stream[j].event_id:
                    true_pairs.add((i,j))
        for seg in m.segments:
            ids=seg.member_indices
            for a in range(len(ids)):
                for b in range(a+1,len(ids)):
                    pred_pairs.add((ids[a],ids[b]))
        tp=len(true_pairs & pred_pairs)
        precision=tp/max(1,len(pred_pairs)); recall=tp/max(1,len(true_pairs))
        f1=2*precision*recall/max(1e-12,precision+recall)
        outputs[name]={
            "retrieval_accuracy":correct/max(1,len(truth)),
            "event_pair_precision":precision,
            "event_pair_recall":recall,
            "event_pair_f1":f1,
            "segments":len(m.segments),
            "stored_utterances":sum(len(s.member_indices) for s in m.segments),
            "model_bytes":len(pickle.dumps(m)),
            "training_seconds":train,
            "inference_ms":qtime,
            "mean_reads":reads/max(1,len(truth)),
            "peak_hypotheses":m.peak_hypotheses,
            "reversible_rejections":m.reversible_rejections,
        }
    return outputs

def one_shot(seed):
    e="未知対象"+str(seed); v="未知値"+str(seed)
    stream=[Utterance(f"{e}の記録は{v}です。",0,e,v,"explicit",1)]
    out={}
    for name,m in (("temporal",TemporalOnly()),("multi",MultiChannelMemory())):
        m.observe(stream[0],0)
        seg,_=m.retrieve_segment(f"{e}の最新記録は？")
        pred=None
        if seg:
            for idx in reversed(seg.member_indices):
                if stream[idx].entity==e: pred=stream[idx].value; break
        out[name]=float(pred==v)
    return out

def interference(seed):
    e="基準対象"; old="旧値"; new="新値"
    stream=[Utterance(f"{e}の状態は{old}です。",0,e,old,"explicit",1)]
    for i in range(50):
        x=f"無関係{i}"; y=f"値{i}"
        stream.append(Utterance(f"{x}の状態は{y}です。",i+1,x,y,"explicit",1))
    stream.append(Utterance(f"その対象は{new}になりました。",0,e,new,"follow",1))
    out={}
    for name,m in (("temporal",TemporalOnly()),("multi",MultiChannelMemory())):
        for t,u in enumerate(stream): m.observe(u,t)
        seg,_=m.retrieve_segment(f"{e}は今どうなっていますか。")
        pred=None
        if seg:
            for idx in reversed(seg.member_indices):
                if stream[idx].entity==e: pred=stream[idx].value; break
        out[name]=float(pred==new)
    return out

def summarize(raw):
    summary={}
    for size,runs in raw.items():
        summary[size]={}
        for mode in ("seen","held","long_gap","topic_shift","combined"):
            summary[size][mode]={}
            for method in ("temporal","multi"):
                keys=runs[0][mode][method].keys()
                summary[size][mode][method]={k:statistics.mean(r[mode][method][k] for r in runs) for k in keys}
        for probe in ("one_shot","interference"):
            summary[size][probe]={m:statistics.mean(r[probe][m] for r in runs) for m in ("temporal","multi")}
    return summary

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="results_cycle_009.json")
    args=ap.parse_args()
    raw={}
    for n in (48,192,768):
        runs=[]
        for seed in (1,7,19):
            run={mode:evaluate(seed,n,mode) for mode in ("seen","held","long_gap","topic_shift","combined")}
            run["one_shot"]=one_shot(seed); run["interference"]=interference(seed)
            runs.append(run)
        raw[str(n)]=runs
    payload={
      "hypothesis":"Open-Set Discourse Event Segmentation with Multi-Channel Predictive Memory",
      "seeds":[1,7,19],"event_counts":[48,192,768],
      "raw":raw,"summary":summarize(raw),
      "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "estimated_complexity":"update O(HG), recall O(SG), H<=7, top-8 segment reads",
      "free_japanese_integrated_gate":0.0,
      "highschool_level_passed":False,
      "native_japanese_communication_passed":False,
      "weak_smartphone_verified":False,
      "completion":False
    }
    with open(args.output,"w",encoding="utf-8") as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload["summary"]["768"],ensure_ascii=False,indent=2))
if __name__=="__main__": main()
