from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
import argparse,json,pickle,random,resource,statistics,time,itertools

OBJECTS=["青い箱","赤い箱","小型端末","大型端末","試料甲","試料乙"]
ALIASES={"青い箱":"青色ケース","赤い箱":"赤色ケース","小型端末":"小さい端末","大型端末":"大きい端末","試料甲":"サンプル甲","試料乙":"サンプル乙"}
REL=["場所","状態","担当"]
VAL={"場所":["棚A","棚B","棚C","棚D"],"状態":["待機","処理中","完了","保留"],"担当":["担当一","担当二","担当三","担当四"]}

@dataclass
class Episode:
    state:str; query:str; answer:str; obj:str; rel:str; session:int
@dataclass
class Binding:
    obj:str; rel:str; value:str; support:int=0; wrong:int=0; sessions:tuple=(); credit:float=0.0; slow:bool=False

def build(seed,n,mode):
    r=random.Random(seed); rows=[]; session=0
    for i in range(n):
        if i and i%6==0: session+=1
        o=r.choice(OBJECTS); surf=ALIASES[o] if mode=="rename" else o
        rel=r.choice(REL); value=r.choice(VAL[rel])
        if mode=="alternate":
            state=f"{surf}：{rel}={value}／補助=維持。"; query=f"{surf}について{rel}を答えてください。"
        elif mode=="omitted":
            state=f"{surf}の{rel}は{value}です。補助記録は維持します。"; query=f"その対象の{rel}は何ですか？"
        elif mode=="paragraph":
            state=f"別件の説明です。記録を確認します。\n{surf}の{rel}は{value}です。\n補助記録は維持します。"; query=f"前の説明を踏まえて、{surf}の{rel}は何ですか？"
        else:
            state=f"{surf}の{rel}は{value}です。補助記録は維持します。"; query=f"{surf}の{rel}は何ですか？"
        rows.append(Episode(state,query,value,surf,rel,session))
    return rows

class Memory:
    def __init__(self,mode):
        self.mode=mode; self.bindings=[]; self.coalitions=[]; self.train_seconds=0
    def fit(self,rows):
        t=time.perf_counter(); d={}
        for e in rows:
            compact=e.state.replace("\n",""); seen=set()
            for i in range(len(compact)):
                for width in range(1,7):
                    v=compact[i:i+width]
                    if len(v)!=width or v in seen or any(c in "。、／=：\n " for c in v): continue
                    seen.add(v)
                    if v in e.query or v in "補助記録維持しますです現在値": continue
                    left=compact[max(0,i-10):i]; key=(left[-8:],v)
                    if key not in d:d[key]=Binding(left[-8:],e.query[:10],v)
                    b=d[key]; b.support+=1; b.sessions=tuple(sorted(set(b.sessions+(e.session,))))
        self.bindings=sorted(d.values(),key=lambda b:b.support,reverse=True)[:24]
        base=[self._predict(e,set())[0] for e in rows]
        base_correct=sum(p==e.answer for p,e in zip(base,rows))
        k=min(6,len(self.bindings)); subsets=[(i,) for i in range(k)]+list(itertools.combinations(range(k),2)); marg=defaultdict(list)
        for sub in subsets:
            pred=[self._predict(e,set(sub))[0] for e in rows]
            correct=sum(p==e.answer for p,e in zip(pred,rows))
            delta=(base_correct-correct)/max(1,len(rows))
            wrong_delta=(sum(p is not None and p!=e.answer for p,e in zip(base,rows))-sum(p is not None and p!=e.answer for p,e in zip(pred,rows)))/max(1,len(rows))
            self.coalitions.append((sub,delta,wrong_delta))
            for i in sub:marg[i].append(delta-wrong_delta)
        for i,b in enumerate(self.bindings):
            if i in marg:b.credit=statistics.mean(marg[i])
        if self.mode=="shapley":
            for b in self.bindings:b.slow=b.credit>0.005 and len(b.sessions)>=2
        elif self.mode=="loo":
            for i,b in enumerate(self.bindings):
                singleton=next((x for x in self.coalitions if x[0]==(i,)),None)
                b.slow=bool(singleton and singleton[1]>0.005 and singleton[2]<=0 and len(b.sessions)>=2)
        self.train_seconds=time.perf_counter()-t
    def _score(self,e,b): return (2.0 if b.obj in e.state else 0)+(1.2 if b.rel in e.query else 0)+0.05*b.support+0.5*b.credit
    def _predict(self,e,removed):
        cand=[]
        for i,b in enumerate(self.bindings):
            if i in removed or b.value not in e.state: continue
            if self.mode in ("loo","shapley") and not b.slow: continue
            cand.append((self._score(e,b),b.value))
        if not cand:return None,0
        cand.sort(reverse=True)
        if len(cand)>1 and abs(cand[0][0]-cand[1][0])<0.02:return None,len(cand)
        return cand[0][1],len(cand)
    def predict(self,e): return self._predict(e,set())

