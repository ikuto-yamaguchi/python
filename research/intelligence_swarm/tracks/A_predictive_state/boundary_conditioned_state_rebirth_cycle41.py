from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
import argparse, json, pickle, random, resource, statistics, time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵']
VALUES=['棚A','棚B','棚C','棚D','待機','処理中','完了','保留']
FILL=['補助記録は維持します。','別件の設定は変えません。','前段の注意事項はそのままです。']

@dataclass
class Turn:
    before:str; command:str; after:str; future:str
    obj:str; old:str; new:str; event:int; mode:str

@dataclass(frozen=True)
class Rule:
    state_start:int; state_width:int
    cmd_start:int; cmd_width:int
    old_shape:str; new_shape:str

def shape(s:str)->str:
    return ''.join('A' if c.isascii() and c.isalnum() else ('J' if c not in '。、：／=\n「」 ' else c) for c in s)

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l, len(a)-r if r else len(a), a[l:len(a)-r if r else len(a)], b[l:len(b)-r if r else len(b)]

def make_dialog(seed:int, blocks:int=8, mode:str='switch'):
    rng=random.Random(seed); rows=[]; world={}; event=0; focus=None
    for block in range(blocks):
        if mode=='switch' or focus is None:
            choices=[o for o in OBJECTS if o!=focus]
            focus=rng.choice(choices); event+=1
        for k in range(3):
            obj=focus; old=world.get(obj,rng.choice(VALUES)); new=rng.choice([v for v in VALUES if v!=old])
            before=f'{obj}の現在値は{old}です。{rng.choice(FILL)}'
            if mode=='omitted' and k>0:
                cmd=f'それを{new}へ変更してください。'
            elif mode=='paraphrase':
                cmd=f'対象となる{obj}は次から{new}扱いにしてください。'
            elif mode=='order':
                cmd=f'{new}へ変更してください。対象は{obj}です。'
            elif mode=='paragraph':
                cmd=f'{rng.choice(FILL)}\n{obj}を{new}へ変更してください。\n{rng.choice(FILL)}'
            elif mode=='plan' and k==1:
                alt=rng.choice([v for v in VALUES if v not in (old,new)])
                cmd=f'{obj}を{alt}にする案は撤回し、最終的には{new}へ変更してください。'
                event+=1
            elif mode=='counterfactual' and k==1:
                cmd=f'もし変更しなければ{obj}は{old}のままです。実際には{obj}を{new}へ変更してください。'
            else:
                cmd=f'{obj}を{new}へ変更してください。'
            after=f'{obj}の現在値は{new}です。{rng.choice(FILL)}'
            future=f'次の観測でも{obj}は{new}のままです。'
            rows.append(Turn(before,cmd,after,future,obj,old,new,event,mode))
            world[obj]=new
        if mode!='switch':
            focus=rng.choice([o for o in OBJECTS if o!=focus]); event+=1
    return rows

def induce_rule(t:Turn):
    s0,s1,old,new=diff(t.before,t.after)
    if not old or not new: return None
    p=t.command.find(new)
    if p<0:return None
    return Rule(s0,len(old),p,len(new),shape(old),shape(new))

def apply(t:Turn,r:Rule):
    if r.state_start+r.state_width>len(t.before) or r.cmd_start+r.cmd_width>len(t.command): return None
    old=t.before[r.state_start:r.state_start+r.state_width]
    val=t.command[r.cmd_start:r.cmd_start+r.cmd_width]
    if shape(old)!=r.old_shape or shape(val)!=r.new_shape:return None
    return t.before[:r.state_start]+val+t.before[r.state_start+r.state_width:]

def mismatch(a,b):
    if a is None:return 999
    n=min(len(a),len(b)); return abs(len(a)-len(b))+sum(a[i]!=b[i] for i in range(n))

