import json, pickle, resource, time
import numpy as np

SEEDS=[1,7,19]
DOMAINS={
'd1':{'obj':['青箱','赤箱','緑箱','白箱'],'op':['右へ','左へ','上へ','下へ'],'goal':['近づけ','離せ']},
'd2':{'obj':['甲器','乙器','丙器','丁器'],'op':['東寄せ','西寄せ','北寄せ','南寄せ'],'goal':['接近','分離']},
'd3':{'obj':['ナロ','ミケ','フサ','トネ'],'op':['ルク','セパ','ゴニ','ハル'],'goal':['ヴァ','ネオ']},}
DIRS=np.array([[1,0],[-1,0],[0,1],[0,-1]],float)

def feat(text,dim=256):
 v=np.zeros(dim); b=text.encode()
 for n in (2,3,4):
  for i in range(max(0,len(b)-n+1)):
   h=2166136261
   for x in b[i:i+n]: h=(h^x)*16777619 & 0xffffffff
   v[h%dim]+=1
 return v/(np.linalg.norm(v)+1e-9)

def utter(dom,t,o,g,s):
 d=DOMAINS[dom]; obj=d['obj'][t%4]; op=d['op'][o]; goal=d['goal'][g]
 return [f'{obj}を{op}動かし、基準へ{goal}。',f'基準へ{goal}ように、{obj}は{op}。',f'前段は維持。\n{obj}を{op}。目的は{goal}。',f'依頼は「{obj}を{op}」で、狙いは{goal}。'][s%4]

def apply(w,t,o):
 z=w.copy(); z[t]+=DIRS[o]; return z

def episode(dom,rng,style=None):
 w=rng.uniform(-2,2,(6,2)); t=int(rng.integers(0,4)); o=int(rng.integers(0,4)); g=int(rng.integers(0,2)); s=int(rng.integers(0,4)) if style is None else style
 return {'dom':dom,'world':w,'target':t,'op':o,'goal':g,'style':s,'utterance':utter(dom,t,o,g,s),'after':apply(w,t,o)}

def world_sig(before,after):
 delta=(after-before).reshape(-1)
 db=np.sort(np.linalg.norm(before[:,None]-before[None,:],axis=2).ravel())[:12]
 da=np.sort(np.linalg.norm(after[:,None]-after[None,:],axis=2).ravel())[:12]
 v=np.r_[delta,da-db]; return v/(np.linalg.norm(v)+1e-9)

def build_candidates(seed, mode='correct'):
 rng=np.random.default_rng(seed); rec=[]
 for dom in ('d1','d2'):
  for _ in range(48):
   ep=episode(dom,rng)
   for k in range(4):
    q=dict(ep)
    if k==0: q['target']=(q['target']+1)%4
    elif k==1: q['op']=(q['op']+1)%4
    elif k==2: q['goal']=1-q['goal']
    else: q['style']=(q['style']+1)%4
    q['utterance']=utter(dom,q['target'],q['op'],q['goal'],q['style']); q['after']=apply(q['world'],q['target'],q['op'])
    ld=feat(q['utterance'])-feat(ep['utterance']); ld/=np.linalg.norm(ld)+1e-9
    wd=world_sig(ep['world'],q['after'])
    rec.append([dom,ld,wd,feat(ep['utterance'])])
 if mode=='outcome_shuffle':
  ws=[r[2] for r in rec]; rng.shuffle(ws)
  for i,r in enumerate(rec): r[2]=ws[i]
 L=[r for r in rec if r[0]=='d1']; R=[r for r in rec if r[0]=='d2']
 a=np.stack([np.r_[r[1],r[2]] for r in L]); b=np.stack([np.r_[r[1],r[2]] for r in R]); sim=a@b.T
 cand=[]
 for i,j in enumerate(np.argmax(sim,axis=1)):
  if np.argmax(sim[:,j])!=i: continue
  la=L[i][1]+R[j][1]; wa=L[i][2]+R[j][2]; la/=np.linalg.norm(la)+1e-9; wa/=np.linalg.norm(wa)+1e-9
  anchor=L[i][3]+R[j][3]; anchor/=np.linalg.norm(anchor)+1e-9
  cand.append({'score':float(sim[i,j]),'la':la,'wa':wa,'anchor':anchor})
 return sorted(cand,key=lambda x:x['score'],reverse=True)[:24]

