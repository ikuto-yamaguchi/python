from __future__ import annotations
import argparse, json, math, pickle, random, resource, statistics, time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

OBJECTS=["装置A","装置B","箱α","箱β","試料甲","試料乙","端末春","端末秋"]
FIELDS={
 "位置":["棚1","棚2","区画東","区画西"],
 "担当":["担当X","担当Y","担当Z","無担当"],
 "状態":["稼働中","停止中","点検中","待機中"],
}
SEEN={
 "位置":["{e}を{v}へ移動する","{v}へ{e}を移してください","{e}の行先を{v}に変える"],
 "担当":["{e}の担当を{v}へ変更する","{v}を{e}の担当にしてください","{e}は{v}の受け持ちにする"],
 "状態":["{e}の状態を{v}へ切り替える","{e}を{v}にしてください","{v}となるよう{e}を変更する"],
}
HELD_ORDER={
 "位置":["対象の{e}について、最終的な移動先を{v}とする"],
 "担当":["今後{v}が受け持つ対象を{e}とする"],
 "状態":["最終状態が{v}となるよう対象の{e}を扱う"],
}
HELD_LEX={
 "位置":["{e}を{v}へ搬送せよ"],
 "担当":["{e}の責任者として{v}を割り当てる"],
 "状態":["{e}を{v}へ遷移させる"],
}
NESTED={k:["安全確認後に、"+v[0],"『"+v[0]+"』という指示を実行する"] for k,v in SEEN.items()}
OMIT={
 "位置":["それを{v}へ移してください"],
 "担当":["その担当を{v}へ変えてください"],
 "状態":["それを{v}にしてください"],
}

def render_state(objects, values, form=0):
    clauses=[]
    for e in objects:
        p,a,s=values[e]
        if form==0:
            clauses.append(f"{e}は{p}にあり、担当は{a}で、状態は{s}です")
        elif form==1:
            clauses.append(f"{e}：所在={p}／受持={a}／稼働={s}")
        else:
            clauses.append(f"{s}の{e}を{a}が管理し、現在地は{p}です")
    return "。".join(clauses)+"。"

def grams(text):
    s="".join(text.split())
    return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))
def cosine(a,b):
    dot=sum(v*b.get(k,0) for k,v in a.items())
    na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return dot/(na*nb+1e-12)
def split_clauses(text):
    out=[]; start=0
    for i,ch in enumerate(text):
        if ch in "。、／":
            if i>start: out.append((start,i,text[start:i]))
            start=i+1
    if start<len(text): out.append((start,len(text),text[start:]))
    return out

def changed_regions(before,after):
    bc=split_clauses(before); ac=split_clauses(after)
    out=[]
    for bi,(bs,be,b) in enumerate(bc):
        if bi>=len(ac): continue
        a_s,a_e,a=ac[bi]
        if b==a: continue
        p=0
        while p<min(len(b),len(a)) and b[p]==a[p]: p+=1
        q=0
        while q<min(len(b)-p,len(a)-p) and b[-1-q]==a[-1-q]: q+=1
        bend=len(b)-q if q else len(b); aend=len(a)-q if q else len(a)
        old,new=b[p:bend],a[p:aend]
        if old and new:
            out.append({"clause_index":bi,"before_clause":b,"after_clause":a,"old":old,"new":new,
                        "prefix":b[:p],"suffix":b[bend:],"global_start":bs})
    return out

def common_spans(a,b,min_len=2,max_len=12):
    out=set()
    for i in range(len(a)):
        for j in range(i+min_len,min(len(a),i+max_len)+1):
            x=a[i:j]
            if x in b: out.add(x)
    return sorted(out,key=lambda x:(-len(x),x))[:20]

@dataclass(frozen=True)
class Candidate:
    entity:str
    old:str
    new:str
    command_template:str
    clause_prefix:str
    clause_suffix:str
    clause_index:int

def propose(before,command,after,contrastive=True):
    regs=changed_regions(before,after)
    out=[]
    for r in regs:
        if r["new"] not in command: continue
        for e in common_spans(r["before_clause"],command):
            if e in r["old"] or e in r["new"] or len(e)<2: continue
            ct=command.replace(e,"<E>",1).replace(r["new"],"<NEW>",1)
            if "<E>" not in ct or "<NEW>" not in ct: continue
            c=Candidate(e,r["old"],r["new"],ct,r["prefix"].replace(e,"<E>"),r["suffix"],r["clause_index"])
            if contrastive:
                preserved=[x[2] for i,x in enumerate(split_clauses(before)) if i!=r["clause_index"]]
                if any(r["old"] in x or r["new"] in x for x in preserved):
                    continue
            out.append(c)
    return list(set(out))

