"""Cycle B008: Joint Role-Effect MDL lattice falsification probe.

Learner input: raw before/command/after Japanese strings only.
No morphology, entity/value lists, semantic slots, ontology, RAG, external LLM,
or task-specific answer labels are used by the learner.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
import json, math, pickle, random, re, resource, statistics, time

ENTITIES=["赤い箱","青い容器","試料甲号","部品乙号","装置あかつき","札しらゆき","対象春風","対象秋月"]
VALUES={
 "loc":["棚A","棚B","机上","廊下","室内","保管庫一"],
 "owner":["田中班","佐藤班","解析組","搬送係","品質班","夜勤組"],
 "state":["待機中","検査済み","封印中","使用可能","点検待ち","搬送中"],
}
STATE_FORMS=[
 lambda e,l,o,s:f"{e}の保管場所は{l}です。担当は{o}です。現在状態は{s}です。",
 lambda e,l,o,s:f"記録：{e}。置き場={l}。受持={o}。状態={s}。",
 lambda e,l,o,s:f"{e}について、{l}にあり、{o}が担当し、{s}となっています。",
]
FORMS={
 "loc":["{e}を{v}へ移してください","{v}へ{e}を移動して","配置先を{v}に変更してください。対象は{e}です"],
 "owner":["{e}の担当を{v}へ替えてください","{v}に{e}を引き継いで","受持を{v}へ変更してください。対象は{e}です"],
 "state":["{e}を{v}にしてください","{v}へ{e}の状態を切り替えて","状態を{v}へ変更してください。対象は{e}です"],
}
HELD_ORDER={
 "loc":["{v}に変更を。保管対象は{e}です","対象{e}について、行き先は{v}です"],
 "owner":["{v}へ変更を。担当対象は{e}です","対象{e}について、受持先は{v}です"],
 "state":["{v}へ変更を。対象は{e}です","対象{e}について、更新後は{v}です"],
}
HELD_LEXEME={
 "loc":["{e}を{v}へ搬送して","{v}へ{e}を送り込んで"],
 "owner":["{e}を{v}へ委ねて","{v}へ{e}を任せて"],
 "state":["{e}を{v}へ遷移させて","{v}へ{e}を移行して"],
}
NESTED={
 "loc":["安全確認が終わったら、{e}については{v}へ動かすよう手配してください"],
 "owner":["確認後、{e}については{v}へ受け渡すよう手配してください"],
 "state":["前処理後、{e}については{v}となるよう更新してください"],
}
OMITTED={
 "loc":["次は{v}へ移してください","{v}への移動でお願いします"],
 "owner":["次は{v}へ引き継いでください","{v}を担当にしてください"],
 "state":["次は{v}へ切り替えてください","{v}に更新してください"],
}
NOOP=["変更せずそのままにしてください","現状を維持してください"]

@dataclass
class Episode:
    kind:str; entity:str; old:str; new:str; before:str; command:str; after:str; noop:bool=False

def state(form,e,vals): return form(e,vals['loc'],vals['owner'],vals['state'])
def make_episode(rng, kind=None, forms=None, state_form=None, rename=False, noop=False):
    kind=kind or rng.choice(tuple(FORMS)); e=(f"未知対象{rng.randrange(10**9)}号" if rename else rng.choice(ENTITIES))
    vals={k:rng.choice(v) for k,v in VALUES.items()}; old=vals[kind]
    new=old if noop else rng.choice([x for x in VALUES[kind] if x!=old])
    if rename:
        old=f"旧値{rng.randrange(10**8)}"; new=old if noop else f"新値{rng.randrange(10**8)}"; vals[kind]=old
    sf=state_form or STATE_FORMS[0]; before=state(sf,e,vals)
    if noop: return Episode(kind,e,old,new,before,rng.choice(NOOP),before,True)
    command=rng.choice(forms or FORMS[kind]).format(e=e,v=new); vals2=dict(vals); vals2[kind]=new
    return Episode(kind,e,old,new,before,command,state(sf,e,vals2),False)

def changed_span(a,b):
    ops=[x for x in SequenceMatcher(None,a,b).get_opcodes() if x[0]!='equal']
    if not ops:return ('','',0,0,0,0)
    i1=min(x[1] for x in ops);i2=max(x[2] for x in ops);j1=min(x[3] for x in ops);j2=max(x[4] for x in ops)
    return a[i1:i2],b[j1:j2],i1,i2,j1,j2

def common_substrings(command, text, min_len=2, max_len=18):
    found=[]
    for n in range(min(max_len,len(command)),min_len-1,-1):
        for i in range(len(command)-n+1):
            s=command[i:i+n]
            if s in text and not any(s in x for x in found): found.append(s)
    return found[:8]

def grams(s): return Counter(s[i:i+n] for n in (2,3,4) for i in range(max(0,len(s)-n+1)))
def cosine(a,b):
    d=sum(v*b.get(k,0) for k,v in a.items()); na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return d/(na*nb+1e-12)

def effect_signature(ep):
    old,new,i1,i2,j1,j2=changed_span(ep.before,ep.after)
    if ep.noop or (not old and not new): return ('NOOP',)
    left=max(ep.before.rfind('。',0,i1),ep.before.rfind('、',0,i1),ep.before.rfind('=',0,i1))+1
    rights=[x for x in (ep.before.find('。',i2),ep.before.find('、',i2)) if x>=0]; right=min(rights)+1 if rights else len(ep.before)
    left2=max(ep.after.rfind('。',0,j1),ep.after.rfind('、',0,j1),ep.after.rfind('=',0,j1))+1
    rights2=[x for x in (ep.after.find('。',j2),ep.after.find('、',j2)) if x>=0]; right2=min(rights2)+1 if rights2 else len(ep.after)
    return (ep.before[left:right].replace(old,'<X>',1),ep.after[left2:right2].replace(new,'<X>',1))

def candidate_lattice(ep, max_candidates=24):
    if ep.noop:return [(ep.command,'','',('NOOP',),0)]
    old,new,*_=changed_span(ep.before,ep.after)
    common_b=common_substrings(ep.command,ep.before); common_a=common_substrings(ep.command,ep.after)
    ent_candidates=[x for x in common_b if x in ep.after]
    val_candidates=[x for x in common_a if x not in ep.before]
    ent_candidates=(ent_candidates[:4] or [''])
    val_candidates=(val_candidates[:4] or [''])
    sig=effect_signature(ep); out=[]
    for ent in ent_candidates:
      for val in val_candidates:
        residue=ep.command
        if ent: residue=residue.replace(ent,'<E>',1)
        if val: residue=residue.replace(val,'<V>',1)
        recon=residue.replace('<E>',ent,1).replace('<V>',val,1)
        recon_cost=sum(a!=b for a,b in zip(recon,ep.command))+abs(len(recon)-len(ep.command))
        mdl=len(residue)+len(ent)+len(val)+len(json.dumps(sig,ensure_ascii=False))*.12+recon_cost*4
        out.append((residue,ent,val,sig,mdl))
        swapped=ep.command
        if ent:swapped=swapped.replace(ent,'<V>',1)
        if val:swapped=swapped.replace(val,'<E>',1)
        out.append((swapped,val,ent,sig,mdl+1.5))
    return sorted(out,key=lambda x:x[-1])[:max_candidates]

def apply_sig(before, ent, val, sig):
    if sig==('NOOP',): return before
    if not val:return None
    b,a=sig; pat=re.escape(b).replace(re.escape('<X>'),'(?P<X>.+?)')
    m=re.search(pat,before)
    if not m:return None
    return before[:m.start()]+a.replace('<X>',val)+before[m.end():]

class JointLattice:
    def __init__(self,max_candidates=24):
        self.max_candidates=max_candidates; self.primitives={}; self.residue_edges=defaultdict(Counter); self.tentative={}
    def fit(self,rows):
        for ep in rows:self.observe(ep,commit=True)
        ranked=sorted(self.residue_edges.items(), key=lambda kv: sum(kv[1].values()), reverse=True)[:48]
        self.residue_edges=defaultdict(Counter, ranked)
        self._gram_cache={k:grams(k) for k in self.residue_edges}
        return self
    def observe(self,ep,commit=False):
        cands=candidate_lattice(ep,self.max_candidates)
        for residue,ent,val,sig,mdl in cands:
            key=json.dumps(sig,ensure_ascii=False)
            score=1/(1+mdl)
            self.primitives.setdefault(key,sig)
            if commit:self.residue_edges[residue][key]+=score
            else:self.tentative[residue]=(key,score)
        return cands
    def bridge(self,ep): self.observe(ep,commit=False)
    def consolidate(self,ep):
        for residue,ent,val,sig,mdl in candidate_lattice(ep,self.max_candidates):
            key=json.dumps(sig,ensure_ascii=False)
            if residue in self.tentative:
                old,score=self.tentative[residue]
                if old==key:self.residue_edges[residue][key]+=score+1/(1+mdl); del self.tentative[residue]
                else:del self.tentative[residue]
    def contradict(self,ep):
        for residue,_,_,sig,_ in candidate_lattice(ep,self.max_candidates):
            key=json.dumps(sig,ensure_ascii=False)
            if residue in self.tentative and self.tentative[residue][0]!=key:del self.tentative[residue]
    def predict(self,ep):
        candidates=candidate_lattice(ep,self.max_candidates); scored=[]
        for residue,ent,val,sig,mdl in candidates:
            q=grams(residue)
            for known,counts in self.residue_edges.items():
                sim=cosine(q,self._gram_cache.get(known,grams(known)))
                for key,support in counts.items():
                    scored.append((sim+0.025*math.log1p(support)-0.002*mdl,key,ent,val))
            if residue in self.tentative:
                key,s=self.tentative[residue]; scored.append((0.18+s,key,ent,val))
        scored.sort(reverse=True)
        if not scored or scored[0][0]<.20 or (len(scored)>1 and scored[0][0]-scored[1][0]<.01):return None
        _,key,ent,val=scored[0]
        return apply_sig(ep.before,ent,val,self.primitives.get(key,json.loads(key)))

def evaluate(seed,n):
    rng=random.Random(seed); train=[make_episode(rng) for _ in range(n)]+[make_episode(rng,noop=True) for _ in range(max(12,n//6))]
    t=time.perf_counter(); model=JointLattice().fit(train); train_s=time.perf_counter()-t
    bridged=pickle.loads(pickle.dumps(model)); tentative=pickle.loads(pickle.dumps(model)); wrong=pickle.loads(pickle.dumps(model))
    for kind in FORMS:
        d1=make_episode(rng,kind,HELD_LEXEME[kind]); d2=make_episode(rng,kind,HELD_LEXEME[kind])
        tentative.bridge(d1); bridged.bridge(d1); bridged.consolidate(d2); wrong.bridge(d1)
        other={'loc':'owner','owner':'state','state':'loc'}[kind]
        wrong.contradict(make_episode(rng,other,HELD_LEXEME[other]))
    def rows(forms,rename=False,sf=None,count=12):
        return [make_episode(rng,k:=rng.choice(tuple(FORMS)),forms[k],sf,rename) for _ in range(count)]
    splits={
      'seen':rows(FORMS), 'held_order':rows(HELD_ORDER), 'unseen_lexeme':rows(HELD_LEXEME),
      'rename_unseen_lexeme':rows(HELD_LEXEME,True), 'nested':rows(NESTED),
      'subject_omission':rows(OMITTED), 'alternate_state':rows(FORMS,sf=rng.choice(STATE_FORMS[1:])),
      'noop':[make_episode(rng,noop=True) for _ in range(12)],
    }
    models={'base':model,'tentative_one_shot':tentative,'consolidated_two_shot':bridged,'contradiction_retracted':wrong}; out={}
    for split,items in splits.items():
      out[split]={}
      for name,m in models.items():
        t=time.perf_counter(); preds=[m.predict(x) for x in items]; ms=(time.perf_counter()-t)*1000/len(items)
        out[split][name]={'accuracy':sum(p==x.after for p,x in zip(preds,items))/len(items),'abstention':sum(p is None for p in preds)/len(items),'ms_query':ms}
    allc=[len(candidate_lattice(x)) for x in splits['seen']]
    out.update(model_bytes=len(pickle.dumps(model)),bridged_bytes=len(pickle.dumps(bridged)),primitive_count=len(model.primitives),residue_count=len(model.residue_edges),tentative_count=len(tentative.tentative),candidate_mean=statistics.mean(allc),candidate_max=max(allc),training_seconds=train_s,training_examples=len(train))
    return out

def summarize(raw):
    out={}
    for n,runs in raw.items():
      out[n]={}
      for split in ('seen','held_order','unseen_lexeme','rename_unseen_lexeme','nested','subject_omission','alternate_state','noop'):
        out[n][split]={}
        for model in ('base','tentative_one_shot','consolidated_two_shot','contradiction_retracted'):
          out[n][split][model]={k:statistics.mean(r[split][model][k] for r in runs) for k in ('accuracy','abstention','ms_query')}
      for k in ('model_bytes','bridged_bytes','primitive_count','residue_count','tentative_count','candidate_mean','candidate_max','training_seconds','training_examples'):
        out[n][k]=statistics.mean(r[k] for r in runs)
    return out

def main():
    raw={str(n):[evaluate(s,n) for s in (1,7,19)] for n in (30,90,180)}
    payload={'hypothesis':'Joint Role-Effect MDL Lattice with Reversible Primitive Bridging','seeds':[1,7,19],'train_sizes':[30,90,180],'raw':raw,'summary':summarize(raw),'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'proposal O(H*L^2), scoring O(H*R*G), H<=24','free_japanese_integrated_gate':0.0,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open('results_cycle_008.json','w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload['summary']['180'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
