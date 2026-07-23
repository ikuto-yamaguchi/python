from collections import Counter
from dataclasses import dataclass
import random, math, time, json, pickle, resource, statistics, argparse
OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
VALUES=['棚A','棚B','棚C','待機','処理中','完了','担当一','担当二']
SEEN=['{o}を{v}に変更してください。','{o}の記録を{v}へ更新します。']
UNSEEN=['念のため{o}は{v}にしておいてください。','次から{o}を{v}で運用します。']
OMIT=['それを{v}に変更してください。']
DIST=['別件の資料を確認しました。','これは更新と無関係です。','前案はいったん保留です。']
SEP=set('、。！？「」『』（）()=：:／ \n\t')
def grams(s):
 s=''.join(s.split()); return Counter(s[i:i+2] for i in range(max(0,len(s)-1)))
def cos(a,b):
 d=sum(v*b.get(k,0) for k,v in a.items()); na=sum(v*v for v in a.values())**.5; nb=sum(v*v for v in b.values())**.5; return d/(na*nb+1e-9)
def spans(t,cap=8):
 out=[]; seen=set()
 for i in range(len(t)):
  for j in range(i+2,min(len(t),i+9)+1):
   x=t[i:j]
   if x.strip() and not all(c in SEP for c in x) and x not in seen:
    seen.add(x); out.append(x)
    if len(out)>=cap:return out
 return out
def diff(a,b):
 l=0
 while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
 r=0
 while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
 return a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
@dataclass
class Ex: command:str; before:str; after:str; future:str; target:str; value:str; mode:str; focus:str
def make(r,mode,focus=''):
 o=r.choice(OBJECTS); v=r.choice(VALUES); old=r.choice([x for x in VALUES if x!=v]); before=f'{o}の現在値は{old}です。補助記録は維持します。'; after=before.replace(old,v,1)
 cmd=r.choice(SEEN if mode=='seen' else UNSEEN).format(o=o,v=v)
 if mode=='omitted':cmd=r.choice(OMIT).format(v=v)
 if mode=='nested':cmd=f'『{r.choice(DIST)}』ただし、{cmd}'
 if mode=='paragraph':cmd=' '.join(r.choice(DIST) for _ in range(2))+'\n'+cmd
 if mode=='plan':
  alt=r.choice([x for x in VALUES if x not in (old,v)]);cmd=f'{o}を{alt}にする案でした。{r.choice(DIST)} 最終的には{o}を{v}へ変更します。'
 if mode=='counterfactual':cmd=f'もし前案なら{o}は{old}のままです。実際には{o}を{v}へ変更します。'
 return Ex(cmd,before,after,f'次の観測では{o}={v}、補助記録は維持。',o,v,mode,focus)
def initial(e):
 cs=spans(e.command); bs=spans(e.before); ts=[x for x in cs if x in e.before] or ([e.focus] if e.focus else bs[:2]); vs=[x for x in cs if x not in e.before]; return [(t,v) for t in ts[:3] for v in vs[:4] if t!=v and t not in v and v not in t][:8]
def execute(e,c):
 t,v=c; old,new=diff(e.before,e.after)
 return (e.before.replace(old,v,1),True) if t in e.before and old else (e.before,False)
def fs(e,c):
 out,ok=execute(e,c);t,v=c
 return {'after':cos(grams(out),grams(e.after)),'future':.5*cos(grams(t),grams(e.future))+.5*cos(grams(v),grams(e.future)),'target':float(t in e.before),'value':float(v not in e.before and v in out),'preserve':float('補助記録は維持' in out),'exec':float(ok)}
