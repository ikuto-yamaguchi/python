"""Track C Cycle 022: executable effect hypergraphs from contrastive transition transport.
Controlled falsification experiment. Learner sees only raw Japanese strings and order.
Hidden object/field/value labels are evaluator-only.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse,json,math,pickle,random,resource,statistics,time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
FIELDS=['場所','状態','担当']
VALUES={'場所':['棚A','棚B','棚C','棚D'],'状態':['待機','処理中','完了','保留'],'担当':['担当一','担当二','担当三','担当四']}
STATE_FORMS=['{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。','{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。']
CMD={'場所':['{o}を{v}へ移してください。','{o}の保管先を{v}へ変更します。'],'状態':['{o}を{v}にしてください。','{o}の進行状態を{v}へ切り替えます。'],'担当':['{o}を{v}の担当にしてください。','{o}の受け持ちを{v}へ変更します。']}
HELD={'場所':['対象{o}、次から{v}で保管。'],'状態':['対象{o}は以後{v}扱い。'],'担当':['{o}は{v}へ引き継ぎ。']}
OMIT={'場所':['それを{v}へ移してください。'],'状態':['その対象を{v}にしてください。'],'担当':['担当は{v}へ変えてください。']}
DIST=['別件の資料を確認しました。','前の案はいったん保留です。','この文は更新と無関係です。']

@dataclass
class Ex:
    before:str; command:str; after:str; future:str
    obj:str; field:str; value:str; mode:str; focus:str

def grams(s):
    s=''.join(s.split())
    return Counter(s[i:i+n] for n in (1,2,3) for i in range(max(0,len(s)-n+1)))
def cosine(a,b):
    d=sum(v*b.get(k,0) for k,v in a.items());na=math.sqrt(sum(v*v for v in a.values()));nb=math.sqrt(sum(v*v for v in b.values()))
    return d/(na*nb+1e-12)
def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def state(o,d,form):return STATE_FORMS[form].format(o=o,loc=d['場所'],status=d['状態'],owner=d['担当'])
def make_stream(seed,n,mode):
    rng=random.Random(seed);world={};out=[];focus=''
    for _ in range(n):
        c=rng.choice(OBJECTS);o=ALIASES[c] if mode=='rename' else c
        world.setdefault(c,{f:rng.choice(VALUES[f]) for f in FIELDS})
        f=rng.choice(FIELDS);nv=rng.choice([v for v in VALUES[f] if v!=world[c][f]])
        form=1 if mode=='alternate' else 0
        before=state(o,world[c],form)
        forms=OMIT[f] if mode=='omitted' else (HELD[f] if mode in ('held','paragraph','plan','counterfactual') else CMD[f])
        command=rng.choice(forms).format(o=o,v=nv)
        if mode=='paragraph':command=' '.join(rng.choice(DIST) for _ in range(3))+'\n'+command
        if mode=='plan':
            old=rng.choice([x for x in VALUES[f] if x not in (world[c][f],nv)])
            command=f'{o}を{old}にする案でした。{rng.choice(DIST)} 最終的には'+command
        world[c][f]=nv;after=state(o,world[c],form)
        future=f'次の観測でも{o}の更新結果は{nv}で、補助記録は維持されます。'
        if mode=='counterfactual':future=f'もし更新しなければ{o}は以前の値のままです。実行時は{nv}です。'
        out.append(Ex(before,command,after,future,o,f,nv,mode,focus));focus=o
    return out

@dataclass
class Rule:
    cl:str;cr:str;sl:str;sr:str;cmd_sig:Counter;state_sig:Counter
    support:int=1;success:int=0;wrong:int=0;null:int=0;fp:tuple=()

class Model:
    def __init__(self,kind):self.kind=kind;self.rules=[];self.hyper=[];self.train_s=0
    def fit(self,examples):
        t=time.perf_counter()
        for ex in examples:
            l,r,old,new=diff(ex.before,ex.after)
            if not old or not new:continue
            p=ex.command.find(new)
            if p<0:continue
            cl=ex.command[max(0,p-8):p];cr=ex.command[p+len(new):p+len(new)+8]
            sl=ex.before[max(0,l-8):l];sr=ex.before[len(ex.before)-r:len(ex.before)-r+8] if r else ex.before[l+len(old):l+len(old)+8]
            fp=(min(8,len(old)),min(8,len(new)),int('補助' in ex.before and '補助' in ex.after),int(new in ex.future))
            self.rules.append(Rule(cl,cr,sl,sr,grams(cl+'|'+cr),grams(sl+'|'+sr),fp=fp))
        self.rules=self.rules[-64:]
        for rule in self.rules:
            for ex in examples:
                out,ok=self._apply(ex.before,ex.command,rule)
                if not ok:rule.null+=1
                elif out==ex.after:rule.success+=1
                else:rule.wrong+=1
        if self.kind=='hypergraph':
            buckets=defaultdict(list)
            for i,r in enumerate(self.rules):
                if r.success>=2 and r.success/(r.success+r.wrong+1)>=0.45:
                    key=(r.fp, round(r.success/(r.success+r.wrong+1),1))
                    buckets[key].append(i)
            self.hyper=[v for v in buckets.values() if len(v)>=2][:24]
        self.train_s=time.perf_counter()-t
    def _extract(self,cmd,r):
        i=cmd.find(r.cl) if r.cl else 0
        if i<0:return None
        st=i+len(r.cl);en=cmd.find(r.cr,st) if r.cr else len(cmd)
        if en<st:return None
        v=cmd[st:en]
        return v if 0<len(v)<=14 else None
    def _apply(self,before,cmd,r):
        v=self._extract(cmd,r)
        if v is None:return before,False
        i=before.find(r.sl) if r.sl else 0
        if i<0:return before,False
        st=i+len(r.sl);en=before.find(r.sr,st) if r.sr else len(before)
        if en<st:return before,False
        return before[:st]+v+before[en:],True
    def predict(self,ex):
        cand=[]
        for i,r in enumerate(self.rules):
            out,ok=self._apply(ex.before,ex.command,r)
            if not ok:continue
            base=.55*cosine(grams(ex.command),r.cmd_sig)+.45*cosine(grams(ex.before),r.state_sig)
            if self.kind in ('transport','hypergraph'):
                total=r.success+r.wrong
                reliability=(r.success+1)/(total+2)
                base+=.35*reliability-.25*(r.wrong/(total+1))
            if self.kind=='hypergraph':
                g=next((g for g in self.hyper if i in g),[])
                base+=.08*min(4,len(g))
                base+=.12*int(r.fp[2] and '補助' in out and '維持' in out)
            cand.append((base,out,i))
        if not cand:return ex.before,0,1
        cand.sort(reverse=True,key=lambda x:x[0])
        if len(cand)>1 and cand[0][0]-cand[1][0]<.02:return ex.before,len(cand),1
        return cand[0][1],len(cand),0

def evaluate(seed,n,mode):
    train=[]
    for k,m in enumerate(('seen','held','rename','alternate')):train+=make_stream(seed+31*k,n//4,m)
    test=make_stream(seed+999,max(8,n//6),mode);out={}
    for kind in ('surface','transport','hypergraph'):
        m=Model(kind);m.fit(train);t=time.perf_counter();correct=wrong=null=cands=0
        for ex in test:
            pred,c,z=m.predict(ex);cands+=c;correct+=int(pred==ex.after);null+=int(z);wrong+=int(pred!=ex.after and not z)
        out[kind]={'accuracy':correct/len(test),'wrong_commit':wrong/len(test),'null_rate':null/len(test),'mean_candidates':cands/len(test),'rules':len(m.rules),'hyperedges':len(m.hyper),'transport_success':sum(r.success for r in m.rules),'transport_wrong':sum(r.wrong for r in m.rules),'transport_null':sum(r.null for r in m.rules),'model_bytes':len(pickle.dumps(m)),'training_seconds':m.train_s,'inference_ms':(time.perf_counter()-t)*1000/len(test)}
    return out

def sequential(seed,n):
    seq=make_stream(seed+700,n,'seen');out={}
    for kind in ('surface','transport','hypergraph'):
        m=Model(kind);m.fit(seq[:n//2]);cov=correct=0
        for a,b in zip(seq[n//2:-1],seq[n//2+1:]):
            p1,c1,z1=m.predict(a);b2=Ex(p1,b.command,b.after,b.future,b.obj,b.field,b.value,b.mode,b.focus);p2,c2,z2=m.predict(b2)
            if c1 and c2 and not z1 and not z2:cov+=1;correct+=int(p2==b.after)
        out[kind]={'coverage':cov/max(1,len(seq[n//2:-1])),'accuracy_conditional':correct/max(1,cov)}
    return out

def summarize(raw):
    out={}
    for n,runs in raw.items():
        out[n]={}
        for mode in ('seen','held','rename','alternate','omitted','paragraph','plan','counterfactual'):
            out[n][mode]={}
            for kind in ('surface','transport','hypergraph'):
                out[n][mode][kind]={k:statistics.mean(r[mode][kind][k] for r in runs) for k in runs[0][mode][kind]}
        out[n]['sequential']={kind:{k:statistics.mean(r['sequential'][kind][k] for r in runs) for k in runs[0]['sequential'][kind]} for kind in ('surface','transport','hypergraph')}
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_022.json');a=ap.parse_args();raw={}
    for n in (48,144,288):
        runs=[]
        for seed in (1,7,19):
            r={mode:evaluate(seed,n,mode) for mode in ('seen','held','rename','alternate','omitted','paragraph','plan','counterfactual')};r['sequential']=sequential(seed,max(24,n//3));runs.append(r)
        raw[str(n)]=runs
    payload={'hypothesis':'Executable Effect Hypergraphs from Contrastive Transition Transport','seeds':[1,7,19],'sizes':[48,144,288],'raw':raw,'summary':summarize(raw),'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'fit O(PN G), transport audit O(PN G), inference O(PG), P<=64','hidden_labels_used_by_learner':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload['summary']['288'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
