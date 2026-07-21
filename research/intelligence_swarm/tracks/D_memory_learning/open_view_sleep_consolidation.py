import random,re,time,pickle,resource,json,statistics,difflib
from collections import Counter,defaultdict

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
def anti_pair(a,b):
    sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
    blocks=[x for x in sm.get_matching_blocks() if x.size>=3]
    vals=[]
    for x in sorted(blocks,key=lambda z:z.size,reverse=True):
        v=a[x.a:x.a+x.size]
        if v.strip("。、！？") and all(v not in y and y not in v for y in vals): vals.append(v)
        if len(vals)==2: break
    if len(vals)<2:return None
    vals=sorted(vals,key=a.index);clean=[]
    for x in vals:
        while len(x)>3 and x[0] in "はがをにでへと": x=x[1:]
        while len(x)>3 and x[-1] in "はがをにでへと": x=x[:-1]
        clean.append(x)
    pa,pb=a,b
    for k,x in enumerate(clean):
        pa=pa.replace(x,f"{{S{k}}}",1);pb=pb.replace(x,f"{{S{k}}}",1)
    return pa,pb,tuple(clean)
def compile_pat(pat):
    s=re.escape(pat)
    for k in range(3):s=s.replace(re.escape(f"{{S{k}}}"),f"(?P<S{k}>.+?)")
    return re.compile("^"+s+"$")
def extract(pat,s):
    m=compile_pat(pat).match(norm(s))
    return tuple(m.group(f"S{k}") for k in range(3) if f"S{k}" in m.groupdict() and m.group(f"S{k}") is not None) if m else None

class SleepMemory:
    def __init__(self,min_support=2):
        self.min_support=min_support;self.views=[];self.query_links=[];self.bindings={};self.clock=0
        self.provisional=defaultdict(list);self.rejected=0
    def fit_seed_views(self,episodes):
        counts=Counter();q_examples=[]
        for s1,s2,q in episodes:
            z=anti_pair(norm(s1),norm(s2))
            if z: counts[(z[0],z[1])]+=1
            q_examples.append((norm(q),norm(s1),norm(s2)))
        self.views=[k for k,c in counts.items() if c>=self.min_support]
        votes=Counter()
        for q,s1,s2 in q_examples:
            for vi,(p1,p2) in enumerate(self.views):
                m1=extract(p1,s1);m2=extract(p2,s2)
                if not m1 or not m2 or len(m1)<2: continue
                for slot,v in enumerate(m1[:2]):
                    if v in q:votes[(q.replace(v,"{Q}",1),vi,slot)]+=1
        self.query_links=[k for k,c in votes.items() if c>=self.min_support]
    def _write_from_pattern(self,vi,pat,s):
        vals=extract(pat,s)
        if not vals or len(vals)<2:return False
        self.clock+=1
        self.bindings[(vi,0,vals[0])]=(vals[1],self.clock)
        self.bindings[(vi,1,vals[1])]=(vals[0],self.clock)
        return True
    def observe(self,s):
        s=norm(s)
        for vi,(p1,p2,*rest) in enumerate(self.views):
            for p in (p1,p2,*rest):
                if self._write_from_pattern(vi,p,s): return True
        return False
    def propose_new_view(self,unknown,known):
        unknown,known=norm(unknown),norm(known);matches=[]
        for vi,(p1,p2,*rest) in enumerate(self.views):
            for p in (p1,p2,*rest):
                vals=extract(p,known)
                if vals and len(vals)>=2: matches.append((vi,vals[:2]))
        if len(matches)!=1:self.rejected+=1;return False
        vi,vals=matches[0]
        if not all(v in unknown for v in vals):self.rejected+=1;return False
        pat=unknown
        for k,v in enumerate(vals):pat=pat.replace(v,f"{{S{k}}}",1)
        if extract(pat,unknown)!=vals:self.rejected+=1;return False
        self.provisional[(vi,pat)].append(vals);return True
    def sleep(self):
        added=0
        for (vi,pat),vals_list in list(self.provisional.items()):
            distinct=len(set(vals_list))
            if len(vals_list)>=self.min_support and distinct>=self.min_support:
                row=list(self.views[vi])
                if pat not in row:row.append(pat);self.views[vi]=tuple(row);added+=1
        self.provisional.clear();return added
    def query(self,q):
        q=norm(q);cands=[];reads=0
        for qp,vi,slot in self.query_links:
            reads+=1
            m=re.compile("^"+re.escape(qp).replace(re.escape("{Q}"),"(.+?)")+"$").match(q)
            if m:
                z=self.bindings.get((vi,slot,m.group(1)))
                if z:cands.append(z)
        return (max(cands,key=lambda x:x[1])[0],reads) if cands else (None,reads)
    def bytes(self):return len(pickle.dumps((self.views,self.query_links,self.bindings)))

