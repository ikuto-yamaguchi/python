from __future__ import annotations
import argparse,json,math,pickle,random,re,resource,statistics,time
from collections import Counter
from dataclasses import dataclass,field

OBJECTS=['青箱','赤箱','端末甲','端末乙','試料A','試料B','搬送台','検査票']
ALIASES={'青箱':['青い容器'],'赤箱':['赤い容器'],'端末甲':['第一端末'],'端末乙':['第二端末'],'試料A':['試料アルファ'],'試料B':['試料ベータ'],'搬送台':['運搬台'],'検査票':['確認票']}
FIELDS=['場所','状態','担当']
VALUES={'場所':['棚一','棚二','棚三','棚四'],'状態':['待機','稼働','停止','保留'],'担当':['佐藤','鈴木','田中','高橋']}
STATE_FORMS=[
 lambda rows:' '.join(f'{o}は場所={d["場所"]}、状態={d["状態"]}、担当={d["担当"]}。' for o,d in rows),
 lambda rows:'\n'.join(f'{o}について、担当:{d["担当"]}／場所:{d["場所"]}／状態:{d["状態"]}。' for o,d in rows)]
COMMANDS={'場所':['{o}の場所を{v}へ変更してください。','{o}を{v}へ移します。'], '状態':['{o}の状態を{v}へ更新してください。','{o}を{v}として扱います。'], '担当':['{o}の担当を{v}へ変更してください。','{o}は{v}が受け持ちます。']}
HELD={'場所':['保管先は{v}です。対象は{o}。'],'状態':['{o}を{v}モードへ切り替え。'],'担当':['受け持ちは{v}、対象は{o}。']}

def grams(s):
 s=''.join(s.split());return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))
def cos(a,b):
 dot=sum(v*b.get(k,0) for k,v in a.items());na=math.sqrt(sum(v*v for v in a.values()));nb=math.sqrt(sum(v*v for v in b.values()));return dot/(na*nb+1e-12)
def clauses(s):return [x.strip()+'。' for x in re.split('[。\n]+',s) if x.strip()]
def changed(before,after):
 bs,as_=clauses(before),clauses(after);return [(i,b,a) for i,(b,a) in enumerate(zip(bs,as_)) if b!=a]
def delta(a,b):
 l=0
 while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
 r=0
 while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
 return a[:l],a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)],a[len(a)-r:] if r else ''
def norm(s):return ''.join(s.split())

@dataclass
class Node:
 anchor:Counter
 trajectory:Counter=field(default_factory=Counter)
 contexts:Counter=field(default_factory=Counter)
 support:int=0
 last_clause:str=''

class Surface:
 def __init__(self):self.rows=[]
 def fit(self,seqs):
  for seq in seqs:
   for b,c,a in seq:
    ch=changed(b,a)
    if len(ch)==1:self.rows.append((grams(c),ch[0][1],ch[0][2]))
 def apply(self,b,c):
  if not self.rows:return b
  cg=grams(c);_,o,n=max((cos(cg,g),o,n) for g,o,n in self.rows);return b.replace(o,n,1) if o in b else b

class ObjectNodes:
 def __init__(self,use_temporal=True,use_intervention=True):
  self.use_temporal=use_temporal;self.use_intervention=use_intervention;self.nodes=[];self.raw=0;self.merges=0
 def fit(self,seqs):
  for seq in seqs:
   prev_node=None
   for b,c,a in seq:
    ch=changed(b,a)
    if len(ch)!=1:continue
    _,old,new=ch[0];p,o,n,s=delta(old,new)
    if not o or not n:continue
    self.raw+=1;anchor=grams(p+s);traj=grams(c) if self.use_intervention else Counter();context=grams(''.join(x for x in clauses(b) if x!=old));cand=[]
    for nd in self.nodes:
     score=.55*cos(anchor,nd.anchor)
     if self.use_intervention:score+=.25*cos(traj,nd.trajectory)
     if self.use_temporal and prev_node is nd:score+=.20
     cand.append((score,nd))
    if cand and max(cand,key=lambda x:x[0])[0]>=.46:
     nd=max(cand,key=lambda x:x[0])[1];nd.anchor.update(anchor);nd.trajectory.update(traj);nd.contexts.update(context);nd.support+=1;nd.last_clause=new;self.merges+=1
    else:
     nd=Node(anchor,traj,context,1,new);self.nodes.append(nd)
    prev_node=nd
  self.nodes=sorted(self.nodes,key=lambda x:x.support,reverse=True)[:64]
 def apply(self,b,c):
  cg=grams(c);cand=[]
  for nd in self.nodes:
   for i,cl in enumerate(clauses(b)):
    score=.55*cos(grams(cl),nd.anchor)+(.35*cos(cg,nd.trajectory) if self.use_intervention else 0)+.1*math.log1p(nd.support)
    toks=[x for x in re.split(r'[、。:=／\s]+',c) if 1<=len(x)<=8 and x not in cl]
    if toks:
     v=max(toks,key=len);matches=list(re.finditer(r'(=|:)([^、。／]+)',cl))
     for mm in matches:
      out=cl[:mm.start(2)]+v+cl[mm.end(2):];cs=clauses(b);cs[i]=out;cand.append((score,' '.join(cs)))
  return max(cand,key=lambda x:x[0])[1] if cand else b

