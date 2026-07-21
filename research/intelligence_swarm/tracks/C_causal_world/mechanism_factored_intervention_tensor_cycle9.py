"""系列C Cycle 009: 機構分解型介入テンソルの反証probe。"""
from __future__ import annotations
import json,random,time,pickle,resource,statistics,math,argparse
from collections import Counter,defaultdict
OPS=['運ぶ','開ける','割り当てる','点灯する']
CTX_GROUPS=[('自由に実行できる',[1,1,1,1]),('通路が塞がっている',[0,1,1,1]),('鍵が掛かっている',[1,0,1,1]),('担当変更が禁止されている',[1,1,0,1]),('電源が切れている',[1,1,1,0]),('安全停止中である',[0,0,1,0])]
PARA={'自由に実行できる':['作業に制限はない','通常運転中だ'],'通路が塞がっている':['経路を通れない','搬送路に障害がある'],'鍵が掛かっている':['施錠されている','解錠されていない'],'担当変更が禁止されている':['担当者は固定されている','割当変更は許可されない'],'電源が切れている':['給電されていない','装置が無通電だ'],'安全停止中である':['安全機構が作動中だ','非常停止が有効だ']}
ENTS=['対象甲','対象乙','装置春','荷物星','端末月','箱青']
def grams(s):
 c=Counter();s=''.join(s.split())
 for n in (2,3):
  for i in range(max(0,len(s)-n+1)):c[s[i:i+n]]+=1
 return c
def cos(a,b):
 d=sum(v*b.get(k,0) for k,v in a.items());na=math.sqrt(sum(v*v for v in a.values()));nb=math.sqrt(sum(v*v for v in b.values()));return d/(na*nb+1e-12)
def sample(rng,held_surface=False,omit=False,multi=False,plan=False):
 name,sig=rng.choice(CTX_GROUPS);ctx=rng.choice(PARA[name]) if held_surface else name;ent=rng.choice(ENTS);opi=rng.randrange(len(OPS));op=OPS[opi];subj='' if omit else ent+'を';cmd=f'{subj}{op}。'
 if multi:ctx=f'現在の状況を説明する。\n{ctx}。\n次の指示を処理する。'
 if plan:cmd=f'{ent}を{OPS[(opi+1)%4]}。ただし計画を変更し、{cmd}'
 return {'context':ctx,'command':cmd,'op':opi,'outcome':sig[opi],'signature':sig,'factor':name}
class MechanismTensor:
 def __init__(self,rank=3):self.rank=rank;self.protos=[];self.sigs=[]
 def fit(self,rows):
  by=defaultdict(list)
  for r in rows:by[r['context']].append(r)
  for ctx,rs in by.items():
   obs=[None]*4
   for r in rs:obs[r['op']]=r['outcome']
   self.protos.append((ctx,grams(ctx)));self.sigs.append(obs)
  return self
 def predict(self,r,masked_op=None):
  q=grams(r['context']);scores=sorted(((cos(q,g),i) for i,(_,g) in enumerate(self.protos)),reverse=True);top=scores[:self.rank]
  if not top or top[0][0]<0.08:return None,0
  op=r['op'] if masked_op is None else masked_op;votes=[]
  for s,i in top:
   v=self.sigs[i][op]
   if v is not None:votes.append((s,v))
  if not votes:return None,len(top)
  z=sum(s for s,v in votes);p=sum(s*v for s,v in votes)/(z+1e-12)
  if abs(p-.5)<.12:return None,len(top)
  return int(p>.5),len(top)
def run(seed,n,rank):
 rng=random.Random(seed);train=[]
 for _ in range(n):
  base=sample(rng)
  for op in rng.sample(range(4),3):
   x=dict(base);x['op']=op;x['command']=f"{base['command'].split('。')[0]}{OPS[op]}。";x['outcome']=x['signature'][op];train.append(x)
 t=time.perf_counter();m=MechanismTensor(rank).fit(train);train_s=time.perf_counter()-t
 splits={'seen':[sample(rng) for _ in range(240)],'unseen_context':[sample(rng,held_surface=True) for _ in range(240)],'subject_omission':[sample(rng,omit=True) for _ in range(240)],'multi_paragraph':[sample(rng,multi=True) for _ in range(240)],'plan_change':[sample(rng,plan=True) for _ in range(240)]};out={}
 for k,rows in splits.items():
  st=time.perf_counter();pairs=[m.predict(r) for r in rows];preds=[x[0] for x in pairs];reads=[x[1] for x in pairs];out[k]={'accuracy':sum(p==r['outcome'] for p,r in zip(preds,rows))/len(rows),'abstention':sum(p is None for p in preds)/len(rows),'ms':(time.perf_counter()-st)*1000/len(rows),'reads':statistics.mean(reads)}
 tests=[{'context':ctx,'op':op,'outcome':sig[op]} for ctx,sig in CTX_GROUPS for op in range(4)];ps=[m.predict(r)[0] for r in tests];out['counterfactual_completion']={'accuracy':sum(p==r['outcome'] for p,r in zip(ps,tests))/len(tests),'abstention':sum(p is None for p in ps)/len(ps)}
 rows=[sample(rng) for _ in range(240)]
 for r in rows:r['outcome']=1-r['outcome'];r['context']='先に別操作を実行した後、'+r['context']
 ps=[m.predict(r)[0] for r in rows];out['order_counterfactual']={'accuracy':sum(p==r['outcome'] for p,r in zip(ps,rows))/len(ps),'abstention':sum(p is None for p in ps)/len(ps)};out.update({'model_bytes':len(pickle.dumps(m)),'factor_nodes':len(m.protos),'train_seconds':train_s,'rank':rank});return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_009.json');a=ap.parse_args();raw={str(n):{str(rank):[run(s,n,rank) for s in (1,7,19)] for rank in (1,3,6)} for n in (48,192,768)};summary={}
 for n,d in raw.items():
  summary[n]={}
  for rank,runs in d.items():
   z={}
   for split in ['seen','unseen_context','subject_omission','multi_paragraph','plan_change','counterfactual_completion','order_counterfactual']:z[split]={key:statistics.mean(r[split][key] for r in runs) for key in runs[0][split]}
   for key in ['model_bytes','factor_nodes','train_seconds']:z[key]=statistics.mean(r[key] for r in runs)
   summary[n][rank]=z
 payload={'hypothesis':'Mechanism-Factored Intervention Tensor with Counterfactual Completion','seeds':[1,7,19],'raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False};open(a.output,'w').write(json.dumps(payload,ensure_ascii=False,indent=2));print(json.dumps(summary['768'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
