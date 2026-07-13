from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import permutations
import json
from pathlib import Path
import re
import unicodedata
from typing import Mapping, Sequence

RELATIONS = ("以上", "以下", "より大きい", "より小さい")
OPS = ("GE", "LE", "GT", "LT")
TRUE_MAP = {"以上": "GE", "以下": "LE", "より大きい": "GT", "より小さい": "LT"}
REVERSE = {"GE": "LE", "LE": "GE", "GT": "LT", "LT": "GT"}

class NonIdentifiableInequalityError(ValueError):
    pass

@dataclass(frozen=True)
class Constraint:
    a: Fraction
    b: Fraction
    op: str
    c: Fraction

@dataclass(frozen=True)
class BoundStep:
    original: Constraint
    threshold: Fraction | None
    normalized_op: str | None
    always: bool = False
    impossible: bool = False

@dataclass(frozen=True)
class Interval:
    lower: Fraction | None = None
    lower_closed: bool = False
    upper: Fraction | None = None
    upper_closed: bool = False
    empty: bool = False

@dataclass(frozen=True)
class Solution:
    interval: Interval
    steps: tuple[BoundStep, ...]

@dataclass(frozen=True)
class InequalityModel:
    relation_map: tuple[tuple[str, str], ...]

    @property
    def bits(self) -> int:
        return len(json.dumps({"relations": self.relation_map}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()) * 8

    def parse(self, text: str) -> tuple[Constraint, ...]:
        return parse_problem(text, dict(self.relation_map))

    def solve(self, text: str) -> Solution | None:
        try:
            constraints = self.parse(text)
            solution = solve_constraints(constraints)
            return solution if verify_solution(constraints, solution) else None
        except ValueError:
            return None

def norm(text: str) -> str:
    return "".join(unicodedata.normalize("NFKC", text).split())

def num(token: str) -> Fraction:
    if "/" in token:
        a, b = token.split("/", 1)
        return Fraction(int(a), int(b))
    return Fraction(int(token))

ROW_RE = re.compile(
    r"アキを(?P<a>-?\d+(?:/\d+)?)倍して"
    r"(?P<b>\d+(?:/\d+)?)(?P<shift>増やした|減らした)数は"
    r"(?P<c>-?\d+(?:/\d+)?)(?P<rel>以上|以下|より大きい|より小さい)"
)

def parse_constraint(text: str, mapping: Mapping[str, str]) -> Constraint:
    m = ROW_RE.fullmatch(norm(text).rstrip("。"))
    if not m:
        raise ValueError("unsupported inequality sentence")
    b = num(m.group("b"))
    if m.group("shift") == "減らした":
        b = -b
    op = mapping.get(m.group("rel"))
    if op is None:
        raise ValueError("unknown relation")
    return Constraint(num(m.group("a")), b, op, num(m.group("c")))

def parse_problem(text: str, mapping: Mapping[str, str]) -> tuple[Constraint, ...]:
    clean = norm(text)
    if "条件:" not in clean or "質問:" not in clean:
        raise ValueError("missing sections")
    body, query = clean.split("質問:", 1)
    if "アキの範囲" not in query:
        raise ValueError("range query required")
    parts = [p for p in body.split("条件:", 1)[1].split("。") if p]
    if not 1 <= len(parts) <= 4:
        raise ValueError("one to four constraints required")
    return tuple(parse_constraint(p, mapping) for p in parts)

def compare(value: Fraction, op: str, target: Fraction) -> bool:
    return {"GE": value >= target, "LE": value <= target, "GT": value > target, "LT": value < target}[op]

def normalize_constraint(c: Constraint) -> BoundStep:
    if c.a == 0:
        ok = compare(c.b, c.op, c.c)
        return BoundStep(c, None, None, always=ok, impossible=not ok)
    q = (c.c - c.b) / c.a
    op = c.op if c.a > 0 else REVERSE[c.op]
    return BoundStep(c, q, op)

def intersect(interval: Interval, step: BoundStep) -> Interval:
    if interval.empty or step.impossible:
        return Interval(empty=True)
    if step.always:
        return interval
    assert step.threshold is not None and step.normalized_op is not None
    q, op = step.threshold, step.normalized_op
    lo, lc, hi, hc = interval.lower, interval.lower_closed, interval.upper, interval.upper_closed
    if op in ("GE", "GT"):
        closed = op == "GE"
        if lo is None or q > lo:
            lo, lc = q, closed
        elif q == lo:
            lc = lc and closed
    else:
        closed = op == "LE"
        if hi is None or q < hi:
            hi, hc = q, closed
        elif q == hi:
            hc = hc and closed
    if lo is not None and hi is not None:
        if lo > hi or (lo == hi and not (lc and hc)):
            return Interval(empty=True)
    return Interval(lo, lc, hi, hc, False)

def solve_constraints(constraints: Sequence[Constraint]) -> Solution:
    steps = tuple(normalize_constraint(c) for c in constraints)
    interval = Interval()
    for step in steps:
        interval = intersect(interval, step)
    return Solution(interval, steps)

def verify_solution(constraints: Sequence[Constraint], solution: Solution) -> bool:
    expected_steps = tuple(normalize_constraint(c) for c in constraints)
    if solution.steps != expected_steps:
        return False
    interval = Interval()
    for step in expected_steps:
        interval = intersect(interval, step)
    return solution.interval == interval

def fmt(x: Fraction) -> str:
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"

def render_constraint(a: Fraction, b: Fraction, op_word: str, c: Fraction) -> str:
    shift = f"{fmt(abs(b))}{'増やした' if b >= 0 else '減らした'}"
    return f"アキを{fmt(a)}倍して{shift}数は{fmt(c)}{op_word}"

def make_problem(specs: Sequence[tuple[Fraction, Fraction, str, Fraction]]) -> str:
    return "条件:" + "。".join(render_constraint(*s) for s in specs) + "。質問:アキの範囲を求めよ。"

CALIBRATION = (
    ("以上", (Fraction(2), Fraction(1), Fraction(7)), Interval(lower=Fraction(3), lower_closed=True)),
    ("以下", (Fraction(3), Fraction(-2), Fraction(10)), Interval(upper=Fraction(4), upper_closed=True)),
    ("より大きい", (Fraction(4), Fraction(0), Fraction(8)), Interval(lower=Fraction(2), lower_closed=False)),
    ("より小さい", (Fraction(5), Fraction(5), Fraction(0)), Interval(upper=Fraction(-1), upper_closed=False)),
)

def calibration_error(mapping: Mapping[str, str]) -> int:
    errors = 0
    for word, (a, b, c), expected in CALIBRATION:
        constraint = Constraint(a, b, mapping[word], c)
        errors += solve_constraints((constraint,)).interval != expected
    return errors

def induce_model() -> tuple[InequalityModel, dict[str, int]]:
    scored = []
    for values in permutations(OPS):
        mapping = dict(zip(RELATIONS, values))
        scored.append((calibration_error(mapping), mapping))
    best_error = min(e for e, _ in scored)
    best = [m for e, m in scored if e == best_error]
    if len(best) != 1:
        raise NonIdentifiableInequalityError(f"optima={len(best)}")
    second = min(e for e, _ in scored if e > best_error)
    return InequalityModel(tuple(sorted(best[0].items()))), {"candidates": len(scored), "errors": best_error, "second": second}

HELDOUT = (
    ((Fraction(-4), Fraction(2), "以下", Fraction(4)), (Fraction(3), Fraction(1), "以下", Fraction(8))),
    ((Fraction(2), Fraction(0), "より大きい", Fraction(-4)), (Fraction(-4), Fraction(1), "より大きい", Fraction(-4))),
    ((Fraction(-3), Fraction(6), "以上", Fraction(0)),),
    ((Fraction(2), Fraction(0), "以上", Fraction(6)), (Fraction(-5), Fraction(0), "以上", Fraction(-15))),
    ((Fraction(1), Fraction(0), "より大きい", Fraction(2)), (Fraction(1), Fraction(0), "以下", Fraction(2))),
    ((Fraction(0), Fraction(5), "以上", Fraction(5)), (Fraction(7), Fraction(-1), "より大きい", Fraction(6))),
)

def heldout() -> tuple[tuple[str, Interval], ...]:
    rows = []
    for specs in HELDOUT:
        text = make_problem(specs)
        constraints = tuple(Constraint(a, b, TRUE_MAP[w], c) for a, b, w, c in specs)
        expected = solve_constraints(constraints).interval
        rows.append((text, expected))
        rows.append((text.replace("条件:", "条件: ").replace("。質問", "。 質問"), expected))
    return tuple(rows)

def evaluate(model: InequalityModel) -> tuple[float, float, float]:
    correct = answered = verified = 0
    for text, expected in heldout():
        solution = model.solve(text)
        if solution is None:
            continue
        answered += 1
        correct += solution.interval == expected
        verified += verify_solution(model.parse(text), solution)
    n = len(heldout())
    return correct / n, answered / n, verified / n

def boundary_free_calibration_is_nonidentifying() -> bool:
    witnesses = (Fraction(-2), Fraction(2))
    ge = tuple(compare(x, "GE", 0) for x in witnesses)
    gt = tuple(compare(x, "GT", 0) for x in witnesses)
    le = tuple(compare(x, "LE", 0) for x in witnesses)
    lt = tuple(compare(x, "LT", 0) for x in witnesses)
    return ge == gt and le == lt

def tampered_interval_is_rejected(model: InequalityModel) -> bool:
    text, _ = heldout()[0]
    constraints = model.parse(text)
    solution = solve_constraints(constraints)
    assert solution.interval.lower is not None
    bad = Solution(Interval(solution.interval.lower + 1, solution.interval.lower_closed, solution.interval.upper, solution.interval.upper_closed), solution.steps)
    return not verify_solution(constraints, bad)

def unknown_relation_abstains(model: InequalityModel) -> bool:
    text = "条件:アキを2倍して1増やした数は7未満。質問:アキの範囲を求めよ。"
    return model.solve(text) is None

def run() -> dict[str, object]:
    model, fit = induce_model()
    accuracy, coverage, verified = evaluate(model)
    intervals = [expected for _, expected in heldout()]
    checks = {
        "four_relation_semantics_are_unique": dict(model.relation_map) == TRUE_MAP,
        "positive_identifiability_margin": fit["second"] > fit["errors"],
        "heldout_intervals_are_exact": accuracy == coverage == verified == 1.0,
        "negative_coefficients_reverse_order": any(s.normalized_op != s.original.op for text, _ in heldout() for s in model.solve(text).steps if s.threshold is not None and s.original.a < 0),
        "open_closed_empty_and_point_intervals_present": any(i.empty for i in intervals) and any(i.lower == i.upper and not i.empty for i in intervals) and any((i.lower is not None and not i.lower_closed) or (i.upper is not None and not i.upper_closed) for i in intervals),
        "boundary_free_calibration_is_nonidentifying": boundary_free_calibration_is_nonidentifying(),
        "tampered_interval_is_rejected": tampered_interval_is_rejected(model),
        "unknown_relation_abstains": unknown_relation_abstains(model),
    }
    return {
        "campaign": {"name": "phase18b5-affine-inequality-intervals-c1", "relation_names_preassigned": False, "domain": "exact rationals", "public_examples": 0},
        "induction": {**fit, "relation_map": [list(x) for x in model.relation_map]},
        "evaluation": {"calibration_relations": len(CALIBRATION), "heldout_problems": len(heldout()), "accuracy": accuracy, "coverage": coverage, "verified_trace_rate": verified},
        "resources": {"model_bits": model.bits, "source_bytes": Path(__file__).read_bytes().__len__(), "python_runtime_included": False},
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {"controlled_affine_inequalities": all(checks.values()), "ordinary_word_problems": False, "high_school_mathematics": False},
        "limitations": ["one explicit unknown", "controlled affine syntax", "no absolute values, quadratic inequalities, or integer-domain reasoning", "relation calibration supplies expected intervals", "Python substrate excluded"],
    }

def markdown(p: Mapping[str, object]) -> str:
    i, e, r = p["induction"], p["evaluation"], p["resources"]
    return f'''# Phase 18b-5 results: affine inequalities and interval reasoning

- Relation candidates: **{i["candidates"]}**
- Best / second calibration errors: **{i["errors"]} / {i["second"]}**
- Induced relation map: **{i["relation_map"]}**
- Held-out problems: **{e["heldout_problems"]}**
- Accuracy / coverage / verified proofs: **{100*e["accuracy"]:.1f}% / {100*e["coverage"]:.1f}% / {100*e["verified_trace_rate"]:.1f}%**
- Learned payload: **{r["model_bits"]} bits**

This is exact affine-inequality and interval reasoning in a controlled Japanese language, not general high-school mathematics.
'''

def main() -> None:
    p = run()
    Path("results").mkdir(exist_ok=True)
    Path("results/phase18b5.json").write_text(json.dumps(p, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    Path("results/phase18b5.md").write_text(markdown(p), encoding="utf-8")
    print(markdown(p), end="")

if __name__ == "__main__":
    main()
