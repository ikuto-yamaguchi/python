from __future__ import annotations

import json
import random
import resource
import sys
import time
from collections import Counter
from dataclasses import dataclass
from difflib import SequenceMatcher
from statistics import mean

# Generator-only vocabularies. The learner never receives these lists.
ENTITIES = ["ノクタ", "ミレア", "ソルン", "カディ", "フレナ", "リュモ"]
VALUES = ["青い棚", "北の箱", "丸い台", "静かな室", "第三庫", "窓側"]
STATE_TEMPLATES = [
    "{e}は{v}にあります。",
    "{v}には{e}があります。",
    "現在、{e}の場所は{v}です。",
    "保管記録：{e}→{v}。",
]
TRAIN_COMMANDS = [
    "{e}を{v}へ移してください。",
    "{v}に{e}を運んで。",
    "{e}の置き場を{v}に変更。",
]
UNSEEN_COMMANDS = [
    "行き先は{v}。対象は{e}です。",
    "{e}について、最終的な所在を{v}とせよ。",
    "いま{e}がある場所ではなく{v}へ配置し直す。",
]
NOOP_COMMANDS = ["{e}の状態を確認してください。", "{e}には触れないでください。"]


@dataclass(frozen=True)
class Episode:
    before: str
    command: str
    after: str
    changed: bool


@dataclass(frozen=True)
class Candidate:
    entity: str
    old_value: str
    new_value: str
    orientation: str


def generate(seed: int, count: int, unseen: bool, include_noop: bool) -> list[Episode]:
    rng = random.Random(seed)
    rows: list[Episode] = []
    for index in range(count):
        entity = rng.choice(ENTITIES) + str(rng.randrange(1000, 9999))
        old_value = rng.choice(VALUES) + str(rng.randrange(10, 99))
        new_value = rng.choice(VALUES) + str(rng.randrange(10, 99))
        state_template = rng.choice(STATE_TEMPLATES)
        changed = not (include_noop and index % 7 == 0)
        before = state_template.format(e=entity, v=old_value)
        if changed:
            command_template = rng.choice(UNSEEN_COMMANDS if unseen else TRAIN_COMMANDS)
            command = command_template.format(e=entity, v=new_value)
            after = state_template.format(e=entity, v=new_value)
        else:
            command = rng.choice(NOOP_COMMANDS).format(e=entity)
            after = before
        rows.append(Episode(before, command, after, changed))
    return rows


def common_spans(left: str, right: str) -> list[str]:
    matcher = SequenceMatcher(None, left, right, autojunk=False)
    spans: list[str] = []
    for block in matcher.get_matching_blocks():
        if block.size < 2:
            continue
        span = left[block.a : block.a + block.size]
        spans.append(span)
        if len(span) >= 4:
            spans.extend((span[1:], span[:-1]))
    return sorted(set(spans), key=len, reverse=True)[:10]


