from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
VALUES=['棚A','棚B','棚C','待機','処理中','完了','担当一','担当二']
SEP=set('、。！？「」『』（）()=：:／ \n\t')
DIST=['別件の資料を確認しました。','これは更新と無関係です。','前案はいったん保留です。']

ENV_FORMS={
 'base':('{o}の現在値は{old}です。補助記録は維持します。','{o}を{v}に変更してください。','次の観測では{o}={v}、補助記録は維持。'),
 'rename':('{o}の現在値は{old}です。補助記録は維持します。','{o}の記録を{v}へ更新します。','次の観測では{o}={v}、補助記録は維持。'),
 'order':('{o}の現在値は{old}です。補助記録は維持します。','{v}へ変更してください。対象は{o}です。','更新後も{o}は{v}です。補助記録は維持。'),
 'state':('{o}：値={old}／補助=維持。','対象{o}は次から{v}で運用します。','次回観測：{o}／値={v}／補助=維持。'),
 'unknown':('記録対象{o}［現値:{old}］。付帯情報保持。','これ以降、{v}を{o}へ適用。','追跡結果：{o}は{v}。付帯情報保持。'),
}

def grams(s,n=2):
 s=''.join(s.split());return Counter(s[i:i+n] for i in range(max(0,len(s)-n+1)))
def cosine(a,b):
 d=sum(v*b.get(k,0) for k,v in a.items());na=sum(v*v for v in a.values())**.5;nb=sum(v*v for v in b.values())**.5
 return d/(na*nb+1e-9)
def diff_window(a,b):
 l=0
 while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
 r=0
 while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
 return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def spans(text,max_len=14,cap=96):
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
  if len(ans)>=cap:break
 return ans

@dataclass
class Ex:
 command:str;before:str;after:str;future:str;target:str;value:str;mode:str;focus:str;env:str

def make_bundle(r,mode='base',focus=''):
 o=r.choice(OBJECTS);v=r.choice(VALUES);old=r.choice([x for x in VALUES if x!=v])
 bundle=[]
 envs=('unknown',) if mode=='unseen' else ('base','rename','order','state')
 for env in envs:
  surf=ALIASES[o] if env=='rename' else o
  bf,cf,ff=ENV_FORMS[env]
  before=bf.format(o=surf,old=old);after=bf.format(o=surf,old=v);cmd=cf.format(o=surf,v=v);future=ff.format(o=surf,v=v)
  if mode=='omitted':cmd=f'それを{v}に変更してください。'
  if mode=='nested':cmd=f'『{r.choice(DIST)}』ただし、{cmd}'
  if mode=='paragraph':cmd=' '.join(r.choice(DIST) for _ in range(3))+'\n'+cmd
  if mode=='plan':
   alt=r.choice([x for x in VALUES if x not in (old,v)]);cmd=f'{surf}を{alt}にする案でした。{r.choice(DIST)} 最終的には'+cmd
  if mode=='counterfactual':cmd=f'もし前案なら{surf}は{old}のままです。実際には'+cmd
  if mode=='ambiguous':cmd=f'{surf}を{old}のままにする案と{v}へ変える案があります。最終決定は'+cmd
  bundle.append(Ex(cmd,before,after,future,surf,v,mode,focus,env))
 return bundle

def execute(e,t,v):
 _,_,old,_=diff_window(e.before,e.after)
 if not old or t not in e.before:return e.before,False
 return e.before.replace(old,v,1),True

def response(e,t,v):
 out,ok=execute(e,t,v)
 base={
  'after':1-cosine(grams(out),grams(e.after)),
  'future':1-cosine(grams(t+'='+v),grams(e.future)),
  'non_target':float('補助' not in out or '維持' not in out),
  'execution':float(not ok or v not in e.after or v in e.before),
 }
 occ_t=t[:-1] if len(t)>1 else ''
 occ_v=v[:-1] if len(v)>1 else ''
 out2,ok2=execute(e,occ_t,occ_v)
 pert={
  'd_after':(1-cosine(grams(out2),grams(e.after)))-base['after'],
  'd_future':(1-cosine(grams(occ_t+'='+occ_v),grams(e.future)))-base['future'],
  'd_non_target':float('補助' not in out2 or '維持' not in out2)-base['non_target'],
  'd_execution':float(not ok2 or occ_v not in e.after)-base['execution'],
 }
 return tuple(round(base[k],2) for k in ('after','future','non_target','execution'))+tuple(round(pert[k],2) for k in ('d_after','d_future','d_non_target','d_execution'))

def base_candidates(e,cap=8):
 obj=[];val=[]
 for i,j,s in spans(e.command):
  b=int(i==0 or e.command[i-1] in SEP)+int(j==len(e.command) or e.command[j:j+1] in SEP)
  obj.append((1.5*int(s in e.before)+.8*int(s in e.future)+.1*b-.02*len(s),s))
  val.append((1.4*int(s in e.after and s not in e.before)+.8*int(s in e.future)+.1*b-.02*len(s),s))
 if e.focus:obj.append((.5,e.focus))
 def top(z):
  z.sort(reverse=True);o=[]
  for sc,s in z:
   if sc>0 and s not in o:o.append(s)
   if len(o)>=cap:break
  return o
 return top(obj),top(val)

