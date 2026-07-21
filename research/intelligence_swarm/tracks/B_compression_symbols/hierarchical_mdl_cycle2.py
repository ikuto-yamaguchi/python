from __future__ import annotations
import json,pickle,random,resource,statistics,time
from collections import Counter,defaultdict
from dataclasses import dataclass

@dataclass
class Example:
    text:str
    spans:list[tuple[int,int]]
    family:str

FAMILIES=[("move","{a}を{b}へ移して"),("temp","{a}の温度を{b}に設定して"),("stop","もし{a}なら{b}を止めて"),("start","{a}が終わったら{b}を開始して"),("nested","{a}を{b}へ移してから{c}を開始して"),("cond","{a}が{b}なら{c}を停止して")]
PARA={"move":["{a}を{b}まで運んで","{b}へ{a}を移動して","{a}は{b}へ移して"],"temp":["{a}の温度設定を{b}へ変更して","{a}を{b}の温度にして","温度を{b}にして、対象は{a}"],"stop":["{a}の場合は{b}を停止して","{a}ならば{b}を止めて","{b}を止めて、条件は{a}"],"start":["{a}完了後、{b}を起動して","{a}の後で{b}を始めて","{b}を開始、ただし{a}完了後"],"nested":["{a}を{b}まで運び、その後{c}を起動して","{c}を始める前に{a}を{b}へ移して","{a}は{b}へ、そのあと{c}を開始"],"cond":["{a}が{b}の場合は{c}を止めて","{c}を停止、条件は{a}が{b}","{a}が{b}ならば{c}を停止して"]}
KNOWN=["青い箱","赤い容器","試料A","装置甲","左側の部品","小型ポンプ","棚B","保管庫C","25度","停止状態","搬送機","検査工程"]
NONCE=["ミラコフ","ネグサ粒子","未知体X7","ふわる対象","ケトラ装置","ゾル棚","42度域","未知工程Q","奥側区画","休止モード","トルカ系","ペノラ値"]

def inst(fam,fmt,vals):
    text=fmt.format(a=vals[0],b=vals[1],c=vals[2] if len(vals)>2 else "");sp=[];used=set()
    for v in vals:
        start=0
        while True:
            i=text.find(v,start)
            if i<0:break
            z=(i,i+len(v))
            if z not in used:sp.append(z);used.add(z);break
            start=i+1
    return Example(text,sorted(sp),fam)

def data(seed,n=360,m=120):
    r=random.Random(seed);tr=[]
    for _ in range(n):
        fam,fmt=r.choice(FAMILIES);k=3 if "{c}" in fmt else 2;tr.append(inst(fam,fmt,r.sample(KNOWN,k)))
    no=[];pa=[];om=[]
    for _ in range(m):
        fam,fmt=r.choice(FAMILIES);k=3 if "{c}" in fmt else 2;vals=r.sample(NONCE,k)
        no.append(inst(fam,fmt,vals));pa.append(inst(fam,r.choice(PARA[fam]),vals))
        if fam in ("move","temp"):
            fmt2="それを{b}へ移して" if fam=="move" else "それを{b}に設定して";e=inst(fam,fmt2,[vals[1],vals[1]]);i=e.text.index(vals[1]);e.spans=[(i,i+len(vals[1]))];om.append(e)
        else:om.append(pa[-1])
    return tr,no,pa,om

class Anchors:
    def __init__(self):self.a={}
    def fit(self,texts):
        occ=defaultdict(list)
        for t in texts:
            for L in range(2,min(10,len(t))+1):
                for i in range(len(t)-L+1):
                    s=t[i:i+L];occ[s].append((t[i-1] if i else '^',t[i+L] if i+L<len(t) else '$'))
        scored={}
        for s,c in occ.items():
            if len(c)<4:continue
            ld=len({x for x,_ in c});rd=len({y for _,y in c});g=(len(c)-1)*len(s)-len(s)-2
            if g>0 and (ld>=2 or rd>=2):scored[s]=(g,ld+rd,len(c))
        self.a=dict(sorted(scored.items(),key=lambda x:(-x[1][0],-len(x[0])))[:400]);return self
    @staticmethod
    def candidate(s):
        z=s.strip("、。！？, ");return len(z)>=2 and not all(c in set("をへにがはのとでならもし後からそのただし") for c in z)
    def segment(self,text):
        matches=[]
        for s,(g,_,_) in self.a.items():
            p=0
            while True:
                i=text.find(s,p)
                if i<0:break
                matches.append((i,i+len(s),g+.1*len(s),s));p=i+1
        by=defaultdict(list)
        for x in matches:by[x[1]].append(x)
        dp=[(0,[]) for _ in range(len(text)+1)]
        for e in range(1,len(text)+1):
            dp[e]=dp[e-1]
            for b,_,w,s in by[e]:
                c=(dp[b][0]+w,dp[b][1]+[(b,e,s)])
                if c[0]>dp[e][0]:dp[e]=c
        an=sorted(dp[-1][1]);res=[];p=0
        for b,e,_ in an:
            if b>p and self.candidate(text[p:b]):res.append((p,b))
            p=max(p,e)
        if p<len(text) and self.candidate(text[p:]):res.append((p,len(text)))
        out=[]
        for z in res:
            if out and z[0]-out[-1][1]<=1:out[-1]=(out[-1][0],z[1])
            else:out.append(z)
        return out,an

