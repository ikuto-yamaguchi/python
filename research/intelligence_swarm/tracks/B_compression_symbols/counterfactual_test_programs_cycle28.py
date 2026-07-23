from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse,json,math,pickle,random,resource,statistics,time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
FIELDS=['場所','状態','担当']
VALUES={'場所':['棚A','棚B','棚C','棚D'],'状態':['待機','処理中','完了','保留'],'担当':['担当一','担当二','担当三','担当四']}
STATE0='{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。'
STATE1='{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。'
CMDS={'場所':['{o}を{v}へ移してください。','{o}の保管先を{v}へ変更します。'],'状態':['{o}を{v}にしてください。','{o}の進行状態を{v}へ切り替えます。'],'担当':['{o}を{v}の担当にしてください。','{o}の受け持ちを{v}へ変更します。']}
HELD_ORDER={'場所':['{v}へ移してください、対象は{o}です。'],'状態':['{v}扱いにしてください、対象は{o}です。'],'担当':['{v}へ引き継いでください、対象は{o}です。']}
HELD_LEX={'場所':['対象{o}は次から{v}で保管。'],'状態':['対象{o}は以後{v}として運用。'],'担当':['対象{o}の受持を{v}へ。']}
OMIT={'場所':['それを{v}へ移してください。'],'状態':['その対象を{v}にしてください。'],'担当':['担当は{v}へ変えてください。']}

@dataclass
class Ex:
    before:str; command:str; after:str; future:str; obj:str; field:str; old:str; new:str; mode:str
@dataclass
class Endpoint:
    sl:str; sr:str; old_shape:str; new_shape:str; support:int=0
@dataclass
class Triangle:
    obj_shape:str; val_shape:str; endpoint:int; support:int=0; wrong:int=0; noexec:int=0
    tests:tuple=(); mdl_bits:int=0

def state(o,d,form): return (STATE1 if form else STATE0).format(o=o,loc=d['場所'],status=d['状態'],owner=d['担当'])
def shape(s): return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、／=：:\n ' else c for c in s)
def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def spans(text,max_len=12):return {text[i:j] for i in range(len(text)) for j in range(i+1,min(len(text),i+max_len)+1)}
def build(seed,n,mode):
    rng=random.Random(seed);world={};out=[]
    for _ in range(n):
        canon=rng.choice(OBJECTS);surf=ALIASES[canon] if mode=='rename' else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS})
        f=rng.choice(FIELDS);old=world[canon][f];new=rng.choice([x for x in VALUES[f] if x!=old])
        form=1 if mode=='alternate' else 0;before=state(surf,world[canon],form)
        forms=HELD_ORDER[f] if mode=='order' else HELD_LEX[f] if mode=='lexeme' else OMIT[f] if mode=='omitted' else CMDS[f]
        command=rng.choice(forms).format(o=surf,v=new)
        if mode=='nested':command='依頼内容は「'+command+'」です。'
        if mode=='paragraph':command='前段の説明があります。別件は変更しません。\n'+command+'\n補助記録は維持してください。'
        world[canon][f]=new;after=state(surf,world[canon],form)
        future=f'次の観測でも{surf}の更新結果は{new}で、補助記録は維持されます。'
        out.append(Ex(before,command,after,future,surf,f,old,new,mode))
    return out

def apply_endpoint(before,value,p):
    hits=[];q=0
    while True:
        i=before.find(p.sl,q) if p.sl else q
        if i<0:break
        a=i+len(p.sl);b=before.find(p.sr,a) if p.sr else len(before)
        if b>=a and shape(before[a:b])==p.old_shape:hits.append((a,b))
        q=i+1
        if not p.sl or q>=len(before):break
    if len(hits)!=1:return None
    a,b=hits[0];return before[:a]+value+before[b:]

