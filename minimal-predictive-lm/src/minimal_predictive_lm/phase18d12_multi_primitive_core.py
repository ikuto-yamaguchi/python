from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import json
from typing import Any, Mapping, Protocol, Sequence

from .phase18d10_primitive_core import (
    IndexAffinePrimitive,
    SequenceLookupPrimitive,
)
from .phase18d11_ungrouped_online_residual import (
    ResidualRow,
    base_operations,
    canonical,
    decode,
    encode,
    kind,
)


class NoPromotablePrimitiveError(ValueError):
    pass


class SequencePrimitive(Protocol):
    def apply(self, value: Any) -> Any: ...
    def render(self) -> Mapping[str, Any]: ...
    @property
    def payload_bits(self) -> int: ...


@dataclass(frozen=True)
class ElementAffinePrimitive:
    scale: int
    offset: int
    kind: str = "element_affine"

    def apply(self, value: Any) -> Any:
        if isinstance(value, str):
            output = []
            for character in value:
                codepoint = self.scale * ord(character) + self.offset
                if not 0 <= codepoint <= 0x10FFFF:
                    raise ValueError("invalid Unicode codepoint")
                output.append(chr(codepoint))
            return "".join(output)
        if isinstance(value, tuple):
            return tuple(
                Fraction(self.scale) * item + Fraction(self.offset)
                for item in value
            )
        raise TypeError("element primitive requires a sequence")

    def render(self) -> Mapping[str, Any]:
        return {
            "kind": self.kind,
            "scale": self.scale,
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
class Promotion:
    position: int
    primitive: SequencePrimitive
    support_positions: tuple[int, ...]
    support_types: tuple[str, ...]
    candidates_evaluated: int
    behavior_classes: int
    literal_bits: int
    model_bits: int
    mdl_gain_bits: int


@dataclass(frozen=True)
class OnlineResult:
    predictions: tuple[Any | None, ...]
    observed_operations: tuple[str | None, ...]
    unresolved_positions: tuple[int, ...]
    promotions: tuple[Promotion, ...]
    library: tuple[SequencePrimitive, ...]
    candidates_evaluated: int


def _operation_predictions(
    value: Any,
    library: Sequence[SequencePrimitive],
) -> Mapping[str, Any]:
    output = dict(base_operations(value))
    for index, primitive in enumerate(library):
        try:
            output[f"INVENTED_{index}"] = primitive.apply(value)
        except (TypeError, ValueError):
            continue
    return output


def _matching_operations(
    value: Any,
    target: Any,
    library: Sequence[SequencePrimitive],
) -> tuple[str, ...]:
    return tuple(
        name
        for name, prediction in _operation_predictions(value, library).items()
        if canonical(prediction) == canonical(target)
    )


def _literal_bits(rows: Sequence[ResidualRow]) -> int:
    payload = [
        {
            "position": row.position,
            "source": encode(row.source),
            "target": encode(row.target),
        }
        for row in rows
    ]
    return len(
        json.dumps(
            payload,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ) * 8


def _candidate_primitives(
    rows: Sequence[ResidualRow],
) -> tuple[SequencePrimitive, ...]:
    maximum_length = max(len(row.source) for row in rows)
    lookup = SequenceLookupPrimitive(
        tuple((canonical(row.source), row.target) for row in rows)
    )
    candidates: list[SequencePrimitive] = [lookup]
    for multiplier in range(-maximum_length - 1, maximum_length + 2):
        for offset in range(-maximum_length - 1, maximum_length + 2):
            candidates.append(IndexAffinePrimitive(multiplier, offset))
    for scale in (-1, 0, 1):
        for offset in range(-3, 4):
            candidates.append(ElementAffinePrimitive(scale, offset))
    return tuple(candidates)


def _probe_signature(primitive: SequencePrimitive) -> tuple[Any, ...]:
    probes: tuple[Any, ...] = (
        "abcdefg",
        tuple(Fraction(value) for value in (1, 3, 6, 10, 15, 21, 28)),
    )
    output = []
    for probe in probes:
        try:
            output.append(canonical(primitive.apply(probe)))
        except (TypeError, ValueError):
            output.append(("ERROR",))
    return tuple(output)


def _support(
    primitive: SequencePrimitive,
    rows: Sequence[ResidualRow],
) -> tuple[ResidualRow, ...]:
    supported = []
    for row in rows:
        try:
            prediction = primitive.apply(row.source)
        except (TypeError, ValueError):
            continue
        if canonical(prediction) == canonical(row.target):
            supported.append(row)
    return tuple(supported)


def select_next_primitive(
    rows: Sequence[ResidualRow],
    existing_library: Sequence[SequencePrimitive] = (),
    *,
    minimum_support: int = 6,
    minimum_types: int = 2,
    call_bits: int = 20,
) -> Promotion:
    rows = tuple(rows)
    if len(rows) < minimum_support:
        raise NoPromotablePrimitiveError("insufficient residual support")
    candidates = _candidate_primitives(rows)
    existing_behaviors = {
        _probe_signature(primitive)
        for primitive in existing_library
    }
    literal_all = _literal_bits(rows)
    scored = []
    for primitive in candidates:
        behavior = _probe_signature(primitive)
        if behavior in existing_behaviors:
            continue
        support = _support(primitive, rows)
        support_types = {kind(row.source) for row in support}
        if len(support) < minimum_support or len(support_types) < minimum_types:
            continue
        unsupported = tuple(row for row in rows if row not in support)
        model_bits = (
            primitive.payload_bits
            + call_bits * len(support)
            + _literal_bits(unsupported)
        )
        gain = literal_all - model_bits
        if gain > 0:
            scored.append((gain, behavior, primitive, support, model_bits))
    if not scored:
        raise NoPromotablePrimitiveError("no reusable residual cluster")
    best_gain = max(row[0] for row in scored)
    best = [row for row in scored if row[0] == best_gain]
    behavior_classes = {row[1] for row in best}
    if len(behavior_classes) != 1:
        raise NoPromotablePrimitiveError(
            "top residual cluster is behaviorally ambiguous"
        )
    gain, _, primitive, support, model_bits = min(
        best,
        key=lambda row: (
            row[2].payload_bits,
            json.dumps(row[2].render(), sort_keys=True),
        ),
    )
    return Promotion(
        position=max(row.position for row in rows),
        primitive=primitive,
        support_positions=tuple(row.position for row in support),
        support_types=tuple(sorted({kind(row.source) for row in support})),
        candidates_evaluated=len(candidates),
        behavior_classes=len(behavior_classes),
        literal_bits=literal_all,
        model_bits=model_bits,
        mdl_gain_bits=gain,
    )


def online_learn(
    records: Sequence[Mapping[str, Any]],
    *,
    minimum_support: int = 6,
) -> OnlineResult:
    unresolved: list[ResidualRow] = []
    library: list[SequencePrimitive] = []
    promotions: list[Promotion] = []
    current_operation: str | None = None
    predictions: list[Any | None] = []
    observed_operations: list[str | None] = []
    candidates_evaluated = 0

    for position, raw in enumerate(records):
        source = decode(raw["input"])
        target = decode(raw["output"])
        operations = _operation_predictions(source, library)
        predictions.append(
            operations.get(current_operation)
            if current_operation is not None
            else None
        )

        matches = _matching_operations(source, target, library)
        if current_operation in matches:
            observed = current_operation
        elif matches:
            base_matches = tuple(
                name for name in matches if not name.startswith("INVENTED_")
            )
            if len(base_matches) == 1:
                observed = base_matches[0]
            elif len(matches) == 1:
                observed = matches[0]
            else:
                observed = min(matches)
        else:
            observed = None
            unresolved.append(ResidualRow(position, source, target))
            while True:
                try:
                    promotion = select_next_primitive(
                        unresolved,
                        library,
                        minimum_support=minimum_support,
                    )
                except NoPromotablePrimitiveError:
                    break
                library.append(promotion.primitive)
                promotions.append(promotion)
                candidates_evaluated += promotion.candidates_evaluated
                supported = set(promotion.support_positions)
                unresolved = [
                    row for row in unresolved
                    if row.position not in supported
                ]
                try:
                    promoted_prediction = promotion.primitive.apply(source)
                except (TypeError, ValueError):
                    promoted_prediction = None
                if (
                    promoted_prediction is not None
                    and canonical(promoted_prediction) == canonical(target)
                ):
                    observed = f"INVENTED_{len(library) - 1}"
        observed_operations.append(observed)
        current_operation = observed

    return OnlineResult(
        tuple(predictions),
        tuple(observed_operations),
        tuple(row.position for row in unresolved),
        tuple(promotions),
        tuple(library),
        candidates_evaluated,
    )


def metrics(
    result: OnlineResult,
    records: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any]:
    correct = wrong = abstained = 0
    wrong_positions = []
    for position, (prediction, raw) in enumerate(
        zip(result.predictions, records)
    ):
        target = decode(raw["output"])
        if prediction is None:
            abstained += 1
        elif canonical(prediction) == canonical(target):
            correct += 1
        else:
            wrong += 1
            wrong_positions.append(position)
    covered = correct + wrong
    return {
        "correct": correct,
        "wrong": wrong,
        "abstained": abstained,
        "coverage": covered / len(records),
        "covered_accuracy": correct / covered if covered else 0.0,
        "wrong_positions": wrong_positions,
    }
