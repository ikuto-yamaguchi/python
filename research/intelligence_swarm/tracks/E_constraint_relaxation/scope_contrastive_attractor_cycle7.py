from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass
import json, math, pickle, random, resource, statistics, time

PUNCT='。！？\n'
NAMES=['アオ','キリ','ミナ','ソラ','ハル','ユキ','ナギ','レオ']
VALS=['棚A','棚B','棚C','箱一','箱二','東室','西室','机上']
CMD_SEEN=['{x}を{v}へ移してください。','{x}の置き場を{v}に変更。','{v}へ{x}を動かす。']
CMD_HELD=['{x}を{v}へ回してください。','{x}の行き先は{v}でお願いします。']
CTX_ACT=['通路は開いています。','作業は許可されています。','妨げはありません。']
CTX_BLOCK=['通路は閉じています。','作業は禁止されています。','障害があります。']
CTX_HELD_ACT=['進行可能な状態です。','実施して問題ありません。']
CTX_HELD_BLOCK=['先へ進めません。','実施できない状況です。']
STATE=['{x}の現在位置は{v}です。','現在、{x}は{v}にあります。']

def grams(s):
    return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))

def cos(a,b):
    d=sum(v*b.get(k,0) for k,v in a.items()); na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return d/(na*nb+1e-12)

def split_units(text):
    out=[]; cur=''
    for ch in text:
        cur+=ch
        if ch in PUNCT:
            if cur.strip(): out.append(cur.strip())
            cur=''
    if cur.strip(): out.append(cur.strip())
    return out

def diff_middle(a,b):
    i=0
    while i<min(len(a),len(b)) and a[i]==b[i]: i+=1
    j=0
    while j<min(len(a)-i,len(b)-i) and a[-1-j]==b[-1-j]: j+=1
    return a[i:len(a)-j if j else len(a)],b[i:len(b)-j if j else len(b)],a[:i],a[len(a)-j:] if j else ''

def mk(rng,split='seen'):
    x=rng.choice(NAMES); old,new=rng.sample(VALS,2); before=rng.choice(STATE).format(x=x,v=old); blocked=rng.random()<.5
    ctx=rng.choice((CTX_HELD_BLOCK if blocked else CTX_HELD_ACT) if split in ('held_context','nested_held') else (CTX_BLOCK if blocked else CTX_ACT))
    cmd=rng.choice(CMD_HELD if split=='held_command' else CMD_SEEN).format(x=x,v=new)
    units=[]
    if split in ('multi','plan_change'): units.append('補足情報です。別件の確認もあります。')
    units.append(('担当者は次の条件を確認しました。'+ctx) if split in ('nested','nested_held') else ctx)
    units.append(cmd); final=new
    if split=='plan_change':
        alt=rng.choice([v for v in VALS if v not in (old,new)]); units.append('先ほどの指示を訂正します。'+rng.choice(CMD_SEEN).format(x=x,v=alt)); final=alt
    after=rng.choice(STATE).format(x=x,v=old if blocked else final)
    return {'before':before,'text':'\n'.join(units),'after':after}

@dataclass
class Cand:
    cmd_i:int; a:int; b:int; branch:str; revision:str; energy:float=0.0

