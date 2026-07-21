"""Cycle A005: self-predicting reply-state programs without outcome-value leakage.

Falsification probe. The model never receives the final target value in post-reply evidence.
It only receives generic accept/reject feedback. No pretrained model, morphology,
semantic slot labels, RAG, or external LLM.
"""
from __future__ import annotations
from collections import Counter, defaultdict
import argparse, json, math, pickle, random, resource, statistics, time

VALUES = ["棚A", "棚B", "棚C", "棚D", "箱一", "箱二", "部屋東", "部屋西", "机上", "廊下"]
DIRECT = ["{v}", "{v}です", "答えは{v}です"]
ORD = {0: ["前者です", "一つ目です", "最初の候補です"], 1: ["後者です", "二つ目です", "最後の候補です"]}
NEG = ["{a}ではない方", "{a}じゃないほう", "{a}以外です"]
CORR = ["やっぱり{v}", "訂正して{v}", "いや、{v}です"]
HELD = ["そちらで", "前に出た方", "後ろの候補", "{a}でない方にして", "考え直して{v}"]
ACCEPT = ["その理解で進めてください", "はい、それで合っています", "その解釈で大丈夫です"]
REJECT = ["違います。もう一方を検討してください", "その理解ではありません", "読み直してください"]
HELD_ACCEPT = ["そのまま進めて", "認識は合っています", "それでお願いします"]
HELD_REJECT = ["そうではありません", "選び直してください", "その認識は違います"]
UNINFORMATIVE = ["了解しました", "確認しました", "続けてください"]

def grams(text: str) -> Counter[str]:
    return Counter(text[i:i+n] for n in (2, 3) for i in range(max(0, len(text)-n+1)))

def cosine(a: Counter[str], b: Counter[str]) -> float:
    dot = sum(v*b.get(k, 0) for k, v in a.items())
    na = math.sqrt(sum(v*v for v in a.values()))
    nb = math.sqrt(sum(v*v for v in b.values()))
    return dot/(na*nb+1e-12)

def mask(text: str, values: tuple[str, ...]) -> str:
    out = text
    for i, v in sorted(enumerate(values), key=lambda x: -len(x[1])):
        out = out.replace(v, f"<V{i}>")
    return out

def make_episode(rng: random.Random, kind: str, arity: int = 2) -> dict:
    values = tuple(rng.sample(VALUES, arity)); rank = rng.randrange(arity); target = values[rank]
    question = "確認です。候補は" + "、".join(f"「{v}」" for v in values) + "のどれですか？"
    if kind == "direct": reply = rng.choice(DIRECT).format(v=target)
    elif kind == "ordinal" and arity == 2: reply = rng.choice(ORD[rank])
    elif kind == "neg" and arity == 2: reply = rng.choice(NEG).format(a=values[1-rank])
    elif kind == "corr": reply = rng.choice(CORR).format(v=target)
    else:
        form = rng.choice(HELD)
        if "{v}" in form: reply = form.format(v=target, a=values[(rank+1) % arity])
        elif "{a}" in form: reply = form.format(a=values[(rank+1) % arity], v=target)
        elif "前" in form: rank, target, reply = 0, values[0], form
        elif "後ろ" in form or "そちら" in form: rank, target, reply = arity-1, values[-1], form
        else: reply = form
    return {"values": values, "rank": rank, "target": target, "question": question, "reply": reply}

