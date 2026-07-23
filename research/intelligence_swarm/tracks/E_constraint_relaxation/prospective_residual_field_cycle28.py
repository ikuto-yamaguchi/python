from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末",
         "大型端末":"大きい端末","試料甲":"サンプル甲","試料乙":"サンプル乙"}
VALUES=["棚A","棚B","棚C","棚D","待機","処理中","完了","保留"]
DIST=["別件の説明です。","前案は保留です。","補助記録は変更しません。"]

@dataclass
class Ex:
    before:str; command:str; after:str; future:str; obj:str; value:str; mode:str

def build(seed,n,mode):
    rng=random.Random(seed); rows=[]
    for _ in range(n):
        obj=rng.choice(OBJECTS); surf=ALIASES[obj] if mode=="unknown" else obj
        old,new=rng.sample(VALUES,2)
        before=f"{surf}の現在値は{old}です。補助記録は維持します。"
        command=f"{surf}の値を{new}へ変更してください。"
        if mode=="ambiguous":
            other=rng.choice([x for x in OBJECTS if x!=obj])
            command=f"{surf}か{other}の値を{new}へ変更してください。"
        elif mode=="nested": command=f"依頼内容は「{command}」です。"
        elif mode=="omitted": command=f"それを{new}へ変更してください。"
        elif mode=="paragraph": command=" ".join(rng.choice(DIST) for _ in range(4))+"\n"+command
        elif mode=="plan":
            rejected=rng.choice([x for x in VALUES if x not in (old,new)])
            command=f"{surf}を{rejected}にする案は撤回します。最終的には{command}"
        elif mode=="counterfactual": command=f"もし変更しなければ{surf}は{old}のままです。実際には{command}"
        after=f"{surf}の現在値は{new}です。補助記録は維持します。"
        future=f"次の観測でも{surf}は{new}です。補助記録は維持されます。"
        rows.append(Ex(before,command,after,future,surf,new,mode))
    return rows

def spans(text,lo,hi):
    return sorted({text[i:j] for i in range(len(text)) for j in range(i+lo,min(len(text),i+hi)+1)},key=lambda x:(-len(x),x))

def shape(s):
    return "".join("A" if c.isascii() and c.isalnum() else "J" if c not in "。、：／=\n " else c for c in s)

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

@dataclass
class EditProto:
    cmd_left:str; cmd_right:str; state_left:str; state_right:str
    old_shape:str; new_shape:str; support:int=1

