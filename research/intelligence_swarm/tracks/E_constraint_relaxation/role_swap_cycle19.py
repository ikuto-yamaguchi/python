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

def substrings(text,min_len=2,max_len=8,cap=24):
    out=[]
    for i in range(len(text)):
        for j in range(i+min_len,min(len(text),i+max_len)+1):
            s=text[i:j]
            if s.strip() and not all(c in SEP for c in s):
                boundary=int(i==0 or text[i-1] in SEP)+int(j==len(text) or text[j:j+1] in SEP)
                out.append((boundary,-len(s),i,j,s))
    out.sort(reverse=True)
    seen=set(); ans=[]
    for _,_,i,j,s in out:
        if s not in seen:
            seen.add(s); ans.append((i,j,s))
        if len(ans)>=cap: break
    return ans

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

def candidate_sets(e,cap=6):
    spans=substrings(e.command)
    stable=[]; changed=[]; contextual=[]
    for i,j,s in spans:
        boundary=int(i==0 or e.command[i-1] in SEP)+int(j==len(e.command) or e.command[j:j+1] in SEP)
        stable.append((1.5*int(s in e.before)+1.0*int(s in e.future)+.25*boundary-.02*len(s),s))
        changed.append((1.5*int(s in e.after and s not in e.before)+1.0*int(s in e.future)+.25*boundary-.02*len(s),s))
        contextual.append((.7*boundary+.4*cosine(grams(s),grams(e.command))-.015*len(s),s))
    if e.focus and e.focus not in [s for _,s in stable]: stable.append((1.0,e.focus))
    def top(xs):
        xs.sort(reverse=True); out=[]
        for score,s in xs:
            if score<=0: continue
            if s not in out: out.append(s)
            if len(out)>=cap: break
        return out
    return top(stable),top(changed),top(contextual)

def execute(e,t,v):
    _,_,old,_=diff_window(e.before,e.after)
    if not old or t not in e.before: return e.before,False
    return e.before.replace(old,v,1),True

def residual(e,t,v,scope=''):
    out,ok=execute(e,t,v)
    return (round(1-cosine(grams(out),grams(e.after)),3),round(1-.5*cosine(grams(t),grams(e.future))-.5*cosine(grams(v),grams(e.future)),3),float(t not in e.before),float(v not in e.after or v in e.before),float('補助記録は維持' not in out),float(not ok),round(1-cosine(grams(scope),grams(e.command)),3) if scope else 1.0)

def energy(vec,w): return sum(a*b for a,b in zip(vec,w))

def swap_vector(e,base,other,axis):
    t,v,s=base; ot,ov,os=other; before=residual(e,t,v,s)
    after=residual(e,ot,v,s) if axis==0 else residual(e,t,ov,s) if axis==1 else residual(e,t,v,os)
    return tuple(round(a-b,2) for a,b in zip(after,before))

