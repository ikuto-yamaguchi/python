from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import math
import re
from typing import Mapping, Sequence

Slot = tuple[str, str]


@dataclass(frozen=True)
class Observation:
    """A partial observation of opaque relation slots.

    Missing slots are unknown, not deleted. This distinction prevents a partial
    sensor read from being interpreted as a world-state transition.
    """

    values: Mapping[Slot, str]
    observed: frozenset[Slot]

    @classmethod
    def from_values(
        cls,
        values: Mapping[Slot, str],
        observed: Sequence[Slot] | None = None,
    ) -> "Observation":
        visible = frozenset(values if observed is None else observed)
        return cls(dict(values), visible)


@dataclass(frozen=True)
class MultiRelationTrace:
    pre: Observation
    utterance: str
    immediate: Observation
    response: str
    delayed: Observation | None = None


@dataclass(frozen=True)
class LatentOperation:
    operation: str
    relation: str
    key: str
    value: str | None
    latency: int
    confidence: float
    template: str


@dataclass(frozen=True)
class SchemaRule:
    operation: str
    relation: str
    template: str
    support: int
    confidence_sum: float

    @property
    def cue(self) -> str:
        literals = [piece for piece in re.split(r"\{[KV]\}", self.template) if piece]
        return max(literals, key=len, default="")

    def description_bits(self) -> int:
        return 12 + 8 * len(self.template.encode("utf-8"))


@dataclass(frozen=True)
class ParseResult:
    operation: str
    relation: str
    key: str
    value: str | None


@dataclass
class LatentRelationSchema:
    rules: tuple[SchemaRule, ...]
    keys: Mapping[str, tuple[str, ...]]
    values: Mapping[str, tuple[str, ...]]
    min_support: int

    def __post_init__(self) -> None:
        cue_index: dict[str, list[SchemaRule]] = defaultdict(list)
        fallback: list[SchemaRule] = []
        for rule in self.rules:
            if rule.cue:
                cue_index[rule.cue].append(rule)
            else:
                fallback.append(rule)
        self._cue_index = {cue: tuple(items) for cue, items in cue_index.items()}
        self._fallback = tuple(fallback)

    @property
    def relation_count(self) -> int:
        return len(set(self.keys) | set(self.values))

    @property
    def index_bits(self) -> int:
        if not self.rules:
            return 0
        pointer_bits = max(1, math.ceil(math.log2(len(self.rules))))
        return pointer_bits * len(self.rules)

    @property
    def description_bits(self) -> int:
        rule_bits = sum(rule.description_bits() for rule in self.rules)
        symbols: set[tuple[str, str, str]] = set()
        for relation, items in self.keys.items():
            symbols.update((relation, "key", item) for item in items)
        for relation, items in self.values.items():
            symbols.update((relation, "value", item) for item in items)
        symbol_bits = sum(2 + 8 * len(symbol.encode("utf-8")) for _, _, symbol in symbols)
        relation_bits = 5 * self.relation_count
        return rule_bits + symbol_bits + relation_bits + self.index_bits

    def _candidate_rules(self, text: str) -> tuple[SchemaRule, ...]:
        selected: list[SchemaRule] = []
        seen: set[tuple[str, str, str]] = set()
        for cue, rules in self._cue_index.items():
            if cue not in text:
                continue
            for rule in rules:
                marker = (rule.operation, rule.relation, rule.template)
                if marker not in seen:
                    selected.append(rule)
                    seen.add(marker)
        selected.extend(self._fallback)
        return tuple(selected)

    def parse_with_cost(self, text: str) -> tuple[ParseResult | None, int, int]:
        clean = normalize_surface(text)
        candidates = self._candidate_rules(clean)
        rule_checks = 0
        symbol_checks = 0
        for rule in candidates:
            rule_checks += 1
            key_symbols = sorted(self.keys.get(rule.relation, ()), key=len, reverse=True)
            value_symbols = sorted(self.values.get(rule.relation, ()), key=len, reverse=True)
            if rule.operation == "get":
                for key in key_symbols:
                    symbol_checks += 1
                    if key in clean and clean.replace(key, "{K}") == rule.template:
                        return ParseResult("get", rule.relation, key, None), rule_checks, symbol_checks
                continue
            for key in key_symbols:
                symbol_checks += 1
                if key not in clean:
                    continue
                for value in value_symbols:
                    symbol_checks += 1
                    if value not in clean:
                        continue
                    abstracted = clean.replace(value, "{V}").replace(key, "{K}")
                    if abstracted == rule.template:
                        return ParseResult("set", rule.relation, key, value), rule_checks, symbol_checks
        return None, rule_checks, symbol_checks

    def parse(self, text: str) -> ParseResult | None:
        return self.parse_with_cost(text)[0]


