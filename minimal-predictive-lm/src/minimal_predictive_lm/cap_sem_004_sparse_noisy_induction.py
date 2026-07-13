from __future__ import annotations

from collections import Counter, defaultdict
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
    RawExample,
    SurfaceBridge,
    build_raw_training_records,
    learn_surface_bridge,
    render_raw_heldout,
)
from .cap_sem_003_open_relation_grounding import (
    NOVEL_QUERY_GROUPS,
    NOVEL_STATEMENT_GROUPS,
    OpenLexicon,
    OpenRelationModel,
    _anchor_by_code,
    evaluate_open,
    exact_raw_memorizer_accuracy,
    parse_open_example,
)

CAPABILITY_ID = "CAP-SEM-004"

DEFAULT_DEFINITION_TEMPLATES = (
    ("「{left}」は「{right}」と同じ向きである。", 0),
    ("比較すると「{left}」と「{right}」は同じ向きだ。", 0),
    ("「{left}」は「{right}」の逆向きである。", 1),
    ("比較すると「{left}」と「{right}」は逆向きだ。", 1),
)
ALTERNATE_DEFINITION_TEMPLATES = (
    ("「{left}」と「{right}」は一致方向にある。", 0),
    ("方向関係では「{left}」と「{right}」が一致する。", 0),
    ("「{left}」と「{right}」は反転方向にある。", 1),
    ("方向関係では「{left}」と「{right}」が反転する。", 1),
)


@dataclass(frozen=True)
class EvidenceDocument:
    text: str
    answer: bool | None


@dataclass(frozen=True)
class SparseEvidenceCorpus:
    documents: tuple[EvidenceDocument, ...]
    statement_groups: tuple[tuple[str, ...], ...]
    query_groups: tuple[tuple[str, ...], ...]
    intentionally_corrupted: int


@dataclass(frozen=True)
class SparseLexicon:
    statement_codes: Mapping[str, int]
    query_codes: Mapping[str, int]
    connector_deltas: Mapping[str, int]
    training_operations: int
    evidence_documents: int
    accepted_corruptions: int

    def payload(self) -> Mapping[str, object]:
        return {
            "statement_codes": dict(sorted(self.statement_codes.items())),
            "query_codes": dict(sorted(self.query_codes.items())),
            "connector_deltas": dict(sorted(self.connector_deltas.items())),
        }


@dataclass(frozen=True)
class ParsedUsage:
    target: str
    target_is_query: bool
    record: Record


QUOTE_PATTERN = re.compile(r"「([^」]+)」")


