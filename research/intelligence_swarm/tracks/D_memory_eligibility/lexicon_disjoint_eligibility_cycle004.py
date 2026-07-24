from __future__ import annotations
import hashlib, json, pickle, random, resource, statistics, time
from pathlib import Path
import numpy as np

DIM_X, DIM_Y = 256, 48
SEEDS = (1, 7, 19)
DIRS = ((1,0),(-1,0),(0,1),(0,-1))
SELECTORS = ("nearest","farthest","leftmost","rightmost")
MOVES = ("right","left","up","down")
PAIRS = np.array([(i,j) for i in range(8) for j in range(i+1,8)])
PROJECTION = np.random.default_rng(123).normal(size=(19,DIM_Y)).astype(np.float32)
OPAQUE = {
"D":{
"nearest":["ネラフを選ぶ","ケミオに属するもの"],"farthest":["ソヴァルを選ぶ","ルグナに属するもの"],
"leftmost":["ピダンを選ぶ","ホゼクに属するもの"],"rightmost":["タメルを選ぶ","ワシオに属するもの"],
"right":["アクトする","ゼル方向へ送る"],"left":["ビレンする","ナク方向へ送る"],
"up":["クオラする","ミト方向へ送る"],"down":["セディする","ラフ方向へ送る"]},
"E":{
"nearest":["ユペクを指定","サノミのもの"],"farthest":["ガルテを指定","ヒレアのもの"],
"leftmost":["ボクシを指定","ネドウのもの"],"rightmost":["メラフを指定","キソンのもの"],
"right":["トゥラする","フェン側へ"],"left":["ラギルする","ポア側へ"],
"up":["シェムする","ウル側へ"],"down":["ドナクする","エギ側へ"]}}

def stable_hash(text:str)->int:
    return int.from_bytes(hashlib.blake2b(text.encode("utf-8"),digest_size=8).digest(),"little")

def language_feature(text:str)->np.ndarray:
    v=np.zeros(DIM_X,np.float32); src="^"+text+"$"
    for width in (2,3):
        for i in range(len(src)-width+1):
            h=stable_hash(src[i:i+width]); v[h%DIM_X]+=1.0 if ((h>>8)&1)==0 else -1.0
    return v/(np.linalg.norm(v)+1e-8)

def generate_world(rng:random.Random, scale:int)->np.ndarray:
    pts=[]; used=set()
    while len(pts)<8:
        p=(rng.randint(-5,5),rng.randint(-5,5))
        if p!=(0,0) and p not in used: used.add(p); pts.append(p)
    return np.array(pts,np.int16)*scale

def select_target(points:np.ndarray, selector:str)->int:
    radial=(points.astype(float)**2).sum(axis=1)
    if selector=="nearest": return int(np.argmin(radial))
    if selector=="farthest": return int(np.argmax(radial))
    if selector=="leftmost": return int(np.argmin(points[:,0]))
    return int(np.argmax(points[:,0]))

def apply_move(points:np.ndarray,target:int,move:str)->np.ndarray:
    out=points.copy(); out[target]+=np.array(DIRS[MOVES.index(move)]); return out

def consequence_base(before:np.ndarray,after:np.ndarray)->np.ndarray:
    bf=before.astype(np.float32); af=after.astype(np.float32); d=af-bf
    changed=np.abs(d).sum(axis=1)>0
    rb=np.sqrt((bf*bf).sum(axis=1)); ra=np.sqrt((af*af).sum(axis=1))
    pb=np.sqrt(((bf[PAIRS[:,0]]-bf[PAIRS[:,1]])**2).sum(axis=1))
    pa=np.sqrt(((af[PAIRS[:,0]]-af[PAIRS[:,1]])**2).sum(axis=1))
    rc=np.sort(ra-rb); pc=np.sort(pa-pb)
    origin=bf[changed].mean(axis=0) if changed.any() else np.zeros(2)
    f=[float(changed.sum()),float(d[:,0].sum()),float(d[:,1].sum()),
       float(np.linalg.norm(d.sum(axis=0))),float(origin[0]),float(origin[1]),float(np.linalg.norm(origin))]
    f.extend(float(x) for x in np.quantile(rc,[0,.25,.5,.75,1]))
    f.extend(float(x) for x in np.quantile(pc,[0,.1,.25,.5,.75,.9,1]))
    return np.array(f,np.float32)

def consequence_feature(before,after,center,scale):
    z=(consequence_base(before,after)-center)/(scale+1e-6)
    y=np.tanh(z@PROJECTION); return y/(np.linalg.norm(y)+1e-8)

def render(rng,selector,move,domain,mode):
    p=OPAQUE[domain]; a=rng.choice(p[selector]); b=rng.choice(p[move])
    if mode=="word_order": return f"{b}。対象条件は{a}。"
    if mode=="paragraph": return f"周囲は維持します。\n{a}。\n続いて{b}。"
    if mode=="free": return f"ほかには触れず、{a}ものだけを{b}ようにしてください。"
    if mode=="inverse": return f"{a}対象に対し、結果として{b}処理を行う。"
    return f"{a}対象を{b}。"

def make_dataset(seed,count,domain,modes,scale):
    rng=random.Random(seed); rows=[]
    for _ in range(count):
        before=generate_world(rng,scale); selector=rng.choice(SELECTORS); mv=rng.choice(MOVES)
        target=select_target(before,selector); after=apply_move(before,target,mv)
        rows.append({"text":render(rng,selector,mv,domain,rng.choice(modes)),"before":before,
                     "after":after,"selector":selector,"move":mv,"target":target,"domain":domain})
    return rows

