from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
import argparse, json, pickle, random, resource, statistics, time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末"]
VALUES=["棚A","棚B","待機","完了"]
FILL=["補助記録は維持します。","別件は変えません。"]

@dataclass
class Turn:
    before:str; command:str; after:str; future:str
    obj:str; old:str; new:str; kind:str; episode:int

@dataclass(frozen=True)
class Rule:
    left:str; right:str; old_shape:str
    cmd_left:str; cmd_right:str; obj_shape:str

def shape(s:str)->str:
    return ''.join('J' if c not in '。、\n「」 ' else c for c in s)

def diff(a:str,b:str):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

def make_dialog(seed:int, episodes:int, mode:str):
    rng=random.Random(seed); rows=[]
    for ep in range(episodes):
        obj,other=rng.sample(OBJECTS,2)
        old,new,other_v=rng.sample(VALUES,3)
        before=f"{obj}の現在値は{old}です。{other}の現在値は{other_v}です。{rng.choice(FILL)}"
        if mode=="paraphrase": cmd=f"対象{obj}は次から{new}扱いにします。"
        elif mode=="order": cmd=f"{new}へ変更してください、対象は{obj}です。"
        elif mode=="paragraph": cmd=f"{rng.choice(FILL)}\n{obj}を{new}へ変更してください。"
        else: cmd=f"{obj}を{new}へ変更してください。"
        after=before.replace(f"{obj}の現在値は{old}",f"{obj}の現在値は{new}",1)
        future=f"次の観測でも{obj}は{new}で、{other}は{other_v}です。"
        rows.append(Turn(before,cmd,after,future,obj,old,new,"explicit",ep))

        new2=rng.choice([v for v in VALUES if v!=new and v!=other_v])
        cmd2=f"それを{new2}へ変更してください。"
        after2=after.replace(f"{obj}の現在値は{new}",f"{obj}の現在値は{new2}",1)
        future2=f"次の観測でも{obj}は{new2}で、{other}は{other_v}です。"
        rows.append(Turn(after,cmd2,after2,future2,obj,new,new2,"omitted",ep))

        switch_v=rng.choice([v for v in VALUES if v!=other_v and v!=new2])
        if mode=="plan":
            abandoned=rng.choice([v for v in VALUES if v not in (other_v,switch_v)])
            cmd3=f"{other}を{abandoned}にする案は撤回し、最終的に{switch_v}へ変更してください。"
        elif mode=="counterfactual":
            cmd3=f"変更しなければ{other}は{other_v}のままです。実際には{other}を{switch_v}へ変更してください。"
        else: cmd3=f"{other}を{switch_v}へ変更してください。"
        after3=after2.replace(f"{other}の現在値は{other_v}",f"{other}の現在値は{switch_v}",1)
        future3=f"次の観測でも{other}は{switch_v}で、{obj}は{new2}です。"
        rows.append(Turn(after2,cmd3,after3,future3,other,other_v,switch_v,"switch",ep))
    return rows

def spans(text,maxw=10):
    for i in range(len(text)):
        for j in range(i+1,min(len(text),i+maxw)+1):
            x=text[i:j]
            if not any(c in x for c in '。、\n「」'): yield i,j,x

def induce_rule(t:Turn):
    l,r,old,new=diff(t.before,t.after)
    if not old or not new: return None
    p=t.command.find(new)
    if p<0: return None
    oc=[x for _,_,x in spans(t.command,8) if x in t.before and len(x)>=2]
    obj=max(oc,key=len) if oc else ""
    return Rule(t.before[max(0,l-6):l],t.before[len(t.before)-r:len(t.before)-r+6] if r else "",shape(old),t.command[max(0,p-6):p],t.command[p+len(new):p+len(new)+6],shape(obj))

def value_candidates(t:Turn):
    c=sorted(set(x for _,_,x in spans(t.command,8) if x not in t.before),key=lambda x:(-len(x),x))
    return [x for x in c if not any(x!=y and x in y for y in c)][:12]+c[:8]

def object_candidates(t:Turn):
    c=[x for _,_,x in spans(t.command,8) if x in t.before and len(x)>=2]
    return sorted(set(c),key=lambda x:(-len(x),x))[:8]

def apply_rule(before,value,rule):
    hits=[]; start=0
    while start<=len(before):
        i=before.find(rule.left,start) if rule.left else start
        if i<0: break
        a=i+len(rule.left); b=before.find(rule.right,a) if rule.right else len(before)
        if b>=a and shape(before[a:b])==rule.old_shape: hits.append((a,b))
        start=i+1
        if not rule.left: break
    if len(hits)!=1: return None
    a,b=hits[0]
    return before[:a]+value+before[b:]