class Model:
    def __init__(self): self.cmd=[]; self.scope=defaultdict(list); self.trans=[]
    def fit(self,rows):
        for r in rows:
            us=split_units(r['text']); old,new,pre,suf=diff_middle(r['before'],r['after'])
            for u in us:
                if (new and new in u) or (old and old in u):
                    if len(self.cmd)<48: self.cmd.append(grams(u.replace(new,'<V>').replace(old,'<V>')))
            y='noop' if r['before']==r['after'] else 'action'
            for a in range(len(us)):
                for b in range(a,min(len(us),a+2)):
                    if len(self.scope[y])<64: self.scope[y].append(grams(' '.join(us[a:b+1])))
            self.trans.append((pre,suf))
        return self
    def cmd_score(self,u):
        g=grams(u); return max([cos(g,p) for p in self.cmd] or [0])
    def scope_score(self,s,y):
        arr=self.scope[y]
        if not arr:return 0
        vals=sorted((cos(grams(s),p) for p in arr),reverse=True)[:8]
        return sum(vals)/len(vals)
    def propose(self,r):
        us=split_units(r['text']); out=[]
        for ci in range(len(us)):
            for a in range(len(us)):
                for b in range(a,min(len(us),a+2)):
                    for y in ('action','noop'):
                        for rev in ('first','last'): out.append(Cand(ci,a,b,y,rev))
        return out[:32]
    def execute(self,r,c):
        if c.branch=='noop': return r['before']
        us=split_units(r['text']); cu=[u for u in us if self.cmd_score(u)>.15]
        if not cu:return None
        cmd=cu[0] if c.revision=='first' else cu[-1]
        pre=suf=old=None
        for p,s in self.trans:
            if r['before'].startswith(p) and (not s or r['before'].endswith(s)):
                pre,suf=p,s; old=r['before'][len(p):len(r['before'])-len(s) if s else len(r['before'])]; break
        if old is None:return None
        pieces=[]
        for u in us:
            for q in u.replace('。','').replace('、','').split('は'):
                if 1<=len(q)<=12 and q not in r['before'] and q in cmd: pieces.append(q)
        if not pieces:return None
        return pre+min(pieces,key=len)+suf
    def predict(self,r,mode='attractor'):
        if mode=='flat': return self.execute(r,Cand(0,0,0,'action','last')),1,1,0.0
        us=split_units(r['text']); cs=self.propose(r); prev=None; sweeps=0
        for _ in range(8):
            sweeps+=1
            for c in cs:
                e=.55*self.cmd_score(us[c.cmd_i])+.35*self.scope_score(' '.join(us[c.a:c.b+1]),c.branch)+(.05 if c.a<=c.cmd_i<=c.b else 0)
                if c.revision=='last' and any('訂正' in u for u in us): e+=.08
                c.energy=-e
            cs.sort(key=lambda z:z.energy); cur=(cs[0].cmd_i,cs[0].a,cs[0].b,cs[0].branch,cs[0].revision)
            if cur==prev: break
            prev=cur
        margin=cs[1].energy-cs[0].energy if len(cs)>1 else 1
        return (None if margin<.005 else self.execute(r,cs[0])),sweeps,len(cs),margin

def run(seed,n):
    rng=random.Random(seed); train=[mk(rng) for _ in range(n)]; t=time.perf_counter(); m=Model().fit(train); train_s=time.perf_counter()-t; out={}
    for split in ['seen','held_context','held_command','nested','nested_held','multi','plan_change']:
        rows=[mk(rng,split) for _ in range(20)]
        for mode in ['flat','attractor']:
            ok=ab=0; sw=[]; ac=[]; ma=[]; st=time.perf_counter()
            for r in rows:
                p,s,a,mg=m.predict(r,mode); ok+=p==r['after']; ab+=p is None; sw.append(s); ac.append(a); ma.append(mg)
            out[f'{split}_{mode}']={'accuracy':ok/len(rows),'abstention':ab/len(rows),'ms':(time.perf_counter()-st)*1000/len(rows),'sweeps':statistics.mean(sw),'active':statistics.mean(ac),'margin':statistics.mean(ma)}
    out.update(model_bytes=len(pickle.dumps(m)),train_s=train_s,cmd_views=len(m.cmd),scope_views=sum(map(len,m.scope.values())))
    return out

raw={str(n):[run(s,n) for s in (1,7,19)] for n in (24,48,96)}; summary={}
for n,rs in raw.items():
    summary[n]={}
    for k in rs[0]:
        summary[n][k]=({m:statistics.mean(r[k][m] for r in rs) for m in rs[0][k]} if isinstance(rs[0][k],dict) else statistics.mean(r[k] for r in rs))
p={'hypothesis':'Scope-Contrastive Factor Proposal with Reversible Attractor Selection','raw':raw,'summary':summary,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'seeds':[1,7,19],'train_sizes':[24,48,96],'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
with open('results_cycle_007.json','w',encoding='utf-8') as f: json.dump(p,f,ensure_ascii=False,indent=2)
print(json.dumps(summary['96'],ensure_ascii=False,indent=2))
