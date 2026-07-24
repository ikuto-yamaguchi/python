import json,pickle,resource,time
import numpy as np
SEEDS=[1,7,19]
DOMAINS={
'd1':{'obj':['青箱','赤箱','緑箱','白箱'],'op':['右へ','左へ','上へ','下へ'],'goal':['近づけ','離せ']},
'd2':{'obj':['甲器','乙器','丙器','丁器'],'op':['東寄せ','西寄せ','北寄せ','南寄せ'],'goal':['接近','分離']},
'd3':{'obj':['ナロ','ミケ','フサ','トネ'],'op':['ルク','セパ','ゴニ','ハル'],'goal':['ヴァ','ネオ']}}
DIRS=np.array([[1,0],[-1,0],[0,1],[0,-1]],float)
LDIM=384; WDIM=96; CDIM=LDIM+WDIM

def hash_feat(raw,dim):
 v=np.zeros(dim)
 for n in (2,3,4,5):
  for i in range(len(raw)-n+1):
   h=2166136261
   for b in raw[i:i+n]: h=((h^b)*16777619)&0xffffffff
   v[h%dim]+=1
 return v/(np.linalg.norm(v)+1e-9)

def lfeat(text): return hash_feat(text.encode(),LDIM)
def wfeat(w):
 d=w[:,None,:]-w[None,:,:]
 dist=np.linalg.norm(d,axis=2)
 angles=np.arctan2(d[:,:,1],d[:,:,0])
 raw=np.r_[np.sort(dist.ravel()),np.sort(np.cos(angles).ravel()),np.sort(np.sin(angles).ravel())]
 v=np.zeros(WDIM)
 for i,x in enumerate(raw): v[i%WDIM]+=x*(1 if (i//WDIM)%2==0 else -1)
 return v/(np.linalg.norm(v)+1e-9)

def feat(e): return np.r_[lfeat(e['text']),wfeat(e['w'])]
def utter(d,t,o,g,s):
 z=DOMAINS[d];a,b,c=z['obj'][t],z['op'][o],z['goal'][g]
 forms=[f'{a}を{b}動かし、基準へ{c}。',f'基準へ{c}ように、{a}は{b}。',f'前段を保つ。\n対象は{a}、動きは{b}、狙いは{c}。',f'最終的に{c}ため、{a}へ{b}の変化を与えて。',f'{c}という意図なら、{b}のは{a}。']
 return forms[s%5]
def apply(w,t,o): x=w.copy();x[t]+=DIRS[o];return x
def ep(d,r,s=None):
 w=r.uniform(-2,2,(6,2));t=int(r.integers(4));o=int(r.integers(4));g=int(r.integers(2));s=int(r.integers(5)) if s is None else s
 return {'d':d,'w':w,'t':t,'o':o,'g':g,'s':s,'text':utter(d,t,o,g,s),'after':apply(w,t,o)}
def idx(e): return (e['t']*4+e['o'])*2+e['g']

def fit(records,outcomes=None):
 p=np.zeros((32,CDIM)); c=np.zeros(32)
 if outcomes is None: outcomes=[idx(e) for e in records]
 for e,i in zip(records,outcomes): p[i]+=feat(e);c[i]+=1
 p/=np.maximum(c[:,None],1);p/=np.linalg.norm(p,axis=1,keepdims=True)+1e-9
 return p

def predict(p,e): return int(np.argmax(p@feat(e)))

def train(seed,mode):
 r=np.random.default_rng(seed); base=[]
 for d in ('d1','d2'): base += [ep(d,r) for _ in range(24)]
 p0=fit(base)
 pool=[]
 for d in ('d1','d2'): pool += [ep(d,r) for _ in range(96)]
 if mode=='random': selected=list(r.choice(pool,24,replace=False))
 else:
  val=[]
  for e in pool:
   s=p0@feat(e); q=np.partition(s,-2)[-2:]; val.append(float(q[-1]-q[-2]))
  selected=[pool[i] for i in np.argsort(val)[:24]]
 outcomes=[idx(e) for e in selected]
 if mode=='shuffle': r.shuffle(outcomes)
 residual=np.zeros_like(p0); rc=np.zeros(32); births=0
 for e,y in zip(selected,outcomes):
  pred=predict(p0,e)
  if pred!=y:
   x=feat(e); residual[y]+=x; residual[pred]-=.25*x; rc[y]+=1; births+=1
 residual/=np.maximum(rc[:,None],1)
 residual/=np.linalg.norm(residual,axis=1,keepdims=True)+1e-9
 if mode=='base': p=p0
 else:
  p=p0+.75*residual; p/=np.linalg.norm(p,axis=1,keepdims=True)+1e-9
 return {'p':p,'births':births,'residual':residual}

def evaluate(model,seed,d,style):
 r=np.random.default_rng(seed+sum(map(ord,d))+style*101)
 out={k:[] for k in ('joint','target','inverse','closed','repair')}
 for _ in range(48):
  e=ep(d,r,style); s=model['p']@feat(e); j=int(np.argmax(s)); pred=(j//8,(j//2)%4,j%2)
  joint=pred==(e['t'],e['o'],e['g']);out['joint'].append(joint);out['target'].append(pred[0]==e['t'])
  inds=[(e['t']*4+o)*2+e['g'] for o in range(4)]; inv=int(np.argmax(s[inds]))==e['o'];out['inverse'].append(inv)
  out['closed'].append(joint and inv)
  wrong=(e['o']+1)%4;e3=dict(e);e3['text']=utter(d,e['t'],wrong,e['g'],style)+' 失敗したので修正して。';k=int(np.argmax(model['p']@feat(e3)));out['repair'].append(((k//2)%4)==e['o'])
 return {k:float(np.mean(v)) for k,v in out.items()}

def main():
 st=time.perf_counter();raw={};sizes=[];modes=['base','residual','random','shuffle'];styles=[(0,'held'),(1,'word_order'),(2,'paragraph'),(3,'free'),(4,'rename')]
 for seed in SEEDS:
  raw[str(seed)]={}
  for mode in modes:
   m=train(seed,mode);sizes.append(len(pickle.dumps(m)));raw[str(seed)][mode]={'births':m['births'],'eval':{}}
   for d in DOMAINS:
    for s,l in styles: raw[str(seed)][mode]['eval'][f'{d}_{l}']=evaluate(m,seed,d,s)
 summary={}
 for mode in modes:
  summary[mode]={'births':float(np.mean([raw[str(s)][mode]['births'] for s in SEEDS])),'eval':{}}
  for key in raw['1'][mode]['eval']:
   summary[mode]['eval'][key]={metric:float(np.mean([raw[str(s)][mode]['eval'][key][metric] for s in SEEDS])) for metric in ('joint','target','inverse','closed','repair')}
 strict=[]
 for seed in SEEDS:
  ok=True
  for key in ('d3_word_order','d3_free','d3_paragraph'):
   for metric in ('joint','inverse','closed','repair'):
    x=raw[str(seed)]['residual']['eval'][key][metric]; b=max(raw[str(seed)]['base']['eval'][key][metric],raw[str(seed)]['random']['eval'][key][metric],raw[str(seed)]['shuffle']['eval'][key][metric]); ok &= x-b>=.10
  strict.append(bool(ok))
 print(json.dumps({'cycle':7,'hypothesis':'Intervention-Residual Candidate Birth before Memory Eligibility','seeds':SEEDS,'summary':summary,'raw':raw,'strict_gate_by_seed':strict,'formal_memory_eligible_units':0,'model_bytes_mean':float(np.mean(sizes)),'runtime_seconds':time.perf_counter()-st,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'candidate_count':32,'observation_budget':24,'estimated_ops_update_per_episode':CDIM*32,'estimated_ops_inference_per_query':CDIM*32,'answer_leakage':False,'post_treatment_test_input':False,'fixed_ontology':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
