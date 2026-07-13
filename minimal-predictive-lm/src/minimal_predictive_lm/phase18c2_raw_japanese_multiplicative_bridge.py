from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
import json
from pathlib import Path
import re
from typing import Mapping, Sequence

from .phase18c1_multiplicative_relation_core import (
    COUNT,
    CURRENCY,
    LENGTH,
    MASS,
    TIME,
    ZERO_DIM,
    Dimension,
    NonIdentifiableProductError,
    OrientationModel,
    ProductGraph,
    ProductSolution,
    StructuredCase,
    compile_case,
    dim_sub,
    induce as induce_orientations,
    solve,
    verify,
)

Q = Fraction
SENTENCE_SPLIT_RE = re.compile(r"[。！？]+")
FACT_RE = re.compile(r"^(.+?)は(-?\d+(?:/\d+)?(?:\.\d+)?)(km/h|円/個|km|h|g|%|個|円)である$")
QUESTION_RE = re.compile(r"^(.+?)を求めよ$")

DISTANCE = "DISTANCE"
SPEED = "SPEED"
DURATION = "TIME"
CONCENTRATION = "CONCENTRATION"
SOLUTION = "SOLUTION"
SOLUTE = "SOLUTE"
QUANTITY = "QUANTITY"
TOTAL_PRICE = "TOTAL_PRICE"
UNIT_PRICE = "UNIT_PRICE"

RELATION_ROLES = {
    "速度関係": (DISTANCE, SPEED, DURATION),
    "濃度関係": (CONCENTRATION, SOLUTION, SOLUTE),
    "価格関係": (QUANTITY, TOTAL_PRICE, UNIT_PRICE),
}
ROLE_DIMENSIONS: dict[str, Dimension] = {
    DISTANCE: LENGTH,
    SPEED: dim_sub(LENGTH, TIME),
    DURATION: TIME,
    CONCENTRATION: ZERO_DIM,
    SOLUTION: MASS,
    SOLUTE: MASS,
    QUANTITY: COUNT,
    TOTAL_PRICE: CURRENCY,
    UNIT_PRICE: dim_sub(CURRENCY, COUNT),
}
ROLE_UNITS = {
    DISTANCE: "km",
    SPEED: "km/h",
    DURATION: "h",
    CONCENTRATION: "%",
    SOLUTION: "g",
    SOLUTE: "g",
    QUANTITY: "個",
    TOTAL_PRICE: "円",
    UNIT_PRICE: "円/個",
}
UNIT_ROLE_CANDIDATES = {
    "km": (DISTANCE,),
    "km/h": (SPEED,),
    "h": (DURATION,),
    "%": (CONCENTRATION,),
    "g": (SOLUTION, SOLUTE),
    "個": (QUANTITY,),
    "円": (TOTAL_PRICE,),
    "円/個": (UNIT_PRICE,),
}
CUES = {
    DISTANCE: ("道のり", "進んだ距離"),
    SPEED: ("速さ", "移動速度"),
    DURATION: ("時間", "所要時間"),
    CONCENTRATION: ("濃度", "成分割合"),
    SOLUTION: ("溶液全体", "液体の量"),
    SOLUTE: ("溶けた物質", "中の成分"),
    QUANTITY: ("個数", "品数"),
    TOTAL_PRICE: ("代金", "支払額"),
    UNIT_PRICE: ("単価", "一個価格"),
}


class NonIdentifiableLanguageBridgeError(ValueError):
    pass


@dataclass(frozen=True)
class QuantityFact:
    cue: str
    value: Q
    unit: str


@dataclass(frozen=True)
class ParsedProblem:
    facts: tuple[QuantityFact, ...]
    question_cue: str
    text: str


@dataclass(frozen=True)
class Demonstration:
    text: str
    answer: Q


