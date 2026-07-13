from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
from itertools import product
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

CAPABILITY_ID = "CAP-SEM-002"

STATEMENT_TEMPLATES = (
    "{left}は{right}より{marker}",
    "{right}より{left}が{marker}",
    "{marker}なのは{left}で相手は{right}",
)
QUERY_TEMPLATES = (
    "{left}は{right}より{marker}",
    "{right}に対して{left}が{marker}",
    "{marker}なのは{left}で比較相手は{right}",
)


@dataclass(frozen=True)
class RawExample:
    text: str
    answer: bool


@dataclass(frozen=True)
class SurfaceBridge:
    statement_separator: str
    query_terminator: str
    statement_skeletons: tuple[str, ...]
    query_skeletons: tuple[str, ...]
    statement_orientations: Mapping[str, int]
    query_orientations: Mapping[str, int]
    zero_error_assignments: int
    behavioral_classes: int
    orientation_assignments_evaluated: int

    def payload(self) -> Mapping[str, object]:
        return {
            "statement_separator": self.statement_separator,
            "query_terminator": self.query_terminator,
            "statement_skeletons": self.statement_skeletons,
            "query_skeletons": self.query_skeletons,
            "statement_orientations": dict(sorted(self.statement_orientations.items())),
            "query_orientations": dict(sorted(self.query_orientations.items())),
        }


@dataclass(frozen=True)
class RawEvaluation:
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


STATEMENT_MARKERS = tuple(
    sorted(
        {marker for group in STATEMENT_GROUPS for marker in group},
        key=lambda marker: (-len(marker), marker),
    )
)
QUERY_MARKERS = tuple(
    sorted(
        {marker for group in QUERY_GROUPS for marker in group},
        key=lambda marker: (-len(marker), marker),
    )
)


