"""Cycle E006: role-structured conditional attractor graphs.

A falsification probe for whether energy relaxation becomes informative only when
candidate graphs generate genuinely different action/no-op worlds.  The learner
uses no pretrained model, morphology, semantic slot labels, fixed entity/value
ontology, RAG, or external LLM.
"""
from __future__ import annotations
import json, random, time, resource, pickle, math, re, statistics
from collections import Counter, defaultdict
from dataclasses import dataclass

ENT=['アオ','ユキ','ソラ','ミナ','レン','ナギ','トワ','カイ']
VAL=['北棚','南箱','窓辺','入口','奥室','机下','庭先','書庫']
ACT_CTX=['扉が開いている','通路に空きがある','搬送経路が使える','作業許可が出ている']
BLOCK_CTX=['扉が閉じている','通路が塞がっている','搬送経路が使えない','作業許可が出ていない']
HELD_ACT=['出入口に問題はない','途中を通過できる']
HELD_BLOCK=['出入口を通れない','途中が遮断されている']
STATE=['{e}は{v}にある。{c}。','現在の{e}の場所は{v}。状況は{c}。','{e}の所在={v}。周辺条件={c}。']
CMD=['{e}を{v}へ移す。','{e}の行き先を{v}にする。','{v}へ{e}を運ぶ。']
HELD_CMD=['今いる所から{v}まで、{e}を持っていって。','{e}について、次の所在地を{v}へ変更して。']

@dataclass
class Ep:
    before:str; command:str; after:str; act:bool

def grams(s): return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))
def cos(a,b):
    d=sum(v*b.get(k,0) for k,v in a.items()); na=sum(v*v for v in a.values())**.5; nb=sum(v*v for v in b.values())**.5
    return d/(na*nb+1e-12)

def lcs(strings):
    base=min(strings,key=len); best=''
    for i in range(len(base)):
      for j in range(i+1,len(base)+1):
        x=base[i:j]
        if len(x)>len(best) and all(x in s for s in strings): best=x
    return best

def affix_diff(a,b):
    i=0
    while i<min(len(a),len(b)) and a[i]==b[i]: i+=1
    j=0
    while j<min(len(a)-i,len(b)-i) and a[-1-j]==b[-1-j]: j+=1
    return a[:i], a[i:len(a)-j if j else len(a)], b[i:len(b)-j if j else len(b)], a[len(a)-j:] if j else ''

def skeleton(text, spans):
    out=text
    for span,tag in sorted([(x,t) for x,t in spans if x], key=lambda z:-len(z[0])): out=out.replace(span,tag,1)
    return out

def parse(text, skel, tags):
    pattern=re.escape(skel)
    for t in tags: pattern=pattern.replace(re.escape(t),f'(?P<{t[1:-1]}>.+?)')
    m=re.fullmatch(pattern,text)
    return m.groupdict() if m else None

def induce(ep):
    if ep.before==ep.after: return None
    ident=lcs([ep.before,ep.command,ep.after]).strip('、。=へをのは ')
    prefix,old,new,suffix=affix_diff(ep.before,ep.after)
    hints=[]
    for i in range(len(ep.command)):
      for j in range(i+1,min(len(ep.command),i+16)+1):
        x=ep.command[i:j]
        if x in ep.after and x not in ep.before: hints.append(x)
    hint=max(hints,key=len,default=new)
    if not ident or not old or not hint:return None
    # The final sentence residue is only an unnamed condition candidate.  This
    # is intentionally audited as a limitation in the report.
    chunks=[x for x in ep.before.split('。') if x]
    ctx=chunks[-1] if len(chunks)>1 else ''
    bs=skeleton(ep.before,[(ident,'<ID>'),(old,'<OLD>'),(ctx,'<CTX>')])
    cs=skeleton(ep.command,[(ident,'<ID>'),(hint,'<NEW>')])
    af=skeleton(ep.after,[(ident,'<ID>'),(hint,'<NEW>'),(ctx,'<CTX>')])
    return bs,cs,af,ident,old,hint

def context_residue(before, bs, vals):
    return vals.get('CTX','')

class FlatScalar:
    def __init__(self): self.views=[]
    def fit(self,rows):
      for ep in rows:
        z=induce(ep)
        if z:self.views.append(z[:3])
      self.views=list(dict.fromkeys(self.views)); return self
    def predict(self,before,command):
      outs=[]
      for bs,cs,af in self.views:
        cv=parse(command,cs,['<ID>','<NEW>']); bv=parse(before,bs,['<ID>','<OLD>','<CTX>'])
        if cv and bv and cv['ID']==bv['ID']:
          out=af
          for t,v in {'<ID>':bv['ID'],'<OLD>':bv['OLD'],'<NEW>':cv['NEW'],'<CTX>':bv.get('CTX','')}.items():out=out.replace(t,v)
          outs.append(out)
      return outs[0] if len(set(outs))==1 else None, 1, len(outs), 0.0
    def bytes(self):return len(pickle.dumps(self.views))