def inverse_endpoint(after,old,p):
    hits=[];q=0
    while True:
        i=after.find(p.sl,q) if p.sl else q
        if i<0:break
        a=i+len(p.sl);b=after.find(p.sr,a) if p.sr else len(after)
        if b>=a and shape(after[a:b])==p.new_shape:hits.append((a,b))
        q=i+1
        if not p.sl or q>=len(after):break
    if len(hits)!=1:return None
    a,b=hits[0];return after[:a]+old+after[b:]

def output_tests(before,pred,value,p):
    l,r,old,new=diff(before,pred)
    pos=round(l/max(1,len(before)),1)
    preservation=int((before[:l]+before[len(before)-r if r else len(before):]) == (pred[:l]+pred[len(pred)-r if r else len(pred):]))
    aux=int(('補助記録' in before)==('補助記録' in pred))
    inv=int(inverse_endpoint(pred,old,p)==before)
    recurrence=int(value in pred)
    width=min(12,len(new))
    return (('pos',pos),('pres',preservation),('aux',aux),('inv',inv),('rec',recurrence),('w',width),('newsh',shape(new)))

class Model:
    def __init__(self,mode):
        self.mode=mode;self.endpoints=[];self.triangles=[];self.raw_candidates=0;self.audit_count=0;self.test_count=0;self.description_bits=0;self.training_seconds=0
    def fit(self,eps):
        t0=time.perf_counter();epc=Counter();records=[]
        for e in eps:
            l,r,old,new=diff(e.before,e.after)
            if not old or not new:continue
            ep=(e.before[max(0,l-8):l],e.before[len(e.before)-r:len(e.before)-r+8] if r else '',shape(old),shape(new));epc[ep]+=1
            oc=sorted([x for x in spans(e.command)&spans(e.before)&spans(e.after)&spans(e.future) if 2<=len(x)<=12],key=lambda x:(-len(x),x))[:4]
            vc=sorted([x for x in spans(e.command)&spans(e.after)&spans(e.future) if x not in e.before and 1<=len(x)<=10],key=lambda x:(-len(x),x))[:4]
            self.raw_candidates+=len(oc)+len(vc);records.append((e,ep,oc,vc,old))
        self.endpoints=[Endpoint(*k,support=n) for k,n in epc.most_common(32)]
        epi={(p.sl,p.sr,p.old_shape,p.new_shape):i for i,p in enumerate(self.endpoints)}
        stats=defaultdict(lambda:[0,0,0,Counter()])
        for e,ep,ocs,vcs,old in records:
            pi=epi.get(ep)
            if pi is None:continue
            p=self.endpoints[pi]
            for o in ocs:
                for v in vcs:
                    self.audit_count+=1;pred=apply_endpoint(e.before,v,p);key=(shape(o),shape(v),pi)
                    ok=(pred==e.after and o in e.command and o in e.before)
                    if pred is None:stats[key][2]+=1
                    elif ok:stats[key][0]+=1
                    else:stats[key][1]+=1
                    if pred is not None:
                        for test in output_tests(e.before,pred,v,p):stats[key][3][test]+=1 if ok else -1
        for (osh,vsh,pi),(pos,wrong,noexec,tc) in stats.items():
            if pos<3 or wrong>pos:continue
            tests=tuple(t for t,g in tc.most_common(6) if g>=2)
            tri=Triangle(osh,vsh,pi,pos,wrong,noexec,tests,96+sum(16+8*len(str(t)) for t in tests))
            self.triangles.append(tri);self.test_count+=len(tests)
        self.triangles=sorted(self.triangles,key=lambda t:(t.support-t.wrong,len(t.tests)),reverse=True)[:64]
        literal=sum(8*(len(e.before)+len(e.command)+len(e.after)+len(e.future)) for e in eps)
        graph=sum(64+8*(len(p.sl)+len(p.sr)) for p in self.endpoints)+sum(t.mdl_bits for t in self.triangles)+len(eps)*48
        self.description_bits=graph if self.mode=='mdl' else literal
        if self.mode=='mdl' and graph>=literal:self.triangles=[]
        self.training_seconds=time.perf_counter()-t0
    def predict(self,e):
        common=[x for x in spans(e.command)&spans(e.before) if 2<=len(x)<=12]
        novel=[x for x in spans(e.command,10) if x not in e.before and 1<=len(x)<=10]
        candidates=[];pairs=[]
        for ti,t in enumerate(self.triangles):
            p=self.endpoints[t.endpoint]
            os=[x for x in common if shape(x)==t.obj_shape][:3]
            vs=[x for x in novel if shape(x)==t.val_shape][:6]
            for o in os:
                for v in vs:
                    pred=apply_endpoint(e.before,v,p)
                    if pred is None:continue
                    tests=set(output_tests(e.before,pred,v,p));hit=sum(x in tests for x in t.tests)
                    score=t.support-t.wrong
                    if self.mode in ('test','mdl'): score += 1.5*hit-.4*(len(t.tests)-hit)
                    candidates.append((score,pred,ti,tests));pairs.append((score,o,v))
        if not candidates:return e.before,False,0,[],0
        bypred={}
        for score,pred,ti,tests in candidates:
            if pred not in bypred or score>bypred[pred][0]:bypred[pred]=(score,ti,tests)
        ranked=[];alltests=[x[2] for x in bypred.values()]
        for pred,(score,ti,tests) in bypred.items():
            unique=sum(1 for t in tests if sum(t in z for z in alltests)==1)
            if self.mode in ('test','mdl'):score+=.75*unique
            ranked.append((score,pred))
        ranked.sort(reverse=True)
        if len(ranked)>1 and ranked[0][0]-ranked[1][0]<.5:return e.before,False,len(ranked),pairs[:32],sum(len(x) for x in alltests)
        return ranked[0][1],True,len(ranked),pairs[:32],sum(len(x) for x in alltests)

