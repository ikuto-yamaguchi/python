from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse,json,pickle,random,resource,statistics,time,math

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末',
         '北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
FIELDS=['場所','状態','担当']
VALUES={'場所':['棚A','棚B','棚C','棚D'],'状態':['待機','処理中','完了','保留'],'担当':['担当一','担当二','担当三','担当四']}
STATE0='{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。'
STATE1='{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。'
CMDS={'場所':['{o}を{v}へ移してください。','{o}の保管先を{v}へ変更します。'],
      '状態':['{o}を{v}にしてください。','{o}の進行状態を{v}へ切り替えます。'],
      '担当':['{o}を{v}の担当にしてください。','{o}の受け持ちを{v}へ変更します。']}
ORDER={'場所':['{v}へ移してください、対象は{o}です。'],
       '状態':['{v}扱いにしてください、対象は{o}です。'],
       '担当':['{v}へ引き継いでください、対象は{o}です。']}
LEX={'場所':['対象{o}は次から{v}で保管。'],
     '状態':['対象{o}は以後{v}として運用。'],
     '担当':['対象{o}の受持を{v}へ。']}
OMIT={'場所':['それを{v}へ移してください。'],
      '状態':['その対象を{v}にしてください。'],
      '担当':['担当は{v}へ変えてください。']}

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
    support:int=0; wrong:int=0; noexec:int=0

def state(o,d,form):
    return (STATE1 if form else STATE0).format(o=o,loc=d['場所'],status=d['状態'],owner=d['担当'])
def shape(s):
    return ''.join('A' if c.isascii() and c.isalnum() else
                   'J' if c not in '。、／=：:\n 「」' else c for c in s)
def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def spans(text,max_len=12):
    return {text[i:j] for i in range(len(text))
            for j in range(i+1,min(len(text),i+max_len)+1)}
def build(seed,n,mode):
    rng=random.Random(seed);world={};out=[];focus=None
    for i in range(n):
        canon=focus if mode=='omitted' and focus is not None else rng.choice(OBJECTS)
        surf=ALIASES[canon] if mode=='rename' else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS})
        f=rng.choice(FIELDS);old=world[canon][f];new=rng.choice([x for x in VALUES[f] if x!=old])
        form=1 if mode=='alternate' else 0;before=state(surf,world[canon],form)
        forms=ORDER[f] if mode=='order' else LEX[f] if mode=='lexeme' else OMIT[f] if mode=='omitted' else CMDS[f]
        command=random.Random(seed*1000+i).choice(forms).format(o=surf,v=new)
        if mode=='nested':command='依頼内容は「'+command+'」です。'
        if mode=='paragraph':command='前段の説明があります。別件は変更しません。\n'+command+'\n補助記録は維持してください。'
        world[canon][f]=new;after=state(surf,world[canon],form)
        future=f'次の観測でも{surf}の更新結果は{new}で、補助記録は維持されます。'
        out.append(Ex(before,command,after,future,surf,f,old,new,mode));focus=canon
    return out
