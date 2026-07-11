from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Iterable, Mapping, Protocol

from .hierarchical_event_graph import EventEdge, EventGraph, EventNode


CONNECTOR_ROLES = (
    "SEQUENCE",
    "CONDITION_TRUE",
    "CONDITION_FALSE",
    "REFERENCE",
    "CONTENT",
)


class Grounder(Protocol):
    def predict(self, raw: str): ...


@dataclass(frozen=True)
class ConnectorObservation:
    connector: str
    proposition_value: bool | None = None
    action_executed: bool | None = None
    has_previous_event: bool | None = None
    references_previous: bool | None = None
    carries_content: bool | None = None
    temporal_successor: bool | None = None


@dataclass(frozen=True)
class ConnectorRule:
    connector: str
    role: str
    support: int
    data_bits: float


@dataclass(frozen=True)
class ConnectorLexicon:
    rules: tuple[ConnectorRule, ...]
    observations: int

    def role(self, connector: str) -> str | None:
        for rule in self.rules:
            if rule.connector == connector:
                return rule.role
        return None

    @property
    def description_bits(self) -> int:
        role_bits = max(1, math.ceil(math.log2(len(CONNECTOR_ROLES))))
        count_bits = max(1, math.ceil(math.log2(self.observations + 1)))
        return sum(
            len(rule.connector.encode("utf-8")) * 8
            + role_bits
            + count_bits
            + 8
            for rule in self.rules
        )


@dataclass(frozen=True)
class ConnectorInductionResult:
    lexicon: ConnectorLexicon
    candidate_evaluations: int
    total_data_bits: float


@dataclass(frozen=True)
class RoleSignature:
    needs_proposition: bool
    action_when_proposition: bool | None
    references_previous: bool
    carries_content: bool
    temporal_successor: bool


ROLE_SIGNATURES: Mapping[str, RoleSignature] = {
    "SEQUENCE": RoleSignature(False, None, False, False, True),
    "CONDITION_TRUE": RoleSignature(True, True, False, False, False),
    "CONDITION_FALSE": RoleSignature(True, False, False, False, False),
    "REFERENCE": RoleSignature(False, None, True, False, False),
    "CONTENT": RoleSignature(False, None, False, True, False),
}


def _bernoulli_bits(observed: bool, expected: bool, error: float = 0.02) -> float:
    probability = 1.0 - error if observed == expected else error
    return -math.log2(probability)


def role_data_bits(role: str, observations: Iterable[ConnectorObservation]) -> float:
    signature = ROLE_SIGNATURES[role]
    total = 0.0
    for observation in observations:
        if signature.needs_proposition:
            if observation.proposition_value is None or observation.action_executed is None:
                total += 8.0
            else:
                expected_action = (
                    observation.proposition_value
                    if signature.action_when_proposition
                    else not observation.proposition_value
                )
                total += _bernoulli_bits(observation.action_executed, expected_action)
        elif observation.proposition_value is not None and observation.action_executed is not None:
            total += 1.0

        for observed, expected in (
            (observation.references_previous, signature.references_previous),
            (observation.carries_content, signature.carries_content),
            (observation.temporal_successor, signature.temporal_successor),
        ):
            if observed is not None:
                total += _bernoulli_bits(observed, expected)

        if observation.has_previous_event is not None:
            expected_previous = role in ("SEQUENCE", "REFERENCE")
            total += _bernoulli_bits(observation.has_previous_event, expected_previous)
    return total


def induce_connector_lexicon(
    observations: Iterable[ConnectorObservation],
) -> ConnectorInductionResult:
    items = list(observations)
    if not items:
        raise ValueError("at least one connector observation is required")
    grouped: dict[str, list[ConnectorObservation]] = {}
    for observation in items:
        grouped.setdefault(observation.connector, []).append(observation)

    rules: list[ConnectorRule] = []
    evaluations = 0
    total_data_bits = 0.0
    role_bits = max(1, math.ceil(math.log2(len(CONNECTOR_ROLES))))
    for connector, connector_observations in sorted(grouped.items()):
        candidates: list[tuple[float, str]] = []
        connector_bits = len(connector.encode("utf-8")) * 8
        for role in CONNECTOR_ROLES:
            evaluations += 1
            data_bits = role_data_bits(role, connector_observations)
            objective = connector_bits + role_bits + data_bits
            candidates.append((objective, role))
        candidates.sort()
        best_objective, best_role = candidates[0]
        second_objective = candidates[1][0]
        if math.isclose(best_objective, second_objective, abs_tol=1e-9):
            raise ValueError(f"connector role is not identifiable: {connector!r}")
        best_data = role_data_bits(best_role, connector_observations)
        total_data_bits += best_data
        rules.append(
            ConnectorRule(
                connector=connector,
                role=best_role,
                support=len(connector_observations),
                data_bits=best_data,
            )
        )

    return ConnectorInductionResult(
        ConnectorLexicon(tuple(rules), len(items)),
        evaluations,
        total_data_bits,
    )


