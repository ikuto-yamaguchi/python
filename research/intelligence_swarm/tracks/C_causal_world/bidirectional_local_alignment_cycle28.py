from __future__ import annotations
from dataclasses import dataclass
from collections import Counter,defaultdict
import argparse,json,math,pickle,random,resource,statistics,time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
FIELDS=['場所','状態','担当']
VALUES={'場所':['棚A','棚B','棚C','棚D'],'状態':['待機','処理中','完了','保留'],'担当':['担当一','担当二','担当三','担当四']}
STATE=['{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。','{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。']
CMD={'場所':['{o}を{v}へ移してください。','{o}の保管先を{v}へ変更します。'],'状態':['{o}を{v}にしてください。','{o}の進行状態を{v}へ切り替えます。'],'担当':['{o}を{v}の担当にしてください。','{o}の受け持ちを{v}へ変更します。']}
HELD={'場所':['対象{o}は次から{v}で保管。'],'状態':['対象{o}は以後{v}扱い。'],'担当':['{o}は{v}へ引き継ぎ。']}
OMIT={'場所':['それを{v}へ移してください。'],'状態':['その対象を{v}にしてください。'],'担当':['担当は{v}へ変えてください。']}
DIST=['別件の資料を確認しました。','旧案はいったん保留です。','この文は更新と無関係です。']

@dataclass
class Ex:
    before:str;command:str;after:str;future:str;env:int
    obj:str;field:str;old:str;new:str;focus:str
@dataclass
class Event:
    cl:str;cr:str;sl:str;sr:str;oldshape:str;newshape:str;support:int=1
@dataclass
class Alignment:
    source:int;target:int;score:float;forward_ok:bool;inverse_ok:bool;damage:int
    source_env:int;target_env:int
@dataclass
class Fiber:
    events:tuple;alignments:tuple;envs:tuple

def state(o,d,form):return STATE[form].format(o=o,loc=d['場所'],status=d['状態'],owner=d['担当'])
def shape(s):return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、／=：:\n ' else c for c in s)
def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def grams(s):
    s=''.join(s.split());return Counter(s[i:i+n] for n in (1,2,3) for i in range(max(0,len(s)-n+1)))
def cos(a,b):
    d=sum(v*b.get(k,0) for k,v in a.items());na=math.sqrt(sum(v*v for v in a.values()));nb=math.sqrt(sum(v*v for v in b.values()))
    return d/(na*nb+1e-12)

def build(seed,n,mode,env):
    rng=random.Random(seed);world={};out=[];focus=''
    for _ in range(n):
        canon=rng.choice(OBJECTS);surf=ALIASES[canon] if mode=='rename' else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS})
        f=rng.choice(FIELDS);old=world[canon][f];new=rng.choice([v for v in VALUES[f] if v!=old])
        form=1 if mode=='alternate' else 0;before=state(surf,world[canon],form)
        forms=OMIT[f] if mode=='omitted' else HELD[f] if mode in ('held','paragraph','plan','counterfactual') else CMD[f]
        command=rng.choice(forms).format(o=surf,v=new)
        if mode=='paragraph':command=' '.join(rng.choice(DIST) for _ in range(3))+'\n'+command
        if mode=='plan':
            prior=rng.choice([v for v in VALUES[f] if v not in (old,new)])
            command=f'{surf}を{prior}にする案でした。{rng.choice(DIST)} 最終的には'+command
        world[canon][f]=new;after=state(surf,world[canon],form)
        future=f'次の観測でも{surf}の更新結果は{new}で、補助記録は維持されます。'
        if mode=='counterfactual':future=f'もし実行しなければ{surf}は{old}のままです。実行時は{new}です。'
        out.append(Ex(before,command,after,future,env,surf,f,old,new,focus));focus=surf
    return out