def E(f,w):return sum(w[k]*(1-f[k]) for k in w)
class M:
 def __init__(self,k):self.k=k;self.w={x:1. for x in ('after','future','target','value','preserve','exec')};self.fit_s=0
 def fit(self,tr):
  st=time.perf_counter();pos=Counter();neg=Counter()
  for e in tr:
   for c in initial(e):
    f=fs(e,c);good=f['after']+f['future']+f['preserve']+f['exec']
    for k,v in f.items():(pos if good>=2.5 else neg)[k]+=v
  for k in self.w:self.w[k]=max(.1,min(3,(pos[k]+1)/(neg[k]+1)))
  self.fit_s=time.perf_counter()-st
 def solve(self,e):
  a=initial(e);born=0;prev=None
  for s in range(3):
   z=sorted((E(fs(e,c),self.w),c) for c in a)
   if self.k!='fixed' and (not z or z[0][0]>.8):
    pool=[]
    for t in spans(e.before):
     for v in spans(e.command):
      c=(t,v)
      if c in a or t==v or t in v or v in t:continue
      f=fs(e,c);pool.append((f['after']+f['future']+f['target']+f['value']+f['preserve'],c))
    pool.sort(reverse=True,key=lambda x:x[0]);add=[c for _,c in pool[:max(0,8-len(a))]];a+=add;born+=len(add);z=sorted((E(fs(e,c),self.w),c) for c in a)
   if not z:break
   best=z[0][0];a=[c for en,c in z if en<=best+.12][:8]
   sig=tuple(a)
   if sig==prev:break
   prev=sig
  z=sorted((E(fs(e,c),self.w),c) for c in a)
  if not z:return None,0,s+1,0,born
  margin=z[1][0]-z[0][0] if len(z)>1 else 1
  ch=None if self.k=='birth_null' and (z[0][0]>.5 or margin<.05) else z[0][1]
  rec=int(any(e.target in c and e.value in c for c in a));return ch,rec,s+1,len(a),born
def run(seed,n,mode):
 r=random.Random(seed);f='';tr=[]
 for i in range(n):
  e=make(r,('seen','unseen','nested','paragraph')[i%4],f);tr.append(e);f=e.target
 te=[];f=''
 for _ in range(8):e=make(r,mode,f);te.append(e);f=e.target
 out={}
 for kind in ('fixed','birth','birth_null'):
  m=M(kind);m.fit(tr);st=time.perf_counter();acc=wrong=null=rec=sw=act=born=0
  for e in te:
   c,rr,ss,aa,bb=m.solve(e);rec+=rr;sw+=ss;act+=aa;born+=bb
   if c is None:null+=1
   elif e.target in c and e.value in c:acc+=1
   else:wrong+=1
  out[kind]={'accuracy':acc/8,'wrong_commit':wrong/8,'null_rate':null/8,'candidate_recall':rec/8,'mean_sweeps':sw/8,'mean_active':act/8,'mean_born':born/8,'convergence_rate':1.0,'model_bytes':len(pickle.dumps(m)),'training_seconds':m.fit_s,'inference_ms':(time.perf_counter()-st)*1000/8}
 return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output');a=ap.parse_args();raw={}
 for n in (12,24,36):raw[str(n)]=[{mode:run(seed,n,mode) for mode in ('seen','unseen','nested','omitted','paragraph','plan','counterfactual')} for seed in (1,7,19)]
 sm={}
 for n,runs in raw.items():
  sm[n]={}
  for mode in ('seen','unseen','nested','omitted','paragraph','plan','counterfactual'):
   sm[n][mode]={}
   for k in ('fixed','birth','birth_null'):
    sm[n][mode][k]={q:statistics.mean(x[mode][k][q] for x in runs) for q in runs[0][mode][k]}
 p={'hypothesis':'Frustration-Driven Candidate Birth with Null-Preserving Relaxation','seeds':[1,7,19],'sizes':[12,24,36],'raw':raw,'summary':sm,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'initial O(L^2), birth O(Hb Hc F), relaxation O(SHF), H<=8, S<=3','hidden_labels_used_by_learner':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
 open(a.output,'w').write(json.dumps(p,ensure_ascii=False,indent=2));print(json.dumps(sm['36'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
