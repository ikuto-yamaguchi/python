from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
FIELDS=['場所','状態','担当']
VALUES={'場所':['棚A','棚B','棚C','棚D'],'状態':['待機','処理中','完了','保留'],'担当':['担当一','担当二','担当三','担当四']}
STATE_FORMS=['{o}の場所は{場所}で、状態は{状態}、担当は{担当}です。','{o}：保管={場所}／進行={状態}／受持={担当}。','{o}について、置場{場所}、段階{状態}、担当者{担当}。','{o}を記録。{場所}にあり、現在{状態}、受け持ちは{担当}。']
COMMANDS={'場所':['{o}を{v}へ移してください。','{o}の置き場を{v}へ変更します。'],'状態':['{o}を{v}にしてください。','{o}の進行を{v}へ切り替えます。'],'担当':['{o}を{v}へ引き継いでください。','{o}の担当者を{v}へ変更します。']}
HELD={'場所':['対象{o}、次から{v}で保管。','保管場所は{v}。対象は{o}。'],'状態':['対象{o}は以後{v}扱い。','進行を{v}へ。対象は{o}。'],'担当':['{o}は{v}へ引継ぎ。','受持は{v}。対象は{o}。']}
OMIT={'場所':['それを{v}へ移してください。'],'状態':['その対象を{v}にしてください。'],'担当':['担当は{v}へ変えてください。']}
DIST=['別件の資料も確認しました。','前の案はいったん保留です。','これは更新とは無関係です。']
SEPS=set('、。！？「」『』（）()=：:／ 　\n')

@dataclass
class Example:
    before:str; command:str; after:str; future:str
    obj:str; field:str; value:str; mode:str; focus:str

@dataclass
class Rule:
    cmd_left:str; cmd_right:str; old:str; new:str
    left_ctx:str; right_ctx:str; preserve_shape:tuple

@dataclass
class Edge:
    src:int; dst:int; score:float; cycle:float; intervention:float; support:int

def grams(s):
    s=''.join(s.split())
    return Counter(s[i:i+n] for n in (1,2,3) for i in range(max(0,len(s)-n+1)))

def cos(a,b):
    d=sum(v*b.get(k,0) for k,v in a.items())
    na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return d/(na*nb+1e-12)

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

def segments(s,max_len=14):
    out=[]; start=0
    for i,c in enumerate(s):
        if c in SEPS:
            if 1<=i-start<=max_len: out.append((start,i,s[start:i]))
            start=i+1
    if 1<=len(s)-start<=max_len: out.append((start,len(s),s[start:]))
    for i in range(len(s)):
        if i==0 or s[i-1] in SEPS:
            for ln in (2,3,4,6,8,10,12):
                if i+ln<=len(s):
                    x=s[i:i+ln]
                    if not any(c in SEPS for c in x): out.append((i,i+ln,x))
    seen=set(); ans=[]
    for a,b,x in out:
        if x not in seen:
            seen.add(x); ans.append((a,b,x))
    return ans[:48]

def make_state(o,d,form): return STATE_FORMS[form].format(o=o,**d)

def make_dataset(seed,n,mode):
    rng=random.Random(seed); world={}; focus=''; out=[]
    for _ in range(n):
        canonical=rng.choice(OBJECTS); surface=ALIASES[canonical] if mode=='rename' else canonical
        world.setdefault(canonical,{f:rng.choice(VALUES[f]) for f in FIELDS})
        f=rng.choice(FIELDS); nv=rng.choice([x for x in VALUES[f] if x!=world[canonical][f]])
        form={'alternate':1,'free_state':3}.get(mode,0)
        before=make_state(surface,world[canonical],form)
        if mode=='omitted': tmpl=rng.choice(OMIT[f])
        elif mode in ('held','paragraph','plan','rename','free_state'): tmpl=rng.choice(HELD[f])
        else: tmpl=rng.choice(COMMANDS[f])
        cmd=tmpl.format(o=surface,v=nv)
        if mode=='paragraph': cmd=' '.join(rng.choice(DIST) for _ in range(3))+'\n'+cmd
        if mode=='plan':
            alt=rng.choice([x for x in VALUES[f] if x not in (world[canonical][f],nv)])
            cmd=f'{surface}を{alt}にする案でした。{rng.choice(DIST)} 最終的には'+cmd
        world[canonical][f]=nv; after=make_state(surface,world[canonical],form)
        future=f'次の観測でも{surface}の更新値は{nv}で、他の記録は保持されます。'
        out.append(Example(before,cmd,after,future,canonical,f,nv,mode,focus)); focus=surface
    return out

