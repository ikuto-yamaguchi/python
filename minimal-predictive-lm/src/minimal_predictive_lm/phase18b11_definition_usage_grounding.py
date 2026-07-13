from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
import json
from pathlib import Path
import re
from typing import Mapping, Sequence

from .phase18b7_shared_linear_constraint_graph import Solution, verify
from .phase18b9_raw_japanese_span_schema import (
    COUNT_PROGRAMS,
    QUESTION_TEMPLATES,
    ROLES,
    VALUE_PROGRAMS,
    Demonstration,
    ParsedProblem,
    RawSchemaModel,
    parse,
)

Q = Fraction
TOKENS = ("ゼルク", "ノヴァ", "ミルテ", "ラゴン", "セフィ", "トゥラ")
CONCEPTS = {"総数": "COUNT", "個別係数": "RATE", "全体結果": "VALUE"}
PREVIOUS_ANCHORS = ("全部", "合わせると", "総数", "単価", "一つ分", "ごと", "売上", "全体量", "合計")

DIRECT_RE = re.compile(r'^語「([^」]+)」は概念「([^」]+)」である$')
NOT_RE = re.compile(r'^語「([^」]+)」は概念「([^」]+)」ではない$')
ALIAS_RE = re.compile(r'^語「([^」]+)」は語「([^」]+)」と同じである$')
DIFF_RE = re.compile(r'^語「([^」]+)」と語「([^」]+)」は異なる$')


class NonIdentifiableDefinitionError(ValueError):
    pass


@dataclass(frozen=True)
class SemanticConstraint:
    kind: str
    left: str
    right: str


@dataclass(frozen=True)
class DefinitionGroundedModel:
    token_roles: tuple[tuple[str, str], ...]
    count_program: str
    value_program: str

    @property
    def bits(self) -> int:
        payload = {
            "token_roles": self.token_roles,
            "count_program": self.count_program,
            "value_program": self.value_program,
        }
        return len(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()) * 8

    def role_for_cue(self, cue: str) -> str | None:
        roles = dict(self.token_roles)
        matched = tuple(token for token in roles if token in cue)
        if len(matched) != 1:
            return None
        return roles[matched[0]]

    def compile_parsed(self, parsed: ParsedProblem):
        cue_roles = []
        for fact in parsed.facts:
            role = self.role_for_cue(fact.cue)
            if role is None:
                raise NonIdentifiableDefinitionError("each fact must contain exactly one grounded token")
            cue_roles.append((fact.cue, role))
        exact = RawSchemaModel(tuple(cue_roles), self.count_program, self.value_program)
        return exact.compile_parsed(parsed)

    def answer_parsed(self, parsed: ParsedProblem) -> Solution | None:
        try:
            cue_roles = []
            for fact in parsed.facts:
                role = self.role_for_cue(fact.cue)
                if role is None:
                    return None
                cue_roles.append((fact.cue, role))
            exact = RawSchemaModel(tuple(cue_roles), self.count_program, self.value_program)
            return exact.answer_parsed(parsed)
        except (ValueError, NonIdentifiableDefinitionError):
            return None

    def answer(self, text: str) -> Solution | None:
        try:
            return self.answer_parsed(parse(text))
        except ValueError:
            return None


def parse_definition(text: str) -> SemanticConstraint:
    for regex, kind in (
        (NOT_RE, "NOT_ROLE"),
        (DIRECT_RE, "ROLE"),
        (ALIAS_RE, "SAME"),
        (DIFF_RE, "DIFFERENT"),
    ):
        match = regex.fullmatch(text)
        if not match:
            continue
        left, right = match.groups()
        if kind in {"ROLE", "NOT_ROLE"}:
            if left not in TOKENS or right not in CONCEPTS:
                raise ValueError("unknown token or concept")
            right = CONCEPTS[right]
        elif left not in TOKENS or right not in TOKENS or left == right:
            raise ValueError("invalid token relation")
        return SemanticConstraint(kind, left, right)
    raise ValueError("unsupported definition form")


def definition_texts() -> tuple[str, ...]:
    return (
        '語「ゼルク」は概念「総数」である',
        '語「ノヴァ」は語「ゼルク」と同じである',
        '語「ラゴン」は語「ミルテ」と同じである',
        '語「トゥラ」は語「セフィ」と同じである',
        '語「ミルテ」と語「セフィ」は異なる',
        '語「ミルテ」は概念「総数」ではない',
        '語「セフィ」は概念「総数」ではない',
    )


def semantic_constraints(texts: Sequence[str] | None = None) -> tuple[SemanticConstraint, ...]:
    return tuple(parse_definition(text) for text in (definition_texts() if texts is None else texts))


