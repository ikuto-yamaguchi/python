from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations, product
import json
import marshal
from pathlib import Path
from typing import Mapping, Sequence
import unicodedata
import zlib

from .cap_sem_001_relational_meaning import (
    Evaluation,
    LearnedMeaning,
    Record,
    build_heldout_records,
    build_training_records,
    evaluate,
    learn_meaning,
    metamorphic_records,
    predict as semantic_predict,
)

CAPABILITY_ID = "CAP-SEM-002"

MAX_ENTITY_CHARACTERS = 10
MAX_DELIMITER_CHARACTERS = 6
MAX_MARKER_CHARACTERS = 8
MAX_QUERY_SUFFIX_CHARACTERS = 3
MAX_CANDIDATE_NGRAMS = 24
MAX_CANDIDATE_PAIRS = 16


@dataclass(frozen=True)
class RawRecord:
    text: str
    answer: bool


@dataclass(frozen=True)
class SurfaceFrame:
    first_delimiter: str
    second_delimiter: str
    reverse_arguments: bool

    def payload(self) -> dict[str, object]:
        return {
            "first_delimiter": self.first_delimiter,
            "second_delimiter": self.second_delimiter,
            "reverse_arguments": self.reverse_arguments,
        }


@dataclass(frozen=True)
class ParserSearchResult:
    frames: tuple[SurfaceFrame, ...]
    query_suffix: str
    candidate_ngrams: int
    candidate_pairs: int
    equivalent_best_models: int
    calibration_accuracy: float
    training_operations: int


@dataclass(frozen=True)
class RawSemanticModel:
    frames: tuple[SurfaceFrame, ...]
    query_suffix: str
    semantic: LearnedMeaning
    training_operations: int

    def payload(self) -> dict[str, object]:
        return {
            "frames": [frame.payload() for frame in self.frames],
            "query_suffix": self.query_suffix,
            "semantic": self.semantic.payload(),
        }


@dataclass(frozen=True)
class RawEvaluation:
    correct: int
    total: int
    answered: int
    inference_operations: int
    predictions: tuple[bool | None, ...]

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0

    @property
    def coverage(self) -> float:
        return self.answered / self.total if self.total else 0.0


def split_raw_clauses(text: str) -> tuple[tuple[str, ...], int]:
    clauses: list[str] = []
    current: list[str] = []
    operations = 0
    for character in unicodedata.normalize("NFKC", text):
        operations += 1
        if unicodedata.category(character).startswith("P"):
            if current:
                clauses.append("".join(current))
                current = []
        elif not character.isspace():
            current.append(character)
    if current:
        clauses.append("".join(current))
    return tuple(clauses), operations


def learn_query_suffix(
    raw_records: Sequence[RawRecord],
) -> tuple[str, int]:
    queries: list[str] = []
    operations = 0
    for row in raw_records:
        clauses, used = split_raw_clauses(row.text)
        operations += used
        if len(clauses) < 2:
            raise ValueError("every training document needs facts and a query")
        queries.append(clauses[-1])

    reversed_suffix: list[str] = []
    for characters in zip(*(query[::-1] for query in queries)):
        operations += len(characters)
        if (
            len(set(characters)) != 1
            or len(reversed_suffix) >= MAX_QUERY_SUFFIX_CHARACTERS
        ):
            break
        reversed_suffix.append(characters[0])
    suffix = "".join(reversed_suffix)[::-1]
    if not suffix:
        raise ValueError("query suffix is not identifiable")
    return suffix, operations


