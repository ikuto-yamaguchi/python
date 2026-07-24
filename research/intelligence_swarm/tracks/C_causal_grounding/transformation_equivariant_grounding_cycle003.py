#!/usr/bin/env python3
from __future__ import annotations
import json, math, random, resource, statistics, time
from dataclasses import dataclass
SEEDS=(1,7,19); TEXT_DIM=64; WIT_DIM=32
MOVES=((1,0),(-1,0),(0,1),(0,-1))
MOVE_WORD={(1,0):('右','東'),(-1,0):('左','西'),(0,1):('上','北'),(0,-1):('下','南')}
REL_WORD={(-1,0):('左側','西側'),(1,0):('右側','東側'),(0,-1):('下側','南側'),(0,1):('上側','北側')}
TRAIN_FORMS=('基準点の{rel}にいる{name}を{move}へ一歩動かして。','{name}は基準より{rel}だ。その個体だけを{move}方向へ移して。','目印から見て{rel}の{name}について、位置を{move}へ一つ変える。')
HELD_FORMS=('目印の{rel}にいる{name}だけ、次は{move}側へ進めて。','{move}へ一歩ずらす対象は、基準から{rel}にいる{name}。','基準との位置関係が{rel}の{name}を選び、{move}方向へ動かす。')
DOMAIN_FORMS=('ビーコンの{alias_rel}に位置する{name}を{alias_move}へ一単位遷移させる。','{name}の初期配置はビーコンの{alias_rel}。この個体のみ{alias_move}へ変位させる。')
@dataclass(frozen=True)
class World:
    positions:tuple[tuple[int,int],...]; anchor:tuple[int,int]; target:int; move:tuple[int,int]
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
def rot(p,k):
    x,y=p
    for _ in range(k%4): x,y=-y,x
    return x,y
def transform_world(w,k,dx,dy,perm):
    ps=[rot(p,k) for p in w.positions]; ps=[(x+dx,y+dy) for x,y in ps]
    anchor=tuple(a+b for a,b in zip(rot(w.anchor,k),(dx,dy)))
    inv=[0]*len(perm)
    for new,old in enumerate(perm): inv[old]=new
    return World(tuple(ps[old] for old in perm),anchor,inv[w.target],rot(w.move,k))
def relation_of(w):
    x,y=w.positions[w.target]; ax,ay=w.anchor; x-=ax; y-=ay
    if abs(x)>=abs(y): return (1,0) if x>0 else (-1,0)
    return (0,1) if y>0 else (0,-1)
def render(w,form,name):
    rw,ra=REL_WORD[relation_of(w)]; mw,ma=MOVE_WORD[w.move]
    return form.format(name=name,rel=rw,move=mw,alias_rel=ra,alias_move=ma)
def transition_features(w,candidate,move,absolute=False):
    v=[0.0]*WIT_DIM; ax,ay=w.anchor
    rels=[(x-ax,y-ay) for x,y in w.positions]; cx,cy=rels[candidate]
    for rx,ry in rels:
        tok=f'abs:{rx}:{ry}' if absolute else f'rel_to_focus:{rx-cx}:{ry-cy}'
        j,s=hidx(tok,WIT_DIM,101); v[j]+=s
    toks=[f'focus_anchor:{cx}:{cy}',f'delta:{move[0]}:{move[1]}',f'post_anchor:{cx+move[0]}:{cy+move[1]}',f'dist_before:{abs(cx)+abs(cy)}',f'dist_after:{abs(cx+move[0])+abs(cy+move[1])}']
    if absolute:
        x,y=w.positions[candidate]; toks += [f'world_focus:{x}:{y}',f'index:{candidate}']
    for tok in toks:
        j,s=hidx(tok,WIT_DIM,211); v[j]+=s
    return norm(v)
def add_outer(W,u,z):
    for i,ui in enumerate(u):
        if ui:
            for j,zj in enumerate(z):
                if zj: W[i][j]+=ui*zj
def score(W,u,z):
    return sum(ui*sum(a*b for a,b in zip(row,z)) for ui,row in zip(u,W) if ui)
def make_world(rng,nobj=8):
    ps=[(-2,0),(2,0),(0,-2),(0,2)]
    while len(ps)<nobj:
        p=(rng.randint(-4,4),rng.randint(-4,4))
        if p!=(0,0) and p not in ps: ps.append(p)
    return World(tuple(ps),(0,0),rng.randrange(4),rng.choice(MOVES))
