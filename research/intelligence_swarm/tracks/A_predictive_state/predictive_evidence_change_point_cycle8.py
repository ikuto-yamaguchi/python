"""Track A Cycle 008: Predictive Evidence-Channel Change-Point States.

Controlled falsification probe for event-driven predictive-state revision.
The model receives raw Japanese reply strings and delayed binary interaction
success/failure. The downstream signal never contains the hidden target value.

No pretrained model, tokenizer, morphology, hand-written reply dictionary,
fixed semantic ontology, RAG, or external LLM is used. Candidate worlds are
still supplied by the experiment, so this is not evidence of free-Japanese
structure induction.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import argparse, json, math, pickle, random, resource, statistics, time

PHRASES = [
    "はい、その理解で進めてください", "ええ、それで構いません", "その通りです",
    "いいえ、その理解ではありません", "違います。反対側です", "そうではないです",
    "了解しました", "少し考えます", "確認しました",
]
HELD = [
    "認識どおりでお願いします", "その線で続行して", "読み方を反転してください",
    "別の側に切り替えて", "一旦保留します", "判断材料が足りません",
]


def grams(text: str) -> Counter[str]:
    s = "".join(text.split())
    return Counter(s[i:i+n] for n in (2,3,4) for i in range(max(0, len(s)-n+1)))


def cosine(a: Counter[str], b: Counter[str]) -> float:
    dot = sum(v*b.get(k,0) for k,v in a.items())
    na = math.sqrt(sum(v*v for v in a.values())); nb = math.sqrt(sum(v*v for v in b.values()))
    return dot/(na*nb+1e-12)


@dataclass
class Prototype:
    text: str
    pos: float = 1.0
    neg: float = 1.0
    unknown: float = 1.0
    run_length: int = 0
    surprise_run: int = 0
    changes: int = 0

    def probs(self):
        z = self.pos+self.neg+self.unknown
        return self.pos/z, self.neg/z, self.unknown/z

    def update(self, label: int|None, decay: float=1.0):
        self.pos *= decay; self.neg *= decay; self.unknown *= decay
        if label == 1: self.pos += 1
        elif label == 0: self.neg += 1
        else: self.unknown += 1
        self.run_length += 1


class StaticChannel:
    def __init__(self):
        self.protos: dict[str, Prototype] = {}

    def observe(self, speaker: str, text: str, label: int|None):
        p = self.protos.setdefault(text, Prototype(text))
        p.update(label)

    def interpret(self, speaker: str, text: str):
        q=grams(text); scored=[]
        for p in self.protos.values():
            sim=cosine(q, grams(p.text)); pp,pn,pu=p.probs()
            label=max(((pp,1),(pn,0),(pu,None)), key=lambda x:x[0])[1]
            conf=max(pp,pn,pu)*sim
            scored.append((conf,label))
        if not scored: return None,0.0,0
        scored.sort(reverse=True,key=lambda x:x[0]); conf,label=scored[0]
        if conf<0.34: return None,conf,min(5,len(scored))
        return label,conf,min(5,len(scored))


class DecayChannel(StaticChannel):
    def observe(self, speaker, text, label):
        p=self.protos.setdefault(text,Prototype(text)); p.update(label,decay=0.94)


class ChangePointChannel:
    """Speaker-local event-driven evidence states with reversible resets."""
    def __init__(self, trigger: int=2, confirm: int=3):
        self.global_protos: dict[str,Prototype] = {}
        self.local: dict[tuple[str,str],Prototype] = {}
        self.trigger=trigger; self.confirm=confirm
        self.tentative: dict[tuple[str,str],Prototype] = {}
        self.rollback_count=0; self.change_count=0

    def _base(self,text):
        if text not in self.global_protos: self.global_protos[text]=Prototype(text)
        return self.global_protos[text]

    def interpret(self,speaker,text):
        key=(speaker,text)
        if key in self.tentative: p=self.tentative[key]
        elif key in self.local: p=self.local[key]
        else:
            q=grams(text); best=None
            for p0 in self.global_protos.values():
                sim=cosine(q,grams(p0.text))
                if best is None or sim>best[0]: best=(sim,p0)
            if best is None or best[0]<0.42: return None,0.0,min(5,len(self.global_protos))
            p=best[1]
        pp,pn,pu=p.probs(); ranked=sorted(((pp,1),(pn,0),(pu,None)),reverse=True,key=lambda x:x[0])
        conf=ranked[0][0]-ranked[1][0]
        if conf<0.22: return None,conf,min(5,max(1,len(self.global_protos)))
        return ranked[0][1],conf,min(5,max(1,len(self.global_protos)))

    def observe(self,speaker,text,label,predicted=None):
        self._base(text).update(label,decay=0.997)
        key=(speaker,text)
        current=self.tentative.get(key) or self.local.setdefault(key, Prototype(text))
        error = predicted is not None and label is not None and predicted != label
        agree = predicted == label and label is not None
        if key in self.tentative:
            t=self.tentative[key]; t.update(label,decay=0.9)
            if agree:
                t.surprise_run=0
                if t.run_length>=self.confirm:
                    self.local[key]=t; del self.tentative[key]; self.change_count+=1
            elif error:
                t.surprise_run+=1
            else:
                t.surprise_run+=1
            if t.surprise_run>=self.trigger:
                del self.tentative[key]; self.rollback_count+=1
            return
        if error:
            current.surprise_run+=1
            if current.surprise_run>=self.trigger:
                t=Prototype(text, pos=0.25, neg=0.25, unknown=0.25)
                t.update(label); self.tentative[key]=t; current.surprise_run=0
        else:
            current.surprise_run=max(0,current.surprise_run-1); current.update(label,decay=0.995)


@dataclass
class Episode:
    speaker: str
    text: str
    label: int|None
    target_side: int


def stream(seed:int, length:int, scenario:str):
    rng=random.Random(seed)
    speakers=["話者甲","話者乙","話者丙"]
    base_map={PHRASES[i]: (1 if i<3 else 0 if i<6 else None) for i in range(len(PHRASES))}
    held_map={HELD[i]: (1 if i<2 else 0 if i<4 else None) for i in range(len(HELD))}
    mapping={s:dict(base_map) for s in speakers}
    for t in range(length):
        speaker=rng.choice(speakers); phase=t/length
        if scenario=="abrupt" and phase>=0.45:
            mapping[speaker]={k:(1-v if v is not None else None) for k,v in base_map.items()}
        elif scenario=="speaker" and speaker=="話者乙" and phase>=0.35:
            mapping[speaker]={k:(1-v if v is not None else None) for k,v in base_map.items()}
        elif scenario=="temporary" and 0.35<=phase<0.55:
            mapping[speaker]={k:(1-v if v is not None else None) for k,v in base_map.items()}
        elif scenario=="gradual" and phase>=0.25:
            prob=min(1.0,(phase-0.25)/0.5); m={}
            for k,v in base_map.items():
                m[k]=(1-v if v is not None and rng.random()<prob else v)
            mapping[speaker]=m
        else:
            mapping[speaker]=dict(base_map)
        if scenario=="held" and phase>=0.45:
            text=rng.choice(HELD); label=held_map[text]
        else:
            text=rng.choice(PHRASES); label=mapping[speaker][text]
        yield Episode(speaker,text,label,rng.randrange(2))


def run(method, seed, scenario, length=1200, warmup=180):
    for ep in stream(seed,warmup,"stable"):
        method.observe(ep.speaker,ep.text,ep.label)
    correct=wrong=abstain=reads=0; adaptation=[]
    start=time.perf_counter()
    for i,ep in enumerate(stream(seed+7,length,scenario)):
        pred,conf,r=method.interpret(ep.speaker,ep.text); reads+=r
        if pred is None or ep.label is None:
            abstain+=1; ok=None
        else:
            chosen=ep.target_side if pred==ep.label else 1-ep.target_side
            ok=chosen==ep.target_side; correct+=int(ok); wrong+=int(not ok)
        inferred_label = ep.label if ok is not None else None
        try: method.observe(ep.speaker,ep.text,inferred_label,predicted=pred)
        except TypeError: method.observe(ep.speaker,ep.text,inferred_label)
        if scenario in ("abrupt","speaker","temporary") and i>=int(length*0.45) and len(adaptation)<20:
            adaptation.append(0 if ok is None else int(ok))
    elapsed=(time.perf_counter()-start)*1000/length
    coverage=(correct+wrong)/length
    return {
        "accuracy_all":correct/length,"coverage":coverage,
        "selective_accuracy":correct/max(1,correct+wrong),
        "wrong_commit_rate":wrong/length,"abstention_rate":abstain/length,
        "first20_post_change_accuracy":statistics.mean(adaptation) if adaptation else None,
        "candidate_reads":reads/length,"ms_per_episode":elapsed,
        "change_count":getattr(method,"change_count",0),
        "rollback_count":getattr(method,"rollback_count",0),
        "model_bytes":len(pickle.dumps(method)),
    }


def evaluate(seed:int):
    out={}
    for name,ctor in (("static",StaticChannel),("decay",DecayChannel),("change_point",ChangePointChannel)):
        out[name]={scenario:run(ctor(),seed,scenario) for scenario in ("stable","abrupt","speaker","temporary","gradual","held")}
    return out


def summarize(raw):
    out={}
    for method in ("static","decay","change_point"):
        out[method]={}
        for scenario in ("stable","abrupt","speaker","temporary","gradual","held"):
            keys=[k for k,v in raw[0][method][scenario].items() if isinstance(v,(int,float)) and not isinstance(v,bool)]
            out[method][scenario]={k:statistics.mean(r[method][scenario][k] for r in raw) for k in keys}
    return out


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="results_cycle_008.json")
    args=ap.parse_args(); seeds=[1,7,19]
    started=time.perf_counter(); raw=[evaluate(s) for s in seeds]
    payload={
        "hypothesis":"Predictive Evidence-Channel Change-Point States",
        "seeds":seeds,"stream_length":1200,"warmup":180,
        "raw":raw,"summary":summarize(raw),
        "runtime_seconds":time.perf_counter()-started,
        "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "estimated_complexity":"interpret O(PG), sparse local top-state update O(1); P<=15",
        "outcome_contains_target_value":False,"free_japanese_integrated_gate":0.0,
        "highschool_level_passed":False,"native_japanese_communication_passed":False,
        "weak_smartphone_verified":False,"completion":False,
    }
    with open(args.output,"w",encoding="utf-8") as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload["summary"],ensure_ascii=False,indent=2))

if __name__=="__main__": main()
