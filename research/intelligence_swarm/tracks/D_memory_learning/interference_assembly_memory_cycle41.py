from __future__ import annotations
from dataclasses import dataclass
import argparse, json, math, pickle, random, resource, statistics, time
from collections import defaultdict

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末","大型端末":"大きい端末","北側の鍵":"北のキー","南側の鍵":"南のキー","試料甲":"サンプル甲","試料乙":"サンプル乙"}
VALUES=["棚A","棚B","棚C","棚D","待機","処理中","完了","保留","担当一","担当二","担当三","担当四"]
FILL=["補助記録は維持します。","別件は変更しません。","前段の注意事項はそのままです。"]

@dataclass
class Episode:
    before:str; command:str; after:str; query:str; answer:str
    obj:str; value:str; old:str; mode:str; session:int=0

@dataclass
class Generator:
    left_shape:str; right_shape:str; old_shape:str; new_shape:str
    cmd_prefix_shape:str; cmd_suffix_shape:str
    query_prefix_shape:str; query_suffix_shape:str
    support:int=0; write_ok:int=0; read_ok:int=0; wrong:int=0
    description_bits:int=0


def shape(s):
    out=[]
    for c in s:
        if c.isdigit(): out.append("D")
        elif c.isascii() and c.isalpha(): out.append("A")
        elif c in "。、：／=\n「」": out.append(c)
        else: out.append("J")
    return "".join(out)


def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]


def make_episode(rng,mode,session=0):
    obj=rng.choice(OBJECTS); surf=ALIASES[obj] if mode=="rename" else obj
    old=rng.choice(VALUES); new=rng.choice([v for v in VALUES if v!=old]); fill=rng.choice(FILL)
    if mode=="alternate":
        before=f"{fill} 現在、{surf}は{old}という状態です。"; command=f"次の状態を{new}へ切り替え、対象は{surf}とします。"; after=f"{fill} 現在、{surf}は{new}という状態です。"; query=f"{surf}について、いまの状態を答えてください。"
    elif mode=="order":
        before=f"{surf}の現在値は{old}です。{fill}"; command=f"{new}へ変更してください。対象は{surf}です。"; after=f"{surf}の現在値は{new}です。{fill}"; query=f"現在値を答えてください。対象は{surf}です。"
    elif mode=="nested":
        before=f"{surf}の現在値は{old}です。{fill}"; command=f"依頼内容は「{surf}の値を{new}へ変更してください」です。"; after=f"{surf}の現在値は{new}です。{fill}"; query=f"質問文は「{surf}の現在値は何ですか」です。"
    elif mode=="paragraph":
        before=f"{fill}\n{surf}の現在値は{old}です。\n{rng.choice(FILL)}"; command=f"{rng.choice(FILL)}\n{surf}を{new}へ変更してください。\n{rng.choice(FILL)}"; after=f"{fill}\n{surf}の現在値は{new}です。\n{rng.choice(FILL)}"; query=f"{rng.choice(FILL)}\n{surf}の現在値を答えてください。"
    elif mode=="free":
        before=f"作業メモです。{surf}については今のところ{old}として扱っています。"; command=f"方針を更新します。以後、{surf}は{new}扱いにしてください。"; after=f"作業メモです。{surf}については今のところ{new}として扱っています。"; query=f"確認です。{surf}はいま何扱いですか。"
    elif mode=="omission":
        before=f"{surf}の現在値は{old}です。{fill}"; command=f"それを{new}へ変更してください。"; after=f"{surf}の現在値は{new}です。{fill}"; query="その対象の現在値を答えてください。"
    else:
        before=f"{surf}の現在値は{old}です。{fill}"; command=f"{surf}の値を{new}へ変更してください。"; after=f"{surf}の現在値は{new}です。{fill}"; query=f"{surf}の現在値を答えてください。"
    return Episode(before,command,after,query,new,surf,new,old,mode,session)


def find_context(text,start,end,w=7): return text[max(0,start-w):start], text[end:end+w]

def induce(ep):
    l,r,old,new=diff(ep.before,ep.after)
    if not old or not new: return None
    p=ep.command.find(new); q=ep.query.find(ep.obj)
    if p<0 or q<0: return None
    left,right=find_context(ep.before,l,l+len(old)); cp,cs=find_context(ep.command,p,p+len(new)); qp,qs=find_context(ep.query,q,q+len(ep.obj))
    return Generator(shape(left),shape(right),shape(old),shape(new),shape(cp),shape(cs),shape(qp),shape(qs),support=1,description_bits=8*(len(left)+len(right)+len(cp)+len(cs)+len(qp)+len(qs)+4))

