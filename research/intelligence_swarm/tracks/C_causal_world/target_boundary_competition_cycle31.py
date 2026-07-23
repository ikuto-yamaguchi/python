from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse, json, pickle, random, resource, statistics, time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末","大型端末":"大きい端末",
         "北側の鍵":"北のキー","南側の鍵":"南のキー","試料甲":"サンプル甲","試料乙":"サンプル乙"}
FIELDS=["場所","状態","担当"]
VALUES={"場所":["棚A","棚B","棚C","棚D"],"状態":["待機","処理中","完了","保留"],"担当":["担当一","担当二","担当三","担当四"]}
STATE0="{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。"
STATE1="{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。"
CMDS={"場所":["{o}を{v}へ移してください。","{o}の保管先を{v}へ変更してください。"],
      "状態":["{o}を{v}にしてください。","{o}の進行状態を{v}へ切り替えてください。"],
      "担当":["{o}を{v}の担当にしてください。","{o}の受け持ちを{v}へ変更してください。"]}
HELD={"場所":["{v}へ移してください、対象は{o}です。"],"状態":["{v}扱いにしてください、対象は{o}です。"],
      "担当":["{v}へ引き継いでください、対象は{o}です。"]}
LEX={"場所":["対象{o}は次から{v}で保管。"],"状態":["対象{o}は以後{v}として運用。"],"担当":["対象{o}の受持を{v}へ。"]}
OMIT={"場所":["それを{v}へ移してください。"],"状態":["その対象を{v}にしてください。"],"担当":["担当は{v}へ変えてください。"]}
DIST=["別件は変更しません。","前段の説明を維持します。","補助記録には触れません。"]

@dataclass
class Ex:
    before:str; command:str; after:str; future:str
    obj:str; canonical:str; field:str; old:str; new:str; mode:str

@dataclass
class Mechanism:
    left_shape:str; right_shape:str; old_shape:str; new_shape:str
    cmd_left_shape:str; cmd_right_shape:str
    support:int=0; wrong:int=0; noexec:int=0

def state(o,d,alt=False):
    return (STATE1 if alt else STATE0).format(o=o,loc=d["場所"],status=d["状態"],owner=d["担当"])

def shape(s):
    return "".join("A" if c.isascii() and c.isalnum() else
                   "J" if c not in "。、／=：:\n 「」" else c for c in s)

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

def spans(text,lo=1,hi=10):
    return [(i,j,text[i:j]) for i in range(len(text)) for j in range(i+lo,min(len(text),i+hi)+1)
            if not any(c in text[i:j] for c in "。、\n「」")]

def build(seed,n,mode):
    rng=random.Random(seed); world={}; out=[]; focus=None
    for t in range(n):
        continuation=mode=="omitted" and t>0
        canon=focus if continuation else rng.choice(OBJECTS)
        surf=ALIASES[canon] if mode=="rename" else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS})
        fld=rng.choice(FIELDS); old=world[canon][fld]; new=rng.choice([v for v in VALUES[fld] if v!=old])
        alt=mode=="alternate"; before=state(surf,world[canon],alt)
        forms=HELD[fld] if mode=="order" else LEX[fld] if mode=="lexeme" else OMIT[fld] if mode=="omitted" else CMDS[fld]
        command=rng.choice(forms).format(o=surf,v=new)
        if mode=="nested": command=f'依頼内容は「{command}」です。'
        elif mode=="paragraph": command=" ".join(rng.choice(DIST) for _ in range(4))+"\n"+command
        elif mode=="plan":
            altv=rng.choice([v for v in VALUES[fld] if v not in (old,new)])
            command=f"{surf}を{altv}にする案は撤回します。最終的には{command}"
        elif mode=="counterfactual":
            command=f"もし変更しなければ{surf}は{old}のままです。実際には{command}"
        world[canon][fld]=new; after=state(surf,world[canon],alt)
        future=f"次の観測でも{surf}の更新結果は{new}で、補助記録は維持されます。"
        out.append(Ex(before,command,after,future,surf,canon,fld,old,new,mode)); focus=canon
    return out

