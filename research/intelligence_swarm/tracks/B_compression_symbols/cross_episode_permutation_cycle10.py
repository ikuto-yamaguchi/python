from __future__ import annotations
import argparse, json, math, pickle, random, resource, statistics, time, re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

ENTS=["装置A","装置B","箱α","箱β","部品甲","部品乙","試料春","試料秋"]
VALS=["棚1","棚2","区画東","区画西","担当X","担当Y","室内","廊下"]
SEEN=["{e}を{v}へ移動する","{v}へ{e}を移してください","{e}の行先を{v}に変える"]
HELD_ORDER=["最終的に{v}となるよう、対象の{e}を動かす"]
HELD_LEX=["{e}を{v}へ搬送せよ","{e}を{v}に収容する"]
NESTED=["安全確認後に、{e}を{v}へ移動する"]
OMIT=["それを{v}へ移してください"]
ALT_STATE=["{e}：現在地={v}"]

def state(e,v): return f"{e}の現在位置は{v}です。"
def effect(before,after):
    p=0
    while p<min(len(before),len(after)) and before[p]==after[p]: p+=1
    s=0
    while s<min(len(before)-p,len(after)-p) and before[-1-s]==after[-1-s]: s+=1
    bend=len(before)-s if s else len(before); aend=len(after)-s if s else len(after)
    return before[p:bend],after[p:aend],before[:p],before[bend:]
def maximal_common_substrings(a,b,min_len=2,max_len=12):
    hits=[]
    for i in range(len(a)):
        for j in range(i+min_len,min(len(a),i+max_len)+1):
            x=a[i:j]
            if x in b: hits.append(x)
    hits=sorted(set(hits),key=lambda x:(-len(x),x)); out=[]
    for x in hits:
        if not any(x in y for y in out): out.append(x)
    return out[:12]
def replace_once(text,span,token):
    i=text.find(span)
    return None if i<0 else text[:i]+token+text[i+len(span):]

@dataclass(frozen=True)
class Candidate:
    state_before_t:str; state_after_t:str; command_t:str
    entity_span:str; old_span:str; new_span:str

def propose(before,command,after):
    old,new,_,_=effect(before,after)
    if not old or not new or new not in command: return []
    proposals=[]
    for ent in maximal_common_substrings(before,command):
        if ent in old or ent in new or len(ent)<2: continue
        bt=replace_once(before,ent,"<E>"); at=replace_once(after,ent,"<E>"); ct=replace_once(command,ent,"<E>")
        if None in (bt,at,ct): continue
        bt=replace_once(bt,old,"<OLD>"); at=replace_once(at,new,"<NEW>"); ct=replace_once(ct,new,"<NEW>")
        if None in (bt,at,ct): continue
        proposals.append(Candidate(bt,at,ct,ent,old,new))
    return proposals

class Model:
    def __init__(self,cross_episode=True,min_support=2):
        self.cross_episode=cross_episode; self.min_support=min_support
        self.programs={}; self.raw_candidates=0; self.accepted_candidates=0
    def fit(self,rows):
        buckets=defaultdict(list)
        for b,c,a,_,_,_ in rows:
            ps=propose(b,c,a); self.raw_candidates+=len(ps)
            for p in ps: buckets[(p.state_before_t,p.state_after_t,p.command_t)].append(p)
        for key,items in buckets.items():
            entities={x.entity_span for x in items}; news={x.new_span for x in items}; support=len(items)
            if self.cross_episode and (support<self.min_support or len(entities)<2 or len(news)<2): continue
            mdl=len("".join(key))+math.log2(1+support)
            self.programs[key]={"support":support,"mdl":mdl,"entities":tuple(sorted(entities)),"news":tuple(sorted(news))}
            self.accepted_candidates+=1
        return self
    def predict(self,before,command):
        outs=[]; reads=0
        for (bt,at,ct),meta in self.programs.items():
            reads+=1
            pattern=re.escape(bt).replace(re.escape("<E>"),"(.+?)").replace(re.escape("<OLD>"),"(.+?)")
            m=re.fullmatch(pattern,before)
            if not m: continue
            ent,_old=m.group(1),m.group(2)
            cpattern=re.escape(ct.replace("<E>",ent)).replace(re.escape("<NEW>"),"(.+?)")
            cm=re.fullmatch(cpattern,command)
            if not cm: continue
            new=cm.group(1); out=at.replace("<E>",ent).replace("<NEW>",new)
            outs.append((meta["support"],-meta["mdl"],out))
        if not outs: return None,reads,0
        outs.sort(reverse=True); best=outs[0][:2]; unique={o for s,m,o in outs if (s,m)==best}
        return (next(iter(unique)) if len(unique)==1 else None),reads,len(outs)

