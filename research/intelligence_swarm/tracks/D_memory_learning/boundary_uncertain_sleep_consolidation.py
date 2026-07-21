import random,re,time,pickle,resource,json,statistics
from collections import defaultdict,Counter

RELATIONS=[
 (["{e}の保管場所は{v}です。","{e}は{v}に置かれています。","{v}に保管されているのは{e}です。","保管先が{v}なのは{e}です。"],
  ["{e}はどこですか？","{e}の置き場所は？"]),
 (["{e}の担当者は{v}です。","{e}を担当する人は{v}です。","{v}が{e}を担当しています。","担当が{v}なのは{e}です。"],
  ["{e}の担当は誰ですか？","{e}を担当する人は？"]),
 (["{e}の合言葉は{v}です。","{e}では{v}を合言葉にします。","{v}が{e}の合言葉です。","合言葉として{v}を使うのは{e}です。"],
  ["{e}の合言葉を教えて。","{e}で使う合言葉は？"])
]
CHARS=list("甲乙丙丁戊己庚辛壬癸春夏秋冬東西南北天地海山川星月花鳥風雲")
def names(r,n,p): return [p+''.join(r.sample(CHARS,4))+str(i) for i in range(n)]
def norm(s): return re.sub(r"\s+","",s)

def pattern_from_values(s,e,v,expand_e=0,expand_v=0):
    s=norm(s); spans=[]
    for name,val,ex in (("E",e,expand_e),("V",v,expand_v)):
        i=s.find(val)
        if i<0:return None
        a=max(0,i-ex); b=min(len(s),i+len(val)+ex)
        spans.append([a,b,name])
    spans.sort()
    if spans[0][1]>spans[1][0]: return None
    out=[]; pos=0; order=[]
    for a,b,name in spans:
        out.append(re.escape(s[pos:a])); out.append(f"(?P<{name}>.+?)"); pos=b; order.append(name)
    out.append(re.escape(s[pos:]))
    return "^"+''.join(out)+"$", tuple(order)

def proposal_patterns(unknown,e,v):
    candidates=[]
    for ee in (0,1):
      for vv in (0,1):
        z=pattern_from_values(unknown,e,v,expand_e=ee,expand_v=vv)
        if z and z not in candidates:candidates.append(z)
    return candidates

def extract(pat,s):
    m=re.match(pat,norm(s))
    return (m.group("E"),m.group("V")) if m else None

class UncertainSleepMemory:
    def __init__(self,min_support=2,deconsolidate=True):
        self.min_support=min_support; self.deconsolidate=deconsolidate
        self.views=defaultdict(list); self.prov=defaultdict(lambda:Counter())
        self.bindings={}; self.clock=0; self.query_patterns=[]; self.revoked=0
    def seed(self,episodes):
        for rid,s1,s2,q,e,v in episodes:
            for s in (s1,s2):
                p=proposal_patterns(s,e,v)[0]
                if p not in self.views[rid]:self.views[rid].append(p)
            qp=re.escape(norm(q)).replace(re.escape(e),"(?P<E>.+?)")
            item=("^"+qp+"$",rid)
            if item not in self.query_patterns:self.query_patterns.append(item)
    def observe(self,s):
        s=norm(s)
        for rid,patterns in self.views.items():
            for pat,_ in patterns:
                z=extract(pat,s)
                if z:
                    e,v=z; self.clock+=1; self.bindings[(rid,e)]=(v,self.clock); return True
        return False
    def propose(self,rid,unknown,known):
        vals=None
        for pat,_ in self.views[rid]:
            vals=extract(pat,known)
            if vals:break
        if not vals:return 0
        e,v=vals; n=0
        for p in proposal_patterns(unknown,e,v):
            z=extract(p[0],unknown)
            if z:self.prov[(rid,p)][z]+=1; n+=1
        return n
    def sleep(self):
        added=0
        for (rid,p),ctr in list(self.prov.items()):
            if len(ctr)<self.min_support:continue
            self.views[rid].append(p); added+=1
        self.prov.clear(); return added
    def contradict(self,rid,s,expected_e,expected_v):
        if not self.deconsolidate:return 0
        keep=[]; removed=0
        for p in self.views[rid]:
            z=extract(p[0],s)
            if z and z!=(expected_e,expected_v): removed+=1
            else: keep.append(p)
        self.views[rid]=keep; self.revoked+=removed; return removed
    def query(self,q):
        q=norm(q); c=[]; reads=0
        for qp,rid in self.query_patterns:
            reads+=1;m=re.match(qp,q)
            if m:
                z=self.bindings.get((rid,m.group("E")))
                if z:c.append(z)
        return (max(c,key=lambda x:x[1])[0],reads) if c else (None,reads)
    def bytes(self):return len(pickle.dumps((dict(self.views),self.query_patterns,self.bindings)))