def boundary_features(text,a,b):
    left=text[max(0,a-7):a]; right=text[b:b+7]
    return shape(left),shape(right),shape(text[a:b]),min(7,a//8),min(7,(len(text)-b)//8)

def replace(before,a,b,value):
    return before[:a]+value+before[b:]

def inverse(pred,a,b,old,value):
    return pred[:a]+old+pred[a+len(value):]

class Model:
    def __init__(self,method):
        self.method=method
        self.mechanisms=[]
        self.vote_credit=Counter()
        self.probe_audits=0; self.probe_discriminations=0
        self.train_seconds=0

    def fit(self,induction,probe,shuffle=False):
        t=time.perf_counter()
        counts=defaultdict(lambda:[0,0,0])
        for e in induction:
            l,r,old,new=diff(e.before,e.after)
            if not old or not new: continue
            p=e.command.find(new)
            if p<0: continue
            lf,rf,osh,_,_=boundary_features(e.before,l,len(e.before)-r if r else len(e.before))
            clf,crf,_,_,_=boundary_features(e.command,p,p+len(new))
            key=(lf,rf,osh,shape(new),clf,crf)
            counts[key][0]+=1
        self.mechanisms=[Mechanism(*k,support=v[0]) for k,v in sorted(counts.items(),key=lambda kv:kv[1][0],reverse=True)[:64]]

        outcomes=[e.after for e in probe]
        if shuffle and outcomes: outcomes=outcomes[1:]+outcomes[:1]
        for e,observed in zip(probe,outcomes):
            cands=self.generate(e)
            if len(cands)<2: continue
            bypred={c["pred"]:c for c in cands}
            items=list(bypred.values())
            for i,a in enumerate(items):
                for b in items[i+1:]:
                    if a["pred"]==b["pred"]: continue
                    self.probe_audits+=1
                    ca=int(a["pred"]==observed); cb=int(b["pred"]==observed)
                    if ca==cb: continue
                    self.probe_discriminations+=1
                    winner=a if ca else b; loser=b if ca else a
                    self.vote_credit[(winner["signature"],loser["signature"])]+=1
        self.train_seconds=time.perf_counter()-t

    def value_candidates(self,e):
        raw=[s for _,_,s in spans(e.command,1,10) if s not in e.before]
        maximal=[x for x in raw if not any(x in y and x!=y for y in raw)]
        return sorted(set(maximal+raw),key=lambda x:(-len(x),x))[:14]

    def boundary_candidates(self,e):
        out=[]
        for a in range(len(e.before)):
            for b in range(a+1,min(len(e.before),a+11)+1):
                seg=e.before[a:b]
                if any(c in seg for c in "。、\n"): continue
                lf,rf,osh,lb,rb=boundary_features(e.before,a,b)
                out.append((a,b,seg,lf,rf,osh,lb,rb))
        return out

    def generate(self,e):
        vals=self.value_candidates(e); bounds=self.boundary_candidates(e); out=[]
        for a,b,old,lf,rf,osh,lb,rb in bounds:
            for val in vals:
                vsh=shape(val)
                supporting=[]
                for mi,m in enumerate(self.mechanisms):
                    score=(lf==m.left_shape)+(rf==m.right_shape)+(osh==m.old_shape)+(vsh==m.new_shape)
                    if score>=2: supporting.append((mi,score))
                if len(supporting)<2: continue
                pred=replace(e.before,a,b,val)
                preserved=int(("補助" in e.before)==("補助" in pred))
                inv=int(inverse(pred,a,b,old,val)==e.before)
                cmd=int(val in e.command)
                base=sum(sc for _,sc in supporting)+2*preserved+2*inv+cmd
                signature=(osh,vsh,lb,rb,len(supporting))
                out.append({"pred":pred,"a":a,"b":b,"old":old,"val":val,"base":base,
                            "support":len(supporting),"signature":signature})
        best={}
        for c in out:
            k=(c["pred"],c["signature"])
            if k not in best or c["base"]>best[k]["base"]: best[k]=c
        return sorted(best.values(),key=lambda c:c["base"],reverse=True)[:96]

    def predict(self,e):
        cands=self.generate(e)
        if not cands:return None,0,"candidate_collapse"
        for c in cands:
            score=c["base"]
            if self.method in ("probe","fiber"):
                for other in cands:
                    score += 0.9*self.vote_credit.get((c["signature"],other["signature"]),0)
                    score -= 0.9*self.vote_credit.get((other["signature"],c["signature"]),0)
            if self.method=="fiber": score += 0.2*min(5,c["support"])
            c["score"]=score
        ranked=sorted(cands,key=lambda c:c["score"],reverse=True)
        if len(ranked)>1 and ranked[0]["score"]-ranked[1]["score"]<0.75:
            return None,len(ranked),"tie"
        return ranked[0],len(ranked),"commit"

def evaluate(model,test):
    t=time.perf_counter(); correct=wrong=null=pair=0;cands=[];reasons=Counter()
    for e in test:
        p,n,r=model.predict(e);cands.append(n);reasons[r]+=1
        if p is None:null+=1;continue
        if p["pred"]==e.after:correct+=1
        else:wrong+=1
        pair+=int(e.obj in e.command and p["val"]==e.new and e.before[p["a"]:p["b"]]==e.old)
    N=len(test)
    return {"accuracy":correct/N,"wrong_commit":wrong/N,"null_rate":null/N,
            "exact_target_value_recall":pair/N,"mean_candidates":statistics.mean(cands),
            "probe_audits":model.probe_audits,"probe_discriminations":model.probe_discriminations,
            "credits":len(model.vote_credit),"mechanisms":len(model.mechanisms),
            "model_bytes":len(pickle.dumps(model)),"training_seconds":model.train_seconds,
            "inference_ms":(time.perf_counter()-t)*1000/N,"reasons":dict(reasons)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="MEASUREMENTS_CYCLE_031.json");a=ap.parse_args()
    modes=["seen","order","lexeme","rename","alternate","nested","omitted","paragraph","plan","counterfactual"]
    raw={}
    for seed in (1,7,19):
        data=build(seed,288,"seen")
        induction,probe=data[:190],data[190:]
        models={}
        for method in ("surface","probe","fiber","shuffle"):
            m=Model("probe" if method=="shuffle" else method)
            m.fit(induction,probe,shuffle=(method=="shuffle"));models[method]=m
        run={}
        for mode in modes:
            test=build(seed+999,36,mode)
            run[mode]={k:evaluate(m,test) for k,m in models.items()}
        raw[str(seed)]=run
    summary={}
    for mode in modes:
        summary[mode]={}
        for method in ("surface","probe","fiber","shuffle"):
            keys=[k for k,v in raw["1"][mode][method].items() if isinstance(v,(int,float))]
            summary[mode][method]={k:statistics.mean(raw[str(seed)][mode][method][k] for seed in (1,7,19)) for k in keys}
    payload={"cycle":31,"hypothesis":"Target-Boundary Competition from Source-Mechanism Predictive Cuts",
      "seeds":[1,7,19],"raw":raw,"summary":summary,
      "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "estimated_complexity":"mechanism O(NL), boundary search O(L^2), mechanism voting O(BVPL), probe audit O(QH^2), inference O(BVPL)",
      "target_after_future_used_for_candidate_or_ranking":False,
      "probe_partition_independent":True,"fixed_ontology_or_handwritten_slots_used_by_model":False,
      "highschool_level_passed":False,"native_japanese_communication_passed":False,
      "weak_smartphone_verified":False,"completion":False}
    with open(a.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