def action_scores(c, ep):
 ls=feat(ep['utterance']); vals=[]
 for t in range(4):
  for o in range(4):
   qtext=utter(ep['dom'],t,o,ep['goal'],ep['style'])
   ld=feat(qtext)-feat(ep['utterance']); ld/=np.linalg.norm(ld)+1e-9
   wd=world_sig(ep['world'],apply(ep['world'],t,o))
   vals.append(float(ls@c['anchor']+ld@c['la']+wd@c['wa']))
 return np.array(vals)

def certify(seed, mode='correct', selector='active'):
 rng=np.random.default_rng(seed+991); cand=build_candidates(seed,mode)
 if not cand: return {'survivors':0,'probes':0,'model':{'cand':[]}}
 pool=[]
 for dom in ('d1','d2'):
  for _ in range(24): pool.append(episode(dom,rng,style=int(rng.integers(0,4))))
 alive=list(range(len(cand))); used=[]
 for _ in range(12):
  if len(alive)<=1: break
  best=None; choices=[i for i in range(len(pool)) if i not in used]
  if selector=='random': rng.shuffle(choices); choices=choices[:1]
  for pi in choices:
   preds=[int(np.argmax(action_scores(cand[ci],pool[pi]))) for ci in alive]
   _,counts=np.unique(preds,return_counts=True); split=len(counts)-max(counts) if len(counts) else 0
   if best is None or split>best[0]: best=(split,pi,preds)
  if best is None: break
  _,pi,preds=best; used.append(pi); ep=pool[pi]; truth=ep['target']*4+ep['op']
  if mode=='outcome_shuffle': truth=int(rng.integers(0,16))
  new=[ci for ci,p in zip(alive,preds) if p==truth]
  if not new: alive=[]; break
  alive=new
 return {'survivors':len(alive),'probes':len(used),'model':{'cand':[cand[i] for i in alive]}}

def evaluate(cert,seed,dom,style):
 rng=np.random.default_rng(seed+sum(map(ord,dom))+style*37); cs=cert['model']['cand']; out={'joint':[],'target':[],'inverse':[],'closed':[]}
 for _ in range(32):
  ep=episode(dom,rng,style)
  if not cs: pred=-1
  else: pred=int(np.argmax(np.mean(np.stack([action_scores(c,ep) for c in cs]),axis=0)))
  pt,po=(pred//4,pred%4) if pred>=0 else (-1,-1)
  joint=(pt==ep['target'] and po==ep['op']); out['joint'].append(joint); out['target'].append(pt==ep['target'])
  inv=[]
  for o in range(4):
   idx=ep['target']*4+o; inv.append(np.mean([action_scores(c,ep)[idx] for c in cs]) if cs else -1e9)
  invok=int(np.argmax(inv))==ep['op']; out['inverse'].append(invok); out['closed'].append(joint and invok)
 return {k:float(np.mean(v)) for k,v in out.items()}

def main():
 start=time.perf_counter(); raw={}; sizes=[]
 for seed in SEEDS:
  raw[str(seed)]={}
  for mode,selector in [('active','active'),('random','random'),('shuffle','active')]:
   cert=certify(seed,'outcome_shuffle' if mode=='shuffle' else 'correct',selector); sizes.append(len(pickle.dumps(cert['model'])))
   rec={'survivors':cert['survivors'],'probes':cert['probes'],'eval':{}}
   for dom in ('d1','d2','d3'):
    for style,label in ((0,'held'),(1,'word_order'),(2,'paragraph'),(3,'free')): rec['eval'][f'{dom}_{label}']=evaluate(cert,seed,dom,style)
   raw[str(seed)][mode]=rec
 summary={}
 for mode in ('active','random','shuffle'):
  summary[mode]={'survivors':float(np.mean([raw[str(s)][mode]['survivors'] for s in SEEDS])),'probes':float(np.mean([raw[str(s)][mode]['probes'] for s in SEEDS])),'eval':{}}
  for key in raw['1'][mode]['eval']:
   summary[mode]['eval'][key]={m:float(np.mean([raw[str(s)][mode]['eval'][key][m] for s in SEEDS])) for m in ('joint','target','inverse','closed')}
 result={'cycle':6,'hypothesis':'Intervention-Certified Memory Eligibility from Minimal Discriminating Action-Set Survival','seeds':SEEDS,'summary':summary,'raw':raw,'model_bytes_mean':float(np.mean(sizes)),'runtime_seconds':time.perf_counter()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'candidate_cap':24,'probe_budget':12,'estimated_ops_train_per_pair':2304,'estimated_ops_inference_per_query':98304,'answer_leakage':False,'post_treatment_test_input':False,'formal_memory_eligible':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
