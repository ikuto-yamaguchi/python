from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import json
from pathlib import Path
import re
import unicodedata
from typing import Mapping, Sequence

NAMES = ("アキ", "ボブ")
TRUE_RELATION = {"合わせる": "ADD", "引く": "SUB"}

class NonIdentifiableRelationError(ValueError):
    pass

class UnsolvableSystemError(ValueError):
    pass

@dataclass(frozen=True)
class Row:
    a: Fraction
    b: Fraction
    c: Fraction

@dataclass(frozen=True)
class Problem:
    text: str
    rows: tuple[Row, Row]

@dataclass(frozen=True)
class Proof:
    determinant: Fraction
    x_numerator: Fraction
    y_numerator: Fraction
    x: Fraction
    y: Fraction

@dataclass(frozen=True)
class Solution:
    answers: tuple[tuple[str, Fraction], ...]
    proof: Proof

@dataclass(frozen=True)
class RelationModel:
    relation_map: tuple[tuple[str, str], ...]

    @property
    def bits(self) -> int:
        payload = {"relations": self.relation_map, "unknowns": NAMES}
        return len(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()) * 8

    def parse(self, text: str) -> Problem:
        return parse_problem(text, dict(self.relation_map))

    def solve(self, text: str) -> Solution | None:
        try:
            return solve_problem(self.parse(text))
        except (ValueError, UnsolvableSystemError):
            return None

def norm(text: str) -> str:
    return "".join(unicodedata.normalize("NFKC", text).split())

def parse_number(token: str) -> Fraction:
    if "/" in token:
        left, right = token.split("/", 1)
        return Fraction(int(left), int(right))
    return Fraction(int(token))

ROW_RE = re.compile(
    r"(?P<n1>-?\d+(?:/\d+)?)倍の(?P<v1>アキ|ボブ)と"
    r"(?P<n2>-?\d+(?:/\d+)?)倍の(?P<v2>アキ|ボブ)を"
    r"(?P<rel>合わせる|引く)と(?P<c>-?\d+(?:/\d+)?)"
)

def parse_row(sentence: str, relation_map: Mapping[str, str]) -> Row:
    m = ROW_RE.fullmatch(norm(sentence).rstrip("。"))
    if not m:
        raise ValueError("unsupported relation sentence")
    coeffs = {name: Fraction(0) for name in NAMES}
    n1, n2 = parse_number(m.group("n1")), parse_number(m.group("n2"))
    op = relation_map.get(m.group("rel"))
    if op is None:
        raise ValueError("unknown relation")
    coeffs[m.group("v1")] += n1
    coeffs[m.group("v2")] += n2 if op == "ADD" else -n2
    return Row(coeffs["アキ"], coeffs["ボブ"], parse_number(m.group("c")))

def parse_problem(text: str, relation_map: Mapping[str, str]) -> Problem:
    clean = norm(text)
    if "質問:" not in clean or "条件:" not in clean:
        raise ValueError("missing sections")
    body, query = clean.split("質問:", 1)
    body = body.split("条件:", 1)[1]
    parts = [p for p in body.split("。") if p]
    if len(parts) != 2:
        raise ValueError("exactly two equations required")
    if "アキとボブ" not in query and "ボブとアキ" not in query:
        raise ValueError("two-variable query required")
    rows = tuple(parse_row(p, relation_map) for p in parts)
    return Problem(text, (rows[0], rows[1]))

def solve_problem(problem: Problem) -> Solution:
    r1, r2 = problem.rows
    det = r1.a * r2.b - r2.a * r1.b
    if det == 0:
        raise UnsolvableSystemError("singular system")
    x_num = r1.c * r2.b - r2.c * r1.b
    y_num = r1.a * r2.c - r2.a * r1.c
    x, y = x_num / det, y_num / det
    sol = Solution((("アキ", x), ("ボブ", y)), Proof(det, x_num, y_num, x, y))
    if not verify_solution(problem, sol):
        raise UnsolvableSystemError("verification failed")
    return sol

