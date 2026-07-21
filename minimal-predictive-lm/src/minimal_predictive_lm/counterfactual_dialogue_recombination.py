from __future__ import annotations
import json, random, resource, statistics, time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

def grams(s: str, n=(2,3)):
    s=''.join(s.split()); out=set()
    for k in n: out |= {s[i:i+k] for i in range(max(0,len(s)-k+1))}
    return out

@dataclass(frozen=True)
class Trace:
    utterance:str; operation:str; response:str; outcome:str

class ContrastiveDialogueSynthesizer:
    def __init__(self, capacity=256, max_reads=32):
        self.capacity=capacity; self.max_reads=max_reads; self.forms={}; self.outcomes={}; self.fragments={}; self.reads=0
    def fit(self, traces:Sequence[Trace]):
        by={}
        for t in traces[-self.capacity:]: by.setdefault((t.response,t.outcome),[]).append(t)
        self.forms={s:[x.utterance for x in xs] for s,xs in by.items()}; self.outcomes={s:xs[0].operation for s,xs in by.items()}
        for sig,xs in by.items():
            local={}; other=set()
            for x in xs:
                for g in grams(x.utterance): local[g]=local.get(g,0)+1
            for s2,ys in by.items():
                if s2!=sig:
                    for y in ys: other |= grams(y.utterance)
            keep=sorted(((c,g) for g,c in local.items() if g not in other),reverse=True)
            self.fragments[sig]=[g for _,g in keep[:12]]
        return self
    def hypotheses(self, utterance:str):
        ug=grams(utterance); rows=[]; self.reads=0
        for sig,forms in list(self.forms.items())[:self.max_reads]:
            self.reads+=1; fg=set(self.fragments.get(sig,()))
            lexical=max((len(ug&grams(f))/max(1,len(ug|grams(f))) for f in forms),default=0)
            discr=len(ug&fg)/max(1,len(fg)); rows.append((0.65*discr+0.35*lexical,sig))
        rows.sort(reverse=True)
        if not rows:return []
        best=rows[0][0]; return [sig for score,sig in rows if score>=best-0.05][:4]
    def clarify(self, utterance:str):
        hs=self.hypotheses(utterance)
        if len(hs)<=1:return '確認せず実行' if hs else '意味候補を構成できません'
        reps=[min(self.forms[s],key=len).strip('。！？?') for s in hs[:2]]
        return '、'.join(reps)+'？'
    def serialized_bytes(self):
        return len(json.dumps({'forms':{str(k):v for k,v in self.forms.items()},'fragments':{str(k):v for k,v in self.fragments.items()}},ensure_ascii=False).encode())

OPS={'color':(['色を教えて','何色ですか','色彩を知りたい','どんな色なの'],'赤です','色が判明'),'place':(['場所を教えて','どこにありますか','所在地は','位置を知りたい'],'駅前です','場所が判明'),'owner':(['持ち主を教えて','誰のものですか','所有者は','だれが持ってる'],'佐藤さんです','所有者が判明'),'count':(['数を教えて','いくつありますか','個数は','何個あるの'],'三つです','数量が判明')}
UNSEEN={'color':['カラーはどうなっていますか','見た目の色合いを尋ねたい'],'place':['所在する地点を答えて','どちらに置かれていますか'],'owner':['これは誰に属しますか','保有している人は'],'count':['数量はいくらですか','全部で何点ありますか']}

def make(n,seed):
    rng=random.Random(seed); out=[]; keys=list(OPS)
    for i in range(n):
        op=keys[i%len(keys)]; forms,resp,outcome=OPS[op]
        out.append(Trace(rng.choice(['','念のため、','この件について、','まず、'])+rng.choice(forms),op,resp,outcome))
    rng.shuffle(out); return out

def evaluate(n,seed):
    tr=make(n,seed); t0=time.perf_counter(); m=ContrastiveDialogueSynthesizer().fit(tr); fit_ms=(time.perf_counter()-t0)*1000
    seen=[]; unseen=[]; outputs=[]
    for op,(forms,_,_) in OPS.items():
        for u in forms:
            hs=m.hypotheses(u); seen.append(any(m.outcomes[h]==op for h in hs))
        for u in UNSEEN[op]:
            hs=m.hypotheses(u); unseen.append(any(m.outcomes[h]==op for h in hs)); outputs.append((u,m.clarify(u),[m.outcomes[h] for h in hs]))
    decoys=['今日の天気を教えて','好きな色は赤です','駅前で何個買う','佐藤さんはどこ']
    decoy_accept=sum(bool(m.hypotheses(x)) for x in decoys)/len(decoys)
    clar=[m.clarify(x) for x in ['それを教えて','詳しく知りたい']]
    natural=sum(('それとも' in q or 'か、' in q) and len(q)<=80 for q in clar)/len(clar)
    t0=time.perf_counter(); reads=[]
    for _ in range(1000): m.hypotheses('カラーと所在地のどちらを聞いているの'); reads.append(m.reads)
    infer_ms=(time.perf_counter()-t0)*1000/1000
    return {'n':n,'seed':seed,'seen':sum(seen)/len(seen),'unseen':sum(unseen)/len(unseen),'decoy_accept':decoy_accept,'natural_clarification':natural,'bytes':m.serialized_bytes(),'fit_ms':fit_ms,'infer_ms':infer_ms,'max_candidates':4,'mean_reads':statistics.mean(reads),'outputs':outputs,'ambiguous_outputs':clar}

def run(output='counterfactual_dialogue_recombination_report.json'):
    rows=[]; peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    for n in [16,64,256,1024]:
        for seed in [1,7,19,31,43]: rows.append(evaluate(n,seed)); peak=max(peak,resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    scaling={}
    for n in [16,64,256,1024]:
        rr=[x for x in rows if x['n']==n]; scaling[str(n)]={k:statistics.mean(x[k] for x in rr) for k in ['seen','unseen','decoy_accept','natural_clarification','bytes','fit_ms','infer_ms','mean_reads']}
    report={'experiment':'counterfactual-dialogue-recombination-001','scaling':scaling,'peak_rss_kib':peak,'all_rows':rows,'integrated_gate':{k:False for k in ['free_dialogue','instruction_following','reading','reasoning','planning','causal_counterfactual','free_writing','long_dialogue','continual_learning']},'highschool_level_passed':False,'native_japanese_communication_passed':False,'completion':False,'verdict':'rejected: fragment recombination accepts decoys and does not synthesize natural clarification'}
    Path(output).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8'); return report

if __name__=='__main__': print(json.dumps(run(),ensure_ascii=False,indent=2))