@dataclass(frozen=True)
class MultiplicativeLanguageModel:
    cue_roles: tuple[tuple[str, str], ...]
    orientations: OrientationModel

    @property
    def bits(self) -> int:
        payload = {"cue_roles": self.cue_roles}
        return len(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()) * 8

    def compile_parsed(self, parsed: ParsedProblem) -> tuple[ProductGraph, dict[str, Q], str]:
        roles = dict(self.cue_roles)
        fact_roles = []
        for fact in parsed.facts:
            role = roles.get(fact.cue)
            if role is None or ROLE_UNITS[role] != fact.unit:
                raise NonIdentifiableLanguageBridgeError("unknown cue or unit-role mismatch")
            fact_roles.append((role, fact))
        target_role = roles.get(parsed.question_cue)
        if target_role is None:
            raise NonIdentifiableLanguageBridgeError("unknown question cue")
        if target_role in {role for role, _ in fact_roles}:
            raise NonIdentifiableLanguageBridgeError("question target is already supplied")
        present_roles = {target_role, *(role for role, _ in fact_roles)}
        relation = next((name for name, relation_roles in RELATION_ROLES.items() if present_roles == set(relation_roles)), None)
        if relation is None or len(fact_roles) != 2:
            raise NonIdentifiableLanguageBridgeError("facts do not form one supported relation")
        relation_roles = RELATION_ROLES[relation]
        values: list[Q | None] = []
        fact_by_role = {role: fact for role, fact in fact_roles}
        if len(fact_by_role) != 2:
            raise NonIdentifiableLanguageBridgeError("duplicate semantic role")
        for role in relation_roles:
            values.append(None if role == target_role else fact_by_role[role].value)
        case = StructuredCase(
            relation,
            relation_roles,
            tuple(ROLE_DIMENSIONS[role] for role in relation_roles),
            tuple(values),  # type: ignore[arg-type]
            Q(0),
        )
        return compile_case(self.orientations, case)

    def answer_parsed(self, parsed: ParsedProblem) -> ProductSolution | None:
        try:
            graph, known, target = self.compile_parsed(parsed)
            return solve(graph, known, (target,))
        except (ValueError, NonIdentifiableProductError, NonIdentifiableLanguageBridgeError):
            return None

    def answer(self, text: str) -> ProductSolution | None:
        try:
            return self.answer_parsed(parse(text))
        except ValueError:
            return None


def parse_number(text: str, unit: str) -> Q:
    value = Q(text)
    return value / 100 if unit == "%" else value


def parse(text: str) -> ParsedProblem:
    sentences = tuple(part.strip() for part in SENTENCE_SPLIT_RE.split(text) if part.strip())
    facts = []
    questions = []
    for sentence in sentences:
        fact_match = FACT_RE.fullmatch(sentence)
        if fact_match:
            cue, number, unit = fact_match.groups()
            facts.append(QuantityFact(cue, parse_number(number, unit), unit))
            continue
        question_match = QUESTION_RE.fullmatch(sentence)
        if question_match:
            questions.append(question_match.group(1))
            continue
        if re.search(r"\d", sentence):
            raise ValueError("unrecognized numeric sentence")
    if len(facts) != 2 or len(questions) != 1:
        raise ValueError("exactly two facts and one question are required")
    if len({fact.cue for fact in facts}) != 2:
        raise ValueError("duplicate cue")
    return ParsedProblem(tuple(facts), questions[0], text)


def format_number(value: Q, unit: str) -> str:
    raw = value * 100 if unit == "%" else value
    return str(raw.numerator) if raw.denominator == 1 else f"{raw.numerator}/{raw.denominator}"


def render(
    relation: str,
    values: tuple[Q, Q, Q],
    target_index: int,
    variants: tuple[int, int, int],
    reverse_facts: bool = False,
    distractor: str = "背景情報は計算に使わない",
) -> Demonstration:
    roles = RELATION_ROLES[relation]
    facts = []
    for index, role in enumerate(roles):
        if index == target_index:
            continue
        cue = CUES[role][variants[index]]
        unit = ROLE_UNITS[role]
        facts.append(f"{cue}は{format_number(values[index], unit)}{unit}である")
    if reverse_facts:
        facts.reverse()
    question = f"{CUES[roles[target_index]][variants[target_index]]}を求めよ"
    text = "。".join((distractor, *facts, question)) + "。"
    return Demonstration(text, values[target_index])