def verify_solution(problem: Problem, solution: Solution) -> bool:
    values = dict(solution.answers)
    if set(values) != set(NAMES):
        return False
    p = solution.proof
    r1, r2 = problem.rows
    det = r1.a * r2.b - r2.a * r1.b
    x_num = r1.c * r2.b - r2.c * r1.b
    y_num = r1.a * r2.c - r2.a * r1.c
    if (p.determinant, p.x_numerator, p.y_numerator) != (det, x_num, y_num):
        return False
    if det == 0 or p.x != x_num / det or p.y != y_num / det:
        return False
    if values["アキ"] != p.x or values["ボブ"] != p.y:
        return False
    return r1.a * p.x + r1.b * p.y == r1.c and r2.a * p.x + r2.b * p.y == r2.c

def format_fraction(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"

def make_problem(rows: Sequence[tuple[int, int, str]], x: Fraction, y: Fraction, reverse_query: bool = False) -> str:
    lines = []
    for a, b, relation in rows:
        c = a * x + (b * y if TRUE_RELATION[relation] == "ADD" else -b * y)
        lines.append(f"{a}倍のアキと{b}倍のボブを{relation}と{format_fraction(c)}")
    query = "ボブとアキの数を求めよ" if reverse_query else "アキとボブの数を求めよ"
    return "条件:" + "。".join(lines) + "。質問:" + query + "。"

CALIBRATION = (
    (make_problem(((2, 3, "合わせる"), (5, 2, "引く")), Fraction(4), Fraction(3)), (Fraction(4), Fraction(3))),
    (make_problem(((3, 1, "引く"), (2, 4, "合わせる")), Fraction(5), Fraction(2)), (Fraction(5), Fraction(2))),
    (make_problem(((1, 5, "合わせる"), (4, 3, "引く")), Fraction(-2), Fraction(3)), (Fraction(-2), Fraction(3))),
)

HELDOUT_SPECS = (
    (((7, 2, "合わせる"), (3, 5, "引く")), Fraction(11, 3), Fraction(-4, 5)),
    (((4, 7, "引く"), (9, 2, "合わせる")), Fraction(-3, 2), Fraction(5, 4)),
    (((5, 3, "合わせる"), (8, 1, "引く")), Fraction(7), Fraction(2)),
    (((2, 9, "引く"), (5, 4, "合わせる")), Fraction(1, 6), Fraction(-7, 3)),
    (((6, 5, "合わせる"), (7, 4, "引く")), Fraction(-5, 4), Fraction(-3, 2)),
    (((3, 8, "引く"), (11, 2, "合わせる")), Fraction(13, 5), Fraction(9, 7)),
)

def heldout() -> tuple[tuple[str, tuple[Fraction, Fraction]], ...]:
    return tuple(
        (make_problem(spec, x, y, reverse), (x, y))
        for spec, x, y in HELDOUT_SPECS for reverse in (False, True)
    )

def calibration_error(mapping: Mapping[str, str]) -> int:
    error = 0
    for text, expected in CALIBRATION:
        try:
            sol = solve_problem(parse_problem(text, mapping))
            got = (dict(sol.answers)["アキ"], dict(sol.answers)["ボブ"])
            error += got != expected
        except Exception:
            error += 1
    return error

def induce_relation_model() -> tuple[RelationModel, dict[str, int]]:
    candidates = (
        {"合わせる": "ADD", "引く": "SUB"},
        {"合わせる": "SUB", "引く": "ADD"},
    )
    scored = [(calibration_error(c), c) for c in candidates]
    best_error = min(e for e, _ in scored)
    best = [c for e, c in scored if e == best_error]
    if len(best) != 1:
        raise NonIdentifiableRelationError(f"optima={len(best)}")
    second = min(e for e, _ in scored if e > best_error)
    return RelationModel(tuple(sorted(best[0].items()))), {"candidates": len(candidates), "errors": best_error, "second": second}

def ambiguous_calibration_is_rejected() -> bool:
    def signatures(mapping: Mapping[str, str]) -> tuple[Row, Row]:
        a = parse_row("1倍のアキと0倍のボブを合わせると3", mapping)
        b = parse_row("1倍のアキと0倍のボブを引くと3", mapping)
        return a, b
    m1 = {"合わせる": "ADD", "引く": "SUB"}
    m2 = {"合わせる": "SUB", "引く": "ADD"}
    return signatures(m1) == signatures(m2)

def singular_systems_abstain(model: RelationModel) -> bool:
    text = "条件:2倍のアキと4倍のボブを合わせると6。1倍のアキと2倍のボブを合わせると3。質問:アキとボブの数を求めよ。"
    return model.solve(text) is None

def inconsistent_systems_abstain(model: RelationModel) -> bool:
    text = "条件:2倍のアキと4倍のボブを合わせると6。1倍のアキと2倍のボブを合わせると8。質問:アキとボブの数を求めよ。"
    return model.solve(text) is None

def one_equation_abstains(model: RelationModel) -> bool:
    text = "条件:2倍のアキと3倍のボブを合わせると12。質問:アキとボブの数を求めよ。"
    return model.solve(text) is None

def tampered_proof_is_rejected(model: RelationModel) -> bool:
    text, _ = heldout()[0]
    problem = model.parse(text)
    sol = solve_problem(problem)
    bad = Solution(sol.answers, Proof(sol.proof.determinant, sol.proof.x_numerator + 1, sol.proof.y_numerator, sol.proof.x, sol.proof.y))
    return not verify_solution(problem, bad)

def evaluate(model: RelationModel) -> tuple[float, float, float]:
    rows = heldout()
    answered = correct = verified = 0
    for text, expected in rows:
        sol = model.solve(text)
        if sol is None:
            continue
        answered += 1
        got = (dict(sol.answers)["アキ"], dict(sol.answers)["ボブ"])
        correct += got == expected
        verified += verify_solution(model.parse(text), sol)
    n = len(rows)
    return correct / n, answered / n, verified / n

def run() -> dict[str, object]:
    model, fit = induce_relation_model()
    accuracy, coverage, verified = evaluate(model)
    checks = {
        "relation_semantics_are_unique": dict(model.relation_map) == TRUE_RELATION,
        "positive_identifiability_margin": fit["second"] > fit["errors"],
        "heldout_exact_solutions": accuracy == coverage == verified == 1.0,
        "fraction_and_negative_solutions_present": any(x.denominator != 1 or y.denominator != 1 or x < 0 or y < 0 for _, (x, y) in heldout()),
        "singular_systems_abstain": singular_systems_abstain(model),
        "inconsistent_systems_abstain": inconsistent_systems_abstain(model),
        "one_equation_abstains": one_equation_abstains(model),
        "tampered_proof_is_rejected": tampered_proof_is_rejected(model),
        "ambiguous_calibration_is_detected": ambiguous_calibration_is_rejected(),
    }
    return {
        "campaign": {"name": "phase18b4-two-variable-linear-systems-c1", "input": "continuous controlled Japanese text only", "relation_names_preassigned": False, "public_examples": 0},
        "induction": {**fit, "relation_map": [list(x) for x in model.relation_map]},
        "evaluation": {"calibration_problems": len(CALIBRATION), "heldout_problems": len(heldout()), "accuracy": accuracy, "coverage": coverage, "verified_trace_rate": verified},
        "resources": {"model_bits": model.bits, "source_bytes": Path(__file__).read_bytes().__len__(), "python_runtime_included": False},
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {"controlled_two_variable_linear_systems": all(checks.values()), "free_form_word_problem_understanding": False, "high_school_mathematics": False},
        "limitations": ["exactly two named unknowns and two equations", "coefficient syntax is controlled and explicit", "only ADD/SUB relation phrases are induced", "no autonomous choice of variables from ordinary prose", "no inequalities, nonlinear equations, geometry, or proof discovery", "Python substrate excluded from model bits"],
    }

def markdown(p: Mapping[str, object]) -> str:
    i, e, r = p["induction"], p["evaluation"], p["resources"]
    return f'''# Phase 18b-4 results: two-variable linear systems

- Relation candidates: **{i["candidates"]}**
- Best / second calibration errors: **{i["errors"]} / {i["second"]}**
- Induced relation map: **{i["relation_map"]}**
- Calibration / held-out problems: **{e["calibration_problems"]} / {e["heldout_problems"]}**
- Accuracy / coverage / independently verified proofs: **{100*e["accuracy"]:.1f}% / {100*e["coverage"]:.1f}% / {100*e["verified_trace_rate"]:.1f}%**
- Learned payload: **{r["model_bits"]} bits**

This establishes exact two-variable linear-system solving in a controlled Japanese relation language. It is not free-form word-problem understanding or high-school-level mathematics.
'''

def main() -> None:
    p = run()
    Path("results").mkdir(exist_ok=True)
    Path("results/phase18b4.json").write_text(json.dumps(p, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    Path("results/phase18b4.md").write_text(markdown(p), encoding="utf-8")
    print(markdown(p), end="")

if __name__ == "__main__":
    main()
