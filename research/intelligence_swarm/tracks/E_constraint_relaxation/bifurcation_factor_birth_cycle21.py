from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
import argparse,json,math,pickle,random,resource,statistics,time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
VALUES=['棚A','棚B','棚C','待機','処理中','完了','担当一','担当二']
SEEN=['{o}を{v}に変更してください。','{o}の記録を{v}へ更新します。']
UNSEEN=['念のため{o}は{v}にしておいてください。','次から{o}を{v}で運用します。']
DIST=['別件の資料を確認しました。','これは更新と無関係です。','前案はいったん保留です。']
SEP=set('、。！？「」『』（）()=：:／ \n\t')

def grams(s,n=2):
 s=''.join(s.split()); return Counter(s[i:i+n] for i in range(max(0,len(s)-n+1)))
def cosine(a,b):
 d=sum(v*b.get(k,0) for k,v in a.items());na=sum(v*v for v in a.values())**.5;nb=sum(v*v for v in b.values())**.5
 return d/(na*nb+1e-9)
def diff_window(a,b):
 l=0
 while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
 r=0
 while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
 return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def spans(text,max_len=14):
 out=[]
 for i in range(len(text)):
  for j in range(i+1,min(len(text),i+max_len)+1):
   s=text[i:j]
   if not s.strip() or all(c in SEP for c in s):continue
   boundary=int(i==0 or text[i-1] in SEP)+int(j==len(text) or text[j:j+1] in SEP)
   out.append((boundary,-abs(len(s)-4),i,j,s))
 out.sort(reverse=True);ans=[];seen=set()
 for _,_,i,j,s in out:
  if s not in seen:seen.add(s);ans.append((i,j,s))
  if len(ans)>=64:break
 return ans

@dataclass
class Ex:
 command:str;before:str;after:str;future:str;target:str;value:str;mode:str;focus:str

def make(r,mode,focus=''):
 o=r.choice(OBJECTS);v=r.choice(VALUES);old=r.choice([x for x in VALUES if x!=v])
 before=f'{o}の現在値は{old}です。補助記録は維持します。';after=before.replace(old,v,1)
 cmd=r.choice(SEEN if mode=='seen' else UNSEEN).format(o=o,v=v)
 if mode=='omitted':cmd=f'それを{v}に変更してください。'
 if mode=='nested':cmd=f'『{r.choice(DIST)}』ただし、{cmd}'
 if mode=='paragraph':cmd=' '.join(r.choice(DIST) for _ in range(3))+'\n'+cmd
 if mode=='plan':
  alt=r.choice([x for x in VALUES if x not in (old,v)]);cmd=f'{o}を{alt}にする案でした。{r.choice(DIST)} 最終的には{o}を{v}へ変更します。'
 if mode=='counterfactual':cmd=f'もし前案なら{o}は{old}のままです。実際には{o}を{v}へ変更します。'
 future=f'次の観測では{o}={v}、補助記録は維持。'
 return Ex(cmd,before,after,future,o,v,mode,focus)

def execute(e,t,v):
 _,_,old,_=diff_window(e.before,e.after)
 if not old or t not in e.before:return e.before,False
 return e.before.replace(old,v,1),True

def residual(e,t,v):
 out,ok=execute(e,t,v)
 return (1-cosine(grams(out),grams(e.after)),1-cosine(grams(t+'='+v),grams(e.future)),
         float(t not in e.before),float(v not in e.after or v in e.before),
         float('補助記録は維持' not in out),float(not ok))
W=(1.4,1.2,1.0,1.0,.8,1.2)
def energy(e,t,v):return sum(a*b for a,b in zip(residual(e,t,v),W))

def base_candidates(e,cap=8):
 ss=spans(e.command)
 obj=[];val=[]
 for i,j,s in ss:
  b=int(i==0 or e.command[i-1] in SEP)+int(j==len(e.command) or e.command[j:j+1] in SEP)
  obj.append((1.6*int(s in e.before)+1.0*int(s in e.future)+.1*b-.02*len(s),s))
  val.append((1.5*int(s in e.after and s not in e.before)+.9*int(s in e.future)+.1*b-.02*len(s),s))
 if e.focus:obj.append((.7,e.focus))
 def top(z):
  z.sort(reverse=True);o=[]
  for sc,s in z:
   if sc>0 and s not in o:o.append(s)
   if len(o)>=cap:break
  return o
 return top(obj),top(val)

def local_segments(text,center,radius=5):
 out=[]
 lo=max(0,center-radius);hi=min(len(text),center+radius+1)
 for i in range(lo,hi):
  for j in range(i+1,min(hi,i+9)+1):
   s=text[i:j]
   if s.strip() and not all(c in SEP for c in s):out.append(s)
 return list(dict.fromkeys(out))

