from __future__ import annotations
import argparse,json,math,pickle,random,re,resource,statistics,time,unicodedata
from collections import Counter,defaultdict
from dataclasses import asdict,dataclass
from difflib import SequenceMatcher
from pathlib import Path

VAR="◆"

def norm(s):
    return re.sub(r"\s+","",unicodedata.normalize("NFKC",s)).strip()

def grams(s,n=2):
    return {s[i:i+n] for i in range(max(0,len(s)-n+1))} or ({s} if s else set())

def jac(a,b):
    return len(a&b)/max(1,len(a|b))

def cls(s):
    return "q" if s.endswith(("?","？")) else "e" if s.endswith(("!","！")) else "s"

def anti(a,b):
    if a==b or min(len(a),len(b))<5:return None
    m=SequenceMatcher(None,a,b,autojunk=False)
    blocks=[x for x in m.get_matching_blocks() if x.size>=2]
    if sum(x.size for x in blocks)<max(4,int(.42*min(len(a),len(b)))):return None
    out=[];fa=[];fb=[];pa=pb=0
    for x in blocks:
        da,db=a[pa:x.a],b[pb:x.b]
        if da or db:
            if not da or not db:return None
            out.append(VAR);fa.append(da);fb.append(db)
        out.append(a[x.a:x.a+x.size]);pa=x.a+x.size;pb=x.b+x.size
    da,db=a[pa:],b[pb:]
    if da or db:
        if not da or not db:return None
        out.append(VAR);fa.append(da);fb.append(db)
    t="".join(out)
    if not fa or len(fa)>3 or len(t.replace(VAR,""))<4:return None
    if t.startswith(VAR) and t.endswith(VAR):return None
    if any(len(x)>16 for x in fa+fb):return None
    return t,tuple(fa),tuple(fb)

def rx(t):
    return re.compile("^"+"(.+?)".join(re.escape(x) for x in t.split(VAR))+"$")

def match(t,s):
    m=rx(t).match(s);return tuple(m.groups()) if m else None

@dataclass
class Rec:
    d:int;i:int;text:str;nxt:str;nxt2:str;end:int

@dataclass
class Cand:
    t:str;ids:set;fills:list;support:int=0;div:float=0;coh:float=0;gain:float=0;score:float=0

@dataclass
class Metrics:
    method:str;seed:int;dialogues:int;templates:int;variables:int;operations:int;goals:int
    coverage:float;next_frame:float;response_jaccard:float;rename:float;shuffle_ratio:float
    operation_reuse:float;goal_accuracy:float;free_gate:float;model_bytes:int;peak_rss_kib:int
    train_seconds:float;inference_ms:float;reads:int

def load(path):
    out=[]
    for f in sorted(Path(path).glob("*.json")):
        try:o=json.loads(f.read_text(encoding="utf-8"))
        except Exception:continue
        u=[norm(x.get("text","")) for x in o.get("utterances",[])]
        u=[x for x in u if 3<=len(x)<=100 and "＊＊" not in x]
        if len(u)>=8:out.append(u)
    return out

def fixture():
    items=[
      ("映画","最近映画を見ましたか?","昨日映画を見ました。","どんな映画でしたか?","静かな映画でした。"),
      ("本","最近本を読みましたか?","昨日本を読みました。","どんな本でしたか?","歴史の本でした。"),
      ("料理","料理はよくしますか?","週末に料理をします。","何を作りますか?","カレーを作ります。"),
      ("散歩","散歩は好きですか?","朝に散歩をします。","どこを歩きますか?","公園を歩きます。")]
    return [["よろしくお願いします。",q,a,q2,a2,f"{x}の話は楽しいですね。","また話したいです。","ありがとうございました。"]
            for k in range(24) for x,q,a,q2,a2 in [items[k%4]]]

def recs(ds):
    return [Rec(d,i,u[i],u[i+1],u[i+2] if i+2<len(u) else "<END>",len(u)-1-i)
            for d,u in enumerate(ds) for i in range(len(u)-1)]

def coherence(xs):
    if len(xs)<2:return 0.
    xs=xs[:32];v=[jac(xs[i],xs[j]) for i in range(len(xs)) for j in range(i+1,len(xs))]
    return statistics.mean(v) if v else 0.

