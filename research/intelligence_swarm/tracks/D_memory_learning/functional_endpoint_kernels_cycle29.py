from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
import argparse,json,pickle,random,resource,statistics,time,re,math

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末","大型端末":"大きい端末","試料甲":"サンプル甲","試料乙":"サンプル乙"}
FIELDS=["場所","状態","担当"]
VALUES={"場所":["棚A","棚B","棚C","棚D"],"状態":["待機","処理中","完了","保留"],"担当":["担当一","担当二","担当三","担当四"]}
STATE0="{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。"
STATE1="{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。"
Q={"場所":["{o}の場所はどこですか？","{o}はどこにありますか？"],"状態":["{o}の状態はどうなっていますか？","{o}はいまどういう状態ですか？"],"担当":["{o}の担当は誰ですか？","{o}を受け持つのは誰ですか？"]}
CMD={"場所":["{o}を{v}へ移してください。","{o}の保管先を{v}へ変更します。"],"状態":["{o}を{v}にしてください。","{o}の進行状態を{v}へ切り替えます。"],"担当":["{o}を{v}の担当にしてください。","{o}の受け持ちを{v}へ変更します。"]}

@dataclass
class Ep:
    before:str;command:str;after:str;future:str;query:str;answer:str;session:int;mode:str

def state(o,d,alt=False):
    return (STATE1 if alt else STATE0).format(o=o,loc=d["場所"],status=d["状態"],owner=d["担当"])

