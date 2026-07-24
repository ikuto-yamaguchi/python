#!/usr/bin/env python3
from __future__ import annotations
import json, math, random, resource, statistics, time
from dataclasses import dataclass
import numpy as np

SEEDS=(1,7,19)
TEXT_DIM=128
CONS_DIM=32
MOVES=((1,0),(-1,0),(0,1),(0,-1))
RELS=((1,0),(-1,0),(0,1),(0,-1))
DOMAINS={
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
FREE='えっと、{anchor}から{rel}の{name}、あれだけ{move}感じでお願い。'
PARA='{anchor}を確認する。\n候補は複数存在する。\n{rel}にいる{name}だけ{move}。'

@dataclass(frozen=True)
class Episode:
    text:str
    rel:tuple[int,int]
    move:tuple[int,int]


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

def cons_features(rel,move):
    v=[0.0]*CONS_DIM
    toks=(f'r:{rel[0]}:{rel[1]}',f'm:{move[0]}:{move[1]}',f'j:{rel[0]}:{rel[1]}:{move[0]}:{move[1]}')
    for k,t in enumerate(toks):
        j,s=hidx(t,CONS_DIM,101+k); v[j]+=(1.0 if k<2 else .5)*s
    return norm(v)

def render(domain,rel,move,form,name,alt=False):
    d=DOMAINS[domain]
    return form.format(anchor=d['anchor'],rel=d['rel'][rel][1 if alt else 0],move=d['move'][move][1 if alt else 0],name=name)

def pool(seed,domain):
    rng=random.Random(seed*7919+sum(map(ord,domain))); out=[]
    for rel in RELS:
        for move in MOVES:
            for fi,form in enumerate(TRAIN_FORMS):
                out.append(Episode(render(domain,rel,move,form,f'新規{rng.randrange(10**9)}',alt=(fi%2==1)),rel,move))
    return out

def query(seed,domain,cond,rel,move,i):
    rng=random.Random(seed*100003+i*97+sum(map(ord,domain+cond)))
    name=f'対象{rng.randrange(10**12)}'; d=DOMAINS[domain]
    if cond=='held': return render(domain,rel,move,rng.choice(HELD_FORMS),name,alt=rng.random()<.5)
    if cond=='rename': return render(domain,rel,move,rng.choice(HELD_FORMS),f'符号{rng.randrange(10**15)}',alt=True)
    if cond=='word_order': return f'{d["move"][move][1]}という結果にする。{d["anchor"]}との関係が{d["rel"][rel][1]}の{name}が対象。'
    if cond=='paragraph': return render(domain,rel,move,PARA,name,alt=True)
    if cond=='free': return render(domain,rel,move,FREE,name,alt=True)
    raise ValueError(cond)

def update(W,e):
    W += np.outer(text_features(e.text),cons_features(e.rel,e.move))

def bootstrap_models(observed,seed,n=7):
    rng=random.Random(seed); models=[]
    for _ in range(n):
        W=np.zeros((TEXT_DIM,CONS_DIM),dtype=np.float32)
        if observed:
            sample=[rng.choice(observed) for _ in range(len(observed))]
            for e in sample:update(W,e)
        models.append(W)
    return models

def disagreement(ep,models):
    u=text_features(ep.text); opts=[cons_features(r,m) for r in RELS for m in MOVES]
    preds=[]
    for W in models:
        scores=[float(u@W@z) for z in opts]
        preds.append(int(np.argmax(scores)))
    counts={p:preds.count(p) for p in set(preds)}
    n=len(preds)
    return 1.0-sum((c/n)**2 for c in counts.values())

def select_active(all_eps,budget,seed):
    remaining=list(all_eps); observed=[]
    for step in range(budget):
        models=bootstrap_models(observed,seed*1009+step)
        ranked=[(disagreement(e,models),-len(e.text),idx,e) for idx,e in enumerate(remaining)]
        _,_,idx,e=max(ranked)
        observed.append(e); remaining.pop(idx)
    return observed

def select_random(all_eps,budget,seed):
    rng=random.Random(seed*65537+budget); return rng.sample(all_eps,budget)

def train(selected,shuffle,seed):
    W=np.zeros((TEXT_DIM,CONS_DIM),dtype=np.float32)
    zs=[(e.rel,e.move) for e in selected]
    if shuffle:
        rng=random.Random(seed*31337+len(selected)); rng.shuffle(zs)
    for e,(r,m) in zip(selected,zs):
        W += np.outer(text_features(e.text),cons_features(r,m))
    return W

def evaluate(W,seed,domain,cond,n=96):
    rng=random.Random(seed*8191+sum(map(ord,domain+cond))); ok=0
    opts=[(r,m,cons_features(r,m)) for r in RELS for m in MOVES]
    for i in range(n):
        rel=rng.choice(RELS); move=rng.choice(MOVES); u=text_features(query(seed,domain,cond,rel,move,i))
        pr,pm,_=max(opts,key=lambda x:float(u@W@x[2]))
        ok += pr==rel and pm==move
    return ok/n

def inverse(W,seed,domain,n=96):
    rng=random.Random(seed*17713+sum(map(ord,domain))); ok=0
    for i in range(n):
        rel=rng.choice(RELS); move=rng.choice(MOVES); z=cons_features(rel,move)
        texts=[query(seed,domain,'held',rel,m,i*10+j) for j,m in enumerate(MOVES)]
        pred=MOVES[max(range(4),key=lambda j:float(text_features(texts[j])@W@z))]
        ok += pred==move
    return ok/n

def run_seed(seed):
    eps=pool(seed,'nova'); out={'seed':seed,'budgets':{}}
    for b in (2,4,8,16):
        active=select_active(eps,b,seed); rnd=select_random(eps,b,seed)
        Wa=train(active,False,seed); Wr=train(rnd,False,seed); Ws=train(active,True,seed)
        conds=('held','rename','word_order','paragraph','free')
        out['budgets'][str(b)]={
          'active':{c:evaluate(Wa,seed,'nova',c) for c in conds},
          'random':{c:evaluate(Wr,seed,'nova',c) for c in conds},
          'shuffle':{c:evaluate(Ws,seed,'nova',c) for c in conds},
          'inverse':{'active':inverse(Wa,seed,'nova'),'random':inverse(Wr,seed,'nova'),'shuffle':inverse(Ws,seed,'nova')},
          'second_domain':{'active':evaluate(Wa,seed,'quasar','free'),'random':evaluate(Wr,seed,'quasar','free'),'shuffle':evaluate(Ws,seed,'quasar','free')},
          'selected_unique_joint':len({(e.rel,e.move) for e in active})
        }
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
    mean={}
    for b in ('2','4','8','16'):
        mean[b]={}
        for mode in ('active','random','shuffle'):
            mean[b][mode]={c:mean_path(per,'budgets',b,mode,c) for c in ('held','rename','word_order','paragraph','free')}
        mean[b]['inverse']={m:mean_path(per,'budgets',b,'inverse',m) for m in ('active','random','shuffle')}
        mean[b]['second_domain']={m:mean_path(per,'budgets',b,'second_domain',m) for m in ('active','random','shuffle')}
        mean[b]['selected_unique_joint']=mean_path(per,'budgets',b,'selected_unique_joint')
    result={
      'cycle':'C_CAUSAL_GROUNDING_004',
      'hypothesis':'Active Consequence Disambiguation Identifiability under Opaque-Domain Utterances',
      'seeds':list(SEEDS),'per_seed':per,'mean':mean,'chance_joint':1/16,'chance_inverse':1/4,
      'resources':{
        'matrix_bytes_float32':TEXT_DIM*CONS_DIM*4,
        'training_seconds_total':elapsed,
        'peak_rss_kib_python_runtime_included':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        'update_ops_per_observation':TEXT_DIM*CONS_DIM,
        'inference_ops_per_option':TEXT_DIM*CONS_DIM,
        'options_per_query':16,
        'active_selection_complexity':'O(B * P * E * K * T * C)'
      },
      'leakage_audit':{
        'test_outcomes_used_for_selection':False,
        'selection_uses_model_disagreement_only':True,
        'post_treatment_result_used_only_after_observation_selected':True,
        'span_proposals':False,'string_retrieval':False,'external_llm':False,'shared_domain_dictionary':False
      }
    }
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
