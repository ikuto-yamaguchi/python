from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import json
import marshal
from pathlib import Path
import random
from typing import Iterable, Mapping, Sequence
import zlib

CAPABILITY_ID = "CAP-SEM-001"

STATEMENT_GROUPS = (
    ("さき", "まえ", "先行"),
    ("あと", "うしろ", "後続"),
    ("なか", "内部", "内側"),
    ("つつむ", "含む", "外側"),
)
QUERY_GROUPS = (
    ("よりまえ", "に先行", "以前"),
    ("よりあと", "に後続", "以後"),
    ("のなか", "の内部", "内包される"),
    ("をつつむ", "を含む", "外包する"),
)
INVERSE_GROUP = {0: 1, 1: 0, 2: 3, 3: 2}


@dataclass(frozen=True)
class Record:
    facts: tuple[tuple[str, str, str], ...]
    query: tuple[str, str, str]
    answer: bool


@dataclass(frozen=True)
class LearnedMeaning:
    marker_codes: Mapping[str, int]
    inverse_codes: Mapping[int, int]
    training_operations: int

    def payload(self) -> dict[str, object]:
        return {
            "marker_codes": dict(sorted(self.marker_codes.items())),
            "inverse_codes": {
                str(key): value for key, value in sorted(self.inverse_codes.items())
            },
        }


@dataclass(frozen=True)
class Evaluation:
    correct: int
    total: int
    inference_operations: int
    predictions: tuple[bool, ...]

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0


def _all_statement_markers() -> tuple[str, ...]:
    return tuple(marker for group in STATEMENT_GROUPS for marker in group)


def _all_query_markers() -> tuple[str, ...]:
    return tuple(marker for group in QUERY_GROUPS for marker in group)


def _gold_code(marker: str) -> int:
    for code, group in enumerate(STATEMENT_GROUPS):
        if marker in group:
            return code
    for code, group in enumerate(QUERY_GROUPS):
        if marker in group:
            return code
    raise KeyError(marker)


def build_training_records() -> tuple[Record, ...]:
    """Create weak supervision: tokenized clauses plus final truth labels only."""
    rows: list[Record] = []
    statements = _all_statement_markers()
    queries = _all_query_markers()
    names = ("アオ", "キ", "ミドリ", "シロ", "クロ", "アカ")
    for statement_index, statement in enumerate(statements):
        for query_index, query in enumerate(queries):
            left = names[(statement_index + query_index) % len(names)]
            right = names[(statement_index + query_index + 1) % len(names)]
            statement_code = _gold_code(statement)
            query_code = _gold_code(query)
            rows.append(
                Record(
                    facts=((left, statement, right),),
                    query=(left, query, right),
                    answer=statement_code == query_code,
                )
            )
            rows.append(
                Record(
                    facts=((left, statement, right),),
                    query=(right, query, left),
                    answer=INVERSE_GROUP[statement_code] == query_code,
                )
            )
    return tuple(rows)


def _single_fact_signature(
    records: Sequence[Record],
    statement_markers: Sequence[str],
    query_markers: Sequence[str],
) -> tuple[dict[str, tuple[bool, ...]], dict[str, tuple[bool, ...]], int]:
    same: dict[tuple[str, str], bool] = {}
    reverse: dict[tuple[str, str], bool] = {}
    operations = 0
    for row in records:
        if len(row.facts) != 1:
            continue
        fact_left, statement, fact_right = row.facts[0]
        query_left, query, query_right = row.query
        operations += 1
        if (query_left, query_right) == (fact_left, fact_right):
            same[(statement, query)] = row.answer
        elif (query_left, query_right) == (fact_right, fact_left):
            reverse[(statement, query)] = row.answer
    same_signature = {
        statement: tuple(
            bool(same.get((statement, query), False)) for query in query_markers
        )
        for statement in statement_markers
    }
    reverse_signature = {
        statement: tuple(
            bool(reverse.get((statement, query), False)) for query in query_markers
        )
        for statement in statement_markers
    }
    return same_signature, reverse_signature, operations


