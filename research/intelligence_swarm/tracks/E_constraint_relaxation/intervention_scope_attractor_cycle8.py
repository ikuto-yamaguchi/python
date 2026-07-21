from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
import argparse,json,math,pickle,random,resource,statistics,time
ENTITIES=['荷物甲','荷物乙','試料赤','試料青','箱春','箱秋']; VALUES=['棚A','棚B','棚C','室内','廊下','机上']
CMD_SEEN=['{e}を{v}へ移してください。','{e}の置き場所を{v}に変更してください。','{v}へ{e}を動かしてください。']
CMD_HELD=['{e}は{v}に収めてください。','{e}を{v}側へ回してください。']
ALLOW=['通路は利用できます。','移動を妨げるものはありません。','作業は許可されています。']; BLOCK=['通路が塞がれています。','移動は現在許可されていません。','固定具が外れていません。']
HALLOW=['経路に支障はありません。','作業を進めても問題ありません。']; HBLOCK=['経路を通せない状態です。','今は作業を進められません。']
REV=['先ほどの指示は取り消します。','計画を変更します。','前の依頼を訂正します。']; FILL=['担当者は記録を確認しました。','周囲は静かです。']
def grams(s):
 s=''.join(s.split()); return frozenset(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))
def sim(a,b): return len(a&b)/(math.sqrt(len(a)*len(b))+1e-9) if a and b else 0.0
def sent(t): return [x.strip()+'。' for x in t.replace('\n','').split('。') if x.strip()]
def state(e,v): return f'{e}の現在位置は{v}です。'
def make(r,split):
 e=r.choice(ENTITIES); old,new=r.sample(VALUES,2); allow=r.random()<.5
 cf=CMD_HELD if 'held_command' in split else CMD_SEEN; af=HALLOW if 'held_context' in split else ALLOW; bf=HBLOCK if 'held_context' in split else BLOCK
 cmd=r.choice(cf).format(e=e,v=new); cond=r.choice(af if allow else bf); idx=1; chunks=[cond,cmd]
 if split=='nested': chunks=[FILL[0],f'{cond[:-1]}場合に限り、{cmd}']; idx=1
 elif split=='multi_paragraph': chunks=[cond,r.choice(FILL),cmd]; idx=2
 elif split=='plan_change':
  alt=r.choice([v for v in VALUES if v not in (old,new)]); chunks=[cond,r.choice(CMD_SEEN).format(e=e,v=alt),r.choice(REV),cmd]; idx=3
 elif split=='counterfactual': chunks=[cond,cmd,'もし条件が反対なら結果も反対になるか検討します。']; idx=1
 return {'text':'\n'.join(chunks),'before':state(e,old),'after':state(e,new if allow else old),'entity':e,'target':new,'idx':idx,'split':split,'branch':int(allow)}
