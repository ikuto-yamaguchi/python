from __future__ import annotations

import argparse
import json
import math
import random
import re
import statistics
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

PARTICLE_SPLIT = re.compile(r"(?:から|まで|より|には|では|へ|に|を|は|が|の|と|、|。|，|．|\s)+")
NUMBER = re.compile(r"(?<!\d)(\d+)(?!\d)")
PUNCT = re.compile(r"[、。！？!?,，．\s]+")


def chunks(text: str) -> list[str]:
    compounds: dict[str, str] = {}
    compound = re.compile(
        r"([一-龥ァ-ヶA-Za-z0-9]{1,8}の[一-龥ァ-ヶA-Za-z0-9]{1,8})"
        r"(?=(?:には|へ|から|は|が|に|を|で|、|。))"
    )

    def protect(match: re.Match[str]) -> str:
        key = f"§{chr(65 + len(compounds))}§"
        compounds[key] = match.group(1)
        return key

    protected = compound.sub(protect, text)
    result: list[str] = []
    for piece in PARTICLE_SPLIT.split(protected):
        piece = NUMBER.sub("", piece)
        piece = PUNCT.sub("", piece).strip()
        for key, value in compounds.items():
            piece = piece.replace(key, value)
        piece = re.sub(r"^(?:現在|合計|持つ|所持する|保管中の)+", "", piece)
        piece = re.sub(
            r"(?:個あります|個です|個入っています|あります|入っています|"
            r"持っています|所持しています|でした|です|個|つ)$",
            "",
            piece,
        ).strip()
        if piece and piece not in result:
            result.append(piece)
    return result


def ngrams(text: str, sizes: tuple[int, ...] = (3,)) -> Counter[str]:
    text = re.sub(r"\s+", "", text)
    result: Counter[str] = Counter()
    for size in sizes:
        if len(text) < size:
            if text:
                result[text] += 1
            continue
        result.update(text[index : index + size] for index in range(len(text) - size + 1))
    return result


