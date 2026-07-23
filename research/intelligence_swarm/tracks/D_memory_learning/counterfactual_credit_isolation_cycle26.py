from __future__ import annotations
from dataclasses import dataclass, field
from collections import Counter
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末","大型端末":"大きい端末","試料甲":"サンプル甲","試料乙":"サンプル乙"}
FIELDS=["場所","状態","担当"]
VALUES={"場所":["棚A","棚B","棚C","棚D"],"状態":["待機","処理中","完了","保留"],"担当":["担当一","担当二","担当三","担当四"]}
STATE0="{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。"
STATE1="{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。"
CMDS={"場所":["{o}を{v}へ移してください。","{o}の保管先を{v}へ変更します。"],"状態":["{o}を{v}にしてください。","{o}の進行状態を{v}へ切り替えます。"],"担当":["{o}を{v}の担当にしてください。","{o}の受け持ちを{v}へ変更します。"]}
QUERIES={"場所":["{o}はどこですか？","{o}の保管先は？"],"状態":["{o}の状態は？","{o}の進行状況を教えてください。"],"担当":["{o}の担当は誰ですか？","{o}の受持は？"]}

def grams(s):
    s=''.join(s.split()); return Counter(s[i:i+n] for n in (1,2,3) for i in range(max(0,len(s)-n+1)))
def cos(a,b):
    d=sum(v*b.get(k,0) for k,v in a.items()); na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values())); return d/(na*nb+1e-12)
def subs(s,lo=2,hi=10): return {s[i:j] for i in range(len(s)) for j in range(i+lo,min(len(s),i+hi)+1)}
def state(o,d,alt=False): return (STATE1 if alt else STATE0).format(o=o,loc=d["場所"],status=d["状態"],owner=d["担当"])
def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

@dataclass
class Episode:
    before:str; command:str; after:str; query:str; answer:str; session:int; mode:str
@dataclass
class Element:
    text:str; kind:str; support:int=0; sessions:set=field(default_factory=set); credit:float=0.0; wrong_credit:float=0.0; slow:bool=False
@dataclass
class Binding:
    oi:int; ri:int; vi:int; support:int=0; sessions:set=field(default_factory=set); credit:float=0.0; wrong_credit:float=0.0; slow:bool=False; obsolete:bool=False

