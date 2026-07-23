from dataclasses import dataclass
from collections import Counter
import random,json,time,pickle,resource,statistics,argparse

OBJECTS=["青い箱","赤い箱","小型端末","大型端末"]
VALUES=["棚A","棚B","待機","完了"]
FILL=["補助記録は維持します。","別件は変えません。"]

@dataclass
class T:
    before:str; command:str; after:str; future:str; obj:str; old:str; new:str; mode:str

def make(seed,n,mode):
    r=random.Random(seed); w={}; out=[]
    for i in range(n):
        o=r.choice(OBJECTS); old=w.get(o,r.choice(VALUES)); new=r.choice([x for x in VALUES if x!=old])
        b=f"{o}の現在値は{old}です。{r.choice(FILL)}"
        if mode=="order": c=f"{new}へ変更してください、対象は{o}です。"
        elif mode=="lexeme": c=f"対象{o}は次から{new}扱いにします。"
        elif mode=="nested": c=f"依頼内容は「{o}を{new}へ変更」です。"
        elif mode=="omitted": c=f"それを{new}へ変更してください。"
        elif mode=="paragraph": c=f"{r.choice(FILL)}\n{o}を{new}へ変更してください。"
        elif mode=="plan": c=f"{o}を{old}にする案は撤回し、最終的に{new}へ変更してください。"
        elif mode=="counterfactual": c=f"変更しなければ{o}は{old}のまま。実際には{new}へ変更してください。"
        else:c=f"{o}を{new}へ変更してください。"
        a=f"{o}の現在値は{new}です。{r.choice(FILL)}"; f=f"次でも{o}は{new}です。"
        out.append(T(b,c,a,f,o,old,new,mode)); w[o]=new
    return out

def spans(s,maxw=6):
    for i in range(len(s)):
        for j in range(i+1,min(len(s),i+maxw)+1):
            x=s[i:j]
            if not any(c in x for c in "。、\n「」"): yield i,j,x

def candidates(t,limit=24):
    ss=[(i,j,x) for i,j,x in spans(t.before) if x in t.command or len(x)<=4]
    vs=[(i,j,x) for i,j,x in spans(t.command) if x not in t.before]
    out=[]
    for si,sj,sx in ss[:8]:
        for vi,vj,vx in vs[:8]:
            out.append((si,sj,vi,vj))
            if len(out)>=limit:return out
    return out

def apply(t,b):
    si,sj,vi,vj=b
    return t.before[:si]+t.command[vi:vj]+t.before[sj:]

def delta(a,b):
    n=min(len(a),len(b)); return abs(len(a)-len(b))+sum(a[i]!=b[i] for i in range(n))

def mutate(b,t):
    si,sj,vi,vj=b; out=[]
    for ds,de,dv,dve in [(-1,0,0,0),(1,0,0,0),(0,-1,0,0),(0,1,0,0),(0,0,-1,0),(0,0,1,0),(0,0,0,-1),(0,0,0,1)]:
        x=(si+ds,sj+de,vi+dv,vj+dve)
        if 0<=x[0]<x[1]<=len(t.before) and 0<=x[2]<x[3]<=len(t.command):out.append(x)
    return out

class M:
    def __init__(self,mode): self.mode=mode;self.rules=Counter();self.steps=0;self.audits=0;self.train=0
    def fit(self,ind,probe):
        t0=time.perf_counter(); base=Counter()
        for t in ind:
            cs=candidates(t)
            for b in sorted(cs,key=lambda b:delta(apply(t,b),t.after))[:3]:base[b]+=1
        if self.mode=="fixed":
            self.rules=Counter({b:n for b,n in base.items() if n>=2});self.train=time.perf_counter()-t0;return
        targets=[x.after for x in probe]
        if self.mode=="shuffle":targets=targets[1:]+targets[:1]
        learned=Counter()
        for t,target in zip(probe,targets):
            pop=candidates(t)
            for _ in range(2):
                ranked=sorted(pop,key=lambda b:delta(apply(t,b),target))[:4]
                births=[]
                for b in ranked:
                    bs=delta(apply(t,b),target)
                    val=t.command[b[2]:b[3]]
                    bc=0 if val in target else len(val)+1
                    for m in mutate(b,t):
                        ms=delta(apply(t,m),target)
                        mv=t.command[m[2]:m[3]]
                        mc=0 if mv in target else len(mv)+1
                        self.audits+=1
                        ok=(ms<bs) if self.mode=="oneway" else ((ms<bs and mc<=bc) or (mc<bc and ms<=bs))
                        if ok:births.append(m)
                self.steps+=len(births);pop=list(dict.fromkeys(ranked+births))[:16]
            for b in sorted(pop,key=lambda b:delta(apply(t,b),target))[:2]:
                if apply(t,b)==target:learned[b]+=1
        self.rules=Counter({b:n for b,n in learned.items() if n>=2});self.train=time.perf_counter()-t0
    def pred(self,t):
        ps=[(n,apply(t,b),b) for b,n in self.rules.items() if b[1]<=len(t.before) and b[3]<=len(t.command)]
        if not ps:return None,0
        ps.sort(reverse=True); top=ps[0][0];active=[p for p in ps if p[0]==top]
        return (active[0] if len(active)==1 else None),len(active)

def evalone(seed,mode):
    train=[]
    for j,m in enumerate(("seen","paragraph","plan")):train+=make(seed+j,10,m)
    cut=20;ind,probe=train[:cut],train[cut:];test=make(seed+99,12,mode);out={}
    for method in ("fixed","oneway","reciprocal","shuffle"):
        m=M(method);m.fit(ind,probe);t0=time.perf_counter();rows=[]
        for x in test:
            p,a=m.pred(x);rows.append((p is not None and p[1]==x.after,p is not None and p[1]!=x.after,p is None,a))
        out[method]={"accuracy":statistics.mean(float(x[0]) for x in rows),"wrong":statistics.mean(float(x[1]) for x in rows),"null":statistics.mean(float(x[2]) for x in rows),"mean_active":statistics.mean(x[3] for x in rows),"rules":len(m.rules),"transport_steps":m.steps,"probe_audits":m.audits,"model_bytes":len(pickle.dumps(m)),"training_seconds":m.train,"inference_ms":(time.perf_counter()-t0)*1000/len(test)}
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output");a=ap.parse_args()
    modes=("seen","order","lexeme","nested","omitted","paragraph","plan","counterfactual")
    raw={str(s):{m:evalone(s,m) for m in modes} for s in (1,7,19)}
    summary={}
    for m in modes:
        summary[m]={}
        for method in ("fixed","oneway","reciprocal","shuffle"):
            summary[m][method]={k:statistics.mean(raw[str(s)][m][method][k] for s in (1,7,19)) for k in raw["1"][m][method]}
    payload={"cycle":36,"hypothesis":"Reciprocal Boundary Birth from Cross-View Predictive Error Transport","seeds":[1,7,19],"summary":summary,"raw":raw,"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"estimated_complexity":"candidate O(L^2) bounded 24; transport O(QSHM); inference O(R)","final_test_outcome_used_for_ranking":False,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    open(a.output,"w",encoding="utf-8").write(json.dumps(payload,ensure_ascii=False,indent=2))
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
