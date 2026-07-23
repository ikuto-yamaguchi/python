from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict, Counter
import argparse, json, pickle, random, resource, statistics, time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
FIELDS=['場所','状態','担当']
VALUES={'場所':['棚A','棚B','棚C','棚D'],'状態':['待機','処理中','完了','保留'],'担当':['担当一','担当二','担当三','担当四']}
S0='{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。'
S1='{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。'
Q={'場所':['{o}の場所はどこですか？','{o}はどこにありますか？'], '状態':['{o}の状態はどうなっていますか？','{o}はいまどういう状態ですか？'], '担当':['{o}の担当は誰ですか？','{o}を受け持つのは誰ですか？']}
CMD={'場所':['{o}を{v}へ移してください。','{o}の保管先を{v}へ変更します。'], '状態':['{o}を{v}にしてください。','{o}の進行状態を{v}へ切り替えます。'], '担当':['{o}を{v}の担当にしてください。','{o}の受け持ちを{v}へ変更します。']}

@dataclass
class Ep:
    before:str; command:str; after:str; future:str; query:str; answer:str; session:int; mode:str

@dataclass
class Address:
    wb0:int; wb1:int; cv0:int; cv1:int; co0:int; co1:int; qo0:int; qo1:int
    old_shape:str; new_shape:str; obj_shape:str
    support:int=0; pos:int=0; neg:int=0; sessions:int=0
    unique_closed:int=0; replacement_closed:int=0; necessity:float=0.0; slow:bool=False

def shape(s):
    return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、：／=？\n ' else c for c in s)

def state(o,d,alt=False):
    return (S1 if alt else S0).format(o=o,loc=d['場所'],status=d['状態'],owner=d['担当'])

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

def bucket(i,n): return max(0,min(20,round(20*i/max(1,n))))
def unbucket(b,n): return max(0,min(n,round(b*n/20)))

def spans(text,lo=2,hi=12):
    return [(i,j,text[i:j]) for i in range(len(text)) for j in range(i+lo,min(len(text),i+hi)+1)
            if not any(c in text[i:j] for c in '。、：／=？\n ')]

def maximal_common(a,b,c):
    sa=spans(a); vals=[]
    for i,j,s in sa:
        if s in b and s in c and not any(s in t and s!=t for _,_,t in sa if t in b and t in c):
            vals.append((i,j,s))
    return sorted(vals,key=lambda x:(-len(x[2]),x[0]))[:8]

