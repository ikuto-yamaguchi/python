from __future__ import annotations
import hashlib, json, pickle, random, resource, statistics, time
import numpy as np

SEEDS=(1,7,19)
DIM_X=96
DIM_Y=16
DIRS=((1,0),(-1,0),(0,1),(0,-1))
PAIRS=np.array([(i,j) for i in range(8) for j in range(i+1,8)])
PROJ=np.random.default_rng(31415).normal(size=(19,DIM_Y)).astype(np.float32)

LEX={
'D': {'sel':[['基点へ最接近の個体','標から距離が最小のもの','参照点そばの対象'],['基点から最大隔離の個体','標から距離が最大のもの','参照点から遠い対象'],['横軸で最小位置の個体','左端側の対象','水平値が最小のもの'],['横軸で最大位置の個体','右端側の対象','水平値が最大のもの']], 'move':[['東方へ一単位遷移','横軸正方向へ送る','右方向へ移送'],['西方へ一単位遷移','横軸負方向へ送る','左方向へ移送'],['天側へ一単位遷移','縦軸正方向へ送る','上方向へ移送'],['地側へ一単位遷移','縦軸負方向へ送る','下方向へ移送']], 'goal':['周辺配置を保持','基準距離の変化を優先'], 'wrap':['航路盤では','観測面上で']},
'E': {'sel':[['核へ最短の粒子','中心との間隔が最小の点','核近傍の要素'],['核へ最長の粒子','中心との間隔が最大の点','核遠方の要素'],['第一軸の下限粒子','甲方向端の点','第一成分最小の要素'],['第一軸の上限粒子','乙方向端の点','第一成分最大の要素']], 'move':[['甲側へ一刻進める','第一成分を増す','陽甲方向へ送る'],['乙側へ一刻進める','第一成分を減らす','陰甲方向へ送る'],['丙側へ一刻進める','第二成分を増す','陽丙方向へ送る'],['丁側へ一刻進める','第二成分を減らす','陰丙方向へ送る']], 'goal':['他粒子の配置保存','中心間隔の変化を優先'], 'wrap':['粒子帳では','核配置上で']},
'F': {'sel':[['灯台に最寄りの艇','灯標距離が最小の船','灯台近辺の艇'],['灯台に最遠の艇','灯標距離が最大の船','灯台遠方の艇'],['海図西縁の艇','経度値が最小の船','西側端の艇'],['海図東縁の艇','経度値が最大の船','東側端の艇']], 'move':[['順潮へ一目盛進航','海図横正方向へ送る','右舷側へ移す'],['逆潮へ一目盛進航','海図横負方向へ送る','左舷側へ移す'],['沖側へ一目盛進航','海図縦正方向へ送る','上方へ移す'],['岸側へ一目盛進航','海図縦負方向へ送る','下方へ移す']], 'goal':['他艇の位置を維持','灯標距離変化を優先'], 'wrap':['海図記録では','航行盤上で']}}

def stable_hash(s): return int.from_bytes(hashlib.blake2b(s.encode(),digest_size=8).digest(),'little')
def lang(text):
    v=np.zeros(DIM_X,np.float32); src='^'+text+'$'
    for w in (2,3):
        for i in range(len(src)-w+1):
            h=stable_hash(src[i:i+w]); v[h%DIM_X]+=1 if ((h>>9)&1)==0 else -1
    return v/(np.linalg.norm(v)+1e-8)

def world(rng,scale):
    pts=[]; used=set()
    while len(pts)<8:
        p=(rng.randint(-6,6),rng.randint(-6,6))
        if p!=(0,0) and p not in used: used.add(p); pts.append(p)
    return np.array(pts,np.int16)*scale

def target(points,s):
    radial=(points.astype(float)**2).sum(1)
    return int(np.argmin(radial) if s==0 else np.argmax(radial) if s==1 else np.argmin(points[:,0]) if s==2 else np.argmax(points[:,0]))

def move(points,t,m):
    result=points.copy(); result[t]+=np.array(DIRS[m]); return result

def base_effect(before,after,goal):
    bf=before.astype(np.float32); af=after.astype(np.float32); d=af-bf
    changed=np.abs(d).sum(1)>0
    rb=np.sqrt((bf*bf).sum(1)); ra=np.sqrt((af*af).sum(1))
    pb=np.sqrt(((bf[PAIRS[:,0]]-bf[PAIRS[:,1]])**2).sum(1)); pa=np.sqrt(((af[PAIRS[:,0]]-af[PAIRS[:,1]])**2).sum(1))
    rc=np.sort(ra-rb); pc=np.sort(pa-pb); origin=bf[changed].mean(0) if changed.any() else np.zeros(2)
    f=[changed.sum(),d[:,0].sum(),d[:,1].sum(),np.linalg.norm(d.sum(0)),origin[0],origin[1],np.linalg.norm(origin)]
    f+=list(np.quantile(rc,[0,.25,.5,.75,1])); f+=list(np.quantile(pc,[0,.1,.25,.5,.75,.9,1]))
    x=np.array(f,np.float32)
    if goal==1: x[7:12]*=1.6; x[12:]*=.6
    return x

