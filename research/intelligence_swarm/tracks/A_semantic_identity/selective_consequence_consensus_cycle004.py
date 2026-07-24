#!/usr/bin/env python3
from __future__ import annotations
import json, math, random, resource, statistics, time
from dataclasses import dataclass
import numpy as np

SEEDS=(1,7,19)
TEXT_DIM=256
RESP_DIM=96
MOVES=((1,0),(-1,0),(0,1),(0,-1))
RELS=((1,0),(-1,0),(0,1),(0,-1))
DOMAINS={
'd1':{'rel':{(1,0):('ネヴァ域','セリオ域'),(-1,0):('トルム域','ガディア域'),(0,1):('リュネ域','ファル域'),(0,-1):('モルカ域','ゼイン域')},
'move':{(1,0):('パルス化','リオ化'),(-1,0):('デム化','クオ化'),(0,1):('フィン化','サル化'),(0,-1):('ノクト化','ヴェル化')},
'goal':('整合相','収束相'),'anchor':'ビーコン'},
'd2':{'rel':{(1,0):('アーク相','ケルン相'),(-1,0):('ボイド相','メルク相'),(0,1):('シータ相','ルクス相'),(0,-1):('グラフ相','ニクス相')},
'move':{(1,0):('アル化','ゼフ化'),(-1,0):('ベタ化','オル化'),(0,1):('ガン化','イプ化'),(0,-1):('デル化','ウル化')},
'goal':('安定核','選択核'),'anchor':'中枢'}}
FORMS={
'd1':{'train':(
'ビーコン照合。{rel}の{name}単独に{move}を施し、{goal}へ収めよ。',
'{goal}へ整える対象は{name}。所在符号{rel}、処理符号{move}。',
'{rel}に対応する{name}へ{move}。到達条件は{goal}。'),
'held':(
'{name}の照合域は{rel}。単独で{move}し{goal}へ。',
'ビーコンから{rel}の{name}を選定、{move}後に{goal}。',
'{goal}を満たすには{rel}側の{name}へ{move}。'),
'word':'先に{goal}を指定。{move}を施す対象は、ビーコン照合で{rel}の{name}。',
'omission':'照合済み候補の{rel}側。単独で{move}し{goal}へ。',
'free':'あの、ビーコン照合で{rel}の{name}だけ、{move}して{goal}にして。'},
'd2':{'train':(
'中枢観測：{goal}。{name}は{rel}位相ゆえ{move}を適用。',
'{move}適用先={name}；位相={rel}；終端={goal}。',
'終端{goal}へ向け、{rel}位相の{name}だけ{move}。'),
'held':(
'位相{rel}にある{name}へ{move}を掛け、終端{goal}。',
'{goal}終端を選ぶ。中枢観測で{rel}の{name}に{move}。',
'{name}は{rel}位相。ほかを不変にして{move}、結果{goal}。'),
'word':'終端は{goal}。中枢観測{rel}位相の{name}を対象に{move}。',
'omission':'先ほどの{rel}位相だけ。{move}を掛けて終端{goal}。',
'free':'えーと、中枢で{rel}っぽい{name}だけに{move}を掛けて、{goal}終端で。'}}

@dataclass(frozen=True)
class World:
    positions:tuple[tuple[int,int],...]
    anchor:tuple[int,int]
    target:int
    move:tuple[int,int]
    goal:int

def hidx(s,dim,salt):
    h=2166136261^salt
    for ch in s:
        h^=ord(ch); h=(h*16777619)&0xffffffff
    return h%dim,(-1.0 if h>>31 else 1.0)

def norm(v):
    z=math.sqrt(sum(x*x for x in v)) or 1.0
    return np.asarray([x/z for x in v],dtype=np.float32)

def text_features(text):
    v=[0.0]*TEXT_DIM; p='^'+text+'$'
    for n in (1,2,3,4,5):
        for i in range(len(p)-n+1):
            j,s=hidx(p[i:i+n],TEXT_DIM,17+n); v[j]+=s
    return norm(v)

def make_world(rng,nobj=8):
    ps=[]
    for r in RELS: ps.append((r[0]*rng.choice((1,2,3)),r[1]*rng.choice((1,2,3))))
    while len(ps)<nobj:
        p=(rng.randint(-4,4),rng.randint(-4,4))
        if p!=(0,0) and p not in ps: ps.append(p)
    return World(tuple(ps),(0,0),rng.randrange(4),rng.choice(MOVES),rng.randrange(2))

