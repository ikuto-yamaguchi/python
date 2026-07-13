from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
import json
from pathlib import Path
import re
from typing import Mapping, Sequence

from .phase18b7_shared_linear_constraint_graph import (
    ConstraintGraph,
    NonIdentifiableConstraintError,
    Solution,
    verify,
)
from .phase18b9_raw_japanese_span_schema import (
    COUNT_TEMPLATES,
    QUESTION_TEMPLATES,
    RATE_TEMPLATES,
    ROLES,
    VALUE_TEMPLATES,
    Demonstration,
    Fact,
    ParsedProblem,
    RawSchemaModel,
    induce as induce_exact_schema,
    parse,
)

Q = Fraction
STOPWORDS = ("による", "になる", "である", "だった", "ある", "から", "は", "を", "の", "に", "で", "だ")
PLACEHOLDERS = ("<E>", "<N>", "<U>")

EXT_COUNT = (
    "{x}と{y}の全部を数えると{n}{unit}だった",
    "{x}と{y}をもう一度合わせると{n}{unit}になる",
    "{x}と{y}の総数を確認すると{n}{unit}だ",
)
EXT_RATE = (
    "{entity}の単価としては{rate}{unit}である",
    "{entity}一つ分に必要な値は{rate}{unit}だ",
    "{entity}ごとに加わる量は{rate}{unit}になる",
)
EXT_VALUE = (
    "最終的な売上は{total}{unit}だった",
    "{x}と{y}から得た全体量は{total}{unit}だ",
    "計算した合計値は{total}{unit}になる",
)

NOVEL_COUNT = (
    "{x}と{y}を全部まとめると{n}{unit}になった",
    "{x}と{y}を合わせると最終的に{n}{unit}だった",
    "{x}と{y}について総数を調べると{n}{unit}である",
)
NOVEL_RATE = (
    "{entity}の単価を使うと{rate}{unit}になる",
    "{entity}一つ分だけなら{rate}{unit}である",
    "{entity}ごとに必要な値は{rate}{unit}だ",
)
NOVEL_VALUE = (
    "総売上の結果は{total}{unit}だった",
    "最終の全体量として{total}{unit}になった",
    "求めた合計値は{total}{unit}である",
)


class NonIdentifiableAnchorError(ValueError):
    pass


@dataclass(frozen=True)
class AnchorModel:
    anchors: tuple[tuple[str, str], ...]
    count_program: str
    value_program: str

    @property
    def bits(self) -> int:
        payload = {"anchors": self.anchors, "count_program": self.count_program, "value_program": self.value_program}
        return len(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()) * 8

    def role_for(self, fact: Fact) -> str | None:
        matched_roles = {role for anchor, role in self.anchors if anchor in fact.cue}
        if len(matched_roles) != 1:
            return None
        role = next(iter(matched_roles))
        if role == "RATE" and len(fact.entities) != 1:
            return None
        if role != "RATE" and len(fact.entities) == 1:
            return None
        return role

    def compile_parsed(self, parsed: ParsedProblem) -> ConstraintGraph:
        cue_roles = []
        for fact in parsed.facts:
            role = self.role_for(fact)
            if role is None:
                raise NonIdentifiableConstraintError("zero, conflicting, or structurally invalid anchor evidence")
            cue_roles.append((fact.cue, role))
        return RawSchemaModel(tuple(cue_roles), self.count_program, self.value_program).compile_parsed(parsed)

    def answer_parsed(self, parsed: ParsedProblem) -> Solution | None:
        cue_roles = []
        for fact in parsed.facts:
            role = self.role_for(fact)
            if role is None:
                return None
            cue_roles.append((fact.cue, role))
        return RawSchemaModel(tuple(cue_roles), self.count_program, self.value_program).answer_parsed(parsed)

    def answer(self, text: str) -> Solution | None:
        try:
            return self.answer_parsed(parse(text))
        except ValueError:
            return None


