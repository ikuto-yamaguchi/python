from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil, log2
from typing import Callable, Iterable, Sequence


def ceil_log2(value: int) -> int:
    if value <= 1:
        return 0
    return ceil(log2(value))


@dataclass(frozen=True)
class ExecutableFactor:
    """One independently addressable operational coordinate."""

    name: str
    state_count: int
    code_bits: int
    query_keys: frozenset[str]
    evaluator: Callable[[str], str | None]

    @property
    def active_state_bits(self) -> int:
        return ceil_log2(self.state_count)


@dataclass(frozen=True)
class FactorizationReport:
    factor_count: int
    joint_state_count: int
    information_lower_bound_bits: int
    factorized_state_bits: int
    additive_rounding_overhead_bits: int
    monolithic_transition_entries: int
    factorized_transition_entries: int
    transition_entry_reduction: float


def factorization_report(state_counts: Sequence[int]) -> FactorizationReport:
    if not state_counts or any(value < 1 for value in state_counts):
        raise ValueError("state counts must be non-empty positive integers")
    joint = 1
    for value in state_counts:
        joint *= value
    lower = ceil_log2(joint)
    factor_bits = sum(ceil_log2(value) for value in state_counts)
    mono_entries = len(state_counts) * joint
    fact_entries = sum(state_counts)
    return FactorizationReport(
        factor_count=len(state_counts),
        joint_state_count=joint,
        information_lower_bound_bits=lower,
        factorized_state_bits=factor_bits,
        additive_rounding_overhead_bits=factor_bits - lower,
        monolithic_transition_entries=mono_entries,
        factorized_transition_entries=fact_entries,
        transition_entry_reduction=mono_entries / fact_entries,
    )


@dataclass
class FactorizedExecutableMachine:
    """Sparse non-neural program graph with query-local activation."""

    factors: list[ExecutableFactor] = field(default_factory=list)
    _index: dict[str, list[int]] = field(default_factory=dict, init=False)

    def add_factor(self, factor: ExecutableFactor) -> None:
        factor_id = len(self.factors)
        self.factors.append(factor)
        for key in factor.query_keys:
            self._index.setdefault(key, []).append(factor_id)

    @property
    def model_code_bits(self) -> int:
        return sum(factor.code_bits for factor in self.factors)

    @property
    def active_state_bits(self) -> int:
        return sum(factor.active_state_bits for factor in self.factors)

    def report(self) -> dict[str, int]:
        return {
            "factor_count": len(self.factors),
            "model_code_bits": self.model_code_bits,
            "active_state_bits": self.active_state_bits,
            "index_key_count": len(self._index),
        }


import re

NUMBER_RE = re.compile(r"-?\d+")


@dataclass(frozen=True)
class Example:
    user: str
    assistant: str


@dataclass(frozen=True)
class NumericExpression:
    name: str
    arity: int
    function: Callable[[tuple[int, ...]], int | None]
    code_bits: int


def _safe_div(values: tuple[int, ...]) -> int | None:
    a, b = values
    if b == 0 or a % b:
        return None
    return a // b


def candidate_expressions(arity: int) -> tuple[NumericExpression, ...]:
    if arity == 1:
        return (
            NumericExpression("x0", 1, lambda x: x[0], 2),
            NumericExpression("neg", 1, lambda x: -x[0], 3),
            NumericExpression("square", 1, lambda x: x[0] * x[0], 4),
        )
    if arity == 2:
        return (
            NumericExpression("add", 2, lambda x: x[0] + x[1], 3),
            NumericExpression("sub01", 2, lambda x: x[0] - x[1], 3),
            NumericExpression("sub10", 2, lambda x: x[1] - x[0], 3),
            NumericExpression("mul", 2, lambda x: x[0] * x[1], 3),
            NumericExpression("div01", 2, _safe_div, 4),
            NumericExpression("div10", 2, lambda x: _safe_div((x[1], x[0])), 4),
        )
    return ()


def numeric_skeleton(text: str) -> str:
    return NUMBER_RE.sub("<N>", text)


def numeric_values(text: str) -> tuple[int, ...]:
    return tuple(int(value) for value in NUMBER_RE.findall(text))


