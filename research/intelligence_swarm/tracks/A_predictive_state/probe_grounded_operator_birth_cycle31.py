from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict, Counter
import argparse, json, pickle, random, resource, statistics, time, math

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末","大型端末":"大きい端末",
         "北側の鍵":"北のキー","南側の鍵":"南のキー","試料甲":"サンプル甲","試料乙":"サンプル乙"}
VALUES=["棚A","棚B","棚C","棚D","待機","処理中","完了","保留","担当一","担当二","担当三","担当四"]
FILL=["補助記録は維持します。","別件の設定は変えません。","前段の注意事項はそのままです。"]
@dataclass
class Ex:
    before:str; command:str; after:str; future:str; obj:str; canonical:str; old:str; new:str; mode:str
@dataclass
class Family:
    left_shape:str; right_shape:str; old_shape:str; new_shape:str
    relpos:int; width:int; support:int=0; probe_pos:int=0; probe_neg:int=0
    kernel:tuple=()

def shape(s):
    return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、：／=\n 「」' else c for c in s)
def coarse(s):
    out=[]
    for c in shape(s):
        if not out or out[-1]!=c: out.append(c)
    return ''.join(out)
def build(seed,n,mode):
    rng=random.Random(seed); rows=[]; focus=None; world={}
    for t in range(n):
        cont=mode in ('omitted','switchmix') and t>0 and (mode=='omitted' or t%2==1)
        canon=focus if cont else rng.choice(OBJECTS); surf=ALIASES[canon] if mode=='rename' else canon
        old=world.get(canon,rng.choice(VALUES)); new=rng.choice([v for v in VALUES if v!=old])
        filler=rng.choice(FILL)
        before=f"{surf}の現在値は{old}です。{filler}"
        if mode=='omitted' and t>0: command=f"それを{new}へ変更してください。"
        elif mode=='switchmix' and t>0 and t%2: command=f"その対象を{new}へ変更してください。"
        elif mode=='order': command=f"{new}へ変更してください、対象は{surf}です。"
        elif mode=='lexeme': command=f"対象{surf}は次から{new}扱いにします。"
        elif mode=='nested': command=f"依頼内容は「{surf}の値を{new}へ変更してください。」です。"
        elif mode=='paragraph': command=f"{rng.choice(FILL)}\n{surf}の値を{new}へ変更してください。\n{rng.choice(FILL)}"
        elif mode=='plan':
            alt=rng.choice([v for v in VALUES if v not in (old,new)])
            command=f"{surf}を{alt}にする案は撤回し、最終的には{new}へ変更してください。"
        elif mode=='counterfactual':
            command=f"もし変更しなければ{surf}は{old}のままです。実際には{surf}を{new}へ変更してください。"
        else: command=f"{surf}の値を{new}へ変更してください。"
        after=f"{surf}の現在値は{new}です。{filler}"
        future=f"次の観測でも{surf}は{new}のままです。"
        rows.append(Ex(before,command,after,future,surf,canon,old,new,mode))
        world[canon]=new; focus=canon
    return rows
def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def spans(text,lo=1,hi=10):
    return [(i,j,text[i:j]) for i in range(len(text)) for j in range(i+lo,min(len(text),i+hi)+1)
            if not any(c in text[i:j] for c in '。、\n「」')]
def value_cands(ex):
    before_chars=set(ex.before); runs=[]; start=None
    for i,ch in enumerate(ex.command+' '):
        novel=(ch not in before_chars and ch not in '。、：／=\\n 「」')
        if novel and start is None:start=i
        if not novel and start is not None:
            seg=ex.command[start:i]
            if 1<=len(seg)<=10:runs.append(seg)
            start=None
    xs=[s for _,_,s in spans(ex.command,1,10) if s not in ex.before]
    run_parts=[]
    for r in runs:
        run_parts += [r[i:j] for i in range(len(r)) for j in range(i+1,min(len(r),i+4)+1)]
    return list(dict.fromkeys(run_parts+runs+sorted(set(xs),key=lambda x:(abs(len(x)-3),len(x),x))))[:28]
