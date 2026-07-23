from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse,json,pickle,random,resource,statistics,time,re

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末',
         '北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
FIELDS=['場所','状態','担当']
VALUES={'場所':['棚A','棚B','棚C','棚D'],'状態':['待機','処理中','完了','保留'],'担当':['担当一','担当二','担当三','担当四']}
S0='{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。'
S1='{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。'
Q={'場所':['{o}の場所はどこですか？','{o}はどこにありますか？'],
   '状態':['{o}の状態はどうなっていますか？','{o}はいまどういう状態ですか？'],
   '担当':['{o}の担当は誰ですか？','{o}を受け持つのは誰ですか？']}
CMD={'場所':['{o}を{v}へ移してください。','{o}の保管先を{v}へ変更します。'],
     '状態':['{o}を{v}にしてください。','{o}の進行状態を{v}へ切り替えます。'],
     '担当':['{o}を{v}の担当にしてください。','{o}の受け持ちを{v}へ変更します。']}

@dataclass
class Ep:
    before:str;command:str;after:str;future:str;query:str;answer:str;session:int;mode:str;canonical:str
@dataclass
class Proposal:
    wb0:int;wb1:int;cv0:int;cv1:int;co0:int;co1:int;qo0:int;qo1:int
    old_shape:str;new_shape:str;obj_shape:str;support:int=0;pos:int=0;neg:int=0;sessions:int=0;slow:bool=False

def shape(s):
    return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、：／=？\n ' else c for c in s)

def state(o,d,alt=False):return (S1 if alt else S0).format(o=o,loc=d['場所'],status=d['状態'],owner=d['担当'])

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

def bucket(i,n):return max(0,min(16,round(16*i/max(1,n))))
def unbucket(b,n):return max(0,min(n,round(b*n/16)))

