#!/usr/bin/env python3
from __future__ import annotations
import json, math, random, resource, statistics, time
from dataclasses import dataclass

SEEDS=(1,7,19)
TEXT_DIM=256
REL_DIM=128
STEPS=((1,0),(-1,0),(0,1),(0,-1))
DIR={(1,0):("右","東"),(-1,0):("左","西"),(0,1):("上","北"),(0,-1):("下","南")}

TRAIN_FORMS=(
    "{name}の動きを{verb}して、{goal}状態にしてください。",
    "{goal}になるように{name}へ{verb}を適用する。",
    "{name}について、操作は{verb}。目標は{goal}です。",
)
HELD_FORMS=(
    "{name}を{goal}にしたいので、動きへ{verb}をかけて。",
    "対象{name}の軌跡を{verb}し、結果を{goal}へ合わせて。",
    "{goal}が目的。{name}には{verb}を実行して。",
)
DOMAIN_FORMS=(
    "{name}の三段シーケンスへ{verb2}を施し、終端条件を{goal2}にする。",
    "系列{name}に対する変換は{verb2}、到達条件は{goal2}。",
)

# Generator-only language families. The model never receives operation IDs or goal slots.
VERBS={
    "rotate":(("右回転","時計方向へ回す"),("正旋回","クロック変換")),
    "mirror":(("左右反転","横向きを逆にする"),("鏡映変換","水平反射")),
    "reverse":(("順番を逆転","動く順序を反対にする"),("逆順化","系列反転")),
    "swap":(("最初と最後を交換","両端の動きを入れ替える"),("端点交換","首尾転置")),
}
GOALS={
    "east":(("最後を右向き","終点を東向き"),("終端東向き","東終端")),
    "north":(("最後を上向き","終点を北向き"),("終端北向き","北終端")),
}

@dataclass(frozen=True)
class Obj:
    ident:int
    traj:tuple[tuple[int,int],...]
    scar:int

def hidx(s:str,dim:int,salt:int)->tuple[int,float]:
    h=2166136261^salt
    for ch in s:
        h^=ord(ch); h=(h*16777619)&0xffffffff
    return h%dim,(-1.0 if h>>31 else 1.0)

def sparse_features(text:str,dim:int,salt:int)->list[float]:
    v=[0.0]*dim; p="^"+text+"$"
    for n in (1,2,3):
        for i in range(len(p)-n+1):
            j,s=hidx(p[i:i+n],dim,salt+n); v[j]+=s
    z=math.sqrt(sum(x*x for x in v)) or 1.0
    return [x/z for x in v]

def text_features(text:str)->list[float]:
    return sparse_features(text,TEXT_DIM,17)

def apply_latent(traj,op):
    if op=="rotate": return tuple((y,-x) for x,y in traj)
    if op=="mirror": return tuple((-x,y) for x,y in traj)
    if op=="reverse": return tuple(reversed(traj))
    if op=="swap":
        t=list(traj); t[0],t[-1]=t[-1],t[0]; return tuple(t)
    raise ValueError(op)

def force_goal(traj,goal):
    t=list(traj); t[-1]=(1,0) if goal=="east" else (0,1); return tuple(t)

def relation_token(before,after,scar_before,scar_after):
    parts=[f"{i}:{a[0]}:{a[1]}>{b[0]}:{b[1]}" for i,(a,b) in enumerate(zip(before,after))]
    parts.append(f"scar:{(scar_before^scar_after)&0xffff}")
    return "|".join(parts)

def relation_features(before,after,sb,sa):
    return sparse_features(relation_token(before,after,sb,sa),REL_DIM,101)

def add_outer(W,u,r):
    for i,ui in enumerate(u):
        if not ui: continue
        row=W[i]
        for j,rj in enumerate(r):
            if rj: row[j]+=ui*rj

def score(W,u,r):
    return sum(ui*sum(row[j]*r[j] for j in range(REL_DIM) if r[j]) for ui,row in zip(u,W) if ui)

