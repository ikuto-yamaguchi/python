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
ROLES = ("COUNT", "RATE", "VALUE")
COUNT_PROGRAMS = ("SUM", "X_MINUS_Y", "Y_MINUS_X")
VALUE_PROGRAMS = ("WEIGHTED_SUM", "X_MINUS_Y", "Y_MINUS_X", "CROSS_SUM")
UNITS = ("kg", "枚", "円", "個", "本", "点", "分", "回", "匹", "台", "冊", "g", "人")
NUMBER_UNIT_RE = re.compile(r"(-?\d+)(" + "|".join(map(re.escape, sorted(UNITS, key=len, reverse=True))) + r")")
SENTENCE_SPLIT_RE = re.compile(r"[。！？]+")
QUESTION_PATTERNS = (
    re.compile(r"^(.+?)と(.+?)はそれぞれ何(?:枚|円|個|本|点|分|回|匹|台|冊|g|人|つ)か$"),
    re.compile(r"^(.+?)と(.+?)の(?:個数|数)を求めよ$"),
    re.compile(r"^(.+?)と(.+?)はいくつずつ(?:ある)?か$"),
)

COUNT_TEMPLATES = (
    "{x}と{y}は全部で{n}{unit}ある",
    "{x}と{y}を合わせると{n}{unit}になる",
    "{x}と{y}の総数は{n}{unit}だ",
)
RATE_TEMPLATES = (
    "{entity}の単価は{rate}{unit}だ",
    "{entity}一つ分の値は{rate}{unit}である",
    "{entity}ごとの量は{rate}{unit}になる",
)
VALUE_TEMPLATES = (
    "売上の合計は{total}{unit}だった",
    "{x}と{y}による全体量は{total}{unit}だ",
    "二種類から得た合計値は{total}{unit}になる",
)
QUESTION_TEMPLATES = (
    "{x}と{y}はそれぞれ何{unit}か",
    "{x}と{y}の個数を求めよ",
    "{x}と{y}はいくつずつあるか",
)


class NonIdentifiableRawSchemaError(ValueError):
    pass


@dataclass(frozen=True)
class Fact:
    cue: str
    value: int
    unit: str
    entities: tuple[str, ...]
    surface: str


@dataclass(frozen=True)
class ParsedProblem:
    entities: tuple[str, str]
    facts: tuple[Fact, ...]
    question: str
    text: str


@dataclass(frozen=True)
class Demonstration:
    text: str
    answer: tuple[int, int]


