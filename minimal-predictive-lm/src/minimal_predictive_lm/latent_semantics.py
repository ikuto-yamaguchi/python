from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .semantic_induction import InducedFeatureParser


@dataclass(frozen=True)
class InteractionTrace:
    pre_state: Mapping[str, str]
    utterance: str
    post_state: Mapping[str, str]
    response: str


@dataclass(frozen=True)
class InferredOperation:
    operation: str
    key: str
    value: str | None


@dataclass(frozen=True)
class DiscoveredRoles:
    keys: tuple[str, ...]
    values: tuple[str, ...]

    @property
    def all_symbols(self) -> tuple[str, ...]:
        return tuple(sorted(set(self.keys) | set(self.values)))

    def assignment_bits(self) -> int:
        return 2 + len(self.all_symbols)

    def symbol_string_bits(self) -> int:
        return sum(8 * len(symbol.encode("utf-8")) for symbol in self.all_symbols)


def infer_operation(trace: InteractionTrace) -> InferredOperation | None:
    """Infer SET/GET from an observed transition without intent/type labels."""

    changed: list[tuple[str, str | None]] = []
    for key in set(trace.pre_state) | set(trace.post_state):
        before = trace.pre_state.get(key)
        after = trace.post_state.get(key)
        if before != after:
            changed.append((key, after))

    if len(changed) == 1:
        key, value = changed[0]
        if value is not None and key in trace.utterance and value in trace.utterance:
            return InferredOperation("set", key, value)
        return None

    if changed:
        return None

    exposed = [
        (key, value)
        for key, value in trace.pre_state.items()
        if key in trace.utterance
        and key in trace.response
        and value in trace.response
    ]
    if len(exposed) == 1:
        key, _ = exposed[0]
        return InferredOperation("get", key, None)

    return None


def discover_roles(operations: Sequence[InferredOperation]) -> DiscoveredRoles:
    keys = sorted({operation.key for operation in operations})
    values = sorted(
        {
            operation.value
            for operation in operations
            if operation.operation == "set" and operation.value is not None
        }
    )
    return DiscoveredRoles(tuple(keys), tuple(values))


def extend_roles(
    roles: DiscoveredRoles,
    operations: Sequence[InferredOperation],
) -> DiscoveredRoles:
    return discover_roles(
        [
            *(InferredOperation("get", key, None) for key in roles.keys),
            *(InferredOperation("set", roles.keys[0], value) for value in roles.values),
            *operations,
        ]
    )


def parser_with_roles(
    parser: InducedFeatureParser,
    roles: DiscoveredRoles,
) -> InducedFeatureParser:
    """Reuse learned rules while extending only the runtime symbol table."""

    return InducedFeatureParser(
        parser.rules,
        roles.keys,
        roles.values,
        min_ngram=parser.min_ngram,
        validation_objective=parser.validation_objective,
    )
