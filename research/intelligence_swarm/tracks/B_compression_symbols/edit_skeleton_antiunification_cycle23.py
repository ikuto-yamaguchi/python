from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict, Counter
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=['青い箱','赤い箱','小型端末','大型端末','北側の鍵','南側の鍵','試料甲','試料乙']
ALIASES={'青い箱':'青色ケース','赤い箱':'赤色ケース','小型端末':'小さい端末','大型端末':'大きい端末','北側の鍵':'北のキー','南側の鍵':'南のキー','試料甲':'サンプル甲','試料乙':'サンプル乙'}
FIELDS=['場所','状態','担当']
VALUES={'場所':['棚A','棚B','棚C','棚D'],'状態':['待機','処理中','完了','保留'],'担当':['担当一','担当二','担当三','担当四']}
STATE_FORMS=['{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。','{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。']
COMMANDS={'場所':['{o}を{v}へ移してください。','{o}の保管先を{v}へ変更します。'],'状態':['{o}を{v}にしてください。','{o}の進行状態を{v}へ切り替えます。'],'担当':['{o}を{v}の担当にしてください。','{o}の受け持ちを{v}へ変更します。']}
HELD_ORDER={'場所':['{v}へ移してください、対象は{o}です。'],'状態':['{v}扱いにしてください、対象は{o}です。'],'担当':['{v}へ引き継いでください、対象は{o}です。']}
HELD_LEX={'場所':['対象{o}は次回から{v}で保管。'],'状態':['対象{o}は以後{v}として運用。'],'担当':['対象{o}の受持を{v}へ。']}
OMIT={'場所':['それを{v}へ移してください。'],'状態':['その対象を{v}にしてください。'],'担当':['担当は{v}へ変えてください。']}

@dataclass
class Ep:
    before:str; command:str; after:str; obj:str; field:str; value:str; mode:str

@dataclass
class Script:
    cmd_l:str; cmd_r:str; st_l:str; st_r:str; support:int=1
    success:tuple=(); wrong:tuple=(); noexec:tuple=()

@dataclass
class Grammar:
    cmd_l_parts:tuple; cmd_r_parts:tuple; st_l_parts:tuple; st_r_parts:tuple
    members:tuple; support:int; reversible:int; heldout:int; wrong:int
    def bits(self):
        sequences=(self.cmd_l_parts,self.cmd_r_parts,self.st_l_parts,self.st_r_parts)
        const=sum(len(x) for seq in sequences for x in seq if x!='*')
        variables=sum(x=='*' for seq in sequences for x in seq)
        return 8*const+12*variables+16*len(self.members)+64

def state(o,d,form=0):
    return STATE_FORMS[form].format(o=o,loc=d['場所'],status=d['状態'],owner=d['担当'])

def diff(a,b):
    left=0
    while left<min(len(a),len(b)) and a[left]==b[left]: left+=1
    right=0
    while right<min(len(a)-left,len(b)-left) and a[-1-right]==b[-1-right]: right+=1
    return left,right,a[left:len(a)-right if right else len(a)],b[left:len(b)-right if right else len(b)]

def contexts(text,value,width=10):
    out=[]; position=0
    while value:
        index=text.find(value,position)
        if index<0: break
        out.append((text[max(0,index-width):index],text[index+len(value):index+len(value)+width]))
        position=index+1
    return out[:4]

def build(seed,n,mode):
    rng=random.Random(seed); world={}; episodes=[]
    for _ in range(n):
        canonical=rng.choice(OBJECTS)
        obj=ALIASES[canonical] if mode=='rename' else canonical
        world.setdefault(canonical,{field:rng.choice(VALUES[field]) for field in FIELDS})
        field=rng.choice(FIELDS)
        value=rng.choice([candidate for candidate in VALUES[field] if candidate!=world[canonical][field]])
        form=1 if mode=='alternate' else 0
        before=state(obj,world[canonical],form)
        forms=HELD_ORDER[field] if mode=='held_order' else HELD_LEX[field] if mode in ('held_lex','rename') else OMIT[field] if mode=='omitted' else COMMANDS[field]
        command=rng.choice(forms).format(o=obj,v=value)
        if mode=='nested': command='依頼内容は「'+command+'」です。'
        if mode=='paragraph': command='背景説明です。別件は維持します。\n'+command+'\n以上が最終指示です。'
        world[canonical][field]=value
        after=state(obj,world[canonical],form)
        episodes.append(Ep(before,command,after,obj,field,value,mode))
    return episodes