def learn_meaning(records: Sequence[Record]) -> LearnedMeaning:
    statement_markers = tuple(
        sorted({fact[1] for row in records for fact in row.facts})
    )
    query_markers = tuple(sorted({row.query[1] for row in records}))
    same, reverse, operations = _single_fact_signature(
        records, statement_markers, query_markers
    )

    query_columns: dict[str, tuple[bool, ...]] = {
        query: tuple(same[statement][index] for statement in statement_markers)
        for index, query in enumerate(query_markers)
    }
    unique_columns = sorted(set(query_columns.values()))
    if len(unique_columns) != 4:
        raise ValueError(
            f"expected four latent semantic classes, got {len(unique_columns)}"
        )
    column_to_class = {
        column: index for index, column in enumerate(unique_columns)
    }
    query_class = {
        query: column_to_class[column] for query, column in query_columns.items()
    }

    statement_class: dict[str, int] = {}
    inverse_class: dict[int, int] = {}
    for statement in statement_markers:
        same_hits = [
            query_class[query]
            for index, query in enumerate(query_markers)
            if same[statement][index]
        ]
        reverse_hits = [
            query_class[query]
            for index, query in enumerate(query_markers)
            if reverse[statement][index]
        ]
        if len(set(same_hits)) != 1 or len(set(reverse_hits)) != 1:
            raise ValueError("non-identifiable marker signatures")
        current = same_hits[0]
        opposite = reverse_hits[0]
        statement_class[statement] = current
        previous = inverse_class.setdefault(current, opposite)
        if previous != opposite:
            raise ValueError("inconsistent inverse relation")

    if any(
        inverse_class.get(inverse_class.get(code, -1), -1) != code
        for code in inverse_class
    ):
        raise ValueError("inverse mapping is not involutive")

    semantic_code: dict[int, int] = {}
    relation = 0
    for latent_class in sorted(inverse_class):
        if latent_class in semantic_code:
            continue
        opposite = inverse_class[latent_class]
        if opposite == latent_class:
            raise ValueError(
                "self-inverse classes are outside this capability gate"
            )
        semantic_code[latent_class] = 2 * relation
        semantic_code[opposite] = 2 * relation + 1
        relation += 1
    if relation != 2:
        raise ValueError(f"expected two relation pairs, got {relation}")

    marker_codes = {
        marker: semantic_code[latent]
        for marker, latent in statement_class.items()
    }
    marker_codes.update(
        {
            marker: semantic_code[latent]
            for marker, latent in query_class.items()
        }
    )
    inverse_codes = {code: code ^ 1 for code in range(4)}
    operations += len(statement_markers) * len(query_markers) * 2
    return LearnedMeaning(marker_codes, inverse_codes, operations)


def _decode(code: int) -> tuple[int, bool]:
    return code // 2, bool(code % 2)


def predict(model: LearnedMeaning, row: Record) -> tuple[bool, int]:
    graphs: tuple[dict[str, set[str]], ...] = (
        defaultdict(set),
        defaultdict(set),
    )
    operations = 0
    for left, marker, right in row.facts:
        relation, inverse = _decode(model.marker_codes[marker])
        operations += 1
        if inverse:
            left, right = right, left
        graphs[relation][left].add(right)

    source, marker, target = row.query
    relation, inverse = _decode(model.marker_codes[marker])
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


def evaluate(
    model: LearnedMeaning, records: Sequence[Record]
) -> Evaluation:
    predictions: list[bool] = []
    correct = 0
    operations = 0
    for row in records:
        prediction, used = predict(model, row)
        predictions.append(prediction)
        correct += int(prediction == row.answer)
        operations += used
    return Evaluation(correct, len(records), operations, tuple(predictions))