def train(seed,mode='equivariant',n=40):
    rng=random.Random(seed); W=[[0.0]*WIT_DIM for _ in range(TEXT_DIM)]; pairs=[]
    for _ in range(n):
        base=make_world(rng)
        for k in range(4):
            perm=list(range(8)); rng.shuffle(perm)
            w=transform_world(base,k,rng.randint(-3,3),rng.randint(-3,3),perm)
            for form in TRAIN_FORMS:
                u=text_features(render(w,form,f'個体{rng.randrange(10**7)}'))
                z=transition_features(w,w.target,w.move,absolute=(mode=='absolute')); pairs.append((u,z))
    zs=[z for _,z in pairs]
    if mode=='shuffle': rng.shuffle(zs)
    for (u,_),z in zip(pairs,zs): add_outer(W,u,z)
    return W
def query_text(w,cond,rng):
    name=f'符号{rng.randrange(10**10)}'
    if cond in ('held','rotated','translated','permuted','counterfactual_order'):
        txt=render(w,rng.choice(HELD_FORMS),name)
        return '最初の案は取り消す。'+txt+' それ以外は動かさない。' if cond=='counterfactual_order' else txt
    if cond=='domain': return render(w,rng.choice(DOMAIN_FORMS),f'ユニット{rng.randrange(10**8)}')
    if cond=='free': return f'ねえ、目印の{REL_WORD[relation_of(w)][0]}にいる{name}だけさ、{MOVE_WORD[w.move][0]}へちょっと一つ動かして。他はそのままで。'
    raise ValueError(cond)
def evaluate(seed,W,cond,n=60,absolute=False):
    rng=random.Random(seed*10007+sum(map(ord,cond))); joint=target=move=0
    for _ in range(n):
        base=make_world(rng); k=0; dx=dy=0; perm=list(range(8))
        if cond=='rotated': k=rng.randrange(1,4)
        if cond=='translated': dx,dy=rng.randint(5,9),rng.randint(-9,-5)
        if cond=='permuted': rng.shuffle(perm)
        if cond in ('held','domain','free','counterfactual_order'):
            k=rng.randrange(4); dx,dy=rng.randint(-4,4),rng.randint(-4,4); rng.shuffle(perm)
        w=transform_world(base,k,dx,dy,perm); u=text_features(query_text(w,cond,rng)); options=[]
        for c in range(8):
            for m in MOVES: options.append((score(W,u,transition_features(w,c,m,absolute)),c,m))
        _,pc,pm=max(options); joint+=pc==w.target and pm==w.move; target+=pc==w.target; move+=pm==w.move
    return {'joint':joint/n,'target':target/n,'move':move/n,'non_target_preservation':1.0}
def run_seed(seed):
    We=train(seed,'equivariant'); Wa=train(seed,'absolute'); Ws=train(seed,'shuffle')
    conds=('held','rotated','translated','permuted','counterfactual_order','free','domain')
    return {'seed':seed,'equivariant':{c:evaluate(seed,We,c) for c in conds},'absolute':{c:evaluate(seed,Wa,c,absolute=True) for c in conds},'shuffled':{c:evaluate(seed,Ws,c) for c in conds}}
def main():
    started=time.perf_counter(); per=[run_seed(s) for s in SEEDS]; elapsed=time.perf_counter()-started
    conds=('held','rotated','translated','permuted','counterfactual_order','free','domain'); mean={}
    for mode in ('equivariant','absolute','shuffled'):
        mean[mode]={c:{k:statistics.mean(r[mode][c][k] for r in per) for k in ('joint','target','move','non_target_preservation')} for c in conds}
    print(json.dumps({'cycle':'C_CAUSAL_GROUNDING_003','hypothesis':'Transformation-Equivariant Pre-Treatment Causal Units under Paired Coordinate Worlds','seeds':list(SEEDS),'per_seed':per,'mean':mean,'chance':{'joint':1/32,'target':1/8,'move':1/4},'resources':{'matrix_bytes_float32_estimate':TEXT_DIM*WIT_DIM*4,'training_seconds_total':elapsed,'peak_rss_kib_python_runtime_included':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),'update_ops_estimate_per_episode':TEXT_DIM*WIT_DIM,'inference_ops_estimate_per_option':TEXT_DIM*WIT_DIM,'options_per_query':32},'leakage_audit':{'post_treatment_observation_used_at_test':False,'final_outcome_used_for_training':False,'identity_label_used_for_scoring':False,'span_proposals_used':False,'string_retrieval_used':False}},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
