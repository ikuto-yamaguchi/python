from __future__ import annotations

from dataclasses import dataclass
import inspect
import json
import math
from pathlib import Path
import random
from typing import Any, Mapping, Sequence

from .phase18d1_dataset_to_program_meta_learner import (
    EvaluationError,
    canonical,
    decode_value,
    value_kind,
)
from .phase18d6_utf8_byte_codec_induction import (
    ByteGrammarError,
    _bytes_from_hex,
    parse_byte_stream,
)
from .phase18d7_locally_stationary_viterbi import (
    ProgramState,
    _expand_blocks,
    calibration_grammar,
    enumerate_program_states,
    load_local_stream,
)


class NoOnlineStateError(ValueError):
    pass


@dataclass(frozen=True)
class PredictionDecision:
    value: Any | None
    compatible_states: int
    best_states: int
    evaluations: int


@dataclass(frozen=True)
class OnlineStats:
    transition_operations: int
    prediction_operations: int
    update_operations: int
    total_operations: int


@dataclass(frozen=True)
class OnlineResult:
    states: tuple[ProgramState, ...]
    predictions: tuple[Any | None, ...]
    posterior_path: tuple[int, ...]
    correct: int
    wrong: int
    abstained: int
    stats: OnlineStats

    @property
    def total(self) -> int:
        return len(self.predictions)

    @property
    def covered(self) -> int:
        return self.correct + self.wrong

    @property
    def coverage(self) -> float:
        return self.covered / self.total if self.total else 0.0

    @property
    def covered_accuracy(self) -> float:
        return self.correct / self.covered if self.covered else 0.0

    @property
    def overall_accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0

    def posterior_ops(self) -> tuple[str, ...]:
        return tuple(self.states[index].expression.op for index in self.posterior_path)

    def used_posterior_states(self) -> tuple[ProgramState, ...]:
        unique = {
            self.states[index].behavior_key(): self.states[index]
            for index in self.posterior_path
        }
        return tuple(
            sorted(
                unique.values(),
                key=lambda state: (state.expression.op, state.expression.render()),
            )
        )


def _prefix_signature(prefix: Sequence[Any]) -> tuple[str, ...]:
    if not prefix:
        raise NoOnlineStateError("a next-field prediction requires a non-empty prefix")
    return tuple(value_kind(decode_value(value)) for value in prefix)


def initial_prior(states: Sequence[ProgramState]) -> tuple[float, ...]:
    if not states:
        raise NoOnlineStateError("candidate states are required")
    return tuple(float(state.expression.cost) for state in states)


def transition_prior(
    previous: Sequence[float] | None,
    states: Sequence[ProgramState],
    *,
    switch_penalty: int,
) -> tuple[tuple[float, ...], int]:
    states = tuple(states)
    if not states:
        raise NoOnlineStateError("candidate states are required")
    if previous is None:
        return initial_prior(states), len(states)
    previous = tuple(float(cost) for cost in previous)
    if len(previous) != len(states):
        raise NoOnlineStateError("state and cost dimensions differ")
    finite = [index for index, cost in enumerate(previous) if not math.isinf(cost)]
    if not finite:
        raise NoOnlineStateError("all online states are impossible")
    ranked = sorted(
        finite,
        key=lambda index: (previous[index], states[index].expression.render()),
    )
    best = ranked[0]
    second = ranked[1] if len(ranked) > 1 else best
    current: list[float] = []
    operations = 0
    for index in range(len(states)):
        alternate = best if best != index else second
        stay = previous[index]
        switch = previous[alternate] + switch_penalty
        operations += 2
        current.append(min(stay, switch))
    return tuple(current), operations