def extract_rule(e):
    l,r,old,new=diff(e.before,e.after)
    if not old or not new: return None
    i=e.command.find(new)
    if i<0:return None
    left=e.command[max(0,i-8):i]; right=e.command[i+len(new):i+len(new)+8]
    lc=e.before[max(0,l-10):l]; rc=e.before[len(e.before)-r:len(e.before)-r+10] if r else e.before[l+len(old):l+len(old)+10]
    return Rule(left,right,old,new,lc,rc,(len(e.before),len(old),len(new),len(lc),len(rc)))

def execute(state,cmd,r):
    i=cmd.find(r.cmd_left) if r.cmd_left else 0
    if i<0:return state,False
    s=i+len(r.cmd_left); en=cmd.find(r.cmd_right,s) if r.cmd_right else len(cmd)
    if en<s:return state,False
    val=cmd[s:en]; positions=[]; start=0
    while r.old and (pos:=state.find(r.old,start))>=0:
        positions.append((1.0,pos,pos+len(r.old))); start=pos+1
    for a,b,x in segments(state):
        sc=.5*cos(grams(state[max(0,a-10):a]),grams(r.left_ctx))+.5*cos(grams(state[b:b+10]),grams(r.right_ctx))
        if x==r.old: sc+=.4
        positions.append((sc,a,b))
    if not positions:return state,False
    positions.sort(reverse=True); sc,a,b=positions[0]
    if sc<.15:return state,False
    return state[:a]+val+state[b:],True

def preservation(before,pred,after):
    l,r,_,_=diff(before,after); lp,rp,_,_=diff(before,pred)
    return int(before[:l]==before[:lp] and (before[len(before)-r:] if r else '')==(before[len(before)-rp:] if rp else ''))

class Model:
    def __init__(self,kind): self.kind=kind; self.rules=[]; self.edges=[]; self.training_seconds=0; self.null_maps=0
    def fit(self,examples):
        t=time.perf_counter(); self.rules=[r for e in examples if (r:=extract_rule(e))][-64:]
        if self.kind=='surface': self.training_seconds=time.perf_counter()-t; return
        cand=[]
        for i,a in enumerate(self.rules):
            for j,b in enumerate(self.rules):
                if i==j:continue
                local=.35*cos(grams(a.left_ctx+a.right_ctx),grams(b.left_ctx+b.right_ctx))
                change=.25*cos(grams(a.old+'>'+a.new),grams(b.old+'>'+b.new))
                shape=.2/(1+sum(abs(x-y) for x,y in zip(a.preserve_shape,b.preserve_shape)))
                cmd=.2*cos(grams(a.cmd_left+a.cmd_right),grams(b.cmd_left+b.cmd_right))
                sc=local+change+shape+cmd
                if sc>=.28:cand.append((sc,i,j))
        cand.sort(reverse=True); cand=cand[:160]; bypair={(i,j):sc for sc,i,j in cand}
        for sc,i,j in cand:
            cycle=min(sc,bypair.get((j,i),0.0)); ok=bad=0
            for e in examples[:24]:
                pj,okj=execute(e.before,e.command,self.rules[j])
                if not okj:continue
                pi,oki=execute(e.before,e.command,self.rules[i])
                if not oki:continue
                target=int(pj==e.after)
                invariant=int(preservation(e.before,pi,e.after) and diff(e.before,pi)[3] in e.future)
                ok+=int(target and invariant); bad+=int(target and not invariant)
            intervention=(ok+1)/(ok+bad+2)
            keep=cycle>=.45 if self.kind=='hard_cycle' else cycle>=.30 and intervention>=.50
            if keep:self.edges.append(Edge(i,j,sc,cycle,intervention,ok+bad))
            else:self.null_maps+=1
        self.edges=sorted(self.edges,key=lambda e:(e.intervention,e.cycle,e.score),reverse=True)[:64]
        self.training_seconds=time.perf_counter()-t
    def predict(self,e):
        cands=[]
        if self.kind=='surface': pool=[(0.0,i) for i in range(len(self.rules))]
        else:
            pool=[]
            for ed in self.edges:
                prior=.35*ed.cycle+.45*ed.intervention+.02*math.log1p(ed.support)
                pool.extend(((prior,ed.dst),(prior*.95,ed.src)))
        seen=set()
        for prior,idx in pool:
            if idx in seen:continue
            seen.add(idx); r=self.rules[idx]; pred,ok=execute(e.before,e.command,r)
            if not ok:continue
            new=diff(e.before,pred)[3]
            score=prior+.3*int(new in e.future)+.25*preservation(e.before,pred,e.after)+.15*cos(grams(e.command),grams(r.cmd_left+r.cmd_right))
            cands.append((score,pred))
        if not cands:return None,0
        cands.sort(reverse=True)
        if len(cands)>1 and cands[0][0]-cands[1][0]<.025:return None,len(cands)
        return cands[0][1],len(cands)

