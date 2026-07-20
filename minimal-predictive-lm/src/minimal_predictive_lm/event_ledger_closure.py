from __future__ import annotations

import argparse
import hashlib
import json
import random
import resource
import statistics
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


def _atoms(text: str) -> tuple[str, ...]:
    """Raw, task-agnostic Japanese character atoms and bounded skip-bigrams."""
    value = "".join(text.split())
    out = [value[i : i + 2] for i in range(max(0, len(value) - 1))]
    out += [value[i] + value[i + 2] for i in range(max(0, len(value) - 2))]
    return tuple(dict.fromkeys(out))


def _stable(text: str, buckets: int) -> int:
    digest = hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % buckets


@dataclass(frozen=True, slots=True)
class Episode:
    context: tuple[str, ...]
    observation_before: str
    intervention: str
    observation_after: str
    response: str


@dataclass(frozen=True, slots=True)
class Event:
    pre: tuple[int, ...]
    cue: tuple[int, ...]
    add: tuple[int, ...]
    remove: tuple[int, ...]
    support: int


class EventLedger:
    """Bounded non-neural learner of recurring counterfactual state updates.

    It stores neither complete prompts nor complete responses. Events survive only
    when the same sparse before/intervention -> after change recurs. Generation is
    a proof trace over active state changes, deliberately exposing whether a
    genuine reusable state algebra emerged.
    """

    def __init__(self, buckets: int = 8192, capacity: int = 2048) -> None:
        self.buckets = buckets
        self.capacity = capacity
        self.counts: Counter[tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...], tuple[int, ...]]] = Counter()
        self.events: list[Event] = []
        self.state: Counter[int] = Counter()
        self.reads = 0

    def code(self, text: str) -> frozenset[int]:
        return frozenset(_stable(atom, self.buckets) for atom in _atoms(text))

    def observe(self, episode: Episode) -> None:
        before = self.code(episode.observation_before)
        cue = self.code("\n".join((*episode.context[-4:], episode.intervention)))
        after = self.code(episode.observation_after)
        add = tuple(sorted(after - before))
        remove = tuple(sorted(before - after))
        # Keep only recurring transitions; unique surface fingerprints are rejected.
        key = (tuple(sorted(before & after)), tuple(sorted(cue)), add, remove)
        self.counts[key] += 1

    def consolidate(self, minimum_support: int = 2) -> None:
        rows = sorted(self.counts.items(), key=lambda item: (-item[1], item[0]))
        self.events = [Event(*key, support) for key, support in rows if support >= minimum_support][: self.capacity]

    def reset(self) -> None:
        self.state.clear()
        self.reads = 0

    @staticmethod
    def _jaccard(left: frozenset[int], right: Sequence[int]) -> float:
        target = set(right)
        union = len(left | target)
        return len(left & target) / union if union else 0.0

    def step(self, context: Sequence[str], utterance: str) -> str:
        cue = self.code("\n".join((*context[-4:], utterance)))
        active = frozenset(self.state)
        best: Event | None = None
        best_score = 0.0
        for event in self.events:
            self.reads += 1
            score = 0.72 * self._jaccard(cue, event.cue) + 0.28 * self._jaccard(active, event.pre)
            score *= 1.0 + min(4, event.support) * 0.03
            if score > best_score:
                best_score, best = score, event
        if best is None or best_score < 0.08:
            return "この発話から再利用可能な状態変化を確定できません。"
        for atom in best.remove:
            self.state.pop(atom, None)
        for atom in best.add:
            self.state[atom] += 1
        # No stored answer text. This intentionally weak realizer exposes whether
        # the induced event itself carries enough semantics for free expression.
        if best.add and best.remove:
            return f"状態を更新しました。追加{len(best.add)}項目、取消{len(best.remove)}項目です。"
        if best.add:
            return f"新しい状態を{len(best.add)}項目反映しました。"
        if best.remove:
            return f"以前の状態を{len(best.remove)}項目取り消しました。"
        return "状態は変わりません。"

    def serialized_bytes(self) -> int:
        payload = {
            "buckets": self.buckets,
            "capacity": self.capacity,
            "events": [
                {"pre": e.pre, "cue": e.cue, "add": e.add, "remove": e.remove, "support": e.support}
                for e in self.events
            ],
        }
        return len(json.dumps(payload, separators=(",", ":")).encode())


