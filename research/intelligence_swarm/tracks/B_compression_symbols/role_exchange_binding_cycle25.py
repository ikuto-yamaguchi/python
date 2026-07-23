from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse, json, math, pickle, random, resource, statistics, time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末","大型端末":"大きい端末",
         "北側の鍵":"北のキー","南側の鍵":"南のキー","試料甲":"サンプル甲","試料乙":"サンプル乙"}
FIELDS=["場所","状態","担当"]
VALUES={"場所":["棚A","棚B","棚C","棚D"],"状態":["待機","処理中","完了","保留"],"担当":["担当一","担当二","担当三","担当四"]}
STATE0="{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。"
STATE1="{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。"
CMDS={"場所":["{o}を{v}へ移してください。","{o}の保管先を{v}へ変更します。"],
      "状態":["{o}を{v}にしてください。","{o}の進行状態を{v}へ切り替えます。"],
      "担当":["{o}を{v}の担当にしてください。","{o}の受け持ちを{v}へ変更します。"]}
HELD_ORDER={"場所":["{v}へ移してください、対象は{o}です。"],"状態":["{v}扱いにしてください、対象は{o}です。"],"担当":["{v}へ引き継いでください、対象は{o}です。"]}
HELD_LEX={"場所":["対象{o}は次から{v}で保管。"],"状態":["対象{o}は以後{v}として運用。"],"担当":["対象{o}の受持を{v}へ。"]}
OMIT={"場所":["それを{v}へ移してください。"],"状態":["その対象を{v}にしてください。"],"担当":["担当は{v}へ変えてください。"]}

@dataclass
class Ex:
    before:str; command:str; after:str; future:str
    obj:str; field:str; old:str; new:str; mode:str

@dataclass
class Seed:
    text:str; role:str; left:str; right:str
    support:int=0; swap_success:int=0; swap_wrong:int=0; inverse_success:int=0; damage:int=0

@dataclass
class Program:
    obj_left:str; obj_right:str; val_left:str; val_right:str
    state_left:str; state_right:str
    support:int; wrong:int
    def bits(self):
        return 8*(len(self.obj_left)+len(self.obj_right)+len(self.val_left)+len(self.val_right)+len(self.state_left)+len(self.state_right)+12)

def state(o,d,form):
    return (STATE1 if form else STATE0).format(o=o,loc=d["場所"],status=d["状態"],owner=d["担当"])

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]: l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]: r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

def contexts(text,span,w=8):
    out=[];p=0
    while span:
        i=text.find(span,p)
        if i<0:break
        out.append((text[max(0,i-w):i],text[i+len(span):i+len(span)+w]))
        p=i+1
    return out

def repeated_spans(ex,max_len=10):
    cmd={ex.command[i:j] for i in range(len(ex.command)) for j in range(i+1,min(len(ex.command),i+max_len)+1)}
    before={ex.before[i:j] for i in range(len(ex.before)) for j in range(i+1,min(len(ex.before),i+max_len)+1)}
    after={ex.after[i:j] for i in range(len(ex.after)) for j in range(i+1,min(len(ex.after),i+max_len)+1)}
    future={ex.future[i:j] for i in range(len(ex.future)) for j in range(i+1,min(len(ex.future),i+max_len)+1)}
    obj=[x for x in cmd & before & after & future if 2<=len(x)<=10]
    val=[x for x in cmd & after & future if 1<=len(x)<=8 and x not in before]
    return sorted(obj,key=lambda x:(len(x),x))[:12],sorted(val,key=lambda x:(len(x),x))[:12]

def replace_one(text,old,new):
    i=text.find(old)
    return None if i<0 else text[:i]+new+text[i+len(old):]

def build(seed,n,mode):
    rng=random.Random(seed);world={};out=[]
    for _ in range(n):
        canon=rng.choice(OBJECTS);surf=ALIASES[canon] if mode=="rename" else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS})
        f=rng.choice(FIELDS);old=world[canon][f];new=rng.choice([x for x in VALUES[f] if x!=old])
        form=1 if mode=="alternate" else 0
        before=state(surf,world[canon],form)
        forms=HELD_ORDER[f] if mode=="order" else HELD_LEX[f] if mode=="lexeme" else OMIT[f] if mode=="omitted" else CMDS[f]
        command=rng.choice(forms).format(o=surf,v=new)
        if mode=="nested":command="依頼内容は「"+command+"」です。"
        if mode=="paragraph":command="前段の説明があります。別件は変更しません。\n"+command+"\n補助記録は維持してください。"
        world[canon][f]=new;after=state(surf,world[canon],form)
        future=f"次の観測でも{surf}の更新結果は{new}で、補助記録は維持されます。"
        out.append(Ex(before,command,after,future,surf,f,old,new,mode))
    return out