def evaluate(model,test):
    t=time.perf_counter();correct=wrong=commit=recall=cands=tests=0
    for e in test:
        pred,did,n,pairs,nt=model.predict(e);cands+=n;tests+=nt;commit+=did
        correct+=int(did and pred==e.after);wrong+=int(did and pred!=e.after)
        recall+=int(any(o==e.obj and v==e.new for _,o,v in pairs))
    return {'accuracy':correct/len(test),'wrong_commit':wrong/len(test),'commit_rate':commit/len(test),'pair_recall':recall/len(test),'mean_candidates':cands/len(test),'mean_test_outcomes':tests/len(test),'triangles':len(model.triangles),'test_programs':model.test_count,'raw_candidates':model.raw_candidates,'audit_count':model.audit_count,'description_bits':model.description_bits,'model_bytes':len(pickle.dumps(model)),'training_seconds':model.training_seconds,'inference_ms':(time.perf_counter()-t)*1000/len(test)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='MEASUREMENTS_CYCLE_028.json');a=ap.parse_args()
    modes=['seen','order','lexeme','rename','alternate','nested','omitted','paragraph'];raw={}
    for n in (48,144,288):
        runs=[]
        for seed in (1,7,19):
            train=build(seed,n,'seen');models={}
            for mode in ('graph','test','mdl'):
                m=Model(mode);m.fit(train);models[mode]=m
            run={}
            for mode in modes:
                test=build(seed+999,24,mode);run[mode]={k:evaluate(m,test) for k,m in models.items()}
            runs.append(run)
        raw[str(n)]=runs
    summary={}
    for n,runs in raw.items():
        summary[n]={}
        for mode in modes:
            summary[n][mode]={}
            for method in ('graph','test','mdl'):
                summary[n][mode][method]={k:statistics.mean(r[mode][method][k] for r in runs) for k in runs[0][mode][method]}
    payload={'hypothesis':'Counterfactual Test Programs from Competing Binding-Graph Output Disagreements','seeds':[1,7,19],'sizes':[48,144,288],'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'candidate O(NL^2), audit O(NKoKv), test induction O(TF), disagreement selection O(C^2F), inference O(TL^2)','hidden_labels_used_by_learner':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary['288'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
