from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import time
from typing import Callable, Sequence

import numpy as np

from .adaptive_recurrent_core import AdaptiveMultiScaleRecurrentCore
from .mobile_sparse_core import (
    MOBILE_1GB_PROFILE,
    MobilePagedSparseCore,
    MobileSparseProfile,
)
from .scalable_recurrent_core import ModelProfile, MultiScaleRecurrentCore


@dataclass(frozen=True)
class RouteScale:
    name: str
    recurrent: ModelProfile
    mobile: MobileSparseProfile


@dataclass(frozen=True)
class RouteMetrics:
    family: str
    scale: str
    model_bytes: int
    active_macs_per_byte: int
    training_seconds: float
    train_nll_before: float
    train_nll_after: float
    train_nll_gain: float
    compositional_transfer_accuracy: float
    long_dependency_accuracy: float
    continual_retention: float
    one_shot_exact_accuracy: float
    one_shot_paraphrase_accuracy: float


@dataclass(frozen=True)
class FamilyVerdict:
    family: str
    scale_points: int
    transfer_slope: float
    long_dependency_slope: float
    retention_at_largest: float
    one_shot_paraphrase_at_largest: float
    monotonic_transfer: bool
    mobile_projection_feasible: bool
    route_go: bool
    failed_requirements: tuple[str, ...]


SCALES = (
    RouteScale(
        "tiny",
        ModelProfile(
            name="route-tiny",
            vocab_buckets=256,
            embedding_dim=8,
            latent_dim=16,
            recurrent_rank=4,
            memory_slots=16,
            memory_key_dim=16,
            memory_value_bytes=32,
            parameter_dtype_bytes=4,
            embedding_dtype_bytes=4,
            memory_dtype_bytes=4,
            optimizer_multiplier=1.0,
        ),
        MobileSparseProfile(
            name="route-mobile-tiny",
            vocab_buckets=256,
            embedding_dim=8,
            coarse_groups=2,
            blocks_per_group=4,
            block_dim=12,
            recurrent_rank=4,
            active_groups=1,
            active_blocks_per_group=1,
            state_cache_blocks=4,
            memory_slots=16,
            memory_key_dim=16,
            memory_value_bytes=32,
            weight_bytes=4,
            state_bytes=4,
        ),
    ),
    RouteScale(
        "small",
        ModelProfile(
            name="route-small",
            vocab_buckets=512,
            embedding_dim=12,
            latent_dim=32,
            recurrent_rank=8,
            memory_slots=32,
            memory_key_dim=24,
            memory_value_bytes=48,
            parameter_dtype_bytes=4,
            embedding_dtype_bytes=4,
            memory_dtype_bytes=4,
            optimizer_multiplier=1.0,
        ),
        MobileSparseProfile(
            name="route-mobile-small",
            vocab_buckets=512,
            embedding_dim=12,
            coarse_groups=4,
            blocks_per_group=4,
            block_dim=20,
            recurrent_rank=4,
            active_groups=1,
            active_blocks_per_group=1,
            state_cache_blocks=8,
            memory_slots=32,
            memory_key_dim=24,
            memory_value_bytes=48,
            weight_bytes=4,
            state_bytes=4,
        ),
    ),
    RouteScale(
        "medium",
        ModelProfile(
            name="route-medium",
            vocab_buckets=1024,
            embedding_dim=16,
            latent_dim=48,
            recurrent_rank=12,
            memory_slots=64,
            memory_key_dim=32,
            memory_value_bytes=64,
            parameter_dtype_bytes=4,
            embedding_dtype_bytes=4,
            memory_dtype_bytes=4,
            optimizer_multiplier=1.0,
        ),
        MobileSparseProfile(
            name="route-mobile-medium",
            vocab_buckets=1024,
            embedding_dim=16,
            coarse_groups=4,
            blocks_per_group=8,
            block_dim=32,
            recurrent_rank=8,
            active_groups=1,
            active_blocks_per_group=2,
            state_cache_blocks=16,
            memory_slots=64,
            memory_key_dim=32,
            memory_value_bytes=64,
            weight_bytes=4,
            state_bytes=4,
        ),
    ),
)


FAMILIES = (
    "readout_only_recurrent",
    "adaptive_recurrent",
    "adaptive_recurrent_plus_episodic",
    "mobile_sparse_routed_plus_episodic",
)


def _rule_rows(delta: int, values: Sequence[int], label: str) -> list[str]:
    return [f"規則{label}|入力{value}|答え{(value + delta) % 10}" for value in values]