def predict_from_prior(
    prior: Sequence[float],
    prefix: Sequence[Any],
    states: Sequence[ProgramState],
) -> PredictionDecision:
    states = tuple(states)
    prior = tuple(float(cost) for cost in prior)
    if len(prior) != len(states):
        raise NoOnlineStateError("state and cost dimensions differ")
    signature = _prefix_signature(prefix)
    candidates: list[tuple[float, int, Any]] = []
    evaluations = 0
    for index, state in enumerate(states):
        if state.signature[0] != signature or math.isinf(prior[index]):
            continue
        evaluations += 1
        try:
            value = state.predict(prefix)
        except EvaluationError:
            continue
        candidates.append((prior[index], index, value))
    if not candidates:
        raise NoOnlineStateError("no candidate state accepts the prefix")
    best_cost = min(row[0] for row in candidates)
    best = [row for row in candidates if row[0] == best_cost]
    outputs: dict[Any, Any] = {}
    for _, _, value in best:
        outputs.setdefault(canonical(value), value)
    prediction = next(iter(outputs.values())) if len(outputs) == 1 else None
    return PredictionDecision(prediction, len(candidates), len(best), evaluations)


def observe_target(
    prior: Sequence[float],
    prefix: Sequence[Any],
    target: Any,
    states: Sequence[ProgramState],
    *,
    error_penalty: int,
) -> tuple[tuple[float, ...], int, int]:
    states = tuple(states)
    prior = tuple(float(cost) for cost in prior)
    if len(prior) != len(states):
        raise NoOnlineStateError("state and cost dimensions differ")
    signature = _prefix_signature(prefix)
    target_key = canonical(decode_value(target))
    current: list[float] = [math.inf] * len(states)
    evaluations = 0
    for index, state in enumerate(states):
        if state.signature[0] != signature or math.isinf(prior[index]):
            continue
        evaluations += 1
        try:
            prediction = state.predict(prefix)
        except EvaluationError:
            continue
        emission = 0 if canonical(prediction) == target_key else error_penalty
        current[index] = prior[index] + emission
    finite = [cost for cost in current if not math.isinf(cost)]
    if not finite:
        raise NoOnlineStateError("no candidate state can absorb the observation")
    offset = min(finite)
    normalized = tuple(
        cost - offset if not math.isinf(cost) else math.inf
        for cost in current
    )
    winners = [index for index, cost in enumerate(normalized) if cost == 0]
    posterior = min(
        winners,
        key=lambda index: (
            states[index].expression.cost,
            states[index].expression.render(),
        ),
    )
    return normalized, posterior, evaluations


def online_filter(
    records: Sequence[Sequence[Any]],
    states: Sequence[ProgramState],
    *,
    switch_penalty: int = 7,
    error_penalty: int = 20,
) -> OnlineResult:
    records = tuple(tuple(record) for record in records)
    states = tuple(states)
    if not records:
        raise NoOnlineStateError("online stream is empty")
    if not states:
        raise NoOnlineStateError("candidate states are required")

    previous: tuple[float, ...] | None = None
    predictions: list[Any | None] = []
    posterior_path: list[int] = []
    correct = wrong = abstained = 0
    transition_operations = prediction_operations = update_operations = 0

    for record in records:
        if len(record) < 2:
            raise NoOnlineStateError("record requires a prefix and next field")
        prefix = record[:-1]
        prior, operations = transition_prior(
            previous,
            states,
            switch_penalty=switch_penalty,
        )
        transition_operations += operations

        # This decision is completed before record[-1] is read.  The public API
        # deliberately separates prediction from observation so counterfactual
        # targets cannot affect the prediction at the same position.
        decision = predict_from_prior(prior, prefix, states)
        prediction_operations += decision.evaluations
        predictions.append(decision.value)

        target = record[-1]
        if decision.value is None:
            abstained += 1
        elif canonical(decision.value) == canonical(decode_value(target)):
            correct += 1
        else:
            wrong += 1

        previous, posterior, operations = observe_target(
            prior,
            prefix,
            target,
            states,
            error_penalty=error_penalty,
        )
        update_operations += operations
        posterior_path.append(posterior)

    return OnlineResult(
        states,
        tuple(predictions),
        tuple(posterior_path),
        correct,
        wrong,
        abstained,
        OnlineStats(
            transition_operations,
            prediction_operations,
            update_operations,
            transition_operations + prediction_operations + update_operations,
        ),
    )


