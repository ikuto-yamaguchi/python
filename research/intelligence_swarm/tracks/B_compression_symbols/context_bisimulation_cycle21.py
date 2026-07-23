from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse,json,math,pickle,random,resource,statistics,time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
FIELDS=['置き場所','状態','担当']
VALUES={'置き場所':['棚A','棚B','棚C','棚D'],'状態':['待機','処理中','完了','保留'],'担当':['担当一','担当二','担当三','担当四']}
STATE_FORMS=['{o}の置き場所は{loc}。{o}の状態は{status}。{o}の担当は{owner}。','{o}について、保管先={loc}／進行={status}／受持={owner}。']
COMMANDS={'置き場所':['{o}を{v}へ移してください。','{o}の保管先を{v}へ変更します。'],'状態':['{o}を{v}にしてください。','{o}の進行状態を{v}へ切り替えます。'],'担当':['{o}を{v}の担当にしてください。','{o}の受け持ちを{v}へ変更します。']}
HELD_ORDER={'置き場所':['{v}へ移してください、対象は{o}です。'],'状態':['{v}扱いにしてください、対象は{o}です。'],'担当':['{v}へ引き継いでください、対象は{o}です。']}
HELD_LEXEME={'置き場所':['対象{o}は次から{v}で保管。'],'状態':['対象{o}は以後{v}として運用。'],'担当':['対象{o}の受持を{v}へ。']}
OMITTED={'置き場所':['それを{v}へ移してください。'],'状態':['その対象を{v}にしてください。'],'担当':['担当は{v}へ変えてください。']}

def grams(s):
 s=''.join(s.split());return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))
def cosine(a,b):
 d=sum(v*b.get(k,0) for k,v in a.items());na=math.sqrt(sum(v*v for v in a.values()));nb=math.sqrt(sum(v*v for v in b.values()));return d/(na*nb+1e-12)
def clauses(t):
 cuts=[0]
 for i,x in enumerate(t):
  if x in '。\n／':cuts.append(i+1)
 if cuts[-1]!=len(t):cuts.append(len(t))
 return [t[a:b] for a,b in zip(cuts,cuts[1:]) if t[a:b].strip()][:12]
def diff(a,b):
 l=0
 while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
 r=0
 while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
 return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]
def contexts(t,x,radius=10):
 out=[];p=0
 while x:
  i=t.find(x,p)
  if i<0:break
  out.append((t[max(0,i-radius):i],t[i+len(x):i+len(x)+radius]));p=i+1
 return out[:4]
def shape(s):
 return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、／=\n ' else c for c in s)
def state(o,d,form=0):return STATE_FORMS[form].format(o=o,loc=d['置き場所'],status=d['状態'],owner=d['担当'])

@dataclass
class Episode: before:str;command:str;after:str;obj:str;field_name:str;value:str;focus:str|None
@dataclass
class Program:
 cmd_left:str;cmd_right:str;state_left:str;state_right:str;support:int=1
 success:tuple=();wrong:tuple=();noexec:tuple=();fillers:tuple=()
 def bits(self):return 8*(len(self.cmd_left)+len(self.cmd_right)+len(self.state_left)+len(self.state_right)+8)
@dataclass
class ContextNT:
 members:tuple; fillers:tuple; success:tuple; wrong:tuple; noexec:tuple; support:int; heldout_score:float
 def bits(self):
  return 32+sum(8*(len(a)+len(b)+len(c)+len(d)) for a,b,c,d in self.members)+sum(8*len(x) for x in self.fillers)

