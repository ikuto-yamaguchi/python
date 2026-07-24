from __future__ import annotations
import argparse,json,pickle,random,resource,statistics,time
from collections import Counter
from dataclasses import dataclass

OBJECTS=['青い箱','赤い箱','北側端末','南側端末','試料甲','試料乙','鍵A','鍵B']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','北側端末':'北の端末','南側端末':'南の端末','試料甲':'サンプル甲','試料乙':'サンプル乙','鍵A':'第一キー','鍵B':'第二キー'}
VALUES=['棚A','棚B','棚C','棚D','待機','処理中','完了','保留']
OPS=['変更してください','切り替えてください','更新してください','移してください']
FILL=['補助記録は維持します。','別件の設定は変えません。','注意事項はそのままです。']

@dataclass
class Ex:
    before:str; command:str; after:str; obj:str; value:str; old:str; mode:str; group:int

def shape(s):
    return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、：／=\n「」' else c for c in s)

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,len(a)-r,a[l:len(a)-r],b[l:len(b)-r]

def spans(s,lo=1,hi=12):
    return [(i,j,s[i:j]) for i in range(len(s)) for j in range(i+lo,min(len(s),i+hi)+1)
            if not any(c in s[i:j] for c in '。、\n「」')]

def bucket(p,n,k=8): return min(k-1,int(k*p/max(1,n)))

def make_group(seed,gid,mode='seen'):
    r=random.Random(seed+gid*1009); base=r.choice(OBJECTS); alt=r.choice([x for x in OBJECTS if x!=base])
    old=r.choice(VALUES); vals=r.sample([v for v in VALUES if v!=old],3); worlds=[]
    for wi,(obj,val,op) in enumerate([(base,vals[0],OPS[0]),(base,vals[1],OPS[1]),(alt,vals[0],OPS[2]),(base,vals[2],OPS[3])]):
        surf=ALIASES[obj] if mode=='rename' else obj
        before=f'{surf}の現在値は{old}です。{r.choice(FILL)}'
        if mode=='order': cmd=f'{val}へ{op} 対象は{surf}です。'
        elif mode=='lexeme': cmd=f'{surf}を次から{val}扱いにします。'
        elif mode=='nested': cmd=f'依頼は「{surf}を{val}へ{op}」です。'
        elif mode=='omitted': cmd=f'それを{val}へ{op}'
        elif mode=='paragraph': cmd=f'{r.choice(FILL)}\n{surf}を{val}へ{op}\n{r.choice(FILL)}'
        elif mode=='plan': cmd=f'{surf}を{vals[(wi+1)%3]}にする案は撤回し、最終的に{val}へ{op}'
        elif mode=='counterfactual': cmd=f'変更しなければ{surf}は{old}です。実際には{val}へ{op}'
        else: cmd=f'{surf}を{val}へ{op}'
        after=f'{surf}の現在値は{val}です。{r.choice(FILL)}'
        worlds.append(Ex(before,cmd,after,surf,val,old,mode,gid))
    return worlds

