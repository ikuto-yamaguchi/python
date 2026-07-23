from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import json, random, time, pickle, resource, statistics, argparse

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー'}
VALUES=['棚A','棚B','棚C','棚D','待機','処理中','完了','保留']

@dataclass
class Ex:
    before:str; command:str; after:str; future:str
    target:str; other:str; old:str; new:str; target_span:tuple[int,int]; mode:str

@dataclass
class Proposal:
    state_bucket:int; width:int; value_bucket:int; value_width:int
    support:int=0; wrong:int=0

@dataclass
class Edge:
    object_sig:str; source_bucket:int; target_bucket:int; support:int=0; wrong:int=0

def sh(s):
    return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、：／=\n「」 ' else c for c in s)

def state_pair(a,va,b,vb,mode):
    if mode=='alternate': return f'{a}：現在={va}／補助=維持。{b}：現在={vb}／補助=維持。'
    if mode=='paragraph': return f'前段の説明です。\n{a}の現在値は{va}です。補助記録は維持します。\n{b}の現在値は{vb}です。別件は変えません。'
    return f'{a}の現在値は{va}です。{b}の現在値は{vb}です。補助記録は維持します。'

def make(seed,n,mode):
    r=random.Random(seed); out=[]
    for i in range(n):
        a,b=r.sample(OBJECTS,2); ta,tb=(a,b) if i%2==0 else (b,a)
        sa=ALIASES[a] if mode=='rename' else a; sb=ALIASES[b] if mode=='rename' else b
        surf={a:sa,b:sb}; va,vb=r.sample(VALUES,2); old={a:va,b:vb}; new=r.choice([x for x in VALUES if x!=old[ta]])
        before=state_pair(sa,va,sb,vb,mode)
        if mode=='order': cmd=f'{new}へ変更してください、対象は{surf[ta]}です。'
        elif mode=='lexeme': cmd=f'対象{surf[ta]}は次から{new}扱いにします。'
        elif mode=='nested': cmd=f'依頼内容は「{surf[ta]}の値を{new}へ変更してください。」です。'
        elif mode=='omitted': cmd=f'その対象を{new}へ変更してください。'
        elif mode=='plan': cmd=f'{surf[ta]}を{r.choice([x for x in VALUES if x not in (old[ta],new)])}にする案は撤回し、最終的には{new}へ変更してください。'
        elif mode=='counterfactual': cmd=f'もし変更しなければ{surf[ta]}は{old[ta]}のままです。実際には{surf[ta]}を{new}へ変更してください。'
        elif mode=='paragraph': cmd=f'前段の注意は維持します。\n{surf[ta]}の値を{new}へ変更してください。\n別件は変更しません。'
        else: cmd=f'{surf[ta]}の値を{new}へ変更してください。'
        nv={a:va,b:vb}; nv[ta]=new; after=state_pair(sa,nv[a],sb,nv[b],mode)
        st=before.find(old[ta])
        out.append(Ex(before,cmd,after,f'次の観測でも{surf[ta]}は{new}です。',surf[ta],surf[tb],old[ta],new,(st,st+len(old[ta])),mode))
    return out