def _long_rows(values: Sequence[int], distractor_lengths: Sequence[int]) -> list[str]:
    rows: list[str] = []
    for value in values:
        for length in distractor_lengths:
            distractor = "雑音" * length
            rows.append(f"鍵{value}|{distractor}|答え{value}")
    return rows


def _prefix_targets(rows: Sequence[str]) -> list[tuple[str, int]]:
    examples: list[tuple[str, int]] = []
    for row in rows:
        data = row.encode("utf-8")
        if not data or data[-1] >= 128:
            raise ValueError("route rows must end in one ASCII target byte")
        examples.append((data[:-1].decode("utf-8"), int(data[-1])))
    return examples


def _recurrent_logits(model: MultiScaleRecurrentCore, prefix: str) -> np.ndarray:
    data = prefix.encode("utf-8")
    state = np.zeros(model.profile.latent_dim, dtype=np.float32)
    previous = 2
    for current in data:
        state = model._step(state, previous, current)
        previous = current
    return state @ model.decoder + model.decoder_bias


def _mobile_logits(model: MobilePagedSparseCore, prefix: str) -> np.ndarray:
    data = prefix.encode("utf-8")
    model.reset_state()
    previous = 2
    logits = np.zeros(256, dtype=np.float32)
    for current in data:
        logits, _routes, _states = model._step(previous, current)
        previous = current
    return logits


def _accuracy(
    model: object,
    examples: Sequence[tuple[str, int]],
    logits_fn: Callable[[object, str], np.ndarray],
) -> float:
    if not examples:
        return 0.0
    correct = sum(
        int(int(logits_fn(model, prefix).argmax()) == target)
        for prefix, target in examples
    )
    return correct / len(examples)


def _target_nll(
    model: object,
    examples: Sequence[tuple[str, int]],
    logits_fn: Callable[[object, str], np.ndarray],
) -> float:
    losses: list[float] = []
    for prefix, target in examples:
        logits = logits_fn(model, prefix)
        shifted = logits - float(logits.max())
        exp = np.exp(shifted)
        probability = float(exp[target] / max(float(exp.sum()), 1e-12))
        losses.append(-math.log(max(probability, 1e-9)))
    return float(np.mean(losses)) if losses else 0.0


def _recurrent_macs(profile: ModelProfile) -> int:
    return (
        profile.embedding_dim * profile.latent_dim
        + 2 * profile.latent_dim * profile.recurrent_rank
        + profile.latent_dim * 256
    )


def _fit(model: object, rows: Sequence[str], family: str) -> tuple[float, float, float]:
    before = float(model.sequence_nll(rows))
    started = time.perf_counter()
    if family == "readout_only_recurrent":
        model.fit_texts(rows, epochs=6, learning_rate=0.04)
    elif family.startswith("adaptive_recurrent"):
        model.fit_texts(
            rows,
            epochs=5,
            learning_rate=0.035,
            feature_learning_rate=0.0015,
        )
    else:
        model.fit_texts(
            rows,
            epochs=5,
            learning_rate=0.04,
            feature_learning_rate=0.001,
        )
    seconds = time.perf_counter() - started
    after = float(model.sequence_nll(rows))
    return before, after, seconds


def _make_model(family: str, scale: RouteScale, seed: int) -> object:
    if family == "readout_only_recurrent":
        return MultiScaleRecurrentCore(profile=scale.recurrent, seed=seed)
    if family in ("adaptive_recurrent", "adaptive_recurrent_plus_episodic"):
        return AdaptiveMultiScaleRecurrentCore(profile=scale.recurrent, seed=seed)
    if family == "mobile_sparse_routed_plus_episodic":
        return MobilePagedSparseCore(profile=scale.mobile, seed=seed)
    raise ValueError(f"unknown route family: {family}")


def _logits_function(family: str) -> Callable[[object, str], np.ndarray]:
    if family == "mobile_sparse_routed_plus_episodic":
        return _mobile_logits
    return _recurrent_logits


def _model_bytes(model: object, family: str) -> int:
    if family == "mobile_sparse_routed_plus_episodic":
        return int(model.report()["allocated_reference_bytes"])
    return int(model.resource_report()["actual_persistent_bytes"])


def _active_macs(model: object, family: str) -> int:
    if family == "mobile_sparse_routed_plus_episodic":
        return int(model.profile.macs_per_byte_step())
    return _recurrent_macs(model.profile)


