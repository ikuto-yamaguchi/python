from __future__ import annotations

import json
import random
import resource
import statistics
import time
from pathlib import Path

from minimal_predictive_lm.counterfactual_predicate_induction import (
    CounterfactualPredicateInducer,
    Episode,
)

SPECS = (
    ("color", ("色を教えて？", "何色ですか？", "色合いを確認したいです。"), ("表示色が確定", "塗装を選べる")),
    ("location", ("場所を教えて？", "どこにありますか？", "所在地を確認したいです。"), ("移動先が確定", "経路を選べる")),
    ("owner", ("持ち主を教えて？", "誰の物ですか？", "所有者を確認したいです。"), ("権限者が確定", "連絡先を選べる")),
    ("count", ("個数を教えて？", "いくつありますか？", "数量を確認したいです。"), ("必要数が確定", "配分を選べる")),
)
UNSEEN = {
    "color": "外観の色彩を知りたい。",
    "location": "配送先の位置情報が必要。",
    "owner": "責任者が不明です。",
    "count": "在庫の数量が分からない。",
}
DECOYS = ("今日の天気を知りたい。", "好きな食べ物を教えて。", "眠いです。", "音楽を聴きたい。")


def make_data(size: int, seed: int) -> list[Episode]:
    rng = random.Random(seed)
    objects = ("箱", "端末", "荷物", "部品", "資料")
    states = ("情報が足りない。", "判断に必要です。", "先へ進めません。")
    rows = []
    for _ in range(size):
        latent, questions, future = rng.choice(SPECS)
        rows.append(Episode((f"{rng.choice(objects)}について確認したい。", rng.choice(states)), latent, rng.choice(questions), future))
    return rows


def evaluate(size: int, seed: int) -> dict:
    model = CounterfactualPredicateInducer()
    started = time.perf_counter()
    model.fit(make_data(size, seed))
    fit_ms = (time.perf_counter() - started) * 1000
    correct = 0
    natural = 0
    latencies = []
    outputs = []
    for latent, text in UNSEEN.items():
        started = time.perf_counter()
        candidates = model.infer_candidates((text,))
        output = model.clarify(candidates)
        latencies.append((time.perf_counter() - started) * 1000)
        correct += int(model.latent_to_signature.get(latent) in candidates[:2])
        natural += int(output.endswith(("？", "?", "。")) and "、" not in output[:-1])
        outputs.append({"input": text, "output": output, "candidate_count": len(candidates)})
    decoy_reject = 0
    for text in DECOYS:
        decoy_reject += int(not model.infer_candidates((text,)))
    return {
        "size": size,
        "seed": seed,
        "correct_predicate_in_top2": correct / len(UNSEEN),
        "natural_clarification": natural / len(UNSEEN),
        "decoy_rejection": decoy_reject / len(DECOYS),
        "model_bytes": model.serialized_bytes(),
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "fit_ms": fit_ms,
        "mean_inference_ms": statistics.mean(latencies),
        "p95_inference_ms": max(latencies),
        "max_candidate_count": max(row["candidate_count"] for row in outputs),
        "feature_reads": model.reads,
        "outputs": outputs,
        "integrated_gate": {
            "free_dialogue": False,
            "instruction_following": False,
            "reading": False,
            "reasoning": False,
            "planning": False,
            "causal_counterfactual": False,
            "free_writing": False,
            "long_dialogue": False,
            "continual_learning": False,
        },
    }


def main() -> None:
    rows = [evaluate(size, seed) for size in (16, 64, 256, 1024) for seed in (1, 7, 19, 31, 43)]
    summary = {}
    for size in (16, 64, 256, 1024):
        selected = [row for row in rows if row["size"] == size]
        summary[str(size)] = {
            key: statistics.mean(row[key] for row in selected)
            for key in (
                "correct_predicate_in_top2", "natural_clarification", "decoy_rejection",
                "model_bytes", "peak_rss_kib", "fit_ms", "mean_inference_ms",
                "max_candidate_count", "feature_reads",
            )
        }
    report = {
        "experiment": "counterfactual-predicate-induction-001",
        "rows": rows,
        "summary": summary,
        "claim_boundary": {
            "highschool_level_passed": False,
            "native_japanese_communication_passed": False,
            "completion": False,
        },
    }
    Path("counterfactual_predicate_induction_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