class Model:
 def __init__(self,kind):self.kind=kind;self.proto=Counter();self.fit_s=0
 def fit(self,bundles):
  st=time.perf_counter()
  if self.kind in ('invariant','invariant_null'):
   bysig=defaultdict(set);counts=Counter()
   for bundle in bundles:
    for e in bundle:
     aa,bb=base_candidates(e,6)
     for t in aa:
      for v in bb:
       if t==v or t in v or v in t:continue
       sig=response(e,t,v);bysig[sig].add(e.env);counts[sig]+=1
   for sig,envs in bysig.items():
    if len(envs)>=3 and counts[sig]>=4:self.proto[sig]=counts[sig]
  self.fit_s=time.perf_counter()-st
 def solve(self,e):
  aa,bb=base_candidates(e);ore=int(e.target in aa);vre=int(e.value in bb)
  cand=[(t,v) for t in aa[:8] for v in bb[:8] if t!=v and t not in v and v not in t][:48]
  pre=int((e.target,e.value) in cand)
  if not cand:return None,(ore,vre,pre),0,0,0,0
  scored=[]
  for t,v in cand:
   sig=response(e,t,v)
   en=1.4*sig[0]+1.2*sig[1]+.8*sig[2]+1.2*sig[3]
   if self.kind.startswith('invariant'):
    en-=.08*math.log1p(self.proto.get(sig,0))
    if sig not in self.proto:en+=.2
   scored.append([en,t,v,sig])
  active=scored;prev=None;sweeps=0
  for _ in range(5):
   sweeps+=1;active.sort();best=active[0][0];nxt=[z for z in active if z[0]<=best+.04][:8]
   sigx=tuple((x[1],x[2]) for x in nxt)
   if sigx==prev:break
   prev=sigx;active=nxt
  active.sort();best,t,v,sig=active[0];margin=active[1][0]-best if len(active)>1 else 1
  x=(t,v)
  if self.kind=='invariant_null' and (best>1.45 or margin<.035 or sig not in self.proto):x=None
  return x,(ore,vre,pre),sweeps,len(active),len(cand),len(self.proto)

def run(seed,n,mode):
 r=random.Random(seed);bundles=[];focus=''
 for i in range(n):
  b=make_bundle(r,('base','nested','paragraph','counterfactual')[i%4],focus);bundles.append(b);focus=b[0].target
 te=[];focus=''
 for _ in range(12):
  b=make_bundle(r,mode,focus);e=r.choice(b);te.append(e);focus=e.target
 out={}
 for kind in ('base','invariant','invariant_null'):
  m=Model(kind);m.fit(bundles);st=time.perf_counter();acc=wrong=null=ore=vre=pre=sw=act=cc=0
  for e in te:
   x,rec,s,a,c,p=m.solve(e);ore+=rec[0];vre+=rec[1];pre+=rec[2];sw+=s;act+=a;cc+=c
   if x is None:null+=1
   elif x==(e.target,e.value):acc+=1
   else:wrong+=1
  out[kind]={'accuracy':acc/len(te),'wrong_commit':wrong/len(te),'null_rate':null/len(te),'object_recall':ore/len(te),'value_recall':vre/len(te),'pair_recall':pre/len(te),'mean_sweeps':sw/len(te),'mean_active':act/len(te),'mean_candidates':cc/len(te),'prototype_count':len(m.proto),'model_bytes':len(pickle.dumps(m)),'training_seconds':m.fit_s,'inference_ms':(time.perf_counter()-st)*1000/len(te)}
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();modes=('base','unseen','ambiguous','nested','omitted','paragraph','plan','counterfactual')
 raw={'48':[{mode:run(seed,48,mode) for mode in modes} for seed in (1,7,19)]};sm={'48':{}}
 for mode in modes:
  sm['48'][mode]={}
  for k in ('base','invariant','invariant_null'):
   sm['48'][mode][k]={q:statistics.mean(x[mode][k][q] for x in raw['48']) for q in raw['48'][0][mode][k]}
 payload={'hypothesis':'Environment-Decoupled Factor Birth from Intervention-Invariant Energy Responses','seeds':[1,7,19],'sizes':[48],'raw':raw,'summary':sm,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'candidate O(L^2), response O(HF), environment prototype O(NEH), relaxation O(SH), E=4,H<=48,S<=5','hidden_labels_used_by_learner':False,'environment_bundle_labels_used':True,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
 open(a.output,'w',encoding='utf-8').write(json.dumps(payload,ensure_ascii=False,indent=2));print(json.dumps(sm['48'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
