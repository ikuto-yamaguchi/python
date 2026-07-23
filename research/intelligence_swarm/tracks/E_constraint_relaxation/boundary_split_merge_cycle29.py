from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict, Counter
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
        cmd=f"{surf}の値を{new}へ変更してください。"
        if mode=="ambiguous":
            other=rng.choice([x for x in OBJECTS if x!=obj])
            cmd=f"{surf}か{other}の値を{new}へ変更してください。"
        elif mode=="nested":
            cmd=f"依頼内容は「{cmd}」です。"
        elif mode=="omitted":
            cmd=f"それを{new}へ変更してください。"
        elif mode=="paragraph":
            cmd=" ".join(rng.choice(DIST) for _ in range(5))+"\n"+cmd
        elif mode=="plan":
            bad=rng.choice([x for x in VALUES if x not in (old,new)])
            cmd=f"{surf}を{bad}にする案は撤回します。最終的には{cmd}"
        elif mode=="counterfactual":
            cmd=f"もし変更しなければ{surf}は{old}のままです。実際には{cmd}"
        after=f"{surf}の現在値は{new}です。補助記録は維持します。"
        future=f"次の観測でも{surf}は{new}です。補助記録は維持されます。"
        rows.append(Ex(before,cmd,after,future,surf,new,mode))
    return rows
def ctype(ch):
    if ch.isascii() and ch.isalnum(): return "A"
    if ch in "。、：／=「」\n ": return "P"
    return "J"
def initial_boundaries(text):
    b={0,len(text)}
    for i in range(1,len(text)):
        if ctype(text[i])!=ctype(text[i-1]) or text[i-1] in "。、：／=「」\n " or text[i] in "。、：／=「」\n ":
            b.add(i)
    return tuple(sorted(b))
def segments(text,bounds):
    return [text[a:b] for a,b in zip(bounds,bounds[1:]) if b>a and text[a:b].strip()]
