from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict, Counter
import argparse,json,math,pickle,random,resource,statistics,time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末","大型端末":"大きい端末",
"北側の鍵":"北のキー","南側の鍵":"南のキー","試料甲":"サンプル甲","試料乙":"サンプル乙"}
FIELDS=["場所","状態","担当"]
VALUES={"場所":["棚A","棚B","棚C","棚D"],"状態":["待機","処理中","完了","保留"],"担当":["担当一","担当二","担当三","担当四"]}
STATE=["{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。",
       "{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。"]
CMD={"場所":["{o}を{v}へ移してください。","{o}の保管先を{v}へ変更します。"],
"状態":["{o}を{v}にしてください。","{o}の進行状態を{v}へ切り替えます。"],
"担当":["{o}を{v}の担当にしてください。","{o}の受け持ちを{v}へ変更します。"]}
HELD={"場所":["対象{o}は次から{v}で保管。"],"状態":["対象{o}は以後{v}扱い。"],"担当":["{o}は{v}へ引き継ぎ。"]}
OMIT={"場所":["それを{v}へ移してください。"],"状態":["その対象を{v}にしてください。"],"担当":["担当は{v}へ変えてください。"]}
DIST=["別件の資料を確認しました。","旧案はいったん保留です。","この文は更新と無関係です。"]

@dataclass
class Ex:
    before:str; command:str; after:str; future:str; env:int
    obj:str; field:str; old:str; new:str; focus:str
@dataclass
class Event:
    cl:str;cr:str;sl:str;sr:str;oldshape:str;newshape:str;support:int=1
    signature:tuple=(); stability:float=0.0; cls:int=-1

def state(o,d,form): return STATE[form].format(o=o,loc=d["場所"],status=d["状態"],owner=d["担当"])
def shape(s): return ''.join("A" if c.isascii() and c.isalnum() else "J" if c not in "。、／=：:\n " else c for c in s)
def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def grams(s):
    s=''.join(s.split());return Counter(s[i:i+n] for n in (1,2,3) for i in range(max(0,len(s)-n+1)))
def cos(a,b):
    d=sum(v*b.get(k,0) for k,v in a.items());na=math.sqrt(sum(v*v for v in a.values()));nb=math.sqrt(sum(v*v for v in b.values()))
    return d/(na*nb+1e-12)

def build(seed,n,mode,env):
    rng=random.Random(seed);world={};out=[];focus=""
    for _ in range(n):
        canon=rng.choice(OBJECTS);surf=ALIASES[canon] if mode=="rename" else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS})
        f=rng.choice(FIELDS);old=world[canon][f];new=rng.choice([v for v in VALUES[f] if v!=old])
        form=1 if mode=="alternate" else 0
        before=state(surf,world[canon],form)
        forms=OMIT[f] if mode=="omitted" else HELD[f] if mode in ("held","paragraph","plan","counterfactual") else CMD[f]
        command=rng.choice(forms).format(o=surf,v=new)
        if mode=="paragraph":command=" ".join(rng.choice(DIST) for _ in range(3))+"\n"+command
        if mode=="plan":
            oldplan=rng.choice([v for v in VALUES[f] if v not in (old,new)])
            command=f"{surf}を{oldplan}にする案でした。{rng.choice(DIST)} 最終的には"+command
        world[canon][f]=new;after=state(surf,world[canon],form)
        future=f"次の観測でも{surf}の更新結果は{new}で、補助記録は維持されます。"
        if mode=="counterfactual":future=f"もし実行しなければ{surf}は{old}のままです。実行時は{new}です。"
        out.append(Ex(before,command,after,future,env,surf,f,old,new,focus));focus=surf
    return out

