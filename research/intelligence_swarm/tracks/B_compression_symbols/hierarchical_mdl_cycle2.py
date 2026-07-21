from __future__ import annotations
import random, time, json, pickle, resource, statistics
from collections import defaultdict, Counter
from dataclasses import dataclass

@dataclass
class Example:
    text: str
    spans: list[tuple[int,int]]
    family: str

TRAIN_FAMILIES=[("move","{a}を{b}へ移して"),("temp","{a}の温度を{b}に設定して"),("stop","もし{a}なら{b}を止めて"),("start","{a}が終わったら{b}を開始して"),("nested","{a}を{b}へ移してから{c}を開始して"),("cond","{a}が{b}なら{c}を停止して")]
PARAPHRASES={"move":["{a}を{b}まで運んで","{b}へ{a}を移動して","{a}は{b}へ移して"],"temp":["{a}の温度設定を{b}へ変更して","{a}を{b}の温度にして","温度を{b}にして、対象は{a}"],"stop":["{a}の場合は{b}を停止して","{a}ならば{b}を止めて","{b}を止めて、条件は{a}"],"start":["{a}完了後、{b}を起動して","{a}の後で{b}を始めて","{b}を開始、ただし{a}完了後"],"nested":["{a}を{b}まで運び、その後{c}を起動して","{c}を始める前に{a}を{b}へ移して","{a}は{b}へ、そのあと{c}を開始"],"cond":["{a}が{b}の場合は{c}を止めて","{c}を停止、条件は{a}が{b}","{a}が{b}ならば{c}を停止して"]}
KNOWN=["青い箱","赤い容器","試料A","装置甲","左側の部品","小型ポンプ","棚B","保管庫C","25度","停止状態","搬送機","検査工程"]
NONCE=["ミラコフ","ネグサ粒子","未知体X7","ふわる対象","ケトラ装置","ゾル棚","42度域","未知工程Q","奥側区画","休止モード","トルカ系","ペノラ値"]

def instantiate(family,fmt,vals):
    text=fmt.format(a=vals[0],b=vals[1],c=vals[2] if len(vals)>2 else "")
    spans=[];used=[]
    for v in vals:
        start=0
        while True:
            i=text.find(v,start)
            if i<0: break
            if (i,i+len(v)) not in used:
                spans.append((i,i+len(v)));used.append((i,i+len(v)));break
            start=i+1
    return Example(text,sorted(spans),family)

def make_data(seed,n_train=360,n_test=120):
    rng=random.Random(seed);train=[]
    for _ in range(n_train):
        fam,fmt=rng.choice(TRAIN_FAMILIES);k=3 if "{c}" in fmt else 2
        train.append(instantiate(fam,fmt,rng.sample(KNOWN,k)))
    nonce=[];para=[];omission=[]
    for _ in range(n_test):
        fam,fmt=rng.choice(TRAIN_FAMILIES);k=3 if "{c}" in fmt else 2;vals=rng.sample(NONCE,k)
        nonce.append(instantiate(fam,fmt,vals));para.append(instantiate(fam,rng.choice(PARAPHRASES[fam]),vals))
        if fam in ("move","temp"):
            ot="それを{b}へ移して" if fam=="move" else "それを{b}に設定して"
            e=instantiate(fam,ot,[vals[1],vals[1]]);i=e.text.index(vals[1]);e.spans=[(i,i+len(vals[1]))];omission.append(e)
        else: omission.append(para[-1])
    return train,nonce,para,omission

class AnchorResidual:
    def __init__(self,min_len=2,max_len=10,min_count=5,diversity=3): self.min_len=min_len;self.max_len=max_len;self.min_count=min_count;self.diversity=diversity
    def fit(self,texts):
        occ=defaultdict(list)
        for t in texts:
            for L in range(self.min_len,min(self.max_len,len(t))+1):
                for i in range(len(t)-L+1):
                    s=t[i:i+L];occ[s].append((t[i-1] if i else '^',t[i+L] if i+L<len(t) else '$'))
        scored={}
        for s,ctx in occ.items():
            if len(ctx)<self.min_count: continue
            ld=len({x for x,_ in ctx});rd=len({y for _,y in ctx});gain=(len(ctx)-1)*len(s)-len(s)-2
            if gain,_ in ctx});rd=len({y for _,y in ctx});gain=(len(ctx)-1)*len(s)-len(s)-2
            if gain self.anchors=dict(sorted(scored.items(),key=lambda z:(-z[1][0],-len(z[0])))[:400]);return self
    def segment(self,text):
        matches=[]
        for s,(g,_,_) in self.anchors.items():
            st=0
            while True:
                i=text.find(s,st)
                if i<0: break
                matches.append((i,i+len(s),g+.1*len(s),s));st=i+1
        byend=defaultdict(list)
        for m in matches: byend[m[1]].append(m)
        dp=[(0.0,[]) for _ in range(len(text)+1)]
        for e in range(1,len(text)+1):
            dp[e]=dp[e-1]
            for b,_,w,s in byend[e]:
                c=(dp[b][0]+w,dp[b][1]+[(b,e,s)])
                if c[0]>dp[e][0]: dp[e]=c
        anchors=sorted(dp[-1][1]);res=[];cur=0
        for b,e,_ in anchors:
            if b>cur and self._cand(text[cur:b]): res.append((cur,b))
            cur=max(cur,e)
        if cur<len(text) and self._cand(text[cur:]): res.append((cur,len(text)))
        return self._merge(res),anchors
    @staticmethod
    def _cand(s):
        z=s.strip('、。！？, ');particles=set('をへにがはのとでならもし後からそのただし')
        return len(z)>=2 and not all(c in particles for c in z)
    @staticmethod
    def _merge(xs):
        out=[]
        for x in xs:
            if out and x[0]-out[-1][1]<=1: out[-1]=(out[-1][0],x[1])
            else: out.append(x)
        return out