class HierarchicalMDL:
    def __init__(self):self.base=Anchors();self.frames=[]
    @staticmethod
    def lcs(a,b):
        d=[[()]*(len(b)+1) for _ in range(len(a)+1)]
        for i in range(1,len(a)+1):
            for j in range(1,len(b)+1):d[i][j]=d[i-1][j-1]+(a[i-1],) if a[i-1]==b[j-1] else (d[i-1][j] if len(d[i-1][j])>=len(d[i][j-1]) else d[i][j-1])
        return d[-1][-1]
    @staticmethod
    def subseq(a,b):
        it=iter(b);return all(any(x==y for y in it) for x in a)
    def fit(self,texts):
        self.base.fit(texts);sk=Counter()
        for t in texts:
            gaps,an=self.base.segment(t);l=[s for b,e,s in an if not any(b>=x and e<=y for x,y in gaps)][:8]
            if l:sk[tuple(l)]+=1
        cand={};keys=list(sk)
        for k,c in sk.items():
            g=c*sum(map(len,k))-(sum(map(len,k))+2*len(k))
            if g>0:cand[k]=g
        for i in range(min(120,len(keys))):
            for j in range(i+1,min(120,len(keys))):
                q=self.lcs(keys[i],keys[j])
                if not q:continue
                sup=sum(c for k,c in sk.items() if self.subseq(q,k));g=sup*sum(map(len,q))-(sum(map(len,q))+3*len(q))
                if sup>=4 and g>0:cand[q]=max(cand.get(q,0),g)
        self.frames=[k for k,_ in sorted(cand.items(),key=lambda x:(-x[1],-len(x[0])))[:250]];return self
    def segment(self,text):
        cand=[]
        for f in self.frames:
            pos=[];p=0
            for lit in f:
                i=text.find(lit,p)
                if i<0:pos=[];break
                pos.append((i,i+len(lit),lit));p=i+len(lit)
            if not pos:continue
            gaps=[];p=0
            for b,e,_ in pos:
                if b>p and Anchors.candidate(text[p:b]):gaps.append((p,b))
                p=e
            if p<len(text) and Anchors.candidate(text[p:]):gaps.append((p,len(text)))
            cov=sum(e-b for b,e,_ in pos);cost=len(text)-cov+2*len(gaps)+.15*len(f)
            if gaps and len(gaps)<=4:cand.append((cost,gaps,pos,f))
        bg,ba=self.base.segment(text);cand.append((len(text)-sum(e-b for b,e,_ in ba)+2*len(bg)+1,bg,ba,("BASE",)));cand.sort(key=lambda x:x[0]);return cand[0][1],cand[:8]

def f1(p,g):
    a={i for b,e in p for i in range(b,e)};b={i for x,y in g for i in range(x,y)};tp=len(a&b);pr=tp/len(a) if a else 0;re=tp/len(b) if b else 0;return 2*pr*re/(pr+re) if pr+re else 0

def evaluate(seed,n):
    tr,no,pa,om=data(seed,n);t=time.perf_counter();h=HierarchicalMDL().fit([x.text for x in tr]);ts=time.perf_counter()-t;base=Anchors().fit([x.text for x in tr])
    def score(ds,m):
        fs=[];ex=[];lat=[];cs=[]
        for x in ds:
            q=time.perf_counter_ns();pred,c=h.segment(x.text) if m=="h" else (base.segment(x.text)[0],[0]);lat.append((time.perf_counter_ns()-q)/1e6);fs.append(f1(pred,x.spans));ex.append(int(sorted(pred)==x.spans));cs.append(len(c))
        return {"f1":statistics.mean(fs),"exact":statistics.mean(ex),"latency_ms":statistics.mean(lat),"candidate_count":statistics.mean(cs)}
    return {"seed":seed,"n_train":n,"model_bytes":len(pickle.dumps(h)),"train_seconds":ts,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"anchor_count":len(h.base.a),"frame_count":len(h.frames),"nonce":score(no,"h"),"paraphrase":score(pa,"h"),"omission":score(om,"h"),"base_nonce":score(no,"b"),"base_paraphrase":score(pa,"b"),"base_omission":score(om,"b")}

if __name__=="__main__":print(json.dumps([evaluate(s,n) for n in (90,360) for s in (1,7,19)],ensure_ascii=False,indent=2))
