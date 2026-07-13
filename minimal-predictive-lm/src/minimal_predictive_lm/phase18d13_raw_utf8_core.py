from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping, Protocol, Sequence

from .phase18d10_primitive_core import IndexAffinePrimitive
from .phase18d12_multi_primitive_core import ElementAffinePrimitive
from .phase18d13_raw_utf8_grammar import (
    NoGrammarError,
    RawGrammar,
    alphabet_family,
    canonical,
    decode_hex,
    infer_grammar,
)


class NoPromotablePrimitiveError(ValueError):
    pass


class RawPrimitive(Protocol):
    def apply(self, value: str) -> str: ...
    def render(self) -> Mapping[str, Any]: ...
    @property
    def payload_bits(self) -> int: ...


@dataclass(frozen=True)
class RawLookupPrimitive:
    rows: tuple[tuple[str, str], ...]
    kind: str = "raw_lookup"

    def apply(self, value: str) -> str:
        return dict(self.rows).get(value, value)

    def render(self) -> Mapping[str, Any]:
        return {"kind": self.kind, "rows": [list(row) for row in self.rows]}

    @property
    def payload_bits(self) -> int:
        return len(json.dumps(self.render(), ensure_ascii=False,
                              sort_keys=True, separators=(",", ":")).encode()) * 8


@dataclass(frozen=True)
class RawResidual:
    position: int
    source: str
    target: str


@dataclass(frozen=True)
class RawPromotion:
    position: int
    primitive: RawPrimitive
    support_positions: tuple[int, ...]
    support_alphabets: tuple[str, ...]
    candidates_evaluated: int
    literal_bits: int
    model_bits: int
    mdl_gain_bits: int


@dataclass(frozen=True)
class RawOnlineResult:
    grammar: RawGrammar
    predictions: tuple[str | None, ...]
    observed_operations: tuple[str | None, ...]
    unresolved_positions: tuple[int, ...]
    promotions: tuple[RawPromotion, ...]
    library: tuple[RawPrimitive, ...]
    candidates_evaluated: int


def base_operations(value: str) -> Mapping[str, str]:
    return {"IDENTITY": value, "UPPER": value.upper(), "LOWER": value.lower(),
            "REVERSE": value[::-1], "SORT": "".join(sorted(value))}


def _predictions(value: str, library: Sequence[RawPrimitive]):
    output = dict(base_operations(value))
    for index, primitive in enumerate(library):
        try:
            prediction = primitive.apply(value)
        except (TypeError, ValueError):
            continue
        if isinstance(prediction, str):
            output[f"INVENTED_{index}"] = prediction
    return output


def _literal_bits(rows: Sequence[RawResidual]) -> int:
    payload = [{"position": r.position, "source": r.source, "target": r.target}
               for r in rows]
    return len(json.dumps(payload, ensure_ascii=False,
                          separators=(",", ":")).encode()) * 8


def _candidates(rows: Sequence[RawResidual]) -> tuple[RawPrimitive, ...]:
    maximum = max(len(row.source) for row in rows)
    output: list[RawPrimitive] = [
        RawLookupPrimitive(tuple((row.source, row.target) for row in rows))
    ]
    output.extend(IndexAffinePrimitive(a, b)
                  for a in range(-maximum - 1, maximum + 2)
                  for b in range(-maximum - 1, maximum + 2))
    output.extend(ElementAffinePrimitive(scale, offset)
                  for scale in (-1, 0, 1) for offset in range(-3, 4))
    return tuple(output)


def _probe(primitive: RawPrimitive):
    probes = ("abcdefg", "".join(chr(0xE600 + x)
                                   for x in (1, 3, 6, 10, 15, 21, 28)))
    output = []
    for probe in probes:
        try:
            output.append(canonical(primitive.apply(probe)))
        except (TypeError, ValueError):
            output.append(("ERROR",))
    return tuple(output)


def _support(primitive: RawPrimitive, rows: Sequence[RawResidual]):
    output = []
    for row in rows:
        try:
            prediction = primitive.apply(row.source)
        except (TypeError, ValueError):
            continue
        if isinstance(prediction, str) and canonical(prediction) == canonical(row.target):
            output.append(row)
    return tuple(output)