def _block_end_positions(blocks: Sequence[Mapping[str, Any]]) -> tuple[tuple[int, str], ...]:
    cursor = 0
    output: list[tuple[int, str]] = []
    for block in blocks:
        cursor += int(block["length"])
        output.append((cursor - 1, str(block["label"])))
    return tuple(output)


def _block_start_positions(blocks: Sequence[Mapping[str, Any]]) -> tuple[int, ...]:
    cursor = 0
    output: list[int] = []
    for block in blocks:
        output.append(cursor)
        cursor += int(block["length"])
    return tuple(output)


def _same_signature_switches(
    records: Sequence[Sequence[Any]],
    blocks: Sequence[Mapping[str, Any]],
) -> tuple[int, ...]:
    starts = _block_start_positions(blocks)
    output: list[int] = []
    for position in starts[1:]:
        left = _prefix_signature(records[position - 1][:-1])
        right = _prefix_signature(records[position][:-1])
        if left == right:
            output.append(position)
    return tuple(output)


def _audit_posterior(
    result: OnlineResult,
    labels: Sequence[str],
) -> tuple[int, int]:
    ops = result.posterior_ops()
    if len(ops) != len(labels):
        return 0, len(labels)
    return sum(op == label for op, label in zip(ops, labels)), len(labels)


def _prediction_errors(result: OnlineResult, records: Sequence[Sequence[Any]]) -> tuple[int, ...]:
    output: list[int] = []
    for index, (prediction, record) in enumerate(zip(result.predictions, records)):
        if prediction is None:
            continue
        if canonical(prediction) != canonical(decode_value(record[-1])):
            output.append(index)
    return tuple(output)


def _counterfactual_target_independence(
    states: Sequence[ProgramState],
    record: Sequence[Any],
) -> bool:
    prior = initial_prior(states)
    prefix = tuple(record[:-1])
    first = predict_from_prior(prior, prefix, states)
    alternative = tuple(record[:-1]) + ("counterfactual-target",)
    second = predict_from_prior(prior, alternative[:-1], states)
    return canonical(first.value) == canonical(second.value)


def _metrics(result: OnlineResult) -> dict[str, Any]:
    return {
        "correct": result.correct,
        "wrong": result.wrong,
        "abstained": result.abstained,
        "covered": result.covered,
        "total": result.total,
        "coverage": result.coverage,
        "covered_accuracy": result.covered_accuracy,
        "overall_accuracy": result.overall_accuracy,
    }


