#!/usr/bin/env python3
from __future__ import annotations
import json, math, random, resource, statistics, time
from dataclasses import dataclass
import numpy as np

SEEDS=(1,7,19); TEXT_DIM=256; RESP_DIM=96
MOVES=((1,0),(-1,0),(0,1),(0,-1)); RELS=MOVES
DOMAINS={
'd1':{'rel':{(1,0):('ネヴァ域','セリオ域'),(-1,0):('トルム域','ガディア域'),(0,1):('リュネ域','ファル域'),(0,-1):('モルカ域','ゼイン域')},'move':{(1,0):('パルス化','リオ化'),(-1,0):('デム化','クオ化'),(0,1):('フィン化','サル化'),(0,-1):('ノクト化','ヴェル化')},'goal':('整合相','収束相'),'anchor':'ビーコン','prefix':'標'},
'd2':{'rel':{(1,0):('アーク相','ケルン相'),(-1,0):('ボイド相','メルク相'),(0,1):('シータ相','ルクス相'),(0,-1):('グラフ相','ニクス相')},'move':{(1,0):('アル化','ゼフ化'),(-1,0):('ベタ化','オル化'),(0,1):('ガン化','イプ化'),(0,-1):('デル化','ウル化')},'goal':('安定核','選択核'),'anchor':'中枢','prefix':'相'},
'd3':{'rel':{(1,0):('ソーマ環','ケプラ環'),(-1,0):('リグナ環','ヴァル環'),(0,1):('テオラ環','ミュラ環'),(0,-1):('パキス環','ノエマ環')},'move':{(1,0):('エルド化','キル化'),(-1,0):('アス化','ポル化'),(0,1):('ユラ化','ネス化'),(0,-1):('クロ化','ティム化')},'goal':('静穏層','選抜層'),'anchor':'結節','prefix':'環'}}
FORMS={}
for d,x in DOMAINS.items():
    a=x['anchor']
    FORMS[d]={'train':(f'{a}照合。{{rel}}の{{name}}単独に{{move}}を施し、{{goal}}へ収めよ。',f'{{goal}}へ整える対象は{{name}}。所在符号{{rel}}、処理符号{{move}}。',f'{{rel}}に対応する{{name}}へ{{move}}。到達条件は{{goal}}。'),
    'held':(f'{{name}}の照合域は{{rel}}。単独で{{move}}し{{goal}}へ。',f'{a}から{{rel}}の{{name}}を選定、{{move}}後に{{goal}}。',f'{{goal}}を満たすには{{rel}}側の{{name}}へ{{move}}。'),
    'word':f'先に{{goal}}を指定。{{move}}を施す対象は、{a}照合で{{rel}}の{{name}}。','omission':'照合済み候補の{rel}側。単独で{move}し{goal}へ。','free':f'あの、{a}照合で{{rel}}の{{name}}だけ、{{move}}して{{goal}}にして。'}

@dataclass(frozen=True)
class World:
    positions:tuple[tuple[int,int],...]; anchor:tuple[int,int]; target:int; move:tuple[int,int]; goal:int

def hidx(s,dim,salt):
    h=2166136261^salt
    for ch in s: h^=ord(ch); h=(h*16777619)&0xffffffff
    return h%dim,(-1.0 if h>>31 else 1.0)

def norm(v):
    a=np.asarray(v,dtype=np.float32); return a/(np.linalg.norm(a) or 1.0)

def text_features(text):
    v=[0.0]*TEXT_DIM; p='^'+text+'$'
    for n in (1,2,3,4,5):
        for i in range(len(p)-n+1):
            j,s=hidx(p[i:i+n],TEXT_DIM,17+n); v[j]+=s
    return norm(v)

def make_world(rng):
    ps=[]
    for r in RELS: ps.append((r[0]*rng.choice((1,2,3)),r[1]*rng.choice((1,2,3))))
    while len(ps)<8:
        p=(rng.randint(-4,4),rng.randint(-4,4))
        if p!=(0,0) and p not in ps: ps.append(p)
    return World(tuple(ps),(0,0),rng.randrange(4),rng.choice(MOVES),rng.randrange(2))

def rel_of(w,t=None):
    t=w.target if t is None else t; x,y=w.positions[t]
    if abs(x)>=abs(y): return (1,0) if x>0 else (-1,0)
    return (0,1) if y>0 else (0,-1)

