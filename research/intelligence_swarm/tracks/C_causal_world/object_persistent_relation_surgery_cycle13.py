from __future__ import annotations
import argparse,json,math,pickle,random,resource,statistics,time,re
from collections import Counter,defaultdict
from dataclasses import dataclass

OBJECTS=['青箱','赤箱','端末甲','端末乙','試料A','試料B','搬送台','検査票']
FIELDS=['場所','状態','担当']
VALUES={'場所':['棚一','棚二','棚三','棚四'],'状態':['待機','稼働','停止','保留'],'担当':['佐藤','鈴木','田中','高橋']}
STATE_FORMS=[
 lambda rows:' '.join(f'{o}は場所={d["場所"]}、状態={d["状態"]}、担当={d["担当"]}。' for o,d in rows),
 lambda rows:'\n'.join(f'{o}について、担当:{d["担当"]}／場所:{d["場所"]}／状態:{d["状態"]}。' for o,d in rows),
]
COMMANDS={
 '場所':['{o}の場所を{v}へ変更してください。','{o}を{v}に移してください。'],
 '状態':['{o}の状態を{v}へ更新してください。','{o}を{v}として扱ってください。'],
 '担当':['{o}の担当を{v}へ変更してください。','{o}は{v}が担当します。']}
HELD={
 '場所':['{o}の所在先を{v}にしてください。'],
 '状態':['{o}を{v}モードへ切り替えてください。'],
 '担当':['{o}の受け持ちを{v}へ。']}

def grams(s):
 s=''.join(s.split());return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))
def cos(a,b):
 dot=sum(v*b.get(k,0) for k,v in a.items());na=math.sqrt(sum(v*v for v in a.values()));nb=math.sqrt(sum(v*v for v in b.values()));return dot/(na*nb+1e-12)
def clauses(s):return [x.strip()+'。' for x in re.split('[。\n]+',s) if x.strip()]
def common_prefix(a,b):
 i=0
 while i<min(len(a),len(b)) and a[i]==b[i]:i+=1
 return a[:i]
def common_suffix(a,b):
 i=0
 while i<min(len(a),len(b)) and a[-1-i]==b[-1-i]:i+=1
 return a[len(a)-i:] if i else ''
def changed_pairs(before,after):
 bs,as_=clauses(before),clauses(after);return [(i,b,a) for i,(b,a) in enumerate(zip(bs,as_)) if b!=a]
def delta(old,new):
 p=common_prefix(old,new);s=common_suffix(old[len(p):],new[len(p):]);oe=len(old)-len(s) if s else len(old);ne=len(new)-len(s) if s else len(new);return p,old[len(p):oe],new[len(p):ne],s

@dataclass
class Edge:
 cmd:Counter
 prefix:str
 old:str
 new:str
 suffix:str
 support:int=1
 swap_safe:int=0
 inverse_safe:int=0
 order_safe:int=0

class SurfaceChunk:
 def __init__(self):self.rows=[]
 def fit(self,eps):
  for b,c,a,*_ in eps:
   for _,old,new in changed_pairs(b,a):self.rows.append((grams(c),old,new))
 def apply(self,b,c):
  if not self.rows:return b
  cg=grams(c);_,old,new=max(((cos(cg,g),o,n) for g,o,n in self.rows),key=lambda x:x[0]);return b.replace(old,new,1) if old in b else b

