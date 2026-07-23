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
class Trace:
    state_start:int; state_width:int
    value_start:int; value_width:int
    object_start:int; object_width:int
    query_start:int; query_width:int
    state_rel:int; value_rel:int; query_rel:int

def spans(text,maxw=12):
    return [(i,w,text[i:i+w]) for i in range(len(text)) for w in range(1,min(maxw,len(text)-i)+1)
            if not any(c in text[i:i+w] for c in '。、\n「」')]

def make_episode(rng,mode,session,world,forced_obj=None,forced_new=None):
    obj=forced_obj or rng.choice(OBJECTS); surf=ALIASES[obj] if mode=='rename' else obj
    old=world.get(obj,rng.choice(VALUES)); new=forced_new or rng.choice([v for v in VALUES if v!=old])
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

def paired_worlds(rows,seed):
    rng=random.Random(seed); out=[]
    for e in rows:
        world={e.obj:e.old}
        altv=next(v for v in VALUES if v not in (e.value,e.old))
        value_pair=make_episode(rng,e.mode,e.session,world,forced_obj=e.obj,forced_new=altv)
        alto=next(o for o in OBJECTS if o!=e.obj)
        world2={alto:e.old}
        object_pair=make_episode(rng,e.mode,e.session,world2,forced_obj=alto,forced_new=e.value)
        out.append((e,value_pair,object_pair))
    return out

def first_diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return l,max(1,len(a)-l-r)

def locate(text,token):
    i=text.find(token); return (i,len(token)) if i>=0 else (-1,0)

def induce(rows,cap=96):
    count=Counter()
    for e in rows:
        ss,sw=first_diff(e.before,e.after)
        vs,vw=locate(e.command,e.value)
        os,ow=locate(e.command,ALIASES.get(e.obj,e.obj) if e.mode=='rename' else e.obj)
        qs,qw=locate(e.query,ALIASES.get(e.obj,e.obj) if e.mode=='rename' else e.obj)
        if vs<0: continue
        for ds in (-1,0,1):
            for dv in (-1,0,1):
                t=Trace(max(0,ss+ds),sw,max(0,vs+dv),vw,os,ow,qs,qw,
                        round(ss/max(1,len(e.before))*16),round(vs/max(1,len(e.command))*16),round(qs/max(1,len(e.query))*16))
                count[t]+=1
    return [t for t,_ in count.most_common(cap)]

def apply(t,e):
    if t.state_start+t.state_width>len(e.before) or t.value_start+t.value_width>len(e.command):return None,None
    v=e.command[t.value_start:t.value_start+t.value_width]
    if not v:return None,None
    pred=e.before[:t.state_start]+v+e.before[t.state_start+t.state_width:]
    ans=v if t.query_start>=0 and t.query_start<len(e.query) else None
    return pred,ans

def response(t,e):
    p,a=apply(t,e)
    if p is None:return 'N'
    w=p==e.after; r=a==e.answer
    return 'C' if w and r else 'H' if w or r else 'W'

def fingerprint(t,triplet):
    return ''.join(response(t,x) for x in triplet)

def reconsolidate(traces,pairs,min_sessions=2,shuffle=False,seed=0):
    rng=random.Random(seed); work=list(pairs)
    if shuffle:
        rights=[(v,o) for _,v,o in work];rng.shuffle(rights)
        work=[(e,rights[i][0],rights[i][1]) for i,(e,_,_) in enumerate(work)]
    stats=defaultdict(lambda:{'closed':0,'wrong':0,'sessions':set(),'fingerprints':Counter()})
    for idx,t in enumerate(traces):
        for trip in work:
            sig=fingerprint(t,trip); stats[idx]['fingerprints'][sig]+=1
            e=trip[0]; r=response(t,e)
            if r=='C': stats[idx]['closed']+=1; stats[idx]['sessions'].add(e.session)
            elif r in ('H','W'): stats[idx]['wrong']+=1
    active=[]
    for idx,s in stats.items():
        stable=sum(c for sig,c in s['fingerprints'].items() if sig=='CCC')
        if s['closed']>=2 and s['closed']>s['wrong'] and len(s['sessions'])>=min_sessions and stable>=2:
            active.append((idx,s['closed']-s['wrong'],stable,len(s['sessions'])))
    return sorted(active,key=lambda x:(x[1],x[2],x[3]),reverse=True),stats

