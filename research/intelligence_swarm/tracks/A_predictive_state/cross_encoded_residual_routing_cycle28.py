"""系列A Cycle 028: cross-encoded residual routing.

前turnのafter/futureから得るcommitment表現と、current before/commandから得る
residual表現を別hash・別random projectionで符号化する。route scoreには直接の
文字列overlapを使わない。current after/futureはroute選択へ使用しない。
"""
from __future__ import annotations
from collections import defaultdict
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末","大型端末":"大きい端末","北側の鍵":"北のキー","南側の鍵":"南のキー","試料甲":"サンプル甲","試料乙":"サンプル乙"}
VALUES=["棚A","棚B","棚C","棚D","待機","処理中","完了","保留","担当一","担当二","担当三","担当四"]
FILL=["なお補助記録は維持します。","別件の説明は変更しません。","前段の注意事項はそのままです。"]

def hashed_features(text,salt,bins=64):
    feats=[0.0]*bins
    text=''.join(text.split())
    for n in (2,3,4):
        for i in range(max(0,len(text)-n+1)):
            g=text[i:i+n]
            h=hash((salt,n,g))%bins
            feats[h]+=1 if (hash((g,salt,'sign'))&1)==0 else -1
    z=math.sqrt(sum(x*x for x in feats)) or 1
    return [x/z for x in feats]

def project(v,seed,out=16):
    y=[]
    for j in range(out):
        s=0.0
        for i,x in enumerate(v):
            h=hash((seed,j,i))%7
            s += x if h==0 else -x if h==1 else 0
        y.append(s)
    z=math.sqrt(sum(x*x for x in y)) or 1
    return [x/z for x in y]

def cosine(a,b):
    return sum(x*y for x,y in zip(a,b))/(math.sqrt(sum(x*x for x in a))*math.sqrt(sum(y*y for y in b))+1e-9)

def spans(text,lo=2,hi=10):
    out=[]
    for i in range(len(text)):
        for j in range(i+lo,min(len(text),i+hi)+1):
            s=text[i:j]
            if not any(c in s for c in "。、\n"):
                out.append(s)
    return out

def make_dialog(seed,n,mode):
    rng=random.Random(seed); rows=[]; focus=None; world={}
    for turn in range(n):
        if mode in ("omitted","switchmix") and turn>0 and (mode=="omitted" or turn%2==1):
            obj=focus
        else:
            obj=rng.choice(OBJECTS)
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
            command=f"{surf}を{alt}にする案でしたが、最終的には{new}へ変更してください。"
        else:
            command=f"{surf}の値を{new}へ変更してください。"
        after=f"{surf}の現在値は{new}です。{rng.choice(FILL)}"
        future=f"次の観測でも{surf}は{new}のままです。"
        rows.append({"before":before,"command":command,"after":after,"future":future,
                     "obj":surf,"canonical":obj,"value":new})
        world[obj]=new; focus=obj
    return rows