@dataclass(frozen=True)
class RawSchemaModel:
    cue_roles: tuple[tuple[str, str], ...]
    count_program: str
    value_program: str

    @property
    def bits(self) -> int:
        payload = {
            "cue_roles": self.cue_roles,
            "count_program": self.count_program,
            "value_program": self.value_program,
        }
        return len(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()) * 8

    def compile_parsed(self, parsed: ParsedProblem) -> ConstraintGraph:
        roles = dict(self.cue_roles)
        buckets: dict[str, list[Fact]] = {role: [] for role in ROLES}
        for fact in parsed.facts:
            role = roles.get(fact.cue)
            if role is None:
                raise NonIdentifiableConstraintError("unknown relation span")
            buckets[role].append(fact)

        if len(buckets["COUNT"]) != 1 or len(buckets["VALUE"]) != 1:
            raise NonIdentifiableConstraintError("count and value facts must be unique")

        rate_by_entity: dict[str, Fact] = {}
        for fact in buckets["RATE"]:
            if len(fact.entities) != 1:
                raise NonIdentifiableConstraintError("rate fact must mention exactly one target entity")
            entity = fact.entities[0]
            if entity in rate_by_entity:
                raise NonIdentifiableConstraintError("duplicate rate fact")
            rate_by_entity[entity] = fact
        if set(rate_by_entity) != set(parsed.entities):
            raise NonIdentifiableConstraintError("one rate per entity is required")

        count_fact = buckets["COUNT"][0]
        value_fact = buckets["VALUE"][0]
        if len(count_fact.entities) == 1 or len(value_fact.entities) == 1:
            raise NonIdentifiableConstraintError("global facts cannot mention exactly one target entity")

        x, y = parsed.entities
        rate_x = rate_by_entity[x]
        rate_y = rate_by_entity[y]
        if rate_x.unit != rate_y.unit or value_fact.unit != rate_x.unit:
            raise NonIdentifiableConstraintError("weighted-total units disagree")
        if count_fact.unit == value_fact.unit:
            raise NonIdentifiableConstraintError("count and weighted-total units must be distinct")

        count_coefficients = {
            "SUM": {x: 1, y: 1},
            "X_MINUS_Y": {x: 1, y: -1},
            "Y_MINUS_X": {x: -1, y: 1},
        }[self.count_program]
        value_coefficients = {
            "WEIGHTED_SUM": {x: rate_x.value, y: rate_y.value},
            "X_MINUS_Y": {x: rate_x.value, y: -rate_y.value},
            "Y_MINUS_X": {x: -rate_x.value, y: rate_y.value},
            "CROSS_SUM": {x: rate_y.value, y: rate_x.value},
        }[self.value_program]

        return ConstraintGraph.build(
            parsed.entities,
            (
                LinearConstraint.make(count_coefficients, "EQ", count_fact.value, f"span:{count_fact.cue}"),
                LinearConstraint.make(value_coefficients, "EQ", value_fact.value, f"span:{value_fact.cue}"),
            ),
        )

    def answer_parsed(self, parsed: ParsedProblem) -> Solution | None:
        try:
            graph = self.compile_parsed(parsed)
            answer = solve(graph)
        except (ValueError, NonIdentifiableConstraintError):
            return None
        values = dict(answer.values)
        if set(values) != set(parsed.entities):
            return None
        if any(value.denominator != 1 or value < 0 for value in values.values()):
            return None
        return answer

    def answer(self, text: str) -> Solution | None:
        try:
            return self.answer_parsed(parse(text))
        except ValueError:
            return None


def _question_entities(sentence: str) -> tuple[str, str] | None:
    for pattern in QUESTION_PATTERNS:
        match = pattern.fullmatch(sentence)
        if match:
            left, right = match.group(1), match.group(2)
            if left != right:
                return left, right
    return None


def _relation_span(sentence: str, entities: tuple[str, str]) -> str:
    normalized = sentence
    for entity in sorted(entities, key=len, reverse=True):
        normalized = normalized.replace(entity, "<E>")
    normalized = NUMBER_UNIT_RE.sub("<N><U>", normalized)
    return normalized


def parse(text: str) -> ParsedProblem:
    sentences = tuple(part.strip() for part in SENTENCE_SPLIT_RE.split(text) if part.strip())
    questions = tuple((sentence, _question_entities(sentence)) for sentence in sentences if _question_entities(sentence))
    if len(questions) != 1:
        raise ValueError("exactly one supported question sentence is required")
    question, entities_or_none = questions[0]
    assert entities_or_none is not None
    entities = entities_or_none

    facts: list[Fact] = []
    for sentence in sentences:
        if sentence == question:
            continue
        numeric_mentions = NUMBER_UNIT_RE.findall(sentence)
        if not numeric_mentions:
            if re.search(r"\d", sentence):
                raise ValueError("unrecognized numeric expression")
            continue
        if len(numeric_mentions) != 1:
            raise ValueError("each numeric fact sentence must contain exactly one recognized quantity")
        number, unit = numeric_mentions[0]
        mentioned = tuple(entity for entity in entities if entity in sentence)
        facts.append(Fact(_relation_span(sentence, entities), int(number), unit, mentioned, sentence))

    if len(facts) != 4:
        raise ValueError("the current hypothesis family requires exactly four numeric facts")
    if any(sum(entity in fact.entities for fact in facts) < 2 for entity in entities):
        raise ValueError("question entities must be grounded in multiple facts")
    return ParsedProblem(entities, tuple(facts), question, text)