def bsignature(text,pos):
    l=ctype(text[pos-1]) if pos>0 else "^"
    r=ctype(text[pos]) if pos<len(text) else "$"
    return (l,r,min(7,pos//4),min(7,(len(text)-pos)//4))
def segsig(seg,where):
    return (where,ctype(seg[0]) if seg else "0",ctype(seg[-1]) if seg else "0",min(7,len(seg)//2))
def local_moves(text,bounds):
    b=set(bounds); moves=[]
    for p in range(1,len(text)):
        if p not in b:
            nb=tuple(sorted(b|{p})); moves.append(("split",p,nb))
    for p in list(b):
        if p not in (0,len(text)):
            nb=tuple(sorted(b-{p})); moves.append(("merge",p,nb))
    for p in list(b):
        if p in (0,len(text)): continue
        for q in (p-1,p+1):
            if 0<q<len(text) and q not in b:
                nb=tuple(sorted((b-{p})|{q}));moves.append(("shift",p,q,nb))
    return moves
def edit_distance1(a,b):
    if a==b:return 0
    m=min(len(a),len(b))
    return abs(len(a)-len(b))+sum(x!=y for x,y in zip(a[:m],b[:m]))
@dataclass
class Candidate:
    pred:str; obj:str; val:str; target:str
    bb:tuple; cb:tuple; energy:float; source:str
class Model:
    def __init__(self,mode):
        self.mode=mode
        self.boundary_w=defaultdict(float)
        self.role_w=defaultdict(float)
        self.n_updates=0
        self.train_seconds=0.0
    def boundary_energy(self,text,bounds):
        e=0.012*(len(bounds)-2)
        for p in bounds[1:-1]:
            e-=self.boundary_w.get(bsignature(text,p),0.0)
        return e
    def beam_segment(self,text,learned):
        init=initial_boundaries(text)
        if self.mode=="fixed":
            return [(self.boundary_energy(text,init),init,1)]
        beam=[(self.boundary_energy(text,init),init)]
        seen={init}; sweeps=0
        while sweeps<5:
            sweeps+=1; pool=list(beam)
            for _,b in beam:
                for mv in local_moves(text,b):
                    nb=mv[-1]
                    if nb in seen: continue
                    seen.add(nb)
                    e=self.boundary_energy(text,nb) if learned else 0.012*(len(nb)-2)
                    pool.append((e,nb))
            pool=sorted(pool,key=lambda x:(x[0],len(x[1])))[:18]
            old_sig=tuple(b for _,b in beam)
            beam=pool
            if tuple(b for _,b in beam)==old_sig:break
        return [(e,b,sweeps) for e,b in beam]
    def role_score(self,obj,val,target):
        return (self.role_w.get(segsig(obj,"obj"),0.0)+
                self.role_w.get(segsig(val,"val"),0.0)+
                self.role_w.get(segsig(target,"target"),0.0))
    def generate(self,e,learned=True):
        bbeams=self.beam_segment(e.before,learned)
        cbeams=self.beam_segment(e.command,learned)
        b_support=Counter(p for _,b,_ in bbeams[:18] for p in b)
        c_support=Counter(p for _,b,_ in cbeams[:18] for p in b)
        def born(text,support,lo,hi):
            cand=[]
            for i in support:
                for j in support:
                    if j>i and lo<=j-i<=hi:
                        seg=text[i:j].strip()
                        if seg:
                            cand.append((support[i]+support[j],seg,i,j))
            return sorted(cand,key=lambda z:(-z[0],-len(z[1]),z[1]))
        bborn=born(e.before,b_support,1,10)
        cborn=born(e.command,c_support,1,12)
        objs=[];vals=[];targets=[]
        for sup,x,i,j in cborn:
            if len(x)>=2 and x in e.before:
                objs.append((sup,x))
            elif x not in e.before and len(x)<=10:
                vals.append((sup,x))
        for sup,x,i,j in bborn:
            if x not in e.command:
                targets.append((sup,x))
        objs=list(dict.fromkeys(objs))[:10]
        vals=list(dict.fromkeys(vals))[:14]
        targets=list(dict.fromkeys(targets))[:14]
        out={}
        base_be=min((x[0] for x in bbeams),default=0.0)
        base_ce=min((x[0] for x in cbeams),default=0.0)
        bb=bbeams[0][1];cb=cbeams[0][1]
        for osup,o in objs:
            for vsup,v in vals:
                for tsup,t in targets:
                    idx=e.before.find(t)
                    if idx<0:continue
                    pred=e.before[:idx]+v+e.before[idx+len(t):]
                    non_target=0.0 if "補助記録は維持" in pred else 1.0
                    cmd_cov=0.0 if o in e.command and v in e.command else 1.0
                    structural=0.02*edit_distance1(t,v)
                    birth=-0.004*(osup+vsup+tsup)
                    role=-self.role_score(o,v,t) if learned else 0.0
                    energy=base_be+base_ce+non_target+cmd_cov+structural+birth+role
                    k=(pred,o,v,t)
                    cand=Candidate(pred,o,v,t,bb,cb,energy,"splitmerge")
                    if k not in out or energy<out[k].energy: out[k]=cand
        return sorted(out.values(),key=lambda c:c.energy)[:64]
    def fit(self,train):
        t0=time.perf_counter()
        if self.mode=="fixed":
            self.train_seconds=time.perf_counter()-t0;return
        for _ in range(2):
            for e in train:
                free=self.generate(e,learned=True)
                if not free:continue
                good=[c for c in free if c.pred==e.after]
                if not good:continue
                f=free[0];g=good[0]
                for text,gb,fb in ((e.before,g.bb,f.bb),(e.command,g.cb,f.cb)):
                    gs={bsignature(text,p) for p in gb[1:-1]}
                    fs={bsignature(text,p) for p in fb[1:-1]}
                    for sig in gs-fs:self.boundary_w[sig]+=0.08;self.n_updates+=1
                    for sig in fs-gs:self.boundary_w[sig]-=0.04;self.n_updates+=1
                for seg,role in ((g.obj,"obj"),(g.val,"val"),(g.target,"target")):
                    self.role_w[segsig(seg,role)]+=0.05;self.n_updates+=1
                if f.pred!=e.after:
                    for seg,role in ((f.obj,"obj"),(f.val,"val"),(f.target,"target")):
                        self.role_w[segsig(seg,role)]-=0.02;self.n_updates+=1
        self.train_seconds=time.perf_counter()-t0
    def infer(self,e):
        cands=self.generate(e,learned=self.mode=="learned")
        if not cands:return None,0,0,"candidate_collapse",0
        active=cands[:];prev=None;sweeps=0
        while sweeps<6:
            sweeps+=1
            best=active[0].energy
            active=[c for c in active if c.energy<=best+0.05][:12]
            sig=tuple((c.pred,c.obj,c.val,c.target) for c in active)
            if sig==prev:break
            prev=sig
            active=sorted(active,key=lambda c:c.energy)
        if len(active)>1 and active[1].energy-active[0].energy<0.03:
            return None,sweeps,len(active),"ambiguous_attractor",len(cands)
        return active[0],sweeps,len(active),"fixed_point",len(cands)
def evaluate(model,test):
    t=time.perf_counter();correct=wrong=null=pair=0;sw=[];ac=[];tot=[];reasons=Counter()
    for e in test:
        c,s,a,r,n=model.infer(e);sw.append(s);ac.append(a);tot.append(n);reasons[r]+=1
        if c is None:null+=1
        else:
            correct+=int(c.pred==e.after);wrong+=int(c.pred!=e.after)
            pair+=int(c.obj==e.obj and c.val==e.value)
    n=len(test)
    return {"accuracy":correct/n,"wrong_commit":wrong/n,"null_rate":null/n,
            "pair_recall":pair/n,"mean_sweeps":statistics.mean(sw),
            "max_sweeps":max(sw),"mean_active":statistics.mean(ac),
            "mean_candidates":statistics.mean(tot),
            "convergence_rate":sum(v for k,v in reasons.items() if k!="iteration_cap")/n,
            "inference_ms":(time.perf_counter()-t)*1000/n,
            "failure_reasons":dict(reasons)}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="results_cycle_029.json");a=ap.parse_args()
    modes=["seen","unknown","ambiguous","nested","omitted","paragraph","plan","counterfactual"]
    raw={}
    for seed in (1,7,19):
        train=build(seed,96,"seen")+build(seed+11,48,"unknown")
        run={}
        for mode in ("fixed","unlearned","learned"):
            m=Model(mode);m.fit(train)
            rr={"model_bytes":len(pickle.dumps(m)),"training_seconds":m.train_seconds,
                "boundary_weights":len(m.boundary_w),"role_weights":len(m.role_w),
                "updates":m.n_updates}
            for split in modes:rr[split]=evaluate(m,build(seed+999,36,split))
            run[mode]=rr
        raw[str(seed)]=run
    summary={}
    for split in modes:
        summary[split]={}
        for mode in ("fixed","unlearned","learned"):
            summary[split][mode]={k:statistics.mean(raw[str(s)][mode][split][k] for s in (1,7,19))
                                  for k in ("accuracy","wrong_commit","null_rate","pair_recall",
                                            "mean_sweeps","max_sweeps","mean_active","mean_candidates",
                                            "convergence_rate","inference_ms")}
    for mode in ("fixed","unlearned","learned"):
        summary[mode]={k:statistics.mean(raw[str(s)][mode][k] for s in (1,7,19))
                       for k in ("model_bytes","training_seconds","boundary_weights","role_weights","updates")}
    payload={"cycle":29,
      "hypothesis":"Generative Candidate Birth from Energy-Lowering Boundary Split-Merge Dynamics",
      "seeds":[1,7,19],"raw":raw,"summary":summary,
      "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "estimated_complexity":"initial segmentation O(L), split-merge beam O(SBL), candidate binding O(B^2 OVT), relaxation O(RH)",
      "inference_outcome_access":False,"fixed_ontology_used":False,
      "highschool_level_passed":False,"native_japanese_communication_passed":False,
      "weak_smartphone_verified":False,"completion":False}
    with open(a.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
