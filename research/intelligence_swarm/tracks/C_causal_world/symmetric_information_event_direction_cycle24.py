from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末","大型端末":"大きい端末",
"北側の鍵":"北のキー","南側の鍵":"南のキー","試料甲":"サンプル甲","試料乙":"サンプル乙"}
FIELDS=["場所","状態","担当"]
VALUES={"場所":["棚A","棚B","棚C","棚D"],"状態":["待機","処理中","完了","保留"],"担当":["担当一","担当二","担当三","担当四"]}
STATE_FORMS=[
"{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。",
"{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。"]
CMD={"場所":["{o}を{v}へ移してください。","{o}の保管先を{v}へ変更します。"],
"状態":["{o}を{v}にしてください。","{o}の進行状態を{v}へ切り替えます。"],
"担当":["{o}を{v}の担当にしてください。","{o}の受け持ちを{v}へ変更します。"]}
HELD={"場所":["対象{o}、次から{v}で保管。"],"状態":["対象{o}は以後{v}扱い。"],"担当":["{o}は{v}へ引き継ぎ。"]}
OMIT={"場所":["それを{v}へ移してください。"],"状態":["その対象を{v}にしてください。"],"担当":["担当は{v}へ変えてください。"]}
DIST=["別件の資料を確認しました。","前の案はいったん保留です。","この文は更新と無関係です。"]

@dataclass
class Ex:
    before:str; command:str; after:str; future:str
    obj:str; field:str; old:str; new:str; mode:str; focus:str

@dataclass
class Event:
    cl:str; cr:str; sl:str; sr:str
    old_shape:str; new_shape:str
    old_values:tuple=(); new_values:tuple=()
    forward_success:int=0; forward_wrong:int=0
    reverse_success:int=0; reverse_wrong:int=0
    forward_null:int=0; reverse_null:int=0
    symmetric_score:float=0.0; support:int=1

def shape(s):
    return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、／=：:\n ' else c for c in s)

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

def grams(s):
    s=''.join(s.split())
    return Counter(s[i:i+n] for n in (1,2,3) for i in range(max(0,len(s)-n+1)))

def cosine(a,b):
    d=sum(v*b.get(k,0) for k,v in a.items())
    na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return d/(na*nb+1e-12)

def state(o,d,form):
    return STATE_FORMS[form].format(o=o,loc=d["場所"],status=d["状態"],owner=d["担当"])

def make_stream(seed,n,mode):
    rng=random.Random(seed); world={}; out=[]; focus=""
    for _ in range(n):
        canon=rng.choice(OBJECTS); o=ALIASES[canon] if mode=="rename" else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS})
        field=rng.choice(FIELDS); old=world[canon][field]
        new=rng.choice([v for v in VALUES[field] if v!=old])
        form=1 if mode=="alternate" else 0
        before=state(o,world[canon],form)
        forms=OMIT[field] if mode=="omitted" else HELD[field] if mode in ("held","paragraph","plan","counterfactual") else CMD[field]
        command=rng.choice(forms).format(o=o,v=new)
        if mode=="paragraph": command=" ".join(rng.choice(DIST) for _ in range(3))+"\n"+command
        if mode=="plan":
            prior=rng.choice([x for x in VALUES[field] if x not in (old,new)])
            command=f"{o}を{prior}にする案でした。{rng.choice(DIST)} 最終的には"+command
        world[canon][field]=new
        after=state(o,world[canon],form)
        future=f"次の観測でも{o}の更新結果は{new}で、補助記録は維持されます。"
        if mode=="counterfactual":
            future=f"もし更新しなければ{o}は{old}のままです。実行時は{new}です。"
        out.append(Ex(before,command,after,future,o,field,old,new,mode,focus))
        focus=o
    return out