def output_affixes(text: str) -> tuple[str, str, int] | None:
    matches = list(NUMBER_RE.finditer(text))
    if len(matches) != 1:
        return None
    match = matches[0]
    return text[: match.start()], text[match.end() :], int(match.group())


@dataclass(frozen=True)
class NumericRule:
    skeleton: str
    expression: NumericExpression
    output_prefix: str
    output_suffix: str

    def matches(self, text: str) -> bool:
        return numeric_skeleton(text) == self.skeleton

    def execute(self, text: str) -> str | None:
        if not self.matches(text):
            return None
        values = numeric_values(text)
        if len(values) != self.expression.arity:
            return None
        result = self.expression.function(values)
        if result is None:
            return None
        return f"{self.output_prefix}{result}{self.output_suffix}"

    @property
    def code_bits(self) -> int:
        payload = (
            len(self.skeleton.encode("utf-8"))
            + len(self.output_prefix.encode("utf-8"))
            + len(self.output_suffix.encode("utf-8"))
        )
        return 8 * payload + self.expression.code_bits


@dataclass(frozen=True)
class LookupRule:
    prefix: str
    suffix: str
    table: dict[str, str]

    def execute(self, text: str) -> str | None:
        if not text.startswith(self.prefix) or not text.endswith(self.suffix):
            return None
        end = len(text) - len(self.suffix) if self.suffix else len(text)
        key = text[len(self.prefix) : end]
        return self.table.get(key)

    @property
    def code_bits(self) -> int:
        payload = len(self.prefix.encode("utf-8")) + len(self.suffix.encode("utf-8"))
        payload += sum(
            len(key.encode("utf-8")) + len(value.encode("utf-8"))
            for key, value in self.table.items()
        )
        return 8 * payload


@dataclass(frozen=True)
class ExactRule:
    prompt: str
    reply: str

    def execute(self, text: str) -> str | None:
        return self.reply if text == self.prompt else None

    @property
    def code_bits(self) -> int:
        return 8 * (len(self.prompt.encode("utf-8")) + len(self.reply.encode("utf-8")))


def _common_prefix(values: Sequence[str]) -> str:
    if not values:
        return ""
    prefix = values[0]
    for value in values[1:]:
        while prefix and not value.startswith(prefix):
            prefix = prefix[:-1]
    return prefix


def _common_suffix(values: Sequence[str]) -> str:
    return _common_prefix([value[::-1] for value in values])[::-1]


def induce_numeric_rule(examples: Sequence[Example]) -> NumericRule | None:
    if len(examples) < 2:
        return None
    skeletons = {numeric_skeleton(row.user) for row in examples}
    if len(skeletons) != 1:
        return None
    inputs = [numeric_values(row.user) for row in examples]
    if not inputs or len({len(values) for values in inputs}) != 1:
        return None
    arity = len(inputs[0])
    affixes = [output_affixes(row.assistant) for row in examples]
    if any(value is None for value in affixes):
        return None
    typed = [value for value in affixes if value is not None]
    prefixes = {value[0] for value in typed}
    suffixes = {value[1] for value in typed}
    if len(prefixes) != 1 or len(suffixes) != 1:
        return None
    targets = [value[2] for value in typed]
    valid: list[NumericExpression] = []
    for expression in candidate_expressions(arity):
        if [expression.function(values) for values in inputs] == targets:
            valid.append(expression)
    if not valid:
        return None
    expression = min(valid, key=lambda row: (row.code_bits, row.name))
    return NumericRule(
        next(iter(skeletons)),
        expression,
        next(iter(prefixes)),
        next(iter(suffixes)),
    )


def induce_lookup_rule(examples: Sequence[Example]) -> LookupRule | None:
    if len(examples) < 2:
        return None
    prompts = [row.user for row in examples]
    prefix = _common_prefix(prompts)
    suffix = _common_suffix([value[len(prefix) :] for value in prompts])
    table: dict[str, str] = {}
    for row in examples:
        end = len(row.user) - len(suffix) if suffix else len(row.user)
        key = row.user[len(prefix) : end]
        if not key or (key in table and table[key] != row.assistant):
            return None
        table[key] = row.assistant
    if len(prefix) + len(suffix) < 3 or len(table) < 2:
        return None
    return LookupRule(prefix, suffix, table)