class Model:
    def __init__(self,method,seed):
        self.method=method; self.seed=seed; self.route_protos=[]
    def commit_enc(self,after,future):
        return project(hashed_features(after+"|"+future,("commit",self.seed)),self.seed+101)
    def residual_enc(self,before,command):
        a=project(hashed_features(before,("resA",self.seed)),self.seed+211)
        b=project(hashed_features(command,("resB",self.seed)),self.seed+307)
        d=[abs(x-y) for x,y in zip(a,b)]
        z=math.sqrt(sum(x*x for x in d)) or 1
        return [x/z for x in d]
    def fit(self,dialogs):
        buckets={}
        for rows in dialogs:
            for prev,cur in zip(rows[:-1],rows[1:]):
                ce=self.commit_enc(prev["after"],prev["future"])
                re=self.residual_enc(cur["before"],cur["command"])
                k=(round(cosine(ce,re),1),tuple(int(x>0) for x in ce[:6]),tuple(int(x>0) for x in re[:6]))
                neg,pos=buckets.get(k,(0,0))
                if cur["canonical"]==prev["canonical"]: pos+=1
                else: neg+=1
                buckets[k]=(neg,pos)
        self.route_protos=[(k,pos,neg) for k,(neg,pos) in buckets.items() if pos>=2 and pos>neg][:64]
    def route(self,prev,cur):
        if self.method=="none": return False,0.0
        if self.method=="unconditional": return True,1.0
        ce=self.commit_enc(prev["after"],prev["future"])
        re=self.residual_enc(cur["before"],cur["command"])
        k=(round(cosine(ce,re),1),tuple(int(x>0) for x in ce[:6]),tuple(int(x>0) for x in re[:6]))
        score=max([p-n for kk,p,n in self.route_protos if kk==k] or [0])
        return score>0,float(score)
    def infer(self,prev,cur):
        current=set(spans(cur["before"]+" "+cur["command"]))
        objects=[s for s in current if s in cur["before"] and s in cur["command"]]
        values=[s for s in current if s in cur["command"] and s not in cur["before"]]
        carry,credit=self.route(prev,cur)
        if carry:
            objects += spans(prev["after"]+" "+prev["future"])
        object_recall=cur["obj"] in objects
        value_recall=cur["value"] in values
        pair_recall=object_recall and value_recall
        chosen_o=max(objects,key=len,default="")
        chosen_v=max(values,key=len,default="")
        return {"object_recall":object_recall,"value_recall":value_recall,
                "pair_recall":pair_recall,"accuracy":chosen_o==cur["obj"] and chosen_v==cur["value"],
                "carry":carry,"credit":credit,
                "wrong_carry":carry and cur["canonical"]!=prev["canonical"],
                "continuation_hit":carry and cur["canonical"]==prev["canonical"],
                "active_pairs":min(64,len(set(objects))*max(1,len(set(values))))}

def evaluate(seed,mode):
    train=[make_dialog(seed+i,48,m) for i,m in enumerate(("seen","rename","switchmix","paragraph"))]
    test=make_dialog(seed+999,24,mode); out={}
    for method in ("none","unconditional","cross_encoded"):
        model=Model(method,seed)
        t=time.perf_counter(); model.fit(train); train_s=time.perf_counter()-t
        t=time.perf_counter()
        vals=[model.infer(a,b) for a,b in zip(test[:-1],test[1:])]
        infer_ms=(time.perf_counter()-t)*1000/len(vals)
        out[method]={k:statistics.mean(float(v[k]) for v in vals) for k in vals[0]}
        out[method].update({"route_prototypes":len(model.route_protos),
                            "model_bytes":len(pickle.dumps(model)),
                            "training_seconds":train_s,"inference_ms":infer_ms})
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="results_cycle_028.json")
    args=ap.parse_args()
    modes=("seen","rename","nested","omitted","switchmix","paragraph","plan")
    raw={str(seed):{m:evaluate(seed,m) for m in modes} for seed in (1,7,19)}
    summary={}
    for mode in modes:
        summary[mode]={}
        for method in ("none","unconditional","cross_encoded"):
            summary[mode][method]={k:statistics.mean(raw[str(seed)][mode][method][k] for seed in (1,7,19))
                                   for k in raw["1"][mode][method]}
    payload={"cycle":28,
             "hypothesis":"Cross-Encoded Residual Routing by Predictive Information Exclusion",
             "seeds":[1,7,19],"summary":summary,"raw":raw,
             "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             "estimated_complexity":"encoding O(L), sparse projection O(BD), routing O(R), candidate spans O(L^2), pairing O(KoKv)",
             "hidden_labels_used_by_learner":False,
             "current_turn_after_future_used_for_route_selection":False,
             "direct_lexical_overlap_used_in_route_score":False,
             "highschool_level_passed":False,
             "native_japanese_communication_passed":False,
             "weak_smartphone_verified":False,"completion":False}
    with open(args.output,"w",encoding="utf-8") as f:
        json.dump(payload,f,ensure_ascii=False,indent=2)

if __name__=="__main__":
    main()
