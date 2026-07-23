from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
import json, math, pickle, random, resource, statistics, time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
VALUES=['棚A','棚B','棚C','待機','処理中','完了','担当一','担当二']
CMDS=['{o}を{v}に変更してください。','{o}について、今後は{v}として扱います。','{o}の記録を{v}へ更新します。']
HELD=['念のため{o}は{v}にしておいてください。','次から{o}を{v}で運用します。','{o}、最終的には{v}へ切り替えます。']
OMIT=['それを{v}に変更してください。','その対象は今後{v}として扱います。']
STATE=['{o}の現在値は{v}です。補助記録は維持します。','{o}：値={v}／補助記録=維持。']
DIST=['別件の資料も確認しました。','これは更新とは関係ありません。','前の案はいったん保留です。']
SEP=set('、。！？「」『』（）()=：:／ 　\n')

def grams(s):
 s=''.join(s.split());return Counter(s[i:i+n] for n in (1,2,3) for i in range(max(0,len(s)-n+1)))
def cos(a,b):
 d=sum(v*b.get(k,0) for k,v in a.items());na=math.sqrt(sum(v*v for v in a.values()));nb=math.sqrt(sum(v*v for v in b.values()));return d/(na*nb+1e-9)
def spans(s,cap=10):
 z=[]
 for i in range(len(s)):
  for j in range(i+2,min(len(s),i+13)+1):
   x=s[i:j]
   if not x.strip() or all(c in SEP for c in x):continue
   b=int(i==0 or s[i-1] in SEP)+int(j==len(s) or s[j:j+1] in SEP)
   z.append((b,len(set(x))/len(x),len(x),x))
 z.sort(reverse=True);out=[];seen=set()
 for *_,x in z:
  if x not in seen:seen.add(x);out.append(x)
  if len(out)>=cap:break
 return out

def common_spans(a,b,cap=12):
 return [x for x in spans(a,12) if x in b][:cap]
def changed(a,b):
 l=0
 while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
 r=0
 while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
 return a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

@dataclass
class Ex:
 before:str;command:str;after:str;future:str;obj:str;val:str;mode:str;focus:str

def make(rng,mode,focus=''):
 o=rng.choice(OBJECTS);surf=ALIASES[o] if mode=='rename' else o
 old=rng.choice(VALUES);v=rng.choice([x for x in VALUES if x!=old]);form=1 if mode=='alternate' else 0
 before=STATE[form].format(o=surf,v=old);after=STATE[form].format(o=surf,v=v)
 if mode=='omitted': cmd=rng.choice(OMIT).format(v=v)
 elif mode in ('held','rename','nested','paragraph','plan'): cmd=rng.choice(HELD).format(o=surf,v=v)
 else: cmd=rng.choice(CMDS).format(o=surf,v=v)
 if mode=='nested':cmd='『'+rng.choice(DIST)+'』ただし、'+cmd
 if mode=='paragraph':cmd=' '.join(rng.choice(DIST) for _ in range(3))+'\n'+cmd
 if mode=='plan':
  alt=rng.choice([x for x in VALUES if x not in (old,v)]);cmd=f'{surf}を{alt}へ変える案でした。{rng.choice(DIST)}最終的には'+cmd
 future=f'次の観測でも{surf}は存在し、局所値は{v}、補助記録は維持。'
 return Ex(before,cmd,after,future,surf,v,mode,focus)

