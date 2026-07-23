from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict, Counter
import argparse, json, pickle, random, resource, statistics, time, re

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","北側の鍵","南側の鍵","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末","大型端末":"大きい端末","北側の鍵":"北のキー","南側の鍵":"南のキー","試料甲":"サンプル甲","試料乙":"サンプル乙"}
FIELDS=["場所","状態","担当"]
VALUES={"場所":["棚A","棚B","棚C","棚D"],"状態":["待機","処理中","完了","保留"],"担当":["担当一","担当二","担当三","担当四"]}
STATE0="{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。"
STATE1="{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。"
Q={"場所":["{o}の場所はどこですか？","{o}はどこにありますか？"],"状態":["{o}の状態はどうなっていますか？","{o}はいまどういう状態ですか？"],"担当":["{o}の担当は誰ですか？","{o}を受け持つのは誰ですか？"]}
CMD={"場所":["{o}を{v}へ移してください。","{o}の保管先を{v}へ変更します。"],"状態":["{o}を{v}にしてください。","{o}の進行状態を{v}へ切り替えます。"],"担当":["{o}を{v}の担当にしてください。","{o}の受け持ちを{v}へ変更します。"]}

@dataclass
class Ep:
    before:str; command:str; after:str; future:str; query:str; answer:str
    session:int; mode:str; canonical:str

@dataclass
class OpMem:
    left_shape:str; right_shape:str; old_shape:str; new_shape:str
    cmd_left_shape:str; cmd_right_shape:str
    query_kernel:tuple; write_kernel:tuple; read_kernel:tuple
    value:str; support:int; sessions:tuple; positive:int; negative:int; slow:bool=False


def state(o,d,alt=False):
    return (STATE1 if alt else STATE0).format(o=o,loc=d["場所"],status=d["状態"],owner=d["担当"])

