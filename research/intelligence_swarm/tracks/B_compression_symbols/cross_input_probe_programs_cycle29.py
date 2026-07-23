from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse, json, pickle, random, resource, statistics, time

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
class Endpoint:
    sl:str; sr:str; old_shape:str; new_shape:str; support:int=0

@dataclass
class Triangle:
    obj_shape:str; val_shape:str; endpoint:int
    support:int=0; wrong:int=0; noexec:int=0; mdl_bits:int=0

def state(o,d,form):
    return (STATE1 if form else STATE0).format(o=o,loc=d['場所'],status=d['状態'],owner=d['担当'])

def shape(s):
    return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、／=：:\n ' else c for c in s)

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

def spans(text,max_len=12):
    return {text[i:j] for i in range(len(text)) for j in range(i+1,min(len(text),i+max_len)+1)}

def build(seed,n,mode):
    rng=random.Random(seed); world={}; out=[]
    for _ in range(n):
        canon=rng.choice(OBJECTS); surf=ALIASES[canon] if mode=='rename' else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS})
        f=rng.choice(FIELDS); old=world[canon][f]; new=rng.choice([x for x in VALUES[f] if x!=old])
        form=1 if mode=='alternate' else 0; before=state(surf,world[canon],form)
        forms=HELD_ORDER[f] if mode=='order' else HELD_LEX[f] if mode=='lexeme' else OMIT[f] if mode=='omitted' else CMDS[f]
        command=rng.choice(forms).format(o=surf,v=new)
        if mode=='nested': command='依頼内容は「'+command+'」です。'
        if mode=='paragraph': command='前段の説明があります。別件は変更しません。\n'+command+'\n補助記録は維持してください。'
        world[canon][f]=new; after=state(surf,world[canon],form)
        future=f'次の観測でも{surf}の更新結果は{new}で、補助記録は維持されます。'
        out.append(Ex(before,command,after,future,surf,f,old,new,mode))
    return out

def apply_endpoint(before,value,p):
    hits=[]; q=0
    while True:
        i=before.find(p.sl,q) if p.sl else q
        if i<0: break
        a=i+len(p.sl); b=before.find(p.sr,a) if p.sr else len(before)
        if b>=a and shape(before[a:b])==p.old_shape: hits.append((a,b))
        q=i+1
        if not p.sl or q>=len(before): break
    if len(hits)!=1: return None
    a,b=hits[0]; return before[:a]+value+before[b:]

def inverse_endpoint(after,old,p):
    hits=[]; q=0
    while True:
        i=after.find(p.sl,q) if p.sl else q
        if i<0: break
        a=i+len(p.sl); b=after.find(p.sr,a) if p.sr else len(after)
        if b>=a and shape(after[a:b])==p.new_shape: hits.append((a,b))
        q=i+1
        if not p.sl or q>=len(after): break
    if len(hits)!=1: return None
    a,b=hits[0]; return after[:a]+old+after[b:]