def parse_with_delimiters(
    clause: str,
    delimiters: tuple[str, str],
) -> tuple[tuple[str, str, str] | None, int]:
    first_delimiter, second_delimiter = delimiters
    matches: list[tuple[str, str, str]] = []
    operations = 0
    start = 0
    while True:
        first = clause.find(first_delimiter, start)
        operations += 1
        if first < 0:
            break
        second = clause.find(
            second_delimiter,
            first + len(first_delimiter) + 1,
        )
        operations += 1
        if second >= 0:
            first_entity = clause[:first]
            second_entity = clause[
                first + len(first_delimiter) : second
            ]
            marker = clause[second + len(second_delimiter) :]
            if (
                1 <= len(first_entity) <= MAX_ENTITY_CHARACTERS
                and 1 <= len(second_entity) <= MAX_ENTITY_CHARACTERS
                and 1 <= len(marker) <= MAX_MARKER_CHARACTERS
            ):
                matches.append((first_entity, second_entity, marker))
        start = first + 1

    unique = tuple(dict.fromkeys(matches))
    if len(unique) != 1:
        return None, operations
    return unique[0], operations


def collect_training_clauses(
    raw_records: Sequence[RawRecord],
    query_suffix: str,
) -> tuple[tuple[str, ...], int]:
    clauses: list[str] = []
    operations = 0
    for row in raw_records:
        document, used = split_raw_clauses(row.text)
        operations += used
        for index, clause in enumerate(document):
            if index == len(document) - 1:
                if not clause.endswith(query_suffix):
                    continue
                clause = clause[: -len(query_suffix)]
            clauses.append(clause)
    return tuple(clauses), operations