class Model:
    def __init__(self,kind):
        self.kind=kind;self.events=[];self.classes=[];self.edges=[];self.train_seconds=0
    def extract(self,cmd,e):
        i=cmd.find(e.cl) if e.cl else 0
        if i<0:return None
        st=i+len(e.cl);en=cmd.find(e.cr,st) if e.cr else len(cmd)
        if en<st:return None
        x=cmd[st:en];return x if 0<len(x)<=14 else None
    def apply(self,before,cmd,e):
        v=self.extract(cmd,e)
        if v is None:return before,False,0
        hits=[];p=0
        while True:
            i=before.find(e.sl,p) if e.sl else p
            if i<0:break
            st=i+len(e.sl);en=before.find(e.sr,st) if e.sr else len(before)
            if en>=st:hits.append((st,en))
            p=i+1
            if not e.sl or p>=len(before):break
        if len(hits)!=1:return before,False,len(hits)
        st,en=hits[0]
        if shape(before[st:en])!=e.oldshape:return before,False,1
        return before[:st]+v+before[en:],True,1
    def fit(self,train):
        t=time.perf_counter();d={}
        for x in train:
            l,r,old,new=diff(x.before,x.after)
            if not old or not new:continue
            p=x.command.find(new)
            if p<0:continue
            e=Event(x.command[max(0,p-8):p],x.command[p+len(new):p+len(new)+8],
                    x.before[max(0,l-8):l],x.before[len(x.before)-r:len(x.before)-r+8] if r else "",
                    shape(old),shape(new))
            k=(e.cl,e.cr,e.sl,e.sr,e.oldshape,e.newshape)
            if k in d:d[k].support+=1
            else:d[k]=e
        self.events=sorted(d.values(),key=lambda e:e.support,reverse=True)[:64]
        envs=sorted(set(x.env for x in train))
        for e in self.events:
            sig=[]
            for env in envs:
                rows=[x for x in train if x.env==env];s=w=n=dam=fut=0
                for x in rows:
                    pred,ok,amb=self.apply(x.before,x.command,e)
                    if not ok or amb!=1:n+=1
                    elif pred==x.after:s+=1
                    else:w+=1
                    if ok and "補助記録" not in pred:dam+=1
                    if ok:
                        _,_,_,nv=diff(x.before,pred);fut+=int(bool(nv and nv in x.future))
                z=max(1,len(rows));sig.append((round(s/z,2),round(w/z,2),round(n/z,2),round(dam/z,2),round(fut/z,2)))
            e.signature=tuple(sig)
            success=[q[0] for q in sig];wrong=[q[1] for q in sig];damage=[q[3] for q in sig]
            e.stability=max(0,1-statistics.pstdev(success)-statistics.mean(wrong)-statistics.mean(damage))
        if self.kind in ("identity","graph"):
            buckets=defaultdict(list)
            for i,e in enumerate(self.events):
                key=tuple(tuple(round(v/0.25)*0.25 for v in q) for q in e.signature)
                buckets[key].append(i)
            for ids in buckets.values():
                if len(ids)>=2 and statistics.mean(self.events[i].stability for i in ids)>=0.65:
                    cid=len(self.classes);self.classes.append(tuple(ids))
                    for i in ids:self.events[i].cls=cid
        if self.kind=="graph":
            for ci,c in enumerate(self.classes):
                for cj,dids in enumerate(self.classes):
                    if ci==cj:continue
                    a=self.events[c[0]];b=self.events[dids[0]]
                    if a.newshape==b.oldshape and a.stability>.65 and b.stability>.65:
                        self.edges.append((ci,cj,min(a.stability,b.stability)))
            self.edges=sorted(self.edges,key=lambda z:z[2],reverse=True)[:96]
        self.train_seconds=time.perf_counter()-t
    def predict(self,x):
        cand=[];cg=grams(x.command);sg=grams(x.before)
        for i,e in enumerate(self.events):
            pred,ok,amb=self.apply(x.before,x.command,e)
            if not ok or amb!=1:continue
            score=.45*cos(cg,grams(e.cl+"|"+e.cr))+.35*cos(sg,grams(e.sl+"|"+e.sr))+.2*min(1,e.support/4)
            if self.kind in ("identity","graph"):score+=.25*e.stability+.10*(e.cls>=0)
            if self.kind=="graph" and e.cls>=0:score+=.02*sum(1 for a,_,_ in self.edges if a==e.cls)
            cand.append((score,pred))
        if not cand:return x.before,0,1
        cand.sort(reverse=True)
        if len(cand)>1 and cand[0][0]-cand[1][0]<.02:return x.before,len(cand),1
        return cand[0][1],len(cand),0

