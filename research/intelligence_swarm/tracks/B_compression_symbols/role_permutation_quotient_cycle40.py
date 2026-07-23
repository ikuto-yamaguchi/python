from __future__ import annotations
import json, math, pickle, random, resource, statistics, time
from collections import Counter

OBJECTS = ["青い箱","赤い箱","北の鍵","南の鍵","試料甲","試料乙","端末一","端末二"]
VALUES = ["棚A","棚B","棚C","棚D","待機","完了","保留","処理中"]
ALIASES = {"青い箱":"青色ケース","赤い箱":"赤色ケース","北の鍵":"北側キー","南の鍵":"南側キー",
           "試料甲":"サンプル甲","試料乙":"サンプル乙","端末一":"第一端末","端末二":"第二端末"}
MODES = ["seen","word_order","lexeme","rename","alternate","nested","omitted","paragraph"]

def episode(rng, mode, obj=None, old=None, new=None):
    obj = obj or rng.choice(OBJECTS)
    old = old or rng.choice(VALUES)
    new = new or rng.choice([v for v in VALUES if v != old])
    surf = ALIASES[obj] if mode == "rename" else obj
    before = f"{surf}の現在値は{old}です。補助記録は維持します。"
    if mode == "word_order":
        command = f"{new}へ変更してください。対象は{surf}です。"
    elif mode == "lexeme":
        command = f"{surf}を次回から{new}扱いにします。"
    elif mode == "alternate":
        before = f"状態報告：{surf}={old}。補助記録は維持。"
        command = f"{surf}を{new}へ。"
    elif mode == "nested":
        command = f"依頼内容は「{surf}を{new}へ変更」です。"
    elif mode == "omitted":
        command = f"それを{new}へ変更してください。"
    elif mode == "paragraph":
        command = f"前段は維持します。\n{surf}を{new}へ変更してください。\n後段も維持します。"
    else:
        command = f"{surf}を{new}へ変更してください。"
    after = before.replace(old, new, 1)
    return {"before":before,"command":command,"after":after,
            "obj":surf,"old":old,"new":new,"mode":mode}

def diff_span(a, b):
    l = 0
    while l < min(len(a),len(b)) and a[l] == b[l]: l += 1
    r = 0
    while r < min(len(a)-l,len(b)-l) and a[-1-r] == b[-1-r]: r += 1
    return (l, len(a)-r, l, len(b)-r)

def allspans(s, maxlen=12):
    return [(i,j,s[i:j]) for i in range(len(s)) for j in range(i+1,min(len(s),i+maxlen)+1)]

def normalized_bucket(i, j, n):
    if n <= 0: return (0,0)
    return (min(7, int(8*i/n)), min(7, int(8*j/n)))

def changed_span(a, b):
    l = 0
    while l < min(len(a),len(b)) and a[l] == b[l]: l += 1
    r = 0
    while r < min(len(a)-l,len(b)-l) and a[-1-r] == b[-1-r]: r += 1
    return (l, len(a)-r, l, len(b)-r)

def canonical_object(surface):
    return next((o for o in OBJECTS if o in surface or ALIASES.get(o)==surface), OBJECTS[0])

def multiworlds(ep, rng):
    obj2 = rng.choice([o for o in OBJECTS if o not in ep["obj"] and ALIASES.get(o,o) != ep["obj"]])
    val2 = rng.choice([v for v in VALUES if v != ep["new"] and v != ep["old"]])
    base_mode = ep["mode"] if ep["mode"] in ("seen","word_order","lexeme") else "seen"
    obj_world = episode(rng, base_mode, obj=obj2, old=ep["old"], new=ep["new"])
    val_world = episode(rng, base_mode, obj=canonical_object(ep["obj"]), old=ep["old"], new=val2)
    order_world = episode(rng, "word_order" if base_mode!="word_order" else "seen",
                          obj=canonical_object(ep["obj"]), old=ep["old"], new=ep["new"])
    return obj_world, val_world, order_world

def anonymous_proposals(ep, worlds, shuffled=False):
    objw, valw, ordw = worlds
    if shuffled: objw, valw = valw, objw
    oc = changed_span(ep["command"], objw["command"])
    vc = changed_span(ep["command"], valw["command"])
    sc = diff_span(ep["before"], ep["after"])
    spans = {"r0":(oc[0],oc[1]), "r1":(vc[0],vc[1]), "r2":(sc[0],sc[1])}
    if any(a>=b for a,b in spans.values()): return []
    payload0 = ep["command"][oc[0]:oc[1]]
    payload1 = ep["command"][vc[0]:vc[1]]
    commute = payload0 in ordw["command"] and payload1 in ordw["command"]
    sig = {
        "state_width": min(7, sc[1]-sc[0]),
        "cmd0_width": min(7, oc[1]-oc[0]),
        "cmd1_width": min(7, vc[1]-vc[0]),
        "state_pos": normalized_bucket(sc[0],sc[1],len(ep["before"])),
        "cmd0_pos": normalized_bucket(oc[0],oc[1],len(ep["command"])),
        "cmd1_pos": normalized_bucket(vc[0],vc[1],len(ep["command"])),
        "order": tuple(sorted(("r0","r1"), key=lambda r: spans[r][0])),
        "commute": commute,
    }
    sep = int(payload0 != payload1 and commute)
    return [(sig, sep)]