def render(
    entities: tuple[str, str],
    counts: tuple[int, int],
    rates: tuple[int, int],
    count_unit: str,
    value_unit: str,
    count_template: int,
    rate_templates: tuple[int, int],
    value_template: int,
    question_template: int,
    order: Sequence[int],
    distractors: Sequence[str] = (),
) -> Demonstration:
    x, y = entities
    nx, ny = counts
    rx, ry = rates
    clauses = (
        COUNT_TEMPLATES[count_template].format(x=x, y=y, n=nx + ny, unit=count_unit),
        RATE_TEMPLATES[rate_templates[0]].format(entity=x, rate=rx, unit=value_unit),
        RATE_TEMPLATES[rate_templates[1]].format(entity=y, rate=ry, unit=value_unit),
        VALUE_TEMPLATES[value_template].format(x=x, y=y, total=rx * nx + ry * ny, unit=value_unit),
    )
    question = QUESTION_TEMPLATES[question_template].format(x=x, y=y, unit=count_unit)
    sentences = tuple(distractors) + tuple(clauses[index] for index in order) + (question,)
    return Demonstration("。".join(sentences) + "。", counts)


def training() -> tuple[Demonstration, ...]:
    specifications = (
        (("大人券", "子供券"), (7, 10), (900, 500), "枚", "円", 0, (0, 1), 0, 0, (2, 0, 3, 1)),
        (("白玉", "黒玉"), (4, 9), (30, 70), "個", "g", 1, (1, 2), 1, 1, (3, 1, 0, 2)),
        (("普通車", "大型車"), (11, 5), (4, 6), "台", "本", 2, (2, 0), 2, 2, (1, 3, 2, 0)),
        (("鉛筆", "ノート"), (8, 3), (60, 140), "個", "円", 0, (1, 0), 1, 2, (0, 2, 1, 3)),
        (("正解", "誤答"), (13, 7), (5, -2), "回", "点", 1, (2, 1), 2, 0, (3, 0, 1, 2)),
        (("赤箱", "青箱"), (2, 12), (400, 150), "個", "円", 2, (0, 2), 0, 1, (2, 1, 3, 0)),
        (("午前券", "午後券"), (9, 6), (700, 1100), "枚", "円", 0, (2, 2), 2, 1, (1, 0, 3, 2)),
        (("小袋", "大袋"), (10, 4), (80, 230), "個", "g", 1, (0, 0), 0, 2, (3, 2, 0, 1)),
        (("短冊", "長冊"), (3, 8), (25, 90), "枚", "円", 2, (1, 1), 1, 0, (0, 3, 2, 1)),
    )
    return tuple(render(*specification, distractors=("参考として会場は静かだった",)) for specification in specifications)


def heldout() -> tuple[Demonstration, ...]:
    specifications = (
        (("ニワトリ", "カメ"), (13, 7), (2, 4), "匹", "本", 2, (0, 2), 2, 0, (3, 1, 0, 2)),
        (("学生券", "一般券"), (12, 5), (600, 1200), "枚", "円", 1, (2, 0), 0, 1, (2, 0, 3, 1)),
        (("軽い荷物", "重い荷物"), (9, 4), (3, 8), "個", "kg", 0, (1, 2), 1, 2, (1, 3, 2, 0)),
        (("一等賞", "二等賞"), (6, 11), (10, 4), "本", "点", 2, (2, 1), 0, 0, (0, 2, 1, 3)),
        (("小皿", "大皿"), (14, 3), (120, 350), "枚", "円", 1, (0, 2), 2, 1, (3, 0, 1, 2)),
        (("短時間", "長時間"), (8, 5), (15, 40), "回", "分", 0, (2, 0), 1, 2, (2, 1, 0, 3)),
    )
    rows: list[Demonstration] = []
    for index, specification in enumerate(specifications):
        rows.append(render(*specification, distractors=("この説明には不要な背景文も含まれる",)))
        entities, counts, rates, count_unit, value_unit, count_index, rate_indexes, value_index, question_index, order = specification
        rows.append(
            render(
                (entities[1], entities[0]),
                (counts[1], counts[0]),
                (rates[1], rates[0]),
                count_unit,
                value_unit,
                (count_index + 1) % len(COUNT_TEMPLATES),
                ((rate_indexes[1] + 1) % len(RATE_TEMPLATES), (rate_indexes[0] + 1) % len(RATE_TEMPLATES)),
                (value_index + 1) % len(VALUE_TEMPLATES),
                (question_index + 1) % len(QUESTION_TEMPLATES),
                tuple(reversed(order)),
                distractors=(f"昨日の記録{index + 1}も確認した",),
            )
        )
    return tuple(rows)


