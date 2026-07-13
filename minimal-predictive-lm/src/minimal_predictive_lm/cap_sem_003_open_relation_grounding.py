from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import marshal
from pathlib import Path
import re
from typing import Mapping, Sequence
import zlib

from .cap_sem_001_relational_meaning import (
    QUERY_GROUPS,
    STATEMENT_GROUPS,
    LearnedMeaning,
    Record,
    build_heldout_records,
    build_training_records,
    learn_meaning,
    predict,
)
from .cap_sem_002_raw_japanese_bridge import (
    QUERY_MARKERS,
    STATEMENT_MARKERS,
    QUERY_TEMPLATES,
    STATEMENT_TEMPLATES,
    RawExample,
    SurfaceBridge,
    build_raw_training_records,
    learn_surface_bridge,
    render_raw_heldout,
)

CAPABILITY_ID = "CAP-SEM-003"

# Opaque surface forms. Their semantic code is used only by the data generator;
# the learner receives raw strings and final Boolean answers.
NOVEL_STATEMENT_GROUPS = (
    ("ネサ", "リホ"),
    ("クマ", "テユ"),
    ("ソケ", "ハヌ"),
    ("ミロ", "ワセ"),
)
NOVEL_QUERY_GROUPS = (
    ("トア", "ミゼ"),
    ("ケヌ", "ホラ"),
    ("フメ", "サコ"),
    ("ユリ", "ワテ"),
)


@dataclass(frozen=True)
class OpenLexicon:
    statement_codes: Mapping[str, int]
    query_codes: Mapping[str, int]
    training_operations: int

    def payload(self) -> dict[str, object]:
        return {
            "statement_codes": dict(sorted(self.statement_codes.items())),
            "query_codes": dict(sorted(self.query_codes.items())),
        }


@dataclass(frozen=True)
class OpenRelationModel:
    bridge: SurfaceBridge
    lexicon: OpenLexicon
    semantic: LearnedMeaning


@dataclass(frozen=True)
class OpenEvaluation:
    correct: int
    total: int
    coverage: int
    inference_operations: int
    predictions: tuple[bool | None, ...]

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0

    @property
    def coverage_rate(self) -> float:
        return self.coverage / self.total if self.total else 0.0


