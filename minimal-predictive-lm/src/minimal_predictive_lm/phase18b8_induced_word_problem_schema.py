from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
import json
from pathlib import Path
import re
from typing import Iterable, Mapping, Sequence

from .phase18b7_shared_linear_constraint_graph import (
    ConstraintGraph,
    LinearConstraint,
    NonIdentifiableConstraintError,
    Solution,
    solve,
    verify,
)

Q = Fraction
COUNT_PROGRAMS = ("SUM", "X_MINUS_Y", "Y_MINUS_X")
VALUE_PROGRAMS = ("WEIGHTED_SUM", "X_MINUS_Y", "Y_MINUS_X", "CROSS_SUM")
TRUE_COUNT = "SUM"
TRUE_VALUE = "WEIGHTED_SUM"
COUNT_CUES = ("全部で", "総数", "合わせた数")
VALUE_CUES = ("総額", "全体量", "合計値")
RATE_CUES = ("一つあたり", "単位量", "一個につき")


class NonIdentifiableSchemaError(ValueError):
    pass


@dataclass(frozen=True)
class Clause:
    cue: str
    value: int
    unit: str
    entity: str | None


@dataclass(frozen=True)
class ParsedProblem:
    entities: tuple[str, str]
    clauses: tuple[Clause, ...]
    text: str


@dataclass(frozen=True)
class Demonstration:
    text: str
    answer: tuple[int, int]


@dataclass(frozen=True)
class SchemaModel:
    global_roles: tuple[tuple[str, str], ...]
    rate_active: tuple[tuple[str, bool], ...]
    count_program: str
    value_program: str

    @property
    def bits(self) -> int:
        payload = {
            "g": self.global_roles,
            "r": self.rate_active,
            "c": self.count_program,
            "v": self.value_program,
        }
        return len(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()) * 8

    def compile(self, text: str) -> ConstraintGraph:
        parsed = parse(text)
        roles = dict(self.global_roles)
        active = dict(self.rate_active)
        globals_by_role: dict[str, list[Clause]] = {"COUNT": [], "VALUE": []}
        rates: dict[str, list[Clause]] = {name: [] for name in parsed.entities}
        for clause in parsed.clauses:
            if clause.entity is None:
                if clause.cue not in roles:
                    raise NonIdentifiableConstraintError("unknown global cue")
                globals_by_role[roles[clause.cue]].append(clause)
            else:
                if clause.cue not in active or not active[clause.cue]:
                    raise NonIdentifiableConstraintError("unknown or inactive rate cue")
                rates[clause.entity].append(clause)
        if len(globals_by_role["COUNT"]) != 1 or len(globals_by_role["VALUE"]) != 1:
            raise NonIdentifiableConstraintError("global roles are not unique")
        if any(len(rates[name]) != 1 for name in parsed.entities):
            raise NonIdentifiableConstraintError("one rate per entity is required")
        x, y = parsed.entities
        count = globals_by_role["COUNT"][0]
        value = globals_by_role["VALUE"][0]
        rx = rates[x][0]
        ry = rates[y][0]
        if rx.unit != ry.unit or value.unit != rx.unit or count.unit == value.unit:
            raise NonIdentifiableConstraintError("unit signature mismatch")
        count_coeff = {
            "SUM": {x: 1, y: 1},
            "X_MINUS_Y": {x: 1, y: -1},
            "Y_MINUS_X": {x: -1, y: 1},
        }[self.count_program]
        value_coeff = {
            "WEIGHTED_SUM": {x: rx.value, y: ry.value},
            "X_MINUS_Y": {x: rx.value, y: -ry.value},
            "Y_MINUS_X": {x: -rx.value, y: ry.value},
            "CROSS_SUM": {x: ry.value, y: rx.value},
        }[self.value_program]
        return ConstraintGraph.build(
            parsed.entities,
            (
                LinearConstraint.make(count_coeff, "EQ", count.value, f"cue:{count.cue}"),
                LinearConstraint.make(value_coeff, "EQ", value.value, f"cue:{value.cue}"),
            ),
        )

    def answer(self, text: str) -> Solution | None:
        try:
            graph = self.compile(text)
            return solve(graph)
        except (ValueError, NonIdentifiableConstraintError):
            return None


