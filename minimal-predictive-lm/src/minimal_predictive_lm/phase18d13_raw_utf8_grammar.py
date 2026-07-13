from __future__ import annotations

from dataclasses import dataclass


class NoGrammarError(ValueError):
    pass


@dataclass(frozen=True)
class RawGrammar:
    record_separator: str
    field_separator: str
    records: tuple[tuple[str, str], ...]
    separator_candidates: int
    valid_grammars: int


def decode_hex(stream_hex: str) -> str:
    try:
        return bytes.fromhex(stream_hex).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise NoGrammarError("invalid hex or UTF-8") from exc


def is_payload_symbol(character: str) -> bool:
    return (
        character.isascii() and character.isalpha()
    ) or 0xE000 <= ord(character) <= 0xF8FF


def _parse(text: str, record_separator: str, field_separator: str):
    pieces = text.split(record_separator)
    if len(pieces) < 2 or any(not piece for piece in pieces):
        return None
    records = []
    for piece in pieces:
        fields = piece.split(field_separator)
        if len(fields) != 2 or any(
            not field
            or not all(is_payload_symbol(character) for character in field)
            for field in fields
        ):
            return None
        records.append(tuple(fields))
    return tuple(records)


def infer_grammar(stream_hex: str) -> RawGrammar:
    text = decode_hex(stream_hex)
    separators = tuple(
        sorted({character for character in text if not is_payload_symbol(character)})
    )
    candidates = []
    for record_separator in separators:
        for field_separator in separators:
            if record_separator == field_separator:
                continue
            records = _parse(text, record_separator, field_separator)
            if records is not None:
                candidates.append(
                    (len(records), record_separator, field_separator, records)
                )
    if not candidates:
        raise NoGrammarError("no complete two-field grammar")
    maximum_records = max(row[0] for row in candidates)
    best = [row for row in candidates if row[0] == maximum_records]
    if len(best) != 1:
        raise NoGrammarError("separator roles are ambiguous")
    _, record_separator, field_separator, records = best[0]
    return RawGrammar(
        record_separator,
        field_separator,
        records,
        len(separators) * max(0, len(separators) - 1),
        len(candidates),
    )


def alphabet_family(value: str) -> str:
    if value and all(
        character.isascii() and character.isalpha() for character in value
    ):
        return "ascii_letters"
    if value and all(0xE000 <= ord(character) <= 0xF8FF for character in value):
        return "private_use"
    return "mixed"


def canonical(value: str) -> tuple[int, ...]:
    return tuple(map(ord, value))