class RoleAttractor:
    def __init__(self):
      self.ops={}; self.act_ctx=defaultdict(list); self.noop_ctx=defaultdict(list)
    def fit(self,rows):
      changed=[x for x in rows if x.before!=x.after]
      for ep in changed:
        z=induce(ep)
        if not z:continue
        bs,cs,af,ident,old,new=z; key=(bs,cs,af); self.ops[key]=self.ops.get(key,0)+1
      for ep in rows:
        for key in self.ops:
          bs,cs,af=key; cv=parse(ep.command,cs,['<ID>','<NEW>']); bv=parse(ep.before,bs,['<ID>','<OLD>','<CTX>'])
          if cv and bv and cv['ID']==bv['ID']:
            r=context_residue(ep.before,bs,bv)
            (self.act_ctx if ep.before!=ep.after else self.noop_ctx)[key].append(grams(r))
      return self
    def candidates(self,before,command):
      c=[]
      for key,support in self.ops.items():
        bs,cs,af=key; cv=parse(command,cs,['<ID>','<NEW>']); bv=parse(before,bs,['<ID>','<OLD>','<CTX>'])
        if not cv or not bv or cv['ID']!=bv['ID']:continue
        bind={'<ID>':bv['ID'],'<OLD>':bv['OLD'],'<NEW>':cv['NEW'],'<CTX>':bv.get('CTX','')}
        action=af
        for t,v in bind.items():action=action.replace(t,v)
        residue=grams(context_residue(before,bs,bv))
        a=max((cos(residue,g) for g in self.act_ctx[key]),default=0)
        n=max((cos(residue,g) for g in self.noop_ctx[key]),default=0)
        # These branches are executable and produce different worlds.
        c.append({'key':key,'branch':'action','output':action,'energy':1-a-0.01*min(support,5)})
        c.append({'key':key,'branch':'noop','output':before,'energy':1-n-0.01*min(support,5)})
      return c
    def predict(self,before,command):
      c=self.candidates(before,command)
      if not c:return None,0,0,0.0
      current=0; sweeps=0
      for _ in range(8):
        sweeps+=1; best=min(range(len(c)),key=lambda i:c[i]['energy'])
        if best==current:break
        current=best
      ordered=sorted(x['energy'] for x in c)
      margin=ordered[1]-ordered[0] if len(ordered)>1 else 0
      if margin<0.025:return None,sweeps,len(c),margin
      return c[current]['output'],sweeps,len(c),margin
    def bytes(self):return len(pickle.dumps((self.ops,dict(self.act_ctx),dict(self.noop_ctx))))

def make(r,held_cmd=False,held_ctx=False,rename=False,act=None,nested=False,multipara=False,plan_change=False):
    e=r.choice(ENT); old,new,new2=r.sample(VAL,3); act=r.choice([True,False]) if act is None else act
    ctx=r.choice((HELD_ACT if act else HELD_BLOCK) if held_ctx else (ACT_CTX if act else BLOCK_CTX))
    sf=r.choice(STATE); cf=r.choice(HELD_CMD if held_cmd else CMD)
    before=sf.format(e=e,v=old,c=ctx); command=cf.format(e=e,v=new); after=sf.format(e=e,v=new if act else old,c=ctx)
    if nested: command='もし安全確認が終わったなら、'+command+'ただし担当者の許可も必要です。'
    if multipara: before='前の議論を踏まえます。\n'+before; command='次の段落の指示です。\n'+command
    if plan_change: command=command+' いや、やはり'+new2+'に変更してください。'; after=sf.format(e=e,v=new2 if act else old,c=ctx)
    if rename:
      mp={**dict(zip(ENT,['ヌル','キオ','ラマ','セト','ビア','ホク','メラ','ジン'])),**dict(zip(VAL,['第一域','第二域','第三域','第四域','第五域','第六域','第七域','第八域']))}
      for a,b in mp.items():before=before.replace(a,b);command=command.replace(a,b);after=after.replace(a,b)
    return Ep(before,command,after,act)

def eval_model(m,r,n=120,**kw):
    ok=ab=0;sweeps=[];active=[];marg=[];t=time.perf_counter()
    for _ in range(n):
      ep=make(r,**kw);p,sw,ac,ma=m.predict(ep.before,ep.command);ok+=p==ep.after;ab+=p is None;sweeps.append(sw);active.append(ac);marg.append(ma)
    return {'accuracy':ok/n,'abstention':ab/n,'ms':(time.perf_counter()-t)*1000/n,'sweeps':statistics.mean(sweeps),'active':statistics.mean(active),'margin':statistics.mean(marg)}

def run(seed,n):
    r=random.Random(seed);train=[make(r,act=True) for _ in range(n)]+[make(r,act=False) for _ in range(max(24,n//2))]
    out={}
    for name,m in [('flat',FlatScalar()),('role_attractor',RoleAttractor())]:
      t=time.perf_counter();m.fit(train);ts=time.perf_counter()-t
      q=lambda z:random.Random(seed+z)
      out[name]={
       'seen':eval_model(m,q(1)), 'action_only':eval_model(m,q(8),act=True), 'blocked_only':eval_model(m,q(9),act=False), 'rename':eval_model(m,q(2),rename=True),
       'held_command':eval_model(m,q(3),held_cmd=True), 'held_context':eval_model(m,q(4),held_ctx=True),
       'nested':eval_model(m,q(5),nested=True), 'multi_paragraph':eval_model(m,q(6),multipara=True),
       'plan_change':eval_model(m,q(7),plan_change=True), 'model_bytes':m.bytes(),'train_seconds':ts,
       'ops':len(getattr(m,'ops',getattr(m,'views',[]))) }
    return out

def main():
  raw={str(n):[run(s,n) for s in (1,7,19)] for n in (48,192,384)}; summary={}
  for n,runs in raw.items():
    summary[n]={}
    for model in ('flat','role_attractor'):
      summary[n][model]={}
      for split in ('seen','action_only','blocked_only','rename','held_command','held_context','nested','multi_paragraph','plan_change'):
        summary[n][model][split]={k:statistics.mean(x[model][split][k] for x in runs) for k in ('accuracy','abstention','ms','sweeps','active','margin')}
      for k in ('model_bytes','train_seconds','ops'):summary[n][model][k]=statistics.mean(x[model][k] for x in runs)
  payload={'hypothesis':'Role-Structured Conditional Attractor Graphs','seeds':[1,7,19],'train_sizes':[48,192,384],'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'free_japanese_integrated_gate':0.0,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
  print(json.dumps(payload,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