TARGET_RE = re.compile(r"対象は([^。]+?)と([^。]+?)。")
CLAUSE_RE = re.compile(r"(?:(?P<entity>[^。]+?)の)?手掛かり「(?P<cue>[^」]+)」(?P<value>-?\d+)(?P<unit>[^。]+)。")
QUESTION_RE = re.compile(r"問:([^。]+?)と([^。]+?)の個数。")


def parse(text: str) -> ParsedProblem:
    target = TARGET_RE.search(text)
    question = QUESTION_RE.search(text)
    if not target or not question:
        raise ValueError("target/question")
    entities = (target.group(1), target.group(2))
    if set(entities) != {question.group(1), question.group(2)}:
        raise ValueError("question entities")
    clauses = []
    for match in CLAUSE_RE.finditer(text):
        entity = match.group("entity")
        if entity is not None and entity not in entities:
            raise ValueError("unknown entity")
        clauses.append(Clause(match.group("cue"), int(match.group("value")), match.group("unit"), entity))
    if len(clauses) < 4:
        raise ValueError("insufficient clauses")
    return ParsedProblem(entities, tuple(clauses), text)


def render(
    entities: tuple[str, str],
    counts: tuple[int, int],
    rates: tuple[int, int],
    count_cue: str,
    value_cue: str,
    rate_cues: tuple[str, str],
    count_unit: str,
    value_unit: str,
    order: Sequence[int] = (0, 1, 2, 3),
) -> Demonstration:
    x, y = counts
    total_count = x + y
    total_value = rates[0] * x + rates[1] * y
    clauses = (
        f"手掛かり「{count_cue}」{total_count}{count_unit}。",
        f"{entities[0]}の手掛かり「{rate_cues[0]}」{rates[0]}{value_unit}。",
        f"{entities[1]}の手掛かり「{rate_cues[1]}」{rates[1]}{value_unit}。",
        f"手掛かり「{value_cue}」{total_value}{value_unit}。",
    )
    body = "".join(clauses[index] for index in order)
    text = f"対象は{entities[0]}と{entities[1]}。{body}問:{entities[0]}と{entities[1]}の個数。"
    return Demonstration(text, counts)


def training() -> tuple[Demonstration, ...]:
    specs = (
        (("大人券", "子供券"), (7, 10), (900, 500), 0, 0, (0, 1), (0, 1, 2, 3)),
        (("白玉", "黒玉"), (4, 9), (30, 70), 1, 1, (1, 2), (3, 0, 2, 1)),
        (("普通車", "大型車"), (11, 5), (4, 6), 2, 2, (2, 0), (2, 1, 3, 0)),
        (("鉛筆", "ノート"), (8, 3), (60, 140), 0, 1, (1, 0), (1, 3, 0, 2)),
        (("正解", "誤答"), (13, 7), (5, -2), 1, 2, (2, 1), (0, 3, 1, 2)),
        (("赤箱", "青箱"), (2, 12), (400, 150), 2, 0, (0, 2), (3, 2, 0, 1)),
        (("午前券", "午後券"), (9, 6), (700, 1100), 0, 2, (2, 2), (2, 0, 3, 1)),
        (("小袋", "大袋"), (10, 4), (80, 230), 1, 0, (0, 0), (1, 2, 0, 3)),
        (("短冊", "長冊"), (3, 8), (25, 90), 2, 1, (1, 1), (3, 1, 2, 0)),
    )
    return tuple(
        render(
            entities,
            counts,
            rates,
            COUNT_CUES[count_index],
            VALUE_CUES[value_index],
            (RATE_CUES[rate_indexes[0]], RATE_CUES[rate_indexes[1]]),
            "個",
            "点" if entities == ("正解", "誤答") else "円",
            order,
        )
        for entities, counts, rates, count_index, value_index, rate_indexes, order in specs
    )