def build(seed,n,mode):
    rng=random.Random(seed); world={}; out=[]
    for i in range(n):
        canon=rng.choice(OBJECTS); o=ALIASES[canon] if mode=="rename" else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS})
        f=rng.choice(FIELDS); old=world[canon][f]; new=rng.choice([x for x in VALUES[f] if x!=old])
        before=state(o,world[canon],mode=="alternate")
        cmd=rng.choice(CMD[f]).format(o=o,v=new)
        if mode=="held":
            cmd={"場所":f"対象{o}は次から{new}で保管。","状態":f"対象{o}は以後{new}として運用。","担当":f"対象{o}の受持を{new}へ。"}[f]
        elif mode=="omitted":
            cmd={"場所":f"それを{new}へ移してください。","状態":f"その対象を{new}にしてください。","担当":f"担当は{new}へ変えてください。"}[f]
        elif mode=="paragraph":
            cmd="前段の説明があります。別件は変更しません。\n"+cmd+"\n補助記録は維持してください。"
        elif mode=="free":
            cmd={"場所":f"{o}は今後{new}に置くことにしよう。","状態":f"{o}はこれから{new}扱いで。","担当":f"{o}は{new}に任せる。"}[f]
        world[canon][f]=new; after=state(o,world[canon],mode=="alternate")
        future=f"次の観測でも{o}について更新された内容は{new}で維持されます。"
        query=rng.choice(Q[f]).format(o=o)
        if mode=="free":
            query={"場所":f"{o}を探すなら今どこを見ればいい？","状態":f"{o}はいまどんな具合？","担当":f"{o}を今みている人は誰？"}[f]
        out.append(Ep(before,cmd,after,future,query,new,i//6,mode,canon))
    return out

def shape(s):
    return "".join("A" if c.isascii() and c.isalnum() else "J" if c not in "。、：／=？\n " else c for c in s)

def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

def segments(t):
    xs=[x for x in re.split(r"[。、：／=？\n\s]+|(?:は|を|へ|に|の|で|と|が)",t) if 1<=len(x)<=14]
    out=[]
    for x in xs:
        out.append(x)
        if len(x)>4:out += [x[:4],x[-4:]]
    return list(dict.fromkeys(out))[:32]

def sim(a,b):
    A=set(a);B=set(b);return len(A&B)/max(1,len(A|B))

def q6(x):return int(round(max(-1,min(1,x))*6))

def replace_once(text,left,right,value,old_shape):
    starts=[]; pos=0
    while True:
        i=text.find(left,pos) if left else pos
        if i<0:break
        a=i+len(left); b=text.find(right,a) if right else len(text)
        if b>=a and shape(text[a:b])==old_shape:starts.append((a,b))
        pos=i+1
        if not left or pos>=len(text):break
    if len(starts)!=1:return None
    a,b=starts[0];return text[:a]+value+text[b:]

def inverse_once(text,left,right,old,new_shape):
    starts=[];pos=0
    while True:
        i=text.find(left,pos) if left else pos
        if i<0:break
        a=i+len(left);b=text.find(right,a) if right else len(text)
        if b>=a and shape(text[a:b])==new_shape:starts.append((a,b))
        pos=i+1
        if not left or pos>=len(text):break
    if len(starts)!=1:return None
    a,b=starts[0];return text[:a]+old+text[b:]

def kernel(ep,left,right,old,new):
    pred=replace_once(ep.before,left,right,new,shape(old))
    if pred is None:return (0,0,0,0,0)
    inv=inverse_once(pred,left,right,old,shape(new))
    write_ok=int(pred==ep.after)
    inverse_ok=int(inv==ep.before)
    preserve=q6(sim(ep.before,pred)-sim(ep.before,ep.after))
    future=q6(sim(pred,ep.future)-sim(ep.before,ep.future))
    idempotent=int(replace_once(pred,left,right,new,shape(new))==pred)
    return (write_ok,inverse_ok,preserve,future,idempotent)

def query_kernel(ep):
    return (q6(sim(ep.query,ep.before)),q6(sim(ep.query,ep.command)),len(segments(ep.query))//2,shape(ep.query)[:12])

class Learner:
    def __init__(self,mode):
        self.mode=mode;self.mem=[];self.updates=0;self.training_seconds=0
    def fit(self,train,probe):
        t=time.perf_counter(); candidates=[]
        for ep in train:
            l,r,old,new=diff(ep.before,ep.after)
            if not old or not new:continue
            p=ep.command.find(new)
            if p<0:continue
            left=ep.before[max(0,l-8):l];right=ep.before[len(ep.before)-r:len(ep.before)-r+8] if r else ""
            cl=ep.command[max(0,p-8):p];cr=ep.command[p+len(new):p+len(new)+8]
            wk=kernel(ep,left,right,old,new)
            if wk[0] and wk[1]:
                candidates.append((left,right,old,new,cl,cr,query_kernel(ep),wk,ep.answer,ep.session))
        stats=defaultdict(lambda:{"pos":0,"neg":0,"sess":set(),"q":Counter(),"wk":Counter(),"rk":Counter(),"value":Counter()})
        for left,right,old,new,cl,cr,qk,wk,val,sess in candidates:
            key=(shape(left),shape(right),shape(old),shape(new),shape(cl),shape(cr))
            st=stats[key];st["q"][qk]+=1;st["wk"][wk]+=1;st["value"][val]+=1;st["sess"].add(sess)
        for ep in probe:
            for key,st in stats.items():
                ls,rs,osh,nsh,cls,crs=key
                vals=[x for x in segments(ep.command) if shape(x)==nsh and x not in ep.before][:8]
                bounds=[]
                for left in segments(ep.before):
                    if shape(left)!=ls:continue
                    for right in segments(ep.before):
                        if shape(right)!=rs:continue
                        bounds.append((left,right))
                for left,right in bounds[:16]:
                    for v in vals:
                        pred=replace_once(ep.before,left,right,v,osh)
                        if pred is None:continue
                        self.updates+=1
                        rk=(int(pred==ep.after),q6(sim(ep.query,pred)-sim(ep.query,ep.before)),q6(sim(pred,ep.future)-sim(ep.before,ep.future)))
                        st["rk"][rk]+=1
                        if pred==ep.after:st["pos"]+=1;st["sess"].add(ep.session+100)
                        else:st["neg"]+=1
        mem=[]
        for key,st in stats.items():
            support=sum(st["value"].values());pos=st["pos"];neg=st["neg"]
            qk=st["q"].most_common(1)[0][0];wk=st["wk"].most_common(1)[0][0]
            rk=st["rk"].most_common(1)[0][0] if st["rk"] else (0,0,0)
            value=st["value"].most_common(1)[0][0]
            slow=pos>=2 and len(st["sess"])>=2 and neg<=pos
            mem.append(OpMem(*key,qk,wk,rk,value,support,tuple(sorted(st["sess"])),pos,neg,slow))
        self.mem=sorted(mem,key=lambda m:(m.slow,m.positive-m.negative,m.support),reverse=True)[:64]
        self.training_seconds=time.perf_counter()-t
    def score(self,ep,m):
        qk=query_kernel(ep)
        qs=sum(a==b for a,b in zip(qk[:3],m.query_kernel[:3]))/3
        vals=[x for x in segments(ep.command) if shape(x)==m.new_shape and x not in ep.before][:8]
        best=-1e9;bestv=None
        for left in segments(ep.before):
            if shape(left)!=m.left_shape:continue
            for right in segments(ep.before):
                if shape(right)!=m.right_shape:continue
                for v in vals:
                    pred=replace_once(ep.before,left,right,v,m.old_shape)
                    if pred is None:continue
                    forward=(q6(sim(ep.query,pred)-sim(ep.query,ep.before)),int("補助" in pred)==int("補助" in ep.before))
                    functional=.5*forward[1]+.1*forward[0]
                    sc=qs+functional+.05*(m.positive-m.negative)+.01*m.support
                    if sc>best:best=sc;bestv=v
        return best,bestv
    def read(self,ep):
        pool=[m for m in self.mem if self.mode!="slow" or m.slow]
        cs=[]
        for m in pool:
            score,v=self.score(ep,m)
            if v is not None:cs.append((score,v))
        if not cs:return None
        cs.sort(reverse=True)
        if len(cs)>1 and cs[0][0]-cs[1][0]<.12:return None
        return cs[0][1]

def evaluate(m,test):
    t=time.perf_counter();ok=wrong=null=0
    for ep in test:
        g=m.read(ep);ok+=g==ep.answer;wrong+=g is not None and g!=ep.answer;null+=g is None
    n=len(test);return {"accuracy":ok/n,"wrong_read":wrong/n,"null_rate":null/n,"inference_ms":(time.perf_counter()-t)*1000/n}

def run(seed):
    alltrain=build(seed,54,"seen")+build(seed+17,27,"held")
    cut=int(len(alltrain)*.7);train,probe=alltrain[:cut],alltrain[cut:]
    models={}
    for mode in ("surface","operator","slow"):
        m=Learner(mode);m.fit(train,probe);models[mode]=m
    out={}
    for mode in ("seen","held","rename","alternate","omitted","paragraph","free"):
        test=build(seed+999,18,mode);out[mode]={k:evaluate(m,test) for k,m in models.items()}
    out["diag"]={k:{"model_bytes":len(pickle.dumps(m)),"memory":len(m.mem),"slow_memory":sum(x.slow for x in m.mem),"updates":m.updates,"training_seconds":m.training_seconds,"positive":sum(x.positive for x in m.mem),"negative":sum(x.negative for x in m.mem)} for k,m in models.items()}
    one=build(seed+5,1,"seen")
    long=build(seed+6,72,"seen")+build(seed+7,72,"paragraph")
    inter=long[:18]
    unknown=build(seed+8,54,"free"); up=unknown[-18:]
    latest=build(seed+9,72,"seen"); lp=latest[-18:]
    for name,tr,te in (("one_shot",one,one),("long_dialogue",long,inter),("unknown_transfer",unknown,up),("interference_latest",latest,lp)):
        out[name]={}
        c=max(1,int(len(tr)*.7));a,b=tr[:c],tr[c:]
        for mode in ("surface","operator","slow"):
            m=Learner(mode);m.fit(a,b);out[name][mode]=evaluate(m,te)["accuracy"]
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="results_cycle_030.json");a=ap.parse_args()
    runs=[run(s) for s in (1,7,19)];summary={}
    for mode in ("seen","held","rename","alternate","omitted","paragraph","free"):
        summary[mode]={}
        for method in ("surface","operator","slow"):
            summary[mode][method]={k:statistics.mean(r[mode][method][k] for r in runs) for k in runs[0][mode][method]}
    summary["diag"]={m:{k:statistics.mean(r["diag"][m][k] for r in runs) for k in runs[0]["diag"][m]} for m in ("surface","operator","slow")}
    for name in ("one_shot","long_dialogue","unknown_transfer","interference_latest"):
        summary[name]={m:statistics.mean(r[name][m] for r in runs) for m in ("surface","operator","slow")}
    payload={"cycle":30,"hypothesis":"Operator-Centered Memory Endpoints from Bidirectional Read-Write Consequence Kernels","seeds":[1,7,19],"raw":runs,"summary":summary,
             "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             "estimated_complexity":"operator induction O(NL), independent probe audit O(PBVL), read O(BCL), B<=64",
             "fixed_value_inventory_used_by_learner":False,"test_answers_used_for_retrieval":False,"independent_probe_partition":True,
             "highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(a.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
