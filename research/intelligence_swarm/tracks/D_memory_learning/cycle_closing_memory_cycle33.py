from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict, Counter
import argparse,json,pickle,random,resource,statistics,time,re

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
    before:str; command:str; after:str; future:str; query:str; answer:str; session:int; mode:str; canonical:str
@dataclass
class WNode:
    sl:int; sr:int; old_shape:str; new_shape:str; support:int=0; pos:int=0; neg:int=0
@dataclass
class VNode:
    shape:str; length:int; support:int=0
@dataclass
class QNode:
    sig:tuple; support:int=0
@dataclass
class Cycle:
    w:int; v:int; q:int; support:int=0; pos:int=0; neg:int=0; sessions:int=0; slow:bool=False

def state(o,d,alt=False): return (S1 if alt else S0).format(o=o,loc=d['場所'],status=d['状態'],owner=d['担当'])
def shape(s): return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、：／=？\n ' else c for c in s)
def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def segs(t):
    xs=[x for x in re.split(r'[。、：／=？\n\s]+|(?:は|を|へ|に|の|で|と|が)',t) if 1<=len(x)<=14]
    return list(dict.fromkeys(xs+[y for x in xs if len(x)>3 for y in (x[:3],x[-3:])]))[:48]
def qsig(q): return (shape(q)[:12],len(q)//4,tuple(sorted(len(x)//2 for x in segs(q)[:5])))
def build(seed,n,mode,start_session=0):
    rng=random.Random(seed);world={};out=[];focus=None
    for i in range(n):
        canon=focus if mode=='omitted' and focus else rng.choice(OBJECTS);o=ALIASES[canon] if mode=='rename' else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS});f=rng.choice(FIELDS);old=world[canon][f];new=rng.choice([x for x in VALUES[f] if x!=old])
        before=state(o,world[canon],mode=='alternate');cmd=rng.choice(CMD[f]).format(o=o,v=new)
        if mode=='held':cmd={'場所':f'対象{o}は次から{new}で保管。','状態':f'対象{o}は以後{new}として運用。','担当':f'対象{o}の受持を{new}へ。'}[f]
        elif mode=='omitted':cmd={'場所':f'それを{new}へ移してください。','状態':f'その対象を{new}にしてください。','担当':f'担当は{new}へ変えてください。'}[f]
        elif mode=='paragraph':cmd='前段の説明があります。別件は変更しません。\n'+cmd+'\n補助記録は維持してください。'
        elif mode=='free':cmd={'場所':f'{o}は今後{new}に置くことにしよう。','状態':f'{o}はこれから{new}扱いで。','担当':f'{o}は{new}に任せる。'}[f]
        world[canon][f]=new;after=state(o,world[canon],mode=='alternate');future=f'次の観測でも{o}について更新された内容は{new}で維持されます。'
        query=rng.choice(Q[f]).format(o=o)
        if mode=='free':query={'場所':f'{o}を探すなら今どこを見ればいい？','状態':f'{o}はいまどんな具合？','担当':f'{o}を今みている人は誰？'}[f]
        out.append(Ep(before,cmd,after,future,query,new,start_session+i//6,mode,canon));focus=canon
    return out

def apply(before,value,w):
    L=len(before);a=max(0,min(L,round(w.sl*L/16)));b=max(a,min(L,round(w.sr*L/16)))
    if shape(before[a:b])!=w.old_shape:return None
    return before[:a]+value+before[b:]
def vals(ep,v): return [x for x in segs(ep.command) if shape(x)==v.shape and len(x)==v.length and x not in ep.before][:8]

class Memory:
    def __init__(self,mode):self.mode=mode;self.ws=[];self.vs=[];self.qs=[];self.cycles=[];self.audit=0;self.birth=0;self.train_s=0
    def induce(self,train):
        wc=Counter();vc=Counter();qc=Counter();links=[]
        for ep in train:
            l,r,old,new=diff(ep.before,ep.after);p=ep.command.find(new)
            if not old or not new or p<0:continue
            sl=round(16*l/max(1,len(ep.before)));sr=round(16*(len(ep.before)-r)/max(1,len(ep.before)))
            wk=(sl,sr,shape(old),shape(new));vk=(shape(new),len(new));qk=qsig(ep.query)
            wc[wk]+=1;vc[vk]+=1;qc[qk]+=1;links.append((wk,vk,qk,ep.session))
        self.ws=[WNode(*k,support=n) for k,n in wc.most_common(64)];self.vs=[VNode(*k,support=n) for k,n in vc.most_common(32)];self.qs=[QNode(k,support=n) for k,n in qc.most_common(32)]
        wi={ (x.sl,x.sr,x.old_shape,x.new_shape):i for i,x in enumerate(self.ws)};vi={(x.shape,x.length):i for i,x in enumerate(self.vs)};qi={x.sig:i for i,x in enumerate(self.qs)}
        cc=defaultdict(lambda:[0,set()])
        for w,v,q,s in links:
            if w in wi and v in vi and q in qi:cc[(wi[w],vi[v],qi[q])][0]+=1;cc[(wi[w],vi[v],qi[q])][1].add(s)
        self.cycles=[Cycle(*k,support=n,pos=0,sessions=len(ss)) for k,(n,ss) in cc.items() if n>=2][:128]
    def ground(self,probe,shuffle=False):
        targets=[x.after for x in probe];answers=[x.answer for x in probe]
        if shuffle:targets=targets[1:]+targets[:1];answers=answers[1:]+answers[:1]
        for ep,target,ans in zip(probe,targets,answers):
            for c in self.cycles:
                w,v,q=self.ws[c.w],self.vs[c.v],self.qs[c.q]
                if qsig(ep.query)!=q.sig:continue
                for value in vals(ep,v):
                    pred=apply(ep.before,value,w)
                    if pred is None:continue
                    self.audit+=1
                    write_ok=pred==target;read_ok=value==ans
                    if write_ok and read_ok:c.pos+=1
                    else:c.neg+=1
        # joint residual transport: only cycles with one-sided success generate nearby write nodes
        if self.mode in ('cycle','slow'):
            new=[]
            for c in list(self.cycles):
                if c.pos>0 and c.neg<=c.pos:
                    w=self.ws[c.w]
                    for ds in (-1,1):
                        nw=WNode(max(0,min(16,w.sl+ds)),max(0,min(16,w.sr+ds)),w.old_shape,w.new_shape,w.support)
                        idx=len(self.ws)+len(new);new.append(nw);self.cycles.append(Cycle(idx,c.v,c.q,support=c.support,pos=0,neg=0,sessions=c.sessions));self.birth+=1
                    c.slow=c.pos>=2 and c.sessions>=2 and c.neg<=c.pos
            self.ws=(self.ws+new)[:96];self.cycles=self.cycles[:192]
    def fit(self,train,probe,shuffle=False):
        t=time.perf_counter();self.induce(train);self.ground(probe,shuffle);self.train_s=time.perf_counter()-t
    def candidates(self,ep):
        out=[]
        for c in self.cycles:
            if self.mode=='slow' and not c.slow:continue
            q=self.qs[c.q]
            if qsig(ep.query)!=q.sig:continue
            w,v=self.ws[c.w],self.vs[c.v]
            for value in vals(ep,v):
                pred=apply(ep.before,value,w)
                if pred is not None:
                    score=2*c.pos-2*c.neg+.02*c.support+.02*w.support+.01*v.support
                    out.append((score,value,pred,c))
        return sorted(out,reverse=True,key=lambda x:x[0])
    def read_write(self,ep):
        cs=self.candidates(ep)
        if not cs:return None,None
        if len(cs)>1 and cs[0][0]-cs[1][0]<.5:return None,None
        return cs[0][1],cs[0][2]

def evalm(m,test):
    t=time.perf_counter();ra=wa=rw=ww=rn=wn=closed=0
    for ep in test:
        r,w=m.read_write(ep);ra+=r==ep.answer;wa+=w==ep.after;rw+=r is not None and r!=ep.answer;ww+=w is not None and w!=ep.after;rn+=r is None;wn+=w is None;closed+=r==ep.answer and w==ep.after
    n=len(test);return {'read_accuracy':ra/n,'write_accuracy':wa/n,'closed_cycle':closed/n,'wrong_read':rw/n,'wrong_write':ww/n,'read_null':rn/n,'write_null':wn/n,'inference_ms':(time.perf_counter()-t)*1000/n}

def run(seed):
    induction=build(seed,72,'seen',0)+build(seed+11,36,'held',20);probe=build(seed+101,36,'seen',50);modes=['seen','held','rename','alternate','omitted','paragraph','free'];out={}
    for method,shuffle in [('factorized',False),('cycle',False),('slow',False),('shuffle',True)]:
        m=Memory('cycle' if method=='shuffle' else method);m.fit(induction,probe,shuffle);r={'write_nodes':len(m.ws),'value_nodes':len(m.vs),'query_nodes':len(m.qs),'cycles':len(m.cycles),'slow_cycles':sum(c.slow for c in m.cycles),'audit':m.audit,'birth':m.birth,'model_bytes':len(pickle.dumps(m)),'training_seconds':m.train_s}
        for mode in modes:r[mode]=evalm(m,build(seed+999,24,mode,100))
        one=build(seed+500,1,'free',200)[0];fast=Memory('cycle');fast.fit(induction+[one],probe,False);rr,ww=fast.read_write(one);r['one_shot']=int(rr==one.answer and ww==one.after)
        seq=build(seed+700,24,'seen',300);first=Memory('cycle');first.fit(induction+seq[:12],probe,False);pre=sum(first.read_write(x)[0]==x.answer for x in seq[:12])/12;full=Memory('cycle');full.fit(induction+seq,probe,False);post=sum(full.read_write(x)[0]==x.answer for x in seq[:12])/12;latest=sum(full.read_write(x)[0]==x.answer for x in seq[12:])/12
        r.update(interference_before=pre,interference_after=post,latest_recall=latest);out[method]=r
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_033.json');a=ap.parse_args();raw={str(s):run(s) for s in (1,7,19)};summary={}
    for method in ('factorized','cycle','slow','shuffle'):
        summary[method]={};scalar=[k for k,v in raw['1'][method].items() if isinstance(v,(int,float))]
        for k in scalar:summary[method][k]=statistics.mean(raw[str(s)][method][k] for s in (1,7,19))
        for mode in ('seen','held','rename','alternate','omitted','paragraph','free'):
            summary[method][mode]={k:statistics.mean(raw[str(s)][method][mode][k] for s in (1,7,19)) for k in raw['1'][method][mode]}
    payload={'cycle':33,'hypothesis':'Cycle-Closing Memory Addresses from Joint Write-Read Counterexample Transport','raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'induction O(NL), probe O(QCVL), cycle birth O(C), read/write O(CVL)','final_test_outcome_used_for_retrieval':False,'fixed_ontology_or_handwritten_slots_used_by_model':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