class Model:
    def __init__(self,kind):
        self.kind=kind;self.events=[];self.alignments=[];self.fibers=[];self.train_seconds=0
    def extract(self,cmd,e):
        i=cmd.find(e.cl) if e.cl else 0
        if i<0:return None
        st=i+len(e.cl);en=cmd.find(e.cr,st) if e.cr else len(cmd)
        if en<st:return None
        x=cmd[st:en];return x if 0<len(x)<=14 else None
    def locate(self,before,e):
        hits=[];p=0
        while True:
            i=before.find(e.sl,p) if e.sl else p
            if i<0:break
            st=i+len(e.sl);en=before.find(e.sr,st) if e.sr else len(before)
            if en>=st:hits.append((st,en))
            p=i+1
            if not e.sl or p>=len(before):break
        return hits[0] if len(hits)==1 else None
    def apply(self,before,cmd,e):
        v=self.extract(cmd,e);loc=self.locate(before,e)
        if v is None or loc is None:return before,False,0
        st,en=loc
        if shape(before[st:en])!=e.oldshape:return before,False,1
        return before[:st]+v+before[en:],True,1
    def event_from(self,x):
        l,r,old,new=diff(x.before,x.after)
        if not old or not new:return None
        p=x.command.find(new)
        if p<0:return None
        return Event(x.command[max(0,p-8):p],x.command[p+len(new):p+len(new)+8],
                     x.before[max(0,l-8):l],x.before[len(x.before)-r:len(x.before)-r+8] if r else '',
                     shape(old),shape(new))
    def local_align(self,si,ti,rows):
        s=rows[si];t=rows[ti];se=self.events[si]
        te=self.event_from(t)
        if te is None:return None
        score=.25*(se.oldshape==te.oldshape)+.25*(se.newshape==te.newshape)
        score+=.15*cos(grams(se.cl+'|'+se.cr),grams(te.cl+'|'+te.cr))
        score+=.15*cos(grams(se.sl+'|'+se.sr),grams(te.sl+'|'+te.sr))
        score+=.20*(shape(s.new)==shape(t.new))
        fp,ok,a=self.apply(t.before,t.command,te)
        forward=bool(ok and a==1 and fp==t.after)
        ip,iok,ia=self.apply(s.before,s.command,se)
        inverse=bool(iok and ia==1 and ip==s.after)
        damage=int(('補助記録' in t.before) and ('補助記録' not in fp))
        return Alignment(si,ti,score,forward,inverse,damage,s.env,t.env)
    def fit(self,train):
        t0=time.perf_counter(); rows=[]; d={}
        for x in train:
            e=self.event_from(x)
            if e is None:continue
            k=(e.cl,e.cr,e.sl,e.sr,e.oldshape,e.newshape)
            if k in d:d[k].support+=1
            else:d[k]=e
            rows.append(x)
        self.events=sorted(d.values(),key=lambda e:e.support,reverse=True)[:32]
        erows=[]
        for e in self.events:
            found=None
            for x in rows:
                p,ok,a=self.apply(x.before,x.command,e)
                if ok and a==1 and p==x.after:found=x;break
            erows.append(found)
        audit_rows=[x for x in erows if x is not None]
        self.events=self.events[:len(audit_rows)]
        for i in range(len(audit_rows)):
            for j in range(len(audit_rows)):
                if i==j:continue
                al=self.local_align(i,j,audit_rows)
                if al and al.score>=.62 and al.forward_ok and al.inverse_ok and al.damage==0:
                    self.alignments.append(al)
        self.alignments=self.alignments[:256]
        if self.kind in ('alignment','fiber'):
            g=defaultdict(set); envs=defaultdict(set); aids=defaultdict(list)
            for ai,a in enumerate(self.alignments):
                g[a.source].add(a.target);g[a.target].add(a.source)
                envs[a.source]|={a.source_env,a.target_env};envs[a.target]|={a.source_env,a.target_env}
                aids[a.source].append(ai);aids[a.target].append(ai)
            seen=set()
            for node in g:
                if node in seen:continue
                stack=[node];comp=set()
                while stack:
                    q=stack.pop()
                    if q in comp:continue
                    comp.add(q);stack.extend(g[q]-comp)
                seen|=comp
                allenv=set().union(*(envs[x] for x in comp))
                allalign=sorted(set(ai for x in comp for ai in aids[x]))
                if len(comp)>=2 and len(allenv)>=3 and len(allalign)>=3:
                    self.fibers.append(Fiber(tuple(sorted(comp)),tuple(allalign),tuple(sorted(allenv))))
        self.train_seconds=time.perf_counter()-t0
    def predict(self,x):
        cand=[];cg=grams(x.command);sg=grams(x.before)
        aligned_events=set()
        if self.kind in ('alignment','fiber'):
            for a in self.alignments:aligned_events|={a.source,a.target}
        fiber_events=set()
        if self.kind=='fiber':
            for f in self.fibers:fiber_events.update(f.events)
        for i,e in enumerate(self.events):
            p,ok,a=self.apply(x.before,x.command,e)
            if not ok or a!=1:continue
            score=.45*cos(cg,grams(e.cl+'|'+e.cr))+.35*cos(sg,grams(e.sl+'|'+e.sr))+.2*min(1,e.support/4)
            score+=.12*(i in aligned_events)+.18*(i in fiber_events)
            cand.append((score,p))
        if not cand:return x.before,0,1
        cand.sort(reverse=True)
        if len(cand)>1 and cand[0][0]-cand[1][0]<.02:return x.before,len(cand),1
        return cand[0][1],len(cand),0