def anti_parts(a,b):
    if a==b: return (a,)
    left=0
    while left<min(len(a),len(b)) and a[left]==b[left]: left+=1
    right=0
    while right<min(len(a)-left,len(b)-left) and a[-1-right]==b[-1-right]: right+=1
    out=[]
    if left: out.append(a[:left])
    out.append('*')
    if right: out.append(a[len(a)-right:])
    return tuple(out)

def match_parts(text,parts):
    position=0
    for part in parts:
        if part=='*': continue
        index=text.find(part,position)
        if index<0: return False
        position=index+len(part)
    return True

class Model:
    def __init__(self,kind):
        self.kind=kind; self.scripts=[]; self.grammars=[]; self.raw=0
        self.train_s=0.0; self.baseline_bits=0; self.total_bits=0

    def apply(self,before,command,script):
        values=[]; position=0
        while True:
            index=command.find(script.cmd_l,position) if script.cmd_l else position
            if index<0: break
            start=index+len(script.cmd_l)
            end=command.find(script.cmd_r,start) if script.cmd_r else len(command)
            if end>=start and 0<end-start<=14: values.append(command[start:end])
            position=index+1
            if not script.cmd_l or position>=len(command): break
        if len(values)!=1: return before,False
        value=values[0]; hits=[]; position=0
        while True:
            index=before.find(script.st_l,position) if script.st_l else position
            if index<0: break
            start=index+len(script.st_l)
            end=before.find(script.st_r,start) if script.st_r else len(before)
            if end>=start: hits.append((start,end))
            position=index+1
            if not script.st_l or position>=len(before): break
        if len(hits)!=1: return before,False
        start,end=hits[0]
        return before[:start]+value+before[end:],True

    def fit(self,episodes):
        started=time.perf_counter(); unique={}
        for episode in episodes:
            left,right,old,new=diff(episode.before,episode.after)
            if not new: continue
            for command_left,command_right in contexts(episode.command,new):
                self.raw+=1
                state_left=episode.before[max(0,left-10):left]
                state_right=episode.before[len(episode.before)-right:len(episode.before)-right+10] if right else episode.before[left+len(old):left+len(old)+10]
                script=Script(command_left,command_right,state_left,state_right)
                prediction,ok=self.apply(episode.before,episode.command,script)
                if not ok or prediction!=episode.after: continue
                key=(script.cmd_l,script.cmd_r,script.st_l,script.st_r)
                if key in unique: unique[key].support+=1
                else: unique[key]=script
        self.scripts=sorted(unique.values(),key=lambda item:item.support,reverse=True)[:64]
        for script in self.scripts:
            success=[]; wrong=[]; noexec=[]
            for index,episode in enumerate(episodes):
                prediction,ok=self.apply(episode.before,episode.command,script)
                (noexec if not ok else success if prediction==episode.after else wrong).append(index)
            script.success=tuple(success); script.wrong=tuple(wrong); script.noexec=tuple(noexec)
        self.baseline_bits=sum(8*(len(s.cmd_l)+len(s.cmd_r)+len(s.st_l)+len(s.st_r))+32 for s in self.scripts)
        if self.kind!='exact': self.induce(episodes)
        self.total_bits=self.baseline_bits+sum(grammar.bits() for grammar in self.grammars)
        self.train_s=time.perf_counter()-started

    def induce(self,episodes):
        candidates=[]
        for i,a in enumerate(self.scripts):
            for j,b in enumerate(self.scripts[i+1:],i+1):
                if not (set(a.success)&set(b.success)): continue
                parts=(anti_parts(a.cmd_l,b.cmd_l),anti_parts(a.cmd_r,b.cmd_r),anti_parts(a.st_l,b.st_l),anti_parts(a.st_r,b.st_r))
                reversible=heldout=wrong=0
                for index,episode in enumerate(episodes):
                    eligible=match_parts(episode.command,parts[0]) and match_parts(episode.command,parts[1]) and match_parts(episode.before,parts[2]) and match_parts(episode.before,parts[3])
                    if not eligible: continue
                    pa,oka=self.apply(episode.before,episode.command,a)
                    pb,okb=self.apply(episode.before,episode.command,b)
                    good=(oka and pa==episode.after) or (okb and pb==episode.after)
                    bad=(oka and pa!=episode.after) or (okb and pb!=episode.after)
                    if good: reversible+=1
                    if good and index%2: heldout+=1
                    if bad: wrong+=1
                if reversible<2 or heldout<1: continue
                grammar=Grammar(*parts,(i,j),a.support+b.support,reversible,heldout,wrong)
                exact_bits=8*sum(len(x) for x in (a.cmd_l,a.cmd_r,a.st_l,a.st_r,b.cmd_l,b.cmd_r,b.st_l,b.st_r))+64
                candidates.append((exact_bits-grammar.bits(),reversible-wrong,grammar))
        candidates.sort(key=lambda item:(item[0],item[1]),reverse=True)
        used=set()
        for gain,_,grammar in candidates:
            if self.kind=='mdl' and gain<=0: continue
            if any(member in used for member in grammar.members): continue
            self.grammars.append(grammar); used.update(grammar.members)
            if len(self.grammars)>=32: break
        if self.kind=='mdl':
            removed=sum(8*sum(len(x) for x in (self.scripts[i].cmd_l,self.scripts[i].cmd_r,self.scripts[i].st_l,self.scripts[i].st_r))+32 for grammar in self.grammars for i in grammar.members)
            self.total_bits=self.baseline_bits-removed+sum(grammar.bits() for grammar in self.grammars)

    def predict(self,episode):
        candidates=[]
        for script in self.scripts:
            prediction,ok=self.apply(episode.before,episode.command,script)
            if ok: candidates.append((script.support,prediction))
        for grammar in self.grammars:
            eligible=match_parts(episode.command,grammar.cmd_l_parts) and match_parts(episode.command,grammar.cmd_r_parts) and match_parts(episode.before,grammar.st_l_parts) and match_parts(episode.before,grammar.st_r_parts)
            if not eligible: continue
            for member in grammar.members:
                prediction,ok=self.apply(episode.before,episode.command,self.scripts[member])
                if ok: candidates.append((grammar.reversible-grammar.wrong+grammar.support/10,prediction))
        if not candidates: return episode.before,False,0
        by_prediction=defaultdict(float)
        for score,prediction in candidates: by_prediction[prediction]=max(by_prediction[prediction],score)
        ranked=sorted(((score,prediction) for prediction,score in by_prediction.items()),reverse=True)
        if len(ranked)>1 and ranked[0][0]-ranked[1][0]<0.05: return episode.before,False,len(ranked)
        return ranked[0][1],True,len(ranked)

