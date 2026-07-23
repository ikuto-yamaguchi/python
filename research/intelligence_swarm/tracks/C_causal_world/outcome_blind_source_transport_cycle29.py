from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
import argparse,json,random,time,pickle,resource,statistics

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末","大型端末":"大きい端末","北側の鍵":"北のキー","南側の鍵":"南のキー","試料甲":"サンプル甲","試料乙":"サンプル乙"}
FIELDS=["場所","状態","担当"]
VALUES={"場所":["棚A","棚B","棚C","棚D"],"状態":["待機","処理中","完了","保留"],"担当":["担当一","担当二","担当三","担当四"]}
STATE=["{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。","{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。"]
CMD={"場所":["{o}を{v}へ移してください。","{o}の保管先を{v}へ変更します。"],"状態":["{o}を{v}にしてください。","{o}の進行状態を{v}へ切り替えます。"],"担当":["{o}を{v}の担当にしてください。","{o}の受け持ちを{v}へ変更します。"]}
HELD={"場所":["対象{o}、次から{v}で保管。"],"状態":["対象{o}は以後{v}扱い。"],"担当":["{o}は{v}へ引き継ぎ。"]}
OMIT={"場所":["それを{v}へ移してください。"],"状態":["その対象を{v}にしてください。"],"担当":["担当は{v}へ変えてください。"]}
DIST=["別件の資料を確認しました。","前の案はいったん保留です。","この文は更新と無関係です。"]

@dataclass
class Ex:
    before:str; command:str; after:str; future:str
    obj:str; field:str; old:str; new:str; mode:str; focus:str

@dataclass
class Program:
    cl:str; cr:str; sl:str; sr:str; old_shape:str; new_shape:str
    support:int=1; success:int=0; wrong:int=0; noexec:int=0; envs:tuple=()

def shape(s):
    return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、／=：:\n ' else c for c in s)

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

def state(o,d,form=0):
    return STATE[form].format(o=o,loc=d["場所"],status=d["状態"],owner=d["担当"])

def stream(seed,n,mode):
    rng=random.Random(seed); world={}; out=[]; focus=""
    for _ in range(n):
        canon=rng.choice(OBJECTS); o=ALIASES[canon] if mode=="rename" else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS})
        f=rng.choice(FIELDS); old=world[canon][f]; new=rng.choice([x for x in VALUES[f] if x!=old])
        form=1 if mode=="alternate" else 0
        before=state(o,world[canon],form)
        forms=OMIT[f] if mode=="omitted" else HELD[f] if mode in ("held","paragraph","plan","counterfactual") else CMD[f]
        command=rng.choice(forms).format(o=o,v=new)
        if mode=="paragraph": command=" ".join(rng.choice(DIST) for _ in range(3))+"\n"+command
        if mode=="plan":
            prior=rng.choice([x for x in VALUES[f] if x not in (old,new)])
            command=f"{o}を{prior}にする案でした。{rng.choice(DIST)} 最終的には"+command
        world[canon][f]=new; after=state(o,world[canon],form)
        future=f"次の観測でも{o}の更新結果は{new}で、補助記録は維持されます。"
        if mode=="counterfactual": future=f"もし更新しなければ{o}は{old}のままです。実行時は{new}です。"
        out.append(Ex(before,command,after,future,o,f,old,new,mode,focus)); focus=o
    return out

class Model:
    def __init__(self,kind):
        self.kind=kind; self.programs=[]; self.links=[]; self.training_seconds=0.0

    def extract_new(self,cmd,p):
        vals=[]; pos=0
        while True:
            i=cmd.find(p.cl,pos) if p.cl else pos
            if i<0: break
            st=i+len(p.cl); en=cmd.find(p.cr,st) if p.cr else len(cmd)
            if en>=st and 0<en-st<=14: vals.append(cmd[st:en])
            pos=i+1
            if not p.cl or pos>=len(cmd): break
        return min(vals,key=len) if vals else None

    def apply(self,before,cmd,p):
        new=self.extract_new(cmd,p)
        if new is None: return before,False
        hits=[]; pos=0
        while True:
            i=before.find(p.sl,pos) if p.sl else pos
            if i<0: break
            st=i+len(p.sl); en=before.find(p.sr,st) if p.sr else len(before)
            if en>=st and shape(before[st:en])==p.old_shape: hits.append((st,en))
            pos=i+1
            if not p.sl or pos>=len(before): break
        if len(hits)!=1: return before,False
        st,en=hits[0]
        return before[:st]+new+before[en:],True

    def fit(self,train):
        t=time.perf_counter(); dedup={}
        for e in train:
            l,r,old,new=diff(e.before,e.after)
            if not old or not new: continue
            cp=e.command.find(new)
            if cp<0: continue
            p=Program(e.command[max(0,cp-8):cp],e.command[cp+len(new):cp+len(new)+8],e.before[max(0,l-8):l],e.before[len(e.before)-r:len(e.before)-r+8] if r else "",shape(old),shape(new))
            k=(p.cl,p.cr,p.sl,p.sr,p.old_shape,p.new_shape)
            if k in dedup: dedup[k].support+=1
            else: dedup[k]=p
        self.programs=sorted(dedup.values(),key=lambda p:p.support,reverse=True)[:64]
        for p in self.programs:
            env=set()
            for e in train:
                pred,ok=self.apply(e.before,e.command,p)
                if not ok: p.noexec+=1
                elif pred==e.after: p.success+=1; env.add(e.mode)
                else: p.wrong+=1
            p.envs=tuple(sorted(env))
        if self.kind in ("transport","fiber"):
            groups=defaultdict(list)
            for i,p in enumerate(self.programs):
                if p.success>=2 and p.wrong==0: groups[(p.old_shape,p.new_shape)].append(i)
            self.links=[tuple(v) for v in groups.values() if len(v)>=2][:32]
        self.training_seconds=time.perf_counter()-t

    def predict(self,e):
        linked={i for g in self.links for i in g}; cand=[]
        for i,p in enumerate(self.programs):
            pred,ok=self.apply(e.before,e.command,p)
            if not ok: continue
            score=p.support+2*p.success-3*p.wrong
            if self.kind in ("transport","fiber") and i in linked:
                score+=0.4*sum(1 for g in self.links if i in g for _ in g)
            cand.append((score,pred))
        if not cand: return e.before,False,0
        by={}
        for score,pred in cand: by[pred]=max(by.get(pred,-1e9),score)
        ranked=sorted(((s,p) for p,s in by.items()),reverse=True)
        if len(ranked)>1 and ranked[0][0]-ranked[1][0]<1e-9: return e.before,False,len(ranked)
        return ranked[0][1],True,len(ranked)

