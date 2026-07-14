from __future__ import annotations

import argparse
import json
import math
import re
import runpy
import time
import tracemalloc
from collections import Counter, defaultdict
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Iterable, Sequence

NUMBER_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def extract_numbers(text: str) -> tuple[Fraction, ...]:
    return tuple(Fraction(match.group().replace(",", "")) for match in NUMBER_RE.finditer(text))


def normalize_question(text: str) -> str:
    return NUMBER_RE.sub("<N>", text)


def character_features(text: str) -> frozenset[str]:
    normalized = normalize_question(text)
    features: set[str] = {f"COUNT={len(extract_numbers(text))}"}
    for width in range(2, 6):
        features.update(
            f"C{width}:{normalized[index:index + width]}"
            for index in range(max(0, len(normalized) - width + 1))
        )
    for marker in ("%", "パーセント", "半分", "倍", "残", "合計", "全部", "それぞれ", "毎", "差", "利益", "平均"):
        if marker in normalized:
            features.add("M:" + marker)
    return frozenset(features)


@dataclass(frozen=True)
class Expression:
    op: str
    left: "Expression | None" = None
    right: "Expression | None" = None
    index: int | None = None
    constant: int | None = None

    @classmethod
    def number(cls, index: int) -> "Expression":
        return cls("number", index=index)

    @classmethod
    def const(cls, value: int) -> "Expression":
        return cls("const", constant=value)

    @property
    def key(self) -> str:
        if self.op == "number":
            return f"n{self.index}"
        if self.op == "const":
            return f"c{self.constant}"
        assert self.left is not None and self.right is not None
        return f"({self.op} {self.left.key} {self.right.key})"

    @property
    def cost(self) -> int:
        if self.op == "number":
            return 1
        if self.op == "const":
            return 3
        assert self.left is not None and self.right is not None
        return 1 + self.left.cost + self.right.cost

    def evaluate(self, numbers: Sequence[Fraction]) -> Fraction | None:
        if self.op == "number":
            assert self.index is not None
            return numbers[self.index] if self.index < len(numbers) else None
        if self.op == "const":
            assert self.constant is not None
            return Fraction(self.constant)
        assert self.left is not None and self.right is not None
        left = self.left.evaluate(numbers)
        right = self.right.evaluate(numbers)
        if left is None or right is None:
            return None
        if self.op == "+":
            return left + right
        if self.op == "-":
            return left - right
        if self.op == "*":
            return left * right
        if self.op == "/":
            return None if right == 0 else left / right
        raise ValueError(self.op)


def parse_expression(text: str) -> Expression:
    tokens = re.findall(r"\(|\)|[^\s()]+", text)
    position = 0

    def parse() -> Expression:
        nonlocal position
        token = tokens[position]
        position += 1
        if token.startswith("n") and token[1:].isdigit():
            return Expression.number(int(token[1:]))
        if token.startswith("c") and token[1:].lstrip("-").isdigit():
            return Expression.const(int(token[1:]))
        if token != "(":
            raise ValueError(f"invalid expression token: {token}")
        op = tokens[position]
        position += 1
        left = parse()
        right = parse()
        if tokens[position] != ")":
            raise ValueError("missing closing parenthesis")
        position += 1
        return Expression(op, left, right)

    result = parse()
    if position != len(tokens):
        raise ValueError("trailing expression tokens")
    return result


def cue_constants(question: str) -> tuple[int, ...]:
    constants: list[int] = []
    if "%" in question or "パーセント" in question:
        constants.append(100)
    if "半分" in question or "半額" in question:
        constants.append(2)
    if "ダース" in question:
        constants.append(12)
    if "1週間" in question and "7" not in question:
        constants.append(7)
    if "1時間" in question and "60" not in question:
        constants.append(60)
    return tuple(constants)


@dataclass(frozen=True)
class SynthesisResult:
    expressions: tuple[Expression, ...]
    expansions: int


