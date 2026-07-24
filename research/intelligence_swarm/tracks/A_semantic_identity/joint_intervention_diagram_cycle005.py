#!/usr/bin/env python3
from __future__ import annotations
import json, math, random, resource, statistics, time
from dataclasses import dataclass
from pathlib import Path
import numpy as np

SEEDS=(1,7,19)
TEXT_DIM=64
WORLD_DIM=12
LATENT=6
MOVES=((1,0),(-1,0),(0,1),(0,-1))
RELS=((1,0),(-1,0),(0,1),(0,-1))
DOMAINS={
'd1':{'rel':['ネヴァ','トルム','リュネ','モルカ'],'move':['パルス','デム','フィン','ノクト'],'goal':['整合','収束'],'anchor':'ビーコン'},
'd2':{'rel':['アーク','ボイド','シータ','グラフ'],'move':['アル','ベタ','ガン','デル'],'goal':['安定','選択'],'anchor':'中枢'},
'd3':{'rel':['ソル','ヴァク','テラ','ノア'],'move':['キル','ラグ','ミュ','セド'],'goal':['均衡','終端'],'anchor':'基点'},
}
FORMS={
'd1':{
'base':'{anchor}基準で{rel}側の{name}へ{move}し、{goal}へ。',
'held':'{goal}にするため、{anchor}から{rel}の{name}だけ{move}して。',
'word':'先に{goal}を指定。対象は{anchor}照合で{rel}の{name}、処理は{move}。',
'omission':'さっきの{rel}側だけ{move}して{goal}へ。',
'free':'えっと、{anchor}から見て{rel}っぽい{name}だけを{move}して、{goal}にして。',
'para':'補足を挟む。ほかはそのまま。\n{anchor}基準で{rel}の{name}だけ{move}し、最終的に{goal}。'},
'd2':{
'base':'{anchor}観測、{name}は{rel}位相。{move}を適用し{goal}核へ。',
'held':'{rel}位相の{name}に{move}、終端は{goal}核。',
'word':'終端{goal}核。{anchor}観測で{rel}位相の{name}を{move}。',
'omission':'先ほどの{rel}位相だけ。{move}して{goal}核へ。',
'free':'あの、{anchor}で{rel}っぽい{name}だけに{move}を掛けて、{goal}核で。',
'para':'観測記録を追記。非対象は保持。\n{rel}位相の{name}へ{move}、結果{goal}核。'},
'd3':{
'base':'{anchor}照合、{rel}帯の{name}を{move}化し{goal}相へ。',
'held':'{goal}相へ移す対象は{rel}帯の{name}。{move}化。',
'word':'到達相は{goal}。{move}化するのは{anchor}から{rel}帯の{name}。',
'omission':'例の{rel}帯だけ{move}化して{goal}相へ。',
'free':'うーん、{anchor}から{rel}っぽい{name}だけ{move}化して、{goal}相にして。',
'para':'前提は維持。対象外は不変。\n{rel}帯の{name}だけ{move}化し、終端を{goal}相に。'}
}

@dataclass(frozen=True)
class World:
    positions: tuple[tuple[int,int],...]
    target: int
    move: tuple[int,int]
    goal: int


def hidx(s,dim,salt):
    h=2166136261^salt
    for ch in s:
        h^=ord(ch); h=(h*16777619)&0xffffffff
    return h%dim,(-1.0 if h>>31 else 1.0)

def norm(v):
    v=np.asarray(v,dtype=np.float32); z=float(np.linalg.norm(v)) or 1.0
    return v/z

def text_features(text):
    v=np.zeros(TEXT_DIM,dtype=np.float32); p='^'+text+'$'
    for n in (1,2,3,4,5):
        for i in range(len(p)-n+1):
            j,s=hidx(p[i:i+n],TEXT_DIM,31+n); v[j]+=s
    return norm(v)

def world_features(w,target=None,move=None,goal=None):
    target=w.target if target is None else target; move=w.move if move is None else move; goal=w.goal if goal is None else goal
    v=np.zeros(WORLD_DIM,dtype=np.float32)
    tx,ty=w.positions[target]
    for i,(x,y) in enumerate(w.positions[:8]):
        dx,dy=x-tx,y-ty
        vals=(dx,dy,abs(dx),abs(dy),dx*dy,dx*dx+dy*dy)
        for k,val in enumerate(vals):
            j=(i*7+k)%WORLD_DIM; v[j]+=float(val)
    nx,ny=tx+move[0],ty+move[1]
    v[(target*3)%WORLD_DIM]+=nx-tx
    v[(target*3+1)%WORLD_DIM]+=ny-ty
    v[(target*3+2)%WORLD_DIM]+=1.0 if goal else -1.0
    return norm(v)