def evaluate(seed,n,mode):
    train=[]
    for j,m in enumerate(("seen","held","rename","alternate")): train+=stream(seed+37*j,n//4,m)
    test=stream(seed+999,max(18,n//6),mode); out={}
    for kind in ("surface","transport","fiber"):
        model=Model(kind); model.fit(train); t=time.perf_counter(); cor=wrong=null=cand=0
        for e in test:
            pred,did,c=model.predict(e); cand+=c
            cor+=int(did and pred==e.after); wrong+=int(did and pred!=e.after); null+=int(not did)
        out[kind]={"accuracy":cor/len(test),"wrong_commit":wrong/len(test),"null_rate":null/len(test),"mean_candidates":cand/len(test),"programs":len(model.programs),"links":len(model.links),"eligible_programs":sum(p.success>=2 and p.wrong==0 for p in model.programs),"positive_executions":sum(p.success for p in model.programs),"wrong_executions":sum(p.wrong for p in model.programs),"model_bytes":len(pickle.dumps(model)),"training_seconds":model.training_seconds,"inference_ms":(time.perf_counter()-t)*1000/len(test)}
    return out

def sequential(seed,n):
    seq=stream(seed+700,n,"seen"); out={}
    for kind in ("surface","transport","fiber"):
        model=Model(kind); model.fit(seq[:n//2]); cov=cor=0
        for a,b in zip(seq[n//2:-1],seq[n//2+1:]):
            p1,d1,_=model.predict(a)
            b2=Ex(p1,b.command,b.after,b.future,b.obj,b.field,b.old,b.new,b.mode,b.focus)
            p2,d2,_=model.predict(b2)
            if d1 and d2: cov+=1; cor+=int(p2==b.after)
        out[kind]={"coverage":cov/max(1,len(seq[n//2:-1])),"accuracy_conditional":cor/max(1,cov)}
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="results_cycle_029.json"); args=ap.parse_args()
    modes=("seen","held","rename","alternate","omitted","paragraph","plan","counterfactual"); raw={}
    for n in (48,144,288):
        runs=[]
        for seed in (1,7,19):
            r={m:evaluate(seed,n,m) for m in modes}; r["sequential"]=sequential(seed,max(24,n//3)); runs.append(r)
        raw[str(n)]=runs
    summary={}
    for n,runs in raw.items():
        summary[n]={}
        for m in modes:
            summary[n][m]={}
            for kind in ("surface","transport","fiber"):
                summary[n][m][kind]={x:statistics.mean(r[m][kind][x] for r in runs) for x in runs[0][m][kind]}
        summary[n]["sequential"]={kind:{x:statistics.mean(r["sequential"][kind][x] for r in runs) for x in runs[0]["sequential"][kind]} for kind in ("surface","transport","fiber")}
    payload={"cycle":29,"hypothesis":"Outcome-Blind Positive Witness Birth from Source-Only Mechanism Transport","seeds":[1,7,19],"sizes":[48,144,288],"raw":raw,"summary":summary,"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"estimated_complexity":"program extraction O(NL), source-only audit O(PN), link grouping O(P), inference O(PL), P<=64","target_outcome_used_at_inference":False,"hidden_labels_used_by_learner":False,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(args.output,"w",encoding="utf-8") as f: json.dump(payload,f,ensure_ascii=False,indent=2)

if __name__=="__main__": main()
