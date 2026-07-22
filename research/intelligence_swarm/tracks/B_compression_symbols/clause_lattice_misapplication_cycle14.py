from __future__ import annotations
import argparse, json, math, pickle, random, resource, statistics, time
from collections import Counter, defaultdict
from dataclasses import dataclass

OBJECTS=['青い箱','赤い箱','試料甲','試料乙','端末一','端末二','北側の鍵','南側の鍵']
FIELDS=['場所','状態','担当']
VALUES={'場所':['棚A','棚B','棚C','棚D'],'状態':['待機','実行中','完了','保留'],'担当':['佐藤','鈴木','田中','高橋']}
STATE_FORMS=[
 lambda o,d:f"{o}は、場所が{d['場所']}、状態が{d['状態']}、担当が{d['担当']}。",
 lambda o,d:f"{o}：担当={d['担当']}；場所={d['場所']}；状態={d['状態']}。",
 lambda o,d:f"記録対象{o}。現在地{d['場所']}。進行{d['状態']}。受持{d['担当']}。",
]
COMMANDS={
 '場所':["{o}を{v}へ移してください。","{o}の置き先を{v}に変更。","{v}へ{o}を移す。"],
 '状態':["{o}を{v}にしてください。","{o}の状態を{v}へ更新。","{v}として{o}を扱う。"],
 '担当':["{o}の担当を{v}に替えてください。","{o}は{v}が担当します。","{v}へ{o}を引き継ぐ。"],
}
OMIT={
 '場所':["それを{v}へ移してください。"],
 '状態':["その対象を{v}にしてください。"],
 '担当':["担当を{v}へ変更してください。"],
}
SEPS='。、；;\n'

def norm(s): return ''.join(s.split())
def render(world,form): return '\n'.join(STATE_FORMS[form](o,world[o]) for o in sorted(world))

def clause_spans(s):
 out=[]; start=0
 for i,ch in enumerate(s):
  if ch in SEPS:
   if i>start: out.append((start,i+1,s[start:i+1]))
   start=i+1
 if start<len(s): out.append((start,len(s),s[start:]))
 base=list(out)
 for i in range(len(base)-1):
  out.append((base[i][0],base[i+1][1],s[base[i][0]:base[i+1][1]]))
 return out

def edit(a,b):
 p=0
 while p<min(len(a),len(b)) and a[p]==b[p]: p+=1
 q=0
 while q<min(len(a)-p,len(b)-p) and a[-1-q]==b[-1-q]: q+=1
 return a[:p], a[p:len(a)-q if q else len(a)], b[p:len(b)-q if q else len(b)], a[len(a)-q:] if q else ''

def grams(s):
 s=norm(s); return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))
def cos(a,b):
 dot=sum(v*b.get(k,0) for k,v in a.items()); na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
 return dot/(na*nb+1e-12)

@dataclass(frozen=True)
class Candidate:
 left:str; old:str; new:str; right:str; cmd_left:str; cmd_right:str; width:int

@dataclass
class Program:
 left:str; right:str; cmd_left:str; cmd_right:str; support:int=0; destruction:float=0.; forms:set=None
 def __post_init__(self):
  if self.forms is None:self.forms=set()

