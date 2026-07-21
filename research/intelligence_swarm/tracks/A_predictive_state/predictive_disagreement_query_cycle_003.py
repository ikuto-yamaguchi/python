from __future__ import annotations
import difflib,json,pickle,random,resource,statistics,time
from collections import Counter

ENTITIES=["アルファ","ベータ","ガンマ","デルタ","シグマ","オメガ"]
VALUES=["棚A","棚B","棚C","棚D","窓辺","机上"]
TRAIN_FORMS=["{e}を{v}へ移してください。","{e}の置き場を{v}に変えてください。","{v}へ{e}を運んでください。"]
HELD_FORMS=["対象は{e}。行き先は{v}です。","{e}について、最終的な所在を{v}としてください。"]
AMBIGUOUS_FORMS=["{e}を移してください。","{e}の置き場を変えてください。"]
STATE_FORMS=["{e}は{v}にあります。","現在、{e}の場所は{v}です。"]

def grams(text,n=(2,3)):
    return Counter(text[i:i+k] for k in n for i in range(max(0,len(text)-k+1)))

def cosine(left,right):
    if not left or not right:return 0.0
    denom=(sum(v*v for v in left.values())*sum(v*v for v in right.values()))**0.5
    return 0.0 if not denom else sum(v*right.get(k,0) for k,v in left.items())/denom

def train_rows(seed,count):
    rng=random.Random(seed); rows=[]
    for index in range(count):
        entity=rng.choice(ENTITIES[:4]); old,new=rng.sample(VALUES[:4],2); style=index%2
        before=STATE_FORMS[style].format(e=entity,v=old)
        command=rng.choice(TRAIN_FORMS).format(e=entity,v=new)
        after=STATE_FORMS[style].format(e=entity,v=new)
        rows.append((before,command,after))
    return rows

def edit_program(before,after):
    ops=[]
    for tag,i1,i2,j1,j2 in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
        if tag!="equal":ops.append((before[i1:i2],after[j1:j2]))
    return tuple(ops)

def execute(before,program):
    state=before
    for old,new in program:
        if old not in state:return None
        state=state.replace(old,new,1)
    return state

class PredictiveDisagreementModel:
    def fit(self,rows):
        self.rows=[(grams(command),edit_program(before,after),command) for before,command,after in rows]
        return self
    def candidates(self,before,command,k=6):
        query=grams(command); scored=[]
        for features,program,source in self.rows:
            future=execute(before,program)
            if future is not None:scored.append((cosine(query,features),program,future,source))
        scored.sort(reverse=True,key=lambda x:x[0])
        unique=[]
        for item in scored:
            if item[2] not in [x[2] for x in unique]:unique.append(item)
            if len(unique)>=k:break
        return unique
    @staticmethod
    def propose_query(candidates):
        if len(candidates)<2:return None,None
        first,second=candidates[0][2],candidates[1][2]
        left=[];right=[]
        for tag,i1,i2,j1,j2 in difflib.SequenceMatcher(None,first,second,autojunk=False).get_opcodes():
            if tag!="equal":
                if i2>i1:left.append(first[i1:i2])
                if j2>j1:right.append(second[j1:j2])
        a="".join(left).strip("。、！？ ")
        b="".join(right).strip("。、！？ ")
        if not a or not b or a==b:return None,None
        return f"確認です。候補は「{a}」と「{b}」のどちらですか？",(a,b)
    def predict(self,before,command,oracle=None,mode="active"):
        candidates=self.candidates(before,command)
        if not candidates:return None,None,0,0
        if mode=="passive":return candidates[0][2],None,len(candidates),0
        if mode=="no_query":return (candidates[0][2] if len(candidates)==1 else None),None,len(candidates),0
        question,options=self.propose_query(candidates)
        if question is None or oracle is None:return None,question,len(candidates),0
        answer=oracle(options)
        narrowed=[x for x in candidates if answer and answer in x[2]]
        return (narrowed[0][2] if len(narrowed)==1 else None),question,len(candidates)+len(narrowed),1
    def model_bytes(self):return len(pickle.dumps(self.rows))

