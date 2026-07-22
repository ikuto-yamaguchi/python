from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
import argparse, json, pickle, random, resource, statistics, time

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
    correct:Cand|None
    marked:bool
    kind:str


def spans(text:str):
    out=[]
    pairs=[('「','」'),('『','』'),('【','】'),('“','”')]
    for l,r in pairs:
        pos=0
        while True:
            a=text.find(l,pos)
            if a<0: break
            b=text.find(r,a+1)
            if b<0: break
            s=text[a+1:b]
            if s: out.append(s)
            pos=b+1
    if not out:
        chunks=[]
        for sep in '。、！？\n': text=text.replace(sep,'|')
        for c in text.split('|'):
            c=c.strip()
            if 2<=len(c)<=12: chunks.append(c)
            for n in (2,3,4,5,6):
                for i in range(max(0,len(c)-n+1)): chunks.append(c[i:i+n])
        freq=Counter(chunks)
        out=[x for x,_ in sorted(freq.items(),key=lambda kv:(kv[1],len(kv[0])))[:12]]
    return list(dict.fromkeys(out))[:12]


def candidates(ex:Ex):
    ss=spans(ex.text)
    cs=[Cand(a,b) for a in ss for b in ss if a!=b]
    return list(dict.fromkeys(cs))[:24]


def apply(state:str,c:Cand):
    i=state.find(c.target)
    if i<0: return state,False
    tail=state[i+len(c.target):]
    cut=0
    while cut<len(tail) and tail[cut] in ' のはを=：:、': cut+=1
    end=cut
    while end<len(tail) and tail[end] not in '、。／\n ': end+=1
    if end==cut: return state,False
    return state[:i+len(c.target)+cut]+c.value+state[i+len(c.target)+end:],True


def raw_outcome(ex:Ex,c:Cand,probe:str):
    new,ok=apply(ex.state,c)
    if probe=='execute': return int(ok and new!=ex.state)
    if probe=='preserve':
        if not ok: return 0
        before=Counter(ex.state.replace(c.target,'',1))
        after=Counter(new.replace(c.target,'',1))
        return int(sum((before-after).values())<=8)
    if probe=='reverse':
        if not ok:return 0
        back,_=apply(new,Cand(c.target,c.target))
        return int(c.target in back)
    if probe=='recall':
        if not ok:return 0
        return int(c.target in new and c.value in new)
    if probe=='next': return int((sum(map(ord,c.target))+len(c.value)+len(ex.text))%3==0)
    raise ValueError(probe)

PROBES=['execute','preserve','reverse','recall','next']


def env_answer(ex:Ex,probe:str):
    if ex.correct is None: return None
    return raw_outcome(ex,ex.correct,probe)


def hash_outcome(ex:Ex,c:Cand,probe:str):
    return hash((ex.text,c.target,c.value,probe)) & 1


def choose_probe(ex,alive,used,mode):
    best=None; bestscore=-1
    for p in PROBES:
        if p in used: continue
        fn=raw_outcome if mode!='hash' else hash_outcome
        vals=[fn(ex,c,p) for c in alive]
        a=sum(vals); b=len(vals)-a
        split=min(a,b)
        support=sum(raw_outcome(ex,c,'execute') for c in alive)/max(1,len(alive))
        score=split if mode=='hash' else split*(0.5+0.5*support)
        if score>bestscore: bestscore,best=score,p
    return best,bestscore


def infer(ex,mode,max_probes=5,with_null=False):
    alive=candidates(ex)
    initial=len(alive)
    if not alive:return None,0,initial,'proposal_null'
    used=[]
    for _ in range(max_probes):
        if len(alive)<=1:break
        p,g=choose_probe(ex,alive,used,mode)
        if p is None or g<=0:break
        used.append(p)
        ans=env_answer(ex,p)
        if ans is None:
            if with_null:return None,len(used),initial,'proposal_null'
            break
        fn=raw_outcome if mode!='hash' else hash_outcome
        nxt=[c for c in alive if fn(ex,c,p)==ans]
        if not nxt:return (None if with_null else alive[0]),len(used),initial,'contradiction'
        alive=nxt
    if len(alive)==1:return alive[0],len(used),initial,'commit'
    if with_null:
        fits=[raw_outcome(ex,c,'execute')+raw_outcome(ex,c,'recall') for c in alive]
        if not fits or max(fits)<2:return None,len(used),initial,'fit_null'
    return None,len(used),initial,'abstain'


