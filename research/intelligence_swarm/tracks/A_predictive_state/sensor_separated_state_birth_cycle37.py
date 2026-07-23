from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse, json, pickle, random, resource, statistics, time

OBJS=["青い箱","赤い箱","小型端末","大型端末"]
VALS=["棚A","棚B","待機","完了"]
FILL=["補助記録は維持します。","別件は変えません。"]

@dataclass
class Ex:
    before:str; command:str; after:str; future:str
    obj:str; other:str; old:str; new:str; other_value:str; mode:str

@dataclass(frozen=True)
class Cell:
    ss:int; sw:int; vs:int; vw:int; os:int; ow:int

def make(seed,n,mode):
    r=random.Random(seed); out=[]
    for i in range(n):
        obj,other=r.sample(OBJS,2)
        old,new,otherv=r.sample(VALS,3)
        before=f"{obj}の現在値は{old}です。{other}の現在値は{otherv}です。{r.choice(FILL)}"
        if mode=="order": cmd=f"{new}へ変更してください、対象は{obj}です。"
        elif mode=="lexeme": cmd=f"対象{obj}は次から{new}扱いにします。"
        elif mode=="nested": cmd=f"依頼内容は「{obj}を{new}へ変更」です。"
        elif mode=="omitted": cmd=f"それを{new}へ変更してください。"
        elif mode=="paragraph": cmd=f"{r.choice(FILL)}\n{obj}を{new}へ変更してください。"
        elif mode=="plan": cmd=f"{obj}を{old}にする案は撤回し、最終的に{new}へ変更してください。"
        elif mode=="counterfactual": cmd=f"変更しなければ{obj}は{old}のまま。実際には{obj}を{new}へ変更してください。"
        else: cmd=f"{obj}を{new}へ変更してください。"
        after=before.replace(f"{obj}の現在値は{old}",f"{obj}の現在値は{new}",1)
        future=f"次の観測でも{obj}は{new}で、{other}は{otherv}です。"
        out.append(Ex(before,cmd,after,future,obj,other,old,new,otherv,mode))
    return out

def spans(s,maxw=8):
    for i in range(len(s)):
        for j in range(i+1,min(len(s),i+maxw)+1):
            x=s[i:j]
            if not any(c in x for c in "。、\n「」"): yield i,j,x

def candidate_cells(e,limit=64):
    state=[(i,j,x) for i,j,x in spans(e.before) if len(x)<=6]
    novel=[(i,j,x) for i,j,x in spans(e.command) if x not in e.before]
    common=[(i,j,x) for i,j,x in spans(e.command) if x in e.before and len(x)>=2]
    state=sorted(state,key=lambda z:abs(len(z[2])-len(e.old)))[:16]
    novel=sorted(novel,key=lambda z:-len(z[2]))[:12]
    common=sorted(common,key=lambda z:-len(z[2]))[:8]
    out=[]
    for si,sj,_ in state:
        for vi,vj,_ in novel:
            for oi,oj,_ in common[:4] or [(0,0,"")]:
                out.append(Cell(si,sj-si,vi,vj-vi,oi,oj-oi))
                if len(out)>=limit:return out
    return out

def cut(s,start,width):
    return s[start:start+width] if 0<=start<start+width<=len(s) else ""

def apply(e,c,value=None):
    if c.ss+c.sw>len(e.before): return None
    v=value if value is not None else cut(e.command,c.vs,c.vw)
    if not v:return None
    return e.before[:c.ss]+v+e.before[c.ss+c.sw:]

def synthetic_value_target(e,value):
    return e.before.replace(f"{e.obj}の現在値は{e.old}",f"{e.obj}の現在値は{value}",1)

def object_swap_ex(e):
    cmd=e.command.replace(e.obj,e.other,1)
    after=e.before.replace(f"{e.other}の現在値は{e.other_value}",f"{e.other}の現在値は{e.new}",1)
    future=f"次の観測でも{e.other}は{e.new}で、{e.obj}は{e.old}です。"
    return Ex(e.before,cmd,after,future,e.other,e.obj,e.other_value,e.new,e.old,e.mode)

def sensors(e,c,donor_value):
    pred=apply(e,c)
    if pred is None:return (0,0,0,0,0)
    value_swap=int(apply(e,c,donor_value)==synthetic_value_target(e,donor_value))
    oe=object_swap_ex(e)
    object_swap=int(apply(oe,c)==oe.after)
    future=int(e.new in e.future and e.other_value in e.future and pred==e.after)
    non_target=int(f"{e.other}の現在値は{e.other_value}" in pred)
    inverse=int(pred.replace(e.new,e.old,1)==e.before)
    return value_swap,object_swap,future,non_target,inverse