def evaluate(seed,scale):
    rng=random.Random(seed+99)
    model=PredictiveDisagreementModel().fit(train_rows(seed,scale))
    accuracy={name:[] for name in ("passive","no_query","active")}
    reads={name:[] for name in accuracy}; query_rates={name:[] for name in accuracy}
    validity=[]; held=[]; index_reply=[]; three_way=[]
    started=time.perf_counter()
    for index in range(180):
        entity=rng.choice(ENTITIES[4:]); old,target,_=rng.sample(VALUES[:4],3); style=index%2
        before=STATE_FORMS[style].format(e=entity,v=old)
        command=rng.choice(AMBIGUOUS_FORMS).format(e=entity)
        gold=STATE_FORMS[style].format(e=entity,v=target)
        def oracle(options):return next((option for option in options if option in gold),None)
        for mode in accuracy:
            pred,question,count,queried=model.predict(before,command,oracle,mode)
            accuracy[mode].append(pred==gold);reads[mode].append(count);query_rates[mode].append(queried)
        candidates=model.candidates(before,command);question,options=model.propose_query(candidates)
        validity.append(bool(question and options and all(any(o in x[2] for x in candidates) for o in options)))
        def ordinal_oracle(options):return "後者"
        pred,_,_,_=model.predict(before,command,ordinal_oracle,"active")
        index_reply.append(pred==gold)
        third=VALUES[(VALUES.index(target)+1)%4]
        if third==old:third=VALUES[(VALUES.index(third)+1)%4]
        gold3=STATE_FORMS[style].format(e=entity,v=third)
        def third_oracle(options):return next((o for o in options if o in gold3),None)
        pred,_,_,_=model.predict(before,command,third_oracle,"active")
        three_way.append(pred==gold3)
    for index in range(90):
        entity=rng.choice(ENTITIES[4:]);old,target=rng.sample(VALUES[:4],2);style=index%2
        before=STATE_FORMS[style].format(e=entity,v=old)
        command=HELD_FORMS[index%2].format(e=entity,v=target)
        gold=STATE_FORMS[style].format(e=entity,v=target)
        def oracle(options):return next((o for o in options if o in gold),None)
        pred,_,_,_=model.predict(before,command,oracle,"active");held.append(pred==gold)
    elapsed=time.perf_counter()-started
    return {
        "seed":seed,"scale":scale,
        **{f"{name}_accuracy":statistics.mean(values) for name,values in accuracy.items()},
        "query_validity":statistics.mean(validity),
        "held_syntax_accuracy":statistics.mean(held),
        "ordinal_reply_accuracy":statistics.mean(index_reply),
        "three_way_accuracy":statistics.mean(three_way),
        **{f"{name}_reads":statistics.mean(values) for name,values in reads.items()},
        "active_query_rate":statistics.mean(query_rates["active"]),
        "program_count":len({program for _,program,_ in model.rows}),
        "model_bytes":model.model_bytes(),
        "evaluation_seconds":elapsed,
        "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "free_japanese_integrated_gate":0.0,
    }

def run():
    runs=[evaluate(seed,scale) for scale in (32,128,512) for seed in (1,7,19)]
    aggregate={}
    for scale in (32,128,512):
        selected=[row for row in runs if row["scale"]==scale]
        aggregate[str(scale)]={key:statistics.mean(row[key] for row in selected)
                               for key in selected[0] if key not in ("seed","scale")}
    return {
        "hypothesis":"Generate a confirmation utterance from the minimal predictive disagreement between executable future candidates, without pre-specified latent factor axes.",
        "aggregate":aggregate,"runs":runs,
        "verdict":"partial_support_as_literal_binary_query_proposer_but_open_set_dialogue_hypothesis_falsified",
        "claim":{"highschool_level_passed":False,"native_japanese_communication_passed":False,
                 "weak_smartphone_verified":False,"completion":False}
    }

if __name__=="__main__":
    print(json.dumps(run(),ensure_ascii=False,indent=2))