class ClosedMemory(SleepMemory):
    def propose_new_view(self,unknown,known): return False
    def sleep(self): return 0

def make(seed,ntrain):
    r=random.Random(seed);E=names(r,ntrain+1000,"対象");V=names(r,ntrain+1500,"値");train=[]
    for i in range(ntrain):
        forms,qs=RELATIONS[i%3];e,v=E[i],V[i]
        train.append((forms[0].format(e=e,v=v),forms[1].format(e=e,v=v),qs[i%2].format(e=e)))
    return r,E,V,train

def evaluate(seed,ntrain,cls):
    r,E,V,tr=make(seed,ntrain);m=cls();t=time.perf_counter();m.fit_seed_views(tr);train_s=time.perf_counter()-t
    one=[]
    for j in range(60):
        i=ntrain+j;forms,qs=RELATIONS[i%3];e,v=E[i],V[i]
        m.observe(forms[0].format(e=e,v=v));p,_=m.query(qs[0].format(e=e));one.append(p==v)
    iso=[]
    for j in range(30):
        i=ntrain+100+j;forms,qs=RELATIONS[i%3];e,v=E[i],V[i]
        m.observe(forms[2].format(e=e,v=v));p,_=m.query(qs[0].format(e=e));iso.append(p==v)
    for j in range(18):
        i=ntrain+200+j;forms,qs=RELATIONS[i%3];e,v=E[i],V[i]
        m.propose_new_view(forms[2].format(e=e,v=v),forms[0].format(e=e,v=v))
    added=m.sleep();post=[]
    for j in range(60):
        i=ntrain+300+j;forms,qs=RELATIONS[i%3];e,v=E[i],V[i]
        m.observe(forms[2].format(e=e,v=v));p,_=m.query(qs[0].format(e=e));post.append(p==v)
    fourth=[]
    for j in range(30):
        i=ntrain+400+j;forms,qs=RELATIONS[i%3];e,v=E[i],V[i]
        m.observe(forms[3].format(e=e,v=v));p,_=m.query(qs[0].format(e=e));fourth.append(p==v)
    latest=[]
    for j in range(30):
        i=ntrain+500+j;forms,qs=RELATIONS[i%3];e=E[i];v1=V[i];v2=V[i+500]
        m.observe(forms[2].format(e=e,v=v1))
        for z in range(40):
            ff,_=RELATIONS[z%3];m.observe(ff[0].format(e=E[i+z+1],v=V[i+z+1]))
        m.observe(forms[2].format(e=e,v=v2));p,_=m.query(qs[0].format(e=e));latest.append(p==v2)
    rej0=m.rejected;bad=[]
    for j in range(20):
        i=ntrain+700+j;forms,_=RELATIONS[i%3];e,v=E[i],V[i]
        bad.append(not m.propose_new_view("これは全く異なる文章です。",forms[0].format(e=e,v=v)))
    rejected=(m.rejected-rej0)/len(bad);qs=[]
    for j in range(100):
        i=ntrain+800+j;forms,qf=RELATIONS[i%3];qs.append(qf[0].format(e=E[i]))
    t=time.perf_counter();reads=[]
    for q in qs:_,rd=m.query(q);reads.append(rd)
    latency=(time.perf_counter()-t)*1000/len(qs)
    return {"seed":seed,"ntrain":ntrain,"method":cls.__name__,"oneshot":statistics.mean(one),
      "isolated_unseen_before_sleep":statistics.mean(iso),"corroborated_unseen_after_sleep":statistics.mean(post),
      "novel_fourth_syntax":statistics.mean(fourth),"latest_after_interference":statistics.mean(latest),
      "bad_pair_rejection":rejected,"schemas":len(m.views),"added_views":added,"provisional_remaining":sum(map(len,m.provisional.values())),
      "bindings":len(m.bindings),"model_bytes":m.bytes(),"train_seconds":train_s,"inference_ms":latency,
      "query_reads":statistics.mean(reads),"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}

def run():
    rows=[evaluate(s,n,c) for n in (48,180,540) for s in (1,7,19) for c in (ClosedMemory,SleepMemory)];agg={}
    for n in (48,180,540):
      agg[str(n)]={}
      for name in ("ClosedMemory","SleepMemory"):
        rr=[x for x in rows if x["ntrain"]==n and x["method"]==name]
        agg[str(n)][name]={k:statistics.mean(x[k] for x in rr) for k in rr[0] if k not in ("seed","ntrain","method")}
    return {"hypothesis":"Unknown surface views can remain as fast provisional hypotheses and be consolidated into slow write/read schemas only after repeated cross-view corroboration across distinct episodes.","aggregate":agg,"runs":rows,"claim":{"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}}
if __name__=="__main__":print(json.dumps(run(),ensure_ascii=False,indent=2))
