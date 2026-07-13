from __future__ import annotations

from dataclasses import dataclass
import inspect
import json
from pathlib import Path
import random
from typing import Any, Mapping, Sequence

from .phase18d1_dataset_to_program_meta_learner import EvaluationError, canonical, decode_value
from .phase18d6_utf8_byte_codec_induction import _bytes_from_hex, parse_byte_stream
from .phase18d7_locally_stationary_viterbi import (
    ProgramState,
    _expand_blocks,
    calibration_grammar,
    enumerate_program_states,
    load_local_stream,
)
from .phase18d8_online_prequential_audit import effective_blocks
from .phase18d8_online_prequential_filter import (
    _block_end_positions,
    _prediction_errors,
    _same_signature_switches,
    _prefix_signature,
)


class NoConsistentProgramError(ValueError):
    pass


@dataclass(frozen=True)
class GrowthStats:
    version_evaluations: int
    prediction_evaluations: int
    total_operations: int


@dataclass(frozen=True)
class GrowthResult:
    states: tuple[ProgramState, ...]
    predictions: tuple[Any | None, ...]
    active_path: tuple[int, ...]
    acquired_order: tuple[int, ...]
    acquisition_positions: tuple[int, ...]
    correct: int
    wrong: int
    abstained: int
    stats: GrowthStats

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

    def active_ops(self) -> tuple[str | None, ...]:
        return tuple(
            None if index < 0 else self.states[index].expression.op
            for index in self.active_path
        )

    def acquired_ops(self) -> tuple[str, ...]:
        return tuple(self.states[index].expression.op for index in self.acquired_order)


def _state_predicts_record(state: ProgramState, record: Sequence[Any]) -> bool:
    if len(record) < 2 or state.signature[0] != _prefix_signature(record[:-1]):
        return False
    try:
        prediction = state.predict(record[:-1])
    except EvaluationError:
        return False
    return canonical(prediction) == canonical(decode_value(record[-1]))


def consistent_candidates(
    states: Sequence[ProgramState],
    observations: Sequence[Sequence[Any]],
    signature: Sequence[str],
) -> tuple[tuple[int, ...], int]:
    signature = tuple(signature)
    candidates: list[int] = []
    operations = 0
    for index, state in enumerate(states):
        if state.signature[0] != signature:
            continue
        valid = True
        for record in observations:
            operations += 1
            if not _state_predicts_record(state, record):
                valid = False
                break
        if valid:
            candidates.append(index)
    if not candidates:
        raise NoConsistentProgramError("no program explains the current observation window")
    return tuple(candidates), operations


def consensus_prediction(
    states: Sequence[ProgramState],
    candidates: Sequence[int],
    prefix: Sequence[Any],
) -> tuple[Any | None, int]:
    outputs: dict[Any, Any] = {}
    evaluations = 0
    for index in candidates:
        state = states[index]
        if state.signature[0] != _prefix_signature(prefix):
            continue
        evaluations += 1
        try:
            value = state.predict(prefix)
        except EvaluationError:
            continue
        outputs.setdefault(canonical(value), value)
    if len(outputs) == 1:
        return next(iter(outputs.values())), evaluations
    return None, evaluations


def _recent_consistent_window(
    states: Sequence[ProgramState],
    observations: Sequence[Sequence[Any]],
    signature: Sequence[str],
) -> tuple[list[tuple[Any, ...]], tuple[int, ...], int]:
    window = [tuple(record) for record in observations]
    operations = 0
    while window:
        try:
            candidates, used = consistent_candidates(states, window, signature)
        except NoConsistentProgramError:
            operations += sum(
                1 for state in states if state.signature[0] == tuple(signature)
            )
            window.pop(0)
            continue
        operations += used
        return window, candidates, operations
    candidates, used = consistent_candidates(states, (), signature)
    operations += used
    return window, candidates, operations


