"""Track C Cycle 008: latent effect-factor discovery from multi-operation signatures.

The learner sees only raw Japanese context strings plus before/command/after
observations for several operations. It is not given context labels, factor
names, a fixed number of factors, entity/value lists, morphology, RAG, or an
external model.

This is a controlled falsification probe. The experiment generator has a finite
world, but the learner does not receive its ontology.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import argparse, json, math, pickle, random, resource, statistics, time

OPS = [
    ("運ぶ", "保管場所", ["棚A","棚B","棚C"]),
    ("渡す", "担当者", ["担当甲","担当乙","担当丙"]),
    ("起動する", "状態", ["停止","稼働","待機"]),
]
ENTITIES = ["試料甲","試料乙","装置春","装置夏","部品空","部品海"]
CONTEXT_GROUPS = {
    "free": {"seen": ["周囲に妨げはありません。", "作業を進められる状況です。"], "held": ["実行を阻むものは見当たりません。", "予定どおり対応できます。"], "sig": (1,1,1)},
    "move_block": {"seen": ["通路が塞がれています。", "搬送経路を利用できません。"], "held": ["行き先までの道が閉ざされています。", "運搬用の経路が使えません。"], "sig": (0,1,1)},
    "handoff_block": {"seen": ["受取人が不在です。", "引き渡し相手と連絡が取れません。"], "held": ["受領する人が席を外しています。", "渡す相手が応答しません。"], "sig": (1,0,1)},
    "power_block": {"seen": ["電源供給がありません。", "安全装置が作動中です。"], "held": ["給電されていません。", "保護機構が解除されていません。"], "sig": (1,1,0)},
    "all_block": {"seen": ["全面停止の指示が出ています。", "すべての作業が禁止されています。"], "held": ["現在は一切の操作を行えません。", "全工程が凍結されています。"], "sig": (0,0,0)},
}
COMMANDS = {
    0: ["{e}を{v}へ運んでください。", "{v}へ{e}を移してください。"],
    1: ["{e}を{v}へ渡してください。", "{v}を担当するのは{e}です。"],
    2: ["{e}を{v}にしてください。", "{v}となるよう{e}を起動してください。"],
}
HELD_COMMANDS = {
    0: ["{e}の置き先を{v}へ変えて。"],
    1: ["{e}の受け持ちを{v}に交代して。"],
    2: ["{e}が{v}になるよう動作を切り替えて。"],
}
STATE_FORMS = ["{e}の{r}は{v}です。", "{r}について、{e}は{v}となっています。"]
ALT_STATE_FORMS = ["{e}：{r}＝{v}", "{e}では{v}が{r}として記録されています。"]

def grams(text: str) -> Counter[str]:
    s = "".join(text.split())
    return Counter(s[i:i+n] for n in (2,3,4) for i in range(max(0,len(s)-n+1)))

def cosine(a: Counter[str], b: Counter[str]) -> float:
    dot=sum(v*b.get(k,0) for k,v in a.items())
    na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return dot/(na*nb+1e-12)

def make_bundle(rng, group_name, context_form="seen", command_held=False, alt_state=False, plan_change=False, subject_omission=False):
    g=CONTEXT_GROUPS[group_name]
    context=rng.choice(g[context_form]); entity=rng.choice(ENTITIES); observations=[]
    for op_id,(verb,relation,values) in enumerate(OPS):
        old,new=rng.sample(values,2)
        forms = ALT_STATE_FORMS if alt_state else STATE_FORMS
        chosen_form = rng.choice(forms)
        before=chosen_form.format(e=entity,r=relation,v=old)
        cmd_form=rng.choice(HELD_COMMANDS[op_id] if command_held else COMMANDS[op_id])
        cmd=cmd_form.format(e=entity,v=new)
        if subject_omission: cmd=cmd.replace(entity,"それ")
        if plan_change:
            other=rng.choice([x for x in values if x != new])
            cmd=cmd + " ただし訂正し、" + cmd_form.format(e=entity,v=other); new=other
        succeeds=bool(g["sig"][op_id])
        after=chosen_form.format(e=entity,r=relation,v=new if succeeds else old)
        observations.append({"op_id_generator_only":op_id,"before":before,"command":cmd,"after":after,"changed":succeeds})
    return {"context":context,"signature":g["sig"],"observations":observations,"group":group_name}

@dataclass
class FactorNode:
    signature: tuple[int,...]
    residues: Counter[str]=field(default_factory=Counter)
    support:int=0
    contradictions:int=0

class SignatureFactorModel:
    def __init__(self, use_surface=True):
        self.nodes={}; self.use_surface=use_surface; self.bridge={}; self.command_views=defaultdict(Counter)
    def fit(self,bundles):
        for b in bundles:
            sig=tuple(int(o["before"] != o["after"]) for o in b["observations"])
            node=self.nodes.setdefault(sig,FactorNode(sig)); node.support += 1
            for gram,count in grams(b["context"]).items(): node.residues[gram]+=count
            for idx,o in enumerate(b["observations"]): self.command_views[idx].update(grams(o["command"]))
        return self
    def infer_signature(self, context):
        if context in self.bridge: return self.bridge[context],1.0
        if not self.use_surface or not self.nodes: return None,0.0
        q=grams(context); scored=[]
        for sig,node in self.nodes.items(): scored.append((cosine(q,node.residues),sig))
        scored.sort(reverse=True)
        if not scored or scored[0][0] < 0.12: return None, scored[0][0] if scored else 0.0
        margin=scored[0][0]-(scored[1][0] if len(scored)>1 else 0)
        if margin < 0.025: return None,margin
        return scored[0][1],margin
    def observe_effect(self, context, signature):
        previous=self.bridge.get(context)
        if previous is None: self.bridge[context]=tuple(signature); return "added"
        if previous != tuple(signature):
            del self.bridge[context]
            node=self.nodes.get(previous)
            if node: node.contradictions += 1
            return "revoked"
        return "confirmed"
    def predict(self,bundle):
        sig,margin=self.infer_signature(bundle["context"])
        if sig is None: return [None]*len(bundle["observations"]),margin
        return [bool(sig[i]) if i < len(sig) else None for i in range(len(bundle["observations"]))],margin

def eval_split(model,bundles,bridge=False,wrong_bridge=False):
    correct=total=abstain=0; margins=[]; actions=Counter(); start=time.perf_counter()
    for b in bundles:
        if bridge:
            sig=list(b["signature"])
            if wrong_bridge: sig=sig[1:]+sig[:1]
            actions[model.observe_effect(b["context"],sig)] += 1
        pred,margin=model.predict(b); margins.append(margin)
        for p,o in zip(pred,b["observations"]):
            total += 1
            if p is None: abstain += 1
            correct += int(p is not None and p == o["changed"])
    return {"accuracy":correct/total,"abstention":abstain/total,"mean_margin":statistics.mean(margins),"ms_per_bundle":(time.perf_counter()-start)*1000/max(1,len(bundles)),"bridge_actions":dict(actions)}

def evaluate(seed,train_size):
    rng=random.Random(seed); names=list(CONTEXT_GROUPS)
    train=[make_bundle(rng,rng.choice(names),"seen") for _ in range(train_size)]
    base=SignatureFactorModel(True).fit(train); no_surface=SignatureFactorModel(False).fit(train)
    def bundles(form="seen",**kw): return [make_bundle(rng,rng.choice(names),form,**kw) for _ in range(100)]
    splits={"seen":bundles("seen"),"held_context":bundles("held"),"held_command":bundles("seen",command_held=True),"held_both":bundles("held",command_held=True),"alt_state":bundles("seen",alt_state=True),"subject_omission":bundles("seen",subject_omission=True),"plan_change":bundles("seen",plan_change=True)}
    out={"surface":{},"signature_only":{}}
    for name,bs in splits.items():
        out["surface"][name]=eval_split(base,bs); out["signature_only"][name]=eval_split(no_surface,bs)
    held=splits["held_context"]; bridged=pickle.loads(pickle.dumps(base)); wrong=pickle.loads(pickle.dumps(base))
    out["one_shot_bridge"]=eval_split(bridged,held,bridge=True)
    out["wrong_bridge"]=eval_split(wrong,held,bridge=True,wrong_bridge=True)
    revoke=Counter()
    for b in held: revoke[wrong.observe_effect(b["context"],b["signature"])] += 1
    out["wrong_bridge_reversal"]=dict(revoke)
    out["model_bytes"]=len(pickle.dumps(base)); out["bridged_model_bytes"]=len(pickle.dumps(bridged)); out["factor_nodes"]=len(base.nodes); out["bridge_entries"]=len(bridged.bridge)
    return out

def summarize(raw):
    out={}
    for n,runs in raw.items():
        out[n]={}
        for method in ("surface","signature_only"):
            out[n][method]={}
            for split in runs[0][method]: out[n][method][split]={k:statistics.mean(r[method][split][k] for r in runs) for k in ("accuracy","abstention","mean_margin","ms_per_bundle")}
        for method in ("one_shot_bridge","wrong_bridge"): out[n][method]={k:statistics.mean(r[method][k] for r in runs) for k in ("accuracy","abstention","mean_margin","ms_per_bundle")}
        for k in ("model_bytes","bridged_model_bytes","factor_nodes","bridge_entries"): out[n][k]=statistics.mean(r[k] for r in runs)
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="results_cycle_008.json"); args=ap.parse_args()
    raw={str(n):[evaluate(seed,n) for seed in (1,7,19)] for n in (40,120,360)}
    payload={"hypothesis":"Latent Effect-Factor Discovery from Multi-Operation Intervention Signatures","seeds":[1,7,19],"train_sizes":[40,120,360],"raw":raw,"summary":summarize(raw),"estimated_complexity":"train O(N*O*G); infer O(C*G + O), discovered C<=5, O=3","peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"free_japanese_integrated_gate":0.0,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(args.output,"w",encoding="utf-8") as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload["summary"]["360"],ensure_ascii=False,indent=2))
if __name__=="__main__": main()
