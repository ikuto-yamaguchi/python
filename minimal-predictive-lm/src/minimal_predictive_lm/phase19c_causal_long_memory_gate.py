from __future__ import annotations

from collections import Counter, defaultdict, deque
from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

from .phase19a_general_learning_reality_gate import (
    CorpusFile,
    NgramModel,
    collect_corpus,
    encode,
    evaluate_model,
    learn_merges,
    train_ngram,
)

CONTEXT_LENGTHS = (4, 8, 16, 32)
SHORT_WINDOW = 64
LONG_WINDOW = 4096
CONFIDENCES = (0.0, 0.25, 0.5, 0.75)
MIN_SUPPORTS = (1, 2)


@dataclass(frozen=True)
class MemoryConfig:
    window: int
    confidence: float
    minimum_support: int


@dataclass(frozen=True)
class MemoryMetrics:
    bits: float
    bytes: int
    memory_predictions: int
    memory_correct: int
    by_domain_bits: Mapping[str, float]
    by_domain_bytes: Mapping[str, int]


def base_probability(
    model: NgramModel, history: Sequence[int], token: int
) -> float:
    context = tuple(history[-(model.order - 1) :]) if model.order > 1 else ()
    counts = model.contexts.get(context)
    total = model.totals.get(context, 0)
    count = 0 if counts is None else counts.get(token, 0)
    return (count + model.alpha) / (
        total + model.alpha * model.vocabulary_size
    )


def memory_file_token_bits(
    model: NgramModel,
    sequence: Sequence[int],
    config: MemoryConfig,
):
    histories = {length: defaultdict(deque) for length in CONTEXT_LENGTHS}
    prefix: list[int] = []
    token_bits: list[float] = []
    used = 0
    correct = 0
    for position, token in enumerate(sequence):
        base = base_probability(model, prefix, token)
        prediction = None
        if config.confidence > 0:
            for length in reversed(CONTEXT_LENGTHS):
                if len(prefix) < length:
                    continue
                context = tuple(prefix[-length:])
                entries = histories[length].get(context)
                if not entries:
                    continue
                cutoff = position - config.window
                while entries and entries[0][0] < cutoff:
                    entries.popleft()
                if len(entries) < config.minimum_support:
                    continue
                counts = Counter(next_token for _, next_token in entries)
                if len(counts) == 1:
                    prediction = next(iter(counts))
                    break
        if prediction is None:
            probability = base
        else:
            used += 1
            if prediction == token:
                correct += 1
            probability = (1 - config.confidence) * base + config.confidence * (
                1.0 if prediction == token else 0.0
            )
        token_bits.append(-math.log2(max(probability, 1e-300)))
        for length in CONTEXT_LENGTHS:
            if len(prefix) >= length:
                context = tuple(prefix[-length:])
                histories[length][context].append((position, token))
        prefix.append(token)
    return tuple(token_bits), used, correct


def memory_file_bits(
    model: NgramModel,
    sequence: Sequence[int],
    config: MemoryConfig,
):
    token_bits, used, correct = memory_file_token_bits(model, sequence, config)
    return sum(token_bits), used, correct


def evaluate_memory(
    model: NgramModel,
    files: Sequence[CorpusFile],
    merges,
    config: MemoryConfig,
) -> MemoryMetrics:
    total_bits = 0.0
    total_bytes = 0
    used = 0
    correct = 0
    by_bits: Counter[str] = Counter()
    by_bytes: Counter[str] = Counter()
    for row in files:
        bits, memory_used, memory_correct = memory_file_bits(
            model, encode(row.data, merges), config
        )
        total_bits += bits
        total_bytes += len(row.data)
        used += memory_used
        correct += memory_correct
        by_bits[row.domain] += bits
        by_bytes[row.domain] += len(row.data)
    return MemoryMetrics(
        total_bits,
        total_bytes,
        used,
        correct,
        dict(by_bits),
        dict(by_bytes),
    )


def bpb(metrics: MemoryMetrics) -> float:
    return metrics.bits / metrics.bytes


def calibration_split(train: Sequence[CorpusFile]):
    ordered = tuple(sorted(train, key=lambda row: row.rank))
    calibration = tuple(
        row for index, row in enumerate(ordered) if index % 5 == 0
    )
    core = tuple(row for index, row in enumerate(ordered) if index % 5 != 0)
    if not core or not calibration:
        raise ValueError("empty calibration split")
    return core, calibration


def choose_config(
    model: NgramModel,
    files: Sequence[CorpusFile],
    merges,
    window: int,
):
    candidates = []
    for confidence in CONFIDENCES:
        for support in MIN_SUPPORTS:
            config = MemoryConfig(window, confidence, support)
            metrics = evaluate_memory(model, files, merges, config)
            candidates.append(
                (bpb(metrics), confidence, support, config, metrics)
            )
    return min(candidates, key=lambda row: (row[0], row[1], row[2]))


def metrics_dict(metrics: MemoryMetrics, dictionary_bits: int = 0):
    return {
        "heldout_bytes": metrics.bytes,
        "likelihood_bits_per_byte": bpb(metrics),
        "dictionary_amortized_bits_per_byte": (
            metrics.bits + dictionary_bits
        )
        / metrics.bytes,
        "memory_predictions": metrics.memory_predictions,
        "memory_correct": metrics.memory_correct,
        "memory_precision": (
            metrics.memory_correct / metrics.memory_predictions
            if metrics.memory_predictions
            else 0.0
        ),
        "domain_bits_per_byte": {
            domain: metrics.by_domain_bits[domain]
            / metrics.by_domain_bytes[domain]
            for domain in sorted(metrics.by_domain_bytes)
        },
        "domain_bytes": dict(sorted(metrics.by_domain_bytes.items())),
    }


