from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
import json
from pathlib import Path
from typing import Mapping, Sequence

Q = Fraction
BASES = ("length", "time", "mass", "currency", "count")
Dimension = tuple[int, int, int, int, int]
ZERO_DIM: Dimension = (0, 0, 0, 0, 0)
LENGTH: Dimension = (1, 0, 0, 0, 0)
TIME: Dimension = (0, 1, 0, 0, 0)
MASS: Dimension = (0, 0, 1, 0, 0)
CURRENCY: Dimension = (0, 0, 0, 1, 0)
COUNT: Dimension = (0, 0, 0, 0, 1)


class NonIdentifiableProductError(ValueError):
    pass


def dim_add(left: Dimension, right: Dimension) -> Dimension:
    return tuple(a + b for a, b in zip(left, right))  # type: ignore[return-value]


def dim_sub(left: Dimension, right: Dimension) -> Dimension:
    return tuple(a - b for a, b in zip(left, right))  # type: ignore[return-value]


@dataclass(frozen=True)
class ProductConstraint:
    product: str
    factor_left: str
    factor_right: str
    provenance: str


@dataclass(frozen=True)
class ProductGraph:
    dimensions: tuple[tuple[str, Dimension], ...]
    constraints: tuple[ProductConstraint, ...]

    @staticmethod
    def build(dimensions: Mapping[str, Dimension], constraints: Sequence[ProductConstraint]) -> "ProductGraph":
        names = set(dimensions)
        rows = tuple(constraints)
        if not rows:
            raise ValueError("at least one multiplicative constraint is required")
        for row in rows:
            if len({row.product, row.factor_left, row.factor_right}) < 3:
                raise ValueError("constraint variables must be distinct")
            if {row.product, row.factor_left, row.factor_right} - names:
                raise ValueError("constraint references unknown variable")
            if dimensions[row.product] != dim_add(dimensions[row.factor_left], dimensions[row.factor_right]):
                raise NonIdentifiableProductError("dimension equation is inconsistent")
        return ProductGraph(tuple(sorted(dimensions.items())), rows)

    def dimension(self, variable: str) -> Dimension:
        return dict(self.dimensions)[variable]


@dataclass(frozen=True)
class ProductProofStep:
    variable: str
    equation_index: int
    operation: str
    value: Q


@dataclass(frozen=True)
class ProductSolution:
    values: tuple[tuple[str, Q], ...]
    steps: tuple[ProductProofStep, ...]


def solve(graph: ProductGraph, known: Mapping[str, int | Q], targets: Sequence[str]) -> ProductSolution:
    dimensions = dict(graph.dimensions)
    values = {name: Q(value) for name, value in known.items()}
    if set(values) - set(dimensions) or set(targets) - set(dimensions):
        raise ValueError("unknown variable")
    steps: list[ProductProofStep] = []
    progress = True
    while progress:
        progress = False
        for index, row in enumerate(graph.constraints):
            present = {
                row.product: row.product in values,
                row.factor_left: row.factor_left in values,
                row.factor_right: row.factor_right in values,
            }
            count = sum(present.values())
            if count == 3:
                if values[row.product] != values[row.factor_left] * values[row.factor_right]:
                    raise NonIdentifiableProductError("known values contradict a product equation")
                continue
            if count != 2:
                continue
            if not present[row.product]:
                value = values[row.factor_left] * values[row.factor_right]
                variable = row.product
                operation = "multiply"
            elif not present[row.factor_left]:
                divisor = values[row.factor_right]
                if divisor == 0:
                    raise NonIdentifiableProductError("division by zero cannot identify a factor")
                value = values[row.product] / divisor
                variable = row.factor_left
                operation = "divide-right"
            else:
                divisor = values[row.factor_left]
                if divisor == 0:
                    raise NonIdentifiableProductError("division by zero cannot identify a factor")
                value = values[row.product] / divisor
                variable = row.factor_right
                operation = "divide-left"
            if variable in values and values[variable] != value:
                raise NonIdentifiableProductError("derived values conflict")
            if variable not in values:
                values[variable] = value
                steps.append(ProductProofStep(variable, index, operation, value))
                progress = True
    if any(target not in values for target in targets):
        raise NonIdentifiableProductError("targets are not identifiable")
    ordered = tuple(sorted(values.items()))
    return ProductSolution(ordered, tuple(steps))


def verify(graph: ProductGraph, known: Mapping[str, int | Q], targets: Sequence[str], solution: ProductSolution) -> bool:
    try:
        rebuilt = solve(graph, known, targets)
    except (ValueError, NonIdentifiableProductError):
        return False
    return rebuilt == solution


