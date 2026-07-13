from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import inspect
import json
import math
from pathlib import Path
import random
from typing import Any, Mapping, Sequence

from .phase18d1_dataset_to_program_meta_learner import (
    EvaluationError,
    Expr,
    _example_signature,
    _probe_examples,
    canonical,
    decode_value,
    enumerate_expressions,
    evaluate_expr,
    value_kind,
)
from .phase18d6_utf8_byte_codec_induction import (
    ByteGrammar,
    ByteGrammarError,
    _bytes_from_hex,
    _decode_atom,
    induce_byte_grammar,
    load_byte_stream,
    parse_byte_stream,
)


class NoViterbiPathError(ValueError):
    pass


class NonIdentifiableContextError(ValueError):
    pass


@dataclass(frozen=True)
class ProgramState:
    signature: tuple[tuple[str, ...], str]
    expression: Expr
    probe_signature: tuple[Any, ...]

    @property
    def payload_bits(self) -> int:
        return len(self.expression.render().encode("utf-8")) * 8

    def predict(self, prefix: Sequence[Any]) -> Any:
        environment = {
            f"v{index}": decode_value(value)
            for index, value in enumerate(prefix)
        }
        return evaluate_expr(self.expression, environment)

    def behavior_key(self) -> tuple[Any, ...]:
        return self.signature, self.probe_signature


@dataclass(frozen=True)
class ViterbiStats:
    emission_operations: int
    transition_operations: int
    total_operations: int


@dataclass(frozen=True)
class ViterbiResult:
    states: tuple[ProgramState, ...]
    path: tuple[int, ...]
    total_cost: int
    switches: int
    stats: ViterbiStats

    def used_states(self) -> tuple[ProgramState, ...]:
        unique = {
            self.states[index].behavior_key(): self.states[index]
            for index in self.path
        }
        return tuple(
            sorted(
                unique.values(),
                key=lambda state: (
                    state.expression.op,
                    state.expression.render(),
                ),
            )
        )

    def fingerprint(self) -> tuple[Any, ...]:
        return tuple(
            sorted(
                (state.behavior_key() for state in self.used_states()),
                key=repr,
            )
        )


