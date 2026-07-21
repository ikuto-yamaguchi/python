from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import resource
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path

TOKENS = [
    "<unk>", "赤", "青", "緑", "白", "黒", "黄",
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "はい", "いいえ", "濡れる", "乾く", "右", "左", "進む", "戻る",
    "A", "B", "C", "D",
]
TOKEN_TO_ID = {token: index for index, token in enumerate(TOKENS)}
DIMENSION = 64


def softmax(values: list[float]) -> list[float]:
    maximum = max(values)
    exponentials = [math.exp(value - maximum) for value in values]
    total = sum(exponentials)
    return [value / total for value in exponentials]


def key_of(text: str) -> list[float]:
    """Generic UTF-8 n-gram projection without task labels or semantic slots."""
    source = text.encode("utf-8")
    vector = [0.0] * DIMENSION
    grams: list[bytes] = []
    for width in (2, 3, 4):
        grams.extend(source[index:index + width] for index in range(max(0, len(source) - width + 1)))
    for gram in grams or [source]:
        digest = int.from_bytes(hashlib.blake2b(gram, digest_size=8).digest(), "little")
        vector[digest % DIMENSION] += 1.0 if ((digest >> 8) & 1) == 0 else -1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def blind_rename(text: str, rng: random.Random) -> str:
    """Blind symbol permutation used as a counterfactual replay perturbation."""
    symbols = ["A", "B", "C", "D", "赤", "青", "緑", "白", "黒", "黄"]
    replacements = symbols[:]
    rng.shuffle(replacements)
    table = dict(zip(symbols, replacements))
    return "".join(table.get(character, character) for character in text)


def make_example(rng: random.Random) -> tuple[str, str, str]:
    family = rng.randrange(4)
    if family == 0:
        entity = rng.choice("ABCD")
        first, second = rng.sample(["赤", "青", "緑", "白", "黒", "黄"], 2)
        return f"記録 {entity} は {first}。更新 {entity} は {second}。質問 {entity} の色は", second, "overwrite"
    if family == 1:
        left = rng.randrange(6)
        right = rng.randrange(4)
        return f"値は {left}。{right} 加える。質問 値は", str((left + right) % 10), "arithmetic"
    if family == 2:
        cause = rng.choice(["雨", "散水"])
        present = rng.random() < 0.5
        text = f"{cause} なら 地面は濡れる。{cause} は {'ある' if present else 'ない'}。質問 地面は"
        return text, "濡れる" if present else "乾く", "causal"
    start = rng.choice(["左", "右"])
    goal = "右" if start == "左" else "左"
    return f"現在は{start}。目標は{goal}。一歩だけ選ぶ。質問 行動は", "進む" if start == "左" else "戻る", "planning"


class FastMemory:
    def __init__(self, mode: str) -> None:
        self.mode = mode
        self.weights = [[0.0] * len(TOKENS) for _ in range(DIMENSION)]
        self.pending: list[tuple[list[float], int, float]] = []
        self.buffer: list[tuple[str, list[float], int]] = []
        self.accepted = 0
        self.rejected = 0
        self.candidates = 0
        self.reads = 0

    def scores(self, key: list[float]) -> list[float]:
        self.reads += DIMENSION * len(TOKENS)
        return [
            sum(key[index] * self.weights[index][token] for index in range(DIMENSION))
            for token in range(len(TOKENS))
        ]

    def loss(self, key: list[float], target: int, candidate: tuple[list[float], int, float] | None = None) -> float:
        scores = self.scores(key)
        if candidate is not None:
            candidate_key, candidate_target, scale = candidate
            overlap = sum(key[index] * candidate_key[index] for index in range(DIMENSION))
            scores[candidate_target] += scale * overlap
        return -math.log(max(1e-12, softmax(scores)[target]))

    def commit(self, candidate: tuple[list[float], int, float]) -> None:
        key, target, scale = candidate
        for index, value in enumerate(key):
            self.weights[index][target] += scale * value

    def observe(self, text: str, target: str, rng: random.Random) -> None:
        key = key_of(text)
        target_id = TOKEN_TO_ID.get(target, 0)
        self.buffer.append((text, key, target_id))
        self.buffer = self.buffer[-24:]
        self.candidates += 1
        candidate = (key, target_id, 1.25)

        if self.mode == "always":
            self.commit(candidate)
            self.accepted += 1
            return

        self.pending.append(candidate)
        if len(self.pending) < 32:
            return
        candidate = self.pending.pop(0)
        sample = rng.sample(self.buffer, min(4, len(self.buffer)))
        before = 0.0
        after = 0.0
        for replay_text, replay_key, replay_target in sample:
            before += self.loss(replay_key, replay_target)
            after += self.loss(replay_key, replay_target, candidate)
            renamed_key = key_of(blind_rename(replay_text, rng))
            before += self.loss(renamed_key, replay_target)
            after += self.loss(renamed_key, replay_target, candidate)
        if after < before:
            self.commit(candidate)
            self.accepted += 1
        else:
            self.rejected += 1

    def predict(self, text: str) -> str:
        scores = self.scores(key_of(text))
        return TOKENS[max(range(len(scores)), key=scores.__getitem__)]

    def model_bytes(self) -> int:
        matrix_bytes = DIMENSION * len(TOKENS) * 8
        pending_bytes = len(self.pending) * (DIMENSION * 8 + 24)
        return matrix_bytes + pending_bytes