def _render_custom(
    entities: tuple[str, str],
    counts: tuple[int, int],
    rates: tuple[int, int],
    count_unit: str,
    value_unit: str,
    count_template: str,
    rate_templates: tuple[str, str],
    value_template: str,
    question_index: int,
    order: Sequence[int],
    distractor: str = "背景説明は数値を含まない",
) -> Demonstration:
    x, y = entities
    nx, ny = counts
    rx, ry = rates
    clauses = (
        count_template.format(x=x, y=y, n=nx + ny, unit=count_unit),
        rate_templates[0].format(entity=x, rate=rx, unit=value_unit),
        rate_templates[1].format(entity=y, rate=ry, unit=value_unit),
        value_template.format(x=x, y=y, total=rx * nx + ry * ny, unit=value_unit),
    )
    question = QUESTION_TEMPLATES[question_index].format(x=x, y=y, unit=count_unit)
    return Demonstration("。".join((distractor,) + tuple(clauses[index] for index in order) + (question,)) + "。", counts)


def calibration() -> tuple[Demonstration, ...]:
    rows: list[Demonstration] = []
    domains = (
        ("A券", "B券", (6, 9), (700, 300), "枚", "円"),
        ("白箱", "黒箱", (4, 11), (20, 60), "個", "g"),
        ("小型車", "大型車", (12, 3), (4, 8), "台", "本"),
        ("赤札", "青札", (8, 5), (90, 140), "枚", "円"),
        ("短答", "長答", (14, 6), (3, 7), "回", "点"),
        ("軽袋", "重袋", (7, 4), (50, 180), "個", "g"),
        ("午前枠", "午後枠", (9, 7), (400, 900), "人", "円"),
        ("正答", "誤答", (15, 5), (4, -1), "回", "点"),
        ("短冊", "長冊", (5, 8), (30, 100), "冊", "円"),
    )
    for index, (x, y, counts, rates, count_unit, value_unit) in enumerate(domains):
        group = index // 3
        variant = index % 3
        count_template = COUNT_TEMPLATES[0]
        rate_x = RATE_TEMPLATES[0]
        rate_y = RATE_TEMPLATES[1]
        value_template = VALUE_TEMPLATES[0]
        if group == 0:
            count_template = EXT_COUNT[variant]
        elif group == 1:
            rate_x = EXT_RATE[variant]
        else:
            value_template = EXT_VALUE[variant]
        rows.append(
            _render_custom(
                (x, y), counts, rates, count_unit, value_unit,
                count_template, (rate_x, rate_y), value_template,
                variant, (variant, (variant + 1) % 4, (variant + 3) % 4, (variant + 2) % 4),
            )
        )
    return tuple(rows)


@lru_cache(maxsize=1)
def _base_exact() -> tuple[RawSchemaModel, dict[str, int]]:
    return induce_exact_schema()


def _expected_answer(row: Demonstration) -> tuple[Q, Q]:
    return tuple(Q(value) for value in row.answer)


def induce_extension_roles(base: RawSchemaModel) -> tuple[tuple[tuple[str, str], ...], dict[str, int]]:
    base_roles = dict(base.cue_roles)
    learned: list[tuple[str, str]] = []
    trials = 0
    for row in calibration():
        parsed = parse(row.text)
        unknown = sorted({fact.cue for fact in parsed.facts if fact.cue not in base_roles})
        if len(unknown) != 1:
            raise NonIdentifiableAnchorError(f"expected one new span, got {unknown}")
        cue = unknown[0]
        surviving = []
        for role in ROLES:
            trials += 1
            candidate = RawSchemaModel(base.cue_roles + ((cue, role),), base.count_program, base.value_program)
            answer = candidate.answer_parsed(parsed)
            if answer is None:
                continue
            values = dict(answer.values)
            if (values[parsed.entities[0]], values[parsed.entities[1]]) == _expected_answer(row):
                surviving.append(role)
        if len(surviving) != 1:
            raise NonIdentifiableAnchorError(f"span={cue} surviving={surviving}")
        learned.append((cue, surviving[0]))
    if len(dict(learned)) != len(learned):
        raise NonIdentifiableAnchorError("duplicate extension span")
    return tuple(learned), {"extension_spans": len(learned), "role_trials": trials}


def _content_chunks(cue: str) -> tuple[str, ...]:
    text = cue
    for placeholder in PLACEHOLDERS:
        text = text.replace(placeholder, "|")
    for stopword in sorted(STOPWORDS, key=len, reverse=True):
        text = text.replace(stopword, "|")
    return tuple(chunk for chunk in text.split("|") if len(chunk) >= 2)


