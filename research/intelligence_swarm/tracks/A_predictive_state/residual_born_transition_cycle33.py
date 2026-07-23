from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse,json,pickle,random,resource,statistics,time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
VALUES=['棚A','棚B','棚C','棚D','待機','処理中','完了','保留','担当一','担当二','担当三','担当四']
FILL=['補助記録は維持します。','別件の設定は変えません。','前段の注意事項はそのままです。']

@dataclass
class Turn:
    before:str; command:str; after:str; future:str; obj:str; canon:str; value:str; old:str; mode:str
@dataclass(frozen=True)
class Kernel:
    sb:int; sw:int; cb:int; cw:int; oldshape:str; newshape:str

def shape(s):
    return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、：／=\n 「」' else c for c in s)

def make(seed,n,mode):
    r=random.Random(seed); focus=None; world={}; out=[]
    for i in range(n):
        cont=mode in ('omitted','switchmix') and i>0 and (mode=='omitted' or i%2==1)
        canon=focus if cont else r.choice(OBJECTS); obj=ALIASES[canon] if mode=='rename' else canon
        old=world.get(canon,r.choice(VALUES)); new=r.choice([x for x in VALUES if x!=old])
        before=f'{obj}の現在値は{old}です。{r.choice(FILL)}'
        if mode=='omitted' and i>0: cmd=f'それを{new}へ変更してください。'
        elif mode=='switchmix' and i>0 and i%2==1: cmd=f'その対象を{new}へ変更してください。'
        elif mode=='order': cmd=f'{new}へ変更してください、対象は{obj}です。'
        elif mode=='lexeme': cmd=f'対象{obj}は次から{new}扱いにします。'
        elif mode=='nested': cmd=f'依頼内容は「{obj}の値を{new}へ変更してください。」です。'
        elif mode=='paragraph': cmd=f'{r.choice(FILL)}\n{obj}の値を{new}へ変更してください。\n{r.choice(FILL)}'
        elif mode=='plan':
            alt=r.choice([x for x in VALUES if x not in (old,new)]); cmd=f'{obj}を{alt}にする案は撤回し、最終的には{new}へ変更してください。'
        elif mode=='counterfactual': cmd=f'もし変更しなければ{obj}は{old}のままです。実際には{obj}を{new}へ変更してください。'
        else: cmd=f'{obj}の値を{new}へ変更してください。'
        after=f'{obj}の現在値は{new}です。{r.choice(FILL)}'; future=f'次の観測でも{obj}は{new}のままです。'
        out.append(Turn(before,cmd,after,future,obj,canon,new,old,mode)); world[canon]=new; focus=canon
    return out

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    rr=0
    while rr<min(len(a)-l,len(b)-l) and a[-1-rr]==b[-1-rr]: rr+=1
    return l,rr,a[l:len(a)-rr if rr else len(a)],b[l:len(b)-rr if rr else len(b)]

def spans(t,lo=1,hi=12):
    return [(i,j,t[i:j]) for i in range(len(t)) for j in range(i+lo,min(len(t),i+hi)+1) if not any(c in t[i:j] for c in '。、\n「」')]

def candidates(turn,prev=None,carry=False):
    common=[(i,j,s) for i,j,s in spans(turn.command,2,12) if s in turn.before]
    objs=sorted({s for _,_,s in common},key=lambda x:(-len(x),x))[:6]
    if carry and prev:
        objs += sorted({s for _,_,s in spans(prev.future,2,12) if s in prev.after},key=lambda x:(-len(x),x))[:5]
    vals=sorted({s for _,_,s in spans(turn.command,1,10) if s not in turn.before},key=lambda x:(-len(x),x))[:8]
    return list(dict.fromkeys(objs)),vals

def apply(before,val,k):
    s=max(0,min(len(before),round(k.sb*len(before)/8))); e=max(s,min(len(before),s+k.sw))
    if shape(before[s:e])!=k.oldshape:return None
    return before[:s]+val+before[e:]

def edit_distance(a,b):
    prev=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        cur=[i]
        for j,y in enumerate(b,1):cur.append(min(cur[-1]+1,prev[j]+1,prev[j-1]+(x!=y)))
        prev=cur
    return prev[-1]