INTEGRATED_GATE = [
    ("今日は失敗続きで落ち込んでいる。", "気持ち"),
    ("赤、青、緑を逆順に並べて。", "緑"),
    ("葵は青。蓮は赤。葵の色は", "青"),
    ("全ての鳥は動物。すずめは鳥。すずめは", "動物"),
    ("駅へ行き、切符を買い、電車に乗る。最初は", "駅"),
    ("雨が降らなかったなら地面は", "乾く"),
    ("省エネについて短く説明して。", "省"),
    ("最初に名前は葵と言った。名前は", "葵"),
    ("新規則: ピコは青を意味する。ピコは", "青"),
]


@dataclass
class RunMetrics:
    mode: str
    seed: int
    train_examples: int
    accuracy: float
    counterfactual_accuracy: float
    model_bytes: int
    peak_rss_kib: int
    train_seconds: float
    inference_ms: float
    candidates: int
    reads: int
    accepted: int
    rejected: int
    integrated_gate: float


def run(mode: str, seed: int, train_examples: int) -> RunMetrics:
    rng = random.Random(seed)
    memory = FastMemory(mode)
    training = [make_example(rng) for _ in range(train_examples)]
    started = time.perf_counter()
    for text, target, _ in training:
        memory.observe(text, target, rng)
    train_seconds = time.perf_counter() - started

    test = [make_example(random.Random(seed * 100_000 + index)) for index in range(256)]
    accuracy = sum(memory.predict(text) == target for text, target, _ in test) / len(test)
    rename_rng = random.Random(seed + 999)
    counterfactual_accuracy = sum(
        memory.predict(blind_rename(text, rename_rng)) == target for text, target, _ in test
    ) / len(test)

    started = time.perf_counter()
    for text, _, _ in test[:128]:
        memory.predict(text)
    inference_ms = (time.perf_counter() - started) * 1000.0 / 128
    integrated_gate = sum(memory.predict(prompt).startswith(expected) for prompt, expected in INTEGRATED_GATE) / len(INTEGRATED_GATE)

    return RunMetrics(
        mode=mode,
        seed=seed,
        train_examples=train_examples,
        accuracy=accuracy,
        counterfactual_accuracy=counterfactual_accuracy,
        model_bytes=memory.model_bytes(),
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        train_seconds=train_seconds,
        inference_ms=inference_ms,
        candidates=memory.candidates,
        reads=memory.reads,
        accepted=memory.accepted,
        rejected=memory.rejected,
        integrated_gate=integrated_gate,
    )


def run_experiment(output: Path) -> dict:
    runs = [
        run(mode, seed, scale)
        for scale in (128, 512, 2048)
        for seed in (1, 7, 19)
        for mode in ("always", "delayed_counterfactual")
    ]
    aggregate: dict[str, dict[str, dict[str, float]]] = {}
    for mode in ("always", "delayed_counterfactual"):
        aggregate[mode] = {}
        for scale in (128, 512, 2048):
            selected = [item for item in runs if item.mode == mode and item.train_examples == scale]
            aggregate[mode][str(scale)] = {
                "accuracy_mean": statistics.mean(item.accuracy for item in selected),
                "counterfactual_accuracy_mean": statistics.mean(item.counterfactual_accuracy for item in selected),
                "integrated_gate_mean": statistics.mean(item.integrated_gate for item in selected),
                "model_bytes_max": max(item.model_bytes for item in selected),
                "peak_rss_kib_max": max(item.peak_rss_kib for item in selected),
                "train_seconds_mean": statistics.mean(item.train_seconds for item in selected),
                "inference_ms_mean": statistics.mean(item.inference_ms for item in selected),
                "accepted_mean": statistics.mean(item.accepted for item in selected),
                "rejected_mean": statistics.mean(item.rejected for item in selected),
                "candidate_count": scale,
                "read_count_mean": statistics.mean(item.reads for item in selected),
            }
    report = {
        "hypothesis": "Delayed Counterfactual Consolidation",
        "aggregate": aggregate,
        "runs": [asdict(item) for item in runs],
        "claim_boundary": {
            "completion": False,
            "highschool_level_passed": False,
            "native_japanese_communication_passed": False,
            "weak_smartphone_verified": False,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/delayed_counterfactual_consolidation.json"))
    args = parser.parse_args()
    report = run_experiment(args.output)
    print(json.dumps(report["aggregate"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
