from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
FIELDS=['場所','状態','担当']
VALUES={'場所':['棚A','棚B','棚C','棚D'],'状態':['待機','処理中','完了','保留'],'担当':['担当一','担当二','担当三','担当四']}
STATE_FORMS=['{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。','{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。']
CMDS={'場所':['{o}を{v}へ移してください。','{o}の保管先を{v}へ変更します。'],'状態':['{o}を{v}にしてください。','{o}の進行状態を{v}へ切り替えます。'],'担当':['{o}を{v}の担当にしてください。','{o}の受け持ちを{v}へ変更します。']}
HELD={'場所':['対象{o}は次から{v}で保管。'],'状態':['対象{o}は以後{v}扱い。'],'担当':['{o}は{v}へ引き継ぎ。']}
OMIT={'場所':['それを{v}へ移してください。'],'状態':['その対象を{v}にしてください。'],'担当':['担当は{v}へ変えてください。']}

def state(o,d,form=0): return STATE_FORMS[form].format(o=o,loc=d['場所'],status=d['状態'],owner=d['担当'])
def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def shape(s): return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、／=：:\n ' else c for c in s)
def grams(s):
    s=''.join(s.split())
    return Counter(s[i:i+n] for n in (1,2,3) for i in range(max(0,len(s)-n+1)))
def cos(a,b):
    d=sum(v*b.get(k,0) for k,v in a.items())
    na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return d/(na*nb+1e-12)

@dataclass
class Episode:
    before:str; command:str; after:str; query:str; answer:str; obj:str; field:str; value:str; session:int; focus:str
@dataclass
class Trace:
    cl:str; cr:str; sl:str; sr:str; old_shape:str; new_shape:str; value:str
    support:int=1; write_success:int=0; write_wrong:int=0; damage:int=0; sessions:tuple=()
@dataclass
class WriteClass:
    members:tuple; consequence:tuple; support:int; sessions:tuple
@dataclass
class ReadAddress:
    state_left:str; state_right:str; query_left:str; query_right:str; value:str
    support:int=1; wrong:int=0; sessions:tuple=()
@dataclass
class CrossLink:
    write_class:int; read_address:int; value:str; support:int; sessions:tuple; slow:bool

