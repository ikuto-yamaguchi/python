from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import argparse,json,math,pickle,random,resource,statistics,time

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末","大型端末":"大きい端末","試料甲":"サンプル甲","試料乙":"サンプル乙"}
FIELDS=["場所","状態","担当"]
VALUES={"場所":["棚A","棚B","棚C","棚D"],"状態":["待機","処理中","完了","保留"],"担当":["担当一","担当二","担当三","担当四"]}
STATE0="{o}の場所は{loc}、状態は{status}、担当は{owner}です。補助記録は維持します。"
STATE1="{o}：保管={loc}／進行={status}／受持={owner}／補助=維持。"
CMDS={"場所":["{o}を{v}へ移してください。","{o}の保管先を{v}へ変更します。"],
"状態":["{o}を{v}にしてください。","{o}の進行状態を{v}へ切り替えます。"],
"担当":["{o}を{v}の担当にしてください。","{o}の受け持ちを{v}へ変更します。"]}
Q={"場所":["{o}はどこですか？","{o}の保管先は？"],"状態":["{o}の状態は？","{o}の進行状況は？"],"担当":["{o}の担当は誰ですか？","{o}の受持は？"]}

def grams(s):
    s=''.join(s.split())
    return Counter(s[i:i+n] for n in (1,2,3) for i in range(max(0,len(s)-n+1)))
def cos(a,b):
    d=sum(v*b.get(k,0) for k,v in a.items());na=math.sqrt(sum(v*v for v in a.values()));nb=math.sqrt(sum(v*v for v in b.values()))
    return d/(na*nb+1e-12)
def state(o,d,alt=False):
    f=STATE1 if alt else STATE0
    return f.format(o=o,loc=d["場所"],status=d["状態"],owner=d["担当"])
def diff(a,b):
    l=0
    while l<min(len(a),len(b)) and a[l]==b[l]:l+=1
    r=0
    while r<min(len(a)-l,len(b)-l) and a[-1-r]==b[-1-r]:r+=1
    return l,r,a[l:len(a)-r if r else len(a)],b[l:len(b)-r if r else len(b)]

@dataclass
class Episode:
    before:str; command:str; after:str; query:str; answer:str; session:int; mode:str
@dataclass
class Endpoint:
    qctx:str; sleft:str; sright:str; value:str
    q_to_s:int=0; s_to_q:int=0; wrong:int=0; sessions:tuple=()
    stable:bool=False
@dataclass
class WriteTrace:
    cl:str; cr:str; sl:str; sr:str; support:int=1

class Memory:
    def __init__(self,mode):
        self.mode=mode;self.endpoints=[];self.write_traces=[];self.slow_links=[];self.train_seconds=0
    def fit(self,eps):
        t=time.perf_counter();ed={};td={}
        for e in eps:
            p=e.after.find(e.answer)
            if p>=0:
                ep=Endpoint(e.query,e.after[max(0,p-10):p],e.after[p+len(e.answer):p+len(e.answer)+10],e.answer)
                ed.setdefault((ep.qctx,ep.sleft,ep.sright,ep.value),ep)
            l,r,old,new=diff(e.before,e.after);c=e.command.find(new)
            if old and new and c>=0:
                wt=WriteTrace(e.command[max(0,c-8):c],e.command[c+len(new):c+len(new)+8],e.before[max(0,l-8):l],e.before[len(e.before)-r:len(e.before)-r+8] if r else '')
                k=(wt.cl,wt.cr,wt.sl,wt.sr)
                if k in td:td[k].support+=1
                else:td[k]=wt
        self.endpoints=list(ed.values())[:32];self.write_traces=sorted(td.values(),key=lambda x:x.support,reverse=True)[:32]
        for ep in self.endpoints:
            sessions=set()
            for e in eps:
                qsim=1.0 if ep.qctx==e.query else (0.6 if ep.qctx[:4] in e.query or e.query[:4] in ep.qctx else 0.0)
                ssim=1.0 if (ep.sleft in e.after and ep.value in e.after and ep.sright in e.after) else 0.0
                if qsim>.55:
                    if ep.value in e.after:ep.q_to_s+=1;sessions.add(e.session)
                    else:ep.wrong+=1
                if ssim>.55:
                    if qsim>.45:ep.s_to_q+=1
                    else:ep.wrong+=1
            ep.sessions=tuple(sorted(sessions));ep.stable=(ep.q_to_s>=2 and ep.s_to_q>=2 and ep.wrong==0 and len(ep.sessions)>=2)
        for i,ep in enumerate(self.endpoints):
            if not ep.stable:continue
            for j,wt in enumerate(self.write_traces):
                support=sum(ep.value in e.command and wt.cl in e.command and wt.sl in e.before for e in eps)
                if support>=2:self.slow_links.append((i,j,support))
        self.slow_links=sorted(self.slow_links,key=lambda x:x[2],reverse=True)[:64];self.train_seconds=time.perf_counter()-t
    def read(self,e):
        cand=[]
        for i,ep in enumerate(self.endpoints):
            if self.mode in ("bidir","slow") and not ep.stable:continue
            if ep.value not in e.after:continue
            score=(1.0 if ep.qctx==e.query else 0.6 if ep.qctx[:4] in e.query or e.query[:4] in ep.qctx else 0.0)+(1.0 if ep.sleft in e.after and ep.value in e.after and ep.sright in e.after else 0.0)-.4*ep.wrong
            if self.mode=="slow" and any(a==i for a,_,_ in self.slow_links):score+=.5
            cand.append((score,ep.value))
        if not cand:return None
        cand.sort(reverse=True)
        if len(cand)>1 and cand[0][0]-cand[1][0]<.03:return None
        return cand[0][1]