def satisfies(mapping: Mapping[str, str], constraints: Sequence[SemanticConstraint]) -> bool:
    for item in constraints:
        if item.kind == "ROLE" and mapping[item.left] != item.right:
            return False
        if item.kind == "NOT_ROLE" and mapping[item.left] == item.right:
            return False
        if item.kind == "SAME" and mapping[item.left] != mapping[item.right]:
            return False
        if item.kind == "DIFFERENT" and mapping[item.left] == mapping[item.right]:
            return False
    return True


def _render(
    entities: tuple[str, str],
    counts: tuple[int, int],
    rates: tuple[int, int],
    count_unit: str,
    value_unit: str,
    count_token: str,
    rate_tokens: tuple[str, str],
    value_token: str,
    question_index: int,
    order: Sequence[int],
    distractor: str,
) -> Demonstration:
    x, y = entities
    nx, ny = counts
    rx, ry = rates
    clauses = (
        f"{x}と{y}について符号{count_token}は{nx + ny}{count_unit}だ",
        f"{x}に対する符号{rate_tokens[0]}は{rx}{value_unit}だ",
        f"{y}に対する符号{rate_tokens[1]}は{ry}{value_unit}だ",
        f"符号{value_token}として{rx * nx + ry * ny}{value_unit}を記録した",
    )
    question = QUESTION_TEMPLATES[question_index].format(x=x, y=y, unit=count_unit)
    sentences = (distractor,) + tuple(clauses[index] for index in order) + (question,)
    return Demonstration("。".join(sentences) + "。", counts)


def usage_examples() -> tuple[Demonstration, ...]:
    specifications = (
        (("大人券", "子供券"), (7, 10), (900, 500), "枚", "円", 0, (2, 0, 3, 1)),
        (("白箱", "黒箱"), (4, 9), (30, 70), "個", "g", 1, (3, 1, 0, 2)),
        (("普通車", "大型車"), (11, 5), (4, 6), "台", "本", 2, (1, 3, 2, 0)),
        (("正答", "誤答"), (13, 7), (5, -2), "回", "点", 0, (0, 2, 1, 3)),
    )
    return tuple(
        _render(entities, counts, rates, count_unit, value_unit, "ゼルク", ("ミルテ", "ミルテ"), "セフィ", question, order, "未知語の使い方を観測する")
        for entities, counts, rates, count_unit, value_unit, question, order in specifications
    )


def heldout() -> tuple[Demonstration, ...]:
    specifications = (
        (("ニワトリ", "カメ"), (13, 7), (2, 4), "匹", "本"),
        (("学生券", "一般券"), (12, 5), (600, 1200), "枚", "円"),
        (("軽箱", "重箱"), (9, 4), (3, 8), "個", "kg"),
        (("一等賞", "二等賞"), (6, 11), (10, 4), "本", "点"),
        (("小皿", "大皿"), (14, 3), (120, 350), "枚", "円"),
        (("短時間", "長時間"), (8, 5), (15, 40), "回", "分"),
    )
    rows = []
    for index, (entities, counts, rates, count_unit, value_unit) in enumerate(specifications):
        rows.append(
            _render(
                entities, counts, rates, count_unit, value_unit,
                "ノヴァ", ("ラゴン", "ラゴン"), "トゥラ",
                index % 3, (3, 1, 0, 2), "定義から得た別名だけを使う",
            )
        )
        rows.append(
            _render(
                (entities[1], entities[0]), (counts[1], counts[0]), (rates[1], rates[0]),
                count_unit, value_unit, "ノヴァ", ("ラゴン", "ラゴン"), "トゥラ",
                (index + 1) % 3, (2, 0, 3, 1), "語順と対象順を変えて検証する",
            )
        )
    return tuple(rows)


def _candidate_models(
    definitions: Sequence[SemanticConstraint],
    examples: Sequence[Demonstration],
) -> tuple[list[DefinitionGroundedModel], dict[str, int]]:
    symbolic = []
    total = 0
    for assignment in product(ROLES, repeat=len(TOKENS)):
        mapping = dict(zip(TOKENS, assignment))
        for count_program in COUNT_PROGRAMS:
            for value_program in VALUE_PROGRAMS:
                total += 1
                if satisfies(mapping, definitions):
                    symbolic.append(DefinitionGroundedModel(tuple(zip(TOKENS, assignment)), count_program, value_program))

    survivors = []
    best_error = len(examples) + 1
    second_error = len(examples) + 1
    best_models = []
    parsed_examples = tuple(parse(row.text) for row in examples)
    for model in symbolic:
        error = 0
        for parsed, row in zip(parsed_examples, examples):
            answer = model.answer_parsed(parsed)
            if answer is None:
                error += 1
                continue
            values = dict(answer.values)
            error += (values[parsed.entities[0]], values[parsed.entities[1]]) != tuple(Q(value) for value in row.answer)
        if error == 0:
            survivors.append(model)
        if error < best_error:
            second_error = best_error
            best_error = error
            best_models = [model]
        elif error == best_error:
            best_models.append(model)
        elif error < second_error:
            second_error = error

    return survivors, {
        "all_hypotheses": total,
        "after_definition_constraints": len(symbolic),
        "zero_error_after_usage": len(survivors),
        "best_error": best_error,
        "second_error": second_error,
        "best_model_multiplicity": len(best_models),
    }


