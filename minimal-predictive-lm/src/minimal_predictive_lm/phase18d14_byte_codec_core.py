from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping, Protocol, Sequence

from .phase18d10_primitive_core import IndexAffinePrimitive
from .phase18d12_multi_primitive_core import ElementAffinePrimitive
from .phase18d13_raw_utf8_core import online_learn_records
from .phase18d13_raw_utf8_grammar import alphabet_family, canonical


class NoJointModelError(ValueError):
    pass


class ByteCodec(Protocol):
    kind: str
    def decode(self, payload: bytes) -> str | None: ...
    def encode(self, value: str) -> bytes: ...
    def render(self) -> Mapping[str, Any]: ...
    @property
    def payload_bits(self) -> int: ...


@dataclass(frozen=True)
class SingleByteCodec:
    kind: str = "single_byte"

    def decode(self, payload: bytes) -> str | None:
        return "".join(chr(byte) for byte in payload) or None

    def encode(self, value: str) -> bytes:
        return bytes(ord(character) for character in value)

    def render(self) -> Mapping[str, Any]:
        return {"kind": self.kind}

    @property
    def payload_bits(self) -> int:
        return 8


@dataclass(frozen=True)
class TaggedByteCodec:
    marker: int
    kind: str = "tagged_mixed_width"

    def decode(self, payload: bytes) -> str | None:
        output = []
        index = 0
        while index < len(payload):
            byte = payload[index]
            if byte == self.marker:
                if index + 1 >= len(payload):
                    return None
                output.append(chr(0xE000 + payload[index + 1]))
                index += 2
            else:
                output.append(chr(byte))
                index += 1
        return "".join(output) or None

    def encode(self, value: str) -> bytes:
        output = bytearray()
        for character in value:
            codepoint = ord(character)
            if 0xE000 <= codepoint <= 0xE0FF:
                output.extend((self.marker, codepoint - 0xE000))
            elif codepoint <= 0xFF:
                output.append(codepoint)
            else:
                raise ValueError("unsupported tagged symbol")
        return bytes(output)

    def render(self) -> Mapping[str, Any]:
        return {"kind": self.kind, "marker": self.marker}

    @property
    def payload_bits(self) -> int:
        return 16


@dataclass(frozen=True)
class PrefixedPairCodec:
    raw_prefix: int
    tagged_prefix: int
    kind: str = "prefixed_fixed_width_2"

    def decode(self, payload: bytes) -> str | None:
        if not payload or len(payload) % 2:
            return None
        output = []
        for index in range(0, len(payload), 2):
            prefix, value = payload[index], payload[index + 1]
            if prefix == self.raw_prefix:
                output.append(chr(value))
            elif prefix == self.tagged_prefix:
                output.append(chr(0xE000 + value))
            else:
                return None
        return "".join(output)

    def encode(self, value: str) -> bytes:
        output = bytearray()
        for character in value:
            codepoint = ord(character)
            if 0xE000 <= codepoint <= 0xE0FF:
                output.extend((self.tagged_prefix, codepoint - 0xE000))
            elif codepoint <= 0xFF:
                output.extend((self.raw_prefix, codepoint))
            else:
                raise ValueError("unsupported pair symbol")
        return bytes(output)

    def render(self) -> Mapping[str, Any]:
        return {
            "kind": self.kind,
            "raw_prefix": self.raw_prefix,
            "tagged_prefix": self.tagged_prefix,
        }

    @property
    def payload_bits(self) -> int:
        return 24


@dataclass(frozen=True)
class ByteGrammar:
    record_separator: int
    field_separator: int
    codec: ByteCodec
    records: tuple[tuple[str, str], ...]

    @property
    def payload_bits(self) -> int:
        return 16 + self.codec.payload_bits


@dataclass(frozen=True)
class JointCandidate:
    grammar: ByteGrammar
    predictions: tuple[str | None, ...]
    operations: tuple[str | None, ...]
    unresolved: tuple[Any, ...]
    promotions: tuple[Any, ...]
    library: tuple[Any, ...]
    candidates_evaluated: int
    compression_gain_bits: int


@dataclass(frozen=True)
class JointResult:
    selected: JointCandidate
    grammar_candidates: int
    eligible_candidates: int
    positive_candidates: int


def _split(raw: bytes, record_separator: int, field_separator: int, codec: ByteCodec):
    pieces = raw.split(bytes((record_separator,)))
    if len(pieces) < 2 or any(not piece for piece in pieces):
        return None
    output = []
    for piece in pieces:
        fields = piece.split(bytes((field_separator,)))
        if len(fields) != 2 or any(not field for field in fields):
            return None
        decoded = tuple(codec.decode(field) for field in fields)
        if any(value is None or not value for value in decoded):
            return None
        output.append((decoded[0], decoded[1]))
    return tuple(output)