class Memory:
    def __init__(self,mode):
        self.mode=mode
        self.traces=[]; self.write_classes=[]; self.read_addresses=[]; self.cross_links=[]
        self.train_seconds=0.0
    def _extract(self,command,t):
        i=command.find(t.cl) if t.cl else 0
        if i<0:return None
        st=i+len(t.cl); en=command.find(t.cr,st) if t.cr else len(command)
        if en<st:return None
        v=command[st:en]
        return v if 0<len(v)<=14 else None
    def _apply(self,before,command,t):
        v=self._extract(command,t)
        if v is None:return before,False,0,None
        hits=[];p=0
        while True:
            i=before.find(t.sl,p) if t.sl else p
            if i<0:break
            st=i+len(t.sl); en=before.find(t.sr,st) if t.sr else len(before)
            if en>=st:hits.append((st,en))
            p=i+1
            if not t.sl or p>=len(before):break
        if len(hits)!=1:return before,False,len(hits),v
        st,en=hits[0]
        return before[:st]+v+before[en:],True,1,v
    def fit(self,eps):
        t0=time.perf_counter(); td={}
        for e in eps:
            l,r,old,new=diff(e.before,e.after)
            if not old or not new: continue
            p=e.command.find(new)
            if p<0: continue
            tr=Trace(e.command[max(0,p-8):p],e.command[p+len(new):p+len(new)+8],
                     e.before[max(0,l-8):l],e.before[len(e.before)-r:len(e.before)-r+8] if r else '',
                     shape(old),shape(new),new)
            k=(tr.cl,tr.cr,tr.sl,tr.sr,tr.old_shape,tr.new_shape,tr.value)
            if k in td: td[k].support+=1
            else: td[k]=tr
        self.traces=sorted(td.values(),key=lambda x:x.support,reverse=True)[:96]
        for t in self.traces:
            ss=set()
            for e in eps:
                pred,ok,amb,_=self._apply(e.before,e.command,t)
                if ok and amb==1:
                    if pred==e.after: t.write_success+=1; ss.add(e.session)
                    else: t.write_wrong+=1
                    if '補助記録' not in pred: t.damage+=1
            t.sessions=tuple(sorted(ss))
        groups=defaultdict(list)
        for i,t in enumerate(self.traces):
            cons=(t.old_shape,t.new_shape,int(t.write_wrong==0),int(t.damage==0),min(3,t.write_success))
            groups[cons].append(i)
        for cons,idxs in groups.items():
            vals={self.traces[i].value for i in idxs}; sessions=set(s for i in idxs for s in self.traces[i].sessions)
            if len(idxs)>=2 and len(vals)>=2:
                self.write_classes.append(WriteClass(tuple(idxs),cons,sum(self.traces[i].write_success for i in idxs),tuple(sorted(sessions))))
        self.write_classes=sorted(self.write_classes,key=lambda c:(c.support,len(c.sessions),len(c.members)),reverse=True)[:32]
        rd={}
        for e in eps:
            p=e.after.find(e.answer); q=e.query.find(e.answer)
            if p<0: continue
            a=ReadAddress(e.after[max(0,p-10):p],e.after[p+len(e.answer):p+len(e.answer)+10],
                          e.query[max(0,max(0,q)-10):max(0,q)] if q>=0 else e.query[:10],
                          e.query[q+len(e.answer):q+len(e.answer)+10] if q>=0 else e.query[-10:],e.answer)
            k=(a.state_left,a.state_right,a.query_left,a.query_right,a.value)
            if k in rd: rd[k].support+=1
            else: rd[k]=a
        self.read_addresses=sorted(rd.values(),key=lambda a:a.support,reverse=True)[:96]
        for a in self.read_addresses:
            ss=set()
            for e in eps:
                if a.value in e.after:
                    sg=cos(grams(e.after),grams(a.state_left+a.value+a.state_right)); qg=cos(grams(e.query),grams(a.query_left+a.query_right))
                    if sg+qg>0.55:
                        if e.answer==a.value:ss.add(e.session)
                        else:a.wrong+=1
            a.sessions=tuple(sorted(ss))
        for ci,c in enumerate(self.write_classes):
            cvals={self.traces[i].value for i in c.members}
            for ai,a in enumerate(self.read_addresses):
                if a.value not in cvals: continue
                support=sum(self.traces[i].write_success for i in c.members if self.traces[i].value==a.value)+a.support
                sessions=set(a.sessions)
                for i in c.members:
                    if self.traces[i].value==a.value:sessions.update(self.traces[i].sessions)
                slow=(support>=3 and len(sessions)>=2 and a.wrong==0)
                self.cross_links.append(CrossLink(ci,ai,a.value,support,tuple(sorted(sessions)),slow))
        self.cross_links=sorted(self.cross_links,key=lambda x:(x.slow,x.support,len(x.sessions)),reverse=True)[:64]
        self.train_seconds=time.perf_counter()-t0
    def write(self,e):
        cand=[]
        for i,t in enumerate(self.traces):
            pred,ok,amb,v=self._apply(e.before,e.command,t)
            if not ok or amb!=1:continue
            score=t.support+1.5*t.write_success-2*t.write_wrong-2*t.damage
            if self.mode in ('dual','slow'):
                for ci,c in enumerate(self.write_classes):
                    if i in c.members:
                        score += 0.4*c.support + 0.2*len(c.sessions)
                        if self.mode=='slow':
                            linked=any(x.write_class==ci and x.value==v and x.slow for x in self.cross_links)
                            score += 1.0 if linked else -0.5
            cand.append((score,pred))
        if not cand:return e.before,False
        cand.sort(reverse=True)
        if len(cand)>1 and abs(cand[0][0]-cand[1][0])<1e-9:return e.before,False
        return cand[0][1],True
    def read(self,e):
        cand=[]
        for ai,a in enumerate(self.read_addresses):
            if a.value not in e.after: continue
            score=cos(grams(e.after),grams(a.state_left+a.value+a.state_right))+cos(grams(e.query),grams(a.query_left+a.query_right))+0.1*a.support-0.4*a.wrong
            if self.mode=='slow': score += 0.8 if any(x.read_address==ai and x.value==a.value and x.slow for x in self.cross_links) else -0.2
            cand.append((score,a.value))
        if not cand:return None
        cand.sort(reverse=True)
        if len(cand)>1 and cand[0][0]-cand[1][0]<0.03:return None
        return cand[0][1]