def induce(
    texts: Sequence[str] | None = None,
    examples: Sequence[Demonstration] | None = None,
) -> tuple[DefinitionGroundedModel, dict[str, int]]:
    constraints = semantic_constraints(texts)
    survivors, fit = _candidate_models(constraints, tuple(usage_examples() if examples is None else examples))
    if len(survivors) != 1:
        raise NonIdentifiableDefinitionError(f"survivors={len(survivors)}")
    return survivors[0], fit


def evaluate(model: DefinitionGroundedModel) -> tuple[float, float, float]:
    correct = covered = verified_count = 0
    rows = heldout()
    for row in rows:
        parsed = parse(row.text)
        answer = model.answer_parsed(parsed)
        if answer is None:
            continue
        covered += 1
        values = dict(answer.values)
        correct += (values[parsed.entities[0]], values[parsed.entities[1]]) == tuple(Q(value) for value in row.answer)
        verified_count += verify(model.compile_parsed(parsed), answer)
    total = len(rows)
    return correct / total, covered / total, verified_count / total


def definitions_alone_are_ambiguous() -> bool:
    constraints = semantic_constraints()
    survivors, fit = _candidate_models(constraints, ())
    return fit["after_definition_constraints"] == 24 and len(survivors) == 24


def unanchored_alias_cycle_is_rejected() -> bool:
    texts = (
        '語「ゼルク」は語「ノヴァ」と同じである',
        '語「ノヴァ」は語「ゼルク」と同じである',
    )
    try:
        induce(texts, ())
    except NonIdentifiableDefinitionError:
        return True
    return False


def contradictory_definitions_are_rejected() -> bool:
    texts = definition_texts() + ('語「ゼルク」は概念「総数」ではない',)
    try:
        induce(texts, usage_examples())
    except NonIdentifiableDefinitionError:
        return True
    return False


def unknown_and_ambiguous_tokens_abstain(model: DefinitionGroundedModel) -> bool:
    row = heldout()[0]
    unknown = row.text.replace("ノヴァ", "キルム")
    ambiguous = row.text.replace("ノヴァ", "ノヴァトゥラ")
    return model.answer(unknown) is None and model.answer(ambiguous) is None


def exact_usage_surface_memorizer_coverage() -> float:
    known = {fact.cue for row in usage_examples() for fact in parse(row.text).facts}
    rows = heldout()
    covered = 0
    for row in rows:
        cues = {fact.cue for fact in parse(row.text).facts}
        covered += cues.issubset(known)
    return covered / len(rows)


def no_previous_anchor_overlap() -> bool:
    for row in usage_examples() + heldout():
        parsed = parse(row.text)
        for fact in parsed.facts:
            if any(anchor in fact.cue for anchor in PREVIOUS_ANCHORS):
                return False
    return True


def negative_definition_is_causally_used() -> bool:
    without_negation = tuple(text for text in definition_texts() if "ではない" not in text)
    constraints = semantic_constraints(without_negation)
    _, fit = _candidate_models(constraints, ())
    return fit["after_definition_constraints"] > 24


def counterfactual_role_swap_fails(model: DefinitionGroundedModel) -> bool:
    swapped = DefinitionGroundedModel(
        tuple((token, {"RATE": "VALUE", "VALUE": "RATE"}.get(role, role)) for token, role in model.token_roles),
        model.count_program,
        model.value_program,
    )
    return all(swapped.answer(row.text) is None for row in heldout())


def tampered_solution_is_rejected(model: DefinitionGroundedModel) -> bool:
    parsed = parse(heldout()[0].text)
    answer = model.answer_parsed(parsed)
    assert answer is not None
    tampered = Solution(answer.kind, tuple(reversed(answer.values)), answer.interval, answer.proof)
    return not verify(model.compile_parsed(parsed), tampered)


