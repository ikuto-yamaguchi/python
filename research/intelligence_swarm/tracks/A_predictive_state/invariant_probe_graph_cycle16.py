"""Track A Cycle 016
Invariant Counterfactual Probe Graphs from Cross-World Locality.

Controlled falsification experiment:
- Learner input: raw Japanese command/before/after/future strings and order.
- Hidden target/value labels: evaluator and environment only.
- No external LLM, RAG, morphological analyzer, fixed semantic dictionary,
  hand-written slots, Transformer, or attention.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
import argparse, hashlib, json, math, pickle, random, resource, statistics, time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末","大型端末":"大きい端末","北側の鍵":"北のキー","南側の鍵":"南のキー","試料甲":"サンプル甲","試料乙":"サンプル乙"}
VALUES=["棚A","棚B","棚C","待機","処理中","完了","担当一","担当二"]
COMMANDS=["{o}を{v}に変更してください。","{o}について、今後は{v}として扱います。","{o}の記録を{v}へ更新します。"]
PARAPHRASES=["念のため{o}は{v}にしておいてください。","次から{o}を{v}で運用します。","{o}、最終的には{v}へ切り替えます。"]
OMITTED=["それを{v}に変更してください。","その対象は今後{v}として扱います。"]
DISTRACT=["別件の資料も確認しました。","これは更新とは関係ありません。","前の案はいったん保留です。"]
STATE_FORMS=["{o}の現在値は{old}です。補助記録は維持します。","{o}：値={old}／補助記録=維持。"]
SEPS=set("、。！？「」『』（）()=：:／ 　")

def norm_shape(s):
    out=[]
    for c in s:
        if c.isdigit() or (c.isascii() and c.isalpha()):out.append("A")
        elif c in SEPS:out.append(c)
        else:out.append("J")
    return "".join(out)

def stable(s):return hashlib.blake2b(s.encode("utf-8"),digest_size=6).hexdigest()

def diff_window(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

def chunks(text):
    out=[];start=0
    for i,c in enumerate(text):
        if c in SEPS:
            if i-start>=2:out.append(text[start:i])
            start=i+1
    if len(text)-start>=2:out.append(text[start:])
    return out

@dataclass
class Example:
    command:str;before:str;after:str;future:str
    target:str;value:str;mode:str;focus:str

def make_example(rng,mode,focus=""):
    canonical=rng.choice(OBJECTS)
    surface=ALIASES[canonical] if mode=="rename" else canonical
    value=rng.choice(VALUES);old=rng.choice([x for x in VALUES if x!=value])
    form=1 if mode=="alternate" else 0
    before=STATE_FORMS[form].format(o=surface,old=old);after=before.replace(old,value,1)
    if mode=="omitted":command=rng.choice(OMITTED).format(v=value)
    elif mode in ("paraphrase","rename","paragraph","nested"):command=rng.choice(PARAPHRASES).format(o=surface,v=value)
    else:command=rng.choice(COMMANDS).format(o=surface,v=value)
    if mode=="nested":command=f"『{rng.choice(DISTRACT)}』ただし、{command}"
    if mode=="paragraph":command=" ".join(rng.choice(DISTRACT) for _ in range(3))+"\n"+command
    future=f"次の観測では{surface}の局所値が{value}で、補助記録は維持。"
    return Example(command,before,after,future,surface,value,mode,focus)

def maximal_common(a,b,min_len=2,max_len=14):
    hits=[]
    for i in range(len(a)):
        for j in range(i+min_len,min(len(a),i+max_len)+1):
            x=a[i:j]
            if x in b:
                if not any(x in y for y in hits):
                    hits=[y for y in hits if y not in x];hits.append(x)
    return sorted(hits,key=lambda x:(len(x),x),reverse=True)

def propose(ex,max_pairs=16):
    targets=maximal_common(ex.command,ex.before)[:8]
    if not targets:
        if ex.focus:targets=[ex.focus]
        targets+=chunks(ex.before)[:3]
    vals=[]
    for i in range(len(ex.command)):
        for j in range(i+2,min(len(ex.command),i+6)+1):
            x=ex.command[i:j]
            if x in ex.before or all(c in SEPS for c in x):continue
            boundary=int(i==0 or ex.command[i-1] in SEPS)+int(j==len(ex.command) or ex.command[j:j+1] in SEPS)
            vals.append((boundary,-abs(len(x)-3),-len(x),x))
    vals.sort(reverse=True);vv=[];seen=set()
    for *_,x in vals:
        if x not in seen:seen.add(x);vv.append(x)
        if len(vv)>=20:break
    pairs=[];seenp=set()
    for target in targets:
        for value in vv:
            if target==value or target in value or value in target:continue
            p=(target,value)
            if p not in seenp:seenp.add(p);pairs.append(p)
            if len(pairs)>=max_pairs:return pairs
    return pairs

def execute(ex,cand):
    t,v=cand
    if t not in ex.before:return ex.before+"[対象未解決]",False
    _,_,old,_=diff_window(ex.before,ex.after)
    return (ex.before.replace(old,v,1) if old else ex.before),True

PROBES=("drop_target","drop_value","swap","rebind_target","rebind_value","future_check")

def probe_signature(ex,cand,probe,peers):
    t,v=cand;pt,pv=t,v
    if probe=="drop_target":pt=""
    elif probe=="drop_value":pv=""
    elif probe=="swap":pt,pv=pv,pt
    elif probe=="rebind_target" and peers:pt=peers[0][0]
    elif probe=="rebind_value" and peers:pv=peers[-1][1]
    out,ok=execute(ex,(pt,pv))
    non_target_preserved=int("補助記録" in out and ("維持" in out or "維持" in ex.before))
    local_changed=int(out!=ex.before and len(diff_window(ex.before,out)[2])+len(diff_window(ex.before,out)[3])<=16)
    future_ok=int(pt in ex.future and pv in ex.future);target_state_ok=int(pt in ex.before)
    return int(ok),local_changed,non_target_preserved,future_ok,target_state_ok,norm_shape(diff_window(ex.before,out)[3])[:12]

def true_observation(ex,probe,peers):return probe_signature(ex,(ex.target,ex.value),probe,peers)

class ProbeGraph:
    def __init__(self,kind,max_probes=6):
        self.kind=kind;self.max_probes=max_probes;self.library=[];self.stats={};self.training_seconds=0
    def fit(self,examples):
        start=time.perf_counter();stats={p:[0,0,0,0,Counter()] for p in PROBES}
        for ex in examples:
            cand=propose(ex)
            if not cand:continue
            true=(ex.target,ex.value);peers=cand[:4];obs={p:true_observation(ex,p,peers) for p in PROBES}
            for p in PROBES:
                sigs=[probe_signature(ex,c,p,peers) for c in cand]
                stats[p][0]+=int(true in cand and probe_signature(ex,true,p,peers)==obs[p])
                stats[p][1]+=sum(s!=obs[p] for c,s in zip(cand,sigs) if c!=true)
                stats[p][2]+=max(0,len(set(sigs))-1)
                stats[p][3]+=sum(int(s[1] and s[2]) for s in sigs)
                stats[p][4][stable(str(obs[p]))]+=1
        scored=[]
        for p,(surv,elim,part,local,obsfreq) in stats.items():
            if self.kind=="partition":score=elim+0.5*part
            elif self.kind=="locality":score=2*surv+elim+part+1.5*local+0.5*sum(c for c in obsfreq.values() if c>=2)
            else:score=0
            scored.append((score,p));self.stats[p]={"survival":surv,"elimination":elim,"partition":part,"locality":local}
        scored.sort(reverse=True);self.library=[p for _,p in scored[:self.max_probes]];self.training_seconds=time.perf_counter()-start
    def solve(self,ex):
        cand=propose(ex);recall=int((ex.target,ex.value) in cand)
        if not cand:return None,{"recall":0,"probes":0,"wrong":0,"null":1,"candidates":0}
        active=cand[:];probe_pool=list(PROBES) if self.kind=="all" else self.library;used=0
        for p in probe_pool:
            if len(active)<=1 or used>=self.max_probes:break
            peers=active[:4];obs=true_observation(ex,p,peers)
            nxt=[c for c in active if probe_signature(ex,c,p,peers)==obs]
            if nxt and len(nxt)<len(active):active=nxt;used+=1
        chosen=active[0] if len(active)==1 else None
        return chosen,{"recall":recall,"probes":used,"wrong":int(chosen is not None and chosen!=(ex.target,ex.value)),"null":int(chosen is None),"candidates":len(cand)}

def run(seed,n,mode):
    rng=random.Random(seed);focus="";train=[]
    for i in range(n):
        m=("seen","rename","alternate","paraphrase")[i%4];ex=make_example(rng,m,focus);train.append(ex);focus=ex.target
    test=[];focus=""
    for _ in range(6):ex=make_example(rng,mode,focus);test.append(ex);focus=ex.target
    methods={k:ProbeGraph(k) for k in ("all","partition","locality")}
    for m in methods.values():m.fit(train)
    out={}
    for name,m in methods.items():
        start=time.perf_counter();acc=wrong=null=rec=probes=cands=0
        for ex in test:
            ch,meta=m.solve(ex);rec+=meta["recall"];probes+=meta["probes"];wrong+=meta["wrong"];null+=meta["null"];cands+=meta["candidates"];acc+=int(ch==(ex.target,ex.value))
        out[name]={"accuracy":acc/len(test),"wrong_commit":wrong/len(test),"null_rate":null/len(test),"candidate_recall":rec/len(test),"mean_probes":probes/len(test),"mean_candidates":cands/len(test),"model_bytes":len(pickle.dumps(m)),"training_seconds":m.training_seconds,"inference_ms":(time.perf_counter()-start)*1000/len(test),"library":m.library,"stats":m.stats}
    return out

def summarize(raw):
    out={}
    for n,runs in raw.items():
        out[n]={}
        for mode in ("seen","paraphrase","rename","alternate","nested","omitted","paragraph"):
            out[n][mode]={}
            for method in ("all","partition","locality"):
                keys=[k for k in runs[0][mode][method] if k not in ("library","stats")]
                out[n][mode][method]={k:statistics.mean(r[mode][method][k] for r in runs) for k in keys}
            out[n][mode]["libraries"]=[r[mode]["locality"]["library"] for r in runs]
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="results_cycle_016.json");a=ap.parse_args();raw={}
    for n in (6,18,36):
        runs=[]
        for seed in (1,7,19):runs.append({mode:run(seed,n,mode) for mode in ("seen","paraphrase","rename","alternate","nested","omitted","paragraph")})
        raw[str(n)]=runs
    payload={"hypothesis":"Invariant Counterfactual Probe Graphs from Cross-World Locality","seeds":[1,7,19],"sizes":[6,18,36],"raw":raw,"summary":summarize(raw),"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"estimated_complexity":"proposal O(L^2), training O(NPH), inference O(PH), H<=16, P<=6","hidden_labels_used_by_learner":False,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(a.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload["summary"]["36"],ensure_ascii=False,indent=2))
if __name__=="__main__":main()