def render(rng,dom,s,m,g,mode):
    L=LEX[dom]; sp=rng.choice(L['sel'][s]); mp=rng.choice(L['move'][m]); gp=L['goal'][g]; wp=rng.choice(L['wrap'])
    if mode=='word_order': return f'{wp}、{mp}。対象条件は{sp}。目的は{gp}。'
    if mode=='nested': return f'{wp}、依頼内容は「{sp}を{mp}」です。達成条件は{gp}。'
    if mode=='paragraph': return f'{wp}、前段は維持。\n{sp}を{mp}。\n目標は{gp}。'
    if mode=='free': return f'{wp}、周囲を崩さず{sp}だけ{mp}ようにして、{gp}こと。'
    if mode=='repair': return f'{wp}、先の案を撤回。正しくは{sp}を{mp}。{gp}。'
    if mode=='goal_change': return f'{wp}、作用は同じく{sp}を{mp}。ただし今度の目的は{gp}。'
    return f'{wp}、{sp}を{mp}。目的は{gp}。'

def dataset(seed,n,dom,modes,scale):
    rng=random.Random(seed); rows=[]
    for _ in range(n):
        before=world(rng,scale); selector=rng.randrange(4); operation=rng.randrange(4); goal=rng.randrange(2); tgt=target(before,selector); after=move(before,tgt,operation); mode=rng.choice(modes)
        rows.append(dict(text=render(rng,dom,selector,operation,goal,mode),before=before,after=after,selector=selector,move=operation,goal=goal,target=tgt,domain=dom,mode=mode))
    return rows

def fit_stats(rows):
    values=np.stack([base_effect(r['before'],r['after'],r['goal']) for r in rows]); return values.mean(0),values.std(0)+1e-3

def effect(row,center,scale,mask=None):
    y=np.tanh(((base_effect(row['before'],row['after'],row['goal'])-center)/scale)@PROJ)
    if mask is not None: y*=mask
    return y/(np.linalg.norm(y)+1e-8)

def train(rows,center,scale,mask,shuffle=False):
    X=np.stack([lang(r['text']) for r in rows]); Y=np.stack([effect(r,center,scale,mask) for r in rows]); xc=X.mean(0)
    if shuffle: Y=Y[np.random.default_rng(991).permutation(len(Y))]
    return (X-xc).T@Y/len(rows),xc

def intervention_profile(rows,center,scale):
    families=[]; rng=random.Random(8821)
    for row in rows[:32]:
        variants=[]
        for kind in range(4):
            q=dict(row)
            if kind==0:
                q['selector']=(row['selector']+1)%4; q['target']=target(row['before'],q['selector']); q['after']=move(row['before'],q['target'],row['move']); q['text']=render(rng,row['domain'],q['selector'],row['move'],row['goal'],'seen')
            elif kind==1:
                q['move']=(row['move']+1)%4; q['after']=move(row['before'],row['target'],q['move']); q['text']=render(rng,row['domain'],row['selector'],q['move'],row['goal'],'seen')
            elif kind==2:
                q['goal']=1-row['goal']; q['text']=render(rng,row['domain'],row['selector'],row['move'],q['goal'],'goal_change')
            else: q['text']=render(rng,row['domain'],row['selector'],row['move'],row['goal'],'free')
            variants.append(np.abs(effect(q,center,scale)-effect(row,center,scale)))
        families.append(np.stack(variants))
    return np.mean(np.stack(families),axis=0)

def consensus_mask(profiles,shuffled=False):
    ps=[p.copy() for p in profiles]
    if shuffled: ps[1]=ps[1][:,[*range(1,DIM_Y),0]]
    ranks=[np.argsort(np.argsort(p,axis=0),axis=0) for p in ps]; score=np.ones(DIM_Y)
    for i in range(1,len(ranks)): score*=np.mean(ranks[0]==ranks[i],axis=0)
    dominance=[np.max(p,axis=0)/(np.sum(p,axis=0)+1e-8) for p in ps]; stable=np.minimum.reduce(dominance)
    keep=(score>=.75)&(stable>=np.quantile(stable,.55))
    if keep.sum()<4: keep[np.argsort(stable)[-4:]]=True
    return keep.astype(np.float32),{'channels':int(keep.sum()),'mean_selectivity':float(stable[keep].mean()),'rank_agreement':float(score[keep].mean())}