def evaluate(seed,n,mode):
    train=[]
    for offset,train_mode in enumerate(('seen','rename','alternate')):
        train+=build(seed+17*offset,n//3,train_mode)
    test=build(seed+999,48,mode); output={}
    for kind in ('exact','anti','mdl'):
        model=Model(kind); model.fit(train); started=time.perf_counter()
        correct=wrong=recall=commits=candidate_count=0
        for episode in test:
            prediction,did_commit,count=model.predict(episode)
            candidate_count+=count; commits+=did_commit
            correct+=int(did_commit and prediction==episode.after)
            wrong+=int(did_commit and prediction!=episode.after)
            recall+=int(any(model.apply(episode.before,episode.command,script)[1] and model.apply(episode.before,episode.command,script)[0]==episode.after for script in model.scripts))
        output[kind]={
            'accuracy':correct/len(test),'wrong_commit':wrong/len(test),'commit_rate':commits/len(test),
            'candidate_recall':recall/len(test),'scripts':len(model.scripts),'grammars':len(model.grammars),
            'raw_candidates':model.raw,'baseline_bits':model.baseline_bits,'total_bits':model.total_bits,
            'model_bytes':len(pickle.dumps(model)),'training_seconds':model.train_s,
            'inference_ms':(time.perf_counter()-started)*1000/len(test),'mean_candidates':candidate_count/len(test),
        }
    return output

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output',default='results_cycle_023.json'); args=parser.parse_args()
    modes=['seen','held_order','held_lex','rename','nested','omitted','alternate','paragraph']; raw={}
    for n in (48,144,288): raw[str(n)]=[{mode:evaluate(seed,n,mode) for mode in modes} for seed in (1,7,19)]
    summary={}
    for n,runs in raw.items():
        summary[n]={}
        for mode in modes:
            summary[n][mode]={}
            for kind in ('exact','anti','mdl'):
                summary[n][mode][kind]={key:statistics.mean(run[mode][kind][key] for run in runs) for key in runs[0][mode][kind]}
    payload={
        'hypothesis':'MDL-Gated Reversible Edit-Skeleton Grammars by Raw Derivation Anti-Unification',
        'seeds':[1,7,19],'sizes':[48,144,288],'raw':raw,'summary':summary,
        'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'estimated_complexity':'proposal O(NL^2), anti-unification O(P^2 L), audit O(GN), inference O((P+G)L), P<=64 G<=32',
        'hidden_labels_used_by_learner':False,'highschool_level_passed':False,
        'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False,
    }
    with open(args.output,'w',encoding='utf-8') as handle: json.dump(payload,handle,ensure_ascii=False,indent=2)
    print(json.dumps(summary['288'],ensure_ascii=False,indent=2))

if __name__=='__main__': main()
