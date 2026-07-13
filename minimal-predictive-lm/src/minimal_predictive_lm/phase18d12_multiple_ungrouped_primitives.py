from __future__ import annotations

from fractions import Fraction
import inspect
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .phase18d10_primitive_core import IndexAffinePrimitive
from .phase18d11_ungrouped_online_residual import (
    ResidualRow,
    canonical,
    decode,
)
from .phase18d12_multi_primitive_core import (
    ElementAffinePrimitive,
    NoPromotablePrimitiveError,
    OnlineResult,
    metrics,
    online_learn,
    select_next_primitive,
)


def _data_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "data"
        / "phase18d12_multi_primitive_stream.json"
    )


def load_dataset() -> Mapping[str, Any]:
    return json.loads(_data_path().read_text(encoding="utf-8"))


def hidden_future_accuracy(
    result: OnlineResult,
    records: Sequence[Mapping[str, Any]],
    labels: Sequence[str],
) -> tuple[int, int]:
    correct = total = 0
    for position, (raw, label) in enumerate(zip(records, labels)):
        if not label.endswith("_FUTURE"):
            continue
        if not any(
            promotion.position < position
            for promotion in result.promotions
        ):
            continue
        source = decode(raw["input"])
        target = decode(raw["output"])
        matches = 0
        for primitive in result.library:
            try:
                matches += (
                    canonical(primitive.apply(source))
                    == canonical(target)
                )
            except (TypeError, ValueError):
                pass
        total += 1
        correct += matches == 1
    return correct, total


def negative_controls() -> Mapping[str, bool]:
    index = IndexAffinePrimitive(1, 1)
    element = ElementAffinePrimitive(1, 1)
    string_rows = tuple(
        ResidualRow(i, source, index.apply(source))
        for i, source in enumerate(("abcd", "lamp", "quiet"))
    )
    try:
        select_next_primitive(string_rows, minimum_support=3)
    except NoPromotablePrimitiveError:
        one_type_rejected = True
    else:
        one_type_rejected = False

    competing_rows: list[ResidualRow] = []
    index_sources: tuple[Any, ...] = (
        "abcd",
        "lamp",
        tuple(Fraction(x) for x in (1, 3, 5, 7)),
        "quiet",
        tuple(Fraction(x) for x in (2, 6, 10, 14)),
        "stone",
    )
    element_sources: tuple[Any, ...] = (
        "fghi",
        "mnop",
        tuple(Fraction(x) for x in (2, 4, 6, 8)),
        "qrst",
        tuple(Fraction(x) for x in (-3, 1, 5, 9)),
        "bcde",
    )
    for position, source in enumerate(index_sources):
        competing_rows.append(
            ResidualRow(position, source, index.apply(source))
        )
    for position, source in enumerate(element_sources, start=6):
        competing_rows.append(
            ResidualRow(position, source, element.apply(source))
        )
    try:
        select_next_primitive(competing_rows, minimum_support=6)
    except NoPromotablePrimitiveError:
        competing_rejected = True
    else:
        competing_rejected = False

    noise = (
        ResidualRow(0, "abcd", "badc"),
        ResidualRow(
            1,
            tuple(Fraction(x) for x in (1, 2, 3, 4)),
            tuple(Fraction(x) for x in (1, 3, 2, 4)),
        ),
    )
    try:
        select_next_primitive(noise, minimum_support=2)
    except NoPromotablePrimitiveError:
        noise_rejected = True
    else:
        noise_rejected = False

    duplicate_rows = (
        ResidualRow(0, "abcd", index.apply("abcd")),
        ResidualRow(1, "lamp", index.apply("lamp")),
        ResidualRow(2, "quiet", index.apply("quiet")),
        ResidualRow(
            3,
            tuple(Fraction(x) for x in (1, 2, 3, 4)),
            index.apply(tuple(Fraction(x) for x in (1, 2, 3, 4))),
        ),
        ResidualRow(
            4,
            tuple(Fraction(x) for x in (5, 7, 9, 11)),
            index.apply(tuple(Fraction(x) for x in (5, 7, 9, 11))),
        ),
        ResidualRow(
            5,
            tuple(Fraction(x) for x in (2, 6, 10, 14)),
            index.apply(tuple(Fraction(x) for x in (2, 6, 10, 14))),
        ),
    )
    try:
        select_next_primitive(duplicate_rows, (index,))
    except NoPromotablePrimitiveError:
        duplicate_rejected = True
    else:
        duplicate_rejected = False

    return {
        "single_type_cluster_rejected": one_type_rejected,
        "equal_competing_clusters_rejected": competing_rejected,
        "one_off_noise_not_promoted": noise_rejected,
        "existing_behavior_not_repromoted": duplicate_rejected,
    }


