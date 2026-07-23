from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
import argparse,json,pickle,random,resource,statistics,time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
FIELDS=['場所','状態','担当']
VALUES={'場所':['棚A','棚B','棚C','棚D'],'状態':['待機','処理中','完了','保留'],'担当':['担当一','担当二','担当三','担当四']}
S0='{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。'
S1='{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。'
CMD={'場所':['{o}を{v}へ移してください。','{o}の保管先を{v}へ変更します。'],'状態':['{o}を{v}にしてください。','{o}の進行状態を{v}へ切り替えます。'],'担当':['{o}を{v}の担当にしてください。','{o}の受け持ちを{v}へ変更します。']}
HELD={'場所':['対象{o}は次から{v}で保管。'],'状態':['対象{o}は以後{v}扱い。'],'担当':['{o}は{v}へ引き継ぎ。']}
OMIT={'場所':['それを{v}へ移してください。'],'状態':['その対象を{v}にしてください。'],'担当':['担当は{v}へ変えてください。']}
DIST=['別件の説明です。','前案は保留です。','補助記録は変更しません。']

@dataclass
class Ex:
    before:str; command:str; after:str; future:str
    obj:str; field:str; old:str; new:str; mode:str

@dataclass
class Program:
    cl:str; cr:str; sl:str; sr:str; old_shape:str; new_shape:str
    support:int=1; wrong:int=0

@dataclass
class Adapter:
    program:int; cmd_ld:int; cmd_rd:int; state_ld:int; state_rd:int
    support:int=0; wrong:int=0; envs:tuple=()

def shape(s):
    return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、／=：:\n ' else c for c in s)

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

def state(o,d,form):
    return (S1 if form else S0).format(o=o,loc=d['場所'],status=d['状態'],owner=d['担当'])

def build(seed,n,mode):
    rng=random.Random(seed); world={}; out=[]
    for _ in range(n):
        canon=rng.choice(OBJECTS); o=ALIASES[canon] if mode=='rename' else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS})
        f=rng.choice(FIELDS); old=world[canon][f]; new=rng.choice([x for x in VALUES[f] if x!=old])
        form=1 if mode=='alternate' else 0; before=state(o,world[canon],form)
        forms=OMIT[f] if mode=='omitted' else HELD[f] if mode in ('held','paragraph','plan','counterfactual') else CMD[f]
        command=rng.choice(forms).format(o=o,v=new)
        if mode=='paragraph': command=' '.join(rng.choice(DIST) for _ in range(4))+'\n'+command
        if mode=='plan':
            reject=rng.choice([x for x in VALUES[f] if x not in (old,new)])
            command=f'{o}を{reject}にする案は撤回します。最終的には'+command
        if mode=='counterfactual': command=f'もし変更しなければ{o}は{old}のままです。実際には'+command
        world[canon][f]=new; after=state(o,world[canon],form)
        future=f'次の観測でも{o}の更新結果は{new}で、補助記録は維持されます。'
        out.append(Ex(before,command,after,future,o,f,old,new,mode))
    return out

def crop_context(text,pos,val_len,w=8):
    return text[max(0,pos-w):pos],text[pos+val_len:pos+val_len+w]

def locate(text,left,right,ld=0,rd=0):
    l=left[ld:] if ld<len(left) else ''
    r=right[:-rd] if rd and rd<len(right) else right if not rd else ''
    hits=[]; p=0
    while True:
        i=text.find(l,p) if l else p
        if i<0: break
        a=i+len(l); b=text.find(r,a) if r else len(text)
        if b>=a: hits.append((a,b))
        p=i+1
        if not l or p>=len(text): break
    return hits[0] if len(hits)==1 else None

