from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
VALUES=['棚A','棚B','棚C','待機','処理中','完了','担当一','担当二']
SEEN=['{o}を{v}に変更してください。','{o}について今後は{v}として扱います。']
HELD=['念のため{o}は{v}にしておいてください。','次から{o}を{v}で運用します。']
OMIT=['それを{v}に変更してください。','その対象は今後{v}です。']
NOISE=['別件を確認しました。','昨日の案は保留です。','これは更新とは無関係です。']

@dataclass
class Ex:
    text:str; before:str; after:str; future:str; obj:str; value:str; focus:str

def grams(s):
    s=''.join(s.split()); return Counter(s[i:i+n] for n in (1,2,3) for i in range(max(0,len(s)-n+1)))
def cos(a,b):
    d=sum(v*b.get(k,0) for k,v in a.items()); na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values())); return d/(na*nb+1e-9)
def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def spans(s,cap=24):
    out=[]
    for i in range(len(s)):
        for j in range(i+2,min(len(s),i+13)+1):
            x=s[i:j]
            if not x.strip(): continue
            out.append((len(set(x))/len(x),len(x),x))
    out.sort(reverse=True); ans=[]; seen=set()
    for _,_,x in out:
        if x not in seen: seen.add(x); ans.append(x)
        if len(ans)>=cap: break
    return ans

def make(rng,mode,focus=''):
    o=rng.choice(OBJECTS); surf=ALIASES[o] if mode=='rename' else o
    v=rng.choice(VALUES); old=rng.choice([x for x in VALUES if x!=v])
    before=f'{surf}の現在値は{old}です。補助記録は維持。'; after=before.replace(old,v,1)
    forms=OMIT if mode=='omitted' else (HELD if mode in ('held','rename','nested','paragraph','plan') else SEEN)
    text=rng.choice(forms).format(o=surf,v=v)
    if mode=='nested': text=f'「{rng.choice(NOISE)}」ただし、'+text
    if mode=='paragraph': text=' '.join(rng.choice(NOISE) for _ in range(3))+'\n'+text
    if mode=='plan':
        alt=rng.choice([x for x in VALUES if x!=v]); text=f'{surf}を{alt}にする案でした。{rng.choice(NOISE)} 最終的には'+text
    future=f'次回は{surf}={v}、補助記録は維持。'
    return Ex(text,before,after,future,surf,v,focus)

def candidates(ex,cap=32):
    ts=spans(ex.text,24); overlap=[x for x in ts if x in ex.before]
    if not overlap and ex.focus: overlap=[ex.focus]
    vals=[x for x in ts if x not in ex.before]
    out=[]
    for a in overlap[:8]:
        for b in vals[:12]:
            if a==b or a in b or b in a: continue
            out.append((a,b))
            if len(out)>=cap: return out
    return out

def outcome(ex,c):
    a,b=c; old,new=diff(ex.before,ex.after)
    if a not in ex.before: return ex.before+'[null]', '予測不能'
    pred=ex.before.replace(old,b,1) if old else ex.before
    fut=f'次回は{a}={b}、補助記録は維持。'
    return pred,fut

def err(ex,c):
    p,f=outcome(ex,c)
    return 1-cos(grams(p),grams(ex.after)),1-cos(grams(f),grams(ex.future))

class Model:
    def __init__(self,kind): self.kind=kind; self.states=[]; self.train_s=0
    def fit(self,seq):
        t=time.perf_counter(); buckets=defaultdict(list)
        for i,ex in enumerate(seq):
            for c in candidates(ex):
                e0,e1=err(ex,c); sig=(round(e0,1),round(e1,1),len(c[0])//2,len(c[1])//2)
                buckets[sig].append((i,ex,c,e0,e1))
        scored=[]
        for sig,items in buckets.items():
            horizons=[]; good=0
            for i,ex,c,e0,e1 in items:
                good+=int(e0<.15 and e1<.15)
                horizons += [j-i for j,_,_,_,_ in items if 1<=j-i<=12]
            recurrence=len(set(horizons)); purity=good/max(1,len(items))
            if self.kind=='immediate': score=purity*math.log1p(len(items))
            elif self.kind=='delayed': score=purity*math.log1p(len(items))+.35*recurrence
            else: score=random.Random(hash(sig)&0xffff).random()
            scored.append((score,sig,Counter(c for _,_,c,_,_ in items)))
        scored.sort(reverse=True); self.states=scored[:12]; self.train_s=time.perf_counter()-t
    def solve(self,ex):
        cs=candidates(ex); recall=int((ex.obj,ex.value) in cs)
        if not cs:return None,recall,0
        ranked=[]
        for c in cs:
            e0,e1=err(ex,c); sig=(round(e0,1),round(e1,1),len(c[0])//2,len(c[1])//2)
            match=max((s for s,st,_ in self.states if st==sig),default=0)
            ranked.append((match-e0-e1,c))
        ranked.sort(reverse=True)
        if len(ranked)>1 and ranked[0][0]-ranked[1][0]<.08:return None,recall,len(cs)
        return ranked[0][1],recall,len(cs)

def run(seed,n,mode):
    rng=random.Random(seed); focus=''; train=[]
    for i in range(n):
        m=('seen','held','rename')[i%3]; x=make(rng,m,focus); train.append(x); focus=x.obj
    test=[]; focus=''
    for _ in range(24): x=make(rng,mode,focus); test.append(x); focus=x.obj
    out={}
    for kind in ('random','immediate','delayed'):
        m=Model(kind); m.fit(train); t=time.perf_counter(); acc=wrong=null=rec=cnum=0
        for x in test:
            ch,r,k=m.solve(x); rec+=r; cnum+=k
            if ch is None:null+=1
            elif ch==(x.obj,x.value):acc+=1
            else:wrong+=1
        out[kind]={'accuracy':acc/24,'wrong_commit':wrong/24,'null_rate':null/24,'candidate_recall':rec/24,'mean_candidates':cnum/24,'states':len(m.states),'model_bytes':len(pickle.dumps(m)),'training_seconds':m.train_s,'inference_ms':(time.perf_counter()-t)*1000/24}
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',default='results_cycle_017.json'); a=ap.parse_args()
    raw={}
    modes=('seen','held','rename','nested','omitted','paragraph','plan')
    for n in (24,48,96): raw[str(n)]=[{m:run(seed,n,m) for m in modes} for seed in (1,7,19)]
    summary={}
    for n,runs in raw.items():
        summary[n]={m:{k:{q:statistics.mean(z[m][k][q] for z in runs) for q in z0[m][k]} for k in ('random','immediate','delayed')} for m in modes for z0 in [runs[0]]}
    payload={'hypothesis':'Delayed Prediction-Error Recurrence States with Horizon-Separated Credit','seeds':[1,7,19],'sizes':[24,48,96],'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'complexity':'proposal O(L^2), fit O(NH+R^2), inference O(SH), H<=32,S<=12','highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    open(a.output,'w',encoding='utf8').write(json.dumps(payload,ensure_ascii=False,indent=2)); print(json.dumps(summary['96'],ensure_ascii=False,indent=2))
if __name__=='__main__': main()