def cosine(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    dot = sum(value * right.get(key, 0) for key, value in left.items())
    a = math.sqrt(sum(value * value for value in left.values()))
    b = math.sqrt(sum(value * value for value in right.values()))
    return dot / (a * b) if a and b else 0.0


@dataclass(frozen=True)
class Fact:
    sentence: str
    number: int
    content: tuple[str, ...]
    start: int
    end: int


def facts(text: str) -> list[Fact]:
    result: list[Fact] = []
    for match in re.finditer(r"[^。！？!?]+[。！？!?]?", text):
        sentence = match.group(0)
        number = NUMBER.search(sentence)
        content = tuple(dict.fromkeys(chunks(sentence)))
        if number and len(content) >= 2:
            result.append(Fact(sentence, int(number.group(1)), content, match.start(), match.end()))
    return result


def align(before: str, after: str) -> list[tuple[Fact, Fact, int]]:
    after_facts = facts(after)
    used: set[int] = set()
    result: list[tuple[Fact, Fact, int]] = []
    for before_fact in facts(before):
        ranked = []
        for index, after_fact in enumerate(after_facts):
            if index in used:
                continue
            left, right = set(before_fact.content), set(after_fact.content)
            jaccard = len(left & right) / max(1, len(left | right))
            skeleton = cosine(
                ngrams(NUMBER.sub("<N>", before_fact.sentence)),
                ngrams(NUMBER.sub("<N>", after_fact.sentence)),
            )
            ranked.append((0.75 * jaccard + 0.25 * skeleton, index, after_fact))
        if ranked:
            score, index, after_fact = max(ranked)
            if score >= 0.55:
                used.add(index)
                result.append((before_fact, after_fact, after_fact.number - before_fact.number))
    return result


@dataclass(frozen=True)
class Episode:
    command: str
    before: str
    after: str


@dataclass(frozen=True)
class Binding:
    src: str
    dst: str
    item: str
    amount: int


@dataclass(frozen=True)
class SurfacePattern:
    operator: str
    abstract: str
    count: int


class GroundedOrbit:
    """Learns executable role bindings from raw Japanese before/after transitions."""

    def __init__(self) -> None:
        self.patterns: list[SurfacePattern] = []
        self.pattern_grams: list[Counter[str]] = []
        self.cancellation_markers: dict[str, float] = {}
        self.failures: list[str] = []

    @staticmethod
    def induce_binding(episode: Episode) -> tuple[str | None, Binding | None]:
        changed = [row for row in align(episode.before, episode.after) if row[2]]
        if not changed:
            return ("NOOP", None) if episode.before == episode.after else (None, None)
        negative = [row for row in changed if row[2] < 0]
        positive = [row for row in changed if row[2] > 0]
        if len(negative) != 1 or len(positive) != 1:
            return None, None
        if abs(negative[0][2]) != positive[0][2]:
            return None, None
        source, destination = negative[0][0], positive[0][0]
        common = set(source.content) & set(destination.content)
        common = {value for value in common if value in episode.command} or common
        if not common:
            return None, None
        item = max(common, key=len)
        sources = [value for value in source.content if value != item and value in episode.command]
        destinations = [value for value in destination.content if value != item and value in episode.command]
        if not sources or not destinations:
            return None, None
        return "TRANSFER", Binding(
            max(sources, key=len), max(destinations, key=len), item, abs(negative[0][2])
        )

    @staticmethod
    def state_pairs(text: str) -> tuple[dict[frozenset[str], Fact], list[str]]:
        pairs: dict[frozenset[str], Fact] = {}
        vocabulary: set[str] = set()
        for fact in facts(text):
            vocabulary.update(fact.content)
            values = list(dict.fromkeys(fact.content))
            for left in range(len(values)):
                for right in range(left + 1, len(values)):
                    pairs[frozenset((values[left], values[right]))] = fact
        return pairs, sorted(vocabulary, key=lambda value: (-len(value), value))

    @staticmethod
    def abstract(command: str, binding: Binding | None) -> str:
        result = command
        if binding:
            replacements = {
                "SRC": binding.src,
                "DST": binding.dst,
                "ITEM": binding.item,
                "N": str(binding.amount),
            }
            for role, value in sorted(replacements.items(), key=lambda row: -len(row[1])):
                result = result.replace(value, f"<{role}>")
        else:
            result = NUMBER.sub("<N>", result)
        return re.sub(r"\s+", "", result)

    @classmethod
    def neutral_abstract(cls, command: str, before: str) -> str:
        result = command
        _, vocabulary = cls.state_pairs(before)
        for value in sorted((v for v in vocabulary if v in result), key=len, reverse=True):
            result = result.replace(value, "<E>")
        return NUMBER.sub("<N>", re.sub(r"\s+", "", result))

    def fit(self, episodes: Iterable[Episode]) -> None:
        grouped: Counter[tuple[str, str]] = Counter()
        operator_grams: dict[str, Counter[str]] = defaultdict(Counter)
        for episode in episodes:
            operator, binding = self.induce_binding(episode)
            if operator is None:
                self.failures.append(episode.command)
                continue
            abstract = (
                self.neutral_abstract(episode.command, episode.before)
                if operator == "NOOP"
                else self.abstract(episode.command, binding)
            )
            grouped[(operator, abstract)] += 1
            operator_grams[operator].update(
                ngrams(self.neutral_abstract(episode.command, episode.before), (2, 3, 4))
            )
        self.patterns = [SurfacePattern(op, abstract, count) for (op, abstract), count in grouped.items()]
        self.pattern_grams = [ngrams(pattern.abstract) for pattern in self.patterns]
        noop, transfer = operator_grams.get("NOOP", Counter()), operator_grams.get("TRANSFER", Counter())
        markers: dict[str, float] = {}
        for gram, count in noop.items():
            if count < 3 or len(gram) < 4 or re.search(r"[<>。！？!?,，．]", gram):
                continue
            weight = math.log((count + 1.0) / (transfer.get(gram, 0) + 1.0))
            if weight >= 1.0:
                markers[gram] = weight
        self.cancellation_markers = dict(
            sorted(markers.items(), key=lambda row: (-row[1], -len(row[0])))[:32]
        )

    def candidate_bindings(self, command: str, before: str) -> list[Binding]:
        pair_map, vocabulary = self.state_pairs(before)
        mentions = [value for value in vocabulary if value in command]
        number = NUMBER.search(command)
        amount = int(number.group(1)) if number else 0
        result: list[Binding] = []
        for item in mentions:
            for source in mentions:
                for destination in mentions:
                    if len({item, source, destination}) != 3:
                        continue
                    if (
                        frozenset((source, item)) in pair_map
                        and frozenset((destination, item)) in pair_map
                    ):
                        result.append(Binding(source, destination, item, amount))
        return result

    def apply(self, before: str, binding: Binding) -> tuple[str, dict[str, object]]:
        pair_map, _ = self.state_pairs(before)
        source = pair_map.get(frozenset((binding.src, binding.item)))
        destination = pair_map.get(frozenset((binding.dst, binding.item)))
        if source is None or destination is None or source is destination:
            return before, {"operator": "ABSTAIN", "reason": "ambiguous-state-binding"}
        if source.number < binding.amount:
            return before, {"operator": "ABSTAIN", "reason": "precondition"}
        output = before
        replacements = (
            (source, source.number - binding.amount),
            (destination, destination.number + binding.amount),
        )
        for fact, value in sorted(replacements, key=lambda row: row[0].start, reverse=True):
            sentence = NUMBER.sub(str(value), fact.sentence, count=1)
            output = output[: fact.start] + sentence + output[fact.end :]
        return output, {"operator": "TRANSFER", "binding": asdict(binding)}

    def predict(self, command: str, before: str) -> tuple[str, dict[str, object]]:
        neutral = self.neutral_abstract(command, before)
        last_role = max(neutral.rfind("<E>"), neutral.rfind("<N>"))
        evidence = max(
            (
                weight
                for marker, weight in self.cancellation_markers.items()
                if neutral.find(marker) > last_role
            ),
            default=0.0,
        )
        best: tuple[float, str | None, Binding | None, str | None] = (0.0, None, None, None)
        for pattern, grams in zip(self.patterns, self.pattern_grams):
            if pattern.operator != "NOOP":
                continue
            score = cosine(ngrams(neutral), grams) + 0.34 * evidence
            if score > best[0]:
                best = score, "NOOP", None, pattern.abstract
        for binding in self.candidate_bindings(command, before):
            abstract = self.abstract(command, binding)
            for pattern, grams in zip(self.patterns, self.pattern_grams):
                if pattern.operator != "TRANSFER":
                    continue
                score = cosine(ngrams(abstract), grams) - 0.28 * evidence
                if score > best[0]:
                    best = score, "TRANSFER", binding, pattern.abstract
        score, operator, binding, pattern = best
        if operator is None or score < 0.30:
            return before, {"operator": "ABSTAIN", "score": score}
        if operator == "NOOP":
            return before, {"operator": "NOOP", "score": score, "pattern": pattern}
        assert binding is not None
        output, trace = self.apply(before, binding)
        return output, {**trace, "score": score, "pattern": pattern}