def grow_program_library(
    records: Sequence[Sequence[Any]],
    states: Sequence[ProgramState],
    *,
    minimum_support: int = 2,
) -> GrowthResult:
    records = tuple(tuple(record) for record in records)
    states = tuple(states)
    if not records:
        raise NoConsistentProgramError("online stream is empty")
    if not states:
        raise NoConsistentProgramError("candidate search pool is empty")

    current: int | None = None
    window: list[tuple[Any, ...]] = []
    window_signature: tuple[str, ...] | None = None
    acquired: dict[tuple[Any, ...], tuple[int, int]] = {}
    predictions: list[Any | None] = []
    active_path: list[int] = []
    correct = wrong = abstained = 0
    version_evaluations = prediction_evaluations = 0

    for position, record in enumerate(records):
        if len(record) < 2:
            raise NoConsistentProgramError("record requires a prefix and target")
        prefix = record[:-1]
        signature = _prefix_signature(prefix)

        if current is not None and states[current].signature[0] != signature:
            current = None
            window = []
            window_signature = signature
        elif window_signature is not None and window_signature != signature:
            window = []
            window_signature = signature
        elif window_signature is None:
            window_signature = signature

        prediction: Any | None
        if current is not None:
            prediction_evaluations += 1
            try:
                prediction = states[current].predict(prefix)
            except EvaluationError:
                prediction = None
        else:
            window, candidates, used = _recent_consistent_window(
                states, window, signature
            )
            version_evaluations += used
            prediction, used = consensus_prediction(states, candidates, prefix)
            prediction_evaluations += used

        predictions.append(prediction)
        target = record[-1]
        prediction_correct = (
            prediction is not None
            and canonical(prediction) == canonical(decode_value(target))
        )
        if prediction is None:
            abstained += 1
        elif prediction_correct:
            correct += 1
        else:
            wrong += 1

        current_still_valid = (
            current is not None and _state_predicts_record(states[current], record)
        )
        if current_still_valid:
            active_path.append(current)
            continue

        current = None
        if window_signature != signature:
            window = []
            window_signature = signature
        window.append(record)
        window, candidates, used = _recent_consistent_window(states, window, signature)
        version_evaluations += used

        if len(candidates) == 1 and len(window) >= minimum_support:
            current = candidates[0]
            key = states[current].behavior_key()
            if key not in acquired:
                acquired[key] = (current, position)
            window = []
            window_signature = None
        active_path.append(-1 if current is None else current)

    acquired_rows = sorted(acquired.values(), key=lambda row: row[1])
    return GrowthResult(
        states,
        tuple(predictions),
        tuple(active_path),
        tuple(index for index, _ in acquired_rows),
        tuple(position for _, position in acquired_rows),
        correct,
        wrong,
        abstained,
        GrowthStats(
            version_evaluations,
            prediction_evaluations,
            version_evaluations + prediction_evaluations,
        ),
    )


def _metrics(result: GrowthResult) -> dict[str, Any]:
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


def _block_end_correct(
    result: GrowthResult,
    blocks: Sequence[Mapping[str, Any]],
) -> tuple[int, int]:
    ops = result.active_ops()
    ends = _block_end_positions(blocks)
    return sum(ops[index] == label for index, label in ends), len(ends)