def evaluate(rows,model,center,scale,mask):
    W,xc=model; joint=[]; inverse=[]; goal_hits=[]; started=time.perf_counter()
    for row in rows:
        query=(lang(row['text'])-xc)@W; query/=np.linalg.norm(query)+1e-8; candidates=[]
        for tgt in range(8):
            for operation in range(4):
                trial=dict(row); trial['after']=move(row['before'],tgt,operation); candidates.append((float(query@effect(trial,center,scale,mask)),tgt,operation))
        _,predicted_target,predicted_move=max(candidates); joint.append(float(predicted_target==row['target'] and predicted_move==row['move']))
        choices=[(row['selector'],row['move'],row['goal'])]; cr=random.Random(stable_hash(row['text']))
        while len(choices)<8:
            candidate=(cr.randrange(4),cr.randrange(4),cr.randrange(2))
            if candidate not in choices: choices.append(candidate)
        observed=effect(row,center,scale,mask); scores=[]
        for selector,operation,goal in choices:
            z=(lang(render(cr,row['domain'],selector,operation,goal,'seen'))-xc)@W; z/=np.linalg.norm(z)+1e-8; scores.append(float(z@observed))
        inverse.append(float(np.argmax(scores)==0)); goal_scores=[]
        for goal in (0,1):
            trial=dict(row); trial['goal']=goal; goal_scores.append(float(query@effect(trial,center,scale,mask)))
        goal_hits.append(float(int(np.argmax(goal_scores))==row['goal']))
    return {'joint_accuracy':statistics.mean(joint),'inverse_accuracy':statistics.mean(inverse),'goal_accuracy':statistics.mean(goal_hits),'inference_ms':(time.perf_counter()-started)*1000/len(rows)}

def run_seed(seed):
    domains={'D':1,'E':2,'F':3}; training={d:dataset(seed+100*i,72,d,('seen','word_order','nested','paragraph','free'),scale) for i,(d,scale) in enumerate(domains.items())}
    stats={d:fit_stats(rows) for d,rows in training.items()}; profiles=[intervention_profile(training[d],*stats[d]) for d in domains]
    consensus,meta=consensus_mask(profiles); shuffled_consensus,shuffled_meta=consensus_mask(profiles,True); methods={'full':np.ones(DIM_Y,np.float32),'consensus':consensus,'shuffled_consensus':shuffled_consensus}
    output={'mask_meta':{'consensus':meta,'shuffled':shuffled_meta},'methods':{}}
    for method,mask in methods.items():
        output['methods'][method]={}
        for i,(domain,scale) in enumerate(domains.items()):
            model=train(training[domain],*stats[domain],mask); shuffled=train(training[domain],*stats[domain],mask,True)
            tests={'held':dataset(seed+1000+i,8,domain,('seen',),scale),'word_order':dataset(seed+1100+i,8,domain,('word_order',),scale),'free':dataset(seed+1200+i,8,domain,('free',),scale),'goal_change':dataset(seed+1300+i,8,domain,('goal_change',),scale),'repair':dataset(seed+1400+i,8,domain,('repair',),scale)}
            output['methods'][method][domain]={'correct':{k:evaluate(v,model,*stats[domain],mask) for k,v in tests.items()},'shuffle':{k:evaluate(v,shuffled,*stats[domain],mask) for k,v in tests.items()},'model_bytes':len(pickle.dumps((model,stats[domain],mask)))}
    return output

def main():
    raw={str(seed):run_seed(seed) for seed in SEEDS}; summary={}
    for method in ('full','consensus','shuffled_consensus'):
        summary[method]={}
        for domain in ('D','E','F'):
            summary[method][domain]={}
            for condition in ('held','word_order','free','goal_change','repair'):
                summary[method][domain][condition]={side:{metric:statistics.mean(raw[str(seed)]['methods'][method][domain][side][condition][metric] for seed in SEEDS) for metric in ('joint_accuracy','inverse_accuracy','goal_accuracy','inference_ms')} for side in ('correct','shuffle')}
            summary[method][domain]['model_bytes']=statistics.mean(raw[str(seed)]['methods'][method][domain]['model_bytes'] for seed in SEEDS)
    strict=0
    for seed in SEEDS:
        passed=True
        for domain in ('D','E'):
            for condition in ('free','goal_change','repair'):
                correct=raw[str(seed)]['methods']['consensus'][domain]['correct'][condition]['joint_accuracy']; shuffled=raw[str(seed)]['methods']['consensus'][domain]['shuffle'][condition]['joint_accuracy']
                if correct-shuffled<.10: passed=False
        strict+=int(passed)
    return {'track':'B_operation_goal','cycle':4,'hypothesis':'Cross-Lexicon Selective Consequence Subspace from Counterfactual Response Consensus','seeds':list(SEEDS),'summary':summary,'raw':raw,'strict_seed_passes':strict,'consensus_channels':statistics.mean(raw[str(seed)]['mask_meta']['consensus']['channels'] for seed in SEEDS),'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'candidate_count':32,'estimated_update_ops':DIM_X*DIM_Y,'estimated_inference_ops':DIM_X*DIM_Y+32*DIM_Y*19,'post_treatment_at_test':False,'shared_lexicon_across_domains':False,'fixed_ontology_or_handwritten_slot':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}

if __name__=='__main__': print(json.dumps(main(),ensure_ascii=False,indent=2))
