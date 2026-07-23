from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict, Counter
import argparse,json,pickle,random,resource,statistics,time
OBJECTS=['青い箱','赤い箱','小型端末','大型端末','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','試料甲':'サンプル甲','試料乙':'サンプル乙'}
VALUES=['棚A','棚B','棚C','棚D','待機','処理中','完了','保留','担当一','担当二']
FILL=['補助記録は維持します。','別系統は変更しません。','監査メモはそのままです。']
@dataclass
class Ex: before:str; command:str; after:str; future:str; obj:str; old:str; new:str; mode:str
@dataclass(frozen=True)
class Proposal: sb:int; sw:int; vb:int; vw:int; ob:int; ow:int; ss:str; vs:str; os:str
@dataclass
class Diagram: p:Proposal; support:int=0; forward:int=0; reverse:int=0; commute:int=0; wrong:int=0; credit:float=0.0

def sh(s):return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、：／=\n 「」' else c for c in s)
def state(o,v,form,f):
    if form==0:return f'{o}の現在値は{v}です。{f}'
    if form==1:return f'{o}：設定={v}／補助=維持。{f}'
    return f'対象{o}について、記録上の値は「{v}」。{f}'
def build(seed,n,mode):
    r=random.Random(seed); out=[]
    for _ in range(n):
        c=r.choice(OBJECTS); o=ALIASES[c] if mode=='rename' else c; old,new=r.sample(VALUES,2); form=1 if mode=='alternate' else 2 if mode=='alternate2' else 0; f=r.choice(FILL)
        before=state(o,old,form,f); cmd=f'{o}の値を{new}へ変更してください。'
        if mode=='order':cmd=f'{new}へ変更してください。対象は{o}です。'
        elif mode=='lexeme':cmd=f'対象{o}は以後{new}扱いにします。'
        elif mode=='nested':cmd=f'依頼内容は「{o}の値を{new}へ変更してください」です。'
        elif mode=='omitted':cmd=f'それを{new}へ変更してください。'
        elif mode=='paragraph':cmd=f'前段説明。{r.choice(FILL)}\n{cmd}\n後段注記。'
        elif mode=='plan':
            alt=r.choice([x for x in VALUES if x not in (old,new)]);cmd=f'{o}を{alt}にする案は撤回します。最終的には{new}へ変更してください。'
        elif mode=='counterfactual':cmd=f'もし変更しなければ{o}は{old}のままです。実際には{o}を{new}へ変更してください。'
        out.append(Ex(before,cmd,state(o,new,form,f),f'次の観測でも{o}は{new}で、変更対象外は維持されます。',o,old,new,mode))
    return out

def bucket(pos,L):return round(16*pos/max(1,L))
def locate(text,b,w,shape):
    t=round(b*len(text)/16); z=[]
    for a in range(max(0,t-3),min(len(text),t+4)):
        for ww in range(max(1,w-2),min(14,w+3)):
            if a+ww<=len(text) and sh(text[a:a+ww])==shape:z.append((a,a+ww,text[a:a+ww]))
    return z

def extract(e):
    si=e.before.find(e.old);vi=e.command.find(e.new);oi=e.command.find(e.obj)
    if min(si,vi)<0:return None
    if oi<0: oi=0; ow=0; os=''
    else: ow=len(e.obj);os=sh(e.obj)
    return Proposal(bucket(si,len(e.before)),len(e.old),bucket(vi,len(e.command)),len(e.new),bucket(oi,len(e.command)),ow,sh(e.old),sh(e.new),os)

def apply_state(e,p,v):
    return [(e.before[:a]+v+e.before[b:],a,b) for a,b,_ in locate(e.before,p.sb,p.sw,p.ss)]
def values(e,p):return sorted({x for _,_,x in locate(e.command,p.vb,p.vw,p.vs) if x not in e.before})[:8]
def objects(e,p):return sorted({x for _,_,x in locate(e.command,p.ob,p.ow,p.os)})[:6] if p.ow else ['']
def swap_cmd(e,p,newv):
    loc=locate(e.command,p.vb,p.vw,p.vs)
    return [e.command[:a]+newv+e.command[b:] for a,b,_ in loc]

