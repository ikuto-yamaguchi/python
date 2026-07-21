"""Cycle B007: effect-conditioned primitive MDL falsification probe.

Learner input is raw before/command/after Japanese text. No entity/value
ontology, morphology, semantic slot labels, RAG, or external LLM is used.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from difflib import SequenceMatcher
import json, math, pickle, random, re, resource, statistics, time

ENTITIES=["赤い箱","青い容器","試料甲号","部品乙号","装置あかつき","札しらゆき","対象春風","対象秋月"]
LOCATIONS=["棚A","棚B","机上","廊下","室内","保管庫一"]
OWNERS=["田中班","佐藤班","解析組","搬送係","品質班","夜勤組"]
STATES=["待機中","検査済み","封印中","使用可能","点検待ち","搬送中"]
PRIMARY_STATE=lambda e,l,o,s:f"{e}の保管場所は{l}です。担当は{o}です。現在状態は{s}です。"
ALT_STATE_FORMS=[lambda e,l,o,s:f"記録：{e}。置き場={l}。受持={o}。状態={s}。",lambda e,l,o,s:f"{e}について、{l}にあり、{o}が担当し、{s}となっています。"]
FORMS={
 "loc":["{e}を{v}へ移してください","{v}へ{e}を移動して","配置先を{v}に変更してください。対象は{e}です"],
 "owner":["{e}の担当を{v}へ替えてください","{v}に{e}を引き継いで","受持を{v}へ変更してください。対象は{e}です"],
 "state":["{e}を{v}にしてください","{v}へ{e}の状態を切り替えて","状態を{v}へ変更してください。対象は{e}です"]}
HELD_ORDER={"loc":["{v}に変更を。保管対象は{e}です","対象{e}について、行き先は{v}です"],"owner":["{v}へ変更を。担当対象は{e}です","対象{e}について、受持先は{v}です"],"state":["{v}へ変更を。対象は{e}です","対象{e}について、更新後は{v}です"]}
HELD_LEXEME={"loc":["{e}を{v}へ搬送して","{v}へ{e}を送り込んで"],"owner":["{e}を{v}へ委ねて","{v}へ{e}を任せて"],"state":["{e}を{v}へ遷移させて","{v}へ{e}を移行して"]}
NESTED={"loc":["安全確認が終わったら、{e}については{v}へ動かすよう手配してください"],"owner":["確認後、{e}については{v}へ受け渡すよう手配してください"],"state":["前処理後、{e}については{v}となるよう更新してください"]}
OMITTED={"loc":["次は{v}へ移してください","{v}への移動でお願いします"],"owner":["次は{v}へ引き継いでください","{v}を担当にしてください"],"state":["次は{v}へ切り替えてください","{v}に更新してください"]}
NOOP=["変更せずそのままにしてください","現状を維持してください"]

@dataclass
class Episode:
    kind:str; entity:str; old:str; new:str; before:str; command:str; after:str; noop:bool=False

def make_state(form,e,vals): return form(e,vals["loc"],vals["owner"],vals["state"])
def make_episode(rng,kind=None,forms=None,rename=False,noop=False):
    kind=kind or rng.choice(tuple(FORMS)); e=f"未知対象{rng.randrange(10**9)}号" if rename else rng.choice(ENTITIES)
    vals={"loc":rng.choice(LOCATIONS),"owner":rng.choice(OWNERS),"state":rng.choice(STATES)}
    pool={"loc":LOCATIONS,"owner":OWNERS,"state":STATES}[kind]; old=vals[kind]
    new=old if noop else rng.choice([x for x in pool if x!=old])
    if rename:
        old=f"旧値{rng.randrange(10**8)}"; new=old if noop else f"新値{rng.randrange(10**8)}"; vals[kind]=old
    before=make_state(PRIMARY_STATE,e,vals)
    if noop: return Episode(kind,e,old,new,before,rng.choice(NOOP),before,True)
    command=rng.choice(forms or FORMS[kind]).format(e=e,v=new); vals2=dict(vals); vals2[kind]=new
    return Episode(kind,e,old,new,before,command,make_state(PRIMARY_STATE,e,vals2),False)

def diff_span(a,b):
    ops=[x for x in SequenceMatcher(None,a,b).get_opcodes() if x[0]!="equal"]
    if not ops:return "","",0,0,0,0
    i1=min(x[1] for x in ops);i2=max(x[2] for x in ops);j1=min(x[3] for x in ops);j2=max(x[4] for x in ops)
    return a[i1:i2],b[j1:j2],i1,i2,j1,j2

def infer_entity(ep):
    best=""
    for n in range(2,min(16,len(ep.command))+1):
        for i in range(len(ep.command)-n+1):
            s=ep.command[i:i+n]
            if s in ep.before and s in ep.after and len(s)>len(best):best=s
    return best

def infer_new(ep):
    best=""
    for n in range(2,min(16,len(ep.command))+1):
        for i in range(len(ep.command)-n+1):
            s=ep.command[i:i+n]
            if s in ep.after and s not in ep.before and len(s)>len(best):best=s
    return best

def clause_bounds(text,start,end):
    seps="。、「」、；;"; left=max([text.rfind(ch,0,start) for ch in seps]+[-1])+1
    rights=[text.find(ch,end) for ch in seps]; rights=[x for x in rights if x>=0]
    return left,(min(rights)+1 if rights else len(text))

def effect_signature(ep):
    old,new,i1,i2,j1,j2=diff_span(ep.before,ep.after)
    if ep.noop or (not old and not new):return ("NOOP",)
    ent=infer_entity(ep);lb,rb=clause_bounds(ep.before,i1,i2);la,ra=clause_bounds(ep.after,j1,j2)
    cb,ca=ep.before[lb:rb],ep.after[la:ra]
    if ent:cb=cb.replace(ent,"<E>",1);ca=ca.replace(ent,"<E>",1)
    return cb.replace(old,"<X>",1),ca.replace(new,"<X>",1)

def proposed_bindings(ep):return infer_entity(ep),infer_new(ep)
def residue(command,ent,new):
    out=command
    if ent:out=out.replace(ent,"<E>",1)
    if new:out=out.replace(new,"<V>",1)
    return out

def grams(s):return Counter(s[i:i+n] for n in (2,3,4) for i in range(max(0,len(s)-n+1)))
def cosine(a,b):
    d=sum(v*b.get(k,0) for k,v in a.items());na=math.sqrt(sum(v*v for v in a.values()));nb=math.sqrt(sum(v*v for v in b.values()))
    return d/(na*nb+1e-12)

def apply_effect(before,ent,new,sig):
    if sig==("NOOP",):return before
    if not new:return None
    bc,ac=sig;pat=re.escape(bc).replace(re.escape("<E>"),"(?P<E>.+?)").replace(re.escape("<X>"),"(?P<X>.+?)")
    m=re.search(pat,before)
    if not m:return None
    bound=ent or m.groupdict().get("E","");repl=ac.replace("<E>",bound).replace("<X>",new)
    return before[:m.start()]+repl+before[m.end():]

class Literal:
    def __init__(self):self.rules=[]
    def fit(self,rows):
        for ep in rows:
            e,v=proposed_bindings(ep);self.rules.append((residue(ep.command,e,v),effect_signature(ep)))
        return self
    def predict(self,ep):
        e,v=proposed_bindings(ep);r=residue(ep.command,e,v)
        for pat,sig in self.rules:
            if pat==r:return apply_effect(ep.before,e,v,sig)
        return None

class EffectPrimitiveMDL:
    def __init__(self,min_sim=.24):self.effects={};self.fragment_to_effect={};self.support=Counter();self.min_sim=min_sim
    def fit(self,rows):
        for ep in rows:self.observe(ep)
        return self
    def observe(self,ep):
        sig=effect_signature(ep);e,v=proposed_bindings(ep);frag=residue(ep.command,e,v);key=json.dumps(sig,ensure_ascii=False)
        self.effects.setdefault(key,{"signature":sig,"fragments":Counter()})["fragments"][frag]+=1
        self.fragment_to_effect[frag]=key;self.support[key]+=1
    def wrong_bridge(self,ep,key):
        e,v=proposed_bindings(ep);frag=residue(ep.command,e,v);self.effects[key]["fragments"][frag]+=1;self.fragment_to_effect[frag]=key
    def predict(self,ep):
        e,v=proposed_bindings(ep);frag=residue(ep.command,e,v)
        if frag in self.fragment_to_effect:return apply_effect(ep.before,e,v,self.effects[self.fragment_to_effect[frag]]["signature"])
        q=grams(frag);scored=[]
        for key,rec in self.effects.items():
            best=max((cosine(q,grams(x)) for x in rec["fragments"]),default=0);scored.append((best+.015*math.log1p(self.support[key]),key))
        scored.sort(reverse=True)
        if not scored or scored[0][0]<self.min_sim or (len(scored)>1 and scored[0][0]-scored[1][0]<.015):return None
        return apply_effect(ep.before,e,v,self.effects[scored[0][1]]["signature"])

def rows(rng,forms,n=120,rename=False):return [make_episode(rng,k:=rng.choice(tuple(FORMS)),forms[k],rename) for _ in range(n)]
def evaluate(seed,n):
    rng=random.Random(seed);train=[make_episode(rng) for _ in range(n)]+[make_episode(rng,noop=True) for _ in range(max(12,n//5))]
    literal=Literal().fit(train);effect=EffectPrimitiveMDL().fit(train);bridged=pickle.loads(pickle.dumps(effect));wrong=pickle.loads(pickle.dumps(effect))
    demos=[make_episode(rng,k,HELD_LEXEME[k]) for k in FORMS]
    for d in demos:bridged.observe(d)
    keys=list(wrong.effects)
    for i,d in enumerate(demos):wrong.wrong_bridge(d,keys[(i+1)%len(keys)])
    splits={"seen":rows(rng,FORMS),"held_order":rows(rng,HELD_ORDER),"unseen_lexeme_zero_shot":rows(rng,HELD_LEXEME),"unseen_lexeme_one_shot":rows(rng,HELD_LEXEME),"rename_one_shot":rows(rng,HELD_LEXEME,rename=True),"nested_one_shot":rows(rng,NESTED),"subject_omission_one_shot":rows(rng,OMITTED),"noop":[make_episode(rng,noop=True) for _ in range(120)]}
    alt=[]
    for _ in range(120):
        kind=rng.choice(tuple(FORMS));e=rng.choice(ENTITIES);vals={"loc":rng.choice(LOCATIONS),"owner":rng.choice(OWNERS),"state":rng.choice(STATES)};old=vals[kind];pool={"loc":LOCATIONS,"owner":OWNERS,"state":STATES}[kind];new=rng.choice([x for x in pool if x!=old]);sf=rng.choice(ALT_STATE_FORMS);before=make_state(sf,e,vals);vals2=dict(vals);vals2[kind]=new;alt.append(Episode(kind,e,old,new,before,rng.choice(FORMS[kind]).format(e=e,v=new),make_state(sf,e,vals2)))
    splits["alternate_state_format"]=alt;models={"literal":literal,"effect":effect,"bridged":bridged,"wrong_bridge":wrong};out={}
    for split,items in splits.items():
        out[split]={}
        for name,m in models.items():
            t=time.perf_counter();pred=[m.predict(x) for x in items];ms=(time.perf_counter()-t)*1000/len(items)
            out[split][name]={"accuracy":sum(p==x.after for p,x in zip(pred,items))/len(items),"abstention":sum(p is None for p in pred)/len(items),"ms_query":ms}
    out.update(literal_bytes=len(pickle.dumps(literal)),effect_bytes=len(pickle.dumps(effect)),bridged_bytes=len(pickle.dumps(bridged)),primitive_count=len(effect.effects),surface_fragment_count=sum(len(x["fragments"]) for x in effect.effects.values()),bridged_fragment_count=sum(len(x["fragments"]) for x in bridged.effects.values()),training_examples=len(train));return out

def summarize(raw):
    out={}
    for n,runs in raw.items():
        out[n]={}
        for split in [k for k,v in runs[0].items() if isinstance(v,dict)]:
            out[n][split]={m:{k:statistics.mean(r[split][m][k] for r in runs) for k in ("accuracy","abstention","ms_query")} for m in ("literal","effect","bridged","wrong_bridge")}
        for k in ("literal_bytes","effect_bytes","bridged_bytes","primitive_count","surface_fragment_count","bridged_fragment_count","training_examples"):out[n][k]=statistics.mean(r[k] for r in runs)
    return out

def main():
    raw={str(n):[evaluate(s,n) for s in (1,7,19)] for n in (60,180,360)}
    payload={"hypothesis":"Effect-Conditioned Primitive MDL with Held-Lexeme Bridging","seeds":[1,7,19],"train_sizes":[60,180,360],"raw":raw,"summary":summarize(raw),"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"estimated_operations":"O(P*F*G)","free_japanese_integrated_gate":0.0,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open("results_cycle_007.json","w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload["summary"]["360"],ensure_ascii=False,indent=2))
if __name__=="__main__":main()