class Inducer:
    def __init__(self,future=True,cap=256):
        self.future=future;self.cap=cap;self.c={};self.rank=[];self.tr=defaultdict(Counter)
        self.responses=defaultdict(list);self.ops=Counter();self.goal={}
    def fit(self,ds,seed):
        r=recs(ds);rng=random.Random(seed);g=[grams(x.text) for x in r]
        buckets=defaultdict(list)
        for i,x in enumerate(r):buckets[(cls(x.text),min(6,len(x.text)//8))].append(i)
        raw={}
        for b in buckets.values():
            for i in b:
                pool=b if len(b)<=48 else rng.sample(b,48)
                near=sorted(((jac(g[i],g[j]),j) for j in pool if j!=i and r[j].d!=r[i].d),reverse=True)[:10]
                for sim,j in near:
                    if sim<.12:continue
                    z=anti(r[i].text,r[j].text)
                    if not z:continue
                    t,fi,fj=z;v=raw.setdefault(t,Cand(t,set(),[]));v.ids|={i,j};v.fills += [fi,fj]
        fg=[grams(x.nxt+"▹"+x.nxt2) for x in r];ok=[]
        for v in raw.values():
            ids=sorted(v.ids);v.support=len(ids);v.div=len(set(v.fills))/max(1,len(v.fills))
            v.coh=coherence([fg[i] for i in ids]);lit=len(v.t.replace(VAR,""))
            v.gain=sum(max(0,len(r[i].text)-lit-len(match(v.t,r[i].text) or ())) for i in ids)
            v.score=math.log1p(v.support)*v.div+.02*v.gain-1.5*v.t.count(VAR)-.02*len(v.t)+(2.5*v.coh if self.future else 0)
            if v.support>=3 and len(set(v.fills))>=3 and v.score>-.25:ok.append(v)
        ok.sort(key=lambda x:(x.score,x.support,len(x.t)),reverse=True)
        self.c={x.t:x for x in ok[:self.cap]};self.rank=list(self.c)
        by=defaultdict(dict)
        for x in r:
            a=self.assign(x.text)
            if a:by[x.d][x.i]=(a[0],a[1]);self.responses[a[0]].append(x.nxt)
        for turns in by.values():
            for i in sorted(turns):
                if i+1 not in turns:continue
                f1,x1=turns[i];f2,x2=turns[i+1];self.tr[f1][f2]+=1
                mp=tuple((a,b) for a,va in enumerate(x1) for b,vb in enumerate(x2) if va==vb)
                self.ops[(f1,f2,mp)]+=1
        e=defaultdict(list)
        for x in r:
            a=self.assign(x.text)
            if a:e[a[0]].append(int(x.end<=3))
        self.goal={k:statistics.mean(v) for k,v in e.items() if len(v)>=3}
    def assign(self,s):
        best=None;reads=0
        for t in self.rank:
            reads+=1;f=match(t,s)
            if f is None:continue
            key=(self.c[t].score,len(t.replace(VAR,"")))
            if best is None or key>best[0]:best=(key,t,f,reads)
        return (best[1],best[2],best[3]) if best else None
    def next(self,s):
        a=self.assign(s)
        if not a or not self.tr[a[0]]:return None,len(self.rank) if not a else a[2]
        return self.tr[a[0]].most_common(1)[0][0],a[2]
    def response(self,s):
        a=self.assign(s)
        if not a:return None,len(self.rank)
        rs=self.responses[a[0]]
        if not rs:return None,a[2]
        gs=[grams(x) for x in rs]
        score=[statistics.mean(jac(x,y) for y in gs) for x in gs]
        return rs[max(range(len(rs)),key=score.__getitem__)],a[2]
    def size(self):
        return len(pickle.dumps((self.c,{k:dict(v) for k,v in self.tr.items()},self.ops,self.goal)))

class Lexical:
    def fit(self,ds,seed):self.x=[(u[i],u[i+1]) for u in ds for i in range(len(u)-1)]
    def response(self,s):
        q=grams(s);z=max(self.x,key=lambda p:jac(q,grams(p[0])),default=None)
        return (z[1],len(self.x)) if z else (None,0)
    def size(self):return len(pickle.dumps(self.x))

def sim(a,b):return jac(grams(a),grams(b)) if a else 0.

def eval_joint(m,ds):
    rr=recs(ds);cov=nxt=ren=rent=oph=opt=gh=gt=0;rs=[];reads=[];by=defaultdict(list)
    for x in rr:by[x.d].append(x)
    for x in rr:
        a=m.assign(x.text)
        if not a:continue
        cov+=1;f,fill,rd=a;reads.append(rd);na=m.assign(x.nxt);p,_=m.next(x.text)
        nxt += int(bool(p and na and p==na[0]));pr,_=m.response(x.text);rs.append(sim(pr,x.nxt))
        y=x.text
        for i,z in enumerate(fill):y=y.replace(z,f"ヌンス{i}号")
        b=m.assign(y);rent+=1;ren+=int(bool(b and b[0]==f))
        if f in m.goal:gt+=1;gh+=int((m.goal[f]>=.5)==(x.end<=3))
    for seq in by.values():
        for a,b in zip(seq,seq[1:]):
            x,y=m.assign(a.text),m.assign(b.text)
            if x and y:
                opt+=1;mp=tuple((i,j) for i,v in enumerate(x[1]) for j,w in enumerate(y[1]) if v==w)
                oph+=int((x[0],y[0],mp) in m.ops)
    return dict(coverage=cov/max(1,len(rr)),next_frame=nxt/max(1,cov),response_jaccard=statistics.mean(rs) if rs else 0,
                rename=ren/max(1,rent),operation_reuse=oph/max(1,opt),goal_accuracy=gh/max(1,gt),
                reads=int(statistics.mean(reads)) if reads else len(m.rank))

def shuffle(ds,seed):
    rng=random.Random(seed);return [rng.sample(u,len(u)) for u in ds]

def run_one(method,tr,te,seed,scale):
    t=time.perf_counter()
    if method=="lexical":
        m=Lexical();m.fit(tr,seed);train=time.perf_counter()-t
        vals=[sim(m.response(x.text)[0],x.nxt) for x in recs(te)]
        e=dict(coverage=1.,next_frame=0.,response_jaccard=statistics.mean(vals),rename=0.,operation_reuse=0.,goal_accuracy=0.,reads=len(m.x))
        nt=nv=no=ng=0;sr=0.
    else:
        m=Inducer(method=="joint");m.fit(tr,seed);train=time.perf_counter()-t;e=eval_joint(m,te)
        nt=len(m.c);nv=sum(x.count(VAR) for x in m.c);no=sum(v>=2 for v in m.ops.values());ng=sum(v>=.65 for v in m.goal.values())
        if method=="joint":
            q=Inducer(True);q.fit(shuffle(tr,seed+991),seed);sr=len(q.c)/max(1,len(m.c))
        else:sr=1. if m.c else 0.
    sample=[x.text for x in recs(te)[:64]];t=time.perf_counter()
    for x in sample:m.response(x) if method=="lexical" else m.assign(x)
    inf=(time.perf_counter()-t)*1000/max(1,len(sample))
    return Metrics(method,seed,scale,nt,nv,no,ng,e["coverage"],e["next_frame"],e["response_jaccard"],e["rename"],sr,
                   e["operation_reuse"],e["goal_accuracy"],0.,m.size(),resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                   train,inf,e["reads"])

def experiment(ds,scales,out):
    rows=[]
    for n in scales:
        for seed in (1,7,19):
            rng=random.Random(seed*1000+n);x=rng.sample(ds,min(n,len(ds)));cut=max(2,int(.8*len(x)))
            for method in ("lexical","grammar","joint"):rows.append(run_one(method,x[:cut],x[cut:],seed,n))
    agg=defaultdict(dict)
    for method in ("lexical","grammar","joint"):
        for n in scales:
            z=[r for r in rows if r.method==method and r.dialogues==n]
            agg[method][str(n)]={k:statistics.mean(getattr(r,k) for r in z) for k in
              ("templates","variables","operations","goals","coverage","next_frame","response_jaccard","rename",
               "shuffle_ratio","operation_reuse","goal_accuracy","free_gate","train_seconds","inference_ms","reads")}
            agg[method][str(n)]["model_bytes_max"]=max(r.model_bytes for r in z)
            agg[method][str(n)]["peak_rss_kib_max"]=max(r.peak_rss_kib for r in z)
    report={"principle":"Joint Predictive Anti-Unification",
      "claim":{"completion":False,"highschool_level_passed":False,"native_japanese_communication_passed":False,
               "weak_smartphone_verified":False},"aggregate":agg,"runs":[asdict(r) for r in rows]}
    Path(out).parent.mkdir(parents=True,exist_ok=True);Path(out).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument("--corpus",type=Path);p.add_argument("--fixture",action="store_true")
    p.add_argument("--scales",nargs="+",type=int,default=[16,64,256]);p.add_argument("--output",type=Path,default=Path("artifacts/report.json"))
    a=p.parse_args();ds=fixture() if a.fixture else load(a.corpus)
    if len(ds)<max(a.scales):raise SystemExit(f"not enough dialogues: {len(ds)}")
    print(json.dumps(experiment(ds,a.scales,a.output)["aggregate"],ensure_ascii=False,indent=2))
if __name__=="__main__":main()
