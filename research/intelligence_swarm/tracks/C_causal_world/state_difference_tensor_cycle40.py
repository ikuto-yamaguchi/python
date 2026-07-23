from __future__ import annotations
import argparse,json,pickle,random,resource,statistics,time
from collections import Counter
from dataclasses import dataclass
OBJECTS=['青い箱','赤い箱','北側端末','南側端末','試料甲','試料乙','鍵A','鍵B']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','北側端末':'北の端末','南側端末':'南の端末','試料甲':'サンプル甲','試料乙':'サンプル乙','鍵A':'第一キー','鍵B':'第二キー'}
VALUES=['棚A','棚B','棚C','棚D','待機','処理中','完了','保留']
OPS=['変更してください','切り替えてください','更新してください']
FILL=['補助記録は維持します。','別件の設定は変えません。','注意事項はそのままです。']
@dataclass
class Ex: before:str; command:str; after:str; obj:str; value:str; old:str; mode:str

def shape(s): return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、：／=\n「」' else c for c in s)
def make(seed,n,mode):
 r=random.Random(seed);out=[]
 for _ in range(n):
  o=r.choice(OBJECTS);surf=ALIASES[o] if mode=='rename' else o;old=r.choice(VALUES);new=r.choice([v for v in VALUES if v!=old])
  b=f'{surf}の現在値は{old}です。{r.choice(FILL)}'
  if mode=='order': c=f'{new}へ{r.choice(OPS)} 対象は{surf}です。'
  elif mode=='lexeme': c=f'{surf}を次から{new}扱いにします。'
  elif mode=='nested': c=f'依頼は「{surf}を{new}へ{r.choice(OPS)}」です。'
  elif mode=='omitted': c=f'それを{new}へ{r.choice(OPS)}'
  elif mode=='paragraph': c=f'{r.choice(FILL)}\n{surf}を{new}へ{r.choice(OPS)}\n{r.choice(FILL)}'
  elif mode=='plan':
   alt=r.choice([v for v in VALUES if v not in (old,new)]);c=f'{surf}を{alt}にする案は撤回し、最終的に{new}へ{r.choice(OPS)}'
  elif mode=='counterfactual': c=f'変更しなければ{surf}は{old}です。実際には{new}へ{r.choice(OPS)}'
  else:c=f'{surf}を{new}へ{r.choice(OPS)}'
  a=f'{surf}の現在値は{new}です。{r.choice(FILL)}';out.append(Ex(b,c,a,surf,new,old,mode))
 return out

def diff(a,b):
 l=0
 while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
 rr=0
 while rr<min(len(a)-l,len(b)-l) and a[-1-rr]==b[-1-rr]:rr+=1
 return l,len(a)-rr,a[l:len(a)-rr],b[l:len(b)-rr]