class Learner:
 def __init__(self,mode,cap=32):
  self.mode=mode;self.cap=cap;self.programs=[];self.context_nt=[];self.raw=0;self.rejected=0;self.merges=0;self.description_bits=0.
 def extract(self,cmd,left,right):
  starts=[0] if not left else [];p=0
  while left:
   i=cmd.find(left,p)
   if i<0:break
   starts.append(i+len(left));p=i+1
  vals=[]
  for st in starts:
   en=cmd.find(right,st) if right else len(cmd)
   if en>=st and 0<en-st<=14:vals.append(cmd[st:en])
  return min(vals,key=len) if vals else None
 def execute_ctx(self,st,cmd,cl,cr,sl,sr):
  v=self.extract(cmd,cl,cr)
  if v is None:return st,False,0,None
  m=[];p=0
  while True:
   i=st.find(sl,p) if sl else p
   if i<0:break
   a=i+len(sl);b=st.find(sr,a) if sr else len(st)
   if b>=a:m.append((a,b))
   p=i+1
   if not sl or p>=len(st):break
  if len(m)!=1:return st,False,len(m),v
  a,b=m[0];return st[:a]+v+st[b:],True,1,v
 def execute(self,e,p):return self.execute_ctx(e.before,e.command,p.cmd_left,p.cmd_right,p.state_left,p.state_right)
 def propose(self,e):
  out=[]
  for bc in clauses(e.before):
   for ac in clauses(e.after):
    l,r,old,new=diff(bc,ac)
    if not new or len(new)>14 or bc==ac:continue
    for cl,cr in contexts(e.command,new):
     out.append(Program(cl,cr,bc[:l],bc[len(bc)-r:] if r else ''))
     if len(out)>=96:return out
  return out
 def behavior(self,p,eps):
  s=[];w=[];n=[];fs=[]
  for i,e in enumerate(eps):
   out,ok,amb,v=self.execute(e,p)
   if ok and amb==1:fs.append(v)
   (n if not ok or amb!=1 else s if out==e.after else w).append(i)
  p.success=tuple(s);p.wrong=tuple(w);p.noexec=tuple(n);p.fillers=tuple(sorted(set(x for x in fs if x)));return p
 def candidates(self,eps):
  u={}
  for e in eps:
   ps=self.propose(e);self.raw+=len(ps)
   for p in ps:
    out,ok,amb,_=self.execute(e,p)
    if not ok or amb!=1 or out!=e.after:self.rejected+=1;continue
    k=(p.cmd_left,p.cmd_right,p.state_left,p.state_right)
    if k in u:u[k].support+=1
    else:u[k]=p
  return sorted((self.behavior(p,eps) for p in u.values()),key=lambda p:(len(p.success),p.support,-p.bits()),reverse=True)[:64]
 def induce_context_nt(self,ps,eps):
  buckets=defaultdict(list)
  for p in ps:
   sig=(p.success,p.wrong,p.noexec,shape(p.state_left),shape(p.state_right),len(p.fillers))
   buckets[sig].append(p)
  nts=[]
  for sig,group in buckets.items():
   if len(group)<2:continue
   odd=[i for i in sig[0] if i%2];even=[i for i in sig[0] if i%2==0]
   score=min(len(odd),len(even))/max(1,max(len(odd),len(even))) if odd or even else 0
   if score<.5:continue
   members=tuple((p.cmd_left,p.cmd_right,p.state_left,p.state_right) for p in group[:8])
   fillers=tuple(sorted(set(x for p in group for x in p.fillers)))
   nts.append(ContextNT(members,fillers,sig[0],sig[1],sig[2],sum(p.support for p in group),score))
   self.merges+=len(group)-1
  return sorted(nts,key=lambda n:(n.heldout_score,n.support,-n.bits()),reverse=True)[:self.cap]
 def learn(self,eps):
  ps=self.candidates(eps)
  if self.mode=='executable':self.programs=ps[:self.cap]
  elif self.mode=='substitution':
   g={}
   for p in ps:
    k=(p.fillers,p.state_left,p.state_right);q=g.get(k)
    if q is None or p.bits()<q.bits():g[k]=p
   self.programs=sorted(g.values(),key=lambda p:(len(p.success),p.support),reverse=True)[:self.cap]
  else:
   self.context_nt=self.induce_context_nt(ps,eps)
   covered={m for n in self.context_nt for m in n.members}
   self.programs=[p for p in ps if (p.cmd_left,p.cmd_right,p.state_left,p.state_right) not in covered][:self.cap]
  idx=math.ceil(math.log2(max(2,len(eps))))
  self.description_bits=sum(p.bits()+16 for p in self.programs)+sum(n.bits()+idx*max(1,n.support) for n in self.context_nt)
 def infer(self,before,command):
  cand=[]
  for p in self.programs:
   out,ok,amb,_=self.execute_ctx(before,command,p.cmd_left,p.cmd_right,p.state_left,p.state_right)
   if ok and amb==1:cand.append((cosine(grams(command),grams(p.cmd_left+p.cmd_right))+.03*math.log1p(p.support),out))
  for n in self.context_nt:
   for cl,cr,sl,sr in n.members:
    out,ok,amb,v=self.execute_ctx(before,command,cl,cr,sl,sr)
    if ok and amb==1 and v in n.fillers:
     cand.append((cosine(grams(command),grams(cl+cr))+.05*n.heldout_score+.03*math.log1p(n.support),out));break
  if not cand:return before,False,0
  cand.sort(reverse=True,key=lambda z:z[0])
  if len(cand)>1 and abs(cand[0][0]-cand[1][0])<1e-9:return before,False,len(cand)
  return cand[0][1],True,len(cand)

