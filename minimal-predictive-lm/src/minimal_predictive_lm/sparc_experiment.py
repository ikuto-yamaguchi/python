from __future__ import annotations

import json
import resource
import time
from pathlib import Path

import numpy as np

from .sparc_core import SurprisePropagatedGraph, canonical_code


def _make_codes(
    generator: np.random.Generator,
    *,
    concepts: int,
    code_space: int,
    active_bits: int,
) -> list[tuple[int, ...]]:
    codes: list[tuple[int, ...]] = []
    seen: set[tuple[int, ...]] = set()
    while len(codes) < concepts:
        code = tuple(sorted(int(value) for value in generator.choice(code_space, active_bits, replace=False)))
        if code not in seen:
            seen.add(code)
            codes.append(code)
    return codes


def _noisy_code(
    generator: np.random.Generator,
    code: tuple[int, ...],
    *,
    code_space: int,
    replacements: int = 2,
) -> tuple[int, ...]:
    values = set(code)
    removed = generator.choice(tuple(values), replacements, replace=False)
    values.difference_update(int(value) for value in removed)
    while len(values) < len(code):
        candidate = int(generator.integers(code_space))
        values.add(candidate)
    return tuple(sorted(values))


def run_experiment(output: str | Path | None = None) -> dict[str, object]:
    start = time.perf_counter()
    generator = np.random.default_rng(20260716)
    concepts = 256
    cycles = 400
    code_space = 4096
    active_bits = 16
    observations = concepts * cycles
    codes = _make_codes(
        generator,
        concepts=concepts,
        code_space=code_space,
        active_bits=active_bits,
    )
    payloads = [f"concept-{index:03d}" for index in range(concepts)]

    graph = SurprisePropagatedGraph(
        code_space=code_space,
        active_bits=active_bits,
        familiarity_threshold=0.55,
        max_degree=4,
    )
    payload_correct = 0
    transition_correct = 0
    transition_scored = 0
    post_warmup = 0
    post_warmup_writes = 0

    for cycle in range(cycles):
        for index, (code, payload) in enumerate(zip(codes, payloads)):
            observed_code = code if cycle == 0 else _noisy_code(
                generator,
                code,
                code_space=code_space,
                replacements=2,
            )
            step = graph.observe(observed_code, payload)
            if cycle >= 2:
                post_warmup += 1
                payload_correct += int(step.payload_correct)
                if step.transition_correct is not None:
                    transition_scored += 1
                    transition_correct += int(step.transition_correct)
                post_warmup_writes += int(step.wrote)

    recall_correct = 0
    recall_candidates: list[int] = []
    for code, payload in zip(codes, payloads):
        recalled, _similarity, candidates = graph.recall(code)
        recall_correct += int(recalled == payload)
        recall_candidates.append(candidates)

    simulated = graph.simulate(codes[37], 12)
    expected_path = tuple((37 + offset) % concepts for offset in range(12))
    transition_path_correct = simulated == expected_path

    artifact = graph.to_bytes()
    restored = SurprisePropagatedGraph.from_bytes(artifact)
    restored_recall = restored.recall(codes[103])[0]
    report = graph.report()

    # Conservative software-independent accounting. A sparse lookup compares
    # active-bit overlap only for posting-list candidates. A full concept scan
    # compares every active bit against every concept. A history cache stores
    # every observation's sparse key and payload identifier.
    mean_candidates = float(np.mean(recall_candidates))
    sparc_routine_overlap_ops = mean_candidates * active_bits
    full_concept_scan_overlap_ops = concepts * active_bits
    history_cache_bytes = observations * (active_bits * 2 + 4)
    sacs_dense_read_ops = 2 * 32 * 64 + 2 * 1 * 32 * 64

    result: dict[str, object] = {
        "capability_id": "SPARC-001-EVENT-GRAPH",
        "architecture": "surprise-propagated active relational cognition",
        "observations": observations,
        "distinct_concepts": concepts,
        "noise_replacements_per_event": 2,
        "post_warmup": {
            "observations": post_warmup,
            "payload_prediction_accuracy": payload_correct / post_warmup,
            "transition_prediction_accuracy": (
                transition_correct / transition_scored if transition_scored else 0.0
            ),
            "write_fraction": post_warmup_writes / post_warmup,
        },
        "associative_recall": {
            "correct": recall_correct,
            "total": concepts,
            "accuracy": recall_correct / concepts,
            "mean_candidates_inspected": mean_candidates,
            "max_candidates_inspected": max(recall_candidates),
        },
        "relational_simulation": {
            "steps": 12,
            "path_correct": transition_path_correct,
            "predicted_path": simulated,
            "expected_path": expected_path,
        },
        "sparc": {
            **report.__dict__,
            "artifact_roundtrip_correct": restored_recall == payloads[103],
            "routine_overlap_operations": sparc_routine_overlap_ops,
        },
        "comparisons": {
            "full_concept_scan_overlap_operations": full_concept_scan_overlap_ops,
            "full_history_sparse_cache_bytes": history_cache_bytes,
            "sacs_dense_read_multiply_adds": sacs_dense_read_ops,
            "candidate_reduction_vs_full_scan": (
                full_concept_scan_overlap_ops / sparc_routine_overlap_ops
                if sparc_routine_overlap_ops
                else 0.0
            ),
            "state_reduction_vs_history_cache": (
                history_cache_bytes / len(artifact) if artifact else 0.0
            ),
            "routine_op_reduction_vs_sacs": (
                sacs_dense_read_ops / sparc_routine_overlap_ops
                if sparc_routine_overlap_ops
                else 0.0
            ),
        },
        "event_driven": True,
        "global_parameter_scan_used": False,
        "history_scan_used": False,
        "backpropagation_used": False,
        "softmax_attention_used": False,
        "elapsed_seconds": time.perf_counter() - start,
        "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "claim_boundary": (
            "SPARC-001 validates event-indexed predictive memory on a repeated noisy latent process. The event codes "
            "are supplied rather than learned from Japanese, so this is not yet a language model or evidence of "
            "high-school-level intelligence. The next gate must learn the event compiler and renderer."
        ),
    }
    result["passed"] = bool(
        result["post_warmup"]["payload_prediction_accuracy"] >= 0.995
        and result["post_warmup"]["transition_prediction_accuracy"] >= 0.995
        and result["post_warmup"]["write_fraction"] <= 0.01
        and result["associative_recall"]["accuracy"] == 1.0
        and transition_path_correct
        and report.nodes <= concepts * 1.02
        and report.write_fraction <= 0.02
        and mean_candidates <= 24.0
        and len(artifact) <= 100_000
        and result["comparisons"]["candidate_reduction_vs_full_scan"] >= 8.0
        and result["comparisons"]["routine_op_reduction_vs_sacs"] >= 8.0
        and result["peak_process_kib"] <= 250_000
    )
    if output is not None:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        path.with_suffix(".sparc").write_bytes(artifact)
    return result


def main() -> None:
    print(json.dumps(run_experiment("results/sparc_001_event_graph.json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