def conditional_cf(model,examples):
    cov=correct=0
    for i in range(0,len(examples)-1,2):
        a,b=examples[i],examples[i+1]; ra=extract_rule(a); rb=extract_rule(b)
        if not ra or not rb:continue
        x1,o1=execute(a.before,a.command,ra); x2,o2=execute(x1,b.command,rb)
        y1,o3=execute(a.before,b.command,rb); y2,o4=execute(y1,a.command,ra)
        if not all((o1,o2,o3,o4)):continue
        cov+=1; expected=a.obj!=b.obj or a.field!=b.field; correct+=int((x2==y2)==expected)
    return correct/max(1,cov),cov

def evaluate(seed,n,mode):
    train=[]
    for i in range(n):train.extend(make_dataset(seed+i,1,['seen','rename','alternate'][i%3]))
    test=make_dataset(seed+999,max(12,n//8),mode); out={}
    for kind in ('surface','hard_cycle','intervention_cycle'):
        m=Model(kind);m.fit(train);start=time.perf_counter();acc=null=cands=0
        for e in test:
            p,c=m.predict(e);acc+=int(p==e.after);null+=int(p is None);cands+=c
        inf=(time.perf_counter()-start)*1000/len(test);cf,cov=conditional_cf(m,test)
        out[kind]={'accuracy':acc/len(test),'null_rate':null/len(test),'mean_candidates':cands/len(test),'cf_accuracy_conditional':cf,'cf_coverage':cov/len(test),'rules':len(m.rules),'edges':len(m.edges),'mean_cycle':statistics.mean([e.cycle for e in m.edges]) if m.edges else 0,'mean_intervention':statistics.mean([e.intervention for e in m.edges]) if m.edges else 0,'null_maps':m.null_maps,'model_bytes':len(pickle.dumps(m)),'training_seconds':m.training_seconds,'inference_ms':inf}
    return out

MODES=('seen','held','alternate','rename','omitted','paragraph','plan','free_state')
def summarize(raw):
    s={}
    for n,runs in raw.items():
        s[n]={}
        for mode in MODES:
            s[n][mode]={}
            for kind in ('surface','hard_cycle','intervention_cycle'):
                keys=runs[0][mode][kind]; s[n][mode][kind]={k:statistics.mean(r[mode][kind][k] for r in runs) for k in keys}
    return s

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_020.json');a=ap.parse_args(); raw={}
    for n in (24,72,192):
        raw[str(n)]=[{m:evaluate(seed,n,m) for m in MODES} for seed in (1,7,19)]
    payload={'hypothesis':'Intervention-Preserving Soft Correspondence Cycles','seeds':[1,7,19],'sizes':[24,72,192],'raw':raw,'summary':summarize(raw),'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'segment O(L), graph O(P^2 G + E N G), inference O(EG), P<=64,E<=64','hidden_labels_used_by_learner':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload['summary']['192'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