def diff_span(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    rr=0
    while rr<min(len(a)-l,len(b)-l) and a[-1-rr]==b[-1-rr]: rr+=1
    return l,len(a)-rr,len(b)-rr

def candidates(e):
    vals=[]
    for i in range(len(e.command)):
      for j in range(i+1,min(len(e.command),i+9)+1):
        x=e.command[i:j]
        if x not in e.before and not any(c in x for c in '。、\n「」'): vals.append((i,j,x))
    vals=sorted(set(vals),key=lambda z:(-len(z[2]),z[0]))[:12]
    spans=[]
    for i in range(len(e.before)):
      for w in range(1,9):
        j=i+w
        if j<=len(e.before) and not any(c in e.before[i:j] for c in '。、\n「」'): spans.append((i,j))
    return spans,vals

def bucket(pos,L): return int(16*pos/max(1,L))

def apply(e,p,edge=None):
    spans,vals=candidates(e); outs=[]; object_positions=[]
    for i in range(len(e.command)):
      for j in range(i+2,min(len(e.command),i+13)+1):
        x=e.command[i:j]
        if x in e.before: object_positions.append((i,j,x))
    for a,b in spans:
      sb=bucket(a,len(e.before))
      if edge is not None:
        if not any(sh(x)==edge.object_sig for _,_,x in object_positions): continue
        if sb!=edge.target_bucket: continue
      elif sb!=p.state_bucket or (b-a)!=p.width: continue
      for i,j,v in vals:
        if bucket(i,len(e.command))!=p.value_bucket or (j-i)!=p.value_width: continue
        outs.append((e.before[:a]+v+e.before[b:],(a,b),v))
    return outs

class Model:
  def __init__(self,method): self.method=method; self.props=[]; self.edges=[]; self.train_s=0
  def fit(self,induction,probe,shuffle=False):
    t=time.perf_counter(); cnt=Counter()
    for e in induction:
      a,b,_=diff_span(e.before,e.after); vi=e.command.find(e.new)
      if vi>=0: cnt[(bucket(a,len(e.before)),b-a,bucket(vi,len(e.command)),len(e.new))]+=1
    self.props=[Proposal(*k,support=n) for k,n in cnt.most_common(32)]
    edgecnt=defaultdict(lambda:[0,0]); outcomes=[e.after for e in probe]
    if shuffle: outcomes=outcomes[1:]+outcomes[:1]
    for e,obs in zip(probe,outcomes):
      oa,_,_=diff_span(e.before,obs); target_b=bucket(oa,len(e.before)); objs=[]
      for i in range(len(e.command)):
        for j in range(i+2,min(len(e.command),i+13)+1):
          x=e.command[i:j]
          if x in e.before: objs.append(x)
      for p in self.props:
        for x in objs:
          key=(sh(x),p.state_bucket,target_b); pred_any=any(pred==obs for pred,_,_ in apply(e,p))
          edgecnt[key][0 if pred_any else 1]+=1
    self.edges=[Edge(*k,support=v[0],wrong=v[1]) for k,v in edgecnt.items() if v[0]>=2 and v[0]>v[1]]
    self.edges=sorted(self.edges,key=lambda x:(x.support-x.wrong,x.support),reverse=True)[:64]
    self.train_s=time.perf_counter()-t
  def predict(self,e):
    outs=[]
    for p in self.props:
      if self.method=='factorized': outs+=apply(e,p)
      else:
        for ed in self.edges:
          if ed.source_bucket==p.state_bucket: outs+=apply(e,p,ed)
    outs=list({x[0]:x for x in outs}.values())
    return (outs[0],1,outs) if len(outs)==1 else (None,len(outs),outs)

def eval_model(m,seed,mode):
    test=make(seed+1000,16,mode); t=time.perf_counter(); corr=wrong=null=exact=pair=wrong_target=cand=0
    for e in test:
      pred,n,_=m.predict(e); cand+=n
      if pred is None: null+=1; continue
      text,span,v=pred; corr+=text==e.after; wrong+=text!=e.after; exact+=span==e.target_span
      pair+=(span==e.target_span and v==e.new); wrong_target+=span!=e.target_span
    N=len(test)
    return dict(accuracy=corr/N,wrong=wrong/N,null=null/N,exact_boundary=exact/N,pair=pair/N,wrong_target=wrong_target/N,mean_candidates=cand/N,proposals=len(m.props),edges=len(m.edges),model_bytes=len(pickle.dumps(m)),training_seconds=m.train_s,inference_ms=(time.perf_counter()-t)*1000/N)

def main():
  ap=argparse.ArgumentParser(); ap.add_argument('--output',default='MEASUREMENTS_CYCLE_037.json'); a=ap.parse_args()
  modes=['seen','order','lexeme','rename','alternate','nested','omitted','paragraph','plan','counterfactual']; raw={}
  for seed in [1,7,19]:
    train=make(seed,48,'seen'); probe=make(seed+100,24,'seen'); models={}
    for name,method,shuffle in [('factorized','factorized',False),('object_edge','edge',False),('shuffled_edge','edge',True)]:
      mm=Model(method); mm.fit(train,probe,shuffle); models[name]=mm
    raw[str(seed)]={mode:{name:eval_model(mm,seed,mode) for name,mm in models.items()} for mode in modes}
  summary={mode:{meth:{k:statistics.mean(raw[str(s)][mode][meth][k] for s in [1,7,19]) for k in raw['1'][mode][meth]} for meth in ['factorized','object_edge','shuffled_edge']} for mode in modes}
  payload={'cycle':37,'hypothesis':'Object-Edge Birth from Target-Support Residual Transport under Paired Worlds','seeds':[1,7,19],'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'induction O(NL), paired-probe edge birth O(QPOL^2), inference O(EPOVL^2)','final_test_outcomes_used_for_selection':False,'fixed_ontology_or_handwritten_slots_used_by_model':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
  open(a.output,'w').write(json.dumps(payload,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