def _longest_common_substrings(left: str, right: str) -> tuple[str, ...]:
    best_length = 0
    best: set[str] = set()
    for i in range(len(left)):
        for j in range(len(right)):
            length = 0
            while i + length < len(left) and j + length < len(right) and left[i + length] == right[j + length]:
                length += 1
            if length > best_length:
                best_length = length
                best = {left[i : i + length]} if length else set()
            elif length == best_length and length:
                best.add(left[i : i + length])
    return tuple(sorted(best))


def _anchor_candidates(cue_roles: Sequence[tuple[str, str]]) -> tuple[tuple[str, str, frozenset[int]], ...]:
    chunks = tuple(_content_chunks(cue) for cue, _ in cue_roles)
    raw: list[tuple[str, str, frozenset[int]]] = []
    for left_index, (_, left_role) in enumerate(cue_roles):
        for right_index in range(left_index + 1, len(cue_roles)):
            _, right_role = cue_roles[right_index]
            if left_role != right_role:
                continue
            for left_chunk in chunks[left_index]:
                for right_chunk in chunks[right_index]:
                    for anchor in _longest_common_substrings(left_chunk, right_chunk):
                        if len(anchor) < 2:
                            continue
                        if not (re.search(r"[一-龥]", anchor) or anchor == "ごと"):
                            continue
                        coverage = frozenset(index for index, (cue, role) in enumerate(cue_roles) if role == left_role and anchor in cue)
                        if len(coverage) < 2:
                            continue
                        if any(anchor in cue for cue, role in cue_roles if role != left_role):
                            continue
                        raw.append((anchor, left_role, coverage))
    best_by_signature: dict[tuple[str, frozenset[int]], str] = {}
    for anchor, role, coverage in raw:
        key = (role, coverage)
        incumbent = best_by_signature.get(key)
        if incumbent is None or (len(anchor.encode()), anchor) < (len(incumbent.encode()), incumbent):
            best_by_signature[key] = anchor
    return tuple(sorted((anchor, role, coverage) for (role, coverage), anchor in best_by_signature.items()))


def induce_anchors(cue_roles: Sequence[tuple[str, str]]) -> tuple[tuple[tuple[str, str], ...], dict[str, int]]:
    candidates = _anchor_candidates(cue_roles)
    target_mask = (1 << len(cue_roles)) - 1
    valid: list[tuple[tuple[int, int], tuple[tuple[str, str], ...]]] = []
    for subset in range(1 << len(candidates)):
        coverage_mask = 0
        chosen: list[tuple[str, str]] = []
        byte_cost = 0
        for index, (anchor, role, coverage) in enumerate(candidates):
            if not (subset >> index) & 1:
                continue
            chosen.append((anchor, role))
            byte_cost += len(anchor.encode())
            for cue_index in coverage:
                coverage_mask |= 1 << cue_index
        if coverage_mask == target_mask:
            valid.append(((byte_cost, len(chosen)), tuple(sorted(chosen))))
    if not valid:
        raise NonIdentifiableAnchorError("no anchor cover")
    best_score = min(score for score, _ in valid)
    best = {chosen for score, chosen in valid if score == best_score}
    if len(best) != 1:
        raise NonIdentifiableAnchorError(f"minimum covers={len(best)}")
    selected = next(iter(best))
    return selected, {
        "anchor_candidates": len(candidates),
        "anchor_subsets": 1 << len(candidates),
        "valid_covers": len(valid),
        "selected_anchors": len(selected),
        "anchor_utf8_bytes": sum(len(anchor.encode()) for anchor, _ in selected),
    }


@lru_cache(maxsize=1)
def induce() -> tuple[AnchorModel, dict[str, int], tuple[tuple[str, str], ...]]:
    base, base_fit = _base_exact()
    extensions, extension_fit = induce_extension_roles(base)
    cue_roles = base.cue_roles + extensions
    anchors, anchor_fit = induce_anchors(cue_roles)
    return AnchorModel(anchors, base.count_program, base.value_program), {**base_fit, **extension_fit, **anchor_fit}, cue_roles


