from __future__ import annotations
from dataclasses import dataclass
from collections import Counter,defaultdict
import json,random,time,pickle,resource,statistics
OBJ=['青い箱','赤い箱','小型端末','大型端末']; AL={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末'}
VAL=['棚A','棚B','棚C','待機','処理中','完了','担当一','担当二']
@dataclass
class Ex: before:str; command:str; after:str; future:str; obj:str; old:str; new:str; mode:str
@dataclass(frozen=True)
class Sig: pos:int; width:int; old_shape:str; new_shape:str
def sh(s): return ''.join('A' if c.isascii() and c.isalnum() else 'J' for c in s)
def build(seed,n,mode):
 r=random.Random(seed); out=[]; world={}; focus=None
 for i in range(n):
  o=focus if mode=='omitted' and i else r.choice(OBJ); surf=AL[o] if mode=='rename' else o
  old=world.get(o,r.choice(VAL)); new=r.choice([x for x in VAL if x!=old])
  before=f'{surf}の現在値は{old}です。補助記録は維持します。'; cmd=f'{surf}の値を{new}へ変更してください。'
  if mode=='order': cmd=f'{new}へ変更してください、対象は{surf}です。'
  if mode=='lexeme': cmd=f'対象{surf}は次から{new}扱いにします。'
  if mode=='omitted': cmd=f'それを{new}へ変更してください。'
  if mode=='paragraph': cmd='前段説明。別件維持。\n'+cmd+'\n補助記録維持。'
  if mode=='plan': cmd=f'{surf}を{r.choice([x for x in VAL if x not in (old,new)])}にする案は撤回。最終的には{new}へ変更。'
  if mode=='counterfactual': cmd=f'もし変更しなければ{old}のまま。実際には{surf}を{new}へ変更。'
  after=f'{surf}の現在値は{new}です。補助記録は維持します。'; future=f'次も{surf}は{new}です。'
  out.append(Ex(before,cmd,after,future,surf,old,new,mode)); world[o]=new; focus=o
 return out
def true_span(e): a=e.before.find(e.old); return a,a+len(e.old)
def vals(e,ns):
 xs=[]
 for i in range(len(e.command)):
  for j in range(i+1,min(len(e.command),i+10)+1):
   x=e.command[i:j]
   if x not in e.before and sh(x)==ns: xs.append(x)
 return sorted(set(xs),key=lambda x:(-len(x),x))[:8]
def cand(e,s):
 out=[]
 for a in range(max(0,s.pos-3),min(len(e.before),s.pos+4)):
  for w in range(max(1,s.width-3),min(12,s.width+4)):
   b=a+w
   if b>len(e.before) or sh(e.before[a:b])!=s.old_shape: continue
   for v in vals(e,s.new_shape): out.append((e.before[:a]+v+e.before[b:],a,b,v))
 return out
class M:
 def __init__(self,mode): self.mode=mode; self.sigs=[]; self.family=[]; self.credit=Counter(); self.t=0
 def fit(self,ind,probe,shuffle=False):
  t=time.perf_counter(); c=Counter()
  for e in ind:
   a,b=true_span(e)
   for da in (-2,-1,0,1,2):
    for db in (-2,-1,0,1,2):
     x=max(0,a+da); y=min(len(e.before),b+db)
     if x<y: c[Sig(x,y-x,sh(e.before[x:y]),sh(e.new))]+=1
  self.sigs=[s for s,n in c.most_common(32) if n>=2]; obs=[e.after for e in probe]
  if shuffle: obs=obs[1:]+obs[:1]
  resp={s:[] for s in self.sigs}; supports=defaultdict(list)
  for e,o in zip(probe,obs):
   for s in self.sigs:
    cs=cand(e,s); good=[z for z in cs if z[0]==o]; resp[s].append(1 if good else -1 if cs else 0)
    for _,a,b,v in good:
     changed=True
     while changed:
      changed=False
      for na,nb in ((a+1,b),(a,b-1)):
       if na<nb and e.before[:na]+v+e.before[nb:]==o: a,b=na,nb; changed=True; break
     supports[s].append((a,b,v))
  g=defaultdict(list)
  for s,v in resp.items(): g[tuple(v)].append(s)
  for vec,ms in g.items():
   pos=sum(x==1 for x in vec); wrong=sum(x==-1 for x in vec)
   if len(ms)>=2 and pos>=2 and wrong<=pos:
    faithful=[s for s in ms if supports[s] and statistics.mean(b-a for a,b,_ in supports[s])<=s.width]
    self.family+=faithful
    for s in faithful:self.credit[s]=2*pos-wrong
  self.t=time.perf_counter()-t
 def pred(self,e,remove=False):
  act=[] if remove else (self.family if self.mode!='surface' else self.sigs); out=[]
  for s in act:
   for p,a,b,v in cand(e,s): out.append((int(v in e.command)+int('補助記録' in p)+(.2*self.credit[s] if self.mode!='surface' else 0)-.05*(b-a),p,a,b,v,s))
  if not out:return None,0
  out=sorted(out,key=lambda z:(z[0],z[1],z[2],z[3],z[4]),reverse=True); best=out[0][0]; tops=[x for x in out if abs(x[0]-best)<.5]
  if len({x[1] for x in tops})>1:return None,len(out)
  return tops[0],len(out)
def evalm(m,test,remove=False):
 co=wr=nu=ex=0; cs=[]; st=time.perf_counter()
 for e in test:
  p,n=m.pred(e,remove); cs.append(n)
  if p is None:nu+=1
  elif p[1]==e.after:co+=1
  else:wr+=1
  if p is not None:
   a,b=true_span(e); ex+=int(p[2]==a and p[3]==b and p[4]==e.new)
 N=len(test); return dict(accuracy=co/N,wrong=wr/N,null=nu/N,exact_boundary=ex/N,mean_candidates=statistics.mean(cs),model_bytes=len(pickle.dumps(m)),training_seconds=m.t,inference_ms=(time.perf_counter()-st)*1000/N,families=len(m.family),sigs=len(m.sigs))
def main():
 modes=['seen','order','lexeme','rename','omitted','paragraph','plan','counterfactual']; raw={}
 for seed in (1,7,19):
  d=build(seed,72,'seen'); ind,pr=d[:48],d[48:]; mods={}
  for k in ('surface','minimal','shuffle'):
   m=M('surface' if k=='surface' else 'minimal'); m.fit(ind,pr,shuffle=k=='shuffle'); mods[k]=m
  raw[str(seed)]={mo:{k:evalm(m,build(seed+999,18,mo)) for k,m in mods.items()} for mo in modes}; raw[str(seed)]['removal']={mo:evalm(mods['minimal'],build(seed+999,18,mo),True) for mo in modes}
 summary={}
 for mo in modes:
  summary[mo]={}
  for k in ('surface','minimal','shuffle'):
   ks=[x for x,v in raw['1'][mo][k].items() if isinstance(v,(int,float))]; summary[mo][k]={x:statistics.mean(raw[str(s)][mo][k][x] for s in (1,7,19)) for x in ks}
  summary[mo]['removal']={x:statistics.mean(raw[str(s)]['removal'][mo][x] for s in (1,7,19)) for x in raw['1']['removal'][mo] if isinstance(raw['1']['removal'][mo][x],(int,float))}
 out={'cycle':33,'hypothesis':'Boundary-Faithful Mechanism Families from Minimal Intervention Supports','summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
 with open('MEASUREMENTS_CYCLE_033.json','w',encoding='utf-8') as f: json.dump(out,f,ensure_ascii=False,indent=2)
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
