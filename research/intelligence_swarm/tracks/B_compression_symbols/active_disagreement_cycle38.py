from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
import argparse,json,pickle,random,resource,statistics,time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
FIELDS=['場所','状態','担当']
VALUES={'場所':['棚A','棚B','棚C','棚D'],'状態':['待機','処理中','完了','保留'],'担当':['担当一','担当二','担当三','担当四']}
STATE0='{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。'
STATE1='{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。'
CMDS={'場所':['{o}を{v}へ移してください。','{o}の保管先を{v}へ変更します。'],'状態':['{o}を{v}にしてください。','{o}の進行状態を{v}へ切り替えます。'],'担当':['{o}を{v}の担当にしてください。','{o}の受け持ちを{v}へ変更します。']}
ORDER={'場所':['{v}へ移してください、対象は{o}です。'],'状態':['{v}扱いにしてください、対象は{o}です。'],'担当':['{v}へ引き継いでください、対象は{o}です。']}
LEX={'場所':['対象{o}は次から{v}で保管。'],'状態':['対象{o}は以後{v}として運用。'],'担当':['対象{o}の受持を{v}へ。']}
OMIT={'場所':['それを{v}へ移してください。'],'状態':['その対象を{v}にしてください。'],'担当':['担当は{v}へ変えてください。']}

@dataclass
class Ex:
    before:str;command:str;after:str;future:str;obj:str;field:str;old:str;new:str;mode:str
@dataclass(frozen=True)
class Prod:
    sb:int;sw:int;vb:int;vw:int;ob:int;ow:int;osh:str;vsh:str;objsh:str
@dataclass
class Sym:
    p:Prod;support:int=0;wrong:int=0;active_support:int=0;born:bool=False

def shape(s):
    return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、／=：:\n 「」' else c for c in s)
def state(o,d,form):return (STATE1 if form else STATE0).format(o=o,loc=d['場所'],status=d['状態'],owner=d['担当'])
def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def bucket(pos,n,k=16):return min(k-1,max(0,int(k*pos/max(1,n))))
def span(text,b,w,k=16):
    a=round(len(text)*b/k);z=round(len(text)*min(k,b+w)/k)
    return a,max(a+1,min(len(text),z)),text[a:max(a+1,min(len(text),z))]
def build(seed,n,mode):
    rng=random.Random(seed);world={};focus=None;out=[]
    for _ in range(n):
        canon=focus if mode=='omitted' and focus else rng.choice(OBJECTS);surf=ALIASES[canon] if mode=='rename' else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS});f=rng.choice(FIELDS);old=world[canon][f];new=rng.choice([x for x in VALUES[f] if x!=old])
        form=1 if mode=='alternate' else 0;before=state(surf,world[canon],form)
        forms=ORDER[f] if mode=='order' else LEX[f] if mode=='lexeme' else OMIT[f] if mode=='omitted' else CMDS[f]
        command=rng.choice(forms).format(o=surf,v=new)
        if mode=='nested':command='依頼内容は「'+command+'」です。'
        if mode=='paragraph':command='前段の説明があります。別件は変更しません。\n'+command+'\n補助記録は維持してください。'
        world[canon][f]=new;after=state(surf,world[canon],form);future=f'次の観測でも{surf}の更新結果は{new}で、補助記録は維持されます。'
        out.append(Ex(before,command,after,future,surf,f,old,new,mode));focus=canon
    return out

def induce(e):
    l,r,old,new=diff(e.before,e.after);vi=e.command.find(new);oi=e.command.find(e.obj)
    if not old or not new or vi<0 or oi<0:return None
    return Prod(bucket(l,len(e.before)),max(1,bucket(l+len(old),len(e.before))-bucket(l,len(e.before))),bucket(vi,len(e.command)),max(1,bucket(vi+len(new),len(e.command))-bucket(vi,len(e.command))),bucket(oi,len(e.command)),max(1,bucket(oi+len(e.obj),len(e.command))-bucket(oi,len(e.command))),shape(old),shape(new),shape(e.obj))
def apply(e,p):
    sa,sb,s=span(e.before,p.sb,p.sw);_,_,v=span(e.command,p.vb,p.vw);_,_,o=span(e.command,p.ob,p.ow)
    if shape(s)!=p.osh:return None
    return e.before[:sa]+v+e.before[sb:],o,v

def perturb(e,pair):
    qs=[];vals=[x for xs in VALUES.values() for x in xs if x not in e.command][:8]
    for v in vals:
        chunks=[span(e.command,p.vb,p.vw)[2] for p in pair]
        for z in sorted(set(chunks),key=len,reverse=True):
            if z and z in e.command:qs.append(Ex(e.before,e.command.replace(z,v,1),e.after,e.future,e.obj,e.field,e.old,v,'active_value'))
    for o in [x for x in OBJECTS+list(ALIASES.values()) if x not in e.command][:8]:
        chunks=[span(e.command,p.ob,p.ow)[2] for p in pair]
        for z in sorted(set(chunks),key=len,reverse=True):
            if z and z in e.command:qs.append(Ex(e.before,e.command.replace(z,o,1),e.after,e.future,o,e.field,e.old,e.new,'active_object'))
    qs += [Ex(e.before,'補足です。'+e.command,e.after,e.future,e.obj,e.field,e.old,e.new,'prefix'),Ex(e.before,e.command+' 補助記録は維持します。',e.after,e.future,e.obj,e.field,e.old,e.new,'suffix'),Ex(e.before,'依頼内容は「'+e.command+'」です。',e.after,e.future,e.obj,e.field,e.old,e.new,'wrap')]
    return list({q.command:q for q in qs}.values())[:24]