@dataclass(frozen=True)
class RelationExample:
    relation: str
    slots: tuple[Q, Q, Q]


@dataclass(frozen=True)
class OrientationModel:
    product_slots: tuple[tuple[str, int], ...]

    @property
    def bits(self) -> int:
        return len(json.dumps(self.product_slots, ensure_ascii=False, separators=(",", ":")).encode()) * 8

    def product_slot(self, relation: str) -> int | None:
        return dict(self.product_slots).get(relation)


RELATIONS = ("速度関係", "濃度関係", "価格関係")


def calibration_examples() -> tuple[RelationExample, ...]:
    return (
        RelationExample("速度関係", (Q(120), Q(60), Q(2))),
        RelationExample("速度関係", (Q(45), Q(30), Q(3, 2))),
        RelationExample("濃度関係", (Q(1, 5), Q(250), Q(50))),
        RelationExample("濃度関係", (Q(3, 20), Q(400), Q(60))),
        RelationExample("価格関係", (Q(7), Q(840), Q(120))),
        RelationExample("価格関係", (Q(9), Q(2250), Q(250))),
    )


def orientation_hypotheses(examples: Sequence[RelationExample]) -> tuple[OrientationModel, ...]:
    survivors = []
    for assignment in product(range(3), repeat=len(RELATIONS)):
        mapping = dict(zip(RELATIONS, assignment))
        valid = True
        for row in examples:
            product_index = mapping[row.relation]
            factor_indexes = tuple(index for index in range(3) if index != product_index)
            if row.slots[product_index] != row.slots[factor_indexes[0]] * row.slots[factor_indexes[1]]:
                valid = False
                break
        if valid:
            survivors.append(OrientationModel(tuple(zip(RELATIONS, assignment))))
    return tuple(survivors)


def induce(examples: Sequence[RelationExample] | None = None) -> tuple[OrientationModel, dict[str, int]]:
    examples = tuple(calibration_examples() if examples is None else examples)
    survivors = orientation_hypotheses(examples)
    if len(survivors) != 1:
        raise NonIdentifiableProductError(f"orientation survivors={len(survivors)}")
    return survivors[0], {"hypotheses": 3 ** len(RELATIONS), "survivors": len(survivors), "examples": len(examples)}


@dataclass(frozen=True)
class StructuredCase:
    relation: str
    names: tuple[str, str, str]
    dimensions: tuple[Dimension, Dimension, Dimension]
    values: tuple[Q | None, Q | None, Q | None]
    expected: Q


def compile_case(model: OrientationModel, case: StructuredCase) -> tuple[ProductGraph, dict[str, Q], str]:
    product_index = model.product_slot(case.relation)
    if product_index is None:
        raise NonIdentifiableProductError("unknown relation")
    factor_indexes = tuple(index for index in range(3) if index != product_index)
    constraint = ProductConstraint(
        case.names[product_index],
        case.names[factor_indexes[0]],
        case.names[factor_indexes[1]],
        case.relation,
    )
    graph = ProductGraph.build(dict(zip(case.names, case.dimensions)), (constraint,))
    missing = [index for index, value in enumerate(case.values) if value is None]
    if len(missing) != 1:
        raise NonIdentifiableProductError("exactly one unknown is required in a single case")
    known = {case.names[index]: value for index, value in enumerate(case.values) if value is not None}
    return graph, known, case.names[missing[0]]


def heldout_cases() -> tuple[StructuredCase, ...]:
    speed_dim = dim_sub(LENGTH, TIME)
    concentration_dim = ZERO_DIM
    unit_price_dim = dim_sub(CURRENCY, COUNT)
    return (
        StructuredCase("速度関係", ("距離", "速さ", "時間"), (LENGTH, speed_dim, TIME), (None, Q(72), Q(5, 4)), Q(90)),
        StructuredCase("速度関係", ("距離", "速さ", "時間"), (LENGTH, speed_dim, TIME), (Q(150), None, Q(5, 2)), Q(60)),
        StructuredCase("速度関係", ("距離", "速さ", "時間"), (LENGTH, speed_dim, TIME), (Q(84), Q(56), None), Q(3, 2)),
        StructuredCase("速度関係", ("距離", "速さ", "時間"), (LENGTH, speed_dim, TIME), (None, Q(25, 2), Q(8, 5)), Q(20)),
        StructuredCase("濃度関係", ("濃度", "溶液", "溶質"), (concentration_dim, MASS, MASS), (None, Q(320), Q(48)), Q(3, 20)),
        StructuredCase("濃度関係", ("濃度", "溶液", "溶質"), (concentration_dim, MASS, MASS), (Q(1, 8), None, Q(45)), Q(360)),
        StructuredCase("濃度関係", ("濃度", "溶液", "溶質"), (concentration_dim, MASS, MASS), (Q(7, 50), Q(500), None), Q(70)),
        StructuredCase("濃度関係", ("濃度", "溶液", "溶質"), (concentration_dim, MASS, MASS), (None, Q(600), Q(90)), Q(3, 20)),
        StructuredCase("価格関係", ("個数", "代金", "単価"), (COUNT, CURRENCY, unit_price_dim), (None, Q(1560), Q(130)), Q(12)),
        StructuredCase("価格関係", ("個数", "代金", "単価"), (COUNT, CURRENCY, unit_price_dim), (Q(15), None, Q(80)), Q(1200)),
        StructuredCase("価格関係", ("個数", "代金", "単価"), (COUNT, CURRENCY, unit_price_dim), (Q(8), Q(1400), None), Q(175)),
        StructuredCase("価格関係", ("個数", "代金", "単価"), (COUNT, CURRENCY, unit_price_dim), (None, Q(825), Q(75)), Q(11)),
    )


