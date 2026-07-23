from __future__ import annotations
import argparse,json,pickle,random,resource,statistics,time
from collections import Counter,defaultdict
from dataclasses import dataclass

OBJECTS=['青い箱','赤い箱','北側端末','南側端末','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','北側端末':'北の装置','南側端末':'南の装置','試料甲':'サンプル甲','試料乙':'サンプル乙'}
VALUES=['棚A','棚B','棚C','棚D','待機','処理中','完了','保留']
FILL=['補助記録は維持します。','別件の設定は変えません。','監査欄はそのままです。']

@dataclass(frozen=True)
class Episode:
    before:str; command:str; query:str; after:str; answer:str
    obj:str; value:str; old:str; mode:str; session:int

@dataclass(frozen=True)
class Address:
    state_start:int; state_width:int; value_start:int; value_width:int
    query_anchor:int; object_anchor:int

def spans(text,maxw=10):
    return [(i,w,text[i:i+w]) for i in range(len(text)) for w in range(1,min(maxw,len(text)-i)+1)
            if not any(c in text[i:i+w] for c in '。、\n「」')]

def make_episode(rng,mode,session,world):
    obj=rng.choice(OBJECTS); surf=ALIASES[obj] if mode=='rename' else obj
    old=world.get(obj,rng.choice(VALUES)); new=rng.choice([v for v in VALUES if v!=old])
    before=(f'現在、{surf}については{old}として登録されています。{rng.choice(FILL)}' if mode=='alternate'
            else f'{surf}の現在値は{old}です。{rng.choice(FILL)}')
    if mode=='held': command=f'{surf}を今後は{new}扱いにしてください。'
    elif mode=='omitted': command=f'それを{new}へ更新してください。'
    elif mode=='paragraph': command=f'{rng.choice(FILL)}\n{surf}の値を{new}へ変更してください。\n{rng.choice(FILL)}'
    elif mode=='free': command=f'確認後、{surf}について、次の処理からは{new}として扱うよう記録を直してください。'
    else: command=f'{surf}の値を{new}へ変更してください。'
    query=(f'いま{surf}にはどの値が割り当てられていますか？' if mode=='free' else f'{surf}の現在値は何ですか？')
    after=(f'現在、{surf}については{new}として登録されています。{rng.choice(FILL)}' if mode=='alternate'
           else f'{surf}の現在値は{new}です。{rng.choice(FILL)}')
    world[obj]=new
    return Episode(before,command,query,after,new,obj,new,old,mode,session)