class Model:
    def __init__(self,kind):
        self.kind=kind; self.programs=[]; self.adapters=[]; self.train_s=0

    def fit(self,train):
        started=time.perf_counter(); d={}
        for e in train:
            l,r,old,new=diff(e.before,e.after); p=e.command.find(new)
            if not old or not new or p<0: continue
            cl,cr=crop_context(e.command,p,len(new))
            sl=e.before[max(0,l-8):l]
            sr=e.before[len(e.before)-r:len(e.before)-r+8] if r else ''
            k=(cl,cr,sl,sr,shape(old),shape(new))
            if k in d: d[k].support+=1
            else: d[k]=Program(*k)
        self.programs=sorted(d.values(),key=lambda x:x.support,reverse=True)[:32]

        # Adapter proposals use only target before/command. Target outcome is consulted only after proposal for audit.
        evidence=defaultdict(lambda:[0,0,set()])
        for env in ('seen','held','rename','alternate'):
            for e in [x for x in train if x.mode==env]:
                for pi,p in enumerate(self.programs):
                    for cld in range(min(2,len(p.cl))+1):
                      for crd in range(min(2,len(p.cr))+1):
                        cp=locate(e.command,p.cl,p.cr,cld,crd)
                        if not cp: continue
                        val=e.command[cp[0]:cp[1]]
                        if not (0<len(val)<=14): continue
                        for sld in range(min(2,len(p.sl))+1):
                          for srd in range(min(2,len(p.sr))+1):
                            sp=locate(e.before,p.sl,p.sr,sld,srd)
                            if not sp: continue
                            old=e.before[sp[0]:sp[1]]
                            if shape(old)!=p.old_shape: continue
                            pred=e.before[:sp[0]]+val+e.before[sp[1]:]
                            key=(pi,cld,crd,sld,srd); ok=pred==e.after
                            evidence[key][0 if ok else 1]+=1
                            if ok: evidence[key][2].add(env)
        for (pi,a,b,c,d),(pos,wrong,envs) in evidence.items():
            if pos>=3 and wrong<=max(1,pos//4):
                self.adapters.append(Adapter(pi,a,b,c,d,pos,wrong,tuple(sorted(envs))))
        self.adapters=sorted(self.adapters,key=lambda x:(len(x.envs),x.support-x.wrong),reverse=True)[:64]
        self.train_s=time.perf_counter()-started

    def candidates(self,e,use_adapter):
        if use_adapter:
            specs=[(a.program,a.cmd_ld,a.cmd_rd,a.state_ld,a.state_rd,a.support-a.wrong,len(a.envs)) for a in self.adapters]
        else:
            specs=[(i,0,0,0,0,p.support,0) for i,p in enumerate(self.programs)]
        out=[]
        for pi,cld,crd,sld,srd,base,cov in specs:
            p=self.programs[pi]
            cp=locate(e.command,p.cl,p.cr,cld,crd); sp=locate(e.before,p.sl,p.sr,sld,srd)
            if not cp or not sp: continue
            val=e.command[cp[0]:cp[1]]; old=e.before[sp[0]:sp[1]]
            if not (0<len(val)<=14) or shape(old)!=p.old_shape: continue
            pred=e.before[:sp[0]]+val+e.before[sp[1]:]
            score=base+(0.5*cov if self.kind=='fiber' else 0)
            out.append((score,pred,pi,val))
        return out

    def predict(self,e):
        candidates=self.candidates(e,self.kind!='surface')
        if not candidates: return e.before,False,0
        best_by_output={}
        for x in candidates:
            if x[1] not in best_by_output or x[0]>best_by_output[x[1]][0]: best_by_output[x[1]]=x
        ranked=sorted(best_by_output.values(),reverse=True)
        if len(ranked)>1 and ranked[0][0]-ranked[1][0]<0.5: return e.before,False,len(ranked)
        return ranked[0][1],True,len(ranked)

def evaluate(seed,n,mode):
    train=[]
    for j,m in enumerate(('seen','held','rename','alternate')): train+=build(seed+31*j,n//4,m)
    test=build(seed+999,max(24,n//4),mode); out={}
    for kind in ('surface','adapter','fiber'):
        model=Model(kind); model.fit(train); started=time.perf_counter(); correct=wrong=null=candidates=0
        for e in test:
            pred,did,count=model.predict(e); candidates+=count
            correct+=int(did and pred==e.after); wrong+=int(did and pred!=e.after); null+=int(not did)
        out[kind]={'accuracy':correct/len(test),'wrong_commit':wrong/len(test),'null_rate':null/len(test),
                   'mean_candidates':candidates/len(test),'programs':len(model.programs),'adapters':len(model.adapters),
                   'multi_env_adapters':sum(len(a.envs)>=2 for a in model.adapters),'model_bytes':len(pickle.dumps(model)),
                   'training_seconds':model.train_s,'inference_ms':(time.perf_counter()-started)*1000/len(test)}
    return out

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output',default='results_cycle_030.json'); args=parser.parse_args()
    modes=('seen','held','rename','alternate','omitted','paragraph','plan','counterfactual'); raw={}
    for n in (48,144,288):
        runs=[]
        for seed in (1,7,19): runs.append({m:evaluate(seed,n,m) for m in modes})
        raw[str(n)]=runs
    summary={}
    for n,runs in raw.items():
        summary[n]={}
        for mode in modes:
            summary[n][mode]={}
            for kind in ('surface','adapter','fiber'):
                summary[n][mode][kind]={key:statistics.mean(run[mode][kind][key] for run in runs) for key in runs[0][mode][kind]}
    payload={'cycle':30,'hypothesis':'Target-Context Mechanism Adapters from Outcome-Blind Structural Edit Search',
             'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             'estimated_complexity':'program extraction O(NL), adapter audit O(NEPD^4), inference O((P+A)L), D<=2',
             'target_outcome_used_for_candidate_generation':False,
             'target_outcome_used_for_adapter_audit_after_proposal':True,
             'highschool_level_passed':False,'native_japanese_communication_passed':False,
             'weak_smartphone_verified':False,'completion':False}
    with open(args.output,'w',encoding='utf-8') as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary['288'],ensure_ascii=False,indent=2))

if __name__=='__main__': main()
