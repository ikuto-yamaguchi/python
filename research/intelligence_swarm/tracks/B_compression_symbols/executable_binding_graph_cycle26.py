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
    before:str; command:str; after:str; future:str
    obj:str; field:str; old:str; new:str; mode:str
@dataclass
class ExactProgram:
    cl:str; cr:str; sl:str; sr:str; support:int=1; wrong:int=0
@dataclass
class ObjNode:
    shape:str; min_len:int; max_len:int; support:int=0
@dataclass
class ValNode:
    shape:str; min_len:int; max_len:int; support:int=0
@dataclass
class Endpoint:
    sl:str; sr:str; old_shape:str; new_shape:str; support:int=0; wrong:int=0; inverse:int=0; damage:int=0
@dataclass
class Triangle:
    obj:int; val:int; endpoint:int; support:int; wrong:int; inverse:int
    def bits(self): return 96

def state(o,d,form): return (STATE1 if form else STATE0).format(o=o,loc=d['場所'],status=d['状態'],owner=d['担当'])
def shape(s): return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、／=：:\n ' else c for c in s)
def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def contexts(text,span,w=8):
    out=[];p=0
    while span:
        i=text.find(span,p)
        if i<0:break
        out.append((text[max(0,i-w):i],text[i+len(span):i+len(span)+w]));p=i+1
    return out
def spans(text,max_len=12):
    return {text[i:j] for i in range(len(text)) for j in range(i+1,min(len(text),i+max_len)+1)}

def build(seed,n,mode):
    rng=random.Random(seed);world={};out=[]
    for _ in range(n):
        canon=rng.choice(OBJECTS);surf=ALIASES[canon] if mode=='rename' else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS})
        f=rng.choice(FIELDS);old=world[canon][f];new=rng.choice([x for x in VALUES[f] if x!=old])
        form=1 if mode=='alternate' else 0
        before=state(surf,world[canon],form)
        forms=HELD_ORDER[f] if mode=='order' else HELD_LEX[f] if mode=='lexeme' else OMIT[f] if mode=='omitted' else CMDS[f]
        command=rng.choice(forms).format(o=surf,v=new)
        if mode=='nested': command='依頼内容は「'+command+'」です。'
        if mode=='paragraph': command='前段の説明があります。別件は変更しません。\n'+command+'\n補助記録は維持してください。'
        world[canon][f]=new;after=state(surf,world[canon],form)
        future=f'次の観測でも{surf}の更新結果は{new}で、補助記録は維持されます。'
        out.append(Ex(before,command,after,future,surf,f,old,new,mode))
    return out