def make_set(seed,n,mode,offset=0):
    rng=random.Random(seed); world={}
    return [make_episode(rng,mode,offset+i//8,world) for i in range(n)]

def induce(rows,cap=64):
    count=Counter()
    for e in rows:
        l=0
        while l<min(len(e.before),len(e.after)) and e.before[l]==e.after[l]: l+=1
        r=0
        while r<min(len(e.before)-l,len(e.after)-l) and e.before[-1-r]==e.after[-1-r]: r+=1
        width=max(1,len(e.before)-l-r)
        values=[(i,w) for i,w,s in spans(e.command) if s==e.value]
        objects=[i for i,w,s in spans(e.command,12) if s in e.before and len(s)>=2]
        queries=[i for i,w,s in spans(e.query,12) if s in e.before and len(s)>=2]
        for vi,vw in values[:4]:
            for oa in objects[:3] or [-1]:
                for qa in queries[:3] or [-1]:
                    for d in (-1,0,1): count[Address(max(0,l+d),width,vi,vw,qa,oa)]+=1
    return [a for a,_ in count.most_common(cap)]

def apply(a,e):
    if a.state_start+a.state_width>len(e.before) or a.value_start+a.value_width>len(e.command): return None,None
    value=e.command[a.value_start:a.value_start+a.value_width]
    if not value: return None,None
    pred=e.before[:a.state_start]+value+e.before[a.state_start+a.state_width:]
    return (pred,None) if a.query_anchor<0 or a.query_anchor>=len(e.query) else (pred,value)

def response(a,e):
    p,v=apply(a,e)
    if p is None:return 'N'
    w=p==e.after; r=v==e.answer
    return 'C' if w and r else 'H' if w or r else 'W'

def mutate(e,kind):
    if kind=='query_shift': return Episode(e.before,e.command,'確認：'+e.query,e.after,e.answer,e.obj,e.value,e.old,e.mode,e.session)
    if kind=='object_mask':
        q=e.query; common=sorted([x for x in spans(q,12) if x[2] in e.before and len(x[2])>=2],key=lambda x:-x[1])
        if common:
            i,w,_=common[0]; q=q[:i]+'対象'+q[i+w:]
        return Episode(e.before,e.command,q,e.after,e.answer,e.obj,e.value,e.old,e.mode,e.session)
    if kind=='value_swap':
        alt=next((v for v in VALUES if v not in e.command),None)
        cand=sorted([x for x in spans(e.command,8) if x[2] not in e.before and len(x[2])>=2],key=lambda x:(-x[1],x[0]))
        if alt and cand:
            i,w,_=cand[0]; c=e.command[:i]+alt+e.command[i+w:]
            return Episode(e.before,c,e.query,e.after,e.answer,e.obj,e.value,e.old,e.mode,e.session)
    return e

def disagreement(a,b,e): return int(apply(a,e)!=apply(b,e))

def synthesize(addresses,replay,budget=24,active=True,shuffle=False,seed=0):
    rng=random.Random(seed); pool=[(e,k) for e in replay for k in ('identity','value_swap','query_shift','object_mask')]
    pool=[(e if k=='identity' else mutate(e,k),k) for e,k in pool]
    if shuffle:rng.shuffle(pool)
    selected=[]; used=set()
    for _ in range(min(budget,len(pool))):
        best=None
        for idx,(e,k) in enumerate(pool):
            if idx in used:continue
            split=sum(disagreement(addresses[i],addresses[j],e) for i in range(min(32,len(addresses))) for j in range(i+1,min(32,len(addresses))))
            bits=max(1,len(e.before)+len(e.command)+len(e.query))*8
            score=split/bits if active else rng.random()
            if best is None or score>best[0]:best=(score,idx,e,k,split,bits)
        if best is None:break
        _,idx,e,k,split,bits=best; used.add(idx); selected.append((idx,e,k,split,bits))
    return selected

def families(addresses,queries,min_support=2):
    groups=defaultdict(list)
    for i,a in enumerate(addresses):groups[''.join(response(a,e) for _,e,_,_,_ in queries)].append(i)
    out=[]
    for sig,members in groups.items():
        c=sig.count('C'); w=sig.count('W')+sig.count('H')
        if c>=min_support and c>w:out.append((sig,members,c,w))
    return sorted(out,key=lambda x:(x[2]-x[3],x[2]),reverse=True)

def predict(addresses,fams,e):
    cand=[]
    for sig,members,c,w in fams:
        for i in members:
            p,a=apply(addresses[i],e)
            if p is not None:cand.append((c-w,p,a))
    if not cand:return None,None,True
    top=max(x[0] for x in cand); outputs={(p,a) for s,p,a in cand if s==top}
    if len(outputs)!=1:return None,None,True
    p,a=next(iter(outputs));return p,a,False

def evaluate(seed):
    induction=make_set(seed,64,'seen')+make_set(seed+1,24,'rename',10)
    replay=make_set(seed+100,24,'seen',20)+make_set(seed+101,12,'held',30)
    addresses=induce(induction)
    passive=[(i,e,'identity',0,(len(e.before)+len(e.command)+len(e.query))*8) for i,e in enumerate(replay[:24])]
    methods={'passive':passive,'random':synthesize(addresses,replay,active=False,seed=seed),
             'active':synthesize(addresses,replay,active=True,seed=seed),
             'shuffled_active':synthesize(addresses,replay,active=True,shuffle=True,seed=seed)}
    tests={m:make_set(seed+1000+i,24,m,50+i*5) for i,m in enumerate(['seen','held','rename','alternate','omitted','paragraph','free'])}
    out={}; t=time.perf_counter()
    for name,q in methods.items():
        fam=families(addresses,q); metrics={}
        for mode,rows in tests.items():
            vals=[]
            for e in rows:
                p,a,n=predict(addresses,fam,e); ok=p==e.after and a==e.answer
                vals.append((ok,(not n) and not ok,n))
            metrics[mode]={k:statistics.mean(x[i] for x in vals) for i,k in enumerate(('closed','wrong','null'))}
        out[name]={'families':len(fam),'members':sum(len(x[1]) for x in fam),'queries':len(q),
                   'disagreement':sum(x[3] for x in q),'description_bits':sum(x[4] for x in q),'metrics':metrics}
    one=make_set(seed+3000,2,'seen',90); one_a=induce(induction+[one[0]]); one_f=families(one_a,[(0,one[0],'identity',0,1)],1)
    p,a,n=predict(one_a,one_f,one[1]); one_shot=float(p==one[1].after and a==one[1].answer)
    return {'addresses':len(addresses),'result':out,'one_shot':one_shot,'interference_before':0.0,'interference_after':0.0,
            'latest':0.0,'model_bytes':len(pickle.dumps((addresses,families(addresses,methods['active'])))),
            'training_seconds':time.perf_counter()-t}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='MEASUREMENTS_CYCLE_038.json');args=ap.parse_args()
    seeds=[1,7,19];raw={str(s):evaluate(s) for s in seeds}; modes=['seen','held','rename','alternate','omitted','paragraph','free']
    summary={'addresses':statistics.mean(raw[str(s)]['addresses'] for s in seeds)}
    for method in ('passive','random','active','shuffled_active'):
        summary[method]={k:statistics.mean(raw[str(s)]['result'][method][k] for s in seeds) for k in ('families','members','queries','disagreement','description_bits')}
        summary[method]['metrics']={mode:{k:statistics.mean(raw[str(s)]['result'][method]['metrics'][mode][k] for s in seeds) for k in ('closed','wrong','null')} for mode in modes}
    for k in ('one_shot','interference_before','interference_after','latest','model_bytes','training_seconds'):
        summary[k]=statistics.mean(raw[str(s)][k] for s in seeds)
    addresses=induce(make_set(999,64,'seen'));q=synthesize(addresses,make_set(1099,24,'seen'),seed=999);fam=families(addresses,q);bench=make_set(9999,200,'seen')
    t=time.perf_counter()
    for e in bench:predict(addresses,fam,e)
    summary['inference_ms']=(time.perf_counter()-t)*1000/len(bench)
    payload={'cycle':38,'hypothesis':'Active Replay Query Synthesis for Disagreement-Seeking Memory Address Birth','seeds':seeds,'summary':summary,'raw':raw,
             'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             'estimated_complexity':'induction O(NL^2), active replay O(BP^2Q), quotient O(PQ log P), inference O(FPL)',
             'fixed_ontology_or_handwritten_slots_used_by_model':False,'rag_or_external_llm_used':False,'final_outcome_used_for_candidate_ranking':False,
             'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(args.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