def make_world(rng,nobj=8):
    ps=[]
    for r in RELS: ps.append((r[0]*rng.choice((1,2,3)),r[1]*rng.choice((1,2,3))))
    while len(ps)<nobj:
        p=(rng.randint(-4,4),rng.randint(-4,4))
        if p!=(0,0) and p not in ps: ps.append(p)
    return World(tuple(ps),rng.randrange(4),rng.choice(MOVES),rng.randrange(2))

def rel_index(w,target=None):
    t=w.target if target is None else target; x,y=w.positions[t]
    if abs(x)>=abs(y): return 0 if x>0 else 1
    return 2 if y>0 else 3

def render(w,domain,cond,rng,override=None):
    rel,move,goal,target=(rel_index(w),MOVES.index(w.move),w.goal,w.target)
    if override is not None:
        rel,move,goal,target=override
    d=DOMAINS[domain]
    return FORMS[domain][cond].format(anchor=d['anchor'],rel=d['rel'][rel],move=d['move'][move],goal=d['goal'][goal],name=f'{domain.upper()}-{rng.randrange(10**9)}')

def paired_examples(seed,domain,n=24):
    rng=random.Random(seed*1009+sum(map(ord,domain))); out=[]
    factors=('identity','operation','goal','wording')
    for _ in range(n):
        w=make_world(rng); base=render(w,domain,'base',rng)
        factor=rng.choice(factors)
        rel,mi,gi,ti=rel_index(w),MOVES.index(w.move),w.goal,w.target
        if factor=='identity':
            cands=[i for i in range(4) if i!=rel]; rel2=rng.choice(cands)
            targets=[i for i in range(4) if rel_index(w,i)==rel2]
            ti2=targets[0] if targets else (ti+1)%4; changed=(rel2,mi,gi,ti2); cond='held'
        elif factor=='operation':
            mi2=rng.choice([i for i in range(4) if i!=mi]); changed=(rel,mi2,gi,ti); cond='held'
        elif factor=='goal':
            changed=(rel,mi,1-gi,ti); cond='held'
        else:
            changed=(rel,mi,gi,ti); cond=rng.choice(('word','omission','free','para'))
        text2=render(w,domain,cond,rng,changed)
        w2=World(w.positions,changed[3],MOVES[changed[1]],changed[2])
        out.append((base,text2,w,w2,factor))
    return out

def fit(seed,domains,shuffle_lang=False,shuffle_world=False):
    X=[]; Y=[]
    rng=random.Random(seed*31337)
    for d in domains:
        for a,b,w,w2,_ in paired_examples(seed,d):
            X.append(text_features(b)-text_features(a))
            Y.append(world_features(w2)-world_features(w))
    if shuffle_lang: rng.shuffle(X)
    if shuffle_world: rng.shuffle(Y)
    X=np.stack(X); Y=np.stack(Y)
    C=X.T@Y/len(X)
    U,S,Vt=np.linalg.svd(C,full_matrices=False)
    k=min(LATENT,len(S))
    P=U[:,:k]@np.diag(np.sqrt(S[:k]+1e-8))
    Q=Vt[:k,:].T@np.diag(np.sqrt(S[:k]+1e-8))
    return P.astype(np.float32),Q.astype(np.float32),S[:k]

def diagram_score(P,Q,base,current,w,c,m,g):
    dl=(text_features(current)-text_features(base))@P
    dw=(world_features(w,c,m,g)-world_features(w))@Q
    return float(dl@dw)/(float(np.linalg.norm(dl)*np.linalg.norm(dw))+1e-8)

def eval_condition(seed,P,Q,domain,cond,n=8):
    rng=random.Random(seed*91009+sum(map(ord,domain+cond))); joint=target=move=goal=0
    for _ in range(n):
        w=make_world(rng); base=render(w,domain,'base',rng); current=render(w,domain,cond,rng)
        best=(-1e9,None,None,None)
        for c in range(len(w.positions)):
            for m in MOVES:
                for g in range(2):
                    s=diagram_score(P,Q,base,current,w,c,m,g)
                    if s>best[0]: best=(s,c,m,g)
        _,pc,pm,pg=best
        joint+=pc==w.target and pm==w.move and pg==w.goal
        target+=pc==w.target; move+=pm==w.move; goal+=pg==w.goal
    return {'joint':joint/n,'target':target/n,'move':move/n,'goal':goal/n}

