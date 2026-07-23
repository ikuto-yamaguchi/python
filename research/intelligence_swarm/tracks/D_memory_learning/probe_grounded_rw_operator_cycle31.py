from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict, Counter
import argparse, json, pickle, random, resource, statistics, time, re

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末","大型端末":"大きい端末",
         "北側の鍵":"北のキー","南側の鍵":"南のキー","試料甲":"サンプル甲","試料乙":"サンプル乙"}
FIELDS=["場所","状態","担当"]
VALUES={"場所":["棚A","棚B","棚C","棚D"],"状態":["待機","処理中","完了","保留"],"担当":["担当一","担当二","担当三","担当四"]}
S0="{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。"
S1="{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。"
Q={"場所":["{o}の場所はどこですか？","{o}はどこにありますか？"],
   "状態":["{o}の状態はどうなっていますか？","{o}はいまどういう状態ですか？"],
   "担当":["{o}の担当は誰ですか？","{o}を受け持つのは誰ですか？"]}
CMD={"場所":["{o}を{v}へ移してください。","{o}の保管先を{v}へ変更します。"],
     "状態":["{o}を{v}にしてください。","{o}の進行状態を{v}へ切り替えます。"],
     "担当":["{o}を{v}の担当にしてください。","{o}の受け持ちを{v}へ変更します。"]}

@dataclass
class Ep:
    before:str; command:str; after:str; future:str; query:str; answer:str
    session:int; mode:str; canonical:str

@dataclass
class Family:
    state_l:int; state_r:int; cmd_l:int; cmd_r:int
    old_shape:str; new_shape:str; query_sig:tuple
    support:int=0; pos:int=0; neg:int=0; slow:bool=False
    values:tuple=()

def state(o,d,alt=False):
    return (S1 if alt else S0).format(o=o,loc=d["場所"],status=d["状態"],owner=d["担当"])