class Model:
    def __init__(self,mode):
        self.mode=mode; self.rules=Counter(); self.signature=Counter()
        self.audits=0; self.train_s=0; self.channel_accept=Counter()
    def fit(self,ind,probe):
        t=time.perf_counter()
        seeds=Counter()
        for e in ind:
            ss=e.before.find(e.old)
            vs=e.command.find(e.new)
            os=e.command.find(e.obj)
            if ss>=0 and vs>=0:
                c=Cell(ss,len(e.old),vs,len(e.new),os if os>=0 else 0,len(e.obj) if os>=0 else 0)
                seeds[c]+=1
            for c in candidate_cells(e):
                p=apply(e,c)
                if p==e.after: seeds[c]+=1
        pool=[c for c,_ in seeds.most_common(48)]
        for idx,e in enumerate(probe):
            donor=probe[(idx+1)%len(probe)].new
            for c in pool:
                self.audits+=1
                sig=sensors(e,c,donor)
                if self.mode=="shuffle":
                    parts=[sensors(probe[(idx+k)%len(probe)],c,probe[(idx+k+1)%len(probe)].new)[k]
                           for k in range(5)]
                    sig=tuple(parts)
                if self.mode=="shared":
                    ok=int(apply(e,c)==e.after)
                elif self.mode=="single":
                    ok=sig[0]
                else:
                    ok=int(sum(sig)>=3)
                if ok:
                    self.rules[c]+=1; self.signature[(c,sig)]+=1
                    for k,v in enumerate(sig):
                        if v:self.channel_accept[k]+=1
        self.rules=Counter({c:n for c,n in self.rules.items() if n>=2})
        self.train_s=time.perf_counter()-t
    def predict(self,e):
        ps=[]
        for c,n in self.rules.items():
            p=apply(e,c)
            if p is not None: ps.append((n,p,c))
        if not ps:return None,0
        ps.sort(reverse=True); top=ps[0][0]; a=[x for x in ps if x[0]==top]
        return (a[0] if len(a)==1 else None),len(a)

def evaluate(seed,mode):
    train=make(seed,36,"seen")+make(seed+1,18,"paragraph")+make(seed+2,18,"plan")
    cutn=48; ind,probe=train[:cutn],train[cutn:]
    test=make(seed+999,18,mode); out={}
    for method in ("shared","single","separated","shuffle"):
        m=Model(method);m.fit(ind,probe); rows=[]; t=time.perf_counter()
        for e in test:
            p,a=m.predict(e)
            rows.append((p is not None and p[1]==e.after,p is not None and p[1]!=e.after,p is None,a))
        out[method]={
          "accuracy":statistics.mean(float(x[0]) for x in rows),
          "wrong":statistics.mean(float(x[1]) for x in rows),
          "null":statistics.mean(float(x[2]) for x in rows),
          "mean_active":statistics.mean(x[3] for x in rows),
          "rules":len(m.rules),"probe_audits":m.audits,
          "value_sensor_accept":m.channel_accept[0],"object_sensor_accept":m.channel_accept[1],
          "future_sensor_accept":m.channel_accept[2],"non_target_sensor_accept":m.channel_accept[3],
          "inverse_sensor_accept":m.channel_accept[4],
          "model_bytes":len(pickle.dumps(m)),"training_seconds":m.train_s,
          "inference_ms":(time.perf_counter()-t)*1000/len(test)
        }
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output");a=ap.parse_args()
    modes=("seen","order","lexeme","nested","omitted","paragraph","plan","counterfactual")
    raw={str(s):{m:evaluate(s,m) for m in modes} for s in (1,7,19)}
    summary={}
    for m in modes:
        summary[m]={}
        for method in ("shared","single","separated","shuffle"):
            summary[m][method]={k:statistics.mean(raw[str(s)][m][method][k] for s in (1,7,19))
                                for k in raw["1"][m][method]}
    payload={"cycle":37,"hypothesis":"Counterfactual Sensor Separation for Multi-Channel Predictive State Birth",
      "seeds":[1,7,19],"summary":summary,"raw":raw,
      "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "estimated_complexity":"candidate O(L^2) bounded 64; probe O(QC); inference O(R)",
      "final_test_outcome_used_for_ranking":False,
      "highschool_level_passed":False,"native_japanese_communication_passed":False,
      "weak_smartphone_verified":False,"completion":False}
    open(a.output,"w",encoding="utf-8").write(json.dumps(payload,ensure_ascii=False,indent=2))
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
