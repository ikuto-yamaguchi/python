#!/usr/bin/env python3
from __future__ import annotations
import json, math, random, resource, statistics, time
import numpy as np
from dataclasses import dataclass

SEEDS=(1,7,19)
TEXT_DIM=256
CONS_DIM=64
MOVES=((1,0),(-1,0),(0,1),(0,-1))
RELS=((1,0),(-1,0),(0,1),(0,-1))

DOMAINS={
 'base':{
  'rel':{(1,0):('右側','東側'),(-1,0):('左側','西側'),(0,1):('上側','北側'),(0,-1):('下側','南側')},
  'move':{(1,0):('右へ','東へ'),(-1,0):('左へ','西へ'),(0,1):('上へ','北へ'),(0,-1):('下へ','南へ')},
  'anchor':'基準点'},
 'nova':{
  'rel':{(1,0):('ネヴァ域','セリオ域'),(-1,0):('トルム域','ガディア域'),(0,1):('リュネ域','ファル域'),(0,-1):('モルカ域','ゼイン域')},
  'move':{(1,0):('パルス化','リオ化'),(-1,0):('デム化','クオ化'),(0,1):('フィン化','サル化'),(0,-1):('ノクト化','ヴェル化')},
  'anchor':'ビーコン'},
 'quasar':{
  'rel':{(1,0):('アーク相','ケルン相'),(-1,0):('ボイド相','メルク相'),(0,1):('シータ相','ルクス相'),(0,-1):('グラフ相','ニクス相')},
  'move':{(1,0):('アル化','ゼフ化'),(-1,0):('ベタ化','オル化'),(0,1):('ガン化','イプ化'),(0,-1):('デル化','ウル化')},
  'anchor':'中枢'}
}
TRAIN_FORMS=(
 '{anchor}の{rel}にいる{name}だけを{move}一単位変化させる。',
 '{name}は{anchor}から見て{rel}。この対象のみ{move}。',
 '{move}対象は、{anchor}との関係が{rel}である{name}。')
HELD_FORMS=(
 '{anchor}基準で{rel}に位置する{name}を選び、{move}。',
 '{name}の現在関係は{rel}。他は保ち、この個体だけ{move}。',
 '候補の中から{rel}の{name}を対象にして{move}。')
PARA='{anchor}を確認する。\n候補は複数存在する。\n{rel}にいる{name}だけ{move}。'
FREE='えっと、{anchor}から{rel}の{name}、あれだけ{move}感じでお願い。'
OMIT='さっきの候補で{rel}の方。それだけ{move}。'

@dataclass(frozen=True)
class World:
    positions:tuple[tuple[int,int],...]
    anchor:tuple[int,int]
    target:int
    move:tuple[int,int]

def hidx(s,dim,salt):
    h=2166136261^salt
    for ch in s:
        h^=ord(ch); h=(h*16777619)&0xffffffff
    return h%dim,(-1.0 if h>>31 else 1.0)

def norm(v):
    z=math.sqrt(sum(x*x for x in v)) or 1.0
    return [x/z for x in v]

def text_features(text):
    v=[0.0]*TEXT_DIM; p='^'+text+'$'
    for n in (1,2,3,4,5):
        for i in range(len(p)-n+1):
            j,s=hidx(p[i:i+n],TEXT_DIM,17+n); v[j]+=s
    return norm(v)

def rel_of(w,target=None):
    t=w.target if target is None else target
    x,y=w.positions[t]; ax,ay=w.anchor; dx,dy=x-ax,y-ay
    if abs(dx)>=abs(dy): return (1,0) if dx>0 else (-1,0)
    return (0,1) if dy>0 else (0,-1)

def consequence_features(w,target,move):
    v=[0.0]*CONS_DIM
    r=rel_of(w,target)
    x,y=w.positions[target]; ax,ay=w.anchor
    tokens=(
      f'relation:{r[0]}:{r[1]}',
      f'delta:{move[0]}:{move[1]}',
      f'distance:{min(3,abs(x-ax)+abs(y-ay))}',
      f'preserved:{len(w.positions)-1}',
      f'joint:{r[0]}:{r[1]}:{move[0]}:{move[1]}')
    for k,tok in enumerate(tokens):
        j,s=hidx(tok,CONS_DIM,101+k); v[j]+=(1.0 if k<2 else 0.45)*s
    return norm(v)