def evaluate(seed,n,mode):
    train=[]
    for j,m in enumerate(("seen","rename","alternate","paragraph")): train += build(seed+31*j,n//4,m)
    test=build(seed+999,max(18,n//4),mode); out={}
    for method in ("support","loo","shapley"):
        M=Memory(method);M.fit(train);t=time.perf_counter();cor=wrong=null=active=0
        for e in test:
            p,a=M.predict(e);active+=a;cor+=p==e.answer;wrong+=p is not None and p!=e.answer;null+=p is None
        out[method]={"read_accuracy":cor/len(test),"wrong_read":wrong/len(test),"null_rate":null/len(test),"bindings":len(M.bindings),"slow_bindings":sum(b.slow for b in M.bindings),"coalitions":len(M.coalitions),"mean_credit":statistics.mean([b.credit for b in M.bindings]) if M.bindings else 0,"model_bytes":len(pickle.dumps(M)),"training_seconds":M.train_seconds,"inference_ms":(time.perf_counter()-t)*1000/len(test),"mean_active":active/len(test)}
    return out

def one_shot(seed):
    e=build(seed,1,"seen")[0];out={}
    for m in ("support","loo","shapley"):
        M=Memory(m);M.fit([e]);out[m]=int(M.predict(e)[0]==e.answer)
    return out

def interference(seed):
    base=build(seed,24,"seen");noise=build(seed+1,72,"paragraph");probe=base[-12:];out={}
    for m in ("support","loo","shapley"):
        M=Memory(m);M.fit(base+noise);out[m]=sum(M.predict(e)[0]==e.answer for e in probe)/len(probe)
    return out

def forgetting(seed):
    first=build(seed,24,"seen");second=build(seed+11,24,"seen");probe=second[-12:];out={}
    for m in ("support","loo","shapley"):
        M=Memory(m);M.fit(first+second);out[m]=sum(M.predict(e)[0]==e.answer for e in probe)/len(probe)
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="results_cycle_027.json");a=ap.parse_args()
    modes=["seen","rename","alternate","omitted","paragraph","domain"];raw={}
    for n in (24,48,96):
        runs=[]
        for seed in (1,7,19):
            r={m:evaluate(seed,n,"seen" if m=="domain" else m) for m in modes};r["one_shot"]=one_shot(seed);r["interference"]=interference(seed);r["forgetting"]=forgetting(seed);runs.append(r)
        raw[str(n)]=runs
    summary={}
    for n,runs in raw.items():
        summary[n]={}
        for mode in modes:
            summary[n][mode]={}
            for method in ("support","loo","shapley"):
                summary[n][mode][method]={k:statistics.mean(r[mode][method][k] for r in runs) for k in runs[0][mode][method]}
        for extra in ("one_shot","interference","forgetting"):
            summary[n][extra]={m:statistics.mean(r[extra][m] for r in runs) for m in ("support","loo","shapley")}
    payload={"cycle":27,"hypothesis":"Shapley-Sparse Credit Sets with Redundancy-Aware Reconsolidation","seeds":[1,7,19],"sizes":[24,48,96],"raw":raw,"summary":summary,"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"estimated_complexity":"candidate O(NL^2), sparse coalitions O(k^2 N) with k<=6, inference O(BL)","hidden_labels_used_by_learner":False,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(a.output,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
if __name__=="__main__":main()
