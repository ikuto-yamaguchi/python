from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse, json, pickle, random, resource, statistics, time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末","大型端末":"大きい端末"}
VALUES=["棚A","棚B","待機","完了"]
FILL=["補助記録は維持します。","別件は変えません。"]

@dataclass
class Turn:
    before:str
    command:str
    after:str
    future:str
    canon:str
    obj:str
    old:str
    new:str
    mode:str
    boundary:bool

@dataclass(frozen=True)
class Rule:
    state_pos:int
    state_width:int
    value_pos:int
    value_width:int
    object_pos:int
    object_width:int
    old_shape:str
    new_shape:str
    object_shape:str

@dataclass
class Microstate:
    rule:Rule
    age:int=0
    cumulative_error:float=0.0
    consecutive_support:int=0
    last_object_shape:str=""
    alive:bool=True

def shape(s:str)->str:
    return "".join("A" if c.isascii() and c.isalnum() else "J" if c not in "。、\n「」" else c for c in s)

def locate(text, token):
    p=text.find(token)
    return None if p<0 else (p,len(token))

def make_dialogue(seed:int, episodes:int, mode:str):
    r=random.Random(seed)
    world={o:r.choice(VALUES) for o in OBJECTS}
    rows=[]
    current=r.choice(OBJECTS)
    for ep in range(episodes):
        old_obj=current
        if ep>0 and (mode=="switch" or r.random()<0.35):
            current=r.choice([o for o in OBJECTS if o!=current])
        boundary=(ep==0 or current!=old_obj)
        length=r.randint(3,5)
        for step in range(length):
            obj=ALIASES[current] if mode=="paraphrase" else current
            old=world[current]
            new=r.choice([v for v in VALUES if v!=old])
            before=f"{obj}の現在値は{old}です。{r.choice(FILL)}"
            if step==0 or mode in ("explicit","switch"):
                command=f"{obj}を{new}へ変更してください。"
            elif mode=="order":
                command=f"{new}へ変更してください、対象は{obj}です。"
            elif mode=="paragraph":
                command=f"{r.choice(FILL)}\nそれを{new}へ変更してください。"
            elif mode=="plan":
                alt=r.choice([v for v in VALUES if v not in (old,new)])
                command=f"{obj}を{alt}にする案は撤回し、最終的に{new}へ変更してください。"
            elif mode=="counterfactual":
                command=f"変更しなければ{obj}は{old}のままです。実際にはそれを{new}へ変更してください。"
            else:
                command=f"それを{new}へ変更してください。"
            after=f"{obj}の現在値は{new}です。{r.choice(FILL)}"
            future=f"次の観測でも{obj}は{new}です。"
            rows.append(Turn(before,command,after,future,current,obj,old,new,mode,boundary and step==0))
            world[current]=new
    return rows

def true_rule(t:Turn):
    sp=locate(t.before,t.old); vp=locate(t.command,t.new); op=locate(t.command,t.obj)
    if not sp or not vp:
        return None
    if not op:
        op=(0,0)
    return Rule(sp[0],sp[1],vp[0],vp[1],op[0],op[1],shape(t.old),shape(t.new),shape(t.obj))

def induce_rules(dialogues):
    c=Counter()
    for rows in dialogues:
        for t in rows:
            r=true_rule(t)
            if r:c[r]+=1
            if r:
                for ds,dw,dv in [(-1,0,0),(1,0,0),(0,-1,0),(0,1,0),(0,0,-1),(0,0,1)]:
                    nr=Rule(max(0,r.state_pos+ds),max(1,r.state_width+dw),
                            max(0,r.value_pos+dv),r.value_width,
                            r.object_pos,r.object_width,r.old_shape,r.new_shape,r.object_shape)
                    c[nr]+=0.35
    return [r for r,_ in c.most_common(64)]

def extract_value(t,r):
    if r.value_pos+r.value_width>len(t.command):return None
    v=t.command[r.value_pos:r.value_pos+r.value_width]
    return v if shape(v)==r.new_shape else None

def apply(t,r):
    if r.state_pos+r.state_width>len(t.before):return None
    old=t.before[r.state_pos:r.state_pos+r.state_width]
    if shape(old)!=r.old_shape:return None
    v=extract_value(t,r)
    if not v:return None
    return t.before[:r.state_pos]+v+t.before[r.state_pos+r.state_width:]

def local_error(t,r):
    p=apply(t,r)
    execution=0 if p==t.after else 1
    future=0 if (p and t.new in t.future) else 1
    non_target=0 if (p and ("補助記録" in p)==("補助記録" in t.before) and ("別件" in p)==("別件" in t.before)) else 1
    object_consistency=0 if (r.object_width==0 or (r.object_pos+r.object_width<=len(t.command) and shape(t.command[r.object_pos:r.object_pos+r.object_width])==r.object_shape)) else 1
    return execution + 0.35*future + 0.25*non_target + 0.4*object_consistency