class Model:
    def __init__(self,kind):
        self.kind=kind; self.events=[]; self.edges=[]; self.training_seconds=0.0
    def fit(self,examples):
        t=time.perf_counter(); d={}
        for ex in examples:
            l,r,old,new=diff(ex.before,ex.after)
            if not old or not new: continue
            p=ex.command.find(new)
            if p<0: continue
            ev=Event(ex.command[max(0,p-8):p],ex.command[p+len(new):p+len(new)+8],
                     ex.before[max(0,l-8):l],ex.before[len(ex.before)-r:len(ex.before)-r+8] if r else ex.before[l+len(old):l+len(old)+8],
                     shape(old),shape(new),(old,),(new,))
            k=(ev.cl,ev.cr,ev.sl,ev.sr,ev.old_shape,ev.new_shape)
            if k in d:
                x=d[k]; x.support+=1
                x.old_values=tuple(sorted(set(x.old_values+(old,))))[:8]
                x.new_values=tuple(sorted(set(x.new_values+(new,))))[:8]
            else:d[k]=ev
        self.events=sorted(d.values(),key=lambda e:e.support,reverse=True)[:64]
        for ev in self.events:
            for ex in examples:
                f,okf=self.apply(ex.before,ex.command,ev,False)
                r,okr=self.apply(ex.after,ex.command,ev,True)
                if okf and f==ex.after: ev.forward_success+=1
                elif okf: ev.forward_wrong+=1
                else: ev.forward_null+=1
                if okr and r==ex.before: ev.reverse_success+=1
                elif okr: ev.reverse_wrong+=1
                else: ev.reverse_null+=1
            fp=(ev.forward_success+1)/(ev.forward_success+ev.forward_wrong+2)
            rp=(ev.reverse_success+1)/(ev.reverse_success+ev.reverse_wrong+2)
            coverage=min(ev.forward_success+ev.forward_wrong,ev.reverse_success+ev.reverse_wrong)
            ev.symmetric_score=(fp-rp)*(1-math.exp(-coverage/3))
        if self.kind=="graph":
            for i,a in enumerate(self.events):
                if abs(a.symmetric_score)<0.05: continue
                for j,b in enumerate(self.events):
                    if i==j: continue
                    compatible=a.new_shape==b.old_shape or a.sr==b.sl
                    if compatible:
                        self.edges.append((i,j,a.symmetric_score,b.symmetric_score))
            self.edges=sorted(self.edges,key=lambda x:abs(x[2])+abs(x[3]),reverse=True)[:96]
        self.training_seconds=time.perf_counter()-t
    def extract_new(self,command,ev):
        i=command.find(ev.cl) if ev.cl else 0
        if i<0:return None
        st=i+len(ev.cl); en=command.find(ev.cr,st) if ev.cr else len(command)
        if en<st:return None
        v=command[st:en]
        return v if 0<len(v)<=14 else None
    def locate(self,text,ev):
        i=text.find(ev.sl) if ev.sl else 0
        if i<0:return None
        st=i+len(ev.sl); en=text.find(ev.sr,st) if ev.sr else len(text)
        return (st,en) if en>=st else None
    def apply(self,text,command,ev,reverse):
        loc=self.locate(text,ev)
        if not loc:return text,False
        st,en=loc; current=text[st:en]
        if reverse:
            cands=list(ev.old_values)[:8]
            valid=[v for v in cands if shape(current)==ev.new_shape and 0<len(v)<=14]
            if len(valid)!=1:return text,False
            return text[:st]+valid[0]+text[en:],True
        new=self.extract_new(command,ev)
        if new is None or shape(current)!=ev.old_shape:return text,False
        return text[:st]+new+text[en:],True
    def predict(self,ex):
        cand=[]; cg=grams(ex.command); sg=grams(ex.before)
        for i,ev in enumerate(self.events):
            pred,ok=self.apply(ex.before,ex.command,ev,False)
            if not ok:continue
            score=.45*cosine(cg,grams(ev.cl+'|'+ev.cr))+.35*cosine(sg,grams(ev.sl+'|'+ev.sr))+.2*min(1,ev.support/4)
            if self.kind in ("symmetric","graph"):
                reliability=(ev.forward_success+1)/(ev.forward_success+ev.forward_wrong+2)
                score+=.2*reliability+.2*ev.symmetric_score
            if self.kind=="graph":
                score+=.02*sum(1 for a,_,_,_ in self.edges if a==i)
            cand.append((score,pred))
        if not cand:return ex.before,0,1
        cand.sort(reverse=True)
        if len(cand)>1 and cand[0][0]-cand[1][0]<.02:return ex.before,len(cand),1
        return cand[0][1],len(cand),0