class ObjectPersistentEdges:
 def __init__(self,use_surgery=True):self.use_surgery=use_surgery;self.edges=[];self.raw=0;self.rejected=0
 def fit(self,eps):
  buckets=defaultdict(list)
  for b,c,a,*_ in eps:
   pairs=changed_pairs(b,a)
   if len(pairs)!=1:continue
   idx,old_clause,new_clause=pairs[0];p,o,n,s=delta(old_clause,new_clause)
   if not o or not n:continue
   self.raw+=1;key=(p[-10:],s[:10],len(o)//2,len(n)//2);buckets[key].append((b,c,a,idx,Edge(grams(c),p,o,n,s)))
  for items in buckets.values():
   if len(items)<2:continue
   for b,c,a,idx,e in items:
    e.support=len(items);bs=clauses(b);target=bs[idx]
    for j in range(len(bs)):
     if j==idx:continue
     swapped=list(bs);swapped[idx],swapped[j]=swapped[j],swapped[idx];matches=sum(1 for cl in swapped if cl.startswith(e.prefix) and cl.endswith(e.suffix) and e.old in cl);e.swap_safe+=int(matches<=1 and e.old not in swapped[idx])
    forward=target.replace(e.old,e.new,1) if e.old in target else target;backward=forward.replace(e.new,e.old,1) if e.new in forward else forward;e.inverse_safe=int(backward==target and forward!=target)
    twice=forward.replace(e.old,e.new,1) if e.old in forward else forward;e.order_safe=int(twice==forward)
    possible=max(1,len(bs)-1);keep=(e.swap_safe==possible and e.inverse_safe and e.order_safe) if self.use_surgery else True
    if keep:self.edges.append(e)
    else:self.rejected+=1
  q={}
  for e in self.edges:
   k=(e.prefix,e.old,e.new,e.suffix)
   if k not in q or e.support>q[k].support:q[k]=e
  self.edges=sorted(q.values(),key=lambda x:(x.support,x.inverse_safe,x.swap_safe),reverse=True)[:64]
 def apply(self,b,c):
  cg=grams(c);cand=[]
  for e in self.edges:
   for i,cl in enumerate(clauses(b)):
    if cl.startswith(e.prefix) and cl.endswith(e.suffix) and e.old in cl:
     score=cos(cg,e.cmd)+0.03*math.log1p(e.support);cs=clauses(b);cs[i]=cl.replace(e.old,e.new,1);cand.append((score,' '.join(cs)))
  return max(cand,key=lambda x:x[0])[1] if cand else b

def normalize(s):return ''.join(s.split())
def make_episode(rng,form=0,cmd_form=0,held=False,omit=False,multi=False,plan=False,nobj=2,swap_order=False):
 objs=rng.sample(OBJECTS,nobj);rows=[(o,{f:rng.choice(VALUES[f]) for f in FIELDS}) for o in objs];field=rng.choice(FIELDS);ti=rng.randrange(nobj);o,d=rows[ti];nv=rng.choice([v for v in VALUES[field] if v!=d[field]])
 before=STATE_FORMS[form](rows);after_rows=[(x,dict(y)) for x,y in rows];after_rows[ti][1][field]=nv;after=STATE_FORMS[form](after_rows);template=HELD[field][0] if held else COMMANDS[field][cmd_form%2];command=template.format(o=o,v=nv)
 if omit:command=command.replace(o,'それ',1)
 if multi:command='前段には別件の説明があります。\n'+command+'\nこの操作だけを反映します。'
 if plan:
  wrong=rng.choice([v for v in VALUES[field] if v not in (d[field],nv)]);command=COMMANDS[field][0].format(o=o,v=wrong)+' ただし撤回し、'+command
 if swap_order:command='実行順を逆に考えます。 '+command
 return before,command,after,o,field,nv

def evaluate(seed,n):
 rng=random.Random(seed);train=[make_episode(rng,rng.randrange(2),rng.randrange(2),nobj=rng.choice([2,3])) for _ in range(n)];models={'surface':SurfaceChunk(),'edge_no_surgery':ObjectPersistentEdges(False),'edge_surgery':ObjectPersistentEdges(True)}
 for m in models.values():m.fit(train)
 splits={'seen':[make_episode(rng,0,0,nobj=3) for _ in range(120)],'rename_order':[make_episode(rng,0,1,nobj=3) for _ in range(120)],'alternate_state':[make_episode(rng,1,0,nobj=3) for _ in range(120)],'held_command':[make_episode(rng,0,0,held=True,nobj=3) for _ in range(120)],'subject_omission':[make_episode(rng,0,0,omit=True,nobj=3) for _ in range(120)],'multi_paragraph':[make_episode(rng,0,0,multi=True,nobj=3) for _ in range(120)],'plan_change':[make_episode(rng,0,0,plan=True,nobj=3) for _ in range(120)],'order_counterfactual':[make_episode(rng,0,0,swap_order=True,nobj=3) for _ in range(120)]}
 out={}
 for name,m in models.items():
  md={}
  for sp,rows in splits.items():
   st=time.perf_counter();ok=sum(normalize(m.apply(b,c))==normalize(a) for b,c,a,*_ in rows);md[sp]={'accuracy':ok/len(rows),'ms':(time.perf_counter()-st)*1000/len(rows)}
  md['model_bytes']=len(pickle.dumps(m));md['edges']=len(getattr(m,'edges',getattr(m,'rows',[])));md['raw']=getattr(m,'raw',0);md['rejected']=getattr(m,'rejected',0);out[name]=md
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_013.json');args=ap.parse_args();raw={str(n):[evaluate(s,n) for s in (1,7,19)] for n in (48,192,512)};summary={};splits=['seen','rename_order','alternate_state','held_command','subject_omission','multi_paragraph','plan_change','order_counterfactual']
 for n,runs in raw.items():
  summary[n]={}
  for model in runs[0]:
   summary[n][model]={}
   for sp in splits:summary[n][model][sp]={k:statistics.mean(x[model][sp][k] for x in runs) for k in ('accuracy','ms')}
   for k in ('model_bytes','edges','raw','rejected'):summary[n][model][k]=statistics.mean(x[model][k] for x in runs)
 payload={'hypothesis':'Identity-Conservation Causal Edge Discovery by Object-Swap Surgery','seeds':[1,7,19],'sizes':[48,192,512],'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'train O(N C^2), infer O(E C G), E<=64','highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False};open(args.output,'w',encoding='utf8').write(json.dumps(payload,ensure_ascii=False,indent=2));print(json.dumps(summary['512'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
