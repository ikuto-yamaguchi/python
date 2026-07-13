from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence

from .phase19a_general_learning_reality_gate import (
    CorpusFile,
    Merge,
    NgramModel,
    collect_corpus,
    encode,
    learn_merges,
    nested_training_slice,
    train_ngram,
)


@dataclass(frozen=True)
class SpanTask:
    path: str
    domain: str
    left: bytes
    target: bytes
    right: bytes
    candidates: tuple[bytes, ...]


def _rank_bytes(payload: bytes) -> int:
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _eligible_windows(row: CorpusFile, *, span_bytes: int, context_bytes: int) -> tuple[tuple[bytes, bytes, bytes], ...]:
    data = row.data
    if len(data) < context_bytes * 2 + span_bytes:
        return ()
    starts: list[int] = []
    for index in range(len(data) - span_bytes):
        if index < context_bytes or index + span_bytes + context_bytes > len(data):
            continue
        if index == 0 or data[index - 1] in b"\n\r\t ,:;()[]{}=+-*/<>\"'":
            starts.append(index)
    if not starts:
        starts = list(range(context_bytes, len(data) - span_bytes - context_bytes + 1, max(span_bytes, 16)))
    windows = []
    for start in starts:
        target = data[start : start + span_bytes]
        if len(set(target)) <= 1:
            continue
        left = data[start - context_bytes : start]
        right = data[start + span_bytes : start + span_bytes + context_bytes]
        windows.append((left, target, right))
    windows.sort(key=lambda row_: _rank_bytes(row_[0] + b"\0" + row_[1] + b"\0" + row_[2]))
    return tuple(windows)


def build_span_tasks(
    heldout: Sequence[CorpusFile],
    *,
    span_bytes: int = 8,
    context_bytes: int = 24,
    tasks_per_file: int = 3,
    candidate_count: int = 8,
) -> tuple[SpanTask, ...]:
    windows_by_path = {
        row.path: _eligible_windows(row, span_bytes=span_bytes, context_bytes=context_bytes)
        for row in heldout
    }
    pool_by_domain: dict[str, list[tuple[str, bytes]]] = {}
    ordered_heldout = tuple(sorted(heldout, key=lambda row: (row.rank, row.path)))
    for row in ordered_heldout:
        pool = pool_by_domain.setdefault(row.domain, [])
        for _, target, _ in windows_by_path[row.path]:
            pool.append((row.path, target))
    tasks: list[SpanTask] = []
    for row in ordered_heldout:
        windows = windows_by_path[row.path][:tasks_per_file]
        domain_pool = pool_by_domain.get(row.domain, [])
        for task_index, (left, target, right) in enumerate(windows):
            distractors = {
                candidate
                for source_path, candidate in sorted(
                    domain_pool,
                    key=lambda item: _rank_bytes(
                        row.path.encode("utf-8")
                        + task_index.to_bytes(2, "big")
                        + item[0].encode("utf-8")
                        + item[1]
                    ),
                )
                if source_path != row.path and candidate != target
            }
            ordered_distractors = sorted(
                distractors,
                key=lambda candidate: _rank_bytes(
                    row.path.encode("utf-8") + task_index.to_bytes(2, "big") + candidate
                ),
            )
            if len(ordered_distractors) < candidate_count - 1:
                continue
            candidates = [target, *ordered_distractors[: candidate_count - 1]]
            candidates.sort(
                key=lambda candidate: _rank_bytes(
                    b"candidate-order\0"
                    + row.path.encode("utf-8")
                    + task_index.to_bytes(2, "big")
                    + candidate
                )
            )
            tasks.append(SpanTask(row.path, row.domain, left, target, right, tuple(candidates)))
    tasks.sort(key=lambda task: (task.domain, task.path, _rank_bytes(task.left + task.target + task.right)))
    return tuple(tasks)


def _window_bits(
    model: NgramModel,
    reverse_model: NgramModel,
    merges: Sequence[Merge],
    left: bytes,
    candidate: bytes,
    right: bytes,
) -> float:
    encoded = encode(left + candidate + right, merges)
    return model.bits(encoded) + reverse_model.bits(tuple(reversed(encoded)))