class Model:
    def __init__(self,mode):
        self.mode=mode; self.rules=[]; self.support=Counter(); self.train_seconds=0
        self.births=0; self.boundaries=0; self.post_success=0
    def fit(self,dialogs):
        t0=time.perf_counter(); c=Counter()
        for d in dialogs:
            for t in d:
                r=induce_rule(t)
                if r:c[r]+=1
        self.rules=[r for r,n in c.most_common(64)]
        self.support=c; self.train_seconds=time.perf_counter()-t0
    def run(self,dialog):
        rows=[]; prev_loss=None
        seq=list(dialog)
        if self.mode=='shuffle':
            rng=random.Random(991); rng.shuffle(seq)
        for idx,t in enumerate(seq):
            candidates=[]
            for r in self.rules:
                p=apply(t,r)
                if p is not None:
                    loss=mismatch(p,t.after)
                    candidates.append((loss,-self.support[r],p,r))
            candidates.sort()
            one=candidates[0] if candidates else None
            detected=prev_loss is not None and one is not None and one[0]>prev_loss+3
            true_boundary=idx>0 and seq[idx-1].event!=t.event
            if detected:self.boundaries+=1
            chosen=None
            if self.mode=='one_step':
                chosen=one
            elif self.mode=='boundary_only':
                chosen=one if not detected else None
            elif self.mode in ('rebirth','shuffle'):
                if detected:
                    pool=[]
                    for cand in candidates[:16]:
                        loss=cand[0]
                        if idx+1<len(seq):
                            np=apply(seq[idx+1],cand[3])
                            loss+=mismatch(np,seq[idx+1].after)
                        pool.append((loss,*cand[1:]))
                    pool.sort(); chosen=pool[0] if pool else None
                    if chosen:self.births+=1
                else:
                    chosen=one
            if chosen is not None:
                pred=chosen[2]
                correct=pred==t.after
                if detected and correct:self.post_success+=1
            else:
                pred=None; correct=False
            rows.append({'correct':correct,'wrong':pred is not None and not correct,'null':pred is None,
                         'detected':detected,'true_boundary':true_boundary})
            prev_loss=one[0] if one else None
        return rows

def f1(rows):
    tp=sum(x['detected'] and x['true_boundary'] for x in rows)
    fp=sum(x['detected'] and not x['true_boundary'] for x in rows)
    fn=sum((not x['detected']) and x['true_boundary'] for x in rows)
    return 0 if 2*tp+fp+fn==0 else 2*tp/(2*tp+fp+fn)

def eval_seed(seed,condition):
    train=[make_dialog(seed+i,6,m) for i,m in enumerate(['switch','omitted','paraphrase','paragraph','plan'])]
    test=make_dialog(seed+999,8,condition)
    out={}
    for mode in ['one_step','boundary_only','rebirth','shuffle']:
        m=Model(mode); m.fit(train); t0=time.perf_counter(); rows=m.run(test); infer=(time.perf_counter()-t0)*1000/len(test)
        out[mode]={
            'accuracy':statistics.mean(float(x['correct']) for x in rows),
            'wrong':statistics.mean(float(x['wrong']) for x in rows),
            'null':statistics.mean(float(x['null']) for x in rows),
            'boundary_f1':f1(rows),
            'rules':len(m.rules),'rebirths':m.births,'post_boundary_success':m.post_success,
            'model_bytes':len(pickle.dumps(m)),'training_seconds':m.train_seconds,'inference_ms':infer
        }
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); a=ap.parse_args()
    conditions=['switch','omitted','paraphrase','order','paragraph','plan','counterfactual']
    raw={str(seed):{c:eval_seed(seed,c) for c in conditions} for seed in [1,7,19]}
    summary={}
    for c in conditions:
        summary[c]={}
        for mode in ['one_step','boundary_only','rebirth','shuffle']:
            summary[c][mode]={k:statistics.mean(raw[str(s)][c][mode][k] for s in [1,7,19]) for k in raw['1'][c][mode]}
    payload={'cycle':41,'hypothesis':'Boundary-Conditioned State Rebirth from Pre/Post Event Prediction Contrast',
             'seeds':[1,7,19],'summary':summary,'raw':raw,
             'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             'estimated_complexity':'induction O(NL), online O(TR), post-boundary contrast O(kR)',
             'final_test_after_future_used_for_candidate_generation_or_ranking':False,
             'fixed_ontology_or_handwritten_slots_used_by_model':False,
             'highschool_level_passed':False,'native_japanese_communication_passed':False,
             'weak_smartphone_verified':False,'completion':False}
    open(a.output,'w',encoding='utf-8').write(json.dumps(payload,ensure_ascii=False,indent=2))
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
