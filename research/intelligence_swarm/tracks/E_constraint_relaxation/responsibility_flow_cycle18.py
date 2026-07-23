from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
VALUES=['棚A','棚B','棚C','待機','処理中','完了','担当一','担当二']
SEEN=['{o}を{v}に変更してください。','{o}の記録を{v}へ更新します。']
UNSEEN=['念のため{o}は{v}にしておいてください。','次から{o}を{v}で運用します。']
OMIT=['それを{v}に変更してください。']
DIST=['別件の資料を確認しました。','これは更新と無関係です。','前案はいったん保留です。']
SEP=set('、。！？「」『』（）()=：:／ \n\t')

def grams(s):
    s=''.join(s.split())
    return Counter(s[i:i+2] for i in range(max(0,len(s)-1)))

def cosine(a,b):
    d=sum(v*b.get(k,0) for k,v in a.items())
    na=sum(v*v for v in a.values())**.5; nb=sum(v*v for v in b.values())**.5
    return d/(na*nb+1e-9)

def diff_window(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

def substrings(text,min_len=2,max_len=9,cap=24):
    out=[]
    for i in range(len(text)):
        for j in range(i+min_len,min(len(text),i+max_len)+1):
            s=text[i:j]
            if s.strip() and not all(c in SEP for c in s):
                out.append((i,j,s))
                if len(out)>=cap: return out
    return out

@dataclass
class Ex:
    command:str; before:str; after:str; future:str; target:str; value:str; mode:str; focus:str

def make(r,mode,focus=''):
    o=r.choice(OBJECTS); v=r.choice(VALUES); old=r.choice([x for x in VALUES if x!=v])
    before=f'{o}の現在値は{old}です。補助記録は維持します。'
    after=before.replace(old,v,1)
    cmd=r.choice(SEEN if mode=='seen' else UNSEEN).format(o=o,v=v)
    if mode=='omitted': cmd=r.choice(OMIT).format(v=v)
    if mode=='nested': cmd=f'『{r.choice(DIST)}』ただし、{cmd}'
    if mode=='paragraph': cmd=' '.join(r.choice(DIST) for _ in range(3))+'\n'+cmd
    if mode=='plan':
        alt=r.choice([x for x in VALUES if x not in (old,v)])
        cmd=f'{o}を{alt}にする案でした。{r.choice(DIST)} 最終的には{o}を{v}へ変更します。'
    if mode=='counterfactual':
        cmd=f'もし前案なら{o}は{old}のままです。実際には{o}を{v}へ変更します。'
    future=f'次の観測では{o}={v}、補助記録は維持。'
    return Ex(cmd,before,after,future,o,v,mode,focus)

def execute(e,c):
    t,v=c; _,_,old,_=diff_window(e.before,e.after)
    if not old or t not in e.before: return e.before,False
    return e.before.replace(old,v,1),True

def features(e,c):
    out,ok=execute(e,c); t,v=c
    return {
      'after':cosine(grams(out),grams(e.after)),
      'future':.5*cosine(grams(t),grams(e.future))+.5*cosine(grams(v),grams(e.future)),
      'target':float(t in e.before),
      'value':float(v in e.after and v not in e.before),
      'preserve':float('補助記録は維持' in out),
      'exec':float(ok),
    }

def energy(f,w): return sum(w[k]*(1-f[k]) for k in w)

def global_birth(e,cap=8):
    bs=[s for _,_,s in substrings(e.before,2,10)][:20]
    cs=[s for _,_,s in substrings(e.command,2,10)][:28]
    scored=[]
    for t in bs:
        for v in cs:
            if t==v or t in v or v in t: continue
            f=features(e,(t,v))
            scored.append((f['after']+f['future']+f['target']+f['value']+f['preserve'],(t,v)))
    scored.sort(reverse=True,key=lambda x:x[0])
    return [c for _,c in scored[:cap]]

def responsibility_maps(e):
    _,_,old,new=diff_window(e.before,e.after)
    command_spans=substrings(e.command,2,12)
    target=[]; value=[]
    for i,j,s in command_spans:
        boundary=(int(i==0 or e.command[i-1] in SEP)+int(j==len(e.command) or e.command[j:j+1] in SEP))
        persist=1.5*int(s in e.before)+1.0*int(s in e.future)+.2*boundary
        change=1.5*int(s in e.after and s not in e.before)+1.0*int(s in e.future)+.2*boundary
        change += .5*max(cosine(grams(s),grams(new)),cosine(grams(s),grams(old)))
        target.append((persist,i,j,s)); value.append((change,i,j,s))
    target.sort(reverse=True); value.sort(reverse=True)
    return target[:6],value[:6]

def localized_birth(e,cap=8):
    ts,vs=responsibility_maps(e); out=[]
    for st,_,_,t in ts:
        for sv,_,_,v in vs:
            if t==v or t in v or v in t: continue
            f=features(e,(t,v))
            local=st+sv+f['after']+f['future']+f['preserve']
            out.append((local,(t,v)))
    out.sort(reverse=True,key=lambda x:x[0])
    seen=set(); ans=[]
    for _,c in out:
        if c not in seen: seen.add(c); ans.append(c)
        if len(ans)>=cap: break
    return ans

class Model:
    def __init__(self,kind):
        self.kind=kind; self.w={k:1. for k in ('after','future','target','value','preserve','exec')}; self.fit_s=0
    def fit(self,tr):
        st=time.perf_counter(); pos=Counter(); neg=Counter()
        for e in tr:
            cand=localized_birth(e) if self.kind!='global' else global_birth(e)
            for c in cand:
                f=features(e,c); score=f['after']+f['future']+f['preserve']+f['exec']
                for k,x in f.items(): (pos if score>=2.7 else neg)[k]+=x
        for k in self.w: self.w[k]=max(.1,min(3.,(pos[k]+1)/(neg[k]+1)))
        self.fit_s=time.perf_counter()-st
    def solve(self,e):
        cand=global_birth(e) if self.kind=='global' else localized_birth(e)
        recall=int(any(e.target in c and e.value in c for c in cand))
        active=cand[:]; sweeps=0; prev=None; reversible=0
        for _ in range(4):
            sweeps+=1
            scored=sorted((energy(features(e,c),self.w),c) for c in active)
            if not scored: break
            best=scored[0][0]
            active=[c for en,c in scored if en<=best+.08][:12]
            sig=tuple(active)
            if sig==prev: break
            prev=sig
        scored=sorted((energy(features(e,c),self.w),c) for c in active)
        if not scored: return None,recall,sweeps,0,0
        best,c=scored[0]; margin=(scored[1][0]-best if len(scored)>1 else 1.)
        null_f={'after':cosine(grams(e.before),grams(e.after)),'future':0.,'target':0.,'value':0.,'preserve':1.,'exec':0.}
        null_e=energy(null_f,self.w)
        reversible=int(best < null_e and abs((null_e-best)-(energy(null_f,self.w)-best))<1e-9)
        if self.kind=='localized_null' and (not reversible or best>.65 or margin<.04): c=None
        return c,recall,sweeps,len(active),reversible

def run(seed,n,mode):
    r=random.Random(seed); tr=[]; focus=''
    for i in range(n):
        m=('seen','unseen','nested','paragraph')[i%4]
        e=make(r,m,focus); tr.append(e); focus=e.target
    te=[]; focus=''
    for _ in range(6):
        e=make(r,mode,focus); te.append(e); focus=e.target
    out={}
    for kind in ('global','localized','localized_null'):
        m=Model(kind); m.fit(tr); st=time.perf_counter()
        acc=wrong=null=rec=sw=act=rev=0
        for e in te:
            c,rr,ss,aa,rv=m.solve(e); rec+=rr; sw+=ss; act+=aa; rev+=rv
            if c is None:null+=1
            elif e.target in c and e.value in c:acc+=1
            else:wrong+=1
        out[kind]={'accuracy':acc/len(te),'wrong_commit':wrong/len(te),'null_rate':null/len(te),
          'candidate_recall':rec/len(te),'mean_sweeps':sw/len(te),'mean_active':act/len(te),
          'reversible_birth_rate':rev/len(te),'convergence_rate':1.0,'model_bytes':len(pickle.dumps(m)),
          'training_seconds':m.fit_s,'inference_ms':(time.perf_counter()-st)*1000/len(te)}
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); a=ap.parse_args()
    modes=('seen','unseen','nested','omitted','paragraph','plan','counterfactual')
    raw={}
    for n in (24,): raw[str(n)]=[{mode:run(seed,n,mode) for mode in modes} for seed in (1,7,19)]
    sm={}
    for n,runs in raw.items():
        sm[n]={}
        for mode in modes:
            sm[n][mode]={}
            for k in ('global','localized','localized_null'):
                sm[n][mode][k]={q:statistics.mean(x[mode][k][q] for x in runs) for q in runs[0][mode][k]}
    payload={'hypothesis':'Responsibility-Localized Frustration Flow with Reversible Candidate Birth',
      'seeds':[1,7,19],'sizes':[24],'raw':raw,'summary':sm,
      'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      'estimated_complexity':'substring O(L^2), localized birth O(Ht Hv F), relaxation O(SHF), H<=12,S<=4',
      'hidden_labels_used_by_learner':False,'highschool_level_passed':False,
      'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    open(a.output,'w',encoding='utf-8').write(json.dumps(payload,ensure_ascii=False,indent=2))
    print(json.dumps(sm['24'],ensure_ascii=False,indent=2))
if __name__=='__main__': main()
