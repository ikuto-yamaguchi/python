from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

OPTION_RE = re.compile(r"^\((\d+)\)(.*)$")
ANSWER_RE = re.compile(r"^\((\d+)\)")


@dataclass(frozen=True)
class ChoiceExample:
    raw_question: str
    stem: str
    options: tuple[str, ...]
    answer_index: int


def parse_choice_question(text: str) -> tuple[str, tuple[str, ...]] | None:
    stem_lines: list[str] = []
    options: dict[int, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line == "解答：":
            continue
        match = OPTION_RE.match(line)
        if match:
            options[int(match.group(1))] = match.group(2).strip()
        else:
            stem_lines.append(line.removeprefix("問題："))
    if not options:
        return None
    ordered = tuple(options[index] for index in range(max(options) + 1) if index in options)
    if len(ordered) != len(options) or len(ordered) < 2:
        return None
    return " ".join(stem_lines).strip(), ordered


def load_choice_dataset(path: str | Path) -> list[ChoiceExample]:
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    result: list[ChoiceExample] = []
    for row in rows:
        raw_question = str(row.get("question", ""))
        parsed = parse_choice_question(raw_question)
        match = ANSWER_RE.match(str(row.get("answer", "")))
        if parsed is None or match is None:
            continue
        stem, options = parsed
        answer_index = int(match.group(1))
        if answer_index < len(options):
            result.append(ChoiceExample(raw_question, stem, options, answer_index))
    return result


def stable_choice_split(
    rows: Sequence[ChoiceExample],
    *,
    test_threshold: int = 2000,
    namespace: str = "outer:",
) -> tuple[list[ChoiceExample], list[ChoiceExample]]:
    train: list[ChoiceExample] = []
    test: list[ChoiceExample] = []
    for row in rows:
        digest = hashlib.sha256((namespace + row.raw_question).encode()).digest()
        code = int.from_bytes(digest[:8], "little") % 10000
        (test if code < test_threshold else train).append(row)
    return train, test


def _index(namespace: str, token: str, dimensions: int) -> tuple[int, int]:
    digest = hashlib.blake2b((namespace + token).encode(), digest_size=8).digest()
    code = int.from_bytes(digest, "little")
    return 1 + code % (dimensions - 1), 1 if code >> 63 else -1


def _ngrams(text: str, widths: Sequence[int]) -> list[str]:
    normalized = re.sub(r"\s+", "", text)
    result: list[str] = []
    for width in widths:
        result.extend(
            normalized[index : index + width]
            for index in range(max(0, len(normalized) - width + 1))
        )
    return result


def _unique_limited(tokens: Sequence[str], limit: int) -> list[str]:
    return list(dict.fromkeys(tokens))[:limit]


def legacy_choice_features(
    stem: str,
    option: str,
    position: int,
    *,
    dimensions: int = 16384,
) -> dict[int, int]:
    """Exact CIC-003 feature map retained as an internal comparison baseline."""
    values: Counter[int] = Counter({0: 1})
    stem_tokens = _ngrams(stem, (2, 3, 4))
    option_tokens = _ngrams(option, (1, 2, 3))
    for namespace, tokens in (("Q:", stem_tokens), ("O:", option_tokens)):
        for token in tokens:
            index, sign = _index(namespace, token, dimensions)
            values[index] += sign
    for question_token in _ngrams(stem[-20:], (2, 3))[-40:]:
        for option_token in option_tokens[:32]:
            index, sign = _index("R:", question_token + "=>" + option_token, dimensions)
            values[index] += sign
    overlap = min(4, len(set(_ngrams(stem, (2,))) & set(_ngrams(option, (2,)))))
    for token in (
        f"OVERLAP={overlap}",
        f"OLEN={min(8, len(option) // 2)}",
        f"POSITION={position}",
        "ENDING=" + stem[-8:],
    ):
        index, sign = _index("M:", token, dimensions)
        values[index] += 2 * sign
    return {index: max(-6, min(6, value)) for index, value in values.items()}


def choice_features(
    stem: str,
    option: str,
    position: int,
    *,
    dimensions: int = 32768,
) -> dict[int, float]:
    """Build a compact task-free relation vector for one question/option pair.

    Question-only features are intentionally omitted because they are identical
    for every option and cannot affect ranking. Capacity is spent on option
    priors, question/option relations, suffix cues and structural metadata.
    """

    values: Counter[int] = Counter({0: 1.0})
    question_tokens = _unique_limited(
        _ngrams(stem, (2, 3, 4))[-96:] + _ngrams(stem, (1,))[-32:], 128
    )
    option_tokens = _unique_limited(_ngrams(option, (1, 2, 3, 4)), 48)

    for token in option_tokens:
        index, sign = _index("O:", token, dimensions)
        values[index] += 0.65 * sign

    for question_token in question_tokens:
        for option_token in option_tokens[:28]:
            index, sign = _index("R:", question_token + "=>" + option_token, dimensions)
            values[index] += sign

    compact_stem = re.sub(r"\s+", "", stem)
    for width in (6, 10, 16, 24):
        suffix = compact_stem[-width:]
        for option_token in option_tokens[:24]:
            index, sign = _index(f"S{width}:", suffix + "=>" + option_token, dimensions)
            values[index] += 1.5 * sign

    overlap = min(6, len(set(_ngrams(stem, (2,))) & set(_ngrams(option, (2,)))))
    for token, magnitude in (
        (f"OVERLAP={overlap}", 1.0),
        (f"OLEN={min(12, len(option) // 2)}", 1.0),
        (f"POSITION={position}", 0.75),
        ("ENDING=" + compact_stem[-12:], 1.25),
        ("QMARK=" + str(compact_stem.endswith(("?", "？"))), 0.5),
    ):
        index, sign = _index("M:", token, dimensions)
        values[index] += magnitude * sign

    norm = math.sqrt(sum(value * value for value in values.values())) or 1.0
    return {index: value / norm for index, value in values.items()}
