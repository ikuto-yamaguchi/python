from __future__ import annotations

import argparse
import json
import random
import resource
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class Episode:
    context: str
    response: str


def split_change(a: str, b: str) -> tuple[str, str, str, str]:
    prefix = 0
    while prefix < min(len(a), len(b)) and a[prefix] == b[prefix]:
        prefix += 1
    suffix = 0
    while (
        suffix < min(len(a) - prefix, len(b) - prefix)
        and a[-1 - suffix] == b[-1 - suffix]
    ):
        suffix += 1
    end_a = len(a) - suffix if suffix else len(a)
    end_b = len(b) - suffix if suffix else len(b)
    return a[prefix:end_a], b[prefix:end_b], a[:prefix], a[end_a:]


@dataclass
class ExchangeRule:
    context_prefix: str
    context_source: str
    context_suffix: str
    response_prefix: str
    response_source: str
    response_suffix: str
    support: int = 1

    def apply(self, text: str) -> tuple[str, int] | None:
        if not text.startswith(self.context_prefix) or not text.endswith(self.context_suffix):
            return None
        end = len(text) - len(self.context_suffix) if self.context_suffix else len(text)
        middle = text[len(self.context_prefix) : end]
        if self.context_source not in middle:
            return None
        binding = middle.replace(self.context_source, "", 1)
        response = self.response_prefix + self.response_source.replace("{x}", binding) + self.response_suffix
        evidence = len(self.context_prefix) + len(self.context_suffix) + len(self.context_source)
        return response, evidence


class ExchangeBindingClosure:
    """Induce sparse bindings from exchange-preserving prompt/response changes.

    The learner receives only raw Japanese episode pairs. It has no task labels,
    answer keys, topic dictionary, retrieval corpus, or external language model.
    This experiment intentionally tests whether exchange closure is sufficient;
    it is not presented as a successful language model.
    """

    def __init__(self, max_rules: int = 256, max_reads: int = 32) -> None:
        self.max_rules = max_rules
        self.max_reads = max_reads
        self.rules: list[ExchangeRule] = []
        self.last_reads = 0

    def fit(self, episodes: Sequence[Episode]) -> None:
        candidates: dict[tuple[str, ...], int] = {}
        for index, first in enumerate(episodes):
            for second in episodes[index + 1 : min(len(episodes), index + 9)]:
                left_context, right_context, context_prefix, context_suffix = split_change(
                    first.context, second.context
                )
                left_response, right_response, response_prefix, response_suffix = split_change(
                    first.response, second.response
                )
                if (
                    not left_context
                    or not right_context
                    or left_context == right_context
                    or not left_response
                    or not right_response
                ):
                    continue
                if left_context not in left_response or right_context not in right_response:
                    continue
                key = (
                    context_prefix,
                    left_context,
                    context_suffix,
                    response_prefix,
                    left_response.replace(left_context, "{x}", 1),
                    response_suffix,
                )
                candidates[key] = candidates.get(key, 0) + 1
        ranked = sorted(candidates.items(), key=lambda item: (-item[1], item[0]))[: self.max_rules]
        self.rules = [ExchangeRule(*key, support=support) for key, support in ranked]

    def generate(self, context: str) -> str:
        best: tuple[str, int] | None = None
        self.last_reads = 0
        for rule in self.rules[: self.max_reads]:
            self.last_reads += 1
            result = rule.apply(context)
            if result is not None and (best is None or result[1] > best[1]):
                best = result
        return best[0] if best else "未解決の要求を構成できません。"

    def serialized_bytes(self) -> int:
        payload = [rule.__dict__ for rule in self.rules]
        return len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


NAMES = ["葵", "蓮", "凛", "湊", "結衣", "樹", "紬", "陽太", "澪", "蒼"]
ITEMS = ["赤い鍵", "青い本", "銀の箱", "白い封筒", "黒い石", "緑の札"]
PLACES = ["机", "棚", "玄関", "倉庫", "庭", "教室"]


def training_examples() -> list[Episode]:
    examples: list[Episode] = []
    for name in NAMES:
        for item in ITEMS:
            examples.extend(
                [
                    Episode(
                        f"{name}が持っている{item}を覚えて。",
                        f"{name}が{item}を持っている状態を記録しました。",
                    ),
                    Episode(
                        f"{name}の{item}を{PLACES[len(name + item) % len(PLACES)]}へ移して。",
                        f"{item}を指定場所へ移す手順を記録しました。",
                    ),
                    Episode(
                        f"{name}は{item}を失くして落ち込んでいる。",
                        f"{name}の気持ちを受け止め、最後に見た場所を一緒に整理します。",
                    ),
                ]
            )
    return examples


