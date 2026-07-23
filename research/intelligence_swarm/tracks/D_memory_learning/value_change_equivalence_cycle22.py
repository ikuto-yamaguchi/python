from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict, Counter
import argparse,json,math,pickle,random,resource,statistics,time

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
    s=''.join(s.split()); return Counter(s[i:i+n] for n in (1,2,3) for i in range(max(0,len(s)-n+1)))
def cos(a,b):
    d=sum(v*b.get(k,0) for k,v in a.items()); na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return d/(na*nb+1e-12)

@dataclass
class Episode:
    before:str; command:str; after:str; query:str; answer:str; obj:str; field:str; value:str; session:int; focus:str
@dataclass
class Trace:
    cl:str; cr:str; sl:str; sr:str; old_shape:str; new_shape:str; value:str
    support:int=1; write_success:int=0; write_wrong:int=0; read_success:int=0; damage:int=0; sessions:tuple=()
@dataclass
class ValueClass:
    members:tuple; consequence:tuple; support:int; sessions:tuple; slow:bool=False

class Memory:
    def __init__(self,mode):
        self.mode=mode; self.traces=[]; self.classes=[]; self.train_seconds=0.0
    def _extract_value(self,command,t):
        i=command.find(t.cl) if t.cl else 0
        if i<0:return None
        st=i+len(t.cl); en=command.find(t.cr,st) if t.cr else len(command)
        if en<st:return None
        v=command[st:en]
        return v if 0<len(v)<=14 else None
    def _apply(self,before,command,t):
        v=self._extract_value(command,t)
        if v is None:return before,False,0
        starts=[];p=0
        while True:
            i=before.find(t.sl,p) if t.sl else p
            if i<0:break
            st=i+len(t.sl); en=before.find(t.sr,st) if t.sr else len(before)
            if en>=st:starts.append((st,en))
            p=i+1
            if not t.sl or p>=len(before):break
        if len(starts)!=1:return before,False,len(starts)
        st,en=starts[0]
        return before[:st]+v+before[en:],True,1
    def fit(self,eps):
        t0=time.perf_counter(); d={}
        for e in eps:
            l,r,old,new=diff(e.before,e.after)
            if not old or not new:continue
            p=e.command.find(new)
            if p<0:continue
            tr=Trace(e.command[max(0,p-8):p],e.command[p+len(new):p+len(new)+8],e.before[max(0,l-8):l],e.before[len(e.before)-r:len(e.before)-r+8] if r else '',shape(old),shape(new),new)
            k=(tr.cl,tr.cr,tr.sl,tr.sr,tr.old_shape,tr.new_shape,tr.value)
            if k in d:d[k].support+=1
            else:d[k]=tr
        self.traces=sorted(d.values(),key=lambda x:x.support,reverse=True)[:96]
        for t in self.traces:
            sess=set()
            for e in eps:
                pred,ok,amb=self._apply(e.before,e.command,t)
                if ok and amb==1:
                    if pred==e.after:t.write_success+=1;sess.add(e.session)
                    else:t.write_wrong+=1
                if t.value in e.answer and t.value in e.after:t.read_success+=1
                if ok and pred!=e.after and '補助記録は維持' not in pred:t.damage+=1
            t.sessions=tuple(sorted(sess))
        if self.mode in ('class','slow'):
            groups=defaultdict(list)
            for i,t in enumerate(self.traces):
                consequence=(t.old_shape,t.new_shape,int(t.write_success>0),int(t.write_wrong==0),int(t.damage==0),min(3,t.write_success),min(3,t.read_success))
                groups[consequence].append(i)
            for cons,idxs in groups.items():
                vals={self.traces[i].value for i in idxs}; sessions=set(s for i in idxs for s in self.traces[i].sessions)
                if len(idxs)>=2 and len(vals)>=2:
                    slow=(len(sessions)>=2 and all(self.traces[i].write_success>0 and self.traces[i].write_wrong==0 and self.traces[i].damage==0 for i in idxs))
                    self.classes.append(ValueClass(tuple(idxs),cons,sum(self.traces[i].write_success for i in idxs),tuple(sorted(sessions)),slow))
            self.classes=sorted(self.classes,key=lambda c:(c.slow,c.support,len(c.members)),reverse=True)[:32]
        self.train_seconds=time.perf_counter()-t0
    def write(self,e):
        cand=[]
        for i,t in enumerate(self.traces):
            pred,ok,amb=self._apply(e.before,e.command,t)
            if not ok or amb!=1:continue
            score=t.support+1.5*t.write_success-2*t.write_wrong-2*t.damage
            if self.mode in ('class','slow'):
                for c in self.classes:
                    if i in c.members:
                        if self.mode=='slow' and not c.slow: continue
                        score += 2+0.2*c.support+0.5*len(c.sessions)
            cand.append((score,pred))
        if not cand:return e.before,False
        cand.sort(reverse=True); return cand[0][1],True
    def read(self,e):
        cand=[]; sg=grams(e.after); qg=grams(e.query)
        for i,t in enumerate(self.traces):
            if t.value not in e.after:continue
            score=cos(sg,grams(t.sl+t.value+t.sr))+cos(qg,grams(t.cl+t.cr))+0.1*t.read_success
            if self.mode in ('class','slow'):
                for c in self.classes:
                    if i in c.members:
                        if self.mode=='slow' and not c.slow:continue
                        score+=0.5+0.1*c.support
            cand.append((score,t.value))
        if not cand:return None
        cand.sort(reverse=True); return cand[0][1]

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
        if mode=='paragraph':command='前置きの説明です。別件も確認しました。\n'+command+'\n補助記録は維持してください。'
        world[canon][f]=v;after=state(o,world[canon],1 if mode=='alternate' else 0)
        eps.append(Episode(before,command,after,f'{o}の{f}は何ですか？',v,o,f,v,session,focus));focus=o
    return eps

