from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Iterable, Protocol, Sequence


@dataclass(frozen=True)
class StringTransformExample:
    family: str
    source: str
    target: str


class StringPrimitive(Protocol):
    kind: str

    def apply(self, value: str) -> str:
        ...

    def render(self) -> object:
        ...

    @property
    def description_bits(self) -> int:
        ...


def _description_bits(payload: object) -> int:
    return len(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ) * 8


@dataclass(frozen=True)
class LookupPrimitive:
    rows: tuple[tuple[str, str], ...]
    kind: str = "lookup"

    def apply(self, value: str) -> str:
        return dict(self.rows).get(value, value)

    def render(self) -> object:
        return {"kind": self.kind, "rows": [list(row) for row in self.rows]}

    @property
    def description_bits(self) -> int:
        return _description_bits(self.render())


@dataclass(frozen=True)
class CharacterMapPrimitive:
    rows: tuple[tuple[int, int], ...]
    kind: str = "character_map"

    def apply(self, value: str) -> str:
        table = dict(self.rows)
        return "".join(chr(table.get(ord(character), ord(character))) for character in value)

    def render(self) -> object:
        return {"kind": self.kind, "rows": [list(row) for row in self.rows]}

    @property
    def description_bits(self) -> int:
        return _description_bits(self.render())


@dataclass(frozen=True)
class AffineCharacterPrimitive:
    lower_codepoint: int
    upper_codepoint: int
    offset: int
    kind: str = "conditional_character_offset"

    def apply(self, value: str) -> str:
        output: list[str] = []
        for character in value:
            codepoint = ord(character)
            if self.lower_codepoint <= codepoint <= self.upper_codepoint:
                output.append(chr(codepoint + self.offset))
            else:
                output.append(character)
        return "".join(output)

    def render(self) -> object:
        return {
            "kind": self.kind,
            "lower_codepoint": self.lower_codepoint,
            "upper_codepoint": self.upper_codepoint,
            "offset": self.offset,
        }

    @property
    def description_bits(self) -> int:
        return _description_bits(self.render())


@dataclass(frozen=True)
class PrimitiveProposal:
    primitive: StringPrimitive
    training_accuracy: float
    validation_accuracy: float
    validation_families: tuple[str, ...]


@dataclass(frozen=True)
class PrimitiveAdoptionDecision:
    adopted: bool
    primitive_bits: int
    validation_bits: int
    migration_bits: int
    expected_future_calls: int
    error_reduction: float
    error_cost_bits: int
    normalized_lifetime_gain_bits: int


@dataclass(frozen=True)
class InventedStringProgram:
    primitive: StringPrimitive
    argument_index: int = 0

    def execute(self, arguments: Sequence[str]) -> str:
        return self.primitive.apply(arguments[self.argument_index])

    @property
    def description_bits(self) -> int:
        payload = {
            "op": "APPLY_INVENTED_PRIMITIVE",
            "argument_index": self.argument_index,
            "primitive": self.primitive.render(),
        }
        return _description_bits(payload)


def primitive_accuracy(
    primitive: StringPrimitive,
    examples: Iterable[StringTransformExample],
) -> float:
    items = tuple(examples)
    if not items:
        raise ValueError("at least one example is required")
    correct = sum(primitive.apply(example.source) == example.target for example in items)
    return correct / len(items)


def _aligned_character_pairs(
    examples: Sequence[StringTransformExample],
) -> tuple[tuple[int, int], ...] | None:
    rows: list[tuple[int, int]] = []
    for example in examples:
        if len(example.source) != len(example.target):
            return None
        rows.extend((ord(left), ord(right)) for left, right in zip(example.source, example.target))
    return tuple(rows)