def build(seed,n,kind):
    rng=random.Random(seed); out=[]
    for _ in range(n):
        o=rng.choice(OBJECTS); v=rng.choice(VALUES)
        state=f'{o}の記録は旧値、別対象の記録は保持値です。'
        if kind=='seen':
            text=f'対象「{o}」を値「{v}」へ更新してください。'; correct=Cand(o,v); marked=True
        elif kind=='ambiguous':
            d=rng.choice([x for x in OBJECTS if x!=o]); w=rng.choice([x for x in VALUES if x!=v])
            text=f'候補「{d}」「{o}」と値「{w}」「{v}」があります。実行対象を決めてください。'; correct=Cand(o,v); marked=True
        elif kind=='nested':
            text=f'報告「旧案『{o}』ではなく、最終値『{v}』を使う」と伝えてください。'; correct=Cand(o,v); marked=True
        elif kind=='paraphrase':
            text=f'{o}について、これからは{v}として扱ってください。'; correct=Cand(o,v); marked=False
        elif kind=='subject_omission':
            text=f'先ほどの対象についてです。値を{v}へ変更してください。'; correct=Cand(o,v); marked=False
        elif kind=='paragraph':
            text=f'{rng.choice(FILLERS)}\n対象は{o}です。\n最終的に{v}へ更新してください。'; correct=Cand(o,v); marked=False
        elif kind=='outset':
            text=f'この依頼には該当候補が含まれていません。{rng.choice(FILLERS)}'; correct=None; marked=False
        else: raise ValueError(kind)
        out.append(Ex(text,state,correct,marked,kind))
    return out


def run(seed,n,kind):
    xs=build(seed,n,kind); ans={}
    for mode,null in [('hash',False),('causal',False),('causal_null',True)]:
        good=wrong=abst=nulls=recall=probes=cands=0
        start=time.perf_counter()
        for ex in xs:
            cs=candidates(ex); cands+=len(cs)
            if ex.correct is not None and ex.correct in cs:recall+=1
            pred,p,_,status=infer(ex,'hash' if mode=='hash' else 'causal',with_null=null)
            probes+=p
            if pred is None:
                abst+=1
                if 'null' in status:nulls+=1
            elif ex.correct is not None and pred==ex.correct:good+=1
            else:wrong+=1
        sec=time.perf_counter()-start
        ans[mode]={'candidate_recall':recall/max(1,len(xs)),'accuracy':good/max(1,len(xs)),
                   'wrong_commit':wrong/max(1,len(xs)),'abstain':abst/max(1,len(xs)),
                   'null_rate':nulls/max(1,len(xs)),'mean_probes':probes/max(1,len(xs)),
                   'mean_candidates':cands/max(1,len(xs)),'seconds':sec,
                   'inference_ms':sec*1000/max(1,len(xs))}
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
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_014.json');a=ap.parse_args()
    raw={}; kinds=['seen','ambiguous','nested','paraphrase','subject_omission','paragraph','outset']
    for n in (60,180,540):
        runs=[]
        for seed in (1,7,19):runs.append({k:run(seed,n,k) for k in kinds})
        raw[str(n)]=runs
    payload={'hypothesis':'Causal-Survival Probe Programs with Counterfactual Outcome Partitions',
             'seeds':[1,7,19],'sizes':[60,180,540],'raw':raw,'summary':summarize(raw),
             'model_bytes':len(pickle.dumps({'probes':PROBES,'max_candidates':24,'max_probes':5})),
             'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             'estimated_complexity':'proposal O(L^2), probe selection O(PH), recursive update O(PH); H<=24,P<=5',
             'highschool_level_passed':False,'native_japanese_communication_passed':False,
             'weak_smartphone_verified':False,'completion':False}
    with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload['summary']['540'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