class Model:
    def __init__(self,mode):
        self.mode=mode;self.obj_seeds=[];self.val_seeds=[];self.programs=[]
        self.raw_candidates=0;self.permutation_tests=0;self.accepted_obj=0;self.accepted_val=0
        self.description_bits=0;self.training_seconds=0.0
    def fit(self,eps):
        t=time.perf_counter();obj_occ=[];val_occ=[]
        for ei,e in enumerate(eps):
            os,vs=repeated_spans(e);self.raw_candidates+=len(os)+len(vs)
            for x in os:
                for l,r in contexts(e.command,x):
                    obj_occ.append((ei,x,l,r))
            for x in vs:
                for l,r in contexts(e.command,x):
                    val_occ.append((ei,x,l,r))
        obj_stats=defaultdict(lambda:[0,0,0,0]); val_stats=defaultdict(lambda:[0,0,0,0])
        for occ,other,role,stats in ((obj_occ,obj_occ,"obj",obj_stats),(val_occ,val_occ,"val",val_stats)):
            for a in occ[:160]:
                for b in other[:160]:
                    if a[0]==b[0] or a[1]==b[1]: continue
                    self.permutation_tests+=1
                    ea=eps[a[0]]
                    originals=(ea.before,ea.command,ea.after,ea.future)
                    if role=="obj":
                        views=[replace_one(text,a[1],b[1]) for text in originals]
                        if any(z is None for z in views): continue
                    else:
                        views=[ea.before]+[replace_one(text,a[1],b[1]) for text in originals[1:]]
                        if any(z is None for z in views[1:]): continue
                    before,command,after,future=views
                    consistent=(b[1] in before and b[1] in command and b[1] in after and b[1] in future) if role=="obj" else (b[1] in command and b[1] in after and b[1] in future and before==ea.before)
                    damage=("補助記録" not in after or "維持" not in future)
                    if role=="obj":
                        inv=all(replace_one(z,b[1],a[1])==orig for z,orig in zip(views,originals))
                    else:
                        inv=(views[0]==originals[0] and all(replace_one(z,b[1],a[1])==orig for z,orig in zip(views[1:],originals[1:])))
                    key=(a[2],a[3])
                    stats[key][0]+=1
                    stats[key][1]+=int(consistent and not damage)
                    stats[key][2]+=int(not consistent or damage)
                    stats[key][3]+=int(inv)
        def retain(stats,role):
            arr=[]
            for (l,r),(n,s,w,inv) in stats.items():
                if n>=4 and s/n>=.8 and w/n<=.2 and inv/n>=.8:
                    arr.append(Seed("",role,l,r,n,s,w,inv,0))
            return sorted(arr,key=lambda x:(x.swap_success/x.support,x.inverse_success/x.support,x.support),reverse=True)[:32]
        self.obj_seeds=retain(obj_stats,"obj")
        self.val_seeds=retain(val_stats,"val")
        self.accepted_obj=len(self.obj_seeds);self.accepted_val=len(self.val_seeds)
        state_ctx=Counter()
        for e in eps:
            l,r,old,new=diff(e.before,e.after)
            if old and new:
                sl=e.before[max(0,l-8):l]
                sr=e.before[len(e.before)-r:len(e.before)-r+8] if r else e.before[l+len(old):l+len(old)+8]
                state_ctx[(sl,sr)]+=1
        learned_state=[x for x,_ in state_ctx.most_common(8)]
        for o in self.obj_seeds:
            for v in self.val_seeds:
                for sl,sr in learned_state:
                    self.programs.append(Program(o.left,o.right,v.left,v.right,sl,sr,min(o.support,v.support),o.swap_wrong+v.swap_wrong))
        self.programs=self.programs[:64]
        literal_bits=sum(8*(len(e.command)+len(e.before)+len(e.after)) for e in eps)
        library_bits=sum(p.bits()+16 for p in self.programs)+sum(64 for _ in eps)
        self.description_bits=library_bits if self.mode=="mdl" else literal_bits
        if self.mode=="mdl" and library_bits>=literal_bits:
            self.programs=[]
        self.training_seconds=time.perf_counter()-t
    def extract_between(self,text,l,r,max_len=14):
        starts=[0] if not l else [];p=0
        while l:
            i=text.find(l,p)
            if i<0:break
            starts.append(i+len(l));p=i+1
        vals=[]
        for st in starts:
            en=text.find(r,st) if r else len(text)
            if en>=st and 0<en-st<=max_len:vals.append(text[st:en])
        return vals
    def predict(self,e):
        cand=[]
        for p in self.programs:
            os=self.extract_between(e.command,p.obj_left,p.obj_right,12)
            vs=self.extract_between(e.command,p.val_left,p.val_right,12)
            if not os or not vs:continue
            for o in os[:2]:
                for v in vs[:2]:
                    if e.before.find(o)<0:continue
                    starts=[];q=0;sl,sr=p.state_left,p.state_right
                    while True:
                        j=e.before.find(sl,q) if sl else q
                        if j<0:break
                        a=j+len(sl);b=e.before.find(sr,a) if sr else len(e.before)
                        if b>=a:starts.append((a,b))
                        q=j+1
                        if not sl or q>=len(e.before):break
                    for a,b in starts:
                        pred=e.before[:a]+v+e.before[b:]
                        score=p.support-2*p.wrong+int(o in e.before)+int(o in e.command)
                        cand.append((score,pred,o,v))
        if not cand:return e.before,False,0,[]
        by={}
        for score,pred,o,v in cand:
            if pred not in by or score>by[pred][0]:by[pred]=(score,o,v)
        ranked=sorted([(s,pred,o,v) for pred,(s,o,v) in by.items()],reverse=True)
        if len(ranked)>1 and ranked[0][0]==ranked[1][0]:
            return e.before,False,len(ranked),[(x[2],x[3]) for x in ranked[:16]]
        return ranked[0][1],True,len(ranked),[(x[2],x[3]) for x in ranked[:16]]

