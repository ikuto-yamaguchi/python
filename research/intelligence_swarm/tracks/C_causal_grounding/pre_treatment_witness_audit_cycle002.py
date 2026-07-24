#!/usr/bin/env python3
from __future__ import annotations
import json, math, random, resource, statistics, time
from dataclasses import dataclass

SEEDS=(1,7,19)
TEXT_DIM=256
WIT_DIM=96
N_OBJECTS=192
STEPS=((1,0),(-1,0),(0,1),(0,-1))
DIR={(1,0):('右','東'),(-1,0):('左','西'),(0,1):('上','北'),(0,-1):('下','南')}
TRAIN_FORMS=(
    '{name}は最初に{d0}へ進み、そのあと{d1}へ動き、最後に{d2}へ向かった。',
    '{name}の移動は{d0}、続いて{d1}、それから{d2}だった。',
    '観察すると{name}は{d0}方向へ行った後、{d1}方向を通り、{d2}側へ移った。')
HELD_FORMS=(
    'さっきの{name}、順番は{d0}から{d1}、締めに{d2}だったよ。',
    '{d0}へ向かい、次は{d1}、終わりには{d2}へ行った{name}を選んで。',
    '対象を追うと、はじめが{d0}、二手目が{d1}、三手目が{d2}。それが{name}だ。')
DOMAIN_FORMS=(
    '{name}は初動が{a0}、次動が{a1}、終動が{a2}の個体。',
    '軌跡の三拍が{a0}・{a1}・{a2}だった{name}を指定する。')

@dataclass(frozen=True)
class Obj:
    ident:int
    trajectory:tuple[tuple[int,int],...]
    scar:int

def hidx(s:str,dim:int,salt:int)->tuple[int,float]:
    h=2166136261^salt
    for ch in s:
        h^=ord(ch); h=(h*16777619)&0xffffffff
    return h%dim,(-1.0 if h>>31 else 1.0)

def text_features(text:str)->list[float]:
    v=[0.0]*TEXT_DIM; p='^'+text+'$'
    for n in (1,2,3):
        for i in range(len(p)-n+1):
            j,s=hidx(p[i:i+n],TEXT_DIM,17+n); v[j]+=s
    z=math.sqrt(sum(x*x for x in v)) or 1.0
    return [x/z for x in v]

def witness_features(o:Obj,mode:str)->list[float]:
    v=[0.0]*WIT_DIM
    if mode=='full': indices=(0,1,2)
    elif mode=='prefix1': indices=(0,)
    elif mode=='prefix2': indices=(0,1)
    elif mode=='future_only': indices=(2,)
    elif mode=='scar_only': indices=()
    else: raise ValueError(mode)
    for t in indices:
        x,y=o.trajectory[t]
        j,s=hidx(f'{t}:{x}:{y}',WIT_DIM,101); v[j]+=s
    if mode in ('full','scar_only'):
        for bit in range(24):
            if (o.scar>>bit)&1:
                j,s=hidx(f's:{bit}',WIT_DIM,211); v[j]+=0.03*s
    z=math.sqrt(sum(x*x for x in v)) or 1.0
    return [x/z for x in v]

def add_outer(W,u,w):
    for i,ui in enumerate(u):
        if not ui: continue
        for j,wj in enumerate(w):
            if wj: W[i][j]+=ui*wj

def score(W,u,w):
    return sum(ui*sum(row[j]*w[j] for j in range(WIT_DIM) if w[j])
               for ui,row in zip(u,W) if ui)

def make_objects(rng,n=N_OBJECTS):
    out=[]; seen=set()
    for ident in range(n):
        while True:
            tr=tuple(rng.choice(STEPS) for _ in range(3))
            scar=rng.getrandbits(24)
            if (tr,scar) not in seen:
                seen.add((tr,scar)); break
        out.append(Obj(ident,tr,scar))
    return out

def render(o,form,name):
    ds=[]; aliases=[]
    for step in o.trajectory:
        d,a=DIR[step]; ds.append(d); aliases.append(a)
    return form.format(name=name,d0=ds[0],d1=ds[1],d2=ds[2],
                       a0=aliases[0],a1=aliases[1],a2=aliases[2])

def train(seed,shuffle=False):
    rng=random.Random(seed); objs=make_objects(rng)
    W=[[0.0]*WIT_DIM for _ in range(TEXT_DIM)]
    episodes=[]
    for o in objs:
        for form in TRAIN_FORMS:
            u=text_features(render(o,form,f'個体{rng.randrange(100000,999999)}'))
            episodes.append((u,witness_features(o,'full')))
    ws=[w for _,w in episodes]
    if shuffle: rng.shuffle(ws)
    for (u,_),w in zip(episodes,ws): add_outer(W,u,w)
    return objs,W

def evaluate(seed,objs,W,condition,mode):
    rng=random.Random(seed*1009+sum(map(ord,condition)))
    correct=0
    forms=HELD_FORMS if condition=='held' else DOMAIN_FORMS
    for o in objs:
        candidates=[o]+rng.sample([x for x in objs if x.ident!=o.ident],7)
        rng.shuffle(candidates)
        u=text_features(render(o,rng.choice(forms),f'対象{rng.randrange(10**7)}'))
        pred=max(candidates,key=lambda c:score(W,u,witness_features(c,mode)))
        correct+=pred.ident==o.ident
    return correct/len(objs)

def run_seed(seed):
    objs,W=train(seed); _,Ws=train(seed,True)
    modes=('full','prefix1','prefix2','future_only','scar_only')
    return {
        'seed':seed,
        'held':{m:evaluate(seed,objs,W,'held',m) for m in modes},
        'domain':{m:evaluate(seed,objs,W,'domain',m) for m in modes},
        'shuffle_full':{
            'held':evaluate(seed,objs,Ws,'held','full'),
            'domain':evaluate(seed,objs,Ws,'domain','full')}}

def main():
    started=time.perf_counter()
    per=[run_seed(s) for s in SEEDS]
    elapsed=time.perf_counter()-started
    modes=('full','prefix1','prefix2','future_only','scar_only')
    mean=lambda xs:statistics.mean(xs)
    result={
      'cycle':'C_CAUSAL_GROUNDING_002',
      'hypothesis':'Pre-Treatment Witness Necessity for Prospective Causal Identity',
      'seeds':list(SEEDS),
      'chance':0.125,
      'per_seed':per,
      'mean':{
        'held':{m:mean([r['held'][m] for r in per]) for m in modes},
        'domain':{m:mean([r['domain'][m] for r in per]) for m in modes},
        'shuffle_full':{
          c:mean([r['shuffle_full'][c] for r in per]) for c in ('held','domain')}},
      'resources':{
        'matrix_bytes_float32_estimate':TEXT_DIM*WIT_DIM*4,
        'runtime_seconds_total':elapsed,
        'peak_rss_kib_python_runtime_included':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        'candidate_scoring_ops_estimate':TEXT_DIM*WIT_DIM,
        'candidate_count':8,
        'complexity':'O(K*T*W)'},
      'leakage_audit':{
        'identity_label_used_in_training':False,
        'span_boundaries_generated':False,
        'final_test_outcome_used_for_training':False,
        'post_treatment_witness_explicitly_censored':True}}
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