def grammar_key(sig, method):
    if method == "pair":
        return (sig["state_width"], sig["cmd1_width"], sig["state_pos"], sig["cmd1_pos"])
    if method == "multiworld":
        return (sig["state_width"], sig["cmd0_width"], sig["cmd1_width"],
                sig["state_pos"], sig["cmd0_pos"], sig["cmd1_pos"], sig["order"])
    return (sig["state_width"], sig["cmd0_width"], sig["cmd1_width"], sig["order"], sig["commute"])

def train(seed, method):
    rng = random.Random(seed)
    rows = [episode(rng, rng.choice(["seen","word_order","lexeme","rename"])) for _ in range(96)]
    t0 = time.perf_counter(); counts=Counter(); supports=Counter(); residual_bits=Counter()
    for ep in rows:
        for sig,sep in anonymous_proposals(ep,multiworlds(ep,rng),shuffled=(method=="shuffle")):
            key=grammar_key(sig,method); counts[key]+=1; supports[key]+=sep; residual_bits[key]+=(1-sep)
    grammar=[]
    for key,c in counts.items():
        bits=8*len(repr(key))+12*residual_bits[key]+math.log2(1+c)
        gain=24*c-bits
        if method=="mdl" and gain<=0: continue
        if method in ("multiworld","quotient","mdl") and supports[key]<2: continue
        grammar.append((key,c,supports[key],bits,gain))
    grammar.sort(key=lambda x:(x[4],x[2],x[1]),reverse=True)
    return grammar[:48],time.perf_counter()-t0

def novel_spans(command,before,maxlen=10):
    return [(i,j,s) for i,j,s in allspans(command,maxlen)
            if s not in before and not any(ch in s for ch in "。、\n「」")]

def common_spans(command,before,maxlen=12):
    return [(i,j,s) for i,j,s in allspans(command,maxlen)
            if len(s)>=2 and s in before and not any(ch in s for ch in "。、\n「」")]

def infer(ep,grammar,method):
    ns=novel_spans(ep["command"],ep["before"]); cs=common_spans(ep["command"],ep["before"])
    candidates=[]
    for key,count,support,bits,gain in grammar:
        if method=="pair":
            sw,vw,sp,vp=key; order=("r0","r1")
        elif method=="multiworld":
            sw,ow,vw,sp,op,vp,order=key
        else:
            sw,ow,vw,order,commute=key
        vals=[x for x in ns if min(7,x[1]-x[0])==vw]
        for si,sj,ss in allspans(ep["before"],12):
            if min(7,sj-si)!=sw: continue
            for vi,vj,val in vals:
                obj_evidence=True if method=="pair" else any((oi<vi)==(order[0]=="r0") for oi,oj,o in cs)
                if not obj_evidence: continue
                pred=ep["before"][:si]+val+ep["before"][sj:]
                score=gain+support*4-math.log2(1+len(vals))
                candidates.append((pred,score,si,sj,vi,vj,val))
    best={}
    for c in candidates:
        if c[0] not in best or c[1]>best[c[0]][1]: best[c[0]]=c
    ranked=sorted(best.values(),key=lambda x:x[1],reverse=True)
    if not ranked: return None,0,0
    entropy=math.log2(len(ranked))
    if len(ranked)>1 and abs(ranked[0][1]-ranked[1][1])<1e-9: return None,len(ranked),entropy
    return ranked[0],len(ranked),entropy

def run():
    methods=["pair","multiworld","quotient","mdl","shuffle"]; raw={}
    for seed in (1,7,19):
        raw[str(seed)]={}
        for method in methods:
            grammar,tr=train(seed,method)
            raw[str(seed)][method]={"grammar":len(grammar),"model_bytes":len(pickle.dumps(grammar)),
                                   "training_seconds":tr,"description_bits":sum(x[3] for x in grammar)}
            for mode in MODES:
                rng=random.Random(seed*1000+MODES.index(mode)); vals=[]; t0=time.perf_counter()
                for _ in range(36):
                    ep=episode(rng,mode); p,n,e=infer(ep,grammar,method)
                    vals.append({"accuracy":p is not None and p[0]==ep["after"],
                                 "wrong":p is not None and p[0]!=ep["after"],"null":p is None,
                                 "candidates":n,"entropy_bits":e,
                                 "exact_state_boundary":p is not None and (p[2],p[3])==(ep["before"].find(ep["old"]),ep["before"].find(ep["old"])+len(ep["old"])),
                                 "value_recall":p is not None and p[6]==ep["new"]})
                raw[str(seed)][method][mode]={k:statistics.mean(float(v[k]) for v in vals) for k in vals[0]}
                raw[str(seed)][method][mode]["inference_ms"]=(time.perf_counter()-t0)*1000/len(vals)
    summary={}
    for method in methods:
        summary[method]={}
        for mode in MODES:
            summary[method][mode]={k:statistics.mean(raw[str(seed)][method][mode][k] for seed in (1,7,19)) for k in raw["1"][method][mode]}
        for k in ("grammar","model_bytes","training_seconds","description_bits"):
            summary[method][k]=statistics.mean(raw[str(seed)][method][k] for seed in (1,7,19))
    return {"cycle":40,"hypothesis":"Role-Permutation Quotient Grammar from Multi-World Co-Segmentation",
            "seeds":[1,7,19],"summary":summary,"raw":raw,
            "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "estimated_complexity":"multi-world co-segmentation O(NL), quotient O(P log P), inference O(GL^2V)",
            "fixed_ontology_or_handwritten_slots_used_by_model":False,
            "final_after_future_used_for_ranking":False,"highschool_level_passed":False,
            "native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}

if __name__=="__main__": print(json.dumps(run(),ensure_ascii=False,indent=2))
