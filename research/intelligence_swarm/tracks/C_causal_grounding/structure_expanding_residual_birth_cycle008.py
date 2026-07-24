import json,pickle,resource,time
import numpy as np
SEEDS=[1,7,19]
DOMAINS={
'd1':{'obj':['青箱','赤箱','緑箱','白箱'],'op':['右へ','左へ','上へ','下へ'],'goal':['近づけ','離せ']},
'd2':{'obj':['甲器','乙器','丙器','丁器'],'op':['東寄せ','西寄せ','北寄せ','南寄せ'],'goal':['接近','分離']},
'd3':{'obj':['ナロ','ミケ','フサ','トネ'],'op':['ルク','セパ','ゴニ','ハル'],'goal':['ヴァ','ネオ']}}
DIRS=np.array([[1,0],[-1,0],[0,1],[0,-1]],float)
LDIM=256; WDIM=64; IDIM=128

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
 d=w[:,None,:]-w[None,:,:]; dist=np.linalg.norm(d,axis=2); ang=np.arctan2(d[:,:,1],d[:,:,0])
 raw=np.r_[np.sort(dist.ravel()),np.sort(np.cos(ang).ravel()),np.sort(np.sin(ang).ravel())]
 v=np.zeros(WDIM)
 for i,x in enumerate(raw): v[i%WDIM]+=x*(1 if (i//WDIM)%2==0 else -1)
 return v/(np.linalg.norm(v)+1e-9)
def utter(d,t,o,g,s):
 z=DOMAINS[d];a,b,c=z['obj'][t],z['op'][o],z['goal'][g]
 forms=[f'{a}を{b}動かし、基準へ{c}。',f'基準へ{c}ように、{a}は{b}。',f'前段を保つ。\n対象は{a}、動きは{b}、狙いは{c}。',f'最終的に{c}ため、{a}へ{b}の変化を与えて。',f'{c}という意図なら、{b}のは{a}。']
 return forms[s%5]
def apply(w,t,o): x=w.copy();x[t]+=DIRS[o];return x
def ep(d,r,s=None,t=None,o=None,g=None,w=None):
 w=r.uniform(-2,2,(6,2)) if w is None else w.copy();t=int(r.integers(4)) if t is None else t;o=int(r.integers(4)) if o is None else o;g=int(r.integers(2)) if g is None else g;s=int(r.integers(5)) if s is None else s
 return {'d':d,'w':w,'t':t,'o':o,'g':g,'s':s,'text':utter(d,t,o,g,s),'after':apply(w,t,o)}
def idx(e): return (e['t']*4+e['o'])*2+e['g']
def base_feat(e): return np.r_[lfeat(e['text']),wfeat(e['w'])]

def interaction(e,seed):
 rng=np.random.default_rng(seed+991)
 A=rng.choice([-1.,1.],(16,LDIM))/np.sqrt(LDIM); B=rng.choice([-1.,1.],(8,WDIM))/np.sqrt(WDIM)
 a=A@lfeat(e['text']); b=B@wfeat(e['w']); z=np.outer(a,b).ravel()
 return z/(np.linalg.norm(z)+1e-9)

def fit_base(records):
 p=np.zeros((32,LDIM+WDIM));c=np.zeros(32)
 for e in records:p[idx(e)]+=base_feat(e);c[idx(e)]+=1
 p/=np.maximum(c[:,None],1);p/=np.linalg.norm(p,axis=1,keepdims=True)+1e-9
 return p

def score_base(p,e): return p@base_feat(e)

def train(seed,mode):
 r=np.random.default_rng(seed); base=[]
 for d in ('d1','d2'): base += [ep(d,r) for _ in range(32)]
 p=fit_base(base)
 pool=[]
 for d in ('d1','d2'):
  for _ in range(48):
   w=r.uniform(-2,2,(6,2)); t=int(r.integers(4));o=int(r.integers(4));g=int(r.integers(2));s=int(r.integers(5))
   pool.append(ep(d,r,s,t,o,g,w))
 residual=np.zeros((32,LDIM+WDIM));rc=np.zeros(32)
 born=[[] for _ in range(32)]
 outcomes=[idx(e) for e in pool]
 if mode=='shuffle': r.shuffle(outcomes)
 for e,y in zip(pool,outcomes):
  pred=int(np.argmax(score_base(p,e)))
  if pred==y: continue
  if mode=='weight': residual[y]+=base_feat(e);rc[y]+=1
  elif mode in ('expand','shuffle'):
   born[y].append((e['d'],interaction(e,seed)))
 if mode=='weight':
  residual/=np.maximum(rc[:,None],1);residual/=np.linalg.norm(residual,axis=1,keepdims=True)+1e-9
  p2=p+.6*residual;p2/=np.linalg.norm(p2,axis=1,keepdims=True)+1e-9
  return {'p':p2,'heads':{},'births':int(np.sum(rc>0))}
 if mode in ('expand','shuffle'):
  heads={}; births=0
  for y,items in enumerate(born):
   ds={d for d,_ in items}
   if len(ds)<2 or len(items)<4: continue
   arr=np.stack([z for _,z in items]); mu=arr.mean(0);mu/=np.linalg.norm(mu)+1e-9
   proj=arr@mu
   pos=arr[proj>=np.median(proj)].mean(0);neg=arr[proj<np.median(proj)].mean(0)
   pos/=np.linalg.norm(pos)+1e-9;neg/=np.linalg.norm(neg)+1e-9
   heads[y]=(pos,neg);births+=2
  return {'p':p,'heads':heads,'births':births}
 return {'p':p,'heads':{},'births':0}

def scores(m,e,seed):
 s=score_base(m['p'],e).copy();z=interaction(e,seed)
 for y,(a,b) in m['heads'].items(): s[y]+=0.7*max(a@z,b@z)
 return s

def evaluate(m,seed,d,style):
 r=np.random.default_rng(seed+sum(map(ord,d))+style*101);out={k:[] for k in ('joint','target','inverse','repair')}
 for _ in range(64):
  e=ep(d,r,style);s=scores(m,e,seed);j=int(np.argmax(s));pred=(j//8,(j//2)%4,j%2)
  out['joint'].append(pred==(e['t'],e['o'],e['g']));out['target'].append(pred[0]==e['t'])
  inds=[(e['t']*4+o)*2+e['g'] for o in range(4)];out['inverse'].append(int(np.argmax(s[inds]))==e['o'])
  wrong=(e['o']+1)%4;e2=dict(e);e2['text']=utter(d,e['t'],wrong,e['g'],style)+' 失敗したので修正して。';k=int(np.argmax(scores(m,e2,seed)));out['repair'].append(((k//2)%4)==e['o'])
 return {k:float(np.mean(v)) for k,v in out.items()}

def main():
 st=time.perf_counter();modes=['base','weight','expand','shuffle'];styles=[(0,'held'),(1,'word_order'),(2,'paragraph'),(3,'free'),(4,'rename')];raw={};sizes=[]
 for seed in SEEDS:
  raw[str(seed)]={}
  for mode in modes:
   m=train(seed,mode);sizes.append(len(pickle.dumps(m)));raw[str(seed)][mode]={'births':m['births'],'eval':{}}
   for d in DOMAINS:
    for s,n in styles:raw[str(seed)][mode]['eval'][f'{d}_{n}']=evaluate(m,seed,d,s)
 summary={}
 for mode in modes:
  summary[mode]={'births':float(np.mean([raw[str(s)][mode]['births'] for s in SEEDS])),'eval':{}}
  for key in raw['1'][mode]['eval']:
   summary[mode]['eval'][key]={metric:float(np.mean([raw[str(s)][mode]['eval'][key][metric] for s in SEEDS])) for metric in ('joint','target','inverse','repair')}
 strict=[]
 for seed in SEEDS:
  ok=True
  for key in ('d3_word_order','d3_paragraph','d3_free','d3_rename'):
   for metric in ('joint','inverse','repair'):
    x=raw[str(seed)]['expand']['eval'][key][metric];b=max(raw[str(seed)]['base']['eval'][key][metric],raw[str(seed)]['weight']['eval'][key][metric],raw[str(seed)]['shuffle']['eval'][key][metric]);ok &= x-b>=.10
  strict.append(bool(ok))
 print(json.dumps({'cycle':8,'hypothesis':'Structure-Expanding Residual Birth from Cross-Episode Counterfactual Repair','seeds':SEEDS,'summary':summary,'raw':raw,'strict_gate_by_seed':strict,'model_bytes_mean':float(np.mean(sizes)),'runtime_seconds':time.perf_counter()-st,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'candidate_count':32,'interaction_dim':IDIM,'estimated_ops_update_per_episode':(LDIM+WDIM)*32+IDIM*32,'estimated_ops_inference_per_query':(LDIM+WDIM)*32+IDIM*32,'answer_leakage':False,'post_treatment_test_input':False,'fixed_ontology':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
