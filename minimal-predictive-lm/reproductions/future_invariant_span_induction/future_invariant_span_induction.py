from __future__ import annotations
import argparse, collections, json, math, random, resource, time
from dataclasses import dataclass, asdict
from pathlib import Path

REAL_UTTERANCES = [
"よろしくお願いいたします。","よろしくお願いします！","今日は涼しいですね","雨が降って、何か涼しくなりましたね。",
"そうですね、明日も涼しいと聞きました","そうなんですか！でも、ちょっと湿度が高い気がします。",
"確かに、雨の名残でしょうか","今日の天気はどうでしたか？","私のところは曇りでした",
"そうなんですね！関東地方とかですか？","そうです！都内にいます","関東は曇りなんですね。こちらは関西です。",
"関西良いですね！お天気はどうでしょうか？","午前中は、雷が鳴って、土砂降りでした。",
"えっ、それは。明日関東も雨かもしれませんね","行きますね、その雨雲が。","プレゼントみたいですね",
"嫌なプレゼントだー！今はカンカン照りです。","えっ、そしたら月曜日晴れちゃいますね",
"もう暑いのは勘弁です。夏バテしてませんか？","してます、してます。もうぐったりです",
"食欲はどうですか？","食欲もそんなにわかず。","そういう時は、何か食べますか？私は麺類が多めになります。",
"分かります、後はグラノーラ食べますね","健康的ですね！グラノーラの存在すっかり忘れてました。",
"グラノーラ地味に大切な存在です。","栄養素たっぷりですもんね！私も、買っておこうかな。",
"おすすめします！パットしたときに食べられるので、ぜひ","ナイスな情報ありがとうございます！ではまた。"
]
NAMES=["葵","蓮","凛","空","海","森","結衣","陽斗"]
PLACES=["東京","大阪","京都","札幌","福岡","仙台","長野","神戸"]
FOODS=["うどん","そば","カレー","寿司","パン","ラーメン","りんご","餃子"]
GOALS=["旅行したい","試験に受かりたい","早起きしたい","料理を覚えたい","走れるようになりたい","本を読みたい"]

def make_dialogues(seed:int,n:int):
    rng=random.Random(seed); pairs=[]; gold=[]
    templates=[("私は{X}に住んでいます。","{X}はどんなところですか？"),("最近は{X}をよく食べます。","{X}がお好きなんですね。"),("友達の{X}さんと話しました。","{X}さんとは長い付き合いですか？"),("目標は{X}です。","{X}なら最初の一歩は何ですか？")]
    pools=[PLACES,FOODS,NAMES,GOALS]
    for _ in range(n):
        k=rng.randrange(4); a,b=templates[k]; val=rng.choice(pools[k]); u=a.format(X=val); v=b.format(X=val)
        pairs.append((u,v)); gold.append((u.index(val),u.index(val)+len(val),val,k))
    return pairs,gold

def trigrams(s): return {s} if len(s)<3 else {s[i:i+3] for i in range(len(s)-2)}
def jaccard(a,b): return len(a&b)/max(1,len(a|b))

@dataclass
class Metrics:
    method:str; seed:int; examples:int; span_f1:float; unseen_rename_f1:float; future_retrieval:float; decoy_rejection:float; unified_gate:float; model_bytes:int; peak_rss_kib:int; train_seconds:float; inference_ms:float; candidates:int; reads:int; induced_frames:int