def make_objects(rng,n=160):
    out=[]; seen=set()
    for ident in range(n):
        while True:
            tr=tuple(rng.choice(STEPS) for _ in range(4)); scar=rng.getrandbits(20)
            if (tr,scar) not in seen: seen.add((tr,scar)); break
        out.append(Obj(ident,tr,scar))
    return out

def render_command(obj,op,goal,form,domain,rng,name=None):
    name=name or f"対象{rng.randrange(10**7,10**8)}"
    verb=VERBS[op][1 if domain else 0][rng.randrange(2)]
    goalw=GOALS[goal][1 if domain else 0][rng.randrange(2)]
    return form.format(name=name,verb=verb,goal=goalw,verb2=verb,goal2=goalw)

def outcome(obj,op,goal):
    tr=force_goal(apply_latent(obj.traj,op),goal)
    scar=obj.scar ^ (sum((i+1)*(x+2*y+7) for i,(x,y) in enumerate(tr)) & 0xffff)
    return Obj(obj.ident,tr,scar)

def train(seed,shuffle=False):
    rng=random.Random(seed); objs=make_objects(rng); W=[[0.0]*REL_DIM for _ in range(TEXT_DIM)]; eps=[]
    ops=tuple(VERBS); goals=tuple(GOALS)
    for o in objs:
        for k in range(3):
            op=ops[(o.ident+k)%len(ops)]; goal=goals[(o.ident+2*k)%len(goals)]; after=outcome(o,op,goal)
            text=render_command(o,op,goal,TRAIN_FORMS[k],False,rng)
            eps.append((text_features(text),relation_features(o.traj,after.traj,o.scar,after.scar)))
    rs=[r for _,r in eps]
    if shuffle: rng.shuffle(rs)
    for (u,_),r in zip(eps,rs): add_outer(W,u,r)
    return objs,W,eps

def query_text(o,op,goal,condition,rng):
    name=f"未知名{rng.randrange(10**8,10**9)}"
    if condition in ("held","rename"): return render_command(o,op,goal,rng.choice(HELD_FORMS),False,rng,name)
    if condition=="word_order":
        v=VERBS[op][0][rng.randrange(2)]; g=GOALS[goal][0][rng.randrange(2)]
        return f"目標は{g}。実施するのは{v}。対象は{name}。"
    if condition=="nested": return f"依頼は「{render_command(o,op,goal,HELD_FORMS[0],False,rng,name)}」という内容です。"
    if condition=="paragraph": return "前の記録は維持。\n"+render_command(o,op,goal,HELD_FORMS[1],False,rng,name)+"\n補助情報は変更しない。"
    if condition=="free":
        v=VERBS[op][0][rng.randrange(2)]; g=GOALS[goal][0][rng.randrange(2)]
        return f"ねえ{name}のやつ、{g}にしたいんだ。動きは{v}って感じでお願い。"
    if condition=="domain": return render_command(o,op,goal,rng.choice(DOMAIN_FORMS),True,rng,name)
    raise ValueError(condition)

def candidates_for(o,rng):
    pairs=[(op,goal,outcome(o,op,goal)) for op in VERBS for goal in GOALS]; rng.shuffle(pairs); return pairs

def prospective(seed,objs,W,condition):
    rng=random.Random(seed*1009+sum(map(ord,condition))); hit=0
    for o in objs:
        op=rng.choice(tuple(VERBS)); goal=rng.choice(tuple(GOALS)); u=text_features(query_text(o,op,goal,condition,rng))
        pred=max(candidates_for(o,rng),key=lambda x:score(W,u,relation_features(o.traj,x[2].traj,o.scar,x[2].scar)))
        hit += pred[0]==op and pred[1]==goal
    return hit/len(objs)

def inverse(seed,objs,W,domain=False):
    rng=random.Random(seed*2017+(31 if domain else 7)); hit=0; condition="domain" if domain else "held"
    for o in objs:
        op=rng.choice(tuple(VERBS)); goal=rng.choice(tuple(GOALS)); after=outcome(o,op,goal)
        target=relation_features(o.traj,after.traj,o.scar,after.scar)
        choices=[(op,goal,query_text(o,op,goal,condition,rng))]
        other=[(a,b) for a in VERBS for b in GOALS if (a,b)!=(op,goal)]
        for a,b in rng.sample(other,7): choices.append((a,b,query_text(o,a,b,condition,rng)))
        rng.shuffle(choices); pred=max(choices,key=lambda x:score(W,text_features(x[2]),target)); hit += pred[0]==op and pred[1]==goal
    return hit/len(objs)