class HierarchicalMDL:
    def __init__(self): self.base=AnchorResidual(min_count=4,diversity=2);self.frames=[]
    def fit(self,texts):
        self.base.fit(texts);skeletons=Counter()
        for t in texts:
            residuals,anchors=self.base.segment(t);lits=[]
            for b,e,s in anchors:
                if not any(b>=rb and e<=re for rb,re in residuals): lits.append(s)
            sk=tuple(lits[:8])
            if sk: skeletons[sk]+=1
        candidates={};keys=list(skeletons)
        for sk,c in skeletons.items():
            gain=c*sum(map(len,sk))-(sum(map(len,sk))+2*len(sk))
            if gain>0: candidates[sk]=gain
        for i in range(min(120,len(keys))):
            for j in range(i+1,min(120,len(keys))):
                lcs=self._lcs(keys[i],keys[j])
                if not lcs: continue
                support=sum(c for sk,c in skeletons.items() if self._is_subseq(lcs,sk));gain=support*sum(map(len,lcs))-(sum(map(len,lcs))+3*len(lcs))
                if support>=4 and gain>0: candidates[lcs]=max(candidates.get(lcs,0),gain)
        self.frames=[k for k,_ in sorted(candidates.items(),key=lambda z:(-z[1],-len(z[0])))[:250]];return self
    @staticmethod
    def _lcs(a,b):
        dp=[[()]*(len(b)+1) for _ in range(len(a)+1)]
        for i in range(1,len(a)+1):
            for j in range(1,len(b)+1):
                if a[i-1]==b[j-1]: dp[i][j]=dp[i-1][j-1]+(a[i-1],)
                else: dp[i][j]=dp[i-1][j] if len(dp[i-1][j])>=len(dp[i][j-1]) else dp[i][j-1]
        return dp[-1][-1]
    @staticmethod
    def _is_subseq(a,b):
        it=iter(b);return all(any(x==y for y in it) for x in a)
    def segment(self,text):
        cand=[]
        for frame in self.frames:
            positions=[];cur=0;ok=True
            for lit in frame:
                i=text.find(lit,cur)
                if i<0: ok=False;break
                positions.append((i,i+len(lit),lit));cur=i+len(lit)
            if not ok: continue
            gaps=[];p=0
            for b,e,_ in positions:
                if b>p and AnchorResidual._cand(text[p:b]): gaps.append((p,b))
                p=e
            if p<len(text) and AnchorResidual._cand(text[p:]): gaps.append((p,len(text)))
            coverage=sum(e-b for b,e,_ in positions);cost=(len(text)-coverage)+2*len(gaps)+.15*len(frame)
            if gaps and len(gaps)<=4: cand.append((cost,gaps,positions,frame))
        base_gaps,base_anchors=self.base.segment(text);base_cov=sum(e-b for b,e,_ in base_anchors)
        cand.append(((len(text)-base_cov)+2*len(base_gaps)+1,base_gaps,base_anchors,('BASE',)));cand.sort(key=lambda x:x[0])
        return cand[0][1],cand[:8]

def char_f1(pred,gold):
    p={i for b,e in pred for i in range(b,e)};g={i for b,e in gold for i in range(b,e)};tp=len(p&g);pr=tp/len(p) if p else 0;re=tp/len(g) if g else 0
    return 2*pr*re/(pr+re) if pr+re else 0

def evaluate(seed,n_train=360):
    tr,nonce,para,omit=make_data(seed,n_train=n_train);t0=time.perf_counter();h=HierarchicalMDL().fit([x.text for x in tr]);train_s=time.perf_counter()-t0;base=AnchorResidual(min_count=4,diversity=2).fit([x.text for x in tr])
    def score(data,method):
        fs=[];ex=[];lat=[];cands=[]
        for x in data:
            q=time.perf_counter_ns()
            if method=='h': pred,cs=h.segment(x.text);cands.append(len(cs))
            else: pred,_=base.segment(x.text);cands.append(1)
            lat.append((time.perf_counter_ns()-q)/1e6);fs.append(char_f1(pred,x.spans));ex.append(int(sorted(pred)==sorted(x.spans)))
        return {'f1':statistics.mean(fs),'exact':statistics.mean(ex),'latency_ms':statistics.mean(lat),'candidate_count':statistics.mean(cands)}
    return {'seed':seed,'n_train':n_train,'model_bytes':len(pickle.dumps(h)),'train_seconds':train_s,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'anchor_count':len(h.base.anchors),'frame_count':len(h.frames),'nonce':score(nonce,'h'),'paraphrase':score(para,'h'),'omission':score(omit,'h'),'base_nonce':score(nonce,'b'),'base_paraphrase':score(para,'b'),'base_omission':score(omit,'b')}

if __name__=='__main__': print(json.dumps([evaluate(s,n) for n in (90,360) for s in (1,7,19)],ensure_ascii=False,indent=2))