def heldout() -> tuple[Demonstration, ...]:
    specs = (
        (("ニワトリ", "カメ"), (13, 7), (2, 4), 2, 2, (0, 1), "匹", "本", (3, 1, 0, 2)),
        (("学生券", "一般券"), (12, 5), (600, 1200), 1, 0, (2, 0), "枚", "円", (2, 0, 3, 1)),
        (("軽い荷物", "重い荷物"), (9, 4), (3, 8), 0, 1, (1, 2), "個", "kg", (1, 3, 2, 0)),
        (("一等賞", "二等賞"), (6, 11), (10, 4), 2, 0, (2, 1), "本", "点", (0, 2, 1, 3)),
        (("小皿", "大皿"), (14, 3), (120, 350), 1, 2, (0, 2), "枚", "円", (3, 0, 1, 2)),
        (("短時間", "長時間"), (8, 5), (15, 40), 0, 2, (1, 0), "回", "分", (2, 1, 0, 3)),
    )
    rows = []
    for entities, counts, rates, ci, vi, ri, cu, vu, order in specs:
        rows.append(render(entities, counts, rates, COUNT_CUES[ci], VALUE_CUES[vi], (RATE_CUES[ri[0]], RATE_CUES[ri[1]]), cu, vu, order))
        rows.append(render((entities[1], entities[0]), (counts[1], counts[0]), (rates[1], rates[0]), COUNT_CUES[(ci + 1) % 3], VALUE_CUES[(vi + 1) % 3], (RATE_CUES[(ri[1] + 1) % 3], RATE_CUES[(ri[0] + 1) % 3]), cu, vu, tuple(reversed(order))))
    return tuple(rows)


def _candidate_models(rows: Sequence[Demonstration]) -> Iterable[SchemaModel]:
    parsed = tuple(parse(row.text) for row in rows)
    global_cues = tuple(sorted({c.cue for p in parsed for c in p.clauses if c.entity is None}))
    rate_cues = tuple(sorted({c.cue for p in parsed for c in p.clauses if c.entity is not None}))
    for global_bits in product(("COUNT", "VALUE"), repeat=len(global_cues)):
        if set(global_bits) != {"COUNT", "VALUE"}:
            continue
        global_roles = tuple(zip(global_cues, global_bits))
        for active_bits in product((False, True), repeat=len(rate_cues)):
            rate_active = tuple(zip(rate_cues, active_bits))
            for count_program in COUNT_PROGRAMS:
                for value_program in VALUE_PROGRAMS:
                    yield SchemaModel(global_roles, rate_active, count_program, value_program)


def _model_error(model: SchemaModel, rows: Sequence[Demonstration]) -> int:
    errors = 0
    for row in rows:
        answer = model.answer(row.text)
        if answer is None:
            errors += 1
            continue
        values = dict(answer.values)
        entities = parse(row.text).entities
        errors += (values.get(entities[0]), values.get(entities[1])) != tuple(Q(x) for x in row.answer)
    return errors


def induce(rows: Sequence[Demonstration] | None = None) -> tuple[SchemaModel, dict[str, int]]:
    rows = tuple(training() if rows is None else rows)
    scored = []
    for model in _candidate_models(rows):
        scored.append((_model_error(model, rows), model))
    best_error = min(error for error, _ in scored)
    best = {model for error, model in scored if error == best_error}
    if len(best) != 1:
        raise NonIdentifiableSchemaError(f"optima={len(best)} error={best_error}")
    model = next(iter(best))
    second = min((error for error, _ in scored if error > best_error), default=best_error)
    return model, {"candidates": len(scored), "errors": best_error, "second": second}