class Model:
    def __init__(self, contrastive=True, preservation=True):
        self.contrastive=contrastive; self.preservation=preservation
        self.programs=[]; self.raw=0; self.rejected=0
    def fit(self,rows):
        buckets=defaultdict(list)
        for row in rows:
            b,c,a=row[0],row[1],row[2]
            ps=propose(b,c,a,self.contrastive); self.raw+=len(ps)
            for p in ps: buckets[(p.command_template,p.clause_prefix,p.clause_suffix)].append((p,row))
        for key,items in buckets.items():
            ents={p.entity for p,_ in items}; news={p.new for p,_ in items}; olds={p.old for p,_ in items}
            if len(items)<2 or len(ents)<2 or len(news)<2 or len(olds)<2: continue
            valid=[]
            for p,row in items[:96]:
                b,c,a,*_=row
                clauses=split_clauses(b)
                if p.clause_index>=len(clauses): continue
                s,e,cl=clauses[p.clause_index]
                pred=b[:s]+cl.replace(p.old,p.new,1)+b[e:]
                ok=pred==a
                if self.preservation:
                    bcl=[x[2] for x in split_clauses(b)]; acl=[x[2] for x in split_clauses(a)]
                    ok=ok and all(x==y for i,(x,y) in enumerate(zip(bcl,acl)) if i!=p.clause_index)
                if ok: valid.append(p)
                else: self.rejected+=1
            if not valid: continue
            can=min(valid,key=lambda p:(len(p.command_template)+len(p.clause_prefix)+len(p.clause_suffix),p.command_template))
            self.programs.append({"command_template":can.command_template,
                "command_features":grams(can.command_template),"prefix":can.clause_prefix,"suffix":can.clause_suffix,
                "prefix_features":grams(can.clause_prefix+"|"+can.clause_suffix),"support":len(items),
                "mdl":len(can.command_template)+len(can.clause_prefix)+len(can.clause_suffix)+math.log2(1+len(items))})
        return self
    def predict(self,before,command):
        clauses=split_clauses(before); candidates=[]; reads=0
        for prog in self.programs:
            reads+=1
            for ci,(_,_,cl) in enumerate(clauses):
                for ent in common_spans(cl,command)[:5]:
                    masked=command.replace(ent,"<E>",1)
                    simc=cosine(grams(masked),prog["command_features"])
                    if simc<0.24: continue
                    t=prog["command_template"]
                    if "<NEW>" not in t: continue
                    left,right=t.split("<NEW>",1)
                    left=left.replace("<E>",ent); right=right.replace("<E>",ent)
                    pos=command.find(left)
                    if pos<0: continue
                    ns=pos+len(left); ne=command.find(right,ns) if right else len(command)
                    if ne<ns: continue
                    new=command[ns:ne]
                    if len(new)<1 or len(new)>12: continue
                    pref=prog["prefix"].replace("<E>",ent); suff=prog["suffix"]
                    if not cl.startswith(pref) or (suff and not cl.endswith(suff)): continue
                    old_end=len(cl)-len(suff) if suff else len(cl)
                    old=cl[len(pref):old_end]
                    if not old: continue
                    sidx,eidx,_=clauses[ci]
                    newcl=pref+new+suff
                    out=before[:sidx]+newcl+before[eidx:]
                    sims=cosine(grams(prog["prefix"]+"|"+prog["suffix"]),prog["prefix_features"])
                    candidates.append((0.7*simc+0.3*sims,-prog["mdl"],out,ci))
        if not candidates: return None,reads,0
        candidates.sort(reverse=True); best=candidates[0][0]
        outs={o for score,_,o,_ in candidates if score>=best-1e-9}
        return (next(iter(outs)) if len(outs)==1 else None),reads,len(candidates)