def propose_string_primitives(
    examples: Iterable[StringTransformExample],
) -> tuple[StringPrimitive, ...]:
    items = tuple(examples)
    if not items:
        raise ValueError("at least one example is required")

    candidates: list[StringPrimitive] = [
        LookupPrimitive(tuple(sorted((example.source, example.target) for example in items)))
    ]
    pairs = _aligned_character_pairs(items)
    if pairs is None:
        return tuple(candidates)

    mapping: dict[int, int] = {}
    consistent = True
    for source, target in pairs:
        previous = mapping.get(source)
        if previous is not None and previous != target:
            consistent = False
            break
        mapping[source] = target
    if consistent:
        candidates.append(CharacterMapPrimitive(tuple(sorted(mapping.items()))))

    changed = tuple((source, target) for source, target in pairs if source != target)
    if changed:
        offsets = {target - source for source, target in changed}
        changed_sources = {source for source, _ in changed}
        if len(offsets) == 1:
            lower = min(changed_sources)
            upper = max(changed_sources)
            offset = next(iter(offsets))
            affine = AffineCharacterPrimitive(lower, upper, offset)
            if primitive_accuracy(affine, items) == 1.0:
                candidates.append(affine)

    unique: dict[str, StringPrimitive] = {}
    for candidate in candidates:
        key = json.dumps(candidate.render(), ensure_ascii=False, sort_keys=True)
        incumbent = unique.get(key)
        if incumbent is None or candidate.description_bits < incumbent.description_bits:
            unique[key] = candidate
    return tuple(
        sorted(unique.values(), key=lambda candidate: (candidate.description_bits, candidate.kind))
    )


def evaluate_primitive_proposals(
    training: Iterable[StringTransformExample],
    validation: Iterable[StringTransformExample],
) -> tuple[PrimitiveProposal, ...]:
    training_items = tuple(training)
    validation_items = tuple(validation)
    families = tuple(sorted({example.family for example in validation_items}))
    return tuple(
        PrimitiveProposal(
            candidate,
            primitive_accuracy(candidate, training_items),
            primitive_accuracy(candidate, validation_items),
            families,
        )
        for candidate in propose_string_primitives(training_items)
    )


def select_reusable_primitive(
    training: Iterable[StringTransformExample],
    validation: Iterable[StringTransformExample],
    *,
    minimum_validation_families: int = 2,
) -> PrimitiveProposal:
    proposals = evaluate_primitive_proposals(training, validation)
    valid = [
        proposal
        for proposal in proposals
        if proposal.training_accuracy == 1.0
        and proposal.validation_accuracy == 1.0
        and len(proposal.validation_families) >= minimum_validation_families
    ]
    if not valid:
        raise ValueError("no primitive survives cross-family validation")
    return min(
        valid,
        key=lambda proposal: (
            proposal.primitive.description_bits,
            proposal.primitive.kind,
        ),
    )


def validation_payload_bits(examples: Iterable[StringTransformExample]) -> int:
    payload = [
        {"family": example.family, "source": example.source, "target": example.target}
        for example in examples
    ]
    return _description_bits(payload)


def decide_primitive_adoption(
    proposal: PrimitiveProposal,
    validation: Iterable[StringTransformExample],
    *,
    expected_future_calls: int,
    baseline_error_rate: float,
    error_cost_bits: int = 64,
    migration_bits: int = 128,
) -> PrimitiveAdoptionDecision:
    if not 0.0 <= baseline_error_rate <= 1.0:
        raise ValueError("baseline_error_rate must be in [0, 1]")
    if expected_future_calls < 0:
        raise ValueError("expected_future_calls must be non-negative")
    validation_bits = validation_payload_bits(validation)
    error_reduction = max(0.0, baseline_error_rate - (1.0 - proposal.validation_accuracy))
    benefit = round(expected_future_calls * error_reduction * error_cost_bits)
    cost = proposal.primitive.description_bits + validation_bits + migration_bits
    gain = benefit - cost
    return PrimitiveAdoptionDecision(
        adopted=gain > 0 and proposal.validation_accuracy == 1.0,
        primitive_bits=proposal.primitive.description_bits,
        validation_bits=validation_bits,
        migration_bits=migration_bits,
        expected_future_calls=expected_future_calls,
        error_reduction=error_reduction,
        error_cost_bits=error_cost_bits,
        normalized_lifetime_gain_bits=gain,
    )