def parameter_recovery_controls() -> Mapping[str, bool]:
    index = IndexAffinePrimitive(1, 2)
    element = ElementAffinePrimitive(1, -1)
    rows = [
        ResidualRow(position, source, index.apply(source))
        for position, source in enumerate(
            (
                "abcdef",
                tuple(Fraction(x) for x in (1, 2, 3, 4, 5)),
                "lampqr",
                tuple(Fraction(x) for x in (8, 6, 4, 2)),
                "quietz",
                tuple(Fraction(x) for x in (3, 7, 11, 15)),
            )
        )
    ]
    first = select_next_primitive(rows)
    remaining = [
        ResidualRow(position, source, element.apply(source))
        for position, source in enumerate(
            (
                "bcdef",
                tuple(Fraction(x) for x in (2, 4, 6, 8)),
                "ghijk",
                tuple(Fraction(x) for x in (9, 5, 1, -3)),
                "mnopq",
                tuple(Fraction(x) for x in (12, 7, 2, -3)),
            ),
            start=10,
        )
    ]
    second = select_next_primitive(remaining, (first.primitive,))
    return {
        "different_index_parameter_recovered": (
            isinstance(first.primitive, IndexAffinePrimitive)
            and (first.primitive.multiplier, first.primitive.offset)
            == (1, 2)
        ),
        "different_element_parameter_recovered": (
            isinstance(second.primitive, ElementAffinePrimitive)
            and (second.primitive.scale, second.primitive.offset)
            == (1, -1)
        ),
    }


