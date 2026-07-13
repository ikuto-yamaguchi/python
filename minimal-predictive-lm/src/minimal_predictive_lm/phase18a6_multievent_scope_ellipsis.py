from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import permutations, product
import json, unicodedata
from pathlib import Path
from typing import Iterable, Mapping, Sequence

ENTS=("アキ","ボブ","チカ","ダイ","エリ","フミ")
ACTS=("渡す","受ける","写す","移す")
AB={"渡す":1,"受ける":0,"写す":1,"移す":0}
PROGRAMS=("LR","RL","R")
TRUE_C={"続いて":"LR","先立ち":"RL","せずに":"R"}
TRUE_E={"にも":("R","L"),"も":("L","R")}
REPS=9; FLIPS=1
PUNCT="。、，,！？!?「」『』（）()【】"
State=tuple[int,...]; Event=tuple[int,int]

class NonIdentifiableDiscourseError(ValueError): pass

@dataclass(frozen=True)
class Obs:
    sentence:str; before:State; after:State
    @property
    def text(self): return norm(self.sentence)

@dataclass(frozen=True)
class Clause:
    left:int; right:int; action:str
    @property
    def event(self): return (self.left,self.right) if AB[self.action] else (self.right,self.left)

@dataclass(frozen=True)
class Fragment: explicit:int; marker:str; action:str
@dataclass(frozen=True)
class Parsed: left:Clause; connector:str; full:Clause|None; fragment:Fragment|None

@dataclass(frozen=True)
class Model:
    connectors:tuple[tuple[str,str],...]
    ellipsis:tuple[tuple[str,str,str],...]
    @property
    def bits(self):
        return len(json.dumps({"c":self.connectors,"e":self.ellipsis,"a":AB,"n":ENTS},ensure_ascii=False,separators=(",",":"),sort_keys=True).encode())*8
    def predict(self,sentence:str,before:Sequence[int]):
        try:
            p=parse(sentence); right=resolve(p,emap(self.ellipsis)); prog=dict(self.connectors)[p.connector]
            return execute(tuple(before),p.left.event,right,prog)
        except (ValueError,KeyError): return None


def norm(s:str):
    s=unicodedata.normalize("NFKC",s)
    for c in PUNCT:s=s.replace(c,"")
    return "".join(s.split())

def full(c:Clause): return ENTS[c.left]+"が"+ENTS[c.right]+"に"+c.action
def frag(f:Fragment): return ENTS[f.explicit]+f.marker+f.action
def render(left:Clause,conn:str,right:Clause|Fragment,i:int,eval=False):
    pre=("念のため","報告では","あとで") if eval else ("今日は","記録では","その後","静かに")
    return pre[i%len(pre)]+full(left)+conn+(full(right) if isinstance(right,Clause) else frag(right))+"。"

def apply(s:State,e:Event):
    r=list(s);r[e[1]]=s[e[0]];return tuple(r)
def execute(s:State,l:Event,r:Event,p:str):
    if p=="LR":return apply(apply(s,l),r)
    if p=="RL":return apply(apply(s,r),l)
    if p=="R":return apply(s,r)
    raise ValueError(p)

def hidden(left:Clause,f:Fragment):
    ex,inh=TRUE_E[f.marker]; prior=left.left if inh=="L" else left.right
    return Clause(f.explicit,prior,f.action) if ex=="L" else Clause(prior,f.explicit,f.action)

def emap(rows): return {m:(e,i) for m,e,i in rows}

def parse_full(t:str,start:int):
    for li,ln in enumerate(ENTS):
        if not t.startswith(ln+"が",start):continue
        q=start+len(ln)+1
        for ri,rn in enumerate(ENTS):
            if not t.startswith(rn+"に",q):continue
            a0=q+len(rn)+1
            for a in ACTS:
                if t.startswith(a,a0):return Clause(li,ri,a),a0+len(a)
    return None

