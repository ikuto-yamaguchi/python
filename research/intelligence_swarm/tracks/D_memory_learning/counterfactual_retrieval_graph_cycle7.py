"""Track D cycle 007: counterfactual retrieval-graph proposal.

Falsification probe for episodic memory proposal. It generates alternative
antecedent/update graphs from raw Japanese character spans and evaluates them by
future retrieval/non-interference. No tokenizer, fixed entity/value lexicon,
semantic slots, RAG, vector DB, or external model.
"""
from __future__ import annotations
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
import argparse, json, math, pickle, random, resource, statistics, time

RELATIONS = [
    ("保管場所", ["棚A", "棚B", "棚C", "棚D"]),
    ("担当", ["佐藤", "鈴木", "高橋", "田中"]),
    ("合言葉", ["青空", "朝霧", "月影", "白波"]),
]
NAMES = ["装置甲", "装置乙", "試料赤", "試料青", "箱ひとつ", "箱ふたつ", "部品春", "部品秋"]
OBS_FORMS = [
    "「{e}」の{r}は「{v}」です。",
    "{r}について、「{e}」は「{v}」になっています。",
    "記録します。「{e}」—{r}—「{v}」。",
]
PRONOUN_FORMS = ["その対象の{r}は「{v}」です。", "それの{r}を「{v}」に更新します。"]
OMIT_FORMS = ["続いて{r}は「{v}」です。", "次は「{v}」へ更新。"]
Q_DIRECT = ["「{e}」の{r}は？", "{r}について「{e}」はどうなっていますか？"]
Q_PRONOUN = ["その対象の{r}は？", "それについて、{r}は？"]
Q_LONG = "念のため、途中の雑談は無視して、現在の「{e}」に関する{r}だけを答えてください。"
DISTRACT = ["今日は曇りです。", "この文は記憶対象ではありません。", "別件の確認を後で行います。"]


def ngrams(s: str) -> Counter[str]:
    return Counter(s[i:i+n] for n in (2,3) for i in range(max(0, len(s)-n+1)))

def cosine(a: Counter[str], b: Counter[str]) -> float:
    dot = sum(v*b.get(k,0) for k,v in a.items())
    na = math.sqrt(sum(v*v for v in a.values())); nb = math.sqrt(sum(v*v for v in b.values()))
    return dot/(na*nb+1e-12)

def quoted(s: str) -> list[str]:
    out=[]; start=None
    for i,ch in enumerate(s):
        if ch == '「' and start is None: start=i+1
        elif ch == '」' and start is not None:
            if i>start: out.append(s[start:i])
            start=None
    return out

def normalize_variant(s: str) -> str:
    table=str.maketrans({"１":"1","２":"2","３":"3","－":"-","　":" "})
    return ''.join(ch for ch in s.translate(table).lower() if ch not in " ・_-—、。『』「」()（）")

@dataclass(frozen=True)
class Edge:
    entity: str
    relation_surface: str
    value: str
    t: int

class SurfaceScan:
    def __init__(self): self.rows=[]
    def observe(self,text,t): self.rows.append((text,t))
    def answer(self,q):
        qg=ngrams(q); scored=[]
        for text,t in self.rows:
            vals=quoted(text)
            if len(vals)>=2: scored.append((cosine(qg,ngrams(text)),t,vals[-1]))
        return max(scored, default=(0,0,None))[2], len(self.rows)
    def size(self): return len(pickle.dumps(self))