def evaluate(model: SchemaModel) -> tuple[float, float, float]:
    correct = covered = verified_count = 0
    rows = heldout()
    for row in rows:
        answer = model.answer(row.text)
        if answer is None:
            continue
        covered += 1
        parsed = parse(row.text)
        values = dict(answer.values)
        correct += (values[parsed.entities[0]], values[parsed.entities[1]]) == tuple(Q(x) for x in row.answer)
        verified_count += verify(model.compile(row.text), answer)
    n = len(rows)
    return correct / n, covered / n, verified_count / n


def text_memorizer_coverage() -> float:
    known = {row.text for row in training()}
    return sum(row.text in known for row in heldout()) / len(heldout())


def domain_memorizer_coverage() -> float:
    known = {parse(row.text).entities for row in training()}
    return sum(parse(row.text).entities in known for row in heldout()) / len(heldout())


def number_bag_upper_bound(model: SchemaModel) -> float:
    a = render(("甲", "乙"), (6, 4), (2, 5), COUNT_CUES[0], VALUE_CUES[0], (RATE_CUES[0], RATE_CUES[0]), "個", "点")
    b = render(("甲", "乙"), (4, 6), (5, 2), COUNT_CUES[0], VALUE_CUES[0], (RATE_CUES[0], RATE_CUES[0]), "個", "点")
    assert sorted(map(int, re.findall(r"-?\d+", a.text))) == sorted(map(int, re.findall(r"-?\d+", b.text)))
    assert all(model.answer(row.text) is not None for row in (a, b))
    return 0.5


def ambiguous_calibration_is_rejected() -> bool:
    row = render(("甲", "乙"), (5, 5), (1, 1), "同じ手掛かりA", "同じ手掛かりB", ("単位", "単位"), "個", "点")
    try:
        induce((row,))
    except NonIdentifiableSchemaError:
        return True
    return False


def unknown_and_extra_cues_abstain(model: SchemaModel) -> bool:
    row = heldout()[0]
    unknown = row.text.replace("手掛かり「合わせた数」", "手掛かり「見たことのない総数語」")
    extra = row.text.replace("問:", "手掛かり「総額」999本。問:")
    return model.answer(unknown) is None and model.answer(extra) is None


def unit_mismatch_abstains(model: SchemaModel) -> bool:
    row = heldout()[0]
    broken = row.text.replace("4本", "4kg", 1)
    return model.answer(broken) is None


def schema_intervention_changes_prediction(model: SchemaModel) -> bool:
    row = heldout()[1]
    answer = model.answer(row.text)
    roles = dict(model.global_roles)
    cue = next(c.cue for c in parse(row.text).clauses if c.entity is None and roles[c.cue] == "COUNT")
    altered_roles = tuple((name, "VALUE" if name == cue else role) for name, role in model.global_roles)
    altered = SchemaModel(altered_roles, model.rate_active, model.count_program, model.value_program)
    changed = altered.answer(row.text)
    return answer is not None and changed is None