def calibration() -> tuple[Demonstration, ...]:
    relation_values = {
        "速度関係": (
            (Q(120), Q(60), Q(2)),
            (Q(45), Q(30), Q(3, 2)),
            (Q(90), Q(72), Q(5, 4)),
        ),
        "濃度関係": (
            (Q(1, 5), Q(250), Q(50)),
            (Q(3, 20), Q(400), Q(60)),
            (Q(1, 8), Q(360), Q(45)),
        ),
        "価格関係": (
            (Q(7), Q(840), Q(120)),
            (Q(9), Q(2250), Q(250)),
            (Q(15), Q(1200), Q(80)),
        ),
    }
    rows = []
    for relation_index, relation in enumerate(RELATION_ROLES):
        values_set = relation_values[relation]
        for target_index in range(3):
            for variant in range(2):
                variants = tuple((variant + index + relation_index) % 2 for index in range(3))
                rows.append(
                    render(
                        relation,
                        values_set[target_index],
                        target_index,
                        variants,  # type: ignore[arg-type]
                        reverse_facts=bool((target_index + variant) % 2),
                        distractor="語彙と数量の対応を観測する",
                    )
                )
    return tuple(rows)


def cue_units(examples: Sequence[Demonstration]) -> dict[str, str]:
    observed: dict[str, str] = {}
    questions = set()
    for row in examples:
        parsed = parse(row.text)
        questions.add(parsed.question_cue)
        for fact in parsed.facts:
            previous = observed.get(fact.cue)
            if previous is not None and previous != fact.unit:
                raise NonIdentifiableLanguageBridgeError("cue has conflicting units")
            observed[fact.cue] = fact.unit
    if questions - set(observed):
        raise NonIdentifiableLanguageBridgeError("every question cue must appear as a fact elsewhere")
    return observed


def candidate_models(examples: Sequence[Demonstration]) -> tuple[tuple[MultiplicativeLanguageModel, ...], dict[str, int]]:
    examples = tuple(examples)
    observed = cue_units(examples)
    cues = tuple(sorted(observed))
    choices = tuple(UNIT_ROLE_CANDIDATES[observed[cue]] for cue in cues)
    orientations, _ = induce_orientations()
    survivors = []
    hypothesis_count = 1
    for options in choices:
        hypothesis_count *= len(options)
    parsed_examples = tuple(parse(row.text) for row in examples)
    for assignment in product(*choices):
        model = MultiplicativeLanguageModel(tuple(zip(cues, assignment)), orientations)
        valid = True
        for parsed, row in zip(parsed_examples, examples):
            answer = model.answer_parsed(parsed)
            if answer is None:
                valid = False
                break
            target = dict(model.cue_roles)[parsed.question_cue]
            if dict(answer.values)[target] != row.answer:
                valid = False
                break
        if valid:
            survivors.append(model)
    return tuple(survivors), {"lexical_hypotheses": hypothesis_count, "survivors": len(survivors), "examples": len(examples)}


def induce(examples: Sequence[Demonstration] | None = None) -> tuple[MultiplicativeLanguageModel, dict[str, int]]:
    rows = tuple(calibration() if examples is None else examples)
    survivors, fit = candidate_models(rows)
    if len(survivors) != 1:
        raise NonIdentifiableLanguageBridgeError(f"lexicon survivors={len(survivors)}")
    return survivors[0], fit


