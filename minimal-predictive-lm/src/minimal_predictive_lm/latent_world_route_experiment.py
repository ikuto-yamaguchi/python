from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import random
import time
from typing import Mapping, Sequence

from .latent_program_learner import (
    GroundedLatentProgramLearner,
    GroundedTransition,
    LatentPlan,
)
from .sparc_latent_program_gate import (
    _OPERATIONS,
    _transition,
    _unlabelled_corpus,
)


@dataclass(frozen=True)
class LatentScaleResult:
    grounded_examples_per_surface: int
    grounded_examples: int
    latent_programs: int
    model_bytes: int
    training_seconds: float
    heldout_plan_accuracy: float
    heldout_coverage: float
    depth2_world_accuracy: float
    depth4_world_accuracy: float
    depth8_world_accuracy: float
    maximum_candidates: int
    maximum_feature_reads: int


def apply_plan(state: Mapping[str, int], plan: LatentPlan) -> dict[str, int]:
    world = {str(key): int(value) for key, value in state.items()}
    if plan.operation == "increase":
        world[plan.target] += plan.value
    elif plan.operation == "decrease":
        world[plan.target] -= plan.value
    elif plan.operation == "assign":
        world[plan.target] = plan.value
    elif plan.operation == "transfer":
        world[plan.target] -= plan.value
        world[plan.destination] += plan.value
    else:
        raise ValueError(f"unsupported latent operation: {plan.operation}")
    return world


def _training_rows(examples_per_surface: int, seed: int) -> tuple[GroundedTransition, ...]:
    rng = random.Random(seed)
    domains = (
        ("倉庫甲", "倉庫乙"),
        ("口座青", "口座赤"),
        ("チーム東", "チーム西"),
        ("資源一", "資源二"),
    )
    rows: list[GroundedTransition] = []
    for operation, (known, _withheld) in _OPERATIONS.items():
        for verb in known:
            for _ in range(examples_per_surface):
                rows.append(_transition(operation, verb, rng.choice(domains), rng))
    rng.shuffle(rows)
    return tuple(rows)


def _heldout_rows(seed: int, per_operation: int = 48) -> tuple[GroundedTransition, ...]:
    rng = random.Random(seed)
    domains = (
        ("温室北", "温室南"),
        ("研究班一", "研究班二"),
        ("得点白", "得点黒"),
        ("電池左", "電池右"),
    )
    rows: list[GroundedTransition] = []
    for operation, (_known, withheld) in _OPERATIONS.items():
        for index in range(per_operation):
            rows.append(_transition(operation, withheld, domains[index % len(domains)], rng))
    rng.shuffle(rows)
    return tuple(rows)


def _event(
    operation: str,
    state: Mapping[str, int],
    amount: int,
    left: str,
    right: str,
) -> GroundedTransition:
    _known, withheld = _OPERATIONS[operation]
    before = dict(state)
    if operation == "increase":
        after = dict(before)
        after[left] += amount
        text = f"{left} を {amount} {withheld}"
    elif operation == "decrease":
        after = dict(before)
        after[left] -= amount
        text = f"{left} から {amount} {withheld}"
    elif operation == "assign":
        after = dict(before)
        after[left] = amount
        text = f"{left} を {amount} に {withheld}"
    else:
        after = dict(before)
        after[left] -= amount
        after[right] += amount
        text = f"{left} から {right} へ {amount} {withheld}"
    return GroundedTransition(text, before, after)


def _composition_accuracy(
    model: GroundedLatentProgramLearner,
    depth: int,
    seed: int,
    episodes: int = 32,
) -> tuple[float, int, int]:
    rng = random.Random(seed)
    operations = tuple(_OPERATIONS)
    correct = 0
    maximum_candidates = 0
    maximum_reads = 0
    for episode in range(episodes):
        left = f"対象{episode}甲"
        right = f"対象{episode}乙"
        expected = {left: 60 + episode, right: 40 + episode}
        predicted = dict(expected)
        solved = True
        for step in range(depth):
            operation = operations[(episode + step) % len(operations)]
            amount = rng.randint(2, 9)
            transition = _event(operation, expected, amount, left, right)
            expected = dict(transition.after)
            result = model.infer(transition.text, predicted)
            maximum_candidates = max(maximum_candidates, result.candidates)
            maximum_reads = max(maximum_reads, result.feature_reads)
            if result.plan is None:
                solved = False
                break
            predicted = apply_plan(predicted, result.plan)
        correct += int(solved and predicted == expected)
    return correct / episodes, maximum_candidates, maximum_reads