def run() -> dict[str, object]:
    model, fit = induce()
    accuracy, coverage, verified_rate = evaluate(model)
    checks = {
        "unique_schema": fit["errors"] == 0 and fit["second"] > fit["errors"],
        "correct_global_cues": dict(model.global_roles) == {**{x: "COUNT" for x in COUNT_CUES}, **{x: "VALUE" for x in VALUE_CUES}},
        "correct_rate_cues": all(dict(model.rate_active).get(x) for x in RATE_CUES),
        "correct_programs": (model.count_program, model.value_program) == (TRUE_COUNT, TRUE_VALUE),
        "heldout_accuracy": accuracy == 1.0,
        "heldout_coverage": coverage == 1.0,
        "proof_verification": verified_rate == 1.0,
        "text_memorizer_zero": text_memorizer_coverage() == 0.0,
        "domain_memorizer_zero": domain_memorizer_coverage() == 0.0,
        "number_bag_bound": number_bag_upper_bound(model) == 0.5,
        "ambiguous_calibration_rejected": ambiguous_calibration_is_rejected(),
        "unknown_extra_abstain": unknown_and_extra_cues_abstain(model),
        "unit_mismatch_abstains": unit_mismatch_abstains(model),
        "schema_intervention": schema_intervention_changes_prediction(model),
    }
    return {
        "campaign": {
            "name": "phase18b8-induced-word-problem-schema-c1",
            "surface_format": "controlled Japanese clue clauses",
            "clue_semantics_prelisted": False,
            "equation_schema_prelisted": False,
            "shared_solver": "phase18b7",
            "public_examples": 0,
        },
        "induction": {
            **fit,
            "global_roles": [list(x) for x in model.global_roles],
            "rate_active": [list(x) for x in model.rate_active],
            "count_program": model.count_program,
            "value_program": model.value_program,
        },
        "evaluation": {
            "training_examples": len(training()),
            "heldout_examples": len(heldout()),
            "heldout_domains": len(heldout()) // 2,
            "accuracy": accuracy,
            "coverage": coverage,
            "verified_proof_rate": verified_rate,
            "whole_text_memorizer_coverage": text_memorizer_coverage(),
            "domain_memorizer_coverage": domain_memorizer_coverage(),
            "number_bag_upper_bound": number_bag_upper_bound(model),
        },
        "resources": {
            "learned_schema_bits": model.bits,
            "source_bytes": Path(__file__).read_bytes().__len__(),
            "phase18b7_source_excluded_from_this_count": True,
            "python_runtime_included": False,
        },
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {
            "controlled_schema_induction": all(checks.values()),
            "free_japanese_word_problems": False,
            "autonomous_open_grammar": False,
            "high_school_intelligence": False,
        },
        "limitations": [
            "Target, clue, and question spans use a controlled generic wrapper.",
            "Only two-entity count-plus-weighted-total problems are in the hypothesis family.",
            "Known learned cues must recur at evaluation; unseen cues cause abstention.",
            "No nonlinear relations, commonsense unit conversion, or free-form explanation generation.",
        ],
    }


def markdown(payload: Mapping[str, object]) -> str:
    induction = payload["induction"]
    evaluation = payload["evaluation"]
    resources = payload["resources"]
    return f"""# Phase 18b-8 results: induced word-problem schema

- Candidate schema programs: **{induction['candidates']}**
- Training errors / second best: **{induction['errors']} / {induction['second']}**
- Induced count / value programs: **{induction['count_program']} / {induction['value_program']}**
- Training / held-out examples: **{evaluation['training_examples']} / {evaluation['heldout_examples']}**
- Held-out domains: **{evaluation['heldout_domains']}**
- Accuracy / coverage / verified proof: **{100*evaluation['accuracy']:.1f}% / {100*evaluation['coverage']:.1f}% / {100*evaluation['verified_proof_rate']:.1f}%**
- Whole-text / domain memorizer coverage: **{100*evaluation['whole_text_memorizer_coverage']:.1f}% / {100*evaluation['domain_memorizer_coverage']:.1f}%**
- Number-bag upper bound: **{100*evaluation['number_bag_upper_bound']:.1f}%**
- Learned schema payload: **{resources['learned_schema_bits']} bits**

The cue roles and algebraic schema were selected from demonstrations, then executed by the shared Phase 18b-7 solver. This is controlled schema induction, not unrestricted Japanese word-problem understanding or high-school intelligence.
"""


def main() -> None:
    payload = run()
    Path("results").mkdir(exist_ok=True)
    Path("results/phase18b8.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    Path("results/phase18b8.md").write_text(markdown(payload), encoding="utf-8")
    print(markdown(payload), end="")


if __name__ == "__main__":
    main()
