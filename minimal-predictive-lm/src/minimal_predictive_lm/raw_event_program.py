from __future__ import annotations

from dataclasses import dataclass, replace
import json
import math
import re
import unicodedata
from typing import Iterable, Mapping


OPERATIONS = ("SET", "VERIFY", "RETRACT", "EMIT")


@dataclass(frozen=True)
class EffectTrace:
    source: str
    raw: str
    before: tuple[tuple[str, str], ...]
    after: tuple[tuple[str, str], ...]
    observed: bool = False
    emitted: bool = False
    restored: bool = False


@dataclass(frozen=True)
class FeatureRule:
    operation: str
    feature: str
    support: int


@dataclass(frozen=True)
class GroundingResult:
    operation: str | None
    scores: Mapping[str, int]
    matched_rules: int
    feature_reads: int


@dataclass(frozen=True)
class RawGrounder:
    rules: tuple[FeatureRule, ...]
    training_examples: int

    def predict(self, raw: str) -> GroundingResult:
        features = raw_features(raw)
        scores = {operation: 0 for operation in OPERATIONS}
        matched = 0
        index = {rule.feature: rule for rule in self.rules}
        for feature in features:
            rule = index.get(feature)
            if rule is None:
                continue
            matched += 1
            payload = feature.split(":", 1)[1]
            scores[rule.operation] += len(payload)
        maximum = max(scores.values())
        winners = [
            operation
            for operation, score in scores.items()
            if score == maximum and score > 0
        ]
        operation = winners[0] if len(winners) == 1 else None
        return GroundingResult(operation, scores, matched, len(features))

    @property
    def description_bits(self) -> int:
        operation_bits = math.ceil(math.log2(len(OPERATIONS)))
        count_bits = math.ceil(math.log2(self.training_examples + 1))
        pointer_bits = math.ceil(math.log2(len(self.rules) + 1))
        rule_bits = sum(
            len(rule.feature.encode("utf-8")) * 8
            + 8
            + operation_bits
            + count_bits
            + pointer_bits
            for rule in self.rules
        )
        operation_schema_bits = len(OPERATIONS) * 32
        return rule_bits + operation_schema_bits


@dataclass(frozen=True)
class WorkflowState:
    expression: str = "x"
    baseline: str = "x"
    last_test: str = "UNKNOWN"
    patch_index: int = 0
    report: str = ""


@dataclass(frozen=True)
class WorkflowEvent:
    operation: str
    request: str
    artifact: str
    artifact_operation: str | None
    state: WorkflowState


@dataclass(frozen=True)
class WorkflowResult:
    plan: tuple[str, ...]
    events: tuple[WorkflowEvent, ...]
    final_state: WorkflowState
    request_grounding_correct: int
    artifact_grounding_correct: int
    conversion_boundaries_separate: int
    serialized_copy_bits_separate: int


def canonical_text(raw: str) -> str:
    normalized = unicodedata.normalize("NFKC", raw).lower()
    normalized = re.sub(
        r"[^0-9a-zA-Zぁ-んァ-ヶ一-龠_+*=<>.\-]+",
        " ",
        normalized,
    )
    return " ".join(normalized.split())


def raw_features(raw: str) -> frozenset[str]:
    normalized = canonical_text(raw)
    features: set[str] = set()
    for token in normalized.split():
        features.add(f"w:{token}")
        for japanese in re.findall(r"[ぁ-んァ-ヶ一-龠]+", token):
            for width in range(2, min(5, len(japanese)) + 1):
                for start in range(len(japanese) - width + 1):
                    features.add(
                        f"j{width}:{japanese[start:start + width]}"
                    )
        for ascii_token in re.findall(r"[a-z0-9_]+", token):
            features.add(f"a:{ascii_token}")
            for width in range(3, min(6, len(ascii_token)) + 1):
                for start in range(len(ascii_token) - width + 1):
                    features.add(
                        f"a{width}:{ascii_token[start:start + width]}"
                    )
        for symbol in "+*=<>":
            if symbol in token:
                features.add(f"s:{symbol}")
    return frozenset(features)


def infer_operation(trace: EffectTrace) -> str:
    if trace.emitted:
        return "EMIT"
    if trace.restored:
        return "RETRACT"
    if trace.observed and trace.before == trace.after:
        return "VERIFY"
    if trace.before != trace.after:
        return "SET"
    raise ValueError(f"trace has no identifiable effect: {trace.raw!r}")


def _feature_cost(feature: str) -> float:
    payload = feature.split(":", 1)[1]
    description = len(feature.encode("utf-8")) * 8 + 8
    # Very short fragments are cheap to store but collide easily.  This is an
    # explicit expected-collision proxy rather than a hidden hand-written
    # preference for particular words.
    collision = 64.0 / max(1, len(payload) ** 2)
    return description + collision