def changed_parts(before: str, after: str) -> tuple[list[str], list[str]]:
    old_parts: list[str] = []
    new_parts: list[str] = []
    matcher = SequenceMatcher(None, before, after, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("replace", "delete") and i2 > i1:
            old_parts.append(before[i1:i2])
        if tag in ("replace", "insert") and j2 > j1:
            new_parts.append(after[j1:j2])
    return old_parts, new_parts


def enumerate_training_candidates(episode: Episode) -> list[Candidate]:
    if not episode.changed:
        return []
    old_parts, new_parts = changed_parts(episode.before, episode.after)
    entities = common_spans(episode.before, episode.command)
    result: list[Candidate] = []
    for entity in entities[:5]:
        for old_value in old_parts[:3]:
            for new_value in new_parts[:3]:
                if old_value == new_value or entity in old_value or entity in new_value:
                    continue
                for orientation in ("entity-first", "value-first"):
                    result.append(Candidate(entity, old_value, new_value, orientation))
    return result[:64]


def skeleton(text: str, spans: list[str]) -> str:
    output = text
    for index, span in enumerate(sorted(set(spans), key=len, reverse=True)):
        output = output.replace(span, f"§{index}§")
    return output


class FactorGraphLearner:
    def __init__(self, relaxation: bool, contrastive: bool):
        self.relaxation = relaxation
        self.contrastive = contrastive
        self.prototypes: list[tuple[str, str]] = []
        self.factor_counts: Counter[tuple[str, str]] = Counter()
        self.training_seconds = 0.0

    def fit(self, episodes: list[Episode]) -> "FactorGraphLearner":
        started = time.perf_counter()
        for episode in episodes:
            scored: list[tuple[float, Candidate]] = []
            for candidate in enumerate_training_candidates(episode):
                reconstruction = float(
                    candidate.entity in episode.before
                    and candidate.old_value in episode.before
                    and candidate.new_value in episode.after
                )
                identity = float(candidate.entity in episode.after)
                command_support = SequenceMatcher(
                    None, candidate.new_value, episode.command, autojunk=False
                ).ratio()
                contrast = 1.0 if (self.contrastive and episode.changed) else 0.0
                energy = -(2.0 * reconstruction + identity + command_support + contrast)
                scored.append((energy, candidate))
            scored.sort(key=lambda item: item[0])
            winners = scored[:6] if self.relaxation else scored[:1]
            for _, candidate in winners:
                if len(self.prototypes) >= 40:
                    break
                command_skeleton = skeleton(
                    episode.command, [candidate.entity, candidate.new_value]
                )
                self.prototypes.append((command_skeleton, candidate.orientation))
                self.factor_counts[(command_skeleton, candidate.orientation)] += 1
        self.training_seconds = time.perf_counter() - started
        return self

    def input_candidates(self, before: str, command: str) -> list[Candidate]:
        entities = common_spans(before, command)
        candidates: list[Candidate] = []
        for entity in entities[:6]:
            residual = command.replace(entity, "|")
            chunks = [
                chunk.strip("。、，：:→ 　をにはへがのですしてくださいせよ直す")
                for chunk in residual.split("|")
            ]
            chunks = [chunk for chunk in chunks if len(chunk) >= 2]
            before_parts = before.replace(entity, "|").split("|")
            old_values = [
                part.strip("。、，：:→ 　をにはへがのです現在保管記録場所確認置かれています")
                for part in before_parts
            ]
            for old_value in old_values:
                if len(old_value) < 2:
                    continue
                for new_value in chunks[:6]:
                    for orientation in ("entity-first", "value-first"):
                        candidates.append(
                            Candidate(entity, old_value, new_value, orientation)
                        )
        return candidates[:96]

    def predict(self, before: str, command: str) -> tuple[str, int, int, bool]:
        candidates = self.input_candidates(before, command)
        if not candidates:
            return before, 0, 0, False
        states: list[list[object]] = []
        for candidate in candidates:
            command_skeleton = skeleton(command, [candidate.entity, candidate.new_value])
            similarities = [
                SequenceMatcher(None, command_skeleton, prototype, autojunk=False).ratio()
                + (0.1 if orientation == candidate.orientation else 0.0)
                for prototype, orientation in self.prototypes[-20:]
            ]
            support = max(similarities, default=0.0)
            reconstruction = float(
                candidate.entity in before and candidate.old_value in before
            )
            energy = -(1.6 * support + reconstruction)
            states.append([energy, candidate])
        states.sort(key=lambda item: item[0])
        iterations = 1
        if self.relaxation:
            for _ in range(8):
                previous = states[0][1]
                for state in states[:24]:
                    candidate = state[1]
                    assert isinstance(candidate, Candidate)
                    predicted = before.replace(candidate.old_value, candidate.new_value, 1)
                    consistency = int(candidate.entity in predicted) + int(
                        candidate.new_value in predicted
                    )
                    state[0] = float(state[0]) - 0.35 * consistency
                states.sort(key=lambda item: item[0])
                iterations += 1
                if states[0][1] == previous:
                    break
        best = states[0][1]
        assert isinstance(best, Candidate)
        predicted = before.replace(best.old_value, best.new_value, 1)
        margin = float(states[1][0]) - float(states[0][0]) if len(states) > 1 else 99.0
        return predicted, iterations, min(len(states), 24), margin < 0.03

    def model_bytes(self) -> int:
        return len(json.dumps(self.prototypes, ensure_ascii=False).encode("utf-8"))


def evaluate(model: FactorGraphLearner, episodes: list[Episode]) -> dict[str, float]:
    started = time.perf_counter()
    correct = 0
    abstentions = 0
    iterations: list[int] = []
    active: list[int] = []
    for episode in episodes:
        prediction, count, active_count, abstain = model.predict(
            episode.before, episode.command
        )
        correct += int(prediction == episode.after)
        abstentions += int(abstain)
        iterations.append(count)
        active.append(active_count)
    elapsed = time.perf_counter() - started
    return {
        "accuracy": correct / len(episodes),
        "abstention": abstentions / len(episodes),
        "latency_ms": 1000.0 * elapsed / len(episodes),
        "iterations": mean(iterations),
        "active_candidates": mean(active),
    }


def main() -> None:
    rows: list[dict[str, object]] = []
    for seed in (1, 7, 19):
        training = generate(seed, 12, unseen=False, include_noop=True)
        splits = {
            "seen": generate(seed + 100, 8, unseen=False, include_noop=False),
            "unseen_syntax": generate(seed + 200, 8, unseen=True, include_noop=False),
            "confound": generate(seed + 300, 8, unseen=False, include_noop=True),
        }
        methods = (
            ("greedy", False, False),
            ("relax_no_contrast", True, False),
            ("open_factor_relax", True, True),
        )
        for name, relaxation, contrastive in methods:
            model = FactorGraphLearner(relaxation, contrastive).fit(training)
            row: dict[str, object] = {
                "seed": seed,
                "method": name,
                "model_bytes": model.model_bytes(),
                "training_seconds": model.training_seconds,
                "prototype_count": len(model.prototypes),
                "factor_count": len(model.factor_counts),
            }
            for split, episodes in splits.items():
                row[split] = evaluate(model, episodes)
            rows.append(row)

    aggregate: dict[str, dict[str, float]] = {}
    for method in ("greedy", "relax_no_contrast", "open_factor_relax"):
        selected = [row for row in rows if row["method"] == method]
        aggregate[method] = {
            "seen_accuracy": mean(row["seen"]["accuracy"] for row in selected),
            "unseen_syntax_accuracy": mean(
                row["unseen_syntax"]["accuracy"] for row in selected
            ),
            "confound_accuracy": mean(
                row["confound"]["accuracy"] for row in selected
            ),
            "confound_abstention": mean(
                row["confound"]["abstention"] for row in selected
            ),
            "model_bytes": mean(row["model_bytes"] for row in selected),
            "training_seconds": mean(
                row["training_seconds"] for row in selected
            ),
            "inference_latency_ms": mean(
                row["unseen_syntax"]["latency_ms"] for row in selected
            ),
            "iterations": mean(
                row["unseen_syntax"]["iterations"] for row in selected
            ),
            "active_candidates": mean(
                row["unseen_syntax"]["active_candidates"] for row in selected
            ),
            "prototype_count": mean(
                row["prototype_count"] for row in selected
            ),
        }

    result = {
        "hypothesis": "Open-Set Factor Graph Proposal and Contrastive Relaxation",
        "rows": rows,
        "aggregate": aggregate,
        "peak_rss_kib_runtime_included": resource.getrusage(
            resource.RUSAGE_SELF
        ).ru_maxrss,
        "python": sys.version,
        "highschool_level_passed": False,
        "native_japanese_communication_passed": False,
        "weak_smartphone_verified": False,
        "completion": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