def train(rows,shuffled=False):
    bases=np.stack([consequence_base(r["before"],r["after"]) for r in rows])
    center=bases.mean(axis=0); scale=bases.std(axis=0)+1e-3
    x=np.stack([language_feature(r["text"]) for r in rows]); xcenter=x.mean(axis=0)
    y=np.stack([consequence_feature(r["before"],r["after"],center,scale) for r in rows])
    if shuffled: y=y[np.random.default_rng(991).permutation(len(y))]
    matrix=(x-xcenter).T@y/len(rows)
    return matrix,xcenter,center,scale

def evaluate(rows,model):
    matrix,xcenter,center,scale=model
    joint=[]; target_hits=[]; move_hits=[]; inverse=[]
    for row in rows:
        q=(language_feature(row["text"])-xcenter)@matrix; q/=np.linalg.norm(q)+1e-8
        candidates=[]
        for target in range(8):
            for mv in MOVES:
                effect=consequence_feature(row["before"],apply_move(row["before"],target,mv),center,scale)
                candidates.append((float(q@effect),target,mv))
        _,pt,pm=max(candidates)
        joint.append(pt==row["target"] and pm==row["move"])
        target_hits.append(pt==row["target"]); move_hits.append(pm==row["move"])
        choices=[(row["selector"],row["move"])]; rr=random.Random(stable_hash(row["text"]))
        while len(choices)<8:
            pair=(rr.choice(SELECTORS),rr.choice(MOVES))
            if pair not in choices: choices.append(pair)
        observed=consequence_feature(row["before"],row["after"],center,scale)
        scores=[]
        for selector,mv in choices:
            iq=(language_feature(render(rr,selector,mv,row["domain"],"inverse"))-xcenter)@matrix
            iq/=np.linalg.norm(iq)+1e-8; scores.append(float(iq@observed))
        inverse.append(int(np.argmax(scores))==0)
    return {"joint":float(np.mean(joint)),"target":float(np.mean(target_hits)),
            "move":float(np.mean(move_hits)),"inverse":float(np.mean(inverse))}

def run_seed(seed):
    output={}
    for domain,scale in (("D",2),("E",3)):
        adapt=make_dataset(seed+1000+(domain=="E")*100,16,domain,("seen","word_order","paragraph","free"),scale)
        correct=train(adapt,False); shuffled=train(adapt,True)
        tests={"held":make_dataset(seed+2000+(domain=="E")*100,96,domain,("seen",),scale),
               "word_order":make_dataset(seed+2001+(domain=="E")*100,96,domain,("word_order",),scale),
               "free":make_dataset(seed+2002+(domain=="E")*100,96,domain,("free",),scale)}
        output[domain]={"correct":{k:evaluate(v,correct) for k,v in tests.items()},
                        "shuffle":{k:evaluate(v,shuffled) for k,v in tests.items()}}
        output[domain]["eligible"]=(all(output[domain]["correct"][k]["joint"]>output[domain]["shuffle"][k]["joint"] for k in tests)
            and min(output[domain]["correct"][k]["inverse"] for k in tests)>.20
            and output[domain]["correct"]["held"]["joint"]>1/32)
        rng=np.random.default_rng(seed+77); interference=[]
        for row in adapt*4:
            r=dict(row); r["after"]=apply_move(row["before"],int(rng.integers(0,8)),MOVES[int(rng.integers(0,4))])
            interference.append(r)
        post=train(adapt+interference,False)
        output[domain]["post_interference"]={k:evaluate(v,post) for k,v in tests.items()}
        output[domain]["model_bytes"]=len(pickle.dumps(correct))
    return output

def main():
    started=time.perf_counter(); raw={str(seed):run_seed(seed) for seed in SEEDS}
    summary={}
    for domain in ("D","E"):
        summary[domain]={}
        for method in ("correct","shuffle","post_interference"):
            summary[domain][method]={}
            for condition in ("held","word_order","free"):
                summary[domain][method][condition]={metric:statistics.mean(raw[str(seed)][domain][method][condition][metric] for seed in SEEDS)
                    for metric in ("joint","target","move","inverse")}
        summary[domain]["eligible_seeds"]=sum(bool(raw[str(seed)][domain]["eligible"]) for seed in SEEDS)
        summary[domain]["model_bytes"]=statistics.mean(raw[str(seed)][domain]["model_bytes"] for seed in SEEDS)
    result={"track":"D_memory_eligibility","cycle":4,
            "hypothesis":"Lexicon-Disjoint Bidirectional Consequence Consistency as Memory Eligibility",
            "seeds":list(SEEDS),"chance":{"joint":1/32,"target":1/8,"move":1/4,"inverse":1/8},
            "adaptation_records_per_domain":16,"interference_records":64,
            "summary":summary,"raw":raw,"runtime_seconds":time.perf_counter()-started,
            "peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "estimated_update_ops_per_episode":DIM_X*DIM_Y,
            "estimated_inference_ops_per_query":32*DIM_Y}
    out=Path(__file__).with_name("MEASUREMENTS_CYCLE_004.json")
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result["summary"],ensure_ascii=False,indent=2))
    return result

if __name__=="__main__": main()
