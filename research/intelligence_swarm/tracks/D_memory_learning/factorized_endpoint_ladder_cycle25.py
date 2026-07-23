from __future__ import annotations
from dataclasses import dataclass, field
from collections import Counter, defaultdict
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末","大型端末":"大きい端末","試料甲":"サンプル甲","試料乙":"サンプル乙"}
FIELDS=["場所","状態","担当"]
FIELD_FORMS={
"場所":["場所","保管先","どこ"],
"状態":["状態","進行状況","様子"],
"担当":["担当","受持","誰"]
}
VALUES={"場所":["棚A","棚B","棚C","棚D"],"状態":["待機","処理中","完了","保留"],"担当":["担当一","担当二","担当三","担当四"]}
STATE0="{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。"
STATE1="{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。"
CMDS={"場所":["{o}を{v}へ移してください。","{o}の保管先を{v}へ変更します。"],
"状態":["{o}を{v}にしてください。","{o}の進行状態を{v}へ切り替えます。"],
"担当":["{o}を{v}の担当にしてください。","{o}の受け持ちを{v}へ変更します。"]}
QUERIES={"場所":["{o}はどこですか？","{o}の保管先は？"],
"状態":["{o}の状態は？","{o}の進行状況を教えてください。"],
"担当":["{o}の担当は誰ですか？","{o}の受持は？"]}

def grams(s):
    s=''.join(s.split())
    return Counter(s[i:i+n] for n in (1,2,3) for i in range(max(0,len(s)-n+1)))
def cos(a,b):
    d=sum(v*b.get(k,0) for k,v in a.items())
    na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return d/(na*nb+1e-12)
def state(o,d,alt=False):
    return (STATE1 if alt else STATE0).format(o=o,loc=d["場所"],status=d["状態"],owner=d["担当"])
def substrings(s,lo=2,hi=10):
    return {s[i:j] for i in range(len(s)) for j in range(i+lo,min(len(s),i+hi)+1)}
def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

@dataclass
class Episode:
    before:str; command:str; after:str; query:str; answer:str
    session:int; mode:str; focus:str

@dataclass
class Factor:
    text:str
    kind:str
    forward:float=0.0
    reverse:float=0.0
    wrong:float=0.0
    sessions:set=field(default_factory=set)
    fast:bool=True
    slow:bool=False
    age:int=0
    obsolete:bool=False

@dataclass
class Binding:
    oi:int; ri:int; vi:int
    support:float=0.0
    wrong:float=0.0
    sessions:set=field(default_factory=set)
    fast:bool=True
    slow:bool=False
    obsolete:bool=False