def context_signature(e):
    return (shape(e.before[:18]),shape(e.command[:18]),len(e.before)//8,len(e.command)//8)

class Model:
    def __init__(self,mode):
        self.mode=mode; self.endpoints=[]; self.triangles=[]
        self.raw_candidates=0; self.audit_count=0; self.probe_audits=0; self.probe_discriminations=0
        self.preference=Counter(); self.context_preference=Counter(); self.description_bits=0; self.training_seconds=0

    def fit(self,induction,probe):
        t0=time.perf_counter(); epc=Counter(); records=[]
        for e in induction:
            l,r,old,new=diff(e.before,e.after)
            if not old or not new: continue
            ep=(e.before[max(0,l-8):l],e.before[len(e.before)-r:len(e.before)-r+8] if r else '',shape(old),shape(new)); epc[ep]+=1
            oc=sorted([x for x in spans(e.command)&spans(e.before)&spans(e.after)&spans(e.future) if 2<=len(x)<=12],key=lambda x:(-len(x),x))[:4]
            vc=sorted([x for x in spans(e.command)&spans(e.after)&spans(e.future) if x not in e.before and 1<=len(x)<=10],key=lambda x:(-len(x),x))[:4]
            self.raw_candidates+=len(oc)+len(vc); records.append((e,ep,oc,vc,old))
        self.endpoints=[Endpoint(*k,support=n) for k,n in epc.most_common(32)]
        epi={(p.sl,p.sr,p.old_shape,p.new_shape):i for i,p in enumerate(self.endpoints)}
        stats=defaultdict(lambda:[0,0,0])
        for e,ep,ocs,vcs,old in records:
            pi=epi.get(ep)
            if pi is None: continue
            p=self.endpoints[pi]
            for o in ocs:
                for v in vcs:
                    self.audit_count+=1; pred=apply_endpoint(e.before,v,p); key=(shape(o),shape(v),pi)
                    ok=(pred==e.after and o in e.command and o in e.before and inverse_endpoint(e.after,old,p)==e.before)
                    if pred is None: stats[key][2]+=1
                    elif ok: stats[key][0]+=1
                    else: stats[key][1]+=1
        for (osh,vsh,pi),(pos,wrong,noexec) in stats.items():
            if pos>=3 and wrong<=pos: self.triangles.append(Triangle(osh,vsh,pi,pos,wrong,noexec,96))
        self.triangles=sorted(self.triangles,key=lambda t:(t.support-t.wrong,-t.noexec),reverse=True)[:64]
        for probe_index,e in enumerate(probe):
            generated=self.generate(e)
            oracle_after=probe[(probe_index+1)%len(probe)].after if self.mode=='shuffle' else e.after
            bytri={ti:pred for _,pred,ti,_,_ in generated}; tis=sorted(bytri); sig=context_signature(e)
            for i,a in enumerate(tis):
                for b in tis[i+1:]:
                    pa,pb=bytri[a],bytri[b]
                    if pa==pb: continue
                    self.probe_audits+=1; ca=int(pa==oracle_after); cb=int(pb==oracle_after)
                    if ca==cb: continue
                    self.probe_discriminations+=1; winner=a if ca else b; loser=b if ca else a
                    self.preference[(winner,loser)]+=1; self.context_preference[(sig,winner,loser)]+=1
        literal=sum(8*(len(e.before)+len(e.command)+len(e.after)+len(e.future)) for e in induction+probe)
        graph=sum(64+8*(len(p.sl)+len(p.sr)) for p in self.endpoints)+len(self.triangles)*128
        probes=len(self.preference)*40+len(self.context_preference)*56
        self.description_bits=graph+probes if self.mode=='mdl' else literal
        if self.mode=='mdl' and self.description_bits>=literal:
            self.preference.clear(); self.context_preference.clear()
        self.training_seconds=time.perf_counter()-t0

    def generate(self,e):
        common=[x for x in spans(e.command)&spans(e.before) if 2<=len(x)<=12]
        novel=[x for x in spans(e.command,10) if x not in e.before and 1<=len(x)<=10]; out=[]
        for ti,t in enumerate(self.triangles):
            p=self.endpoints[t.endpoint]; os=[x for x in common if shape(x)==t.obj_shape][:3]; vs=[x for x in novel if shape(x)==t.val_shape][:6]
            for o in os:
                for v in vs:
                    pred=apply_endpoint(e.before,v,p)
                    if pred is not None: out.append((t.support-t.wrong,pred,ti,o,v))
        return out

    def predict(self,e):
        generated=self.generate(e)
        if not generated: return e.before,False,0,[],0
        sig=context_signature(e); bypred={}
        for base,pred,ti,o,v in generated:
            score=base
            if self.mode in ('probe','mdl','shuffle'):
                for tj in range(len(self.triangles)):
                    score+=.8*self.preference.get((ti,tj),0)-.8*self.preference.get((tj,ti),0)
                    score+=1.2*self.context_preference.get((sig,ti,tj),0)-1.2*self.context_preference.get((sig,tj,ti),0)
            if pred not in bypred or score>bypred[pred][0]: bypred[pred]=(score,ti,o,v)
        ranked=sorted(((score,pred,ti,o,v) for pred,(score,ti,o,v) in bypred.items()),reverse=True)
        if len(ranked)>1 and ranked[0][0]-ranked[1][0]<.5: return e.before,False,len(ranked),[(x[3],x[4]) for x in ranked[:32]],0
        top=ranked[0]; used=sum(self.preference.get((top[2],j),0)+self.context_preference.get((sig,top[2],j),0) for j in range(len(self.triangles)))
        return top[1],True,len(ranked),[(x[3],x[4]) for x in ranked[:32]],used

def evaluate(model,test):
    t=time.perf_counter(); correct=wrong=commit=recall=cands=probe_use=0
    for e in test:
        pred,did,n,pairs,used=model.predict(e); cands+=n; probe_use+=used; commit+=did
        correct+=int(did and pred==e.after); wrong+=int(did and pred!=e.after); recall+=int(any(o==e.obj and v==e.new for o,v in pairs))
    n=len(test)
    return {'accuracy':correct/n,'wrong_commit':wrong/n,'commit_rate':commit/n,'pair_recall':recall/n,'mean_candidates':cands/n,'mean_probe_evidence':probe_use/n,'triangles':len(model.triangles),'probe_audits':model.probe_audits,'probe_discriminations':model.probe_discriminations,'global_preferences':len(model.preference),'context_preferences':len(model.context_preference),'raw_candidates':model.raw_candidates,'audit_count':model.audit_count,'description_bits':model.description_bits,'model_bytes':len(pickle.dumps(model)),'training_seconds':model.training_seconds,'inference_ms':(time.perf_counter()-t)*1000/n}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',default='MEASUREMENTS_CYCLE_029.json'); a=ap.parse_args()
    modes=['seen','order','lexeme','rename','alternate','nested','omitted','paragraph']; raw={}
    for n in (288,):
        runs=[]
        for seed in (1,7,19):
            alltrain=build(seed,n,'seen'); cut=max(12,int(len(alltrain)*.7)); induction,probe=alltrain[:cut],alltrain[cut:]
            models={}
            for mode in ('graph','probe','shuffle','mdl'):
                m=Model(mode); m.fit(induction,probe); models[mode]=m
            run={}
            for mode in modes:
                test=build(seed+999,24,mode); run[mode]={k:evaluate(m,test) for k,m in models.items()}
            runs.append(run)
        raw[str(n)]=runs
    summary={}
    for n,runs in raw.items():
        summary[n]={}
        for mode in modes:
            summary[n][mode]={}
            for method in ('graph','probe','shuffle','mdl'):
                keys=runs[0][mode][method]; summary[n][mode][method]={k:statistics.mean(r[mode][method][k] for r in runs) for k in keys}
    payload={'cycle':29,'hypothesis':'Cross-Input Discriminating Experiments from Program-Composed Probe States','seeds':[1,7,19],'sizes':[288],'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'candidate O(NL^2), triangle audit O(NKoKv), probe pair audit O(VT^2), inference O(TL^2+T^2)','final_test_outcomes_used_for_selection':False,'probe_partition_independent_from_induction':True,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary['288'],ensure_ascii=False,indent=2))

if __name__=='__main__': main()