def run_gate(root: Path):
    train, heldout = collect_corpus(root)
    core, calibration = calibration_split(train)
    calibration_merges = learn_merges(core)
    calibration_model = train_ngram(
        [encode(row.data, calibration_merges) for row in core],
        order=3,
        vocabulary_size=256 + len(calibration_merges),
    )
    short_choice = choose_config(
        calibration_model,
        calibration,
        calibration_merges,
        SHORT_WINDOW,
    )
    long_choice = choose_config(
        calibration_model,
        calibration,
        calibration_merges,
        LONG_WINDOW,
    )

    merges = learn_merges(train)
    model = train_ngram(
        [encode(row.data, merges) for row in train],
        order=3,
        vocabulary_size=256 + len(merges),
    )
    base_metrics = evaluate_model(model, heldout, merges)
    short_metrics = evaluate_memory(model, heldout, merges, short_choice[3])
    long_metrics = evaluate_memory(model, heldout, merges, long_choice[3])
    dictionary_bits = int(base_metrics["dictionary_bits"])
    short = metrics_dict(short_metrics, dictionary_bits)
    long = metrics_dict(long_metrics, dictionary_bits)
    base_bpb = float(base_metrics["dictionary_amortized_bits_per_byte"])
    short_bpb = float(short["dictionary_amortized_bits_per_byte"])
    long_bpb = float(long["dictionary_amortized_bits_per_byte"])
    domain_long_wins = sum(
        long["domain_bits_per_byte"][domain]
        < short["domain_bits_per_byte"][domain]
        for domain in long["domain_bits_per_byte"]
    )
    checks = {
        "calibration_is_file_disjoint": pairwise_file_disjoint(
            core, calibration, heldout
        ),
        "future_suffix_cannot_change_prefix": causal_invariance_probe(
            model, merges, long_choice[3]
        ),
        "long_memory_beats_base": long_bpb < base_bpb,
        "long_memory_beats_short": long_bpb < short_bpb,
        "long_memory_wins_at_least_two_domains": domain_long_wins >= 2,
        "memory_precision_above_chance": long["memory_precision"] > 0.75,
        "long_range_synthetic_dependency": synthetic_long_range_probe(),
    }
    return {
        "campaign": "phase19c_causal_long_memory_gate",
        "claim": "causal prefix-memory compression only",
        "train_files": len(train),
        "heldout_files": len(heldout),
        "calibration_files": len(calibration),
        "short_config": vars(short_choice[3]),
        "long_config": vars(long_choice[3]),
        "calibration_short_bpb": short_choice[0],
        "calibration_long_bpb": long_choice[0],
        "base": base_metrics,
        "short_memory": short,
        "long_memory": long,
        "long_vs_base_gain": base_bpb - long_bpb,
        "long_vs_short_gain": short_bpb - long_bpb,
        "domain_long_wins": domain_long_wins,
        "checks": checks,
        "passed": all(checks.values()),
        "online_heldout_adaptation": True,
        "semantic_understanding": False,
        "high_school_intelligence": False,
        "general_llm_parity": False,
    }


def pairwise_file_disjoint(*groups):
    path_sets = [{row.path for row in group} for group in groups]
    return all(
        not (left & right)
        for index, left in enumerate(path_sets)
        for right in path_sets[index + 1 :]
    )


def causal_invariance_probe(model, merges, config):
    del merges
    prefix = (65, 66, 67, 65, 66, 67, 65, 66, 68, 69, 70)
    suffix = (71, 72, 73, 74, 75, 76)
    first, _, _ = memory_file_token_bits(model, prefix, config)
    extended, _, _ = memory_file_token_bits(model, prefix + suffix, config)
    return first == extended[: len(prefix)]


def synthetic_long_range_probe():
    vocabulary_size = 258
    model = train_ngram(
        [tuple(b"abc xyz abc xyz")], order=3, vocabulary_size=vocabulary_size
    )
    block = tuple(range(20, 50))
    sequence = block + tuple([7] * 100) + block
    short = MemoryConfig(64, 0.75, 1)
    long = MemoryConfig(4096, 0.75, 1)
    short_bits, _, _ = memory_file_bits(model, sequence, short)
    long_bits, _, _ = memory_file_bits(model, sequence, long)
    return long_bits < short_bits


def render_markdown(result):
    lines = [
        "# Phase 19c: causal long-memory gate",
        "",
        f"Passed: **{result['passed']}**",
        "",
        "| model | bpb | memory uses | precision |",
        "|---|---:|---:|---:|",
    ]
    for key, label in (
        ("base", "base trigram"),
        ("short_memory", "64-token memory"),
        ("long_memory", "4096-token memory"),
    ):
        row = result[key]
        lines.append(
            f"| {label} | {row['dictionary_amortized_bits_per_byte']:.4f} | "
            f"{row.get('memory_predictions', 0)} | "
            f"{row.get('memory_precision', 0):.3f} |"
        )
    lines.extend(
        [
            "",
            f"Long vs base gain: **{result['long_vs_base_gain']:.4f} bpb**",
            f"Long vs short gain: **{result['long_vs_short_gain']:.4f} bpb**",
            "",
            "## Checks",
            "",
        ]
    )
    for name, value in result["checks"].items():
        lines.append(f"- {name}: **{value}**")
    lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            "- Memory reads only the already observed prefix of each held-out file.",
            "- Configuration selection uses training calibration files, not held-out files.",
            "- This is online compression adaptation, not semantic reasoning or high-school intelligence.",
        ]
    )
    return "\n".join(lines) + "\n"


def main():
    root = Path(__file__).resolve().parents[2]
    result = run_gate(root)
    results_dir = root / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "phase19c.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (results_dir / "phase19c.md").write_text(
        render_markdown(result), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
