from __future__ import annotations
import json, math, random, statistics, time, resource, pickle
import numpy as np

TEXT_D=64
SENSOR_D=32
SEEDS=(1,7,19)
OPS_A=[("右へ移す",(1,0)),("左へ移す",(-1,0)),("上へ動かす",(0,1)),("下へ動かす",(0,-1))]
OPS_B=[("東側へずらす",(1,0)),("西側へ寄せる",(-1,0)),("北方へ送る",(0,1)),("南方へ移送する",(0,-1))]
OBJECTS_A=["青い箱","赤い箱","白い箱","黒い箱","丸い駒","四角い駒","鍵A","鍵B"]
OBJECTS_B=["試料甲","試料乙","端末一","端末二","部品イ","部品ロ","資料X","資料Y"]
GOALS_A=["通路を空ける","基準点へ近づける","他の物から離す"]
GOALS_B=["検査域を確保する","中央線へ寄せる","干渉を避ける"]
FORMS=["plain","word_order","rename","nested","paragraph","free"]

def shash(x:str, mod:int)->int:
    h=2166136261
    for ch in x:
        h ^= ord(ch); h=(h*16777619)&0xffffffff
    return h%mod

def text_features(s:str):
    v=np.zeros(TEXT_D,dtype=np.float32)
    n=max(1,len(s))
    for i,ch in enumerate(s):
        cp=ord(ch)
        idx=(cp*1315423911 + (i%7)*2654435761)%TEXT_D
        v[idx]+=(1.0 if ((cp+i)&1)==0 else -1.0)/math.sqrt(n)
        v[(cp*97)%TEXT_D]+=((i+1)/n-0.5)/math.sqrt(n)
    for k in range(4):
        v[shash(f"{k}:{s}",TEXT_D)]+=0.25
    return v

def sensor_features(before,target_idx=None,move=None,after=None):
    v=np.zeros(SENSOR_D,dtype=np.float32)
    for i,(x,y) in enumerate(before):
        vals=(x,y,x*x+y*y)
        for j,val in enumerate(vals):
            v[(i*7+j*9+int(val*5))%SENSOR_D]+=math.tanh(val/4)
    if target_idx is not None:
        x,y=before[target_idx]; dx,dy=move
        for j,val in enumerate((x,y,dx,dy,x+dx,y+dy)):
            v[(17+j*3+int(val*7))%SENSOR_D]+=math.tanh(val/3)
    if after is not None:
        for i,((x,y),(u,w)) in enumerate(zip(before,after)):
            v[(i*5+3)%SENSOR_D]+=u-x
            v[(i*5+4)%SENSOR_D]+=w-y
    return v

def make_world(rng):
    ps=[]; used=set()
    while len(ps)<8:
        p=(rng.randint(-3,3),rng.randint(-3,3))
        if p not in used: ps.append(p); used.add(p)
    return ps

def utterance(obj,op,goal,form):
    if form=="plain": return f"{obj}を{op}。目的は{goal}。"
    if form=="word_order": return f"{goal}ため、{op}対象は{obj}です。"
    if form=="rename": return f"対象物の{obj}について、{op}。狙いは{goal}。"
    if form=="nested": return f"依頼は「{obj}を{op}」で、理由は{goal}です。"
    if form=="paragraph": return f"現在の配置を確認します。\n{obj}を{op}。\n最終的には{goal}。"
    return f"{goal}ようにしたいので、ひとまず{obj}の位置を{op}感じでお願いします。"

def apply_move(before,idx,mv):
    out=list(before); x,y=out[idx]; dx,dy=mv; out[idx]=(x+dx,y+dy); return out

def episode(rng,domain="A",form="plain",op_idx=None,obj_idx=None,goal_idx=None):
    objs=OBJECTS_A if domain=="A" else OBJECTS_B
    ops=OPS_A if domain=="A" else OPS_B
    goals=GOALS_A if domain=="A" else GOALS_B
    before=make_world(rng)
    op_idx=rng.randrange(4) if op_idx is None else op_idx
    obj_idx=rng.randrange(8) if obj_idx is None else obj_idx
    goal_idx=rng.randrange(3) if goal_idx is None else goal_idx
    phrase,mv=ops[op_idx]
    after=apply_move(before,obj_idx,mv)
    return dict(text=utterance(objs[obj_idx],phrase,goals[goal_idx],form),before=before,after=after,
                obj_idx=obj_idx,op_idx=op_idx,goal_idx=goal_idx,move=mv,domain=domain,form=form)

def contrast_groups(rng,n=80):
    out=[]
    for _ in range(n):
        f=rng.choice(FORMS[:4]); base=episode(rng,"A",f)
        e1=episode(rng,"A",f,obj_idx=base["obj_idx"],op_idx=(base["op_idx"]+rng.choice([1,2,3]))%4,goal_idx=base["goal_idx"])
        e2=episode(rng,"A",f,obj_idx=(base["obj_idx"]+rng.choice(range(1,8)))%8,op_idx=base["op_idx"],goal_idx=base["goal_idx"])
        e3=episode(rng,"A",f,obj_idx=base["obj_idx"],op_idx=base["op_idx"],goal_idx=(base["goal_idx"]+rng.choice([1,2]))%3)
        e4=dict(base); e4["before"],e4["after"]=base["after"],base["before"]
        out.append((base,e1,e2,e3,e4))
    return out

def code(e):
    return text_features(e["text"]), sensor_features(e["before"],e["obj_idx"],e["move"],e["after"])