def heldout() -> tuple[Demonstration, ...]:
    relation_values = {
        "速度関係": (
            (Q(150), Q(60), Q(5, 2)),
            (Q(84), Q(56), Q(3, 2)),
            (Q(20), Q(25, 2), Q(8, 5)),
        ),
        "濃度関係": (
            (Q(7, 50), Q(500), Q(70)),
            (Q(3, 20), Q(600), Q(90)),
            (Q(1, 10), Q(450), Q(45)),
        ),
        "価格関係": (
            (Q(12), Q(1560), Q(130)),
            (Q(8), Q(1400), Q(175)),
            (Q(11), Q(825), Q(75)),
        ),
    }
    rows = []
    for relation in RELATION_ROLES:
        for target_index in range(3):
            values = relation_values[relation][target_index]
            for shift in range(2):
                variants = tuple((shift + target_index + index) % 2 for index in range(3))
                rows.append(
                    render(
                        relation,
                        values,
                        target_index,
                        variants,  # type: ignore[arg-type]
                        reverse_facts=bool(shift),
                        distractor="初見の数値と文順で検証する",
                    )
                )
    return tuple(rows)


def evaluate(model: MultiplicativeLanguageModel) -> tuple[float, float, float]:
    correct = covered = verified_count = 0
    rows = heldout()
    for row in rows:
        parsed = parse(row.text)
        answer = model.answer_parsed(parsed)
        if answer is None:
            continue
        covered += 1
        target = dict(model.cue_roles)[parsed.question_cue]
        correct += dict(answer.values)[target] == row.answer
        graph, known, target_name = model.compile_parsed(parsed)
        verified_count += verify(graph, known, (target_name,), answer)
    total = len(rows)
    return correct / total, covered / total, verified_count / total


def ambiguous_mass_lexicon_rejected() -> bool:
    rows = []
    values = (Q(1), Q(100), Q(100))
    for target_index in range(3):
        for variant in range(2):
            rows.append(render("濃度関係", values, target_index, (variant, variant, variant)))
    try:
        induce(tuple(rows))
    except NonIdentifiableLanguageBridgeError:
        return True
    return False


def whole_text_memorizer_coverage() -> float:
    known = {row.text for row in calibration()}
    return sum(row.text in known for row in heldout()) / len(heldout())


def number_unit_bag_upper_bound(model: MultiplicativeLanguageModel) -> float:
    left = render("濃度関係", (Q(1, 2), Q(100), Q(50)), 2, (0, 0, 0))
    right = render("濃度関係", (Q(1, 2), Q(200), Q(100)), 1, (0, 0, 0))
    left_numbers = sorted((fact.value, fact.unit) for fact in parse(left.text).facts)
    right_numbers = sorted((fact.value, fact.unit) for fact in parse(right.text).facts)
    assert left_numbers == right_numbers
    assert model.answer(left.text) is not None and model.answer(right.text) is not None
    return 0.5


def negative_controls(model: MultiplicativeLanguageModel) -> dict[str, bool]:
    row = heldout()[0]
    parsed = parse(row.text)
    unknown = row.text.replace(parsed.question_cue, "未知の量")
    extra = row.text.replace(parsed.question_cue + "を求めよ", f"予備距離は9kmである。{parsed.question_cue}を求めよ")
    bad_unit = row.text.replace("km/h", "g", 1)
    mixed = "背景。道のりは90kmである。中の成分は30gである。時間を求めよ。"
    two_questions = row.text + "速さを求めよ。"
    return {
        "unknown_cue": model.answer(unknown) is None,
        "extra_numeric_fact": model.answer(extra) is None,
        "unit_role_mismatch": model.answer(bad_unit) is None,
        "mixed_relation": model.answer(mixed) is None,
        "two_questions": model.answer(two_questions) is None,
    }


def tampered_proof_rejected(model: MultiplicativeLanguageModel) -> bool:
    parsed = parse(heldout()[0].text)
    answer = model.answer_parsed(parsed)
    assert answer is not None
    graph, known, target = model.compile_parsed(parsed)
    tampered = ProductSolution(tuple((name, value + (1 if name == target else 0)) for name, value in answer.values), answer.steps)
    return not verify(graph, known, (target,), tampered)