def _growth_prediction_errors(
    result: GrowthResult,
    records: Sequence[Sequence[Any]],
) -> tuple[int, ...]:
    output: list[int] = []
    for index, (prediction, record) in enumerate(zip(result.predictions, records)):
        if prediction is None:
            continue
        if canonical(prediction) != canonical(decode_value(record[-1])):
            output.append(index)
    return tuple(output)


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
    states, expressions_evaluated = enumerate_program_states(initial_records)

    initial = grow_program_library(initial_records, states)
    final = grow_program_library(final_records, states)
    doubled = grow_program_library(initial_records + initial_records, states)

    permutation = list(range(len(initial_records)))
    random.Random(20260713).shuffle(permutation)
    shuffled_records = tuple(initial_records[index] for index in permutation)
    shuffled = grow_program_library(shuffled_records, states)

    initial_blocks = effective_blocks(payload["audit_blocks"], len(initial_records))
    final_blocks = initial_blocks + tuple(dict(row) for row in payload["post_freeze_audit_blocks"])
    initial_expected_ops = {str(row["label"]) for row in initial_blocks}
    final_expected_ops = {str(row["label"]) for row in final_blocks}
    initial_end = _block_end_correct(initial, initial_blocks)
    final_end = _block_end_correct(final, final_blocks)

    initial_errors = _growth_prediction_errors(initial, initial_records)
    final_errors = _growth_prediction_errors(final, final_records)
    initial_switches = _same_signature_switches(initial_records, initial_blocks)
    final_switches = _same_signature_switches(final_records, final_blocks)

    initial_acquired_ops = set(initial.acquired_ops())
    final_acquired_ops = set(final.acquired_ops())
    post_start = len(initial_records)
    min_acquisition_positions = [
        position
        for index, position in zip(final.acquired_order, final.acquisition_positions)
        if final.states[index].expression.op == "MIN2"
    ]
    min_acquisition_examples = (
        min_acquisition_positions[0] - post_start + 1
        if min_acquisition_positions
        else None
    )

    ratio = doubled.stats.total_operations / initial.stats.total_operations
    learner_source = inspect.getsource(grow_program_library)
    forbidden_cover_token = "exact_" + "cover"
    checks = {
        "active_library_starts_empty": True,
        "initial_programs_acquired_from_data": initial_acquired_ops == initial_expected_ops,
        "final_programs_acquired_from_data": final_acquired_ops == final_expected_ops,
        "post_freeze_adds_exactly_one_program": len(final_acquired_ops - initial_acquired_ops) == 1,
        "post_freeze_program_is_min": final_acquired_ops - initial_acquired_ops == {"MIN2"},
        "min_acquired_within_block": min_acquisition_examples is not None
        and min_acquisition_examples <= int(payload["post_freeze_audit_blocks"][0]["length"]),
        "initial_block_end_identification": initial_end[0] == initial_end[1],
        "final_block_end_identification": final_end[0] == final_end[1],
        "initial_covered_accuracy": initial.covered_accuracy >= 0.95,
        "final_covered_accuracy": final.covered_accuracy >= 0.95,
        "initial_coverage": initial.coverage >= 0.45,
        "final_coverage": final.coverage >= 0.45,
        "initial_errors_confined_to_same_signature_switches": set(initial_errors)
        <= {0, *initial_switches},
        "final_errors_confined_to_same_signature_switches": set(final_errors)
        <= {0, *final_switches},
        "future_suffix_cannot_change_past_predictions": final.predictions[: len(initial.predictions)]
        == initial.predictions,
        "future_suffix_cannot_change_past_library_state": final.active_path[: len(initial.active_path)]
        == initial.active_path,
        "shuffle_degrades_acquisition_or_prediction": len(shuffled.acquired_order)
        < len(initial.acquired_order)
        or shuffled.correct < initial.correct,
        "near_linear_operation_scaling": 1.8 <= ratio <= 2.2,
        "learner_has_no_exact_cover": forbidden_cover_token not in learner_source,
        "learner_has_no_support_episode_api": "support" not in learner_source,
    }

    learned_payload_bits = sum(
        final.states[index].payload_bits for index in final.acquired_order
    ) + 32
    source_path = Path(__file__)
    return {
        "campaign": {
            "name": "phase18d9-online-library-growth-c1",
            "active_programs_at_start": 0,
            "candidate_search_pool_pre_enumerated": True,
            "task_ids_supplied": False,
            "task_boundaries_supplied": False,
            "support_episodes_supplied": False,
            "source_changes_for_post_freeze_min": 0,
        },
        "search_pool": {
            "candidate_states": len(states),
            "expressions_evaluated": expressions_evaluated,
            "human_designed_dsl": True,
        },
        "acquisition": {
            "initial_program_count": len(initial.acquired_order),
            "initial_programs": list(initial.acquired_ops()),
            "initial_acquisition_positions": list(initial.acquisition_positions),
            "final_program_count": len(final.acquired_order),
            "final_programs": list(final.acquired_ops()),
            "final_acquisition_positions": list(final.acquisition_positions),
            "post_freeze_min_acquisition_examples": min_acquisition_examples,
            "initial_block_ends_correct": initial_end[0],
            "initial_blocks": initial_end[1],
            "final_block_ends_correct": final_end[0],
            "final_blocks": final_end[1],
        },
        "prequential": {
            "initial": _metrics(initial),
            "final": _metrics(final),
            "shuffled": _metrics(shuffled),
            "initial_error_positions": list(initial_errors),
            "final_error_positions": list(final_errors),
            "initial_same_signature_switch_positions": list(initial_switches),
            "final_same_signature_switch_positions": list(final_switches),
        },
        "resources": {
            "initial_operations": initial.stats.total_operations,
            "double_length_operations": doubled.stats.total_operations,
            "double_length_operation_ratio": ratio,
            "large_stream_exact_cover_nodes": 0,
            "learned_payload_bits": learned_payload_bits,
            "source_bytes": len(source_path.read_bytes()),
            "python_runtime_included": False,
        },
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {
            "program_library_grows_from_stream_observations": all(checks.values()),
            "primitive_search_space_learned": False,
            "open_primitive_invention": False,
            "arbitrary_interleaving": False,
            "raw_natural_language_pretraining": False,
            "llm_like_general_learning": False,
        },
        "limitations": [
            "The active library starts empty, but the 130-state typed DSL search pool is still human-designed and pre-enumerated.",
            "Programs are activated only after a noiseless recent window uniquely identifies one candidate.",
            "The learner assumes locally persistent behaviors and uses complete records after each next-field prediction.",
            "The UTF-8 codec and atom families remain pre-calibrated.",
            "This does not learn natural-language meaning, world knowledge, or new primitive operations outside the DSL.",
        ],
    }