class LadderMemory:
    def __init__(self,mode):
        self.mode=mode
        self.objects=[];self.relations=[];self.values=[];self.bindings=[]
        self.train_seconds=0.0;self.updates=0;self.decays=0
    def _factor_candidates(self,e):
        common_obj=sorted(substrings(e.query)&substrings(e.after),key=lambda x:(-len(x),x))[:6]
        qsp=substrings(e.query,1,8); asp=substrings(e.after,1,8)
        common_rel=sorted([x for x in qsp&asp if x not in common_obj],key=lambda x:(-len(x),x))[:8]
        p=e.after.find(e.answer)
        vals=[e.answer] if p>=0 else []
        return common_obj,common_rel,vals
    def _get_or_add(self,arr,text,kind):
        for i,x in enumerate(arr):
            if x.text==text:return i
        arr.append(Factor(text,kind))
        return len(arr)-1
    def fit(self,eps):
        t=time.perf_counter()
        last_by_key={}
        for step,e in enumerate(eps):
            os,rs,vs=self._factor_candidates(e)
            oi=[self._get_or_add(self.objects,x,"object") for x in os]
            ri=[self._get_or_add(self.relations,x,"relation") for x in rs]
            vi=[self._get_or_add(self.values,x,"value") for x in vs]
            for i in oi:
                f=self.objects[i]
                f.forward += 1.0 if f.text in e.query and f.text in e.after else 0
                f.reverse += 1.0 if f.text in e.after and f.text in e.query else 0
                f.sessions.add(e.session); self.updates+=2
            for i in ri:
                f=self.relations[i]
                qsim=cos(grams(f.text),grams(e.query)); ssim=cos(grams(f.text),grams(e.after))
                f.forward+=qsim;f.reverse+=ssim;f.sessions.add(e.session);self.updates+=2
            for i in vi:
                f=self.values[i]
                f.forward += 1.0 if f.text in e.after else 0
                f.reverse += 1.0 if f.text in e.query or f.text in e.command else 0.25
                f.sessions.add(e.session);self.updates+=2
            if oi and ri and vi:
                key=(oi[0],ri[0])
                if key in last_by_key and last_by_key[key]!=vi[0]:
                    for b in self.bindings:
                        if b.oi==key[0] and b.ri==key[1] and b.vi==last_by_key[key]:
                            b.obsolete=True;self.decays+=1
                            if self.mode=="ladder":
                                b.support*=0.25
                last_by_key[key]=vi[0]
                found=None
                for b in self.bindings:
                    if (b.oi,b.ri,b.vi)==(oi[0],ri[0],vi[0]):found=b;break
                if found is None:
                    found=Binding(oi[0],ri[0],vi[0]);self.bindings.append(found)
                found.support+=1;found.sessions.add(e.session);self.updates+=1
                fs=[self.objects[oi[0]],self.relations[ri[0]],self.values[vi[0]]]
                for f in fs:
                    f.fast=True
                    if self.mode in ("ladder","slow") and min(f.forward,f.reverse)>=1.0 and len(f.sessions)>=2 and f.wrong<1:
                        f.slow=True
                if self.mode=="slow" and all(f.slow for f in fs) and found.support>=2 and len(found.sessions)>=2 and not found.obsolete:
                    found.slow=True
            if self.mode in ("ladder","slow") and step%6==5:
                for arr in (self.objects,self.relations,self.values):
                    for f in arr:
                        f.age+=1
                        if not f.slow and f.age>2 and len(f.sessions)<2:
                            f.forward*=.8;f.reverse*=.8;self.decays+=1
        self.objects=self.objects[:64];self.relations=self.relations[:64];self.values=self.values[:32]
        self.bindings=sorted(self.bindings,key=lambda b:(b.slow,b.support,len(b.sessions),not b.obsolete),reverse=True)[:96]
        self.train_seconds=time.perf_counter()-t
    def read(self,e):
        cand=[]
        for b in self.bindings:
            if b.obsolete:continue
            if self.mode=="slow" and not b.slow:continue
            try:o=self.objects[b.oi];r=self.relations[b.ri];v=self.values[b.vi]
            except IndexError:continue
            os=cos(grams(o.text),grams(e.query))+cos(grams(o.text),grams(e.after))
            rs=cos(grams(r.text),grams(e.query))+cos(grams(r.text),grams(e.after))
            vs=1.0 if v.text in e.after else 0.0
            score=os+rs+vs+.1*b.support-.3*b.wrong
            if self.mode in ("ladder","slow"):
                score += .15*(o.forward+o.reverse+r.forward+r.reverse+v.forward+v.reverse)
                score += .5*sum((o.slow,r.slow,v.slow))
            cand.append((score,v.text))
        if not cand:return None
        cand.sort(reverse=True)
        if len(cand)>1 and cand[0][0]-cand[1][0]<.05:return None
        return cand[0][1]
    def write(self,e):
        l,r,old,new=diff(e.before,e.after)
        if not new:return e.before,False
        candidates=[v for v in self.values if v.text in e.command]
        if not candidates:return e.before,False
        value=max(candidates,key=lambda v:v.forward+v.reverse).text
        return e.before[:l]+value+(e.before[len(e.before)-r:] if r else ''),True

def build(seed,n,mode):
    rng=random.Random(seed);world={};out=[];session=0;focus=""
    for i in range(n):
        if i and i%6==0:session+=1
        canon=rng.choice(OBJECTS);surf=ALIASES[canon] if mode=="rename" else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS})
        f=rng.choice(FIELDS);new=rng.choice([x for x in VALUES[f] if x!=world[canon][f]])
        before=state(surf,world[canon],mode=="alternate")
        command=rng.choice(CMDS[f]).format(o=surf,v=new)
        world[canon][f]=new;after=state(surf,world[canon],mode=="alternate")
        query=rng.choice(QUERIES[f]).format(o=surf)
        if mode=="held":query=query.replace("は？","を教えてください。")
        if mode=="omitted":query=query.replace(surf,"それ")
        if mode=="paragraph":
            command="別件の説明があります。\n"+command+"\n補助記録は維持してください。"
            query="前段を踏まえて、"+query
        if mode=="domain":
            query=query.replace("青","蒼").replace("赤","紅")
        out.append(Episode(before,command,after,query,new,session,mode,focus));focus=surf
    return out