def parse_fragment(t:str,start:int):
    out=[]
    for ei,en in enumerate(ENTS):
        if not t.startswith(en,start):continue
        m0=start+len(en)
        for a in ACTS:
            a0=t.find(a,m0+1)
            if a0<0:continue
            m=t[m0:a0]
            if m and len(m)<=3 and not any(x in m for x in ENTS) and a0+len(a)==len(t):out.append((Fragment(ei,m,a),len(t)))
    return out[0] if len(out)==1 else None

def parse(sentence:str):
    t=norm(sentence); out=[]
    for st in range(len(t)):
        x=parse_full(t,st)
        if not x:continue
        left,end=x
        for rs in range(end+1,len(t)):
            conn=t[end:rs]
            if not conn or len(conn)>5:continue
            f=parse_full(t,rs)
            if f and f[1]==len(t):out.append(Parsed(left,conn,f[0],None))
            g=parse_fragment(t,rs)
            if g:out.append(Parsed(left,conn,None,g[0]))
    out=list(dict.fromkeys(out))
    if len(out)!=1:raise ValueError(f"parse={len(out)}")
    return out[0]

def resolve(p:Parsed,rules:Mapping[str,tuple[str,str]]):
    if p.full:return p.full.event
    if not p.fragment or p.fragment.marker not in rules:raise ValueError("ellipsis")
    ex,inh=rules[p.fragment.marker]; prior=p.left.left if inh=="L" else p.left.right
    c=Clause(p.fragment.explicit,prior,p.fragment.action) if ex=="L" else Clause(prior,p.fragment.explicit,p.fragment.action)
    if c.left==c.right:raise ValueError("self")
    return c.event

def dependency(seed:int,la:str,ra:str):
    a=seed%6;b=(seed+1)%6;c=(seed+2)%6;left=Clause(a,b,la);d=left.event[1]
    right=Clause(d,c,ra) if AB[ra] else Clause(c,d,ra)
    return left,right

def instantiate(spec,seed):
    conn,form,la,ra=spec;left,right=dependency(seed,la,ra)
    if form=="FULL":return left,conn,right
    e=(seed+2)%6
    while e in (left.left,left.right):e=(e+1)%6
    return left,conn,Fragment(e,form,ra)

def build(left,conn,right,i,corrupt=False,eval=False):
    before=tuple(i*100+x+1 for x in range(6)); rr=right if isinstance(right,Clause) else hidden(left,right)
    prog=TRUE_C[conn]
    if corrupt:prog=next(x for x in PROGRAMS if x!=prog)
    return Obs(render(left,conn,right,i,eval),before,execute(before,left.event,rr.event,prog))

TRAIN=(
("続いて","FULL","渡す","写す"),("続いて","にも","受ける","渡す"),("続いて","も","写す","受ける"),
("先立ち","FULL","渡す","受ける"),("先立ち","にも","写す","移す"),("先立ち","も","受ける","写す"),
("せずに","FULL","移す","渡す"),("せずに","にも","渡す","受ける"),("せずに","も","写す","移す"))
TEST=(
("続いて","にも","移す","写す"),("続いて","も","渡す","移す"),
("先立ち","にも","受ける","写す"),("先立ち","も","移す","渡す"),
("せずに","にも","写す","渡す"),("せずに","も","受ける","移す"))

def training():
    return tuple(build(*instantiate(s,j+k),j*REPS+k,corrupt=k<FLIPS) for j,s in enumerate(TRAIN) for k in range(REPS))
def heldout():
    rows=[]
    for j,s in enumerate(TEST):
        for swap in (0,1):
            l,c,r=instantiate(s,20+j)
            if swap:
                l=Clause(l.right,l.left,l.action)
                if isinstance(r,Fragment):
                    e=(r.explicit+2)%6
                    while e in (l.left,l.right):e=(e+1)%6
                    r=Fragment(e,r.marker,r.action)
                else:r=Clause(r.right,r.left,r.action)
            rows.append(build(l,c,r,20000+j,eval=True))
    return tuple(rows)

