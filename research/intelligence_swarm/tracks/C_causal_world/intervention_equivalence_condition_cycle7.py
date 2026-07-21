"""Cycle C007: intervention-equivalence condition quotient with one-shot effect bridging."""
from __future__ import annotations
import json, random, time, pickle, resource, statistics
from collections import Counter, defaultdict

ENTITIES=['箱舟','白鷺','月影','青磁','珊瑚','若葉','霧島','小町']
VALUES=['棚甲','棚乙','棚丙','棚丁','区画北','区画南']
ACTION_CTX=['通路は空いている','扉は開いている','移動を妨げる物はない']
BLOCK_CTX=['通路が塞がっている','扉は閉じている','移動経路を使えない']
HELD_ACTION=['進路に障害は見当たらない','入口を通過できる']
HELD_BLOCK=['進路が遮断されている','入口を通過できない']
CMD=['{e}を{v}へ移してください','{v}へ{e}を運んでください','{e}の置き場を{v}に変更してください']
HELD_CMD=['{e}を最終的に{v}へ回してください','行き先は{v}、対象は{e}です']

def grams(s):
 c=Counter()
 for n in (2,3):
  for i in range(max(0,len(s)-n+1)): c[s[i:i+n]]+=1
 return c

def cos(a,b):
 d=sum(v*b.get(k,0) for k,v in a.items()); na=sum(v*v for v in a.values())**.5; nb=sum(v*v for v in b.values())**.5
 return d/(na*nb+1e-9)

def episode(rng, ctx, cmd_templates=CMD):
 e=rng.choice(ENTITIES); old,new=rng.sample(VALUES,2); command=rng.choice(cmd_templates).format(e=e,v=new)
 before=f'{e}の現在位置は{old}です。{ctx}。'; blocked=ctx in BLOCK_CTX or ctx in HELD_BLOCK
 after=before if blocked else f'{e}の現在位置は{new}です。{ctx}。'
 return dict(e=e,old=old,new=new,ctx=ctx,command=command,before=before,after=after,branch='noop' if blocked else 'action')

def strip_bindings(text,row):
 for x in (row['e'],row['old'],row['new']): text=text.replace(x,'<X>')
 return text

class Prototype:
 def __init__(self): self.rows=[]
 def fit(self,rows): self.rows=list(rows); return self
 def predict(self,row):
  q=grams(strip_bindings(row['before']+' '+row['command'],row)); best=(-1,None)
  for r in self.rows[:64]:
   s=cos(q,grams(strip_bindings(r['before']+' '+r['command'],r)))
   if s>best[0]: best=(s,r['branch'])
  return best[1]

class EffectQuotient:
 def __init__(self): self.nodes=defaultdict(Counter); self.bridge={}
 def fit(self,rows):
  for r in rows: self.nodes[r['branch']][strip_bindings(r['ctx'],r)]+=1
  return self
 def bridge_once(self,row): self.bridge[strip_bindings(row['ctx'],row)]=row['branch']
 def predict(self,row):
  ctx=strip_bindings(row['ctx'],row)
  if ctx in self.bridge: return self.bridge[ctx]
  q=grams(ctx); scores=[]
  for branch,patterns in self.nodes.items(): scores.append((max((cos(q,grams(p)) for p in patterns),default=0),branch))
  scores.sort(reverse=True)
  return scores[0][1] if scores and (len(scores)==1 or scores[0][0]-scores[1][0]>.03) else None

def run(seed,n):
 rng=random.Random(seed); train=[episode(rng,rng.choice(ACTION_CTX+BLOCK_CTX)) for _ in range(n)]
 proto=Prototype().fit(train); quot=EffectQuotient().fit(train)
 tests={'seen':[episode(rng,rng.choice(ACTION_CTX+BLOCK_CTX)) for _ in range(120)],'held_context':[episode(rng,rng.choice(HELD_ACTION+HELD_BLOCK)) for _ in range(120)],'held_command':[episode(rng,rng.choice(ACTION_CTX+BLOCK_CTX),HELD_CMD) for _ in range(120)],'both_held':[episode(rng,rng.choice(HELD_ACTION+HELD_BLOCK),HELD_CMD) for _ in range(120)],'subject_omission':[episode(rng,rng.choice(ACTION_CTX+BLOCK_CTX)) for _ in range(120)],'multi_paragraph':[episode(rng,rng.choice(ACTION_CTX+BLOCK_CTX)) for _ in range(120)]}
 for r in tests['subject_omission']: r['command']=r['command'].replace(r['e'],'それ')
 for r in tests['multi_paragraph']: r['before']+='\nなお、直前の予定は変更されていません。'
 bridge_model=EffectQuotient().fit(train)
 for ctx in HELD_ACTION+HELD_BLOCK: bridge_model.bridge_once(episode(rng,ctx))
 out={}
 for name,rows in tests.items():
  out[name]={}
  for label,m in [('prototype',proto),('quotient_zero',quot),('quotient_bridge',bridge_model)]:
   t=time.perf_counter(); ps=[m.predict(r) for r in rows]; elapsed=(time.perf_counter()-t)*1000/len(rows)
   out[name][label]={'accuracy':sum(p==r['branch'] for p,r in zip(ps,rows))/len(rows),'abstention':sum(p is None for p in ps)/len(rows),'ms':elapsed}
 out['resources']={'prototype_bytes':len(pickle.dumps(proto)),'quotient_bytes':len(pickle.dumps(quot)),'bridge_bytes':len(pickle.dumps(bridge_model)),'condition_nodes':2,'surface_residues':sum(len(v) for v in quot.nodes.values()),'candidate_reads':2}
 return out

raw={str(n):[run(s,n) for s in (1,7,19)] for n in (32,128,512)}; summary={}
for n,runs in raw.items():
 summary[n]={}
 for split in ('seen','held_context','held_command','both_held','subject_omission','multi_paragraph'):
  summary[n][split]={}
  for model in ('prototype','quotient_zero','quotient_bridge'):
   summary[n][split][model]={k:statistics.mean(x[split][model][k] for x in runs) for k in ('accuracy','abstention','ms')}
 for k in runs[0]['resources']: summary[n][k]=statistics.mean(x['resources'][k] for x in runs)
payload={'hypothesis':'Intervention-Equivalence Condition Quotient with One-Shot Effect Bridging','seeds':[1,7,19],'train_sizes':[32,128,512],'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'train O(NG), inference O(CG), C=2 branch condition nodes','free_japanese_integrated_gate':0.0,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
with open('results_cycle_007.json','w',encoding='utf-8') as f: json.dump(payload,f,ensure_ascii=False,indent=2)
print(json.dumps(summary['512'],ensure_ascii=False,indent=2))
