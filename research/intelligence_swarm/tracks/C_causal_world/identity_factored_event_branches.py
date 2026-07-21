from __future__ import annotations
import json, random, time, resource, difflib, sys
from dataclasses import dataclass, asdict
from collections import Counter, defaultdict
from pathlib import Path

NAMES=['アオ','ユキ','ソラ','ミナ','レン','ナギ','トワ','カイ']
VALUES=['北棚','南箱','窓辺','入口','奥室','机下','庭先','書庫']
MODES=['通常','固定中']
STATE_TEMPLATES=[
    '{e}は{v}にある。状態は{m}。',
    '現在の{e}の場所は{v}。状態は{m}。',
    '{e}の所在={v}。状態={m}。',
]
COMMAND_TEMPLATES=[
    '{e}を{v}へ移す。',
    '{e}の行き先を{v}にする。',
    '{v}へ{e}を運ぶ。',
]
HELD_COMMANDS=[
    '今いる所から{v}まで、{e}を持っていって。',
    '{e}について、次の所在地を{v}へ変更して。',
]

@dataclass
class Bundle:
    before:str; command:str; after:str; noop_after:str
    reverse_command:str; reverse_after:str
    other_before:str; other_command:str; other_after:str
    composed_command:str; composed_after:str


def longest_common_substring(strings):
    if not strings: return ''
    base=min(strings,key=len); best=''
    for i in range(len(base)):
        for j in range(i+1,len(base)+1):
            s=base[i:j]
            if len(s)>len(best) and all(s in x for x in strings): best=s
    return best


def replace_span_diff(a,b):
    sm=difflib.SequenceMatcher(a=a,b=b,autojunk=False)
    old=[]; new=[]
    for tag,i1,i2,j1,j2 in sm.get_opcodes():
        if tag!='equal': old.append(a[i1:i2]); new.append(b[j1:j2])
    return ''.join(old), ''.join(new)


def best_new_hint(command,before,after):
    cands=[]
    for i in range(len(command)):
        for j in range(i+1,min(len(command),i+16)+1):
            s=command[i:j]
            if s in after and s not in before: cands.append(s)
    return max(cands,key=len,default='')


def extract_binding(before,command,after):
    ident=longest_common_substring([before,command,after])
    old,new=replace_span_diff(before,after)
    hint=best_new_hint(command,before,after) or new
    if not ident or not hint: return None
    if len(ident)>12:
        shorter=[ident[i:j] for i in range(len(ident)) for j in range(i+1,len(ident)+1)
                 if ident[i:j] in command and ident[i:j] not in (hint,old,new)]
        ident=max(shorter,key=len,default=ident)
    return {'id':ident,'old':old,'new':new,'hint':hint}


def skeleton(text,b):
    out=text
    for value,tag in sorted([(b['id'],'<ID>'),(b['old'],'<OLD>'),(b['hint'],'<NEW>'),(b['new'],'<NEW>')], key=lambda x:-len(x[0])):
        if value: out=out.replace(value,tag)
    return out


def parse_by_skeleton(text,skel,tags):
    vals={}; parts=[]; i=0
    while i<len(skel):
        hit=None
        for tag in tags:
            if skel.startswith(tag,i): hit=tag; break
        if hit:
            parts.append(('tag',hit)); i+=len(hit)
        else:
            j=i+1
            while j<len(skel) and not any(skel.startswith(t,j) for t in tags): j+=1
            parts.append(('lit',skel[i:j])); i=j
    pos=0
    for idx,(kind,val) in enumerate(parts):
        if kind=='lit':
            if not text.startswith(val,pos): return None
            pos+=len(val)
        else:
            nextlit=''
            for k in range(idx+1,len(parts)):
                if parts[k][0]=='lit' and parts[k][1]: nextlit=parts[k][1]; break
            end=text.find(nextlit,pos) if nextlit else len(text)
            if end<0:return None
            vals[val]=text[pos:end]; pos=end
    return vals if pos==len(text) else None