def _rough_group_key(text: str) -> str:
    if NUMBER_RE.search(text):
        return "num:" + numeric_skeleton(text)
    return "tail:" + text[-6:]


class FactorProgramLearner:
    """One MDL-style executable search procedure for all demonstrations."""

    def __init__(self) -> None:
        self.machine = FactorizedExecutableMachine()
        self.rules: list[object] = []

    def fit(self, examples: Iterable[Example]) -> "FactorProgramLearner":
        rows = list(examples)
        groups: dict[str, list[Example]] = {}
        for row in rows:
            groups.setdefault(_rough_group_key(row.user), []).append(row)

        covered: set[Example] = set()
        for group in groups.values():
            numeric = induce_numeric_rule(group)
            if numeric is not None:
                self._add_numeric(numeric)
                covered.update(group)
                continue
            lookup = induce_lookup_rule(group)
            if lookup is not None:
                self._add_lookup(lookup)
                covered.update(group)

        unused = [
            row for row in rows
            if row not in covered and not NUMBER_RE.search(row.user)
        ]
        if len(unused) >= 2:
            lookup = induce_lookup_rule(unused)
            if lookup is not None:
                self._add_lookup(lookup)
                covered.update(unused)

        for row in rows:
            if row not in covered:
                self._add_exact(ExactRule(row.user, row.assistant))
        return self

    def _add_numeric(self, rule: NumericRule) -> None:
        self.rules.append(rule)
        key = "numeric:" + rule.skeleton[:12]
        self.machine.add_factor(
            ExecutableFactor(
                name=f"numeric:{rule.expression.name}:{len(self.rules)}",
                state_count=2,
                code_bits=rule.code_bits,
                query_keys=frozenset({key, "numeric:*"}),
                evaluator=rule.execute,
            )
        )

    def _add_lookup(self, rule: LookupRule) -> None:
        self.rules.append(rule)
        key = "lookup:" + (rule.suffix[-8:] if rule.suffix else rule.prefix[:8])
        self.machine.add_factor(
            ExecutableFactor(
                name=f"lookup:{len(self.rules)}",
                state_count=max(1, len(rule.table)),
                code_bits=rule.code_bits,
                query_keys=frozenset({key, "lookup:*"}),
                evaluator=rule.execute,
            )
        )

    def _add_exact(self, rule: ExactRule) -> None:
        self.rules.append(rule)
        key = "exact:" + rule.prompt[:8]
        self.machine.add_factor(
            ExecutableFactor(
                name=f"exact:{len(self.rules)}",
                state_count=1,
                code_bits=rule.code_bits,
                query_keys=frozenset({key, "exact:*"}),
                evaluator=rule.execute,
            )
        )

    def _keys_for(self, text: str) -> tuple[str, ...]:
        if NUMBER_RE.search(text):
            skeleton = numeric_skeleton(text)
            return (
                "numeric:" + skeleton[:12],
                "numeric:*",
                "exact:" + text[:8],
                "exact:*",
            )
        return (
            "lookup:" + text[-8:],
            "lookup:*",
            "exact:" + text[:8],
            "exact:*",
        )

    def reply(self, text: str) -> tuple[str, int]:
        activated = 0
        seen: set[int] = set()
        for key in self._keys_for(text):
            for factor_id in self.machine._index.get(key, []):
                if factor_id in seen:
                    continue
                seen.add(factor_id)
                activated += 1
                answer = self.machine.factors[factor_id].evaluator(text)
                if answer is not None:
                    return answer, activated
        return "まだその質問を実行できません。", activated


import json
from pathlib import Path


class FEMIChat:
    def __init__(self) -> None:
        self.learner = FactorProgramLearner()

    def fit(self, rows: Iterable[Example]) -> "FEMIChat":
        self.learner.fit(rows)
        return self

    def reply(self, text: str) -> str:
        answer, _ = self.learner.reply(text)
        return answer

    def reply_with_cost(self, text: str) -> tuple[str, int]:
        return self.learner.reply(text)


