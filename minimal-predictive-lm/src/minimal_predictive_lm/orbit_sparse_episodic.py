from __future__ import annotations

import json
import math
import pickle
import random
import re
import resource
import statistics
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

NUM = re.compile(r"(?<!\d)(\d+)(?!\d)")


def grams(text: str, ns: tuple[int, ...] = (2, 3, 4)) -> Counter[str]:
    value = re.sub(r"\s+", "", NUM.sub("<N>", text))
    result: Counter[str] = Counter()
    for size in ns:
        result.update(value[index:index + size] for index in range(max(0, len(value) - size + 1)))
    return result


@dataclass(frozen=True)
class Binding:
    src: str
    dst: str
    item: str
    amount: int


@dataclass(frozen=True)
class Turn:
    text: str
    before: str
    after: str


@dataclass(frozen=True)
class Dialogue:
    turns: tuple[Turn, ...]


@dataclass
class Memory:
    binding: Binding
    step: int


def parse_state(text: str) -> dict[tuple[str, str], int]:
    result: dict[tuple[str, str], int] = {}
    for sentence in text.split("。"):
        if not sentence:
            continue
        match = re.match(r"(.+?)には(.+?)が(\d+)個あります", sentence)
        if not match:
            match = re.match(r"(.+?)が持つ(.+?)は(\d+)個です", sentence)
        if match:
            result[(match.group(1), match.group(2))] = int(match.group(3))
    return result


def induce(before: str, after: str) -> Binding | None:
    left, right = parse_state(before), parse_state(after)
    differences = [(key, right.get(key, value) - value) for key, value in left.items() if right.get(key, value) != value]
    negative = [row for row in differences if row[1] < 0]
    positive = [row for row in differences if row[1] > 0]
    if len(negative) != 1 or len(positive) != 1 or -negative[0][1] != positive[0][1]:
        return None
    (src, item), delta = negative[0]
    (dst, other_item), increase = positive[0]
    if item != other_item:
        return None
    return Binding(src, dst, item, increase)


def apply(before: str, binding: Binding) -> str:
    state = parse_state(before)
    if state.get((binding.src, binding.item), -1) < binding.amount:
        return before
    if (binding.dst, binding.item) not in state:
        return before
    values = {
        (binding.src, binding.item): state[(binding.src, binding.item)] - binding.amount,
        (binding.dst, binding.item): state[(binding.dst, binding.item)] + binding.amount,
    }
    output = before
    for (box, item), value in values.items():
        output = re.sub(
            rf"({re.escape(box)}には{re.escape(item)}が)\d+(個あります)",
            rf"\g<1>{value}\2",
            output,
        )
        output = re.sub(
            rf"({re.escape(box)}が持つ{re.escape(item)}は)\d+(個です)",
            rf"\g<1>{value}\2",
            output,
        )
    return output


