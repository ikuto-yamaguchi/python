from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import resource
import statistics
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


def _grams(text: str, n: int = 2) -> set[str]:
    compact = "".join(text.split())
    return {compact[index : index + n] for index in range(max(0, len(compact) - n + 1))}


def _bucket(text: str, buckets: int) -> int:
    digest = hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % buckets


@dataclass(frozen=True, slots=True)
class Episode:
    context: tuple[str, ...]
    intervention: str
    future: str


class TransportResidualClosure:
    """Keep only transformations shared across distinct lexical contexts.

    This is deliberately non-neural and does not store complete answers. A
    candidate transformation survives only if the same residual signature is
    observed in multiple distinct contexts. The experiment asks whether this
    transport criterion is sufficient to induce reusable Japanese meaning.
    """

    def __init__(self, buckets: int = 32_768, max_operators: int = 256, max_reads: int = 32) -> None:
        self.buckets = buckets
        self.max_operators = max_operators
        self.max_reads = max_reads
        self.operators: list[tuple[float, tuple[int, ...], tuple[tuple[int, ...], tuple[int, ...]], int]] = []
        self.reads = 0

    def fit(self, episodes: Sequence[Episode]) -> None:
        candidates: dict[tuple[tuple[int, ...], tuple[int, ...]], list[tuple[int, ...]]] = defaultdict(list)
        for episode in episodes:
            source = _grams(" ".join(episode.context) + episode.intervention)
            future = _grams(episode.future)
            added = tuple(sorted(_bucket(gram, self.buckets) for gram in future - source))
            removed = tuple(sorted(_bucket(gram, self.buckets) for gram in source - future))
            trigger = tuple(sorted(_bucket(gram, self.buckets) for gram in source))
            candidates[(added, removed)].append(trigger)

        scored = []
        for signature, triggers in candidates.items():
            if len(triggers) < 2:
                continue
            distinct_contexts = len({trigger[: min(8, len(trigger))] for trigger in triggers})
            if distinct_contexts < 2:
                continue
            support = len(triggers)
            description_length = len(signature[0]) + len(signature[1])
            score = support * math.log1p(distinct_contexts) / max(1, description_length)
            anchors = tuple(value for value, _ in Counter(value for trigger in triggers for value in trigger).most_common(24))
            scored.append((score, anchors, signature, support))

        scored.sort(reverse=True)
        self.operators = scored[: self.max_operators]

    def generate(self, context: Sequence[str], intervention: str) -> str:
        source = _grams(" ".join(context) + intervention)
        hashed_source = {_bucket(gram, self.buckets) for gram in source}
        ranked = []
        for score, anchors, signature, support in self.operators:
            overlap = len(hashed_source & set(anchors)) / max(1, len(anchors))
            if overlap > 0.0:
                ranked.append((overlap * score, anchors, signature, support))
        ranked.sort(reverse=True)
        chosen = ranked[: self.max_reads]
        self.reads += len(chosen)
        if not chosen:
            return "未解決の要求を構成できません。"

        added: set[int] = set()
        removed: set[int] = set()
        for _, _, signature, _ in chosen[:4]:
            added.update(signature[0])
            removed.update(signature[1])
        return (
            f"予測変換を{len(chosen[:4])}件合成し、"
            f"状態特徴を{len(added)}件追加、{len(removed)}件抑制しました。"
        )

    def serialized_bytes(self) -> int:
        return len(
            json.dumps(
                {"buckets": self.buckets, "operators": self.operators},
                separators=(",", ":"),
            ).encode("utf-8")
        )


SKILLS = (
    "free_dialogue",
    "instruction",
    "reading",
    "reasoning",
    "planning",
    "causal_counterfactual",
    "free_description",
    "long_dialogue",
    "continual_learning",
)

_BASE = (
    ("今日は失敗して落ち込んでいる", "気持ちを整理したい", "まず何が一番つらかったかを言葉にしてみよう。"),
    ("机の上に赤い本と青い本がある", "赤い本だけ箱へ移して", "赤い本を箱へ移し、青い本は机に残す。"),
    ("太郎は駅で花子と会い、その後図書館へ行った", "太郎が花子と会った場所は", "駅です。"),
    ("AはBより速く、BはCより速い", "最も速いのは", "Aです。"),
    ("雨を避けて買い物し、夕方までに帰る", "順序を考えて", "天気を確認し、屋内の店を先に回り、夕方前に帰る。"),
    ("スイッチを押すと灯りがつく", "押さなかった場合は", "灯りはつかない。"),
    ("静かな湖に朝日が映っている", "様子を説明して", "静かな湖面に朝日が柔らかく映っている。"),
    ("旅行先は京都に決めた", "予算は三万円。やっぱり奈良に変更", "旅行先を奈良へ更新し、予算三万円は維持する。"),
    ("毎朝コーヒーを飲むことにした", "今日は紅茶に変えた", "今日の飲み物を紅茶へ更新する。"),
)