def _codecs(controls, record_separator, field_separator):
    remaining = tuple(
        byte for byte in controls
        if byte not in {record_separator, field_separator}
    )
    output: list[ByteCodec] = [SingleByteCodec()]
    output.extend(TaggedByteCodec(marker) for marker in remaining)
    output.extend(
        PrefixedPairCodec(raw_prefix, tagged_prefix)
        for raw_prefix in remaining
        for tagged_prefix in remaining
        if raw_prefix != tagged_prefix
    )
    return tuple(output)


def enumerate_grammars(raw: bytes) -> tuple[ByteGrammar, ...]:
    controls = tuple(sorted({byte for byte in raw if byte >= 0xF0}))
    output = []
    for record_separator in controls:
        for field_separator in controls:
            if record_separator == field_separator:
                continue
            for codec in _codecs(controls, record_separator, field_separator):
                records = _split(raw, record_separator, field_separator, codec)
                if records is not None:
                    output.append(
                        ByteGrammar(
                            record_separator,
                            field_separator,
                            codec,
                            records,
                        )
                    )
    return tuple(output)


def score_grammar(grammar: ByteGrammar) -> JointCandidate:
    values = online_learn_records(grammar.records)
    predictions, operations, unresolved, promotions, library, evaluated = values
    gain = (
        sum(promotion.mdl_gain_bits for promotion in promotions)
        - grammar.payload_bits
    )
    return JointCandidate(
        grammar,
        predictions,
        operations,
        unresolved,
        promotions,
        library,
        evaluated,
        gain,
    )


def joint_infer(stream_hex: str) -> JointResult:
    try:
        raw = bytes.fromhex(stream_hex)
    except ValueError as exc:
        raise NoJointModelError("invalid hex") from exc
    grammars = enumerate_grammars(raw)
    eligible = tuple(
        grammar
        for grammar in grammars
        if {
            alphabet_family(field)
            for record in grammar.records
            for field in record
        }
        == {"ascii_letters", "private_use"}
    )
    candidates = tuple(score_grammar(grammar) for grammar in eligible)
    positive = tuple(
        candidate
        for candidate in candidates
        if candidate.compression_gain_bits > 0
        and len(candidate.library) >= 2
    )
    if not positive:
        raise NoJointModelError("no positive joint codec/primitive model")
    best_gain = max(candidate.compression_gain_bits for candidate in positive)
    best = tuple(
        candidate for candidate in positive
        if candidate.compression_gain_bits == best_gain
    )
    signatures = {
        (
            candidate.grammar.codec.kind,
            tuple(primitive.render()["kind"] for primitive in candidate.library),
        )
        for candidate in best
    }
    if len(signatures) != 1:
        raise NoJointModelError("joint model is ambiguous")
    selected = min(
        best,
        key=lambda candidate: (
            candidate.grammar.payload_bits,
            json.dumps(candidate.grammar.codec.render(), sort_keys=True),
        ),
    )
    return JointResult(
        selected,
        len(grammars),
        len(eligible),
        len(positive),
    )


def encode_records(
    records: Sequence[tuple[str, str]],
    codec: ByteCodec,
    record_separator: int,
    field_separator: int,
) -> str:
    raw = bytearray()
    for index, (source, target) in enumerate(records):
        if index:
            raw.append(record_separator)
        raw.extend(codec.encode(source))
        raw.append(field_separator)
        raw.extend(codec.encode(target))
    return bytes(raw).hex()


def shift_private_use(records: Sequence[tuple[str, str]], delta: int):
    def shift(value: str) -> str:
        return "".join(
            chr(ord(character) + delta)
            if 0xE000 <= ord(character) <= 0xE0FF
            else character
            for character in value
        )
    return tuple((shift(source), shift(target)) for source, target in records)


def primitive_signature(result: JointResult):
    output = []
    for primitive in result.selected.library:
        if isinstance(primitive, IndexAffinePrimitive):
            output.append(("index", primitive.multiplier, primitive.offset))
        elif isinstance(primitive, ElementAffinePrimitive):
            output.append(("element", primitive.scale, primitive.offset))
        else:
            output.append((primitive.render()["kind"], 0, 0))
    return tuple(output)


def metrics(candidate: JointCandidate):
    correct = wrong = abstained = 0
    wrong_positions = []
    for position, (prediction, (_, target)) in enumerate(
        zip(candidate.predictions, candidate.grammar.records)
    ):
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
        "coverage": covered / len(candidate.grammar.records),
        "covered_accuracy": correct / covered if covered else 0.0,
        "wrong_positions": wrong_positions,
    }