def run() -> dict[str, object]:
    model, fit = induce()
    accuracy, coverage, verified_rate = evaluate(model)
    expected = {
        "ゼルク": "COUNT", "ノヴァ": "COUNT",
        "ミルテ": "RATE", "ラゴン": "RATE",
        "セフィ": "VALUE", "トゥラ": "VALUE",
    }
    checks = {
        "definitions_leave_real_ambiguity": definitions_alone_are_ambiguous(),
        "usage_resolves_unique_model": fit["zero_error_after_usage"] == 1,
        "correct_token_roles": dict(model.token_roles) == expected,
        "correct_equation_programs": (model.count_program, model.value_program) == ("SUM", "WEIGHTED_SUM"),
        "heldout_accuracy": accuracy == 1.0,
        "heldout_coverage": coverage == 1.0,
        "proof_verification": verified_rate == 1.0,
        "unanchored_cycle_rejected": unanchored_alias_cycle_is_rejected(),
        "contradiction_rejected": contradictory_definitions_are_rejected(),
        "unknown_ambiguous_tokens_abstain": unknown_and_ambiguous_tokens_abstain(model),
        "usage_surface_memorizer_zero": exact_usage_surface_memorizer_coverage() == 0.0,
        "no_previous_anchor_overlap": no_previous_anchor_overlap(),
        "negative_definition_used": negative_definition_is_causally_used(),
        "counterfactual_role_swap_fails": counterfactual_role_swap_fails(model),
        "tampered_solution_rejected": tampered_solution_is_rejected(model),
    }
    return {
        "campaign": {
            "name": "phase18b11-definition-and-usage-grounding-c1",
            "nonce_tokens": len(TOKENS),
            "fixed_definition_metalanguage": True,
            "shared_characters_with_previous_anchors": False,
            "shared_solver": "phase18b7",
            "raw_parser": "phase18b9",
            "public_examples": 0,
        },
        "induction": {
            **fit,
            "definition_statements": len(definition_texts()),
            "usage_examples": len(usage_examples()),
            "token_roles": [list(item) for item in model.token_roles],
            "count_program": model.count_program,
            "value_program": model.value_program,
        },
        "evaluation": {
            "heldout_examples": len(heldout()),
            "heldout_domains": len(heldout()) // 2,
            "accuracy": accuracy,
            "coverage": coverage,
            "verified_proof_rate": verified_rate,
            "exact_usage_surface_memorizer_coverage": exact_usage_surface_memorizer_coverage(),
        },
        "resources": {
            "learned_model_bits": model.bits,
            "source_bytes": len(Path(__file__).read_bytes()),
            "phase18b7_and_phase18b9_source_excluded": True,
            "python_runtime_included": False,
        },
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {
            "controlled_definition_contrast_usage_grounding": all(checks.values()),
            "open_dictionary_learning": False,
            "free_japanese_definition_understanding": False,
            "broad_semantic_similarity": False,
            "high_school_intelligence": False,
        },
        "limitations": [
            "The definition metalanguage and three canonical role names are fixed.",
            "Usage examples remain within the two-entity count-plus-weighted-total family.",
            "Nonce-token boundaries are explicit substrings rather than autonomously segmented words.",
            "The learner does not infer arbitrary dictionary definitions, metaphor, polysemy, or commonsense meaning.",
            "Sentence splitting, quantity recognition, and question forms remain fixed by Phase 18b-9.",
        ],
    }


def markdown(payload: Mapping[str, object]) -> str:
    induction = payload["induction"]
    evaluation = payload["evaluation"]
    resources = payload["resources"]
    return f"""# Phase 18b-11 results: definition, contrast, and usage grounding

- All mapping/program hypotheses: **{induction['all_hypotheses']}**
- Surviving after definitions/contrast only: **{induction['after_definition_constraints']}**
- Zero-error after usage examples: **{induction['zero_error_after_usage']}**
- Definitions / usage examples: **{induction['definition_statements']} / {induction['usage_examples']}**
- Held-out examples / domains: **{evaluation['heldout_examples']} / {evaluation['heldout_domains']}**
- Accuracy / coverage / verified proof: **{100 * evaluation['accuracy']:.1f}% / {100 * evaluation['coverage']:.1f}% / {100 * evaluation['verified_proof_rate']:.1f}%**
- Exact usage-surface memorizer coverage: **{100 * evaluation['exact_usage_surface_memorizer_coverage']:.1f}%**
- Learned model payload: **{resources['learned_model_bits']} bits**

Definitions and contrasts deliberately leave RATE/VALUE exchangeable; only correct-answer usage examples resolve the remaining ambiguity. Held-out problems use aliases absent from the usage examples and share no Phase 18b-10 anchors. This is controlled definitional grounding, not unrestricted Japanese dictionary understanding or high-school intelligence.
"""


def main() -> None:
    payload = run()
    Path("results").mkdir(exist_ok=True)
    Path("results/phase18b11.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    Path("results/phase18b11.md").write_text(markdown(payload), encoding="utf-8")
    print(markdown(payload), end="")
    if not payload["all_theorem_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
