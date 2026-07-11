from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import json
import re
import unicodedata
from typing import Iterable, Mapping, Sequence

from .primitive_invention import (
    InventedStringProgram,
    StringTransformExample,
    primitive_accuracy,
    propose_string_primitives,
)
from .universal_program_induction import (
    InducedProgram,
    Scalar,
    TransitionTrace,
    UnexpressibleTaskError,
    induce_program,
    program_accuracy,
)


_KEY_VALUE = re.compile(
    r"\b([A-Za-z_][A-Za-z0-9_.-]*)\s*=\s*([A-Za-z0-9_.+-]+)"
)
_NUMBER = re.compile(r"[-+]?\d+(?:/\d+|\.\d+)?")
_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_-]{1,}")
_SYMBOLS = frozenset({"+", "-", "*", "/"})


def _description_bits(payload: object) -> int:
    return len(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ) * 8


def _parse_scalar(raw: str) -> Scalar:
    value = unicodedata.normalize("NFKC", raw).strip()
    lowered = value.casefold()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if re.fullmatch(r"[-+]?\d+(?:/\d+|\.\d+)?", value):
        number = Fraction(value)
        return number.numerator if number.denominator == 1 else number
    return value


def _value_type(value: Scalar) -> str:
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, str):
        return "str"
    return "num"