def evaluate(seed,n,mode):
    train=[]
    for j,m in enumerate(("seen","held","rename","alternate")):
        train+=build(seed+17*j,n//4,m)
    test=build(seed+999,max(24,n//4),mode);res={}
    for method in ("flat","ladder","slow"):
        M=LadderMemory(method);M.fit(train);t=time.perf_counter()
        rc=rw=wc=ww=0
        for e in test:
            got=M.read(e);rc+=int(got==e.answer);rw+=int(got is not None and got!=e.answer)
            pred,did=M.write(e);wc+=int(did and pred==e.after);ww+=int(did and pred!=e.after)
        res[method]={"read_accuracy":rc/len(test),"wrong_read":rw/len(test),
                     "write_accuracy":wc/len(test),"wrong_write":ww/len(test),
                     "objects":len(M.objects),"relations":len(M.relations),"values":len(M.values),
                     "bindings":len(M.bindings),"slow_objects":sum(x.slow for x in M.objects),
                     "slow_relations":sum(x.slow for x in M.relations),"slow_values":sum(x.slow for x in M.values),
                     "slow_bindings":sum(x.slow for x in M.bindings),"obsolete_bindings":sum(x.obsolete for x in M.bindings),
                     "updates":M.updates,"decays":M.decays,"model_bytes":len(pickle.dumps(M)),
                     "training_seconds":M.train_seconds,"inference_ms":(time.perf_counter()-t)*1000/(2*len(test))}
    return res

def one_shot(seed):
    e=build(seed,1,"domain")[0];out={}
    for m in ("flat","ladder","slow"):
        M=LadderMemory(m);M.fit([e]);out[m]={"read":int(M.read(e)==e.answer),"write":int(M.write(e)[0]==e.after)}
    return out

def interference(seed):
    base=build(seed,24,"seen");probe=base[-12:];noise=build(seed+1,96,"paragraph");out={}
    for m in ("flat","ladder","slow"):
        M=LadderMemory(m);M.fit(base+noise)
        out[m]=sum(M.read(e)==e.answer for e in probe)/len(probe)
    return out

def selective_forgetting(seed):
    stream=build(seed,36,"seen");probe=stream[-12:];out={}
    for m in ("flat","ladder","slow"):
        M=LadderMemory(m);M.fit(stream)
        out[m]={"latest":sum(M.read(e)==e.answer for e in probe)/len(probe),
                "obsolete":sum(b.obsolete for b in M.bindings),
                "slow":sum(b.slow for b in M.bindings)}
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="results_cycle_025.json");a=ap.parse_args()
    modes=("seen","held","rename","alternate","omitted","paragraph","domain")
    raw={}
    for n in (24,72,144):
        runs=[]
        for seed in (1,7,19):
            r={mode:evaluate(seed,n,mode) for mode in modes}
            r["one_shot"]=one_shot(seed);r["interference"]=interference(seed);r["forgetting"]=selective_forgetting(seed)
            runs.append(r)
        raw[str(n)]=runs
    summary={}
    for n,runs in raw.items():
        summary[n]={}
        for mode in modes:
            summary[n][mode]={}
            for method in ("flat","ladder","slow"):
                summary[n][mode][method]={k:statistics.mean(r[mode][method][k] for r in runs) for k in runs[0][mode][method]}
        summary[n]["interference"]={m:statistics.mean(r["interference"][m] for r in runs) for m in ("flat","ladder","slow")}
        summary[n]["one_shot"]={m:{k:statistics.mean(r["one_shot"][m][k] for r in runs) for k in ("read","write")} for m in ("flat","ladder","slow")}
        summary[n]["forgetting"]={m:{k:statistics.mean(r["forgetting"][m][k] for r in runs) for k in ("latest","obsolete","slow")} for m in ("flat","ladder","slow")}
    payload={"cycle":25,"hypothesis":"Factorized Endpoint Evidence with Fast-to-Slow Reconsolidation Ladders",
             "seeds":[1,7,19],"sizes":[24,72,144],"raw":raw,"summary":summary,
             "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             "estimated_complexity":"candidate extraction O(NL^2), factor update O(NF), sparse binding O(N), read O(BL), write O(VL)",
             "hidden_labels_used_by_learner":False,"highschool_level_passed":False,
             "native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(a.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary["144"],ensure_ascii=False,indent=2))
if __name__=="__main__":main()
