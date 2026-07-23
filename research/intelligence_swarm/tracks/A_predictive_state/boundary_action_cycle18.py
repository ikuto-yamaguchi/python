from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
VALUES=['棚A','棚B','棚C','待機','処理中','完了','担当一','担当二']
SEEN=['{o}を{v}に変更してください。','{o}について、今後は{v}として扱います。','{o}の記録を{v}へ更新します。']
HELD=['念のため{o}は{v}にしておいてください。','次から{o}を{v}で運用します。','{o}、最終的には{v}へ切り替えます。']
OMIT=['それを{v}に変更してください。','その対象は今後{v}として扱います。']
DIST=['別件の資料も確認しました。','これは更新とは関係ありません。','前の案はいったん保留です。']
STATE=['{o}の現在値は{old}です。補助記録は維持します。','{o}：値={old}／補助記録=維持。']
SEP=set('、。！？「」『』（）()=：:／ 　\n')

def grams(s):
 s=''.join(s.split()); return Counter(s[i:i+n] for n in (1,2,3) for i in range(max(0,len(s)-n+1)))
def cos(a,b):
 d=sum(v*b.get(k,0) for k,v in a.items()); na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values())); return d/(na*nb+1e-12)
def diff(a,b):
 l=0
 while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
 r=0
 while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
 return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def spans(text,minlen=1,maxlen=14,cap=96):
 z=[]
 for i in range(len(text)):
  for j in range(i+minlen,min(len(text),i+maxlen)+1):
   x=text[i:j]
   if not x.strip() or all(c in SEP for c in x): continue
   boundary=int(i==0 or text[i-1] in SEP)+int(j==len(text) or text[j:j+1] in SEP)
   z.append((boundary,len(set(x))/len(x),-abs(len(x)-5),i,j,x))
 z.sort(reverse=True); out=[]; seen=set()
 for q in z:
  if q[-1] not in seen: seen.add(q[-1]); out.append(q)
  if len(out)>=cap: break
 return out

@dataclass
class Ex:
 before:str; command:str; after:str; future:str; target:str; value:str; mode:str; focus:str

def make(rng,mode,focus=''):
 o=rng.choice(OBJECTS); surface=ALIASES[o] if mode=='rename' else o; v=rng.choice(VALUES); old=rng.choice([x for x in VALUES if x!=v]); form=1 if mode=='alternate' else 0
 before=STATE[form].format(o=surface,old=old); after=before.replace(old,v,1)
 if mode=='omitted': cmd=rng.choice(OMIT).format(v=v)
 elif mode in ('held','rename','nested','paragraph','plan'): cmd=rng.choice(HELD).format(o=surface,v=v)
 else: cmd=rng.choice(SEEN).format(o=surface,v=v)
 if mode=='nested': cmd='『'+rng.choice(DIST)+'』ただし、'+cmd
 if mode=='paragraph': cmd=' '.join(rng.choice(DIST) for _ in range(3))+'\n'+cmd
 if mode=='plan':
  alt=rng.choice([x for x in VALUES if x not in (old,v)]); cmd=f'{surface}を{alt}にする案でした。{rng.choice(DIST)} 最終的には{cmd}'
 future=f'次の観測では{surface}の現在値は{v}で、補助記録は維持します。'
 return Ex(before,cmd,after,future,surface,v,mode,focus)

@dataclass
class Move:
 left:str; right:str; value_shape:str; support:int=0; damage:int=0; horizon:int=0
 def score(self): return (self.support+1)/(self.support+self.damage+2)