def build(seed,n,mode):
    rng=random.Random(seed);world={};out=[];session=0
    for i in range(n):
        if i and i%6==0:session+=1
        canon=rng.choice(OBJECTS);surf=ALIASES[canon] if mode=="rename" else canon
        world.setdefault(canon,{f:rng.choice(VALUES[f]) for f in FIELDS})
        f=rng.choice(FIELDS);new=rng.choice([x for x in VALUES[f] if x!=world[canon][f]])
        alt=mode=="alternate";before=state(surf,world[canon],alt);command=rng.choice(CMDS[f]).format(o=surf,v=new)
        if mode=="paragraph":command="別件の説明があります。\n"+command+"\n補助記録は維持してください。"
        world[canon][f]=new;after=state(surf,world[canon],alt);query=rng.choice(Q[f]).format(o=surf)
        if mode=="held":query=query.replace("は？","を教えてください。")
        out.append(Episode(before,command,after,query,new,session,mode))
    return out

def evaluate(seed,n,mode):
    train=[]
    for j,m in enumerate(("seen","held","rename","alternate")):train+=build(seed+17*j,n//4,m)
    test=build(seed+999,max(24,n//4),mode);res={}
    for method in ("raw","bidir","slow"):
        M=Memory(method);M.fit(train);t=time.perf_counter();correct=wrong=0
        for e in test:
            got=M.read(e);correct+=int(got==e.answer);wrong+=int(got is not None and got!=e.answer)
        res[method]={"read_accuracy":correct/len(test),"wrong_read":wrong/len(test),"endpoints":len(M.endpoints),"stable_endpoints":sum(e.stable for e in M.endpoints),"slow_links":len(M.slow_links),"model_bytes":len(pickle.dumps(M)),"training_seconds":M.train_seconds,"inference_ms":(time.perf_counter()-t)*1000/len(test)}
    return res

def interference(seed):
    base=build(seed,24,"seen");noise=build(seed+1,96,"paragraph");probe=base[-12:];out={}
    for method in ("raw","bidir","slow"):
        M=Memory(method);M.fit(base+noise);out[method]=sum(M.read(e)==e.answer for e in probe)/len(probe)
    return out

def one_shot(seed):
    e=build(seed,1,"seen")[0];out={}
    for method in ("raw","bidir","slow"):
        M=Memory(method);M.fit([e]);out[method]=int(M.read(e)==e.answer)
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="results_cycle_024.json");a=ap.parse_args();modes=("seen","held","rename","alternate","paragraph");raw={}
    for n in (24,48,72):
        runs=[]
        for seed in (1,7,19):
            r={m:evaluate(seed,n,m) for m in modes};r["interference"]=interference(seed);r["one_shot"]=one_shot(seed);runs.append(r)
        raw[str(n)]=runs
    summary={}
    for n,runs in raw.items():
        summary[n]={}
        for m in modes:
            summary[n][m]={}
            for method in ("raw","bidir","slow"):summary[n][m][method]={k:statistics.mean(r[m][method][k] for r in runs) for k in runs[0][m][method]}
        summary[n]["interference"]={m:statistics.mean(r["interference"][m] for r in runs) for m in ("raw","bidir","slow")};summary[n]["one_shot"]={m:statistics.mean(r["one_shot"][m] for r in runs) for m in ("raw","bidir","slow")}
    payload={"cycle":24,"hypothesis":"Endpoint Identity from Bidirectional Query–State Reconstruction before Slow Linking","seeds":[1,7,19],"sizes":[24,48,72],"raw":raw,"summary":summary,"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"estimated_complexity":"endpoint extraction O(NL), audit O(AN), slow linking O(AWN), read O(AL)","highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(a.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
if __name__=="__main__":main()