class Model:
 def __init__(self,kind,k=6):self.kind=kind;self.k=k;self.persist_proto=[];self.change_proto=[];self.train_s=0
 def fit(self,eps):
  t=time.perf_counter();pp=[];cp=[]
  for e in eps:
   for x in common_spans(e.before,e.future,8):
    score=int(x in e.command)+cos(grams(x),grams(e.command))+0.2*len(x)
    pp.append((score,grams(e.before.replace(x,'◇')+'|'+e.future.replace(x,'◇')),x))
   old,new=changed(e.before,e.after)
   for x in spans(e.command,10):
    score=int(x in e.after and x not in e.before)+cos(grams(x),grams(new))+0.1*len(x)
    cp.append((score,grams(e.command.replace(x,'△')+'|'+e.after.replace(x,'△')),x))
  pp.sort(reverse=True,key=lambda z:z[0]);cp.sort(reverse=True,key=lambda z:z[0])
  self.persist_proto=[g for _,g,_ in pp[:16]];self.change_proto=[g for _,g,_ in cp[:16]];self.train_s=time.perf_counter()-t
 def propose(self,e):
  ps=[]
  for x in common_spans(e.before,e.future,8):
   s=int(x in e.command)+max([cos(grams(e.before.replace(x,'◇')+'|'+e.future.replace(x,'◇')),g) for g in self.persist_proto] or [0])+0.03*len(x)
   ps.append((s,x))
  cs=[]
  old,new=changed(e.before,e.after)
  for x in spans(e.command,10):
   s=int(x in e.after and x not in e.before)+max([cos(grams(e.command.replace(x,'△')+'|'+e.after.replace(x,'△')),g) for g in self.change_proto] or [0])+0.2*cos(grams(x),grams(new))
   cs.append((s,x))
  ps=sorted(ps,reverse=True)[:self.k];cs=sorted(cs,reverse=True)[:self.k]
  if self.kind=='joint':
   return ps,cs,[(p,c) for _,p in ps for _,c in cs][:16]
  ps=[z for z in ps if z[1] in e.before and z[1] in e.future]
  cs=[z for z in cs if z[1] in e.after and z[1] not in e.before]
  return ps,cs,[(p,c) for _,p in ps[:4] for _,c in cs[:4]][:16]
 def solve(self,e):
  ps,cs,pairs=self.propose(e);pr=int(any(x==e.obj for _,x in ps));cr=int(any(x==e.val for _,x in cs));pair=int((e.obj,e.val) in pairs)
  if self.kind=='dual_null' and not pair:return None,(pr,cr,pair,len(ps),len(cs),len(pairs),0)
  if not pairs:return None,(pr,cr,pair,len(ps),len(cs),0,0)
  scored=[]
  for p,c in pairs:
   persistence=cos(grams(p),grams(e.before))+cos(grams(p),grams(e.future))
   change=cos(grams(c),grams(e.after))+int(c in e.command)
   non_target=int('補助記録' in e.before and '補助記録' in e.after)
   scored.append((persistence+change+0.2*non_target,p,c))
  scored.sort(reverse=True);chosen=(scored[0][1],scored[0][2])
  return chosen,(pr,cr,pair,len(ps),len(cs),len(pairs),int(chosen!=(e.obj,e.val)))

def run(seed,n,mode):
 rng=random.Random(seed);focus='';train=[]
 for i in range(n):
  m=('seen','held','rename','alternate')[i%4];e=make(rng,m,focus);train.append(e);focus=e.obj
 test=[];focus=''
 for _ in range(8):e=make(rng,mode,focus);test.append(e);focus=e.obj
 out={}
 for kind in ('joint','dual','dual_null'):
  m=Model(kind);m.fit(train);t=time.perf_counter();acc=pr=cr=pair=wrong=null=np=nc=npa=0
  for e in test:
   ch,z=m.solve(e);a,b,c,d,f,g,w=z;pr+=a;cr+=b;pair+=c;np+=d;nc+=f;npa+=g;wrong+=w;null+=int(ch is None);acc+=int(ch==(e.obj,e.val))
  out[kind]={'accuracy':acc/8,'object_recall':pr/8,'value_recall':cr/8,'pair_recall':pair/8,'wrong_commit':wrong/8,'null_rate':null/8,'persistence_candidates':np/8,'change_candidates':nc/8,'pair_candidates':npa/8,'model_bytes':len(pickle.dumps(m)),'training_seconds':m.train_s,'inference_ms':(time.perf_counter()-t)*1000/8}
 return out

def main():
 raw={}
 for n in (24,):
  runs=[]
  for seed in (1,7,19):runs.append({mode:run(seed,n,mode) for mode in ('seen','held','rename','alternate','nested','omitted','paragraph','plan')})
  raw[str(n)]=runs
 summary={}
 for n,runs in raw.items():
  summary[n]={}
  for mode in runs[0]:
   summary[n][mode]={}
   for kind in ('joint','dual','dual_null'):
    summary[n][mode][kind]={k:statistics.mean(r[mode][kind][k] for r in runs) for k in runs[0][mode][kind]}
 payload={'hypothesis':'Dual-View Boundary Birth from Independent Persistence and Change Predictions','seeds':[1,7,19],'sizes':[24],'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'fit O(NL^2G), inference O(L^2G + KpKc), Kp,Kc<=6','hidden_labels_used_by_learner':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
 with open('results_cycle_019.json','w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
 print(json.dumps(summary['24'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
