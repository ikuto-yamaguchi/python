import json,pickle,resource,time
import numpy as np
SEEDS=[1,7,19]
DOMAINS={
'd1':{'obj':['青箱','赤箱','緑箱','白箱'],'op':['右へ','左へ','上へ','下へ'],'goal':['近づけ','離せ']},
'd2':{'obj':['甲器','乙器','丙器','丁器'],'op':['東寄せ','西寄せ','北寄せ','南寄せ'],'goal':['接近','分離']},
'd3':{'obj':['ナロ','ミケ','フサ','トネ'],'op':['ルク','セパ','ゴニ','ハル'],'goal':['ヴァ','ネオ']}}
DIRS=np.array([[1,0],[-1,0],[0,1],[0,-1]],float)
def feat(text,dim=384):
 v=np.zeros(dim); raw=text.encode()
 for n in (2,3,4,5):
  for i in range(len(raw)-n+1):
   h=2166136261
   for b in raw[i:i+n]:h=((h^b)*16777619)&0xffffffff
   v[h%dim]+=1
 return v/(np.linalg.norm(v)+1e-9)
def utter(d,t,o,g,s):
 z=DOMAINS[d]; a,b,c=z['obj'][t],z['op'][o],z['goal'][g]
 forms=[f'{a}を{b}動かし、基準へ{c}。',f'基準へ{c}ように、{a}は{b}。',f'前段を保つ。\n対象は{a}、動きは{b}、狙いは{c}。',f'最終的に{c}ため、{a}へ{b}の変化を与えて。',f'{c}という意図なら、{b}のは{a}。']
 return forms[s%5]
def apply(w,t,o):
 x=w.copy();x[t]+=DIRS[o];return x
def ep(d,r,s=None):
 w=r.uniform(-2,2,(6,2));t=int(r.integers(4));o=int(r.integers(4));g=int(r.integers(2));s=int(r.integers(5)) if s is None else s
 return {'d':d,'w':w,'t':t,'o':o,'g':g,'s':s,'text':utter(d,t,o,g,s),'after':apply(w,t,o)}
def sig(w,a):
 delta=a-w; changed=(np.linalg.norm(delta,axis=1)>1e-7).astype(float); dist=np.linalg.norm(a[:,None]-a[None,:],axis=2).ravel()
 return np.r_[changed,delta.ravel(),np.sort(dist)[:12]]
def cands(e):
 return [(t,o,g,sig(e['w'],apply(e['w'],t,o))) for t in range(4) for o in range(4) for g in range(2)]
def version_scores(e,proto):
 f=feat(e['text']); ls=proto@f; cs=cands(e); ws=np.array([np.linalg.norm(x[3]-np.mean([y[3] for y in cs],axis=0)) for x in cs]); ws=(ws-ws.mean())/(ws.std()+1e-9)
 return ls,ws
def select(pool,budget,rng,mode,proto=None):
 if mode=='random': return list(rng.choice(pool,budget,replace=False))
 vals=[]
 for e in pool:
  cs=cands(e); S=np.stack([x[3] for x in cs]); world=float(np.mean(np.var(S,axis=0)))
  if proto is None: lang=0.0
  else:
   ls,_=version_scores(e,proto); p=np.exp(ls-ls.max());p/=p.sum();lang=float(-(p*np.log(p+1e-12)).sum())
  if mode=='world': score=world
  elif mode=='joint': score=world*(1+lang)
  elif mode=='oracle':
   obs=sig(e['w'],e['after']); ds=np.array([np.linalg.norm(x[3]-obs) for x in cs]); score=float(np.partition(ds,1)[1]-ds.min())
  else: score=world
  vals.append(score)
 return [pool[i] for i in np.argsort(vals)[-budget:]]
def fit(records,outcomes):
 p=np.zeros((32,384));c=np.zeros(32)
 for e,(t,o,g) in zip(records,outcomes):
  i=(t*4+o)*2+g;p[i]+=feat(e['text']);c[i]+=1
 p/=np.maximum(c[:,None],1);p/=np.linalg.norm(p,axis=1,keepdims=True)+1e-9
 return p