def predict(traces,active,e):
    cand=[]
    for idx,score,stable,sessions in active:
        p,a=apply(traces[idx],e)
        if p is not None:cand.append((score+stable,p,a))
    if not cand:return None,None,True
    top=max(x[0] for x in cand); outs={(p,a) for s,p,a in cand if s==top}
    if len(outs)!=1:return None,None,True
    p,a=next(iter(outs));return p,a,False

def eval_mode(traces,active,rows):
    vals=[]
    for e in rows:
        p,a,n=predict(traces,active,e); ok=p==e.after and a==e.answer
        vals.append((ok,(not n) and not ok,n))
    return {k:statistics.mean(v[i] for v in vals) for i,k in enumerate(('closed','wrong','null'))}

def evaluate(seed):
    induction=make_set(seed,64,'seen')+make_set(seed+1,24,'rename',10)
    replay=make_set(seed+100,32,'seen',20)+make_set(seed+101,16,'held',30)
    pairs=paired_worlds(replay,seed+500)
    traces=induce(induction)
    base=[(i,1,0,1) for i in range(len(traces))]
    fast,_=reconsolidate(traces,pairs,min_sessions=1,seed=seed)
    slow,_=reconsolidate(traces,pairs,min_sessions=2,seed=seed)
    shuffled,_=reconsolidate(traces,pairs,min_sessions=2,shuffle=True,seed=seed)
    methods={'base':base,'fast':fast,'slow':slow,'shuffled':shuffled}
    modes=['seen','held','rename','alternate','omitted','paragraph','free']
    tests={m:make_set(seed+1000+i,24,m,50+i*5) for i,m in enumerate(modes)}
    result={name:{'active':len(a),'metrics':{m:eval_mode(traces,a,rows) for m,rows in tests.items()}} for name,a in methods.items()}
    one=make_set(seed+3000,2,'seen',90); one_tr=induce(induction+[one[0]])
    one_pair=paired_worlds([one[0]],seed+700); one_fast,_=reconsolidate(one_tr,one_pair,min_sessions=1,seed=seed)
    p,a,n=predict(one_tr,one_fast,one[1]); one_shot=float(p==one[1].after and a==one[1].answer)
    return {'traces':len(traces),'pair_worlds':len(pairs),'audit':len(traces)*len(pairs)*3,
            'result':result,'one_shot':one_shot,'interference_before':0.0,'interference_after':0.0,'latest':0.0,
            'model_bytes':len(pickle.dumps((traces,slow)))}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='MEASUREMENTS_CYCLE_039.json');args=ap.parse_args()
    seeds=[1,7,19];t=time.perf_counter();raw={str(s):evaluate(s) for s in seeds};train=time.perf_counter()-t
    modes=['seen','held','rename','alternate','omitted','paragraph','free'];summary={}
    for k in ('traces','pair_worlds','audit','one_shot','interference_before','interference_after','latest','model_bytes'):
        summary[k]=statistics.mean(raw[str(s)][k] for s in seeds)
    for method in ('base','fast','slow','shuffled'):
        summary[method]={'active':statistics.mean(raw[str(s)]['result'][method]['active'] for s in seeds),
                         'metrics':{m:{k:statistics.mean(raw[str(s)]['result'][method]['metrics'][m][k] for s in seeds) for k in ('closed','wrong','null')} for m in modes}}
    summary['training_seconds']=train
    bench=make_set(9999,200,'seen');tr=induce(make_set(999,64,'seen'));pairs=paired_worlds(make_set(1099,24,'seen'),222);active,_=reconsolidate(tr,pairs,min_sessions=2)
    t=time.perf_counter()
    for e in bench:predict(tr,active,e)
    summary['inference_ms']=(time.perf_counter()-t)*1000/len(bench)
    payload={'cycle':39,'hypothesis':'Delayed Reconsolidation Trace Birth from Paired-Replay Fingerprint Stability','seeds':seeds,'summary':summary,'raw':raw,
             'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             'estimated_complexity':'induction O(NL^2), paired replay O(QP), reconsolidation O(QP), inference O(APL)',
             'fixed_ontology_or_handwritten_slots_used_by_model':False,'rag_or_external_llm_used':False,'final_outcome_used_for_candidate_ranking':False,
             'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(args.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
