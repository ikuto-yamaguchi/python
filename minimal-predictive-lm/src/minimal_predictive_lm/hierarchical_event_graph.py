from __future__ import annotations

from dataclasses import dataclass, replace
import json
import math
import re
import unicodedata
from typing import Iterable, Mapping, Protocol


OPERATIONS = ("SET", "VERIFY", "RETRACT", "EMIT")
NODE_KINDS = ("EVENT", "PROPOSITION")
EDGE_RELATIONS = (
    "NEXT",
    "CONDITION_TRUE",
    "CONDITION_FALSE",
    "CONTENT",
    "REFERS_TO",
)


class Grounder(Protocol):
    def predict(self, raw: str): ...


@dataclass(frozen=True)
class EventNode:
    identifier: int
    kind: str
    label: str
    arguments: tuple[str, ...] = ()
    polarity: bool = True
    source_span: str = ""


@dataclass(frozen=True)
class EventEdge:
    source: int
    target: int
    relation: str


@dataclass(frozen=True)
class EventGraph:
    nodes: tuple[EventNode, ...]
    edges: tuple[EventEdge, ...]
    unresolved: tuple[str, ...] = ()
    feature_reads: int = 0

    def event_nodes(self) -> tuple[EventNode, ...]:
        return tuple(node for node in self.nodes if node.kind == "EVENT")

    def proposition_nodes(self) -> tuple[EventNode, ...]:
        return tuple(node for node in self.nodes if node.kind == "PROPOSITION")

    def operations(self) -> tuple[str, ...]:
        return tuple(node.label for node in self.event_nodes())

    @property
    def description_bits(self) -> int:
        symbols = sorted(
            {
                value
                for node in self.nodes
                for value in (node.kind, node.label, *node.arguments)
            }
            | {edge.relation for edge in self.edges}
        )
        symbol_bits = sum(len(symbol.encode("utf-8")) * 8 + 8 for symbol in symbols)
        pointer_bits = max(1, math.ceil(math.log2(max(2, len(symbols)))))
        node_id_bits = max(1, math.ceil(math.log2(max(2, len(self.nodes)))))
        node_bits = sum(
            node_id_bits
            + 1
            + pointer_bits
            + 1
            + len(node.arguments) * pointer_bits
            for node in self.nodes
        )
        edge_bits = len(self.edges) * (
            2 * node_id_bits
            + max(1, math.ceil(math.log2(len(EDGE_RELATIONS))))
        )
        return symbol_bits + node_bits + edge_bits

    @property
    def flat_json_bits(self) -> int:
        payload = [
            {
                "kind": node.kind,
                "label": node.label,
                "arguments": list(node.arguments),
                "polarity": node.polarity,
                "source": node.source_span,
            }
            for node in self.nodes
        ]
        edges = [
            {
                "source": edge.source,
                "target": edge.target,
                "relation": edge.relation,
            }
            for edge in self.edges
        ]
        return len(
            json.dumps(
                {"nodes": payload, "edges": edges},
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        ) * 8


@dataclass(frozen=True)
class GraphWorkflowState:
    expression: str = "x"
    baseline: str = "x"
    last_test: str = "UNKNOWN"
    patch_index: int = 0
    report: str = ""


@dataclass(frozen=True)
class GraphExecutionResult:
    state: GraphWorkflowState
    executed: tuple[str, ...]
    skipped: tuple[str, ...]
    rollbacks: int
    tests: int


def canonical_text(raw: str) -> str:
    normalized = unicodedata.normalize("NFKC", raw).lower()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _split_units(raw: str) -> tuple[str, ...]:
    text = canonical_text(raw)
    text = text.replace("。", "\n").replace("！", "\n").replace("？", "\n")
    text = re.sub(
        r"、(?=(?:もう一度|別の|結果|最後|成功|失敗|テスト|試験))",
        "\n",
        text,
    )
    return tuple(unit.strip(" 、") for unit in text.splitlines() if unit.strip(" 、"))


def _predicate(text: str) -> tuple[str, tuple[str, ...], bool]:
    normalized = canonical_text(text)
    polarity = not bool(
        re.search(r"(?:ない|なければ|失敗しなければ|成功していなければ)", normalized)
    )
    if any(token in normalized for token in ("失敗", "fail")):
        return "TEST_STATUS", ("FAIL",), polarity
    if any(token in normalized for token in ("成功", "pass")):
        return "TEST_STATUS", ("PASS",), polarity
    if any(token in normalized for token in ("テスト", "試験", "pytest", "check")):
        return "TEST_STATUS", ("KNOWN",), polarity
    if "変更" in normalized or "修正" in normalized:
        return "CHANGE_EXISTS", ("last_change",), polarity
    return "CLAIM", (normalized,), polarity


def _event_arguments(operation: str, text: str) -> tuple[str, ...]:
    normalized = canonical_text(text)
    if operation == "VERIFY":
        if any(token in normalized for token in ("テスト", "試験", "pytest", "成功", "失敗")):
            return ("tests",)
        if any(token in normalized for token in ("根拠", "出典", "引用")):
            return ("evidence",)
        return ("result",)
    if operation == "RETRACT":
        return ("last_change",)
    if operation == "SET":
        if any(token in normalized for token in ("段落", "文章", "原稿")):
            return ("document",)
        return ("change",)
    if operation == "EMIT":
        return ("result",)
    return ()


def _ground_operation(text: str, grounder: Grounder) -> tuple[str | None, int]:
    result = grounder.predict(text)
    return result.operation, result.feature_reads


def parse_event_graph(raw: str, grounder: Grounder) -> EventGraph:
    nodes: list[EventNode] = []
    edges: list[EventEdge] = []
    unresolved: list[str] = []
    feature_reads = 0
    previous_event: int | None = None
    last_change_event: int | None = None

    def add_node(
        kind: str,
        label: str,
        arguments: tuple[str, ...],
        polarity: bool,
        source: str,
    ) -> int:
        identifier = len(nodes)
        nodes.append(EventNode(identifier, kind, label, arguments, polarity, source))
        return identifier

    def add_event(operation: str, text: str, polarity: bool = True) -> int:
        nonlocal previous_event, last_change_event
        identifier = add_node(
            "EVENT",
            operation,
            _event_arguments(operation, text),
            polarity,
            text,
        )
        if previous_event is not None:
            edges.append(EventEdge(previous_event, identifier, "NEXT"))
        previous_event = identifier
        if operation == "SET" and polarity:
            last_change_event = identifier
        if (
            operation == "RETRACT"
            and any(token in text for token in ("その", "それ", "直前", "変更"))
            and last_change_event is not None
        ):
            edges.append(EventEdge(identifier, last_change_event, "REFERS_TO"))
        return identifier

    for unit in _split_units(raw):
        condition_match = re.match(
            r"^(?P<condition>.+?)(?P<connector>たら|場合は|なら|なければ)(?P<action>.+)$",
            unit,
        )
        if condition_match:
            condition_text = condition_match.group("condition")
            action_text = condition_match.group("action").strip(" 、")
            predicate, arguments, condition_polarity = _predicate(
                condition_text + condition_match.group("connector")
            )
            condition_id = add_node(
                "PROPOSITION",
                predicate,
                arguments,
                condition_polarity,
                condition_text,
            )
            operation, reads = _ground_operation(action_text, grounder)
            feature_reads += reads
            if operation is None:
                unresolved.append(action_text)
                continue
            action_polarity = not bool(re.search(r"(?:ないで|しないで|禁止)", action_text))
            action_id = add_event(operation, action_text, action_polarity)
            relation = "CONDITION_TRUE" if condition_polarity else "CONDITION_FALSE"
            edges.append(EventEdge(condition_id, action_id, relation))
            continue

        operation, reads = _ground_operation(unit, grounder)
        feature_reads += reads

        has_report = any(token in unit for token in ("報告", "教えて", "知らせ", "送信", "出力"))
        has_status = any(token in unit for token in ("成功", "失敗", "pass", "fail"))
        if has_report and has_status:
            if any(token in unit for token in ("確認", "照合", "検証", "実行")):
                add_event("VERIFY", unit)
            emit_id = add_event("EMIT", unit)
            predicate, arguments, polarity = _predicate(unit)
            proposition_id = add_node(
                "PROPOSITION",
                predicate,
                arguments,
                polarity,
                unit,
            )
            edges.append(EventEdge(emit_id, proposition_id, "CONTENT"))
            continue

        if (
            has_status
            and previous_event is not None
            and nodes[previous_event].label == "EMIT"
            and not any(token in unit for token in ("確認", "照合", "検証", "実行"))
        ):
            predicate, arguments, polarity = _predicate(unit)
            proposition_id = add_node(
                "PROPOSITION",
                predicate,
                arguments,
                polarity,
                unit,
            )
            edges.append(EventEdge(previous_event, proposition_id, "CONTENT"))
            continue

        if operation is None:
            unresolved.append(unit)
            continue
        polarity = not bool(re.search(r"(?:ないで|しないで|禁止)", unit))
        event_id = add_event(operation, unit, polarity)

        quoted = re.search(r"[「『](.+?)[」』]", unit)
        if operation == "EMIT" and quoted:
            proposition_id = add_node(
                "PROPOSITION",
                "QUOTE",
                (quoted.group(1),),
                True,
                quoted.group(0),
            )
            edges.append(EventEdge(event_id, proposition_id, "CONTENT"))

    return EventGraph(tuple(nodes), tuple(edges), tuple(unresolved), feature_reads)


def _run_tests(expression: str) -> bool:
    def evaluate(value: int) -> int:
        if expression == "x":
            return value
        if expression == "x + 1":
            return value + 1
        if expression == "x * x + 1":
            return value * value + 1
        raise ValueError(expression)

    return all(evaluate(value) == expected for value, expected in ((2, 5), (3, 10)))


def execute_graph_workflow(graph: EventGraph) -> GraphExecutionResult:
    state = GraphWorkflowState()
    executed: list[str] = []
    skipped: list[str] = []
    rollbacks = 0
    tests = 0

    conditions_by_target: dict[int, list[EventNode]] = {}
    for edge in graph.edges:
        if edge.relation not in ("CONDITION_TRUE", "CONDITION_FALSE"):
            continue
        proposition = graph.nodes[edge.source]
        conditions_by_target.setdefault(edge.target, []).append(proposition)

    for node in graph.event_nodes():
        allowed = True
        for condition in conditions_by_target.get(node.identifier, []):
            if condition.label == "TEST_STATUS":
                wanted = condition.arguments[0]
                actual = state.last_test
                satisfied = actual == wanted
                if not condition.polarity:
                    satisfied = not satisfied
                allowed = allowed and satisfied
        if not allowed or not node.polarity:
            skipped.append(node.label)
            continue

        if node.label == "SET":
            patch_index = state.patch_index + 1
            expression = "x + 1" if patch_index == 1 else "x * x + 1"
            state = replace(state, expression=expression, patch_index=patch_index)
        elif node.label == "VERIFY":
            tests += 1
            state = replace(state, last_test="PASS" if _run_tests(state.expression) else "FAIL")
        elif node.label == "RETRACT":
            rollbacks += 1
            state = replace(state, expression=state.baseline)
        elif node.label == "EMIT":
            state = replace(
                state,
                report=(
                    f"最終式は{state.expression}です。"
                    f"テスト結果は{state.last_test}です。"
                ),
            )
        else:
            raise ValueError(node.label)
        executed.append(node.label)

    return GraphExecutionResult(state, tuple(executed), tuple(skipped), rollbacks, tests)


def event_multiset(graph: EventGraph) -> Mapping[str, int]:
    counts = {operation: 0 for operation in OPERATIONS}
    for operation in graph.operations():
        counts[operation] += 1
    return counts


def event_recall(predicted: EventGraph, expected: Iterable[str]) -> float:
    expected_items = list(expected)
    predicted_counts = dict(event_multiset(predicted))
    matched = 0
    for operation in expected_items:
        if predicted_counts.get(operation, 0) > 0:
            predicted_counts[operation] -= 1
            matched += 1
    return matched / len(expected_items)


def edge_relation_recall(predicted: EventGraph, expected: Iterable[str]) -> float:
    expected_items = list(expected)
    available = [edge.relation for edge in predicted.edges]
    matched = 0
    for relation in expected_items:
        if relation in available:
            available.remove(relation)
            matched += 1
    return matched / len(expected_items)