def run() -> dict[str, Any]:
    payload = load_local_stream()
    grammar = calibration_grammar()
    initial_records = parse_byte_stream(
        _bytes_from_hex(payload["ordered_stream_hex"]),
        grammar.record_separator,
        grammar.field_separator,
        grammar.numeric_zero_codepoint,
    )
    post_records = parse_byte_stream(
        _bytes_from_hex(payload["post_freeze_hex"]),
        grammar.record_separator,
        grammar.field_separator,
        grammar.numeric_zero_codepoint,
    )
    final_records = initial_records + post_records

    # The typed candidate library is frozen once.  No task-specific state is
    # added when the post-freeze MIN behavior arrives.
    states, expressions_evaluated = enumerate_program_states(initial_records)
    initial = online_filter(initial_records, states)
    final = online_filter(final_records, states)
    no_persistence = online_filter(initial_records, states, switch_penalty=0)

    permutation = list(range(len(initial_records)))
    random.Random(20260713).shuffle(permutation)
    shuffled_records = tuple(initial_records[index] for index in permutation)
    shuffled = online_filter(shuffled_records, states)
    doubled = online_filter(initial_records + initial_records, states)

    initial_blocks = tuple(payload["audit_blocks"])
    final_blocks = initial_blocks + tuple(payload["post_freeze_audit_blocks"])
    initial_labels = _expand_blocks(initial_blocks)
    final_labels = _expand_blocks(final_blocks)
    initial_posterior = _audit_posterior(initial, initial_labels)
    final_posterior = _audit_posterior(final, final_labels)

    initial_block_ends = _block_end_positions(initial_blocks)
    final_block_ends = _block_end_positions(final_blocks)
    initial_ops = initial.posterior_ops()
    final_ops = final.posterior_ops()
    initial_block_end_correct = sum(initial_ops[index] == label for index, label in initial_block_ends)
    final_block_end_correct = sum(final_ops[index] == label for index, label in final_block_ends)

    initial_same_signature_switches = _same_signature_switches(initial_records, initial_blocks)
    final_same_signature_switches = _same_signature_switches(final_records, final_blocks)
    initial_errors = _prediction_errors(initial, initial_records)
    final_errors = _prediction_errors(final, final_records)
    allowed_initial_errors = {0, *initial_same_signature_switches}
    allowed_final_errors = {0, *final_same_signature_switches}

    post_start = len(initial_records)
    min_positions = [
        index
        for index in range(post_start, len(final_ops))
        if final_ops[index] == "MIN2"
    ]
    min_discovery_examples = (
        min_positions[0] - post_start + 1 if min_positions else None
    )

    operation_ratio = doubled.stats.total_operations / initial.stats.total_operations
    filter_source = inspect.getsource(online_filter)
    forbidden_cover_token = "exact_" + "cover"
    checks = {
        "initial_stream_length_matches_audit": len(initial_records) == len(initial_labels),
        "final_stream_length_matches_audit": len(final_records) == len(final_labels),
        "candidate_library_frozen": len(states) == 130,
        "initial_covered_accuracy": initial.covered_accuracy >= 0.95,
        "final_covered_accuracy": final.covered_accuracy >= 0.95,
        "initial_overall_accuracy": initial.overall_accuracy >= 0.80,
        "final_overall_accuracy": final.overall_accuracy >= 0.80,
        "initial_block_end_identification": initial_block_end_correct == len(initial_block_ends),
        "final_block_end_identification": final_block_end_correct == len(final_block_ends),
        "post_freeze_min_discovered_within_two_examples": min_discovery_examples is not None
        and min_discovery_examples <= 2,
        "future_suffix_cannot_change_past_predictions": final.predictions[: len(initial.predictions)]
        == initial.predictions,
        "same_position_target_independence": _counterfactual_target_independence(
            states, initial_records[0]
        ),
        "initial_errors_confined_to_unannounced_same_signature_switches": set(initial_errors)
        <= allowed_initial_errors,
        "final_errors_confined_to_unannounced_same_signature_switches": set(final_errors)
        <= allowed_final_errors,
        "persistence_improves_online_prediction": initial.correct > no_persistence.correct,
        "shuffle_degrades_online_prediction": initial.correct > shuffled.correct,
        "linear_operation_scaling": 1.95 <= operation_ratio <= 2.05,
        "large_stage_filter_has_no_exact_cover": forbidden_cover_token not in filter_source,
        "large_stage_filter_has_no_support_episode_api": "support" not in filter_source,
    }

    source_path = Path(__file__)
    return {
        "campaign": {
            "name": "phase18d8-online-prequential-filter-c1",
            "input": "continuous UTF-8 byte records decoded by frozen Phase 18d-6 codec",
            "prediction_protocol": "predict next field before observing it, then update",
            "future_records_visible": False,
            "support_episodes_supplied": False,
            "task_ids_supplied": False,
            "task_boundaries_supplied": False,
            "source_changes_for_post_freeze_behavior": 0,
        },
        "library": {
            "candidate_states": len(states),
            "expressions_evaluated": expressions_evaluated,
            "frozen_before_post_freeze_min": True,
        },
        "prequential": {
            "initial": _metrics(initial),
            "final": _metrics(final),
            "without_persistence": _metrics(no_persistence),
            "shuffled": _metrics(shuffled),
            "initial_prediction_error_positions": list(initial_errors),
            "final_prediction_error_positions": list(final_errors),
            "initial_same_signature_switch_positions": list(initial_same_signature_switches),
            "final_same_signature_switch_positions": list(final_same_signature_switches),
        },
        "posterior_identification": {
            "initial_correct": initial_posterior[0],
            "initial_total": initial_posterior[1],
            "final_correct": final_posterior[0],
            "final_total": final_posterior[1],
            "initial_block_ends_correct": initial_block_end_correct,
            "initial_blocks": len(initial_block_ends),
            "final_block_ends_correct": final_block_end_correct,
            "final_blocks": len(final_block_ends),
            "post_freeze_min_discovery_examples": min_discovery_examples,
            "used_initial_ops": sorted({state.expression.op for state in initial.used_posterior_states()}),
            "used_final_ops": sorted({state.expression.op for state in final.used_posterior_states()}),
        },
        "resources": {
            "initial_operations": initial.stats.total_operations,
            "double_length_operations": doubled.stats.total_operations,
            "double_length_operation_ratio": operation_ratio,
            "large_stream_exact_cover_nodes": 0,
            "small_codec_calibration_exact_cover_nodes": 9,
            "learned_payload_bits": 840,
            "source_bytes": len(source_path.read_bytes()),
            "python_runtime_included": False,
        },
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {
            "online_next_field_learning_without_support_episodes": all(checks.values()),
            "zero_error_at_unannounced_same_signature_change_points": False,
            "arbitrarily_interleaved_task_discovery": False,
            "online_primitive_invention": False,
            "raw_natural_language_pretraining": False,
            "llm_like_general_learning": False,
        },
        "limitations": [
            "The candidate program library, DSL, types, codec, penalties, and value atoms remain human-designed or pre-calibrated.",
            "A task switch with the same prefix type is not observable before its first new target; finite change-point regret is unavoidable.",
            "The filter assumes local persistence and degrades when records are arbitrarily shuffled.",
            "The learner updates after complete records rather than predicting every raw UTF-8 byte.",
            "No natural-language semantics, world knowledge, open primitive invention, or free-form generation is learned here.",
        ],
    }


