#!/usr/bin/env python3
from __future__ import annotations
import json, math, random, resource, statistics, time
from dataclasses import dataclass

SEEDS=(1,7,19); TEXT_DIM=128; WIT_DIM=64
MOVES=((1,0),(-1,0),(0,1),(0,-1))
MOVE_WORD={(1,0):('右','東'),(-1,0):('左','西'),(0,1):('上','北'),(0,-1):('下','南')}
REL_WORD={(-1,0):('左側','西側'),(1,0):('右側','東側'),(0,-1):('下側','南側'),(0,1):('上側','北側')}
TRAIN_FORMS=('基準点の{rel}にいる{name}を{move}へ一歩動かして。','{name}は基準より{rel}だ。その個体だけを{move}方向へ移して。','目印から見て{rel}の{name}について、位置を{move}へ一つ変える。')
HELD_FORMS=('目印の{rel}にいる{name}だけ、次は{move}側へ進めて。','{move}へ一歩ずらす対象は、基準から{rel}にいる{name}。','基準との位置関係が{rel}の{name}を選び、{move}方向へ動かす。')
PARAGRAPH='候補は複数いる。\n基準との関係を確認する。\n{rel}にいる{name}だけを{move}へ一歩移してほしい。'
FREE='ねえ、目印から{rel}にいる{name}さ、あれだけ{move}へちょっと一つ動かして。'
OMIT='さっきの候補のうち、基準から{rel}の方。それだけ{move}へ一歩。'
DOMAIN_FORMS=('ビーコンの{alias_rel}に位置する{name}を{alias_move}へ一単位遷移させる。','{name}の初期配置はビーコンの{alias_rel}。この個体のみ{alias_move}へ変位させる。')

@dataclass(frozen=True)
class World:
    positions:tuple[tuple[int,int],...]
    anchor:tuple[int,int]
    target:int
    move:tuple[int,int]

def hidx(s,dim,salt):
    h=2166136261^salt
    for ch in s: h^=ord(ch); h=(h*16777619)&0xffffffff
    return h%dim,(-1.0 if h>>31 else 1.0)

def norm(v):
    z=math.sqrt(sum(x*x for x in v)) or 1.0
    return [x/z for x in v]

def text_features(text):
    v=[0.0]*TEXT_DIM; p='^'+text+'$'
    for n in (1,2,3,4):
        for i in range(len(p)-n+1):
            j,s=hidx(p[i:i+n],TEXT_DIM,19+n); v[j]+=s
    return norm(v)

def raw_transition_features(w,candidate,move):
    v=[0.0]*WIT_DIM; ax,ay=w.anchor
    for i,(x,y) in enumerate(w.positions):
        for tok in (f'pre:{i}:{x-ax}:{y-ay}',f'dist:{i}:{abs(x-ax)+abs(y-ay)}'):
            j,s=hidx(tok,WIT_DIM,101); v[j]+=s
    x,y=w.positions[candidate]; nx,ny=x+move[0],y+move[1]
    for tok,weight in ((f'focus_pre:{x-ax}:{y-ay}',1.0),(f'local_delta:{nx-x}:{ny-y}',1.0),(f'focus_post:{nx-ax}:{ny-ay}',0.7),(f'preserve:{len(w.positions)-1}',0.3)):
        j,s=hidx(tok,WIT_DIM,211); v[j]+=weight*s
    return norm(v)

def add_outer(W,u,z):
    for i,ui in enumerate(u):
        if not ui: continue
        for j,zj in enumerate(z):
            if zj: W[i][j]+=ui*zj

def score(W,u,z):
    nz=[j for j,x in enumerate(z) if x]
    return sum(ui*sum(row[j]*z[j] for j in nz) for ui,row in zip(u,W) if ui)

def make_world(rng,nobj=8):
    rels=[(-1,0),(1,0),(0,-1),(0,1)]
    ps=[(r[0]*rng.choice((1,2)),r[1]*rng.choice((1,2))) for r in rels]
    while len(ps)<nobj:
        p=(rng.randint(-3,3),rng.randint(-3,3))
        if p!=(0,0) and p not in ps: ps.append(p)
    return World(tuple(ps),(0,0),rng.randrange(4),rng.choice(MOVES))

def relation_of(w):
    x,y=w.positions[w.target]
    if abs(x)>=abs(y): return (1,0) if x>0 else (-1,0)
    return (0,1) if y>0 else (0,-1)

def render(w,form,name):
    rw,ra=REL_WORD[relation_of(w)]; mw,ma=MOVE_WORD[w.move]
    return form.format(name=name,rel=rw,move=mw,alias_rel=ra,alias_move=ma)