def run() -> Mapping[str, Any]:
    payload = load_dataset()
    records = tuple(payload["stream"])
    labels = tuple(payload["audit_labels"])
    result = online_learn(records)
    score = metrics(result, records)
    future_correct, future_total = hidden_future_accuracy(
        result, records, labels
    )
    controls = negative_controls()
    recovery = parameter_recovery_controls()

    expected = {
        ("index_affine", 1, 1),
        ("element_affine", 1, 1),
    }
    recovered = set()
    for primitive in result.library:
        if isinstance(primitive, IndexAffinePrimitive):
            recovered.add(
                ("index_affine", primitive.multiplier, primitive.offset)
            )
        elif isinstance(primitive, ElementAffinePrimitive):
            recovered.add(
                ("element_affine", primitive.scale, primitive.offset)
            )
    promoted_support = {
        position
        for promotion in result.promotions
        for position in promotion.support_positions
    }
    theorem_checks = {
        "no_task_or_group_ids_in_stream": all(
            set(row) == {"input", "output"} for row in records
        ),
        "two_primitives_promoted": len(result.promotions) == 2,
        "heterogeneous_meta_families_recovered": recovered == expected,
        "promotion_order": (
            tuple(p.position for p in result.promotions) == (15, 20)
        ),
        "cross_type_support_each": all(
            set(p.support_types) == {"number_list", "string"}
            for p in result.promotions
        ),
        "disjoint_support": len(promoted_support) == sum(
            len(p.support_positions) for p in result.promotions
        ),
        "positive_mdl_gain_each": all(
            p.mdl_gain_bits > 0 for p in result.promotions
        ),
        "future_hidden_accuracy": (
            future_total > 0 and future_correct == future_total
        ),
        "noise_not_promoted": all(
            labels[position].startswith("HIDDEN")
            for position in promoted_support
        ),
        "negative_controls": all(controls.values()),
        "parameter_recovery_controls": all(recovery.values()),
    }
    learner_source = inspect.getsource(online_learn)
    module_source = inspect.getsource(inspect.getmodule(online_learn))
    source_audit = {
        "audit_labels_not_accepted_by_learner": (
            "audit_labels"
            not in inspect.signature(online_learn).parameters
        ),
        "hidden_labels_not_in_learner": (
            ("HIDDEN_" + "INDEX") not in learner_source
            and ("HIDDEN_" + "ELEMENT") not in learner_source
        ),
        "task_dispatch_absent": (
            ("match " + "task") not in module_source.lower()
        ),
        "target_parameters_not_in_dataset": (
            "multiplier" not in json.dumps(payload)
            and "scale" not in json.dumps(payload)
            and "offset" not in json.dumps(payload)
        ),
    }
    theorem_checks["source_audit"] = all(source_audit.values())

    return {
        "campaign": {
            "name": payload["campaign"]["name"],
            "stream_records": len(records),
            "task_ids_supplied": False,
            "residual_groups_supplied": False,
            "candidate_meta_grammar": (
                "affine index transducers, affine element transducers, "
                "and lookup control"
            ),
        },
        "online_invention": {
            "promotions": len(result.promotions),
            "promotion_positions": [
                p.position for p in result.promotions
            ],
            "selected_primitives": [
                p.primitive.render() for p in result.promotions
            ],
            "support_positions": [
                list(p.support_positions) for p in result.promotions
            ],
            "support_types": [
                list(p.support_types) for p in result.promotions
            ],
            "candidates_evaluated": [
                p.candidates_evaluated for p in result.promotions
            ],
            "mdl_gain_bits": [
                p.mdl_gain_bits for p in result.promotions
            ],
            "unresolved_positions": list(result.unresolved_positions),
        },
        "prequential": score,
        "future_hidden": {
            "correct": future_correct,
            "total": future_total,
            "accuracy": future_correct / future_total,
        },
        "negative_controls": controls,
        "parameter_recovery_controls": recovery,
        "source_audit": source_audit,
        "resources": {
            "library_payload_bits": sum(
                primitive.payload_bits for primitive in result.library
            ),
            "candidates_evaluated_total": (
                result.candidates_evaluated
            ),
            "python_runtime_included": False,
            "candidate_meta_grammar_source_included_in_payload": False,
        },
        "theorem_checks": theorem_checks,
        "all_theorem_checks_pass": all(theorem_checks.values()),
        "claim_boundary": {
            "multiple_ungrouped_primitives_invented": all(
                theorem_checks.values()
            ),
            "heterogeneous_candidate_families": True,
            "candidate_meta_grammar_human_designed": True,
            "raw_byte_online_invention": False,
            "arbitrary_new_computation_invented": False,
            "llm_like_general_learning": False,
            "high_school_intelligence": False,
        },
        "limitations": [
            "Records still expose typed input and output fields.",
            "Only two human-designed primitive families are searched.",
            "Promotion uses small exact candidate enumeration.",
            "Local operation persistence is used for prequential prediction.",
            "No natural-language semantics, world knowledge, or unrestricted algorithm invention is claimed.",
        ],
    }


def markdown(payload: Mapping[str, Any]) -> str:
    invention = payload["online_invention"]
    prequential = payload["prequential"]
    future = payload["future_hidden"]
    resources = payload["resources"]
    return f"""# Phase 18d-12 results: multiple ungrouped primitive invention

- Stream records: **{payload['campaign']['stream_records']}**
- Task IDs / residual groups supplied: **no / no**
- Promotions / positions: **{invention['promotions']} / {invention['promotion_positions']}**
- Selected primitives: **{invention['selected_primitives']}**
- Candidate counts: **{invention['candidates_evaluated']}**
- MDL gains: **{invention['mdl_gain_bits']} bits**
- Future hidden accuracy: **{future['correct']}/{future['total']} = {100 * future['accuracy']:.1f}%**
- Prequential correct / wrong / abstain: **{prequential['correct']} / {prequential['wrong']} / {prequential['abstained']}**
- Covered accuracy / coverage: **{100 * prequential['covered_accuracy']:.2f}% / {100 * prequential['coverage']:.2f}%**
- Library payload: **{resources['library_payload_bits']} bits**
- Remaining unresolved positions: **{invention['unresolved_positions']}**

The learner separates and promotes two reusable hidden transformations from one mixed stream without task IDs or residual grouping. The candidate meta-grammar remains human-designed and narrow; this is controlled multi-primitive invention, not unrestricted LLM-like learning.
"""


def main() -> None:
    payload = run()
    results = Path("results")
    results.mkdir(exist_ok=True)
    (results / "phase18d12.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (results / "phase18d12.md").write_text(
        markdown(payload), encoding="utf-8"
    )
    print(markdown(payload), end="")
    if not payload["all_theorem_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