class Model:
    def __init__(self,mode):
        self.mode=mode;self.exact=[];self.obj_nodes=[];self.val_nodes=[];self.endpoints=[];self.triangles=[]
        self.raw_candidates=0;self.audit_count=0;self.description_bits=0;self.training_seconds=0.0
    def fit(self,eps):
        t0=time.perf_counter();exact=Counter();objstat=Counter();valstat=Counter();epstat=Counter();witnesses=[]
        for ei,e in enumerate(eps):
            l,r,old,new=diff(e.before,e.after)
            if not old or not new: continue
            sl=e.before[max(0,l-8):l];sr=e.before[len(e.before)-r:len(e.before)-r+8] if r else ''
            cs=contexts(e.command,new)
            if not cs: continue
            common_obj=spans(e.command)&spans(e.before)&spans(e.after)&spans(e.future)
            obj_candidates=[x for x in common_obj if 2<=len(x)<=12]
            val_candidates=[x for x in spans(e.command)&spans(e.after)&spans(e.future) if x not in e.before and 1<=len(x)<=10]
            self.raw_candidates+=len(obj_candidates)+len(val_candidates)
            obj_candidates=sorted(obj_candidates,key=lambda x:(-len(x),x))[:8]
            val_candidates=sorted(val_candidates,key=lambda x:(-len(x),x))[:8]
            for cl,cr in cs[:2]: exact[(cl,cr,sl,sr)]+=1
            for o in obj_candidates: objstat[(shape(o),len(o))]+=1
            for v in val_candidates: valstat[(shape(v),len(v))]+=1
            epstat[(sl,sr,shape(old),shape(new))]+=1
            witnesses.append((ei,obj_candidates,val_candidates,(sl,sr,shape(old),shape(new)),old,new))
        self.exact=[ExactProgram(*k,support=n) for k,n in exact.most_common(64)]
        ogroups=defaultdict(list);vgroups=defaultdict(list)
        for (sh,ln),n in objstat.items(): ogroups[sh].append((ln,n))
        for (sh,ln),n in valstat.items(): vgroups[sh].append((ln,n))
        self.obj_nodes=[ObjNode(sh,min(x for x,_ in a),max(x for x,_ in a),sum(n for _,n in a)) for sh,a in ogroups.items() if sum(n for _,n in a)>=3][:32]
        self.val_nodes=[ValNode(sh,min(x for x,_ in a),max(x for x,_ in a),sum(n for _,n in a)) for sh,a in vgroups.items() if sum(n for _,n in a)>=3][:32]
        self.endpoints=[Endpoint(*k,support=n) for k,n in epstat.most_common(32)]
        obj_index={n.shape:i for i,n in enumerate(self.obj_nodes)}
        val_index={n.shape:i for i,n in enumerate(self.val_nodes)}
        ep_index={(p.sl,p.sr,p.old_shape,p.new_shape):i for i,p in enumerate(self.endpoints)}
        tristat=defaultdict(lambda:[0,0,0])
        for ei,ocs,vcs,epkey,old,new in witnesses:
            e=eps[ei];pi=ep_index.get(epkey)
            if pi is None: continue
            p=self.endpoints[pi];omap=defaultdict(list);vmap=defaultdict(list)
            for x in ocs:
                oi=obj_index.get(shape(x))
                if oi is not None: omap[oi].append(x)
            for x in vcs:
                vi=val_index.get(shape(x))
                if vi is not None: vmap[vi].append(x)
            for oi,os in list(omap.items())[:4]:
                for vi,vs in list(vmap.items())[:4]:
                    self.audit_count+=1;o=max(os,key=len);v=max(vs,key=len)
                    pred=self._apply_endpoint(e.before,v,p)
                    ok=pred==e.after and o in e.before and o in e.command
                    inv=self._apply_endpoint(e.after,old,Endpoint(p.sl,p.sr,p.new_shape,p.old_shape))==e.before
                    damage=pred is not None and ('補助記録' not in pred or '維持' not in pred)
                    key=(oi,vi,pi);tristat[key][0]+=int(ok and not damage);tristat[key][1]+=int(not ok or damage);tristat[key][2]+=int(inv)
        for (oi,vi,pi),(ss,ww,inv) in tristat.items():
            if ss>=3 and ww==0 and inv>=3:self.triangles.append(Triangle(oi,vi,pi,ss,ww,inv))
        self.triangles=sorted(self.triangles,key=lambda x:(x.support,x.inverse),reverse=True)[:64]
        literal=sum(8*(len(e.before)+len(e.command)+len(e.after)+len(e.future)) for e in eps)
        graph=sum(64+8*(len(p.sl)+len(p.sr)) for p in self.endpoints)+sum(t.bits() for t in self.triangles)+len(eps)*48
        self.description_bits=graph if self.mode=='mdl' else literal
        if self.mode=='mdl' and graph>=literal:self.triangles=[]
        self.training_seconds=time.perf_counter()-t0
    def _apply_endpoint(self,before,v,p):
        starts=[];q=0
        while True:
            i=before.find(p.sl,q) if p.sl else q
            if i<0:break
            a=i+len(p.sl);b=before.find(p.sr,a) if p.sr else len(before)
            if b>=a and shape(before[a:b])==p.old_shape:starts.append((a,b))
            q=i+1
            if not p.sl or q>=len(before):break
        if len(starts)!=1:return None
        a,b=starts[0];return before[:a]+v+before[b:]
    def _between(self,text,l,r):
        out=[];starts=[0] if not l else [];q=0
        while l:
            i=text.find(l,q)
            if i<0:break
            starts.append(i+len(l));q=i+1
        for a in starts:
            b=text.find(r,a) if r else len(text)
            if b>=a and 0<b-a<=14:out.append(text[a:b])
        return out
    def exact_predict(self,e):
        cand=[]
        for p in self.exact:
            for v in self._between(e.command,p.cl,p.cr)[:2]:
                pred=self._apply_endpoint(e.before,v,Endpoint(p.sl,p.sr,'',''))
                if pred:cand.append((p.support,pred))
        return self._choose(cand,e.before)
    def graph_predict(self,e):
        common=spans(e.command)&spans(e.before);os=[x for x in common if 2<=len(x)<=12]
        novel=[x for x in spans(e.command,10) if x not in e.before and 1<=len(x)<=10]
        cand=[];pairs=[]
        for t in self.triangles:
            on=self.obj_nodes[t.obj];vn=self.val_nodes[t.val];p=self.endpoints[t.endpoint]
            ox=[x for x in os if shape(x)==on.shape and on.min_len<=len(x)<=on.max_len]
            vx=[x for x in novel if shape(x)==vn.shape and vn.min_len<=len(x)<=vn.max_len]
            for o in sorted(ox,key=len,reverse=True)[:2]:
                if o not in e.command or o not in e.before:continue
                for v in sorted(vx,key=len)[:4]:
                    pred=self._apply_endpoint(e.before,v,p)
                    if pred:
                        score=t.support+t.inverse+len(o)*.1-len(v)*.01
                        cand.append((score,pred));pairs.append((o,v))
        pred,did,n=self._choose(cand,e.before)
        return pred,did,n,pairs[:16]
    def _choose(self,cand,default):
        if not cand:return default,False,0
        by={}
        for s,p in cand:by[p]=max(s,by.get(p,-1e9))
        ranked=sorted(((s,p) for p,s in by.items()),reverse=True)
        if len(ranked)>1 and abs(ranked[0][0]-ranked[1][0])<1e-9:return default,False,len(ranked)
        return ranked[0][1],True,len(ranked)
    def predict(self,e):
        if self.mode=='exact':
            p,d,n=self.exact_predict(e);return p,d,n,[]
        return self.graph_predict(e)