def evaluate(seed,n,mode):
    train=[]
    for env,m in enumerate(("seen","held","rename","alternate")):train+=build(seed+17*env,n//4,m,env)
    test=build(seed+999,max(12,n//6),mode,99);out={}
    for kind in ("surface","identity","graph"):
        M=Model(kind);M.fit(train);t=time.perf_counter();c=w=z=cs=0
        for x in test:
            p,k,nul=M.predict(x);cs+=k;c+=int(p==x.after);w+=int(p!=x.after and not nul);z+=nul
        out[kind]={"accuracy":c/len(test),"wrong_commit":w/len(test),"null_rate":z/len(test),
        "mean_candidates":cs/len(test),"events":len(M.events),"identity_classes":len(M.classes),"identity_members":sum(len(q) for q in M.classes),
        "edges":len(M.edges),"mean_stability":statistics.mean([e.stability for e in M.events]) if M.events else 0,
        "model_bytes":len(pickle.dumps(M)),"training_seconds":M.train_seconds,"inference_ms":(time.perf_counter()-t)*1000/len(test)}
    return out

def sequential(seed,n):
    seq=build(seed+700,n,"seen",0);out={}
    for kind in ("surface","identity","graph"):
        M=Model(kind);M.fit(seq[:n//2]);cov=cor=0
        for a,b in zip(seq[n//2:-1],seq[n//2+1:]):
            p1,c1,z1=M.predict(a);b2=Ex(p1,b.command,b.after,b.future,b.env,b.obj,b.field,b.old,b.new,b.focus)
            p2,c2,z2=M.predict(b2)
            if c1 and c2 and not z1 and not z2:cov+=1;cor+=int(p2==b.after)
        out[kind]={"coverage":cov/max(1,len(seq[n//2:-1])),"accuracy_conditional":cor/max(1,cov)}
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="results_cycle_025.json");a=ap.parse_args()
    modes=("seen","held","rename","alternate","omitted","paragraph","plan","counterfactual");raw={}
    for n in (48,144,288):
        runs=[]
        for seed in (1,7,19):
            r={m:evaluate(seed,n,m) for m in modes};r["sequential"]=sequential(seed,max(24,n//3));runs.append(r)
        raw[str(n)]=runs
    summary={}
    for n,runs in raw.items():
        summary[n]={}
        for m in modes:
            summary[n][m]={k:{x:statistics.mean(r[m][k][x] for r in runs) for x in runs[0][m][k]} for k in ("surface","identity","graph")}
        summary[n]["sequential"]={k:{x:statistics.mean(r["sequential"][k][x] for r in runs) for x in runs[0]["sequential"][k]} for k in ("surface","identity","graph")}
    payload={"hypothesis":"Environment-Paired Mechanism Residual Partitions for Event Identity","seeds":[1,7,19],"sizes":[48,144,288],
    "raw":raw,"summary":summary,"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    "estimated_complexity":"event extraction O(NL), environment replay O(PNE), partition O(P), graph O(C^2), inference O(PL)",
    "hidden_labels_used_by_learner":False,"highschool_level_passed":False,"native_japanese_communication_passed":False,
    "weak_smartphone_verified":False,"completion":False}
    with open(a.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary["288"],ensure_ascii=False,indent=2))
if __name__=="__main__":main()