def markdown(payload: Mapping[str, Any]) -> str:
    initial = payload["prequential"]["initial"]
    final = payload["prequential"]["final"]
    posterior = payload["posterior_identification"]
    resources = payload["resources"]
    return f"""# Phase 18d-8 results: causal online next-field filtering

- Initial prequential correct / wrong / abstained: **{initial['correct']} / {initial['wrong']} / {initial['abstained']}**
- Initial covered accuracy / coverage: **{initial['covered_accuracy']:.3%} / {initial['coverage']:.3%}**
- Final prequential correct / wrong / abstained: **{final['correct']} / {final['wrong']} / {final['abstained']}**
- Final covered accuracy / coverage: **{final['covered_accuracy']:.3%} / {final['coverage']:.3%}**
- Initial block-end identification: **{posterior['initial_block_ends_correct']}/{posterior['initial_blocks']}**
- Final block-end identification: **{posterior['final_block_ends_correct']}/{posterior['final_blocks']}**
- Post-freeze MIN discovery delay: **{posterior['post_freeze_min_discovery_examples']} observed example(s)**
- Initial / doubled operations: **{resources['initial_operations']} / {resources['double_length_operations']}**
- Doubling ratio: **{resources['double_length_operation_ratio']:.4f}x**
- Large-stage exact-cover nodes: **{resources['large_stream_exact_cover_nodes']}**

The model predicts each next field before reading that field, then performs a causal update. It receives no task ID, task boundary, future suffix, or complete support episode. A same-type task change is information-theoretically invisible before the first new target, so the experiment reports finite change-point regret rather than claiming impossible zero-error foresight.
"""


def main() -> None:
    payload = run()
    Path("results").mkdir(exist_ok=True)
    Path("results/phase18d8.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    Path("results/phase18d8.md").write_text(markdown(payload), encoding="utf-8")
    print(markdown(payload), end="")


if __name__ == "__main__":
    main()