def evaluate(seed,n,mode):
    train=build(seed,n,"seen");test=build(seed+999,48,mode);out={}
    for method in ("surface","permutation","mdl"):
        M=Model(method);M.fit(train)
        if method=="surface":
            M.obj_seeds=[];M.val_seeds=[];M.programs=[]
            for e in train:
                os,vs=repeated_spans(e)
                for o in os[:1]:
                    for l,r in contexts(e.command,o)[:1]:M.obj_seeds.append(Seed(o,"obj",l,r,1,1,0,1,0))
                for v in vs[:1]:
                    for l,r in contexts(e.command,v)[:1]:M.val_seeds.append(Seed(v,"val",l,r,1,1,0,1,0))
            M.obj_seeds=M.obj_seeds[:32];M.val_seeds=M.val_seeds[:32]
            state_ctx=Counter()
            for e in train:
                l,r,old,new=diff(e.before,e.after)
                if old and new:
                    sl=e.before[max(0,l-8):l]
                    sr=e.before[len(e.before)-r:len(e.before)-r+8] if r else e.before[l+len(old):l+len(old)+8]
                    state_ctx[(sl,sr)]+=1
            M.programs=[Program(o.left,o.right,v.left,v.right,sl,sr,1,0)
                        for o in M.obj_seeds for v in M.val_seeds
                        for sl,sr in [x for x,_ in state_ctx.most_common(8)]][:64]
        t=time.perf_counter();correct=wrong=null=cand=pairrec=0
        for e in test:
            pred,did,k,pairs=M.predict(e);cand+=k
            correct+=int(did and pred==e.after);wrong+=int(did and pred!=e.after);null+=int(not did)
            pairrec+=int(any(o==e.obj and v==e.new for o,v in pairs))
        out[method]={"accuracy":correct/len(test),"wrong_commit":wrong/len(test),"null_rate":null/len(test),
                     "pair_recall":pairrec/len(test),"mean_candidates":cand/len(test),
                     "object_role_seeds":len(M.obj_seeds),"value_role_seeds":len(M.val_seeds),
                     "programs":len(M.programs),"raw_candidates":M.raw_candidates,
                     "permutation_tests":M.permutation_tests,"description_bits":M.description_bits,
                     "model_bytes":len(pickle.dumps(M)),"training_seconds":M.training_seconds,
                     "inference_ms":(time.perf_counter()-t)*1000/len(test)}
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="results_cycle_025.json");args=ap.parse_args()
    modes=["seen","order","lexeme","rename","alternate","nested","omitted","paragraph"]
    raw={}
    for n in (48,144,288):
        runs=[]
        for seed in (1,7,19):runs.append({m:evaluate(seed,n,m) for m in modes})
        raw[str(n)]=runs
    summary={}
    for n,runs in raw.items():
        summary[n]={}
        for m in modes:
            summary[n][m]={}
            for method in ("surface","permutation","mdl"):
                summary[n][m][method]={k:statistics.mean(r[m][method][k] for r in runs) for k in runs[0][m][method]}
    payload={"cycle":25,"hypothesis":"Role-Exchange Binding Seeds from Cross-Episode Permutation Tests",
             "seeds":[1,7,19],"sizes":[48,144,288],"raw":raw,"summary":summary,
             "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             "estimated_complexity":"candidate O(NL^2), permutation audit O(R^2 L), library O(OV), inference O(PL^2), caps R<=160 P<=64",
             "hidden_labels_used_by_learner":False,"highschool_level_passed":False,
             "native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(args.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary["288"],ensure_ascii=False,indent=2))
if __name__=="__main__":main()