def synthesize_expressions(
    question: str,
    answer: int,
    *,
    max_terms: int = 4,
    max_values_per_mask: int = 1200,
    max_solutions: int = 12,
) -> SynthesisResult:
    numbers = extract_numbers(question)
    if not numbers:
        return SynthesisResult((), 0)
    numbers = numbers[:7]
    atoms: list[tuple[Fraction, Expression]] = [
        (value, Expression.number(index))
        for index, value in enumerate(numbers)
    ]
    atoms.extend((Fraction(value), Expression.const(value)) for value in cue_constants(question))
    atom_count = len(atoms)
    if atom_count > 9:
        atoms = atoms[:9]
        atom_count = len(atoms)

    target = Fraction(answer)
    bound = max(1000, abs(answer) * 20, int(max(abs(value) for value, _ in atoms)) * 200)
    tables: dict[int, dict[Fraction, Expression]] = {}
    for index, (value, expression) in enumerate(atoms):
        tables[1 << index] = {value: expression}

    expansions = 0
    for size in range(2, min(max_terms, atom_count) + 1):
        masks = [mask for mask in range(1, 1 << atom_count) if mask.bit_count() == size]
        for mask in masks:
            values: dict[Fraction, Expression] = {}
            submask = (mask - 1) & mask
            while submask:
                other = mask ^ submask
                if other and submask < other and submask in tables and other in tables:
                    for left_value, left_expr in tables[submask].items():
                        for right_value, right_expr in tables[other].items():
                            candidates: list[tuple[str, Fraction, Expression, Expression]] = [
                                ("+", left_value + right_value, left_expr, right_expr),
                                ("*", left_value * right_value, left_expr, right_expr),
                                ("-", left_value - right_value, left_expr, right_expr),
                                ("-", right_value - left_value, right_expr, left_expr),
                            ]
                            if right_value != 0:
                                candidates.append(("/", left_value / right_value, left_expr, right_expr))
                            if left_value != 0:
                                candidates.append(("/", right_value / left_value, right_expr, left_expr))
                            expansions += len(candidates)
                            for op, value, first, second in candidates:
                                if abs(value) > bound or value.denominator > 1000:
                                    continue
                                if op in {"+", "*"} and first.key > second.key:
                                    first, second = second, first
                                expression = Expression(op, first, second)
                                existing = values.get(value)
                                if existing is None or (expression.cost, expression.key) < (existing.cost, existing.key):
                                    values[value] = expression
                submask = (submask - 1) & mask
            if len(values) > max_values_per_mask:
                ranked = sorted(
                    values.items(),
                    key=lambda item: (
                        abs(float(item[0] - target)),
                        item[1].cost,
                        item[1].key,
                    ),
                )[:max_values_per_mask]
                values = dict(ranked)
            if values:
                tables[mask] = values

    solutions: dict[str, Expression] = {}
    input_mask = (1 << len(numbers)) - 1
    for mask, values in tables.items():
        if not mask & input_mask:
            continue
        expression = values.get(target)
        if expression is not None:
            solutions[expression.key] = expression
    ranked_solutions = sorted(solutions.values(), key=lambda row: (row.cost, row.key))[:max_solutions]
    return SynthesisResult(tuple(ranked_solutions), expansions)


@dataclass(frozen=True)
class MathRow:
    question: str
    answer: int


def load_mgsm_tsv(path: str | Path) -> list[MathRow]:
    rows: list[MathRow] = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        question, answer = line.rsplit("\t", 1)
        try:
            rows.append(MathRow(question, int(answer.replace(",", ""))))
        except ValueError as error:
            raise ValueError(f"invalid answer on line {line_number}") from error
    return rows


def load_japanese_exemplars(path: str | Path) -> list[MathRow]:
    module = runpy.run_path(str(path))
    examples = module["MGSM_EXEMPLARS"]["ja"]
    answers = module["EXEMPLAR_NUMBER_ANSWERS"]
    return [
        MathRow(examples[str(index + 1)]["q"], int(answer))
        for index, answer in enumerate(answers)
    ]