def _candidate_models(rows: Sequence[Demonstration]) -> Iterable[RawSchemaModel]:
    parsed_rows = tuple(parse(row.text) for row in rows)
    cues = tuple(sorted({fact.cue for parsed in parsed_rows for fact in parsed.facts}))
    for role_assignment in product(ROLES, repeat=len(cues)):
        if set(role_assignment) != set(ROLES):
            continue
        cue_roles = tuple(zip(cues, role_assignment))
        for count_program in COUNT_PROGRAMS:
            for value_program in VALUE_PROGRAMS:
                yield RawSchemaModel(cue_roles, count_program, value_program)


def _model_error(model: RawSchemaModel, parsed_rows: Sequence[ParsedProblem], rows: Sequence[Demonstration]) -> int:
    errors = 0
    for parsed, row in zip(parsed_rows, rows):
        answer = model.answer_parsed(parsed)
        if answer is None:
            errors += 1
            continue
        values = dict(answer.values)
        predicted = (values[parsed.entities[0]], values[parsed.entities[1]])
        errors += predicted != tuple(Q(value) for value in row.answer)
    return errors


def induce(rows: Sequence[Demonstration] | None = None) -> tuple[RawSchemaModel, dict[str, int]]:
    rows = tuple(training() if rows is None else rows)
    parsed_rows = tuple(parse(row.text) for row in rows)
    best_error = len(rows) + 1
    second_error = len(rows) + 1
    best_models: list[RawSchemaModel] = []
    candidate_count = 0
    for model in _candidate_models(rows):
        candidate_count += 1
        error = _model_error(model, parsed_rows, rows)
        if error < best_error:
            second_error = best_error
            best_error = error
            best_models = [model]
        elif error == best_error:
            best_models.append(model)
        elif error < second_error:
            second_error = error
    if len(best_models) != 1:
        raise NonIdentifiableRawSchemaError(f"optima={len(best_models)} error={best_error}")
    return best_models[0], {"candidates": candidate_count, "errors": best_error, "second": second_error}


def evaluate(model: RawSchemaModel) -> tuple[float, float, float]:
    correct = covered = verified_count = 0
    rows = heldout()
    for row in rows:
        try:
            parsed = parse(row.text)
        except ValueError:
            continue
        answer = model.answer_parsed(parsed)
        if answer is None:
            continue
        covered += 1
        values = dict(answer.values)
        correct += (values[parsed.entities[0]], values[parsed.entities[1]]) == tuple(Q(value) for value in row.answer)
        verified_count += verify(model.compile_parsed(parsed), answer)
    total = len(rows)
    return correct / total, covered / total, verified_count / total


def whole_text_memorizer_coverage() -> float:
    known = {row.text for row in training()}
    return sum(row.text in known for row in heldout()) / len(heldout())


def domain_memorizer_coverage() -> float:
    known = {parse(row.text).entities for row in training()}
    return sum(parse(row.text).entities in known for row in heldout()) / len(heldout())


def number_bag_upper_bound(model: RawSchemaModel) -> float:
    left = render(("甲", "乙"), (6, 4), (2, 5), "個", "点", 0, (0, 0), 0, 0, (0, 1, 2, 3))
    right = render(("甲", "乙"), (4, 6), (5, 2), "個", "点", 0, (0, 0), 0, 0, (0, 1, 2, 3))
    assert sorted(map(int, re.findall(r"-?\d+", left.text))) == sorted(map(int, re.findall(r"-?\d+", right.text)))
    assert model.answer(left.text) is not None and model.answer(right.text) is not None
    return 0.5