def oracle(q,source):
    v=None
    for x in [z for xs in VALUES.values() for z in xs]:
        if x in q.command:v=x
    if v is None:v=source.new
    l,r,_,_=diff(source.before,source.after)
    return source.before[:l]+v+source.before[len(source.before)-r if r else len(source.before):]

def mutate(p):
    out=[]
    for attr in ('sb','sw','vb','vw','ob','ow'):
        for d in (-1,1):
            vals=p.__dict__.copy();vals[attr]=max(0 if attr.endswith('b') else 1,min(15 if attr.endswith('b') else 8,vals[attr]+d));out.append(Prod(**vals))
    return out

class Model:
    def __init__(self,mode):
        self.mode=mode;self.syms=[];self.queries=0;self.disagreements=0;self.births=0;self.bits=0;self.train_s=0
    def fit(self,ind,probe,shuffle=False):
        t=time.perf_counter();cnt=Counter(induce(e) for e in ind);cnt.pop(None,None)
        syms=[Sym(p,n) for p,n in cnt.items() if n>=2][:48];birth=Counter();pairs=[]
        for i in range(len(syms)):
            for j in range(i+1,len(syms)):
                if syms[i].p.osh==syms[j].p.osh:pairs.append((i,j))
        for ei,e in enumerate(probe):
            scored=[]
            for i,j in pairs[:160]:
                for q in perturb(e,(syms[i].p,syms[j].p)):
                    a=apply(q,syms[i].p);b=apply(q,syms[j].p)
                    if not a or not b or a[0]==b[0]:continue
                    bits=8*(len(q.before)+len(q.command));scored.append((1.0/bits,i,j,q,a,b))
            if not scored:continue
            _,i,j,q,a,b=max(scored,key=lambda x:x[0]);self.queries+=1
            truth=oracle(q,probe[(ei+1)%len(probe)] if shuffle else e)
            ca=a[0]==truth;cb=b[0]==truth
            if ca==cb:continue
            self.disagreements+=1;winner=i if ca else j;loser=j if ca else i
            syms[winner].active_support+=1;syms[loser].wrong+=1
            if self.mode in ('birth','mdl'):
                for np in mutate(syms[loser].p):
                    z=apply(q,np)
                    if z and z[0]==truth:birth[np]+=1
                    elif z:birth[np]-=1
        if self.mode in ('birth','mdl'):
            for p,n in birth.items():
                if n>=2:syms.append(Sym(p,support=n,active_support=n,born=True));self.births+=1
        self.syms=sorted(syms,key=lambda s:(s.support+s.active_support-s.wrong,s.active_support),reverse=True)[:64]
        literal=sum(8*(len(e.before)+len(e.command)+len(e.after)+len(e.future)) for e in ind+probe)
        grammar=len(self.syms)*120+self.queries*48+self.births*72;residual=sum(s.wrong*16 for s in self.syms)
        self.bits=literal if self.mode=='factorized' else grammar+residual;self.train_s=time.perf_counter()-t
    def predict(self,e):
        cand=[]
        for s in self.syms:
            z=apply(e,s.p)
            if z:cand.append((s.support+s.active_support-s.wrong,z[0],z[1],z[2]))
        best={}
        for x in cand:
            if x[1] not in best or x[0]>best[x[1]][0]:best[x[1]]=x
        ranked=sorted(best.values(),reverse=True)[:64]
        if not ranked:return None,0,[]
        if len(ranked)>1 and ranked[0][0]-ranked[1][0]<1:return None,len(ranked),[(x[2],x[3]) for x in ranked]
        return ranked[0][1],len(ranked),[(x[2],x[3]) for x in ranked]

def evaluate(m,test):
    t=time.perf_counter();c=w=n=p=k=0
    for e in test:
        y,z,pairs=m.predict(e);k+=z;n+=y is None;c+=y==e.after;w+=y is not None and y!=e.after;p+=any(o==e.obj and v==e.new for o,v in pairs)
    N=len(test)
    return {'accuracy':c/N,'wrong_commit':w/N,'null_rate':n/N,'pair_recall':p/N,'mean_candidates':k/N,'symbols':len(m.syms),'active_queries':m.queries,'disagreements':m.disagreements,'born_productions':m.births,'description_bits':m.bits,'model_bytes':len(pickle.dumps(m)),'training_seconds':m.train_s,'inference_ms':(time.perf_counter()-t)*1000/N}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='MEASUREMENTS_CYCLE_038.json');a=ap.parse_args()
    modes=['seen','order','lexeme','rename','alternate','nested','omitted','paragraph'];raw={}
    for seed in (1,7,19):
        allx=build(seed,180,'seen');ind,probe=allx[:120],allx[120:];raw[str(seed)]={};models={}
        for mode in ('factorized','passive','active','birth','mdl','shuffle'):
            m=Model('birth' if mode=='shuffle' else mode);m.fit(ind,probe,shuffle=mode=='shuffle');models[mode]=m
        for tm in modes:raw[str(seed)][tm]={name:evaluate(m,build(seed+999,30,tm)) for name,m in models.items()}
    summary={}
    for tm in modes:
        summary[tm]={}
        for name in ('factorized','passive','active','birth','mdl','shuffle'):
            ks=raw['1'][tm][name];summary[tm][name]={k:statistics.mean(raw[str(s)][tm][name][k] for s in (1,7,19)) for k,v in ks.items() if isinstance(v,(int,float))}
    payload={'cycle':38,'hypothesis':'Disagreement-Seeking Production Birth from Active Counterexample Partitioning','seeds':[1,7,19],'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'induction O(NL), pair query synthesis O(QP^2UL), mutation birth O(DR), inference O(PL)','final_test_outcome_used_for_selection':False,'fixed_ontology_or_handwritten_slots_used_by_model':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    open(a.output,'w',encoding='utf-8').write(json.dumps(payload,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