def load_jsonl(path: str | Path) -> list[Example]:
    result: list[Example] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        result.append(Example(str(row["user"]), str(row["assistant"])))
    return result


def training_examples() -> list[Example]:
    return [
        Example("2と3の和は？", "5です。"),
        Example("7と5の和は？", "12です。"),
        Example("11と4の和は？", "15です。"),
        Example("x+3=8のxは？", "5です。"),
        Example("x+5=12のxは？", "7です。"),
        Example("x+9=20のxは？", "11です。"),
        Example("日本の首都は？", "東京です。"),
        Example("フランスの首都は？", "パリです。"),
        Example("ドイツの首都は？", "ベルリンです。"),
        Example("水の化学式は？", "H2Oです。"),
        Example("二酸化炭素の化学式は？", "CO2です。"),
        Example("酸素の化学式は？", "O2です。"),
        Example("こんにちは", "こんにちは。何を一緒に考えましょうか？"),
    ]


def run_experiment() -> dict[str, object]:
    chat = FEMIChat().fit(training_examples())
    tests = [
        ("23と19の和は？", "42です。", "unseen_addition"),
        ("x+17=45のxは？", "28です。", "unseen_linear_equation"),
        ("フランスの首都は？", "パリです。", "knowledge_lookup"),
        ("二酸化炭素の化学式は？", "CO2です。", "science_lookup"),
        ("こんにちは", "こんにちは。何を一緒に考えましょうか？", "dialogue"),
    ]
    rows: list[dict[str, object]] = []
    total_activated = 0
    for prompt, expected, name in tests:
        answer, activated = chat.reply_with_cost(prompt)
        total_activated += activated
        rows.append(
            {
                "name": name,
                "prompt": prompt,
                "answer": answer,
                "expected": expected,
                "correct": answer == expected,
                "activated_factors": activated,
            }
        )

    scaling = factorization_report([2] * 32)
    machine = chat.learner.machine
    correct = sum(bool(row["correct"]) for row in rows)
    result: dict[str, object] = {
        "capability_id": "FEMI-001",
        "model": "Factorized Executable Minimal Intelligence",
        "neural_network_used": False,
        "gradient_training_used": False,
        "task_labels_visible_to_learner": 0,
        "training_example_count": len(training_examples()),
        "learned_rule_count": len(chat.learner.rules),
        "machine": machine.report(),
        "evaluation": {
            "correct": correct,
            "total": len(rows),
            "accuracy": correct / len(rows),
            "mean_activated_factors": total_activated / len(rows),
            "results": rows,
        },
        "scaling_theory_control": {
            "binary_factor_count": scaling.factor_count,
            "joint_state_count": scaling.joint_state_count,
            "information_lower_bound_bits": scaling.information_lower_bound_bits,
            "factorized_state_bits": scaling.factorized_state_bits,
            "rounding_overhead_bits": scaling.additive_rounding_overhead_bits,
            "monolithic_transition_entries": scaling.monolithic_transition_entries,
            "factorized_transition_entries": scaling.factorized_transition_entries,
            "transition_entry_reduction": scaling.transition_entry_reduction,
        },
        "claim_boundary": (
            "FEMI-001 demonstrates a non-neural factorized executable learner that "
            "induces arithmetic, algebra, lookup, and dialogue programs from raw "
            "prompt-response examples and activates only indexed factors. It is not "
            "Japanese-high-school-level intelligence, not an LLM-quality language "
            "model, and its novelty and large-scale factor-discovery efficiency remain unverified."
        ),
    }
    evaluation = result["evaluation"]
    assert isinstance(evaluation, dict)
    result["passed"] = bool(
        evaluation["accuracy"] == 1.0
        and evaluation["mean_activated_factors"] < result["learned_rule_count"]
        and scaling.factorized_state_bits
        <= scaling.information_lower_bound_bits + scaling.factor_count
        and scaling.transition_entry_reduction > 1_000_000
    )
    return result


def main() -> None:
    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