def ambiguous_calibration_is_rejected() -> bool:
    row = render(("甲", "乙"), (5, 5), (2, 5), "個", "点", 0, (0, 0), 0, 0, (0, 1, 2, 3))
    try:
        induce((row,))
    except NonIdentifiableRawSchemaError:
        return True
    return False


def unknown_extra_and_unit_mismatch_abstain(model: RawSchemaModel) -> bool:
    row = heldout()[0]
    parsed = parse(row.text)
    count_surface = next(fact.surface for fact in parsed.facts if len(fact.entities) == 2)
    unknown_surface = count_surface.replace("総数", "見たことのない関係").replace("合わせる", "混ぜ合わせ切る").replace("全部で", "謎の関係で")
    unknown = row.text.replace(count_surface, unknown_surface)
    extra = row.text.replace(parsed.question + "。", f"予備の費用は999円だった。{parsed.question}。")
    rate_surface = next(fact.surface for fact in parsed.facts if len(fact.entities) == 1)
    rate_match = NUMBER_UNIT_RE.search(rate_surface)
    assert rate_match is not None
    replacement_unit = "kg" if rate_match.group(2) != "kg" else "円"
    mismatch_surface = rate_surface[: rate_match.start(2)] + replacement_unit + rate_surface[rate_match.end(2) :]
    mismatch = row.text.replace(rate_surface, mismatch_surface)
    return model.answer(unknown) is None and model.answer(extra) is None and model.answer(mismatch) is None


def unsupported_question_abstains(model: RawSchemaModel) -> bool:
    row = heldout()[0]
    parsed = parse(row.text)
    unsupported = row.text.replace(parsed.question, f"{parsed.entities[0]}だけを教えてください")
    return model.answer(unsupported) is None


def schema_intervention_changes_prediction(model: RawSchemaModel) -> bool:
    row = heldout()[1]
    parsed = parse(row.text)
    original = model.answer_parsed(parsed)
    roles = dict(model.cue_roles)
    count_cue = next(fact.cue for fact in parsed.facts if roles[fact.cue] == "COUNT")
    altered = RawSchemaModel(tuple((cue, "VALUE" if cue == count_cue else role) for cue, role in model.cue_roles), model.count_program, model.value_program)
    changed = altered.answer_parsed(parsed)
    return original is not None and changed is None


def tampered_solution_is_rejected(model: RawSchemaModel) -> bool:
    parsed = parse(heldout()[0].text)
    answer = model.answer_parsed(parsed)
    assert answer is not None
    tampered = Solution(answer.kind, tuple(reversed(answer.values)), answer.interval, answer.proof)
    return not verify(model.compile_parsed(parsed), tampered)