class ReplyStatePrograms:
    def __init__(self):
        self.reply_patterns: dict[str, Counter[int]] = defaultdict(Counter)
        self.feedback_patterns: dict[str, Counter[str]] = defaultdict(Counter)

    def fit(self, rows, rng):
        for row in rows:
            self.reply_patterns[mask(row["reply"], row["values"])][row["rank"]] += 1
            for accepted, forms in ((True, ACCEPT), (False, REJECT)):
                f = rng.choice(forms)
                self.feedback_patterns[f]["accept" if accepted else "reject"] += 1
        return self

    def rank_candidates(self, row, limit=5):
        query = grams(mask(row["reply"], row["values"])); scored = []
        for pattern, counts in self.reply_patterns.items():
            sim = cosine(query, grams(pattern)); total = sum(counts.values())
            for rank, count in counts.items():
                if rank < len(row["values"]): scored.append((sim*count/total, rank))
        for rank, value in enumerate(row["values"]):
            if value in row["reply"]: scored.append((1.2, rank))
        best = {}
        for score, rank in scored: best[rank] = max(best.get(rank, -1.0), score)
        return sorted(((s, r) for r, s in best.items()), reverse=True)[:limit]

    def feedback_act(self, feedback: str):
        candidates = []
        for pattern, counts in self.feedback_patterns.items():
            sim = cosine(grams(feedback), grams(pattern)); total = sum(counts.values())
            for act, count in counts.items(): candidates.append((sim*count/total, act))
        if not candidates: return None
        candidates.sort(reverse=True); top = candidates[0]; second = candidates[1] if len(candidates)>1 else (0.0, None)
        if top[0] < 0.12 or top[0]-second[0] < 0.015: return None
        return top[1]

    def immediate(self, row):
        ranked = self.rank_candidates(row)
        return ranked[0][1] if ranked else None

    def revise(self, row, feedback):
        ranked = self.rank_candidates(row)
        if not ranked: return None
        proposed = ranked[0][1]; act = self.feedback_act(feedback)
        if act == "accept": return proposed
        if act == "reject":
            alternatives = [r for _, r in ranked if r != proposed]
            return alternatives[0] if len(row["values"]) == 2 and alternatives else None
        return None

def evaluate(seed: int, train_size: int) -> dict:
    rng = random.Random(seed)
    train = [make_episode(rng, rng.choice(("direct", "ordinal", "neg", "corr")), 2) for _ in range(train_size)]
    model = ReplyStatePrograms().fit(train, rng)
    splits = {k: [make_episode(rng, k, 2) for _ in range(160)] for k in ("direct", "ordinal", "neg", "corr", "held")}
    splits["three_way"] = [make_episode(rng, "held", 3) for _ in range(160)]
    out = {}
    for split, rows in splits.items():
        immediate=[]; revised_known=[]; revised_held=[]; uninformative=[]; start=time.perf_counter()
        for row in rows:
            p=model.immediate(row); immediate.append(p); correct=p==row["rank"]
            revised_known.append(model.revise(row, rng.choice(ACCEPT if correct else REJECT)))
            revised_held.append(model.revise(row, rng.choice(HELD_ACCEPT if correct else HELD_REJECT)))
            uninformative.append(model.revise(row, rng.choice(UNINFORMATIVE)))
        out[split]={
            "immediate": sum(p==r["rank"] for p,r in zip(immediate,rows))/len(rows),
            "revised_known_feedback": sum(p==r["rank"] for p,r in zip(revised_known,rows))/len(rows),
            "revised_held_feedback": sum(p==r["rank"] for p,r in zip(revised_held,rows))/len(rows),
            "uninformative_abstention": sum(p is None for p in uninformative)/len(rows),
            "ms_per_query_all_modes": (time.perf_counter()-start)*1000/len(rows),
        }
    out["model_bytes"]=len(pickle.dumps(model)); out["reply_pattern_count"]=len(model.reply_patterns)
    out["feedback_pattern_count"]=len(model.feedback_patterns); out["candidate_reads"]=min(5,max(1,len(model.reply_patterns)))
    return out

def summarize(raw):
    summary={}
    for n,runs in raw.items():
        summary[n]={}
        for split in ("direct","ordinal","neg","corr","held","three_way"):
            summary[n][split]={}
            for metric in ("immediate","revised_known_feedback","revised_held_feedback","uninformative_abstention","ms_per_query_all_modes"):
                summary[n][split][metric]=statistics.mean(r[split][metric] for r in runs)
        for metric in ("model_bytes","reply_pattern_count","feedback_pattern_count","candidate_reads"):
            summary[n][metric]=statistics.mean(r[metric] for r in runs)
    return summary

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--output",default="results_cycle_005.json"); args=parser.parse_args()
    raw={str(n):[evaluate(s,n) for s in (1,7,19)] for n in (32,128,512)}
    payload={"hypothesis":"Self-Predicting Reply-State Programs without Outcome Leakage","seeds":[1,7,19],"train_sizes":[32,128,512],"raw":raw,"summary":summarize(raw),"evidence_contains_target_value":False,"peak_rss_kib_runtime_included":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"free_japanese_integrated_gate":0.0,"highschool_level_passed":False,"native_japanese_communication_passed":False,"weak_smartphone_verified":False,"completion":False}
    with open(args.output,"w",encoding="utf-8") as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(json.dumps(payload["summary"],ensure_ascii=False,indent=2))

if __name__ == "__main__": main()
