from __future__ import annotations
import argparse, json, math, pickle, random, resource, statistics, time
from collections import defaultdict, Counter
from dataclasses import dataclass
from pathlib import Path

ENTS=["装置A","装置B","箱α","箱β","部品甲","部品乙","試料春","試料秋"]
VALS=["棚1","棚2","区画東","区画西","担当X","担当Y","室内","廊下"]
SEEN=["{e}を{v}へ移動する","{v}へ{e}を移してください","{e}の行先を{v}に変える"]
HELD_ORDER=["最終的に{v}となるよう、対象の{e}を動かす","対象の{e}について、移動先は{v}とする"]
HELD_LEX=["{e}を{v}へ搬送せよ","{e}を{v}に収容する"]
NESTED=["安全確認後に、{e}を{v}へ移動する","『{e}を{v}へ移動する』という指示を実行する"]
OMIT=["それを{v}へ移してください","対象を{v}へ移す"]
ALT_STATE=["{e}：現在地={v}","現在、{v}にあるのは{e}です。"]

def state(e,v): return f"{e}の現在位置は{v}です。"
def effect(before,after):
    p=0
    while p<min(len(before),len(after)) and before[p]==after[p]: p+=1
    s=0
    while s<min(len(before)-p,len(after)-p) and before[-1-s]==after[-1-s]: s+=1
    be=len(before)-s if s else len(before); ae=len(after)-s if s else len(after)
    return before[p:be],after[p:ae]
def all_common_spans(a,b,min_len=2,max_len=14):
    out=set()
    for i in range(len(a)):
        for j in range(i+min_len,min(len(a),i+max_len)+1):
            x=a[i:j]
            if x in b: out.add(x)
    return sorted(out,key=lambda x:(-len(x),x))[:24]
def boundary_variants(span,before,command):
    out={span}
    for text in (before,command):
        i=text.find(span)
        if i<0: continue
        for l in range(max(0,i-1),i+1):
            for r in range(i+len(span),min(len(text),i+len(span)+1)+1):
                x=text[l:r]
                if x in before and x in command and len(x)>=2: out.add(x)
    for k in range(1,min(4,len(span)-1)):
        out.add(span[k:]); out.add(span[:-k])
    return {x for x in out if len(x)>=2 and x in before and x in command}
def mask_once(text,span,token):
    i=text.find(span)
    return None if i<0 else text[:i]+token+text[i+len(span):]
def grams(text):
    s=text.replace("<E>","").replace("<NEW>","")
    return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))
def cosine(a,b):
    dot=sum(v*b.get(k,0) for k,v in a.items())
    na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return dot/(na*nb+1e-12)

@dataclass(frozen=True)
class Candidate:
    entity_span:str
    old_span:str
    new_span:str
    command_t:str
    residual:str

def propose(before,command,after,refine=True):
    old,new=effect(before,after)
    if not old or not new or new not in command: return []
    spans=set()
    for x in all_common_spans(before,command):
        if x in old or x in new: continue
        spans.update(boundary_variants(x,before,command) if refine else {x})
    out=[]
    for ent in spans:
        ct=mask_once(command,ent,"<E>")
        if ct is None: continue
        ct=mask_once(ct,new,"<NEW>")
        if ct is None or ent in old or ent in new or old not in before: continue
        out.append(Candidate(ent,old,new,ct,ct.replace("<E>","").replace("<NEW>","")))
    return list(set(out))

class Model:
    def __init__(self,refine=True,counterexamples=True,min_support=2):
        self.refine=refine; self.counterexamples=counterexamples; self.min_support=min_support
        self.programs=[]; self.raw=0; self.rejected=0
    def fit(self,rows):
        buckets=defaultdict(list)
        for b,c,a,_,_,_ in rows:
            ps=propose(b,c,a,self.refine); self.raw+=len(ps)
            for p in ps: buckets[p.command_t].append((p,b,c,a))
        for _,items in buckets.items():
            ents={p.entity_span for p,*_ in items}; news={p.new_span for p,*_ in items}
            if len(items)<self.min_support or len(ents)<2 or len(news)<2: continue
            span_counts=Counter(p.entity_span for p,*_ in items); scored=[]
            for p,b,_,a in items[:96]:
                pred=b.replace(p.old_span,p.new_span,1)
                score=2.0*(pred==a)+1.0*(pred.replace(p.new_span,p.old_span,1)==b)
                score+=1.0*(b.replace(p.old_span,"<X>",1)==a.replace(p.new_span,"<X>",1))
                if self.counterexamples:
                    support=span_counts[p.entity_span]
                    partial=max([span_counts[x] for x in (p.entity_span[1:],p.entity_span[:-1]) if len(x)>=2] or [0])
                    score+=0.35*math.log2(1+support)-0.45*math.log2(1+partial)
                    score-=0.25*sum(ch in "をのはがへに、。：=『』" for ch in (p.entity_span[:1]+p.entity_span[-1:]))
                scored.append((score,p))
            best=max(x[0] for x in scored); kept=[p for s,p in scored if s>=best-0.15]
            canonical=min(kept,key=lambda p:(len(p.command_t),p.command_t))
            self.programs.append({"template":canonical.command_t,"features":grams(canonical.command_t),"support":len(items),"mdl":len(canonical.command_t)+math.log2(1+len(items)),"entities":tuple(sorted(ents))})
            self.rejected+=max(0,len(items)-len(kept))
        return self
    def predict(self,before,command):
        candidates=[]; reads=0
        for prog in self.programs:
            reads+=1
            for ent in [e for e in prog["entities"] if e in before and e in command]:
                masked=command.replace(ent,"<E>",1); vals=[]
                for i in range(len(masked)):
                    for j in range(i+2,min(len(masked),i+10)+1):
                        x=masked[i:j]
                        if "<" in x or ">" in x or x in before: continue
                        vals.append(x)
                vals=sorted(set(vals),key=lambda x:(-len(x),x))[:8]
                sim=cosine(grams(masked),prog["features"])
                for new in vals:
                    old_spans=[]
                    for i in range(len(before)):
                        for j in range(i+2,min(len(before),i+10)+1):
                            old=before[i:j]
                            if old==ent or old in ent or ent in old: continue
                            old_spans.append((len(old),i,j,old))
                    for _,i,j,old in sorted(set(old_spans),reverse=True)[:8]:
                        out=before[:i]+new+before[j:]
                        score=sim+0.03*len(old)-0.01*abs(len(new)-len(old))
                        candidates.append((score,-prog["mdl"],out))
        if not candidates: return None,reads,0
        candidates.sort(reverse=True); top=candidates[0][0]
        outs={o for s,_,o in candidates if s>=top-1e-9}
        return (next(iter(outs)) if len(outs)==1 else None),reads,len(candidates)

