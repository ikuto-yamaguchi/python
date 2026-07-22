from __future__ import annotations
import argparse,json,math,pickle,random,resource,statistics,time
from collections import Counter,defaultdict

OBJECTS=['青箱','赤箱','端末甲','端末乙','試料A','試料B']
FIELDS=['場所','状態','担当']
VALUES={'場所':['棚一','棚二','棚三'],'状態':['待機','稼働','停止'],'担当':['佐藤','鈴木','田中']}
STATE_FORMS=[
 lambda o,d:f'{o}は場所={d["場所"]}、状態={d["状態"]}、担当={d["担当"]}。',
 lambda o,d:f'{o}について、担当:{d["担当"]}／場所:{d["場所"]}／状態:{d["状態"]}。']
COMMANDS={
 '場所':['{o}の場所を{v}へ変更してください。','{o}を{v}に移してください。'],
 '状態':['{o}の状態を{v}へ更新してください。','{o}を{v}として扱ってください。'],
 '担当':['{o}の担当を{v}へ変更してください。','{o}は{v}が担当します。']}
HELD={'場所':['{o}の所在先は{v}です。'],'状態':['{o}を{v}モードへ。'],'担当':['{o}の受け持ちは{v}です。']}

def ngrams(s):
 s=''.join(s.split()); return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))
def cos(a,b):
 dot=sum(v*b.get(k,0) for k,v in a.items()); na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values())); return dot/(na*nb+1e-12)
def chunks(s):
 out=[]; cur=''
 for ch in s:
  cur+=ch
  if ch in '、。／\n':
   if cur.strip(): out.append(cur.strip())
   cur=''
 if cur.strip(): out.append(cur.strip())
 return out

def diff_chunks(before,after):
 b=chunks(before); a=chunks(after); m=max(len(b),len(a)); return [(b[i] if i<len(b) else'',a[i] if i<len(a) else'') for i in range(m) if (b[i] if i<len(b) else'')!=(a[i] if i<len(a) else'')]

class Whole:
 def __init__(self): self.rows=[]
 def fit(self,eps):
  for b,c,a,*_ in eps:self.rows.append((ngrams(c),b,a))
 def apply(self,b,c):
  if not self.rows:return b
  _,bb,aa=max(((cos(ngrams(c),g),bb,aa) for g,bb,aa in self.rows),key=lambda x:x[0])
  db=diff_chunks(bb,aa)
  out=b
  for x,y in db:
   if x in out:out=out.replace(x,y,1)
  return out

class RelationContrast:
 def __init__(self,use_preservation=True):
  self.use_preservation=use_preservation; self.programs=[]; self.proposals=0
 def fit(self,eps):
  buckets=defaultdict(list)
  for b,c,a,*meta in eps:
   ds=diff_chunks(b,a)
   unchanged=set(chunks(b))&set(chunks(a))
   for old,new in ds:
    common=[c[i:j] for i in range(len(c)) for j in range(i+2,min(len(c),i+18)+1) if c[i:j] in old+new]
    for span in sorted(set(common),key=len,reverse=True)[:8] or ['']:
     key=(old[:max(1,len(old)//3)], new[:max(1,len(new)//3)])
     buckets[key].append((ngrams(c),old,new,unchanged,span))
     self.proposals+=1
  for items in buckets.values():
   if len(items)<2: continue
   diversity=len({(x[1],x[2]) for x in items})
   preserved=sum(bool(x[3]) for x in items)
   if diversity>=2 and (not self.use_preservation or preserved>=2):
    self.programs.append(items[:24])
 def apply(self,b,c):
  cg=ngrams(c); cand=[]
  for prog in self.programs:
   sim=max(cos(cg,x[0]) for x in prog)
   for _,old,new,_,span in prog:
    if old in b: cand.append((sim,b.replace(old,new,1)))
  return max(cand,key=lambda x:x[0])[1] if cand else b

def make_episode(rng,form=0,cmd_form=0,held=False,subject_omit=False,multi=False,plan=False):
 o=rng.choice(OBJECTS); field=rng.choice(FIELDS); d={f:rng.choice(VALUES[f]) for f in FIELDS}; nv=rng.choice([v for v in VALUES[field] if v!=d[field]])
 before=STATE_FORMS[form](o,d); nd=dict(d);nd[field]=nv; after=STATE_FORMS[form](o,nd)
 template=(HELD[field][0] if held else COMMANDS[field][cmd_form%2]); command=template.format(o=o,v=nv)
 if subject_omit: command=command.replace(o,'それ',1)
 if multi: command='前段の説明です。\n'+command+'\n以上を反映します。'
 if plan:
  wrong=rng.choice([v for v in VALUES[field] if v not in (d[field],nv)])
  command=COMMANDS[field][0].format(o=o,v=wrong)+' ただし訂正し、'+command
 return (before,command,after,o,field,nv)

def evaluate(seed,n):
 rng=random.Random(seed); train=[make_episode(rng,rng.randrange(2),rng.randrange(2)) for _ in range(n)]
 models={'whole':Whole(),'contrast':RelationContrast(True),'no_preservation':RelationContrast(False)}
 for m in models.values():m.fit(train)
 splits={
 'seen':[make_episode(rng,0,0) for _ in range(120)],
 'rename':[make_episode(rng,0,1) for _ in range(120)],
 'alternate_state':[make_episode(rng,1,0) for _ in range(120)],
 'held_command':[make_episode(rng,0,0,held=True) for _ in range(120)],
 'subject_omission':[make_episode(rng,0,0,subject_omit=True) for _ in range(120)],
 'multi_paragraph':[make_episode(rng,0,0,multi=True) for _ in range(120)],
 'plan_change':[make_episode(rng,0,0,plan=True) for _ in range(120)],
 }
 out={}
 for name,m in models.items():
  md={}
  for sp,rows in splits.items():
   st=time.perf_counter(); ok=sum(m.apply(b,c)==a for b,c,a,*_ in rows); elapsed=(time.perf_counter()-st)*1000/len(rows)
   md[sp]={'accuracy':ok/len(rows),'ms':elapsed}
  md['model_bytes']=len(pickle.dumps(m)); md['programs']=len(getattr(m,'programs',getattr(m,'rows',[]))); md['proposals']=getattr(m,'proposals',0)
  out[name]=md
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_012.json');args=ap.parse_args()
 raw={str(n):[evaluate(s,n) for s in (1,7,19)] for n in (48,192,512)}
 summary={}
 for n,runs in raw.items():
  summary[n]={}
  for model in runs[0]:
   summary[n][model]={}
   for sp in ['seen','rename','alternate_state','held_command','subject_omission','multi_paragraph','plan_change']:
    summary[n][model][sp]={k:statistics.mean(x[model][sp][k] for x in runs) for k in ('accuracy','ms')}
   for k in ('model_bytes','programs','proposals'):summary[n][model][k]=statistics.mean(x[model][k] for x in runs)
 payload={'hypothesis':'Relation-Selective State Variable Discovery from Preservation Contrasts','seeds':[1,7,19],'sizes':[48,192,512],'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'train O(N L^2), infer O(P G + P L), capped spans/programs','highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
 open(args.output,'w',encoding='utf8').write(json.dumps(payload,ensure_ascii=False,indent=2));print(json.dumps(summary['512'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