def _one_shot_metrics(model: object, enabled: bool) -> tuple[float, float]:
    if not enabled:
        return 0.0, 0.0
    memories = (
        ("光合成で植物が取り込む気体は？", "二酸化炭素"),
        ("三角形の内角の和は？", "180度"),
        ("鎌倉幕府を開いた人物は？", "源頼朝"),
        ("速度を求める基本式は？", "距離÷時間"),
    )
    paraphrases = (
        "植物が光合成するとき吸収する気体は？",
        "三角形の三つの内角を合計すると？",
        "鎌倉幕府を始めたのは誰？",
        "距離と時間から速度を出す式は？",
    )
    for prompt, response in memories:
        model.remember(prompt, response)
    if hasattr(model, "answer"):
        recall = model.answer
    else:
        recall = model.memory.recall
    exact = sum(int(recall(prompt) == response) for prompt, response in memories) / len(memories)
    para = sum(
        int(recall(prompt) == response)
        for prompt, (_original, response) in zip(paraphrases, memories)
    ) / len(memories)
    return exact, para


def evaluate_scale(family: str, scale: RouteScale, seed: int = 0) -> RouteMetrics:
    model = _make_model(family, scale, seed)
    logits_fn = _logits_function(family)
    train_rows = (
        _rule_rows(1, range(0, 6), "甲")
        + _rule_rows(2, range(0, 6), "乙")
        + _long_rows(range(0, 6), (1, 3))
    )
    transfer = _prefix_targets(
        _rule_rows(1, range(6, 10), "甲")
        + _rule_rows(2, range(6, 10), "乙")
    )
    long_dependency = _prefix_targets(_long_rows(range(6, 10), (6, 10)))
    before, after, training_seconds = _fit(model, train_rows, family)
    transfer_accuracy = _accuracy(model, transfer, logits_fn)
    long_accuracy = _accuracy(model, long_dependency, logits_fn)

    continual = _make_model(family, scale, seed + 100)
    first_rows = _rule_rows(1, range(0, 8), "甲")
    second_rows = _rule_rows(2, range(0, 8), "乙")
    first_eval = _prefix_targets(_rule_rows(1, range(2, 10), "甲"))
    _fit(continual, first_rows, family)
    nll_before_second = _target_nll(continual, first_eval, logits_fn)
    _fit(continual, second_rows, family)
    nll_after_second = _target_nll(continual, first_eval, logits_fn)
    retention = min(1.0, math.exp(-(nll_after_second - nll_before_second)))

    memory_enabled = family.endswith("plus_episodic")
    one_shot_exact, one_shot_paraphrase = _one_shot_metrics(model, memory_enabled)
    gain = (before - after) / max(abs(before), 1e-9)
    return RouteMetrics(
        family=family,
        scale=scale.name,
        model_bytes=_model_bytes(model, family),
        active_macs_per_byte=_active_macs(model, family),
        training_seconds=training_seconds,
        train_nll_before=before,
        train_nll_after=after,
        train_nll_gain=gain,
        compositional_transfer_accuracy=transfer_accuracy,
        long_dependency_accuracy=long_accuracy,
        continual_retention=retention,
        one_shot_exact_accuracy=one_shot_exact,
        one_shot_paraphrase_accuracy=one_shot_paraphrase,
    )


def family_verdict(rows: Sequence[RouteMetrics]) -> FamilyVerdict:
    if len(rows) < 2:
        raise ValueError("at least two scale points are required")
    ordered = sorted(rows, key=lambda row: row.model_bytes)
    transfer = [row.compositional_transfer_accuracy for row in ordered]
    long_dependency = [row.long_dependency_accuracy for row in ordered]
    monotonic = all(right + 1e-12 >= left for left, right in zip(transfer, transfer[1:]))
    transfer_slope = transfer[-1] - transfer[0]
    long_slope = long_dependency[-1] - long_dependency[0]
    largest = ordered[-1]
    requirements = {
        "positive_compositional_scaling": transfer_slope >= 0.15,
        "monotonic_compositional_scaling": monotonic,
        "largest_compositional_transfer": transfer[-1] >= 0.60,
        "largest_long_dependency": long_dependency[-1] >= 0.60,
        "continual_retention": largest.continual_retention >= 0.80,
        "one_shot_paraphrase_transfer": largest.one_shot_paraphrase_accuracy >= 0.50,
        "mobile_projection_under_hard_caps": bool(MOBILE_1GB_PROFILE.static_gate()["passed"]),
    }
    failed = tuple(name for name, passed in requirements.items() if not passed)
    return FamilyVerdict(
        family=largest.family,
        scale_points=len(ordered),
        transfer_slope=transfer_slope,
        long_dependency_slope=long_slope,
        retention_at_largest=largest.continual_retention,
        one_shot_paraphrase_at_largest=largest.one_shot_paraphrase_accuracy,
        monotonic_transfer=monotonic,
        mobile_projection_feasible=requirements["mobile_projection_under_hard_caps"],
        route_go=not failed,
        failed_requirements=failed,
    )