class SparseEpisodicOrbit:
    """Learns sparse reactivation of executable causal episodes from state transitions."""

    def __init__(self, capacity: int = 8) -> None:
        self.capacity = capacity
        self.selector_weights: dict[int, dict[str, float]] = {}
        self.memories: list[Memory] = []
        self.readouts = 0
        self.candidates = 0

    @staticmethod
    def target_lag(history: list[Memory], current: Binding) -> int | None:
        for lag, memory in enumerate(reversed(history), 1):
            previous = memory.binding
            same = (previous.src, previous.dst, previous.item) == (current.src, current.dst, current.item)
            reverse = (previous.dst, previous.src, previous.item) == (current.src, current.dst, current.item)
            if same or reverse:
                return lag
        return None

    def fit(self, dialogues: Iterable[Dialogue]) -> None:
        by_lag: dict[int, Counter[str]] = defaultdict(Counter)
        for dialogue in dialogues:
            history: list[Memory] = []
            for turn in dialogue.turns:
                current = induce(turn.before, turn.after)
                if current is None:
                    continue
                explicit = current.src in turn.text and current.dst in turn.text and current.item in turn.text
                if explicit or not history:
                    history.append(Memory(current, len(history)))
                    history = history[-self.capacity:]
                    continue
                lag = self.target_lag(history, current)
                if lag is not None:
                    by_lag[lag].update(grams(turn.text))
                history.append(Memory(current, len(history)))
                history = history[-self.capacity:]
        vocabulary = set().union(*(set(values) for values in by_lag.values())) if by_lag else set()
        weights: dict[int, dict[str, float]] = {}
        for lag, own in by_lag.items():
            other: Counter[str] = Counter()
            for candidate, values in by_lag.items():
                if candidate != lag:
                    other.update(values)
            own_denominator = sum(own.values()) + len(vocabulary)
            other_denominator = sum(other.values()) + len(vocabulary)
            selected: dict[str, float] = {}
            for gram, count in own.items():
                weight = math.log(
                    ((count + 1) / own_denominator)
                    / ((other.get(gram, 0) + 1) / other_denominator)
                )
                if weight > 0.25:
                    selected[gram] = weight
            weights[lag] = selected
        self.selector_weights = weights

    def reset(self) -> None:
        self.memories = []

    def predict(self, text: str, before: str) -> tuple[str, dict[str, object]]:
        self.readouts = 0
        self.candidates = 0
        state = parse_state(before)
        entities = {entity for entity, _ in state}
        items = {item for _, item in state}
        mentioned_entities = [entity for entity in entities if entity in text]
        mentioned_items = [item for item in items if item in text]
        number = NUM.search(text)
        if len(mentioned_entities) >= 2 and mentioned_items and number:
            mentioned_entities.sort(key=text.index)
            binding = Binding(mentioned_entities[0], mentioned_entities[1], mentioned_items[0], int(number.group(1)))
            output = apply(before, binding)
            if output != before:
                self.memories.append(Memory(binding, len(self.memories)))
                self.memories = self.memories[-self.capacity:]
            return output, {"mode": "explicit", "binding": asdict(binding), "readouts": 0, "candidates": 1}
        if not self.memories:
            return before, {"mode": "abstain", "reason": "no-memory", "readouts": 0, "candidates": 0}
        features = grams(text)
        ranked: list[tuple[float, int, Memory]] = []
        for lag, memory in enumerate(reversed(self.memories), 1):
            if lag > self.capacity:
                break
            self.readouts += 1
            self.candidates += 1
            cue = sum(weight for gram, weight in self.selector_weights.get(lag, {}).items() if features.get(gram))
            mention = 3.0 * int(memory.binding.item in text)
            mention += 1.5 * int(memory.binding.src in text or memory.binding.dst in text)
            ranked.append((cue + mention + 0.12 / lag, lag, memory))
        score, lag, memory = max(ranked, key=lambda row: row[0])
        amount = int(number.group(1)) if number else memory.binding.amount
        reverse = bool(re.search(r"逆|反対|戻", text))
        if reverse:
            binding = Binding(memory.binding.dst, memory.binding.src, memory.binding.item, amount)
        else:
            binding = Binding(memory.binding.src, memory.binding.dst, memory.binding.item, amount)
        output = apply(before, binding)
        if output != before:
            self.memories.append(Memory(binding, len(self.memories)))
            self.memories = self.memories[-self.capacity:]
        return output, {
            "mode": "episodic",
            "selected_lag": lag,
            "score": score,
            "binding": asdict(binding),
            "readouts": self.readouts,
            "candidates": self.candidates,
        }


BOXES = ("赤箱", "青箱", "緑箱", "黄箱", "北棚", "南棚")
ITEMS = ("りんご", "ねじ", "カード")


def render(values: dict[tuple[str, str], int]) -> str:
    return "".join(f"{box}には{item}が{number}個あります。" for (box, item), number in values.items())