def _semantic_fingerprint(model: LearnedMeaning) -> str:
    payload = json.dumps(
        model.payload(), ensure_ascii=False, sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _bridge_fingerprint(bridge: SurfaceBridge) -> str:
    payload = json.dumps(
        bridge.payload(), ensure_ascii=False, sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _code_from_groups(marker: str, groups: Sequence[Sequence[str]]) -> int:
    for code, group in enumerate(groups):
        if marker in group:
            return code
    raise KeyError(marker)


def _render(template: str, left: str, right: str, marker: str) -> str:
    return template.format(left=left, right=right, marker=marker)


def _raw_pair(
    fact: tuple[str, str, str],
    query: tuple[str, str, str],
    answer: bool,
    *,
    index: int,
    statement_separator: str = "。",
    query_terminator: str = "？",
) -> RawExample:
    fact_text = _render(
        STATEMENT_TEMPLATES[index % len(STATEMENT_TEMPLATES)],
        fact[0],
        fact[2],
        fact[1],
    )
    query_text = _render(
        QUERY_TEMPLATES[(index // 3) % len(QUERY_TEMPLATES)],
        query[0],
        query[2],
        query[1],
    )
    return RawExample(
        fact_text + statement_separator + query_text + query_terminator,
        answer,
    )


def build_open_calibration_records(
    *,
    statement_separator: str = "。",
    query_terminator: str = "？",
) -> tuple[RawExample, ...]:
    """Build behavioral definitions for opaque relation expressions.

    Each novel statement expression is contrasted with every frozen query
    anchor in both argument orders. Novel query expressions are analogously
    contrasted with every frozen statement anchor. Only raw strings and final
    Boolean answers are returned.
    """

    rows: list[RawExample] = []
    index = 0
    for novel_code, group in enumerate(NOVEL_STATEMENT_GROUPS):
        for novel_marker in group:
            for anchor_code, anchor_group in enumerate(QUERY_GROUPS):
                anchor = anchor_group[0]
                left = f"定{index:03d}甲"
                right = f"定{index:03d}乙"
                rows.append(
                    _raw_pair(
                        (left, novel_marker, right),
                        (left, anchor, right),
                        novel_code == anchor_code,
                        index=index,
                        statement_separator=statement_separator,
                        query_terminator=query_terminator,
                    )
                )
                index += 1
                rows.append(
                    _raw_pair(
                        (left, novel_marker, right),
                        (right, anchor, left),
                        (novel_code ^ 1) == anchor_code,
                        index=index,
                        statement_separator=statement_separator,
                        query_terminator=query_terminator,
                    )
                )
                index += 1

    for novel_code, group in enumerate(NOVEL_QUERY_GROUPS):
        for novel_marker in group:
            for anchor_code, anchor_group in enumerate(STATEMENT_GROUPS):
                anchor = anchor_group[0]
                left = f"定{index:03d}甲"
                right = f"定{index:03d}乙"
                rows.append(
                    _raw_pair(
                        (left, anchor, right),
                        (left, novel_marker, right),
                        anchor_code == novel_code,
                        index=index,
                        statement_separator=statement_separator,
                        query_terminator=query_terminator,
                    )
                )
                index += 1
                rows.append(
                    _raw_pair(
                        (left, anchor, right),
                        (right, novel_marker, left),
                        (anchor_code ^ 1) == novel_code,
                        index=index,
                        statement_separator=statement_separator,
                        query_terminator=query_terminator,
                    )
                )
                index += 1
    return tuple(rows)


def _compile_open_skeleton(skeleton: str) -> re.Pattern[str]:
    pieces = re.split(r"(<E0>|<E1>|<M>)", skeleton)
    output: list[str] = []
    for piece in pieces:
        if piece == "<E0>":
            output.append("(?P<e0>.+?)")
        elif piece == "<E1>":
            output.append("(?P<e1>.+?)")
        elif piece == "<M>":
            output.append("(?P<marker>.+?)")
        else:
            output.append(re.escape(piece))
    return re.compile("^" + "".join(output) + "$")


def _parse_open_clause(
    clause: str,
    skeletons: Sequence[str],
    orientations: Mapping[str, int],
) -> tuple[str, str, str]:
    matches: list[tuple[str, str, str]] = []
    for skeleton in skeletons:
        match = _compile_open_skeleton(skeleton).fullmatch(clause)
        if match is None:
            continue
        e0 = match.group("e0")
        e1 = match.group("e1")
        marker = match.group("marker")
        if not marker or e0 == e1:
            continue
        pair = (e0, e1)
        if orientations[skeleton] == 1:
            pair = pair[::-1]
        matches.append((pair[0], marker, pair[1]))
    unique = tuple(dict.fromkeys(matches))
    if len(unique) != 1:
        raise ValueError("open relation clause has zero or multiple parses")
    return unique[0]


def parse_open_example(bridge: SurfaceBridge, example: RawExample) -> Record:
    if not example.text.endswith(bridge.query_terminator):
        raise ValueError("unknown query terminator")
    body = example.text[: -len(bridge.query_terminator)]
    clauses = body.split(bridge.statement_separator)
    if len(clauses) < 2 or any(not clause for clause in clauses):
        raise ValueError("invalid open relation document")
    facts = tuple(
        _parse_open_clause(
            clause,
            bridge.statement_skeletons,
            bridge.statement_orientations,
        )
        for clause in clauses[:-1]
    )
    query = _parse_open_clause(
        clauses[-1],
        bridge.query_skeletons,
        bridge.query_orientations,
    )
    return Record(facts, query, example.answer)


def _anchor_by_code(
    semantic: LearnedMeaning, *, query: bool
) -> dict[int, str]:
    allowed = set(QUERY_MARKERS if query else STATEMENT_MARKERS)
    anchors: dict[int, str] = {}
    for marker, code in sorted(semantic.marker_codes.items()):
        if marker in allowed:
            anchors.setdefault(code, marker)
    if set(anchors) != set(semantic.inverse_codes):
        raise ValueError("frozen semantic runtime lacks one or more anchor codes")
    return anchors


def _rewrite_with_candidate(
    row: Record,
    semantic: LearnedMeaning,
    *,
    target: str,
    candidate_code: int,
    target_is_query: bool,
) -> Record:
    statement_anchors = _anchor_by_code(semantic, query=False)
    query_anchors = _anchor_by_code(semantic, query=True)
    facts = []
    for left, marker, right in row.facts:
        if marker == target and not target_is_query:
            marker = statement_anchors[candidate_code]
        elif marker not in semantic.marker_codes:
            raise KeyError(marker)
        facts.append((left, marker, right))
    left, marker, right = row.query
    if marker == target and target_is_query:
        marker = query_anchors[candidate_code]
    elif marker not in semantic.marker_codes:
        raise KeyError(marker)
    return Record(tuple(facts), (left, marker, right), row.answer)


def _infer_marker_code(
    target: str,
    rows: Sequence[Record],
    semantic: LearnedMeaning,
    *,
    target_is_query: bool,
) -> tuple[int, int]:
    relevant = tuple(
        row
        for row in rows
        if (
            row.query[1] == target
            if target_is_query
            else any(fact[1] == target for fact in row.facts)
        )
    )
    if not relevant:
        raise ValueError(f"no calibration rows for {target}")
    scored: list[tuple[int, int]] = []
    operations = 0
    for candidate_code in sorted(semantic.inverse_codes):
        errors = 0
        for row in relevant:
            rewritten = _rewrite_with_candidate(
                row,
                semantic,
                target=target,
                candidate_code=candidate_code,
                target_is_query=target_is_query,
            )
            prediction, used = predict(semantic, rewritten)
            operations += used + 1
            errors += int(prediction != row.answer)
        scored.append((errors, candidate_code))
    scored.sort()
    if scored[0][0] != 0 or len(scored) < 2 or scored[1][0] == 0:
        raise ValueError(f"marker meaning is not uniquely identifiable: {target}")
    return scored[0][1], operations


def learn_open_lexicon(
    raw_calibration: Sequence[RawExample],
    bridge: SurfaceBridge,
    semantic: LearnedMeaning,
) -> OpenLexicon:
    parsed: list[Record] = []
    operations = 0
    for example in raw_calibration:
        parsed.append(parse_open_example(bridge, example))
        operations += len(example.text) * (
            len(bridge.statement_skeletons) + len(bridge.query_skeletons)
        )

    statement_targets = sorted(
        {
            marker
            for row in parsed
            for _, marker, _ in row.facts
            if marker not in semantic.marker_codes
        }
    )
    query_targets = sorted(
        {
            row.query[1]
            for row in parsed
            if row.query[1] not in semantic.marker_codes
        }
    )
    statement_codes: dict[str, int] = {}
    query_codes: dict[str, int] = {}
    for marker in statement_targets:
        code, used = _infer_marker_code(
            marker, parsed, semantic, target_is_query=False
        )
        statement_codes[marker] = code
        operations += used
    for marker in query_targets:
        code, used = _infer_marker_code(
            marker, parsed, semantic, target_is_query=True
        )
        query_codes[marker] = code
        operations += used
    return OpenLexicon(statement_codes, query_codes, operations)


def rewrite_open_record(
    row: Record, lexicon: OpenLexicon, semantic: LearnedMeaning
) -> Record:
    statement_anchors = _anchor_by_code(semantic, query=False)
    query_anchors = _anchor_by_code(semantic, query=True)
    facts = []
    for left, marker, right in row.facts:
        if marker in semantic.marker_codes:
            rewritten = marker
        else:
            rewritten = statement_anchors[lexicon.statement_codes[marker]]
        facts.append((left, rewritten, right))
    left, marker, right = row.query
    if marker in semantic.marker_codes:
        rewritten_query = marker
    else:
        rewritten_query = query_anchors[lexicon.query_codes[marker]]
    return Record(tuple(facts), (left, rewritten_query, right), row.answer)


def predict_open(
    model: OpenRelationModel, example: RawExample
) -> tuple[bool | None, int]:
    operations = len(example.text) * (
        len(model.bridge.statement_skeletons)
        + len(model.bridge.query_skeletons)
    )
    try:
        parsed = parse_open_example(model.bridge, example)
        rewritten = rewrite_open_record(parsed, model.lexicon, model.semantic)
        prediction, semantic_operations = predict(model.semantic, rewritten)
    except (KeyError, ValueError):
        return None, operations
    return prediction, operations + semantic_operations


def evaluate_open(
    model: OpenRelationModel, rows: Sequence[RawExample]
) -> OpenEvaluation:
    predictions: list[bool | None] = []
    correct = 0
    coverage = 0
    operations = 0
    for row in rows:
        prediction, used = predict_open(model, row)
        operations += used
        predictions.append(prediction)
        if prediction is None:
            continue
        coverage += 1
        correct += int(prediction == row.answer)
    return OpenEvaluation(
        correct, len(rows), coverage, operations, tuple(predictions)
    )


def _novelize_record(row: Record, index: int) -> Record:
    facts = []
    for edge_index, (left, marker, right) in enumerate(row.facts):
        code = _code_from_groups(marker, STATEMENT_GROUPS)
        group = NOVEL_STATEMENT_GROUPS[code]
        facts.append((left, group[(index + edge_index) % len(group)], right))
    left, marker, right = row.query
    code = _code_from_groups(marker, QUERY_GROUPS)
    group = NOVEL_QUERY_GROUPS[code]
    return Record(
        tuple(facts),
        (left, group[index % len(group)], right),
        row.answer,
    )


def build_open_heldout_records(
    *, seed: int = 20260714, size: int = 128
) -> tuple[Record, ...]:
    return tuple(
        _novelize_record(row, index)
        for index, row in enumerate(
            build_heldout_records(seed=seed, size=size)
        )
    )


def _rename_record(row: Record, index: int) -> Record:
    entities = sorted(
        {part for fact in row.facts for part in (fact[0], fact[2])}
        | {row.query[0], row.query[2]}
    )
    mapping = {
        entity: f"未知語{index:03d}_{position:02d}"
        for position, entity in enumerate(entities)
    }
    facts = tuple(
        (mapping[left], marker, mapping[right])
        for left, marker, right in row.facts
    )
    left, marker, right = row.query
    return Record(facts, (mapping[left], marker, mapping[right]), row.answer)


def _swap_novel_synonyms(row: Record) -> Record:
    facts = []
    for left, marker, right in row.facts:
        code = _code_from_groups(marker, NOVEL_STATEMENT_GROUPS)
        group = NOVEL_STATEMENT_GROUPS[code]
        facts.append((left, group[(group.index(marker) + 1) % len(group)], right))
    left, marker, right = row.query
    code = _code_from_groups(marker, NOVEL_QUERY_GROUPS)
    group = NOVEL_QUERY_GROUPS[code]
    return Record(
        tuple(facts),
        (left, group[(group.index(marker) + 1) % len(group)], right),
        row.answer,
    )


def exact_raw_memorizer_accuracy(
    training: Sequence[RawExample], heldout: Sequence[RawExample]
) -> float:
    table = {row.text: row.answer for row in training}
    majority = Counter(row.answer for row in training).most_common(1)[0][0]
    return sum(
        table.get(row.text, majority) == row.answer for row in heldout
    ) / len(heldout)


def learned_payload_bytes(lexicon: OpenLexicon) -> int:
    raw = json.dumps(
        lexicon.payload(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return len(zlib.compress(raw, level=9))


def executable_description_bits() -> int:
    functions = (
        _compile_open_skeleton,
        _parse_open_clause,
        parse_open_example,
        _infer_marker_code,
        learn_open_lexicon,
        rewrite_open_record,
        predict_open,
        predict,
    )
    payload = b"".join(
        marshal.dumps(function.__code__) for function in functions
    )
    return 8 * len(zlib.compress(payload, level=9))


def learner_references_novel_gold_groups() -> bool:
    learner_functions = (
        _infer_marker_code,
        learn_open_lexicon,
        rewrite_open_record,
    )
    forbidden = {"NOVEL_STATEMENT_GROUPS", "NOVEL_QUERY_GROUPS", "_code_from_groups"}
    return any(
        forbidden & set(function.__code__.co_names)
        for function in learner_functions
    )


def run_gate() -> dict[str, object]:
    semantic = learn_meaning(build_training_records())
    bridge = learn_surface_bridge(build_raw_training_records(), semantic)
    semantic_before = _semantic_fingerprint(semantic)
    bridge_before = _bridge_fingerprint(bridge)

    calibration = build_open_calibration_records()
    lexicon = learn_open_lexicon(calibration, bridge, semantic)
    model = OpenRelationModel(bridge, lexicon, semantic)

    heldout_records = build_open_heldout_records()
    heldout_raw = render_raw_heldout(heldout_records)
    heldout = evaluate_open(model, heldout_raw)

    variants = {
        "template_and_order_1": render_raw_heldout(
            heldout_records, template_variant=1
        ),
        "template_and_order_2": render_raw_heldout(
            heldout_records, template_variant=2
        ),
        "entity_renaming": render_raw_heldout(
            tuple(
                _rename_record(row, index)
                for index, row in enumerate(heldout_records)
            ),
            template_variant=1,
        ),
        "novel_synonym_substitution": render_raw_heldout(
            tuple(_swap_novel_synonyms(row) for row in heldout_records),
            template_variant=2,
        ),
    }
    variant_results = {
        name: evaluate_open(model, rows) for name, rows in variants.items()
    }

    alternate_bridge = learn_surface_bridge(
        build_raw_training_records(
            statement_separator="；", query_terminator="！"
        ),
        semantic,
    )
    alternate_calibration = build_open_calibration_records(
        statement_separator="；", query_terminator="！"
    )
    alternate_lexicon = learn_open_lexicon(
        alternate_calibration, alternate_bridge, semantic
    )
    alternate_model = OpenRelationModel(
        alternate_bridge, alternate_lexicon, semantic
    )
    alternate_heldout = evaluate_open(
        alternate_model,
        render_raw_heldout(
            heldout_records,
            template_variant=2,
            statement_separator="；",
            query_terminator="！",
        ),
    )

    semantic_after = _semantic_fingerprint(semantic)
    bridge_after = _bridge_fingerprint(bridge)
    payload_bytes = learned_payload_bytes(lexicon)
    executable_bits = executable_description_bits()
    average_inference_operations = (
        heldout.inference_operations / heldout.total
    )
    memorizer_accuracy = exact_raw_memorizer_accuracy(
        calibration, heldout_raw
    )
    expected_statement_markers = {
        marker for group in NOVEL_STATEMENT_GROUPS for marker in group
    }
    expected_query_markers = {
        marker for group in NOVEL_QUERY_GROUPS for marker in group
    }

    checks = {
        "all_novel_statement_markers_are_grounded": (
            set(lexicon.statement_codes) == expected_statement_markers
        ),
        "all_novel_query_markers_are_grounded": (
            set(lexicon.query_codes) == expected_query_markers
        ),
        "heldout_accuracy_at_least_95_percent": heldout.accuracy >= 0.95,
        "heldout_coverage_at_least_95_percent": (
            heldout.coverage_rate >= 0.95
        ),
        "beats_exact_raw_memorizer_by_25_points": (
            heldout.accuracy - memorizer_accuracy >= 0.25
        ),
        "all_surface_and_lexical_variants_pass": all(
            result.accuracy >= 0.95 and result.coverage_rate >= 0.95
            for result in variant_results.values()
        ),
        "alternate_punctuation_is_relearned": (
            alternate_heldout.accuracy >= 0.95
            and alternate_heldout.coverage_rate >= 0.95
        ),
        "semantic_runtime_is_frozen": semantic_before == semantic_after,
        "surface_bridge_is_frozen": bridge_before == bridge_after,
        "learner_has_no_novel_gold_group_reference": (
            not learner_references_novel_gold_groups()
        ),
        "learned_lexicon_payload_within_4096_bytes": payload_bytes <= 4096,
        "executable_description_within_500k_bits": executable_bits <= 500_000,
        "training_compute_within_500k_operations": (
            lexicon.training_operations <= 500_000
        ),
        "average_inference_within_1024_operations": (
            average_inference_operations <= 1024
        ),
    }

    return {
        "capability_id": CAPABILITY_ID,
        "capability": "opaque relation-expression grounding into a frozen semantic runtime",
        "claim": (
            "behaviorally ground unseen relation strings into the existing "
            "CAP-SEM-001 latent codes while reusing the frozen CAP-SEM-002 "
            "surface bridge and graph predictor"
        ),
        "calibration_documents": len(calibration),
        "heldout_documents": len(heldout_raw),
        "learned_statement_markers": len(lexicon.statement_codes),
        "learned_query_markers": len(lexicon.query_codes),
        "heldout_accuracy": heldout.accuracy,
        "heldout_coverage": heldout.coverage_rate,
        "exact_raw_memorizer_accuracy": memorizer_accuracy,
        "variant_accuracies": {
            name: result.accuracy for name, result in variant_results.items()
        },
        "alternate_punctuation_accuracy": alternate_heldout.accuracy,
        "learned_payload_bytes": payload_bytes,
        "executable_total_description_bits": executable_bits,
        "training_operations": lexicon.training_operations,
        "average_inference_operations": average_inference_operations,
        "semantic_fingerprint": semantic_before,
        "bridge_fingerprint": bridge_before,
        "checks": checks,
        "passed": all(checks.values()),
        "natural_language_definition_understanding": False,
        "unrestricted_relation_learning": False,
        "unrestricted_japanese_understanding": False,
        "high_school_intelligence": False,
        "general_llm_parity": False,
    }


def render_markdown(result: Mapping[str, object]) -> str:
    lines = [
        "# CAP-SEM-003: open relation-expression grounding",
        "",
        f"Passed: **{result['passed']}**",
        "",
        f"- Calibration documents: **{result['calibration_documents']}**",
        f"- Held-out documents: **{result['heldout_documents']}**",
        f"- Learned statement markers: **{result['learned_statement_markers']}**",
        f"- Learned query markers: **{result['learned_query_markers']}**",
        f"- Held-out accuracy: **{result['heldout_accuracy']:.3f}**",
        f"- Held-out coverage: **{result['heldout_coverage']:.3f}**",
        f"- Exact raw memorizer: **{result['exact_raw_memorizer_accuracy']:.3f}**",
        f"- Learned payload: **{result['learned_payload_bytes']} bytes**",
        f"- Training operations: **{result['training_operations']}**",
        f"- Average inference operations: **{result['average_inference_operations']:.1f}**",
        "",
        "## Metamorphic accuracy",
        "",
    ]
    for name, value in result["variant_accuracies"].items():
        lines.append(f"- {name}: **{value:.3f}**")
    lines.extend(["", "## Checks", ""])
    for name, value in result["checks"].items():
        lines.append(f"- {name}: **{value}**")
    lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            "The novel strings are opaque and absent from the frozen semantic model, but their meanings are identified by a controlled set of behavioral definition examples against known anchors. This is not natural-language dictionary-definition understanding, unrestricted vocabulary acquisition, or general Japanese intelligence.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    result = run_gate()
    root = Path(__file__).resolve().parents[2]
    results_dir = root / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "cap_sem_003.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (results_dir / "cap_sem_003.md").write_text(
        render_markdown(result), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