@dataclass(frozen=True)
class ParsedPrompt:
    arguments: tuple[Scalar, ...]
    before: tuple[tuple[str, Scalar], ...]
    features: frozenset[str]

    def before_dict(self) -> dict[str, Scalar]:
        return dict(self.before)

    @property
    def signature(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        return (
            tuple(_value_type(value) for value in self.arguments),
            tuple(key for key, _ in self.before),
        )


@dataclass(frozen=True)
class MixedInteraction:
    prompt: str
    trace: TransitionTrace


@dataclass(frozen=True)
class ProgramHypothesis:
    program: InducedProgram
    kind: str = "typed_program"

    def execute(
        self, arguments: Sequence[Scalar], before: Mapping[str, Scalar]
    ) -> tuple[dict[str, Scalar], Scalar]:
        return self.program.execute(arguments, before)

    @property
    def description_bits(self) -> int:
        return self.program.description_bits

    def render(self) -> object:
        return {
            "kind": self.kind,
            "output": self.program.output.render(),
            "updates": [
                [key.render(), value.render()] for key, value in self.program.updates
            ],
        }


@dataclass(frozen=True)
class StringHypothesis:
    program: InventedStringProgram
    kind: str = "invented_string_program"

    def execute(
        self, arguments: Sequence[Scalar], before: Mapping[str, Scalar]
    ) -> tuple[dict[str, Scalar], Scalar]:
        if not all(isinstance(value, str) for value in arguments):
            raise TypeError("invented string program requires string arguments")
        output = self.program.execute(tuple(str(value) for value in arguments))
        return dict(before), output

    @property
    def description_bits(self) -> int:
        return self.program.description_bits

    def render(self) -> object:
        return {
            "kind": self.kind,
            "argument_index": self.program.argument_index,
            "primitive": self.program.primitive.render(),
        }


Hypothesis = ProgramHypothesis | StringHypothesis


@dataclass(frozen=True)
class RoutingRule:
    signature: tuple[tuple[str, ...], tuple[str, ...]]
    feature: str | None
    hypothesis: Hypothesis
    support: int

    @property
    def description_bits(self) -> int:
        return _description_bits(
            {
                "signature": self.signature,
                "feature": self.feature,
                "hypothesis": self.hypothesis.render(),
            }
        )


@dataclass(frozen=True)
class Prediction:
    output: Scalar | None
    after: tuple[tuple[str, Scalar], ...]
    matched_feature: str | None
    feature_reads: int
    operations: int


@dataclass(frozen=True)
class MixedTaskModel:
    rules: tuple[RoutingRule, ...]
    candidate_evaluations: int
    calibration_examples: int
    domain_specific_handlers: int = 0

    @property
    def description_bits(self) -> int:
        return _description_bits([rule.description_bits for rule in self.rules]) + sum(
            rule.hypothesis.description_bits for rule in self.rules
        )

    def predict(self, prompt: str) -> Prediction:
        parsed = parse_prompt(prompt)
        candidates = [rule for rule in self.rules if rule.signature == parsed.signature]
        feature_reads = 0
        selected: RoutingRule | None = None
        for rule in sorted(
            candidates,
            key=lambda row: (
                row.feature is None,
                -(len(row.feature) if row.feature is not None else 0),
                -row.support,
            ),
        ):
            feature_reads += 1
            if rule.feature is None or rule.feature in parsed.features:
                selected = rule
                break
        if selected is None:
            return Prediction(None, parsed.before, None, feature_reads, feature_reads)
        try:
            after, output = selected.hypothesis.execute(
                parsed.arguments, parsed.before_dict()
            )
        except (KeyError, IndexError, TypeError, ValueError, ZeroDivisionError):
            return Prediction(None, parsed.before, selected.feature, feature_reads, feature_reads)
        operation_count = feature_reads + 1
        if isinstance(selected.hypothesis, ProgramHypothesis):
            operation_count += selected.hypothesis.program.output.node_count
            operation_count += sum(
                key.node_count + value.node_count
                for key, value in selected.hypothesis.program.updates
            )
        else:
            operation_count += sum(len(str(value)) for value in parsed.arguments)
        return Prediction(
            output,
            tuple(sorted(after.items())),
            selected.feature,
            feature_reads,
            operation_count,
        )

    def render(self) -> object:
        return {
            "rules": [
                {
                    "signature": rule.signature,
                    "feature": rule.feature,
                    "support": rule.support,
                    "hypothesis": rule.hypothesis.render(),
                }
                for rule in self.rules
            ],
            "candidate_evaluations": self.candidate_evaluations,
            "calibration_examples": self.calibration_examples,
            "domain_specific_handlers": self.domain_specific_handlers,
        }


def lexical_features(prompt: str) -> frozenset[str]:
    text = unicodedata.normalize("NFKC", prompt).casefold()
    features = {f"word:{word}" for word in _WORD.findall(text)}
    features.update(f"symbol:{symbol}" for symbol in _SYMBOLS if symbol in text)
    return frozenset(features)


def parse_prompt(prompt: str) -> ParsedPrompt:
    normalized = unicodedata.normalize("NFKC", prompt)
    arguments: list[Scalar] = []
    before: dict[str, Scalar] = {}
    masked = list(normalized)
    matches = list(_KEY_VALUE.finditer(normalized))
    for match in matches:
        key = match.group(1)
        value = _parse_scalar(match.group(2))
        if key.casefold().startswith("state_"):
            before[key[6:]] = value
        else:
            arguments.append(value)
        for index in range(match.start(), match.end()):
            masked[index] = " "
    remainder = "".join(masked)
    if not matches:
        arguments.extend(_parse_scalar(token) for token in _NUMBER.findall(remainder))
    return ParsedPrompt(
        tuple(arguments),
        tuple(sorted(before.items())),
        lexical_features(normalized),
    )


def interaction_from_observation(
    prompt: str,
    *,
    after: Mapping[str, Scalar] | None = None,
    output: Scalar,
) -> MixedInteraction:
    parsed = parse_prompt(prompt)
    final_after = parsed.before_dict() if after is None else dict(after)
    return MixedInteraction(
        prompt,
        TransitionTrace.build(
            parsed.arguments,
            parsed.before_dict(),
            final_after,
            output,
        ),
    )


def _hypothesis_accuracy(
    hypothesis: Hypothesis, examples: Sequence[MixedInteraction]
) -> float:
    correct = 0
    for example in examples:
        try:
            after, output = hypothesis.execute(
                example.trace.arguments, example.trace.before_dict()
            )
        except (KeyError, IndexError, TypeError, ValueError, ZeroDivisionError):
            continue
        correct += int(after == example.trace.after_dict() and output == example.trace.output)
    return correct / len(examples) if examples else 0.0


def _fit_string_hypothesis(
    examples: Sequence[MixedInteraction],
) -> StringHypothesis | None:
    if len(examples) < 4:
        return None
    if any(
        len(example.trace.arguments) != 1
        or not isinstance(example.trace.arguments[0], str)
        or not isinstance(example.trace.output, str)
        or example.trace.before != example.trace.after
        for example in examples
    ):
        return None
    split = max(2, len(examples) // 2)
    training = tuple(
        StringTransformExample(
            "calibration-train",
            str(example.trace.arguments[0]),
            str(example.trace.output),
        )
        for example in examples[:split]
    )
    validation = tuple(
        StringTransformExample(
            "calibration-validation",
            str(example.trace.arguments[0]),
            str(example.trace.output),
        )
        for example in examples[split:]
    )
    if not validation:
        return None
    valid = [
        primitive
        for primitive in propose_string_primitives(training)
        if primitive_accuracy(primitive, training) == 1.0
        and primitive_accuracy(primitive, validation) == 1.0
    ]
    if not valid:
        return None
    primitive = min(valid, key=lambda row: (row.description_bits, row.kind))
    return StringHypothesis(InventedStringProgram(primitive, 0))


def _fit_hypothesis(
    examples: Sequence[MixedInteraction],
    *,
    max_candidates: int,
) -> tuple[Hypothesis | None, int]:
    string_hypothesis = _fit_string_hypothesis(examples)
    if string_hypothesis is not None:
        return string_hypothesis, len(examples)
    traces = tuple(example.trace for example in examples)
    try:
        result = induce_program(
            traces,
            max_depth=3,
            max_candidates=max_candidates,
        )
    except (UnexpressibleTaskError, ValueError):
        return None, max_candidates
    if program_accuracy(result.program, traces) != 1.0:
        return None, result.program.candidate_evaluations
    return ProgramHypothesis(result.program), result.program.candidate_evaluations


def _candidate_features(examples: Sequence[MixedInteraction]) -> tuple[str, ...]:
    counts: dict[str, int] = {}
    for example in examples:
        for feature in lexical_features(example.prompt):
            counts[feature] = counts.get(feature, 0) + 1
    return tuple(
        sorted(
            (
                feature
                for feature, count in counts.items()
                if 2 <= count < len(examples)
            ),
            key=lambda feature: (counts[feature], len(feature), feature),
        )
    )


def induce_mixed_task_model(
    calibration: Iterable[MixedInteraction],
    *,
    max_candidates_per_fit: int = 20_000,
) -> MixedTaskModel:
    examples = tuple(calibration)
    if not examples:
        raise ValueError("at least one calibration interaction is required")
    buckets: dict[
        tuple[tuple[str, ...], tuple[str, ...]], list[MixedInteraction]
    ] = {}
    for example in examples:
        parsed = parse_prompt(example.prompt)
        if parsed.arguments != example.trace.arguments or parsed.before != example.trace.before:
            raise ValueError("calibration trace does not match generic prompt extraction")
        buckets.setdefault(parsed.signature, []).append(example)

    rules: list[RoutingRule] = []
    evaluations = 0
    for signature, bucket_rows in sorted(buckets.items(), key=lambda row: repr(row[0])):
        remaining = list(bucket_rows)
        whole, cost = _fit_hypothesis(
            remaining, max_candidates=max_candidates_per_fit
        )
        evaluations += cost
        if whole is not None:
            rules.append(RoutingRule(signature, None, whole, len(remaining)))
            continue

        features = _candidate_features(remaining)
        while remaining:
            best: tuple[
                tuple[int, int, int, str],
                str,
                Hypothesis,
                list[MixedInteraction],
                int,
            ] | None = None
            for feature in features:
                covered = [
                    example
                    for example in remaining
                    if feature in lexical_features(example.prompt)
                ]
                if len(covered) < 2:
                    continue
                hypothesis, fit_cost = _fit_hypothesis(
                    covered, max_candidates=max_candidates_per_fit
                )
                evaluations += fit_cost
                if hypothesis is None or _hypothesis_accuracy(hypothesis, covered) != 1.0:
                    continue
                score = (
                    len(covered),
                    -hypothesis.description_bits,
                    -fit_cost,
                    feature,
                )
                if best is None or score > best[0]:
                    best = (score, feature, hypothesis, covered, fit_cost)
            if best is None:
                fallback, fit_cost = _fit_hypothesis(
                    remaining, max_candidates=max_candidates_per_fit
                )
                evaluations += fit_cost
                if fallback is None:
                    raise UnexpressibleTaskError(
                        f"mixed learner cannot separate signature {signature!r}"
                    )
                rules.append(RoutingRule(signature, None, fallback, len(remaining)))
                remaining.clear()
                break
            _, feature, hypothesis, covered, _ = best
            rules.append(RoutingRule(signature, feature, hypothesis, len(covered)))
            covered_ids = {id(example) for example in covered}
            remaining = [
                example for example in remaining if id(example) not in covered_ids
            ]

    model = MixedTaskModel(tuple(rules), evaluations, len(examples))
    if mixed_model_accuracy(model, examples) != 1.0:
        raise RuntimeError("induced mixed model does not reproduce calibration interactions")
    return model


def mixed_model_accuracy(
    model: MixedTaskModel, examples: Iterable[MixedInteraction]
) -> float:
    items = tuple(examples)
    if not items:
        raise ValueError("at least one example is required")
    correct = 0
    for example in items:
        prediction = model.predict(example.prompt)
        correct += int(
            prediction.output == example.trace.output
            and dict(prediction.after) == example.trace.after_dict()
        )
    return correct / len(items)