def make(rng,n,forms,state_forms="normal"):
    rows=[]
    for _ in range(n):
        e=rng.choice(ENTS); old,new=rng.sample(VALS,2); form=rng.choice(forms)
        if state_forms=="normal": b,a=state(e,old),state(e,new)
        elif state_forms=="alt1": b,a=ALT_STATE[0].format(e=e,v=old),ALT_STATE[0].format(e=e,v=new)
        else: b,a=ALT_STATE[1].format(e=e,v=old),ALT_STATE[1].format(e=e,v=new)
        rows.append((b,form.format(e=e,v=new),a,e,old,new))
    return rows
def quality(rows,refine):
    tp=total=0
    for b,c,a,e,o,n in rows:
        ps=propose(b,c,a,refine); total+=len(ps)
        tp+=any(p.entity_span==e and p.old_span==o and p.new_span==n for p in ps)
    return {"recall":tp/len(rows),"precision":tp/max(1,total),"mean_candidates":total/len(rows)}
def eval_one(seed,n):
    rng=random.Random(seed); train=make(rng,n,SEEN)
    models={"cross_episode":Model(False,False).fit(train),"boundary_refine_no_ce":Model(True,False).fit(train),"counterexample_refine":Model(True,True).fit(train)}
    splits={"seen":make(rng,20,SEEN),"held_order":make(rng,20,HELD_ORDER),"held_lexeme":make(rng,20,HELD_LEX),"nested":make(rng,20,NESTED),"subject_omission":make(rng,20,OMIT),"alternate_state":make(rng,20,SEEN,"alt1"),"alternate_state_inverse":make(rng,20,SEEN,"alt2")}
    out={"proposal_baseline":quality(train,False),"proposal_refined":quality(train,True)}
    for name,m in models.items():
        mo={}
        for sn,rows in splits.items():
            st=time.perf_counter(); ok=reads=cands=0
            for b,c,a,_,_,_ in rows:
                p,r,k=m.predict(b,c); ok+=p==a; reads+=r; cands+=k
            mo[sn]={"accuracy":ok/len(rows),"ms":(time.perf_counter()-st)*1000/len(rows),"reads":reads/len(rows),"candidates":cands/len(rows)}
        mo.update({"model_bytes":len(pickle.dumps(m.programs)),"programs":len(m.programs),"raw_candidates":m.raw,"rejected_counterexamples":m.rejected}); out[name]=mo
    return out
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="results_cycle_011.json"); args=ap.parse_args()
    raw={str(n):[eval_one(s,n) for s in (1,7,19)] for n in (30,90,180)}; summary={}
    for n,runs in raw.items():
        summary[n]={}
        for q in ("proposal_baseline","proposal_refined"):
            summary[n][q]={k:statistics.mean(x[q][k] for x in runs) for k in ("recall","precision","mean_candidates")}
        for method in ("cross_episode","boundary_refine_no_ce","counterexample_refine"):
            d={}
            for split in ("seen","held_order","held_lexeme","nested","subject_omission","alternate_state","alternate_state_inverse"):
                d[split]={k:statistics.mean(x[method][split][k] for x in runs) for k in ("accuracy","ms","reads","candidates")}
            for k in ("model_bytes","programs","raw_candidates","rejected_counterexamples"): d[k]=statistics.mean(x[method][k] for x in runs)
            summary[n][method]=d
    payload={"hypothesis":"Counterexample-Guided Role Boundary Refinement with Cross-Form Execution","seeds":[1,7,19],"train_sizes":[30,90,180],"raw":raw,"summary":summary,"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"estimated_complexity":"train O(N L^2 + C^2); infer O(P L^3), capped value spans 8","free_japanese_integrated_gate":0.0,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    Path(args.output).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(summary["180"],ensure_ascii=False,indent=2))
if __name__=="__main__": main()