def _fingerprint(payload: Mapping[str, object]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _definition_skeleton(text: str) -> tuple[tuple[str, str], str]:
    matches = tuple(QUOTE_PATTERN.finditer(text))
    if len(matches) != 2:
        raise ValueError("definition must contain exactly two quoted expressions")
    terms = (matches[0].group(1), matches[1].group(1))
    output: list[str] = []
    cursor = 0
    for index, match in enumerate(matches):
        output.append(text[cursor : match.start()])
        output.append(f"<T{index}>")
        cursor = match.end()
    output.append(text[cursor:])
    return terms, "".join(output)


def _render_definition(
    left: str,
    right: str,
    templates: Sequence[tuple[str, int]],
    template_index: int,
) -> str:
    template, _ = templates[template_index % len(templates)]
    return template.format(left=left, right=right)


def _learn_connector_deltas(
    definitions: Sequence[str], semantic: LearnedMeaning
) -> tuple[dict[str, int], int]:
    observed: dict[str, set[int]] = defaultdict(set)
    operations = 0
    for text in definitions:
        (left, right), skeleton = _definition_skeleton(text)
        operations += len(text)
        if left not in semantic.marker_codes or right not in semantic.marker_codes:
            continue
        delta = semantic.marker_codes[left] ^ semantic.marker_codes[right]
        if delta not in (0, 1):
            continue
        observed[skeleton].add(delta)
    learned: dict[str, int] = {}
    for skeleton, deltas in observed.items():
        if len(deltas) != 1:
            raise ValueError("definition connector is behaviorally ambiguous")
        learned[skeleton] = next(iter(deltas))
    if len(learned) < 4:
        raise ValueError("insufficient known-known definition calibration")
    return learned, operations


def _definition_proposals(
    definitions: Sequence[str],
    connector_deltas: Mapping[str, int],
    semantic: LearnedMeaning,
) -> tuple[dict[str, list[int]], int]:
    proposals: dict[str, list[int]] = defaultdict(list)
    operations = 0
    for text in definitions:
        (left, right), skeleton = _definition_skeleton(text)
        operations += len(text)
        if skeleton not in connector_deltas:
            continue
        left_known = left in semantic.marker_codes
        right_known = right in semantic.marker_codes
        if left_known == right_known:
            continue
        unknown, known = (right, left) if left_known else (left, right)
        proposals[unknown].append(
            semantic.marker_codes[known] ^ connector_deltas[skeleton]
        )
    return dict(proposals), operations


def _usage_target(record: Record, semantic: LearnedMeaning) -> tuple[str, bool]:
    statement_unknown = {
        marker
        for _, marker, _ in record.facts
        if marker not in semantic.marker_codes
    }
    query_unknown = (
        {record.query[1]} if record.query[1] not in semantic.marker_codes else set()
    )
    if len(statement_unknown) + len(query_unknown) != 1:
        raise ValueError("usage document must contain exactly one unknown marker")
    if query_unknown:
        return next(iter(query_unknown)), True
    return next(iter(statement_unknown)), False


def _parse_usages(
    documents: Sequence[EvidenceDocument],
    bridge: SurfaceBridge,
    semantic: LearnedMeaning,
) -> tuple[tuple[ParsedUsage, ...], int]:
    parsed: list[ParsedUsage] = []
    operations = 0
    for document in documents:
        if document.answer is None:
            continue
        raw = RawExample(document.text, document.answer)
        record = parse_open_example(bridge, raw)
        target, target_is_query = _usage_target(record, semantic)
        parsed.append(ParsedUsage(target, target_is_query, record))
        operations += len(document.text) * (
            len(bridge.statement_skeletons) + len(bridge.query_skeletons)
        )
    return tuple(parsed), operations


def _rewrite_candidate(
    usage: ParsedUsage,
    semantic: LearnedMeaning,
    candidate_code: int,
) -> Record:
    statement_anchors = _anchor_by_code(semantic, query=False)
    query_anchors = _anchor_by_code(semantic, query=True)
    facts = []
    for left, marker, right in usage.record.facts:
        if marker == usage.target and not usage.target_is_query:
            marker = statement_anchors[candidate_code]
        elif marker not in semantic.marker_codes:
            raise KeyError(marker)
        facts.append((left, marker, right))
    left, marker, right = usage.record.query
    if marker == usage.target and usage.target_is_query:
        marker = query_anchors[candidate_code]
    elif marker not in semantic.marker_codes:
        raise KeyError(marker)
    return Record(tuple(facts), (left, marker, right), usage.record.answer)


def _infer_sparse_code(
    target: str,
    target_usages: Sequence[ParsedUsage],
    proposals: Sequence[int],
    semantic: LearnedMeaning,
    *,
    minimum_usages: int = 4,
    maximum_error_fraction: float = 0.25,
) -> tuple[int, int, int]:
    if len(target_usages) < minimum_usages or not proposals:
        raise ValueError(f"insufficient sparse evidence for {target}")
    scored: list[tuple[int, int]] = []
    operations = 0
    for candidate_code in sorted(semantic.inverse_codes):
        errors = sum(proposal != candidate_code for proposal in proposals)
        for usage in target_usages:
            prediction, used = predict(
                semantic, _rewrite_candidate(usage, semantic, candidate_code)
            )
            operations += used + 1
            errors += int(prediction != usage.record.answer)
        scored.append((errors, candidate_code))
    scored.sort()
    evidence_count = len(target_usages) + len(proposals)
    if len(scored) < 2 or scored[0][0] == scored[1][0]:
        raise ValueError(f"sparse evidence remains ambiguous for {target}")
    if scored[0][0] / evidence_count > maximum_error_fraction:
        raise ValueError(f"noise exceeds robust evidence budget for {target}")
    return scored[0][1], operations, scored[0][0]


def learn_sparse_lexicon(
    corpus: SparseEvidenceCorpus,
    bridge: SurfaceBridge,
    semantic: LearnedMeaning,
) -> SparseLexicon:
    definitions = tuple(
        document.text for document in corpus.documents if document.answer is None
    )
    connectors, operations = _learn_connector_deltas(definitions, semantic)
    proposals, used = _definition_proposals(definitions, connectors, semantic)
    operations += used
    usages, used = _parse_usages(corpus.documents, bridge, semantic)
    operations += used
    by_target: dict[str, list[ParsedUsage]] = defaultdict(list)
    channels: dict[str, set[bool]] = defaultdict(set)
    for usage in usages:
        by_target[usage.target].append(usage)
        channels[usage.target].add(usage.target_is_query)
    targets = sorted(set(proposals) | set(by_target))
    statement_codes: dict[str, int] = {}
    query_codes: dict[str, int] = {}
    accepted_corruptions = 0
    for target in targets:
        if len(channels[target]) != 1:
            raise ValueError(f"marker channel is missing or ambiguous: {target}")
        code, used, errors = _infer_sparse_code(
            target,
            by_target[target],
            proposals.get(target, ()),
            semantic,
        )
        operations += used
        accepted_corruptions += errors
        if next(iter(channels[target])):
            query_codes[target] = code
        else:
            statement_codes[target] = code
    if not statement_codes or not query_codes:
        raise ValueError("both statement and query vocabularies are required")
    return SparseLexicon(
        statement_codes,
        query_codes,
        connectors,
        operations,
        len(corpus.documents),
        accepted_corruptions,
    )


def _group_by_semantic_code(
    semantic: LearnedMeaning,
    known_groups: Sequence[Sequence[str]],
    novel_groups: Sequence[Sequence[str]],
) -> dict[int, tuple[str, ...]]:
    return {
        semantic.marker_codes[known_group[0]]: tuple(novel_group)
        for known_group, novel_group in zip(known_groups, novel_groups)
    }


def _renamed_groups(
    groups: Sequence[Sequence[str]], prefix: str
) -> tuple[tuple[str, ...], ...]:
    return tuple(
        tuple(prefix + marker for marker in group) for group in groups
    )


def _definition_calibration(
    semantic: LearnedMeaning,
    templates: Sequence[tuple[str, int]],
) -> list[EvidenceDocument]:
    statement_anchors = _anchor_by_code(semantic, query=False)
    query_anchors = _anchor_by_code(semantic, query=True)
    roots = sorted({min(code, semantic.inverse_codes[code]) for code in semantic.inverse_codes})
    documents: list[EvidenceDocument] = []
    for template_index, (_, delta) in enumerate(templates):
        anchors = statement_anchors if template_index % 2 == 0 else query_anchors
        for root in roots:
            left = anchors[root]
            right = anchors[root ^ delta]
            documents.append(
                EvidenceDocument(
                    _render_definition(left, right, templates, template_index),
                    None,
                )
            )
    return documents


def _usage_record(
    semantic: LearnedMeaning,
    target: str,
    target_code: int,
    *,
    target_is_query: bool,
    contrast_code: int,
    reverse: bool,
    index: int,
) -> RawExample:
    statement_anchors = _anchor_by_code(semantic, query=False)
    query_anchors = _anchor_by_code(semantic, query=True)
    roots = sorted({min(code, semantic.inverse_codes[code]) for code in semantic.inverse_codes})
    other_root = next(root for root in roots if root != contrast_code)
    a, b = f"用{index:04x}甲", f"用{index:04x}乙"
    x, y = f"用{index:04x}外甲", f"用{index:04x}外乙"
    if target_is_query:
        facts = (
            (a, statement_anchors[contrast_code], b),
            (x, statement_anchors[other_root], y),
        )
        query = (b, target, a) if reverse else (a, target, b)
        gold_query = (
            b,
            query_anchors[target_code],
            a,
        ) if reverse else (
            a,
            query_anchors[target_code],
            b,
        )
        gold = Record(facts, gold_query, False)
        answer = predict(semantic, gold)[0]
        raw = Record(facts, query, answer)
    else:
        facts = (
            (a, target, b),
            (x, statement_anchors[other_root], y),
        )
        query = (
            b,
            query_anchors[contrast_code],
            a,
        ) if reverse else (
            a,
            query_anchors[contrast_code],
            b,
        )
        gold_facts = (
            (a, statement_anchors[target_code], b),
            facts[1],
        )
        gold = Record(gold_facts, query, False)
        answer = predict(semantic, gold)[0]
        raw = Record(facts, query, answer)
    return render_raw_heldout((raw,), template_variant=index % 3)[0]


def _multihop_usage(
    semantic: LearnedMeaning,
    target: str,
    target_code: int,
    *,
    target_is_query: bool,
    index: int,
) -> RawExample:
    statement_anchors = _anchor_by_code(semantic, query=False)
    query_anchors = _anchor_by_code(semantic, query=True)
    roots = sorted({min(code, semantic.inverse_codes[code]) for code in semantic.inverse_codes})
    other_root = next(root for root in roots if root != min(target_code, semantic.inverse_codes[target_code]))
    a, b, c = f"鎖{index:04x}甲", f"鎖{index:04x}乙", f"鎖{index:04x}丙"
    x, y = f"鎖{index:04x}外甲", f"鎖{index:04x}外乙"
    if target_is_query:
        facts = (
            (a, statement_anchors[target_code], b),
            (b, statement_anchors[target_code], c),
            (x, statement_anchors[other_root], y),
        )
        gold = Record(facts, (a, query_anchors[target_code], c), False)
        answer = predict(semantic, gold)[0]
        raw = Record(facts, (a, target, c), answer)
    else:
        facts = (
            (a, target, b),
            (b, statement_anchors[target_code], c),
            (x, statement_anchors[other_root], y),
        )
        gold_facts = (
            (a, statement_anchors[target_code], b),
            facts[1],
            facts[2],
        )
        query = (a, query_anchors[target_code], c)
        answer = predict(semantic, Record(gold_facts, query, False))[0]
        raw = Record(facts, query, answer)
    return render_raw_heldout((raw,), template_variant=(index + 1) % 3)[0]


def build_sparse_evidence_corpus(
    semantic: LearnedMeaning,
    *,
    statement_groups: Sequence[Sequence[str]] = NOVEL_STATEMENT_GROUPS,
    query_groups: Sequence[Sequence[str]] = NOVEL_QUERY_GROUPS,
    definition_templates: Sequence[tuple[str, int]] = DEFAULT_DEFINITION_TEMPLATES,
    usage_limit: int = 5,
    noise_per_marker: int = 1,
) -> SparseEvidenceCorpus:
    statement_groups = tuple(tuple(group) for group in statement_groups)
    query_groups = tuple(tuple(group) for group in query_groups)
    statement_by_code = _group_by_semantic_code(
        semantic, STATEMENT_GROUPS, statement_groups
    )
    query_by_code = _group_by_semantic_code(semantic, QUERY_GROUPS, query_groups)
    statement_anchors = _anchor_by_code(semantic, query=False)
    query_anchors = _anchor_by_code(semantic, query=True)
    roots = sorted({min(code, semantic.inverse_codes[code]) for code in semantic.inverse_codes})
    documents = _definition_calibration(semantic, definition_templates)
    corrupted = 0
    marker_index = 0
    for target_is_query, groups_by_code, anchors in (
        (False, statement_by_code, statement_anchors),
        (True, query_by_code, query_anchors),
    ):
        for gold_code in sorted(groups_by_code):
            for target in groups_by_code[gold_code]:
                template_index = marker_index % len(definition_templates)
                _, connector_delta = definition_templates[template_index]
                anchor_code = gold_code ^ connector_delta
                definition_is_noisy = noise_per_marker > 0 and marker_index % 2 == 0
                if definition_is_noisy:
                    anchor_code ^= 1
                    corrupted += 1
                documents.append(
                    EvidenceDocument(
                        _render_definition(
                            target,
                            anchors[anchor_code],
                            definition_templates,
                            template_index,
                        ),
                        None,
                    )
                )
                usages: list[RawExample] = []
                for root in roots:
                    for reverse in (False, True):
                        usages.append(
                            _usage_record(
                                semantic,
                                target,
                                gold_code,
                                target_is_query=target_is_query,
                                contrast_code=root,
                                reverse=reverse,
                                index=marker_index * 10 + len(usages),
                            )
                        )
                usages.append(
                    _multihop_usage(
                        semantic,
                        target,
                        gold_code,
                        target_is_query=target_is_query,
                        index=marker_index,
                    )
                )
                usages = usages[:usage_limit]
                if noise_per_marker > 0 and not definition_is_noisy and usages:
                    flips = min(noise_per_marker, len(usages))
                    for usage_index in range(flips):
                        usage = usages[usage_index]
                        usages[usage_index] = RawExample(usage.text, not usage.answer)
                        corrupted += 1
                documents.extend(
                    EvidenceDocument(usage.text, usage.answer) for usage in usages
                )
                marker_index += 1
    documents.sort(
        key=lambda document: hashlib.sha256(
            document.text.encode("utf-8")
            + (b"N" if document.answer is None else bytes([document.answer]))
        ).digest()
    )
    return SparseEvidenceCorpus(
        tuple(documents), statement_groups, query_groups, corrupted
    )


def _novelize_with_groups(
    semantic: LearnedMeaning,
    rows: Sequence[Record],
    statement_groups: Sequence[Sequence[str]],
    query_groups: Sequence[Sequence[str]],
) -> tuple[Record, ...]:
    statement_by_code = _group_by_semantic_code(
        semantic, STATEMENT_GROUPS, statement_groups
    )
    query_by_code = _group_by_semantic_code(
        semantic, QUERY_GROUPS, query_groups
    )
    output: list[Record] = []
    for index, row in enumerate(rows):
        facts = []
        for edge_index, (left, marker, right) in enumerate(row.facts):
            code = semantic.marker_codes[marker]
            group = statement_by_code[code]
            facts.append((left, group[(index + edge_index) % len(group)], right))
        left, marker, right = row.query
        code = semantic.marker_codes[marker]
        group = query_by_code[code]
        output.append(
            Record(tuple(facts), (left, group[index % len(group)], right), row.answer)
        )
    return tuple(output)


def _open_model(
    bridge: SurfaceBridge,
    semantic: LearnedMeaning,
    lexicon: SparseLexicon,
) -> OpenRelationModel:
    return OpenRelationModel(
        bridge,
        OpenLexicon(
            lexicon.statement_codes,
            lexicon.query_codes,
            lexicon.training_operations,
        ),
        semantic,
    )


def sparse_payload_bytes(lexicon: SparseLexicon) -> int:
    raw = json.dumps(
        lexicon.payload(), ensure_ascii=False, sort_keys=True
    ).encode("utf-8")
    return len(zlib.compress(raw, level=9))


def learner_references_hidden_groups() -> bool:
    learner_functions = (
        _learn_connector_deltas,
        _definition_proposals,
        _parse_usages,
        _infer_sparse_code,
        learn_sparse_lexicon,
    )
    forbidden = {
        "NOVEL_STATEMENT_GROUPS",
        "NOVEL_QUERY_GROUPS",
        "STATEMENT_GROUPS",
        "QUERY_GROUPS",
    }
    return any(
        forbidden & set(function.__code__.co_names)
        for function in learner_functions
    )


def run_gate() -> dict[str, object]:
    semantic = learn_meaning(build_training_records())
    bridge = learn_surface_bridge(build_raw_training_records(), semantic)
    semantic_before = _fingerprint(semantic.payload())
    bridge_before = _fingerprint(bridge.payload())

    corpus = build_sparse_evidence_corpus(semantic)
    lexicon = learn_sparse_lexicon(corpus, bridge, semantic)
    model = _open_model(bridge, semantic, lexicon)
    heldout_records = _novelize_with_groups(
        semantic,
        build_heldout_records(seed=20260715, size=128),
        corpus.statement_groups,
        corpus.query_groups,
    )
    heldout_raw = render_raw_heldout(heldout_records)
    heldout = evaluate_open(model, heldout_raw)
    variant = evaluate_open(
        model, render_raw_heldout(heldout_records, template_variant=2)
    )

    renamed_statement = _renamed_groups(corpus.statement_groups, "新")
    renamed_query = _renamed_groups(corpus.query_groups, "新")
    renamed_corpus = build_sparse_evidence_corpus(
        semantic,
        statement_groups=renamed_statement,
        query_groups=renamed_query,
        definition_templates=ALTERNATE_DEFINITION_TEMPLATES,
    )
    renamed_lexicon = learn_sparse_lexicon(renamed_corpus, bridge, semantic)
    renamed_model = _open_model(bridge, semantic, renamed_lexicon)
    renamed_records = _novelize_with_groups(
        semantic,
        build_heldout_records(seed=20260716, size=128),
        renamed_statement,
        renamed_query,
    )
    renamed = evaluate_open(
        renamed_model,
        render_raw_heldout(renamed_records, template_variant=1),
    )

    try:
        learn_sparse_lexicon(
            build_sparse_evidence_corpus(semantic, usage_limit=2),
            bridge,
            semantic,
        )
        insufficient_rejected = False
    except ValueError:
        insufficient_rejected = True

    try:
        learn_sparse_lexicon(
            build_sparse_evidence_corpus(
                semantic, noise_per_marker=3
            ),
            bridge,
            semantic,
        )
        overnoise_rejected = False
    except ValueError:
        overnoise_rejected = True

    unknown_text = heldout_raw[0].text
    known_markers = tuple(
        marker
        for marker in (*lexicon.statement_codes, *lexicon.query_codes)
        if marker in unknown_text
    )
    if not known_markers:
        raise ValueError("unknown control lacks a learned marker")
    unknown_row = RawExample(
        unknown_text.replace(known_markers[0], "未登録関係"),
        heldout_raw[0].answer,
    )
    unknown = evaluate_open(model, (unknown_row,))

    payload_bytes = sparse_payload_bytes(lexicon)
    average_inference = heldout.inference_operations / heldout.total
    memorizer_accuracy = exact_raw_memorizer_accuracy(
        tuple(
            RawExample(document.text, bool(document.answer))
            for document in corpus.documents
            if document.answer is not None
        ),
        heldout_raw,
    )
    checks = {
        "heldout_accuracy_at_least_95_percent": heldout.accuracy >= 0.95,
        "heldout_coverage_at_least_95_percent": heldout.coverage_rate >= 0.95,
        "beats_exact_raw_memorizer_by_25_points": (
            heldout.accuracy - memorizer_accuracy >= 0.25
        ),
        "template_and_order_variant_passes": (
            variant.accuracy >= 0.95 and variant.coverage_rate >= 0.95
        ),
        "renamed_vocabulary_and_definition_connectors_relearn": (
            renamed.accuracy >= 0.95 and renamed.coverage_rate >= 0.95
        ),
        "all_sixteen_markers_grounded": (
            len(lexicon.statement_codes) == 8
            and len(lexicon.query_codes) == 8
        ),
        "one_corruption_per_marker_is_tolerated": (
            lexicon.accepted_corruptions >= 16
            and corpus.intentionally_corrupted == 16
        ),
        "insufficient_evidence_is_rejected": insufficient_rejected,
        "excess_noise_is_rejected": overnoise_rejected,
        "unregistered_marker_abstains": unknown.coverage == 0,
        "semantic_runtime_is_frozen": (
            semantic_before == _fingerprint(semantic.payload())
        ),
        "surface_bridge_is_frozen": (
            bridge_before == _fingerprint(bridge.payload())
        ),
        "learner_has_no_hidden_group_reference": (
            not learner_references_hidden_groups()
        ),
        "learned_payload_within_4096_bytes": payload_bytes <= 4096,
        "training_compute_within_500k_operations": (
            lexicon.training_operations <= 500_000
        ),
        "average_inference_within_1024_operations": average_inference <= 1024,
    }
    return {
        "capability_id": CAPABILITY_ID,
        "capability": "sparse noisy definition and ordinary-usage induction",
        "claim": (
            "robustly ground opaque relation expressions from sparse definitions "
            "and multi-fact usage while freezing the semantic runtime"
        ),
        "evidence_documents": len(corpus.documents),
        "definition_documents": sum(
            document.answer is None for document in corpus.documents
        ),
        "usage_documents": sum(
            document.answer is not None for document in corpus.documents
        ),
        "intentionally_corrupted_documents": corpus.intentionally_corrupted,
        "accepted_corruptions": lexicon.accepted_corruptions,
        "learned_statement_markers": len(lexicon.statement_codes),
        "learned_query_markers": len(lexicon.query_codes),
        "heldout_documents": heldout.total,
        "heldout_accuracy": heldout.accuracy,
        "heldout_coverage": heldout.coverage_rate,
        "renamed_connector_accuracy": renamed.accuracy,
        "exact_raw_memorizer_accuracy": memorizer_accuracy,
        "learned_payload_bytes": payload_bytes,
        "training_operations": lexicon.training_operations,
        "average_inference_operations": average_inference,
        "checks": checks,
        "passed": all(checks.values()),
        "unrestricted_dictionary_learning": False,
        "new_relation_concept_creation": False,
        "unrestricted_japanese_understanding": False,
        "high_school_intelligence": False,
        "general_llm_parity": False,
    }


def render_markdown(result: Mapping[str, object]) -> str:
    lines = [
        "# CAP-SEM-004: sparse noisy definition and usage induction",
        "",
        f"Passed: **{result['passed']}**",
        "",
        f"- Evidence documents: **{result['evidence_documents']}**",
        f"- Definitions / usages: **{result['definition_documents']} / {result['usage_documents']}**",
        f"- Intentionally corrupted: **{result['intentionally_corrupted_documents']}**",
        f"- Learned statement/query markers: **{result['learned_statement_markers']} / {result['learned_query_markers']}**",
        f"- Held-out accuracy / coverage: **{result['heldout_accuracy']:.3f} / {result['heldout_coverage']:.3f}**",
        f"- Renamed connector accuracy: **{result['renamed_connector_accuracy']:.3f}**",
        f"- Exact raw memorizer: **{result['exact_raw_memorizer_accuracy']:.3f}**",
        f"- Learned payload: **{result['learned_payload_bytes']} bytes**",
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
            "This replaces the complete code-by-direction contrast table with a small definition, four contrast usages, one multi-hop usage, and one corrupted observation per marker. The definition connector meanings are calibrated from known-known examples rather than hard-coded. The corpus and grammar remain synthetic and controlled, and every new term is still mapped into one of four existing latent relation codes.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    result = run_gate()
    root = Path(__file__).resolve().parents[2]
    results_dir = root / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "cap_sem_004.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (results_dir / "cap_sem_004.md").write_text(
        render_markdown(result), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