def build_heldout_records(
    seed: int = 20260713, size: int = 128
) -> tuple[Record, ...]:
    rng = random.Random(seed)
    names = tuple(f"未知{i:02d}" for i in range(32))
    rows: list[Record] = []
    for index in range(size):
        code = index % 4
        relation = code // 2
        direction = code % 2
        chain_length = 2 + (index % 4)
        nodes = rng.sample(names, chain_length + 1)
        facts: list[tuple[str, str, str]] = []
        for edge_index in range(chain_length):
            edge_code = 2 * relation
            marker = rng.choice(STATEMENT_GROUPS[edge_code])
            left, right = nodes[edge_index], nodes[edge_index + 1]
            facts.append((left, marker, right))
        distractor_relation = 1 - relation
        d0, d1 = rng.sample(
            [name for name in names if name not in nodes], 2
        )
        facts.append(
            (
                d0,
                rng.choice(STATEMENT_GROUPS[2 * distractor_relation]),
                d1,
            )
        )

        true_case = index % 2 == 0
        if direction == 0:
            source, target = nodes[0], nodes[-1]
        else:
            source, target = nodes[-1], nodes[0]
        if not true_case:
            target = d0
        query_marker = rng.choice(QUERY_GROUPS[code])
        rng.shuffle(facts)
        rows.append(
            Record(tuple(facts), (source, query_marker, target), true_case)
        )
    return tuple(rows)


def _synonym_variant(row: Record) -> Record:
    facts = []
    for left, marker, right in row.facts:
        code = _gold_code(marker)
        group = STATEMENT_GROUPS[code]
        replacement = group[(group.index(marker) + 1) % len(group)]
        facts.append((left, replacement, right))
    left, marker, right = row.query
    code = _gold_code(marker)
    group = QUERY_GROUPS[code]
    replacement = group[(group.index(marker) + 1) % len(group)]
    return Record(tuple(facts), (left, replacement, right), row.answer)


def _rename_variant(row: Record, index: int) -> Record:
    entities = sorted(
        {part for fact in row.facts for part in (fact[0], fact[2])}
        | {row.query[0], row.query[2]}
    )
    mapping = {
        entity: f"改名{index:03d}_{position:02d}"
        for position, entity in enumerate(entities)
    }
    facts = tuple(
        (mapping[left], marker, mapping[right])
        for left, marker, right in row.facts
    )
    left, marker, right = row.query
    return Record(
        facts, (mapping[left], marker, mapping[right]), row.answer
    )


def _reorder_variant(row: Record) -> Record:
    return Record(tuple(reversed(row.facts)), row.query, row.answer)


def metamorphic_records(
    records: Sequence[Record],
) -> dict[str, tuple[Record, ...]]:
    return {
        "synonym_substitution": tuple(
            _synonym_variant(row) for row in records
        ),
        "entity_renaming": tuple(
            _rename_variant(row, index)
            for index, row in enumerate(records)
        ),
        "fact_reordering": tuple(
            _reorder_variant(row) for row in records
        ),
    }


def exact_memorization_baseline(
    train: Sequence[Record], heldout: Sequence[Record]
) -> Evaluation:
    table: dict[tuple[object, ...], bool] = {
        (row.facts, row.query): row.answer for row in train
    }
    majority = Counter(row.answer for row in train).most_common(1)[0][0]
    predictions = tuple(
        table.get((row.facts, row.query), majority) for row in heldout
    )
    correct = sum(
        prediction == row.answer
        for prediction, row in zip(predictions, heldout)
    )
    return Evaluation(correct, len(heldout), len(heldout), predictions)


def learned_payload_bytes(model: LearnedMeaning) -> int:
    raw = json.dumps(
        model.payload(), ensure_ascii=False, sort_keys=True
    ).encode("utf-8")
    return len(zlib.compress(raw, level=9))


def executable_description_bits() -> int:
    functions = (
        learn_meaning,
        predict,
        evaluate,
        _single_fact_signature,
        _decode,
    )
    payload = b"".join(
        marshal.dumps(function.__code__) for function in functions
    )
    return 8 * len(zlib.compress(payload, level=9))