class SingleBoundaryMemory(UncertainSleepMemory):
    def propose(self,rid,unknown,known):
        vals=None
        for pat,_ in self.views[rid]:
            vals=extract(pat,known)
            if vals:break
        if not vals:return 0
        p=proposal_patterns(unknown,*vals)[-1]
        z=extract(p[0],unknown)
        if z:self.prov[(rid,p)][z]+=1;return 1
        return 0

def make(seed,n):
    r=random.Random(seed);E=names(r,n+1000,"対象");V=names(r,n+1500,"値");eps=[]
    for i in range(n):
        rid=i%3;f,q=RELATIONS[rid];e,v=E[i],V[i]
        eps.append((rid,f[0].format(e=e,v=v),f[1].format(e=e,v=v),q[0].format(e=e),e,v))
    return r,E,V,eps

def evaluate(seed,n,cls):
    r,E,V,eps=make(seed,n);m=cls();t=time.perf_counter();m.seed(eps);train=time.perf_counter()-t
    for j in range(30):
        i=n+j;rid=i%3;f,q=RELATIONS[rid];e,v=E[i],V[i]
        m.propose(rid,f[2].format(e=e,v=v),f[0].format(e=e,v=v))
    added=m.sleep()
    for rid in range(3):
        i=n+100+rid;f,q=RELATIONS[rid];e,v=E[i],V[i]
        m.contradict(rid,f[2].format(e=e,v=v),e,v)
    seen=[];third=[]
    for j in range(90):
        i=n+200+j;rid=i%3;f,q=RELATIONS[rid];e,v=E[i],V[i]
        m.observe(f[0].format(e=e,v=v));p,_=m.query(q[0].format(e=e));seen.append(p==v)
        i2=n+400+j;e2,v2=E[i2],V[i2];m.observe(f[2].format(e=e2,v=v2));p,_=m.query(q[0].format(e=e2));third.append(p==v2)
    wrong=[]
    for j in range(30):
        i=n+600+j;rid=i%3;f,q=RELATIONS[rid];e,v=E[i],V[i]
        before=len(m.views[rid]);m.contradict(rid,f[2].format(e=e,v=v)+"補足",e,v);after=len(m.views[rid]);wrong.append(after<=before)
    latest=[]
    for j in range(30):
        i=n+700+j;rid=i%3;f,q=RELATIONS[rid];e=E[i];v1=V[i];v2=V[i+500]
        m.observe(f[0].format(e=e,v=v1))
        for z in range(50):
            rr=(i+z+1)%3;ff,_=RELATIONS[rr];m.observe(ff[0].format(e=E[i+z+1],v=V[i+z+1]))
        m.observe(f[0].format(e=e,v=v2));p,_=m.query(q[0].format(e=e));latest.append(p==v2)
    qs=[]
    for j in range(100):
        i=n+850+j;rid=i%3;_,q=RELATIONS[rid];qs.append(q[0].format(e=E[i]))
    t=time.perf_counter();reads=[]
    for q in qs:_,rd=m.query(q);reads.append(rd)
    lat=(time.perf_counter()-t)*1000/len(qs)
    return dict(seed=seed,ntrain=n,method=cls.__name__,seen=statistics.mean(seen),consolidated_view=statistics.mean(third),latest_after_interference=statistics.mean(latest),reversible_rejection=statistics.mean(wrong),added=added,revoked=m.revoked,schemas=sum(map(len,m.views.values())),bindings=len(m.bindings),model_bytes=m.bytes(),train_seconds=train,inference_ms=lat,query_reads=statistics.mean(reads),peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

def run():
    rows=[evaluate(s,n,c) for n in (48,180,540) for s in (1,7,19) for c in (SingleBoundaryMemory,UncertainSleepMemory)]
    agg={}
    for n in (48,180,540):
      agg[str(n)]={}
      for name in ("SingleBoundaryMemory","UncertainSleepMemory"):
        rr=[x for x in rows if x['ntrain']==n and x['method']==name]
        agg[str(n)][name]={k:statistics.mean(x[k] for x in rr) for k in rr[0] if k not in ('seed','ntrain','method')}
    return {'hypothesis':'Maintain multiple boundary/binding hypotheses during sleep consolidation and revoke schemas contradicted by later cross-view evidence.','aggregate':agg,'runs':rows,'claim':{'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}}
if __name__=='__main__':print(json.dumps(run(),ensure_ascii=False,indent=2))