def build(seed,n,mode,start_session=0):
    rng=random.Random(seed); world={}; out=[]; focus=None
    for i in range(n):
        canon=focus if mode=='omitted' and focus else rng.choice(OBJECTS)
        o=ALIASES[canon] if mode=='rename' else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS})
        f=rng.choice(FIELDS); old=world[canon][f]; new=rng.choice([x for x in VALUES[f] if x!=old])
        before=state(o,world[canon],mode=='alternate'); command=rng.choice(CMD[f]).format(o=o,v=new)
        if mode=='held': command={'場所':f'対象{o}は次から{new}で保管。','状態':f'対象{o}は以後{new}として運用。','担当':f'対象{o}の受持を{new}へ。'}[f]
        elif mode=='omitted': command={'場所':f'それを{new}へ移してください。','状態':f'その対象を{new}にしてください。','担当':f'担当は{new}へ変えてください。'}[f]
        elif mode=='paragraph': command='長い前置きがあります。別件の記録は変更しません。\n'+command+'\n補助情報は維持してください。'
        elif mode=='free': command={'場所':f'{o}は今後{new}に置くことにしよう。','状態':f'{o}はこれから{new}扱いで。','担当':f'{o}は{new}に任せる。'}[f]
        world[canon][f]=new; after=state(o,world[canon],mode=='alternate')
        future=f'次の観測でも{o}について更新された内容は{new}で維持されます。'
        query=rng.choice(Q[f]).format(o=o)
        if mode=='free': query={'場所':f'{o}を探すなら今どこを見ればいい？','状態':f'{o}はいまどんな具合？','担当':f'{o}を今みている人は誰？'}[f]
        out.append(Ep(before,command,after,future,query,new,start_session+i//6,mode)); focus=canon
    return out

def locate(text,sub):
    i=text.find(sub); return None if i<0 else (bucket(i,len(text)),bucket(i+len(sub),len(text)))

def induce_episode(ep):
    l,r,old,new=diff(ep.before,ep.after)
    if not old or not new: return []
    value_locs=[]
    for i,j,s in spans(ep.command,1,10):
        if s==new or (s in ep.after and s not in ep.before): value_locs.append((bucket(i,len(ep.command)),bucket(j,len(ep.command)),s))
    objs=maximal_common(ep.command,ep.before,ep.query)
    out=[]
    for cv0,cv1,v in value_locs[:6]:
        for ci,cj,obj in objs[:4]:
            q=locate(ep.query,obj)
            if not q: continue
            out.append(Address(bucket(l,len(ep.before)),bucket(len(ep.before)-r,len(ep.before)),cv0,cv1,
                               bucket(ci,len(ep.command)),bucket(cj,len(ep.command)),*q,
                               shape(old),shape(v),shape(obj)))
    return out

def apply(ep,p):
    a,b=unbucket(p.wb0,len(ep.before)),unbucket(p.wb1,len(ep.before))
    c,d=unbucket(p.cv0,len(ep.command)),unbucket(p.cv1,len(ep.command))
    e,f=unbucket(p.co0,len(ep.command)),unbucket(p.co1,len(ep.command))
    g,h=unbucket(p.qo0,len(ep.query)),unbucket(p.qo1,len(ep.query))
    if not (0<=a<=b<=len(ep.before) and 0<=c<=d<=len(ep.command)): return None
    old,value,obj,qobj=ep.before[a:b],ep.command[c:d],ep.command[e:f],ep.query[g:h]
    if not value or not obj or not qobj: return None
    if shape(old)!=p.old_shape or shape(value)!=p.new_shape or shape(obj)!=p.obj_shape or shape(qobj)!=p.obj_shape: return None
    if obj not in ep.before: return None
    return value,ep.before[:a]+value+ep.before[b:],obj

def distance(a,b):
    attrs=('wb0','wb1','cv0','cv1','co0','co1','qo0','qo1')
    return sum(abs(getattr(a,k)-getattr(b,k)) for k in attrs)+(a.old_shape!=b.old_shape)+(a.new_shape!=b.new_shape)+(a.obj_shape!=b.obj_shape)

class Memory:
    def __init__(self,mode):
        self.mode=mode; self.addresses=[]; self.audit=0; self.deletion_tests=0; self.replacement_tests=0; self.train_s=0
    def induce(self,train):
        table=defaultdict(lambda:[0,set()])
        for ep in train:
            for p in induce_episode(ep):
                key=(p.wb0,p.wb1,p.cv0,p.cv1,p.co0,p.co1,p.qo0,p.qo1,p.old_shape,p.new_shape,p.obj_shape)
                table[key][0]+=1; table[key][1].add(ep.session)
        self.addresses=[Address(*k,support=n,sessions=len(ss)) for k,(n,ss) in sorted(table.items(),key=lambda z:z[1][0],reverse=True)[:96]]
    def ground(self,probe,shuffle=False):
        targets=[x.after for x in probe]; answers=[x.answer for x in probe]
        if shuffle: targets=targets[1:]+targets[:1]; answers=answers[1:]+answers[:1]
        coverage=defaultdict(set); wrong=Counter()
        for ei,(ep,target,ans) in enumerate(zip(probe,targets,answers)):
            correct=[]
            for pi,p in enumerate(self.addresses):
                got=apply(ep,p)
                if not got: continue
                self.audit+=1; value,pred,_=got
                if pred==target and value==ans:
                    p.pos+=1; correct.append(pi); coverage[pi].add((ei,ep.session))
                else: p.neg+=1; wrong[pi]+=1
            if len(correct)==1:
                self.addresses[correct[0]].unique_closed+=1
        for pi,p in enumerate(self.addresses):
            self.deletion_tests+=1
            peers=[(distance(p,q),qi,q) for qi,q in enumerate(self.addresses) if qi!=pi]
            peer=min(peers,key=lambda x:x[0])[2] if peers else None
            replacement=0
            for ep,target,ans in zip(probe,targets,answers):
                gp=apply(ep,p)
                if gp and gp[0]==ans and gp[1]==target and peer is not None:
                    self.replacement_tests+=1
                    gr=apply(ep,peer)
                    replacement+=int(gr is not None and gr[0]==ans and gr[1]==target)
            p.replacement_closed=replacement
            p.necessity=max(0.0,p.unique_closed-replacement)-0.5*p.neg
            p.slow=(p.necessity>=2 and p.sessions>=2 and p.pos>p.neg)
    def fit(self,train,probe,shuffle=False):
        t=time.perf_counter(); self.induce(train); self.ground(probe,shuffle); self.train_s=time.perf_counter()-t
    def pool(self):
        if self.mode=='episodic': return self.addresses
        if self.mode=='support': return [p for p in self.addresses if p.pos>p.neg and p.pos>0]
        if self.mode=='necessity': return [p for p in self.addresses if p.slow]
        return self.addresses
    def rw(self,ep):
        c=[]
        for p in self.pool():
            got=apply(ep,p)
            if got:
                score=4*p.necessity+2*p.pos-2*p.neg+.03*p.support+.04*p.sessions
                c.append((score,*got,p))
        c.sort(key=lambda x:x[0],reverse=True)
        if not c or (len(c)>1 and c[0][0]-c[1][0]<.5): return None,None,None
        return c[0][1],c[0][2],c[0][3]

def evalm(m,test):
    t=time.perf_counter(); ra=wa=closed=wr=ww=null=0
    for ep in test:
        r,w,_=m.rw(ep); ra+=r==ep.answer; wa+=w==ep.after; closed+=r==ep.answer and w==ep.after
        wr+=r is not None and r!=ep.answer; ww+=w is not None and w!=ep.after; null+=r is None
    n=len(test)
    return dict(read_accuracy=ra/n,write_accuracy=wa/n,closed_cycle=closed/n,wrong_read=wr/n,wrong_write=ww/n,
                null_rate=null/n,inference_ms=(time.perf_counter()-t)*1000/n)

def run(seed):
    induction=build(seed,72,'seen',0)+build(seed+11,36,'held',20)
    probe=build(seed+101,48,'seen',50)
    modes=['seen','held','rename','alternate','omitted','paragraph','free']; out={}
    for method,shuffle in [('episodic',False),('support',False),('necessity',False),('shuffle',True)]:
        m=Memory('necessity' if method=='shuffle' else method); m.fit(induction,probe,shuffle)
        r={'addresses':len(m.addresses),'active_addresses':len(m.pool()),'slow_addresses':sum(p.slow for p in m.addresses),
           'audit':m.audit,'deletion_tests':m.deletion_tests,'replacement_tests':m.replacement_tests,
           'necessity_sum':sum(p.necessity for p in m.addresses),'unique_closed':sum(p.unique_closed for p in m.addresses),
           'model_bytes':len(pickle.dumps(m)),'training_seconds':m.train_s}
        for mode in modes: r[mode]=evalm(m,build(seed+999,24,mode,100))
        one=build(seed+500,1,'free',200)[0]
        fast=Memory('necessity'); fast.fit(induction+[one],probe,False)
        rr,ww,_=fast.rw(one); r['one_shot_closed']=int(rr==one.answer and ww==one.after)
        seq=build(seed+700,30,'seen',300)
        first=Memory('necessity'); first.fit(induction+seq[:15],probe,False)
        pre=sum(first.rw(x)[0]==x.answer for x in seq[:15])/15
        full=Memory('necessity'); full.fit(induction+seq,probe,False)
        post=sum(full.rw(x)[0]==x.answer for x in seq[:15])/15
        latest=sum(full.rw(x)[0]==x.answer for x in seq[15:])/15
        obsolete=sum(full.rw(x)[0]==x.answer for x in seq[:15] if x.answer!=seq[-1].answer)/max(1,sum(x.answer!=seq[-1].answer for x in seq[:15]))
        r.update(interference_before=pre,interference_after=post,latest_recall=latest,obsolete_recall=obsolete)
        out[method]=r
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',default='MEASUREMENTS_CYCLE_035.json'); a=ap.parse_args()
    raw={str(s):run(s) for s in (1,7,19)}; summary={}
    for method in ('episodic','support','necessity','shuffle'):
        summary[method]={}; scalar=[k for k,v in raw['1'][method].items() if isinstance(v,(int,float))]
        for k in scalar: summary[method][k]=statistics.mean(raw[str(s)][method][k] for s in (1,7,19))
        for mode in ('seen','held','rename','alternate','omitted','paragraph','free'):
            summary[method][mode]={k:statistics.mean(raw[str(s)][method][mode][k] for s in (1,7,19)) for k in raw['1'][method][mode]}
    payload={'cycle':35,'hypothesis':'Deletion-Causal Consolidation from Delayed Replay Necessity',
             'seeds':[1,7,19],'raw':raw,'summary':summary,
             'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             'estimated_complexity':'induction O(NL^2), replay grounding O(QP L), deletion-replacement audit O(QP^2 L), inference O(P L), P<=96',
             'final_test_outcome_used_for_retrieval_or_ranking':False,'fixed_ontology_or_slots_used_by_model':False,
             'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
