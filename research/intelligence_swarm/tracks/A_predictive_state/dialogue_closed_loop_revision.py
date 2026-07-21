"""Cycle A004: dialogue-closed predictive state revision.

No pretrained model, morphology, semantic slot name, external LLM, RAG or answer label is used.
Reply programs are induced from question/reply/later-observation triples.  This is a
small falsification probe, not a Japanese intelligence model.
"""
from __future__ import annotations
from collections import Counter
import argparse, json, math, pickle, random, resource, statistics, time

VALUES = ["棚A", "棚B", "棚C", "棚D", "箱一", "箱二", "部屋東", "部屋西"]
DIRECT = ["{v}", "{v}です", "答えは{v}です"]
NEG = ["{a}ではない方", "{a}じゃないほう", "{a}以外です"]
CORR = ["やっぱり{v}", "訂正して{v}", "いや、{v}です"]
HELD = ["そちらです", "二番目の候補です", "前の方です", "{a}でない方にしてください", "考え直して{v}"]


def grams(text: str) -> Counter[str]:
    return Counter(text[i:i+n] for n in (2, 3) for i in range(max(0, len(text)-n+1)))


def cosine(a: Counter[str], b: Counter[str]) -> float:
    dot = sum(v*b.get(k, 0) for k, v in a.items())
    na = math.sqrt(sum(v*v for v in a.values()))
    nb = math.sqrt(sum(v*v for v in b.values()))
    return dot/(na*nb+1e-12)


def episode(rng: random.Random, kind: str) -> dict:
    a, b = rng.sample(VALUES, 2)
    target = rng.choice((a, b))
    question = f"確認です。候補は「{a}」と「{b}」のどちらですか？"
    if kind == "direct":
        reply = rng.choice(DIRECT).format(v=target)
    elif kind == "ordinal":
        reply = rng.choice(("前者です", "一つ目です") if target == a else ("後者です", "二つ目です"))
    elif kind == "neg":
        reply = rng.choice(NEG).format(a=b if target == a else a)
    elif kind == "corr":
        reply = rng.choice(CORR).format(v=target)
    else:
        form = rng.choice(HELD)
        if "そちら" in form or "二番目" in form:
            target, reply = b, form
        elif "前の方" in form:
            target, reply = a, form
        elif "でない方" in form:
            reply = form.format(a=b if target == a else a, v=target)
        else:
            reply = form.format(v=target, a=b if target == a else a)
    return {"a": a, "b": b, "target": target, "question": question, "reply": reply,
            "observation": f"最終的な状態は「{target}」になりました。"}


class LiteralEcho:
    def fit(self, rows): return self
    def predict(self, row):
        hits = [v for v in (row["a"], row["b"]) if v in row["reply"]]
        return hits[-1] if len(hits) == 1 else None


class InducedReplyPrograms:
    def __init__(self, delayed_revision: bool):
        self.delayed_revision = delayed_revision
        self.prototypes = []

    def fit(self, rows):
        for row in rows:
            program = ("rank", 0 if row["target"] == row["a"] else 1)
            masked = row["reply"].replace(row["a"], "<A>").replace(row["b"], "<B>")
            self.prototypes.append((grams(masked), program))
        return self

    def candidates(self, row, limit=5):
        masked = row["reply"].replace(row["a"], "<A>").replace(row["b"], "<B>")
        scored = sorted(((cosine(grams(masked), f), p) for f, p in self.prototypes), reverse=True)[:limit]
        out = {}
        for score, (_, rank) in scored:
            value = (row["a"], row["b"])[rank]
            out[value] = max(out.get(value, -1.0), score)
        for value in (row["a"], row["b"]):
            if value in row["reply"]:
                out[value] = 1.1
        return sorted(out.items(), key=lambda x: -x[1])

    def predict(self, row):
        candidates = self.candidates(row)
        if not candidates:
            return None
        if not self.delayed_revision:
            return candidates[0][0]
        # Same predictive-state loop revises candidate interpretations after a later observation.
        ranked = []
        for value, prior in candidates:
            future = f"最終的な状態は「{value}」になりました。"
            ranked.append((cosine(grams(future), grams(row["observation"])), prior, value))
        return max(ranked)[2]


def evaluate(seed: int, train_size: int) -> dict:
    rng = random.Random(seed)
    train = [episode(rng, rng.choice(("direct", "ordinal", "neg", "corr"))) for _ in range(train_size)]
    tests = {k: [episode(rng, k) for _ in range(120)] for k in ("direct", "ordinal", "neg", "corr", "held")}
    models = {"literal": LiteralEcho().fit(train),
              "reply_program": InducedReplyPrograms(False).fit(train),
              "closed_loop": InducedReplyPrograms(True).fit(train)}
    result = {}
    for name, model in models.items():
        result[name] = {}
        for split, rows in tests.items():
            start = time.perf_counter()
            pred = [model.predict(row) for row in rows]
            result[name][split] = sum(p == r["target"] for p, r in zip(pred, rows))/len(rows)
            result[name][split+"_ms"] = (time.perf_counter()-start)*1000/len(rows)
        result[name]["model_bytes"] = len(pickle.dumps(model))
        result[name]["candidate_reads"] = 5 if hasattr(model, "prototypes") else 2
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results_cycle_004.json")
    args = parser.parse_args()
    all_results = {str(n): [evaluate(s, n) for s in (1, 7, 19)] for n in (32, 128, 512)}
    payload = {"hypothesis": "Dialogue-Closed Predictive State Revision", "seeds": [1, 7, 19],
               "train_sizes": [32, 128, 512], "raw": all_results,
               "peak_rss_kib_runtime_included": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               "free_japanese_integrated_gate": 0.0,
               "highschool_level_passed": False, "completion": False}
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(json.dumps(payload, ensure_ascii=False))

if __name__ == "__main__":
    main()
