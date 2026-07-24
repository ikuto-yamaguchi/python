from __future__ import annotations
import json, random, time, resource, statistics, math, pickle
from collections import defaultdict, Counter

SEEDS=(1,7,19)
DOMAINS=("d1","d2")
FORMS=("held","rename","unknown_order","omitted","paragraph","free")

LEX={
'd1':{
 'obj':[['ラ','アカモノ'],['ミ','アオモノ']],
 'op':[['ソ','そのまま'],['ギ','ひっくり返す']],
 'noise':['さて','静かに','確認して','次に']},
'd2':{
 'obj':[['プ','ヒダリ'],['ワ','ミギ']],
 'op':[['ト','維持する'],['カ','反転する']],
 'noise':['では','慎重に','観測後','続けて']}}

def effect(before,target,op):
    w=list(before)
    if op==1:w[target]=1-w[target]
    return tuple(w)

def render(rng,dom,target,op,form,alias_train=True):
    L=LEX[dom]
    ai=0 if alias_train else 1
    o=L['obj'][target][ai]; a=L['op'][op][ai]; n=rng.choice(L['noise'])
    if form=='held': return f'{n}{o}を{a}'
    if form=='rename': return f'{L["obj"][target][1]}について{L["op"][op][1]}'
    if form=='unknown_order': return f'{a}、対象は{o}'
    if form=='omitted': return f'{a}'
    if form=='paragraph': return f'{n}\n{o}\n{a}'
    return f'{n}。いま注目しているのは{L["obj"][target][1]}。状態はどうなるか、{L["op"][op][1]}ように扱う。'

def ngrams(s,n=2):
    s=''.join(ch for ch in s if not ch.isspace())
    return [s[i:i+n] for i in range(max(0,len(s)-n+1))]

class DifferenceQuotientModel:
    def __init__(self):
        self.effect_counts=defaultdict(Counter)
        self.pair_counts=defaultdict(Counter)
    def update(self,command,before,after,pair_tag=None):
        delta=(after[0]-before[0],after[1]-before[1])
        for g in set(ngrams(command,2)+ngrams(command,3)):
            self.effect_counts[g][delta]+=1
            if pair_tag is not None:self.pair_counts[g][pair_tag]+=1
    def predict_delta(self,command):
        score=Counter()
        for g in set(ngrams(command,2)+ngrams(command,3)):
            for d,c in self.effect_counts.get(g,{}).items():score[d]+=c
        if not score:return None
        return score.most_common(1)[0][0]
    def predict(self,command,before):
        d=self.predict_delta(command)
        if d is None:return None
        return tuple(max(0,min(1,before[i]+d[i])) for i in range(2))
    def inverse(self,command,before):
        d=self.predict_delta(command)
        if d is None:return None
        if d==(0,0):return ('identity',None)
        if abs(d[0])==1 and d[1]==0:return ('toggle',0)
        if abs(d[1])==1 and d[0]==0:return ('toggle',1)
        return None

def make(seed,dom):
    rng=random.Random(seed*100+(1 if dom=='d1' else 2))
    rows=[]
    for i in range(180):
        before=(rng.randrange(2),rng.randrange(2)); target=rng.randrange(2); op=rng.randrange(2)
        form='held' if i<96 else FORMS[(i-96)%len(FORMS)]
        alias_train=i<96
        cmd=render(rng,dom,target,op,form,alias_train)
        rows.append(dict(before=before,after=effect(before,target,op),target=target,op=op,form=form,command=cmd))
    return rows

def train(rows,method,seed):
    rng=random.Random(seed); m=DifferenceQuotientModel(); train=rows[:96]
    if method=='paired':
        groups=defaultdict(list)
        for r in train:groups[(r['target'],r['op'])].append(r)
        selected=[]
        for _,rs in groups.items():
            best=[]
            for a in rs:
                for b in rs:
                    if a['before'][a['target']]!=b['before'][b['target']]:best=[a,b];break
                if best:break
            selected+=best
        selected=(selected*6)[:32]
    elif method=='random': selected=rng.sample(train,32)
    elif method=='pair_shuffle':
        selected=rng.sample(train,32)
        aft=[r['after'] for r in selected];rng.shuffle(aft)
        selected=[dict(r,after=a) for r,a in zip(selected,aft)]
    else:
        pool=[r for r in train if r['before']==(0,0)]
        selected=(pool*10)[:32]
    for i,r in enumerate(selected):m.update(r['command'],r['before'],r['after'],i//2)
    return m

def eval_model(m,rows):
    out={k:[0,0] for k in ['prospective','inverse','rename','unknown_order','omitted','paragraph','free','counterfactual']}
    for r in rows[96:]:
        p=m.predict(r['command'],r['before']); ok=p==r['after']
        out['prospective'][0]+=ok;out['prospective'][1]+=1
        inv=m.inverse(r['command'],r['before']); truth=('identity',None) if r['op']==0 else ('toggle',r['target'])
        out['inverse'][0]+=inv==truth;out['inverse'][1]+=1
        if r['form'] in out:
            out[r['form']][0]+=ok;out[r['form']][1]+=1
        alt=(1-r['before'][0],1-r['before'][1]); q=m.predict(r['command'],alt)
        out['counterfactual'][0]+=q==effect(alt,r['target'],r['op']);out['counterfactual'][1]+=1
    return {k:a/max(1,b) for k,(a,b) in out.items()}

def main():
    t=time.perf_counter();raw={}
    for s in SEEDS:
        raw[str(s)]={}
        for dom in DOMAINS:
            rows=make(s,dom);raw[str(s)][dom]={}
            for method in ('paired','random','state_static','pair_shuffle'):
                m=train(rows,method,s+len(dom));e=eval_model(m,rows)
                e['model_bytes']=len(pickle.dumps(m));raw[str(s)][dom][method]=e
    summary={}
    for method in ('paired','random','state_static','pair_shuffle'):
        summary[method]={}
        for k in raw['1']['d1'][method]:
            summary[method][k]=statistics.mean(raw[str(s)][d][method][k] for s in SEEDS for d in DOMAINS)
    strict=0
    for s in SEEDS:
        good=True
        for d in DOMAINS:
            a=raw[str(s)][d]['paired']; controls=[raw[str(s)][d][x] for x in ('random','state_static','pair_shuffle')]
            for k in ('rename','unknown_order','free','prospective','inverse','counterfactual'):
                if a[k]-max(c[k] for c in controls)<0.10:good=False
        strict+=good
    result={
      'cycle':12,'hypothesis':'Paired Intervention Difference Quotients Birth Reusable Identity without Enumerated Roles',
      'seeds':SEEDS,'domains':DOMAINS,'summary':summary,'strict_progress_seeds':strict,
      'semantic_identity_gate':False,'decision':'rejected_as_surface_local_pairing',
      'failure_classification':'paired_surface_support_without_cross_alias_identity',
      'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'runtime_seconds':time.perf_counter()-t,
      'model_bytes_mean':summary['paired']['model_bytes'],'estimated_ops':'O(B * |ngrams| * effects)',
      'answer_leakage':False,'under_1gb':True,'weak_smartphone_verified':False,
      'fixed_ontology':False,'enumerated_role_worlds':False,'rag':False,'external_llm':False,
      'highschool_level_passed':False,'completion':False,'raw':raw}
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
