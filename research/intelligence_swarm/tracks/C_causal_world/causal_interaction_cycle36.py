from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
import argparse,json,pickle,random,resource,statistics,time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','試料甲':'サンプル甲','試料乙':'サンプル乙'}
VALUES=['棚A','棚B','棚C','棚D','待機','処理中','完了','保留']
FILL=['補助記録は維持します。','別系統は変更しません。','監査メモはそのままです。']

@dataclass
class Ex:
    before:str;command:str;after:str;future:str
    target:str;other:str;old:str;other_value:str;new:str;mode:str

@dataclass(frozen=True)
class Proposal:
    tb:int;tw:int;ob:int;ow:int;vb:int;vw:int
    ts:str;os:str;vs:str

@dataclass
class ParentSet:
    p:Proposal;support:int=0;base_ok:int=0;value_effect:int=0
    object_gate:int=0;interaction:int=0;wrong:int=0;credit:float=0.0

def sh(s):
    return ''.join('A' if c.isascii() and c.isalnum() else 'J' if c not in '。、：／=\n 「」' else c for c in s)

def bucket(pos,L): return round(20*pos/max(1,L))

def locate(text,b,w,shape):
    t=round(b*len(text)/20); out=[]
    for a in range(max(0,t-4),min(len(text),t+5)):
        for ww in range(max(1,w-2),min(16,w+3)):
            if a+ww<=len(text) and sh(text[a:a+ww])==shape:
                out.append((a,a+ww,text[a:a+ww]))
    return out

def state(o1,v1,o2,v2,form,f):
    if form==0:return f'{o1}の現在値は{v1}です。{o2}の現在値は{v2}です。{f}'
    if form==1:return f'{o1}：設定={v1}／{o2}：設定={v2}／補助=維持。{f}'
    return f'記録には対象{o1}が「{v1}」、対象{o2}が「{v2}」とあります。{f}'

def build(seed,n,mode):
    r=random.Random(seed); out=[]
    for _ in range(n):
        t,o=r.sample(OBJECTS,2); ts=ALIASES[t] if mode=='rename' else t; os=ALIASES[o] if mode=='rename' else o
        old,ov,new=r.sample(VALUES,3); form=1 if mode=='alternate' else 2 if mode=='alternate2' else 0; f=r.choice(FILL)
        before=state(ts,old,os,ov,form,f); cmd=f'{ts}の値を{new}へ変更してください。'
        if mode=='order':cmd=f'{new}へ変更してください。対象は{ts}です。'
        elif mode=='lexeme':cmd=f'対象{ts}は以後{new}扱いにします。'
        elif mode=='nested':cmd=f'依頼内容は「{ts}の値を{new}へ変更してください」です。'
        elif mode=='omitted':cmd=f'それを{new}へ変更してください。'
        elif mode=='paragraph':cmd=f'前段説明。{r.choice(FILL)}\n{cmd}\n後段注記。'
        elif mode=='plan':
            alt=r.choice([x for x in VALUES if x not in (old,ov,new)]);cmd=f'{ts}を{alt}にする案は撤回します。最終的には{new}へ変更してください。'
        elif mode=='counterfactual':cmd=f'もし変更しなければ{ts}は{old}のままです。実際には{ts}を{new}へ変更してください。'
        after=state(ts,new,os,ov,form,f)
        future=f'次の観測でも{ts}は{new}で、{os}は{ov}のままです。'
        out.append(Ex(before,cmd,after,future,ts,os,old,ov,new,mode))
    return out

def extract(e):
    ti=e.before.find(e.old); oi=e.command.find(e.target); vi=e.command.find(e.new)
    if min(ti,vi)<0:return None
    if oi<0: oi=0;ow=0;os=''
    else:ow=len(e.target);os=sh(e.target)
    return Proposal(bucket(ti,len(e.before)),len(e.old),bucket(oi,len(e.command)),ow,bucket(vi,len(e.command)),len(e.new),sh(e.old),os,sh(e.new))

def state_edits(e,p,v):
    return [(e.before[:a]+v+e.before[b:],a,b) for a,b,_ in locate(e.before,p.tb,p.tw,p.ts)]

def cmd_values(e,p):return sorted({x for _,_,x in locate(e.command,p.vb,p.vw,p.vs) if x not in e.before})[:8]
def cmd_objects(e,p):return sorted({x for _,_,x in locate(e.command,p.ob,p.ow,p.os)})[:6] if p.ow else ['']

def swap_command(e,p,obj=None,val=None):
    texts=[e.command]
    if p.ow and obj is not None:
        z=[]
        for s in texts:
            for a,b,_ in locate(s,p.ob,p.ow,p.os):z.append(s[:a]+obj+s[b:])
        texts=z
    if val is not None:
        z=[]
        for s in texts:
            for a,b,_ in locate(s,p.vb,p.vw,p.vs):z.append(s[:a]+val+s[b:])
        texts=z
    return texts

