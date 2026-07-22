from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse, hashlib, json, math, pickle, random, resource, statistics, time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵']
VALUES=['棚A','棚B','棚C','棚D','待機','完了','担当一','担当二']
FILLERS=['念のため確認します。','別件は後で扱います。','昨日の記録も残してください。']

@dataclass(frozen=True)
class Cand:
    target:str
    value:str

@dataclass
class Ex:
    text:str
    state:str
    after:str|None
    correct:Cand|None
    kind:str

@dataclass(frozen=True)
class Probe:
    op:str
    index:int


def stable_bit(s:str)->int:
    return hashlib.blake2b(s.encode(),digest_size=1).digest()[0]&1


def spans(text:str):
    out=[]
    for l,r in [('「','」'),('『','』'),('【','】'),('“','”')]:
        pos=0
        while True:
            a=text.find(l,pos)
            if a<0: break
            b=text.find(r,a+1)
            if b<0: break
            x=text[a+1:b]
            if x: out.append(x)
            pos=b+1
    raw=text
    for sep in '。、！？\n': raw=raw.replace(sep,'|')
    chunks=[]
    for c in raw.split('|'):
        c=c.strip()
        if 2<=len(c)<=12: chunks.append(c)
        for n in (2,3,4,5,6,7,8):
            for i in range(max(0,len(c)-n+1)): chunks.append(c[i:i+n])
    freq=Counter(chunks)
    out += [x for x,_ in sorted(freq.items(),key=lambda kv:(kv[1],abs(len(kv[0])-4)))[:16]]
    return list(dict.fromkeys(out))[:16]


def candidates(ex:Ex):
    ss=spans(ex.text)
    cs=[Cand(a,b) for a in ss for b in ss if a!=b]
    return list(dict.fromkeys(cs))[:32]


def apply(state:str,c:Cand):
    i=state.find(c.target)
    if i<0:return state,False
    tail=state[i+len(c.target):]
    cut=0
    while cut<len(tail) and tail[cut] in ' のはを=：:、':cut+=1
    end=cut
    while end<len(tail) and tail[end] not in '、。／\n ':end+=1
    if end==cut:return state,False
    return state[:i+len(c.target)+cut]+c.value+state[i+len(c.target)+end:],True


def surgery(c:Cand,p:Probe,pool:list[Cand]):
    if p.op=='swap_roles': return Cand(c.value,c.target)
    if p.op=='drop_target': return Cand('',c.value)
    if p.op=='drop_value': return Cand(c.target,'')
    if p.op=='rebind_target':
        return Cand(pool[p.index%len(pool)].target,c.value) if pool else c
    if p.op=='rebind_value':
        return Cand(c.target,pool[p.index%len(pool)].value) if pool else c
    if p.op=='rotate':
        q=pool[p.index%len(pool)] if pool else c
        return Cand(q.target,q.value)
    raise ValueError(p)


def raw_observation(ex:Ex,c:Cand,p:Probe,pool:list[Cand]):
    sc=surgery(c,p,pool)
    out,ok=apply(ex.state,sc)
    if not ok:return 'X'
    delta=sum(a!=b for a,b in zip(ex.state,out))+abs(len(ex.state)-len(out))
    return f'{delta}:{hashlib.blake2b(out.encode(),digest_size=2).hexdigest()}'


def env_observation(ex:Ex,p:Probe,pool:list[Cand]):
    if ex.correct is None or ex.after is None:return None
    sc=surgery(ex.correct,p,pool)
    out,ok=apply(ex.state,sc)
    if not ok:return 'X'
    delta=sum(a!=b for a,b in zip(ex.state,out))+abs(len(ex.state)-len(out))
    return f'{delta}:{hashlib.blake2b(out.encode(),digest_size=2).hexdigest()}'

PROBE_OPS=['swap_roles','drop_target','drop_value','rebind_target','rebind_value','rotate']

def probe_space(pool):
    return [Probe(op,i) for op in PROBE_OPS for i in range(min(4,max(1,len(pool))))]


def partitions(ex,alive,p):
    d=defaultdict(list)
    for c in alive:d[raw_observation(ex,c,p,alive)].append(c)
    return d


def train_probe_library(examples,max_lib=12):
    stats=defaultdict(lambda:[0,0,0])
    for ex in examples:
        cs=candidates(ex)
        if ex.correct is None or ex.correct not in cs:continue
        for p in probe_space(cs):
            obs=env_observation(ex,p,cs)
            parts=partitions(ex,cs,p)
            if obs is None or obs not in parts:continue
            stats[p][0]+=1
            stats[p][1]+=int(ex.correct in parts[obs])
            stats[p][2]+=len(cs)-len(parts[obs])
    ranked=[]
    for p,(u,s,g) in stats.items():
        if u<2:continue
        survival=s/u; gain=g/u
        score=(survival**3)*math.log1p(gain)*math.log1p(u)
        ranked.append((score,p,survival,gain,u))
    ranked.sort(reverse=True,key=lambda x:x[0])
    return [x[1] for x in ranked[:max_lib]],ranked[:max_lib]