class Model:
    def __init__(self,mode):self.mode=mode;self.kernels=[];self.edges=set();self.births=0;self.probe_audits=0;self.train_s=0
    def induce(self,rows):
        c=Counter()
        for t in rows:
            l,r,old,new=diff(t.before,t.after); p=t.command.find(new)
            if not old or p<0:continue
            k=Kernel(round(8*l/max(1,len(t.before))),len(old),round(8*p/max(1,len(t.command))),len(new),shape(old),shape(new));c[k]+=1
        self.kernels=[k for k,n in c.most_common(32) if n>=2]
    def repair_from_probe(self,probe,shuffle=False):
        born=Counter(); kept=[]
        targets=[x.after for x in probe]
        if shuffle: targets=targets[1:]+targets[:1]
        for t,target in zip(probe,targets):
            os,vs=candidates(t); base=[]
            for k in self.kernels:
                for v in vs:
                    pred=apply(t.before,v,k)
                    if pred is not None:base.append((edit_distance(pred,target),k,v,pred))
            self.probe_audits+=len(base)
            if not base:continue
            base.sort(key=lambda x:x[0]); d,k,v,pred=base[0]
            if pred==target: kept.append(k);continue
            for ds in (-1,0,1):
              for dw in (-1,0,1):
               for dc in (-1,0,1):
                nk=Kernel(max(0,min(7,k.sb+ds)),max(1,k.sw+dw),max(0,min(7,k.cb+dc)),k.cw,k.oldshape,k.newshape)
                np=apply(t.before,v,nk)
                if np is not None and edit_distance(np,target)<d:born[nk]+=1
        if self.mode=='prune': self.kernels=list(dict.fromkeys(kept))[:32]
        elif self.mode in ('birth','shuffle'):
            new=[k for k,n in born.items() if n>=2]
            self.births=len(new); self.kernels=list(dict.fromkeys(self.kernels+new))[:64]
            for a in self.kernels:
                for b in self.kernels:
                    if a!=b and abs(a.sb-b.sb)+abs(a.sw-b.sw)<=1:self.edges.add((a,b))
    def fit(self,ind,probe):
        st=time.perf_counter();self.induce(ind)
        if self.mode=='prune':self.repair_from_probe(probe,False)
        elif self.mode=='birth':self.repair_from_probe(probe,False)
        elif self.mode=='shuffle':self.repair_from_probe(probe,True)
        self.train_s=time.perf_counter()-st
    def predict(self,t,prev=None):
        os,vs=candidates(t,prev,self.mode in ('carry','birth','shuffle')); props=[]
        for k in self.kernels:
            for o in os or ['']:
                for v in vs:
                    p=apply(t.before,v,k)
                    if p is None:continue
                    score=-(0 if v in t.command else 2)-(0 if not o or o in t.command or o in t.before else 2)
                    score+=sum(0.15 for a,b in self.edges if a==k)
                    props.append((score,p,o,v,k))
        if not props:return None,0,0
        active=props[:]; prevsig=None;s=0
        while s<6:
            s+=1;active.sort(reverse=True,key=lambda x:x[0]);best=active[0][0];active=[x for x in active if x[0]>=best-.2][:8]
            sig=tuple((x[1],x[2],x[3]) for x in active)
            if sig==prevsig:break
            prevsig=sig
        if len(active)>1 and active[0][0]-active[1][0]<.4:return None,s,len(active)
        return active[0],s,len(active)

def eval_mode(seed,mode):
    train=[]
    for j,m in enumerate(('seen','rename','paragraph','plan','switchmix')):train+=make(seed+j,18,m)
    cut=int(len(train)*.72);ind,probe=train[:cut],train[cut:]
    test=make(seed+999,12,mode);out={}
    for method in ('base','carry','prune','birth','shuffle'):
        M=Model(method);M.fit(ind,probe);res=[];st=time.perf_counter()
        for i,t in enumerate(test):
            pred,sw,act=M.predict(t,test[i-1] if i else None)
            res.append((pred is not None and pred[1]==t.after,pred is not None and pred[1]!=t.after,pred is None,
                        pred is not None and pred[2]==t.obj and pred[3]==t.value,sw,act))
        out[method]={
          'accuracy':statistics.mean(x[0] for x in res),'wrong':statistics.mean(x[1] for x in res),'null':statistics.mean(x[2] for x in res),
          'pair_recall':statistics.mean(x[3] for x in res),'mean_sweeps':statistics.mean(x[4] for x in res),'max_sweeps':max(x[4] for x in res),
          'mean_active':statistics.mean(x[5] for x in res),'kernels':len(M.kernels),'births':M.births,'edges':len(M.edges),
          'probe_audits':M.probe_audits,'model_bytes':len(pickle.dumps(M)),'training_seconds':M.train_s,
          'inference_ms':(time.perf_counter()-st)*1000/len(test)}
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='MEASUREMENTS_CYCLE_033.json');a=ap.parse_args()
    modes=('seen','order','lexeme','rename','nested','omitted','switchmix','paragraph','plan','counterfactual')
    raw={str(s):{m:eval_mode(s,m) for m in modes} for s in (1,7,19)};summary={}
    for m in modes:
      summary[m]={}
      for method in ('base','carry','prune','birth','shuffle'):
       summary[m][method]={k:statistics.mean(raw[str(s)][m][method][k] for s in (1,7,19)) for k in raw['1'][m][method]}
    payload={'cycle':33,'hypothesis':'Residual-Born Transition Kernels from Probe-Localized Error Transport','seeds':[1,7,19],
      'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      'complexity':'induction O(NL), probe residual O(QKVL^2), topology O(K^2), inference O(KOV+SH)',
      'final_test_outcome_used_for_ranking':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