def _split_units(raw: str) -> tuple[str, ...]:
    normalized = raw.replace("！", "。").replace("？", "。")
    return tuple(unit.strip(" 、") for unit in normalized.split("。") if unit.strip(" 、"))


def _predicate(text: str) -> tuple[str, tuple[str, ...]]:
    lowered = text.lower()
    if "失敗" in text or "fail" in lowered:
        return "TEST_STATUS", ("FAIL",)
    if "成功" in text or "pass" in lowered:
        return "TEST_STATUS", ("PASS",)
    if "テスト" in text or "試験" in text or "pytest" in lowered:
        return "TEST_STATUS", ("KNOWN",)
    return "CLAIM", (text.strip(),)


def _event_arguments(operation: str, text: str) -> tuple[str, ...]:
    if operation == "VERIFY":
        return ("tests",) if any(token in text for token in ("テスト", "試験", "成功", "失敗")) else ("result",)
    if operation == "RETRACT":
        return ("last_change",)
    if operation == "SET":
        return ("change",)
    if operation == "EMIT":
        return ("result",)
    return ()


def parse_with_connector_lexicon(
    raw: str,
    grounder: Grounder,
    lexicon: ConnectorLexicon,
) -> EventGraph:
    nodes: list[EventNode] = []
    edges: list[EventEdge] = []
    unresolved: list[str] = []
    feature_reads = 0
    previous_event: int | None = None
    last_set: int | None = None

    def add_node(kind: str, label: str, arguments: tuple[str, ...], source: str) -> int:
        identifier = len(nodes)
        nodes.append(EventNode(identifier, kind, label, arguments, True, source))
        return identifier

    def ground_event(text: str, *, sequence: bool = True) -> int | None:
        nonlocal feature_reads, previous_event, last_set
        result = grounder.predict(text)
        feature_reads += getattr(result, "feature_reads", 0)
        operation = result.operation
        if operation is None:
            unresolved.append(text)
            return None
        identifier = add_node("EVENT", operation, _event_arguments(operation, text), text)
        if sequence and previous_event is not None:
            edges.append(EventEdge(previous_event, identifier, "NEXT"))
        previous_event = identifier
        if operation == "SET":
            last_set = identifier
        return identifier

    connectors = sorted(
        (rule.connector for rule in lexicon.rules),
        key=len,
        reverse=True,
    )
    for unit in _split_units(raw):
        connector = next((item for item in connectors if item in unit), None)
        if connector is None:
            ground_event(unit)
            continue
        role = lexicon.role(connector)
        if role is None:
            unresolved.append(unit)
            continue

        left, right = unit.split(connector, 1)
        left = left.strip(" 、")
        right = right.strip(" 、")

        if role in ("CONDITION_TRUE", "CONDITION_FALSE"):
            predicate, arguments = _predicate(left)
            proposition = add_node("PROPOSITION", predicate, arguments, left)
            action = ground_event(right)
            if action is not None:
                relation = "CONDITION_TRUE" if role == "CONDITION_TRUE" else "CONDITION_FALSE"
                edges.append(EventEdge(proposition, action, relation))
            continue

        if role == "SEQUENCE":
            if left:
                ground_event(left)
            if right:
                ground_event(right)
            continue

        if role == "REFERENCE":
            action = ground_event(unit)
            if action is not None and last_set is not None:
                edges.append(EventEdge(action, last_set, "REFERS_TO"))
            continue

        if role == "CONTENT":
            action = ground_event(right)
            if action is None:
                continue
            quoted = re.search(r"[「『](.+?)[」』]", left)
            content = quoted.group(1) if quoted else left
            proposition = add_node("PROPOSITION", "QUOTE", (content,), left)
            edges.append(EventEdge(action, proposition, "CONTENT"))
            continue

        unresolved.append(unit)

    return EventGraph(tuple(nodes), tuple(edges), tuple(unresolved), feature_reads)