def inverse(seed,P,Q,domain,n=8):
    rng=random.Random(seed*81013+sum(map(ord,domain))); ok=0
    for _ in range(n):
        w=make_world(rng); z=world_features(w,w.target,w.move,w.goal)-world_features(w)
        wz=z@Q; opts=[]
        for cond in ('held','word','omission','free','para'):
            base=render(w,domain,'base',rng); cur=render(w,domain,cond,rng)
            l=(text_features(cur)-text_features(base))@P
            opts.append((float(l@wz)/(float(np.linalg.norm(l)*np.linalg.norm(wz))+1e-8),cond))
        _,pred=max(opts); ok+=pred=='held'
    return ok/n

def counterfactual_repair(seed,P,Q,domain,n=8):
    rng=random.Random(seed*71023+sum(map(ord,domain))); ok=0
    for _ in range(n):
        w=make_world(rng); wrong=World(w.positions,w.target,rng.choice([m for m in MOVES if m!=w.move]),w.goal)
        base=render(wrong,domain,'base',rng); cur=render(w,domain,'held',rng)
        scores=[]
        for m in MOVES:
            scores.append((diagram_score(P,Q,base,cur,wrong,wrong.target,m,wrong.goal),m))
        ok+=max(scores)[1]==w.move
    return ok/n

def run_seed(seed):
    models={
      'correct':fit(seed,('d1','d2')),
      'lang_shuffle':fit(seed,('d1','d2'),shuffle_lang=True),
      'world_shuffle':fit(seed,('d1','d2'),shuffle_world=True),
    }
    out={'seed':seed,'singular_values':models['correct'][2].tolist(),'modes':{}}
    for mode,(P,Q,S) in models.items():
        out['modes'][mode]={}
        for domain in ('d1','d2','d3'):
            out['modes'][mode][domain]={}
            for cond in ('held','word','omission','free','para'):
                out['modes'][mode][domain][cond]=eval_condition(seed,P,Q,domain,cond)
            out['modes'][mode][domain]['inverse']=inverse(seed,P,Q,domain)
            out['modes'][mode][domain]['repair']=counterfactual_repair(seed,P,Q,domain)
    return out

def path_mean(rows,*path):
    vals=[]
    for r in rows:
        x=r
        for p in path: x=x[p]
        vals.append(x)
    return statistics.mean(vals)

def main():
    t=time.perf_counter(); rows=[run_seed(s) for s in SEEDS]; elapsed=time.perf_counter()-t
    mean={}
    for mode in ('correct','lang_shuffle','world_shuffle'):
        mean[mode]={}
        for d in ('d1','d2','d3'):
            mean[mode][d]={}
            for c in ('held','word','omission','free','para'):
                mean[mode][d][c]={k:path_mean(rows,'modes',mode,d,c,k) for k in ('joint','target','move','goal')}
            mean[mode][d]['inverse']=path_mean(rows,'modes',mode,d,'inverse')
            mean[mode][d]['repair']=path_mean(rows,'modes',mode,d,'repair')
    gaps={d:{c:[r['modes']['correct'][d][c]['joint']-max(r['modes']['lang_shuffle'][d][c]['joint'],r['modes']['world_shuffle'][d][c]['joint']) for r in rows] for c in ('held','word','omission','free','para')} for d in ('d1','d2','d3')}
    strict=all(gaps[d][c][i]>=0.10 for d in ('d2','d3') for c in ('free','word') for i in range(len(SEEDS)))
    result={
      'cycle':'A_SEMANTIC_IDENTITY_005',
      'hypothesis':'Jointly Emergent Language-World Intervention Diagrams from Paired Change Commutators',
      'seeds':list(SEEDS),'per_seed':rows,'mean':mean,'gaps':gaps,'strict_progress_gate':strict,
      'resources':{
        'model_bytes':int((TEXT_DIM*LATENT+WORLD_DIM*LATENT)*4),
        'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'runtime_sec':elapsed,
        'train_pairs_per_domain':24,
        'candidate_count':64,
        'estimated_update_ops_per_pair':TEXT_DIM*WORLD_DIM,
        'estimated_inference_ops_per_query':64*LATENT*(TEXT_DIM+WORLD_DIM)
      },
      'status':{'G1':False,'highschool_level':False,'native_japanese':False,'weak_smartphone_verified':False}
    }
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