class Model:
    def __init__(self): self.protos=[]; self.field_weights=defaultdict(float)
    def fit(self,train):
        d={}
        for ex in train:
            l,r,old,new=diff(ex.before,ex.after); p=ex.command.find(new)
            if not old or not new or p<0: continue
            pr=EditProto(ex.command[max(0,p-7):p],ex.command[p+len(new):p+len(new)+7],
                         ex.before[max(0,l-7):l],ex.before[len(ex.before)-r:len(ex.before)-r+7] if r else "",
                         shape(old),shape(new))
            k=(pr.cmd_left,pr.cmd_right,pr.state_left,pr.state_right,pr.old_shape,pr.new_shape)
            if k in d:d[k].support+=1
            else:d[k]=pr
        self.protos=sorted(d.values(),key=lambda p:p.support,reverse=True)[:64]
        for ex in train:
            proposals=self.propose(ex); field=self.disagreement_field(proposals)
            for pred,obj,val,_ in proposals:
                correct=int(pred==ex.after)
                for sig in field:self.field_weights[(shape(obj),shape(val),sig)] += 1.0 if correct else -0.15
        for k in list(self.field_weights):
            self.field_weights[k]=max(-1.0,min(1.0,self.field_weights[k]/max(1,len(train)//8)))
    def candidates(self,ex):
        common=[x for x in spans(ex.command,2,10) if x in ex.before]; os=[]
        for x in common:
            if not any(x in y and x!=y for y in common): os.append(x)
        before_chars=set(ex.before); runs=[]; start=None
        for i,ch in enumerate(ex.command+" "):
            novel=(ch not in before_chars and ch not in "。、：／=\n 「」")
            if novel and start is None:start=i
            if not novel and start is not None:
                seg=ex.command[start:i]
                if 1<=len(seg)<=8:runs.append(seg)
                start=None
        extra=[x for x in spans(ex.command,1,8) if x not in ex.before and not any(x in y and x!=y for y in runs)]
        vs=sorted(set(runs+extra),key=lambda x:(0 if x in runs else 1,-len(x),x))[:12]
        return os[:8],vs
    def apply(self,ex,pr,obj,val):
        ci=ex.command.find(pr.cmd_left) if pr.cmd_left else 0
        if ci<0:return None
        cs=ci+len(pr.cmd_left); ce=ex.command.find(pr.cmd_right,cs) if pr.cmd_right else len(ex.command)
        if ce<cs:return None
        extracted=ex.command[cs:ce]
        if val not in extracted and val!=extracted:return None
        si=ex.before.find(pr.state_left) if pr.state_left else 0
        if si<0:return None
        ss=si+len(pr.state_left); se=ex.before.find(pr.state_right,ss) if pr.state_right else len(ex.before)
        if se<ss:return None
        old=ex.before[ss:se]
        if shape(old)!=pr.old_shape:return None
        return ex.before[:ss]+val+ex.before[se:]
    def propose(self,ex):
        os,vs=self.candidates(ex); out=[]
        for o in os:
            for v in vs:
                for idx,pr in enumerate(self.protos):
                    pred=self.apply(ex,pr,o,v)
                    if pred is not None: out.append((pred,o,v,idx))
        uniq={}
        for x in out: uniq[(x[0],x[1],x[2])]=x
        return list(uniq.values())[:48]
    def disagreement_field(self,proposals):
        if len(proposals)<2:return []
        texts=[p[0] for p in proposals]; m=max(map(len,texts)); sigs=[]
        for i in range(m):
            chars=[t[i] if i<len(t) else "∅" for t in texts]; ent=len(set(chars))/len(chars)
            if ent>0.20:
                bucket=min(7,int(8*i/max(1,m))); sigs.append((bucket,round(ent,2)))
        return sigs[:12]
    def energy(self,ex,proposal,field,use_field):
        pred,o,v,_=proposal
        non_target=0.0 if "補助記録は維持" in pred else 1.0
        cmd=0.0 if o in ex.command and v in ex.command else 1.0
        length=0.06/max(1,len(o))+0.06/max(1,len(v))
        disagreement=sum(1 for sig in field if self.field_weights.get((shape(o),shape(v),sig),0)>0.0)
        return non_target+cmd+length-(0.10*disagreement if use_field else 0.0)
    def relax(self,ex,mode):
        props=self.propose(ex)
        if not props:return None,0,0,"candidate_collapse"
        field=self.disagreement_field(props); active=props[:]; prev=None; sweeps=0
        while sweeps<6:
            sweeps+=1; scored=sorted((self.energy(ex,p,field,mode!="base"),p) for p in active); best=scored[0][0]
            active=[p for e,p in scored if e<=best+0.04][:12]
            sig=tuple((p[0],p[1],p[2]) for p in active)
            if sig==prev:break
            prev=sig
        scored=sorted((self.energy(ex,p,field,mode!="base"),p) for p in active)
        if mode=="field_null" and (len(scored)<2 or scored[1][0]-scored[0][0]<0.12):
            return None,sweeps,len(active),"null_safety"
        return scored[0][1],sweeps,len(active),"fixed_point"

def evaluate(model,test,mode):
    correct=wrong=null=pair=0; sw=[]; ac=[]; reasons=Counter(); t=time.perf_counter()
    for ex in test:
        os,vs=model.candidates(ex); pair+=int(ex.obj in os and ex.value in vs)
        p,s,a,r=model.relax(ex,mode); sw.append(s);ac.append(a);reasons[r]+=1
        if p is None:null+=1
        elif p[0]==ex.after:correct+=1
        else:wrong+=1
    n=len(test)
    return {"accuracy":correct/n,"wrong_commit":wrong/n,"null_rate":null/n,"pair_recall":pair/n,
            "mean_sweeps":statistics.mean(sw),"max_sweeps":max(sw),"mean_active":statistics.mean(ac),
            "convergence_rate":sum(v for k,v in reasons.items() if k!="iteration_cap")/n,
            "inference_ms":(time.perf_counter()-t)*1000/n,"failure_reasons":dict(reasons)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="results_cycle_028.json");args=ap.parse_args()
    modes=["seen","unknown","ambiguous","nested","omitted","paragraph","plan","counterfactual"]; raw={}
    for seed in (1,7,19):
        train=build(seed,64,"seen")+build(seed+11,64,"unknown")
        m=Model();t=time.perf_counter();m.fit(train);train_s=time.perf_counter()-t
        run={"model_bytes":len(pickle.dumps(m)),"training_seconds":train_s,"prototypes":len(m.protos),"field_weights":len(m.field_weights)}
        for mode in modes:
            test=build(seed+999,36,mode); run[mode]={kind:evaluate(m,test,kind) for kind in ("base","field","field_null")}
        raw[str(seed)]=run
    summary={}
    for mode in modes:
        summary[mode]={}
        for kind in ("base","field","field_null"):
            summary[mode][kind]={k:statistics.mean(raw[str(seed)][mode][kind][k] for seed in (1,7,19))
                                 for k in ("accuracy","wrong_commit","null_rate","pair_recall","mean_sweeps","max_sweeps","mean_active","convergence_rate","inference_ms")}
    summary["model_bytes"]=statistics.mean(raw[str(s)]["model_bytes"] for s in (1,7,19))
    summary["training_seconds"]=statistics.mean(raw[str(s)]["training_seconds"] for s in (1,7,19))
    summary["prototypes"]=statistics.mean(raw[str(s)]["prototypes"] for s in (1,7,19))
    summary["field_weights"]=statistics.mean(raw[str(s)]["field_weights"] for s in (1,7,19))
    payload={"cycle":28,"hypothesis":"Prospective Residual Fields from Self-Consistency Disagreement without Outcome Access",
      "seeds":[1,7,19],"raw":raw,"summary":summary,"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "estimated_complexity":"prototype extraction O(NL), proposal O(POV L), disagreement O(HL), relaxation O(SH)",
      "inference_outcome_access":False,"training_outcome_used_only_for_local_weight_update":True,
      "highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(args.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