def rel_of(w,t=None):
    t=w.target if t is None else t
    x,y=w.positions[t]; ax,ay=w.anchor; dx,dy=x-ax,y-ay
    if abs(dx)>=abs(dy): return (1,0) if dx>0 else (-1,0)
    return (0,1) if dy>0 else (0,-1)

def response_features(w,target,move,goal):
    v=[0.0]*RESP_DIM; r=rel_of(w,target)
    toks=((f'r:{r[0]}:{r[1]}',1.0),(f'm:{move[0]}:{move[1]}',1.0),(f'g:{goal}',1.0),
          (f'j:{r}:{move}:{goal}',0.7),(f'p:{len(w.positions)-1}',0.4))
    for k,(tok,wgt) in enumerate(toks):
        j,s=hidx(tok,RESP_DIM,101+k); v[j]+=wgt*s
    return norm(v)

def render(w,domain,form,name,alt=False):
    d=DOMAINS[domain]
    return form.format(anchor=d['anchor'],rel=d['rel'][rel_of(w)][1 if alt else 0],
                       move=d['move'][w.move][1 if alt else 0],goal=d['goal'][w.goal],name=name)

def query(w,domain,cond,rng):
    fs=FORMS[domain]; name=f'{("標" if domain=="d1" else "相")}{rng.randrange(10**9)}'
    if cond=='held': return render(w,domain,rng.choice(fs['held']),name,rng.random()<0.5)
    if cond=='rename': return render(w,domain,rng.choice(fs['held']),f'{("符" if domain=="d1" else "核")}{rng.randrange(10**12)}',True)
    if cond=='word_order': return render(w,domain,fs['word'],name,True)
    if cond=='omission': return render(w,domain,fs['omission'],name,False)
    if cond=='free': return render(w,domain,fs['free'],name,True)
    raise ValueError(cond)

def episodes(seed,domain,n_per=2):
    rng=random.Random(seed*7919+sum(map(ord,domain))); eps=[]; forms=FORMS[domain]['train']
    for rel in RELS:
        for move in MOVES:
            for goal in range(2):
                for k in range(n_per):
                    while True:
                        w=make_world(rng); cand=[i for i in range(4) if rel_of(w,i)==rel]
                        if cand: break
                    w=World(w.positions,w.anchor,rng.choice(cand),move,goal)
                    eps.append((render(w,domain,forms[(k+RELS.index(rel)+MOVES.index(move)+goal)%len(forms)],
                                       f'{("標" if domain=="d1" else "相")}{rng.randrange(10**8)}',k%2==1),w))
    return eps

def train(seed,domain,shuffle=False,selective=True):
    rng=random.Random(seed*12347); W=np.zeros((TEXT_DIM,RESP_DIM),dtype=np.float32); eps=episodes(seed,domain)
    zs=[response_features(w,w.target,w.move,w.goal) for _,w in eps]
    if shuffle: rng.shuffle(zs)
    for (text,w),z in zip(eps,zs):
        u=text_features(text); W += 2*np.outer(u,z)
        if selective and not shuffle:
            W -= 0.35*np.outer(u,response_features(w,rng.choice([i for i in range(len(w.positions)) if i!=w.target]),w.move,w.goal))
            W -= 0.35*np.outer(u,response_features(w,w.target,rng.choice([m for m in MOVES if m!=w.move]),w.goal))
            W -= 0.35*np.outer(u,response_features(w,w.target,w.move,1-w.goal))
    return W

def score(W,u,z): return float(u@W@z)

def evaluate(seed,W,domain,cond,n=96):
    rng=random.Random(seed*100003+sum(map(ord,domain+cond))); vals=[0,0,0,0]
    for _ in range(n):
        w=make_world(rng); u=text_features(query(w,domain,cond,rng)); best=None
        for c in range(len(w.positions)):
            for m in MOVES:
                for g in range(2):
                    s=score(W,u,response_features(w,c,m,g))
                    if best is None or s>best[0]: best=(s,c,m,g)
        _,pc,pm,pg=best
        vals[0]+=pc==w.target and pm==w.move and pg==w.goal
        vals[1]+=pc==w.target; vals[2]+=pm==w.move; vals[3]+=pg==w.goal
    return dict(zip(('joint','target','move','goal'),[v/n for v in vals]))