class Inducer:
    def __init__(self,method="future_invariant",max_len=8): self.method=method; self.max_len=max_len; self.scores={}; self.frames={}
    def fit(self,pairs):
        t=time.perf_counter(); occ=collections.defaultdict(list)
        for idx,(u,v) in enumerate(pairs):
            for i in range(len(u)):
                for L in range(1,min(self.max_len,len(u)-i)+1):
                    s=u[i:i+L]
                    if s.strip("。、！？ ")=="": continue
                    occ[s].append((u[max(0,i-2):i],u[i+L:i+L+2],trigrams(v),idx))
        for s,rows in occ.items():
            if len(rows)<2: continue
            contexts={(a,b) for a,b,_,_ in rows}
            if len(contexts)<2: continue
            futures=[f for _,_,f,_ in rows]
            coh=sum(jaccard(futures[i],futures[j]) for i in range(len(futures)) for j in range(i))/max(1,len(futures)*(len(futures)-1)/2)
            score=math.log1p(len(contexts))/math.sqrt(len(s))
            if self.method=="future_invariant": score*=0.25+coh
            self.scores[s]=score
        top=set(sorted(self.scores,key=self.scores.get,reverse=True)[:256])
        for u,_ in pairs:
            for s in top:
                if s in u: self.frames.setdefault(u.replace(s,"<V>",1),set()).add(s)
        self.train_seconds=time.perf_counter()-t; return self
    def predict_span(self,u):
        hits=[]
        for s,score in self.scores.items():
            start=u.find(s)
            if start>=0: hits.append((score,start,start+len(s),s))
        return max(hits) if hits else None
    def retrieve(self,u,candidates):
        pred=self.predict_span(u)
        if pred is None: return 0
        _,a,b,_=pred; frame=u[:a]+"<V>"+u[b:]; best=(-1,0)
        for i,(cu,_) in enumerate(candidates):
            cp=self.predict_span(cu)
            sim=0 if cp is None else jaccard(trigrams(frame),trigrams(cu[:cp[1]]+"<V>"+cu[cp[2]:]))
            if sim>best[0]: best=(sim,i)
        return best[1]
    def size_bytes(self): return len(json.dumps({"s":self.scores,"f":{k:list(v) for k,v in self.frames.items()}},ensure_ascii=False).encode())

def overlap_f1(pred,g):
    if pred is None:return 0.0
    _,a,b,_=pred; ga,gb,_,_=g; inter=max(0,min(b,gb)-max(a,ga))
    if not inter:return 0.0
    p=inter/(b-a); r=inter/(gb-ga); return 2*p*r/(p+r)

def one_run(method,seed,examples):
    train,_=make_dialogues(seed,examples); raw=list(zip(REAL_UTTERANCES[:-1],REAL_UTTERANCES[1:])); model=Inducer(method).fit(train+raw)
    test,tgold=make_dialogues(seed+1000,128); f1=sum(overlap_f1(model.predict_span(u),g) for (u,_),g in zip(test,tgold))/128
    rename=[(u.replace(g[2],"未知語"+str(i)),v.replace(g[2],"未知語"+str(i))) for i,((u,v),g) in enumerate(zip(test,tgold))]
    rgold=[]
    for i,(u,_) in enumerate(rename):
        val="未知語"+str(i); rgold.append((u.index(val),u.index(val)+len(val),val,0))
    rf1=sum(overlap_f1(model.predict_span(u),g) for (u,_),g in zip(rename,rgold))/128
    rng=random.Random(seed+9); correct=0; started=time.perf_counter(); reads=0
    for i,(u,v) in enumerate(test):
        neg=[test[j] for j in rng.sample([x for x in range(128) if x!=i],3)]; cand=[(u,v)]+neg; rng.shuffle(cand); target=[x[1] for x in cand].index(v)
        correct+=model.retrieve(u,cand)==target; reads+=len(model.scores)*4
    infer=(time.perf_counter()-started)*1000/128
    dec=0
    for (u,_),g in zip(test,tgold):
        wrong=u[:g[0]]+"しかし"+u[g[1]:]; p=model.predict_span(wrong); dec+=int(p is None or p[3]!="しかし")
    return Metrics(method,seed,examples,f1,rf1,correct/128,dec/128,0.0,model.size_bytes(),resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,model.train_seconds,infer,len(model.scores),reads//128,len(model.frames))

def run(out):
    rows=[one_run(m,s,n) for n in (32,128,512) for s in (1,7,19) for m in ("context_only","future_invariant")]; agg={}
    for m in ("context_only","future_invariant"):
        agg[m]={}
        for n in (32,128,512):
            rr=[r for r in rows if r.method==m and r.examples==n]
            agg[m][str(n)]={k:sum(getattr(x,k) for x in rr)/len(rr) for k in ("span_f1","unseen_rename_f1","future_retrieval","decoy_rejection","unified_gate","model_bytes","peak_rss_kib","train_seconds","inference_ms","candidates","reads","induced_frames")}
    report={"hypothesis":"A span is a variable candidate when its surface varies while its surrounding frame and future-dialogue prediction remain stable.","aggregate":agg,"runs":[asdict(r) for r in rows],"claim":{"completion":False,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False}}
    Path(out).parent.mkdir(parents=True,exist_ok=True); Path(out).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8"); return report

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--output",default="artifacts/report.json"); a=p.parse_args(); print(json.dumps(run(a.output)["aggregate"],ensure_ascii=False,indent=2))
