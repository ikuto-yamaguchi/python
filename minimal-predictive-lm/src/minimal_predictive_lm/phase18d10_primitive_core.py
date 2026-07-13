from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from itertools import product
import json
from typing import Any, Mapping, Sequence

from .phase18d1_dataset_to_program_meta_learner import (
    BINARY_PRIMITIVES,
    UNARY_PRIMITIVES,
    EvaluationError,
    Expr,
    _leaf_expressions,
    _probe_examples,
    canonical,
    decode_value,
    evaluate_expr,
    value_kind,
)

class NoProgramError(ValueError):
    def __init__(self, message: str, programs_evaluated: int = 0) -> None:
        super().__init__(message)
        self.programs_evaluated = programs_evaluated


class NonIdentifiableProgramError(ValueError):
    pass


class NoResidualPrimitiveError(ValueError):
    pass


class NonIdentifiablePrimitiveError(ValueError):
    pass


@dataclass(frozen=True)
class IndexAffinePrimitive:
    multiplier: int
    offset: int
    kind: str = "index_affine"

    def apply(self, value: Any) -> Any:
        if not isinstance(value, (str, tuple)):
            raise EvaluationError("index primitive requires a sequence")
        if not value:
            return value
        size = len(value)
        output = [
            value[(self.multiplier * index + self.offset) % size]
            for index in range(size)
        ]
        return "".join(output) if isinstance(value, str) else tuple(output)

    def render(self) -> Mapping[str, Any]:
        return {
            "kind": self.kind,
            "multiplier": self.multiplier,
            "offset": self.offset,
        }

    @property
    def payload_bits(self) -> int:
        return len(
            json.dumps(
                self.render(),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ) * 8


@dataclass(frozen=True)
class SequenceLookupPrimitive:
    rows: tuple[tuple[Any, Any], ...]
    kind: str = "sequence_lookup"

    def apply(self, value: Any) -> Any:
        key = canonical(value)
        for source, target in self.rows:
            if source == key:
                return target
        return value

    def render(self) -> Mapping[str, Any]:
        return {
            "kind": self.kind,
            "rows": [
                {"source": repr(source), "target": repr(target)}
                for source, target in self.rows
            ],
        }

    @property
    def payload_bits(self) -> int:
        return len(
            json.dumps(
                self.render(),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ) * 8


SequencePrimitive = IndexAffinePrimitive | SequenceLookupPrimitive


@dataclass(frozen=True)
class PrimitiveSelection:
    primitive: SequencePrimitive
    candidates_evaluated: int
    exact_candidates: int
    probe_behavior_classes: int
    training_accuracy: float
    validation_accuracy: float
    validation_episodes: int
    validation_types: int
    literal_bits: int
    model_bits: int
    compression_gain_bits: int


@dataclass(frozen=True)
class ExtendedProgram:
    task_id: str
    expression: Expr
    programs_evaluated: int
    minimum_programs: int
    probe_equivalence_classes: int

    @property
    def payload_bits(self) -> int:
        return len(self.expression.render().encode("utf-8")) * 8

    def predict(
        self,
        inputs: Mapping[str, Any],
        library: Sequence[SequencePrimitive],
    ) -> Any:
        environment = {
            name: decode_value(value)
            for name, value in inputs.items()
        }
        return evaluate_extended(self.expression, environment, library)


def _json_value(value: Any) -> Any:
    if isinstance(value, Fraction):
        if value.denominator == 1:
            return value.numerator
        return {"fraction": [value.numerator, value.denominator]}
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    return value


def _base_apply(operation: str, values: Sequence[Any]) -> Any:
    constants = tuple(
        Expr(
            "CONST",
            atom=value,
            result_type=value_kind(value),
        )
        for value in values
    )
    return evaluate_expr(Expr(operation, constants), {})


def evaluate_extended(
    expression: Expr,
    environment: Mapping[str, Any],
    library: Sequence[SequencePrimitive],
) -> Any:
    if expression.op == "VAR":
        return environment[expression.atom]
    if expression.op == "CONST":
        return expression.atom
    values = [
        evaluate_extended(argument, environment, library)
        for argument in expression.args
    ]
    if expression.op.startswith("INVENTED_"):
        index = int(expression.op.removeprefix("INVENTED_"))
        try:
            return library[index].apply(values[0])
        except IndexError as exc:
            raise EvaluationError("unknown invented primitive") from exc
    return _base_apply(expression.op, values)


def _extended_signature(
    expression: Expr,
    examples: Sequence[Mapping[str, Any]],
    library: Sequence[SequencePrimitive],
) -> tuple[Any, ...]:
    output: list[Any] = []
    for example in examples:
        environment = {
            name: decode_value(value)
            for name, value in example["inputs"].items()
        }
        try:
            prediction = evaluate_extended(expression, environment, library)
        except EvaluationError:
            output.append(("ERROR",))
        else:
            output.append(canonical(prediction))
    return tuple(output)


def enumerate_extended_expressions(
    input_types: Mapping[str, str],
    output_type: str,
    max_cost: int,
    library: Sequence[SequencePrimitive],
) -> dict[int, list[Expr]]:
    by_cost: dict[int, list[Expr]] = {
        1: _leaf_expressions(input_types, output_type)
    }
    for cost in range(2, max_cost + 1):
        expressions: list[Expr] = []

        for operation, (accepted, result_type) in UNARY_PRIMITIVES.items():
            for child in by_cost.get(cost - 1, ()):
                if child.result_type in accepted:
                    expressions.append(
                        Expr(operation, (child,), result_type=result_type)
                    )

        for index, _primitive in enumerate(library):
            for child in by_cost.get(cost - 1, ()):
                if child.result_type in {"string", "number_list"}:
                    expressions.append(
                        Expr(
                            f"INVENTED_{index}",
                            (child,),
                            result_type=child.result_type,
                        )
                    )

        for left_cost in range(1, cost - 1):
            right_cost = cost - 1 - left_cost
            for operation, (argument_types, result_type) in BINARY_PRIMITIVES.items():
                for left in by_cost.get(left_cost, ()):
                    if left.result_type != argument_types[0]:
                        continue
                    for right in by_cost.get(right_cost, ()):
                        if right.result_type == argument_types[1]:
                            expressions.append(
                                Expr(
                                    operation,
                                    (left, right),
                                    result_type=result_type,
                                )
                            )

        by_cost[cost] = list(
            {
                expression.render(): expression
                for expression in expressions
            }.values()
        )
    return by_cost


def synthesize_extended_program(
    task: Mapping[str, Any],
    library: Sequence[SequencePrimitive],
    *,
    max_cost: int = 5,
) -> ExtendedProgram:
    training = tuple(task["train"])
    if not training:
        raise NoProgramError("no training examples")

    variable_names = tuple(training[0]["inputs"])
    input_types = {
        name: value_kind(decode_value(training[0]["inputs"][name]))
        for name in variable_names
    }
    output_type = value_kind(decode_value(training[0]["output"]))
    target = tuple(
        canonical(decode_value(example["output"]))
        for example in training
    )
    by_cost = enumerate_extended_expressions(
        input_types,
        output_type,
        max_cost,
        library,
    )
    programs_evaluated = 0

    for cost in range(1, max_cost + 1):
        candidates: list[Expr] = []
        for expression in by_cost[cost]:
            if expression.result_type != output_type:
                continue
            programs_evaluated += 1
            if _extended_signature(expression, training, library) == target:
                candidates.append(expression)
        if not candidates:
            continue

        probe_examples = _probe_examples(input_types)
        equivalence_classes: dict[tuple[Any, ...], list[Expr]] = defaultdict(list)
        for candidate in candidates:
            equivalence_classes[
                _extended_signature(candidate, probe_examples, library)
            ].append(candidate)
        if len(equivalence_classes) != 1:
            raise NonIdentifiableProgramError(
                f"minimum cost {cost}: {len(candidates)} programs, "
                f"{len(equivalence_classes)} probe-distinct behaviors"
            )
        chosen = min(candidates, key=lambda expression: expression.render())
        return ExtendedProgram(
            task_id=str(task["id"]),
            expression=chosen,
            programs_evaluated=programs_evaluated,
            minimum_programs=len(candidates),
            probe_equivalence_classes=len(equivalence_classes),
        )
    raise NoProgramError(
        f"no expression through cost {max_cost}; "
        f"evaluated={programs_evaluated}",
        programs_evaluated,
    )


def _flatten_examples(
    episodes: Sequence[Mapping[str, Any]],
    split: str,
) -> tuple[tuple[str, Any, Any], ...]:
    output: list[tuple[str, Any, Any]] = []
    for episode in episodes:
        for example in episode[split]:
            if len(example["inputs"]) != 1:
                raise ValueError("primitive residual episodes require one input")
            source = decode_value(next(iter(example["inputs"].values())))
            target = decode_value(example["output"])
            if value_kind(source) not in {"string", "number_list"}:
                raise ValueError("primitive residual requires a sequence")
            if value_kind(source) != value_kind(target):
                raise ValueError("primitive residual must preserve sequence type")
            if len(source) != len(target):
                raise ValueError("primitive residual must preserve length")
            output.append((str(episode["id"]), source, target))
    return tuple(output)


def _primitive_accuracy(
    primitive: SequencePrimitive,
    rows: Sequence[tuple[str, Any, Any]],
) -> float:
    if not rows:
        raise ValueError("primitive accuracy requires examples")
    return sum(
        primitive.apply(source) == target
        for _, source, target in rows
    ) / len(rows)


def _literal_bits(rows: Sequence[tuple[str, Any, Any]]) -> int:
    payload = [
        {
            "episode": episode,
            "source": _json_value(source),
            "target": _json_value(target),
        }
        for episode, source, target in rows
    ]
    return len(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ) * 8


def propose_sequence_primitives(
    episodes: Sequence[Mapping[str, Any]],
) -> tuple[SequencePrimitive, ...]:
    training = _flatten_examples(episodes, "train")
    validation = _flatten_examples(episodes, "validation")
    all_rows = training + validation
    if not all_rows:
        raise NoResidualPrimitiveError("no residual examples")

    lookup = SequenceLookupPrimitive(
        tuple(
            (canonical(source), target)
            for _, source, target in training
        )
    )
    maximum_length = max(len(source) for _, source, _ in all_rows)
    candidates: list[SequencePrimitive] = [lookup]
    for multiplier in range(-maximum_length - 1, maximum_length + 2):
        for offset in range(-maximum_length - 1, maximum_length + 2):
            candidates.append(IndexAffinePrimitive(multiplier, offset))
    return tuple(candidates)


def _primitive_probe_signature(primitive: SequencePrimitive) -> tuple[Any, ...]:
    probes: tuple[Any, ...] = (
        "abcdef",
        tuple(Fraction(value) for value in (1, 2, 3, 4, 5, 6)),
    )
    return tuple(canonical(primitive.apply(value)) for value in probes)


def select_reusable_primitive(
    episodes: Sequence[Mapping[str, Any]],
    *,
    minimum_validation_episodes: int = 2,
    minimum_validation_types: int = 2,
    call_bits_per_example: int = 24,
) -> PrimitiveSelection:
    training = _flatten_examples(episodes, "train")
    validation = _flatten_examples(episodes, "validation")
    validation_episodes = len({episode for episode, _, _ in validation})
    validation_types = len({value_kind(source) for _, source, _ in validation})
    if validation_episodes < minimum_validation_episodes:
        raise NoResidualPrimitiveError("insufficient cross-episode validation")
    if validation_types < minimum_validation_types:
        raise NoResidualPrimitiveError("insufficient cross-type validation")

    candidates = propose_sequence_primitives(episodes)
    exact = [
        primitive
        for primitive in candidates
        if _primitive_accuracy(primitive, training) == 1.0
        and _primitive_accuracy(primitive, validation) == 1.0
    ]
    if not exact:
        raise NoResidualPrimitiveError("no primitive survives validation")

    behavior_classes: dict[tuple[Any, ...], list[SequencePrimitive]] = defaultdict(list)
    for primitive in exact:
        behavior_classes[_primitive_probe_signature(primitive)].append(primitive)
    if len(behavior_classes) != 1:
        raise NonIdentifiablePrimitiveError(
            f"{len(exact)} exact primitives form "
            f"{len(behavior_classes)} probe-distinct behaviors"
        )

    chosen = min(
        exact,
        key=lambda primitive: (
            primitive.payload_bits,
            json.dumps(
                primitive.render(),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
    )
    rows = training + validation
    literal_bits = _literal_bits(rows)
    model_bits = chosen.payload_bits + call_bits_per_example * len(rows)
    compression_gain = literal_bits - model_bits
    if compression_gain <= 0:
        raise NoResidualPrimitiveError("primitive has no positive MDL gain")

    return PrimitiveSelection(
        primitive=chosen,
        candidates_evaluated=len(candidates),
        exact_candidates=len(exact),
        probe_behavior_classes=len(behavior_classes),
        training_accuracy=_primitive_accuracy(chosen, training),
        validation_accuracy=_primitive_accuracy(chosen, validation),
        validation_episodes=validation_episodes,
        validation_types=validation_types,
        literal_bits=literal_bits,
        model_bits=model_bits,
        compression_gain_bits=compression_gain,
    )
