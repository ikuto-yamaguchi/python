from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
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
    render_raw_heldout,
)
from .cap_sem_003_open_relation_grounding import parse_open_example

CAPABILITY_ID = "CAP-SEM-005"

NEW_STATEMENT_GROUPS = (
    ("ヴァル", "エシ"),
    ("ドネ", "リク"),
)
NEW_QUERY_GROUPS = (
    ("ヴェル", "オシ"),
    ("デナ", "ラク"),
)


@dataclass(frozen=True)
class OntologyExtension:
    marker_codes: Mapping[str, int]
    inverse_codes: Mapping[int, int]
    training_operations: int
    mapped_to_existing: int
    new_relation_pairs: int

    def payload(self) -> Mapping[str, object]:
        return {
            "marker_codes": dict(sorted(self.marker_codes.items())),
            "inverse_codes": {
                str(code): inverse
                for code, inverse in sorted(self.inverse_codes.items())
            },
        }


@dataclass(frozen=True)
class DynamicEvaluation:
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


def _fingerprint(payload: Mapping[str, object]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _render(template: str, left: str, right: str, marker: str) -> str:
    return template.format(left=left, right=right, marker=marker)


def _raw_pair(
    fact: tuple[str, str, str],
    query: tuple[str, str, str],
    answer: bool,
    *,
    index: int,
) -> RawExample:
    statement = _render(
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
    return RawExample(statement + "。" + query_text + "？", answer)


def _known_anchors(semantic: LearnedMeaning, *, query: bool) -> dict[int, str]:
    vocabulary = {
        marker
        for group in (QUERY_GROUPS if query else STATEMENT_GROUPS)
        for marker in group
    }
    anchors: dict[int, str] = {}
    for marker, code in sorted(semantic.marker_codes.items()):
        if marker in vocabulary:
            anchors.setdefault(code, marker)
    if set(anchors) != set(semantic.inverse_codes):
        raise ValueError("frozen ontology lacks anchors for all existing codes")
    return anchors


def build_ontology_calibration(
    semantic: LearnedMeaning,
    *,
    statement_groups: Sequence[Sequence[str]] = NEW_STATEMENT_GROUPS,
    query_groups: Sequence[Sequence[str]] = NEW_QUERY_GROUPS,
    duplicate_existing_pair: bool = False,
) -> tuple[RawExample, ...]:
    statement_groups = tuple(tuple(group) for group in statement_groups)
    query_groups = tuple(tuple(group) for group in query_groups)
    statement_anchors = _known_anchors(semantic, query=False)
    query_anchors = _known_anchors(semantic, query=True)
    existing_codes = tuple(sorted(semantic.inverse_codes))
    root = min(existing_codes)

    def gold_code(group_index: int) -> int:
        if duplicate_existing_pair:
            return root if group_index == 0 else semantic.inverse_codes[root]
        return 100 if group_index == 0 else 101

    rows: list[RawExample] = []
    index = 0

    # Contrast each novel statement expression against the frozen query ontology.
    for group_index, group in enumerate(statement_groups):
        novel_code = gold_code(group_index)
        for marker in group:
            for known_code in existing_codes:
                left, right = f"既{index:04x}甲", f"既{index:04x}乙"
                rows.append(
                    _raw_pair(
                        (left, marker, right),
                        (left, query_anchors[known_code], right),
                        novel_code == known_code,
                        index=index,
                    )
                )
                index += 1
                rows.append(
                    _raw_pair(
                        (left, marker, right),
                        (right, query_anchors[known_code], left),
                        (novel_code ^ 1) == known_code,
                        index=index,
                    )
                )
                index += 1

    # Contrast each novel query expression against the frozen statement ontology.
    for group_index, group in enumerate(query_groups):
        novel_code = gold_code(group_index)
        for marker in group:
            for known_code in existing_codes:
                left, right = f"既{index:04x}甲", f"既{index:04x}乙"
                rows.append(
                    _raw_pair(
                        (left, statement_anchors[known_code], right),
                        (left, marker, right),
                        known_code == novel_code,
                        index=index,
                    )
                )
                index += 1
                rows.append(
                    _raw_pair(
                        (left, statement_anchors[known_code], right),
                        (right, marker, left),
                        (known_code ^ 1) == novel_code,
                        index=index,
                    )
                )
                index += 1

    # Learn the residual internal ontology from novel-to-novel behavior.
    for statement_index, statement_group in enumerate(statement_groups):
        statement_code = gold_code(statement_index)
        for statement_marker in statement_group:
            for query_index, query_group in enumerate(query_groups):
                query_code = gold_code(query_index)
                for query_marker in query_group:
                    left, right = f"新{index:04x}甲", f"新{index:04x}乙"
                    rows.append(
                        _raw_pair(
                            (left, statement_marker, right),
                            (left, query_marker, right),
                            statement_code == query_code,
                            index=index,
                        )
                    )
                    index += 1
                    rows.append(
                        _raw_pair(
                            (left, statement_marker, right),
                            (right, query_marker, left),
                            (statement_code ^ 1) == query_code,
                            index=index,
                        )
                    )
                    index += 1
    return tuple(rows)


def _set_observation(
    table: dict[tuple[str, str], bool], key: tuple[str, str], value: bool
) -> None:
    if key in table and table[key] != value:
        raise ValueError("contradictory behavioral observation")
    table[key] = value


def _rewrite_existing_candidate(
    row: Record,
    semantic: LearnedMeaning,
    target: str,
    candidate_code: int,
    *,
    target_is_query: bool,
) -> Record:
    statement_anchors = _known_anchors(semantic, query=False)
    query_anchors = _known_anchors(semantic, query=True)
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


def _try_existing_code(
    target: str,
    rows: Sequence[Record],
    semantic: LearnedMeaning,
    *,
    target_is_query: bool,
) -> tuple[int | None, int]:
    relevant: list[Record] = []
    for row in rows:
        markers = tuple(marker for _, marker, _ in row.facts) + (row.query[1],)
        if target not in markers:
            continue
        unknown = {marker for marker in markers if marker not in semantic.marker_codes}
        if unknown == {target}:
            relevant.append(row)
    if not relevant:
        return None, 0
    scored: list[tuple[int, int]] = []
    operations = 0
    for candidate_code in sorted(semantic.inverse_codes):
        errors = 0
        for row in relevant:
            rewritten = _rewrite_existing_candidate(
                row,
                semantic,
                target,
                candidate_code,
                target_is_query=target_is_query,
            )
            prediction, used = predict(semantic, rewritten)
            operations += used + 1
            errors += int(prediction != row.answer)
        scored.append((errors, candidate_code))
    zero = [candidate for errors, candidate in scored if errors == 0]
    if len(zero) == 1:
        return zero[0], operations
    if len(zero) > 1:
        raise ValueError(f"existing-code grounding is ambiguous for {target}")
    return None, operations


def learn_ontology_extension(
    raw_calibration: Sequence[RawExample],
    bridge: SurfaceBridge,
    semantic: LearnedMeaning,
) -> OntologyExtension:
    parsed = tuple(parse_open_example(bridge, row) for row in raw_calibration)
    operations = sum(
        len(row.text)
        * (len(bridge.statement_skeletons) + len(bridge.query_skeletons))
        for row in raw_calibration
    )
    unknown_statements = tuple(
        sorted(
            {
                marker
                for row in parsed
                for _, marker, _ in row.facts
                if marker not in semantic.marker_codes
            }
        )
    )
    unknown_queries = tuple(
        sorted(
            {
                row.query[1]
                for row in parsed
                if row.query[1] not in semantic.marker_codes
            }
        )
    )
    extension_codes: dict[str, int] = {}
    residual_statements: list[str] = []
    residual_queries: list[str] = []
    mapped_to_existing = 0
    for marker in unknown_statements:
        code, used = _try_existing_code(
            marker, parsed, semantic, target_is_query=False
        )
        operations += used
        if code is None:
            residual_statements.append(marker)
        else:
            extension_codes[marker] = code
            mapped_to_existing += 1
    for marker in unknown_queries:
        code, used = _try_existing_code(
            marker, parsed, semantic, target_is_query=True
        )
        operations += used
        if code is None:
            residual_queries.append(marker)
        else:
            extension_codes[marker] = code
            mapped_to_existing += 1

    if not residual_statements and not residual_queries:
        return OntologyExtension(
            extension_codes, {}, operations, mapped_to_existing, 0
        )
    if not residual_statements or not residual_queries:
        raise ValueError("residual ontology lacks one expression channel")

    same: dict[tuple[str, str], bool] = {}
    reverse: dict[tuple[str, str], bool] = {}
    residual_statement_set = set(residual_statements)
    residual_query_set = set(residual_queries)
    for row in parsed:
        if len(row.facts) != 1:
            continue
        left, statement, right = row.facts[0]
        query_left, query, query_right = row.query
        if statement not in residual_statement_set or query not in residual_query_set:
            continue
        if (query_left, query_right) == (left, right):
            _set_observation(same, (statement, query), row.answer)
        elif (query_left, query_right) == (right, left):
            _set_observation(reverse, (statement, query), row.answer)
        operations += 1

    if any(
        (statement, query) not in same or (statement, query) not in reverse
        for statement in residual_statements
        for query in residual_queries
    ):
        raise ValueError("residual behavioral matrix is incomplete")

    query_columns = {
        query: tuple(same[(statement, query)] for statement in residual_statements)
        for query in residual_queries
    }
    unique_columns = sorted(set(query_columns.values()))
    if len(unique_columns) < 2 or len(unique_columns) % 2:
        raise ValueError("residual classes cannot form inverse pairs")
    column_to_class = {
        column: index for index, column in enumerate(unique_columns)
    }
    query_class = {
        query: column_to_class[column]
        for query, column in query_columns.items()
    }
    statement_class: dict[str, int] = {}
    inverse_class: dict[int, int] = {}
    for statement in residual_statements:
        same_hits = {
            query_class[query]
            for query in residual_queries
            if same[(statement, query)]
        }
        reverse_hits = {
            query_class[query]
            for query in residual_queries
            if reverse[(statement, query)]
        }
        if len(same_hits) != 1 or len(reverse_hits) != 1:
            raise ValueError("residual marker signatures are not identifiable")
        current = next(iter(same_hits))
        opposite = next(iter(reverse_hits))
        if current == opposite:
            raise ValueError("self-inverse residual class is outside this gate")
        statement_class[statement] = current
        previous = inverse_class.setdefault(current, opposite)
        if previous != opposite:
            raise ValueError("inconsistent residual inverse relation")
    if any(
        inverse_class.get(inverse_class.get(code, -1), -1) != code
        for code in inverse_class
    ):
        raise ValueError("residual inverse mapping is not involutive")
    if set(query_class.values()) != set(inverse_class):
        raise ValueError("query and statement residual classes disagree")

    next_code = max(semantic.inverse_codes) + 1
    if next_code % 2:
        next_code += 1
    latent_to_code: dict[int, int] = {}
    new_inverse_codes: dict[int, int] = {}
    pair_count = 0
    for latent in sorted(inverse_class):
        if latent in latent_to_code:
            continue
        opposite = inverse_class[latent]
        forward_code = next_code + 2 * pair_count
        inverse_code = forward_code + 1
        latent_to_code[latent] = forward_code
        latent_to_code[opposite] = inverse_code
        new_inverse_codes[forward_code] = inverse_code
        new_inverse_codes[inverse_code] = forward_code
        pair_count += 1

    extension_codes.update(
        {
            marker: latent_to_code[latent]
            for marker, latent in statement_class.items()
        }
    )
    extension_codes.update(
        {
            marker: latent_to_code[latent]
            for marker, latent in query_class.items()
        }
    )
    operations += len(residual_statements) * len(residual_queries) * 2
    return OntologyExtension(
        extension_codes,
        new_inverse_codes,
        operations,
        mapped_to_existing,
        pair_count,
    )


def extend_semantic_model(
    semantic: LearnedMeaning, extension: OntologyExtension
) -> LearnedMeaning:
    combined_inverse = {**semantic.inverse_codes, **extension.inverse_codes}
    if any(
        combined_inverse.get(combined_inverse.get(code, -1), -1) != code
        for code in combined_inverse
    ):
        raise ValueError("extended inverse map is not involutive")
    return LearnedMeaning(
        {**semantic.marker_codes, **extension.marker_codes},
        combined_inverse,
        semantic.training_operations + extension.training_operations,
    )


def predict_dynamic(model: LearnedMeaning, row: Record) -> tuple[bool, int]:
    graphs: dict[int, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    operations = 0
    for left, marker, right in row.facts:
        code = model.marker_codes[marker]
        relation, inverse = divmod(code, 2)
        if model.inverse_codes.get(code) != (code ^ 1):
            raise ValueError("dynamic runtime requires adjacent inverse codes")
        operations += 1
        if inverse:
            left, right = right, left
        graphs[relation][left].add(right)
    source, marker, target = row.query
    code = model.marker_codes[marker]
    relation, inverse = divmod(code, 2)
    if model.inverse_codes.get(code) != (code ^ 1):
        raise ValueError("dynamic runtime requires adjacent inverse codes")
    operations += 1
    if inverse:
        source, target = target, source
    frontier = [source]
    seen = {source}
    while frontier:
        current = frontier.pop()
        operations += 1
        for following in graphs[relation].get(current, ()):
            operations += 1
            if following == target:
                return True, operations
            if following not in seen:
                seen.add(following)
                frontier.append(following)
    return False, operations


def evaluate_dynamic(
    model: LearnedMeaning, records: Sequence[Record]
) -> DynamicEvaluation:
    predictions: list[bool | None] = []
    correct = 0
    coverage = 0
    operations = 0
    for row in records:
        try:
            prediction, used = predict_dynamic(model, row)
        except (KeyError, ValueError):
            predictions.append(None)
            continue
        predictions.append(prediction)
        coverage += 1
        operations += used
        correct += int(prediction == row.answer)
    return DynamicEvaluation(
        correct, len(records), coverage, operations, tuple(predictions)
    )


def evaluate_raw_dynamic(
    model: LearnedMeaning,
    bridge: SurfaceBridge,
    rows: Sequence[RawExample],
) -> DynamicEvaluation:
    parsed: list[Record] = []
    predictions: list[bool | None] = []
    correct = coverage = operations = 0
    for row in rows:
        try:
            record = parse_open_example(bridge, row)
            prediction, used = predict_dynamic(model, record)
        except (KeyError, ValueError):
            predictions.append(None)
            continue
        parsed.append(record)
        predictions.append(prediction)
        coverage += 1
        operations += used + len(row.text)
        correct += int(prediction == row.answer)
    return DynamicEvaluation(
        correct, len(rows), coverage, operations, tuple(predictions)
    )


def build_new_relation_heldout(
    *,
    statement_groups: Sequence[Sequence[str]] = NEW_STATEMENT_GROUPS,
    query_groups: Sequence[Sequence[str]] = NEW_QUERY_GROUPS,
    size: int = 128,
) -> tuple[Record, ...]:
    old_statement = STATEMENT_GROUPS[0][0]
    rows: list[Record] = []
    for index in range(size):
        chain_length = 2 + index % 4
        nodes = tuple(f"新概念{index:03d}_{position}" for position in range(chain_length + 1))
        facts = [
            (
                nodes[position],
                statement_groups[0][(index + position) % len(statement_groups[0])],
                nodes[position + 1],
            )
            for position in range(chain_length)
        ]
        distractor_left = f"旧概念{index:03d}甲"
        distractor_right = f"旧概念{index:03d}乙"
        facts.append((distractor_left, old_statement, distractor_right))
        direction = index % 2
        true_case = index % 4 < 2
        if direction == 0:
            source, target = nodes[0], nodes[-1]
        else:
            source, target = nodes[-1], nodes[0]
        if not true_case:
            target = distractor_left
        query_marker = query_groups[direction][index % len(query_groups[direction])]
        if index % 3:
            facts.reverse()
        rows.append(Record(tuple(facts), (source, query_marker, target), true_case))
    return tuple(rows)


def _renamed_groups(
    groups: Sequence[Sequence[str]], prefix: str
) -> tuple[tuple[str, ...], ...]:
    return tuple(tuple(prefix + marker for marker in group) for group in groups)


def exact_raw_memorizer_accuracy(
    training: Sequence[RawExample], heldout: Sequence[RawExample]
) -> float:
    table = {row.text: row.answer for row in training}
    majority = Counter(row.answer for row in training).most_common(1)[0][0]
    return sum(table.get(row.text, majority) == row.answer for row in heldout) / len(
        heldout
    )


def extension_payload_bytes(extension: OntologyExtension) -> int:
    raw = json.dumps(
        extension.payload(), ensure_ascii=False, sort_keys=True
    ).encode("utf-8")
    return len(zlib.compress(raw, level=9))


def learner_references_new_gold_groups() -> bool:
    learner_functions = (
        _try_existing_code,
        learn_ontology_extension,
        extend_semantic_model,
        predict_dynamic,
    )
    forbidden = {"NEW_STATEMENT_GROUPS", "NEW_QUERY_GROUPS"}
    return any(
        forbidden & set(function.__code__.co_names)
        for function in learner_functions
    )


def run_gate() -> dict[str, object]:
    semantic = learn_meaning(build_training_records())
    bridge = learn_surface_bridge(build_raw_training_records(), semantic)
    semantic_before = _fingerprint(semantic.payload())
    bridge_before = _fingerprint(bridge.payload())

    calibration = build_ontology_calibration(semantic)
    extension = learn_ontology_extension(calibration, bridge, semantic)
    extended = extend_semantic_model(semantic, extension)
    heldout_records = build_new_relation_heldout()
    heldout_raw = render_raw_heldout(heldout_records)
    heldout = evaluate_raw_dynamic(extended, bridge, heldout_raw)
    variant = evaluate_raw_dynamic(
        extended,
        bridge,
        render_raw_heldout(heldout_records, template_variant=2),
    )

    renamed_statement = _renamed_groups(NEW_STATEMENT_GROUPS, "別")
    renamed_query = _renamed_groups(NEW_QUERY_GROUPS, "別")
    renamed_calibration = build_ontology_calibration(
        semantic,
        statement_groups=renamed_statement,
        query_groups=renamed_query,
    )
    renamed_extension = learn_ontology_extension(
        renamed_calibration, bridge, semantic
    )
    renamed_model = extend_semantic_model(semantic, renamed_extension)
    renamed_heldout = build_new_relation_heldout(
        statement_groups=renamed_statement,
        query_groups=renamed_query,
    )
    renamed = evaluate_raw_dynamic(
        renamed_model,
        bridge,
        render_raw_heldout(renamed_heldout, template_variant=1),
    )

    duplicate_calibration = build_ontology_calibration(
        semantic,
        statement_groups=_renamed_groups(NEW_STATEMENT_GROUPS, "既"),
        query_groups=_renamed_groups(NEW_QUERY_GROUPS, "既"),
        duplicate_existing_pair=True,
    )
    duplicate_extension = learn_ontology_extension(
        duplicate_calibration, bridge, semantic
    )

    incomplete = tuple(
        row
        for row in calibration
        if not any(marker in row.text for marker in NEW_QUERY_GROUPS[1])
    )
    try:
        learn_ontology_extension(incomplete, bridge, semantic)
        incomplete_rejected = False
    except ValueError:
        incomplete_rejected = True

    contradictory = calibration + (
        RawExample(calibration[-1].text, not calibration[-1].answer),
    )
    try:
        learn_ontology_extension(contradictory, bridge, semantic)
        contradiction_rejected = False
    except ValueError:
        contradiction_rejected = True

    base_records = build_heldout_records(seed=20260717, size=128)
    old_predictions = tuple(predict(semantic, row)[0] for row in base_records)
    dynamic_predictions = evaluate_dynamic(semantic, base_records).predictions

    unknown = heldout_raw[0]
    present = next(
        marker
        for group in (*NEW_STATEMENT_GROUPS, *NEW_QUERY_GROUPS)
        for marker in group
        if marker in unknown.text
    )
    unknown_raw = RawExample(
        unknown.text.replace(present, "未登録新関係"), unknown.answer
    )
    unknown_result = evaluate_raw_dynamic(extended, bridge, (unknown_raw,))

    payload_bytes = extension_payload_bytes(extension)
    average_inference = heldout.inference_operations / heldout.total
    memorizer_accuracy = exact_raw_memorizer_accuracy(calibration, heldout_raw)
    checks = {
        "one_new_inverse_pair_allocated": extension.new_relation_pairs == 1,
        "four_new_markers_per_channel_grounded": (
            len(extension.marker_codes) == 8
        ),
        "new_codes_do_not_collide_with_frozen_ontology": (
            not (set(extension.inverse_codes) & set(semantic.inverse_codes))
        ),
        "heldout_accuracy_at_least_95_percent": heldout.accuracy >= 0.95,
        "heldout_coverage_at_least_95_percent": heldout.coverage_rate >= 0.95,
        "beats_exact_raw_memorizer_by_25_points": (
            heldout.accuracy - memorizer_accuracy >= 0.25
        ),
        "surface_and_order_variant_passes": (
            variant.accuracy >= 0.95 and variant.coverage_rate >= 0.95
        ),
        "renamed_ontology_is_relearned": (
            renamed.accuracy >= 0.95
            and renamed.coverage_rate >= 0.95
            and renamed_extension.new_relation_pairs == 1
        ),
        "existing_duplicate_does_not_allocate_new_pair": (
            duplicate_extension.new_relation_pairs == 0
            and duplicate_extension.mapped_to_existing == 8
        ),
        "incomplete_inverse_evidence_is_rejected": incomplete_rejected,
        "contradictory_evidence_is_rejected": contradiction_rejected,
        "old_runtime_predictions_are_preserved": (
            tuple(dynamic_predictions) == old_predictions
        ),
        "unregistered_new_relation_abstains": unknown_result.coverage == 0,
        "semantic_payload_is_frozen": (
            semantic_before == _fingerprint(semantic.payload())
        ),
        "surface_bridge_is_frozen": (
            bridge_before == _fingerprint(bridge.payload())
        ),
        "learner_has_no_new_gold_group_reference": (
            not learner_references_new_gold_groups()
        ),
        "extension_payload_within_4096_bytes": payload_bytes <= 4096,
        "training_compute_within_500k_operations": (
            extension.training_operations <= 500_000
        ),
        "average_inference_within_1024_operations": average_inference <= 1024,
    }
    return {
        "capability_id": CAPABILITY_ID,
        "capability": "data-driven ontology expansion with a new inverse relation pair",
        "claim": (
            "detect behavior unexplained by the frozen four-code ontology, "
            "allocate a new inverse pair, and reuse one generic graph runtime"
        ),
        "calibration_documents": len(calibration),
        "new_relation_pairs": extension.new_relation_pairs,
        "new_marker_mappings": len(extension.marker_codes),
        "new_inverse_codes": dict(sorted(extension.inverse_codes.items())),
        "heldout_documents": heldout.total,
        "heldout_accuracy": heldout.accuracy,
        "heldout_coverage": heldout.coverage_rate,
        "renamed_ontology_accuracy": renamed.accuracy,
        "exact_raw_memorizer_accuracy": memorizer_accuracy,
        "extension_payload_bytes": payload_bytes,
        "training_operations": extension.training_operations,
        "average_inference_operations": average_inference,
        "checks": checks,
        "passed": all(checks.values()),
        "arbitrary_ontology_learning": False,
        "unrestricted_japanese_understanding": False,
        "world_knowledge": False,
        "high_school_intelligence": False,
        "general_llm_parity": False,
    }


def render_markdown(result: Mapping[str, object]) -> str:
    lines = [
        "# CAP-SEM-005: ontology expansion from data",
        "",
        f"Passed: **{result['passed']}**",
        "",
        f"- Calibration documents: **{result['calibration_documents']}**",
        f"- New inverse relation pairs: **{result['new_relation_pairs']}**",
        f"- New marker mappings: **{result['new_marker_mappings']}**",
        f"- Held-out accuracy / coverage: **{result['heldout_accuracy']:.3f} / {result['heldout_coverage']:.3f}**",
        f"- Renamed-ontology accuracy: **{result['renamed_ontology_accuracy']:.3f}**",
        f"- Exact raw memorizer: **{result['exact_raw_memorizer_accuracy']:.3f}**",
        f"- Extension payload: **{result['extension_payload_bytes']} bytes**",
        f"- Training operations: **{result['training_operations']}**",
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
            "The learner allocates one additional directed inverse pair and the graph runtime is generalized from a fixed two-relation tuple to a relation-indexed dictionary. The new relation still has the same transitive directed-graph algebra as the earlier relations. This is not arbitrary concept formation, natural-language ontology induction, world knowledge, or high-school intelligence.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    result = run_gate()
    root = Path(__file__).resolve().parents[2]
    results_dir = root / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "cap_sem_005.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (results_dir / "cap_sem_005.md").write_text(
        render_markdown(result), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