def build(seed,n,mode):
    rng=random.Random(seed);world={};eps=[];focus='';session=0
    for i in range(n):
        if i and i%6==0:session+=1
        canon=rng.choice(OBJECTS);o=ALIASES[canon] if mode=='rename' else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS})
        f=rng.choice(FIELDS);v=rng.choice([x for x in VALUES[f] if x!=world[canon][f]])
        before=state(o,world[canon],1 if mode=='alternate' else 0)
        forms=OMIT[f] if mode=='omitted' else HELD[f] if mode in ('held','paragraph','domain') else CMDS[f]
        command=rng.choice(forms).format(o=o,v=v)
        if mode=='paragraph':command='長い前置きです。別件の説明もあります。\n'+command+'\n補助記録は維持してください。'
        world[canon][f]=v;after=state(o,world[canon],1 if mode=='alternate' else 0)
        query=f'{o}の{f}は何ですか？'
        eps.append(Episode(before,command,after,query,v,o,f,v,session,focus));focus=o
    return eps

def run(seed,n,mode):
    train=[]
    for j,m in enumerate(('seen','held','rename','alternate')): train+=build(seed+17*j,n//4,m)
    test=build(seed+999,max(24,n//4),mode); out={}
    for method in ('trace','dual','slow'):
        M=Memory(method);M.fit(train);t=time.perf_counter();wc=ww=rc=rw=0
        for e in test:
            pred,did=M.write(e);wc+=int(did and pred==e.after);ww+=int(did and pred!=e.after)
            got=M.read(e);rc+=int(got==e.answer);rw+=int(got is not None and got!=e.answer)
        out[method]={'write_accuracy':wc/len(test),'wrong_write':ww/len(test),'read_accuracy':rc/len(test),'wrong_read':rw/len(test),
                     'traces':len(M.traces),'write_classes':len(M.write_classes),'read_addresses':len(M.read_addresses),
                     'cross_links':len(M.cross_links),'slow_links':sum(x.slow for x in M.cross_links),
                     'model_bytes':len(pickle.dumps(M)),'training_seconds':M.train_seconds,
                     'inference_ms':(time.perf_counter()-t)*1000/(2*len(test))}
    return out

def one_shot(seed):
    e=build(seed,1,'domain')[0];res={}
    for m in ('trace','dual','slow'):
        M=Memory(m);M.fit([e]);p,d=M.write(e);res[m]=int(d and p==e.after)
    return res

def interference(seed):
    base=build(seed,12,'seen');noise=build(seed+1,60,'paragraph');probe=base[-6:];res={}
    for m in ('trace','dual','slow'):
        M=Memory(m);M.fit(base+noise);res[m]=sum(M.read(e)==e.answer for e in probe)/len(probe)
    return res

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='MEASUREMENTS_CYCLE_023.json');a=ap.parse_args()
    modes=['seen','held','rename','alternate','omitted','paragraph','domain'];raw={}
    for n in (24,72,144):
        runs=[]
        for seed in (1,7,19):
            r={mode:run(seed,n,mode) for mode in modes};r['one_shot']=one_shot(seed);r['interference']=interference(seed);runs.append(r)
        raw[str(n)]=runs
    summary={}
    for n,runs in raw.items():
        summary[n]={}
        for mode in modes:
            summary[n][mode]={}
            for method in ('trace','dual','slow'):
                summary[n][mode][method]={k:statistics.mean(r[mode][method][k] for r in runs) for k in runs[0][mode][method]}
        summary[n]['one_shot']={m:statistics.mean(r['one_shot'][m] for r in runs) for m in ('trace','dual','slow')}
        summary[n]['interference']={m:statistics.mean(r['interference'][m] for r in runs) for m in ('trace','dual','slow')}
    payload={'hypothesis':'Dual-Channel Value Memory with Write-Only Equivalence and Query-Conditioned Read Addresses','seeds':[1,7,19],'sizes':[24,72,144],'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'trace extraction O(NL), write grouping O(T), read address O(NL), cross-link O(CA), inference O(TL+AL)','hidden_labels_used_by_learner':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary['144'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