class Model:
  def __init__(self,mode):self.mode=mode;self.diagrams=[];self.raw=0;self.audit=0;self.train_s=0
  def fit(self,ind,probe,shuffle=False):
    t=time.perf_counter();cnt=Counter(x for e in ind if (x:=extract(e)));self.raw=len(cnt);obs=[e.after for e in probe]
    if shuffle:obs=obs[1:]+obs[:1]
    ds=[]
    for p,sup in cnt.most_common(48):
      fwd=rev=com=wrong=0
      for e,o in zip(probe,obs):
        vs=values(e,p); os=objects(e,p)
        for v in vs:
          self.audit+=1
          preds=apply_state(e,p,v)
          for pred,a,b in preds:
            ok=pred==o
            fwd+=ok;wrong+=not ok
            old=e.before[a:b]; rev+=int(ok and o[:a]+old+o[a+len(v):]==e.before)
            for alt in vs:
              if alt==v:continue
              cands=swap_cmd(e,p,alt)
              direct={x[0] for x in apply_state(e,p,alt)}
              com+=int(bool(cands) and bool(direct) and (not p.ow or bool(os)))
      accept = fwd>=2 if self.mode=='forward' else fwd>=2 and rev>=fwd and com>=fwd
      if accept:
        d=Diagram(p,sup,fwd,rev,com,wrong);d.credit=(3*fwd+rev+min(com,2*fwd)-wrong)/(1+fwd+wrong);ds.append(d)
    self.diagrams=sorted(ds,key=lambda d:(d.credit,d.forward,d.commute),reverse=True)[:32];self.train_s=time.perf_counter()-t
  def predict(self,e):
    out=[]
    for i,d in enumerate(self.diagrams):
      for v in values(e,d.p):
        for pred,a,b in apply_state(e,d.p,v):
          score=d.credit+int(v in e.command)+.1*d.commute-.02*(b-a);out.append((score,pred,a,b,v,i))
    if not out:return None,0
    out.sort(reverse=True);best=out[0][0];tops=[x for x in out if best-x[0]<.4]
    if len({x[1] for x in tops})>1:return None,len(out)
    return tops[0],len(out)

def eval(m,test):
 c=w=n=exact=pair=0;cs=[];t=time.perf_counter()
 for e in test:
  p,k=m.predict(e);cs.append(k)
  if p is None:n+=1;continue
  _,pred,a,b,v,_=p;c+=pred==e.after;w+=pred!=e.after;ti=e.before.find(e.old);exact+=a==ti and b==ti+len(e.old);pair+=exact and v==e.new
 N=len(test);return {'accuracy':c/N,'wrong_commit':w/N,'null_rate':n/N,'exact_boundary':exact/N,'object_value_pair':pair/N,'mean_candidates':statistics.mean(cs),'diagrams':len(m.diagrams),'raw_proposals':m.raw,'probe_audits':m.audit,'model_bytes':len(pickle.dumps(m)),'training_seconds':m.train_s,'inference_ms':(time.perf_counter()-t)*1000/N}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='MEASUREMENTS_CYCLE_035.json');a=ap.parse_args();modes=['seen','order','lexeme','rename','alternate','alternate2','nested','omitted','paragraph','plan','counterfactual'];methods=['factorized','forward','commutator','shuffle'];raw={}
 for seed in (1,7,19):
  train=build(seed,72,'seen')+build(seed+1,36,'rename')+build(seed+2,36,'alternate');ind,probe=train[:96],train[96:];models={}
  for method in methods:
   x=Model('forward' if method in ('factorized','forward') else 'commutator');x.fit(ind,probe,shuffle=method=='shuffle');models[method]=x
  raw[str(seed)]={mode:{method:eval(x,build(seed+999,24,mode)) for method,x in models.items()} for mode in modes}
 summary={mode:{method:{k:statistics.mean(raw[str(s)][mode][method][k] for s in (1,7,19)) for k in raw['1'][mode][method]} for method in methods} for mode in modes}
 payload={'cycle':35,'hypothesis':'Asymmetric Causal Direction from Command-State Intervention Commutators','seeds':[1,7,19],'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'proposal O(NL), probe commutator O(QFVO L), inference O(FVL)','final_test_outcomes_used_for_ranking':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
 open(a.output,'w',encoding='utf-8').write(json.dumps(payload,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