def evaluate(seed,n,mode):
    train=[]
    for k,m in enumerate(("seen","held","rename","alternate")):
        train+=make_stream(seed+31*k,n//4,m)
    test=make_stream(seed+999,max(12,n//6),mode)
    out={}
    for kind in ("surface","symmetric","graph"):
        M=Model(kind); M.fit(train); t=time.perf_counter()
        correct=wrong=null=cands=0
        for ex in test:
            p,c,z=M.predict(ex); cands+=c
            correct+=int(p==ex.after); wrong+=int(p!=ex.after and not z); null+=z
        directed=sum(abs(e.symmetric_score)>=.05 for e in M.events)
        reversible=sum(abs(e.symmetric_score)<.05 and e.forward_success and e.reverse_success for e in M.events)
        out[kind]={"accuracy":correct/len(test),"wrong_commit":wrong/len(test),"null_rate":null/len(test),
        "mean_candidates":cands/len(test),"events":len(M.events),"directed_events":directed,"reversible_events":reversible,
        "edges":len(M.edges),"forward_success":sum(e.forward_success for e in M.events),
        "forward_wrong":sum(e.forward_wrong for e in M.events),"reverse_success":sum(e.reverse_success for e in M.events),
        "reverse_wrong":sum(e.reverse_wrong for e in M.events),
        "mean_abs_direction":statistics.mean([abs(e.symmetric_score) for e in M.events]) if M.events else 0,
        "model_bytes":len(pickle.dumps(M)),"training_seconds":M.training_seconds,
        "inference_ms":(time.perf_counter()-t)*1000/len(test)}
    return out

def sequential(seed,n):
    seq=make_stream(seed+700,n,"seen"); out={}
    for kind in ("surface","symmetric","graph"):
        M=Model(kind); M.fit(seq[:n//2]); cov=cor=0
        for a,b in zip(seq[n//2:-1],seq[n//2+1:]):
            p1,c1,z1=M.predict(a)
            b2=Ex(p1,b.command,b.after,b.future,b.obj,b.field,b.old,b.new,b.mode,b.focus)
            p2,c2,z2=M.predict(b2)
            if c1 and c2 and not z1 and not z2:
                cov+=1; cor+=int(p2==b.after)
        out[kind]={"coverage":cov/max(1,len(seq[n//2:-1])),"accuracy_conditional":cor/max(1,cov)}
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="results_cycle_024.json"); a=ap.parse_args()
    raw={}
    modes=("seen","held","rename","alternate","omitted","paragraph","plan","counterfactual")
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
            for k in ("surface","symmetric","graph"):
                summary[n][m][k]={x:statistics.mean(r[m][k][x] for r in runs) for x in runs[0][m][k]}
        summary[n]["sequential"]={k:{x:statistics.mean(r["sequential"][k][x] for r in runs) for x in runs[0]["sequential"][k]} for k in ("surface","symmetric","graph")}
    payload={"hypothesis":"Symmetric-Information Event Direction from Paired Intervention Replays",
    "seeds":[1,7,19],"sizes":[48,144,288],"raw":raw,"summary":summary,
    "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    "estimated_complexity":"event extraction O(NL), paired replay O(PN), graph O(P^2), inference O(PL), P<=64",
    "hidden_labels_used_by_learner":False,"highschool_level_passed":False,
    "native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(a.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary["288"],ensure_ascii=False,indent=2))
if __name__=="__main__":main()