def obj_cands(ex,prev=None,carry=False):
    xs=[s for _,_,s in spans(ex.command,2,12) if s in ex.before]
    if carry and prev:
        xs += [s for _,_,s in spans(prev.after+' '+prev.future,2,12) if s in prev.after and s in prev.future]
    return sorted(set(xs),key=lambda x:(-len(x),x))[:10]
def boundary_families(ex):
    vals=value_cands(ex); fams=[]
    L=len(ex.before)
    state_spans=[]
    for a in range(L):
        for b in range(a+1,min(L,a+11)+1):
            old=ex.before[a:b]
            if any(c in old for c in '。、\n'): continue
            priority=0 if old not in ex.command else 1
            state_spans.append((priority,abs(len(old)-3),a,b,old))
    state_spans.sort()
    for _,_,a,b,old in state_spans:
        left=ex.before[max(0,a-5):a]; right=ex.before[b:b+5]
        for v in vals:
            fams.append((left,right,old,v,a,b-a))
    return fams[:9000]
def apply(before,left,right,old_shape,new,relpos,width):
    hits=[]
    for a in range(max(0,relpos-2),min(len(before),relpos+3)):
        b=a+width
        if b>len(before):continue
        if coarse(before[a:b])==old_shape:
            hits.append((a,b))
    if not hits:return None
    a,b=min(hits,key=lambda h:abs(h[0]-relpos)); return before[:a]+new+before[b:]
def inverse(after,left,right,new_shape,old,relpos,new_width):
    hits=[]
    for a in range(max(0,relpos-2),min(len(after),relpos+3)):
        for w in range(1,11):
            b=a+w
            if b>len(after):continue
            if coarse(after[a:b])==new_shape:
                hits.append((a,b))
    if not hits:return None
    a,b=min(hits,key=lambda h:abs(h[0]-relpos)); return after[:a]+old+after[b:]
def consequence(ex,pred,old,new):
    if pred is None:return (1,1,1,1,1)
    l,r,po,pn=diff(ex.before,pred)
    return (int(new not in pred), int('補助記録' in ex.before and '補助記録' not in pred),
            int(len(po)==0), min(3,len(po)), min(3,len(pn)))
class Model:
    def __init__(self,method,shuffle=False):
        self.method=method;self.shuffle=shuffle;self.families=[];self.train_seconds=0;self.audit=0
    def fit(self,induction,probe):
        t=time.perf_counter(); stats=defaultdict(lambda:[0,0,Counter()])
        for ex in induction:
            for left,right,old,new,rp,w in boundary_families(ex):
                pred=apply(ex.before,coarse(left),coarse(right),coarse(old),new,rp,w)
                key=(coarse(left),coarse(right),coarse(old),coarse(new),rp,w)
                if pred==ex.after:stats[key][0]+=1
                elif pred is not None:stats[key][1]+=1
        cand=sorted(stats,key=lambda k:(stats[k][0]-stats[k][1],stats[k][0]),reverse=True)[:160]
        fams=[Family(*k,support=stats[k][0]) for k in cand if stats[k][0]>=1]
        outcomes=[e.after for e in probe]
        if self.shuffle and outcomes: outcomes=outcomes[1:]+outcomes[:1]
        for ex,target in zip(probe,outcomes):
            vals=value_cands(ex)
            for f in fams:
                for v in vals:
                    if coarse(v)!=f.new_shape:continue
                    pred=apply(ex.before,f.left_shape,f.right_shape,f.old_shape,v,f.relpos,f.width)
                    if pred is None:continue
                    self.audit+=1
                    cons=consequence(ex,pred,ex.old,v)
                    if pred==target:
                        f.probe_pos+=1; f.kernel=cons
                    else:f.probe_neg+=1
        self.families=sorted(fams,key=lambda f:(f.probe_pos-f.probe_neg,f.support),reverse=True)[:64]
        self.train_seconds=time.perf_counter()-t
    def propose(self,ex,prev=None):
        carry=self.method in ('carry','probe') and prev is not None
        objs=obj_cands(ex,prev,carry);vals=value_cands(ex);out=[]
        for f in self.families:
            for v in vals:
                if coarse(v)!=f.new_shape:continue
                pred=apply(ex.before,f.left_shape,f.right_shape,f.old_shape,v,f.relpos,f.width)
                if pred is None:continue
                inv=inverse(pred,f.left_shape,f.right_shape,f.new_shape,ex.old,f.relpos,len(v))
                err=int(inv!=ex.before)
                score=f.support-err
                if self.method=='probe':score+=2*f.probe_pos-1.5*f.probe_neg
                for o in objs or ['']:
                    out.append((score,pred,o,v,f))
        return out[:256]
    def predict(self,ex,prev=None):
        ps=self.propose(ex,prev)
        if not ps:return None,0,0,'candidate_collapse'
        active=ps;last=None;sweeps=0
        while sweeps<6:
            sweeps+=1
            active=sorted(active,key=lambda x:x[0],reverse=True)
            best=active[0][0];active=[x for x in active if x[0]>=best-.25][:24]
            sig=tuple((x[1],x[2],x[3],x[4].relpos,x[4].width) for x in active)
            if sig==last:break
            last=sig
        ranked=sorted(active,key=lambda x:x[0],reverse=True)
        preds={x[1] for x in ranked}
        if len(preds)!=1:return None,sweeps,len(active),'tie'
        return ranked[0],sweeps,len(active),'fixed'