def make_dialogue(rng: random.Random, train: bool = True, turns: int = 6) -> Dialogue:
    boxes, items = list(BOXES), list(ITEMS)
    values = {(box, item): 8 for box in boxes for item in items}
    rows: list[Turn] = []
    history: list[Binding] = []
    for index in range(turns):
        before = render(values)
        if index < 3:
            src, dst = rng.sample(boxes, 2)
            item = items[index % len(items)]
            amount = rng.randint(1, 2)
            text = f"{src}から{dst}へ{item}を{amount}個移した。"
        else:
            lag = rng.choice((1, 2, 3))
            reference = history[-lag]
            amount = 1
            training_forms = {
                1: ("直前と同じ操作を1個続けた。", "さっきの操作を1個続けた。"),
                2: ("二つ前の操作を1個続けた。", "一つ飛ばした前の操作を1個続けた。"),
                3: ("三つ前の操作を1個続けた。", "最初の方の操作を1個続けた。"),
            }
            heldout_forms = {
                1: ("いちばん最近の操作を1個繰り返した。",),
                2: ("直前ではなくその前の操作を1個繰り返した。",),
                3: ("もっと前の操作を1個繰り返した。",),
            }
            text = rng.choice((training_forms if train else heldout_forms)[lag])
            src, dst, item = reference.src, reference.dst, reference.item
        values[(src, item)] -= amount
        values[(dst, item)] += amount
        binding = Binding(src, dst, item, amount)
        history.append(binding)
        rows.append(Turn(text, before, render(values)))
    return Dialogue(tuple(rows))


def evaluate(seed: int = 1, ntrain: int = 300, ntest: int = 100) -> dict[str, object]:
    rng = random.Random(seed)
    model = SparseEpisodicOrbit(8)
    training = [make_dialogue(rng, True) for _ in range(ntrain)]
    started = time.perf_counter()
    model.fit(training)
    fit_ms = (time.perf_counter() - started) * 1000
    correct = total = 0
    selected_lags: Counter[int] = Counter()
    readouts: list[int] = []
    inference: list[float] = []
    for _ in range(ntest):
        dialogue = make_dialogue(rng, False)
        model.reset()
        for turn in dialogue.turns:
            started = time.perf_counter()
            output, trace = model.predict(turn.text, turn.before)
            inference.append((time.perf_counter() - started) * 1_000_000)
            correct += output == turn.after
            total += 1
            if "selected_lag" in trace:
                selected_lags[int(trace["selected_lag"])] += 1
            readouts.append(int(trace["readouts"]))
    return {
        "accuracy": correct / total,
        "fit_ms": fit_ms,
        "inference_us_median": statistics.median(inference),
        "inference_us_p95": sorted(inference)[int(0.95 * len(inference)) - 1],
        "model_bytes": len(pickle.dumps(model)),
        "peak_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "mean_readouts": statistics.mean(readouts),
        "max_candidates": max(readouts),
        "selected_lags": dict(selected_lags),
        "learned_lags": sorted(model.selector_weights),
    }


def run(output_dir: Path) -> dict[str, object]:
    seeds = {str(seed): evaluate(seed) for seed in range(10)}
    scaling = {str(size): evaluate(100 + size, ntrain=size, ntest=80) for size in (24, 48, 96, 192, 384)}
    report: dict[str, object] = {
        "capability_id": "ORBIT-SPARSE-EPISODIC-002",
        "principle": (
            "Meaningful dialogue memory is a bounded set of executable causal episodes; reference is learned "
            "as sparse reactivation from observed state transitions, not full-history attention."
        ),
        "architecture": {
            "transformer": False,
            "neural_network": False,
            "gradient_training": False,
            "full_history_attention": False,
            "capacity": 8,
        },
        "seeds": seeds,
        "scaling": scaling,
        "aggregate": {
            "min_accuracy": min(float(row["accuracy"]) for row in seeds.values()),
            "median_model_bytes": statistics.median(float(row["model_bytes"]) for row in seeds.values()),
            "max_peak_rss_kb": max(int(row["peak_rss_kb"]) for row in seeds.values()),
            "median_inference_us": statistics.median(float(row["inference_us_median"]) for row in seeds.values()),
            "max_candidates": max(int(row["max_candidates"]) for row in seeds.values()),
        },
        "integrated_gate": {
            "free_dialogue": False,
            "instruction_following": False,
            "reading_comprehension": False,
            "reasoning": False,
            "planning": False,
            "causal_counterfactual": False,
            "free_generation": False,
            "long_dialogue": False,
            "continual_learning": False,
        },
        "highschool_level_passed": False,
        "falsification": (
            "The learned lag selector does not transfer reliably to held-out paraphrases; sparse memory solves "
            "storage/retrieval structure but lexical grounding remains the bottleneck."
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "orbit-sparse-episodic-002.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/orbit-sparse-episodic-002"))
    arguments = parser.parse_args()
    print(json.dumps(run(arguments.output_dir), ensure_ascii=False, indent=2))
