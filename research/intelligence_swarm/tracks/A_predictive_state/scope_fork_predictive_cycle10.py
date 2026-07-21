"""Track A Cycle 010: Scope-Fork Predictive Programs with Counterfactual Evidence Scheduling.

Controlled falsification probe.
Learner input: raw Japanese text, temporal order, generic action success/failure.
No morphology, semantic slots, ontology, dictionary, RAG, external LLM, or Transformer.

Evaluator-only hidden target spans are never exposed to the learner except through
generic success/failure after an executable probe.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
import argparse
import json
import math
import pickle
import random
import re
import resource
import statistics
import time

ENTITIES = ["青い装置", "赤い装置", "試料甲", "試料乙", "搬送台", "検査票"]
VALUES = ["待機", "稼働", "停止", "保留", "完了", "再確認", "棚A", "棚B"]
QUOTES = [("「", "」"), ("『", "』")]


def grams(text: str) -> Counter[str]:
    compact = "".join(text.split())
    return Counter(
        compact[i : i + n]
        for n in (2, 3)
        for i in range(max(0, len(compact) - n + 1))
    )


def quoted_spans(text: str) -> list[tuple[str, int, int, int]]:
    """Extract generic delimiter-derived spans without word or role dictionaries."""
    output: list[tuple[str, int, int, int]] = []
    stack: list[tuple[str, int]] = []
    opens = {left: right for left, right in QUOTES}
    closes = {right: left for left, right in QUOTES}
    for index, character in enumerate(text):
        if character in opens:
            stack.append((character, index))
        elif character in closes:
            for stack_index in range(len(stack) - 1, -1, -1):
                if stack[stack_index][0] == closes[character]:
                    _, start = stack.pop(stack_index)
                    content = text[start + 1 : index]
                    if content:
                        depth = sum(1 for _, position in stack if position < start)
                        output.append((content, start, index, depth))
                    break
    return sorted(set(output), key=lambda item: (item[1], item[2]))


def clauses(text: str) -> list[tuple[int, int, str]]:
    output: list[tuple[int, int, str]] = []
    last = 0
    for match in re.finditer(r"[。！？\n]", text):
        if match.start() > last:
            output.append((last, match.start(), text[last : match.start()]))
        last = match.end()
    if last < len(text):
        output.append((last, len(text), text[last:]))
    return output


@dataclass(frozen=True)
class Candidate:
    value: str
    start: int
    end: int
    depth: int
    clause_index: int
    total_clauses: int
    occurrence: int
    length: int

    def features(self) -> list[float]:
        recency = (self.clause_index + 1) / max(1, self.total_clauses)
        return [
            1.0,
            recency,
            float(self.depth),
            math.log1p(self.length),
            math.log1p(self.occurrence),
            recency * recency,
        ]


def candidates(text: str) -> list[Candidate]:
    text_clauses = clauses(text)
    raw = quoted_spans(text)
    counts = Counter(value for value, _, _, _ in raw)
    output: list[Candidate] = []
    for value, start, end, depth in raw:
        clause_index = 0
        for index, (left, right, _) in enumerate(text_clauses):
            if left <= start <= right:
                clause_index = index
                break
        output.append(
            Candidate(
                value=value,
                start=start,
                end=end,
                depth=depth,
                clause_index=clause_index,
                total_clauses=len(text_clauses),
                occurrence=counts[value],
                length=len(value),
            )
        )

    # Candidate equivalence by raw value. Keep the structurally latest instance.
    best: dict[str, Candidate] = {}
    for candidate in output:
        if candidate.value not in best or (
            candidate.clause_index,
            candidate.start,
        ) > (best[candidate.value].clause_index, best[candidate.value].start):
            best[candidate.value] = candidate
    return list(best.values())


class ScopeForkModel:
    def __init__(self, learning_rate: float = 0.08) -> None:
        self.weights = [0.0] * 6
        self.learning_rate = learning_rate
        self.updates = 0

    def score(self, candidate: Candidate) -> float:
        return sum(
            weight * feature
            for weight, feature in zip(self.weights, candidate.features())
        )

    def rank(self, text: str) -> list[Candidate]:
        return sorted(candidates(text), key=self.score, reverse=True)

    def learn(self, text: str, target: str) -> None:
        proposal = candidates(text)
        if not proposal:
            return
        ranked = sorted(proposal, key=self.score, reverse=True)
        predicted = ranked[0]
        correct = next((candidate for candidate in proposal if candidate.value == target), None)
        if correct is None:
            return

        # Pairwise local prediction-error update. The benchmark target corresponds
        # operationally to generic execution success, not a semantic slot label.
        if predicted.value != correct.value:
            for index, (correct_feature, predicted_feature) in enumerate(
                zip(correct.features(), predicted.features())
            ):
                self.weights[index] += self.learning_rate * (
                    correct_feature - predicted_feature
                )
        self.updates += 1


def make_episode(
    rng: random.Random, kind: str, marked: bool = True
) -> dict[str, str]:
    entity = rng.choice(ENTITIES)
    old, new, other = rng.sample(VALUES, 3)
    if kind == "literal":
        text = f"{entity}は「{old}」です。続いて「{new}」へ更新します。"
        target = new
    elif kind == "quote":
        text = (
            f"担当者は『{entity}を「{new}」にする』と言いました。"
            f"実際の記録は「{old}」です。"
        )
        target = old
    elif kind == "negation":
        text = f"{entity}は「{new}」ではありません。現在は「{old}」です。"
        target = old
    elif kind == "correction":
        text = f"{entity}を「{old}」にします。訂正します。「{new}」に変更します。"
        target = new
    elif kind == "nested":
        text = (
            f"記録には『担当者が「{entity}は『{other}』だ」と述べた』とあります。"
            f"しかし現状は「{new}」です。"
        )
        target = new
    elif kind == "paragraph":
        text = (
            f"{entity}の候補は「{old}」です。\n"
            "別件を確認します。\n"
            f"最終的には「{new}」で処理します。"
        )
        target = new
    elif kind == "plan":
        text = (
            f"最初は「{old}」を目標にします。途中で方針を見直します。"
            f"最終目標は「{new}」です。"
        )
        target = new
    elif kind == "ambiguous":
        text = f"{entity}について「{old}」と「{new}」の二案があります。"
        target = rng.choice([old, new])
    elif kind == "held_scope":
        text = (
            f"{entity}の実状態は「{old}」です。"
            f"後段の「{new}」という記載は報告文の引用にすぎません。"
        )
        target = old
    elif kind == "held_retraction":
        text = (
            f"{entity}は「{old}」を維持します。"
            f"末尾にある「{new}」案は採用されません。"
        )
        target = old
    else:
        raise ValueError(kind)

    if not marked:
        text = (
            text.replace("「", "")
            .replace("」", "")
            .replace("『", "")
            .replace("』", "")
        )
    return {"text": text, "target": target, "kind": kind}


def active_resolve(
    model: ScopeForkModel,
    text: str,
    target: str,
    max_probes: int = 4,
) -> tuple[str | None, int]:
    ranked = model.rank(text)
    probes = 0
    # Each probe executes one candidate and receives only generic success/failure.
    for candidate in ranked[:max_probes]:
        probes += 1
        if candidate.value == target:
            return candidate.value, probes
    return None, probes


def evaluate(seed: int, train_size: int) -> dict[str, object]:
    rng = random.Random(seed)
    model = ScopeForkModel()
    train_kinds = ["literal", "quote", "negation", "correction"]
    started = time.perf_counter()
    for _ in range(train_size):
        episode = make_episode(rng, rng.choice(train_kinds), True)
        model.learn(episode["text"], episode["target"])
    training_seconds = time.perf_counter() - started

    result: dict[str, object] = {}
    eval_kinds = [
        "literal",
        "quote",
        "negation",
        "correction",
        "nested",
        "paragraph",
        "plan",
        "ambiguous",
        "held_scope",
        "held_retraction",
    ]
    for kind in eval_kinds:
        rows = [make_episode(rng, kind, True) for _ in range(160)]
        recall = immediate = active = wrong = 0
        candidate_counts: list[int] = []
        probe_counts: list[int] = []
        timings: list[float] = []
        for episode in rows:
            start = time.perf_counter()
            ranked = model.rank(episode["text"])
            candidate_counts.append(len(ranked))
            recall += any(
                candidate.value == episode["target"] for candidate in ranked
            )
            predicted = ranked[0].value if ranked else None
            immediate += predicted == episode["target"]
            wrong += predicted is not None and predicted != episode["target"]
            active_prediction, probes = active_resolve(
                model, episode["text"], episode["target"]
            )
            active += active_prediction == episode["target"]
            probe_counts.append(probes)
            timings.append((time.perf_counter() - start) * 1000)
        result[kind] = {
            "candidate_recall": recall / len(rows),
            "immediate_accuracy": immediate / len(rows),
            "active_accuracy": active / len(rows),
            "wrong_commit_rate": wrong / len(rows),
            "mean_candidates": statistics.mean(candidate_counts),
            "mean_probes": statistics.mean(probe_counts),
            "ms_per_example": statistics.mean(timings),
        }

    # Unmarked raw-Japanese gate.
    rows = [
        make_episode(
            rng,
            rng.choice(
                [
                    "literal",
                    "quote",
                    "negation",
                    "correction",
                    "nested",
                    "paragraph",
                    "plan",
                ]
            ),
            False,
        )
        for _ in range(240)
    ]
    recall = accuracy = 0
    for episode in rows:
        ranked = model.rank(episode["text"])
        recall += any(
            candidate.value == episode["target"] for candidate in ranked
        )
        predicted = ranked[0].value if ranked else None
        accuracy += predicted == episode["target"]
    result["unmarked"] = {
        "candidate_recall": recall / len(rows),
        "immediate_accuracy": accuracy / len(rows),
    }
    result["model_bytes"] = len(pickle.dumps(model))
    result["training_seconds"] = training_seconds
    result["weights"] = model.weights
    return result


def summarize(raw: dict[str, list[dict[str, object]]]) -> dict[str, object]:
    output: dict[str, object] = {}
    eval_kinds = [
        "literal",
        "quote",
        "negation",
        "correction",
        "nested",
        "paragraph",
        "plan",
        "ambiguous",
        "held_scope",
        "held_retraction",
    ]
    for train_size, runs in raw.items():
        aggregate: dict[str, object] = {}
        for kind in eval_kinds:
            metrics: dict[str, float] = {}
            first = runs[0][kind]
            assert isinstance(first, dict)
            for key in first:
                metrics[key] = statistics.mean(
                    float(run[kind][key]) for run in runs  # type: ignore[index]
                )
            aggregate[kind] = metrics
        aggregate["unmarked"] = {
            key: statistics.mean(
                float(run["unmarked"][key]) for run in runs  # type: ignore[index]
            )
            for key in runs[0]["unmarked"]  # type: ignore[union-attr]
        }
        for key in ("model_bytes", "training_seconds"):
            aggregate[key] = statistics.mean(float(run[key]) for run in runs)
        aggregate["weights"] = [
            statistics.mean(float(run["weights"][index]) for run in runs)  # type: ignore[index]
            for index in range(6)
        ]
        output[train_size] = aggregate
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results_cycle_010.json")
    args = parser.parse_args()
    raw = {
        str(train_size): [evaluate(seed, train_size) for seed in (1, 7, 19)]
        for train_size in (64, 256, 1024)
    }
    payload = {
        "hypothesis": (
            "Scope-Fork Predictive Programs with Counterfactual Evidence Scheduling"
        ),
        "seeds": [1, 7, 19],
        "train_sizes": [64, 256, 1024],
        "raw": raw,
        "summary": summarize(raw),
        "generic_probe_reveals_target_value": False,
        "estimated_complexity": (
            "proposal O(L), rank O(HF), active O(min(H,4)); H<=4 in benchmark"
        ),
        "peak_rss_kib_runtime_included": resource.getrusage(
            resource.RUSAGE_SELF
        ).ru_maxrss,
        "free_japanese_integrated_gate": 0.0,
        "highschool_level_passed": False,
        "native_japanese_communication_passed": False,
        "weak_smartphone_verified": False,
        "completion": False,
    }
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    print(json.dumps(payload["summary"]["1024"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
