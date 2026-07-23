from __future__ import annotations
from dataclasses import dataclass, asdict
from collections import Counter, defaultdict
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
FIELDS=['場所','状態','担当']
VALUES={'場所':['棚A','棚B','棚C','棚D'],'状態':['待機','処理中','完了','保留'],'担当':['担当一','担当二','担当三','担当四']}
STATE_FORMS=[
 '{o}の場所は{場所}で、状態は{状態}、担当は{担当}です。',
 '{o}：保管={場所}／進行={状態}／受持={担当}。',
 '{o}について、置場{場所}、段階{状態}、担当者{担当}。',
]
COMMANDS={
 '場所':['{o}を{v}へ移してください。','{o}の置き場を{v}へ変更します。'],
 '状態':['{o}を{v}にしてください。','{o}の進行を{v}へ切り替えます。'],
 '担当':['{o}を{v}へ引き継いでください。','{o}の担当者を{v}へ変更します。'],
}
HELD={
 '場所':['対象{o}、次から{v}で保管。','保管場所は{v}。対象は{o}。'],
 '状態':['対象{o}は以後{v}扱い。','進行を{v}へ。対象は{o}。'],
 '担当':['{o}は{v}へ引継ぎ。','受持は{v}。対象は{o}。'],
}
OMIT={'場所':['それを{v}へ移してください。'],'状態':['その対象を{v}にしてください。'],'担当':['担当は{v}へ変えてください。']}
DIST=['別件の資料も確認しました。','前の案はいったん保留です。','これは更新とは無関係です。']

@dataclass
class Example:
    before:str; command:str; after:str; future:str
    obj:str; field:str; value:str; mode:str; focus:str

def grams(s:str)->Counter:
    s=''.join(s.split())
    return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))

def cos(a:Counter,b:Counter)->float:
    d=sum(v*b.get(k,0) for k,v in a.items()); na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return d/(na*nb+1e-12)

def diff(a:str,b:str):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

def local_views(before,after,radius=8):
    l,r,old,new=diff(before,after)
    left=before[max(0,l-radius):l]; right=before[len(before)-r:len(before)-r+radius] if r else before[l+len(old):l+len(old)+radius]
    preserved_prefix=before[:l]; preserved_suffix=before[len(before)-r:] if r else before[l+len(old):]
    return {'left':left,'right':right,'old':old,'new':new,'prefix':preserved_prefix,'suffix':preserved_suffix,'l':l,'r':r}

def make_state(o,d,form): return STATE_FORMS[form].format(o=o,**d)

def make_dataset(seed,n,mode):
    rng=random.Random(seed); world={}; focus=''; out=[]
    for _ in range(n):
        canonical=rng.choice(OBJECTS); surface=ALIASES[canonical] if mode=='rename' else canonical
        world.setdefault(canonical,{f:rng.choice(VALUES[f]) for f in FIELDS})
        f=rng.choice(FIELDS); nv=rng.choice([x for x in VALUES[f] if x!=world[canonical][f]])
        form=1 if mode=='alternate' else (2 if mode=='free_state' else 0)
        before=make_state(surface,world[canonical],form)
        if mode=='omitted': tmpl=rng.choice(OMIT[f])
        elif mode in ('held','paragraph','plan','rename','free_state'): tmpl=rng.choice(HELD[f])
        else: tmpl=rng.choice(COMMANDS[f])
        cmd=tmpl.format(o=surface,v=nv)
        if mode=='paragraph': cmd=' '.join(rng.choice(DIST) for _ in range(3))+'\n'+cmd
        if mode=='plan':
            alt=rng.choice([x for x in VALUES[f] if x not in (world[canonical][f],nv)])
            cmd=f'{surface}を{alt}にする案でした。{rng.choice(DIST)} 最終的には'+cmd
        world[canonical][f]=nv
        after=make_state(surface,world[canonical],form)
        future=f'次の観測でも{surface}の更新値は{nv}で、他の記録は保持されます。'
        out.append(Example(before,cmd,after,future,canonical,f,nv,mode,focus))
        focus=surface
    return out