def add_outer(W,u,z,scale=1.0):
    W += scale*np.outer(np.asarray(u,dtype=np.float32),np.asarray(z,dtype=np.float32))

def score(W,u,z):
    return float(np.asarray(u,dtype=np.float32) @ W @ np.asarray(z,dtype=np.float32))

def make_world(rng,nobj=8):
    ps=[]
    for r in RELS:
        ps.append((r[0]*rng.choice((1,2,3)),r[1]*rng.choice((1,2,3))))
    while len(ps)<nobj:
        p=(rng.randint(-4,4),rng.randint(-4,4))
        if p!=(0,0) and p not in ps: ps.append(p)
    target=rng.randrange(4)
    return World(tuple(ps),(0,0),target,rng.choice(MOVES))

def render(w,domain,form,name,alt=False):
    d=DOMAINS[domain]; r=d['rel'][rel_of(w)][1 if alt else 0]; m=d['move'][w.move][1 if alt else 0]
    return form.format(anchor=d['anchor'],rel=r,move=m,name=name)

def query_text(w,domain,cond,rng):
    name=f'対象{rng.randrange(10**9)}'
    alt=cond in ('rename','word_order')
    if cond=='held': return render(w,domain,rng.choice(HELD_FORMS),name,alt)
    if cond=='rename': return render(w,domain,rng.choice(HELD_FORMS),f'符号{rng.randrange(10**12)}',alt)
    if cond=='word_order':
        d=DOMAINS[domain]; r=d['rel'][rel_of(w)][1]; m=d['move'][w.move][1]
        return f'{m}という結果にする。{d["anchor"]}との関係が{r}の{name}が対象。'
    if cond=='omission': return render(w,domain,OMIT,name,alt)
    if cond=='paragraph': return render(w,domain,PARA,name,alt)
    if cond=='free': return render(w,domain,FREE,name,alt)
    raise ValueError(cond)

def learn(W,episodes,shuffle=False,rng=None,scale=1.0):
    pairs=[(text_features(t),consequence_features(w,w.target,w.move)) for t,w in episodes]
    zs=[z for _,z in pairs]
    if shuffle:
        assert rng is not None; rng.shuffle(zs)
    for (u,_),z in zip(pairs,zs): add_outer(W,u,z,scale)

def base_train(seed,n=60):
    rng=random.Random(seed); W=np.zeros((TEXT_DIM,CONS_DIM),dtype=np.float32); eps=[]
    for _ in range(n):
        w=make_world(rng)
        for form in TRAIN_FORMS:
            eps.append((render(w,'base',form,f'個体{rng.randrange(10**8)}',rng.random()<0.5),w))
    learn(W,eps,rng=rng)
    return W

def adaptation_episodes(seed,domain,shots_per_joint=1):
    rng=random.Random(seed*7919+sum(map(ord,domain))); eps=[]
    for rel in RELS:
        for move in MOVES:
            for shot in range(shots_per_joint):
                while True:
                    w=make_world(rng)
                    candidates=[i for i in range(4) if rel_of(w,i)==rel]
                    if candidates: break
                w=World(w.positions,w.anchor,rng.choice(candidates),move)
                form=TRAIN_FORMS[(shot+RELS.index(rel)+MOVES.index(move))%len(TRAIN_FORMS)]
                eps.append((render(w,domain,form,f'新規{rng.randrange(10**9)}',alt=(shot%2==1)),w))
    return eps

def adapted_model(seed,domain,shots,shuffle=False):
    W=base_train(seed)
    rng=random.Random(seed*12347+shots)
    learn(W,adaptation_episodes(seed,domain,shots),shuffle=shuffle,rng=rng,scale=2.0)
    return W

def evaluate(seed,W,domain,cond,n=48):
    rng=random.Random(seed*100003+sum(map(ord,domain+cond))); joint=target=move=0
    for _ in range(n):
        w=make_world(rng); u=text_features(query_text(w,domain,cond,rng)); opts=[]
        for c in range(len(w.positions)):
            for m in MOVES:
                opts.append((score(W,u,consequence_features(w,c,m)),c,m))
        _,pc,pm=max(opts)
        joint+=pc==w.target and pm==w.move; target+=pc==w.target; move+=pm==w.move
    return {'joint':joint/n,'target':target/n,'move':move/n}