def bifurcation_birth(e):
 ss=spans(e.command)
 if not ss:return [],[]
 obj_score=[];val_score=[]
 for i,j,s in ss:
  free=.06*len(s)-.12*(int(i==0 or e.command[i-1] in SEP)+int(j==len(e.command) or e.command[j:j+1] in SEP))
  po=free + 1.2*(1-int(s in e.before)) + .8*(1-int(s in e.future))
  pv=free + 1.1*(1-int(s in e.after and s not in e.before)) + .7*(1-int(s in e.future))
  obj_score.append((i,j,s,free,po));val_score.append((i,j,s,free,pv))
 def critical(rows):
  last=None;birth=[]
  for lam in (0,.1,.2,.35,.5,.7,1.0):
   ranked=sorted((((1-lam)*fr+lam*nu,i,j,s) for i,j,s,fr,nu in rows));best=ranked[0];sig=(best[1],best[2])
   if last is not None and sig!=last:
    birth.extend(local_segments(e.command,best[1]));birth.extend(local_segments(e.command,best[2]))
   last=sig
  birth.extend(r[3] for r in sorted(((nu,i,j,s) for i,j,s,fr,nu in rows))[:6])
  return list(dict.fromkeys(birth))[:12]
 return critical(obj_score),critical(val_score)

class Model:
 def __init__(self,kind):self.kind=kind;self.proto=Counter();self.fit_s=0
 def fit(self,tr):
  st=time.perf_counter()
  if self.kind in ('bifurcation','bifurcation_null'):
   for e in tr:
    aa,bb=bifurcation_birth(e)
    for t in aa[:6]:
     for v in bb[:6]:self.proto[tuple(round(x,1) for x in residual(e,t,v))]+=1
  self.fit_s=time.perf_counter()-st
 def solve(self,e):
  aa,bb=base_candidates(e) if self.kind=='base' else bifurcation_birth(e)
  ore=int(e.target in aa);vre=int(e.value in bb)
  cand=[(t,v) for t in aa[:8] for v in bb[:8] if t!=v and t not in v and v not in t][:48]
  pre=int((e.target,e.value) in cand)
  if not cand:return None,(ore,vre,pre),0,0,0
  scored=[]
  for t,v in cand:
   en=energy(e,t,v)
   if self.kind!='base':en-=.03*math.log1p(self.proto[tuple(round(x,1) for x in residual(e,t,v))])
   scored.append([en,t,v])
  active=scored;sweeps=0;prev=None
  for _ in range(4):
   sweeps+=1;active.sort();best=active[0][0];nxt=[z for z in active if z[0]<=best+.06][:8]
   sig=tuple((x[1],x[2]) for x in nxt)
   if sig==prev:break
   prev=sig;active=nxt
  active.sort();best,t,v=active[0];margin=active[1][0]-best if len(active)>1 else 1;x=(t,v)
  if self.kind=='bifurcation_null' and (best>1.7 or margin<.04):x=None
  return x,(ore,vre,pre),sweeps,len(active),len(cand)

def run(seed,n,mode):
 r=random.Random(seed);tr=[];focus=''
 for i in range(n):
  e=make(r,('seen','unseen','nested','paragraph')[i%4],focus);tr.append(e);focus=e.target
 te=[];focus=''
 for _ in range(12):
  e=make(r,mode,focus);te.append(e);focus=e.target
 out={}
 for kind in ('base','bifurcation','bifurcation_null'):
  m=Model(kind);m.fit(tr);st=time.perf_counter();acc=wrong=null=ore=vre=pre=sw=act=cc=0
  for e in te:
   x,rec,s,a,c=m.solve(e);ore+=rec[0];vre+=rec[1];pre+=rec[2];sw+=s;act+=a;cc+=c
   if x is None:null+=1
   elif x==(e.target,e.value):acc+=1
   else:wrong+=1
  out[kind]={'accuracy':acc/len(te),'wrong_commit':wrong/len(te),'null_rate':null/len(te),'object_recall':ore/len(te),'value_recall':vre/len(te),'pair_recall':pre/len(te),'mean_sweeps':sw/len(te),'mean_active':act/len(te),'mean_candidates':cc/len(te),'prototype_count':len(m.proto),'model_bytes':len(pickle.dumps(m)),'training_seconds':m.fit_s,'inference_ms':(time.perf_counter()-st)*1000/len(te)}
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args()
 modes=('seen','unseen','nested','omitted','paragraph','plan','counterfactual')
 raw={'48':[{mode:run(seed,48,mode) for mode in modes} for seed in (1,7,19)]};sm={'48':{}}
 for mode in modes:
  sm['48'][mode]={}
  for k in ('base','bifurcation','bifurcation_null'):
   sm['48'][mode][k]={q:statistics.mean(x[mode][k][q] for x in raw['48']) for q in raw['48'][0][mode][k]}
 payload={'hypothesis':'Bifurcation-Guided Open-Set Factor Birth from Basin-Splitting Residuals','seeds':[1,7,19],'sizes':[48],'raw':raw,'summary':sm,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'proposal O(L^2), homotopy O(JH), local birth O(JR^2), relaxation O(SH), J=7,H<=48,S<=4','hidden_labels_used_by_learner':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
 open(a.output,'w',encoding='utf-8').write(json.dumps(payload,ensure_ascii=False,indent=2));print(json.dumps(sm['48'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