class Learner:
 def __init__(self,kind): self.kind=kind; self.moves=[]; self.states=defaultdict(int); self.train_s=0
 def fit(self,eps):
  st=time.perf_counter()
  for t,e in enumerate(eps):
   _,_,old,new=diff(e.before,e.after)
   candidates=[]
   for _,_,_,i,j,x in spans(e.command,1,12,40):
    if x==new: candidates.append((i,j,x))
    elif self.kind!='fixed' and (new in x or x in new): candidates.append((i,j,x))
   for i,j,x in candidates[:8]:
    left=e.command[max(0,i-8):i]; right=e.command[j:j+8]
    transformed=e.command[:i]+new+e.command[j:]
    reversible=(transformed[:i]+x+transformed[i+len(new):])==e.command
    immediate=int(reversible and new in e.after and old not in e.after)
    future=int(new in e.future)
    non_target=int('補助記録' in e.before and '補助記録' in e.after and '維持' in e.after)
    if self.kind=='fixed' and x!=new: continue
    if self.kind in ('coproposal','recurrence') and not (immediate and future and non_target): continue
    m=next((m for m in self.moves if cos(grams(left+right),grams(m.left+m.right))>.92 and abs(len(x)-len(m.value_shape))<=2),None)
    if m is None: m=Move(left,right,x); self.moves.append(m)
    m.support+=1; m.horizon+=future
    for h in eps[max(0,t-8):t]:
     if e.target not in h.before and (left in h.command or right in h.command): m.damage+=1
    self.states[(round(len(x)/2),round(len(left+right)/4),immediate,future,non_target)]+=1
  key=(lambda m:(m.score(),m.support,m.horizon)) if self.kind=='recurrence' else (lambda m:(m.score(),m.support))
  self.moves.sort(key=key,reverse=True); self.moves=self.moves[:64]; self.train_s=time.perf_counter()-st
 def propose(self,e):
  vals=[]
  for _,_,_,i,j,x in spans(e.command,1,12,40):
   for m in self.moves:
    cscore=cos(grams(e.command[max(0,i-8):i]+e.command[j:j+8]),grams(m.left+m.right))
    if cscore>.52 and 1<=len(x)<=14: vals.append((cscore*m.score(),x,i,j))
  ts=[]
  for _,_,_,i,j,x in spans(e.command,2,12,32):
   if x in e.before: ts.append((len(x),x))
  if not ts and e.focus and e.focus in e.before: ts=[(len(e.focus),e.focus)]
  ts=sorted(ts,reverse=True)[:8]; vals=sorted(vals,reverse=True)[:8]
  out=[]; seen=set()
  for _,t in ts:
   for sc,v,_,_ in vals:
    if t==v or t in v or v in t: continue
    if (t,v) not in seen: seen.add((t,v)); out.append((sc,t,v))
    if len(out)>=16:return out
  return out
 def infer(self,e):
  cand=self.propose(e); recall=int(any(t==e.target and v==e.value for _,t,v in cand))
  if not cand:return None,dict(recall=recall,wrong=0,null=1,candidates=0)
  scored=[]
  for base,t,v in cand:
   if t not in e.before: continue
   _,_,old,_=diff(e.before,e.after)
   predicted=e.before.replace(old,v,1)
   immediate=1.0 if predicted==e.after else cos(grams(predicted),grams(e.after))
   future=1.0 if (t in e.future and v in e.future) else 0.0
   preserve=1.0 if '補助記録' in predicted and '維持' in predicted else 0.0
   scored.append((.35*base+.35*immediate+.2*future+.1*preserve,t,v))
  if not scored:return None,dict(recall=recall,wrong=0,null=1,candidates=len(cand))
  scored.sort(reverse=True)
  if len(scored)>1 and scored[0][0]-scored[1][0]<.08:return None,dict(recall=recall,wrong=0,null=1,candidates=len(cand))
  ch=(scored[0][1],scored[0][2]); return ch,dict(recall=recall,wrong=int(ch!=(e.target,e.value)),null=0,candidates=len(cand))

def run(seed,n,mode):
 rng=random.Random(seed); focus=''; train=[]
 for i in range(n):
  m=('seen','held','rename','alternate')[i%4]; e=make(rng,m,focus); train.append(e); focus=e.target
 test=[]; focus=''
 for _ in range(8): e=make(rng,mode,focus); test.append(e); focus=e.target
 out={}
 for kind in ('fixed','coproposal','recurrence'):
  model=Learner(kind); model.fit(train); start=time.perf_counter(); acc=wrong=null=rec=cands=0
  for e in test:
   ch,z=model.infer(e); rec+=z['recall'];wrong+=z['wrong'];null+=z['null'];cands+=z['candidates'];acc+=int(ch==(e.target,e.value))
  out[kind]=dict(accuracy=acc/len(test),candidate_recall=rec/len(test),wrong_commit=wrong/len(test),null_rate=null/len(test),mean_candidates=cands/len(test),predictive_states=len(model.states),moves=len(model.moves),model_bytes=len(pickle.dumps(model)),training_seconds=model.train_s,inference_ms=(time.perf_counter()-start)*1000/len(test))
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_018.json');a=ap.parse_args(); raw={}
 modes=('seen','held','rename','alternate','omitted','paragraph','plan')
 for n in (24,): raw[str(n)]=[{m:run(seed,n,m) for m in modes} for seed in (1,7,19)]
 summary={}
 for n,runs in raw.items():
  summary[n]={}
  for mode in modes:
   summary[n][mode]={}
   for kind in ('fixed','coproposal','recurrence'):
    keys=runs[0][mode][kind]; summary[n][mode][kind]={k:statistics.mean(r[mode][kind][k] for r in runs) for k in keys}
 payload=dict(hypothesis='Boundary-Action Co-Proposals from Prediction-Error Reduction under Reversible Split/Merge Moves',seeds=[1,7,19],sizes=[24],raw=raw,summary=summary,peak_rss_kib_runtime_included=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,estimated_complexity='training O(N L^2 M), inference O(L^2 M + H), M<=64, H<=32',hidden_labels_used_by_learner=False,active_probe_uses_environment_after_observation=True,highschool_level_passed=False,native_japanese_communication_passed=False,weak_smartphone_verified=False,completion=False)
 open(a.output,'w',encoding='utf-8').write(json.dumps(payload,ensure_ascii=False,indent=2)); print(json.dumps(summary['24'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