class ExactSurfaceSchema:
    def __init__(self, operations: Sequence[LatentOperation]) -> None:
        self._programs = {
            normalize_surface(
                operation.template.replace("{K}", operation.key).replace(
                    "{V}", operation.value or ""
                )
            ): ParseResult(
                operation.operation,
                operation.relation,
                operation.key,
                operation.value,
            )
            for operation in operations
        }

    @property
    def description_bits(self) -> int:
        return sum(24 + 8 * len(text.encode("utf-8")) for text in self._programs)

    def parse_with_cost(self, text: str) -> tuple[ParseResult | None, int, int]:
        return self._programs.get(normalize_surface(text)), 1, 1

    def parse(self, text: str) -> ParseResult | None:
        return self.parse_with_cost(text)[0]


def normalize_surface(text: str) -> str:
    return (
        text.strip()
        .replace("へ", "に")
        .replace("？", "?")
        .replace("。", "")
    )


def abstract_template(text: str, key: str, value: str | None) -> str:
    normalized = normalize_surface(text)
    if value is not None:
        normalized = normalized.replace(value, "{V}")
    return normalized.replace(key, "{K}")


def _observable_changes(
    before: Observation,
    after: Observation,
) -> list[tuple[Slot, str | None, bool]]:
    changes: list[tuple[Slot, str | None, bool]] = []
    for slot in before.observed & after.observed:
        old = before.values.get(slot)
        new = after.values.get(slot)
        if old != new:
            changes.append((slot, new, True))
    for slot in after.observed - before.observed:
        changes.append((slot, after.values.get(slot), False))
    return changes


def _set_candidate(
    trace: MultiRelationTrace,
    changes: Sequence[tuple[Slot, str | None, bool]],
    *,
    latency: int,
) -> LatentOperation | None:
    candidates: list[LatentOperation] = []
    for (relation, key), value, observed_before in changes:
        if value is None or key not in trace.utterance or value not in trace.utterance:
            continue
        if latency:
            confidence = 0.90 if observed_before else 0.68
        else:
            confidence = 1.00 if observed_before else 0.72
        candidates.append(
            LatentOperation(
                "set",
                relation,
                key,
                value,
                latency,
                confidence,
                abstract_template(trace.utterance, key, value),
            )
        )
    if len(changes) == 1 and len(candidates) == 1:
        return candidates[0]
    return None


def infer_operation(trace: MultiRelationTrace) -> LatentOperation | None:
    direct = _observable_changes(trace.pre, trace.immediate)
    inferred = _set_candidate(trace, direct, latency=0)
    if inferred is not None:
        return inferred

    if trace.delayed is not None:
        delayed = _observable_changes(trace.immediate, trace.delayed)
        inferred = _set_candidate(trace, delayed, latency=1)
        if inferred is not None:
            return inferred

    visible: dict[Slot, str] = {}
    for observation in (trace.pre, trace.immediate, trace.delayed):
        if observation is not None:
            visible.update(observation.values)
    exposed = [
        (relation, key, value)
        for (relation, key), value in visible.items()
        if key in trace.utterance
        and key in trace.response
        and value in trace.response
    ]
    if len(exposed) == 1:
        relation, key, _value = exposed[0]
        return LatentOperation(
            "get",
            relation,
            key,
            None,
            0,
            0.82,
            abstract_template(trace.utterance, key, None),
        )
    return None


def _discover_symbols(
    traces: Sequence[MultiRelationTrace],
) -> tuple[dict[str, tuple[str, ...]], dict[str, tuple[str, ...]]]:
    keys: dict[str, set[str]] = defaultdict(set)
    values: dict[str, set[str]] = defaultdict(set)
    for trace in traces:
        for observation in (trace.pre, trace.immediate, trace.delayed):
            if observation is None:
                continue
            for (relation, key), value in observation.values.items():
                keys[relation].add(key)
                values[relation].add(value)
    return (
        {relation: tuple(sorted(items)) for relation, items in keys.items()},
        {relation: tuple(sorted(items)) for relation, items in values.items()},
    )


def fit_schema(
    operations: Sequence[LatentOperation],
    traces: Sequence[MultiRelationTrace],
    *,
    min_support: int = 2,
    min_confidence_sum: float = 1.4,
) -> LatentRelationSchema:
    grouped: dict[tuple[str, str, str], list[LatentOperation]] = defaultdict(list)
    for operation in operations:
        grouped[(operation.operation, operation.relation, operation.template)].append(
            operation
        )

    rules: list[SchemaRule] = []
    for (operation, relation, template), instances in grouped.items():
        confidence_sum = sum(instance.confidence for instance in instances)
        if len(instances) < min_support or confidence_sum < min_confidence_sum:
            continue
        rules.append(
            SchemaRule(
                operation,
                relation,
                template,
                len(instances),
                confidence_sum,
            )
        )
    keys, values = _discover_symbols(traces)
    return LatentRelationSchema(
        tuple(
            sorted(
                rules,
                key=lambda rule: (
                    rule.relation,
                    rule.operation,
                    rule.template,
                ),
            )
        ),
        keys,
        values,
        min_support,
    )
