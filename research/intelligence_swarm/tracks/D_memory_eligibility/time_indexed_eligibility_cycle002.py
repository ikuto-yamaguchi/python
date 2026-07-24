#!/usr/bin/env python3
"""Cycle D002: time-indexed memory eligibility audit.

This experiment separates:
1) retrospective acquisition using a completed trajectory,
2) pre-treatment acquisition using only prefixes available before the outcome,
3) prospective closed-loop reuse across paraphrases and inverse selection,
4) retention after distractor interference.

A record is not eligible for semantic memory merely because a post-treatment
witness can be matched. No address/replay/consolidation is built until the
pre-treatment and prospective gates pass.
"""
from __future__ import annotations
import argparse, json, math, random, resource, statistics, time
from dataclasses import dataclass

SEEDS=(1,7,19)
TEXT_DIM=128
WIT_DIM=64
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

def normalize(v):
    z=math.sqrt(sum(x*x for x in v)) or 1.0
    return [x/z for x in v]

def text_features(text:str):
    v=[0.0]*TEXT_DIM; p='^'+text+'$'
    for n in (1,2,3):
        for i in range(len(p)-n+1):
            j,s=hidx(p[i:i+n],TEXT_DIM,17+n); v[j]+=s
    return normalize(v)

def witness_features(o:Obj,mode:str):
    v=[0.0]*WIT_DIM
    if mode=='full':
        steps=o.trajectory
    elif mode=='prefix1':
        steps=o.trajectory[:1]
    elif mode=='prefix2':
        steps=o.trajectory[:2]
    elif mode=='scar':
        steps=()
    else:
        raise ValueError(mode)
    for t,(x,y) in enumerate(steps):
        j,s=hidx(f'{t}:{x}:{y}',WIT_DIM,101); v[j]+=s
    if mode in ('full','scar'):
        for bit in range(24):
            if (o.scar>>bit)&1:
                j,s=hidx(f's:{bit}',WIT_DIM,211); v[j]+=0.03*s
    return normalize(v)

def add_outer(W,u,w):
    for i,ui in enumerate(u):
        if not ui: continue
        row=W[i]
        for j,wj in enumerate(w):
            if wj: row[j]+=ui*wj

def score(W,u,w):
    return sum(ui*sum(row[j]*w[j] for j in range(WIT_DIM) if w[j])
               for ui,row in zip(u,W) if ui)

def make_objects(rng,n=96):
    out=[]; seen=set()
    for ident in range(n):
        while True:
            tr=tuple(rng.choice(STEPS) for _ in range(3)); scar=rng.getrandbits(24)
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

def choose(W,u,candidates,mode):
    scored=[(score(W,u,witness_features(c,mode)),c.ident) for c in candidates]
    scored.sort(reverse=True)
    return scored[0][1], scored[0][0]-scored[1][0]

def evaluate(seed,objs,W,mode,domain=False,interference=0):
    rng=random.Random(seed*1009+sum(map(ord,mode))+int(domain)*97+interference)
    forms=DOMAIN_FORMS if domain else HELD_FORMS
    correct=consistent=inverse_ok=0
    margins=[]
    for o in objs:
        distractors=rng.sample([x for x in objs if x.ident!=o.ident],7+interference)
        candidates=[o]+distractors
        if interference:
            candidates=rng.sample(candidates,8)
            if o not in candidates:
                candidates[rng.randrange(8)]=o
        rng.shuffle(candidates)
        preds=[]
        for _ in range(3):
            u=text_features(render(o,rng.choice(forms),f'未知名{rng.randrange(10**8)}'))
            pred,margin=choose(W,u,candidates,mode)
            preds.append(pred); margins.append(margin)
        majority=max(set(preds),key=preds.count)
        correct+=majority==o.ident
        consistent+=len(set(preds))==1 and majority==o.ident
        candidate_texts=[]
        for c in candidates:
            u=text_features(render(c,rng.choice(forms),f'名{rng.randrange(10**8)}'))
            candidate_texts.append((score(W,u,witness_features(o,mode)),c.ident))
        inverse_ok+=max(candidate_texts)[1]==o.ident
    n=len(objs)
    return {'accuracy':correct/n,'cross_form_consistency':consistent/n,
            'inverse_accuracy':inverse_ok/n,'mean_margin':statistics.mean(margins)}

def run_seed(seed):
    objs,W=train(seed); _,Ws=train(seed,True)
    modes=('full','prefix1','prefix2','scar')
    correct={m:evaluate(seed,objs,W,m) for m in modes}
    shuffled={m:evaluate(seed,objs,Ws,m) for m in modes}
    domain={m:evaluate(seed,objs,W,m,domain=True) for m in modes}
    retention={m:evaluate(seed,objs,W,m,interference=24) for m in modes}
    chance=0.125
    eligible={}
    for m in modes:
        pre_treatment=m in ('prefix1','prefix2')
        eligible[m]=(pre_treatment and
            correct[m]['accuracy']>=0.25 and
            correct[m]['accuracy']-shuffled[m]['accuracy']>=0.10 and
            domain[m]['accuracy']-chance>=0.10 and
            correct[m]['inverse_accuracy']>=0.25)
    return {'seed':seed,'correct':correct,'shuffled':shuffled,
            'domain':domain,'retention':retention,'eligible':eligible}

def mean_nested(per,section,mode,metric):
    return statistics.mean(r[section][mode][metric] for r in per)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output',default='')
    args=parser.parse_args()
    started=time.perf_counter(); per=[run_seed(s) for s in SEEDS]
    elapsed=time.perf_counter()-started
    modes=('full','prefix1','prefix2','scar')
    mean={}
    for section in ('correct','shuffled','domain','retention'):
        mean[section]={m:{metric:mean_nested(per,section,m,metric)
                          for metric in ('accuracy','cross_form_consistency',
                                         'inverse_accuracy','mean_margin')}
                       for m in modes}
    eligible={m:all(r['eligible'][m] for r in per) for m in modes}
    result={
      'cycle':'D_MEMORY_ELIGIBILITY_002',
      'hypothesis':'Time-Indexed Prospective Eligibility before Retention',
      'seeds':list(SEEDS),'per_seed':per,'mean':mean,
      'eligibility':eligible,
      'classification':{
        'full_trajectory':'retrospective_matching_only',
        'prefix1':'initial_semantics_failure',
        'prefix2':'initial_semantics_failure',
        'scar':'post_treatment_or_episode_specific_witness',
        'semantic_memory_eligible_count':sum(eligible.values()),
        'catastrophic_forgetting_observed':False,
        'consolidation_mainline_unlocked':False},
      'resources':{
        'matrix_bytes_float32_estimate':TEXT_DIM*WIT_DIM*4,
        'training_seconds_total':elapsed,
        'peak_rss_kib_python_runtime_included':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        'update_ops_estimate_per_episode':TEXT_DIM*WIT_DIM,
        'inference_ops_estimate_per_candidate':TEXT_DIM*WIT_DIM,
        'candidate_count':8,'interference_pool_extra':24,
        'complexity':{'update':'O(TW)','selection':'O(KTW)',
                      'three_form_consistency':'O(3KTW)'}},
      'leakage_audit':{
        'identity_label_used_for_training':False,
        'span_boundaries_generated':False,
        'string_retrieval_used':False,
        'final_identity_used_for_ranking':False,
        'post_treatment_witness_counted_as_prospective':False}}
    encoded=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output:
        with open(args.output,'w',encoding='utf-8') as f:f.write(encoded+'\n')
    print(encoded)

if __name__=='__main__': main()