def _semantic_fingerprint(model: LearnedMeaning) -> str:
    payload = json.dumps(
        model.payload(), ensure_ascii=False, sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _entity_name(index: int, side: int, prefix: int = 0x3400) -> str:
    """Use unseen, contiguous symbols without leaking a linguistic name class."""
    base = prefix + 4 * (index * 2 + side)
    return chr(base) + chr(base + 1)


def _render(template: str, left: str, right: str, marker: str) -> str:
    return template.format(left=left, right=right, marker=marker)


def build_raw_training_records(
    *, statement_separator: str = "。", query_terminator: str = "？"
) -> tuple[RawExample, ...]:
    rows: list[RawExample] = []
    for index, structured in enumerate(build_training_records()):
        old_left, statement_marker, old_right = structured.facts[0]
        query_left, query_marker, query_right = structured.query
        left = _entity_name(index, 0)
        right = _entity_name(index, 1)
        rename = {old_left: left, old_right: right}
        statement = _render(
            STATEMENT_TEMPLATES[index % len(STATEMENT_TEMPLATES)],
            left,
            right,
            statement_marker,
        )
        query = _render(
            QUERY_TEMPLATES[(index // len(STATEMENT_TEMPLATES)) % len(QUERY_TEMPLATES)],
            rename[query_left],
            rename[query_right],
            query_marker,
        )
        rows.append(
            RawExample(
                statement + statement_separator + query + query_terminator,
                structured.answer,
            )
        )
    return tuple(rows)


def render_raw_heldout(
    records: Sequence[Record] | None = None,
    *,
    template_variant: int = 0,
    statement_separator: str = "。",
    query_terminator: str = "？",
) -> tuple[RawExample, ...]:
    source = build_heldout_records() if records is None else tuple(records)
    output: list[RawExample] = []
    for record_index, structured in enumerate(source):
        facts = [
            _render(
                STATEMENT_TEMPLATES[
                    (record_index + edge_index + template_variant)
                    % len(STATEMENT_TEMPLATES)
                ],
                left,
                right,
                marker,
            )
            for edge_index, (left, marker, right) in enumerate(structured.facts)
        ]
        if template_variant % 2:
            facts.reverse()
        query_left, query_marker, query_right = structured.query
        query = _render(
            QUERY_TEMPLATES[
                (2 * record_index + template_variant) % len(QUERY_TEMPLATES)
            ],
            query_left,
            query_right,
            query_marker,
        )
        output.append(
            RawExample(
                statement_separator.join(facts)
                + statement_separator
                + query
                + query_terminator,
                structured.answer,
            )
        )
    return tuple(output)


def _find_marker(clause: str, allowed: Sequence[str]) -> str:
    hits = [marker for marker in allowed if marker in clause]
    maximal = [
        marker
        for marker in hits
        if not any(marker != other and marker in other for other in hits)
    ]
    if len(maximal) != 1:
        raise ValueError("unknown or ambiguous relation marker")
    return maximal[0]


def _infer_delimiters(rows: Sequence[RawExample]) -> tuple[str, str]:
    if not rows:
        raise ValueError("empty raw training set")
    common_characters = sorted(
        set.intersection(*(set(row.text) for row in rows))
    )
    candidates: list[tuple[str, str]] = []
    for terminator in common_characters:
        if not all(row.text.endswith(terminator) for row in rows):
            continue
        for separator in common_characters:
            if separator == terminator:
                continue
            valid = True
            for row in rows:
                body = row.text[: -len(terminator)]
                pieces = body.split(separator)
                if len(pieces) != 2 or any(not piece for piece in pieces):
                    valid = False
                    break
            if valid:
                candidates.append((separator, terminator))
    if len(candidates) != 1:
        raise ValueError(f"delimiter grammar is not identifiable: {candidates}")
    return candidates[0]


def _document_frequencies(
    texts: Sequence[str], maximum_length: int = 12
) -> tuple[Counter[str], Counter[str]]:
    substring_frequency: Counter[str] = Counter()
    character_frequency: Counter[str] = Counter()
    for text in texts:
        character_frequency.update(set(text))
        seen: set[str] = set()
        for start in range(len(text)):
            for end in range(start + 2, min(len(text), start + maximum_length) + 1):
                seen.add(text[start:end])
        substring_frequency.update(seen)
    return substring_frequency, character_frequency


def _identify_entity_pair(
    fact: str,
    query: str,
    substring_frequency: Mapping[str, int],
    character_frequency: Mapping[str, int],
    document_count: int,
) -> tuple[str, str]:
    candidates: set[str] = set()
    marker_vocabulary = STATEMENT_MARKERS + QUERY_MARKERS
    rare_character_limit = max(2, document_count // 20)
    for start in range(len(fact)):
        for end in range(start + 2, min(len(fact), start + 12) + 1):
            candidate = fact[start:end]
            if candidate not in query:
                continue
            if any(
                marker in candidate or candidate in marker
                for marker in marker_vocabulary
            ):
                continue
            if substring_frequency.get(candidate, 0) > 2:
                continue
            if any(
                character_frequency.get(character, 0) > rare_character_limit
                for character in candidate
            ):
                continue
            candidates.add(candidate)
    maximal = sorted(
        (
            candidate
            for candidate in candidates
            if not any(
                candidate != other and candidate in other
                for other in candidates
            )
        ),
        key=lambda candidate: (-len(candidate), candidate),
    )
    for first in maximal:
        for second in maximal:
            if first >= second or first in second or second in first:
                continue
            if (
                fact.count(first)
                == query.count(first)
                == fact.count(second)
                == query.count(second)
                == 1
            ):
                return first, second
    raise ValueError("entity spans are not identifiable")


def _surface_skeleton(
    clause: str, entities: tuple[str, str], marker: str
) -> tuple[str, tuple[str, str]]:
    spans: list[tuple[int, int, str]] = []
    for entity in entities:
        start = clause.find(entity)
        spans.append((start, start + len(entity), entity))
    marker_start = clause.find(marker)
    spans.append((marker_start, marker_start + len(marker), "<M>"))
    spans.sort()
    if any(start < 0 for start, _, _ in spans):
        raise ValueError("missing entity or marker")
    if any(spans[index][1] > spans[index + 1][0] for index in range(2)):
        raise ValueError("overlapping surface spans")
    entity_spans = [span for span in spans if span[2] != "<M>"]
    label = {
        span[2]: f"<E{index}>" for index, span in enumerate(entity_spans)
    }
    output: list[str] = []
    captured: list[str] = []
    cursor = 0
    for start, end, value in spans:
        output.append(clause[cursor:start])
        if value == "<M>":
            output.append("<M>")
        else:
            output.append(label[value])
            captured.append(value)
        cursor = end
    output.append(clause[cursor:])
    return "".join(output), tuple(captured)  # type: ignore[return-value]


def _prepare_training_rows(
    rows: Sequence[RawExample], separator: str, terminator: str
):
    texts = [row.text for row in rows]
    substring_frequency, character_frequency = _document_frequencies(texts)
    prepared = []
    for row in rows:
        fact, query = row.text[: -len(terminator)].split(separator)
        statement_marker = _find_marker(fact, STATEMENT_MARKERS)
        query_marker = _find_marker(query, QUERY_MARKERS)
        entities = _identify_entity_pair(
            fact,
            query,
            substring_frequency,
            character_frequency,
            len(rows),
        )
        statement_skeleton, statement_entities = _surface_skeleton(
            fact, entities, statement_marker
        )
        query_skeleton, query_entities = _surface_skeleton(
            query, entities, query_marker
        )
        prepared.append(
            (
                statement_skeleton,
                query_skeleton,
                statement_entities,
                query_entities,
                statement_marker,
                query_marker,
                row.answer,
            )
        )
    return tuple(prepared)


def _structured_record(
    prepared,
    statement_orientations: Mapping[str, int],
    query_orientations: Mapping[str, int],
) -> Record:
    (
        statement_skeleton,
        query_skeleton,
        statement_entities,
        query_entities,
        statement_marker,
        query_marker,
        answer,
    ) = prepared
    fact_left, fact_right = (
        statement_entities
        if statement_orientations[statement_skeleton] == 0
        else statement_entities[::-1]
    )
    query_left, query_right = (
        query_entities
        if query_orientations[query_skeleton] == 0
        else query_entities[::-1]
    )
    return Record(
        ((fact_left, statement_marker, fact_right),),
        (query_left, query_marker, query_right),
        answer,
    )


def _orientation_probe_signature(
    semantic_model: LearnedMeaning,
    statement_skeletons: Sequence[str],
    query_skeletons: Sequence[str],
    statement_orientations: Mapping[str, int],
    query_orientations: Mapping[str, int],
) -> tuple[bool, ...]:
    output: list[bool] = []
    for statement_skeleton in statement_skeletons:
        for query_skeleton in query_skeletons:
            for statement_marker in STATEMENT_MARKERS:
                for query_marker in QUERY_MARKERS:
                    for reverse_query in (False, True):
                        statement_entities = ("甲", "乙")
                        query_entities = (
                            ("乙", "甲") if reverse_query else ("甲", "乙")
                        )
                        prepared = (
                            statement_skeleton,
                            query_skeleton,
                            statement_entities,
                            query_entities,
                            statement_marker,
                            query_marker,
                            False,
                        )
                        record = _structured_record(
                            prepared,
                            statement_orientations,
                            query_orientations,
                        )
                        output.append(predict(semantic_model, record)[0])
    return tuple(output)


def learn_surface_bridge(
    rows: Sequence[RawExample], semantic_model: LearnedMeaning
) -> SurfaceBridge:
    separator, terminator = _infer_delimiters(rows)
    prepared = _prepare_training_rows(rows, separator, terminator)
    statement_skeletons = tuple(sorted({row[0] for row in prepared}))
    query_skeletons = tuple(sorted({row[1] for row in prepared}))
    keys = tuple(f"S:{skeleton}" for skeleton in statement_skeletons) + tuple(
        f"Q:{skeleton}" for skeleton in query_skeletons
    )
    zero_error = []
    assignments_evaluated = 0
    for bits in product((0, 1), repeat=len(keys)):
        assignments_evaluated += 1
        raw = dict(zip(keys, bits))
        statement_orientations = {
            skeleton: raw[f"S:{skeleton}"]
            for skeleton in statement_skeletons
        }
        query_orientations = {
            skeleton: raw[f"Q:{skeleton}"] for skeleton in query_skeletons
        }
        errors = 0
        for row in prepared:
            structured = _structured_record(
                row, statement_orientations, query_orientations
            )
            errors += int(predict(semantic_model, structured)[0] != row[-1])
        if errors == 0:
            zero_error.append((statement_orientations, query_orientations))
    if not zero_error:
        raise ValueError("no surface bridge fits final truth labels")
    signatures = {
        _orientation_probe_signature(
            semantic_model,
            statement_skeletons,
            query_skeletons,
            statement_orientations,
            query_orientations,
        )
        for statement_orientations, query_orientations in zero_error
    }
    if len(signatures) != 1:
        raise ValueError("zero-error surface bridges are behaviorally ambiguous")
    statement_orientations, query_orientations = min(
        zero_error,
        key=lambda pair: (
            tuple(sorted(pair[0].items())),
            tuple(sorted(pair[1].items())),
        ),
    )
    return SurfaceBridge(
        separator,
        terminator,
        statement_skeletons,
        query_skeletons,
        statement_orientations,
        query_orientations,
        len(zero_error),
        len(signatures),
        assignments_evaluated,
    )


def _compile_skeleton(skeleton: str, markers: Sequence[str]):
    pieces = re.split(r"(<E0>|<E1>|<M>)", skeleton)
    output: list[str] = []
    for piece in pieces:
        if piece == "<E0>":
            output.append("(?P<e0>.+?)")
        elif piece == "<E1>":
            output.append("(?P<e1>.+?)")
        elif piece == "<M>":
            output.append(
                "(?P<marker>" + "|".join(map(re.escape, markers)) + ")"
            )
        else:
            output.append(re.escape(piece))
    return re.compile("^" + "".join(output) + "$")


def _parse_clause(
    clause: str,
    skeletons: Sequence[str],
    markers: Sequence[str],
    orientations: Mapping[str, int],
) -> tuple[str, str, str]:
    matches = []
    for skeleton in skeletons:
        match = _compile_skeleton(skeleton, markers).fullmatch(clause)
        if match is None or match.group("e0") == match.group("e1"):
            continue
        pair = (match.group("e0"), match.group("e1"))
        if orientations[skeleton] == 1:
            pair = pair[::-1]
        matches.append((pair[0], match.group("marker"), pair[1]))
    if len(matches) != 1:
        raise ValueError("raw clause has zero or multiple parses")
    return matches[0]


def parse_raw_example(bridge: SurfaceBridge, example: RawExample) -> Record:
    if not example.text.endswith(bridge.query_terminator):
        raise ValueError("unknown query terminator")
    body = example.text[: -len(bridge.query_terminator)]
    clauses = body.split(bridge.statement_separator)
    if len(clauses) < 2 or any(not clause for clause in clauses):
        raise ValueError("invalid clause segmentation")
    facts = tuple(
        _parse_clause(
            clause,
            bridge.statement_skeletons,
            STATEMENT_MARKERS,
            bridge.statement_orientations,
        )
        for clause in clauses[:-1]
    )
    query = _parse_clause(
        clauses[-1],
        bridge.query_skeletons,
        QUERY_MARKERS,
        bridge.query_orientations,
    )
    return Record(facts, query, example.answer)


def evaluate_raw(
    bridge: SurfaceBridge,
    semantic_model: LearnedMeaning,
    rows: Sequence[RawExample],
) -> RawEvaluation:
    correct = 0
    coverage = 0
    operations = 0
    for row in rows:
        try:
            parsed = parse_raw_example(bridge, row)
        except (KeyError, ValueError):
            continue
        coverage += 1
        prediction, used = predict(semantic_model, parsed)
        correct += int(prediction == row.answer)
        operations += used
    return RawEvaluation(correct, len(rows), coverage, operations)


def learned_bridge_payload_bytes(bridge: SurfaceBridge) -> int:
    payload = json.dumps(
        bridge.payload(), ensure_ascii=False, sort_keys=True
    ).encode("utf-8")
    return len(zlib.compress(payload, level=9))


def exact_text_memorizer_accuracy(
    train: Sequence[RawExample], heldout: Sequence[RawExample]
) -> float:
    table = {row.text: row.answer for row in train}
    majority = Counter(row.answer for row in train).most_common(1)[0][0]
    correct = sum(table.get(row.text, majority) == row.answer for row in heldout)
    return correct / len(heldout)


def run_gate() -> dict[str, object]:
    semantic_model = learn_meaning(build_training_records())
    semantic_before = _semantic_fingerprint(semantic_model)
    train = build_raw_training_records()
    bridge = learn_surface_bridge(train, semantic_model)
    heldout = render_raw_heldout()
    evaluation = evaluate_raw(bridge, semantic_model, heldout)
    variants = {
        f"template_and_order_variant_{variant}": evaluate_raw(
            bridge,
            semantic_model,
            render_raw_heldout(template_variant=variant),
        )
        for variant in (1, 2)
    }
    alternate_train = build_raw_training_records(
        statement_separator="；", query_terminator="！"
    )
    alternate_bridge = learn_surface_bridge(alternate_train, semantic_model)
    alternate_evaluation = evaluate_raw(
        alternate_bridge,
        semantic_model,
        render_raw_heldout(
            template_variant=2,
            statement_separator="；",
            query_terminator="！",
        ),
    )
    semantic_after = _semantic_fingerprint(semantic_model)
    payload_bytes = learned_bridge_payload_bytes(bridge)
    memorizer_accuracy = exact_text_memorizer_accuracy(train, heldout)
    average_semantic_operations = (
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
        "template_and_fact_order_invariant": all(
            result.accuracy >= 0.95 and result.coverage_rate >= 0.95
            for result in variants.values()
        ),
        "punctuation_roles_are_relearned": (
            alternate_bridge.statement_separator == "；"
            and alternate_bridge.query_terminator == "！"
            and alternate_evaluation.accuracy >= 0.95
            and alternate_evaluation.coverage_rate >= 0.95
        ),
        "semantic_runtime_is_frozen": semantic_before == semantic_after,
        "raw_train_and_heldout_are_disjoint": not (
            {row.text for row in train} & {row.text for row in heldout}
        ),
        "three_statement_and_query_templates_induced": (
            len(bridge.statement_skeletons) == 3
            and len(bridge.query_skeletons) == 3
        ),
        "orientation_behavior_is_identifiable": bridge.behavioral_classes == 1,
        "bridge_payload_within_4096_bytes": payload_bytes <= 4096,
        "average_semantic_inference_within_128_operations": (
            average_semantic_operations <= 128
        ),
    }
    return {
        "capability_id": CAPABILITY_ID,
        "capability": "raw controlled-Japanese clause and argument grounding",
        "claim": (
            "continuous controlled-Japanese surface bridge into the frozen "
            "CAP-SEM-001 relational runtime"
        ),
        "train_records": len(train),
        "heldout_records": len(heldout),
        "heldout_accuracy": evaluation.accuracy,
        "heldout_coverage": evaluation.coverage_rate,
        "exact_text_memorizer_accuracy": memorizer_accuracy,
        "variant_accuracies": {
            name: result.accuracy for name, result in variants.items()
        },
        "alternate_punctuation_accuracy": alternate_evaluation.accuracy,
        "statement_separator": bridge.statement_separator,
        "query_terminator": bridge.query_terminator,
        "statement_skeletons": bridge.statement_skeletons,
        "query_skeletons": bridge.query_skeletons,
        "orientation_assignments_evaluated": (
            bridge.orientation_assignments_evaluated
        ),
        "zero_error_orientation_assignments": bridge.zero_error_assignments,
        "behavioral_orientation_classes": bridge.behavioral_classes,
        "learned_bridge_payload_bytes": payload_bytes,
        "semantic_model_fingerprint": semantic_before,
        "average_semantic_inference_operations": average_semantic_operations,
        "checks": checks,
        "passed": all(checks.values()),
        "unrestricted_japanese_understanding": False,
        "open_domain_semantics": False,
        "high_school_intelligence": False,
        "general_llm_parity": False,
    }


def render_markdown(result: Mapping[str, object]) -> str:
    lines = [
        f"# {result['capability_id']}: raw Japanese surface bridge",
        "",
        f"Passed: **{result['passed']}**",
        "",
        f"- Training records: **{result['train_records']}**",
        f"- Held-out records: **{result['heldout_records']}**",
        f"- Held-out accuracy: **{result['heldout_accuracy']:.3f}**",
        f"- Held-out coverage: **{result['heldout_coverage']:.3f}**",
        (
            "- Exact raw-text memorizer: "
            f"**{result['exact_text_memorizer_accuracy']:.3f}**"
        ),
        (
            "- Learned bridge payload: "
            f"**{result['learned_bridge_payload_bytes']} bytes**"
        ),
        (
            "- Orientation assignments evaluated: "
            f"**{result['orientation_assignments_evaluated']}**"
        ),
        "",
        "## Induced surface grammar",
        "",
        f"- Statement separator: `{result['statement_separator']}`",
        f"- Query terminator: `{result['query_terminator']}`",
    ]
    for skeleton in result["statement_skeletons"]:
        lines.append(f"- statement: `{skeleton}`")
    for skeleton in result["query_skeletons"]:
        lines.append(f"- query: `{skeleton}`")
    lines.extend(["", "## Checks", ""])
    for name, value in result["checks"].items():
        lines.append(f"- {name}: **{value}**")
    lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            "- The CAP-SEM-001 meaning map and graph runtime are frozen.",
            "- Clause separators, entity spans, template literals, and argument direction are induced from raw controlled strings plus final truth labels.",
            "- The relation vocabulary is inherited from CAP-SEM-001; this does not discover arbitrary new Japanese words.",
            "- The grammar remains synthetic and controlled. It is not unrestricted Japanese, world knowledge, dialogue, or high-school intelligence.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    result = run_gate()
    root = Path(__file__).resolve().parents[2]
    results_dir = root / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "cap_sem_002.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (results_dir / "cap_sem_002.md").write_text(
        render_markdown(result), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
