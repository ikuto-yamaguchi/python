from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
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
    QUERY_TEMPLATES,
    STATEMENT_TEMPLATES,
    RawExample,
    SurfaceBridge,
    build_raw_training_records,
    learn_surface_bridge,
)

CAPABILITY_ID = "CAP-SEM-003"

# Hidden only in the data generator. The learner never reads this table.
NOVEL_ALIAS_GROUPS = (
    ("ゼルク", "ノアル"),
    ("ミヴァ", "トレン"),
    ("ラセム", "フィノ"),
    ("グロア", "ネクト"),
)


@dataclass(frozen=True)
class LexicalExtension:
    marker_codes: Mapping[str, int]
    candidates_evaluated: int
    training_operations: int

    def payload(self) -> Mapping[str, int]:
        return dict(sorted(self.marker_codes.items()))


@dataclass(frozen=True)
class LexicalEvaluation:
    correct: int
    total: int
    coverage: int
    semantic_operations: int

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0

    @property
    def coverage_rate(self) -> float:
        return self.coverage / self.total if self.total else 0.0


def _fingerprint(payload: Mapping[str, object]) -> str:
    serialized = json.dumps(
        payload, ensure_ascii=False, sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def _render(template: str, left: str, right: str, marker: str) -> str:
    return template.format(left=left, right=right, marker=marker)


def _compile_open_marker_skeleton(skeleton: str):
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


def _parse_open_marker_clause(
    clause: str,
    skeletons: Sequence[str],
    orientations: Mapping[str, int],
) -> tuple[str, str, str]:
    matches = []
    for skeleton in skeletons:
        match = _compile_open_marker_skeleton(skeleton).fullmatch(clause)
        if match is None or match.group("e0") == match.group("e1"):
            continue
        pair = (match.group("e0"), match.group("e1"))
        if orientations[skeleton] == 1:
            pair = pair[::-1]
        marker = match.group("marker")
        if not marker:
            continue
        matches.append((pair[0], marker, pair[1]))
    if len(matches) != 1:
        raise ValueError("open-vocabulary clause has zero or multiple parses")
    return matches[0]


def parse_open_vocabulary(
    bridge: SurfaceBridge, example: RawExample
) -> Record:
    if not example.text.endswith(bridge.query_terminator):
        raise ValueError("unknown query terminator")
    body = example.text[: -len(bridge.query_terminator)]
    clauses = body.split(bridge.statement_separator)
    if len(clauses) < 2 or any(not clause for clause in clauses):
        raise ValueError("invalid clause segmentation")
    facts = tuple(
        _parse_open_marker_clause(
            clause,
            bridge.statement_skeletons,
            bridge.statement_orientations,
        )
        for clause in clauses[:-1]
    )
    query = _parse_open_marker_clause(
        clauses[-1],
        bridge.query_skeletons,
        bridge.query_orientations,
    )
    return Record(facts, query, example.answer)


def build_lexical_training_records(
    *, alias_prefix: str = ""
) -> tuple[tuple[RawExample, ...], tuple[tuple[str, ...], ...]]:
    base = learn_meaning(build_training_records())
    aliases = tuple(
        tuple(alias_prefix + marker for marker in group)
        for group in NOVEL_ALIAS_GROUPS
    )
    known_statements = tuple(
        marker for group in STATEMENT_GROUPS for marker in group
    )
    known_queries = tuple(marker for group in QUERY_GROUPS for marker in group)
    rows: list[RawExample] = []
    index = 0
    for hidden_code, group in enumerate(aliases):
        for alias in group:
            for known_query in known_queries:
                query_code = base.marker_codes[known_query]
                for reverse in (False, True):
                    left = f"語{index:04x}甲"
                    right = f"語{index:04x}乙"
                    statement = _render(
                        STATEMENT_TEMPLATES[index % len(STATEMENT_TEMPLATES)],
                        left,
                        right,
                        alias,
                    )
                    query_left, query_right = (
                        (right, left) if reverse else (left, right)
                    )
                    query = _render(
                        QUERY_TEMPLATES[
                            (index // len(STATEMENT_TEMPLATES))
                            % len(QUERY_TEMPLATES)
                        ],
                        query_left,
                        query_right,
                        known_query,
                    )
                    effective_code = hidden_code ^ int(reverse)
                    rows.append(
                        RawExample(
                            statement + "。" + query + "？",
                            effective_code == query_code,
                        )
                    )
                    index += 1
            for known_statement in known_statements:
                statement_code = base.marker_codes[known_statement]
                for reverse in (False, True):
                    left = f"語{index:04x}甲"
                    right = f"語{index:04x}乙"
                    statement = _render(
                        STATEMENT_TEMPLATES[index % len(STATEMENT_TEMPLATES)],
                        left,
                        right,
                        known_statement,
                    )
                    query_left, query_right = (
                        (right, left) if reverse else (left, right)
                    )
                    query = _render(
                        QUERY_TEMPLATES[
                            (index // len(STATEMENT_TEMPLATES))
                            % len(QUERY_TEMPLATES)
                        ],
                        query_left,
                        query_right,
                        alias,
                    )
                    effective_statement = statement_code ^ int(reverse)
                    rows.append(
                        RawExample(
                            statement + "。" + query + "？",
                            effective_statement == hidden_code,
                        )
                    )
                    index += 1
    return tuple(rows), aliases


def learn_lexical_extension(
    rows: Sequence[RawExample],
    bridge: SurfaceBridge,
    base_model: LearnedMeaning,
) -> LexicalExtension:
    parsed = tuple(parse_open_vocabulary(bridge, row) for row in rows)
    unknown_markers = tuple(
        sorted(
            {
                marker
                for row in parsed
                for marker in (
                    *(fact[1] for fact in row.facts),
                    row.query[1],
                )
                if marker not in base_model.marker_codes
            }
        )
    )
    learned: dict[str, int] = {}
    operations = 0
    candidates_evaluated = 0
    for marker in unknown_markers:
        relevant = tuple(
            row
            for row in parsed
            if marker in tuple(fact[1] for fact in row.facts) + (row.query[1],)
        )
        valid_codes: list[int] = []
        for candidate_code in range(4):
            candidates_evaluated += 1
            candidate_model = LearnedMeaning(
                {
                    **base_model.marker_codes,
                    **learned,
                    marker: candidate_code,
                },
                base_model.inverse_codes,
                base_model.training_operations,
            )
            errors = 0
            usable = 0
            for row in relevant:
                markers = tuple(fact[1] for fact in row.facts) + (
                    row.query[1],
                )
                if any(
                    value not in candidate_model.marker_codes for value in markers
                ):
                    continue
                prediction, used = predict(candidate_model, row)
                operations += used
                usable += 1
                errors += int(prediction != row.answer)
            if usable and errors == 0:
                valid_codes.append(candidate_code)
        if len(valid_codes) != 1:
            raise ValueError(
                f"novel marker {marker!r} is not identifiable: {valid_codes}"
            )
        learned[marker] = valid_codes[0]
    if not learned:
        raise ValueError("no novel relation expressions found")
    return LexicalExtension(learned, candidates_evaluated, operations)


def extend_semantic_model(
    base_model: LearnedMeaning, extension: LexicalExtension
) -> LearnedMeaning:
    return LearnedMeaning(
        {**base_model.marker_codes, **extension.marker_codes},
        base_model.inverse_codes,
        base_model.training_operations + extension.training_operations,
    )


def build_novel_alias_heldout(
    aliases: Sequence[Sequence[str]], *, template_variant: int = 0
) -> tuple[RawExample, ...]:
    base = learn_meaning(build_training_records())
    output: list[RawExample] = []
    for record_index, structured in enumerate(build_heldout_records()):
        facts = []
        for edge_index, (left, known_marker, right) in enumerate(
            structured.facts
        ):
            code = base.marker_codes[known_marker]
            alias = aliases[code][
                (record_index + edge_index + template_variant)
                % len(aliases[code])
            ]
            facts.append(
                _render(
                    STATEMENT_TEMPLATES[
                        (record_index + edge_index + template_variant)
                        % len(STATEMENT_TEMPLATES)
                    ],
                    left,
                    right,
                    alias,
                )
            )
        if template_variant % 2:
            facts.reverse()
        query_left, known_query, query_right = structured.query
        query_code = base.marker_codes[known_query]
        query_alias = aliases[query_code][
            (record_index + template_variant) % len(aliases[query_code])
        ]
        query = _render(
            QUERY_TEMPLATES[
                (2 * record_index + template_variant)
                % len(QUERY_TEMPLATES)
            ],
            query_left,
            query_right,
            query_alias,
        )
        output.append(RawExample("。".join(facts) + "。" + query + "？", structured.answer))
    return tuple(output)


def evaluate_novel_aliases(
    rows: Sequence[RawExample],
    bridge: SurfaceBridge,
    semantic_model: LearnedMeaning,
) -> LexicalEvaluation:
    correct = 0
    coverage = 0
    operations = 0
    for row in rows:
        try:
            parsed = parse_open_vocabulary(bridge, row)
            prediction, used = predict(semantic_model, parsed)
        except (KeyError, ValueError):
            continue
        coverage += 1
        operations += used
        correct += int(prediction == row.answer)
    return LexicalEvaluation(correct, len(rows), coverage, operations)


def exact_text_memorizer_accuracy(
    train: Sequence[RawExample], heldout: Sequence[RawExample]
) -> float:
    table = {row.text: row.answer for row in train}
    majority = Counter(row.answer for row in train).most_common(1)[0][0]
    correct = sum(table.get(row.text, majority) == row.answer for row in heldout)
    return correct / len(heldout)


def build_ambiguous_calibration() -> tuple[RawExample, ...]:
    """Codes 1 and 3 are both consistent when only codes 0 and 2 are probed."""
    base = learn_meaning(build_training_records())
    alias = "曖昧語"
    rows: list[RawExample] = []
    known_queries = (QUERY_GROUPS[0][0], QUERY_GROUPS[2][0])
    for index, known_query in enumerate(known_queries):
        left, right = f"曖{index}甲", f"曖{index}乙"
        statement = _render(STATEMENT_TEMPLATES[index], left, right, alias)
        query = _render(QUERY_TEMPLATES[index], left, right, known_query)
        rows.append(
            RawExample(
                statement + "。" + query + "？",
                False,
            )
        )
        assert base.marker_codes[known_query] in (0, 2)
    return tuple(rows)


def extension_payload_bytes(extension: LexicalExtension) -> int:
    raw = json.dumps(
        extension.payload(), ensure_ascii=False, sort_keys=True
    ).encode("utf-8")
    return len(zlib.compress(raw, level=9))


def learner_references_hidden_alias_groups() -> bool:
    learner_functions = (
        parse_open_vocabulary,
        learn_lexical_extension,
        extend_semantic_model,
        evaluate_novel_aliases,
    )
    return any(
        "NOVEL_ALIAS_GROUPS" in function.__code__.co_names
        for function in learner_functions
    )


def run_gate() -> dict[str, object]:
    base_model = learn_meaning(build_training_records())
    base_fingerprint = _fingerprint(base_model.payload())
    bridge = learn_surface_bridge(build_raw_training_records(), base_model)
    bridge_fingerprint = _fingerprint(bridge.payload())

    lexical_training, aliases = build_lexical_training_records()
    extension = learn_lexical_extension(lexical_training, bridge, base_model)
    extended_model = extend_semantic_model(base_model, extension)
    heldout = build_novel_alias_heldout(aliases)
    evaluation = evaluate_novel_aliases(
        heldout, bridge, extended_model
    )
    variant = evaluate_novel_aliases(
        build_novel_alias_heldout(aliases, template_variant=1),
        bridge,
        extended_model,
    )

    renamed_training, renamed_aliases = build_lexical_training_records(
        alias_prefix="新"
    )
    renamed_extension = learn_lexical_extension(
        renamed_training, bridge, base_model
    )
    renamed_model = extend_semantic_model(base_model, renamed_extension)
    renamed_evaluation = evaluate_novel_aliases(
        build_novel_alias_heldout(renamed_aliases, template_variant=2),
        bridge,
        renamed_model,
    )

    ambiguous_rejected = False
    try:
        learn_lexical_extension(
            build_ambiguous_calibration(), bridge, base_model
        )
    except ValueError:
        ambiguous_rejected = True

    contradictory_rejected = False
    contradictory = lexical_training[:1] + (
        RawExample(lexical_training[0].text, not lexical_training[0].answer),
    )
    try:
        learn_lexical_extension(contradictory, bridge, base_model)
    except ValueError:
        contradictory_rejected = True

    unknown = build_novel_alias_heldout(aliases)[:1]
    unknown_text = unknown[0].text.replace(aliases[0][0], "未登録関係")
    unknown_evaluation = evaluate_novel_aliases(
        (RawExample(unknown_text, unknown[0].answer),),
        bridge,
        extended_model,
    )

    payload_bytes = extension_payload_bytes(extension)
    memorizer_accuracy = exact_text_memorizer_accuracy(
        lexical_training, heldout
    )
    average_operations = (
        evaluation.semantic_operations / evaluation.coverage
        if evaluation.coverage
        else 0.0
    )
    checks = {
        "heldout_accuracy_at_least_95_percent": evaluation.accuracy >= 0.95,
        "heldout_coverage_at_least_95_percent": evaluation.coverage_rate >= 0.95,
        "beats_exact_text_memorizer_by_25_points": (
            evaluation.accuracy - memorizer_accuracy >= 0.25
        ),
        "template_and_fact_order_invariant": (
            variant.accuracy >= 0.95 and variant.coverage_rate >= 0.95
        ),
        "renamed_aliases_are_relearned": (
            renamed_evaluation.accuracy >= 0.95
            and renamed_evaluation.coverage_rate >= 0.95
        ),
        "all_eight_aliases_grounded": len(extension.marker_codes) == 8,
        "ambiguous_evidence_is_rejected": ambiguous_rejected,
        "contradictory_evidence_is_rejected": contradictory_rejected,
        "unregistered_marker_abstains": unknown_evaluation.coverage == 0,
        "base_semantic_runtime_is_frozen": (
            base_fingerprint == _fingerprint(base_model.payload())
        ),
        "surface_bridge_is_frozen": (
            bridge_fingerprint == _fingerprint(bridge.payload())
        ),
        "learner_does_not_read_hidden_alias_groups": (
            not learner_references_hidden_alias_groups()
        ),
        "extension_payload_within_2048_bytes": payload_bytes <= 2048,
        "average_inference_within_128_operations": average_operations <= 128,
    }
    return {
        "capability_id": CAPABILITY_ID,
        "capability": "open-surface novel relation lexical grounding",
        "claim": (
            "ground unseen relation strings into frozen latent relation classes "
            "from raw usage examples and final truth labels"
        ),
        "training_records": len(lexical_training),
        "novel_aliases": len(extension.marker_codes),
        "candidate_codes_evaluated": extension.candidates_evaluated,
        "training_operations": extension.training_operations,
        "heldout_records": len(heldout),
        "heldout_accuracy": evaluation.accuracy,
        "heldout_coverage": evaluation.coverage_rate,
        "renamed_alias_accuracy": renamed_evaluation.accuracy,
        "exact_text_memorizer_accuracy": memorizer_accuracy,
        "extension_payload_bytes": payload_bytes,
        "average_inference_operations": average_operations,
        "checks": checks,
        "passed": all(checks.values()),
        "new_relation_concept_creation": False,
        "unrestricted_japanese_understanding": False,
        "open_domain_semantics": False,
        "high_school_intelligence": False,
        "general_llm_parity": False,
    }


def render_markdown(result: Mapping[str, object]) -> str:
    lines = [
        f"# {result['capability_id']}: novel relation lexical grounding",
        "",
        f"Passed: **{result['passed']}**",
        "",
        f"- Raw usage records: **{result['training_records']}**",
        f"- Novel relation aliases grounded: **{result['novel_aliases']}**",
        f"- Held-out records: **{result['heldout_records']}**",
        f"- Held-out accuracy: **{result['heldout_accuracy']:.3f}**",
        f"- Held-out coverage: **{result['heldout_coverage']:.3f}**",
        f"- Renamed-alias accuracy: **{result['renamed_alias_accuracy']:.3f}**",
        (
            "- Exact raw-text memorizer: "
            f"**{result['exact_text_memorizer_accuracy']:.3f}**"
        ),
        f"- Learned extension payload: **{result['extension_payload_bytes']} bytes**",
        "",
        "## Checks",
        "",
    ]
    for name, value in result["checks"].items():
        lines.append(f"- {name}: **{value}**")
    lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            "- CAP-SEM-001 and CAP-SEM-002 remain frozen.",
            "- Novel strings are grounded into four already-existing latent relation classes.",
            "- This does not invent a new relation type or learn arbitrary Japanese vocabulary from natural corpora.",
            "- Training still uses synthetic usage examples with final Boolean supervision.",
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