def run(seed,n,mode):
    train=[]
    for j,m in enumerate(('seen','held','rename','alternate')):train+=build(seed+17*j,n//4,m)
    test=build(seed+999,max(24,n//4),mode); out={}
    for method in ('trace','class','slow'):
        M=Memory(method);M.fit(train);t=time.perf_counter();wc=ww=rc=rw=0
        for e in test:
            pred,did=M.write(e);wc+=int(did and pred==e.after);ww+=int(did and pred!=e.after)
            got=M.read(e);rc+=int(got==e.answer);rw+=int(got is not None and got!=e.answer)
        out[method]={'write_accuracy':wc/len(test),'wrong_write':ww/len(test),'read_accuracy':rc/len(test),'wrong_read':rw/len(test),'traces':len(M.traces),'classes':len(M.classes),'slow_classes':sum(c.slow for c in M.classes),'model_bytes':len(pickle.dumps(M)),'training_seconds':M.train_seconds,'inference_ms':(time.perf_counter()-t)*1000/(2*len(test))}
    return out

def one_shot(seed):
    e=build(seed,1,'domain')[0];res={}
    for m in ('trace','class','slow'):
        M=Memory(m);M.fit([e]);p,d=M.write(e);res[m]=int(d and p==e.after)
    return res

def interference(seed):
    base=build(seed,12,'seen');noise=build(seed+1,48,'paragraph');probe=base[-6:];res={}
    for m in ('trace','class','slow'):
        M=Memory(m);M.fit(base+noise);res[m]=sum(M.read(e)==e.answer for e in probe)/len(probe)
    return res

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='MEASUREMENTS_CYCLE_022.json');a=ap.parse_args()
    modes=['seen','held','rename','alternate','omitted','paragraph','domain']; raw={}
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
            for method in ('trace','class','slow'):summary[n][mode][method]={k:statistics.mean(r[mode][method][k] for r in runs) for k in runs[0][mode][method]}
        summary[n]['one_shot']={m:statistics.mean(r['one_shot'][m] for r in runs) for m in ('trace','class','slow')}
        summary[n]['interference']={m:statistics.mean(r['interference'][m] for r in runs) for m in ('trace','class','slow')}
    payload={'hypothesis':'Value-Change Equivalence Classes from Cross-Surface Write Consequences','seeds':[1,7,19],'sizes':[24,72,144],'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'trace extraction O(NL), consequence grouping O(T), read/write O(TL), T<=96','hidden_labels_used_by_learner':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary['144'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