def bucket(p,n,k=8):return min(k-1,int(k*p/max(1,n)))
def extract_candidates(e):
 objs=[]
 for i in range(len(e.command)):
  for j in range(i+2,min(len(e.command),i+11)+1):
   t=e.command[i:j]
   if t in e.before and not any(x in t for x in '。、\n「」'):objs.append((i,t))
 vals=[]
 for i in range(len(e.command)):
  for j in range(i+1,min(len(e.command),i+9)+1):
   t=e.command[i:j]
   if t not in e.before and not any(x in t for x in '。、\n「」'):vals.append((i,t))
 states=[]
 for i in range(len(e.before)):
  for j in range(i+1,min(len(e.before),i+9)+1):
   t=e.before[i:j]
   if not any(x in t for x in '。、\n「」'):states.append((i,j,t))
 objs=sorted(set(objs),key=lambda x:-len(x[1]))[:4];vals=sorted(set(vals),key=lambda x:-len(x[1]))[:6];states=states[:48]
 out=[]
 for oi,o in objs:
  for vi,v in vals:
   for si,sj,st in states:
    sig=(bucket(oi,len(e.command)),bucket(si,len(e.before)),bucket(vi,len(e.command)),len(o)//2,len(st)//2,len(v)//2,shape(o),shape(st),shape(v))
    out.append((sig,si,sj,v,o))
 return out[:128]
def gold_sig(e):
 l,r,old,new=diff(e.before,e.after);oi=e.command.find(e.obj);vi=e.command.find(e.value)
 if oi<0 or vi<0:return None
 return (bucket(oi,len(e.command)),bucket(l,len(e.before)),bucket(vi,len(e.command)),len(e.obj)//2,len(old)//2,len(e.value)//2,shape(e.obj),shape(old),shape(e.value))
class Model:
 def __init__(self,kind):self.kind=kind;self.comp=[];self.train=0
 def fit(self,train,probe,shuffle=False):
  t=time.perf_counter();cnt=Counter(gold_sig(e) for e in train if gold_sig(e));marg=[Counter(),Counter(),Counter()]
  for s,n in cnt.items():
   marg[0][(s[0],s[3],s[6])]+=n;marg[1][(s[1],s[4],s[7])]+=n;marg[2][(s[2],s[5],s[8])]+=n
  support=Counter();wrong=Counter();obs=probe[1:]+probe[:1] if shuffle else probe
  for e,o in zip(probe,obs):
   gs=gold_sig(e)
   if not gs:continue
   support[gs]+=int(e.after==o.after);wrong[gs]+=int(e.after!=o.after)
  comp=[]
  for s,n in cnt.items():
   score=marg[0][(s[0],s[3],s[6])]+marg[1][(s[1],s[4],s[7])]+marg[2][(s[2],s[5],s[8])]
   if self.kind=='literal' and n>=2:comp.append((s,n))
   elif self.kind=='rank1' and score>=6:comp.append((s,score))
   elif self.kind=='tensor' and support[s]>=1 and support[s]>=wrong[s] and score>=6:comp.append((s,score+support[s]-wrong[s]))
  self.comp=sorted(comp,key=lambda x:x[1],reverse=True)[:64];self.train=time.perf_counter()-t
 def infer(self,e):
  allow=dict(self.comp);cs=[]
  for c in extract_candidates(e):
   if c[0] in allow:cs.append((allow[c[0]],e.before[:c[1]]+c[3]+e.before[c[2]:],c))
  if not cs:return None,0
  cs.sort(key=lambda x:x[0],reverse=True);top=cs[0][0];tops=[x for x in cs if x[0]==top]
  if len({x[1] for x in tops})!=1:return None,len(cs)
  return tops[0],len(cs)
def evaluate(seed,mode):
 train=make(seed,24,'seen')+make(seed+1,12,'rename')+make(seed+2,12,'order');probe=make(seed+100,12,'seen');test=make(seed+999,12,mode);out={}
 for name,kind,sh in [('literal','literal',0),('rank1','rank1',0),('tensor','tensor',0),('tensor_shuffle','tensor',1)]:
  m=Model(kind);m.fit(train,probe,bool(sh));vals=[];t=time.perf_counter()
  for e in test:
   p,n=m.infer(e);vals.append({'acc':p is not None and p[1]==e.after,'wrong':p is not None and p[1]!=e.after,'null':p is None,'exact':p is not None and p[2][3]==e.value and p[2][4]==e.obj,'candidates':n})
  ms=(time.perf_counter()-t)*1000/len(test);out[name]={k:statistics.mean(float(v[k]) for v in vals) for k in vals[0]};out[name].update({'components':len(m.comp),'model_bytes':len(pickle.dumps(m)),'training_seconds':m.train,'inference_ms':ms})
 return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='MEASUREMENTS_CYCLE_040.json');a=ap.parse_args();modes=['seen','order','lexeme','rename','nested','omitted','paragraph','plan','counterfactual']
 raw={str(s):{m:evaluate(s,m) for m in modes} for s in (1,7,19)};summary={}
 for m in modes:
  summary[m]={}
  for k in ('literal','rank1','tensor','tensor_shuffle'):summary[m][k]={x:statistics.mean(raw[str(s)][m][k][x] for s in (1,7,19)) for x in raw['1'][m][k]}
 p={'cycle':40,'hypothesis':'Relation-Bearing Event Birth from Cross-Object State-Difference Tensor Factorization','seeds':[1,7,19],'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'induction O(NL), marginal tensor factorization O(F), inference O(L^3) with 128-candidate cap','final_after_future_used_for_ranking':False,'fixed_ontology_or_slots':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
 open(a.output,'w',encoding='utf8').write(json.dumps(p,ensure_ascii=False,indent=2));print(json.dumps(summary['seen'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
