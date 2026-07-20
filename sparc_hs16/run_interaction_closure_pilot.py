from __future__ import annotations

import json
import random
import resource
import statistics
import time
from pathlib import Path

from sparc_hs16.interaction_closure import PreferencePair, SparsePairwiseRanker, shuffled_context_pairs

BASE = [
    ("今日は仕事で失敗して落ち込んでいる", "それはつらかったね。何が一番苦しかった？", "富士山は日本で一番高い山です。"),
    ("明日の会議を延期する連絡文を作って", "体調不良のため、明日の会議を延期させてください。ご迷惑をおかけします。", "会議は重要です。"),
    ("太郎は花子より背が高い。花子は次郎より高い。一番高いのは？", "太郎です。", "次郎です。"),
    ("雨が降ったので試合が中止になった。原因は？", "雨が降ったことです。", "試合が中止になったことです。"),
    ("予算が半分になった。品質を守る計画を立てて", "必須機能を固定し、低優先機能を段階化して、各段階で品質基準を確認します。", "全部を同時に作ります。"),
    ("もし電車が遅れなかったら、遅刻した？", "他の遅延要因がなければ、遅刻しなかった可能性が高いです。", "必ず遅刻しました。"),
    ("この文を要約して。新製品は軽いが電池が短く、価格も高い", "軽量だが電池持ちと価格に課題がある製品です。", "新製品について説明しています。"),
    ("さっき妹と長野へ行くと言った。誰と行く？", "妹と行きます。", "彼女と行きます。"),
    ("赤い箱を机から棚へ移して、その後青い箱を机へ置いて", "赤い箱を棚へ移し、次に青い箱を机へ置きます。", "青い箱を棚へ置きます。"),
    ("猫が皿を割った。叱る前に何を確認する？", "けがの有無と、割れた経緯を確認します。", "すぐ大声で叱ります。"),
]


def make_data(n: int, seed: int) -> list[PreferencePair]:
    rng = random.Random(seed)
    prefixes = ("", "状況をよく読んで答えて。", "簡潔に答えて。", "理由も含めて。")
    suffixes = ("", "お願いします。", "どう思う？", "正確に。")
    out = []
    for i in range(n):
        q, good, bad = BASE[i % len(BASE)]
        out.append(PreferencePair((rng.choice(prefixes) + q + rng.choice(suffixes),), good, bad))
    rng.shuffle(out)
    return out


def timed_accuracy(model, pairs):
    start = time.perf_counter()
    value = model.accuracy(pairs)
    return value, (time.perf_counter() - start) * 1000 / max(1, len(pairs))


def main() -> None:
    rows = []
    for amount in (20, 50, 100, 200, 500):
        for seed in (1, 7, 19):
            train = make_data(amount, seed)
            test = make_data(200, seed + 1000)
            model = SparsePairwiseRanker(dimensions=16384, include_context=True)
            started = time.perf_counter()
            model.fit(train, epochs=4, seed=seed)
            train_ms = (time.perf_counter() - started) * 1000
            acc, infer_ms = timed_accuracy(model, test)
            shuffled_acc, _ = timed_accuracy(model, shuffled_context_pairs(test, seed))
            response_only = SparsePairwiseRanker(dimensions=16384, include_context=False)
            response_only.fit(train, epochs=4, seed=seed)
            response_only_acc, _ = timed_accuracy(response_only, test)
            rows.append({
                "amount": amount,
                "seed": seed,
                "accuracy": acc,
                "shuffled_context_accuracy": shuffled_acc,
                "response_only_accuracy": response_only_acc,
                "train_ms": train_ms,
                "inference_ms_per_pair": infer_ms,
                "model_bytes": model.serialized_bytes(),
                "nonzero_weights": len(model.weights),
                "feature_reads": model.feature_reads,
                "candidate_count": 2,
            })
    final = [r for r in rows if r["amount"] == 500]
    report = {
        "experiment": "interaction-closure sparse preference learner",
        "hypothesis": "prompt-response interaction features learned by local pairwise updates can transfer across Japanese communicative functions without topic branches",
        "rows": rows,
        "summary_500": {
            "accuracy_mean": statistics.mean(r["accuracy"] for r in final),
            "accuracy_min": min(r["accuracy"] for r in final),
            "shuffled_context_mean": statistics.mean(r["shuffled_context_accuracy"] for r in final),
            "response_only_mean": statistics.mean(r["response_only_accuracy"] for r in final),
            "model_bytes_max": max(r["model_bytes"] for r in final),
            "train_ms_mean": statistics.mean(r["train_ms"] for r in final),
            "inference_ms_per_pair_mean": statistics.mean(r["inference_ms_per_pair"] for r in final),
        },
        "peak_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "integrated_gate": {
            "free_dialogue_generation": False,
            "instruction_following_generation": False,
            "reading": "pairwise-only",
            "reasoning": "pairwise-only",
            "planning": "pairwise-only",
            "causal_counterfactual": "pairwise-only",
            "free_form_generation": False,
            "long_dialogue": "single-context-only",
            "continual_learning": True,
        },
        "highschool_level_passed": False,
        "native_japanese_communication_passed": False,
        "claim_boundary": "This is still a learned candidate ranker, not an intelligence model. Passing preference pairs cannot establish generation, understanding, or planning ability.",
    }
    Path("interaction_closure_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