class RetrievalGraphMemory:
    """Keeps competing episodic graphs and consolidates only predictive winners."""
    def __init__(self, max_hyp=12):
        self.max_hyp=max_hyp
        self.active_entities=deque(maxlen=6)
        self.edges: dict[tuple[str,str], Edge] = {}
        self.alias: dict[str, Counter[str]] = defaultdict(Counter)
        self.schemas: Counter[str] = Counter()
        self.hypotheses_generated=0
        self.hypotheses_collapsed=0
        self.revocations=0

    def _relation_surface(self,text, vals):
        residue=text
        for x in vals: residue=residue.replace(f"「{x}」", "<X>").replace(x,"<X>")
        return residue

    def _candidate_edges(self,text,t):
        vals=quoted(text)
        relation=self._relation_surface(text,vals)
        candidates=[]
        if len(vals)>=2:
            a,b=vals[0],vals[-1]
            candidates += [Edge(a,relation,b,t), Edge(b,relation,a,t)]
            self.active_entities.append(a)
        elif len(vals)==1:
            v=vals[0]
            for ent in list(dict.fromkeys(reversed(self.active_entities))):
                candidates.append(Edge(ent,relation,v,t))
        uniq={ (normalize_variant(c.entity), c.relation_surface, c.value):c for c in candidates }
        self.hypotheses_generated += len(candidates)
        self.hypotheses_collapsed += len(candidates)-len(uniq)
        return list(uniq.values())[:self.max_hyp]

    def observe(self,text,t, future_query=None, future_answer=None, negative_queries=()):
        cands=self._candidate_edges(text,t)
        if not cands: return
        scored=[]
        for e in cands:
            score=0.0
            if future_query is not None and future_answer is not None:
                pred=self._answer_with_edge(future_query,e)
                score += 2.0 if pred==future_answer else -1.0
            for nq,nans in negative_queries:
                pred=self._answer_with_edge(nq,e)
                score += 0.5 if pred in (None,nans) else -1.0
            score += 0.15 if e.entity in text else 0.0
            scored.append((score,e))
        scored.sort(key=lambda x:(x[0],x[1].t), reverse=True)
        if len(scored)>1 and scored[0][0] <= scored[1][0]:
            self.revocations += len(scored)
            return
        best=scored[0][1]
        relkey=self._relation_key(best.relation_surface)
        self.edges[(normalize_variant(best.entity),relkey)] = Edge(best.entity,relkey,best.value,t)
        self.schemas[relkey]+=1
        self.alias[normalize_variant(best.entity)][best.entity]+=1

    def _relation_key(self,s):
        return ''.join(ch for ch in s if ch not in "「」<X>。 、")

    def _answer_with_edge(self,q,e):
        ent_score=max(cosine(ngrams(q),ngrams(e.entity)), cosine(ngrams(normalize_variant(q)),ngrams(normalize_variant(e.entity))))
        rel_score=cosine(ngrams(q),ngrams(e.relation_surface))
        return e.value if ent_score+0.35*rel_score>0.2 else None

    def answer(self,q):
        qn=normalize_variant(q); qg=ngrams(q); scored=[]
        rels=list(self.schemas)
        for (ent,rel),edge in self.edges.items():
            es=max(cosine(ngrams(qn),ngrams(ent)), cosine(qg,ngrams(edge.entity)))
            rs=cosine(qg,ngrams(rel))
            scored.append((es+0.35*rs,edge.t,edge.value))
        if not scored:return None,0
        scored.sort(reverse=True)
        if scored[0][0]<0.16 or (len(scored)>1 and scored[0][0]-scored[1][0]<0.01): return None,len(rels)
        return scored[0][2],len(rels)
    def size(self): return len(pickle.dumps(self))


def episode_stream(rng,n):
    rows=[]; current={}; t=0
    for i in range(n):
        e=rng.choice(NAMES); r,vals=rng.choice(RELATIONS); v=rng.choice(vals); t+=1
        style=rng.random()
        if style<0.68 or not rows:
            text=rng.choice(OBS_FORMS).format(e=e,r=r,v=v)
        elif style<0.85:
            e=rows[-1]['entity']; text=rng.choice(PRONOUN_FORMS).format(r=r,v=v)
        else:
            e=rows[-1]['entity']; text=rng.choice(OMIT_FORMS).format(r=r,v=v)
        current[(e,r)]=v
        q=rng.choice(Q_DIRECT).format(e=e,r=r)
        neg_e=rng.choice([x for x in NAMES if x!=e]); neg_r,_=rng.choice(RELATIONS)
        negq=rng.choice(Q_DIRECT).format(e=neg_e,r=neg_r)
        rows.append(dict(t=t,text=text,entity=e,relation=r,value=v,query=q,negative_query=negq,
                         negative_answer=current.get((neg_e,neg_r))))
        if rng.random()<0.25:
            t+=1; rows.append(dict(t=t,text=rng.choice(DISTRACT),entity=e,relation=r,value=v,query=None,
                                   negative_query=None,negative_answer=None,distractor=True))
    return rows,current