class Model:
    def __init__(self,kind):
        self.kind=kind; self.prototypes=[Counter(),Counter(),Counter()]
        self.w=(1.4,1.2,1.0,1.0,.8,1.2,.2); self.fit_s=0
    def fit(self,tr):
        st=time.perf_counter(); pools=[]
        for e in tr:
            a,b,c=candidate_sets(e); pools.append((e,a,b,c))
        for idx,(e,a,b,c) in enumerate(pools):
            if not a or not b or not c: continue
            bases=[(x,y,z) for x in a[:3] for y in b[:3] for z in c[:1]][:9]
            for j in range(max(0,idx-6),idx):
                _,oa,ob,oc=pools[j]
                if not oa or not ob or not oc: continue
                other=(oa[0],ob[0],oc[0])
                for base in bases[:4]:
                    for axis in range(3):
                        vec=swap_vector(e,base,other,axis)
                        if abs(sum(vec))>=.15: self.prototypes[axis][vec]+=1
        self.fit_s=time.perf_counter()-st
    def role_score(self,axis,vec):
        return 0.0 if self.kind=='separated' else math.log1p(self.prototypes[axis][vec])
    def solve(self,e):
        aa,bb,cc=candidate_sets(e)
        rec=(int(e.target in aa),int(e.value in bb),0)
        cand=[(a,b,c) for a in aa[:6] for b in bb[:6] for c in cc[:2] if a!=b and a not in b and b not in a][:48]
        rec=(rec[0],rec[1],int(any(e.target==a and e.value==b for a,b,_ in cand)))
        if not cand: return None,rec,0,0
        ref=(aa[-1],bb[-1],cc[-1]); scored=[]
        for x in cand:
            en=energy(residual(e,*x),self.w)
            if self.kind in ('swap','swap_null'):
                en-=.08*sum(self.role_score(ax,swap_vector(e,x,ref,ax)) for ax in range(3))
            scored.append((en,x))
        active=scored; prev=None; sweeps=0
        for _ in range(4):
            sweeps+=1; active.sort(key=lambda z:z[0]); best=active[0][0]
            active=[z for z in active if z[0]<=best+.08][:8]
            sig=tuple(x for _,x in active)
            if sig==prev: break
            prev=sig
        active.sort(key=lambda z:z[0]); best,x=active[0]
        margin=active[1][0]-best if len(active)>1 else 1.0
        if self.kind=='swap_null' and (best>=energy((1,1,1,1,0,1,1),self.w)-.05 or margin<.04): x=None
        return x,rec,sweeps,len(active)

def run(seed,n,mode):
    r=random.Random(seed); tr=[]; focus=''
    for i in range(n):
        e=make(r,('seen','unseen','nested','paragraph')[i%4],focus); tr.append(e); focus=e.target
    te=[]; focus=''
    for _ in range(3):
        e=make(r,mode,focus); te.append(e); focus=e.target
    out={}
    for kind in ('joint','separated','swap','swap_null'):
        m=Model(kind); m.fit(tr); st=time.perf_counter(); acc=wrong=null=orec=vrec=prec=sw=act=0
        for e in te:
            x,recs,ss,aa=m.solve(e); orec+=recs[0];vrec+=recs[1];prec+=recs[2];sw+=ss;act+=aa
            if x is None:null+=1
            elif x[0]==e.target and x[1]==e.value:acc+=1
            else:wrong+=1
        out[kind]={'accuracy':acc/len(te),'wrong_commit':wrong/len(te),'null_rate':null/len(te),'object_recall':orec/len(te),'value_recall':vrec/len(te),'pair_recall':prec/len(te),'mean_sweeps':sw/len(te),'mean_active':act/len(te),'prototype_count':sum(len(p) for p in m.prototypes),'model_bytes':len(pickle.dumps(m)),'training_seconds':m.fit_s,'inference_ms':(time.perf_counter()-st)*1000/len(te)}
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); a=ap.parse_args()
    modes=('seen','unseen','nested','omitted','paragraph','plan','counterfactual')
    raw={'12':[{mode:run(seed,12,mode) for mode in modes} for seed in (1,7,19)]}
    sm={'12':{}}
    for mode in modes:
        sm['12'][mode]={}
        for k in ('joint','separated','swap','swap_null'):
            sm['12'][mode][k]={q:statistics.mean(x[mode][k][q] for x in raw['12']) for q in raw['12'][0][mode][k]}
    payload={'hypothesis':'Role-Separated Residual Transport with Counterfactual Factor Swaps','seeds':[1,7,19],'sizes':[12],'raw':raw,'summary':sm,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'proposal O(L^2), swap fit O(NWHF), relaxation O(SHF), H<=48,S<=4','hidden_labels_used_by_learner':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    open(a.output,'w',encoding='utf-8').write(json.dumps(payload,ensure_ascii=False,indent=2))
    print(json.dumps(sm['12'],ensure_ascii=False,indent=2))
if __name__=='__main__': main()