def evaluate_scale(examples_per_surface: int, seed: int) -> LatentScaleResult:
    training = _training_rows(examples_per_surface, seed)
    heldout = _heldout_rows(seed + 1)
    model = GroundedLatentProgramLearner()
    started = time.perf_counter()
    programs = model.fit(training, unlabelled_sentences=_unlabelled_corpus())
    training_seconds = time.perf_counter() - started
    correct = 0
    answered = 0
    max_candidates = 0
    max_reads = 0
    for row in heldout:
        result = model.infer(row.text, row.before)
        expected = model.derive_plan(row)
        answered += int(result.plan is not None)
        correct += int(result.plan == expected)
        max_candidates = max(max_candidates, result.candidates)
        max_reads = max(max_reads, result.feature_reads)
    depth2, candidates2, reads2 = _composition_accuracy(model, 2, seed + 2)
    depth4, candidates4, reads4 = _composition_accuracy(model, 4, seed + 3)
    depth8, candidates8, reads8 = _composition_accuracy(model, 8, seed + 4)
    return LatentScaleResult(
        grounded_examples_per_surface=examples_per_surface,
        grounded_examples=len(training),
        latent_programs=programs,
        model_bytes=len(model.to_bytes()),
        training_seconds=training_seconds,
        heldout_plan_accuracy=correct / len(heldout),
        heldout_coverage=answered / len(heldout),
        depth2_world_accuracy=depth2,
        depth4_world_accuracy=depth4,
        depth8_world_accuracy=depth8,
        maximum_candidates=max(max_candidates, candidates2, candidates4, candidates8),
        maximum_feature_reads=max(max_reads, reads2, reads4, reads8),
    )


def run_latent_world_route(output_dir: str | Path) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    scales = [evaluate_scale(value, seed=2100 + value) for value in (1, 4, 16)]

    full_training = _training_rows(16, 991)
    heldout = _heldout_rows(992)
    ablation = GroundedLatentProgramLearner()
    ablation.fit(full_training, unlabelled_sentences=(row.text for row in full_training))
    ablation_correct = sum(
        ablation.infer(row.text, row.before).plan == ablation.derive_plan(row)
        for row in heldout
    ) / len(heldout)

    largest = scales[-1]
    component_checks = {
        "four_reusable_programs_induced_without_operation_labels": largest.latent_programs == 4,
        "withheld_surface_transfer_at_least_80_percent": largest.heldout_plan_accuracy >= 0.80,
        "depth8_composition_at_least_80_percent": largest.depth8_world_accuracy >= 0.80,
        "semantic_context_beats_surface_only_by_20_points": (
            largest.heldout_plan_accuracy - ablation_correct >= 0.20
        ),
        "model_under_one_megabyte": largest.model_bytes <= 1_000_000,
        "bounded_candidates": largest.maximum_candidates <= 8,
        "bounded_feature_reads": largest.maximum_feature_reads <= 1024,
    }
    report = {
        "stage": "latent-world-program-route-001",
        "question": "Can separating surface language from verified latent state transitions create extrapolating reusable procedures that the next-byte cores lacked?",
        "scale_results": [asdict(row) for row in scales],
        "surface_only_ablation_accuracy": ablation_correct,
        "component_checks": component_checks,
        "latent_program_component_go": all(component_checks.values()),
        "route_effect": (
            "retain_as_candidate_reasoning_core"
            if all(component_checks.values())
            else "reject_or_redesign_latent_program_component"
        ),
        "known_missing_links": [
            "autonomous grounding from unrestricted text, images and audio",
            "learning richer programs than the bounded edit algebra",
            "semantic memory that transfers after one exposure",
            "natural language generation and long conversational planning",
            "joint scaling evidence on real Japanese curriculum data",
        ],
        "next_integration_experiment": {
            "architecture": "byte_or_patch_perception -> latent entity/world binder -> reusable program executor -> compressive test-time memory -> language realizer",
            "must_compare": "end-to-end next-byte baseline at equal package bytes and active MACs",
            "falsification": "Reject the hybrid if autonomous grounding or unseen-program transfer remains flat across three scales, even when synthetic execution is perfect.",
        },
        "highschool_level_passed": False,
        "research_gate_passed": True,
    }
    path = output / "latent-world-program-route-001.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run_latent_world_route(args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
