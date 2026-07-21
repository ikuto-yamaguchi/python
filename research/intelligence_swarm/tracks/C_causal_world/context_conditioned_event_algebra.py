from __future__ import annotations
import json, random, time, resource, difflib, pickle
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

NAMES=['アオ','ユキ','ソラ','ミナ','レン','ナギ','トワ','カイ']
VALUES=['北棚','南箱','窓辺','入口','奥室','机下','庭先','書庫']
FREE_CONTEXTS=['扉が開いている','通路に空きがある','搬送経路が使える','作業許可が出ている']
BLOCK_CONTEXTS=['扉が閉じている','通路が塞がっている','搬送経路が使えない','作業許可が出ていない']
HELD_FREE=['出入口に問題はない','途中を通過できる']
HELD_BLOCK=['出入口を通れない','途中が遮断されている']
STATE_TEMPLATES=['{e}は{v}にある。{c}。','現在の{e}の場所は{v}。状況として{c}。','{e}の所在={v}。周辺条件={c}。']
COMMAND_TEMPLATES=['{e}を{v}へ移す。','{e}の行き先を{v}にする。','{v}へ{e}を運ぶ。']
HELD_COMMANDS=['今いる所から{v}まで、{e}を持っていって。','{e}について、次の所在地を{v}へ変更して。']

@dataclass
class Episode:
    before:str; command:str; after:str; context:str; should_act:bool

def lcs(strings):
    if not strings:return ''
    base=min(strings,key=len); best=''
    for i in range(len(base)):
        for j in range(i+1,len(base)+1):
            s=base[i:j]
            if len(s)>len(best) and all(s in x for x in strings):best=s
    return best

def span_diff(a,b):
    sm=difflib.SequenceMatcher(a=a,b=b,autojunk=False); old=[]; new=[]
    for tag,i1,i2,j1,j2 in sm.get_opcodes():
        if tag!='equal':old.append(a[i1:i2]);new.append(b[j1:j2])
    return ''.join(old),''.join(new)

def new_hint(cmd,before,after):
    c=[]
    for i in range(len(cmd)):
        for j in range(i+1,min(len(cmd),i+18)+1):
            s=cmd[i:j]
            if s in after and s not in before:c.append(s)
    return max(c,key=len,default='')

def extract_binding(before,command,after):
    ident=lcs([before,command,after]); old,new=span_diff(before,after); hint=new_hint(command,before,after) or new
    return {'id':ident,'old':old,'new':new,'hint':hint} if ident and hint else None

def skeleton(text,b):
    out=text
    for value,tag in sorted([(b.get('id',''),'<ID>'),(b.get('old',''),'<OLD>'),(b.get('hint',''),'<NEW>'),(b.get('new',''),'<NEW>')],key=lambda x:-len(x[0])):
        if value:out=out.replace(value,tag)
    return out

def parse_skeleton(text,skel,tags):
    vals={};parts=[];i=0
    while i<len(skel):
        hit=next((t for t in tags if skel.startswith(t,i)),None)
        if hit:parts.append(('tag',hit));i+=len(hit)
        else:
            j=i+1
            while j<len(skel) and not any(skel.startswith(t,j) for t in tags):j+=1
            parts.append(('lit',skel[i:j]));i=j
    pos=0
    for idx,(kind,val) in enumerate(parts):
        if kind=='lit':
            if not text.startswith(val,pos):return None
            pos+=len(val)
        else:
            nxt=next((parts[k][1] for k in range(idx+1,len(parts)) if parts[k][0]=='lit' and parts[k][1]),'')
            end=text.find(nxt,pos) if nxt else len(text)
            if end<0:return None
            vals[val]=text[pos:end];pos=end
    return vals if pos==len(text) else None

def grams(text):return Counter(text[i:i+n] for n in (2,3,4) for i in range(max(0,len(text)-n+1)))
def cosine(a,b):
    dot=sum(v*b.get(k,0) for k,v in a.items());na=sum(v*v for v in a.values())**.5;nb=sum(v*v for v in b.values())**.5
    return dot/(na*nb+1e-12)

def context_residue(before,b):
    x=skeleton(before,b)
    for t in ('<ID>','<OLD>','<NEW>','。','=','現在の','場所は','所在','は','にある','状況として','周辺条件'):x=x.replace(t,'')
    return x.strip()

class IdentityEventOnly:
    def __init__(self):self.views=defaultdict(Counter);self.programs={}
    def fit(self,rows):
        for x in rows:
            if x.before==x.after:continue
            b=extract_binding(x.before,x.command,x.after)
            if not b:continue
            bs=skeleton(x.before,b);cs=skeleton(x.command,b);af=skeleton(x.after,b)
            self.programs[(bs,af)]=(bs,af);self.views[cs][(bs,af)]+=1
        return self
    def predict(self,before,command):
        outs=[]
        for cs,counter in self.views.items():
            cv=parse_skeleton(command,cs,['<ID>','<NEW>'])
            if cv is None:continue
            for key,_ in counter.most_common():
                bs,af=self.programs[key];bv=parse_skeleton(before,bs,['<ID>','<OLD>'])
                if bv is None:continue
                out=af;bind={**bv,**cv}
                for t in ('<ID>','<OLD>','<NEW>'):out=out.replace(t,bind.get(t,''))
                outs.append(out)
        return outs[0] if len(set(outs))==1 else None
    def bytes(self):return len(pickle.dumps(self))
    @property
    def reads(self):return len(self.views)