def train(seed,method):
    rng=random.Random(seed); groups=contrast_groups(rng); t0=time.perf_counter()
    diffs=np.zeros((4,TEXT_D),dtype=np.float32)
    enc=[]
    for g in groups:
        cs=[code(e) for e in g]; enc.append((g,cs))
        for ch in range(4): diffs[ch]+=np.abs(cs[0][0]-cs[ch+1][0])
    diffs/=len(groups)
    masks=[]
    for ch in range(4):
        score=np.maximum(0,diffs[ch]-(diffs.sum(axis=0)-diffs[ch])/3)
        ids=np.argsort(score)[-16:]
        m=np.zeros(TEXT_D,dtype=np.float32); m[ids]=1; masks.append(m)
    mats=[]
    for ch in range(4):
        M=np.zeros((TEXT_D,SENSOR_D),dtype=np.float32)
        for g,cs in enc:
            for t,tr in cs: M+=np.outer(t*masks[ch],tr)
        mats.append(M/len(enc))
    scores=[]
    for ch,M in enumerate(mats):
        sc=0
        for g,cs in enc[:24]:
            t,tr=cs[2]; sc+=float((t*masks[ch])@M@tr)
        scores.append(sc)
    chosen=int(np.argmax(scores))
    if method=="shared":
        return dict(mask=np.ones(TEXT_D,dtype=np.float32),M=sum(mats)/4,chosen=-1),time.perf_counter()-t0
    if method=="factorized":
        return dict(mask=masks[chosen],M=mats[chosen],chosen=chosen),time.perf_counter()-t0
    if method=="shuffle":
        q=(chosen+1)%4; return dict(mask=masks[q],M=mats[q],chosen=q),time.perf_counter()-t0
    if method=="no_direction":
        m=np.maximum(masks[chosen],masks[3]); return dict(mask=m,M=mats[chosen]+mats[3],chosen=chosen),time.perf_counter()-t0
    raise ValueError

def candidate_scores(model,e):
    t=text_features(e["text"])*model["mask"]
    out=[]
    for idx in range(8):
        for mv in ((1,0),(-1,0),(0,1),(0,-1)):
            f=sensor_features(e["before"],idx,mv,None)
            out.append((float(t@model["M"]@f),idx,mv))
    return sorted(out,reverse=True)

def evaluate(seed,method,mode,n=24):
    model,tr=train(seed,method); rng=random.Random(seed*1009+shash(mode,1000))
    c=i=g=r=target=0; t0=time.perf_counter()
    form={"held":"plain","rename":"rename","word_order":"word_order","nested":"nested","paragraph":"paragraph","free":"free","domain":"free"}[mode]
    domain="B" if mode=="domain" else "A"
    for _ in range(n):
        e=episode(rng,domain,form)
        ranked=candidate_scores(model,e); p=ranked[0]
        c+=p[1]==e["obj_idx"] and p[2]==e["move"]; target+=p[1]==e["obj_idx"]
        ops=OPS_A if domain=="A" else OPS_B; objs=OBJECTS_A if domain=="A" else OBJECTS_B; goals=GOALS_A if domain=="A" else GOALS_B
        vals=[]
        feat=sensor_features(e["before"],e["obj_idx"],e["move"],None)
        for oi,(phrase,mv) in enumerate(ops):
            t=text_features(utterance(objs[e["obj_idx"]],phrase,goals[e["goal_idx"]],form))*model["mask"]
            vals.append((float(t@model["M"]@feat),oi))
        i+=max(vals)[1]==e["op_idx"]
        e2=episode(rng,domain,form,op_idx=e["op_idx"],obj_idx=e["obj_idx"],goal_idx=(e["goal_idx"]+1)%3)
        g+=candidate_scores(model,e2)[0][2]==e["move"]
        scores={(idx,mv):sc for sc,idx,mv in ranked}; wrong=(-e["move"][0],-e["move"][1])
        r+=scores[(e["obj_idx"],e["move"])]>scores[(e["obj_idx"],wrong)]
    return dict(accuracy=c/n,inverse=i/n,goal_change=g/n,failure_repair=r/n,target_accuracy=target/n,
                inference_ms=(time.perf_counter()-t0)*1000/n,training_seconds=tr,
                model_bytes=len(pickle.dumps(model,protocol=4)),active_text_features=float(model["mask"].sum()),
                chosen_channel=model["chosen"])

def run():
    methods=["shared","factorized","shuffle","no_direction"]
    modes=["held","rename","word_order","nested","paragraph","free","domain"]
    raw={}
    for seed in SEEDS:
        raw[str(seed)]={m:{mode:evaluate(seed,m,mode) for mode in modes} for m in methods}
    summary={}
    for m in methods:
        summary[m]={mode:{k:statistics.mean(raw[str(s)][m][mode][k] for s in SEEDS)
                          for k in raw[str(SEEDS[0])][m][mode]} for mode in modes}
    return dict(track="B_operation_goal",cycle=2,
      hypothesis="Anonymous Four-Way Contrast Factorization for Executable Operation Birth",
      seeds=list(SEEDS),summary=summary,raw=raw,
      peak_rss_kib_runtime_included=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      estimated_update_ops_per_episode=TEXT_D*SENSOR_D,
      estimated_inference_ops_per_query=32*TEXT_D*SENSOR_D,candidate_count=32,
      post_treatment_features_used_at_test=False,answer_leakage=False,
      fixed_ontology_or_handwritten_slots_used_by_model=False,
      highschool_level_passed=False,native_japanese_communication_passed=False,
      weak_smartphone_verified=False,completion=False)

if __name__=="__main__":
    print(json.dumps(run(),ensure_ascii=False,indent=2))