def candidate_delimiter_pairs(
    raw_records: Sequence[RawRecord],
    query_suffix: str,
) -> tuple[tuple[tuple[str, str], ...], int, int]:
    clauses, operations = collect_training_clauses(
        raw_records, query_suffix
    )
    substring_coverage: Counter[str] = Counter()
    for clause in clauses:
        seen: set[str] = set()
        for start in range(len(clause)):
            for length in range(
                1,
                min(
                    MAX_DELIMITER_CHARACTERS,
                    len(clause) - start,
                )
                + 1,
            ):
                seen.add(clause[start : start + length])
                operations += 1
        substring_coverage.update(seen)

    minimum_coverage = max(1, len(clauses) // 5)
    ngrams = tuple(
        substring
        for substring, coverage in sorted(
            substring_coverage.items(),
            key=lambda row: (-row[1], -len(row[0]), row[0]),
        )
        if coverage >= minimum_coverage
    )[:MAX_CANDIDATE_NGRAMS]

    candidates: list[tuple[int, int, tuple[str, str]]] = []
    for first in ngrams:
        for second in ngrams:
            if first == second:
                continue
            coverage = 0
            for clause in clauses:
                parsed, used = parse_with_delimiters(
                    clause, (first, second)
                )
                operations += used
                coverage += int(parsed is not None)
            if coverage >= minimum_coverage:
                candidates.append(
                    (coverage, len(first) + len(second), (first, second))
                )
    candidates.sort(key=lambda row: (-row[0], -row[1], row[2]))
    return (
        tuple(row[2] for row in candidates[:MAX_CANDIDATE_PAIRS]),
        len(ngrams),
        operations,
    )


def parse_surface_clause(
    clause: str,
    frames: Sequence[SurfaceFrame],
) -> tuple[tuple[str, str, str] | None, int]:
    matches: list[
        tuple[int, int, tuple[str, str, str]]
    ] = []
    operations = 0
    for index, frame in enumerate(frames):
        parsed, used = parse_with_delimiters(
            clause,
            (frame.first_delimiter, frame.second_delimiter),
        )
        operations += used
        if parsed is None:
            continue
        first_entity, second_entity, marker = parsed
        left, right = (
            (second_entity, first_entity)
            if frame.reverse_arguments
            else (first_entity, second_entity)
        )
        matches.append(
            (
                len(frame.first_delimiter)
                + len(frame.second_delimiter),
                index,
                (left, marker, right),
            )
        )
    if not matches:
        return None, operations
    best_length = max(row[0] for row in matches)
    best = tuple(row for row in matches if row[0] == best_length)
    if len(best) != 1:
        return None, operations
    return best[0][2], operations


def parse_raw_record(
    row: RawRecord,
    frames: Sequence[SurfaceFrame],
    query_suffix: str,
) -> tuple[Record | None, int]:
    clauses, operations = split_raw_clauses(row.text)
    if len(clauses) < 2:
        return None, operations

    facts: list[tuple[str, str, str]] = []
    for clause in clauses[:-1]:
        parsed, used = parse_surface_clause(clause, frames)
        operations += used
        if parsed is None:
            return None, operations
        facts.append(parsed)

    query_clause = clauses[-1]
    if not query_clause.endswith(query_suffix):
        return None, operations
    query, used = parse_surface_clause(
        query_clause[: -len(query_suffix)],
        frames,
    )
    operations += used
    if query is None:
        return None, operations
    return Record(tuple(facts), query, row.answer), operations


def _rename_record(row: Record, record_index: int) -> Record:
    entities = sorted(
        {part for fact in row.facts for part in (fact[0], fact[2])}
        | {row.query[0], row.query[2]}
    )
    mapping = {
        entity: f"校{record_index:02x}{position:x}"
        for position, entity in enumerate(entities)
    }
    facts = tuple(
        (mapping[left], marker, mapping[right])
        for left, marker, right in row.facts
    )
    left, marker, right = row.query
    return Record(
        facts,
        (mapping[left], marker, mapping[right]),
        row.answer,
    )


def build_parser_calibration_records() -> tuple[Record, ...]:
    return tuple(
        _rename_record(row, index)
        for index, row in enumerate(
            build_heldout_records(seed=20260712, size=64)
        )
    )


def render_surface_clause(
    clause: tuple[str, str, str],
    frame_index: int,
) -> str:
    left, marker, right = clause
    if frame_index == 0:
        return f"{left}は{right}に対して{marker}"
    if frame_index == 1:
        return f"{right}を基準に{left}は{marker}"
    raise ValueError(frame_index)


def render_raw_record(
    row: Record,
    index: int,
    *,
    frame_shift: int = 0,
    punctuation: tuple[str, ...] = ("。", "！"),
) -> RawRecord:
    chunks: list[str] = []
    for fact_index, fact in enumerate(row.facts):
        chunks.append(
            render_surface_clause(
                fact,
                (index + fact_index + frame_shift) % 2,
            )
            + punctuation[(index + fact_index) % len(punctuation)]
        )
    chunks.append(
        render_surface_clause(
            row.query,
            (index + len(row.facts) + 1 + frame_shift) % 2,
        )
        + "か？"
    )
    return RawRecord("".join(chunks), row.answer)


def render_raw_records(
    rows: Sequence[Record],
    *,
    offset: int = 0,
    frame_shift: int = 0,
    punctuation: tuple[str, ...] = ("。", "！"),
) -> tuple[RawRecord, ...]:
    return tuple(
        render_raw_record(
            row,
            offset + index,
            frame_shift=frame_shift,
            punctuation=punctuation,
        )
        for index, row in enumerate(rows)
    )


def induce_surface_parser(
    raw_training: Sequence[RawRecord],
    raw_calibration: Sequence[RawRecord],
) -> ParserSearchResult:
    combined = (*raw_training, *raw_calibration)
    query_suffix, operations = learn_query_suffix(combined)
    pairs, candidate_ngrams, used = candidate_delimiter_pairs(
        combined, query_suffix
    )
    operations += used

    models: list[
        tuple[
            float,
            int,
            tuple[SurfaceFrame, ...],
            tuple[bool, ...],
        ]
    ] = []
    for first_pair, second_pair in combinations(pairs, 2):
        for first_reverse, second_reverse in product(
            (False, True), repeat=2
        ):
            frames = (
                SurfaceFrame(
                    first_pair[0],
                    first_pair[1],
                    first_reverse,
                ),
                SurfaceFrame(
                    second_pair[0],
                    second_pair[1],
                    second_reverse,
                ),
            )
            parsed_training: list[Record] = []
            parsed_calibration: list[Record] = []
            valid = True
            for source, target in (
                (raw_training, parsed_training),
                (raw_calibration, parsed_calibration),
            ):
                for raw_row in source:
                    parsed, parse_operations = parse_raw_record(
                        raw_row, frames, query_suffix
                    )
                    operations += parse_operations
                    if parsed is None:
                        valid = False
                        break
                    target.append(parsed)
                if not valid:
                    break
            if not valid:
                continue
            try:
                semantic = learn_meaning(parsed_training)
                operations += semantic.training_operations
                calibration = evaluate(
                    semantic, parsed_calibration
                )
                operations += calibration.inference_operations
            except ValueError:
                continue
            description_units = (
                sum(
                    len(frame.first_delimiter)
                    + len(frame.second_delimiter)
                    + 1
                    for frame in frames
                )
                + len(query_suffix)
            )
            models.append(
                (
                    calibration.accuracy,
                    -description_units,
                    frames,
                    calibration.predictions,
                )
            )

    if not models:
        raise ValueError("no surface parser explains the calibration data")
    models.sort(
        key=lambda row: (
            -row[0],
            -row[1],
            repr(row[2]),
        )
    )
    best_key = models[0][:2]
    best = tuple(row for row in models if row[:2] == best_key)
    if not all(row[3] == best[0][3] for row in best):
        raise ValueError(
            "minimum-description parser remains behaviorally ambiguous"
        )
    return ParserSearchResult(
        frames=best[0][2],
        query_suffix=query_suffix,
        candidate_ngrams=candidate_ngrams,
        candidate_pairs=len(pairs),
        equivalent_best_models=len(best),
        calibration_accuracy=best[0][0],
        training_operations=operations,
    )


def fit_raw_semantic_model(
    parser: ParserSearchResult,
    raw_training: Sequence[RawRecord],
) -> RawSemanticModel:
    parsed: list[Record] = []
    operations = parser.training_operations
    for row in raw_training:
        tokenized, used = parse_raw_record(
            row, parser.frames, parser.query_suffix
        )
        operations += used
        if tokenized is None:
            raise ValueError("selected parser does not cover training")
        parsed.append(tokenized)
    semantic = learn_meaning(parsed)
    operations += semantic.training_operations
    return RawSemanticModel(
        parser.frames,
        parser.query_suffix,
        semantic,
        operations,
    )


def predict_raw(
    model: RawSemanticModel,
    row: RawRecord,
) -> tuple[bool | None, int]:
    parsed, operations = parse_raw_record(
        row, model.frames, model.query_suffix
    )
    if parsed is None:
        return None, operations
    prediction, semantic_operations = semantic_predict(
        model.semantic, parsed
    )
    return prediction, operations + semantic_operations


def evaluate_raw(
    model: RawSemanticModel,
    rows: Sequence[RawRecord],
) -> RawEvaluation:
    predictions: list[bool | None] = []
    correct = 0
    answered = 0
    operations = 0
    for row in rows:
        prediction, used = predict_raw(model, row)
        operations += used
        predictions.append(prediction)
        if prediction is None:
            continue
        answered += 1
        correct += int(prediction == row.answer)
    return RawEvaluation(
        correct,
        len(rows),
        answered,
        operations,
        tuple(predictions),
    )


def exact_raw_memorization_baseline(
    training: Sequence[RawRecord],
    heldout: Sequence[RawRecord],
) -> RawEvaluation:
    table = {row.text: row.answer for row in training}
    majority = Counter(row.answer for row in training).most_common(1)[0][0]
    predictions = tuple(
        table.get(row.text, majority) for row in heldout
    )
    correct = sum(
        prediction == row.answer
        for prediction, row in zip(predictions, heldout)
    )
    return RawEvaluation(
        correct,
        len(heldout),
        len(heldout),
        len(heldout),
        predictions,
    )


def learned_payload_bytes(model: RawSemanticModel) -> int:
    raw = json.dumps(
        model.payload(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return len(zlib.compress(raw, level=9))


def executable_description_bits() -> int:
    functions = (
        split_raw_clauses,
        learn_query_suffix,
        parse_with_delimiters,
        candidate_delimiter_pairs,
        parse_surface_clause,
        parse_raw_record,
        induce_surface_parser,
        fit_raw_semantic_model,
        predict_raw,
        learn_meaning,
        semantic_predict,
    )
    payload = b"".join(
        marshal.dumps(function.__code__) for function in functions
    )
    return 8 * len(zlib.compress(payload, level=9))


def learner_references_surface_generator() -> bool:
    learner_functions = (
        candidate_delimiter_pairs,
        induce_surface_parser,
        parse_raw_record,
    )
    forbidden = {"render_surface_clause", "render_raw_record"}
    return any(
        forbidden & set(function.__code__.co_names)
        for function in learner_functions
    )


@lru_cache(maxsize=1)
def run_gate() -> dict[str, object]:
    tokenized_training = build_training_records()
    parser_calibration = build_parser_calibration_records()
    raw_training = render_raw_records(tokenized_training)
    raw_calibration = render_raw_records(
        parser_calibration, offset=1000
    )

    parser = induce_surface_parser(
        raw_training, raw_calibration
    )
    model = fit_raw_semantic_model(parser, raw_training)

    heldout_tokens = build_heldout_records(
        seed=20260713, size=128
    )
    raw_heldout = render_raw_records(
        heldout_tokens,
        offset=2000,
        punctuation=("。", "！", "；"),
    )
    heldout = evaluate_raw(model, raw_heldout)
    memorization = exact_raw_memorization_baseline(
        raw_training, raw_heldout
    )

    token_variants = metamorphic_records(heldout_tokens)
    token_variants["entity_renaming"] = tuple(
        _rename_record(row, 128 + index)
        for index, row in enumerate(heldout_tokens)
    )
    variants: dict[str, tuple[RawRecord, ...]] = {
        name: render_raw_records(
            rows,
            offset=3000,
            punctuation=("；", "。", "！"),
        )
        for name, rows in token_variants.items()
    }
    variants["surface_frame_swap"] = render_raw_records(
        heldout_tokens,
        offset=2000,
        frame_shift=1,
        punctuation=("。", "！", "；"),
    )
    variants["punctuation_shift"] = render_raw_records(
        heldout_tokens,
        offset=4000,
        punctuation=("；", "！"),
    )
    variant_results = {
        name: evaluate_raw(model, rows)
        for name, rows in variants.items()
    }

    payload_bytes = learned_payload_bytes(model)
    executable_bits = executable_description_bits()
    average_inference_operations = (
        heldout.inference_operations / heldout.total
    )
    invariant = all(
        result.predictions == heldout.predictions
        for result in variant_results.values()
    )
    checks = {
        "parser_calibration_is_perfect": (
            parser.calibration_accuracy == 1.0
        ),
        "only_global_role_inversion_remains": (
            parser.equivalent_best_models == 2
        ),
        "heldout_accuracy_at_least_95_percent": (
            heldout.accuracy >= 0.95
        ),
        "heldout_coverage_is_complete": heldout.coverage == 1.0,
        "beats_raw_memorization_by_25_points": (
            heldout.accuracy - memorization.accuracy >= 0.25
        ),
        "all_metamorphic_accuracies_at_least_95_percent": all(
            result.accuracy >= 0.95
            and result.coverage == 1.0
            for result in variant_results.values()
        ),
        "surface_and_token_variants_are_prediction_invariant": invariant,
        "raw_training_has_no_whitespace_or_supplied_slots": all(
            not any(character.isspace() for character in row.text)
            for row in (*raw_training, *raw_calibration)
        ),
        "learner_does_not_reference_surface_generator": (
            not learner_references_surface_generator()
        ),
        "learned_payload_within_8192_bytes": payload_bytes <= 8192,
        "executable_description_within_400k_bits": (
            executable_bits <= 400_000
        ),
        "training_compute_within_10m_operations": (
            model.training_operations <= 10_000_000
        ),
        "average_inference_within_512_operations": (
            average_inference_operations <= 512
        ),
    }
    return {
        "capability_id": CAPABILITY_ID,
        "capability": (
            "controlled raw Japanese clause and argument grounding"
        ),
        "claim": (
            "finite-hypothesis surface grammar induction connected to "
            "the frozen CAP-SEM-001 semantic runtime"
        ),
        "training_documents": len(raw_training),
        "parser_calibration_documents": len(raw_calibration),
        "heldout_documents": len(raw_heldout),
        "candidate_ngrams": parser.candidate_ngrams,
        "candidate_pairs": parser.candidate_pairs,
        "equivalent_best_models": parser.equivalent_best_models,
        "learned_frames": [
            frame.payload() for frame in parser.frames
        ],
        "learned_query_suffix": parser.query_suffix,
        "parser_calibration_accuracy": parser.calibration_accuracy,
        "heldout_accuracy": heldout.accuracy,
        "heldout_coverage": heldout.coverage,
        "raw_memorization_accuracy": memorization.accuracy,
        "variant_accuracies": {
            name: result.accuracy
            for name, result in variant_results.items()
        },
        "variant_coverages": {
            name: result.coverage
            for name, result in variant_results.items()
        },
        "learned_payload_bytes": payload_bytes,
        "executable_total_description_bits": executable_bits,
        "training_operations": model.training_operations,
        "average_inference_operations": average_inference_operations,
        "checks": checks,
        "passed": all(checks.values()),
        "controlled_raw_japanese_grounding": True,
        "unrestricted_japanese_understanding": False,
        "open_domain_semantics": False,
        "high_school_intelligence": False,
        "general_llm_parity": False,
    }


def render_markdown(result: Mapping[str, object]) -> str:
    lines = [
        f"# {result['capability_id']}: raw Japanese grounding",
        "",
        f"Passed: **{result['passed']}**",
        "",
        f"- Held-out accuracy: **{result['heldout_accuracy']:.3f}**",
        f"- Held-out coverage: **{result['heldout_coverage']:.3f}**",
        (
            "- Exact raw memorization baseline: "
            f"**{result['raw_memorization_accuracy']:.3f}**"
        ),
        (
            "- Parser calibration accuracy: "
            f"**{result['parser_calibration_accuracy']:.3f}**"
        ),
        (
            "- Equivalent minimum-description parsers: "
            f"**{result['equivalent_best_models']}**"
        ),
        f"- Learned payload: **{result['learned_payload_bytes']} bytes**",
        (
            "- Executable total description: "
            f"**{result['executable_total_description_bits']} bits**"
        ),
        f"- Training operations: **{result['training_operations']}**",
        (
            "- Average inference operations: "
            f"**{result['average_inference_operations']:.1f}**"
        ),
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
            (
                "- The learner receives only continuous raw strings and "
                "final Boolean labels; fact/query tuples and argument slots "
                "are not supplied."
            ),
            (
                "- Unicode punctuation and a last-clause query prior remain "
                "part of the declared hypothesis family."
            ),
            (
                "- Surface grammar search is finite, two-slot, and "
                "predicate-final. Passing is not unrestricted Japanese "
                "parsing or open-domain semantic understanding."
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    result = run_gate()
    root = Path(__file__).resolve().parents[2]
    results_dir = root / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "cap_sem_002.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (results_dir / "cap_sem_002.md").write_text(
        render_markdown(result), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