class ContextConditionedAlgebra(IdentityEventOnly):
    def __init__(self,threshold=.13,margin=.025):
        super().__init__();self.act_contexts=[];self.noop_contexts=[];self.threshold=threshold;self.margin=margin
    def fit(self,rows):
        super().fit(rows)
        for x in rows:
            ident=lcs([x.before,x.command]);hint=new_hint(x.command,x.before,x.command);b={'id':ident,'old':'','new':'','hint':hint}
            residue=context_residue(x.before,b)
            if residue:(self.act_contexts if x.before!=x.after else self.noop_contexts).append(grams(residue))
        return self
    def gate(self,before,command):
        b={'id':lcs([before,command]),'old':'','new':'','hint':new_hint(command,before,command)};q=grams(context_residue(before,b))
        a=max((cosine(q,g) for g in self.act_contexts),default=0);n=max((cosine(q,g) for g in self.noop_contexts),default=0)
        if max(a,n)<self.threshold or abs(a-n)<self.margin:return 'unknown'
        return 'act' if a>n else 'noop'
    def predict(self,before,command):
        gate=self.gate(before,command)
        if gate=='noop':return before
        if gate=='unknown':return None
        return super().predict(before,command)
    def bytes(self):return len(pickle.dumps(self))
    @property
    def reads(self):return len(self.views)+min(16,len(self.act_contexts)+len(self.noop_contexts))

def make_episode(rng,held_command=False,held_context=False,rename=False,act=None):
    e=rng.choice(NAMES);old,new=rng.sample(VALUES,2);should_act=rng.choice([True,False]) if act is None else act
    ctx=rng.choice((HELD_FREE if should_act else HELD_BLOCK) if held_context else (FREE_CONTEXTS if should_act else BLOCK_CONTEXTS))
    st=rng.choice(STATE_TEMPLATES);ct=rng.choice(HELD_COMMANDS if held_command else COMMAND_TEMPLATES)
    before=st.format(e=e,v=old,c=ctx);command=ct.format(e=e,v=new);after=st.format(e=e,v=new if should_act else old,c=ctx)
    ep=Episode(before,command,after,ctx,should_act)
    if rename:
        mapping={**dict(zip(NAMES,['ヌル','キオ','ラマ','セト','ビア','ホク','メラ','ジン'])),**dict(zip(VALUES,['第一域','第二域','第三域','第四域','第五域','第六域','第七域','第八域']))}
        vals=[]
        for s in (ep.before,ep.command,ep.after):
            for a,z in mapping.items():s=s.replace(a,z)
            vals.append(s)
        ep=Episode(*vals,context=ep.context,should_act=ep.should_act)
    return ep

def eval_model(model,rng,n,held_command=False,held_context=False,rename=False,act=None):
    ok=abst=0
    for _ in range(n):
        e=make_episode(rng,held_command,held_context,rename,act);p=model.predict(e.before,e.command);ok+=p==e.after;abst+=p is None
    return ok/n,abst/n

def run(seed,n):
    rng=random.Random(seed);train=[make_episode(rng,act=True) for _ in range(n)]+[make_episode(rng,act=False) for _ in range(max(24,n//2))]
    rows={}
    for name,model in [('event_only',IdentityEventOnly()),('context_algebra',ContextConditionedAlgebra())]:
        t=time.perf_counter();model.fit(train);ts=time.perf_counter()-t;q=random.Random(seed+1000);t=time.perf_counter();seen=eval_model(model,q,80);infer=(time.perf_counter()-t)*1000/80
        rows[name]={'seen_accuracy':seen[0],'seen_abstention':seen[1],'rename_accuracy':eval_model(model,random.Random(seed+1001),80,rename=True)[0],'held_command_accuracy':eval_model(model,random.Random(seed+1002),80,held_command=True)[0],'held_context_accuracy':eval_model(model,random.Random(seed+1003),80,held_context=True)[0],'held_both_accuracy':eval_model(model,random.Random(seed+1004),80,held_command=True,held_context=True)[0],'action_accuracy':eval_model(model,random.Random(seed+1005),80,act=True)[0],'blocked_accuracy':eval_model(model,random.Random(seed+1006),80,act=False)[0],'model_bytes':model.bytes(),'train_seconds':ts,'inference_ms':infer,'candidate_reads':model.reads,'programs':len(model.programs)}
    return rows

def main():
    runs=[]
    for n in (32,128,512):
        for seed in (1,7,19):
            for method,row in run(seed,n).items():runs.append({'train_n':n,'seed':seed,'method':method,**row})
    fields=[k for k in runs[0] if k not in ('train_n','seed','method')];agg={}
    for n in (32,128,512):
        agg[str(n)]={}
        for method in ('event_only','context_algebra'):
            xs=[r for r in runs if r['train_n']==n and r['method']==method];agg[str(n)][method]={k:sum(x[k] for x in xs)/len(xs) for k in fields}
    out={'hypothesis':'Context-conditioned counterfactual event algebra can preserve identity-factored execution while inducing action/no-op branch conditions from outcome-paired context residues without named context slots.','aggregate':agg,'runs':runs,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'free_japanese_integrated_gate':0.0,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    Path(__file__).with_name('results_cycle_006.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(agg,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