@dataclass(frozen=True)
class C: ci:int; a:int; z:int; b:int; rev:int; feats:tuple
class M:
 def __init__(self,learn): self.learn=learn; self.cv=[]; self.sv={0:[],1:[]}; self.w=[1.,1.,.15,0.,.05]
 def fit(self,eps):
  for ep in eps:
   ss=sent(ep['text']); self.cv.extend(grams(x) for x in ss)
   for i in range(len(ss)):
    for z in range(i,min(len(ss),i+2)): self.sv[ep['branch']].append(grams(' '.join(ss[i:z+1])))
  self.cv=self.cv[-20:]; self.sv={b:self.sv[b][-20:] for b in (0,1)}
  if self.learn:
   for ep in eps:
    cs=self.propose(ep)
    if not cs: continue
    free=max(cs,key=lambda c:self.score(c)); cl=[c for c in cs if c.b==ep['branch']]
    if not cl: continue
    pert=max(cl,key=lambda c:self.score(c))
    for i in range(5): self.w[i]=max(-2,min(2,self.w[i]+.08*(pert.feats[i]-free.feats[i])))
  return self
 def mx(self,g,vs): return max((sim(g,v) for v in vs),default=0.)
 def propose(self,ep):
  ss=sent(ep['text']); c=[]; scores=[self.mx(grams(x),self.cv) for x in ss]
  cis=sorted(range(len(ss)),key=lambda i:scores[i],reverse=True)[:min(3,len(ss))]
  hasrev=any(any(m[:-1] in x for m in REV) for x in ss)
  for ci in cis:
   for a in range(max(0,ci-1),ci+1):
    for z in range(ci,min(len(ss)-1,ci+1)+1):
     sg=grams(' '.join(ss[a:z+1])); bs=[self.mx(sg,self.sv[b]) for b in (0,1)]
     if abs(bs[1]-bs[0])<.015: continue
     cg=grams(ss[ci]); cmd=self.mx(cg,self.cv)
     for b in (0,1):
      for rv in (0,1):
       rev=1. if hasrev and rv==1 and ci>=len(ss)-1 else (-1. if hasrev and rv==0 else 0.)
       f=(cmd,bs[b]-bs[1-b],1.,rev,-(z-a)/max(1,len(ss)))
       c.append(C(ci,a,z,b,rv,f))
  return sorted(c,key=lambda x:self.score(x),reverse=True)[:16]
 def score(self,c): return sum(a*b for a,b in zip(self.w,c.feats))
 def infer(self,ep):
  cs=self.propose(ep)
  if not cs:return None,{'reason':'collapse','n':0,'sweeps':0,'margin':0.}
  active=cs; prev=None; sw=0
  for sw in range(1,5):
   active=sorted(active,key=self.score,reverse=True); sig=(active[0].ci,active[0].a,active[0].z,active[0].b,active[0].rev)
   if sig==prev:break
   prev=sig; active=active[:max(2,(len(active)+1)//2)]
  cs=sorted(cs,key=self.score,reverse=True); margin=self.score(cs[0])-self.score(cs[1]) if len(cs)>1 else 1.
  if margin<.01:return None,{'reason':'flat','n':len(cs),'sweeps':sw,'margin':margin}
  return cs[0],{'reason':'ok','n':len(cs),'sweeps':sw,'margin':margin}
def ok(ep,c):
 if c is None:return False
 ss=sent(ep['text']); cmdok=(c.ci==ep['idx']) if ep['split']=='plan_change' else (ep['entity'] in ss[c.ci] and ep['target'] in ss[c.ci])
 return cmdok and c.b==ep['branch']
def ev(seed,n):
 r=random.Random(seed); tr=[make(r,r.choice(['seen','seen','multi_paragraph','plan_change'])) for _ in range(n)]; out={}
 for name,l in [('fixed',0),('learned',1)]:
  t=time.perf_counter(); m=M(l).fit(tr); train=time.perf_counter()-t; rr={}
  for sp in ['seen','held_context','held_command','held_context_held_command','nested','multi_paragraph','plan_change','counterfactual']:
   rows=[make(r,sp) for _ in range(30)]; vals=[]; rec=[]; abst=[]; mar=[]; swe=[]; nn=[]; st=time.perf_counter()
   for e in rows:
    cs=m.propose(e); rec.append(any(ok(e,c) for c in cs)); p,meta=m.infer(e); vals.append(ok(e,p)); abst.append(p is None); mar.append(meta['margin']); swe.append(meta['sweeps']); nn.append(meta['n'])
   rr[sp]={'accuracy':statistics.mean(vals),'candidate_recall':statistics.mean(rec),'abstention':statistics.mean(abst),'margin':statistics.mean(mar),'sweeps':statistics.mean(swe),'active_candidates':statistics.mean(nn),'ms':(time.perf_counter()-st)*1000/len(rows)}
  rr['model_bytes']=len(pickle.dumps(m)); rr['training_seconds']=train; rr['weights']=m.w; out[name]=rr
 return out
def summary(raw):
 z={}
 for n,runs in raw.items():
  z[n]={}
  for meth in ['fixed','learned']:
   d={}
   for sp in ['seen','held_context','held_command','held_context_held_command','nested','multi_paragraph','plan_change','counterfactual']:
    d[sp]={k:statistics.mean(x[meth][sp][k] for x in runs) for k in runs[0][meth][sp]}
   d['model_bytes']=statistics.mean(x[meth]['model_bytes'] for x in runs); d['training_seconds']=statistics.mean(x[meth]['training_seconds'] for x in runs); d['weights']=[statistics.mean(x[meth]['weights'][i] for x in runs) for i in range(5)]; z[n][meth]=d
 return z
def main():
 a=argparse.ArgumentParser(); a.add_argument('--output',default='results_cycle_008.json'); q=a.parse_args(); raw={str(n):[ev(s,n) for s in (1,7,19)] for n in (24,48,96)}; p={'hypothesis':'Intervention-Discriminative Scope Attractors with Learned Local Factors','seeds':[1,7,19],'train_sizes':[24,48,96],'raw':raw,'summary':summary(raw),'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'complexity':'O(HVG)+O(SH), H<=16,S<=4','highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}; json.dump(p,open(q.output,'w',encoding='utf8'),ensure_ascii=False,indent=2); print(json.dumps(p['summary']['96'],ensure_ascii=False,indent=2)); print('rss',p['peak_rss_kib_runtime_included'])
if __name__=='__main__':main()
