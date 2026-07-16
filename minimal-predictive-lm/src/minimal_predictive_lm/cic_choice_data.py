from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

OPTION_RE = re.compile(r"^\((\d+)\)(.*)$")
ANSWER_RE = re.compile(r"^\((\d+)\)")
JNLI_OPTIONS = ("entailment", "contradiction", "neutral")


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


def _read_rows(path: str | Path) -> list[dict[str, object]]:
    text = Path(path).read_text(encoding="utf-8")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    if isinstance(payload, list):
        return [dict(row) for row in payload]
    raise ValueError(f"unsupported choice dataset format: {path}")


def load_choice_dataset(path: str | Path) -> list[ChoiceExample]:
    result: list[ChoiceExample] = []
    for row in _read_rows(path):
        if "sentence1" in row and "sentence2" in row:
            premise = str(row["sentence1"]).strip()
            hypothesis = str(row["sentence2"]).strip()
            label = str(row["label"]).strip()
            if label not in JNLI_OPTIONS:
                continue
            stem = f"前提：{premise}\n仮説：{hypothesis}"
            raw_question = stem + "\n" + "\n".join(
                f"({index}){option}" for index, option in enumerate(JNLI_OPTIONS)
            )
            result.append(
                ChoiceExample(
                    raw_question,
                    stem,
                    JNLI_OPTIONS,
                    JNLI_OPTIONS.index(label),
                )
            )
            continue

        if "choice0" in row:
            stem = str(row.get("question", "")).strip()
            options = tuple(str(row[f"choice{index}"]) for index in range(5))
            answer_index = int(row["label"])
            raw_question = stem + "\n" + "\n".join(
                f"({index}){option}" for index, option in enumerate(options)
            )
            result.append(ChoiceExample(raw_question, stem, options, answer_index))
            continue

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


def _spread_sample(tokens: Sequence[str], limit: int) -> list[str]:
    if len(tokens) <= limit:
        return list(tokens)
    if limit <= 1:
        return [tokens[-1]]
    return [tokens[(index * (len(tokens) - 1)) // (limit - 1)] for index in range(limit)]


def legacy_choice_features(
    stem: str,
    option: str,
    position: int,
    *,
    dimensions: int = 16384,
    hash_salt: str = "",
    relation_scope: str = "tail",
) -> dict[int, int]:
    values: Counter[int] = Counter({0: 1})
    stem_tokens = _ngrams(stem, (2, 3, 4))
    option_tokens = _ngrams(option, (1, 2, 3))
    for namespace, tokens in (("Q:", stem_tokens), ("O:", option_tokens)):
        for token in tokens:
            index, sign = _index(hash_salt + namespace, token, dimensions)
            values[index] += sign

    if relation_scope == "tail":
        relation_tokens = _ngrams(stem[-20:], (2, 3))[-40:]
    elif relation_scope == "full":
        relation_tokens = _spread_sample(_ngrams(stem, (2, 3)), 40)
    else:
        raise ValueError(f"unsupported relation_scope: {relation_scope}")
    for question_token in relation_tokens:
        for option_token in option_tokens[:32]:
            index, sign = _index(
                hash_salt + "R:", question_token + "=>" + option_token, dimensions
            )
            values[index] += sign
    overlap = min(4, len(set(_ngrams(stem, (2,))) & set(_ngrams(option, (2,)))))
    for token in (
        f"OVERLAP={overlap}",
        f"OLEN={min(8, len(option) // 2)}",
        f"POSITION={position}",
        "ENDING=" + stem[-8:],
    ):
        index, sign = _index(hash_salt + "M:", token, dimensions)
        values[index] += 2 * sign
    return {index: max(-6, min(6, value)) for index, value in values.items()}


def choice_features(
    stem: str,
    option: str,
    position: int,
    *,
    dimensions: int = 32768,
    hash_replicas: int = 1,
    relation_scope: str = "tail",
) -> dict[int, int]:
    """Return one or more disjoint signed feature hashes.

    The default tail relation exactly preserves CIC-006. The generic full
    relation samples the whole input at fixed cost so premise/hypothesis and
    long questions can influence candidate ranking without increasing feature
    count per example.
    """
    if hash_replicas < 1:
        raise ValueError("hash_replicas must be positive")
    if dimensions % hash_replicas:
        raise ValueError("dimensions must be divisible by hash_replicas")
    if hash_replicas == 1:
        return legacy_choice_features(
            stem,
            option,
            position,
            dimensions=dimensions,
            relation_scope=relation_scope,
        )

    block = dimensions // hash_replicas
    if block < 2:
        raise ValueError("each hash replica needs at least two dimensions")
    values: Counter[int] = Counter({0: 1})
    for replica in range(hash_replicas):
        local = legacy_choice_features(
            stem,
            option,
            position,
            dimensions=block,
            hash_salt=f"H{replica}:",
            relation_scope=relation_scope,
        )
        offset = replica * block
        for index, value in local.items():
            if index:
                values[offset + index] += value
    return {index: max(-6, min(6, value)) for index, value in values.items()}