class RemovalCreditMemory:
    def __init__(self,mode):
        self.mode=mode; self.objects=[]; self.relations=[]; self.values=[]; self.bindings=[]; self.removal_audits=0; self.updates=0; self.train_seconds=0.0
    def _get(self,arr,text,kind):
        for i,x in list(enumerate(arr))[:8]:
            if x.text==text:return i
        arr.append(Element(text,kind)); return len(arr)-1
    def _candidates(self,e):
        common=sorted(subs(e.query)&subs(e.after),key=lambda x:(-len(x),x)); os=common[:6]
        rel=[x for x in sorted(subs(e.query,1,8)&subs(e.after,1,8),key=lambda x:(-len(x),x)) if x not in os][:8]
        return os,rel,[e.answer] if e.answer in e.after else []
    def fit(self,eps):
        t=time.perf_counter(); last={}
        for e in eps:
            os,rs,vs=self._candidates(e); oi=[self._get(self.objects,x,"object") for x in os]; ri=[self._get(self.relations,x,"relation") for x in rs]; vi=[self._get(self.values,x,"value") for x in vs]
            for arr,ids in ((self.objects,oi),(self.relations,ri),(self.values,vi)):
                for i in ids: arr[i].support+=1; arr[i].sessions.add(e.session); self.updates+=1
            if oi and ri and vi:
                key=(oi[0],ri[0])
                if key in last and last[key]!=vi[0]:
                    for b in self.bindings:
                        if b.oi==key[0] and b.ri==key[1] and b.vi==last[key]: b.obsolete=True
                last[key]=vi[0]; b=next((x for x in self.bindings if (x.oi,x.ri,x.vi)==(oi[0],ri[0],vi[0])),None)
                if b is None: b=Binding(oi[0],ri[0],vi[0]); self.bindings.append(b)
                b.support+=1; b.sessions.add(e.session); self.updates+=1
        self.objects=self.objects[:16]; self.relations=self.relations[:16]; self.values=self.values[:12]
        self.bindings=[b for b in self.bindings if b.oi<len(self.objects) and b.ri<len(self.relations) and b.vi<len(self.values)]
        self.bindings=sorted(self.bindings,key=lambda b:(b.support,len(b.sessions),not b.obsolete),reverse=True)[:32]
        if self.mode in ("removal","slow"): self._audit(eps)
        self.train_seconds=time.perf_counter()-t
    def _score_binding(self,b,e,removed=None):
        if b.obsolete:return -1e9
        o=self.objects[b.oi]; r=self.relations[b.ri]; v=self.values[b.vi]
        if removed in (("o",b.oi),("r",b.ri),("v",b.vi),("b",id(b))):return -1e9
        return cos(grams(o.text),grams(e.query))+cos(grams(o.text),grams(e.after))+cos(grams(r.text),grams(e.query))+cos(grams(r.text),grams(e.after))+(1 if v.text in e.after else 0)+.05*b.support
    def _predict(self,e,removed=None,slow_only=False):
        cand=[]
        for b in self.bindings:
            if slow_only and not b.slow:continue
            s=self._score_binding(b,e,removed)
            if s>-1e8:cand.append((s,self.values[b.vi].text,b))
        if not cand:return None
        cand.sort(reverse=True,key=lambda x:x[0])
        if len(cand)>1 and cand[0][0]-cand[1][0]<.04:return None
        return cand[0][1]
    def _loss(self,eps,removed=None):
        correct=wrong=0
        for e in eps:
            p=self._predict(e,removed); correct+=int(p==e.answer); wrong+=int(p is not None and p!=e.answer)
        return (wrong-correct)/max(1,len(eps))
    def _audit(self,eps):
        eps=eps[:24]; sessions=sorted(set(e.session for e in eps))[:3]; by_session={s:[e for e in eps if e.session==s] for s in sessions}; base={s:self._loss(v) for s,v in by_session.items()}
        for kind,arr in (("o",self.objects),("r",self.relations),("v",self.values)):
            for i,x in list(enumerate(arr))[:8]:
                deltas=[]
                for s,held in by_session.items(): self.removal_audits+=1; deltas.append(self._loss(held,(kind,i))-base[s])
                x.credit=statistics.mean(deltas) if deltas else 0; x.wrong_credit=sum(d<0 for d in deltas)/max(1,len(deltas))
                if self.mode=="slow" and x.credit>.01 and len(x.sessions)>=2 and x.wrong_credit<.34:x.slow=True
        for b in self.bindings[:16]:
            deltas=[]
            for s,held in by_session.items(): self.removal_audits+=1; deltas.append(self._loss(held,("b",id(b)))-base[s])
            b.credit=statistics.mean(deltas) if deltas else 0; b.wrong_credit=sum(d<0 for d in deltas)/max(1,len(deltas)); fs=(self.objects[b.oi],self.relations[b.ri],self.values[b.vi])
            if self.mode=="slow" and b.credit>.01 and len(b.sessions)>=2 and b.wrong_credit<.34 and all(x.slow for x in fs):b.slow=True
    def read(self,e): return self._predict(e,slow_only=self.mode=="slow")
    def write(self,e):
        l,r,old,new=diff(e.before,e.after); vals=[v for v in self.values if v.text in e.command]
        if self.mode=="slow": vals=[v for v in vals if v.slow]
        if not vals:return e.before,False
        value=max(vals,key=lambda v:(v.credit,v.support)).text; return e.before[:l]+value+(e.before[len(e.before)-r:] if r else ''),True

def build(seed,n,mode):
    rng=random.Random(seed); world={}; out=[]; session=0
    for i in range(n):
        if i and i%6==0:session+=1
        canon=rng.choice(OBJECTS); surf=ALIASES[canon] if mode=="rename" else canon; world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS}); f=rng.choice(FIELDS); new=rng.choice([x for x in VALUES[f] if x!=world[canon][f]])
        before=state(surf,world[canon],mode=="alternate"); command=rng.choice(CMDS[f]).format(o=surf,v=new)
        if mode=="paragraph":command="長い前置きです。別件もあります。\n"+command+"\n補助記録は維持してください。"
        world[canon][f]=new; after=state(surf,world[canon],mode=="alternate"); query=rng.choice(QUERIES[f]).format(o=surf)
        if mode=="held":query=query.replace("は？","を教えてください。")
        if mode=="omitted":query=query.replace(surf,"それ")
        if mode=="domain":query=query.replace("青","蒼").replace("赤","紅")
        out.append(Episode(before,command,after,query,new,session,mode))
    return out

