from __future__ import annotations
import json, random, time, resource, difflib, statistics
from dataclasses import dataclass, asdict
from collections import defaultdict

ENTITIES = ["アルファ","ベータ","ガンマ","デルタ","イプシロン","ゼータ"]
VALUES = ["棚A","棚B","棚C","棚D"]
ACTIONS = {
    "move": ["{e}を{v}へ移す","{e}を{v}に移動する","{e}を{v}まで運ぶ"],
    "set": ["{e}の場所を{v}にする","{e}の配置先を{v}へ変更する","{e}は{v}に置く"],
}
NOOPS = ["何もしない","そのままにする","変更しない"]
STATE_PATTERNS = ["{e}は{v}にある。","{e}の場所は{v}です。","{v}には{e}がある。"]

def state(e,v,p=0): return STATE_PATTERNS[p%len(STATE_PATTERNS)].format(e=e,v=v)
def chargrams(s,n=2): return {s[i:i+n] for i in range(max(0,len(s)-n+1))} or {s}
def sim(a,b):
    A=chargrams(a,2)|chargrams(a,3); B=chargrams(b,2)|chargrams(b,3)
    return len(A&B)/max(1,len(A|B))
def extract_identity(before, command):
    commons=[]
    for L in range(2,min(12,len(command))+1):
        for i in range(len(command)-L+1):
            x=command[i:i+L]
            if x in before and x not in "。、「」": commons.append(x)
    return max(commons,key=len) if commons else ""
def abstract_state(before, ident):
    s=before.replace(ident,"<ID>") if ident else before
    for e in ENTITIES: s=s.replace(e,"<ID>")
    for v in VALUES: s=s.replace(v,"<VAL>")
    return s

@dataclass
class Row:
    seed:int; scale:int; method:str; normal:float; rename:float; paraphrase:float
    confound_reject:float; reverse:float; two_step:float; model_bytes:int
    peak_rss_kib:int; train_s:float; infer_ms:float; rules:int; reads:float

class CorrelationModel:
    def __init__(self): self.examples=[]
    def fit(self,data):
        t=time.perf_counter(); self.examples=list(data); return time.perf_counter()-t
    def predict(self,before,cmd):
        if not self.examples: return None
        return max(self.examples,key=lambda x:sim(cmd,x['cmd']))['after']
    def size(self): return len(json.dumps(self.examples,ensure_ascii=False).encode())

class NecessityModel:
    def __init__(self): self.groups=defaultdict(list)
    def fit(self,data):
        t=time.perf_counter(); noops=set(); acted=[]
        for x in data:
            ident=extract_identity(x['before'],x['cmd'])
            frame=abstract_state(x['before'],ident)
            if x['kind']=='noop' and x['before']==x['after']: noops.add(frame)
            elif x['before']!=x['after']: acted.append((frame,x))
        for frame,x in acted:
            if frame in noops: self.groups[frame].append(x)
        return time.perf_counter()-t
    def predict(self,before,cmd):
        ident=extract_identity(before,cmd); frame=abstract_state(before,ident)
        if frame not in self.groups: return None
        vals=[v for v in VALUES if v in cmd]
        current=[v for v in VALUES if v in before]
        if not ident or not vals or not current: return None
        return before.replace(current[0],vals[-1])
    def verify(self,before,cmd,observed_after): return self.predict(before,cmd)==observed_after
    def size(self): return len(json.dumps({k:len(v) for k,v in self.groups.items()},ensure_ascii=False).encode())

def generate(seed,scale):
    rng=random.Random(seed); data=[]
    for _ in range(scale):
        e=rng.choice(ENTITIES[:4]); old,new=rng.sample(VALUES,2); p=rng.randrange(3)
        family=rng.choice(list(ACTIONS)); template=rng.choice(ACTIONS[family][:2])
        before=state(e,old,p); cmd=template.format(e=e,v=new); after=state(e,new,p)
        data += [{"before":before,"cmd":cmd,"after":after,"kind":"act"},
                 {"before":before,"cmd":rng.choice(NOOPS),"after":before,"kind":"noop"}]
    return data

def cases(seed,n=60):
    rng=random.Random(seed); out={k:[] for k in ['normal','rename','paraphrase','confound','reverse','two_step']}
    for _ in range(n):
        e=rng.choice(ENTITIES[:4]); old,new=rng.sample(VALUES,2); p=rng.randrange(3)
        out['normal'].append((state(e,old,p),ACTIONS['move'][0].format(e=e,v=new),state(e,new,p)))
        ue='未知'+str(rng.randrange(1000))
        out['rename'].append((state(ue,old,p),ACTIONS['move'][0].format(e=ue,v=new),state(ue,new,p)))
        out['paraphrase'].append((state(e,old,p),ACTIONS['move'][2].format(e=e,v=new),state(e,new,p)))
        out['confound'].append((state(e,old,p),ACTIONS['move'][0].format(e=e,v=new),state(e,old,p)))
        out['reverse'].append((state(e,new,p),ACTIONS['move'][1].format(e=e,v=old),state(e,old,p)))
        mid,last=rng.sample([v for v in VALUES if v!=old],2)
        out['two_step'].append((state(e,old,p),[ACTIONS['move'][0].format(e=e,v=mid),ACTIONS['set'][1].format(e=e,v=last)],state(e,last,p)))
    return out

def evaluate(model,cs):
    result={}; reads=[]
    for key,items in cs.items():
        ok=0
        for before,cmd,gold in items:
            if key=='two_step':
                pred=before
                for c in cmd:
                    pred=model.predict(pred,c)
                    if pred is None: break
            else: pred=model.predict(before,cmd)
            if key=='confound': ok += int(hasattr(model,'verify') and not model.verify(before,cmd,gold))
            else: ok += int(pred==gold)
            reads.append(len(getattr(model,'groups',getattr(model,'examples',[]))))
        result[key]=ok/len(items)
    return result,statistics.mean(reads)

def run():
    rows=[]
    for scale in (32,128,512):
        for seed in (1,7,19):
            data=generate(seed,scale); cs=cases(seed+900)
            for name,model in [('correlation',CorrelationModel()),('necessity',NecessityModel())]:
                train_s=model.fit(data); t=time.perf_counter(); r,reads=evaluate(model,cs)
                infer=(time.perf_counter()-t)*1000/sum(len(v) for v in cs.values())
                rows.append(Row(seed,scale,name,r['normal'],r['rename'],r['paraphrase'],r['confound'],r['reverse'],r['two_step'],model.size(),resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,train_s,infer,len(getattr(model,'groups',getattr(model,'examples',[]))),reads))
    agg={}
    for name in ('correlation','necessity'):
        agg[name]={}
        for scale in (32,128,512):
            rr=[x for x in rows if x.method==name and x.scale==scale]
            agg[name][str(scale)]={f'{m}_mean':statistics.mean(getattr(x,m) for x in rr) for m in ['normal','rename','paraphrase','confound_reject','reverse','two_step','model_bytes','peak_rss_kib','train_s','infer_ms','rules','reads']}
    return {'hypothesis':'Promote event edges only when matched action/no-op contrasts support necessity after quotienting episode identity.','audit_failure':'Target value extraction still uses a finite VALUES set; therefore positive task scores are not valid open-set causal induction evidence.','claims':{'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False},'aggregate':agg,'runs':[asdict(x) for x in rows]}

if __name__=='__main__': print(json.dumps(run(),ensure_ascii=False,indent=2))