class SurfaceMemory:
    def __init__(self): self.rows=[]
    def fit(self,bundles): self.rows=[(b.before,b.command,b.after) for b in bundles[:128]]
    def predict(self,before,command):
        if not self.rows:return None
        q=before+'|'+command
        row=max(self.rows,key=lambda r:difflib.SequenceMatcher(a=q,b=r[0]+'|'+r[1],autojunk=False).ratio())
        return row[2]
    def bytes(self):return len(json.dumps(self.rows,ensure_ascii=False).encode())
    @property
    def reads(self):return len(self.rows)


class BindingSeparatedCausalProgram:
    def __init__(self):
        self.command_views=defaultdict(Counter)
        self.programs={}
        self.noop_contexts=Counter()
        self.rejected=0

    def fit(self,bundles):
        for x in bundles:
            if x.before==x.after:
                ident=longest_common_substring([x.before,x.command])
                if ident:
                    hint=best_new_hint(x.command,x.before,x.command) or ''
                    b={'id':ident,'old':'','new':'','hint':hint}
                    self.noop_contexts[(skeleton(x.before,b),skeleton(x.command,b))]+=1
                continue
            b=extract_binding(x.before,x.command,x.after)
            if not b:
                self.rejected+=1; continue
            bs=skeleton(x.before,b); cs=skeleton(x.command,b); a=skeleton(x.after,b)
            key=(bs,a)
            self.programs[key]=(bs,a)
            self.command_views[cs][key]+=1
        valid=set()
        for cs,c in self.command_views.items():
            valid.update(k for k,n in c.items() if n>=2)
        self.programs={k:v for k,v in self.programs.items() if k in valid}
        self.command_views={cs:Counter({k:n for k,n in c.items() if k in self.programs}) for cs,c in self.command_views.items()}
        self.command_views={k:v for k,v in self.command_views.items() if v}

    def _match_noop(self,before,command):
        for bs,cs in self.noop_contexts:
            ident=longest_common_substring([before,command])
            if not ident:continue
            b={'id':ident,'old':'','new':'','hint':''}
            if skeleton(before,b)==bs and skeleton(command,b)==cs:return True
        return False

    def predict(self,before,command):
        if self._match_noop(before,command): return before
        outs=[]
        for cs,counter in self.command_views.items():
            vals=parse_by_skeleton(command,cs,['<ID>','<NEW>'])
            if vals is None:continue
            for key,_ in counter.most_common():
                bs,af=self.programs[key]
                oldvals=parse_by_skeleton(before,bs,['<ID>','<OLD>'])
                if oldvals is None:continue
                bind={**oldvals,**vals}
                out=af
                for tag in ('<ID>','<OLD>','<NEW>'):out=out.replace(tag,bind.get(tag,''))
                outs.append(out)
        return outs[0] if len(set(outs))==1 else None

    def bytes(self):
        obj={'views':{k:[(list(x),n) for x,n in v.items()] for k,v in self.command_views.items()},'programs':[(list(k),list(v)) for k,v in self.programs.items()],'noop':[(list(k),n) for k,n in self.noop_contexts.items()]}
        return len(json.dumps(obj,ensure_ascii=False).encode())

    @property
    def reads(self):return len(self.command_views)+len(self.noop_contexts)


def make_bundle(rng,held=False,mode=None,rename=False):
    e,other=rng.sample(NAMES,2); old,new,new2,other_old,other_new=rng.sample(VALUES,5)
    m=mode or rng.choice(MODES)
    st=rng.choice(STATE_TEMPLATES); ct=rng.choice(HELD_COMMANDS if held else COMMAND_TEMPLATES)
    before=st.format(e=e,v=old,m=m); command=ct.format(e=e,v=new)
    after=before if m=='固定中' else st.format(e=e,v=new,m=m)
    noop=before
    reverse_command=ct.format(e=e,v=old); reverse_after=before
    other_before=st.format(e=other,v=other_old,m='通常'); other_command=ct.format(e=other,v=other_new); other_after=st.format(e=other,v=other_new,m='通常')
    composed_command=ct.format(e=e,v=new)+' '+ct.format(e=e,v=new2)
    composed_after=before if m=='固定中' else st.format(e=e,v=new2,m=m)
    b=Bundle(before,command,after,noop,reverse_command,reverse_after,other_before,other_command,other_after,composed_command,composed_after)
    if rename:
        mapping={**dict(zip(NAMES,['ヌル','キオ','ラマ','セト','ビア','ホク','メラ','ジン'])),**dict(zip(VALUES,['第一域','第二域','第三域','第四域','第五域','第六域','第七域','第八域']))}
        vals=[]
        for s in asdict(b).values():
            for a,z in mapping.items():s=s.replace(a,z)
            vals.append(s)
        b=Bundle(*vals)
    return b