def build(seed,n,mode,start_session=0):
    rng=random.Random(seed);world={};out=[];focus=None
    for i in range(n):
        canon=focus if mode=='omitted' and focus else rng.choice(OBJECTS)
        o=ALIASES[canon] if mode=='rename' else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS})
        f=rng.choice(FIELDS);old=world[canon][f];new=rng.choice([x for x in VALUES[f] if x!=old])
        before=state(o,world[canon],mode=='alternate');cmd=rng.choice(CMD[f]).format(o=o,v=new)
        if mode=='held':cmd={'場所':f'対象{o}は次から{new}で保管。','状態':f'対象{o}は以後{new}として運用。','担当':f'対象{o}の受持を{new}へ。'}[f]
        elif mode=='omitted':cmd={'場所':f'それを{new}へ移してください。','状態':f'その対象を{new}にしてください。','担当':f'担当は{new}へ変えてください。'}[f]
        elif mode=='paragraph':cmd='前段の説明があります。別件は変更しません。\n'+cmd+'\n補助記録は維持してください。'
        elif mode=='free':cmd={'場所':f'{o}は今後{new}に置くことにしよう。','状態':f'{o}はこれから{new}扱いで。','担当':f'{o}は{new}に任せる。'}[f]
        world[canon][f]=new;after=state(o,world[canon],mode=='alternate')
        future=f'次の観測でも{o}について更新された内容は{new}で維持されます。'
        query=rng.choice(Q[f]).format(o=o)
        if mode=='free':query={'場所':f'{o}を探すなら今どこを見ればいい？','状態':f'{o}はいまどんな具合？','担当':f'{o}を今みている人は誰？'}[f]
        out.append(Ep(before,cmd,after,future,query,new,start_session+i//6,mode,canon));focus=canon
    return out

def locate(text,sub):
    i=text.find(sub)
    return None if i<0 else (bucket(i,len(text)),bucket(i+len(sub),len(text)))

def apply(ep,p):
    a,b=unbucket(p.wb0,len(ep.before)),unbucket(p.wb1,len(ep.before))
    c,d=unbucket(p.cv0,len(ep.command)),unbucket(p.cv1,len(ep.command))
    oo0,oo1=unbucket(p.co0,len(ep.command)),unbucket(p.co1,len(ep.command))
    qo0,qo1=unbucket(p.qo0,len(ep.query)),unbucket(p.qo1,len(ep.query))
    if not (0<=a<=b<=len(ep.before) and 0<=c<=d<=len(ep.command)):return None
    old=ep.before[a:b];value=ep.command[c:d];obj=ep.command[oo0:oo1];qobj=ep.query[qo0:qo1]
    if shape(old)!=p.old_shape or shape(value)!=p.new_shape or shape(obj)!=p.obj_shape or shape(qobj)!=p.obj_shape:return None
    if not obj or obj not in ep.before:return None
    pred=ep.before[:a]+value+ep.before[b:]
    return value,pred,obj

class Memory:
    def __init__(self,mode):self.mode=mode;self.ps=[];self.audit=0;self.birth=0;self.train_s=0
    def induce(self,train):
        cnt=defaultdict(lambda:[0,set()])
        for ep in train:
            l,r,old,new=diff(ep.before,ep.after)
            if not old or not new:continue
            vl=locate(ep.command,new);ob=next((locate(ep.command,x) for x in [ep.canonical,ALIASES.get(ep.canonical,'')] if x and locate(ep.command,x)),None)
            qo=next((locate(ep.query,x) for x in [ep.canonical,ALIASES.get(ep.canonical,'')] if x and locate(ep.query,x)),None)
            if not vl or not ob or not qo:continue
            key=(bucket(l,len(ep.before)),bucket(len(ep.before)-r,len(ep.before)),*vl,*ob,*qo,shape(old),shape(new),shape(ep.command[unbucket(ob[0],len(ep.command)):unbucket(ob[1],len(ep.command))]))
            cnt[key][0]+=1;cnt[key][1].add(ep.session)
        self.ps=[Proposal(*k,support=n,sessions=len(ss)) for k,(n,ss) in sorted(cnt.items(),key=lambda z:z[1][0],reverse=True)[:96]]
    def ground(self,probe,shuffle=False):
        targets=[x.after for x in probe];answers=[x.answer for x in probe]
        if shuffle:targets=targets[1:]+targets[:1];answers=answers[1:]+answers[:1]
        for ep,target,ans in zip(probe,targets,answers):
            for p in self.ps:
                got=apply(ep,p)
                if got is None:continue
                self.audit+=1;value,pred,obj=got
                ok=pred==target and value==ans
                if ok:p.pos+=1
                else:p.neg+=1
        if self.mode in ('joint','slow'):
            new=[]
            for p in self.ps:
                if p.pos>0 and p.neg<=p.pos:
                    for ds in (-1,1):
                        q=Proposal(max(0,min(16,p.wb0+ds)),max(0,min(16,p.wb1+ds)),
                                   max(0,min(16,p.cv0+ds)),max(0,min(16,p.cv1+ds)),
                                   max(0,min(16,p.co0+ds)),max(0,min(16,p.co1+ds)),
                                   max(0,min(16,p.qo0+ds)),max(0,min(16,p.qo1+ds)),
                                   p.old_shape,p.new_shape,p.obj_shape,p.support,0,0,p.sessions,False)
                        new.append(q);self.birth+=1
                    p.slow=p.pos>=2 and p.sessions>=2 and p.neg<=p.pos
            self.ps=(self.ps+new)[:128]
    def fit(self,train,probe,shuffle=False):
        t=time.perf_counter();self.induce(train);self.ground(probe,shuffle);self.train_s=time.perf_counter()-t
    def candidates(self,ep):
        out=[]
        for p in self.ps:
            if self.mode=='slow' and not p.slow:continue
            got=apply(ep,p)
            if got:
                value,pred,obj=got
                score=3*p.pos-2*p.neg+.02*p.support+.03*p.sessions
                out.append((score,value,pred,obj,p))
        return sorted(out,key=lambda x:x[0],reverse=True)
    def rw(self,ep):
        c=self.candidates(ep)
        if not c:return None,None,None
        if len(c)>1 and c[0][0]-c[1][0]<.5:return None,None,None
        return c[0][1],c[0][2],c[0][3]

def evalm(m,test):
    t=time.perf_counter();ra=wa=closed=wr=ww=null=0
    for ep in test:
        r,w,o=m.rw(ep);ra+=r==ep.answer;wa+=w==ep.after;closed+=r==ep.answer and w==ep.after
        wr+=r is not None and r!=ep.answer;ww+=w is not None and w!=ep.after;null+=r is None
    n=len(test)
    return dict(read_accuracy=ra/n,write_accuracy=wa/n,closed_cycle=closed/n,wrong_read=wr/n,wrong_write=ww/n,null_rate=null/n,inference_ms=(time.perf_counter()-t)*1000/n)

def run(seed):
    induction=build(seed,72,'seen',0)+build(seed+11,36,'held',20)
    probe=build(seed+101,36,'seen',50)
    modes=['seen','held','rename','alternate','omitted','paragraph','free'];out={}
    for method,shuffle in [('factorized',False),('joint',False),('slow',False),('shuffle',True)]:
        m=Memory('joint' if method=='shuffle' else method);m.fit(induction,probe,shuffle)
        r={'proposals':len(m.ps),'slow_proposals':sum(p.slow for p in m.ps),'audit':m.audit,'birth':m.birth,
           'model_bytes':len(pickle.dumps(m)),'training_seconds':m.train_s}
        for mode in modes:r[mode]=evalm(m,build(seed+999,24,mode,100))
        one=build(seed+500,1,'free',200)[0];fast=Memory('joint');fast.fit(induction+[one],probe,False)
        rr,ww,_=fast.rw(one);r['one_shot']=int(rr==one.answer and ww==one.after)
        seq=build(seed+700,24,'seen',300)
        first=Memory('joint');first.fit(induction+seq[:12],probe,False)
        pre=sum(first.rw(x)[0]==x.answer for x in seq[:12])/12
        full=Memory('joint');full.fit(induction+seq,probe,False)
        post=sum(full.rw(x)[0]==x.answer for x in seq[:12])/12
        latest=sum(full.rw(x)[0]==x.answer for x in seq[12:])/12
        r.update(interference_before=pre,interference_after=post,latest_recall=latest)
        out[method]=r
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_034.json');a=ap.parse_args()
    raw={str(s):run(s) for s in (1,7,19)};summary={}
    for method in ('factorized','joint','slow','shuffle'):
        summary[method]={};scalar=[k for k,v in raw['1'][method].items() if isinstance(v,(int,float))]
        for k in scalar:summary[method][k]=statistics.mean(raw[str(s)][method][k] for s in (1,7,19))
        for mode in ('seen','held','rename','alternate','omitted','paragraph','free'):
            summary[method][mode]={k:statistics.mean(raw[str(s)][method][mode][k] for s in (1,7,19))
                                   for k in raw['1'][method][mode]}
    payload={'cycle':34,'hypothesis':'Shared-Generator Memory Cycles from Tri-View Boundary Co-Induction',
             'seeds':[1,7,19],'raw':raw,'summary':summary,
             'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             'estimated_complexity':'induction O(NL), grounding O(QP L), inference O(P L), P<=128',
             'final_test_outcome_used_for_ranking':False,'fixed_ontology_or_slots_used_by_model':False,
             'highschool_level_passed':False,'native_japanese_communication_passed':False,
             'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
