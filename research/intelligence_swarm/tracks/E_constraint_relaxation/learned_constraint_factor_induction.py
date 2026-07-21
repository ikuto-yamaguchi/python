import random,time,pickle,resource,json,statistics,re,difflib
from collections import Counter,defaultdict
ENTS=['アルファ','ベータ','ガンマ','デルタ','ミライ','カナタ'];LOCS=['棚A','棚B','棚C','棚D','机','入口']
CMDS=['{e}を{d}へ移してください。','{d}へ{e}を運んで。','{e}の置き場を{d}に変えて。'];UNSEEN='{e}を今いる所から{d}まで持っていって。';STATE=['{e}は{o}にあります。','現在、{e}の場所は{o}です。']
def grams(s,n=3):return Counter(s[i:i+n] for i in range(max(0,len(s)-n+1)))
def cos(a,b):
 d=(sum(v*v for v in a.values())*sum(v*v for v in b.values()))**.5
 return 0 if not d else sum(v*b.get(k,0) for k,v in a.items())/d
def prog(b,a):
 out=[]
 for tag,i1,i2,j1,j2 in difflib.SequenceMatcher(None,b,a,autojunk=False).get_opcodes():
  if tag!='equal':out.append((b[i1:i2],a[j1:j2]))
 return tuple(out)
def apply(b,p):
 s=b
 for old,new in p:
  if old in s:s=s.replace(old,new,1)
  else:return None
 return s
def gen(seed,n,contrasts=True):
 r=random.Random(seed);rows=[]
 for i in range(n):
  e=r.choice(ENTS[:4]);o,d=r.sample(LOCS[:4],2);sf=i%2;cf=i%3;b=STATE[sf].format(e=e,o=o);c=CMDS[cf].format(e=e,d=d);a=STATE[sf].format(e=e,o=d);rows.append((b,c,a,1))
  if contrasts and i%4==0:rows.append((b,c,b,0))
 return rows
class Model:
 def __init__(self,learned=True,k=6):self.learned=learned;self.k=k
 def fit(self,rows):
  self.items=[];groups=defaultdict(list)
  for b,c,a,y in rows:
   p=prog(b,a);sig=tuple((len(x),len(z)) for x,z in p);self.items.append((grams(c),p,c,b,a,y,sig));groups[sig].append((b,c,a,y,p))
  self.factor={}
  for sig,xs in groups.items():
   change=[x for x in xs if x[3]==1];no=[x for x in xs if x[3]==0];identity=[];consistency=[];inverse=[]
   for b,c,a,y,p in change:
    eb=set(re.findall(r'[ァ-ヶ一-龥A-Z0-9]+',b));ea=set(re.findall(r'[ァ-ヶ一-龥A-Z0-9]+',a));identity.append(len(eb&ea)/max(1,len(eb)));consistency.append(1.0 if apply(b,p)==a else 0.0);inverse.append(1.0 if apply(a,tuple((n,o) for o,n in reversed(p)))==b else 0.0)
   self.factor[sig]={'identity':statistics.mean(identity) if identity else 0,'consistency':statistics.mean(consistency) if consistency else 0,'inverse':statistics.mean(inverse) if inverse else 0,'contrast':len(change)/(len(change)+len(no)+1e-9)}
 def cand(self,c):
  q=grams(c);z=sorted(((cos(q,g),p,sig,t) for g,p,t,b,a,y,sig in self.items),reverse=True,key=lambda x:x[0]);out=[]
  for x in z:
   if x[1] not in [y[1] for y in out]:out.append(x)
   if len(out)>=self.k:break
  return out
 def energy(self,b,c,p,sim,sig):
  ns=apply(b,p)
  if ns is None:return 99
  if not self.learned:return (1-sim)+(0.8 if ns==b else 0)+0.25*abs(len(ns)-len(b))/max(1,len(b))
  f=self.factor.get(sig,{'identity':0,'consistency':0,'inverse':0,'contrast':0})
  return (1-sim)+1.2*(1-f['identity'])+1.2*(1-f['consistency'])+0.8*(1-f['inverse'])+0.8*(1-f['contrast'])
 def predict(self,b,cmds,max_iter=10):
  cs=[self.cand(c) for c in cmds]
  if any(not x for x in cs):return None,0,0,0,0
  idx=[0]*len(cs);prev=1e9
  def E(sel):
   s=b;e=0
   for t,j in enumerate(sel):
    sim,p,sig,_=cs[t][j];e+=self.energy(s,cmds[t],p,sim,sig);s=apply(s,p)
    if s is None:return 999,None
   return e,s
  for it in range(1,max_iter+1):
   ch=False
   for t in range(len(cs)):
    best=(999,idx[t])
    for j in range(len(cs[t])):
     z=idx[:];z[t]=j;e,_=E(z)
     if e<best[0]-1e-12:best=(e,j)
    if best[1]!=idx[t]:idx[t]=best[1];ch=True
   e,s=E(idx)
   if not ch or abs(prev-e)<1e-9:break
   prev=e
  alt=999
  for t in range(len(cs)):
   for j in range(len(cs[t])):
    if j==idx[t]:continue
    z=idx[:];z[t]=j;alt=min(alt,E(z)[0])
  return s,(alt-e if alt<999 else 0),it,sum(len(x) for x in cs),e
 def bytes(self):return len(pickle.dumps((self.items,self.factor)))
