"""系列A Cycle 029: intervention-coupled temporal response kernels.

前turn commitmentへの局所mask介入が、現在turn before/command のどの位置の
prediction errorを変えるかをkernel化する。文字列一致やembedding cosineではなく、
位置bucket別のNLL差と符号patternだけでrouteを形成する。
"""
from __future__ import annotations
from collections import Counter, defaultdict
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末",
         "大型端末":"大きい端末","北側の鍵":"北のキー","南側の鍵":"南のキー",
         "試料甲":"サンプル甲","試料乙":"サンプル乙"}
VALUES=["棚A","棚B","棚C","棚D","待機","処理中","完了","保留","担当一","担当二","担当三","担当四"]
FILL=["なお補助記録は維持します。","別件の説明は変更しません。","前段の注意事項はそのままです。"]

def make_dialog(seed,n,mode):
    rng=random.Random(seed); rows=[]; focus=None; world={}
    for turn in range(n):
        continuation = mode in ("omitted","switchmix") and turn>0 and (mode=="omitted" or turn%2==1)
        obj=focus if continuation else rng.choice(OBJECTS)
        surf=ALIASES[obj] if mode=="rename" else obj
        old=world.get(obj,rng.choice(VALUES))
        new=rng.choice([v for v in VALUES if v!=old])
        before=f"{surf}の現在値は{old}です。{rng.choice(FILL)}"
        if mode=="omitted" and turn>0:
            command=f"それを{new}へ変更してください。"
        elif mode=="switchmix" and turn>0 and turn%2==1:
            command=f"その対象を{new}へ変更してください。"
        elif mode=="nested":
            command=f"依頼内容は「{surf}の値を{new}へ変更してください。」です。"
        elif mode=="paragraph":
            command=f"{rng.choice(FILL)}\n{surf}の値を{new}へ変更してください。\n{rng.choice(FILL)}"
        elif mode=="plan":
            alt=rng.choice([v for v in VALUES if v not in (old,new)])
            command=f"{surf}を{alt}にする案は撤回し、最終的には{new}へ変更してください。"
        else:
            command=f"{surf}の値を{new}へ変更してください。"
        after=f"{surf}の現在値は{new}です。{rng.choice(FILL)}"
        future=f"次の観測でも{surf}は{new}のままです。"
        rows.append({"before":before,"command":command,"after":after,"future":future,
                     "obj":surf,"canonical":obj,"value":new})
        world[obj]=new; focus=obj
    return rows

def spans(text,lo=2,hi=10):
    out=[]
    for i in range(len(text)):
        for j in range(i+lo,min(len(text),i+hi)+1):
            s=text[i:j]
            if not any(c in s for c in "。、\n"):
                out.append((i,j,s))
    return out

def shape(s):
    return "".join("A" if c.isascii() and c.isalnum() else
                   "J" if c not in "。、：／=\n 「」" else c for c in s)

class CharPredictor:
    def __init__(self,order=3):
        self.order=order; self.counts=defaultdict(Counter); self.vocab=set()
    def fit_pairs(self,pairs):
        for context,target in pairs:
            stream=context+"↦"+target
            self.vocab.update(stream)
            for i,ch in enumerate(stream):
                ctx=stream[max(0,i-self.order):i]
                self.counts[ctx][ch]+=1
    def losses(self,context,target):
        stream=context+"↦"+target; out=[]; V=max(8,len(self.vocab))
        for i,ch in enumerate(stream):
            if i < len(context)+1: continue
            ctx=stream[max(0,i-self.order):i]
            c=self.counts.get(ctx,Counter()); total=sum(c.values())
            p=(c.get(ch,0)+0.2)/(total+0.2*V)
            out.append(-math.log(p))
        return out

def bucketize(losses,bins=8):
    if not losses:return (0,)*bins
    vals=[]
    for b in range(bins):
        lo=int(b*len(losses)/bins); hi=max(lo+1,int((b+1)*len(losses)/bins))
        vals.append(sum(losses[lo:hi])/max(1,hi-lo))
    return vals

def delta_kernel(base,pert):
    d=[p-b for b,p in zip(base,pert)]
    scale=max(1e-9,sum(abs(x) for x in d))
    q=[]
    for x in d:
        z=x/scale
        q.append(2 if z>.12 else 1 if z>.02 else -2 if z<-.12 else -1 if z<-.02 else 0)
    return tuple(q)