def goal_change(seed,objs,W):
    rng=random.Random(seed*3011+13); hit=0
    for o in objs:
        op=rng.choice(tuple(VERBS)); g0,g1=tuple(GOALS); u=text_features(query_text(o,op,g1,"held",rng))
        cand=[(g0,outcome(o,op,g0)),(g1,outcome(o,op,g1))]
        pred=max(cand,key=lambda x:score(W,u,relation_features(o.traj,x[1].traj,o.scar,x[1].scar))); hit += pred[0]==g1
    return hit/len(objs)

def failure_repair(seed,objs,W):
    rng=random.Random(seed*4001+17); hit=0
    for o in objs:
        op=rng.choice(tuple(VERBS)); goal=rng.choice(tuple(GOALS)); text="前の操作は違います。"+query_text(o,op,goal,"held",rng); u=text_features(text)
        pred=max(candidates_for(o,rng),key=lambda x:score(W,u,relation_features(o.traj,x[2].traj,o.scar,x[2].scar))); hit += pred[0]==op and pred[1]==goal
    return hit/len(objs)

def run_seed(seed):
    objs,W,_=train(seed); _,Ws,_=train(seed,True); conds=("held","rename","word_order","nested","paragraph","free","domain")
    return {"seed":seed,"prospective":{c:prospective(seed,objs,W,c) for c in conds},"shuffle":{c:prospective(seed,objs,Ws,c) for c in conds},
      "inverse_held":inverse(seed,objs,W,False),"inverse_domain":inverse(seed,objs,W,True),"goal_change":goal_change(seed,objs,W),
      "goal_change_shuffle":goal_change(seed,objs,Ws),"failure_repair":failure_repair(seed,objs,W),"failure_repair_shuffle":failure_repair(seed,objs,Ws)}

def main():
    start=time.perf_counter(); per=[run_seed(s) for s in SEEDS]; elapsed=time.perf_counter()-start; conds=("held","rename","word_order","nested","paragraph","free","domain"); mean=statistics.mean
    result={"cycle":"B_OPERATION_GOAL_001","hypothesis":"Witness-Conditioned Operation Equivariance without Span Programs","seeds":list(SEEDS),
      "chance":{"prospective":1/8,"inverse":1/8,"goal_change":1/2,"failure_repair":1/8},"per_seed":per,
      "mean":{"prospective":{c:mean([r["prospective"][c] for r in per]) for c in conds},"shuffle":{c:mean([r["shuffle"][c] for r in per]) for c in conds},
        "inverse_held":mean([r["inverse_held"] for r in per]),"inverse_domain":mean([r["inverse_domain"] for r in per]),"goal_change":mean([r["goal_change"] for r in per]),
        "goal_change_shuffle":mean([r["goal_change_shuffle"] for r in per]),"failure_repair":mean([r["failure_repair"] for r in per]),"failure_repair_shuffle":mean([r["failure_repair_shuffle"] for r in per])},
      "resources":{"matrix_bytes_float32_estimate":TEXT_DIM*REL_DIM*4,"training_seconds_total":elapsed,"peak_rss_kib_python_runtime_included":int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        "update_ops_estimate_per_episode":TEXT_DIM*REL_DIM,"candidate_scoring_ops_estimate":TEXT_DIM*REL_DIM,"candidate_count_prospective":len(VERBS)*len(GOALS),"complexity":{"update":"O(TR)","prospective":"O(KTR)","inverse":"O(KTR)"}},
      "leakage_audit":{"operation_label_used_by_model":False,"goal_slot_used_by_model":False,"span_boundaries_generated":False,"string_retrieval_used":False,"final_test_outcome_used_for_training":False},
      "gates":{"G1_passed":False,"G2_passed":False},"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