class Model:
    def __init__(self,method):
        self.method=method; self.rules=[]; self.support=Counter()
        self.active_rule=None; self.active_object=""; self.hysteresis=0.0
        self.switches=0; self.retains=0; self.train_s=0.0
    def fit(self,dialogs):
        t0=time.perf_counter(); counts=Counter()
        for rows in dialogs:
            for t in rows:
                r=induce_rule(t)
                if r: counts[r]+=1
        self.rules=[r for r,n in counts.most_common(64) if n>=2]
        self.support=counts; self.train_s=time.perf_counter()-t0
    def reset(self):
        self.active_rule=None; self.active_object=""; self.hysteresis=0.0
        self.switches=0; self.retains=0
    def propose(self,t):
        props=[]
        for r in self.rules:
            for v in value_candidates(t):
                pred=apply_rule(t.before,v,r)
                if pred is None: continue
                objs=object_candidates(t); explicit=max(objs,key=len) if objs else ""
                props.append({"rule":r,"value":v,"pred":pred,"obj":explicit,"surface":float(self.support[r])+(1 if explicit and shape(explicit)==r.obj_shape else 0)+(1 if v in t.command else 0)})
        return props
    def predict(self,t):
        props=self.propose(t)
        if not props:
            if self.method in ("carry","hysteresis") and self.active_rule is not None:
                for v in value_candidates(t):
                    pred=apply_rule(t.before,v,self.active_rule)
                    if pred is not None:
                        self.retains+=1
                        return {"rule":self.active_rule,"value":v,"pred":pred,"obj":self.active_object},True
            return None,False
        for p in props:
            p["score"]=p["surface"]
            if self.method=="carry" and self.active_rule==p["rule"]: p["score"]+=2.0
            if self.method=="hysteresis":
                explicit=bool(p["obj"]); same=self.active_rule==p["rule"]
                if same and not explicit: p["score"]+=2.5+self.hysteresis
                elif same: p["score"]+=0.5*self.hysteresis
                elif explicit: p["score"]+=1.5
                else: p["score"]-=1.0
        props.sort(key=lambda p:p["score"],reverse=True); top=props[0]["score"]
        tied=[p for p in props if abs(p["score"]-top)<1e-9]
        if len(tied)!=1: return None,False
        best=tied[0]
        if self.method=="stateless": return best,False
        if self.active_rule is not None and best["rule"]!=self.active_rule:
            self.switches+=1
            if self.method=="hysteresis" and not best["obj"]:
                for v in value_candidates(t):
                    pred=apply_rule(t.before,v,self.active_rule)
                    if pred is not None:
                        self.retains+=1; self.hysteresis=min(3.0,self.hysteresis+0.5)
                        return {"rule":self.active_rule,"value":v,"pred":pred,"obj":self.active_object},True
        self.hysteresis=min(3.0,self.hysteresis+0.5) if self.active_rule==best["rule"] else 0.5
        self.active_rule=best["rule"]
        if best["obj"]: self.active_object=best["obj"]
        return best,False

def evaluate(seed,mode):
    train=[make_dialog(seed+i,18,m) for i,m in enumerate(("seen","paraphrase","order","paragraph","plan"))]
    test=make_dialog(seed+999,18,mode); out={}
    for method in ("stateless","carry","hysteresis","shuffled"):
        model=Model("hysteresis" if method=="shuffled" else method)
        fit_train=train
        if method=="shuffled":
            rng=random.Random(seed+77); flat=[t for d in train for t in d]; rng.shuffle(flat); fit_train=[flat]
        model.fit(fit_train); model.reset(); rows=[]; t0=time.perf_counter()
        for t in test:
            p,retained=model.predict(t)
            rows.append({"accuracy":p is not None and p["pred"]==t.after,"wrong":p is not None and p["pred"]!=t.after,"null":p is None,"kind":t.kind,"wrong_carry":retained and p is not None and p["pred"]!=t.after,"retained":retained})
        def cm(key,kind=None):
            xs=[float(x[key]) for x in rows if kind is None or x["kind"]==kind]
            return statistics.mean(xs) if xs else 0.0
        out[method]={"accuracy":cm("accuracy"),"wrong":cm("wrong"),"null":cm("null"),"explicit_accuracy":cm("accuracy","explicit"),"omitted_accuracy":cm("accuracy","omitted"),"switch_accuracy":cm("accuracy","switch"),"wrong_carry":cm("wrong_carry"),"retained_rate":cm("retained"),"rules":len(model.rules),"switches":model.switches,"retains":model.retains,"model_bytes":len(pickle.dumps(model)),"training_seconds":model.train_s,"inference_ms":(time.perf_counter()-t0)*1000/len(test)}
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); args=ap.parse_args()
    modes=("seen","paraphrase","order","paragraph","plan","counterfactual")
    raw={str(seed):{m:evaluate(seed,m) for m in modes} for seed in (1,7,19)}
    summary={m:{method:{k:statistics.mean(raw[str(seed)][m][method][k] for seed in (1,7,19)) for k in raw["1"][m][method]} for method in ("stateless","carry","hysteresis","shuffled")} for m in modes}
    payload={"cycle":39,"hypothesis":"Prediction-Error Hysteresis Cells from Delayed Paraphrase Re-entry","seeds":[1,7,19],"summary":summary,"raw":raw,"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"estimated_complexity":"induction O(NL); proposal O(RVL); recurrent update O(1) per event","final_test_after_future_used_for_ranking":False,"fixed_ontology_or_handwritten_slots_used_by_model":False,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(args.output,"w",encoding="utf-8") as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