def inverse(seed,W,domain,n=96):
    rng=random.Random(seed*400009+sum(map(ord,domain))); ok=0
    for _ in range(n):
        w=make_world(rng); z=response_features(w,w.target,w.move,w.goal); opts=[]
        for m in MOVES:
            for g in range(2):
                ww=World(w.positions,w.anchor,w.target,m,g)
                opts.append((score(W,text_features(query(ww,domain,'held',rng)),z),m,g))
        _,pm,pg=max(opts); ok+=pm==w.move and pg==w.goal
    return ok/n

def lesion(seed,W,domain,channel,n=96):
    rng=random.Random(seed*700001+sum(map(ord,domain+channel))); ok=0
    for _ in range(n):
        w=make_world(rng); u=text_features(query(w,domain,'held',rng)); best=None
        for c in range(len(w.positions)):
            for m in MOVES:
                for g in range(2):
                    z=response_features(w,c,m,g).copy(); r=rel_of(w,c)
                    tok={'identity':f'r:{r[0]}:{r[1]}','operation':f'm:{m[0]}:{m[1]}','goal':f'g:{g}'}[channel]
                    salt={'identity':101,'operation':102,'goal':103}[channel]
                    j,_=hidx(tok,RESP_DIM,salt); z[j]=0
                    s=score(W,u,z)
                    if best is None or s>best[0]: best=(s,c,m,g)
        _,pc,pm,pg=best; ok+=pc==w.target and pm==w.move and pg==w.goal
    return ok/n

def run_seed(seed):
    out={'seed':seed}
    for domain in ('d1','d2'):
        W=train(seed,domain); Ws=train(seed,domain,shuffle=True,selective=False)
        out[domain]={'correct':{},'shuffle':{}}
        for cond in ('held','rename','word_order','omission','free'):
            out[domain]['correct'][cond]=evaluate(seed,W,domain,cond)
            out[domain]['shuffle'][cond]=evaluate(seed,Ws,domain,cond)
        out[domain]['inverse']={'correct':inverse(seed,W,domain),'shuffle':inverse(seed,Ws,domain)}
        out[domain]['lesion']={ch:lesion(seed,W,domain,ch) for ch in ('identity','operation','goal')}
    return out

def mean_path(per,*path):
    vals=[]
    for row in per:
        x=row
        for p in path: x=x[p]
        vals.append(x)
    return statistics.mean(vals)

def main():
    t=time.perf_counter(); per=[run_seed(s) for s in SEEDS]; elapsed=time.perf_counter()-t
    mean={}
    for domain in ('d1','d2'):
        mean[domain]={}
        for cond in ('held','rename','word_order','omission','free'):
            mean[domain][cond]={mode:{k:mean_path(per,domain,mode,cond,k) for k in ('joint','target','move','goal')}
                                for mode in ('correct','shuffle')}
        mean[domain]['inverse']={mode:mean_path(per,domain,'inverse',mode) for mode in ('correct','shuffle')}
        mean[domain]['lesion']={ch:mean_path(per,domain,'lesion',ch) for ch in ('identity','operation','goal')}
    gaps={domain:{cond:[row[domain]['correct'][cond]['joint']-row[domain]['shuffle'][cond]['joint'] for row in per]
                  for cond in ('held','rename','word_order','omission','free')} for domain in ('d1','d2')}
    result={'cycle':'A_SEMANTIC_IDENTITY_004',
            'hypothesis':'Cross-Lexicon Selective Consequence Consensus from Factor-Specific Counterfactual Episodes',
            'seeds':list(SEEDS),'per_seed':per,'mean':mean,'gaps':gaps,
            'chance':{'joint':1/64,'target':1/8,'move':1/4,'goal':1/2,'inverse':1/8},
            'resources':{'matrix_bytes_float32':TEXT_DIM*RESP_DIM*4,'training_seconds_total':elapsed,
                         'peak_rss_kib_python_runtime_included':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
                         'update_ops_estimate_per_episode':TEXT_DIM*RESP_DIM,
                         'inference_ops_estimate_per_option':TEXT_DIM*RESP_DIM,'options_per_query':64},
            'leakage_audit':{'post_treatment_used_at_test':False,'final_test_outcome_used_for_training':False,
                             'shared_content_lexicon_across_domains':False,'shared_domain_dictionary':False,
                             'shared_object_id':False,'span_proposals':False,'string_retrieval':False,'rag':False,'external_llm':False},
            'status':{'g1_passed':False,'progress_recognized':False,'highschool_level_passed':False,
                      'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}}
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