def error(rows,cr,er):
    n=0
    for row in rows:
        try:
            p=parse(row.sentence); pred=execute(row.before,p.left.event,resolve(p,er),cr[p.connector])
        except (ValueError,KeyError):n+=1;continue
        n+=pred!=row.after
    return n

def induce(rows:Iterable[Obs]):
    rows=tuple(rows); ps=[parse(x.sentence) for x in rows]
    cs=tuple(sorted({p.connector for p in ps})); ms=tuple(sorted({p.fragment.marker for p in ps if p.fragment}))
    strategies=tuple(product("LR",repeat=2)); cand=[]
    for pv in permutations(PROGRAMS,len(cs)):
        cr=dict(zip(cs,pv))
        for ev in product(strategies,repeat=len(ms)):
            if len(set(ev))<len(ms):continue
            er=dict(zip(ms,ev)); n=error(rows,cr,er)
            desc=tuple(sorted(cr.items()))+tuple(sorted((m,*v) for m,v in er.items()))
            cand.append((n,desc,cr,er))
    bestn=min(x[0] for x in cand);best=[x for x in cand if x[0]==bestn]
    uniq={x[1]:x for x in best}
    if len(uniq)!=1:raise NonIdentifiableDiscourseError(f"optima={len(uniq)}")
    _,_,cr,er=next(iter(uniq.values()));second=min((x[0] for x in cand if x[0]>bestn),default=None)
    model=Model(tuple(sorted(cr.items())),tuple(sorted((m,*v) for m,v in er.items())))
    return model,{"candidates":len(cand),"errors":bestn,"second":second}

def score(model,rows):
    rows=tuple(rows);ans=[model.predict(x.sentence,x.before) for x in rows]
    return sum(a==x.after for a,x in zip(ans,rows))/len(rows),sum(a is not None for a in ans)/len(rows)
def sentence_coverage(train,test):return sum(x.text in {y.text for y in train} for x in test)/len(test)
def tuple_coverage(train,test):
    def key(x):
        p=parse(x.sentence);return(p.connector,p.fragment.marker if p.fragment else "FULL",p.left.action,(p.fragment.action if p.fragment else p.full.action))
    known={key(x) for x in train};return sum(key(x) in known for x in test)/len(test)
def order_suite():
    l,r=dependency(5,"渡す","写す");return tuple(build(l,c,r,70000,eval=True) for c in ("続いて","先立ち"))
def orderless_bound(rows,model):
    g=defaultdict(Counter)
    for x in rows:
        p=parse(x.sentence);r=resolve(p,emap(model.ellipsis));g[(tuple(sorted((p.left.event,r))),x.before)][x.after]+=1
    return sum(max(c.values()) for c in g.values())/len(tuple(rows))
def commuting_nonid():
    rows=tuple(build(Clause(0,1,"渡す"),c,Clause(2,3,"写す"),80000+k) for c in ("続いて","先立ち") for k in range(4))
    try:induce(rows)
    except NonIdentifiableDiscourseError:return True
    return False
def interventions(model):
    suite=order_suite();p=[model.predict(x.sentence,x.before) for x in suite];order=p[0]!=p[1] and all(a==x.after for a,x in zip(p,suite))
    before=(11,22,33,44,55,66);l,r=dependency(3,"渡す","写す");l2=Clause(4,l.right,"渡す")
    neg=[model.predict(render(x,"せずに",r,0),before) for x in (l,l2)];scope=neg==[apply(before,r.event)]*2
    f=Fragment(3,"にも","写す");a=Clause(0,1,"渡す");b=Clause(2,1,"渡す")
    ant=[model.predict(render(x,"続いて",f,0),before) for x in (a,b)];ellipsis=None not in ant and ant[0]!=ant[1]
    return order,scope,ellipsis
def unknowns(model):
    l,r=dependency(2,"渡す","写す");u1=render(l,"続いて",r,0).replace("続いて","それから")
    u2=render(l,"続いて",Fragment(3,"にも","写す"),0).replace("にも","へも")
    return model.predict(u1,(1,2,3,4,5,6)) is None,model.predict(u2,(1,2,3,4,5,6)) is None