def make(rng,n,forms,alt_state=False):
    rows=[]
    for _ in range(n):
        e=rng.choice(ENTS); old,new=rng.sample(VALS,2); form=rng.choice(forms)
        b=ALT_STATE[0].format(e=e,v=old) if alt_state else state(e,old)
        a=ALT_STATE[0].format(e=e,v=new) if alt_state else state(e,new)
        rows.append((b,form.format(e=e,v=new),a,e,old,new))
    return rows
def candidate_quality(rows):
    tp=total=gold=0
    for b,c,a,e,old,new in rows:
        ps=propose(b,c,a); total+=len(ps); gold+=1
        tp+=any(p.entity_span==e and p.old_span==old and p.new_span==new for p in ps)
    return {"candidate_recall":tp/gold,"candidate_precision":tp/max(1,total),"mean_candidates":total/gold}
def eval_one(seed,n):
    rng=random.Random(seed); train=make(rng,n,SEEN)
    models={"single_episode":Model(False,1).fit(train),"cross_episode":Model(True,2).fit(train)}
    splits={"seen":make(rng,120,SEEN),"held_order":make(rng,120,HELD_ORDER),"held_lexeme":make(rng,120,HELD_LEX),"nested":make(rng,120,NESTED),"subject_omission":make(rng,120,OMIT),"alternate_state":make(rng,120,SEEN,True)}
    out={"proposal_quality":candidate_quality(train)}
    for name,m in models.items():
        mo={}
        for sn,rows in splits.items():
            st=time.perf_counter(); ok=reads=matched=0
            for b,c,a,_,_,_ in rows:
                p,r,k=m.predict(b,c); reads+=r; matched+=k; ok+=p==a
            mo[sn]={"accuracy":ok/len(rows),"ms":(time.perf_counter()-st)*1000/len(rows),"program_reads":reads/len(rows),"matched_candidates":matched/len(rows)}
        mo.update({"model_bytes":len(pickle.dumps(m.programs)),"programs":len(m.programs),"raw_candidates":m.raw_candidates,"accepted_candidates":m.accepted_candidates})
        out[name]=mo
    return out
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="results_cycle_010.json"); args=ap.parse_args()
    raw={str(n):[eval_one(s,n) for s in (1,7,19)] for n in (60,180,360)}; summary={}
    for n,runs in raw.items():
        summary[n]={"proposal_quality":{k:statistics.mean(x["proposal_quality"][k] for x in runs) for k in ("candidate_recall","candidate_precision","mean_candidates")}}
        for method in ("single_episode","cross_episode"):
            d={}
            for split in ("seen","held_order","held_lexeme","nested","subject_omission","alternate_state"):
                d[split]={k:statistics.mean(x[method][split][k] for x in runs) for k in ("accuracy","ms","program_reads","matched_candidates")}
            for k in ("model_bytes","programs","raw_candidates","accepted_candidates"): d[k]=statistics.mean(x[method][k] for x in runs)
            summary[n][method]=d
    payload={"hypothesis":"Cross-Episode Permutation-Complete Anti-Unification","seeds":[1,7,19],"train_sizes":[60,180,360],"raw":raw,"summary":summary,"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"estimated_complexity":"train O(N L^2); infer O(P L^3), P consolidated programs","free_japanese_integrated_gate":0.0,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    Path(args.output).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(summary["360"],ensure_ascii=False,indent=2))
if __name__=="__main__": main()