def records_expose_canonical_labels(records: Iterable[Record]) -> bool:
    forbidden = {
        "relation_0",
        "relation_1",
        "forward",
        "inverse",
        "semantic_code",
    }
    serialized = json.dumps(
        [
            {
                "facts": row.facts,
                "query": row.query,
                "answer": row.answer,
            }
            for row in records
        ],
        ensure_ascii=False,
    )
    return any(token in serialized for token in forbidden)


def run_gate() -> dict[str, object]:
    train = build_training_records()
    heldout = build_heldout_records()
    model = learn_meaning(train)
    learned = evaluate(model, heldout)
    baseline = exact_memorization_baseline(train, heldout)
    variants = metamorphic_records(heldout)
    variant_results = {
        name: evaluate(model, rows) for name, rows in variants.items()
    }
    invariant = all(
        result.predictions == learned.predictions
        for result in variant_results.values()
    )
    payload_bytes = learned_payload_bytes(model)
    executable_bits = executable_description_bits()
    average_inference_ops = learned.inference_operations / learned.total
    checks = {
        "heldout_accuracy_at_least_95_percent": learned.accuracy >= 0.95,
        "beats_exact_memorization_by_25_points": (
            learned.accuracy - baseline.accuracy >= 0.25
        ),
        "synonym_rename_and_order_invariant": invariant,
        "all_metamorphic_accuracies_at_least_95_percent": all(
            result.accuracy >= 0.95
            for result in variant_results.values()
        ),
        "training_records_hide_canonical_semantic_labels": (
            not records_expose_canonical_labels(train)
        ),
        "learned_payload_within_4096_bytes": payload_bytes <= 4096,
        "executable_description_within_200k_bits": (
            executable_bits <= 200_000
        ),
        "training_compute_within_200k_operations": (
            model.training_operations <= 200_000
        ),
        "average_inference_within_128_operations": (
            average_inference_ops <= 128
        ),
    }
    return {
        "capability_id": CAPABILITY_ID,
        "capability": "weakly supervised relational meaning invariance",
        "claim": (
            "controlled tokenized-clause semantic induction and "
            "compositional transfer"
        ),
        "train_records": len(train),
        "heldout_records": len(heldout),
        "learned_accuracy": learned.accuracy,
        "memorization_accuracy": baseline.accuracy,
        "variant_accuracies": {
            name: result.accuracy
            for name, result in variant_results.items()
        },
        "learned_payload_bytes": payload_bytes,
        "executable_total_description_bits": executable_bits,
        "training_operations": model.training_operations,
        "average_inference_operations": average_inference_ops,
        "checks": checks,
        "passed": all(checks.values()),
        "raw_japanese_understanding": False,
        "open_domain_semantics": False,
        "high_school_intelligence": False,
        "general_llm_parity": False,
    }


def render_markdown(result: Mapping[str, object]) -> str:
    lines = [
        f"# {result['capability_id']}: relational meaning invariance",
        "",
        f"Passed: **{result['passed']}**",
        "",
        (
            "- Learned held-out accuracy: "
            f"**{result['learned_accuracy']:.3f}**"
        ),
        (
            "- Exact memorization baseline: "
            f"**{result['memorization_accuracy']:.3f}**"
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
                "- Semantic marker classes and inverse pairs are induced "
                "from final truth labels; canonical relation labels are "
                "not provided."
            ),
            (
                "- Evaluation holds out entity identities, chain "
                "compositions, fact order, and synonym choices."
            ),
            (
                "- Clause boundaries and argument slots are still supplied. "
                "This is not unrestricted Japanese parsing or open-domain "
                "meaning understanding."
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    result = run_gate()
    root = Path(__file__).resolve().parents[2]
    results_dir = root / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "cap_sem_001.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (results_dir / "cap_sem_001.md").write_text(
        render_markdown(result), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