def training_episodes(n: int, seed: int) -> list[Episode]:
    rng = random.Random(seed)
    people = ["葵", "蓮", "美咲", "翔", "結衣", "湊", "凛", "陽斗"]
    objects = ["赤い鍵", "青い本", "白い箱", "古い地図", "銀の鈴"]
    places = ["机", "棚", "玄関", "鞄", "庭"]
    rows: list[Episode] = []
    for index in range(n):
        p, obj, src, dst = rng.choice(people), rng.choice(objects), rng.choice(places), rng.choice(places)
        if dst == src:
            dst = places[(places.index(src) + 1) % len(places)]
        before = f"{obj}は{src}にある。{p}は予定を決めていない。"
        mode = index % 4
        if mode == 0:
            intervention = f"{p}が{obj}を{dst}へ移した。"
            after = f"{obj}は{dst}にある。{p}は予定を決めていない。"
            response = "移動を確認した。"
        elif mode == 1:
            intervention = f"{p}は明日{dst}へ行くと決めた。"
            after = f"{obj}は{src}にある。{p}は明日{dst}へ行く予定だ。"
            response = "予定を記録した。"
        elif mode == 2:
            intervention = f"さっきの予定は取り消す。"
            before = f"{obj}は{src}にある。{p}は明日{dst}へ行く予定だ。"
            after = f"{obj}は{src}にある。{p}は予定を決めていない。"
            response = "予定を取り消した。"
        else:
            intervention = f"もし{obj}を{dst}へ移さなかったら、場所は変わらない。"
            after = before
            response = "反実仮想では状態は維持される。"
        rows.append(Episode((f"{p}について話している。",), before, intervention, after, response))
    return rows


GATE = {
    "free_dialogue": (("今日は仕事で失敗して落ち込んでいる。",), "どうしたら気持ちを整理できるかな？", ("つら", "整理", "気持")),
    "instruction": (("短く答えて。",), "机の鍵を棚へ移したことを一文で確認して。", ("鍵", "棚")),
    "reading": (("美咲は駅で蓮に会った。雨だった。",), "美咲はどこで蓮に会った？", ("駅",)),
    "reasoning": (("すべての青い箱は重い。これは青い箱だ。",), "これは重い？理由も答えて。", ("重", "理由")),
    "planning": (("明日までに資料を提出する。今夜は2時間使える。",), "実行順を計画して。", ("確認", "提出", "順")),
    "causal_counterfactual": (("窓を開けたので部屋が冷えた。",), "窓を開けなかったらどうなる？", ("冷", "開け")),
    "free_description": (("公園に桜が咲き、子どもが走っている。",), "情景を自然に説明して。", ("桜", "子ども", "公園")),
    "long_dialogue": (("旅行先は長野。", "同行者は彼女。", "訂正、同行者は妹。", "予算は三万円。"), "旅行の条件をまとめて。", ("長野", "妹", "三万")),
    "continual_learning": (("新しい約束として、合図『星』は休憩を意味する。",), "星", ("休憩",)),
}


def evaluate(model: EventLedger) -> tuple[dict[str, bool], dict[str, str], list[float], list[int]]:
    checks: dict[str, bool] = {}
    outputs: dict[str, str] = {}
    latencies: list[float] = []
    reads: list[int] = []
    model.reset()
    for name, (context, utterance, required) in GATE.items():
        before_reads = model.reads
        started = time.perf_counter_ns()
        output = model.step(context, utterance)
        latencies.append((time.perf_counter_ns() - started) / 1_000_000)
        reads.append(model.reads - before_reads)
        outputs[name] = output
        checks[name] = all(term in output for term in required)
    return checks, outputs, latencies, reads


def run(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    sizes = (16, 64, 256, 1024)
    seeds = (1, 7, 19)
    results = []
    experiment_started = time.perf_counter()
    for size in sizes:
        for seed in seeds:
            episodes = training_episodes(size, seed)
            model = EventLedger()
            started = time.perf_counter()
            for episode in episodes:
                model.observe(episode)
            model.consolidate()
            train_ms = (time.perf_counter() - started) * 1000
            checks, outputs, latencies, reads = evaluate(model)
            results.append({
                "data_size": size,
                "seed": seed,
                "gate_score": sum(checks.values()) / len(checks),
                "checks": checks,
                "outputs": outputs,
                "events": len(model.events),
                "model_bytes": model.serialized_bytes(),
                "train_ms": train_ms,
                "mean_inference_ms": statistics.mean(latencies),
                "p95_inference_ms": sorted(latencies)[-1],
                "candidate_count": 1,
                "mean_reads": statistics.mean(reads),
                "max_reads": max(reads),
            })
    largest = [row for row in results if row["data_size"] == max(sizes)]
    report = {
        "experiment": "event-ledger-closure-001",
        "hypothesis": "persistent counterfactual event closure can induce a reusable state algebra without answer storage",
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
        },
        "elapsed_s": time.perf_counter() - experiment_started,
        "integrated_gate_passed": all(all(row["checks"].values()) for row in largest),
        "under_1gb": max(row["model_bytes"] for row in results) < 1_000_000_000,
        "highschool_level_passed": False,
        "native_japanese_communication_passed": False,
        "architecture": {
            "transformer": False,
            "neural_network": False,
            "backpropagation": False,
            "rag": False,
            "external_llm": False,
            "stored_complete_answers": False,
            "bounded_event_reads": True,
        },
    }
    (output_dir / "event-ledger-closure-001.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Event Ledger Closure 001", "", f"Integrated gate: {report['integrated_gate_passed']}", ""]
    for row in largest:
        lines += [f"## seed {row['seed']}", ""] + [f"- {key}: {value}" for key, value in row["outputs"].items()] + [""]
    (output_dir / "transcript.md").write_text("\n".join(lines), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/event-ledger-closure-001"))
    args = parser.parse_args()
    print(json.dumps(run(args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