def make_sequence(rng,length=4,form=0,held=False,omit=False,rename=False,multi=False,plan=False):
 objs=rng.sample(OBJECTS,3);states={o:{f:rng.choice(VALUES[f]) for f in FIELDS} for o in objs};seq=[]
 for t in range(length):
  o=rng.choice(objs);fld=rng.choice(FIELDS);nv=rng.choice([v for v in VALUES[fld] if v!=states[o][fld]]);shown=lambda x:(ALIASES[x][0] if rename and t>=2 else x)
  before=STATE_FORMS[form]([(shown(x),states[x]) for x in objs]);command=(HELD[fld][0] if held else COMMANDS[fld][t%2]).format(o=shown(o),v=nv)
  if omit and t>0:command=command.replace(shown(o),'それ',1)
  if multi:command='別件の説明です。\n'+command+'\n上記の更新のみ反映。'
  if plan:
   wrong=rng.choice([v for v in VALUES[fld] if v not in (states[o][fld],nv)]);command=COMMANDS[fld][0].format(o=shown(o),v=wrong)+' ただし撤回し、'+command
  states[o][fld]=nv;after=STATE_FORMS[form]([(shown(x),states[x]) for x in objs]);seq.append((before,command,after))
 return seq

def evaluate(seed,n):
 rng=random.Random(seed);train=[make_sequence(rng,4,rng.randrange(2)) for _ in range(n)];models={'surface':Surface(),'temporal_only':ObjectNodes(True,False),'persistence':ObjectNodes(True,True),'no_temporal':ObjectNodes(False,True)}
 for m in models.values():m.fit(train)
 splits={'seen':[make_sequence(rng,4,0) for _ in range(24)],'rename':[make_sequence(rng,4,0,rename=True) for _ in range(24)],'alternate':[make_sequence(rng,4,1) for _ in range(24)],'held':[make_sequence(rng,4,0,held=True) for _ in range(24)],'omission':[make_sequence(rng,4,0,omit=True) for _ in range(24)],'multi':[make_sequence(rng,4,0,multi=True) for _ in range(24)],'plan':[make_sequence(rng,4,0,plan=True) for _ in range(24)]};out={}
 for name,m in models.items():
  md={}
  for sp,seqs in splits.items():
   st=time.perf_counter();ok=tot=0
   for seq in seqs:
    for b,c,a in seq:ok+=norm(m.apply(b,c))==norm(a);tot+=1
   md[sp]={'accuracy':ok/tot,'ms':(time.perf_counter()-st)*1000/tot}
  md['model_bytes']=len(pickle.dumps(m));md['nodes']=len(getattr(m,'nodes',getattr(m,'rows',[])));md['raw']=getattr(m,'raw',0);md['merges']=getattr(m,'merges',0);out[name]=md
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_014.json');args=ap.parse_args();raw={str(n):[evaluate(s,n) for s in (1,7,19)] for n in (12,36,72)};summary={};splits=['seen','rename','alternate','held','omission','multi','plan']
 for n,runs in raw.items():
  summary[n]={}
  for model in runs[0]:
   summary[n][model]={}
   for sp in splits:summary[n][model][sp]={k:statistics.mean(x[model][sp][k] for x in runs) for k in ('accuracy','ms')}
   for k in ('model_bytes','nodes','raw','merges'):summary[n][model][k]=statistics.mean(x[model][k] for x in runs)
 payload={'hypothesis':'Temporal Co-Reference Object Nodes from Intervention Persistence Signatures','seeds':[1,7,19],'sizes':[12,36,72],'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'train O(N T H G), infer O(H C G), H<=64','highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False};open(args.output,'w',encoding='utf8').write(json.dumps(payload,ensure_ascii=False,indent=2));print(json.dumps(summary['72'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
