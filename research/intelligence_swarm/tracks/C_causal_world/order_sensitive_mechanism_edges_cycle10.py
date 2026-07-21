"""Track C Cycle 010: Order-Sensitive Mechanism Edge Automata.

Controlled falsification probe for compositional causal world models.

Learner input:
- raw Japanese context/command/before/after strings
- temporal order of commands

Not provided:
- semantic slot labels
- entity/value dictionaries
- morphology
- fixed causal ontology
- mechanism names
- RAG/external LLM

Hidden mechanism/operation IDs are generator/evaluator-only. The learner induces:
1) command surface clusters from cross-episode n-gram overlap,
2) anonymous effect symbols from before/after edit signatures,
3) sparse state-conditioned transition edges over effect symbols,
4) order-sensitive pair composition.

This remains a controlled synthetic probe, not free-Japanese understanding.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass
import argparse, json, math, pickle, random, resource, statistics, time, difflib

OBJECTS=["試料甲","試料乙","搬送台","検査票","端末青","端末赤","箱一","箱二"]
PLACES=["棚A","棚B","室内","廊下"]
STATUS=["待機","作動","固定","解除"]

CONTEXT_TRAIN={
 "open_power":["電源経路は通っていて、入口も開いている。","給電は続いており、通路を使える。"],
 "closed_power":["電源は入っているが、入口は閉じている。","給電中だが、通り道が塞がれている。"],
 "open_no_power":["入口は開いているが、電源は落ちている。","通路は使える一方、給電されていない。"],
 "locked":["安全ロックが掛かり、入口も閉じている。","保護機構が作動し、通路が遮断されている。"],
 "override":["保守許可が出ており、安全ロックを一時解除できる。","点検権限により保護状態を上書きできる。"],
}
CONTEXT_HELD={
 "open_power":["動力供給は正常で、出入口の妨げもない。"],
 "closed_power":["稼働電力はあるものの、扉を通過できない。"],
 "open_no_power":["扉は妨げないが、動力が供給されていない。"],
 "locked":["安全装置が有効で、進入は許されていない。"],
 "override":["整備担当の特例で、安全制限を解除可能だ。"],
}
COMMANDS_TRAIN={
 "move":["{o}を{p}へ移動する。","{o}の置き先を{p}に変える。"],
 "activate":["{o}を作動させる。","{o}の運転を開始する。"],
 "unlock":["{o}の固定を解除する。","{o}を自由に動かせる状態へ戻す。"],
}
COMMANDS_HELD={
 "move":["{o}を{p}まで運搬する。"],
 "activate":["{o}を起動状態にする。"],
 "unlock":["{o}の拘束を解く。"],
}

@dataclass(frozen=True)
class HiddenState:
    place:str
    status:str
    locked:bool

def world_step(state:HiddenState, context_kind:str, op:str, place:str)->HiddenState:
    power=context_kind in ("open_power","closed_power","locked","override")
    passage=context_kind in ("open_power","open_no_power","override")
    override=context_kind=="override"
    locked=state.locked
    if op=="unlock":
        if override:
            return HiddenState(state.place,"解除",False)
        return state
    if op=="activate":
        if power and (not locked or override):
            return HiddenState(state.place,"作動",locked)
        return state
    if op=="move":
        if passage and not locked and state.status=="作動":
            return HiddenState(place,state.status,locked)
        return state
    return state

STATE_FORMS=[
 "{o}の場所は{p}、状態は{s}、固定は{l}。",
 "{o}について、{p}にあり、運転状態は{s}、拘束={l}。",
]
ALT_STATE_FORM="{o}は現在{p}。稼働={s}。安全拘束={l}。"

def render_state(rng,o,state,alt=False,form=None):
    f=ALT_STATE_FORM if alt else (form or rng.choice(STATE_FORMS))
    return f.format(o=o,p=state.place,s=state.status,l="有" if state.locked else "無")

def grams(text):
    s="".join(text.split())
    return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))

def cos(a,b):
    dot=sum(v*b.get(k,0) for k,v in a.items())
    na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return dot/(na*nb+1e-12)

def edit_signature(before,after):
    pre=0
    while pre<min(len(before),len(after)) and before[pre]==after[pre]: pre+=1
    suf=0
    while suf<min(len(before)-pre,len(after)-pre) and before[-1-suf]==after[-1-suf]: suf+=1
    old=before[pre:len(before)-suf if suf else len(before)]
    new=after[pre:len(after)-suf if suf else len(after)]
    return (old,new)

def normalize_command(command,before,after):
    out=command
    for source in (before,after):
        m=difflib.SequenceMatcher(None,out,source).find_longest_match(0,len(out),0,len(source))
        if m.size>=2:
            out=out[:m.a]+"<X>"+out[m.a+m.size:]
    return out

class SurfaceCompletion:
    def __init__(self):
        self.rows=[]
    def fit(self,episodes):
        for ep in episodes:
            self.rows.append((grams(ep["context"]),tuple(ep["effects"])))
        return self
    def predict(self,context,commands):
        if not self.rows:return None
        best=max(self.rows,key=lambda r:cos(grams(context),r[0]))
        return best[1][:len(commands)]

class MechanismAutomaton:
    def __init__(self):
        self.command_protos=defaultdict(Counter)
        self.transitions=defaultdict(Counter)
        self.start=defaultdict(Counter)
        self.effect_symbols={}
        self.next_effect=0
        self.cluster_representatives=[]
    def _effect(self,sig):
        if sig not in self.effect_symbols:
            self.effect_symbols[sig]=self.next_effect; self.next_effect+=1
        return self.effect_symbols[sig]
    def _cluster_command(self,residue,create=False):
        g=grams(residue)
        if not self.cluster_representatives:
            if create:
                self.cluster_representatives.append(g); return 0
            return None
        scores=[cos(g,p) for p in self.cluster_representatives]
        best=max(range(len(scores)),key=scores.__getitem__)
        if create and scores[best]<0.18:
            self.cluster_representatives.append(g); return len(self.cluster_representatives)-1
        if scores[best]<0.08:return None
        return best
    def fit(self,episodes):
        for ep in episodes:
            latent=0
            self.start[ep["context"]][latent]+=1
            for b,c,a in zip(ep["befores"],ep["commands"],ep["afters"]):
                sig=edit_signature(b,a); nxt=self._effect(sig)
                cluster=self._cluster_command(normalize_command(c,b,a),create=True)
                self.transitions[(latent,cluster)][nxt]+=1
                latent=nxt
        return self
    def predict(self,context,commands,befores):
        latent=0; outs=[]
        for c,b in zip(commands,befores):
            cluster=self._cluster_command(normalize_command(c,b,b),create=False)
            if cluster is None:return None
            dist=self.transitions.get((latent,cluster))
            if not dist:
                merged=Counter()
                for (s,k),v in self.transitions.items():
                    if k==cluster: merged.update(v)
                if not merged:return None
                if len(merged)>1 and merged.most_common(2)[0][1]==merged.most_common(2)[1][1]:
                    return None
                nxt=merged.most_common(1)[0][0]
            else:nxt=dist.most_common(1)[0][0]
            outs.append(nxt); latent=nxt
        return tuple(outs)

def generate_episode(rng,held_context=False,held_command=False,sequence_len=2,alt_state=False):
    context_kind=rng.choice(list(CONTEXT_TRAIN))
    context=rng.choice((CONTEXT_HELD if held_context else CONTEXT_TRAIN)[context_kind])
    obj=rng.choice(OBJECTS); place=rng.choice(PLACES)
    state=HiddenState(rng.choice(PLACES),rng.choice(["待機","作動"]),rng.random()<0.35)
    ops=[rng.choice(list(COMMANDS_TRAIN)) for _ in range(sequence_len)]
    if sequence_len>=2 and rng.random()<0.65:
        ops=rng.choice([["activate","move"],["unlock","activate"],["unlock","move"],["move","activate"]])
        ops=ops[:sequence_len]
    commands=[]; befores=[]; afters=[]; effects=[]; hidden_states=[state]
    state_form = None if alt_state else rng.choice(STATE_FORMS)
    for op in ops:
        before=render_state(rng,obj,state,alt_state,state_form)
        template=rng.choice((COMMANDS_HELD if held_command else COMMANDS_TRAIN)[op])
        cmd=template.format(o=obj,p=place)
        newstate=world_step(state,context_kind,op,place)
        after=render_state(rng,obj,newstate,alt_state,state_form)
        commands.append(cmd); befores.append(before); afters.append(after)
        effects.append(edit_signature(before,after))
        state=newstate; hidden_states.append(state)
    return {"context":context,"context_kind":context_kind,"commands":commands,
            "befores":befores,"afters":afters,"effects":effects,"ops":ops,
            "hidden_states":hidden_states}

def eval_model(model,rows,mechanism=False):
    correct=abst=0; t0=time.perf_counter()
    for ep in rows:
        pred=model.predict(ep["context"],ep["commands"],ep["befores"]) if mechanism else model.predict(ep["context"],ep["commands"])
        if pred is None:
            abst+=1; continue
        if mechanism:
            truth=tuple(model.effect_symbols.get(x,-999) for x in ep["effects"])
        else: truth=tuple(ep["effects"])
        correct+=pred==truth
    ms=(time.perf_counter()-t0)*1000/len(rows)
    return {"accuracy":correct/len(rows),"abstention":abst/len(rows),"ms":ms}

def run(seed,n):
    rng=random.Random(seed)
    train=[generate_episode(rng,False,False,rng.choice([1,2,3])) for _ in range(n)]
    base=SurfaceCompletion().fit(train)
    mech=MechanismAutomaton().fit(train)
    splits={
      "seen":[generate_episode(rng,False,False,2) for _ in range(60)],
      "held_context":[generate_episode(rng,True,False,2) for _ in range(60)],
      "held_command":[generate_episode(rng,False,True,2) for _ in range(60)],
      "held_both":[generate_episode(rng,True,True,2) for _ in range(60)],
      "order_counterfactual":[generate_episode(rng,False,False,3) for _ in range(60)],
      "alternate_state":[generate_episode(rng,False,False,2,True) for _ in range(60)],
    }
    out={"base":{},"mechanism":{}}
    for k,rows in splits.items():
        out["base"][k]=eval_model(base,rows,False)
        out["mechanism"][k]=eval_model(mech,rows,True)
    out["base"]["model_bytes"]=len(pickle.dumps(base))
    out["mechanism"]["model_bytes"]=len(pickle.dumps(mech))
    out["mechanism"]["effect_symbols"]=len(mech.effect_symbols)
    out["mechanism"]["command_clusters"]=len(mech.cluster_representatives)
    out["mechanism"]["transition_edges"]=len(mech.transitions)
    out["mechanism"]["candidate_reads"]=len(mech.cluster_representatives)
    return out

def summarize(raw):
    result={}
    for n,runs in raw.items():
        result[n]={}
        for method in ("base","mechanism"):
            result[n][method]={}
            for split in ("seen","held_context","held_command","held_both","order_counterfactual","alternate_state"):
                result[n][method][split]={m:statistics.mean(r[method][split][m] for r in runs) for m in ("accuracy","abstention","ms")}
            result[n][method]["model_bytes"]=statistics.mean(r[method]["model_bytes"] for r in runs)
        for metric in ("effect_symbols","command_clusters","transition_edges","candidate_reads"):
            result[n]["mechanism"][metric]=statistics.mean(r["mechanism"][metric] for r in runs)
    return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="results_cycle_010.json")
    args=ap.parse_args()
    t=time.perf_counter()
    raw={str(n):[run(seed,n) for seed in (1,7,19)] for n in (32,128,512)}
    payload={"hypothesis":"Order-Sensitive Mechanism Edge Automata from Intervention Deltas",
      "seeds":[1,7,19],"train_sizes":[32,128,512],"raw":raw,"summary":summarize(raw),
      "full_seconds":time.perf_counter()-t,
      "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "estimated_complexity":"train O(N*K*P), infer O(T*C*G), sparse transition lookup O(1)",
      "free_japanese_integrated_gate":0.0,"highschool_level_passed":False,
      "native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(args.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload["summary"]["512"],ensure_ascii=False,indent=2))
if __name__=="__main__":main()