def inverse(seed,W,domain,n=48):
    rng=random.Random(seed*400009+sum(map(ord,domain))); ok=0
    for _ in range(n):
        w=make_world(rng); z=consequence_features(w,w.target,w.move)
        texts=[query_text(World(w.positions,w.anchor,w.target,m),domain,'held',rng) for m in MOVES]
        scores=[score(W,text_features(t),z) for t in texts]
        ok+=MOVES[max(range(4),key=lambda i:scores[i])]==w.move
    return ok/n

def run_seed(seed):
    conds=('held','rename','word_order','omission','paragraph','free')
    out={'seed':seed,'zero_shot':{},'adapted':{},'shuffled':{},'dose':{}}
    W0=base_train(seed)
    out['zero_shot']={c:evaluate(seed,W0,'nova',c) for c in conds}
    W=adapted_model(seed,'nova',1,False); Ws=adapted_model(seed,'nova',1,True)
    out['adapted']={c:evaluate(seed,W,'nova',c) for c in conds}
    out['shuffled']={c:evaluate(seed,Ws,'nova',c) for c in conds}
    out['inverse']={'adapted':inverse(seed,W,'nova'),'shuffled':inverse(seed,Ws,'nova')}
    Wq=adapted_model(seed,'quasar',1,False); Wqs=adapted_model(seed,'quasar',1,True)
    out['second_domain']={'correct':evaluate(seed,Wq,'quasar','free'),'shuffled':evaluate(seed,Wqs,'quasar','free')}
    for shots in (0,1,2,4):
        Wd=W0 if shots==0 else adapted_model(seed,'nova',shots,False)
        out['dose'][str(shots)]=evaluate(seed,Wd,'nova','held')
    return out

def mean_path(per,*path):
    vals=[]
    for r in per:
        x=r
        for p in path:x=x[p]
        vals.append(x)
    return statistics.mean(vals)

def main():
    t=time.perf_counter(); per=[run_seed(s) for s in SEEDS]; elapsed=time.perf_counter()-t
    conds=('held','rename','word_order','omission','paragraph','free')
    mean={'zero_shot':{},'adapted':{},'shuffled':{}}
    for mode in ('zero_shot','adapted','shuffled'):
        for c in conds:
            mean[mode][c]={k:mean_path(per,mode,c,k) for k in ('joint','target','move')}
    mean['inverse']={k:mean_path(per,'inverse',k) for k in ('adapted','shuffled')}
    mean['second_domain']={k:mean_path(per,'second_domain',k,'joint') for k in ('correct','shuffled')}
    mean['dose']={s:{k:mean_path(per,'dose',s,k) for k in ('joint','target','move')} for s in ('0','1','2','4')}
    gaps=[r['adapted']['held']['joint']-r['shuffled']['held']['joint'] for r in per]
    result={'cycle':'A_SEMANTIC_IDENTITY_003','hypothesis':'Cross-Domain Consequence-Anchored Unit Rebirth from Few Observed Transitions','seeds':list(SEEDS),'per_seed':per,'mean':mean,'chance':{'joint':1/32,'target':1/8,'move':1/4,'inverse':1/4},'paired_held_joint_gap':{'mean':statistics.mean(gaps),'min':min(gaps),'positive_seeds':sum(g>0 for g in gaps)},'resources':{'matrix_bytes_float32_estimate':TEXT_DIM*CONS_DIM*4,'adaptation_records_per_domain':16,'training_seconds_total':elapsed,'peak_rss_kib_python_runtime_included':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),'update_ops_estimate_per_episode':TEXT_DIM*CONS_DIM,'inference_ops_estimate_per_option':TEXT_DIM*CONS_DIM,'options_per_query':32,'complexity':{'update':'O(TC)','query':'O(KTC)'}},'leakage_audit':{'post_treatment_observation_used_at_test':False,'observed_transition_used_only_in_adaptation':True,'final_test_outcome_used_for_training':False,'shared_domain_dictionary_used':False,'shared_identity_used':False,'span_boundaries_generated':False,'string_retrieval_used':False,'external_llm_used':False}}
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
