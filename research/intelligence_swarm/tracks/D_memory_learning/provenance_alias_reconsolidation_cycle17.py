"""Track D Cycle 017: Provenance-Gated Alias Links with Reconsolidating Sparse Address Traces.

Controlled falsification experiment. Hidden canonical object/relation labels are evaluator-only.
Learner receives raw Japanese before/command/after/query strings and event order.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末","大型端末":"大きい端末",
"北側の鍵":"北のキー","南側の鍵":"南のキー","試料甲":"サンプル甲","試料乙":"サンプル乙"}
FIELDS=["場所","状態","担当"]
VALUES={"場所":["棚A","棚B","棚C","棚D"],"状態":["待機","処理中","完了","保留"],"担当":["担当一","担当二","担当三","担当四"]}
STATE=["{o}の場所は{a}、状態は{b}、担当は{c}です。","{o}：保管={a}／進捗={b}／受持={c}。"]
CMD={"場所":["{o}を{v}へ移してください。","{o}の保管先を{v}へ変更。"],
"状態":["{o}を{v}にしてください。","{o}の進捗を{v}へ更新。"],
"担当":["{o}を{v}の担当にしてください。","{o}の受持を{v}へ変更。"]}
HELD={"場所":["対象{o}、次から{v}で保管。"],"状態":["対象{o}は以後{v}扱い。"],"担当":["{o}は{v}へ引き継ぎ。"]}
QUERY={"場所":["{o}の場所は？"],"状態":["{o}の状態は？"],"担当":["{o}の担当は？"]}
DIST=["別件の資料を確認しました。","天気の話をしました。","更新とは無関係です。"]

def grams(s):
    s="".join(s.split())
    return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))
def cos(a,b):
    d=sum(v*b.get(k,0) for k,v in a.items());na=math.sqrt(sum(v*v for v in a.values()));nb=math.sqrt(sum(v*v for v in b.values()))
    return d/(na*nb+1e-12)
def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def spans(s,cap=48):
    out=[]
    for i in range(len(s)):
        for j in range(i+2,min(len(s),i+12)+1):
            x=s[i:j]
            if x.strip() and not all(c in "、。？／=：" for c in x):
                bd=int(i==0 or s[i-1] in "、。／=：")+int(j==len(s) or s[j:j+1] in "、。／=：")
                out.append((bd,len(x),x))
    out.sort(reverse=True);ans=[];seen=set()
    for _,_,x in out:
        if x not in seen:seen.add(x);ans.append(x)
        if len(ans)>=cap:break
    return ans
def ctx(s,tok,r=7):
    i=s.find(tok)
    return None if i<0 else (s[max(0,i-r):i],s[i+len(tok):i+len(tok)+r])
def mkstate(o,d,form=0):return STATE[form].format(o=o,a=d["場所"],b=d["状態"],c=d["担当"])

@dataclass
class Ep:
    before:str;cmd:str;after:str;query:str;surface:str;canonical:str;field:str;value:str;eid:int;session:int
@dataclass
class Trace:
    span:str; qg:Counter=field(default_factory=Counter); prov:set=field(default_factory=set); support:int=0
@dataclass
class Rel:
    cl:str;cr:str;sl:str;sr:str;qg:Counter=field(default_factory=Counter);support:int=0
@dataclass
class Link:
    a:int;b:int;positive:int=0;negative:int=0;prov:set=field(default_factory=set);slow:bool=False
    def score(self):return (self.positive+1)/(self.positive+self.negative+2)
@dataclass
class Addr:
    oi:int;ri:int;support:int=0;damage:int=0

class Memory:
    def __init__(self,aliases=True,reconsolidate=True):
        self.aliases=aliases;self.reconsolidate=reconsolidate
        self.ot=[];self.rt=[];self.links=[];self.addr=[];self.fast_updates=0;self.forgotten=0
    def obj_candidates(self,e):
        q=e.query
        xs=[x for x in spans(e.before) if x in e.cmd and x in q]
        return xs[:4]
    def find_obj(self,x,q,eid):
        qg=grams(q);best=None;bs=0
        for i,t in enumerate(self.ot):
            s=.65*cos(grams(x),grams(t.span))+.35*cos(qg,t.qg)
            if s>bs:bs,best=s,i
        if best is None or bs<.72:
            self.ot.append(Trace(x));return len(self.ot)-1
        return best
    def find_rel(self,e,new):
        c=ctx(e.cmd,new);l,r,_,_=diff(e.before,e.after)
        if not c:return None
        sl=e.before[:l];sr=e.before[len(e.before)-r:] if r else "";qg=grams(e.query)
        best=None;bs=0
        for i,t in enumerate(self.rt):
            s=.4*cos(grams(c[0]+c[1]),grams(t.cl+t.cr))+.4*cos(grams(sl+sr),grams(t.sl+t.sr))+.2*cos(qg,t.qg)
            if s>bs:bs,best=s,i
        if best is None or bs<.7:
            self.rt.append(Rel(c[0],c[1],sl,sr));return len(self.rt)-1
        return best
    def exec(self,state,cmd,r):
        i=cmd.find(r.cl) if r.cl else 0
        if i<0:return state,False
        st=i+len(r.cl);en=cmd.find(r.cr,st) if r.cr else len(cmd)
        if en<st:return state,False
        v=cmd[st:en]
        i=state.find(r.sl) if r.sl else 0
        if i<0:return state,False
        st2=i+len(r.sl);en2=state.find(r.sr,st2) if r.sr else len(state)
        return (state[:st2]+v+state[en2:],True) if en2>=st2 else (state,False)
    def linked(self,oi):
        z={oi}
        for l in self.links:
            if l.slow or l.score()>=.67:
                if l.a==oi:z.add(l.b)
                if l.b==oi:z.add(l.a)
        return z
    def propose_links(self,e,oi,history):
        if not self.aliases:return
        l,r,_,new=diff(e.before,e.after);sig=(e.before[:l],e.before[len(e.before)-r:] if r else "",len(new))
        for j,t in enumerate(self.ot):
            if j==oi or not t.prov or e.session in t.prov:continue
            if cos(t.qg,grams(e.query))<.58:continue
            link=next((x for x in self.links if {x.a,x.b}=={oi,j}),None)
            if link is None:self.links.append(Link(min(oi,j),max(oi,j)));link=self.links[-1]
            link.prov.add(e.session)
    def credit_links(self,e,oi,ri,history):
        for lnk in self.links:
            if oi not in (lnk.a,lnk.b):continue
            other=lnk.b if lnk.a==oi else lnk.a
            r=self.rt[ri]
            pos=0;neg=0
            for h in history[-24:]:
                if self.ot[other].span in h.before:
                    out,ok=self.exec(h.before,e.cmd,r)
                    if ok and out!=h.before:pos+=int(h.field==e.field);neg+=int(h.field!=e.field)
            lnk.positive+=pos;lnk.negative+=neg
            if self.reconsolidate and len(lnk.prov)>=2 and lnk.positive>=2 and lnk.score()>=.72:lnk.slow=True
            if self.reconsolidate and lnk.negative>=3 and lnk.score()<.45:
                lnk.slow=False
    def learn(self,e,history):
        _,_,_,new=diff(e.before,e.after)
        os=self.obj_candidates(e);ri=self.find_rel(e,new)
        if not os or ri is None:return
        r=self.rt[ri];r.qg.update(grams(e.query));r.support+=1
        for x in os:
            oi=self.find_obj(x,e.query,e.eid);o=self.ot[oi];o.qg.update(grams(e.query));o.prov.add(e.session);o.support+=1
            self.propose_links(e,oi,history)
            out,ok=self.exec(e.before,e.cmd,r)
            if ok and out==e.after:
                a=next((a for a in self.addr if a.oi==oi and a.ri==ri),None)
                if a is None:self.addr.append(Addr(oi,ri));a=self.addr[-1]
                a.support+=1;self.fast_updates+=1;self.credit_links(e,oi,ri,history)
        if self.reconsolidate and len(self.addr)>64:
            old=len(self.addr);self.addr=sorted(self.addr,key=lambda a:(a.support-a.damage),reverse=True)[:64];self.forgotten+=old-len(self.addr)
    def write(self,state,cmd):
        cand=[]
        for a in self.addr:
            r=self.rt[a.ri];out,ok=self.exec(state,cmd,r)
            if not ok:continue
            spanset=[self.ot[i].span for i in self.linked(a.oi)]
            os=max([int(x in cmd or x in state) for x in spanset] or [0])
            s=.55*os+.3*cos(grams(cmd),grams(r.cl+r.cr))+.15*(a.support/(a.support+a.damage+1))
            cand.append((s,out,a))
        if not cand:return state,False,0
        cand.sort(reverse=True,key=lambda x:x[0])
        if len(cand)>1 and cand[0][0]-cand[1][0]<.03:return state,False,len(cand)
        return cand[0][1],True,len(cand)
    def read(self,q,states):
        cand=[]
        qg=grams(q)
        for a in self.addr:
            spanset=[self.ot[i].span for i in self.linked(a.oi)]
            os=max([cos(qg,grams(x)) for x in spanset] or [0])
            rs=cos(qg,self.rt[a.ri].qg)
            cand.append((.65*os+.35*rs,a,spanset))
        if not cand:return None,0
        cand.sort(reverse=True,key=lambda x:x[0])
        if len(cand)>1 and cand[0][0]-cand[1][0]<.03:return None,len(cand)
        _,_,sp=cand[0]
        m=[s for s in states if any(x in s for x in sp)]
        return (m[-1],len(cand)) if m else (None,len(cand))

def build(seed,n,mode):
    rng=random.Random(seed);world={};eps=[]
    for i in range(n):
        can=rng.choice(OBJECTS);world.setdefault(can,{f:rng.choice(VALUES[f]) for f in FIELDS})
        session=i//12; surf=ALIASES[can] if mode in ("rename","combined") and session%2 else can
        form=1 if mode in ("alternate","combined") and session%3==2 else 0
        f=rng.choice(FIELDS);v=rng.choice([x for x in VALUES[f] if x!=world[can][f]])
        before=mkstate(surf,world[can],form)
        cmd=rng.choice(HELD[f] if mode in ("held","combined") else CMD[f]).format(o=surf,v=v)
        world[can][f]=v;after=mkstate(surf,world[can],form);q=QUERY[f][0].format(o=surf)
        if mode=="long":cmd=" ".join(rng.choice(DIST) for _ in range(4))+" "+cmd
        eps.append(Ep(before,cmd,after,q,surf,can,f,v,i,session))
    return eps,world

def evaluate(seed,n,mode):
    eps,truth=build(seed,n,mode)
    methods={"no_alias":Memory(False,False),"temporary_alias":Memory(True,False),"reconsolidated":Memory(True,True)}
    out={}
    for name,m in methods.items():
        hist=[];states=[];wc=0
        t=time.perf_counter()
        for e in eps:
            m.learn(e,hist);pred,_,_=m.write(e.before,e.cmd);wc+=int(pred==e.after);states.append(pred);hist.append(e)
        train=time.perf_counter()-t
        rc=wrong=null=tot=0;t=time.perf_counter()
        for can,d in truth.items():
            for surf in (can,ALIASES[can]):
                for f in FIELDS:
                    q=QUERY[f][0].format(o=surf);sel,_=m.read(q,states);tot+=1
                    if sel is None:null+=1
                    else:
                        rc+=int((can in sel or ALIASES[can] in sel) and d[f] in sel)
                        wrong+=int(can not in sel and ALIASES[can] not in sel)
        infer=(time.perf_counter()-t)*1000/max(1,tot)
        out[name]={"write_accuracy":wc/max(1,len(eps)),"read_accuracy":rc/max(1,tot),
        "wrong_object_rate":wrong/max(1,tot),"null_rate":null/max(1,tot),
        "object_traces":len(m.ot),"relation_traces":len(m.rt),"links":len(m.links),
        "slow_links":sum(x.slow for x in m.links),"addresses":len(m.addr),"fast_updates":m.fast_updates,
        "forgotten":m.forgotten,"model_bytes":len(pickle.dumps(m)),"training_seconds":train,"inference_ms":infer}
    return out

def one_shot(seed):
    eps,_=build(seed,1,"seen");e=eps[0];out={}
    for k,m in {"no_alias":Memory(False,False),"temporary_alias":Memory(True,False),"reconsolidated":Memory(True,True)}.items():
        m.learn(e,[]);p,_,_=m.write(e.before,e.cmd);out[k]=float(p==e.after)
    return out

def interference(seed):
    base,_=build(seed,36,"combined");target=base[0];out={}
    for k,m in {"no_alias":Memory(False,False),"temporary_alias":Memory(True,False),"reconsolidated":Memory(True,True)}.items():
        hist=[];states=[]
        for e in base:m.learn(e,hist);p,_,_=m.write(e.before,e.cmd);states.append(p);hist.append(e)
        q=QUERY[target.field][0].format(o=ALIASES[target.canonical]);sel,_=m.read(q,states)
        out[k]=float(sel is not None and (target.canonical in sel or ALIASES[target.canonical] in sel))
    return out

def summarize(raw):
    out={}
    for n,runs in raw.items():
        out[n]={}
        for mode in ("seen","held","rename","alternate","long","combined"):
            out[n][mode]={}
            for method in ("no_alias","temporary_alias","reconsolidated"):
                keys=runs[0][mode][method]
                out[n][mode][method]={k:statistics.mean(r[mode][method][k] for r in runs) for k in keys}
        out[n]["one_shot"]={m:statistics.mean(r["one_shot"][m] for r in runs) for m in ("no_alias","temporary_alias","reconsolidated")}
        out[n]["interference"]={m:statistics.mean(r["interference"][m] for r in runs) for m in ("no_alias","temporary_alias","reconsolidated")}
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="results_cycle_017.json");a=ap.parse_args()
    raw={}
    for n in (36,108,216):
        runs=[]
        for seed in (1,7,19):
            r={mode:evaluate(seed,n,mode) for mode in ("seen","held","rename","alternate","long","combined")}
            r["one_shot"]=one_shot(seed);r["interference"]=interference(seed);runs.append(r)
        raw[str(n)]=runs
    payload={"hypothesis":"Provenance-Gated Alias Links with Reconsolidating Sparse Address Traces",
    "seeds":[1,7,19],"sizes":[36,108,216],"raw":raw,"summary":summarize(raw),
    "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    "estimated_complexity":"proposal O(L^2), link credit O(AH), read/write O((A+K)G), A<=64",
    "highschool_level_passed":False,"native_japanese_communication_passed":False,
    "weak_smartphone_verified":False,"completion":False}
    with open(a.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload["summary"]["216"],ensure_ascii=False,indent=2))
if __name__=="__main__":main()