def all_spans(text,maxlen=12):
    for i in range(len(text)):
        for j in range(i+1,min(len(text),i+maxlen)+1): yield i,j,text[i:j]

def execute_write(g,ep):
    vals=[]
    for i,j,s in all_spans(ep.command,10):
        if shape(ep.command[max(0,i-7):i])==g.cmd_prefix_shape and shape(ep.command[j:j+7])==g.cmd_suffix_shape: vals.append(s)
    targets=[]
    for i,j,s in all_spans(ep.before,12):
        if shape(s)==g.old_shape and shape(ep.before[max(0,i-7):i])==g.left_shape and shape(ep.before[j:j+7])==g.right_shape: targets.append((i,j))
    return sorted(set(ep.before[:i]+v+ep.before[j:] for v in vals for i,j in targets))

def execute_read(g,ep):
    qhits=[]
    for i,j,s in all_spans(ep.query,12):
        if shape(ep.query[max(0,i-7):i])==g.query_prefix_shape and shape(ep.query[j:j+7])==g.query_suffix_shape: qhits.append(s)
    if not qhits: return []
    answers=[]
    for out in execute_write(g,ep):
        _,_,_,new=diff(ep.before,out)
        if new: answers.append(new)
    return sorted(set(answers))

def response(g,ep):
    ws=execute_write(g,ep); rs=execute_read(g,ep)
    closed=int(ep.after in ws and ep.answer in rs)
    wrong=int((bool(ws) and ep.after not in ws) or (bool(rs) and ep.answer not in rs))
    noexec=int(not ws or not rs)
    return closed,wrong,noexec

class Model:
    def __init__(self,mode):
        self.mode=mode; self.generators=[]; self.assemblies=[]; self.slow=[]; self.train_seconds=0.0; self.conflict_edges=0; self.synergy_edges=0
    def fit(self,induction,replay):
        t=time.perf_counter(); grouped={}
        for ep in induction:
            g=induce(ep)
            if not g: continue
            key=(g.left_shape,g.right_shape,g.old_shape,g.new_shape,g.cmd_prefix_shape,g.cmd_suffix_shape,g.query_prefix_shape,g.query_suffix_shape)
            if key not in grouped: grouped[key]=g
            else: grouped[key].support+=1
        self.generators=sorted(grouped.values(),key=lambda g:g.support,reverse=True)[:24]
        R=[[response(g,ep) for ep in replay] for g in self.generators]
        conflicts=defaultdict(set); synergy=defaultdict(set)
        for i in range(len(self.generators)):
            for j in range(i+1,len(self.generators)):
                c=sum(1 for k in range(len(replay)) if R[i][k][1] and R[j][k][1])
                joint=sum(1 for k in range(len(replay)) if (R[i][k][0] or R[j][k][0]) and not (R[i][k][1] and R[j][k][1]))
                indiv=max(sum(x[0] for x in R[i]),sum(x[0] for x in R[j]))
                if c>=2: conflicts[i].add(j); conflicts[j].add(i); self.conflict_edges+=1
                if joint>=indiv+2 and joint>0: synergy[i].add(j); synergy[j].add(i); self.synergy_edges+=1
        scores=[sum(x[0] for x in rr)-sum(x[1] for x in rr) for rr in R]
        order=sorted(range(len(scores)),key=lambda i:scores[i],reverse=True)
        assemblies=[]
        for seed in order:
            if scores[seed]<=0: continue
            a=[seed]
            for j in sorted(synergy[seed],key=lambda z:scores[z],reverse=True):
                if scores[j]>0 and all(j not in conflicts[x] for x in a) and len(a)<4: a.append(j)
            key=tuple(sorted(a))
            if key not in assemblies: assemblies.append(key)
        if self.mode=="shuffled":
            rng=random.Random(9173); rng.shuffle(R)
            assemblies=[]
            for seed in order:
                if scores[seed]>0: assemblies.append((seed,))
        self.assemblies=assemblies[:24]
        sessions=sorted(set(ep.session for ep in replay))
        for a in self.assemblies:
            good=0
            for s in sessions:
                eps=[(k,ep) for k,ep in enumerate(replay) if ep.session==s]
                ok=any(any(R[i][k][0] for i in a) and not any(R[i][k][1] for i in a) for k,_ in eps)
                good+=int(ok)
            if good>=2: self.slow.append(a)
        self.train_seconds=time.perf_counter()-t
    def active_assemblies(self):
        if self.mode=="base": return [(i,) for i in range(len(self.generators))]
        if self.mode=="slow": return self.slow
        return self.assemblies
    def predict(self,ep):
        candidates=[]
        for a in self.active_assemblies():
            outs=[]; ans=[]; total_support=0
            for i in a:
                g=self.generators[i]; outs += execute_write(g,ep); ans += execute_read(g,ep); total_support += g.support
            for w in sorted(set(outs)):
                for v in sorted(set(ans)):
                    candidates.append((total_support+0.1*len(a),w,v,a))
        if not candidates: return None,0
        candidates.sort(reverse=True)
        top=candidates[0]
        if len(candidates)>1 and abs(top[0]-candidates[1][0])<1e-9 and top[1:3]!=candidates[1][1:3]: return None,len(candidates)
        return top,len(candidates)