@dataclass
class Rule:
    cmd_left:str; cmd_right:str; state_left:str; state_right:str
    transition_shape:tuple; support:int=1

@dataclass
class Anchor:
    preserve_sig:tuple; change_sig:tuple; rules:list; support:int=0; transport_ok:int=0; transport_bad:int=0
    def score(self): return (self.transport_ok+1)/(self.transport_ok+self.transport_bad+2)

class Model:
    def __init__(self,kind): self.kind=kind; self.rules=[]; self.anchors=[]; self.null_transports=0
    def _extract_rule(self,e):
        v=local_views(e.before,e.after)
        new=v['new']; i=e.command.find(new)
        if i<0 or not new: return None
        return Rule(e.command[max(0,i-8):i],e.command[i+len(new):i+len(new)+8],v['left'],v['right'],(len(v['old']),len(v['new']),len(v['prefix']),len(v['suffix'])))
    def _execute(self,state,cmd,r):
        i=cmd.find(r.cmd_left) if r.cmd_left else 0
        if i<0:return state,False
        s=i+len(r.cmd_left); en=cmd.find(r.cmd_right,s) if r.cmd_right else len(cmd)
        if en<s:return state,False
        val=cmd[s:en]
        j=state.find(r.state_left) if r.state_left else 0
        if j<0:return state,False
        ss=j+len(r.state_left); ee=state.find(r.state_right,ss) if r.state_right else len(state)
        if ee<ss:return state,False
        return state[:ss]+val+state[ee:],True
    def fit(self,examples):
        start=time.perf_counter(); self.rules=[]; self.anchors=[]
        for e in examples:
            r=self._extract_rule(e)
            if not r: continue
            self.rules.append(r)
            if self.kind=='surface': continue
            v=local_views(e.before,e.after)
            preserve=(len(v['prefix'])//4,len(v['suffix'])//4,tuple(sorted(grams(v['left']+v['right']).most_common(6))))
            change=(len(v['old']),len(v['new']),tuple(sorted(grams(v['old']+'>'+v['new']).most_common(6))))
            if self.kind=='anchor_no_bidir': key=(preserve,())
            else: key=(preserve,change)
            a=next((x for x in self.anchors if (x.preserve_sig,x.change_sig)==key),None)
            if a is None:
                a=Anchor(key[0],key[1],[]); self.anchors.append(a)
            a.rules.append(r); a.support+=1
        if self.kind!='surface':
            for a in self.anchors:
                for r in a.rules[:12]:
                    for e in examples[:48]:
                        pred,ok=self._execute(e.before,e.command,r)
                        if not ok: self.null_transports+=1; continue
                        before_back,ok2=self._reverse(pred,e.command,r,e.before)
                        exact=int(pred==e.after and ok2 and before_back==e.before)
                        preserve=int(self._preservation_ok(e.before,pred,e.after))
                        if exact and preserve: a.transport_ok+=1
                        else: a.transport_bad+=1
        self.rules=self.rules[-64:]; self.anchors=sorted(self.anchors,key=lambda a:(a.score(),a.support),reverse=True)[:32]
        self.training_seconds=time.perf_counter()-start
    def _reverse(self,pred,cmd,r,original):
        v=local_views(original,pred)
        if not v['new']: return pred,False
        return pred[:v['l']]+v['old']+(pred[len(pred)-v['r']:] if v['r'] else pred[v['l']+len(v['new']):]),True
    def _preservation_ok(self,before,pred,after):
        vb=local_views(before,after); vp=local_views(before,pred)
        return vb['prefix']==vp['prefix'] and vb['suffix']==vp['suffix']
    def predict(self,e):
        candidates=[]
        if self.kind=='surface': pool=[(0.0,r) for r in self.rules]
        else:
            pool=[]
            for a in self.anchors:
                if self.kind=='anchor_bidir' and a.score()<0.58: continue
                for r in a.rules:
                    pool.append((a.score()+0.01*a.support,r))
        for prior,r in pool:
            pred,ok=self._execute(e.before,e.command,r)
            if not ok: continue
            vv=local_views(e.before,pred)
            preservation=self._preservation_ok(e.before,pred,e.after)
            future=vv['new'] in e.future if vv['new'] else False
            score=prior+.45*int(preservation)+.25*int(future)+.2*cos(grams(e.command),grams(r.cmd_left+r.cmd_right))
            candidates.append((score,pred,r))
        if not candidates:return None,0
        candidates.sort(reverse=True,key=lambda x:x[0])
        if len(candidates)>1 and candidates[0][0]-candidates[1][0]<0.02:return None,len(candidates)
        return candidates[0][1],len(candidates)

def conditional_counterfactual(model,examples):
    covered=correct=0
    for i in range(0,len(examples)-1,2):
        a,b=examples[i],examples[i+1]
        pa,ca=model.predict(a); pb,cb=model.predict(b)
        if pa is None or pb is None: continue
        ea=model._extract_rule(a); eb=model._extract_rule(b)
        if not ea or not eb: continue
        ab1,ok1=model._execute(a.before,a.command,ea); ab2,ok2=model._execute(ab1,b.command,eb)
        ba1,ok3=model._execute(a.before,b.command,eb); ba2,ok4=model._execute(ba1,a.command,ea)
        if not all((ok1,ok2,ok3,ok4)): continue
        covered+=1
        expected_same=(a.field!=b.field or a.obj!=b.obj)
        correct+=int((ab2==ba2)==expected_same)
    return correct/max(1,covered),covered

def evaluate(seed,n,mode):
    train=[]
    for i in range(n): train.extend(make_dataset(seed+i,1,['seen','rename','alternate'][i%3]))
    test=make_dataset(seed+999,n//2,mode)
    out={}
    for kind in ('surface','anchor_no_bidir','anchor_bidir'):
        m=Model(kind); m.fit(train); t=time.perf_counter(); acc=null=cand=0
        for e in test:
            p,c=m.predict(e); cand+=c; null+=int(p is None); acc+=int(p==e.after)
        inf=(time.perf_counter()-t)*1000/max(1,len(test))
        cf,cov=conditional_counterfactual(m,test)
        out[kind]={'accuracy':acc/len(test),'null_rate':null/len(test),'mean_candidates':cand/len(test),'cf_accuracy_conditional':cf,'cf_coverage':cov/len(test),'rules':len(m.rules),'anchors':len(m.anchors),'anchor_members':sum(len(a.rules) for a in m.anchors),'transport_ok':sum(a.transport_ok for a in m.anchors),'transport_bad':sum(a.transport_bad for a in m.anchors),'null_transports':m.null_transports,'model_bytes':len(pickle.dumps(m)),'training_seconds':m.training_seconds,'inference_ms':inf}
    return out

def summarize(raw):
    s={}
    for n,runs in raw.items():
        s[n]={}
        for mode in MODES:
            s[n][mode]={}
            for kind in ('surface','anchor_no_bidir','anchor_bidir'):
                keys=runs[0][mode][kind]
                s[n][mode][kind]={k:statistics.mean(r[mode][kind][k] for r in runs) for k in keys}
    return s

MODES=('seen','held','alternate','rename','omitted','paragraph','plan','free_state')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_019.json');args=ap.parse_args()
    raw={}
    for n in (48,144,432):
        runs=[]
        for seed in (1,7,19): runs.append({m:evaluate(seed,n,m) for m in MODES})
        raw[str(n)]=runs
    payload={'hypothesis':'Latent State Anchors from Bidirectional Before/After Transport Residuals','seeds':[1,7,19],'sizes':[48,144,432],'raw':raw,'summary':summarize(raw),'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'fit O(PNG), transport audit O(APN G), inference O(APG), P<=64 A<=32','hidden_labels_used_by_learner':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(args.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload['summary']['432'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