class Learner:
 def __init__(self,mode):
  self.mode=mode; self.programs=[]; self.raw=0; self.rejected=0; self.quotients=0
 def propose(self,b,c,a):
  bs=clause_spans(b); aas=clause_spans(a); out=[]
  for i,(l,r,x) in enumerate(bs):
   for j,(l2,r2,y) in enumerate(aas):
    if x==y: continue
    L,old,new,R=edit(x,y)
    if not old or not new or len(old)>20 or len(new)>20: continue
    if len(L)+len(R)<2: continue
    pos=c.find(new)
    if pos<0: continue
    cl=c[max(0,pos-8):pos]; cr=c[pos+len(new):pos+len(new)+8]
    out.append(Candidate(L,old,new,R,cl,cr,1 if (i==j) else 2))
  uniq=list(dict.fromkeys(out)); uniq.sort(key=lambda z:(z.width,len(z.old)+len(z.new),-(len(z.left)+len(z.right))))
  self.raw+=min(len(uniq),96); return uniq[:96]
 def signature(self,p):
  return (norm(p.left[-8:]),norm(p.right[:8]),norm(p.cmd_left[-6:]),norm(p.cmd_right[:6]))
 def execute(self,b,c,p):
  pos=c.find(p.cmd_left) if p.cmd_left else 0
  if pos<0:return None
  st=pos+len(p.cmd_left); en=c.find(p.cmd_right,st) if p.cmd_right else len(c)
  if en<st:return None
  nv=c[st:en]
  if not nv or len(nv)>20:return None
  hits=[]
  for l,r,x in clause_spans(b):
   if p.left and not x.startswith(p.left): continue
   if p.right and not x.endswith(p.right): continue
   a=len(p.left); z=len(x)-len(p.right) if p.right else len(x)
   if z<a:continue
   hits.append((l,r,x[:a]+nv+x[z:]))
  if len(hits)!=1:return None
  l,r,y=hits[0]; return b[:l]+y+b[r:]
 def misapplication_damage(self,b,c,a,p):
  correct=self.execute(b,c,p)
  if correct is None:return 1.0
  alternatives=0; accidental=0
  pos=c.find(p.cmd_left) if p.cmd_left else 0
  st=pos+len(p.cmd_left) if pos>=0 else 0; en=c.find(p.cmd_right,st) if p.cmd_right else len(c)
  nv=c[st:en] if en>=st else ''
  for l,r,x in clause_spans(b):
   if len(x)<len(p.left)+len(p.right):continue
   y=x[:len(p.left)]+nv+(x[len(x)-len(p.right):] if p.right else '')
   alt=b[:l]+y+b[r:]
   if alt!=correct:
    alternatives+=1
    if alt==a: accidental+=1
  return (alternatives>0)*0.5 + accidental/max(1,alternatives)
 def fit(self,episodes):
  buckets=defaultdict(list)
  for b,c,a in episodes:
   for x in self.propose(b,c,a):
    if self.mode!='clause':
     trial=Program(x.left,x.right,x.cmd_left,x.cmd_right)
     pred=self.execute(b,c,trial)
     if pred!=a:self.rejected+=1;continue
     dmg=self.misapplication_damage(b,c,a,trial)
     if self.mode in ('misapply','quotient') and dmg>=0.75:self.rejected+=1;continue
    buckets[self.signature(x)].append((b,c,a,x))
  programs=[]
  for sig,items in buckets.items():
   if len(items)<2:self.rejected+=len(items);continue
   x=items[0][3]; p=Program(x.left,x.right,x.cmd_left,x.cmd_right,support=len(items))
   p.forms={norm(i[3].cmd_left+i[3].cmd_right) for i in items}
   p.destruction=statistics.mean(self.misapplication_damage(b,c,a,p) for b,c,a,_ in items[:12])
   programs.append(p)
  if self.mode=='quotient':
   programs.sort(key=lambda p:-(math.log1p(p.support)+.4*math.log1p(len(p.forms))-0.03*(len(p.left)+len(p.right)+len(p.cmd_left)+len(p.cmd_right))-p.destruction))
   merged={}
   for p in programs:
    q=(norm(p.left[-4:]),norm(p.right[:4]),round(p.destruction,1))
    if q not in merged:merged[q]=p
   self.quotients=len(merged); programs=list(merged.values())
  self.programs=programs[:32]
 def predict(self,b,c):
  cand=[]
  for p in self.programs:
   y=self.execute(b,c,p)
   if y is None:continue
   score=math.log1p(p.support)+.2*math.log1p(len(p.forms))-.5*p.destruction
   cand.append((score,y))
  if not cand:return None,0
  cand.sort(reverse=True,key=lambda x:x[0]); return cand[0][1],len(cand)

def episode(rng,form=0,variant=0,omit=False,nested=False,paragraph=False):
 objs=rng.sample(OBJECTS,3); world={o:{f:rng.choice(VALUES[f]) for f in FIELDS} for o in objs}; target=rng.choice(objs); field=rng.choice(FIELDS)
 nv=rng.choice([v for v in VALUES[field] if v!=world[target][field]])
 before=render(world,form); afterw={o:d.copy() for o,d in world.items()}; afterw[target][field]=nv; after=render(afterw,form)
 cmd=(OMIT[field][0] if omit else COMMANDS[field][variant%3]).format(o=target,v=nv)
 if nested:cmd=f"確認文『実行対象は「{cmd}」です』"
 if paragraph:cmd=f"別件を確認しました。\nその後の指示です。{cmd}"
 return before,cmd,after

def run(seed,n,mode,method):
 rng=random.Random(seed); train=[]
 for i in range(n):train.append(episode(rng,0,i%2))
 m=Learner(method); st=time.perf_counter();m.fit(train);ts=time.perf_counter()-st
 tests=[]
 for _ in range(100):
  if mode=='seen':tests.append(episode(rng,0,0))
  elif mode=='held_order':tests.append(episode(rng,0,2))
  elif mode=='held_lexeme':tests.append(episode(rng,0,1))
  elif mode=='nested':tests.append(episode(rng,0,0,nested=True))
  elif mode=='omitted':tests.append(episode(rng,0,0,omit=True))
  elif mode=='alternate':tests.append(episode(rng,1,0))
  elif mode=='freeform':tests.append(episode(rng,2,2,paragraph=True))
 reads=correct=0; st=time.perf_counter()
 for b,c,a in tests:
  y,r=m.predict(b,c);reads+=r;correct+=y==a
 infer=(time.perf_counter()-st)*1000/len(tests)
 return {'accuracy':correct/len(tests),'model_bytes':len(pickle.dumps(m)),'programs':len(m.programs),'quotients':m.quotients,'raw_candidates':m.raw,'rejected':m.rejected,'train_seconds':ts,'infer_ms':infer,'reads':reads/len(tests)}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_014.json');args=ap.parse_args()
 modes=('seen','held_order','held_lexeme','nested','omitted','alternate','freeform'); methods=('clause','misapply','quotient'); raw={}
 for n in (48,144,432):
  runs=[]
  for seed in (1,7,19):runs.append({m:{x:run(seed,n,x,m) for x in modes} for m in methods})
  raw[str(n)]=runs
 summary={}
 for n,runs in raw.items():
  summary[n]={m:{x:{k:statistics.mean(r[m][x][k] for r in runs) for k in runs[0][m][x]} for x in modes} for m in methods}
 payload={'hypothesis':'Clause-Lattice Misapplication Execution with Relation Quotient Induction','seeds':[1,7,19],'sizes':[48,144,432],'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'proposal O(N C^2), execution O(P C), P<=32, clause lattice O(L)','highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
 open(args.output,'w',encoding='utf-8').write(json.dumps(payload,ensure_ascii=False,indent=2)); print(json.dumps(summary['432'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