def make_data(size: int, seed: int) -> list[Episode]:
    rng = random.Random(seed)
    people = ("太郎", "花子", "健", "美咲", "翔", "葵")
    places = ("駅", "公園", "図書館", "学校", "店")
    items = ("本", "鍵", "傘", "箱", "ノート")
    output = []
    for index in range(size):
        context, intervention, future = _BASE[index % len(_BASE)]
        replacements = {
            "太郎": rng.choice(people),
            "花子": rng.choice(people),
            "駅": rng.choice(places),
            "図書館": rng.choice(places),
            "本": rng.choice(items),
            "箱": rng.choice(items),
        }
        for source, target in replacements.items():
            context = context.replace(source, target)
            intervention = intervention.replace(source, target)
            future = future.replace(source, target)
        output.append(Episode((context,), intervention, future))
    return output


def _probes() -> dict[str, tuple[str, str]]:
    return {skill: (_BASE[index][0], _BASE[index][1]) for index, skill in enumerate(SKILLS)}


def _valid(skill: str, text: str) -> bool:
    expected = ("つら", "残", "駅", "A", "天気", "つかない", "湖", "奈良", "紅茶")[SKILLS.index(skill)]
    return expected in text and "特徴" not in text


def run_experiment(output_dir: str | Path) -> dict:
    results = []
    started = time.perf_counter()
    for data_size in (18, 72, 288, 1152):
        for seed in (1, 7, 19):
            model = TransportResidualClosure()
            training = make_data(data_size, seed)
            train_started = time.perf_counter()
            model.fit(training)
            train_ms = (time.perf_counter() - train_started) * 1000.0

            outputs = {}
            inference_times = []
            reads = []
            for skill, (context, intervention) in _probes().items():
                before_reads = model.reads
                inference_started = time.perf_counter()
                outputs[skill] = model.generate((context,), intervention)
                inference_times.append((time.perf_counter() - inference_started) * 1000.0)
                reads.append(model.reads - before_reads)
            checks = {skill: _valid(skill, output) for skill, output in outputs.items()}
            results.append(
                {
                    "data_size": data_size,
                    "seed": seed,
                    "gate_score": sum(checks.values()) / len(checks),
                    "checks": checks,
                    "outputs": outputs,
                    "operators": len(model.operators),
                    "model_bytes": model.serialized_bytes(),
                    "train_ms": train_ms,
                    "mean_inference_ms": statistics.mean(inference_times),
                    "p95_inference_ms": sorted(inference_times)[-1],
                    "candidate_count": 1,
                    "mean_reads": statistics.mean(reads),
                    "max_reads": max(reads),
                }
            )

    largest = [row for row in results if row["data_size"] == 1152]
    report = {
        "experiment": "transport-residual-closure-001",
        "hypothesis": "only counterfactually transportable residual-reducing transformations should become concepts",
        "results": results,
        "largest_scale": {
            "mean_gate_score": statistics.mean(row["gate_score"] for row in largest),
            "min_gate_score": min(row["gate_score"] for row in largest),
            "max_model_bytes": max(row["model_bytes"] for row in largest),
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "mean_train_ms": statistics.mean(row["train_ms"] for row in largest),
            "mean_inference_ms": statistics.mean(row["mean_inference_ms"] for row in largest),
            "max_reads": max(row["max_reads"] for row in largest),
            "candidate_count": 1,
            "operators": [row["operators"] for row in largest],
        },
        "elapsed_s": time.perf_counter() - started,
        "integrated_gate_passed": all(all(row["checks"].values()) for row in largest),
        "under_1gb": max(row["model_bytes"] for row in largest) < 1_000_000_000,
        "highschool_level_passed": False,
        "native_japanese_communication_passed": False,
        "architecture": {
            "transformer": False,
            "neural_network": False,
            "backpropagation": False,
            "rag": False,
            "external_llm": False,
            "stored_complete_answers": False,
            "problem_specific_branching": False,
            "bounded_reads": True,
        },
    }

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "transport-residual-closure-001.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    transcript = ["# Transport Residual Closure 001", "", f"Integrated gate: {report['integrated_gate_passed']}"]
    for row in largest:
        transcript.extend(["", f"## seed {row['seed']}"])
        transcript.extend(f"- {skill}: {output}" for skill, output in row["outputs"].items())
    (destination / "transcript.md").write_text("\n".join(transcript), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="artifacts/transport-residual-closure-001")
    arguments = parser.parse_args()
    print(json.dumps(run_experiment(arguments.output_dir)["largest_scale"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