def evaluate_span_tasks(
    tasks: Sequence[SpanTask],
    model: NgramModel,
    reverse_model: NgramModel,
    merges: Sequence[Merge],
) -> Mapping[str, object]:
    correct = 0
    reciprocal_rank = 0.0
    by_domain: dict[str, list[float]] = {}
    ranks: list[int] = []
    margins: list[float] = []
    for task in tasks:
        scored = [
            (_window_bits(model, reverse_model, merges, task.left, candidate, task.right), candidate)
            for candidate in task.candidates
        ]
        scored.sort(key=lambda row: (row[0], row[1]))
        target_rank = next(index + 1 for index, (_, candidate) in enumerate(scored) if candidate == task.target)
        ranks.append(target_rank)
        reciprocal_rank += 1.0 / target_rank
        if target_rank == 1:
            correct += 1
        by_domain.setdefault(task.domain, []).append(1.0 / target_rank)
        if len(scored) > 1:
            target_score = next(score for score, candidate in scored if candidate == task.target)
            best_other = min(score for score, candidate in scored if candidate != task.target)
            margins.append(best_other - target_score)
    task_count = len(tasks)
    return {
        "tasks": task_count,
        "candidate_count": len(tasks[0].candidates) if tasks else 0,
        "top1_accuracy": correct / task_count if task_count else 0.0,
        "mean_reciprocal_rank": reciprocal_rank / task_count if task_count else 0.0,
        "median_rank": sorted(ranks)[len(ranks) // 2] if ranks else None,
        "mean_margin_bits": sum(margins) / len(margins) if margins else 0.0,
        "domain_mrr": {domain: sum(values) / len(values) for domain, values in sorted(by_domain.items())},
        "domain_tasks": {domain: len(values) for domain, values in sorted(by_domain.items())},
    }


def _train_bidirectional(files: Sequence[CorpusFile], merges: Sequence[Merge], *, order: int = 4):
    vocabulary_size = 256 + len(merges)
    sequences = [encode(row.data, merges) for row in files]
    forward = train_ngram(sequences, order=order, vocabulary_size=vocabulary_size)
    backward = train_ngram(
        [tuple(reversed(sequence)) for sequence in sequences],
        order=order,
        vocabulary_size=vocabulary_size,
    )
    return forward, backward


def run_gate(root: Path) -> Mapping[str, object]:
    train, heldout = collect_corpus(root)
    tasks = build_span_tasks(heldout)
    scaling: list[Mapping[str, object]] = []
    for fraction in (0.25, 0.5, 1.0):
        subset = nested_training_slice(train, fraction)
        merges = learn_merges(subset)
        forward, backward = _train_bidirectional(subset, merges)
        scaling.append({
            "fraction": fraction,
            "training_files": len(subset),
            "training_bytes": sum(len(row.data) for row in subset),
            "merges": len(merges),
            **evaluate_span_tasks(tasks, forward, backward, merges),
        })
    raw_forward, raw_backward = _train_bidirectional(train, ())
    raw = evaluate_span_tasks(tasks, raw_forward, raw_backward, ())
    full = scaling[-1]
    mrr = [float(row["mean_reciprocal_rank"]) for row in scaling]
    candidate_count = max(1, int(full["candidate_count"]))
    chance_top1 = 1.0 / candidate_count
    chance_mrr = sum(1.0 / rank for rank in range(1, candidate_count + 1)) / candidate_count
    domain_mrr = {str(key): float(value) for key, value in full["domain_mrr"].items()}
    checks = {
        "enough_file_disjoint_tasks": len(tasks) >= 48,
        "all_domains_represented": {"code", "prose", "structured"}.issubset(domain_mrr),
        "candidate_choice_is_nontrivial": candidate_count >= 8,
        "full_model_beats_chance_top1": float(full["top1_accuracy"]) >= chance_top1 + 0.05,
        "full_model_beats_chance_mrr": float(full["mean_reciprocal_rank"]) >= chance_mrr + 0.03,
        "scaling_does_not_reverse": mrr[2] + 0.02 >= mrr[1] and mrr[1] + 0.02 >= mrr[0],
        "dictionary_model_beats_raw_mrr": float(full["mean_reciprocal_rank"]) >= float(raw["mean_reciprocal_rank"]) + 0.005,
        "at_least_two_domains_above_chance": sum(value >= chance_mrr + 0.02 for value in domain_mrr.values()) >= 2,
        "heldout_is_file_disjoint": not ({row.path for row in train} & {row.path for row in heldout}),
    }
    return {
        "campaign": "phase19b_cross_file_span_reconstruction_gate",
        "claim": "self-supervised file-disjoint contextual span ranking only",
        "train_files": len(train),
        "heldout_files": len(heldout),
        "tasks": len(tasks),
        "chance_top1": chance_top1,
        "chance_mrr": chance_mrr,
        "scaling": scaling,
        "raw_byte_baseline": raw,
        "checks": checks,
        "passed": all(checks.values()),
        "high_school_intelligence": False,
        "general_llm_parity": False,
    }


def render_markdown(result: Mapping[str, object]) -> str:
    lines = [
        "# Phase 19b: cross-file contextual span gate",
        "",
        f"Passed: **{result['passed']}**",
        "",
        "This ranks the true masked byte span against same-domain distractors in entirely held-out files.",
        "It is not a claim of semantic understanding.",
        "",
        "| train fraction | train bytes | tasks | top-1 | MRR |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in result["scaling"]:
        lines.append(
            f"| {row['fraction']:.2f} | {row['training_bytes']} | {row['tasks']} | "
            f"{row['top1_accuracy']:.4f} | {row['mean_reciprocal_rank']:.4f} |"
        )
    raw = result["raw_byte_baseline"]
    lines.extend([
        "",
        f"Raw-byte bidirectional n-gram baseline: top-1 **{raw['top1_accuracy']:.4f}**, MRR **{raw['mean_reciprocal_rank']:.4f}**",
        "",
        "## Domain MRR at full scale",
        "",
    ])
    for domain, value in result["scaling"][-1]["domain_mrr"].items():
        lines.append(f"- {domain}: **{value:.4f}**")
    lines.extend(["", "## Checks", ""])
    for name, value in result["checks"].items():
        lines.append(f"- {name}: **{value}**")
    lines.extend([
        "",
        "## Claim boundary",
        "",
        "- Candidate spans are supplied by the evaluator; the model does not generate arbitrary-length text.",
        "- The corpus is a single repository and remains tiny relative to LLM training.",
        "- Passing shows context-sensitive cross-file prediction, not Japanese high-school intelligence.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    result = run_gate(root)
    results_dir = root / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "phase19b.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (results_dir / "phase19b.md").write_text(render_markdown(result), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