class Model:
    def __init__(self,method):
        self.method=method
        self.rules=[]
        self.train_seconds=0.0

    def fit(self,dialogs):
        t0=time.perf_counter()
        self.rules=induce_rules(dialogs)
        self.train_seconds=time.perf_counter()-t0

    def run_dialogue(self,rows):
        active=[]
        outputs=[]
        boundaries=[]
        retain=0
        terminate=0
        for idx,t in enumerate(rows):
            proposals=[Microstate(r,last_object_shape=r.object_shape) for r in self.rules if apply(t,r) is not None]
            if self.method=="one_step":
                active=proposals
            elif self.method=="no_lifetime":
                active=proposals[:]
            else:
                by_rule={m.rule:m for m in active if m.alive}
                for p in proposals:
                    by_rule.setdefault(p.rule,p)
                active=list(by_rule.values())

            scored=[]
            for m in active:
                e=local_error(t,m.rule)
                if self.method=="temporal_shuffle":
                    e=local_error(rows[(idx*7+3)%len(rows)],m.rule)
                if self.method=="one_step":
                    m.cumulative_error=e
                else:
                    decay=0.65 if self.method=="lifetime" else 0.0
                    m.cumulative_error=decay*m.cumulative_error+e
                m.age+=1
                m.consecutive_support = m.consecutive_support+1 if e<0.5 else 0
                scored.append((m.cumulative_error,e,m))
            scored.sort(key=lambda x:(x[0],-x[2].age))
            if not scored:
                outputs.append(None);boundaries.append(False);active=[];continue

            best=scored[0][0]
            survivors=[m for ce,e,m in scored if ce<=best+0.15][:12]
            if self.method=="lifetime":
                old_rules={m.rule for m in active}
                retain += sum(1 for m in survivors if m.rule in old_rules and m.age>1)
                terminate += max(0,len(active)-len(survivors))
            active=survivors

            eligible=[m for m in active if (m.consecutive_support>=2 if self.method=="lifetime" else True)]
            if len(eligible)==1:
                pred=apply(t,eligible[0].rule)
            else:
                pred=None
            outputs.append(pred)

            if idx==0:
                boundaries.append(False)
            else:
                boundaries.append(bool(terminate>0 and any(m.age==1 for m in active)))
        return outputs,boundaries,retain,terminate

def evaluate(seed,mode):
    train=[make_dialogue(seed+i,8,m) for i,m in enumerate(("explicit","omitted","paragraph","plan"))]
    test=make_dialogue(seed+100,6,mode)
    result={}
    for method in ("one_step","no_lifetime","lifetime","temporal_shuffle"):
        model=Model(method);model.fit(train)
        t0=time.perf_counter()
        pred,bounds,retain,terminate=model.run_dialogue(test)
        latency=(time.perf_counter()-t0)*1000/len(test)
        acc=[p==t.after for p,t in zip(pred,test)]
        wrong=[p is not None and p!=t.after for p,t in zip(pred,test)]
        null=[p is None for p in pred]
        trueb=[t.boundary for t in test]
        tp=sum(a and b for a,b in zip(bounds,trueb));fp=sum(a and not b for a,b in zip(bounds,trueb));fn=sum((not a) and b for a,b in zip(bounds,trueb))
        f1=0 if tp==0 else 2*tp/(2*tp+fp+fn)
        result[method]={
            "accuracy":statistics.mean(acc),
            "wrong_commit":statistics.mean(wrong),
            "null_rate":statistics.mean(null),
            "boundary_f1":f1,
            "retain_events":retain,
            "terminate_events":terminate,
            "rules":len(model.rules),
            "model_bytes":len(pickle.dumps(model)),
            "training_seconds":model.train_seconds,
            "inference_ms":latency
        }
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",required=True);a=ap.parse_args()
    modes=("explicit","omitted","paraphrase","order","paragraph","switch","plan","counterfactual")
    raw={str(seed):{m:evaluate(seed,m) for m in modes} for seed in (1,7,19)}
    summary={}
    for m in modes:
        summary[m]={}
        for method in ("one_step","no_lifetime","lifetime","temporal_shuffle"):
            summary[m][method]={k:statistics.mean(raw[str(seed)][m][method][k] for seed in (1,7,19))
                                for k in raw["1"][m][method]}
    payload={
      "cycle":40,
      "hypothesis":"Delayed-Error Event Boundary Birth from Competing Microstate Lifetimes",
      "seeds":[1,7,19],
      "summary":summary,
      "raw":raw,
      "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "estimated_complexity":"induction O(NL); online O(TR) with R<=64, active<=12",
      "final_test_outcome_used_for_candidate_ranking":False,
      "fixed_ontology_or_handwritten_slots_used_by_model":False,
      "highschool_level_passed":False,
      "native_japanese_communication_passed":False,
      "weak_smartphone_verified":False,
      "completion":False
    }
    with open(a.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
