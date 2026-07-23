"""Track C Cycle 021: intervention footprint hyperedges.

Controlled falsification experiment. Learner sees only raw Japanese strings
(before, command, after, future) and episode order. Hidden object/relation/value
labels are evaluator-only. No external model, dictionary, ontology or RAG.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末","大型端末":"大きい端末","北側の鍵":"北のキー","南側の鍵":"南のキー","試料甲":"サンプル甲","試料乙":"サンプル乙"}
FIELDS=["場所","状態","担当"]
VALUES={"場所":["棚A","棚B","棚C","棚D"],"状態":["待機","処理中","完了","保留"],"担当":["担当一","担当二","担当三","担当四"]}
STATE_FORMS=["{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。","{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。"]
CMD={"場所":["{o}を{v}へ移してください。","{o}の保管先を{v}へ変更します。"],"状態":["{o}を{v}にしてください。","{o}の進行状態を{v}へ切り替えます。"],"担当":["{o}を{v}の担当にしてください。","{o}の受け持ちを{v}へ変更します。"]}
HELD={"場所":["対象{o}、次から{v}で保管。"],"状態":["対象{o}は以後{v}扱い。"],"担当":["{o}は{v}へ引き継ぎ。"]}
OMIT={"場所":["それを{v}へ移してください。"],"状態":["その対象を{v}にしてください。"],"担当":["担当は{v}へ変えてください。"]}
DIST=["別件の資料を確認しました。","前の案はいったん保留です。","この文は更新と無関係です。"]

@dataclass
class Ex:
    before:str; command:str; after:str; future:str
    obj:str; field:str; value:str; mode:str; focus:str

def grams(s:str)->Counter:
    s=''.join(s.split())
    return Counter(s[i:i+n] for n in (1,2,3) for i in range(max(0,len(s)-n+1)))

def cosine(a:Counter,b:Counter)->float:
    d=sum(v*b.get(k,0) for k,v in a.items()); na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return d/(na*nb+1e-12)

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

def state(o,d,form):
    return STATE_FORMS[form].format(o=o,loc=d['場所'],status=d['状態'],owner=d['担当'])

def make_stream(seed,n,mode):
    rng=random.Random(seed); world={}; out=[]; focus=''
    for _ in range(n):
        canonical=rng.choice(OBJECTS); surface=ALIASES[canonical] if mode=='rename' else canonical
        if canonical not in world: world[canonical]={f:rng.choice(VALUES[f]) for f in FIELDS}
        f=rng.choice(FIELDS); nv=rng.choice([v for v in VALUES[f] if v!=world[canonical][f]])
        form=1 if mode=='alternate' else 0
        before=state(surface,world[canonical],form)
        forms=OMIT[f] if mode=='omitted' else (HELD[f] if mode in ('held','paragraph','plan','counterfactual') else CMD[f])
        command=rng.choice(forms).format(o=surface,v=nv)
        if mode=='paragraph': command=' '.join(rng.choice(DIST) for _ in range(3))+'\n'+command
        if mode=='plan':
            oldplan=rng.choice([x for x in VALUES[f] if x not in (world[canonical][f],nv)])
            command=f"{surface}を{oldplan}にする案でした。{rng.choice(DIST)} 最終的には"+command
        world[canonical][f]=nv; after=state(surface,world[canonical],form)
        future=f"次の観測でも{surface}の更新結果は{nv}で、補助記録は維持されます。"
        if mode=='counterfactual': future=f"もし更新しなければ{surface}は以前の値のままです。実行時は{nv}です。"
        out.append(Ex(before,command,after,future,surface,f,nv,mode,focus)); focus=surface
    return out

@dataclass
class Rule:
    cmd_left:str; cmd_right:str; state_left:str; state_right:str
    cmd_shape:Counter; footprint:tuple; support:int=1; damage:int=0

class Model:
    def __init__(self,kind): self.kind=kind; self.rules=[]; self.hyper=[]; self.train_s=0
    def fit(self,examples):
        t=time.perf_counter()
        for ex in examples:
            l,r,old,new=diff(ex.before,ex.after)
            if not old or not new: continue
            pos=ex.command.find(new)
            if pos<0: continue
            cl=ex.command[max(0,pos-8):pos]; cr=ex.command[pos+len(new):pos+len(new)+8]
            sl=ex.before[max(0,l-8):l]; sr=(ex.before[len(ex.before)-r:len(ex.before)-r+8] if r else ex.before[l+len(old):l+len(old)+8])
            fp=(min(7,len(old)),min(7,len(new)),int(ex.before[:l]==ex.after[:l]),int((ex.before[-r:] if r else '')==(ex.after[-r:] if r else '')),int(new in ex.future))
            self.rules.append(Rule(cl,cr,sl,sr,grams(cl+'|'+cr),fp))
        self.rules=self.rules[-64:]
        if self.kind in ('footprint','compositional'):
            buckets=defaultdict(list)
            for i,r in enumerate(self.rules): buckets[r.footprint].append(i)
            self.hyper=[ids for ids in buckets.values() if len(ids)>=2][:32]
        self.train_s=time.perf_counter()-t
    def _extract(self,cmd,r):
        i=cmd.find(r.cmd_left) if r.cmd_left else 0
        if i<0:return None
        st=i+len(r.cmd_left); en=cmd.find(r.cmd_right,st) if r.cmd_right else len(cmd)
        if en<st:return None
        v=cmd[st:en]
        return v if 0<len(v)<=14 else None
    def _apply(self,before,cmd,r):
        v=self._extract(cmd,r)
        if v is None:return before,False
        i=before.find(r.state_left) if r.state_left else 0
        if i<0:return before,False
        st=i+len(r.state_left); en=before.find(r.state_right,st) if r.state_right else len(before)
        if en<st:return before,False
        return before[:st]+v+before[en:],True
    def predict(self,ex):
        cand=[]
        for idx,r in enumerate(self.rules):
            out,ok=self._apply(ex.before,ex.command,r)
            if not ok: continue
            score=cosine(grams(ex.command),r.cmd_shape)
            if self.kind in ('footprint','compositional'):
                group=max((g for g in self.hyper if idx in g),default=[])
                score += .08*min(4,len(group))
                score += .12*int(r.footprint[-1] and ('維持' in ex.future or '実行時' in ex.future))
            if self.kind=='compositional':
                score += .20*int('補助' in out and '維持' in out)
                score -= .30*int(out.count('補助')!=ex.before.count('補助'))
            cand.append((score,out,idx))
        if not cand:return ex.before,0,0
        cand.sort(reverse=True,key=lambda z:z[0])
        if len(cand)>1 and cand[0][0]-cand[1][0]<.015:return ex.before,len(cand),1
        return cand[0][1],len(cand),0

def evaluate(seed,n,mode):
    train=[]
    for k,m in enumerate(('seen','held','rename','alternate')): train+=make_stream(seed+31*k,n//4,m)
    test=make_stream(seed+999,n//4,mode)
    out={}
    for kind in ('surface','footprint','compositional'):
        model=Model(kind);model.fit(train)
        t=time.perf_counter();correct=wrong=null=cands=0
        for ex in test:
            pred,c,abst=model.predict(ex);cands+=c
            correct+=int(pred==ex.after);null+=int(abst or c==0);wrong+=int(pred!=ex.after and not (abst or c==0))
        dt=(time.perf_counter()-t)*1000/max(1,len(test))
        out[kind]={"accuracy":correct/len(test),"wrong_commit":wrong/len(test),"null_rate":null/len(test),"mean_candidates":cands/len(test),"rules":len(model.rules),"hyperedges":len(model.hyper),"model_bytes":len(pickle.dumps(model)),"training_seconds":model.train_s,"inference_ms":dt}
    return out

def counterfactual(seed,n):
    seq=make_stream(seed+500,n,'seen'); out={}
    for kind in ('surface','footprint','compositional'):
        m=Model(kind);m.fit(seq[:max(8,n//2)]); covered=correct=0
        for a,b in zip(seq[n//2:-1],seq[n//2+1:]):
            p1,c1,z1=m.predict(a)
            b2=Ex(p1,b.command,b.after,b.future,b.obj,b.field,b.value,b.mode,b.focus)
            p2,c2,z2=m.predict(b2)
            if c1 and c2 and not z1 and not z2:
                covered+=1;correct+=int(p2==b.after)
        out[kind]={"coverage":covered/max(1,len(seq[n//2:-1])),"accuracy_conditional":correct/max(1,covered)}
    return out

def summarize(raw):
    res={}
    for n,runs in raw.items():
        res[n]={}
        for mode in ('seen','held','rename','alternate','omitted','paragraph','plan','counterfactual'):
            res[n][mode]={}
            for kind in ('surface','footprint','compositional'):
                keys=runs[0][mode][kind]
                res[n][mode][kind]={k:statistics.mean(r[mode][kind][k] for r in runs) for k in keys}
        res[n]['sequential_counterfactual']={kind:{k:statistics.mean(run['sequential_counterfactual'][kind][k] for run in runs) for k in runs[0]['sequential_counterfactual'][kind]} for kind in ('surface','footprint','compositional')}
    return res

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_021.json');a=ap.parse_args()
    raw={}
    for n in (48,144,288):
        runs=[]
        for seed in (1,7,19):
            r={mode:evaluate(seed,n,mode) for mode in ('seen','held','rename','alternate','omitted','paragraph','plan','counterfactual')}
            r['sequential_counterfactual']=counterfactual(seed,max(24,n//3));runs.append(r)
        raw[str(n)]=runs
    payload={"hypothesis":"Stable Intervention Footprint Hyperedges with Non-Target-Preserving Effect Algebra","seeds":[1,7,19],"sizes":[48,144,288],"raw":raw,"summary":summarize(raw),"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"estimated_complexity":"fit O(NL), footprint grouping O(P), inference O(PG), P<=64","hidden_labels_used_by_learner":False,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(a.output,'w',encoding='utf-8') as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload['summary']['288'],ensure_ascii=False,indent=2))
if __name__=='__main__': main()