def evaluate(seed,n,mode):
    train=[]
    for env,m in enumerate(('seen','held','rename','alternate')):train+=build(seed+17*env,n//4,m,env)
    test=build(seed+999,24,mode,99);out={}
    for kind in ('surface','alignment','fiber'):
        M=Model(kind);M.fit(train);t=time.perf_counter();c=w=z=cs=0
        for x in test:
            p,k,nul=M.predict(x);cs+=k;c+=int(p==x.after);w+=int(p!=x.after and not nul);z+=nul
        envcov=len(set(a.target_env for a in M.alignments))
        out[kind]={'accuracy':c/len(test),'wrong_commit':w/len(test),'null_rate':z/len(test),
          'mean_candidates':cs/len(test),'events':len(M.events),'alignments':len(M.alignments),
          'alignment_env_coverage':envcov,'fibers':len(M.fibers),
          'fiber_members':sum(len(f.events) for f in M.fibers),
          'model_bytes':len(pickle.dumps(M)),'training_seconds':M.train_seconds,
          'inference_ms':(time.perf_counter()-t)*1000/len(test)}
    return out

def sequential(seed,n):
    seq=build(seed+700,n,'seen',0);out={}
    for kind in ('surface','alignment','fiber'):
        M=Model(kind);M.fit(seq[:n//2]);cov=cor=0
        for a,b in zip(seq[n//2:-1],seq[n//2+1:]):
            p1,c1,z1=M.predict(a);b2=Ex(p1,b.command,b.after,b.future,b.env,b.obj,b.field,b.old,b.new,b.focus)
            p2,c2,z2=M.predict(b2)
            if c1 and c2 and not z1 and not z2:cov+=1;cor+=int(p2==b.after)
        out[kind]={'coverage':cov/max(1,len(seq[n//2:-1])),'accuracy_conditional':cor/max(1,cov)}
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_028.json');a=ap.parse_args()
    modes=('seen','held','rename','alternate','omitted','paragraph','plan','counterfactual');raw={}
    for n in (96,):
        runs=[]
        for seed in (1,7,19):
            r={m:evaluate(seed,n,m) for m in modes};r['sequential']=sequential(seed,max(24,n//3));runs.append(r)
        raw[str(n)]=runs
    summary={}
    for n,runs in raw.items():
        summary[n]={}
        for m in modes:
            summary[n][m]={}
            for k in ('surface','alignment','fiber'):
                summary[n][m][k]={x:statistics.mean(r[m][k][x] for r in runs) for x in runs[0][m][k]}
        summary[n]['sequential']={k:{x:statistics.mean(r['sequential'][k][x] for r in runs) for x in runs[0]['sequential'][k]} for k in ('surface','alignment','fiber')}
    payload={'hypothesis':'Positive Witness Birth from Bidirectional Local Alignment Search','seeds':[1,7,19],'sizes':[96],
      'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      'estimated_complexity':'event extraction O(NL), bidirectional alignment O(P^2L), components O(P+A), inference O(PL), P<=32',
      'hidden_labels_used_by_learner':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,
      'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
if __name__=='__main__':main()