def _next_research(verdicts: Sequence[FamilyVerdict]) -> list[dict[str, str]]:
    failed = {item for verdict in verdicts for item in verdict.failed_requirements}
    proposals: list[dict[str, str]] = []
    if "positive_compositional_scaling" in failed or "largest_compositional_transfer" in failed:
        proposals.append(
            {
                "priority": "P0",
                "hypothesis": "latent_world_and_program_learning",
                "experiment": "Replace pure next-byte supervision with a shared latent state transition objective, then test length and value extrapolation on unseen algorithms without task labels.",
                "falsification": "Reject if three increasing scales do not improve held-out algorithmic transfer or if gains require operation-specific routing.",
            }
        )
    if "largest_long_dependency" in failed:
        proposals.append(
            {
                "priority": "P0",
                "hypothesis": "learned_compressive_test_time_memory",
                "experiment": "Train a bounded memory writer/reader that updates from prediction surprise and compare fixed-state, episodic retrieval and compressive memory at equal active MACs.",
                "falsification": "Reject if retrieval accuracy collapses with distractor length or memory writes overwrite unrelated facts.",
            }
        )
    if "continual_retention" in failed:
        proposals.append(
            {
                "priority": "P1",
                "hypothesis": "stable_program_memory_plus_plastic_episode_memory",
                "experiment": "Separate slow reusable procedures from fast episodic facts and measure forward transfer, forgetting and byte cost over sequential curricula.",
                "falsification": "Reject if retention remains below 0.8 or the stable store grows linearly with examples.",
            }
        )
    if "one_shot_paraphrase_transfer" in failed:
        proposals.append(
            {
                "priority": "P1",
                "hypothesis": "semantic_binding_without_surface_memorization",
                "experiment": "Learn entity/relation bindings from contrasting paraphrases and test one-shot recall under unseen wording and reordered clauses.",
                "falsification": "Reject if exact recall rises without paraphrase recall or if a hand-written synonym list is required.",
            }
        )
    return proposals


def run_route_discovery(output_dir: str | Path) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    metrics: list[RouteMetrics] = []
    for family_index, family in enumerate(FAMILIES):
        for scale_index, scale in enumerate(SCALES):
            metrics.append(evaluate_scale(family, scale, seed=1000 + family_index * 10 + scale_index))
    verdicts = [
        family_verdict([row for row in metrics if row.family == family])
        for family in FAMILIES
    ]
    discovered = [verdict.family for verdict in verdicts if verdict.route_go]
    report = {
        "stage": "intelligence-route-discovery-001",
        "fixed_completion_conditions": {
            "package_bytes_max": 1_000_000_000,
            "weak_phone_required": True,
            "all_japanese_university_entrance_exams_exact": True,
            "natural_long_dialogue_required": True,
            "general_learning_from_diverse_data_required": True,
            "transformer_efficiency_improvement_required": True,
        },
        "purpose": "Discover or falsify scalable routes to the fixed target; a local synthetic score cannot establish completion.",
        "families": [asdict(verdict) for verdict in verdicts],
        "scale_measurements": [asdict(row) for row in metrics],
        "route_discovered": bool(discovered),
        "discovered_families": discovered,
        "current_architecture_claim": (
            "candidate_route_found" if discovered else "no_current_candidate_has_a_valid_scaling_route"
        ),
        "next_research": _next_research(verdicts),
        "integrity_checks": {
            "all_families_have_three_scales": all(verdict.scale_points == 3 for verdict in verdicts),
            "all_measurements_finite": all(
                math.isfinite(value)
                for row in metrics
                for value in (
                    row.training_seconds,
                    row.train_nll_before,
                    row.train_nll_after,
                    row.train_nll_gain,
                    row.compositional_transfer_accuracy,
                    row.long_dependency_accuracy,
                    row.continual_retention,
                    row.one_shot_exact_accuracy,
                    row.one_shot_paraphrase_accuracy,
                )
            ),
            "resource_accounting_present": all(
                row.model_bytes > 0 and row.active_macs_per_byte > 0 for row in metrics
            ),
            "completion_not_claimed_from_route_gate": True,
        },
        "highschool_level_passed": False,
        "wall_seconds": time.perf_counter() - started,
    }
    report["research_gate_passed"] = all(report["integrity_checks"].values())
    path = output / "intelligence-route-discovery-001.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if not report["research_gate_passed"]:
        raise SystemExit("route-discovery integrity gate failed")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run_route_discovery(args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
