from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import inspect
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .phase18d10_primitive_core import (
    IndexAffinePrimitive,
    SequenceLookupPrimitive,
    SequencePrimitive,
)


class NoPromotablePrimitiveError(ValueError):
    pass


@dataclass(frozen=True)
class ResidualRow:
    position: int
    source: Any
    target: Any


@dataclass(frozen=True)
class Promotion:
    position: int
    primitive: SequencePrimitive
    support_positions: tuple[int, ...]
    support_types: tuple[str, ...]
    candidates_evaluated: int
    behavior_classes: int
    literal_bits: int
    model_bits: int
    mdl_gain_bits: int


@dataclass(frozen=True)
class OnlineResult:
    predictions: tuple[Any | None, ...]
    observed_operations: tuple[str | None, ...]
    residual_positions: tuple[int, ...]
    promotion: Promotion | None
    primitive: SequencePrimitive | None
    candidates_evaluated: int


def _data_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "phase18d11_ungrouped_stream.json"


def load_dataset() -> Mapping[str, Any]:
    return json.loads(_data_path().read_text(encoding="utf-8"))


def decode(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(Fraction(item) for item in value)
    return value


def encode(value: Any) -> Any:
    if isinstance(value, tuple):
        return [
            int(item)
            if item.denominator == 1
            else {"fraction": [item.numerator, item.denominator]}
            for item in value
        ]
    return value


def kind(value: Any) -> str:
    if isinstance(value, str):
        return "string"
    if isinstance(value, tuple):
        return "number_list"
    raise TypeError(type(value))


def canonical(value: Any) -> Any:
    if isinstance(value, tuple):
        return tuple((item.numerator, item.denominator) for item in value)
    return value


def base_operations(value: Any) -> Mapping[str, Any]:
    if isinstance(value, str):
        return {
            "IDENTITY": value,
            "UPPER": value.upper(),
            "LOWER": value.lower(),
            "REVERSE": value[::-1],
        }
    if isinstance(value, tuple):
        return {
            "IDENTITY": value,
            "SORT": tuple(sorted(value)),
            "REVERSE": tuple(reversed(value)),
        }
    raise TypeError(type(value))


def _operation_predictions(
    value: Any,
    primitive: SequencePrimitive | None,
) -> Mapping[str, Any]:
    output = dict(base_operations(value))
    if primitive is not None:
        output["INVENTED"] = primitive.apply(value)
    return output


def _matching_operations(
    value: Any,
    target: Any,
    primitive: SequencePrimitive | None,
) -> tuple[str, ...]:
    return tuple(
        name
        for name, prediction in _operation_predictions(value, primitive).items()
        if canonical(prediction) == canonical(target)
    )


def _literal_bits(rows: Sequence[ResidualRow]) -> int:
    payload = [
        {
            "position": row.position,
            "source": encode(row.source),
            "target": encode(row.target),
        }
        for row in rows
    ]
    return len(
        json.dumps(
            payload,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ) * 8


def _candidate_primitives(
    rows: Sequence[ResidualRow],
) -> tuple[SequencePrimitive, ...]:
    maximum_length = max(len(row.source) for row in rows)
    lookup = SequenceLookupPrimitive(
        tuple((canonical(row.source), row.target) for row in rows)
    )
    candidates: list[SequencePrimitive] = [lookup]
    for multiplier in range(-maximum_length - 1, maximum_length + 2):
        for offset in range(-maximum_length - 1, maximum_length + 2):
            candidates.append(IndexAffinePrimitive(multiplier, offset))
    return tuple(candidates)


def _probe_signature(primitive: SequencePrimitive) -> tuple[Any, ...]:
    probes: tuple[Any, ...] = (
        "abcdef",
        tuple(Fraction(value) for value in (1, 2, 3, 4, 5, 6)),
    )
    return tuple(canonical(primitive.apply(probe)) for probe in probes)


def _support(
    primitive: SequencePrimitive,
    rows: Sequence[ResidualRow],
) -> tuple[ResidualRow, ...]:
    return tuple(
        row
        for row in rows
        if canonical(primitive.apply(row.source)) == canonical(row.target)
    )


def select_cluster_primitive(
    rows: Sequence[ResidualRow],
    *,
    minimum_support: int = 6,
    minimum_types: int = 2,
    call_bits: int = 20,
) -> Promotion:
    rows = tuple(rows)
    if len(rows) < minimum_support:
        raise NoPromotablePrimitiveError("insufficient residual support")
    candidates = _candidate_primitives(rows)
    literal_all = _literal_bits(rows)
    scored: list[
        tuple[
            int,
            tuple[Any, ...],
            SequencePrimitive,
            tuple[ResidualRow, ...],
            int,
            int,
        ]
    ] = []
    for primitive in candidates:
        support = _support(primitive, rows)
        support_types = {kind(row.source) for row in support}
        if len(support) < minimum_support or len(support_types) < minimum_types:
            continue
        unsupported = tuple(row for row in rows if row not in support)
        model_bits = (
            primitive.payload_bits
            + call_bits * len(support)
            + _literal_bits(unsupported)
        )
        gain = literal_all - model_bits
        if gain <= 0:
            continue
        scored.append(
            (
                -gain,
                _probe_signature(primitive),
                primitive,
                support,
                model_bits,
                gain,
            )
        )
    if not scored:
        raise NoPromotablePrimitiveError("no reusable residual cluster")
    best_gain = min(row[0] for row in scored)
    best = [row for row in scored if row[0] == best_gain]
    behavior_classes = {row[1] for row in best}
    if len(behavior_classes) != 1:
        raise NoPromotablePrimitiveError(
            "top residual cluster is behaviorally ambiguous"
        )
    chosen = min(
        best,
        key=lambda row: (
            row[2].payload_bits,
            json.dumps(row[2].render(), sort_keys=True),
        ),
    )
    _, _, primitive, support, model_bits, gain = chosen
    return Promotion(
        position=max(row.position for row in rows),
        primitive=primitive,
        support_positions=tuple(row.position for row in support),
        support_types=tuple(sorted({kind(row.source) for row in support})),
        candidates_evaluated=len(candidates),
        behavior_classes=len(behavior_classes),
        literal_bits=literal_all,
        model_bits=model_bits,
        mdl_gain_bits=gain,
    )


def online_learn(
    records: Sequence[Mapping[str, Any]],
    *,
    minimum_support: int = 6,
) -> OnlineResult:
    residuals: list[ResidualRow] = []
    primitive: SequencePrimitive | None = None
    promotion: Promotion | None = None
    current_operation: str | None = None
    predictions: list[Any | None] = []
    observed_operations: list[str | None] = []
    candidates_evaluated = 0

    for position, raw in enumerate(records):
        source = decode(raw["input"])
        target = decode(raw["output"])
        operations = _operation_predictions(source, primitive)
        prediction = (
            operations.get(current_operation)
            if current_operation is not None
            else None
        )
        predictions.append(prediction)

        matches = _matching_operations(source, target, primitive)
        if current_operation in matches:
            observed = current_operation
        elif matches:
            base_matches = tuple(
                name for name in matches if name != "INVENTED"
            )
            if len(base_matches) == 1:
                observed = base_matches[0]
            elif len(matches) == 1:
                observed = matches[0]
            else:
                observed = min(matches)
        else:
            observed = None
            residuals.append(ResidualRow(position, source, target))
            if primitive is None:
                try:
                    candidate = select_cluster_primitive(
                        residuals,
                        minimum_support=minimum_support,
                    )
                except NoPromotablePrimitiveError:
                    pass
                else:
                    primitive = candidate.primitive
                    promotion = candidate
                    candidates_evaluated += candidate.candidates_evaluated
                    if canonical(primitive.apply(source)) == canonical(target):
                        observed = "INVENTED"
        observed_operations.append(observed)
        current_operation = observed

    return OnlineResult(
        tuple(predictions),
        tuple(observed_operations),
        tuple(row.position for row in residuals),
        promotion,
        primitive,
        candidates_evaluated,
    )


def _metrics(
    result: OnlineResult,
    records: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any]:
    correct = wrong = abstained = 0
    for prediction, raw in zip(result.predictions, records):
        target = decode(raw["output"])
        if prediction is None:
            abstained += 1
        elif canonical(prediction) == canonical(target):
            correct += 1
        else:
            wrong += 1
    covered = correct + wrong
    return {
        "correct": correct,
        "wrong": wrong,
        "abstained": abstained,
        "coverage": covered / len(records),
        "covered_accuracy": correct / covered if covered else 0.0,
    }


def _invented_future_accuracy(
    result: OnlineResult,
    records: Sequence[Mapping[str, Any]],
    labels: Sequence[str],
) -> tuple[int, int]:
    if result.promotion is None:
        return 0, 0
    correct = total = 0
    for position in range(result.promotion.position + 1, len(records)):
        if labels[position] != "HIDDEN":
            continue
        total += 1
        target = decode(records[position]["output"])
        primitive = result.primitive
        if (
            primitive is not None
            and canonical(
                primitive.apply(decode(records[position]["input"]))
            )
            == canonical(target)
        ):
            correct += 1
    return correct, total


def negative_controls(
    records: Sequence[Mapping[str, Any]],
) -> Mapping[str, bool]:
    decoded = [
        ResidualRow(i, decode(row["input"]), decode(row["output"]))
        for i, row in enumerate(records)
    ]
    target = IndexAffinePrimitive(1, 1)
    strings_only = tuple(
        row
        for row in decoded
        if kind(row.source) == "string"
        and canonical(target.apply(row.source)) == canonical(row.target)
    )
    try:
        select_cluster_primitive(strings_only, minimum_support=3)
    except NoPromotablePrimitiveError:
        one_type_rejected = True
    else:
        one_type_rejected = False

    conflict_rows = (
        ResidualRow(0, "abcd", "bcda"),
        ResidualRow(1, "lamp", "ampl"),
        ResidualRow(
            2,
            tuple(Fraction(x) for x in (1, 2, 3)),
            tuple(Fraction(x) for x in (2, 3, 1)),
        ),
        ResidualRow(3, "wxyz", "zwxy"),
        ResidualRow(4, "quiet", "etqui"),
        ResidualRow(
            5,
            tuple(Fraction(x) for x in (4, 5, 6)),
            tuple(Fraction(x) for x in (6, 4, 5)),
        ),
    )
    try:
        select_cluster_primitive(conflict_rows, minimum_support=3)
    except NoPromotablePrimitiveError:
        conflict_rejected = True
    else:
        conflict_rejected = False

    noise = (
        ResidualRow(0, "abcd", "badc"),
        ResidualRow(
            1,
            tuple(Fraction(x) for x in (1, 2, 3, 4)),
            tuple(Fraction(x) for x in (1, 3, 2, 4)),
        ),
    )
    try:
        select_cluster_primitive(noise, minimum_support=2)
    except NoPromotablePrimitiveError:
        noise_rejected = True
    else:
        noise_rejected = False

    return {
        "single_type_cluster_rejected": one_type_rejected,
        "competing_hidden_behaviors_rejected": conflict_rejected,
        "one_off_noise_not_promoted": noise_rejected,
    }


def run() -> Mapping[str, Any]:
    payload = load_dataset()
    records = tuple(payload["stream"])
    labels = tuple(payload["audit_labels"])
    result = online_learn(records)
    metrics = _metrics(result, records)
    future_correct, future_total = _invented_future_accuracy(
        result,
        records,
        labels,
    )
    controls = negative_controls(records)
    promotion = result.promotion
    checks = {
        "no_task_ids_in_stream": all(
            set(row) == {"input", "output"} for row in records
        ),
        "primitive_promoted": promotion is not None,
        "cross_type_support": (
            promotion is not None
            and set(promotion.support_types) == {"number_list", "string"}
        ),
        "positive_mdl_gain": (
            promotion is not None and promotion.mdl_gain_bits > 0
        ),
        "target_behavior_recovered": (
            isinstance(result.primitive, IndexAffinePrimitive)
            and (
                result.primitive.multiplier,
                result.primitive.offset,
            )
            == (1, 1)
        ),
        "future_hidden_accuracy": (
            future_total > 0 and future_correct == future_total
        ),
        "noise_not_in_support": (
            promotion is not None
            and all(
                labels[position] == "HIDDEN"
                for position in promotion.support_positions
            )
        ),
        "negative_controls": all(controls.values()),
    }
    source = inspect.getsource(inspect.getmodule(online_learn))
    source_audit = {
        "audit_labels_not_accepted_by_learner": (
            "audit_labels"
            not in inspect.signature(online_learn).parameters
        ),
        "hidden_label_not_in_learner": (
            ("HID" + "DEN") not in inspect.getsource(online_learn)
        ),
        "task_dispatch_absent": (
            ("match " + "task") not in source.lower()
        ),
    }
    checks["source_audit"] = all(source_audit.values())
    return {
        "campaign": {
            "name": payload["campaign"]["name"],
            "stream_records": len(records),
            "task_ids_supplied": False,
            "residual_groups_supplied": False,
            "causal_online_updates": True,
        },
        "invention": {
            "promotion_position": (
                None if promotion is None else promotion.position
            ),
            "residual_observations_at_promotion": (
                None
                if promotion is None
                else len(
                    [
                        position
                        for position in result.residual_positions
                        if position <= promotion.position
                    ]
                )
            ),
            "support_positions": (
                [] if promotion is None else list(promotion.support_positions)
            ),
            "support_types": (
                [] if promotion is None else list(promotion.support_types)
            ),
            "candidates_evaluated": (
                0 if promotion is None else promotion.candidates_evaluated
            ),
            "selected_primitive": (
                None if result.primitive is None else result.primitive.render()
            ),
            "literal_bits": (
                None if promotion is None else promotion.literal_bits
            ),
            "model_bits": (
                None if promotion is None else promotion.model_bits
            ),
            "mdl_gain_bits": (
                None if promotion is None else promotion.mdl_gain_bits
            ),
        },
        "online_prediction": metrics,
        "future_hidden": {
            "correct": future_correct,
            "total": future_total,
            "accuracy": (
                future_correct / future_total if future_total else 0.0
            ),
        },
        "negative_controls": controls,
        "source_audit": source_audit,
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {
            "ungrouped_online_residual_invention": all(checks.values()),
            "raw_byte_stream": False,
            "meta_grammar_human_designed": True,
            "unrestricted_primitive_invention": False,
            "llm_like_general_learning": False,
            "high_school_intelligence": False,
        },
        "limitations": [
            "Records still expose complete typed input and output fields.",
            "Local operation persistence is human-designed and unannounced change points remain unpredictable.",
            "The affine-index candidate grammar is fixed.",
            "Residual clustering is global over observed rows and only one primitive is promoted.",
            "No natural-language or open-domain learning is claimed.",
        ],
    }


def markdown(payload: Mapping[str, Any]) -> str:
    invention = payload["invention"]
    online = payload["online_prediction"]
    future = payload["future_hidden"]
    return f"""# Phase 18d-11 results: ungrouped online residual invention

- Stream records: **{payload['campaign']['stream_records']}**
- Task IDs / residual groups supplied: **False / False**
- Promotion position / residual observations: **{invention['promotion_position']} / {invention['residual_observations_at_promotion']}**
- Candidate primitives: **{invention['candidates_evaluated']}**
- Selected primitive: **{invention['selected_primitive']}**
- Cross-type support: **{invention['support_types']}**
- Literal / model / MDL gain: **{invention['literal_bits']} / {invention['model_bits']} / {invention['mdl_gain_bits']} bits**
- Online correct / wrong / abstained: **{online['correct']} / {online['wrong']} / {online['abstained']}**
- Covered accuracy / coverage: **{100*online['covered_accuracy']:.2f}% / {100*online['coverage']:.2f}%**
- Future hidden primitive accuracy: **{future['correct']}/{future['total']} ({100*future['accuracy']:.1f}%)**

The learner observes one unlabeled stream and promotes a reusable cross-type residual cluster. Records remain typed input/output pairs and the candidate meta-grammar is still human-designed, so this is not raw LLM-like learning.
"""


def main() -> None:
    payload = run()
    Path("results").mkdir(exist_ok=True)
    Path("results/phase18d11.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    Path("results/phase18d11.md").write_text(
        markdown(payload),
        encoding="utf-8",
    )
    print(markdown(payload), end="")
    if not payload["all_theorem_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