def make(rng,n,forms=SEEN,state_form=0,n_objects=2):
    rows=[]; fkeys=list(FIELDS)
    for _ in range(n):
        objs=rng.sample(OBJECTS,n_objects)
        vals={e:tuple(rng.choice(FIELDS[k]) for k in fkeys) for e in objs}
        target=rng.choice(objs); field=rng.choice(fkeys); fi=fkeys.index(field)
        old=vals[target][fi]; new=rng.choice([x for x in FIELDS[field] if x!=old])
        aftervals=dict(vals); tv=list(vals[target]); tv[fi]=new; aftervals[target]=tuple(tv)
        before=render_state(objs,vals,state_form); after=render_state(objs,aftervals,state_form)
        cmd=rng.choice(forms[field]).format(e=target,v=new)
        rows.append((before,cmd,after,target,field,old,new))
    return rows

def quality(rows,contrastive):
    tp=total=0
    for b,c,a,e,f,o,n in rows:
        ps=propose(b,c,a,contrastive); total+=len(ps)
        tp+=any(p.entity==e and p.old==o and p.new==n for p in ps)
    return {"recall":tp/len(rows),"precision":tp/max(1,total),"mean_candidates":total/len(rows)}

def evaluate(seed,n):
    rng=random.Random(seed); train=make(rng,n)
    models={
      "single_change":Model(False,False).fit(train),
      "contrastive_no_preservation":Model(True,False).fit(train),
      "relation_preservation":Model(True,True).fit(train),
    }
    splits={
      "seen":make(rng,24),
      "held_order":make(rng,24,HELD_ORDER),
      "held_lexeme":make(rng,24,HELD_LEX),
      "nested":make(rng,24,NESTED),
      "subject_omission":make(rng,24,OMIT),
      "alternate_state":make(rng,24,SEEN,1),
      "alternate_state_inverse":make(rng,24,SEEN,2),
      "three_objects":make(rng,24,SEEN,0,3),
    }
    out={"proposal_single":quality(train,False),"proposal_contrastive":quality(train,True)}
    for name,m in models.items():
        md={}
        for sn,rows in splits.items():
            st=time.perf_counter(); ok=reads=cands=preserved=0
            for b,c,a,*_ in rows:
                p,r,k=m.predict(b,c); ok+=p==a; reads+=r; cands+=k
                if p is not None:
                    bc=[x[2] for x in split_clauses(b)]; pc=[x[2] for x in split_clauses(p)]; ac=[x[2] for x in split_clauses(a)]
                    changed=[i for i,(x,y) in enumerate(zip(bc,ac)) if x!=y]
                    preserved += bool(changed) and all(pc[i]==bc[i] for i in range(min(len(bc),len(pc))) if i not in changed)
            md[sn]={"accuracy":ok/len(rows),"preservation_rate":preserved/len(rows),
                    "ms":(time.perf_counter()-st)*1000/len(rows),"reads":reads/len(rows),"candidates":cands/len(rows)}
        md.update({"model_bytes":len(pickle.dumps(m.programs)),"programs":len(m.programs),"raw_candidates":m.raw,"rejected":m.rejected})
        out[name]=md
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="results_cycle_012.json"); args=ap.parse_args()
    raw={str(n):[evaluate(s,n) for s in (1,7,19)] for n in (32,96,192)}; summary={}
    for n,runs in raw.items():
        summary[n]={}
        for q in ("proposal_single","proposal_contrastive"):
            summary[n][q]={k:statistics.mean(x[q][k] for x in runs) for k in ("recall","precision","mean_candidates")}
        for method in ("single_change","contrastive_no_preservation","relation_preservation"):
            d={}
            for split in ("seen","held_order","held_lexeme","nested","subject_omission","alternate_state","alternate_state_inverse","three_objects"):
                d[split]={k:statistics.mean(x[method][split][k] for x in runs) for k in ("accuracy","preservation_rate","ms","reads","candidates")}
            for k in ("model_bytes","programs","raw_candidates","rejected"): d[k]=statistics.mean(x[method][k] for x in runs)
            summary[n][method]=d
    payload={"hypothesis":"Relation-Preservation Anti-Unification with Contrastive Multi-Field States",
      "seeds":[1,7,19],"train_sizes":[32,96,192],"raw":raw,"summary":summary,
      "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "estimated_complexity":"train O(N L^2 + C); infer O(P C L^3), capped spans 8/6",
      "free_japanese_integrated_gate":0.0,"highschool_level_passed":False,
      "native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    Path(args.output).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(summary["192"],ensure_ascii=False,indent=2))
if __name__=="__main__": main()