def heldout() -> tuple[Demonstration, ...]:
    specifications = (
        (("普通券", "優待券"), (8, 6), (800, 300), "枚", "円"),
        (("白鳥", "亀"), (10, 5), (2, 4), "匹", "本"),
        (("軽箱", "重箱"), (7, 9), (40, 90), "個", "g"),
        (("短答", "長答"), (12, 4), (3, 8), "回", "点"),
        (("午前車", "午後車"), (9, 3), (4, 6), "台", "本"),
        (("小皿", "大皿"), (11, 5), (100, 260), "枚", "円"),
    )
    rows: list[Demonstration] = []
    for index, (x, y, counts, rates, count_unit, value_unit) in enumerate(specifications):
        count_index = index % 3
        rate_left = (index + 1) % 3
        rate_right = (index + 2) % 3
        value_index = (index + 2) % 3
        rows.append(
            _render_custom(
                (x, y), counts, rates, count_unit, value_unit,
                NOVEL_COUNT[count_index], (NOVEL_RATE[rate_left], NOVEL_RATE[rate_right]), NOVEL_VALUE[value_index],
                index % 3, (2, 0, 3, 1), "初見の言い回しを含む",
            )
        )
        rows.append(
            _render_custom(
                (y, x), (counts[1], counts[0]), (rates[1], rates[0]), count_unit, value_unit,
                NOVEL_COUNT[(count_index + 1) % 3],
                (NOVEL_RATE[(rate_right + 1) % 3], NOVEL_RATE[(rate_left + 1) % 3]),
                NOVEL_VALUE[(value_index + 1) % 3],
                (index + 1) % 3, (1, 3, 0, 2), "別の語順でも条件は同じ",
            )
        )
    return tuple(rows)


def evaluate(model: AnchorModel) -> tuple[float, float, float]:
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


def exact_span_baseline_coverage() -> float:
    base, _ = _base_exact()
    return sum(base.answer(row.text) is not None for row in heldout()) / len(heldout())


def conflict_unknown_and_arity_controls(model: AnchorModel) -> dict[str, bool]:
    row = heldout()[0]
    parsed = parse(row.text)
    count_fact = next(fact for fact in parsed.facts if len(fact.entities) == 2)
    conflict = row.text.replace(count_fact.surface, count_fact.surface.replace("全部", "全部の合計値"))
    unknown = row.text.replace(count_fact.surface, count_fact.surface.replace("全部", "二種類をまとめた結果"))
    arity = row.text.replace(count_fact.surface, re.sub(r"を全部まとめると", "の単価情報では", count_fact.surface))
    return {
        "conflicting_anchors": model.answer(conflict) is None,
        "no_known_anchor": model.answer(unknown) is None,
        "rate_anchor_wrong_arity": model.answer(arity) is None,
    }


def unseen_synonym_without_anchor_abstains(model: AnchorModel) -> bool:
    row = heldout()[0]
    parsed = parse(row.text)
    count_fact = next(fact for fact in parsed.facts if len(fact.entities) == 2)
    synonym = row.text.replace(count_fact.surface, count_fact.surface.replace("全部", "総計対象を"))
    return model.answer(synonym) is None


def anchor_ablation_reduces_coverage(model: AnchorModel) -> bool:
    full = evaluate(model)[1]
    reduced_coverages = []
    for index in range(len(model.anchors)):
        reduced = AnchorModel(model.anchors[:index] + model.anchors[index + 1 :], model.count_program, model.value_program)
        reduced_coverages.append(evaluate(reduced)[1])
    return full == 1.0 and all(coverage < full for coverage in reduced_coverages)


def tampered_solution_is_rejected(model: AnchorModel) -> bool:
    parsed = parse(heldout()[0].text)
    answer = model.answer_parsed(parsed)
    assert answer is not None
    tampered = Solution(answer.kind, tuple(reversed(answer.values)), answer.interval, answer.proof)
    return not verify(model.compile_parsed(parsed), tampered)