def evaluate(model: OrientationModel) -> tuple[float, float, float]:
    correct = covered = verified_count = 0
    rows = heldout_cases()
    for case in rows:
        try:
            graph, known, target = compile_case(model, case)
            solution = solve(graph, known, (target,))
        except (ValueError, NonIdentifiableProductError):
            continue
        covered += 1
        correct += dict(solution.values)[target] == case.expected
        verified_count += verify(graph, known, (target,), solution)
    total = len(rows)
    return correct / total, covered / total, verified_count / total


def multistep_chain() -> tuple[Q, int, bool]:
    speed_dim = dim_sub(LENGTH, TIME)
    cost_rate_dim = dim_sub(CURRENCY, LENGTH)
    dimensions = {
        "速さ": speed_dim,
        "時間": TIME,
        "距離": LENGTH,
        "距離単価": cost_rate_dim,
        "総費用": CURRENCY,
    }
    constraints = (
        ProductConstraint("距離", "速さ", "時間", "distance=speed*time"),
        ProductConstraint("総費用", "距離", "距離単価", "cost=distance*rate"),
    )
    graph = ProductGraph.build(dimensions, constraints)
    known = {"速さ": Q(60), "時間": Q(3, 2), "距離単価": Q(8)}
    solution = solve(graph, known, ("総費用",))
    return dict(solution.values)["総費用"], len(solution.steps), verify(graph, known, ("総費用",), solution)


def constraint_order_invariant() -> bool:
    speed_dim = dim_sub(LENGTH, TIME)
    cost_rate_dim = dim_sub(CURRENCY, LENGTH)
    dimensions = {"速さ": speed_dim, "時間": TIME, "距離": LENGTH, "距離単価": cost_rate_dim, "総費用": CURRENCY}
    rows = (
        ProductConstraint("距離", "速さ", "時間", "a"),
        ProductConstraint("総費用", "距離", "距離単価", "b"),
    )
    known = {"速さ": Q(60), "時間": Q(3, 2), "距離単価": Q(8)}
    left = solve(ProductGraph.build(dimensions, rows), known, ("総費用",))
    right = solve(ProductGraph.build(dimensions, tuple(reversed(rows))), known, ("総費用",))
    return dict(left.values) == dict(right.values)


def ambiguous_orientation_rejected() -> bool:
    examples = tuple(RelationExample(relation, (Q(1), Q(1), Q(1))) for relation in RELATIONS)
    try:
        induce(examples)
    except NonIdentifiableProductError:
        return True
    return False


def impossible_orientation_rejected() -> bool:
    examples = calibration_examples() + (RelationExample("速度関係", (Q(2), Q(3), Q(5))),)
    try:
        induce(examples)
    except NonIdentifiableProductError:
        return True
    return False


def negative_controls() -> dict[str, bool]:
    controls: dict[str, bool] = {}
    try:
        ProductGraph.build(
            {"距離": LENGTH, "速さ": LENGTH, "時間": TIME},
            (ProductConstraint("距離", "速さ", "時間", "bad dimensions"),),
        )
    except NonIdentifiableProductError:
        controls["dimension_mismatch"] = True
    else:
        controls["dimension_mismatch"] = False

    graph = ProductGraph.build(
        {"積": ZERO_DIM, "左": ZERO_DIM, "右": ZERO_DIM},
        (ProductConstraint("積", "左", "右", "zero division"),),
    )
    for name, known, target in (
        ("two_unknowns", {"左": Q(2)}, "積"),
        ("zero_division", {"積": Q(0), "右": Q(0)}, "左"),
        ("contradictory_known", {"積": Q(7), "左": Q(2), "右": Q(3)}, "積"),
    ):
        try:
            solve(graph, known, (target,))
        except NonIdentifiableProductError:
            controls[name] = True
        else:
            controls[name] = False
    return controls