def response_features(w,target,move,goal):
    v=[0.0]*RESP_DIM; r=rel_of(w,target)
    for k,(tok,wgt) in enumerate(((f'r:{r[0]}:{r[1]}',1.0),(f'm:{move[0]}:{move[1]}',1.0),(f'g:{goal}',1.0),(f'j:{r}:{move}:{goal}',.7),(f'p:{len(w.positions)-1}',.4))):
        j,s=hidx(tok,RESP_DIM,101+k); v[j]+=wgt*s
    return norm(v)

def render(w,d,form,name,alt=False):
    x=DOMAINS[d]
    return form.format(rel=x['rel'][rel_of(w)][1 if alt else 0],move=x['move'][w.move][1 if alt else 0],goal=x['goal'][w.goal],name=name)

def query(w,d,cond,rng):
    fs=FORMS[d]; pre=DOMAINS[d]['prefix']; name=f'{pre}{rng.randrange(10**9)}'
    if cond=='held': return render(w,d,rng.choice(fs['held']),name,rng.random()<.5)
    if cond=='rename': return render(w,d,rng.choice(fs['held']),f'{pre}{rng.randrange(10**12)}',True)
    if cond=='word_order': return render(w,d,fs['word'],name,True)
    if cond=='omission': return render(w,d,fs['omission'],name,False)
    if cond=='free': return render(w,d,fs['free'],name,True)
    raise ValueError(cond)

def episodes(seed,d,n_per=2):
    rng=random.Random(seed*7919+sum(map(ord,d))); eps=[]; forms=FORMS[d]['train']; pre=DOMAINS[d]['prefix']
    for rel in RELS:
        for mv in MOVES:
            for goal in range(2):
                for k in range(n_per):
                    while True:
                        w=make_world(rng); cand=[i for i in range(4) if rel_of(w,i)==rel]
                        if cand: break
                    w=World(w.positions,w.anchor,rng.choice(cand),mv,goal)
                    eps.append((render(w,d,forms[(k+RELS.index(rel)+MOVES.index(mv)+goal)%3],f'{pre}{rng.randrange(10**8)}',k%2==1),w))
    return eps

def train(seed,d,shuffle=False):
    rng=random.Random(seed*12347); W=np.zeros((TEXT_DIM,RESP_DIM),np.float32); eps=episodes(seed,d)
    zs=[response_features(w,w.target,w.move,w.goal) for _,w in eps]
    if shuffle: rng.shuffle(zs)
    for (text,w),z in zip(eps,zs):
        u=text_features(text); W+=2*np.outer(u,z)
        if not shuffle:
            W-=.35*np.outer(u,response_features(w,rng.choice([i for i in range(8) if i!=w.target]),w.move,w.goal))
            W-=.35*np.outer(u,response_features(w,w.target,rng.choice([m for m in MOVES if m!=w.move]),w.goal))
            W-=.35*np.outer(u,response_features(w,w.target,w.move,1-w.goal))
    return W

def score(W,u,z): return float(u@W@z)

def evaluate(seed,W,d,cond,n=96):
    rng=random.Random(seed*100003+sum(map(ord,d+cond))); vals=[0,0,0,0]
    for _ in range(n):
        w=make_world(rng); u=text_features(query(w,d,cond,rng)); best=max((score(W,u,response_features(w,c,m,g)),c,m,g) for c in range(8) for m in MOVES for g in range(2))
        _,pc,pm,pg=best; vals[0]+=pc==w.target and pm==w.move and pg==w.goal; vals[1]+=pc==w.target; vals[2]+=pm==w.move; vals[3]+=pg==w.goal
    return dict(zip(('joint','target','move','goal'),[v/n for v in vals]))

def inverse(seed,W,d,n=96):
    rng=random.Random(seed*400009+sum(map(ord,d))); ok=0
    for _ in range(n):
        w=make_world(rng); z=response_features(w,w.target,w.move,w.goal)
        _,pm,pg=max((score(W,text_features(query(World(w.positions,w.anchor,w.target,m,g),d,'held',rng)),z),m,g) for m in MOVES for g in range(2))
        ok+=pm==w.move and pg==w.goal
    return ok/n