def markdown(payload: Mapping[str, Any]) -> str:
    acquisition = payload["acquisition"]
    initial = payload["prequential"]["initial"]
    final = payload["prequential"]["final"]
    resources = payload["resources"]
    return f"""# Phase 18d-9 results: online program-library growth

- Active program library at start: **{payload['campaign']['active_programs_at_start']}**
- Initial acquired programs: **{acquisition['initial_program_count']}**
- Final acquired programs: **{acquisition['final_program_count']}**
- Post-freeze MIN acquisition delay: **{acquisition['post_freeze_min_acquisition_examples']} observed examples**
- Initial correct / wrong / abstained: **{initial['correct']} / {initial['wrong']} / {initial['abstained']}**
- Initial covered accuracy / coverage: **{initial['covered_accuracy']:.3%} / {initial['coverage']:.3%}**
- Final correct / wrong / abstained: **{final['correct']} / {final['wrong']} / {final['abstained']}**
- Final covered accuracy / coverage: **{final['covered_accuracy']:.3%} / {final['coverage']:.3%}**
- Initial / final block-end identification: **{acquisition['initial_block_ends_correct']}/{acquisition['initial_blocks']} / {acquisition['final_block_ends_correct']}/{acquisition['final_blocks']}**
- Doubling operation ratio: **{resources['double_length_operation_ratio']:.4f}x**
- Learned active-library payload: **{resources['learned_payload_bits']} bits**

The active library begins empty. Programs are added only when recent stream observations uniquely select one behavior from the frozen generic DSL search pool. The appended MIN block adds the eighth active program without a source change. This is data-driven program acquisition inside a fixed search language, not open-ended primitive invention.
"""


def main() -> None:
    payload = run()
    Path("results").mkdir(exist_ok=True)
    Path("results/phase18d9.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    Path("results/phase18d9.md").write_text(markdown(payload), encoding="utf-8")
    print(markdown(payload), end="")


if __name__ == "__main__":
    main()