def query_text(w,cond,rng):
    name=f'未知個体{rng.randrange(10**8)}'
    if cond=='held': return render(w,rng.choice(HELD_FORMS),name)
    if cond=='rename': return render(w,rng.choice(HELD_FORMS),f'符号{rng.randrange(10**10)}')
    if cond=='word_order':
        return f'{MOVE_WORD[w.move][0]}へ一歩、という変更をする。対象は{name}で、基準からは{REL_WORD[relation_of(w)][0]}にいる。'
    if cond=='omission': return render(w,OMIT,name)
    if cond=='paragraph': return render(w,PARAGRAPH,name)
    if cond=='free': return render(w,FREE,name)
    if cond=='domain': return render(w,rng.choice(DOMAIN_FORMS),f'ユニット{rng.randrange(10**8)}')
    raise ValueError(cond)

def train(seed,shuffle=False,n=80):
    rng=random.Random(seed); W=[[0.0]*WIT_DIM for _ in range(TEXT_DIM)]; eps=[]
    for _ in range(n):
        w=make_world(rng)
        for form in TRAIN_FORMS:
            eps.append((text_features(render(w,form,f'個体{rng.randrange(10**7)}')),raw_transition_features(w,w.target,w.move)))
    zs=[z for _,z in eps]
    if shuffle: rng.shuffle(zs)
    for (u,_),z in zip(eps,zs): add_outer(W,u,z)
    return W

def evaluate(seed,W,cond,n=80,lesion=None):
    rng=random.Random(seed*10007+sum(map(ord,cond))); joint=target=move=0
    for _ in range(n):
        w=make_world(rng); u=text_features(query_text(w,cond,rng)); options=[]
        for c in range(len(w.positions)):
            for m in MOVES:
                z=raw_transition_features(w,c,m)
                if lesion=='relation': z=raw_transition_features(World(tuple((0,0) for _ in w.positions),(0,0),w.target,w.move),c,m)
                elif lesion=='operation': z=raw_transition_features(w,c,(0,0))
                options.append((score(W,u,z),c,m))
        _,pc,pm=max(options); joint+=pc==w.target and pm==w.move; target+=pc==w.target; move+=pm==w.move
    return {'joint':joint/n,'target':target/n,'move':move/n}

def run_seed(seed):
    W=train(seed); Ws=train(seed,True); conds=('held','rename','word_order','omission','paragraph','free','domain')
    return {'seed':seed,'correct':{c:evaluate(seed,W,c) for c in conds},'shuffled':{c:evaluate(seed,Ws,c) for c in conds},'lesions':{'relation':evaluate(seed,W,'held',lesion='relation'),'operation':evaluate(seed,W,'held',lesion='operation')}}

def main():
    started=time.perf_counter(); per=[run_seed(s) for s in SEEDS]; elapsed=time.perf_counter()-started
    conds=('held','rename','word_order','omission','paragraph','free','domain')
    def avg(path):
        values=[]
        for r in per:
            x=r
            for key in path: x=x[key]
            values.append(x)
        return statistics.mean(values)
    mean={'correct':{},'shuffled':{}}
    for c in conds:
        mean['correct'][c]={k:avg(('correct',c,k)) for k in ('joint','target','move')}
        mean['shuffled'][c]={k:avg(('shuffled',c,k)) for k in ('joint','target','move')}
    mean['lesions']={l:{k:avg(('lesions',l,k)) for k in ('joint','target','move')} for l in ('relation','operation')}
    print(json.dumps({'cycle':'A_SEMANTIC_IDENTITY_002','hypothesis':'Pre-Treatment Relational Change Binding by Joint Target-Transition Prediction','seeds':list(SEEDS),'per_seed':per,'mean':mean,'chance':{'joint':1/32,'target':1/8,'move':1/4},'resources':{'matrix_bytes_float32_estimate':TEXT_DIM*WIT_DIM*4,'training_seconds_total':elapsed,'peak_rss_kib_python_runtime_included':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),'update_ops_estimate_per_episode':TEXT_DIM*WIT_DIM,'inference_ops_estimate_per_option':TEXT_DIM*WIT_DIM,'options_per_query':32,'complexity':{'update':'O(TW)','query':'O(KMTW)'}},'leakage_audit':{'post_treatment_observation_used_at_test':False,'final_test_outcome_used_for_training':False,'identity_label_used_in_training':False,'span_boundaries_generated':False,'string_retrieval_used':False}},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