def predict_composed(model,b):
    cur=b.before
    for cmd in [x.strip()+'。' for x in b.composed_command.split('。') if x.strip()]:
        out=model.predict(cur,cmd)
        if out is None:return None
        cur=out
    return cur


def eval_model(model,rng,n,held=False,rename=False,mode=None,kind='normal'):
    ok=0
    for _ in range(n):
        b=make_bundle(rng,held=held,rename=rename,mode=mode)
        if kind=='normal': pred=model.predict(b.before,b.command); target=b.after
        elif kind=='reverse': pred=model.predict(b.after,b.reverse_command); target=b.reverse_after
        elif kind=='other': pred=model.predict(b.other_before,b.other_command); target=b.other_after
        elif kind=='compose': pred=predict_composed(model,b); target=b.composed_after
        else: raise ValueError(kind)
        ok+=pred==target
    return ok/n


def run(seed,n):
    rng=random.Random(seed)
    train=[make_bundle(rng,mode='通常') for _ in range(n)] + [make_bundle(rng,mode='固定中') for _ in range(max(8,n//4))]
    rows={}
    for name,model in [('surface',SurfaceMemory()),('binding_branch',BindingSeparatedCausalProgram())]:
        t=time.perf_counter();model.fit(train);train_s=time.perf_counter()-t
        q=random.Random(seed+1000);t=time.perf_counter();seen=eval_model(model,q,40,mode='通常');infer=(time.perf_counter()-t)*1000/40
        rows[name]={
          'seen':seen,
          'rename':eval_model(model,random.Random(seed+1001),40,rename=True,mode='通常'),
          'held_syntax':eval_model(model,random.Random(seed+1002),40,held=True,mode='通常'),
          'pre_observation_noop':eval_model(model,random.Random(seed+1003),40,mode='固定中'),
          'reverse':eval_model(model,random.Random(seed+1004),40,mode='通常',kind='reverse'),
          'other_identity':eval_model(model,random.Random(seed+1005),40,mode='通常',kind='other'),
          'two_step':eval_model(model,random.Random(seed+1006),40,mode='通常',kind='compose'),
          'model_bytes':model.bytes(),'train_seconds':train_s,'inference_ms':infer,'candidate_reads':model.reads,
          'programs':len(getattr(model,'programs',{}))
        }
    return rows


def main():
    runs=[]
    for n in (32,128,512):
      for seed in (1,7,19):
        for method,row in run(seed,n).items():runs.append({'train_n':n,'seed':seed,'method':method,**row})
    fields=['seen','rename','held_syntax','pre_observation_noop','reverse','other_identity','two_step','model_bytes','train_seconds','inference_ms','candidate_reads','programs']
    agg={}
    for n in (32,128,512):
      agg[str(n)]={}
      for method in ('surface','binding_branch'):
        s=[r for r in runs if r['train_n']==n and r['method']==method]
        agg[str(n)][method]={k:sum(x[k] for x in s)/len(s) for k in fields}
    report={'hypothesis':'Identity-factored executable event programs can reuse one causal transition across action/no-op/reverse/other/composition branches without a predefined entity/value ontology.','aggregate':agg,'runs':runs,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    Path(__file__).with_name('results_cycle_005.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(agg,ensure_ascii=False,indent=2))


def self_test():
    rng=random.Random(2); train=[make_bundle(rng,mode='通常') for _ in range(128)]
    m=BindingSeparatedCausalProgram();m.fit(train);assert m.programs
    assert eval_model(m,random.Random(9),40,mode='通常')>.4
    print('self-test ok')


if __name__=='__main__':
    self_test() if '--self-test' in sys.argv else main()
