from __future__ import annotations
import difflib, json, pickle, random, resource, statistics, time
from collections import Counter
from dataclasses import dataclass

ENTITIES=['試料A','試料B','青箱','赤容器','装置甲','装置乙','未知体X','ミラコフ']
VALUES=['棚B','保管庫C','検査台D','奥区画','20度','30度','停止状態','運転状態']
TRAIN_FORMS=[
    '{e}を{v}へ移して', '{v}へ{e}を移動して', '{e}の置き場を{v}に変更して',
    '{e}を{v}に設定して', '{v}にして、対象は{e}'
]
HELD_ORDER=['対象は{e}、行き先は{v}', '{v}が最終値で、対象は{e}', '{e}については最終的に{v}']
HELD_SYNONYM=['{e}を{v}まで運んで', '{e}を{v}へ配置し直して', '{e}の値を{v}へ調整して']
STATE_FORMS=['{e}は{v}です。','現在の{e}は{v}。','記録：{e}→{v}。']
NOOPS=['{e}はそのままにして','{e}を確認して','{e}には触れないで']

@dataclass
class Ep:
    before:str; command:str; after:str; changed:bool

def make(seed,n,mode='train'):
    r=random.Random(seed); out=[]
    forms=TRAIN_FORMS if mode=='train' else HELD_ORDER if mode=='order' else HELD_SYNONYM
    ents=ENTITIES[:6] if mode!='rename' else ENTITIES[6:]
    for i in range(n):
        e=r.choice(ents); old,new=r.sample(VALUES,2); sf=i%len(STATE_FORMS)
        b=STATE_FORMS[sf].format(e=e,v=old)
        if mode=='confound' and i%2==0:
            c=r.choice(NOOPS).format(e=e); a=b; ch=False
        else:
            c=r.choice(forms).format(e=e,v=new); a=STATE_FORMS[sf].format(e=e,v=new); ch=True
        out.append(Ep(b,c,a,ch))
    return out

def lcs_blocks(a,b,minlen=2):
    sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
    return [a[x.a:x.a+x.size] for x in sm.get_matching_blocks() if x.size>=minlen]

def diff_one(b,a):
    old=[]; new=[]
    for tag,i1,i2,j1,j2 in difflib.SequenceMatcher(None,b,a,autojunk=False).get_opcodes():
        if tag in ('replace','delete') and i2>i1: old.append(b[i1:i2])
        if tag in ('replace','insert') and j2>j1: new.append(a[j1:j2])
    return (old[0],new[0]) if len(old)==len(new)==1 else None

def induce_graph(ep):
    d=diff_one(ep.before,ep.after)
    if not d or not ep.changed: return None
    old,new=d
    commons=[x for x in lcs_blocks(ep.before,ep.command) if x not in old and x not in new]
    entity=max(commons,key=len,default='')
    if not entity or new not in ep.command: return None
    cmd=ep.command.replace(entity,'¤0¤',1).replace(new,'¤1¤',1)
    literals=tuple(sorted([x for x in cmd.replace('¤0¤','|').replace('¤1¤','|').split('|') if x]))
    state=ep.before.replace(entity,'¤0¤',1).replace(old,'¤OLD¤',1)
    after=ep.after.replace(entity,'¤0¤',1).replace(new,'¤NEW¤',1)
    return (literals,state,after)

def extract_bindings(before,command,graph):
    literals,state_pat,after_pat=graph
    commons=sorted(set(lcs_blocks(before,command)),key=len,reverse=True)
    for entity in commons[:12]:
        if len(entity)<2: continue
        residual=command.replace(entity,'¤0¤',1)
        for lit in literals:
            residual=residual.replace(lit,'',1)
        new=residual.replace('¤0¤','').strip('。、，：:→ 　をにはへがのですしてくださいせよ直す変更設定移動対象最終値行き先')
        if not new: continue
        tmp=before.replace(entity,'¤0¤',1)
        parts=[p.strip('。、，：:→ 　をにはへがのです現在記録') for p in tmp.replace('¤0¤','|').split('|')]
        olds=[p for p in parts if len(p)>=1]
        for old in olds:
            if old in before and old!=new:
                pred=before.replace(old,new,1)
                return entity,old,new,pred
    return None

class Prototype:
    def fit(self,eps): self.rows=[e for e in eps if e.changed]
    def predict(self,b,c):
        if not self.rows:return None,0
        best=max(self.rows,key=lambda e:difflib.SequenceMatcher(None,c,e.command,autojunk=False).ratio())
        d=diff_one(best.before,best.after)
        return (b.replace(d[0],d[1],1) if d and d[0] in b else None),len(self.rows)
    def bytes(self): return len(pickle.dumps(self.rows))

class BindingMDL:
    def fit(self,eps):
        counts=Counter(g for e in eps if (g:=induce_graph(e)) is not None)
        self.graphs={g:n for g,n in counts.items()}
    def predict(self,b,c):
        scored=[]
        for g,sup in self.graphs.items():
            z=extract_bindings(b,c,g)
            if z:
                score=(sup+1).bit_length()-0.15*len(g[0])
                scored.append((score,z[3],g))
        scored.sort(reverse=True,key=lambda x:x[0])
        return (scored[0][1] if scored else None),len(self.graphs)
    def bytes(self): return len(pickle.dumps(self.graphs))

def evaluate(seed,n):
    train=make(seed,n,'train')
    out={'seed':seed,'n':n}
    for name,model in [('prototype',Prototype()),('binding_mdl',BindingMDL())]:
        t=time.perf_counter(); model.fit(train); out[name+'_train_s']=time.perf_counter()-t
        out[name+'_bytes']=model.bytes(); out[name+'_graphs']=len(getattr(model,'graphs',getattr(model,'rows',[])))
        for split,mode in [('seen','train'),('order','order'),('synonym','synonym'),('rename','rename'),('confound','confound')]:
            data=make(seed+100+len(split),120,mode)
            ok=[]; abst=[]; reads=[]; lat=[]
            for ep in data:
                st=time.perf_counter_ns(); p,r=model.predict(ep.before,ep.command); lat.append((time.perf_counter_ns()-st)/1e6);reads.append(r)
                if split=='confound':
                    abst.append(p is None or p==ep.before)
                else:ok.append(p==ep.after)
            if split=='confound': out[name+'_'+split]=statistics.mean(abst)
            else: out[name+'_'+split]=statistics.mean(ok)
            out[name+'_'+split+'_ms']=statistics.mean(lat);out[name+'_'+split+'_reads']=statistics.mean(reads)
    out['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return out

def main():
    rows=[evaluate(s,n) for n in (60,240,720) for s in (1,7,19)]
    agg={}
    for n in (60,240,720):
        rr=[x for x in rows if x['n']==n]; agg[str(n)]={}
        for m in ('prototype','binding_mdl'):
            keys=[m+'_seen',m+'_order',m+'_synonym',m+'_rename',m+'_confound',m+'_bytes',m+'_graphs',m+'_train_s',m+'_seen_ms',m+'_seen_reads']
            agg[str(n)][m]={k[len(m)+1:]:statistics.mean(x[k] for x in rr) for k in keys}
    print(json.dumps({'hypothesis':'Compositional Binding MDL with Contrastive Views','aggregate':agg,'rows':rows,'peak_rss_kib_runtime_included':max(x['peak_rss_kib'] for x in rows)},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