def apply(before,value,p):
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
def inverse(after,old,p):
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
def ctx(e):
    return (shape(e.before[:18]),shape(e.command[:18]),len(e.before)//8,len(e.command)//8)

class Model:
    def __init__(self,mode,budget=16):
        self.mode=mode;self.budget=budget;self.endpoints=[];self.triangles=[]
        self.pref=Counter();self.cpref=Counter();self.selected=[]
        self.symbol_of={};self.symbol_members=defaultdict(list);self.symbol_pref=Counter()
        self.stats=Counter();self.train_s=0;self.bits=0

    def fit(self,induction,pool):
        t=time.perf_counter(); epc=Counter(); records=[]
        for e in induction:
            l,r,old,new=diff(e.before,e.after)
            if not old or not new:continue
            ep=(e.before[max(0,l-8):l],
                e.before[len(e.before)-r:len(e.before)-r+8] if r else '',
                shape(old),shape(new));epc[ep]+=1
            oc=sorted([x for x in spans(e.command)&spans(e.before)&spans(e.after)&spans(e.future)
                       if 2<=len(x)<=12],key=lambda x:(-len(x),x))[:4]
            vc=sorted([x for x in spans(e.command)&spans(e.after)&spans(e.future)
                       if x not in e.before and 1<=len(x)<=10],key=lambda x:(-len(x),x))[:4]
            records.append((e,ep,oc,vc,old))
        self.endpoints=[Endpoint(*k,support=n) for k,n in epc.most_common(32)]
        epi={(p.sl,p.sr,p.old_shape,p.new_shape):i for i,p in enumerate(self.endpoints)}
        st=defaultdict(lambda:[0,0,0])
        for e,ep,ocs,vcs,old in records:
            pi=epi.get(ep)
            if pi is None:continue
            p=self.endpoints[pi]
            for o in ocs:
                for v in vcs:
                    pred=apply(e.before,v,p);key=(shape(o),shape(v),pi)
                    ok=pred==e.after and o in e.command and o in e.before and inverse(e.after,old,p)==e.before
                    if pred is None:st[key][2]+=1
                    elif ok:st[key][0]+=1
                    else:st[key][1]+=1
        for (osh,vsh,pi),(pos,wrong,noexec) in st.items():
            if pos>=3 and wrong<=pos:
                self.triangles.append(Triangle(osh,vsh,pi,pos,wrong,noexec))
        self.triangles=sorted(self.triangles,key=lambda z:(z.support-z.wrong,-z.noexec),reverse=True)[:64]

        probe_records=[]
        tri_resp={i:[] for i in range(len(self.triangles))}
        for idx,e in enumerate(pool):
            generated=self.generate(e,relaxed=False)
            by={ti:pred for _,pred,ti,_,_ in generated}
            pairs=[]
            for a in sorted(by):
                for b in sorted(by):
                    if a>=b or by[a]==by[b]:continue
                    ca=by[a]==e.after;cb=by[b]==e.after
                    if ca==cb:continue
                    pairs.append((a,b) if ca else (b,a))
            for ti in range(len(self.triangles)):
                tri_resp[ti].append(1 if by.get(ti)==e.after else -1 if ti in by else 0)
            if pairs:
                desc=8*(len(e.before)+len(e.command))
                probe_records.append((len(set(pairs))/max(1,desc),desc,idx,e,pairs))

        chosen=sorted(probe_records,reverse=True)[:self.budget]
        chosen_idx={x[2] for x in chosen}
        for _,desc,idx,e,pairs in chosen:
            self.selected.append((idx,desc,len(pairs))); sig=ctx(e)
            for a,b in pairs:self.pref[(a,b)]+=1;self.cpref[(sig,a,b)]+=1

        sig_to_members=defaultdict(list)
        ordered_pool_indices=[i for i in range(len(pool)) if i in chosen_idx]
        for ti in range(len(self.triangles)):
            response=tuple(tri_resp[ti][i] for i in ordered_pool_indices)
            ep=self.endpoints[self.triangles[ti].endpoint]
            consequence=(ep.old_shape,ep.new_shape,len(ep.sl)//2,len(ep.sr)//2,response)
            sig_to_members[consequence].append(ti)
        sid=0
        for sig,members in sorted(sig_to_members.items(),key=lambda kv:(-len(kv[1]),str(kv[0]))):
            if len(members)<2:continue
            for ti in members:self.symbol_of[ti]=sid
            self.symbol_members[sid]=members
            sid+=1

        for (a,b),n in self.pref.items():
            sa=self.symbol_of.get(a);sb=self.symbol_of.get(b)
            if sa is not None and sb is not None and sa!=sb:self.symbol_pref[(sa,sb)]+=n

        self.stats['probe_candidates']=len(probe_records)
        self.stats['selected_probes']=len(chosen)
        self.stats['discriminations']=sum(len(x[4]) for x in chosen)
        self.stats['symbols']=len(self.symbol_members)
        self.stats['symbol_members']=sum(len(v) for v in self.symbol_members.values())
        literal=sum(8*(len(e.before)+len(e.command)+len(e.after)+len(e.future)) for e in induction+pool)
        graph=sum(64+8*(len(p.sl)+len(p.sr)) for p in self.endpoints)+len(self.triangles)*128
        probe_bits=sum(x[1] for x in chosen)+len(self.pref)*24+len(self.cpref)*32
        symbol_bits=len(self.symbol_members)*64+sum(len(v)*6 for v in self.symbol_members.values())+len(self.symbol_pref)*24
        self.bits=graph+probe_bits+(symbol_bits if self.mode in ('symbol','shuffle_symbol') else 0)
        if self.mode=='graph':self.bits=literal
        if self.mode=='shuffle_symbol':
            self.symbol_pref=Counter({(b,a):n for (a,b),n in self.symbol_pref.items()})
        self.train_s=time.perf_counter()-t

    def generate(self,e,relaxed=False):
        common=[x for x in spans(e.command)&spans(e.before) if 2<=len(x)<=12]
        novel=[x for x in spans(e.command,10) if x not in e.before and 1<=len(x)<=10]
        out=[]
        for ti,t in enumerate(self.triangles):
            p=self.endpoints[t.endpoint]
            if relaxed and ti in self.symbol_of:
                members=self.symbol_members[self.symbol_of[ti]]
                osh={self.triangles[m].obj_shape for m in members}
                vsh={self.triangles[m].val_shape for m in members}
            else:
                osh={t.obj_shape};vsh={t.val_shape}
            os=[x for x in common if shape(x) in osh][:4]
            vs=[x for x in novel if shape(x) in vsh][:8]
            for o in os:
                for v in vs:
                    pred=apply(e.before,v,p)
                    if pred is not None:out.append((t.support-t.wrong,pred,ti,o,v))
        return out

    def predict(self,e):
        relaxed=self.mode in ('symbol','shuffle_symbol')
        g=self.generate(e,relaxed=relaxed)
        if not g:return e.before,False,0,[]
        sig=ctx(e);best={}
        for base,pred,ti,o,v in g:
            score=base
            if self.mode in ('probe','symbol','shuffle_symbol'):
                for tj in range(len(self.triangles)):
                    score+=.8*(self.pref[(ti,tj)]-self.pref[(tj,ti)])
                    score+=1.2*(self.cpref[(sig,ti,tj)]-self.cpref[(sig,tj,ti)])
            if self.mode in ('symbol','shuffle_symbol') and ti in self.symbol_of:
                si=self.symbol_of[ti]
                for sj in self.symbol_members:
                    score+=.5*(self.symbol_pref[(si,sj)]-self.symbol_pref[(sj,si)])
                score+=.05*len(self.symbol_members[si])
            if pred not in best or score>best[pred][0]:best[pred]=(score,ti,o,v)
        r=sorted(((sc,pred,ti,o,v) for pred,(sc,ti,o,v) in best.items()),reverse=True)
        if len(r)>1 and r[0][0]-r[1][0]<.5:return e.before,False,len(r),[(x[3],x[4]) for x in r]
        return r[0][1],True,len(r),[(x[3],x[4]) for x in r]

def evalm(m,test):
    t=time.perf_counter();c=w=k=rec=cands=0
    for e in test:
        p,d,n,pairs=m.predict(e);k+=d;c+=d and p==e.after;w+=d and p!=e.after
        cands+=n;rec+=any(o==e.obj and v==e.new for o,v in pairs)
    n=len(test)
    return {'accuracy':c/n,'wrong_commit':w/n,'commit_rate':k/n,
            'pair_recall':rec/n,'mean_candidates':cands/n,
            'triangles':len(m.triangles),'probe_candidates':m.stats['probe_candidates'],
            'selected_probes':m.stats['selected_probes'],'discriminations':m.stats['discriminations'],
            'symbols':m.stats['symbols'],'symbol_members':m.stats['symbol_members'],
            'description_bits':m.bits,'model_bytes':len(pickle.dumps(m)),
            'training_seconds':m.train_s,'inference_ms':(time.perf_counter()-t)*1000/n}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='MEASUREMENTS_CYCLE_031.json');a=ap.parse_args()
    modes=['seen','order','lexeme','rename','alternate','nested','omitted','paragraph'];raw={}
    for seed in (1,7,19):
        alltr=build(seed,288,'seen');ind=alltr[:190];pool=alltr[190:];models={}
        for mode in ('graph','probe','symbol','shuffle_symbol'):
            model=Model(mode,16);model.fit(ind,pool);models[mode]=model
        raw[str(seed)]={mode:{k:evalm(v,build(seed+999,24,mode)) for k,v in models.items()} for mode in modes}
    summary={mode:{method:{k:statistics.mean(raw[str(seed)][mode][method][k] for seed in (1,7,19))
                          for k in raw['1'][mode][method]}
                   for method in ('graph','probe','symbol','shuffle_symbol')} for mode in modes}
    payload={'cycle':31,
      'hypothesis':'Probe-Conditioned Symbol Birth from Minimal Equivalence-Class Splits',
      'raw':raw,'summary':summary,
      'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      'estimated_complexity':'triangle O(NKoKv), response O(VT), equivalence grouping O(TV log T), inference O(TL^2+T^2)',
      'final_test_outcome_used':False,'probe_pool_independent':True,
      'fixed_ontology_or_handwritten_slots_used_by_model':False,
      'highschool_level_passed':False,'native_japanese_communication_passed':False,
      'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
