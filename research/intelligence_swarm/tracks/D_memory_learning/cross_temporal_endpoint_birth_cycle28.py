from __future__ import annotations
import argparse, json, pickle, random, resource, statistics, time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末","大型端末":"大きい端末","試料甲":"サンプル甲","試料乙":"サンプル乙"}
VALUES=["棚A","棚B","棚C","棚D","待機","処理中","完了","保留","担当一","担当二"]

def make(seed,n,mode):
    rng=random.Random(seed); rows=[]; focus=""
    for i in range(n):
        obj=rng.choice(OBJECTS); surface=ALIASES[obj] if mode=="rename" else obj
        old,new=rng.sample(VALUES,2)
        before=f"{surface}の現在値は{old}です。補助記録は維持します。"
        command=f"{surface}の値を{new}へ変更してください。"
        if mode=="held": command=f"対象{surface}は次から{new}扱いにします。"
        if mode=="omitted": command=f"それを{new}へ変更してください。"
        if mode=="paragraph": command="別件の説明です。前の案は保留です。\n"+command+"\n補助記録は維持してください。"
        if mode=="alternate": before=f"{surface}：値={old}／補助=維持。"
        after=f"{surface}：値={new}／補助=維持。" if mode=="alternate" else f"{surface}の現在値は{new}です。補助記録は維持します。"
        future=f"次の観測でも{surface}の値は{new}で、補助記録は維持されます。"
        query=f"{surface}の現在値は何ですか？"
        rows.append({"before":before,"command":command,"after":after,"future":future,"query":query,"answer":new,"session":i//6,"focus":focus})
        focus=surface
    return rows

def spans(text,max_len=8):
    for i in range(len(text)):
        for j in range(i+1,min(len(text),i+max_len)+1):
            value=text[i:j]
            if not any(c.isspace() for c in value): yield i,j,value

def mask(text,i,j): return text[:i]+"□"+text[j:]
def overlap(a,b):
    sa,sb=set(a),set(b)
    return len(sa&sb)/(len(sa|sb) or 1)

class EndpointModel:
    def __init__(self,mode):
        self.mode=mode; self.endpoints=[]; self.slow=[]; self.training_seconds=0.0
    def fit(self,rows):
        started=time.perf_counter(); records={}
        for row in rows:
            for i,j,span in spans(row["after"]):
                query_harm=int(span in row["command"] and (span in row["query"] or span in row["after"]))
                state_harm=int(span in row["command"] and span in row["after"] and span not in row["before"])
                future_harm=int(span in row["future"] and span in row["after"])
                preserve=int("補助記録" in mask(row["after"],i,j) or "補助" in mask(row["after"],i,j))
                signature=(query_harm,state_harm,future_harm,preserve)
                if sum(signature[:3])<2: continue
                rec=records.setdefault((span,signature),{"support":0,"sessions":set(),"contexts":[]})
                rec["support"]+=1; rec["sessions"].add(row["session"])
                rec["contexts"].append((row["query"][:10],row["after"][max(0,i-6):i],row["after"][j:j+6]))
        endpoints=[]
        for (span,signature),rec in records.items():
            endpoints.append({"span":span,"signature":signature,"support":rec["support"],"sessions":len(rec["sessions"]),"contexts":rec["contexts"][:8]})
        endpoints.sort(key=lambda e:(sum(e["signature"][:3]),e["sessions"],e["support"],len(e["span"])),reverse=True)
        self.endpoints=endpoints[:64]
        if self.mode=="slow":
            self.slow=[e for e in self.endpoints if e["sessions"]>=2 and e["support"]>=3 and sum(e["signature"][:3])==3]
        self.training_seconds=time.perf_counter()-started
    def read(self,row):
        pool=self.slow if self.mode=="slow" else self.endpoints
        candidates=[]
        for endpoint in pool:
            span=endpoint["span"]
            if span not in row["after"]: continue
            score=endpoint["support"]*0.05+sum(endpoint["signature"][:3])
            if self.mode in ("necessity","slow"):
                score+=max((overlap(row["query"],q)+overlap(row["after"],left+span+right) for q,left,right in endpoint["contexts"]),default=0.0)
            candidates.append((score,span))
        if not candidates: return None
        candidates.sort(reverse=True)
        if len(candidates)>1 and candidates[0][0]-candidates[1][0]<0.05: return None
        return candidates[0][1]

def evaluate(seed,n,mode):
    train=[]
    for index,train_mode in enumerate(("seen","held","rename","alternate")):
        train+=make(seed+31*index,n//4,train_mode)
    test=make(seed+999,max(24,n//4),mode); result={}
    for method in ("support","necessity","slow"):
        model=EndpointModel(method); model.fit(train); started=time.perf_counter(); correct=wrong=null=0
        for row in test:
            answer=model.read(row); correct+=answer==row["answer"]; wrong+=answer is not None and answer!=row["answer"]; null+=answer is None
        result[method]={"read_accuracy":correct/len(test),"wrong_read":wrong/len(test),"null_rate":null/len(test),"endpoints":len(model.endpoints),"slow_endpoints":len(model.slow),"model_bytes":len(pickle.dumps(model)),"training_seconds":model.training_seconds,"inference_ms":(time.perf_counter()-started)*1000/len(test)}
    return result

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--output",default="results_cycle_028.json"); args=parser.parse_args()
    modes=("seen","held","rename","alternate","omitted","paragraph"); raw={}
    for n in (24,48,96): raw[str(n)]=[{mode:evaluate(seed,n,mode) for mode in modes} for seed in (1,7,19)]
    summary={}
    for n,runs in raw.items():
        summary[n]={}
        for mode in modes:
            summary[n][mode]={}
            for method in ("support","necessity","slow"):
                summary[n][mode][method]={key:statistics.mean(run[mode][method][key] for run in runs) for key in runs[0][mode][method]}
    payload={"cycle":28,"hypothesis":"Endpoint Birth by Cross-Temporal Predictive Necessity before Coalition Credit","seeds":[1,7,19],"sizes":[24,48,96],"raw":raw,"summary":summary,"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"estimated_complexity":"raw span O(NL^2), multi-channel necessity O(E), read O(BL), B<=64","fixed_value_inventory_used_by_learner":False,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(args.output,"w",encoding="utf-8") as handle: json.dump(payload,handle,ensure_ascii=False,indent=2)
if __name__=="__main__": main()
