#!/usr/bin/env python3
from __future__ import annotations
import json, math, random, resource, statistics, time
from dataclasses import dataclass

SEEDS=(1,7,19); TEXT_DIM=256; WIT_DIM=96
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
DISJOINT_FORMS=(
'{name}は初動が{a0}、次動が{a1}、終動が{a2}の個体。',
'軌跡の三拍が{a0}・{a1}・{a2}だった{name}を指定する。')
PARAGRAPH_FORM='いくつか候補がいる。\nその中で{name}について説明する。\n動きは{d0}、その後{d1}、最後が{d2}だった。'
OMIT_FORM='さっき話した方。最初は{d0}、次は{d1}、最後は{d2}。それを選んで。'

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

def witness_features(o:Obj,mode:str='joint')->list[float]:
    v=[0.0]*WIT_DIM
    if mode in ('joint','trajectory'):
        for t,(x,y) in enumerate(o.trajectory):
            j,s=hidx(f'{t}:{x}:{y}',WIT_DIM,101); v[j]+=s
    if mode in ('joint','scar'):
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

def make_objects(rng,n=192):
    out=[]; seen=set()
    for ident in range(n):
        while True:
            tr=tuple(rng.choice(STEPS) for _ in range(3)); scar=rng.getrandbits(24)
            if (tr,scar) not in seen: seen.add((tr,scar)); break
        out.append(Obj(ident,tr,scar))
    return out

def render(o,form,name):
    ds=[]; aliases=[]
    for step in o.trajectory:
        d,a=DIR[step]; ds.append(d); aliases.append(a)
    return form.format(name=name,d0=ds[0],d1=ds[1],d2=ds[2],a0=aliases[0],a1=aliases[1],a2=aliases[2])

def train(seed,shuffle=False):
    rng=random.Random(seed); objs=make_objects(rng)
    W=[[0.0]*WIT_DIM for _ in range(TEXT_DIM)]; episodes=[]
    for o in objs:
        for form in TRAIN_FORMS:
            u=text_features(render(o,form,f'個体{rng.randrange(100000,999999)}'))
            episodes.append((u,witness_features(o)))
    ws=[w for _,w in episodes]
    if shuffle: rng.shuffle(ws)
    for (u,_),w in zip(episodes,ws): add_outer(W,u,w)
    return objs,W,episodes

def query_text(o,condition,rng):
    name=f'対象{rng.randrange(1000000,9999999)}'
    if condition=='held': return render(o,rng.choice(HELD_FORMS),name)
    if condition=='rename': return render(o,rng.choice(HELD_FORMS),f'未知名{rng.randrange(10**8)}')
    if condition=='word_order':
        return f'最後は{DIR[o.trajectory[2]][0]}。その前が{DIR[o.trajectory[1]][0]}。最初は{DIR[o.trajectory[0]][0]}。該当する{name}。'
    if condition=='omission': return render(o,OMIT_FORM,name)
    if condition=='paragraph': return render(o,PARAGRAPH_FORM,name)
    if condition=='free':
        return f'ねえ、{name}なんだけど、出だし{DIR[o.trajectory[0]][0]}で、次{DIR[o.trajectory[1]][0]}、ラスト{DIR[o.trajectory[2]][0]}だったやつ。あれをお願い。'
    if condition=='domain': return render(o,rng.choice(DISJOINT_FORMS),name)
    raise ValueError(condition)

def evaluate(seed,objs,W,condition,mode='joint'):
    rng=random.Random(seed*1009+sum(map(ord,condition))); correct=0
    for o in objs:
        candidates=[o]+rng.sample([x for x in objs if x.ident!=o.ident],7); rng.shuffle(candidates)
        u=text_features(query_text(o,condition,rng))
        pred=max(candidates,key=lambda c:score(W,u,witness_features(c,mode)))
        correct+=pred.ident==o.ident
    return correct/len(objs)

def inverse(seed,objs,W,domain=False):
    rng=random.Random(seed*2017+7); correct=0
    forms=DISJOINT_FORMS if domain else HELD_FORMS
    for o in objs:
        candidates=[o]+rng.sample([x for x in objs if x.ident!=o.ident],7); rng.shuffle(candidates)
        scored=[]
        for c in candidates:
            u=text_features(render(c,rng.choice(forms),f'名{rng.randrange(10**7)}'))
            scored.append((score(W,u,witness_features(o)),c.ident))
        correct+=max(scored)[1]==o.ident
    return correct/len(objs)

def surface(seed,episodes,objs,domain=False):
    rng=random.Random(seed*3037+11); correct=0
    train_u=[u for u,_ in episodes]; train_w=[w for _,w in episodes]
    obj_w=[witness_features(o) for o in objs]
    forms=DISJOINT_FORMS if domain else HELD_FORMS
    for o in objs:
        u=text_features(render(o,rng.choice(forms),f'対象{rng.randrange(10**7)}'))
        idx=max(range(len(train_u)),key=lambda k:sum(a*b for a,b in zip(u,train_u[k])))
        pred=max(range(len(objs)),key=lambda k:sum(a*b for a,b in zip(train_w[idx],obj_w[k])))
        correct+=objs[pred].ident==o.ident
    return correct/len(objs)

def run_seed(seed):
    objs,W,episodes=train(seed); _,Ws,_=train(seed,True)
    conds=('held','rename','word_order','omission','paragraph','free','domain')
    return {'seed':seed,
      'correct':{c:evaluate(seed,objs,W,c) for c in conds},
      'shuffled':{c:evaluate(seed,objs,Ws,c) for c in conds},
      'surface':{'held':surface(seed,episodes,objs),'domain':surface(seed,episodes,objs,True)},
      'inverse_held':inverse(seed,objs,W),'inverse_domain':inverse(seed,objs,W,True),
      'lesions':{'trajectory_only':evaluate(seed,objs,W,'held','trajectory'),'scar_only':evaluate(seed,objs,W,'held','scar')}}

def main():
    started=time.perf_counter(); per=[run_seed(s) for s in SEEDS]; elapsed=time.perf_counter()-started
    conds=('held','rename','word_order','omission','paragraph','free','domain')
    mean=lambda xs:statistics.mean(xs)
    result={'cycle':'A_SEMANTIC_IDENTITY_001','hypothesis':'Utterance-Witness Synchrony Binding without Span Proposals','seeds':list(SEEDS),'per_seed':per,
      'mean':{'correct':{c:mean([r['correct'][c] for r in per]) for c in conds},
              'shuffled':{c:mean([r['shuffled'][c] for r in per]) for c in conds},
              'surface':{c:mean([r['surface'][c] for r in per]) for c in ('held','domain')},
              'inverse_held':mean([r['inverse_held'] for r in per]),'inverse_domain':mean([r['inverse_domain'] for r in per]),
              'lesions':{k:mean([r['lesions'][k] for r in per]) for k in ('trajectory_only','scar_only')}},
      'resources':{'matrix_bytes_float32_estimate':TEXT_DIM*WIT_DIM*4,'training_seconds_total':elapsed,
        'peak_rss_kib_python_runtime_included':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        'update_ops_estimate_per_episode':TEXT_DIM*WIT_DIM,'inference_ops_estimate_per_candidate':TEXT_DIM*WIT_DIM,
        'complexity':{'update':'O(TW)','candidate_scoring':'O(KTW)'}},
      'leakage_audit':{'identity_label_used_in_training':False,'span_boundaries_generated':False,
        'string_retrieval_used_by_main_method':False,'final_test_outcome_used_for_training':False}}
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