def literal_bits(model):
    grid=[(c,f,a,b) for c,_ in model.connectors for f in ("FULL",*(x[0] for x in model.ellipsis)) for a in ACTS for b in ACTS]
    return len(json.dumps(grid,ensure_ascii=False,separators=(",",":")).encode())*8

def run():
    tr=training();te=heldout();m,fit=induce(tr);acc,cov=score(m,te);order,scope,ell=interventions(m);u1,u2=unknowns(m)
    checks={
    "connector_programs":dict(m.connectors)==TRUE_C,"ellipsis_rules":emap(m.ellipsis)==TRUE_E,
    "bounded_noise":fit["errors"]==len(TRAIN)*FLIPS,"positive_margin":fit["second"]>fit["errors"],
    "heldout":acc==cov==1,"sentence_memorizer":sentence_coverage(tr,te)==0,"tuple_memorizer":tuple_coverage(tr,te)==0,
    "orderless_bound":orderless_bound(order_suite(),m)==.5,"commuting_nonidentifiable":commuting_nonid(),
    "unknowns_abstain":u1 and u2,"order_intervention":order,"negation_scope":scope,"antecedent_intervention":ell,
    "continuous":all(not any(c.isspace() for c in x.sentence) for x in (*tr,*te))}
    return {"campaign":{"name":"phase18a6-multievent-scope-ellipsis-c1","connector_and_marker_spans_prelisted":False,"inherited":"entity/action/case atoms","public_examples":0},
    "induction":{**fit,"connectors":[list(x) for x in m.connectors],"ellipsis":[list(x) for x in m.ellipsis]},
    "evaluation":{"training_cells":len(TRAIN),"training_rows":len(tr),"heldout_cells":len(TEST),"heldout_rows":len(te),"accuracy":acc,"coverage":cov,"sentence_coverage":sentence_coverage(tr,te),"tuple_coverage":tuple_coverage(tr,te),"orderless_bound":orderless_bound(order_suite(),m)},
    "resources":{"model_bits":m.bits,"literal_grid_bits":literal_bits(m),"source_bytes":Path(__file__).read_bytes().__len__(),"python_included":False},
    "theorem_checks":checks,"all_theorem_checks_pass":all(checks.values()),
    "claim_boundary":{"controlled_two_event_scope_ellipsis":all(checks.values()),"general_discourse":False,"high_school_intelligence":False},
    "limitations":["entity/action/case atoms are inherited","two events only","three connector programs","two one-role ellipsis patterns","no open-domain coreference or explanation","Python substrate excluded"]}

def markdown(p:Mapping[str,object]):
    i=p["induction"];e=p["evaluation"];r=p["resources"]
    return f'''# Phase 18a-6 results: multi-event scope and ellipsis

- Candidate models: **{i["candidates"]}**
- Training errors / second best: **{i["errors"]} / {i["second"]}**
- Connector programs: **{i["connectors"]}**
- Ellipsis rules: **{i["ellipsis"]}**
- Training cells / rows: **{e["training_cells"]} / {e["training_rows"]}**
- Held-out cells / rows: **{e["heldout_cells"]} / {e["heldout_rows"]}**
- Accuracy / coverage: **{100*e["accuracy"]:.1f}% / {100*e["coverage"]:.1f}%**
- Sentence / joint-tuple memorizer coverage: **{100*e["sentence_coverage"]:.1f}% / {100*e["tuple_coverage"]:.1f}%**
- Orderless-event upper bound: **{100*e["orderless_bound"]:.1f}%**
- Factorized payload / literal capability grid: **{r["model_bits"]} / {r["literal_grid_bits"]} bits**

This is controlled two-event order, suppress-left scope, and one-role ellipsis—not general Japanese discourse or high-school intelligence.
'''
def main():
    p=run();Path("results").mkdir(exist_ok=True);Path("results/phase18a6.json").write_text(json.dumps(p,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");Path("results/phase18a6.md").write_text(markdown(p),encoding="utf-8");print(markdown(p),end="")
if __name__=="__main__":main()
