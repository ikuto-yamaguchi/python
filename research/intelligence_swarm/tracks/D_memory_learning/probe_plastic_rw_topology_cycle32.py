from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict, Counter
import argparse, json, pickle, random, resource, statistics, time, re, math

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
class Node:
    sl:int; sr:int; cl:int; cr:int; old_shape:str; new_shape:str
    query_shape:tuple; support:int=0; pos:int=0; neg:int=0; sessions:int=0
    slow:bool=False; values:tuple=()

@dataclass
class Edge:
    src:int; dst:int; kind:str; weight:float; support:int=0

def state(o,d,alt=False):
    return (S1 if alt else S0).format(o=o,loc=d["場所"],status=d["状態"],owner=d["担当"])

def build(seed,n,mode,start_session=0):
    rng=random.Random(seed); world={}; out=[]; focus=None
    for i in range(n):
        canon=focus if mode=="omitted" and focus is not None else rng.choice(OBJECTS)
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
        world[canon][f]=new
        after=state(o,world[canon],mode=="alternate")
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
    return list(dict.fromkeys(out))[:48]

def qshape(q):
    return (shape(q)[:12], len(q)//4, tuple(sorted(len(x)//2 for x in segs(q)[:5])))

def apply_node(before,value,n):
    L=len(before); a=max(0,min(L,round(n.sl*L/16))); b=max(a,min(L,round(n.sr*L/16)))
    if shape(before[a:b])!=n.old_shape:return None
    return before[:a]+value+before[b:]

def values_for(ep,n):
    return [x for x in segs(ep.command) if shape(x)==n.new_shape and x not in ep.before][:10]

class Topology:
    def __init__(self,mode):
        self.mode=mode; self.nodes=[]; self.edges=[]; self.rewires=0; self.updates=0; self.train_s=0
    def induce(self,train):
        st=defaultdict(lambda:{"support":0,"sess":set(),"vals":Counter(),"q":Counter()})
        for ep in train:
            l,r,old,new=diff(ep.before,ep.after); p=ep.command.find(new)
            if not old or not new or p<0:continue
            sl=round(16*l/max(1,len(ep.before))); sr=round(16*(len(ep.before)-r)/max(1,len(ep.before)))
            cl=round(16*p/max(1,len(ep.command))); cr=round(16*(p+len(new))/max(1,len(ep.command)))
            for dl in (-1,0,1):
              for dr in (-1,0,1):
                a=max(0,min(16,sl+dl));b=max(a,min(16,sr+dr))
                key=(a,b,max(0,min(16,cl)),max(0,min(16,cr)),shape(old),shape(new))
                s=st[key];s["support"]+=1;s["sess"].add(ep.session);s["vals"][new]+=1;s["q"][qshape(ep.query)]+=1
        nodes=[]
        for key,s in st.items():
            qs=s["q"].most_common(1)[0][0]
            nodes.append(Node(*key,qs,s["support"],0,0,len(s["sess"]),False,
                              tuple(x for x,_ in s["vals"].most_common(8))))
        self.nodes=sorted(nodes,key=lambda n:n.support,reverse=True)[:96]
    def ground_and_rewire(self,probe,shuffle=False):
        targets=[x.after for x in probe]
        if shuffle:targets=targets[1:]+targets[:1]
        outcomes=defaultdict(list)
        for ei,(ep,target) in enumerate(zip(probe,targets)):
            for i,n in enumerate(self.nodes):
                for v in values_for(ep,n):
                    pred=apply_node(ep.before,v,n)
                    if pred is None:continue
                    self.updates+=1; ok=pred==target
                    outcomes[i].append((ei,ok,pred,v))
                    if ok:n.pos+=1
                    else:n.neg+=1
        edges=[]; sigs={}
        for i,n in enumerate(self.nodes):
            rows=outcomes.get(i,[])
            sigs[i]=tuple((ei,int(ok),shape(v)) for ei,ok,_,v in rows[:24])
        for i in range(len(self.nodes)):
            for j in range(i+1,len(self.nodes)):
                if not sigs[i] or not sigs[j]:continue
                agree=sum(a==b for a,b in zip(sigs[i],sigs[j]))/max(len(sigs[i]),len(sigs[j]))
                if agree>=.75:edges.append(Edge(i,j,"merge",agree,min(len(sigs[i]),len(sigs[j]))))
                elif agree<=.25:edges.append(Edge(i,j,"inhibit",1-agree,min(len(sigs[i]),len(sigs[j]))))
        new_nodes=[]
        for i,n in enumerate(self.nodes):
            if self.mode in ("plastic","slow") and n.pos>0:
                for ds in (-1,1):
                    m=Node(max(0,min(16,n.sl+ds)),max(0,min(16,n.sr+ds)),n.cl,n.cr,
                           n.old_shape,n.new_shape,n.query_shape,n.support,n.pos,n.neg,n.sessions,False,n.values)
                    success=False
                    for ep,target in zip(probe,targets):
                        for v in values_for(ep,m):
                            if apply_node(ep.before,v,m)==target:success=True;break
                        if success:break
                    if success:new_nodes.append(m);self.rewires+=1
            n.slow=n.pos>=2 and n.sessions>=2 and n.neg<=n.pos
        if self.mode in ("plastic","slow"):
            self.nodes=sorted(self.nodes+new_nodes,key=lambda n:(n.slow,n.pos-n.neg,n.support),reverse=True)[:96]
            self.edges=edges[:256]
        else:self.edges=[]
    def fit(self,train,probe,shuffle=False):
        t=time.perf_counter();self.induce(train);self.ground_and_rewire(probe,shuffle);self.train_s=time.perf_counter()-t
    def score(self,ep,n,i):
        qm=sum(a==b for a,b in zip(qshape(ep.query),n.query_shape))/3
        topo=0
        if self.mode in ("plastic","slow"):
            topo=sum(e.weight*(1 if e.kind=="merge" else -1) for e in self.edges if e.src==i or e.dst==i)*.02
        return qm+.15*(n.pos-n.neg)+.01*n.support+topo
    def read(self,ep):
        cs=[]
        for i,n in enumerate(self.nodes):
            if self.mode=="slow" and not n.slow:continue
            for v in values_for(ep,n):
                pred=apply_node(ep.before,v,n)
                if pred is not None:cs.append((self.score(ep,n,i),v,i))
        if not cs:return None
        cs.sort(reverse=True)
        if len(cs)>1 and cs[0][0]-cs[1][0]<.2:return None
        return cs[0][1]
    def write(self,ep):
        cs=[]
        for i,n in enumerate(self.nodes):
            if self.mode=="slow" and not n.slow:continue
            for v in values_for(ep,n):
                pred=apply_node(ep.before,v,n)
                if pred is not None:cs.append((self.score(ep,n,i),pred,i))
        if not cs:return None
        cs.sort(reverse=True)
        if len(cs)>1 and cs[0][0]-cs[1][0]<.2:return None
        return cs[0][1]

def evalm(m,test):
    t=time.perf_counter();ra=rw=rn=wa=ww=wn=0
    for ep in test:
        r=m.read(ep);w=m.write(ep)
        ra+=r==ep.answer;rw+=r is not None and r!=ep.answer;rn+=r is None
        wa+=w==ep.after;ww+=w is not None and w!=ep.after;wn+=w is None
    N=len(test)
    return dict(read_accuracy=ra/N,wrong_read=rw/N,read_null=rn/N,
                write_accuracy=wa/N,wrong_write=ww/N,write_null=wn/N,
                inference_ms=(time.perf_counter()-t)*1000/N)

def run(seed):
    induction=build(seed,72,"seen",0)+build(seed+11,36,"held",20)
    probe=build(seed+101,36,"seen",50)
    modes=["seen","held","rename","alternate","omitted","paragraph","free"]
    result={}
    for method,shuffle in (("family",False),("plastic",False),("slow",False),("shuffle",True)):
        m=Topology("plastic" if method=="shuffle" else method);m.fit(induction,probe,shuffle)
        r={"nodes":len(m.nodes),"edges":len(m.edges),"slow_nodes":sum(n.slow for n in m.nodes),
           "rewires":m.rewires,"updates":m.updates,"positive":sum(n.pos for n in m.nodes),
           "negative":sum(n.neg for n in m.nodes),"model_bytes":len(pickle.dumps(m)),
           "training_seconds":m.train_s}
        for mode in modes:r[mode]=evalm(m,build(seed+999,24,mode,100))
        one=build(seed+500,1,"free",200)[0]
        fast=Topology("plastic");fast.fit(induction+[one],probe,False)
        r["one_shot"]=int(fast.read(one)==one.answer and fast.write(one)==one.after)
        seq=build(seed+700,24,"seen",300)
        first=Topology("plastic");first.fit(induction+seq[:12],probe,False)
        pre=sum(first.read(x)==x.answer for x in seq[:12])/12
        full=Topology("plastic");full.fit(induction+seq,probe,False)
        post=sum(full.read(x)==x.answer for x in seq[:12])/12
        latest=sum(full.read(x)==x.answer for x in seq[12:])/12
        r["interference_before"]=pre;r["interference_after"]=post;r["latest_recall"]=latest
        obsolete=0;tot=0
        for a,b in zip(seq[:-1],seq[1:]):
            if a.canonical==b.canonical:
                pred=full.read(b);obsolete+=pred==a.answer;tot+=1
        r["obsolete_recall"]=obsolete/max(1,tot)
        result[method]=r
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="results_cycle_032.json");a=ap.parse_args()
    raw={str(s):run(s) for s in (1,7,19)}
    summary={}
    for method in ("family","plastic","slow","shuffle"):
        summary[method]={}
        scalar=[k for k,v in raw["1"][method].items() if isinstance(v,(int,float))]
        for k in scalar:summary[method][k]=statistics.mean(raw[str(s)][method][k] for s in (1,7,19))
        for mode in ("seen","held","rename","alternate","omitted","paragraph","free"):
            summary[method][mode]={k:statistics.mean(raw[str(s)][method][mode][k] for s in (1,7,19))
                                   for k in raw["1"][method][mode]}
    payload={"cycle":32,
      "hypothesis":"Probe-Plastic Read-Write Address Topology from Consequence-Preserving Boundary Rewiring",
      "raw":raw,"summary":summary,
      "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "estimated_complexity":"induction O(NL), probe grounding O(QFBV), topology O(F^2), read/write O(FBL)",
      "final_test_outcome_used_for_retrieval":False,
      "fixed_ontology_or_handwritten_slots_used_by_model":False,
      "highschool_level_passed":False,"native_japanese_communication_passed":False,
      "weak_smartphone_verified":False,"completion":False}
    with open(a.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