def tampered_proof_rejected(model: OrientationModel) -> bool:
    case = heldout_cases()[0]
    graph, known, target = compile_case(model, case)
    solution = solve(graph, known, (target,))
    step = solution.steps[0]
    tampered = ProductSolution(solution.values, (ProductProofStep(step.variable, step.equation_index, step.operation, step.value + 1),))
    return not verify(graph, known, (target,), tampered)


def run() -> dict[str, object]:
    model, fit = induce()
    accuracy, coverage, verified_rate = evaluate(model)
    chain_value, chain_steps, chain_verified = multistep_chain()
    controls = negative_controls()
    expected = {"速度関係": 0, "濃度関係": 2, "価格関係": 1}
    checks = {
        "unique_orientation_model": fit["survivors"] == 1,
        "correct_orientations": dict(model.product_slots) == expected,
        "heldout_accuracy": accuracy == 1.0,
        "heldout_coverage": coverage == 1.0,
        "proof_verification": verified_rate == 1.0,
        "multistep_chain": chain_value == Q(720) and chain_steps == 2 and chain_verified,
        "constraint_order_invariance": constraint_order_invariant(),
        "ambiguous_orientation_rejected": ambiguous_orientation_rejected(),
        "impossible_orientation_rejected": impossible_orientation_rejected(),
        "negative_controls": all(controls.values()),
        "tampered_proof_rejected": tampered_proof_rejected(model),
    }
    return {
        "campaign": {
            "name": "phase18c1-multiplicative-relation-core-c1",
            "domains": ["speed-distance-time", "concentration-solution-solute", "quantity-price-unit-price"],
            "raw_language_parser": False,
            "public_examples": 0,
        },
        "induction": {**fit, "product_slots": [list(item) for item in model.product_slots]},
        "evaluation": {
            "heldout_cases": len(heldout_cases()),
            "accuracy": accuracy,
            "coverage": coverage,
            "verified_proof_rate": verified_rate,
            "multistep_chain_value": str(chain_value),
            "multistep_chain_steps": chain_steps,
        },
        "negative_controls": controls,
        "resources": {
            "learned_orientation_bits": model.bits,
            "source_bytes": len(Path(__file__).read_bytes()),
            "python_runtime_included": False,
        },
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {
            "exact_dimension_checked_multiplicative_reasoning": all(checks.values()),
            "new_math_family_beyond_linear_constraints": all(checks.values()),
            "general_nonlinear_solver": False,
            "raw_japanese_word_problem_understanding": False,
            "high_school_intelligence": False,
        },
        "limitations": [
            "Inputs are structured triples; raw-language compilation is not included.",
            "Each product equation is monomial and propagation requires exactly one unknown at a time.",
            "No polynomial systems, inequalities over products, uncertainty, or unit conversion.",
            "Dimensions are supplied rather than inferred from natural-language units.",
        ],
    }


def markdown(payload: Mapping[str, object]) -> str:
    induction = payload["induction"]
    evaluation = payload["evaluation"]
    resources = payload["resources"]
    return f"""# Phase 18c-1 results: multiplicative relation core

- Orientation hypotheses / survivors: **{induction['hypotheses']} / {induction['survivors']}**
- Calibration examples: **{induction['examples']}**
- Held-out cases: **{evaluation['heldout_cases']}**
- Accuracy / coverage / verified proof: **{100 * evaluation['accuracy']:.1f}% / {100 * evaluation['coverage']:.1f}% / {100 * evaluation['verified_proof_rate']:.1f}%**
- Two-step chain result / proof steps: **{evaluation['multistep_chain_value']} / {evaluation['multistep_chain_steps']}**
- Learned orientation payload: **{resources['learned_orientation_bits']} bits**

The same exact, dimension-checked product graph solves speed, concentration, and unit-price relations with any one of the three quantities unknown, and propagates through a two-equation chain. This is a new controlled mathematical family, not a general nonlinear solver or raw Japanese understanding.
"""


def main() -> None:
    payload = run()
    Path("results").mkdir(exist_ok=True)
    Path("results/phase18c1.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    Path("results/phase18c1.md").write_text(markdown(payload), encoding="utf-8")
    print(markdown(payload), end="")
    if not payload["all_theorem_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
