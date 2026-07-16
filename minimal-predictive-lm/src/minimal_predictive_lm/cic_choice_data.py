from __future__ import annotations

import difflib
import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Sequence

OPTION_RE = re.compile(r"^\((\d+)\)(.*)$")
ANSWER_RE = re.compile(r"^\((\d+)\)")
NUMBER_RE = re.compile(r"[0-9０-９]+")
JNLI_OPTIONS = ("entailment", "contradiction", "neutral")
NEGATIONS = ("ない", "ません", "ぬ", "ず", "無い", "なく", "なかった")


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
    if isinstance(payload, dict):
        return [dict(payload)]
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


def _bin(value: float, bins: int = 20) -> int:
    return max(0, min(bins, int(round(value * bins))))


def _shared_edge(left: str, right: str, *, reverse: bool = False) -> int:
    if reverse:
        left, right = left[::-1], right[::-1]
    count = 0
    for a, b in zip(left, right):
        if a != b:
            break
        count += 1
    return count


def _strip_field_label(line: str) -> str:
    return line.split("：", 1)[1] if "：" in line else line


@lru_cache(maxsize=512)
def _span_relation_tokens(stem: str) -> tuple[str, ...]:
    """Describe relations between the first two non-empty text spans.

    This is format-generic rather than JNLI-specific: any two-line candidate
    question can activate the same fielded, overlap and edit-relation features.
    The small LRU only avoids recomputing a span relation for adjacent options.
    """

    lines = [line.strip() for line in stem.splitlines() if line.strip()]
    if len(lines) < 2:
        return ()
    left = re.sub(r"\s+", "", _strip_field_label(lines[0]))
    right = re.sub(r"\s+", "", _strip_field_label(lines[1]))
    if not left or not right:
        return ()

    tokens: list[str] = ["PAIR_BIAS"]
    left_ngrams = _ngrams(left, (1, 2, 3))
    right_ngrams = _ngrams(right, (1, 2, 3))
    tokens.extend("LEFT:" + token for token in _spread_sample(left_ngrams, 180))
    tokens.extend("RIGHT:" + token for token in _spread_sample(right_ngrams, 180))

    left_bigrams = set(_ngrams(left, (2,)))
    right_bigrams = set(_ngrams(right, (2,)))
    intersection = len(left_bigrams & right_bigrams)
    union = len(left_bigrams | right_bigrams)
    tokens.extend(
        (
            f"LEFT_LEN:{min(20, len(left) // 5)}",
            f"RIGHT_LEN:{min(20, len(right) // 5)}",
            f"LEN_DELTA:{max(-20, min(20, (len(right) - len(left)) // 3))}",
            f"JACCARD:{_bin(intersection / union if union else 1.0)}",
            f"LEFT_CONTAIN:{_bin(intersection / len(left_bigrams) if left_bigrams else 1.0)}",
            f"RIGHT_CONTAIN:{_bin(intersection / len(right_bigrams) if right_bigrams else 1.0)}",
            f"PREFIX:{min(12, _shared_edge(left, right) // 2)}",
            f"SUFFIX:{min(12, _shared_edge(left, right, reverse=True) // 2)}",
            f"EXACT:{left == right}",
            f"LEFT_IN_RIGHT:{left in right}",
            f"RIGHT_IN_LEFT:{right in left}",
        )
    )

    left_negation = tuple(marker for marker in NEGATIONS if marker in left)
    right_negation = tuple(marker for marker in NEGATIONS if marker in right)
    left_numbers = tuple(NUMBER_RE.findall(left))
    right_numbers = tuple(NUMBER_RE.findall(right))
    tokens.extend(
        (
            f"LEFT_NEG:{bool(left_negation)}",
            f"RIGHT_NEG:{bool(right_negation)}",
            f"NEG_MISMATCH:{bool(left_negation) != bool(right_negation)}",
            f"NEG_PAIR:{','.join(left_negation)}=>{','.join(right_negation)}",
            f"LEFT_NUM:{bool(left_numbers)}",
            f"RIGHT_NUM:{bool(right_numbers)}",
            f"NUM_SAME:{left_numbers == right_numbers}",
            f"NUM_PAIR:{','.join(left_numbers)}=>{','.join(right_numbers)}",
        )
    )

    matcher = difflib.SequenceMatcher(a=left, b=right, autojunk=False)
    opcodes = matcher.get_opcodes()
    tokens.extend(
        (
            "OPS:" + ",".join(tag for tag, *_rest in opcodes),
            f"EDIT_RATIO:{_bin(matcher.ratio())}",
            f"OP_COUNT:{min(12, len(opcodes))}",
        )
    )
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            continue
        removed = left[i1:i2]
        added = right[j1:j2]
        tokens.extend(
            (
                f"OP:{tag}",
                f"OP_LEN:{tag}:{min(12, len(removed))}:{min(12, len(added))}",
            )
        )
        removed_parts = _spread_sample(_ngrams(removed, (1, 2, 3)), 18)
        added_parts = _spread_sample(_ngrams(added, (1, 2, 3)), 18)
        tokens.extend("REMOVED:" + token for token in removed_parts)
        tokens.extend("ADDED:" + token for token in added_parts)
        for removed_part in removed_parts[:12]:
            for added_part in added_parts[:12]:
                tokens.append("REPLACE:" + removed_part + "=>" + added_part)
    return tuple(tokens)


def legacy_choice_features(
    stem: str,
    option: str,
    position: int,
    *,
    dimensions: int = 16384,
    hash_salt: str = "",
    relation_scope: str = "tail",
) -> dict[int, int | float]:
    values: Counter[int] = Counter({0: 1})
    stem_tokens = _ngrams(stem, (2, 3, 4))
    option_tokens = _ngrams(option, (1, 2, 3))

    # Question-only features have the same score for every option and cancel
    # exactly in ranking updates. CIC-006 keeps them for strict reproduction;
    # adaptive mode drops that dead capacity.
    fields = (("O:", option_tokens),) if relation_scope == "adaptive" else (("Q:", stem_tokens), ("O:", option_tokens))
    for namespace, tokens in fields:
        for token in tokens:
            index, sign = _index(hash_salt + namespace, token, dimensions)
            values[index] += sign

    if relation_scope in ("tail", "adaptive"):
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

    if relation_scope == "adaptive":
        for relation_token in _span_relation_tokens(stem):
            index, sign = _index(
                hash_salt + "PAIR:", relation_token + "=>" + option, dimensions
            )
            values[index] += sign
    return {index: max(-6.0, min(6.0, float(value))) for index, value in values.items()}


def choice_features(
    stem: str,
    option: str,
    position: int,
    *,
    dimensions: int = 32768,
    hash_replicas: int = 1,
    relation_scope: str = "tail",
) -> dict[int, int | float]:
    """Return one or more disjoint signed feature hashes.

    ``adaptive`` preserves the compact tail relation for ordinary questions and
    adds fielded edit relations whenever the input naturally contains two text
    spans. No external task identifier or router is supplied.
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
    return {index: max(-6.0, min(6.0, float(value))) for index, value in values.items()}
