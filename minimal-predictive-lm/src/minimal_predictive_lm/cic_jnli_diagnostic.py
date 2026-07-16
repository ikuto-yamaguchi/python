from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import math
import random
import re
import resource
import time
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from .cic_choice_data import ChoiceExample, JNLI_OPTIONS, load_choice_dataset, stable_choice_split

NEGATIONS = ("ない", "ません", "ぬ", "ず", "無い", "なく", "なかった")
NUMBER_RE = re.compile(r"[0-9０-９]+")


@dataclass(frozen=True)
class DiagnosticConfig:
    name: str
    include_premise: bool
    include_hypothesis: bool
    include_diff: bool
    include_cross: bool


CONFIGS = (
    DiagnosticConfig("hypothesis_only", False, True, False, False),
    DiagnosticConfig("fielded_bag", True, True, False, False),
    DiagnosticConfig("structural_diff", False, False, True, True),
    DiagnosticConfig("fielded_diff", True, True, True, True),
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _parse_pair(row: ChoiceExample) -> tuple[str, str]:
    marker = "\n仮説："
    if not row.stem.startswith("前提：") or marker not in row.stem:
        raise ValueError("row is not a JNLI premise/hypothesis pair")
    premise, hypothesis = row.stem[len("前提：") :].split(marker, 1)
    return _normalize(premise), _normalize(hypothesis)


def _ngrams(text: str, widths: Iterable[int]) -> list[str]:
    result: list[str] = []
    for width in widths:
        result.extend(text[index : index + width] for index in range(max(0, len(text) - width + 1)))
    return result


def _spread(items: Sequence[str], limit: int) -> list[str]:
    if len(items) <= limit:
        return list(items)
    if limit == 1:
        return [items[len(items) // 2]]
    return [items[(index * (len(items) - 1)) // (limit - 1)] for index in range(limit)]


def _bin(value: float, bins: int = 20) -> int:
    return max(0, min(bins, int(round(value * bins))))


def _prefix_length(left: str, right: str) -> int:
    count = 0
    for a, b in zip(left, right):
        if a != b:
            break
        count += 1
    return count


def _suffix_length(left: str, right: str) -> int:
    return _prefix_length(left[::-1], right[::-1])


def _pair_tokens(row: ChoiceExample, config: DiagnosticConfig) -> list[str]:
    premise, hypothesis = _parse_pair(row)
    tokens: list[str] = ["BIAS"]

    premise_ngrams = _ngrams(premise, (1, 2, 3))
    hypothesis_ngrams = _ngrams(hypothesis, (1, 2, 3))
    if config.include_premise:
        tokens.extend("P:" + token for token in _spread(premise_ngrams, 180))
    if config.include_hypothesis:
        tokens.extend("H:" + token for token in _spread(hypothesis_ngrams, 180))

    p2 = set(_ngrams(premise, (2,)))
    h2 = set(_ngrams(hypothesis, (2,)))
    union = len(p2 | h2)
    jaccard = len(p2 & h2) / union if union else 1.0
    containment_p = len(p2 & h2) / len(p2) if p2 else 1.0
    containment_h = len(p2 & h2) / len(h2) if h2 else 1.0
    tokens.extend(
        (
            f"LENP:{min(20, len(premise) // 5)}",
            f"LENH:{min(20, len(hypothesis) // 5)}",
            f"LEND:{max(-20, min(20, (len(hypothesis) - len(premise)) // 3))}",
            f"J2:{_bin(jaccard)}",
            f"CP:{_bin(containment_p)}",
            f"CH:{_bin(containment_h)}",
            f"PREFIX:{min(12, _prefix_length(premise, hypothesis) // 2)}",
            f"SUFFIX:{min(12, _suffix_length(premise, hypothesis) // 2)}",
            f"EXACT:{premise == hypothesis}",
            f"P_IN_H:{premise in hypothesis}",
            f"H_IN_P:{hypothesis in premise}",
        )
    )

    p_neg = tuple(marker for marker in NEGATIONS if marker in premise)
    h_neg = tuple(marker for marker in NEGATIONS if marker in hypothesis)
    tokens.extend(
        (
            f"PNEG:{bool(p_neg)}",
            f"HNEG:{bool(h_neg)}",
            f"NEGMISMATCH:{bool(p_neg) != bool(h_neg)}",
            f"NEGPAIR:{','.join(p_neg)}=>{','.join(h_neg)}",
        )
    )
    p_numbers = tuple(NUMBER_RE.findall(premise))
    h_numbers = tuple(NUMBER_RE.findall(hypothesis))
    tokens.extend(
        (
            f"PNUM:{bool(p_numbers)}",
            f"HNUM:{bool(h_numbers)}",
            f"NUMSAME:{p_numbers == h_numbers}",
            f"NUMPAIR:{','.join(p_numbers)}=>{','.join(h_numbers)}",
        )
    )

    if config.include_diff:
        matcher = difflib.SequenceMatcher(a=premise, b=hypothesis, autojunk=False)
        opcodes = matcher.get_opcodes()
        tokens.append("OPS:" + ",".join(tag for tag, *_rest in opcodes))
        tokens.append(f"RATIO:{_bin(matcher.ratio())}")
        tokens.append(f"OPCOUNT:{min(12, len(opcodes))}")
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == "equal":
                continue
            removed = premise[i1:i2]
            added = hypothesis[j1:j2]
            tokens.extend(
                (
                    f"OP:{tag}",
                    f"OPLEN:{tag}:{min(12, len(removed))}:{min(12, len(added))}",
                )
            )
            removed_parts = _spread(_ngrams(removed, (1, 2, 3)), 18)
            added_parts = _spread(_ngrams(added, (1, 2, 3)), 18)
            tokens.extend("REM:" + token for token in removed_parts)
            tokens.extend("ADD:" + token for token in added_parts)
            if config.include_cross:
                for left in removed_parts[:12]:
                    for right in added_parts[:12]:
                        tokens.append("X:" + left + "=>" + right)

    return tokens


@lru_cache(maxsize=500_000)
def _hash_token(token: str, dimensions: int) -> tuple[int, float]:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    code = int.from_bytes(digest, "little")
    return code % dimensions, 1.0 if code >> 63 else -1.0


def _vectorize(row: ChoiceExample, config: DiagnosticConfig, dimensions: int) -> tuple[np.ndarray, np.ndarray]:
    values: Counter[int] = Counter()
    for token in _pair_tokens(row, config):
        index, sign = _hash_token(token, dimensions)
        values[index] += sign
    if not values:
        return np.empty(0, dtype=np.int32), np.empty(0, dtype=np.float32)
    indices = np.fromiter(values.keys(), dtype=np.int32)
    vector = np.fromiter(values.values(), dtype=np.float32)
    norm = float(np.linalg.norm(vector))
    if norm:
        vector /= norm
    return indices, vector


@dataclass
class PairClassifier:
    weights: np.ndarray
    config: DiagnosticConfig
    dimensions: int

    def predict(self, row: ChoiceExample) -> int:
        indices, values = _vectorize(row, self.config, self.dimensions)
        scores = self.weights[:, indices] @ values if len(indices) else np.zeros(len(JNLI_OPTIONS))
        return int(np.argmax(scores))


def train_classifier(
    rows: Sequence[ChoiceExample],
    config: DiagnosticConfig,
    *,
    dimensions: int = 65536,
    epochs: int = 3,
    aggressiveness: float = 0.20,
    seed: int = 0,
) -> PairClassifier:
    weights = np.zeros((len(JNLI_OPTIONS), dimensions), dtype=np.float32)
    totals = np.zeros_like(weights, dtype=np.float64)
    timestamps = np.zeros_like(weights, dtype=np.int64)
    generator = random.Random(seed)
    step = 0
    for _epoch in range(epochs):
        order = list(range(len(rows)))
        generator.shuffle(order)
        for row_index in order:
            step += 1
            row = rows[row_index]
            indices, values = _vectorize(row, config, dimensions)
            if not len(indices):
                continue
            scores = weights[:, indices] @ values
            gold = row.answer_index
            strongest_wrong = max((index for index in range(len(scores)) if index != gold), key=lambda index: scores[index])
            margin = float(scores[gold] - scores[strongest_wrong])
            if margin >= 1.0:
                continue
            squared_norm = 2.0 * float(values @ values)
            tau = min(aggressiveness, (1.0 - margin) / (squared_norm + 1e-12))
            for label, direction in ((gold, 1.0), (strongest_wrong, -1.0)):
                totals[label, indices] += (step - timestamps[label, indices]) * weights[label, indices]
                timestamps[label, indices] = step
                weights[label, indices] += direction * tau * values
    if step:
        totals += (step + 1 - timestamps) * weights
        weights = (totals / (step + 1)).astype(np.float32)
    return PairClassifier(weights, config, dimensions)


def evaluate(model: PairClassifier, rows: Sequence[ChoiceExample]) -> dict[str, object]:
    confusion = np.zeros((len(JNLI_OPTIONS), len(JNLI_OPTIONS)), dtype=np.int64)
    for row in rows:
        confusion[row.answer_index, model.predict(row)] += 1
    correct = int(np.trace(confusion))
    total = int(confusion.sum())
    return {
        "correct": correct,
        "total": total,
        "accuracy": correct / total if total else 0.0,
        "prediction_distribution": {
            JNLI_OPTIONS[index]: int(confusion[:, index].sum()) for index in range(len(JNLI_OPTIONS))
        },
        "confusion_gold_rows_pred_columns": confusion.tolist(),
    }


def label_distribution(rows: Sequence[ChoiceExample]) -> dict[str, int]:
    counts = Counter(row.answer_index for row in rows)
    return {label: counts[index] for index, label in enumerate(JNLI_OPTIONS)}


def run_diagnostic(train_path: str | Path, valid_path: str | Path, output: str | Path | None = None) -> dict[str, object]:
    start = time.perf_counter()
    train_rows = load_choice_dataset(train_path)
    valid_rows = load_choice_dataset(valid_path)
    inner_train, inner_valid = stable_choice_split(train_rows, test_threshold=1500, namespace="jnli-diagnostic:")

    inner_scores: dict[str, dict[str, object]] = {}
    for config in CONFIGS:
        model = train_classifier(inner_train, config)
        inner_scores[config.name] = evaluate(model, inner_valid)
    selected = max(CONFIGS, key=lambda config: (float(inner_scores[config.name]["accuracy"]), -CONFIGS.index(config)))
    final_model = train_classifier(train_rows, selected)
    valid_result = evaluate(final_model, valid_rows)

    valid_counts = label_distribution(valid_rows)
    majority = max(valid_counts.values()) / len(valid_rows) if valid_rows else 0.0
    result: dict[str, object] = {
        "capability_id": "CIC-007-JNLI-DIAGNOSTIC",
        "train_rows": len(train_rows),
        "valid_rows": len(valid_rows),
        "train_label_distribution": label_distribution(train_rows),
        "valid_label_distribution": valid_counts,
        "inner_train_rows": len(inner_train),
        "inner_valid_rows": len(inner_valid),
        "inner_variant_results": inner_scores,
        "selected_variant": selected.name,
        "official_valid": valid_result,
        "majority_accuracy": majority,
        "gain_over_majority": float(valid_result["accuracy"]) - majority,
        "elapsed_seconds": time.perf_counter() - start,
        "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    result["passed"] = bool(float(valid_result["accuracy"]) > majority)
    if output is not None:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose compact JNLI pair representations")
    parser.add_argument("train")
    parser.add_argument("valid")
    parser.add_argument("--output", default="results/cic_007_jnli_diagnostic.json")
    args = parser.parse_args()
    print(json.dumps(run_diagnostic(args.train, args.valid, args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