def induce_raw_grounder(
    traces: Iterable[EffectTrace],
    *,
    minimum_support: int = 2,
) -> RawGrounder:
    examples = list(traces)
    if not examples:
        raise ValueError("at least one trace is required")
    feature_sets = {trace.raw: raw_features(trace.raw) for trace in examples}
    labels = {trace.raw: infer_operation(trace) for trace in examples}
    selected_rules: list[FeatureRule] = []

    for operation in OPERATIONS:
        positives = [trace.raw for trace in examples if labels[trace.raw] == operation]
        negatives = [trace.raw for trace in examples if labels[trace.raw] != operation]
        if not positives:
            raise ValueError(f"operation {operation} has no examples")
        candidate_features = set().union(
            *(feature_sets[raw] for raw in positives)
        )
        candidates: list[tuple[str, frozenset[str], float]] = []
        for feature in candidate_features:
            covered = frozenset(
                raw for raw in positives if feature in feature_sets[raw]
            )
            contamination = sum(
                feature in feature_sets[raw] for raw in negatives
            )
            if len(covered) < minimum_support or contamination:
                continue
            candidates.append((feature, covered, _feature_cost(feature)))

        uncovered = set(positives)
        chosen: list[tuple[str, frozenset[str], float]] = []
        while uncovered:
            available = [
                candidate
                for candidate in candidates
                if candidate[1].intersection(uncovered)
            ]
            if not available:
                raise ValueError(
                    f"no stable feature cover for {operation}; "
                    f"uncovered={sorted(uncovered)!r}"
                )
            best = max(
                available,
                key=lambda candidate: (
                    len(candidate[1].intersection(uncovered))
                    / candidate[2],
                    len(candidate[1].intersection(uncovered)),
                    len(candidate[0]),
                    candidate[0],
                ),
            )
            chosen.append(best)
            uncovered.difference_update(best[1])

        for feature, covered, _ in chosen:
            selected_rules.append(
                FeatureRule(operation, feature, len(covered))
            )

    return RawGrounder(
        tuple(sorted(selected_rules, key=lambda rule: (rule.operation, rule.feature))),
        len(examples),
    )


def exact_surface_accuracy(
    training: Iterable[EffectTrace],
    validation: Iterable[EffectTrace],
) -> float:
    lookup = {
        canonical_text(trace.raw): infer_operation(trace)
        for trace in training
    }
    validation_items = list(validation)
    correct = sum(
        lookup.get(canonical_text(trace.raw)) == infer_operation(trace)
        for trace in validation_items
    )
    return correct / len(validation_items)


def grounding_accuracy(
    grounder: RawGrounder,
    validation: Iterable[EffectTrace],
) -> float:
    validation_items = list(validation)
    correct = sum(
        grounder.predict(trace.raw).operation == infer_operation(trace)
        for trace in validation_items
    )
    return correct / len(validation_items)


def split_clauses(raw: str) -> tuple[str, ...]:
    return tuple(
        clause.strip()
        for clause in re.split(r"[。！？]+", raw)
        if clause.strip()
    )


def _run_transform_tests(expression: str) -> tuple[bool, tuple[tuple[int, int, int], ...]]:
    cases = ((2, 5), (3, 10))

    def evaluate(value: int) -> int:
        if expression == "x":
            return value
        if expression == "x + 1":
            return value + 1
        if expression == "x * x + 1":
            return value * value + 1
        raise ValueError(f"unknown expression: {expression}")

    failures = tuple(
        (value, expected, evaluate(value))
        for value, expected in cases
        if evaluate(value) != expected
    )
    return not failures, failures


def _serialized_state_bits(state: WorkflowState) -> int:
    payload = json.dumps(
        {
            "goal": "fix_transform",
            "expression": state.expression,
            "test": state.last_test,
            "step": state.patch_index,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return len(payload) * 8


def execute_transform_workflow(
    request: str,
    grounder: RawGrounder,
) -> WorkflowResult:
    clauses = split_clauses(request)
    grounded = tuple(grounder.predict(clause).operation for clause in clauses)
    if any(operation is None for operation in grounded):
        raise ValueError(f"ungrounded request clauses: {list(zip(clauses, grounded))!r}")

    state = WorkflowState()
    events: list[WorkflowEvent] = []
    request_correct = 0
    artifact_correct = 0
    expected_plan = ("SET", "VERIFY", "RETRACT", "SET", "VERIFY", "EMIT")

    for expected, operation, clause in zip(expected_plan, grounded, clauses):
        request_correct += int(operation == expected)
        artifact = ""
        artifact_expected = operation

        if operation == "SET":
            patch_index = state.patch_index + 1
            expression = "x + 1" if patch_index == 1 else "x * x + 1"
            state = replace(state, expression=expression, patch_index=patch_index)
            artifact = f"Return(value={expression})"
        elif operation == "VERIFY":
            passed, failures = _run_transform_tests(state.expression)
            if passed:
                state = replace(state, last_test="PASS")
                artifact = "PASSED 2 tests"
            else:
                state = replace(state, last_test="FAIL")
                first = failures[0]
                artifact = (
                    "FAILED test_transform "
                    f"expected={first[1]} got={first[2]}"
                )
        elif operation == "RETRACT":
            if state.last_test == "FAIL":
                state = replace(state, expression=state.baseline)
                artifact = "git restore module.py"
            else:
                artifact_expected = "EMIT"
                artifact = "rollback skipped"
        elif operation == "EMIT":
            report = (
                "作業結果を報告します。最初の修正は失敗したため戻し、"
                f"{state.expression}へ修正して全テストに成功しました。"
            )
            state = replace(state, report=report)
            artifact = report
        else:
            raise AssertionError(operation)

        artifact_operation = grounder.predict(artifact).operation
        artifact_correct += int(artifact_operation == artifact_expected)
        events.append(
            WorkflowEvent(
                operation,
                clause,
                artifact,
                artifact_operation,
                state,
            )
        )

    # A domain-separated pipeline must hand the active state into an action
    # runtime and copy the result back into the planner.  The shared event
    # runtime keeps one state object and has no internal representation
    # boundary.  We expose both boundary count and the bytes of this concrete
    # JSON hand-off instead of burying them in an arbitrary scalar score.
    conversion_boundaries = 2 * len(events)
    copied_bits = 2 * sum(_serialized_state_bits(event.state) for event in events)

    return WorkflowResult(
        expected_plan,
        tuple(events),
        state,
        request_correct,
        artifact_correct,
        conversion_boundaries,
        copied_bits,
    )