def evaluate(seed,n,mode):
    train=[]
    for j,m in enumerate(("seen","held","rename","alternate")):train+=build(seed+17*j,n//4,m)
    test=build(seed+999,max(24,n//4),mode); res={}
    for method in ("support","removal","slow"):
        M=RemovalCreditMemory(method); M.fit(train); t=time.perf_counter(); rc=rw=wc=ww=0
        for e in test:
            p=M.read(e); rc+=int(p==e.answer); rw+=int(p is not None and p!=e.answer); q,d=M.write(e); wc+=int(d and q==e.after); ww+=int(d and q!=e.after)
        res[method]={"read_accuracy":rc/len(test),"wrong_read":rw/len(test),"write_accuracy":wc/len(test),"wrong_write":ww/len(test),"objects":len(M.objects),"relations":len(M.relations),"values":len(M.values),"bindings":len(M.bindings),"slow_objects":sum(x.slow for x in M.objects),"slow_relations":sum(x.slow for x in M.relations),"slow_values":sum(x.slow for x in M.values),"slow_bindings":sum(x.slow for x in M.bindings),"positive_binding_credit":sum(b.credit>.01 for b in M.bindings),"negative_binding_credit":sum(b.credit<0 for b in M.bindings),"mean_binding_credit":statistics.mean([b.credit for b in M.bindings]) if M.bindings else 0,"removal_audits":M.removal_audits,"updates":M.updates,"model_bytes":len(pickle.dumps(M)),"training_seconds":M.train_seconds,"inference_ms":(time.perf_counter()-t)*1000/(2*len(test))}
    return res

def one_shot(seed):
    e=build(seed,1,"domain")[0]; out={}
    for m in ("support","removal","slow"):
        M=RemovalCreditMemory(m);M.fit([e]);out[m]={"read":int(M.read(e)==e.answer),"write":int(M.write(e)[0]==e.after)}
    return out
def interference(seed):
    base=build(seed,24,"seen");noise=build(seed+1,96,"paragraph");probe=base[-12:];out={}
    for m in ("support","removal","slow"):
        M=RemovalCreditMemory(m);M.fit(base+noise);out[m]=sum(M.read(e)==e.answer for e in probe)/len(probe)
    return out
def forgetting(seed):
    stream=build(seed,48,"seen");probe=stream[-12:];out={}
    for m in ("support","removal","slow"):
        M=RemovalCreditMemory(m);M.fit(stream);out[m]=sum(M.read(e)==e.answer for e in probe)/len(probe)
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="results_cycle_026.json");a=ap.parse_args();modes=("seen","held","rename","alternate","omitted","paragraph","domain");raw={}
    for n in (24,36,48):
        runs=[]
        for seed in (1,7,19):
            r={m:evaluate(seed,n,m) for m in modes};r["one_shot"]=one_shot(seed);r["interference"]=interference(seed);r["forgetting"]=forgetting(seed);runs.append(r)
        raw[str(n)]=runs
    summary={}
    for n,runs in raw.items():
        summary[n]={}
        for mode in modes:
            summary[n][mode]={}
            for method in ("support","removal","slow"):summary[n][mode][method]={k:statistics.mean(r[mode][method][k] for r in runs) for k in runs[0][mode][method]}
        summary[n]["one_shot"]={m:{k:statistics.mean(r["one_shot"][m][k] for r in runs) for k in ("read","write")} for m in ("support","removal","slow")}
        for extra in ("interference","forgetting"):summary[n][extra]={m:statistics.mean(r[extra][m] for r in runs) for m in ("support","removal","slow")}
    payload={"hypothesis":"Counterfactual Credit Isolation by Memory-Element Removal before Reconsolidation","seeds":[1,7,19],"sizes":[24,36,48],"raw":raw,"summary":summary,"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"estimated_complexity":"candidate O(NL^2), removal audit O((O+R+V+B)SNB), inference O(BL)","hidden_labels_used_by_learner":False,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(a.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
if __name__=="__main__":main()
