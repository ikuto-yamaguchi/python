import random,time,json,pickle,resource,statistics
from collections import defaultdict
SEEDS=[1,7,19]
CONDS=['seen','word_order','lexeme','rename','alternate','nested','omitted','paragraph','plan','counterfactual']

def shape(s):
 return ''.join('J' if ord(c)>127 and c not in '。、\n「」' else c for c in s)

def episode(r,cond):
 objs=['青箱','赤箱','端末甲','端末乙']; vals=['棚A','棚B','待機','完了']
 o=r.choice(objs); other=r.choice([x for x in objs if x!=o]); old=r.choice(vals); new=r.choice([x for x in vals if x!=old])
 before=f'{o}の状態は{old}です。{other}の状態は{r.choice(vals)}です。'
 cmd=f'{o}の状態を{new}へ変更してください。'
 if cond=='word_order': cmd=f'{new}へ変更してください。対象は{o}です。'
 if cond=='lexeme': cmd=f'{o}を今後{new}扱いにします。'
 if cond=='rename': cmd=cmd.replace(o,o+'改') ; before=before.replace(o,o+'改')
 if cond=='alternate': before=f'{o}：{old}／{other}：{r.choice(vals)}。'
 if cond=='nested': cmd=f'依頼「{cmd}」を実行してください。'
 if cond=='omitted': cmd=f'それを{new}へ変更してください。'
 if cond=='paragraph': cmd=f'補足です。\n{cmd}\n他は維持します。'
 if cond=='plan': cmd=f'{o}を棚Cにする案は撤回し、最終的に{new}へ変更してください。'
 if cond=='counterfactual': cmd=f'変更しなければ{o}は{old}です。実際には{new}へ変更してください。'
 after=before.replace(old,new,1)
 return dict(before=before,command=cmd,after=after,obj=o,old=old,new=new)

def candidates(ep):
 out=[]
 b,c=ep['before'],ep['command']
 for i in range(len(b)):
  for j in range(i+1,min(len(b),i+9)+1):
   old=b[i:j]
   for k in range(len(c)):
    for l in range(k+1,min(len(c),k+9)+1):
     new=c[k:l]
     pred=b[:i]+new+b[j:]
     out.append((i,j,k,l,shape(old),shape(new),pred))
 return out[:96]

def train(seed):
 r=random.Random(seed); worlds=[]
 for _ in range(12):
  worlds.append(episode(r,'seen'))
 fam=defaultdict(lambda:[0,0,set()])
 t0=time.perf_counter()
 for ep in worlds:
  for x in candidates(ep):
   key=(x[1]-x[0],x[3]-x[2],x[0]//4,x[2]//4,x[4],x[5])
   ok=x[6]==ep['after']
   fam[key][0]+=ok; fam[key][1]+=not ok
   if ok: fam[key][2].add(ep['obj'])
 kept={k:v for k,v in fam.items() if v[0]>=2 and v[0]>v[1] and len(v[2])>=2}
 return kept,time.perf_counter()-t0

def eval_seed(seed):
 fam,tr=train(seed); r=random.Random(seed+1000); res={}
 for cond in CONDS:
  vals=[]; t0=time.perf_counter()
  for _ in range(8):
   ep=episode(r,cond); cs=[]
   for x in candidates(ep):
    key=(x[1]-x[0],x[3]-x[2],x[0]//4,x[2]//4,x[4],x[5])
    if key in fam: cs.append(x)
   preds={x[6] for x in cs}
   pred=next(iter(preds)) if len(preds)==1 else None
   vals.append((pred==ep['after'],pred is not None and pred!=ep['after'],pred is None,len(cs),any(x[0]==ep['before'].find(ep['old']) and x[2]==ep['command'].find(ep['new']) for x in cs)))
  ms=(time.perf_counter()-t0)*1000/8
  res[cond]={'accuracy':statistics.mean(v[0] for v in vals),'wrong':statistics.mean(v[1] for v in vals),'null':statistics.mean(v[2] for v in vals),'candidates':statistics.mean(v[3] for v in vals),'exact_event_recall':statistics.mean(v[4] for v in vals),'inference_ms':ms}
 return fam,tr,res
raw={}; sizes=[]; trs=[]; fams=[]
for s in SEEDS:
 f,t,r=eval_seed(s); raw[str(s)]=r; sizes.append(len(pickle.dumps(f))); trs.append(t); fams.append(len(f))
summary={c:{k:statistics.mean(raw[str(s)][c][k] for s in SEEDS) for k in raw['1'][c]} for c in CONDS}
out={'cycle':39,'hypothesis':'Event-Centered Causal Units from Multi-World Intervention-Closure Co-Segmentation','seeds':SEEDS,'event_family_count':statistics.mean(fams),'model_bytes':statistics.mean(sizes),'training_seconds':statistics.mean(trs),'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'summary':summary,'raw':raw,'estimated_complexity':'O(N L^4) candidate audit, capped at 96/episode; inference O(F L^4)','highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
print(json.dumps(out,ensure_ascii=False,indent=2))