def build(seed,n,mode):
    rng=random.Random(seed);world={};out=[]
    for i in range(n):
        canon=rng.choice(OBJECTS);o=ALIASES[canon] if mode=="rename" else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS})
        f=rng.choice(FIELDS);new=rng.choice([x for x in VALUES[f] if x!=world[canon][f]])
        before=state(o,world[canon],mode=="alternate")
        cmd=rng.choice(CMD[f]).format(o=o,v=new)
        if mode=="held":cmd={"場所":f"対象{o}は次から{new}で保管。","状態":f"対象{o}は以後{new}として運用。","担当":f"対象{o}の受持を{new}へ。"}[f]
        elif mode=="omitted":cmd={"場所":f"それを{new}へ移してください。","状態":f"その対象を{new}にしてください。","担当":f"担当は{new}へ変えてください。"}[f]
        elif mode=="paragraph":cmd="前段の説明があります。別件は変更しません。\n"+cmd+"\n補助記録は維持してください。"
        world[canon][f]=new;after=state(o,world[canon],mode=="alternate")
        future=f"次の観測でも{o}について更新された内容は{new}で維持されます。"
        query=rng.choice(Q[f]).format(o=o)
        if mode=="free":query={"場所":f"{o}を探すなら今どこを見ればいい？","状態":f"{o}はいまどんな具合？","担当":f"{o}を今みている人は誰？"}[f]
        out.append(Ep(before,cmd,after,future,query,new,i//6,mode))
    return out

def shape(s):return "".join("A" if c.isascii() and c.isalnum() else "J" if c not in "。、：／=？\n " else c for c in s)
def sim(a,b):
    A=set(a);B=set(b);return len(A&B)/max(1,len(A|B))
def remove(t,s):
    i=t.find(s);return t if i<0 else t[:i]+t[i+len(s):]
def q(x):return int(round(max(-1,min(1,x))*6))
def segs(t):
    xs=[x for x in re.split(r"[。、：／=？\n\s]+|(?:は|を|へ|に|の|で|と|が)",t) if 1<=len(x)<=12]
    out=[]
    for x in xs:
        out.append(x)
        if len(x)>4:out += [x[:4],x[-4:]]
    return list(dict.fromkeys(out))[:24]

def response(ep,span,view):
    texts={"query":ep.query,"after":ep.after,"future":ep.future,"command":ep.command,"before":ep.before}
    base=(sim(ep.query,ep.after),sim(ep.command,ep.after),sim(ep.after,ep.future),sim(ep.before,ep.after))
    p=dict(texts);p[view]=remove(texts[view],span)
    cur=(sim(p["query"],p["after"]),sim(p["command"],p["after"]),sim(p["after"],p["future"]),sim(p["before"],p["after"]))
    pos=texts[view].find(span);bucket=-1 if pos<0 else min(5,int(6*pos/max(1,len(texts[view]))))
    return (view,bucket,min(12,len(span)),shape(span))+tuple(q(c-b) for b,c in zip(base,cur))

@dataclass
class Mem:
    value:str;qk:tuple;sk:tuple;fk:tuple;support:int;sessions:tuple;slow:bool=False

class Learner:
    def __init__(self,mode):self.mode=mode;self.mem=[];self.updates=0;self.training_seconds=0
    def fit(self,eps):
        t=time.perf_counter();d={}
        for ep in eps:
            qs=segs(ep.query)
            if not qs or ep.answer not in ep.after:continue
            qb=max(qs,key=lambda s:abs(response(ep,s,"query")[-3]))
            key=(response(ep,qb,"query"),response(ep,ep.answer,"after"),response(ep,ep.answer,"future"),ep.answer)
            d.setdefault(key,[0,set()]);d[key][0]+=1;d[key][1].add(ep.session);self.updates+=3
        self.mem=[]
        for (qk,sk,fk,v),(n,sess) in d.items():
            self.mem.append(Mem(v,qk,sk,fk,n,tuple(sess),n>=2 and len(sess)>=2))
        self.mem=sorted(self.mem,key=lambda m:(m.slow,m.support),reverse=True)[:64]
        self.training_seconds=time.perf_counter()-t
    def qk(self,ep):
        pseudo=Ep(ep.before,ep.command,ep.before,ep.before,ep.query,"",ep.session,ep.mode)
        xs=segs(ep.query)
        if not xs:return ("query",-1,0,"",0,0,0,0)
        b=max(xs,key=lambda s:abs(response(pseudo,s,"query")[-3]))
        return response(pseudo,b,"query")
    def score(self,ep,m):
        if self.mode=="surface":
            return (1 if m.value in ep.after else 0)+.02*m.support
        qk=self.qk(ep);qs=sum(a==b for a,b in zip(qk[1:],m.qk[1:]))/(len(qk)-1)
        pseudo=Ep(ep.before,ep.command,ep.after,ep.after,ep.query,"",ep.session,ep.mode)
        best=0
        for s in segs(ep.after):
            sk=response(pseudo,s,"after")
            best=max(best,sum(a==b for a,b in zip(sk[1:],m.sk[1:]))/(len(sk)-1))
        return qs+best+.03*m.support
    def read(self,ep):
        cs=[(self.score(ep,m),m.value) for m in self.mem if self.mode!="slow" or m.slow]
        if not cs:return None
        cs.sort(reverse=True)
        if len(cs)>1 and cs[0][0]-cs[1][0]<.05:return None
        return cs[0][1]

def evaluate(m,test):
    t=time.perf_counter();ok=wrong=null=0
    for ep in test:
        g=m.read(ep);ok+=g==ep.answer;wrong+=g is not None and g!=ep.answer;null+=g is None
    n=len(test);return {"accuracy":ok/n,"wrong_read":wrong/n,"null_rate":null/n,"inference_ms":(time.perf_counter()-t)*1000/n}

def run(seed):
    train=build(seed,36,"seen")+build(seed+17,18,"held");models={}
    for mode in ("surface","kernel","slow"):
        m=Learner(mode);m.fit(train);models[mode]=m
    out={}
    for mode in ("seen","held","rename","alternate","omitted","paragraph","free"):
        test=build(seed+999,18,mode);out[mode]={k:evaluate(m,test) for k,m in models.items()}
    out["diag"]={k:{"model_bytes":len(pickle.dumps(m)),"memory":len(m.mem),"slow_memory":sum(x.slow for x in m.mem),"updates":m.updates,"training_seconds":m.training_seconds} for k,m in models.items()}
    one=build(seed+5,1,"seen");it=build(seed+6,18,"seen")+build(seed+7,36,"paragraph");probe=it[:9];lat=build(seed+8,36,"seen");lprobe=lat[-9:]
    for name,tr,te in (("one_shot",one,one),("interference",it,probe),("latest",lat,lprobe)):
        out[name]={}
        for mode in ("surface","kernel","slow"):
            m=Learner(mode);m.fit(tr);out[name][mode]=evaluate(m,te)["accuracy"]
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="results_cycle_029.json");a=ap.parse_args()
    runs=[run(s) for s in (1,7,19)];summary={}
    for mode in ("seen","held","rename","alternate","omitted","paragraph","free"):
        summary[mode]={}
        for method in ("surface","kernel","slow"):
            summary[mode][method]={k:statistics.mean(r[mode][method][k] for r in runs) for k in runs[0][mode][method]}
    summary["diag"]={m:{k:statistics.mean(r["diag"][m][k] for r in runs) for k in runs[0]["diag"][m]} for m in ("surface","kernel","slow")}
    for name in ("one_shot","interference","latest"):
        summary[name]={m:statistics.mean(r[name][m] for r in runs) for m in ("surface","kernel","slow")}
    payload={"cycle":29,"hypothesis":"Functional Endpoint Birth from Cross-Channel Intervention Response Kernels","seeds":[1,7,19],"raw":runs,"summary":summary,
             "peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             "estimated_complexity":"segment O(NL), response audit O(NSC), read O(BCL), B<=64",
             "fixed_value_inventory_used_by_learner":False,"test_answers_used_for_retrieval":False,
             "highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(a.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