def eval_model(model,test):
    t=time.perf_counter();correct=wrong=commits=recall=candidates=0
    for e in test:
        pred,did,count,pairs=model.predict(e);candidates+=count;commits+=did
        correct+=int(did and pred==e.after);wrong+=int(did and pred!=e.after)
        recall+=int(any(o==e.obj and v==e.new for o,v in pairs))
    return {'accuracy':correct/len(test),'wrong_commit':wrong/len(test),'commit_rate':commits/len(test),'pair_recall':recall/len(test),'mean_candidates':candidates/len(test),'model_bytes':len(pickle.dumps(model)),'training_seconds':model.training_seconds,'inference_ms':(time.perf_counter()-t)*1000/len(test),'obj_nodes':len(model.obj_nodes),'val_nodes':len(model.val_nodes),'endpoints':len(model.endpoints),'triangles':len(model.triangles),'raw_candidates':model.raw_candidates,'audit_count':model.audit_count,'description_bits':model.description_bits}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='MEASUREMENTS_CYCLE_026.json');args=parser.parse_args()
    modes=['seen','order','lexeme','rename','alternate','nested','omitted','paragraph'];raw={}
    for n in (48,144,288):
        runs=[]
        for seed in (1,7,19):
            train=build(seed,n,'seen');models={}
            for method in ('exact','graph','mdl'):
                model=Model(method);model.fit(train);models[method]=model
            run={}
            for mode in modes:
                test=build(seed+999,24,mode);run[mode]={method:eval_model(model,test) for method,model in models.items()}
            runs.append(run)
        raw[str(n)]=runs
    summary={}
    for n,runs in raw.items():
        summary[n]={}
        for mode in modes:
            summary[n][mode]={}
            for method in ('exact','graph','mdl'):
                summary[n][mode][method]={k:statistics.mean(r[mode][method][k] for r in runs) for k in runs[0][mode][method]}
    payload={'hypothesis':'Executable Binding Graphs from Role-Exchange Consequence Factorization','seeds':[1,7,19],'sizes':[48,144,288],'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'proposal O(NL^2), observed-triple audit O(NK_oK_v), inference O(TL^2), K_o,K_v<=4,T<=64','hidden_labels_used_by_learner':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(args.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary['288'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