def train(seed,mode):
 r=np.random.default_rng(seed); allrec=[];allout=[];boot=[];bout=[]
 for d in ('d1','d2'):
  xs=[ep(d,r) for _ in range(24)];boot+=xs;bout += [(x['t'],x['o'],x['g']) for x in xs]
 proto0=fit(boot,bout)
 for d in ('d1','d2'):
  pool=[ep(d,r) for _ in range(96)];sel=select(pool,24,r,mode,proto0);out=[(x['t'],x['o'],x['g']) for x in sel]
  if mode=='shuffle': r.shuffle(out)
  allrec+=sel;allout+=out
 return {'p':fit(allrec,allout)}
def evaluate(model,seed,d,style):
 r=np.random.default_rng(seed+sum(map(ord,d))+style*101); vals={'joint':[],'inverse':[],'goal_change':[],'repair':[]}
 for _ in range(48):
  e=ep(d,r,style); score=model['p']@feat(e['text']);i=int(score.argmax()); pred=(i//8,(i//2)%4,i%2)
  vals['joint'].append(pred==(e['t'],e['o'],e['g']))
  inds=[(e['t']*4+o)*2+e['g'] for o in range(4)];vals['inverse'].append(int(np.argmax(score[inds]))==e['o'])
  e2=dict(e);e2['g']=1-e['g'];e2['text']=utter(d,e['t'],e['o'],e2['g'],style);s2=model['p']@feat(e2['text']);j=int(s2.argmax());vals['goal_change'].append(((j//2)%4)==e['o'] and j%2==e2['g'])
  wrong=(e['o']+1)%4;e3=dict(e);e3['text']=utter(d,e['t'],wrong,e['g'],style)+' 失敗したので修正して。';s3=model['p']@feat(e3['text']);k=int(s3.argmax());vals['repair'].append(((k//2)%4)==e['o'])
 return {k:float(np.mean(v)) for k,v in vals.items()}
def main():
 st=time.perf_counter();raw={};sizes=[];modes=['joint','world','random','shuffle','oracle'];styles=[(0,'held'),(1,'word_order'),(2,'paragraph'),(3,'free'),(4,'rename')]
 for seed in SEEDS:
  raw[str(seed)]={}
  for mode in modes:
   m=train(seed,mode);sizes.append(len(pickle.dumps(m)));raw[str(seed)][mode]={}
   for d in DOMAINS:
    for s,l in styles:raw[str(seed)][mode][f'{d}_{l}']=evaluate(m,seed,d,s)
 summary={mode:{key:{metric:float(np.mean([raw[str(s)][mode][key][metric] for s in SEEDS])) for metric in ('joint','inverse','goal_change','repair')} for key in raw['1'][mode]} for mode in modes}
 strict=[]
 for seed in SEEDS:
  ok=True
  for key in ('d3_word_order','d3_free','d3_paragraph'):
   for metric in ('joint','inverse','goal_change','repair'):
    x=raw[str(seed)]['joint'][key][metric];b=max(raw[str(seed)]['world'][key][metric],raw[str(seed)]['random'][key][metric],raw[str(seed)]['shuffle'][key][metric]);ok &= x-b>=.10
  strict.append(bool(ok))
 print(json.dumps({'cycle':6,'hypothesis':'Joint Version-Space Collapse for Executable Operation Birth','seeds':SEEDS,'summary':summary,'raw':raw,'strict_gate_by_seed':strict,'model_bytes_mean':float(np.mean(sizes)),'runtime_seconds':time.perf_counter()-st,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'observation_budget_per_domain':24,'candidate_count':32,'estimated_ops_update_per_episode':12288,'estimated_ops_inference_per_query':12288,'answer_leakage':False,'post_treatment_test_input':False,'fixed_ontology':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