def observed_axis(ex):
    l,r,old,new=diff(ex.before,ex.after)
    objs=[x for x in spans(ex.command,2,12) if x[2] in ex.before]
    vals=[x for x in spans(ex.command,1,10) if x[2] in ex.after and x[2] not in ex.before]
    return [(bucket(oi,len(ex.command)),bucket(l,len(ex.before)),bucket(vi,len(ex.command)),len(o)//2,len(old)//2,len(v)//2,shape(o),shape(old),shape(v),r-l)
            for oi,oj,o in objs[:12] for vi,vj,v in vals[:12]]

def predictive_candidates(ex):
    objs=[x for x in spans(ex.command,2,12) if x[2] in ex.before]
    vals=[x for x in spans(ex.command,1,10) if x[2] not in ex.before]
    out=[]
    for oi,oj,o in objs[:10]:
      for vi,vj,v in vals[:10]:
       for si,sj,st in spans(ex.before,1,10):
        sig=(bucket(oi,len(ex.command)),bucket(si,len(ex.before)),bucket(vi,len(ex.command)),len(o)//2,len(st)//2,len(v)//2,shape(o),shape(st),shape(v),sj-si)
        out.append((sig,ex.before[:si]+v+ex.before[sj:],o,v,si,sj))
    return out[:256]

class Model:
    def __init__(self,kind): self.kind=kind; self.axes=[]; self.train_seconds=0; self.completion_hits=0
    def fit(self,groups,shuffle=False):
      t=time.perf_counter(); score=Counter(); wrong=Counter(); hits=Counter(); order=list(range(len(groups)))
      if shuffle: order=order[1:]+order[:1]
      for gi,g in enumerate(groups):
        axes=[observed_axis(x) for x in g]; target=[observed_axis(x) for x in groups[order[gi]]]
        for h in range(len(g)):
          ctx=[a for i,aa in enumerate(axes) if i!=h for a in aa]
          obj=Counter((a[0],a[3],a[6]) for a in ctx); sup=Counter((a[1],a[4],a[7],a[9]) for a in ctx); pay=Counter((a[2],a[5],a[8]) for a in ctx)
          truth=set(target[h]); proposals=[]
          for oa,oc in obj.most_common(3):
           for sa,sc in sup.most_common(3):
            for pa,pc in pay.most_common(3):
             a=(oa[0],sa[0],pa[0],oa[1],sa[1],pa[1],oa[2],sa[2],pa[2],sa[3]); proposals.append((oc+sc+pc,a))
          for rank,a in sorted(proposals,reverse=True)[:24]:
            if a in truth: score[a]+=rank; hits[a]+=1
            else: wrong[a]+=1
      kept=[]
      for a in set(score)|set(wrong):
        if self.kind=='literal' and score[a]>0: kept.append((a,score[a]))
        elif self.kind=='rank1' and score[a]>=wrong[a]: kept.append((a,score[a]-wrong[a]+1))
        elif self.kind=='completion' and hits[a]>=2 and score[a]>2*wrong[a]: kept.append((a,score[a]-wrong[a]))
      self.axes=sorted(kept,key=lambda x:x[1],reverse=True)[:24]; self.completion_hits=sum(hits[a] for a,_ in self.axes); self.train_seconds=time.perf_counter()-t
    def infer(self,e):
      allowed=dict(self.axes); cand=[(allowed[c[0]],)+c for c in predictive_candidates(e) if c[0] in allowed]
      if not cand:return None,0
      cand.sort(key=lambda x:x[0],reverse=True); top=cand[0][0]; tops=[x for x in cand if x[0]==top]
      if len({x[2] for x in tops})!=1:return None,len(cand)
      return tops[0],len(cand)

def evaluate(seed,mode):
    groups=[make_group(seed,i,'seen' if i%3 else 'rename') for i in range(16)]
    test=[make_group(seed+900,i,mode)[0] for i in range(12)]; out={}
    for name,kind,sh in [('literal','literal',False),('rank1','rank1',False),('completion','completion',False),('shuffle','completion',True)]:
      m=Model(kind); m.fit(groups,sh); vals=[]; t=time.perf_counter()
      for e in test:
        p,n=m.infer(e); vals.append({'acc':p is not None and p[2]==e.after,'wrong':p is not None and p[2]!=e.after,'null':p is None,'exact':p is not None and p[4]==e.obj and p[5]==e.value,'candidates':n})
      out[name]={k:statistics.mean(float(v[k]) for v in vals) for k in vals[0]}
      out[name].update({'axes':len(m.axes),'completion_hits':m.completion_hits,'model_bytes':len(pickle.dumps(m)),'training_seconds':m.train_seconds,'inference_ms':(time.perf_counter()-t)*1000/len(test)})
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',default='MEASUREMENTS_CYCLE_041.json'); a=ap.parse_args()
    modes=['seen','order','lexeme','rename','nested','omitted','paragraph','plan','counterfactual']
    raw={str(s):{m:evaluate(s,m) for m in modes} for s in (1,7,19)}; summary={}
    for m in modes:
      summary[m]={}
      for k in ('literal','rank1','completion','shuffle'):
        summary[m][k]={x:statistics.mean(raw[str(s)][m][k][x] for s in (1,7,19)) for x in raw['1'][m][k]}
    payload={'cycle':41,'hypothesis':'Predictive Relation Axes from Leave-One-World-Out Difference Completion','seeds':[1,7,19],'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'training O(G W A^3), inference O(L^3) with axes<=24 and candidate cap 256','final_after_future_used_for_ranking':False,'fixed_ontology_or_slots':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    open(a.output,'w',encoding='utf8').write(json.dumps(payload,ensure_ascii=False,indent=2))
    print(json.dumps(summary['seen'],ensure_ascii=False,indent=2))
if __name__=='__main__': main()