def build(seed,n,mode):
 rng=random.Random(seed);world={};eps=[];focus=None
 for _ in range(n):
  o=rng.choice(OBJECTS);surf=ALIASES[o] if mode=='rename' else o;world.setdefault(o,{f:rng.choice(VALUES[f]) for f in FIELDS});f=rng.choice(FIELDS);v=rng.choice([x for x in VALUES[f] if x!=world[o][f]]);form=1 if mode=='alternate' else 0;before=state(surf,world[o],form)
  forms=HELD_ORDER[f] if mode=='held_order' else HELD_LEXEME[f] if mode in ('held_lexeme','rename') else OMITTED[f] if mode=='omitted' else COMMANDS[f]
  cmd=rng.choice(forms).format(o=surf,v=v);world[o][f]=v;after=state(surf,world[o],form)
  if mode=='nested':cmd='確認ですが、「'+cmd+'」という依頼です。'
  if mode=='freeform':cmd='前段の説明を踏まえます。\n'+cmd+'\nただし他の記録は維持してください。'
  eps.append(Episode(before,cmd,after,surf,f,v,focus));focus=surf
 return eps

def evaluate(seed,n,mode):
 train=build(seed,n,'seen');test=build(seed+10000,60,mode);res={}
 for m in ('executable','substitution','context_bisim'):
  L=Learner(m);t=time.perf_counter();L.learn(train);tr=time.perf_counter()-t;correct=wrong=commit=recall=reads=0;t=time.perf_counter()
  for e in test:
   pred,did,r=L.infer(e.before,e.command);reads+=r;commit+=did;correct+=int(did and pred==e.after);wrong+=int(did and pred!=e.after)
   recall+=int(any(L.execute(e,p)[1] and L.execute(e,p)[2]==1 and L.execute(e,p)[0]==e.after for p in L.programs) or any(any(L.execute_ctx(e.before,e.command,*mem)[1] and L.execute_ctx(e.before,e.command,*mem)[2]==1 and L.execute_ctx(e.before,e.command,*mem)[0]==e.after for mem in nt.members) for nt in L.context_nt))
  res[m]={'accuracy':correct/len(test),'wrong_commit':wrong/len(test),'commit_rate':commit/len(test),'candidate_execution_recall':recall/len(test),'model_bytes':len(pickle.dumps(L)),'training_seconds':tr,'inference_ms':(time.perf_counter()-t)*1000/len(test),'programs':len(L.programs),'context_nonterminals':len(L.context_nt),'raw_candidates':L.raw,'rejected':L.rejected,'merges':L.merges,'description_bits':L.description_bits,'mean_read_candidates':reads/len(test)}
 return res

def summarize(raw):
 out={}
 for n,runs in raw.items():
  out[n]={}
  for mode in ('seen','held_order','held_lexeme','rename','nested','omitted','alternate','freeform'):
   out[n][mode]={}
   for method in ('executable','substitution','context_bisim'):
    keys=runs[0][mode][method];out[n][mode][method]={k:statistics.mean(r[mode][method][k] for r in runs) for k in keys}
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_021.json');a=ap.parse_args();raw={}
 for n in (48,144,288):
  raw[str(n)]=[{mode:evaluate(seed,n,mode) for mode in ('seen','held_order','held_lexeme','rename','nested','omitted','alternate','freeform')} for seed in (1,7,19)]
 payload={'hypothesis':'Second-Order Context Nonterminals from Derivation-Graph Bisimulation','seeds':[1,7,19],'sizes':[48,144,288],'raw':raw,'summary':summarize(raw),'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'proposal O(NC^2), behavior O(PN), bisimulation quotient O(P), inference O((P+G)L)','hidden_labels_used_by_learner':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
 with open(a.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
 print(json.dumps(payload['summary']['288'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