def build(seed,n,mode,start_session=0):
    rng=random.Random(seed); world={}; out=[]
    focus=None
    for i in range(n):
        canon=rng.choice(OBJECTS) if mode!="omitted" or focus is None else focus
        o=ALIASES[canon] if mode=="rename" else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS})
        f=rng.choice(FIELDS); old=world[canon][f]; new=rng.choice([x for x in VALUES[f] if x!=old])
        before=state(o,world[canon],mode=="alternate")
        cmd=rng.choice(CMD[f]).format(o=o,v=new)
        if mode=="held":
            cmd={"場所":f"対象{o}は次から{new}で保管。","状態":f"対象{o}は以後{new}として運用。","担当":f"対象{o}の受持を{new}へ。"}[f]
        elif mode=="omitted":
            cmd={"場所":f"それを{new}へ移してください。","状態":f"その対象を{new}にしてください。","担当":f"担当は{new}へ変えてください。"}[f]
        elif mode=="paragraph":
            cmd="前段の説明があります。別件は変更しません。\n"+cmd+"\n補助記録は維持してください。"
        elif mode=="free":
            cmd={"場所":f"{o}は今後{new}に置くことにしよう。","状態":f"{o}はこれから{new}扱いで。","担当":f"{o}は{new}に任せる。"}[f]
        world[canon][f]=new; after=state(o,world[canon],mode=="alternate")
        future=f"次の観測でも{o}について更新された内容は{new}で維持されます。"
        query=rng.choice(Q[f]).format(o=o)
        if mode=="free":
            query={"場所":f"{o}を探すなら今どこを見ればいい？","状態":f"{o}はいまどんな具合？","担当":f"{o}を今みている人は誰？"}[f]
        out.append(Ep(before,cmd,after,future,query,new,start_session+i//6,mode,canon))
        focus=canon
    return out

def shape(s):
    return "".join("A" if c.isascii() and c.isalnum() else "J" if c not in "。、：／=？\n " else c for c in s)

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

def segs(t):
    xs=[x for x in re.split(r"[。、：／=？\n\s]+|(?:は|を|へ|に|の|で|と|が)",t) if 1<=len(x)<=14]
    out=[]
    for x in xs:
        out.append(x)
        if len(x)>3: out += [x[:3],x[-3:]]
    return list(dict.fromkeys(out))[:40]

def qsig(q):
    ss=segs(q)
    return (len(ss)//2, shape(q)[:10], tuple(sorted(len(x)//2 for x in ss[:4])))

def apply_rel(before,value,f):
    n=len(before)
    a=max(0,min(n,int(round(f.state_l*n/16))))
    b=max(a,min(n,int(round(f.state_r*n/16))))
    if shape(before[a:b])!=f.old_shape: return None
    return before[:a]+value+before[b:]

def candidate_values(ep,f):
    xs=[x for x in segs(ep.command) if shape(x)==f.new_shape and x not in ep.before]
    return xs[:8]

class Mem:
    def __init__(self,mode):
        self.mode=mode; self.fams=[]; self.updates=0; self.train_s=0
    def fit(self,train,probe,shuffle=False):
        t=time.perf_counter()
        stats=defaultdict(lambda:{"support":0,"pos":0,"neg":0,"sess":set(),"vals":Counter(),"q":Counter()})
        for ep in train:
            l,r,old,new=diff(ep.before,ep.after)
            if not old or not new: continue
            p=ep.command.find(new)
            if p<0: continue
            sl=round(16*l/max(1,len(ep.before))); sr=round(16*(len(ep.before)-r)/max(1,len(ep.before)))
            cl=round(16*p/max(1,len(ep.command))); cr=round(16*(p+len(new))/max(1,len(ep.command)))
            for dl in (-1,0,1):
                for dr in (-1,0,1):
                    a=max(0,min(16,sl+dl)); b=max(a,min(16,sr+dr))
                    key=(a,b,max(0,min(16,cl)),max(0,min(16,cr)),shape(old),shape(new))
                    st=stats[key]; st["support"]+=1; st["sess"].add(ep.session); st["vals"][new]+=1; st["q"][qsig(ep.query)]+=1
        probe_targets=[ep.after for ep in probe]
        if shuffle: probe_targets=probe_targets[1:]+probe_targets[:1]
        for ep,target in zip(probe,probe_targets):
            for key,st in stats.items():
                f=Family(*key,qsig(ep.query))
                vals=candidate_values(ep,f)
                for v in vals:
                    pred=apply_rel(ep.before,v,f)
                    if pred is None: continue
                    self.updates+=1
                    if pred==target:
                        st["pos"]+=1; st["sess"].add(ep.session+100); st["vals"][v]+=1
                    else: st["neg"]+=1
        fams=[]
        for key,st in stats.items():
            q=st["q"].most_common(1)[0][0] if st["q"] else (0,"",())
            slow=st["pos"]>=2 and len(st["sess"])>=3 and st["neg"]<=st["pos"]
            fams.append(Family(*key,q,st["support"],st["pos"],st["neg"],slow,
                               tuple(x for x,_ in st["vals"].most_common(8))))
        self.fams=sorted(fams,key=lambda f:(f.slow,f.pos-f.neg,f.support),reverse=True)[:96]
        self.train_s=time.perf_counter()-t
    def read(self,ep):
        pool=[f for f in self.fams if self.mode!="slow" or f.slow]
        cs=[]
        for f in pool:
            if self.mode=="surface" and f.pos==0: continue
            qmatch=sum(a==b for a,b in zip(qsig(ep.query),f.query_sig))/3
            for v in candidate_values(ep,f):
                pred=apply_rel(ep.before,v,f)
                if pred is None: continue
                score=qmatch+.12*(f.pos-f.neg)+.01*f.support
                cs.append((score,v,f))
        if not cs:return None
        cs.sort(key=lambda x:x[0],reverse=True)
        if len(cs)>1 and cs[0][0]-cs[1][0]<.18:return None
        return cs[0][1]
    def write(self,ep):
        pool=[f for f in self.fams if self.mode!="slow" or f.slow]
        cs=[]
        for f in pool:
            for v in candidate_values(ep,f):
                pred=apply_rel(ep.before,v,f)
                if pred is not None: cs.append((.12*(f.pos-f.neg)+.01*f.support,pred))
        if not cs:return None
        cs.sort(reverse=True)
        if len(cs)>1 and cs[0][0]-cs[1][0]<.18:return None
        return cs[0][1]

def eval_model(m,test):
    t=time.perf_counter(); ro=rw=rn=wo=ww=wn=0
    for ep in test:
        r=m.read(ep); w=m.write(ep)
        ro+=r==ep.answer; rw+=r is not None and r!=ep.answer; rn+=r is None
        wo+=w==ep.after; ww+=w is not None and w!=ep.after; wn+=w is None
    n=len(test)
    return {"read_accuracy":ro/n,"wrong_read":rw/n,"read_null":rn/n,
            "write_accuracy":wo/n,"wrong_write":ww/n,"write_null":wn/n,
            "inference_ms":(time.perf_counter()-t)*1000/n}

def run(seed):
    induction=build(seed,72,"seen",0)+build(seed+11,36,"held",20)
    probe=build(seed+101,36,"seen",50)
    modes=["seen","held","rename","alternate","omitted","paragraph","free"]
    result={}
    for method,shuffle in (("surface",False),("operator",False),("slow",False),("shuffle",True)):
        m=Mem("operator" if method=="shuffle" else method); m.fit(induction,probe,shuffle)
        r={"families":len(m.fams),"slow":sum(f.slow for f in m.fams),"updates":m.updates,
           "positive":sum(f.pos for f in m.fams),"negative":sum(f.neg for f in m.fams),
           "model_bytes":len(pickle.dumps(m)),"training_seconds":m.train_s}
        for mode in modes:r[mode]=eval_model(m,build(seed+999,24,mode,100))
        one=build(seed+500,1,"free",200)[0]
        mm=Mem("operator");mm.fit(induction+[one],probe,False)
        r["one_shot"]=int(mm.read(one)==one.answer)
        seq=build(seed+700,18,"seen",300)
        m2=Mem("operator");m2.fit(induction+seq[:9],probe,False)
        before=sum(m2.read(x)==x.answer for x in seq[:9])/9
        m2.fit(induction+seq,probe,False)
        after=sum(m2.read(x)==x.answer for x in seq[:9])/9
        latest=sum(m2.read(x)==x.answer for x in seq[9:])/9
        r["interference_before"]=before;r["interference_after"]=after;r["latest_recall"]=latest
        result[method]=r
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="results_cycle_031.json");a=ap.parse_args()
    raw={str(s):run(s) for s in (1,7,19)}
    summary={}
    for method in ("surface","operator","slow","shuffle"):
        summary[method]={}
        scalar=[k for k,v in raw["1"][method].items() if isinstance(v,(int,float))]
        for k in scalar:summary[method][k]=statistics.mean(raw[str(s)][method][k] for s in (1,7,19))
        for mode in ("seen","held","rename","alternate","omitted","paragraph","free"):
            summary[method][mode]={k:statistics.mean(raw[str(s)][method][mode][k] for s in (1,7,19))
                                   for k in raw["1"][method][mode]}
    payload={"cycle":31,
      "hypothesis":"Probe-Grounded Read-Write Operator Birth from Variable Boundary Families",
      "seeds":[1,7,19],"raw":raw,"summary":summary,
      "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "estimated_complexity":"family birth O(NL), probe grounding O(QFBV), read/write O(FBL)",
      "test_outcome_used_for_retrieval":False,"probe_partition_independent":True,
      "highschool_level_passed":False,"native_japanese_communication_passed":False,
      "weak_smartphone_verified":False,"completion":False}
    with open(a.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