@dataclass
class ProgramSelector:
    programs: dict[str, Expression]
    document_counts: Counter[str]
    feature_counts: dict[str, Counter[str]]
    global_features: Counter[str]
    training_documents: int
    synthesis_expansions: int
    solved_training_rows: int

    @classmethod
    def fit(cls, rows: Sequence[MathRow]) -> "ProgramSelector":
        candidate_rows: list[tuple[MathRow, tuple[Expression, ...], frozenset[str]]] = []
        support: Counter[str] = Counter()
        expansions = 0
        for row in rows:
            synthesis = synthesize_expressions(row.question, row.answer)
            expansions += synthesis.expansions
            if not synthesis.expressions:
                continue
            features = character_features(row.question)
            candidate_rows.append((row, synthesis.expressions, features))
            for rank, expression in enumerate(synthesis.expressions):
                support[expression.key] += 1.0 / (rank + 1)

        programs: dict[str, Expression] = {}
        document_counts: Counter[str] = Counter()
        feature_counts: dict[str, Counter[str]] = defaultdict(Counter)
        global_features: Counter[str] = Counter()
        for _row, candidates, features in candidate_rows:
            chosen = min(
                candidates,
                key=lambda expression: (
                    expression.cost - 1.5 * math.log2(1.0 + support[expression.key]),
                    expression.key,
                ),
            )
            key = chosen.key
            programs[key] = chosen
            document_counts[key] += 1
            feature_counts[key].update(features)
            global_features.update(features)

        return cls(
            programs=programs,
            document_counts=document_counts,
            feature_counts=dict(feature_counts),
            global_features=global_features,
            training_documents=len(candidate_rows),
            synthesis_expansions=expansions,
            solved_training_rows=len(candidate_rows),
        )

    def rank(self, question: str) -> list[tuple[float, Expression]]:
        features = character_features(question)
        numbers = extract_numbers(question)
        total = max(1, self.training_documents)
        scored: list[tuple[float, Expression]] = []
        for key, expression in self.programs.items():
            count = self.document_counts[key]
            score = math.log(count + 0.25)
            local = self.feature_counts[key]
            for feature in features:
                observed = local.get(feature, 0)
                if not observed:
                    continue
                global_count = self.global_features[feature]
                idf = math.log((total + 1.0) / (global_count + 1.0)) + 1.0
                score += idf * math.log1p(4.0 * observed / count)
            value = expression.evaluate(numbers)
            if value is None:
                continue
            scored.append((score, expression))
        return sorted(scored, key=lambda item: (-item[0], item[1].cost, item[1].key))

    def predict(self, question: str, *, max_attempts: int = 64) -> tuple[int | None, int]:
        numbers = extract_numbers(question)
        attempts = 0
        for _score, expression in self.rank(question)[:max_attempts]:
            attempts += 1
            value = expression.evaluate(numbers)
            if value is None or value.denominator != 1:
                continue
            integer = int(value)
            if abs(integer) > 10**12:
                continue
            return integer, attempts
        return None, attempts

    def serialized_bytes(self) -> int:
        payload = {
            "programs": sorted(self.programs),
            "document_counts": dict(self.document_counts),
            "feature_counts": {
                key: dict(values)
                for key, values in self.feature_counts.items()
            },
        }
        return len(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8"))


@dataclass(frozen=True)
class Evaluation:
    accuracy: float
    correct: int
    total: int
    answered: int
    mean_attempts: float
    elapsed_seconds: float


def evaluate(model: ProgramSelector, rows: Sequence[MathRow]) -> Evaluation:
    correct = 0
    answered = 0
    attempts = 0
    start = time.perf_counter()
    for row in rows:
        prediction, used = model.predict(row.question)
        attempts += used
        if prediction is not None:
            answered += 1
        if prediction == row.answer:
            correct += 1
    elapsed = time.perf_counter() - start
    total = len(rows)
    return Evaluation(
        accuracy=correct / total if total else 0.0,
        correct=correct,
        total=total,
        answered=answered,
        mean_attempts=attempts / total if total else 0.0,
        elapsed_seconds=elapsed,
    )


def _evaluation_dict(row: Evaluation) -> dict[str, float | int]:
    return {
        "accuracy": row.accuracy,
        "correct": row.correct,
        "total": row.total,
        "answered": row.answered,
        "mean_program_attempts": row.mean_attempts,
        "elapsed_seconds": row.elapsed_seconds,
        "questions_per_second": row.total / row.elapsed_seconds if row.elapsed_seconds else 0.0,
    }


def run_public_experiment(
    dataset_path: str | Path,
    exemplars_path: str | Path,
    *,
    adaptation_train: int = 200,
) -> dict[str, object]:
    rows = load_mgsm_tsv(dataset_path)
    exemplars = load_japanese_exemplars(exemplars_path)
    if len(rows) != 250:
        raise ValueError(f"expected 250 MGSM rows, found {len(rows)}")
    if not 1 <= adaptation_train < len(rows):
        raise ValueError("adaptation_train must leave a non-empty holdout")

    tracemalloc.start()
    official_model = ProgramSelector.fit(exemplars)
    official_eval = evaluate(official_model, rows)
    official_peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.reset_peak()

    train_rows = rows[:adaptation_train]
    holdout_rows = rows[adaptation_train:]
    adaptation_model = ProgramSelector.fit(train_rows)
    adaptation_eval = evaluate(adaptation_model, holdout_rows)
    adaptation_peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()

    result: dict[str, object] = {
        "capability_id": "FEMI-002-MGSM",
        "dataset": {
            "name": "MGSM Japanese",
            "public_rows": len(rows),
            "official_exemplars": len(exemplars),
            "adaptation_train_rows": len(train_rows),
            "adaptation_holdout_rows": len(holdout_rows),
            "holdout_is_official_zero_shot_score": False,
        },
        "official_eight_shot": {
            **_evaluation_dict(official_eval),
            "program_count": len(official_model.programs),
            "model_bytes": official_model.serialized_bytes(),
            "training_synthesis_expansions": official_model.synthesis_expansions,
            "solved_training_rows": official_model.solved_training_rows,
            "peak_python_bytes": official_peak,
        },
        "public_adaptation_holdout": {
            **_evaluation_dict(adaptation_eval),
            "program_count": len(adaptation_model.programs),
            "model_bytes": adaptation_model.serialized_bytes(),
            "training_synthesis_expansions": adaptation_model.synthesis_expansions,
            "solved_training_rows": adaptation_model.solved_training_rows,
            "peak_python_bytes": adaptation_peak,
            "exact_memorization_baseline_accuracy": 0.0,
        },
        "neural_network_used": False,
        "gradient_training_used": False,
        "claim_boundary": (
            "This is a public Japanese grade-school arithmetic evaluation of a non-neural "
            "program-induction learner. The 200/50 result is a public-corpus adaptation split, "
            "not the official MGSM zero-shot score. It is not Japanese high-school-level "
            "intelligence, not general dialogue competence, and not yet an LLM comparison."
        ),
    }
    result["passed"] = bool(
        adaptation_eval.accuracy >= 0.10
        and adaptation_eval.accuracy > 0.0
        and adaptation_model.solved_training_rows >= 80
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="FEMI public MGSM evaluation")
    parser.add_argument("dataset_tsv")
    parser.add_argument("exemplars_py")
    parser.add_argument("--adaptation-train", type=int, default=200)
    args = parser.parse_args()
    result = run_public_experiment(
        args.dataset_tsv,
        args.exemplars_py,
        adaptation_train=args.adaptation_train,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