def run() -> dict[str, object]:
    model, fit, cue_roles = induce()
    accuracy, coverage, verified_rate = evaluate(model)
    expected_anchors = {
        ("全部", "COUNT"), ("合わせると", "COUNT"), ("総数", "COUNT"),
        ("単価", "RATE"), ("一つ分", "RATE"), ("ごと", "RATE"),
        ("売上", "VALUE"), ("全体量", "VALUE"), ("合計", "VALUE"),
    }
    controls = conflict_unknown_and_arity_controls(model)
    exact_bits = len(json.dumps(cue_roles, ensure_ascii=False, separators=(",", ":")).encode()) * 8
    checks = {
        "unique_base_schema": fit["errors"] == 0 and fit["second"] > 0,
        "all_extension_roles_unique": fit["extension_spans"] == 9 and fit["role_trials"] == 27,
        "unique_minimum_anchor_cover": set(model.anchors) == expected_anchors and fit["selected_anchors"] == 9,
        "heldout_accuracy": accuracy == 1.0,
        "heldout_coverage": coverage == 1.0,
        "proof_verification": verified_rate == 1.0,
        "exact_span_baseline_zero": exact_span_baseline_coverage() == 0.0,
        "negative_controls": all(controls.values()),
        "unseen_synonym_without_anchor_abstains": unseen_synonym_without_anchor_abstains(model),
        "anchor_ablation": anchor_ablation_reduces_coverage(model),
        "tampered_solution_rejected": tampered_solution_is_rejected(model),
    }
    return {
        "campaign": {
            "name": "phase18b10-mdl-paraphrase-anchors-c2",
            "generalization_type": "unseen full-span recombination around learned character anchors",
            "fully_unseen_synonyms": False,
            "fixed_morpheme_splitter": True,
            "public_examples": 0,
        },
        "induction": {
            **fit,
            "anchors": [list(item) for item in model.anchors],
            "count_program": model.count_program,
            "value_program": model.value_program,
        },
        "evaluation": {
            "calibration_examples": len(calibration()),
            "heldout_examples": len(heldout()),
            "heldout_domains": len(heldout()) // 2,
            "accuracy": accuracy,
            "coverage": coverage,
            "verified_proof_rate": verified_rate,
            "exact_span_baseline_coverage": exact_span_baseline_coverage(),
        },
        "negative_controls": controls,
        "resources": {
            "anchor_model_bits": model.bits,
            "exact_cue_map_bits": exact_bits,
            "compression_ratio_exact_over_anchor": exact_bits / model.bits,
            "source_bytes": len(Path(__file__).read_bytes()),
            "phase18b7_and_phase18b9_source_excluded": True,
            "python_runtime_included": False,
        },
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {
            "surface_morpheme_recombination": all(checks.values()),
            "semantic_synonym_understanding": False,
            "free_japanese": False,
            "high_school_intelligence": False,
        },
        "limitations": [
            "Positive held-out paraphrases contain a learned discriminative character anchor.",
            "Completely unseen synonyms without an anchor abstain.",
            "The morpheme splitter and candidate-anchor rules are fixed.",
            "The same two-entity count-plus-weighted-total family and three question forms remain.",
            "This is surface compositional transfer, not broad semantic language understanding.",
        ],
    }


def markdown(payload: Mapping[str, object]) -> str:
    induction = payload["induction"]
    evaluation = payload["evaluation"]
    resources = payload["resources"]
    return f"""# Phase 18b-10 results: MDL paraphrase anchors

- Extension spans / role trials: **{induction['extension_spans']} / {induction['role_trials']}**
- Anchor candidates / subsets / valid covers: **{induction['anchor_candidates']} / {induction['anchor_subsets']} / {induction['valid_covers']}**
- Selected anchors: **{induction['selected_anchors']}**, UTF-8 content **{induction['anchor_utf8_bytes']} bytes**
- Held-out unseen full spans: **{evaluation['heldout_examples']}** across **{evaluation['heldout_domains']}** domains
- Accuracy / coverage / proof: **{100 * evaluation['accuracy']:.1f}% / {100 * evaluation['coverage']:.1f}% / {100 * evaluation['verified_proof_rate']:.1f}%**
- Exact-span baseline coverage: **{100 * evaluation['exact_span_baseline_coverage']:.1f}%**
- Anchor model / exact cue-map bits: **{resources['anchor_model_bits']} / {resources['exact_cue_map_bits']}**

The model transfers to unseen complete relation spans only when they recombine a learned pure character anchor. Anchor conflicts, absent anchors, wrong structural arity, and completely unseen synonyms abstain. This is controlled surface-morpheme recombination, not semantic synonym understanding or high-school intelligence.
"""


def main() -> None:
    payload = run()
    Path("results").mkdir(exist_ok=True)
    Path("results/phase18b10.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    Path("results/phase18b10.md").write_text(markdown(payload), encoding="utf-8")
    print(markdown(payload), end="")


if __name__ == "__main__":
    main()
