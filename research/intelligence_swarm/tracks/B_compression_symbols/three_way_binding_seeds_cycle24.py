"""Cycle 024: three-way derivation intersections before MDL compression."""
from collections import Counter
import json, random, pickle, resource, statistics, time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末","大型端末":"大きい端末","試料甲":"サンプル甲","試料乙":"サンプル乙"}
VALUES=["棚A","棚B","棚C","棚D","待機","処理中","完了","保留"]

def substrings(text, limit=10):
    return {text[i:j] for i in range(len(text)) for j in range(i+1,min(len(text),i+limit)+1)}

def build(seed,n,mode):
    rng=random.Random(seed); rows=[]
    for _ in range(n):
        obj=rng.choice(OBJECTS); surface=ALIASES[obj] if mode=="rename" else obj
        old,new=rng.sample(VALUES,2)
        before=f"{surface}の現在値は{old}です。補助記録は維持します。"
        command=(f"{new}へ変更してください、対象は{surface}です。" if mode=="order"
                 else f"対象{surface}を次から{new}扱いにします。" if mode=="lexeme"
                 else f"それを{new}へ変更してください。" if mode=="omitted"
                 else f"{surface}の値を{new}へ変更してください。")
        if mode=="nested": command=f"依頼内容は「{command}」です。"
        after=f"{surface}の現在値は{new}です。補助記録は維持します。"
        future=f"次の観測でも{surface}は{new}で、補助記録は維持されます。"
        rows.append((before,command,after,future))
    return rows

class Learner:
    def __init__(self, mdl=False):
        self.mdl=mdl; self.objects=[]; self.values=[]; self.programs=[]
    def fit(self, rows):
        oc,vc=Counter(),Counter()
        for before,command,after,future in rows:
            c=substrings(command); b=substrings(before); a=substrings(after); f=substrings(future)
            for x in c & b & a & f:
                if 2<=len(x)<=10: oc[x]+=1
            for x in c & a & f:
                if 1<=len(x)<=8: vc[x]+=1
        self.objects=[x for x,n in oc.most_common(32) if n>=2]
        self.values=[x for x,n in vc.most_common(32) if n>=2]
        self.programs=[(o,v) for o in self.objects for v in self.values][:64]
    def infer(self,row):
        before,command,after,future=row
        os=[x for x in self.objects if x in command and x in before]
        vs=[x for x in self.values if x in command and x in future]
        pair=bool(os and vs)
        if self.mdl:
            library=sum(8*(len(o)+len(v)+4) for o,v in self.programs)
            literal=max(1,len(self.programs))*64
            pair=pair and library<literal
        return bool(os),bool(vs),pair

def main():
    modes=["seen","order","lexeme","rename","nested","omitted"]; raw={}
    start=time.perf_counter()
    for seed in (1,7,19):
        train=build(seed,288,"seen"); raw[str(seed)]={}
        for name,mdl in (("intersection",False),("mdl",True)):
            model=Learner(mdl); model.fit(train); raw[str(seed)][name]={}
            for mode in modes:
                vals=[model.infer(x) for x in build(seed+999,48,mode)]
                raw[str(seed)][name][mode]={
                    "object_recall":statistics.mean(v[0] for v in vals),
                    "value_recall":statistics.mean(v[1] for v in vals),
                    "pair_recall":statistics.mean(v[2] for v in vals)}
            raw[str(seed)][name]["model_bytes"]=len(pickle.dumps(model))
            raw[str(seed)][name]["object_seeds"]=len(model.objects)
            raw[str(seed)][name]["value_seeds"]=len(model.values)
            raw[str(seed)][name]["programs"]=len(model.programs)
    payload={"cycle":24,"raw":raw,"seconds":time.perf_counter()-start,
             "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             "highschool_level_passed":False,"completion":False}
    with open("results_cycle_024.json","w",encoding="utf-8") as f:
        json.dump(payload,f,ensure_ascii=False,indent=2)

if __name__=="__main__":
    main()