def choose_probe(ex,alive,used,mode,library):
    ps=library if mode!='all_surgery' else probe_space(alive)
    best=None;bestscore=-1
    for p in ps:
        if p in used:continue
        parts=partitions(ex,alive,p)
        sizes=[len(v) for v in parts.values()]
        if len(sizes)<=1:continue
        split=len(alive)-max(sizes)
        balance=split/max(1,len(alive))
        score=balance
        if score>bestscore:bestscore,best=score,p
    return best,bestscore


def infer(ex,mode,library,max_probes=6,with_null=True):
    alive=candidates(ex);initial=len(alive)
    if not alive:return None,0,initial,'proposal_null'
    used=[]
    for _ in range(max_probes):
        if len(alive)<=1:break
        p,g=choose_probe(ex,alive,used,mode,library)
        if p is None or g<=0:break
        used.append(p);obs=env_observation(ex,p,alive)
        if obs is None:return (None if with_null else alive[0]),len(used),initial,'proposal_null'
        part=partitions(ex,alive,p).get(obs,[])
        if not part:return (None if with_null else alive[0]),len(used),initial,'contradiction'
        alive=part
    if len(alive)==1:return alive[0],len(used),initial,'commit'
    if with_null:
        fits=[]
        for c in alive:
            out,ok=apply(ex.state,c)
            fits.append(int(ok and out!=ex.state))
        if not fits or max(fits)==0:return None,len(used),initial,'fit_null'
    return None,len(used),initial,'abstain'


def build(seed,n,kind):
    rng=random.Random(seed);out=[]
    for _ in range(n):
        o=rng.choice(OBJECTS);v=rng.choice(VALUES)
        state=f'{o}の記録は旧値、別対象の記録は保持値です。'
        correct=Cand(o,v)
        after,_=apply(state,correct)
        if kind=='seen':text=f'対象「{o}」を値「{v}」へ更新してください。'
        elif kind=='ambiguous':
            d=rng.choice([x for x in OBJECTS if x!=o]);w=rng.choice([x for x in VALUES if x!=v])
            text=f'候補「{d}」「{o}」と値「{w}」「{v}」があります。実行対象を決めてください。'
        elif kind=='nested':text=f'報告「旧案『{o}』ではなく、最終値『{v}』を使う」と伝えてください。'
        elif kind=='paraphrase':text=f'{o}について、これからは{v}として扱ってください。'
        elif kind=='subject_omission':text=f'先ほどの対象についてです。値を{v}へ変更してください。'
        elif kind=='paragraph':text=f'{rng.choice(FILLERS)}\n対象は{o}です。\n最終的に{v}へ更新してください。'
        elif kind=='outset':text=f'この依頼には該当候補が含まれていません。{rng.choice(FILLERS)}';correct=None;after=None
        else:raise ValueError(kind)
        out.append(Ex(text,state,after,correct,kind))
    return out


def run(seed,n,kind,library):
    xs=build(seed,n,kind);ans={}
    for mode in ('all_surgery','learned'):
        good=wrong=abst=nulls=recall=probes=cands=0
        start=time.perf_counter()
        for ex in xs:
            cs=candidates(ex);cands+=len(cs)
            if ex.correct is not None and ex.correct in cs:recall+=1
            pred,p,_,status=infer(ex,mode,library)
            probes+=p
            if pred is None:
                abst+=1
                if 'null' in status:nulls+=1
            elif ex.correct is not None and pred==ex.correct:good+=1
            else:wrong+=1
        sec=time.perf_counter()-start
        ans[mode]={'candidate_recall':recall/len(xs),'accuracy':good/len(xs),'wrong_commit':wrong/len(xs),
                   'abstain':abst/len(xs),'null_rate':nulls/len(xs),'mean_probes':probes/len(xs),
                   'mean_candidates':cands/len(xs),'inference_ms':sec*1000/len(xs)}
    return ans


def summarize(raw):
    out={}
    for n,runs in raw.items():
        out[n]={}
        for kind in runs[0]:
            out[n][kind]={}
            for mode in runs[0][kind]:
                out[n][kind][mode]={k:statistics.mean(r[kind][mode][k] for r in runs) for k in runs[0][kind][mode]}
    return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_015.json');a=ap.parse_args()
    raw={};libs={};kinds=['seen','ambiguous','nested','paraphrase','subject_omission','paragraph','outset']
    for n in (30,90,180):
        runs=[];lib_meta=[]
        for seed in (1,7,19):
            train=build(seed+1000,n,'seen')+build(seed+2000,n,'ambiguous')+build(seed+3000,n,'nested')
            lib,meta=train_probe_library(train)
            lib_meta.append([{'probe':p.__dict__,'score':s,'survival':sv,'gain':g,'support':u} for s,p,sv,g,u in meta])
            runs.append({k:run(seed,n,k,lib) for k in kinds})
        raw[str(n)]=runs;libs[str(n)]=lib_meta
    payload={'hypothesis':'Self-Generated Probe Programs from Prediction-Error Gradients',
      'seeds':[1,7,19],'sizes':[30,90,180],'raw':raw,'summary':summarize(raw),'probe_libraries':libs,
      'model_bytes':len(pickle.dumps(libs['180'])),'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      'estimated_complexity':'proposal O(L^2), surgery proposal O(HK), training O(NHK), inference O(PH); H<=32,P<=12',
      'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload['summary']['180'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