def eval_run(seed,n):
    rng=random.Random(seed); rows,truth=episode_stream(rng,n)
    base=SurfaceScan(); mem=RetrievalGraphMemory(); t0=time.perf_counter()
    for row in rows:
        base.observe(row['text'],row['t'])
        if row.get('distractor'): mem.observe(row['text'],row['t']); continue
        mem.observe(row['text'],row['t'],row['query'],row['value'],[(row['negative_query'],row['negative_answer'])])
    train=time.perf_counter()-t0
    splits={k:[] for k in ('direct','pronoun','variant','long','distractor','one_shot','interference_latest')}
    items=list(truth.items())
    for (e,r),v in rng.sample(items,min(160,len(items))):
        splits['direct'].append((rng.choice(Q_DIRECT).format(e=e,r=r),v))
        splits['variant'].append((rng.choice(Q_DIRECT).format(e=e.replace('ひとつ','１').replace('ふたつ','２'),r=r),v))
        splits['long'].append((Q_LONG.format(e=e,r=r),v))
    for (e,r),v in rng.sample(items,min(120,len(items))): splits['pronoun'].append((rng.choice(Q_PRONOUN).format(r=r),v))
    for (e,r),v in rng.sample(items,min(120,len(items))):
        q="雑談を挟みます。"+rng.choice(DISTRACT)+rng.choice(Q_DIRECT).format(e=e,r=r)
        splits['distractor'].append((q,v))
    novel=[]
    for j in range(60):
        e=f"未知対象{seed}_{j}"; r,vals=rng.choice(RELATIONS); v=rng.choice(vals); t=10000+j
        text=rng.choice(OBS_FORMS).format(e=e,r=r,v=v); q=rng.choice(Q_DIRECT).format(e=e,r=r)
        mem.observe(text,t,q,v,[]); novel.append((q,v))
    splits['one_shot']=novel
    latest=[]
    for j in range(40):
        e=f"更新対象{j}"; r,vals=rng.choice(RELATIONS); v1,v2=rng.sample(vals,2)
        q=rng.choice(Q_DIRECT).format(e=e,r=r)
        mem.observe(rng.choice(OBS_FORMS).format(e=e,r=r,v=v1),11000+2*j,q,v1,[])
        for k in range(15): mem.observe(rng.choice(DISTRACT),12000+j*20+k)
        mem.observe(rng.choice(PRONOUN_FORMS).format(r=r,v=v2),11001+2*j,q,v2,[])
        latest.append((q,v2))
    splits['interference_latest']=latest
    result={}
    for name,pairs in splits.items():
        for model_name,model in [('surface',base),('graph',mem)]:
            st=time.perf_counter(); preds=[model.answer(q)[0] for q,_ in pairs]; dt=(time.perf_counter()-st)*1000/max(1,len(pairs))
            result.setdefault(name,{})[model_name]={
                'accuracy':sum(p==a for p,(_,a) in zip(preds,pairs))/max(1,len(pairs)),
                'abstention':sum(p is None for p in preds)/max(1,len(pairs)),
                'ms_per_query':dt,
            }
    result.update(model_bytes={'surface':base.size(),'graph':mem.size()}, training_seconds=train,
                  edge_count=len(mem.edges), schema_count=len(mem.schemas),
                  generated_hypotheses=mem.hypotheses_generated, collapsed_hypotheses=mem.hypotheses_collapsed,
                  revocations=mem.revocations, graph_reads=max(1,len(mem.schemas)), surface_reads=len(base.rows))
    return result


def summarize(raw):
    out={}
    for n,runs in raw.items():
        out[n]={}
        for split in ('direct','pronoun','variant','long','distractor','one_shot','interference_latest'):
            out[n][split]={}
            for model in ('surface','graph'):
                out[n][split][model]={m:statistics.mean(x[split][model][m] for x in runs) for m in ('accuracy','abstention','ms_per_query')}
        for k in ('training_seconds','edge_count','schema_count','generated_hypotheses','collapsed_hypotheses','revocations','graph_reads','surface_reads'):
            out[n][k]=statistics.mean(x[k] for x in runs)
        out[n]['model_bytes']={m:statistics.mean(x['model_bytes'][m] for x in runs) for m in ('surface','graph')}
    return out


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',default='results_cycle_007.json'); args=ap.parse_args()
    raw={str(n):[eval_run(s,n) for s in (1,7,19)] for n in (48,180,540)}
    payload={'hypothesis':'Counterfactual Retrieval-Graph Proposal with Self-Supervised Coreference',
             'seeds':[1,7,19],'train_sizes':[48,180,540],'raw':raw,'summary':summarize(raw),
             'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             'estimated_update_complexity':'O(H*(Q+N)*G), H<=12','estimated_retrieval_complexity':'O(S*G)',
             'free_japanese_integrated_gate':0.0,'highschool_level_passed':False,
             'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(args.output,'w',encoding='utf-8') as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload['summary'],ensure_ascii=False,indent=2))
if __name__=='__main__': main()