def load_local_stream(path: Path | None = None) -> dict[str, Any]:
    if path is None:
        path = (
            Path(__file__).parents[2]
            / "data"
            / "phase18d7_locally_stationary_byte_stream.json"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported locally stationary stream schema")
    return payload


@lru_cache(maxsize=1)
def calibration_grammar() -> ByteGrammar:
    payload = load_byte_stream()
    return induce_byte_grammar(_bytes_from_hex(payload["byte_stream_hex"]))


def _record_signature(record: Sequence[Any]) -> tuple[tuple[str, ...], str]:
    if len(record) < 2:
        raise ValueError("record requires a prefix and next value")
    return (
        tuple(value_kind(decode_value(value)) for value in record[:-1]),
        value_kind(decode_value(record[-1])),
    )


def enumerate_program_states(
    records: Sequence[Sequence[Any]],
    *,
    max_cost: int = 3,
) -> tuple[tuple[ProgramState, ...], int]:
    signatures = sorted({_record_signature(record) for record in records}, key=repr)
    states: list[ProgramState] = []
    expressions_evaluated = 0
    for input_signature, output_type in signatures:
        input_types = {
            f"v{index}": kind
            for index, kind in enumerate(input_signature)
        }
        probes = _probe_examples(input_types)
        by_cost = enumerate_expressions(input_types, output_type, max_cost)
        deduplicated: dict[tuple[Any, ...], Expr] = {}
        for cost in range(1, max_cost + 1):
            for expression in by_cost.get(cost, ()):
                if expression.result_type != output_type:
                    continue
                expressions_evaluated += 1
                signature = _example_signature(expression, probes)
                existing = deduplicated.get(signature)
                if existing is None or (
                    expression.cost,
                    expression.render(),
                ) < (
                    existing.cost,
                    existing.render(),
                ):
                    deduplicated[signature] = expression
        states.extend(
            ProgramState((input_signature, output_type), expression, probe_signature)
            for probe_signature, expression in deduplicated.items()
        )
    return (
        tuple(
            sorted(
                states,
                key=lambda state: (
                    repr(state.signature),
                    state.expression.cost,
                    state.expression.render(),
                ),
            )
        ),
        expressions_evaluated,
    )


def _emission_cost(
    state: ProgramState,
    record: Sequence[Any],
    error_penalty: int,
) -> int | float:
    if state.signature != _record_signature(record):
        return math.inf
    try:
        prediction = state.predict(record[:-1])
    except EvaluationError:
        return math.inf
    return (
        0
        if canonical(prediction) == canonical(decode_value(record[-1]))
        else error_penalty
    )


def infer_locally_stationary_path(
    records: Sequence[Sequence[Any]],
    states: Sequence[ProgramState],
    *,
    switch_penalty: int = 7,
    error_penalty: int = 20,
) -> ViterbiResult:
    records = tuple(tuple(record) for record in records)
    states = tuple(states)
    if not records or not states:
        raise NoViterbiPathError("records and states are required")

    emission_operations = 0
    transition_operations = 0
    previous: list[int | float] = []
    for state in states:
        emission_operations += 1
        previous.append(
            state.expression.cost
            + _emission_cost(state, records[0], error_penalty)
        )
    if all(math.isinf(cost) for cost in previous):
        raise NoViterbiPathError("no state accepts the first record")

    backpointers: list[list[int]] = []
    for record in records[1:]:
        ranked = sorted(
            range(len(states)),
            key=lambda index: (
                previous[index],
                states[index].expression.render(),
            ),
        )
        best_index = ranked[0]
        second_index = ranked[1] if len(ranked) > 1 else ranked[0]
        current: list[int | float] = [math.inf] * len(states)
        back: list[int] = [-1] * len(states)

        for index, state in enumerate(states):
            emission_operations += 1
            emission = _emission_cost(state, record, error_penalty)
            if math.isinf(emission):
                continue
            alternate = best_index if best_index != index else second_index
            stay_cost = previous[index]
            switch_cost = previous[alternate] + switch_penalty
            transition_operations += 2
            if stay_cost <= switch_cost:
                current[index] = stay_cost + emission
                back[index] = index
            else:
                current[index] = switch_cost + emission
                back[index] = alternate

        if all(math.isinf(cost) for cost in current):
            raise NoViterbiPathError("no state path accepts the stream")
        previous = current
        backpointers.append(back)

    end = min(
        range(len(states)),
        key=lambda index: (
            previous[index],
            states[index].expression.render(),
        ),
    )
    path = [end]
    for back in reversed(backpointers):
        end = back[end]
        if end < 0:
            raise NoViterbiPathError("broken backpointer")
        path.append(end)
    path.reverse()
    switches = sum(left != right for left, right in zip(path, path[1:]))
    return ViterbiResult(
        states,
        tuple(path),
        int(min(previous)),
        switches,
        ViterbiStats(
            emission_operations,
            transition_operations,
            emission_operations + transition_operations,
        ),
    )


def _expand_blocks(blocks: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    return tuple(
        str(block["label"])
        for block in blocks
        for _ in range(int(block["length"]))
    )


def audit_path(result: ViterbiResult, labels: Sequence[str]) -> tuple[int, int]:
    if len(result.path) != len(labels):
        return 0, len(labels)
    correct = sum(
        result.states[state_index].expression.op == label
        for state_index, label in zip(result.path, labels)
    )
    return correct, len(labels)


def _decode_episode_record(
    grammar: ByteGrammar,
    value: str,
    *,
    minimum_fields: int = 2,
) -> tuple[Any, ...]:
    fields = _bytes_from_hex(value).split(bytes((grammar.field_separator,)))
    if len(fields) < minimum_fields or any(not field for field in fields):
        raise ByteGrammarError("invalid episode record")
    return tuple(
        _decode_atom(field, grammar.numeric_zero_codepoint)
        for field in fields
    )


def route_from_context(
    used_states: Sequence[ProgramState],
    support: Sequence[Sequence[Any]],
) -> ProgramState:
    if not support:
        raise NonIdentifiableContextError("support is empty")
    matches: dict[tuple[Any, ...], ProgramState] = {}
    for state in used_states:
        valid = True
        for record in support:
            if state.signature != _record_signature(record):
                valid = False
                break
            try:
                prediction = state.predict(record[:-1])
            except EvaluationError:
                valid = False
                break
            if canonical(prediction) != canonical(decode_value(record[-1])):
                valid = False
                break
        if valid:
            matches[state.behavior_key()] = state
    if len(matches) != 1:
        raise NonIdentifiableContextError(
            f"support selects {len(matches)} behaviors"
        )
    return next(iter(matches.values()))


def evaluate_context_episodes(
    grammar: ByteGrammar,
    used_states: Sequence[ProgramState],
    episodes: Sequence[Mapping[str, Any]],
) -> tuple[int, int, int]:
    correct = covered = total = 0
    for episode in episodes:
        total += len(episode["queries"])
        try:
            support = tuple(
                _decode_episode_record(grammar, value)
                for value in episode["support_hex"]
            )
            state = route_from_context(used_states, support)
        except (ByteGrammarError, NonIdentifiableContextError):
            continue
        covered += len(episode["queries"])
        for query in episode["queries"]:
            try:
                prefix = _decode_episode_record(
                    grammar,
                    query["prefix_hex"],
                    minimum_fields=1,
                )
                target = _decode_atom(
                    _bytes_from_hex(query["target_hex"]),
                    grammar.numeric_zero_codepoint,
                )
                prediction = state.predict(prefix)
            except (ByteGrammarError, EvaluationError):
                continue
            correct += canonical(prediction) == canonical(decode_value(target))
    return correct, covered, total


def _failure_controls(
    grammar: ByteGrammar,
    used_states: Sequence[ProgramState],
) -> dict[str, bool]:
    controls: dict[str, bool] = {}
    try:
        infer_locally_stationary_path((), used_states)
    except NoViterbiPathError:
        controls["empty_stream_abstains"] = True
    else:
        controls["empty_stream_abstains"] = False

    zero = chr(grammar.numeric_zero_codepoint).encode("utf-8")
    ambiguous = (
        _decode_episode_record(
            grammar,
            (
                zero
                + bytes((grammar.field_separator,))
                + zero
                + bytes((grammar.field_separator,))
                + zero
            ).hex(),
        ),
    )
    try:
        route_from_context(used_states, ambiguous)
    except NonIdentifiableContextError:
        controls["ambiguous_context_abstains"] = True
    else:
        controls["ambiguous_context_abstains"] = False

    cube_support = ((2, 8), (3, 27))
    try:
        route_from_context(used_states, cube_support)
    except NonIdentifiableContextError:
        controls["outside_used_library_abstains"] = True
    else:
        controls["outside_used_library_abstains"] = False
    return controls


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
    states, expressions_evaluated = enumerate_program_states(initial_records)
    initial = infer_locally_stationary_path(initial_records, states)
    initial_labels = _expand_blocks(payload["audit_blocks"])
    initial_audit_correct, initial_audit_total = audit_path(
        initial, initial_labels
    )
    initial_correct, initial_covered, initial_total = evaluate_context_episodes(
        grammar,
        initial.used_states(),
        payload["episodes"],
    )

    final_records = initial_records + post_records
    final = infer_locally_stationary_path(final_records, states)
    final_labels = initial_labels + _expand_blocks(
        payload["post_freeze_audit_blocks"]
    )
    final_audit_correct, final_audit_total = audit_path(final, final_labels)
    all_episodes = tuple(payload["episodes"]) + tuple(
        payload["post_freeze_episodes"]
    )
    final_correct, final_covered, final_total = evaluate_context_episodes(
        grammar,
        final.used_states(),
        all_episodes,
    )
    old_unchanged = set(initial.fingerprint()).issubset(set(final.fingerprint()))

    no_switch_prior = infer_locally_stationary_path(
        initial_records,
        states,
        switch_penalty=0,
    )
    no_prior_correct, no_prior_total = audit_path(
        no_switch_prior, initial_labels
    )

    permutation = list(range(len(initial_records)))
    random.Random(20260713).shuffle(permutation)
    shuffled_records = tuple(initial_records[index] for index in permutation)
    shuffled_labels = tuple(initial_labels[index] for index in permutation)
    shuffled = infer_locally_stationary_path(shuffled_records, states)
    shuffled_correct, shuffled_total = audit_path(shuffled, shuffled_labels)

    doubled = infer_locally_stationary_path(
        initial_records + initial_records,
        states,
    )
    operation_ratio = (
        doubled.stats.total_operations / initial.stats.total_operations
    )
    controls = _failure_controls(grammar, final.used_states())
    source = inspect.getsource(inspect.getmodule(run))
    data_path = (
        Path(__file__).parents[2]
        / "data"
        / "phase18d7_locally_stationary_byte_stream.json"
    )
    audit_names = {
        str(block["label"])
        for block in tuple(payload["audit_blocks"])
        + tuple(payload["post_freeze_audit_blocks"])
    }

    checks = {
        "candidate_state_count": len(states) == 130,
        "initial_path_audit": initial_audit_correct == initial_audit_total,
        "final_path_audit": final_audit_correct == final_audit_total,
        "initial_used_programs": len(initial.used_states()) == 7,
        "final_used_programs": len(final.used_states()) == 8,
        "initial_context_accuracy": initial_correct == initial_total,
        "initial_context_coverage": initial_covered == initial_total,
        "final_context_accuracy": final_correct == final_total,
        "final_context_coverage": final_covered == final_total,
        "old_programs_unchanged": old_unchanged,
        "switch_prior_is_causal": no_prior_correct < no_prior_total,
        "local_stationarity_is_causal": shuffled_correct < shuffled_total,
        "linear_operation_scaling": 1.95 <= operation_ratio <= 2.05,
        "large_stream_exact_cover_absent": (
            "_exact_disjoint_cover" not in source
            and "discover_partition" not in source
        ),
        "audit_names_absent_from_source": all(
            name not in source for name in audit_names
        ),
        "failure_controls": all(controls.values()),
    }

    learned_program_bits = sum(
        state.payload_bits for state in final.used_states()
    )
    return {
        "campaign": {
            "name": "phase18d7-locally-stationary-viterbi-programs-c1",
            "training_input": "ordered UTF-8 byte records",
            "task_ids_supplied": False,
            "task_count_supplied": False,
            "boundaries_supplied": False,
            "local_stationarity_prior": True,
            "source_changes_for_appended_behavior": 0,
        },
        "induction": {
            "candidate_states": len(states),
            "expressions_evaluated_once": expressions_evaluated,
            "initial_records": len(initial_records),
            "initial_used_programs": len(initial.used_states()),
            "initial_switches": initial.switches,
            "final_records": len(final_records),
            "final_used_programs": len(final.used_states()),
            "final_switches": final.switches,
            "programs": [
                state.expression.render()
                for state in final.used_states()
            ],
        },
        "evaluation": {
            "initial_path_audit_correct": initial_audit_correct,
            "initial_path_audit_total": initial_audit_total,
            "final_path_audit_correct": final_audit_correct,
            "final_path_audit_total": final_audit_total,
            "initial_context_correct": initial_correct,
            "initial_context_covered": initial_covered,
            "initial_context_total": initial_total,
            "final_context_correct": final_correct,
            "final_context_covered": final_covered,
            "final_context_total": final_total,
            "zero_switch_prior_audit_rate": no_prior_correct / no_prior_total,
            "shuffled_stream_audit_rate": shuffled_correct / shuffled_total,
        },
        "continual_learning": {
            "old_programs_unchanged": old_unchanged,
            "new_behaviors_from_appended_bytes": len(final.used_states())
            - len(initial.used_states()),
        },
        "controls": controls,
        "resources": {
            "calibration_exact_cover_nodes": grammar.partition.stats.exact_cover_nodes,
            "large_stream_exact_cover_nodes": 0,
            "initial_viterbi_operations": initial.stats.total_operations,
            "doubled_viterbi_operations": doubled.stats.total_operations,
            "operation_ratio_2x_records": operation_ratio,
            "learned_program_bits": learned_program_bits,
            "codec_and_separator_bits": grammar.codec_payload_bits,
            "total_learned_payload_bits": learned_program_bits
            + grammar.codec_payload_bits,
            "source_bytes": len(Path(__file__).read_bytes()),
            "data_bytes": len(data_path.read_bytes()),
            "python_runtime_included": False,
        },
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {
            "locally_stationary_program_induction": all(checks.values()),
            "large_stage_without_exact_cover": all(checks.values()),
            "arbitrarily_interleaved_task_discovery": False,
            "natural_language_context_learning": False,
            "open_primitive_discovery": False,
            "llm_like_general_learning": False,
        },
        "limitations": [
            "A small Phase 18d-6 calibration prefix still uses exact cover to identify the byte codec.",
            "The large stream assumes local stationarity; this is an implicit context signal.",
            "The primitive DSL, UTF-8 atom family, error penalty, and switch penalty are human-designed.",
            "Evaluation supplies complete context records before masked queries.",
            "This is not arbitrary interleaving, natural language, code, or world-model pretraining.",
        ],
    }


def markdown(payload: Mapping[str, Any]) -> str:
    induction = payload["induction"]
    evaluation = payload["evaluation"]
    resources = payload["resources"]
    return f"""# Phase 18d-7 results: locally stationary Viterbi program induction

- Initial / final records: **{induction['initial_records']} / {induction['final_records']}**
- Candidate states: **{induction['candidate_states']}**
- Initial / final used programs: **{induction['initial_used_programs']} / {induction['final_used_programs']}**
- Initial / final path audit: **{evaluation['initial_path_audit_correct']}/{evaluation['initial_path_audit_total']} / {evaluation['final_path_audit_correct']}/{evaluation['final_path_audit_total']}**
- Initial / final context prediction: **{evaluation['initial_context_correct']}/{evaluation['initial_context_total']} / {evaluation['final_context_correct']}/{evaluation['final_context_total']}**
- Zero-switch / shuffled audit rate: **{100*evaluation['zero_switch_prior_audit_rate']:.1f}% / {100*evaluation['shuffled_stream_audit_rate']:.1f}%**
- Large-stream exact-cover nodes: **{resources['large_stream_exact_cover_nodes']}**
- Viterbi operations, N / 2N: **{resources['initial_viterbi_operations']} / {resources['doubled_viterbi_operations']}**
- 2x-record operation ratio: **{resources['operation_ratio_2x_records']:.3f}**
- Total learned payload: **{resources['total_learned_payload_bits']} bits**

The large stream is decoded with the small Phase 18d-6 codec calibration and segmented by a linear-time Viterbi dynamic program. Local persistence replaces global exact disjoint cover at the large stage. This improves scaling only under a locally stationary context assumption; it does not solve arbitrary interleaving or natural-language context learning.
"""


def main() -> None:
    payload = run()
    Path("results").mkdir(exist_ok=True)
    Path("results/phase18d7.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    Path("results/phase18d7.md").write_text(markdown(payload), encoding="utf-8")
    print(markdown(payload), end="")


if __name__ == "__main__":
    main()