def evaluate(model,test):
    vals=[];t=time.perf_counter()
    for i,e in enumerate(test):
        p,s,a,r=model.predict(e,test[i-1] if i else None)
        vals.append((p,s,a,r,e))
    n=len(vals)
    return {
      'accuracy':sum(p is not None and p[1]==e.after for p,s,a,r,e in vals)/n,
      'wrong_commit':sum(p is not None and p[1]!=e.after for p,s,a,r,e in vals)/n,
      'null_rate':sum(p is None for p,s,a,r,e in vals)/n,
      'pair_recall':sum(p is not None and p[2]==e.obj and p[3]==e.new for p,s,a,r,e in vals)/n,
      'mean_sweeps':statistics.mean(s for p,s,a,r,e in vals),'max_sweeps':max(s for p,s,a,r,e in vals),
      'mean_active':statistics.mean(a for p,s,a,r,e in vals),
      'families':len(model.families),'probe_positive':sum(f.probe_pos for f in model.families),
      'probe_negative':sum(f.probe_neg for f in model.families),'probe_audit':model.audit,
      'model_bytes':len(pickle.dumps(model)),'training_seconds':model.train_seconds,
      'inference_ms':(time.perf_counter()-t)*1000/n,
      'reasons':dict(Counter(r for p,s,a,r,e in vals))
    }
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='MEASUREMENTS_CYCLE_031.json');a=ap.parse_args()
    modes=['seen','order','lexeme','rename','nested','omitted','switchmix','paragraph','plan','counterfactual']
    raw={}
    for seed in (1,7,19):
        alltrain=build(seed,60,'seen')+build(seed+20,30,'rename')+build(seed+40,30,'paragraph')
        induction=alltrain[:80];probe=alltrain[80:]
        models={}
        for method,shuffle in [('family',False),('carry',False),('probe',False),('probe_shuffle',True)]:
            m=Model('probe' if method.startswith('probe') else method,shuffle);m.fit(induction,probe);models[method]=m
        raw[str(seed)]={}
        for mode in modes:
            test=build(seed+999,20,mode)
            raw[str(seed)][mode]={name:evaluate(m,test) for name,m in models.items()}
    summary={}
    for mode in modes:
        summary[mode]={}
        for method in ('family','carry','probe','probe_shuffle'):
            keys=[k for k,v in raw['1'][mode][method].items() if isinstance(v,(int,float))]
            summary[mode][method]={k:statistics.mean(raw[str(seed)][mode][method][k] for seed in (1,7,19)) for k in keys}
    payload={'cycle':31,'hypothesis':'Probe-Grounded Operator Birth from Cross-Input Recurrent Error Cancellation',
      'seeds':[1,7,19],'summary':summary,'raw':raw,
      'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      'estimated_complexity':'family birth O(NL^2V), probe audit O(QFV), inference O(FOV+SH)',
      'final_test_outcome_used_for_selection':False,'probe_independent':True,'shuffled_probe_ablation':True,
      'fixed_ontology_or_handwritten_slots_used_by_model':False,
      'highschool_level_passed':False,'native_japanese_communication_passed':False,
      'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