def run() -> dict[str, object]:
    model, fit = induce()
    accuracy, coverage, verified_rate = evaluate(model)
    controls = negative_controls(model)
    expected = {cue: role for role, cues in CUES.items() for cue in cues}
    checks = {
        "unique_lexicon": fit["survivors"] == 1,
        "correct_cue_roles": dict(model.cue_roles) == expected,
        "heldout_accuracy": accuracy == 1.0,
        "heldout_coverage": coverage == 1.0,
        "proof_verification": verified_rate == 1.0,
        "ambiguous_mass_lexicon_rejected": ambiguous_mass_lexicon_rejected(),
        "whole_text_memorizer_zero": whole_text_memorizer_coverage() == 0.0,
        "number_unit_bag_bound": number_unit_bag_upper_bound(model) == 0.5,
        "negative_controls": all(controls.values()),
        "tampered_proof_rejected": tampered_proof_rejected(model),
    }
    return {
        "campaign": {
            "name": "phase18c2-raw-japanese-multiplicative-bridge-c1",
            "relations": list(RELATION_ROLES),
            "fixed_sentence_splitter": True,
            "fixed_quantity_syntax": True,
            "fixed_units": sorted(UNIT_ROLE_CANDIDATES),
            "shared_core": "phase18c1",
            "public_examples": 0,
        },
        "induction": {**fit, "cue_roles": [list(item) for item in model.cue_roles]},
        "evaluation": {
            "calibration_examples": len(calibration()),
            "heldout_examples": len(heldout()),
            "accuracy": accuracy,
            "coverage": coverage,
            "verified_proof_rate": verified_rate,
            "whole_text_memorizer_coverage": whole_text_memorizer_coverage(),
            "number_unit_bag_upper_bound": number_unit_bag_upper_bound(model),
        },
        "negative_controls": controls,
        "resources": {
            "learned_lexicon_bits": model.bits,
            "source_bytes": len(Path(__file__).read_bytes()),
            "phase18c1_source_excluded": True,
            "python_runtime_included": False,
        },
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {
            "controlled_raw_japanese_multiplicative_word_problems": all(checks.values()),
            "unseen_word_understanding": False,
            "free_japanese_parsing": False,
            "unit_conversion": False,
            "high_school_intelligence": False,
        },
        "limitations": [
            "Sentence shape, decimal/fraction syntax, units, and question suffix are fixed.",
            "All cue phrases appear in calibration; unseen synonyms abstain.",
            "Only speed, concentration, and unit-price product relations are supported.",
            "No unit conversion, mixed units, irrelevant numeric facts, or multi-paragraph discourse.",
        ],
    }


def markdown(payload: Mapping[str, object]) -> str:
    induction = payload["induction"]
    evaluation = payload["evaluation"]
    resources = payload["resources"]
    return f"""# Phase 18c-2 results: raw Japanese multiplicative bridge

- Lexical hypotheses / survivors: **{induction['lexical_hypotheses']} / {induction['survivors']}**
- Calibration / held-out examples: **{evaluation['calibration_examples']} / {evaluation['heldout_examples']}**
- Accuracy / coverage / verified proof: **{100 * evaluation['accuracy']:.1f}% / {100 * evaluation['coverage']:.1f}% / {100 * evaluation['verified_proof_rate']:.1f}%**
- Whole-text memorizer coverage: **{100 * evaluation['whole_text_memorizer_coverage']:.1f}%**
- Number-unit bag upper bound: **{100 * evaluation['number_unit_bag_upper_bound']:.1f}%**
- Learned lexicon payload: **{resources['learned_lexicon_bits']} bits**

Short Japanese facts and questions are compiled into the Phase 18c-1 product graph for speed, concentration, and unit-price problems. This is a controlled language bridge with fixed syntax and units, not free Japanese understanding or high-school intelligence.
"""


def main() -> None:
    payload = run()
    Path("results").mkdir(exist_ok=True)
    Path("results/phase18c2.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    Path("results/phase18c2.md").write_text(markdown(payload), encoding="utf-8")
    print(markdown(payload), end="")
    if not payload["all_theorem_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