def lesion(seed,W,d,ch,n=96):
    rng=random.Random(seed*700001+sum(map(ord,d+ch))); ok=0
    for _ in range(n):
        w=make_world(rng); u=text_features(query(w,d,'held',rng)); candidates=[]
        for c in range(8):
            for m in MOVES:
                for g in range(2):
                    z=response_features(w,c,m,g).copy(); r=rel_of(w,c)
                    tok={'identity':f'r:{r[0]}:{r[1]}','operation':f'm:{m[0]}:{m[1]}','goal':f'g:{g}'}[ch]
                    j,_=hidx(tok,RESP_DIM,{'identity':101,'operation':102,'goal':103}[ch]); z[j]=0
                    candidates.append((score(W,u,z),c,m,g))
        _,pc,pm,pg=max(candidates); ok+=pc==w.target and pm==w.move and pg==w.goal
    return ok/n

def run_seed(seed):
    out={'seed':seed}
    for d in DOMAINS:
        W,Ws=train(seed,d),train(seed,d,True); out[d]={'correct':{},'shuffle':{},'inverse':{},'lesion_drop':{}}
        for c in ('held','rename','word_order','omission','free'):
            out[d]['correct'][c]=evaluate(seed,W,d,c); out[d]['shuffle'][c]=evaluate(seed,Ws,d,c)
        out[d]['inverse']={'correct':inverse(seed,W,d),'shuffle':inverse(seed,Ws,d)}
        base=out[d]['correct']['held']['joint']
        out[d]['lesion_drop']={ch:base-lesion(seed,W,d,ch) for ch in ('identity','operation','goal')}
    passes={}
    for d in DOMAINS:
        gaps=[out[d]['correct'][c]['joint']-out[d]['shuffle'][c]['joint'] for c in ('word_order','free')]
        passes[d]=min(gaps)>=.10 and out[d]['inverse']['correct']-out[d]['inverse']['shuffle']>=.10 and all(v>0 for v in out[d]['lesion_drop'].values())
    signs={ch:[int(np.sign(out[d]['lesion_drop'][ch])) for d in DOMAINS] for ch in ('identity','operation','goal')}
    out['eligibility']={'domain_pass':passes,'all_domains':all(passes.values()),'lesion_sign_consensus':all(len(set(v))==1 and v[0]>0 for v in signs.values()),'signs':signs}
    return out

def path_mean(rows,*path):
    values=[]
    for row in rows:
        x=row
        for p in path: x=x[p]
        values.append(x)
    return statistics.mean(values)

def main():
    started=time.perf_counter(); per=[run_seed(s) for s in SEEDS]; mean={}
    for d in DOMAINS:
        mean[d]={}
        for c in ('held','rename','word_order','omission','free'):
            mean[d][c]={mode:{k:path_mean(per,d,mode,c,k) for k in ('joint','target','move','goal')} for mode in ('correct','shuffle')}
        mean[d]['inverse']={mode:path_mean(per,d,'inverse',mode) for mode in ('correct','shuffle')}
        mean[d]['lesion_drop']={ch:path_mean(per,d,'lesion_drop',ch) for ch in ('identity','operation','goal')}
    result={'cycle':'D_MEMORY_ELIGIBILITY_005','hypothesis':'Cross-Lexicon Consensus Eligibility from Shared Selective Lesion Signatures','seeds':list(SEEDS),'per_seed':per,'mean':mean,
    'strict_gate_pass_seeds':sum(r['eligibility']['all_domains'] and r['eligibility']['lesion_sign_consensus'] for r in per),
    'chance':{'joint':1/64,'target':1/8,'move':1/4,'goal':1/2,'inverse':1/8},
    'resources':{'matrix_bytes_per_domain':TEXT_DIM*RESP_DIM*4,'three_domain_matrix_bytes':TEXT_DIM*RESP_DIM*12,'runtime_seconds_total':time.perf_counter()-started,'peak_rss_kib_python_runtime_included':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),'update_ops_estimate_per_episode':TEXT_DIM*RESP_DIM,'inference_ops_estimate_per_option':TEXT_DIM*RESP_DIM,'options_per_query':64},
    'leakage_audit':{'post_treatment_used_at_test':False,'test_outcome_used_for_training':False,'shared_content_lexicon_across_domains':False,'shared_domain_dictionary':False,'shared_object_id':False,'span_proposals':False,'string_retrieval':False,'rag':False,'external_llm':False},
    'status':{'g1_passed':False,'g2_passed':False,'memory_eligibility_passed':False,'retention_mainline_enabled':False,'progress_recognized':False,'failure_class':'initial_semantics_failure','highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}}
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