class Model:
    def __init__(self,method):
        self.method=method
        self.transition=CharPredictor(3)
        self.local=CharPredictor(2)
        self.route_protos=[]
    def fit(self,dialogs):
        tp=[]; lp=[]
        for rows in dialogs:
            for prev,cur in zip(rows[:-1],rows[1:]):
                tp.append((prev["after"]+"|"+prev["future"],cur["before"]+"|"+cur["command"]))
                lp.append((cur["before"],cur["command"]))
        self.transition.fit_pairs(tp); self.local.fit_pairs(lp)

        buckets=defaultdict(lambda:[0,0])
        for rows in dialogs:
            for prev,cur in zip(rows[:-1],rows[1:]):
                pk=self.commitment_kernels(prev,cur)
                rk=self.residual_kernels(cur)
                for ck in pk:
                    for rr in rk:
                        key=(ck,rr)
                        common={s for _,_,s in spans(cur["before"]) if s in cur["command"]}
                        omitted_signal=len(common)==0
                        if omitted_signal: buckets[key][1]+=1
                        else: buckets[key][0]+=1
        self.route_protos=[(k,pos,neg) for k,(neg,pos) in buckets.items()
                           if pos>=2 and pos>=2*max(1,neg)][:64]

    def commitment_kernels(self,prev,cur):
        ctx=prev["after"]+"|"+prev["future"]; target=cur["before"]+"|"+cur["command"]
        base=bucketize(self.transition.losses(ctx,target))
        candidates=sorted(spans(ctx,2,10),key=lambda x:-len(x[2]))[:12]
        out=[]
        for i,j,s in candidates:
            masked=ctx[:i]+("□"*(j-i))+ctx[j:]
            pert=bucketize(self.transition.losses(masked,target))
            k=delta_kernel(base,pert)
            if any(k): out.append((shape(s),k))
        return out[:8]

    def residual_kernels(self,cur):
        context=cur["before"]; target=cur["command"]
        base=bucketize(self.local.losses(context,target))
        candidates=sorted(spans(context,2,10),key=lambda x:-len(x[2]))[:12]
        out=[]
        for i,j,s in candidates:
            masked=context[:i]+("□"*(j-i))+context[j:]
            pert=bucketize(self.local.losses(masked,target))
            k=delta_kernel(base,pert)
            if any(k): out.append((shape(s),k))
        return out[:8]

    def route(self,prev,cur):
        if self.method=="none": return False,0.0
        if self.method=="unconditional": return True,1.0
        pk=self.commitment_kernels(prev,cur); rk=self.residual_kernels(cur)
        score=0
        proto={k:p-n for k,p,n in self.route_protos}
        for a in pk:
            for b in rk:
                score=max(score,proto.get((a,b),0))
        return score>0,float(score)

    def infer(self,prev,cur):
        current=spans(cur["before"]+" "+cur["command"])
        objects=[s for _,_,s in current if s in cur["before"] and s in cur["command"]]
        values=[s for _,_,s in current if s in cur["command"] and s not in cur["before"]]
        carry,credit=self.route(prev,cur)
        if carry:
            objects += [s for _,_,s in spans(prev["after"]+" "+prev["future"])]
        object_recall=cur["obj"] in objects
        value_recall=cur["value"] in values
        pair_recall=object_recall and value_recall
        chosen_o=max(set(objects),key=len,default="")
        chosen_v=max(set(values),key=len,default="")
        return {"object_recall":object_recall,"value_recall":value_recall,
                "pair_recall":pair_recall,
                "accuracy":chosen_o==cur["obj"] and chosen_v==cur["value"],
                "carry":carry,"credit":credit,
                "wrong_carry":carry and cur["canonical"]!=prev["canonical"],
                "continuation_hit":carry and cur["canonical"]==prev["canonical"],
                "active_pairs":min(128,len(set(objects))*max(1,len(set(values))))}

def evaluate(seed,mode):
    train=[make_dialog(seed+i,48,m) for i,m in enumerate(("seen","rename","switchmix","paragraph"))]
    test=make_dialog(seed+999,24,mode); out={}
    for method in ("none","unconditional","kernel"):
        m=Model(method)
        t=time.perf_counter(); m.fit(train); train_s=time.perf_counter()-t
        t=time.perf_counter()
        vals=[m.infer(a,b) for a,b in zip(test[:-1],test[1:])]
        infer_ms=(time.perf_counter()-t)*1000/len(vals)
        out[method]={k:statistics.mean(float(v[k]) for v in vals) for k in vals[0]}
        out[method].update({"route_prototypes":len(m.route_protos),
                            "model_bytes":len(pickle.dumps(m)),
                            "training_seconds":train_s,"inference_ms":infer_ms})
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="MEASUREMENTS_CYCLE_029.json")
    args=ap.parse_args()
    modes=("seen","rename","nested","omitted","switchmix","paragraph","plan")
    raw={str(seed):{mode:evaluate(seed,mode) for mode in modes} for seed in (1,7,19)}
    summary={}
    for mode in modes:
        summary[mode]={}
        for method in ("none","unconditional","kernel"):
            summary[mode][method]={k:statistics.mean(raw[str(seed)][mode][method][k] for seed in (1,7,19))
                                   for k in raw["1"][mode][method]}
    payload={"cycle":29,
      "hypothesis":"Intervention-Coupled Route Identity from Shared Temporal Response Kernels",
      "seeds":[1,7,19],"summary":summary,"raw":raw,
      "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "estimated_complexity":"predictor fit O(NL), intervention kernels O(KL), route lookup O(KcKr), candidate spans O(L^2)",
      "hidden_labels_used_by_route_training":False,
      "current_turn_after_future_used_for_route_selection":False,
      "direct_lexical_overlap_or_embedding_used_in_route_score":False,
      "highschool_level_passed":False,"native_japanese_communication_passed":False,
      "weak_smartphone_verified":False,"completion":False}
    with open(args.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)

if __name__=="__main__":main()