def run() -> dict[str, object]:
    model, fit = induce()
    accuracy, coverage, verified_rate = evaluate(model)
    expected_roles = {
        **{template.format(x="<E>", y="<E>", n="<N>", unit="<U>"): "COUNT" for template in COUNT_TEMPLATES},
        **{template.format(entity="<E>", rate="<N>", unit="<U>"): "RATE" for template in RATE_TEMPLATES},
        **{template.format(x="<E>", y="<E>", total="<N>", unit="<U>"): "VALUE" for template in VALUE_TEMPLATES},
    }
    checks = {
        "unique_zero_error_schema": fit["errors"] == 0 and fit["second"] > 0,
        "correct_span_roles": dict(model.cue_roles) == expected_roles,
        "correct_equation_programs": (model.count_program, model.value_program) == ("SUM", "WEIGHTED_SUM"),
        "heldout_accuracy": accuracy == 1.0,
        "heldout_coverage": coverage == 1.0,
        "proof_verification": verified_rate == 1.0,
        "whole_text_memorizer_zero": whole_text_memorizer_coverage() == 0.0,
        "domain_memorizer_zero": domain_memorizer_coverage() == 0.0,
        "number_bag_bound": number_bag_upper_bound(model) == 0.5,
        "ambiguous_calibration_rejected": ambiguous_calibration_is_rejected(),
        "unknown_extra_unit_abstain": unknown_extra_and_unit_mismatch_abstain(model),
        "unsupported_question_abstains": unsupported_question_abstains(model),
        "schema_intervention": schema_intervention_changes_prediction(model),
        "tampered_solution_rejected": tampered_solution_is_rejected(model),
    }
    return {
        "campaign": {
            "name": "phase18b9-raw-japanese-span-schema-c1",
            "explicit_target_wrapper": False,
            "quoted_clue_wrapper": False,
            "explicit_question_prefix": False,
            "fixed_sentence_splitter": True,
            "fixed_number_unit_recognizer": True,
            "fixed_supported_question_forms": len(QUESTION_PATTERNS),
            "public_examples": 0,
        },
        "induction": {**fit, "cue_roles": [list(item) for item in model.cue_roles], "count_program": model.count_program, "value_program": model.value_program},
        "evaluation": {
            "training_examples": len(training()),
            "heldout_examples": len(heldout()),
            "heldout_domains": len(heldout()) // 2,
            "accuracy": accuracy,
            "coverage": coverage,
            "verified_proof_rate": verified_rate,
            "whole_text_memorizer_coverage": whole_text_memorizer_coverage(),
            "domain_memorizer_coverage": domain_memorizer_coverage(),
            "number_bag_upper_bound": number_bag_upper_bound(model),
        },
        "resources": {
            "learned_schema_bits": model.bits,
            "source_bytes": len(Path(__file__).read_bytes()),
            "phase18b7_shared_solver_excluded": True,
            "python_runtime_included": False,
        },
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {
            "controlled_raw_sentence_span_induction": all(checks.values()),
            "free_japanese_parsing": False,
            "unseen_paraphrase_understanding": False,
            "high_school_intelligence": False,
        },
        "limitations": [
            "Sentence splitting, number-unit recognition, and three question forms are fixed.",
            "The current family requires four numeric facts and exactly two target entities.",
            "Relation spans must have appeared during training; unseen paraphrases abstain.",
            "Only count plus weighted-total linear word problems are available.",
            "No broad morphology, commonsense units, nonlinear algebra, or open Japanese generation.",
        ],
    }


def markdown(payload: Mapping[str, object]) -> str:
    induction = payload["induction"]
    evaluation = payload["evaluation"]
    resources = payload["resources"]
    return f"""# Phase 18b-9 results: raw Japanese span/schema induction

- Candidate role/equation programs: **{induction['candidates']}**
- Best / second training error: **{induction['errors']} / {induction['second']}**
- Learned programs: **{induction['count_program']} / {induction['value_program']}**
- Training / held-out: **{evaluation['training_examples']} / {evaluation['heldout_examples']}**
- Held-out domains: **{evaluation['heldout_domains']}**
- Accuracy / coverage / verified proof: **{100 * evaluation['accuracy']:.1f}% / {100 * evaluation['coverage']:.1f}% / {100 * evaluation['verified_proof_rate']:.1f}%**
- Whole-text / domain memorizer coverage: **{100 * evaluation['whole_text_memorizer_coverage']:.1f}% / {100 * evaluation['domain_memorizer_coverage']:.1f}%**
- Number-bag upper bound: **{100 * evaluation['number_bag_upper_bound']:.1f}%**
- Learned span/schema payload: **{resources['learned_schema_bits']} bits**

The explicit target/clue/question wrapper is gone. Recurrent raw relation spans and the two equation programs are selected from answers, then executed by the shared exact solver. Sentence splitting, quantity recognition, supported question forms, and the four-fact two-entity family remain fixed; this is not free Japanese or high-school intelligence.
"""


def main() -> None:
    payload = run()
    Path("results").mkdir(exist_ok=True)
    Path("results/phase18b9.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    Path("results/phase18b9.md").write_text(markdown(payload), encoding="utf-8")
    print(markdown(payload), end="")


if __name__ == "__main__":
    main()