def evaluate(seed):
    rng=random.Random(seed)
    induction=[]; replay=[]
    for session in range(3):
        induction += [make_episode(rng,m,session) for m in (["seen"]*8+["rename"]*3+["order"]*3+["alternate"]*3)]
        replay += [make_episode(rng,m,session) for m in (["seen"]*4+["rename"]*2+["alternate"]*2)]
    tests={m:[make_episode(rng,m,4) for _ in range(10)] for m in ("seen","order","rename","alternate","nested","omission","paragraph","free")}
    out={}
    for mode in ("base","assembly","slow","shuffled"):
        model=Model(mode); model.fit(induction,replay)
        out[mode]={"generator_count":len(model.generators),"assembly_count":len(model.assemblies),"slow_count":len(model.slow),"conflict_edges":model.conflict_edges,"synergy_edges":model.synergy_edges,"model_bytes":len(pickle.dumps(model)),"training_seconds":model.train_seconds}
        for name,eps in tests.items():
            vals=[]; t=time.perf_counter()
            for ep in eps:
                pred,c=model.predict(ep)
                vals.append({"closed":pred is not None and pred[1]==ep.after and pred[2]==ep.answer,"read":pred is not None and pred[2]==ep.answer,"write":pred is not None and pred[1]==ep.after,"wrong":pred is not None and (pred[1]!=ep.after or pred[2]!=ep.answer),"null":pred is None,"candidates":c})
            ms=(time.perf_counter()-t)*1000/len(eps)
            out[mode][name]={k:statistics.mean(float(v[k]) for v in vals) for k in ("closed","read","write","wrong","null","candidates")}; out[mode][name]["inference_ms"]=ms
        ones=[]
        for ep in replay[:12]:
            pred,_=model.predict(ep); ones.append(int(pred is not None and pred[1]==ep.after and pred[2]==ep.answer))
        out[mode]["one_shot_closed"]=statistics.mean(ones)
        latest=[]; obsolete=[]
        for _ in range(12):
            ep1=make_episode(rng,"seen",5); ep2=make_episode(rng,"seen",6)
            ep2.obj=ep1.obj
            p,_=model.predict(ep2)
            latest.append(int(p is not None and p[2]==ep2.answer)); obsolete.append(int(p is not None and p[2]==ep1.answer and ep1.answer!=ep2.answer))
        out[mode]["latest_recall"]=statistics.mean(latest); out[mode]["obsolete_recall"]=statistics.mean(obsolete)
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="MEASUREMENTS_CYCLE_041.json"); args=ap.parse_args()
    raw={str(s):evaluate(s) for s in (1,7,19)}; summary={}
    for mode in ("base","assembly","slow","shuffled"):
        summary[mode]={}
        for key in raw["1"][mode]:
            if isinstance(raw["1"][mode][key],dict): summary[mode][key]={k:statistics.mean(raw[str(s)][mode][key][k] for s in (1,7,19)) for k in raw["1"][mode][key]}
            else: summary[mode][key]=statistics.mean(raw[str(s)][mode][key] for s in (1,7,19))
    payload={"cycle":41,"hypothesis":"Interference-Graph Memory Assemblies from Non-Additive Bidirectional Replay Closure","seeds":[1,7,19],"summary":summary,"raw":raw,"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"estimated_complexity":"induction O(NL), replay response O(QG), conflict graph O(G^2Q), greedy sparse assembly O(G^2), inference O(AGL)","fixed_ontology_or_handwritten_slots_used_by_model":False,"rag_or_external_llm_used":False,"final_outcome_used_for_ranking":False,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(args.output,"w",encoding="utf-8") as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