def select_next_primitive(rows: Sequence[RawResidual],
                          existing_library: Sequence[RawPrimitive] = (), *,
                          minimum_support: int = 6,
                          minimum_alphabets: int = 2,
                          call_bits: int = 20) -> RawPromotion:
    rows = tuple(rows)
    if len(rows) < minimum_support:
        raise NoPromotablePrimitiveError("insufficient support")
    candidates = _candidates(rows)
    blocked = {_probe(p) for p in existing_library}
    blocked.add(_probe(RawLookupPrimitive(())))
    literal = _literal_bits(rows)
    scored = []
    for primitive in candidates:
        behavior = _probe(primitive)
        if behavior in blocked:
            continue
        support = _support(primitive, rows)
        alphabets = {alphabet_family(row.source) for row in support}
        if len(support) < minimum_support or len(alphabets) < minimum_alphabets:
            continue
        unsupported = tuple(row for row in rows if row not in support)
        model = primitive.payload_bits + call_bits * len(support) + _literal_bits(unsupported)
        gain = literal - model
        if gain > 0:
            scored.append((gain, behavior, primitive, support, model))
    if not scored:
        raise NoPromotablePrimitiveError("no reusable raw cluster")
    gain = max(row[0] for row in scored)
    best = [row for row in scored if row[0] == gain]
    if len({row[1] for row in best}) != 1:
        raise NoPromotablePrimitiveError("top raw cluster is ambiguous")
    _, _, primitive, support, model = min(
        best, key=lambda row: (row[2].payload_bits,
                               json.dumps(row[2].render(), sort_keys=True)))
    return RawPromotion(max(row.position for row in rows), primitive,
                        tuple(row.position for row in support),
                        tuple(sorted({alphabet_family(row.source) for row in support})),
                        len(candidates), literal, model, gain)


def online_learn_records(records: Sequence[tuple[str, str]], *,
                         minimum_support: int = 6):
    unresolved: list[RawResidual] = []
    promotions: list[RawPromotion] = []
    library: list[RawPrimitive] = []
    predictions: list[str | None] = []
    operations: list[str | None] = []
    current: str | None = None
    evaluated = 0
    for position, (source, target) in enumerate(records):
        available = _predictions(source, library)
        predictions.append(available.get(current) if current is not None else None)
        matches = tuple(name for name, prediction in available.items()
                        if canonical(prediction) == canonical(target))
        if current in matches:
            observed = current
        elif matches:
            base = tuple(name for name in matches if not name.startswith("INVENTED_"))
            observed = base[0] if len(base) == 1 else matches[0] if len(matches) == 1 else min(matches)
        else:
            observed = None
            unresolved.append(RawResidual(position, source, target))
            while True:
                try:
                    promotion = select_next_primitive(
                        unresolved, library, minimum_support=minimum_support)
                except NoPromotablePrimitiveError:
                    break
                library.append(promotion.primitive)
                promotions.append(promotion)
                evaluated += promotion.candidates_evaluated
                supported = set(promotion.support_positions)
                unresolved = [row for row in unresolved if row.position not in supported]
                try:
                    prediction = promotion.primitive.apply(source)
                except (TypeError, ValueError):
                    prediction = None
                if isinstance(prediction, str) and canonical(prediction) == canonical(target):
                    observed = f"INVENTED_{len(library) - 1}"
        operations.append(observed)
        current = observed
    return (tuple(predictions), tuple(operations), tuple(unresolved),
            tuple(promotions), tuple(library), evaluated)


def learn_raw_stream(stream_hex: str, *, minimum_support: int = 6) -> RawOnlineResult:
    grammar = infer_grammar(stream_hex)
    predictions, operations, unresolved, promotions, library, evaluated = \
        online_learn_records(grammar.records, minimum_support=minimum_support)
    return RawOnlineResult(grammar, predictions, operations,
                           tuple(row.position for row in unresolved),
                           promotions, library, evaluated)


def metrics(result: RawOnlineResult) -> Mapping[str, Any]:
    correct = wrong = abstained = 0
    wrong_positions = []
    for position, (prediction, (_, target)) in enumerate(
            zip(result.predictions, result.grammar.records)):
        if prediction is None:
            abstained += 1
        elif canonical(prediction) == canonical(target):
            correct += 1
        else:
            wrong += 1
            wrong_positions.append(position)
    covered = correct + wrong
    return {"correct": correct, "wrong": wrong, "abstained": abstained,
            "coverage": covered / len(result.grammar.records),
            "covered_accuracy": correct / covered if covered else 0.0,
            "wrong_positions": wrong_positions}