INTEGRATED_GATE = [
    ("自由対話", "今日は失敗続きで落ち込んでる。", "気持ち"),
    ("指示遂行", "机の上の青い本だけを棚へ移し、赤い鍵には触れないで。", "青い本"),
    ("読解", "葵は鍵を蓮に渡した。その後、蓮は箱へ入れた。今、鍵を持つのは誰？", "蓮"),
    ("推論", "すべての鳥は羽がある。ペンギンは鳥だ。ペンギンに羽はある？", "ある"),
    ("計画", "雨が降る前に洗濯物を取り込み、窓を閉めたい。順番を考えて。", "洗濯"),
    ("因果・反実仮想", "もし電池を外していたら、懐中電灯は点いただろうか。", "点か"),
    ("自由記述", "静かな海辺の朝を三文で描写して。", "海"),
    ("長期対話", "さっき決めた旅行予算を二万円減らして、宿泊費から調整して。", "宿泊"),
    ("継続学習", "新しい約束：今後『青信号』と言ったら休憩を始める。青信号。", "休憩"),
]


def run_once(size: int, seed: int) -> dict[str, object]:
    rng = random.Random(seed)
    data = training_examples()
    rng.shuffle(data)
    train = data[:size]
    model = ExchangeBindingClosure()
    started = time.perf_counter()
    model.fit(train)
    train_ms = (time.perf_counter() - started) * 1000.0

    outputs: dict[str, dict[str, object]] = {}
    inference_times: list[float] = []
    reads: list[int] = []
    for ability, prompt, required_fragment in INTEGRATED_GATE:
        started = time.perf_counter()
        output = model.generate(prompt)
        inference_times.append((time.perf_counter() - started) * 1000.0)
        reads.append(model.last_reads)
        outputs[ability] = {
            "prompt": prompt,
            "output": output,
            "passed": required_fragment in output,
        }

    shuffled = [
        Episode(episode.context, response.response)
        for episode, response in zip(train, train[1:] + train[:1])
    ]
    decoy = ExchangeBindingClosure()
    decoy.fit(shuffled)

    return {
        "size": size,
        "seed": seed,
        "rules": len(model.rules),
        "decoy_rules": len(decoy.rules),
        "gate_score": sum(int(item["passed"]) for item in outputs.values()) / len(outputs),
        "model_bytes": model.serialized_bytes(),
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "train_ms": train_ms,
        "infer_mean_ms": statistics.mean(inference_times),
        "infer_p95_ms": max(inference_times),
        "candidate_count": 1,
        "mean_reads": statistics.mean(reads),
        "max_reads": max(reads),
        "outputs": outputs,
    }


def experiment() -> dict[str, object]:
    sizes = [18, 72, 180]
    seeds = [1, 7, 19]
    results = [run_once(size, seed) for size in sizes for seed in seeds]
    largest = [result for result in results if result["size"] == max(sizes)]
    return {
        "hypothesis": "交換後も応答変化が保存される部分構造を潜在束縛とする",
        "results": results,
        "aggregate": {
            "max_size_gate_mean": statistics.mean(float(result["gate_score"]) for result in largest),
            "max_size_gate_min": min(float(result["gate_score"]) for result in largest),
            "max_model_bytes": max(int(result["model_bytes"]) for result in results),
            "max_peak_rss_kib": max(int(result["peak_rss_kib"]) for result in results),
            "max_train_ms": max(float(result["train_ms"]) for result in results),
            "max_infer_mean_ms": max(float(result["infer_mean_ms"]) for result in results),
            "max_reads": max(int(result["max_reads"]) for result in results),
            "max_rules": max(int(result["rules"]) for result in results),
            "max_decoy_rules": max(int(result["decoy_rules"]) for result in results),
        },
        "highschool_level_passed": False,
        "native_japanese_communication_passed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="artifacts/exchange-binding-closure-001")
    args = parser.parse_args()
    report = experiment()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "exchange-binding-closure-001.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report["aggregate"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
