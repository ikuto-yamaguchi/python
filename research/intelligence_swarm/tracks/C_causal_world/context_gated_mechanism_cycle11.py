"""Track C Cycle 011: Context-Gated Mechanism Edge Separation.

Controlled falsification probe. Learner receives raw Japanese context, command,
before and after strings from intervention episodes. It is not given operation,
context, object, relation, value or mechanism labels. Hidden labels are evaluator-only.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass
import argparse, difflib, json, math, pickle, random, resource, statistics, time

OBJECTS=["試料甲","試料乙","搬送台","検査票","端末青","端末赤","箱一","箱二"]
PLACES=["棚A","棚B","室内","廊下"]
CONTEXT_TRAIN={
 "ready":["電源経路は通っていて、入口も開いている。","給電は続いており、通路を使える。"],
 "blocked":["電源は入っているが、入口は閉じている。","給電中だが、通り道が塞がれている。"],
 "unpowered":["入口は開いているが、電源は落ちている。","通路は使える一方、給電されていない。"],
 "locked":["安全ロックが掛かり、入口も閉じている。","保護機構が作動し、通路が遮断されている。"],
 "override":["保守許可が出ており、安全ロックを一時解除できる。","点検権限により保護状態を上書きできる。"],
}
CONTEXT_HELD={
 "ready":["動力供給は正常で、出入口の妨げもない。"],
 "blocked":["稼働電力はあるものの、扉を通過できない。"],
 "unpowered":["扉は妨げないが、動力が供給されていない。"],
 "locked":["安全装置が有効で、進入は許されていない。"],
 "override":["整備担当の特例で、安全制限を解除可能だ。"],
}
COMMAND_TRAIN={
 "move":["{o}を{p}へ移動する。","{o}の置き先を{p}に変える。"],
 "activate":["{o}を作動させる。","{o}の運転を開始する。"],
 "unlock":["{o}の固定を解除する。","{o}を自由に動かせる状態へ戻す。"],
}
COMMAND_HELD={
 "move":["{o}を{p}まで運搬する。"],
 "activate":["{o}を起動状態にする。"],
 "unlock":["{o}の拘束を解く。"],
}
STATE_FORMS=["{o}の場所は{p}、状態は{s}、固定は{l}。","{o}について、{p}にあり、運転状態は{s}、拘束={l}。"]
ALT_STATE="{o}は現在{p}。稼働={s}。安全拘束={l}。"

@dataclass(frozen=True)
class HiddenState:
    place:str; status:str; locked:bool

def world_step(st,ctx,op,dest):
    power=ctx in ("ready","blocked","locked","override")
    passage=ctx in ("ready","unpowered","override")
    override=ctx=="override"
    if op=="unlock": return HiddenState(st.place,"解除",False) if override else st
    if op=="activate": return HiddenState(st.place,"作動",st.locked) if power and (not st.locked or override) else st
    if op=="move": return HiddenState(dest,st.status,st.locked) if passage and not st.locked and st.status=="作動" else st
    return st

def render(rng,o,st,alt=False,form=None):
    f=ALT_STATE if alt else (form or rng.choice(STATE_FORMS))
    return f.format(o=o,p=st.place,s=st.status,l="有" if st.locked else "無")

def grams(text):
    s="".join(text.split()); return Counter(s[i:i+n] for n in (2,3) for i in range(max(0,len(s)-n+1)))

def cos(a,b):
    dot=sum(v*b.get(k,0) for k,v in a.items()); na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return dot/(na*nb+1e-12)

def edit_signature(before,after):
    ops=[]
    for tag,i1,i2,j1,j2 in difflib.SequenceMatcher(None,before,after).get_opcodes():
        if tag!="equal": ops.append((tag,before[i1:i2],after[j1:j2]))
    return tuple(ops) or (("same","",""),)

def residue(command,before,after):
    out=command
    for src in (before,after):
        m=difflib.SequenceMatcher(None,out,src).find_longest_match(0,len(out),0,len(src))
        if m.size>=2: out=out[:m.a]+"<X>"+out[m.a+m.size:]
    return out

def fingerprint(text,mod):
    return sum(sum(ord(ch) for ch in k)*v for k,v in grams(text).items())%mod

class SurfaceAutomaton:
    def __init__(self):
        self.cmd=[]; self.ctx=[]; self.effects={}; self.transitions=defaultdict(Counter)
    def _effect(self,s):
        if s not in self.effects:self.effects[s]=len(self.effects)
        return self.effects[s]
    def _nearest(self,g,protos,threshold,create):
        if not protos:
            if create:protos.append(g);return 0
            return None
        scores=[cos(g,p) for p in protos];i=max(range(len(scores)),key=scores.__getitem__)
        if create and scores[i]<threshold:protos.append(g);return len(protos)-1
        return i if scores[i]>=threshold/2 else None
    def fit(self,eps):
        for ep in eps:
            self._nearest(grams(ep['context']),self.ctx,.20,True);latent=0
            for b,c,a in zip(ep['befores'],ep['commands'],ep['afters']):
                ki=self._nearest(grams(residue(c,b,a)),self.cmd,.12,True);nxt=self._effect(edit_signature(b,a))
                self.transitions[(latent,ki)][nxt]+=1;latent=nxt
        return self
    def predict(self,context,commands,befores):
        latent=0;out=[]
        for c,b in zip(commands,befores):
            ki=self._nearest(grams(residue(c,b,b)),self.cmd,.12,False)
            if ki is None:return None
            dist=self.transitions.get((latent,ki))
            if not dist:return None
            nxt=dist.most_common(1)[0][0];out.append(nxt);latent=nxt
        return tuple(out)

class ProbeSeparatedAutomaton(SurfaceAutomaton):
    def __init__(self,use_context=True,use_state=True):
        super().__init__();self.use_context=use_context;self.use_state=use_state;self.gated=defaultdict(Counter)
    def fit(self,eps):
        rows=[]
        for ep in eps:
            for b,c,a in zip(ep['befores'],ep['commands'],ep['afters']):rows.append((ep['context'],b,c,a,self._effect(edit_signature(b,a))))
        groups=[]
        for row in rows:
            ctx,b,c,a,eff=row;g=grams(residue(c,b,a));placed=False
            for group in groups:
                if cos(g,group['proto'])>=.10:group['rows'].append(row);group['proto'].update(g);placed=True;break
            if not placed:groups.append({'proto':g.copy(),'rows':[row]})
        for group in groups:
            split=defaultdict(list)
            for row in group['rows']:
                ctx,b,c,a,eff=row
                ck=fingerprint(ctx,11) if self.use_context else 0;sk=fingerprint(b,17) if self.use_state else 0
                split[(eff,ck,sk)].append(row)
            for items in split.values():
                proto=Counter()
                for ctx,b,c,a,eff in items:proto.update(grams(residue(c,b,a)))
                kid=len(self.cmd);self.cmd.append(proto)
                for ctx,b,c,a,eff in items:
                    ck=fingerprint(ctx,11) if self.use_context else 0;sk=fingerprint(b,17) if self.use_state else 0
                    self.gated[(ck,sk,kid)][eff]+=1
        return self
    def predict(self,context,commands,befores):
        out=[]
        for c,b in zip(commands,befores):
            ck=fingerprint(context,11) if self.use_context else 0;sk=fingerprint(b,17) if self.use_state else 0
            g=grams(residue(c,b,b));scores=[cos(g,p) for p in self.cmd];best=None
            for kid in sorted(range(len(scores)),key=lambda i:scores[i],reverse=True)[:min(6,len(scores))]:
                dist=self.gated.get((ck,sk,kid))
                if not dist:
                    merged=Counter()
                    for (c2,s2,k2),v in self.gated.items():
                        if k2==kid and ((not self.use_context or c2==ck) or (not self.use_state or s2==sk)):merged.update(v)
                    dist=merged
                if dist:
                    cand=(scores[kid],dist.most_common(1)[0][0])
                    if best is None or cand>best:best=cand
            if best is None:return None
            out.append(best[1])
        return tuple(out)

def generate(rng,held_context=False,held_command=False,n=2,alt=False,subject_omit=False):
    ctx_kind=rng.choice(list(CONTEXT_TRAIN));ctx=rng.choice((CONTEXT_HELD if held_context else CONTEXT_TRAIN)[ctx_kind])
    o=rng.choice(OBJECTS);dest=rng.choice(PLACES);st=HiddenState(rng.choice(PLACES),rng.choice(["待機","作動"]),rng.random()<.35)
    ops=[rng.choice(list(COMMAND_TRAIN)) for _ in range(n)]
    if n>=2 and rng.random()<.75:ops=rng.choice([["activate","move"],["unlock","activate"],["unlock","move"],["move","activate"]])[:n]
    cmds=[];bs=[];aas=[];effects=[];form=None if alt else rng.choice(STATE_FORMS)
    for i,op in enumerate(ops):
        b=render(rng,o,st,alt,form);c=rng.choice((COMMAND_HELD if held_command else COMMAND_TRAIN)[op]).format(o=o,p=dest)
        if subject_omit and i>0:c=c.replace(o,"その対象")
        ns=world_step(st,ctx_kind,op,dest);a=render(rng,o,ns,alt,form)
        cmds.append(c);bs.append(b);aas.append(a);effects.append(edit_signature(b,a));st=ns
    return {'context':ctx,'commands':cmds,'befores':bs,'afters':aas,'effects':effects}

def eval_model(model,rows):
    corr=abst=0;t=time.perf_counter()
    for ep in rows:
        p=model.predict(ep['context'],ep['commands'],ep['befores'])
        if p is None:abst+=1;continue
        corr+=p==tuple(model.effects.get(x,-999) for x in ep['effects'])
    return {'accuracy':corr/len(rows),'abstention':abst/len(rows),'ms':(time.perf_counter()-t)*1000/len(rows)}

def run(seed,n):
    rng=random.Random(seed);train=[generate(rng,False,False,rng.choice([1,2,3])) for _ in range(n)]
    models={'surface':SurfaceAutomaton().fit(train),'probe':ProbeSeparatedAutomaton(True,True).fit(train),'no_context':ProbeSeparatedAutomaton(False,True).fit(train),'no_state':ProbeSeparatedAutomaton(True,False).fit(train)}
    splits={'seen':[generate(rng,False,False,2) for _ in range(30)],'held_context':[generate(rng,True,False,2) for _ in range(30)],'held_command':[generate(rng,False,True,2) for _ in range(30)],'held_both':[generate(rng,True,True,2) for _ in range(30)],'order_counterfactual':[generate(rng,False,False,3) for _ in range(30)],'alternate_state':[generate(rng,False,False,2,True) for _ in range(30)],'subject_omission':[generate(rng,False,False,3,False,True) for _ in range(30)]}
    out={}
    for name,m in models.items():
        out[name]={k:eval_model(m,v) for k,v in splits.items()};out[name].update({'model_bytes':len(pickle.dumps(m)),'effect_symbols':len(m.effects),'command_edges':len(m.cmd),'transition_edges':len(m.transitions),'gated_edges':len(m.gated) if hasattr(m,'gated') else 0,'candidate_reads':min(6,len(m.cmd))})
    out['free_japanese_gate']=0.0;return out

def summarize(raw):
    res={}
    for n,runs in raw.items():
        res[n]={}
        for method in ('surface','probe','no_context','no_state'):
            res[n][method]={}
            for split in ('seen','held_context','held_command','held_both','order_counterfactual','alternate_state','subject_omission'):
                res[n][method][split]={k:statistics.mean(r[method][split][k] for r in runs) for k in ('accuracy','abstention','ms')}
            for k in ('model_bytes','effect_symbols','command_edges','transition_edges','gated_edges','candidate_reads'):res[n][method][k]=statistics.mean(r[method][k] for r in runs)
        res[n]['free_japanese_gate']=0.0
    return res

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_011.json');args=ap.parse_args();t=time.perf_counter()
    raw={str(n):[run(s,n) for s in (1,7,19)] for n in (32,96,192)}
    payload={'hypothesis':'Context-Gated Mechanism Edge Separation with Counterfactual State Probes','seeds':[1,7,19],'train_sizes':[32,96,192],'raw':raw,'summary':summarize(raw),'elapsed_seconds':time.perf_counter()-t,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'train O(N*H*G), infer O(T*K*G), K<=6; sparse gate lookup O(1)','free_japanese_integrated_gate':0.0,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    with open(args.output,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload['summary']['192'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