class Model:
    def __init__(self,mode):self.mode=mode;self.parents=[];self.raw=0;self.audit=0;self.train_s=0
    def fit(self,ind,probe,shuffle=False):
        t=time.perf_counter();cnt=Counter(x for e in ind if (x:=extract(e)));self.raw=len(cnt);obs=[e.after for e in probe]
        if shuffle:obs=obs[1:]+obs[:1]
        ps=[]
        for p,sup in cnt.most_common(48):
            base=value_eff=obj_gate=inter=wrong=0
            for e,y in zip(probe,obs):
                vals=cmd_values(e,p);objs=cmd_objects(e,p)
                altvals=[x for x in VALUES if x not in (e.old,e.other_value,e.new)][:2]
                altobjs=[e.other]+[x for x in OBJECTS if x not in (e.target,e.other)][:1]
                for v in vals:
                    for pred,a,b in state_edits(e,p,v):
                        self.audit+=1;ok=pred==y;base+=ok;wrong+=not ok
                        if not ok:continue
                        val_hits=0
                        for av in altvals:
                            val_hits+=int(bool(swap_command(e,p,val=av)) and any(q[0]==e.before[:a]+av+e.before[b:] for q in state_edits(e,p,av)))
                        value_eff+=val_hits>0
                        gate_hits=0
                        for ao in altobjs:
                            if ao==e.target:continue
                            commands=swap_command(e,p,obj=ao)
                            same_support=any(q[0]==e.before[:a]+v+e.before[b:] for q in state_edits(e,p,v))
                            gate_hits+=int(bool(commands) and not same_support)
                        obj_gate+=gate_hits>0
                        inter+=int(val_hits>0 and gate_hits>0)
            accept=base>=2
            if self.mode=='interaction':accept=base>=2 and value_eff>=2 and obj_gate>=2 and inter>=2
            if accept:
                x=ParentSet(p,sup,base,value_eff,obj_gate,inter,wrong)
                x.credit=(3*base+value_eff+2*obj_gate+3*inter-wrong)/(1+base+wrong);ps.append(x)
        self.parents=sorted(ps,key=lambda x:(x.credit,x.interaction,x.base_ok),reverse=True)[:32];self.train_s=time.perf_counter()-t
    def predict(self,e):
        out=[]
        for i,d in enumerate(self.parents):
            for v in cmd_values(e,d.p):
                for pred,a,b in state_edits(e,d.p,v):
                    score=d.credit+int(v in e.command)+.2*d.interaction-.02*(b-a);out.append((score,pred,a,b,v,i))
        if not out:return None,0
        out.sort(reverse=True);best=out[0][0];tops=[x for x in out if best-x[0]<.35]
        if len({x[1] for x in tops})>1:return None,len(out)
        return tops[0],len(out)

def ev(m,test):
    c=w=n=exact=pair=wrong_target=0;cs=[];t=time.perf_counter()
    for e in test:
        p,k=m.predict(e);cs.append(k)
        if p is None:n+=1;continue
        _,pred,a,b,v,_=p;c+=pred==e.after;w+=pred!=e.after
        ti=e.before.find(e.old);ex=a==ti and b==ti+len(e.old);exact+=ex;pair+=ex and v==e.new
        oi=e.before.find(e.other_value);wrong_target+=a==oi and b==oi+len(e.other_value)
    N=len(test);return {'accuracy':c/N,'wrong_commit':w/N,'null_rate':n/N,'exact_boundary':exact/N,'object_value_pair':pair/N,'wrong_target':wrong_target/N,'mean_candidates':statistics.mean(cs),'parent_sets':len(m.parents),'raw_proposals':m.raw,'probe_audits':m.audit,'model_bytes':len(pickle.dumps(m)),'training_seconds':m.train_s,'inference_ms':(time.perf_counter()-t)*1000/N}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='MEASUREMENTS_CYCLE_036.json');a=ap.parse_args()
    modes=['seen','order','lexeme','rename','alternate','alternate2','nested','omitted','paragraph','plan','counterfactual'];methods=['factorized','value_only','interaction','shuffle'];raw={}
    for seed in (1,7,19):
        train=build(seed,72,'seen')+build(seed+1,36,'rename')+build(seed+2,36,'alternate');ind,probe=train[:96],train[96:];models={}
        for method in methods:
            x=Model('interaction' if method in ('interaction','shuffle') else 'value');x.fit(ind,probe,shuffle=method=='shuffle');models[method]=x
        raw[str(seed)]={mode:{method:ev(x,build(seed+999,24,mode)) for method,x in models.items()} for mode in modes}
    summary={mode:{method:{k:statistics.mean(raw[str(s)][mode][method][k] for s in (1,7,19)) for k in raw['1'][mode][method]} for method in methods} for mode in modes}
    payload={'cycle':36,'hypothesis':'Object-Selective Causal Parent Sets from Double-Intervention Difference-in-Differences','seeds':[1,7,19],'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'proposal O(NL), probe 2x2 intervention grid O(QFVO L), inference O(FVL)','final_test_outcomes_used_for_ranking':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    open(a.output,'w',encoding='utf-8').write(json.dumps(payload,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
