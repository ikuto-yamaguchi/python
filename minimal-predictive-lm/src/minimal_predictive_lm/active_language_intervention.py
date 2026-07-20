from __future__ import annotations
import json, random, time, resource, statistics
from dataclasses import dataclass
from collections import defaultdict

@dataclass(frozen=True)
class Episode:
    world: str
    utterance: str
    partition: tuple[tuple[int,...],...]

class PartitionSemanticInducer:
    def __init__(self):
        self.signature_to_forms=defaultdict(list)
        self.form_signatures={}
        self.reads=0
    def fit(self, episodes):
        for e in episodes:
            sig=tuple(sorted(tuple(sorted(g)) for g in e.partition))
            self.signature_to_forms[sig].append(e.utterance)
            self.form_signatures[e.utterance]=sig
    def infer_signature(self, utterance):
        self.reads += len(self.form_signatures)
        return self.form_signatures.get(utterance)
    def bytes(self):
        return len(json.dumps({"forms":self.form_signatures,"classes":{str(k):v for k,v in self.signature_to_forms.items()}},ensure_ascii=False,separators=(",",":")).encode())

BASE={
"color":[("色は何色ですか",((0,),(1,),(2,))),("色を教えて",((0,),(1,),(2,))),("何色なの",((0,),(1,),(2,)))],
"place":[("どこにありますか",((0,),(1,),(2,))),("場所を教えて",((0,),(1,),(2,))),("どこなの",((0,),(1,),(2,)))],
"owner":[("誰のものですか",((0,),(1,),(2,))),("持ち主を教えて",((0,),(1,),(2,))),("誰のなの",((0,),(1,),(2,)))],
"binary":[("動きますか",((0,1),(2,))),("作動する",((0,1),(2,))),("動くの",((0,1),(2,)))]}
UNSEEN={"color":["どんな色合いですか","色彩は"],"place":["所在地はどちらですか","位置を知りたい"],"owner":["所有者はどなたですか","誰が所有していますか"],"binary":["稼働しますか","機能しているのでしょうか"]}

def make_train(per_class,seed):
    rng=random.Random(seed); out=[]
    for rows in BASE.values():
        for i in range(per_class):
            u,p=rows[i%len(rows)]; out.append(Episode(f"w{i%5}",u,p))
    rng.shuffle(out); return out

def evaluate(model):
    seen=total=0
    for rows in BASE.values():
        for u,p in rows:
            total+=1; target=tuple(sorted(tuple(sorted(g)) for g in p)); seen += model.infer_signature(u)==target
    unseen=ut=0
    for cls,forms in UNSEEN.items():
        target=tuple(sorted(tuple(sorted(g)) for g in BASE[cls][0][1]))
        for u in forms:
            ut+=1; unseen += model.infer_signature(u)==target
    return seen/total,unseen/ut

def integrated_gate():
    prompts={"自由対話":"今日は仕事で失敗して落ち込んでる。話を聞いて。","指示遂行":"次の三語を逆順に並べて。猫、空、海","読解":"太郎は花子に本を渡した。受け取ったのは誰？","推論":"AはBより高く、BはCより高い。最も高いのは？","計画":"午前中に郵便局と病院へ行き、病院は11時予約。順番を決めて。","因果反実仮想":"雨が降らなかったら地面はどうなっていた？","自由記述":"春の朝を二文で描写して。","長期対話":"最初に言った旅行相手を覚えている？","継続学習":"この会話では『ルナ』を青い鍵の意味として覚えて。ルナは何？"}
    return {k:{"input":v,"output":"意味介入を構成できません。","pass":False} for k,v in prompts.items()}

def run():
    scales=[1,2,4,16,64]; seeds=[1,7,19,31,43]; rows=[]; start=time.perf_counter()
    for n in scales:
      for seed in seeds:
        train=make_train(n,seed); m=PartitionSemanticInducer(); t=time.perf_counter(); m.fit(train); fit_ms=(time.perf_counter()-t)*1000
        m.reads=0; t=time.perf_counter(); seen,unseen=evaluate(m); infer_ms=(time.perf_counter()-t)*1000/20; reads=m.reads/20
        decoys=[Episode("d","今日の天気は",BASE["color"][0][1]),Episode("d","好きな食べ物は",BASE["place"][0][1])]
        dm=PartitionSemanticInducer(); dm.fit(train+decoys); decoy_accept=sum(dm.infer_signature(e.utterance) is not None for e in decoys)/2
        rows.append({"scale":n,"seed":seed,"train_episodes":len(train),"seen_accuracy":seen,"unseen_paraphrase_accuracy":unseen,"decoy_acceptance":decoy_accept,"model_bytes":m.bytes(),"fit_ms":fit_ms,"mean_infer_ms":infer_ms,"mean_reads":reads,"candidate_classes":len(m.signature_to_forms)})
    return {"experiment":"active-language-intervention-signature-001","rows":rows,"summary":{"seen_mean":statistics.mean(r["seen_accuracy"] for r in rows),"unseen_mean":statistics.mean(r["unseen_paraphrase_accuracy"] for r in rows),"decoy_mean":statistics.mean(r["decoy_acceptance"] for r in rows),"max_model_bytes":max(r["model_bytes"] for r in rows),"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"max_fit_ms":max(r["fit_ms"] for r in rows),"mean_infer_ms":statistics.mean(r["mean_infer_ms"] for r in rows),"max_reads":max(r["mean_reads"] for r in rows),"max_candidate_classes":max(r["candidate_classes"] for r in rows),"wall_seconds":time.perf_counter()-start},"integrated_gate":integrated_gate(),"integrated_gate_score":0.0,"highschool_level_passed":False,"native_japanese_communication_passed":False,"completion":False,"verdict":"REJECTED: partition signatures identify seen interventions but neither ground unseen Japanese nor reject semantically unrelated decoys sharing an imposed effect."}

if __name__=="__main__": print(json.dumps(run(),ensure_ascii=False,indent=2))