def eval_one(seed,n,learned):
 m=Model(learned);t=time.perf_counter();m.fit(gen(seed,n));tr=time.perf_counter()-t;r=random.Random(seed+99);plan=[];unseen=[];ab=[];lat=[];its=[];act=[];conv=[]
 for i in range(120):
  e=r.choice(ENTS[4:]);o,d1,d2=r.sample(LOCS[:4],3);sf=i%2;b=STATE[sf].format(e=e,o=o);cmds=[CMDS[i%3].format(e=e,d=d1),CMDS[(i+1)%3].format(e=e,d=d2)];target=STATE[sf].format(e=e,o=d2);st=time.perf_counter();p,ma,it,a,en=m.predict(b,cmds);lat.append((time.perf_counter()-st)*1000);its.append(it);act.append(a);conv.append(p is not None);plan.append(p==target)
 for i in range(80):
  e=r.choice(ENTS[4:]);o,d=r.sample(LOCS[:4],2);sf=i%2;b=STATE[sf].format(e=e,o=o);c=UNSEEN.format(e=e,d=d);a=STATE[sf].format(e=e,o=d);p,ma,_,_,_=m.predict(b,[c]);unseen.append(p==a)
 for i in range(80):
  e=r.choice(ENTS[4:]);o,d=r.sample(LOCS[:4],2);sf=i%2;b=STATE[sf].format(e=e,o=o);c=CMDS[0].format(e=e,d=d);p,ma,_,_,_=m.predict(b,[c]);ab.append(ma<0.08)
 return {'method':'learned_factors' if learned else 'hand_surface','seed':seed,'n':n,'plan':statistics.mean(plan),'unseen':statistics.mean(unseen),'confound_abstain':statistics.mean(ab),'model_bytes':m.bytes(),'train_s':tr,'infer_ms':statistics.mean(lat),'iterations':statistics.mean(its),'active':statistics.mean(act),'convergence':statistics.mean(conv),'factor_count':len(m.factor),'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
def run(output='results_cycle_002.json'):
 rows=[eval_one(s,n,l) for n in (48,192,768) for s in (1,7,19) for l in (False,True)];agg={}
 for n in (48,192,768):
  agg[str(n)]={}
  for method in ('hand_surface','learned_factors'):
   rr=[x for x in rows if x['n']==n and x['method']==method];agg[str(n)][method]={k:statistics.mean(x[k] for x in rr) for k in rr[0] if k not in ('method','seed','n')}
 out={'hypothesis':'Self-supervised local factor reliabilities induced from reconstruction, identity preservation, inverse consistency and no-action contrast can replace hand-written surface constraints in sparse relaxation.','aggregate':agg,'runs':rows,'claim':{'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}}
 open(output,'w').write(json.dumps(out,ensure_ascii=False,indent=2));return out
if __name__=='__main__':print(json.dumps(run()['aggregate']['768'],ensure_ascii=False,indent=2))
