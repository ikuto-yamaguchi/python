from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Sequence

from .multi_relation_semantics import (
    ExactSurfaceSchema,
    LatentOperation,
    MultiRelationTrace,
    Observation,
    ParseResult,
    fit_schema,
    infer_operation,
)

Slot = tuple[str, str]


@dataclass(frozen=True)
class ExpectedExample:
    text: str
    expected: ParseResult | None


def _observation(
    world: dict[Slot, str],
    slots: set[Slot] | None = None,
) -> Observation:
    visible = set(world) if slots is None else slots
    return Observation.from_values(
        {slot: world[slot] for slot in visible if slot in world},
        tuple(visible),
    )


def _set_trace(
    world: dict[Slot, str],
    relation: str,
    key: str,
    value: str,
    utterance: str,
    mode: str,
) -> tuple[MultiRelationTrace, dict[Slot, str], ParseResult]:
    before = dict(world)
    after = dict(world)
    after[(relation, key)] = value
    if mode == "full":
        slots = set(before) | {(relation, key)}
        trace = MultiRelationTrace(
            _observation(before, slots),
            utterance,
            _observation(after, slots),
            "了解",
        )
    elif mode == "partial":
        unrelated = next(slot for slot in before if slot != (relation, key))
        trace = MultiRelationTrace(
            _observation(before, {unrelated}),
            utterance,
            _observation(after, {unrelated, (relation, key)}),
            "了解",
        )
    elif mode == "delayed":
        slots = {(relation, key)}
        trace = MultiRelationTrace(
            _observation(before, slots),
            utterance,
            _observation(before, slots),
            "処理中",
            _observation(after, slots),
        )
    else:
        raise ValueError(f"unknown mode: {mode}")
    return trace, after, ParseResult("set", relation, key, value)


def _get_trace(
    world: dict[Slot, str],
    relation: str,
    key: str,
    utterance: str,
) -> tuple[MultiRelationTrace, ParseResult]:
    value = world[(relation, key)]
    visible = {(relation, key)}
    observation = _observation(world, visible)
    return (
        MultiRelationTrace(
            observation,
            utterance,
            observation,
            f"{key}は{value}です",
        ),
        ParseResult("get", relation, key, None),
    )


def _training_records() -> tuple[
    list[tuple[MultiRelationTrace, ParseResult | None, str]],
    dict[Slot, str],
]:
    world: dict[Slot, str] = {
        ("c0", "青い箱"): "倉庫",
        ("c0", "試作品"): "検査室",
        ("c0", "工具"): "棚B",
        ("c0", "センサー"): "作業室",
        ("c1", "青い箱"): "佐藤",
        ("c1", "試作品"): "田中",
        ("c1", "工具"): "山田",
        ("c1", "センサー"): "鈴木",
        ("c2", "api.py"): "core",
        ("c2", "worker.py"): "queue",
        ("c2", "cache.py"): "redis",
        ("c2", "ui.py"): "theme",
    }
    records: list[tuple[MultiRelationTrace, ParseResult | None, str]] = []
    set_specs = (
        ("c0", "青い箱", "検査室", "青い箱は検査室にある", "full"),
        ("c0", "工具", "倉庫", "工具は倉庫にある", "partial"),
        ("c0", "試作品", "棚B", "試作品を棚Bに移して", "delayed"),
        ("c0", "センサー", "検査室", "センサーを検査室に移して", "full"),
        ("c1", "青い箱", "田中", "青い箱は田中のもの", "full"),
        ("c1", "工具", "鈴木", "工具は鈴木のもの", "partial"),
        ("c1", "試作品", "佐藤", "試作品を佐藤に渡して", "delayed"),
        ("c1", "センサー", "山田", "センサーを山田に渡して", "full"),
        ("c2", "api.py", "redis", "api.pyはredisに依存する", "full"),
        ("c2", "ui.py", "core", "ui.pyはcoreに依存する", "partial"),
        (
            "c2",
            "worker.py",
            "theme",
            "worker.pyの依存先をthemeに変更して",
            "delayed",
        ),
        (
            "c2",
            "cache.py",
            "queue",
            "cache.pyの依存先をqueueに変更して",
            "full",
        ),
    )
    for relation, key, value, utterance, mode in set_specs:
        trace, world, expected = _set_trace(
            world,
            relation,
            key,
            value,
            utterance,
            mode,
        )
        records.append((trace, expected, f"set_{mode}"))

    get_specs = (
        ("c0", "青い箱", "青い箱はどこ?"),
        ("c0", "工具", "工具はどこ?"),
        ("c0", "試作品", "試作品の場所を教えて"),
        ("c0", "センサー", "センサーの場所を教えて"),
        ("c1", "青い箱", "青い箱の持ち主は?"),
        ("c1", "工具", "工具の持ち主は?"),
        ("c1", "試作品", "試作品は誰のもの?"),
        ("c1", "センサー", "センサーは誰のもの?"),
        ("c2", "api.py", "api.pyの依存先は?"),
        ("c2", "ui.py", "ui.pyの依存先は?"),
        ("c2", "worker.py", "worker.pyは何に依存してる?"),
        ("c2", "cache.py", "cache.pyは何に依存してる?"),
    )
    for relation, key, utterance in get_specs:
        trace, expected = _get_trace(world, relation, key, utterance)
        records.append((trace, expected, "get"))

    before = dict(world)
    after = dict(world)
    after[("c0", "青い箱")] = "倉庫"
    slot = {("c0", "青い箱")}
    records.append(
        (
            MultiRelationTrace(
                _observation(before, slot),
                "青い箱と倉庫について雑談した",
                _observation(after, slot),
                "そうですね",
            ),
            None,
            "noise_accidental",
        )
    )

    observation = _observation(world, {("c1", "試作品")})
    records.append(
        (
            MultiRelationTrace(
                observation,
                "試作品は誰のもの?",
                observation,
                "試作品は鈴木です",
            ),
            None,
            "noise_response",
        )
    )

    before = dict(world)
    after = dict(world)
    after[("c0", "工具")] = "棚B"
    after[("c1", "工具")] = "佐藤"
    slots = {("c0", "工具"), ("c1", "工具")}
    records.append(
        (
            MultiRelationTrace(
                _observation(before, slots),
                "工具を棚Bにして佐藤へ渡して",
                _observation(after, slots),
                "了解",
            ),
            None,
            "noise_multi_effect",
        )
    )
    return records, world


def _validation() -> list[ExpectedExample]:
    return [
        ExpectedExample(
            "青い箱を作業室に移して",
            ParseResult("set", "c0", "青い箱", "作業室"),
        ),
        ExpectedExample(
            "工具は検査室にある",
            ParseResult("set", "c0", "工具", "検査室"),
        ),
        ExpectedExample(
            "試作品はどこ?",
            ParseResult("get", "c0", "試作品", None),
        ),
        ExpectedExample(
            "工具の場所を教えて",
            ParseResult("get", "c0", "工具", None),
        ),
        ExpectedExample(
            "工具を田中に渡して",
            ParseResult("set", "c1", "工具", "田中"),
        ),
        ExpectedExample(
            "センサーは佐藤のもの",
            ParseResult("set", "c1", "センサー", "佐藤"),
        ),
        ExpectedExample(
            "センサーの持ち主は?",
            ParseResult("get", "c1", "センサー", None),
        ),
        ExpectedExample(
            "工具は誰のもの?",
            ParseResult("get", "c1", "工具", None),
        ),
        ExpectedExample(
            "ui.pyの依存先をredisに変更して",
            ParseResult("set", "c2", "ui.py", "redis"),
        ),
        ExpectedExample(
            "cache.pyはcoreに依存する",
            ParseResult("set", "c2", "cache.py", "core"),
        ),
        ExpectedExample(
            "cache.pyの依存先は?",
            ParseResult("get", "c2", "cache.py", None),
        ),
        ExpectedExample(
            "api.pyは何に依存してる?",
            ParseResult("get", "c2", "api.py", None),
        ),
        ExpectedExample("倉庫を青い箱に移して", None),
        ExpectedExample("田中を工具に渡して", None),
        ExpectedExample("coreはapi.pyに依存する", None),
        ExpectedExample("工具と棚Bについて雑談した", None),
        ExpectedExample("試作品と田中について雑談した", None),
        ExpectedExample("api.pyとcoreについて雑談した", None),
        ExpectedExample("今日は晴れ", None),
    ]


def _evaluate(
    parser: object,
    examples: Sequence[ExpectedExample],
) -> dict[str, object]:
    correct = 0
    failures: list[dict[str, object]] = []
    rule_checks = 0
    symbol_checks = 0
    for example in examples:
        predicted, rules, symbols = parser.parse_with_cost(example.text)
        rule_checks += rules
        symbol_checks += symbols
        if predicted == example.expected:
            correct += 1
        else:
            failures.append(
                {
                    "text": example.text,
                    "expected": (
                        None
                        if example.expected is None
                        else example.expected.__dict__
                    ),
                    "predicted": (
                        None if predicted is None else predicted.__dict__
                    ),
                }
            )
    total = len(examples)
    return {
        "correct": correct,
        "total": total,
        "accuracy": correct / total,
        "failures": failures,
        "average_rule_checks": rule_checks / total,
        "average_symbol_checks": symbol_checks / total,
    }


def _objective(
    parser: object,
    evaluation: dict[str, object],
    error_bits: int = 1024,
) -> int:
    errors = int(evaluation["total"]) - int(evaluation["correct"])
    return parser.description_bits + error_bits * errors


def _new_relation_bootstrap(
    records: Sequence[tuple[MultiRelationTrace, ParseResult | None, str]],
    operations: Sequence[LatentOperation],
) -> dict[str, object]:
    traces = [record[0] for record in records]
    additions: list[MultiRelationTrace] = []
    for key, value in (("障害A", "高"), ("障害B", "低")):
        post = {("c3", key): value}
        additions.append(
            MultiRelationTrace(
                _observation({}, set()),
                f"{key}の優先度は{value}",
                _observation(post, {("c3", key)}),
                "了解",
            )
        )
    inferred = [infer_operation(trace) for trace in additions]
    accepted = [operation for operation in inferred if operation is not None]
    base = fit_schema(operations, traces, min_support=2)
    expanded = fit_schema(
        [*operations, *accepted],
        [*traces, *additions],
        min_support=2,
    )
    example = ExpectedExample(
        "障害Aの優先度は低",
        ParseResult("set", "c3", "障害A", "低"),
    )
    evaluation = _evaluate(expanded, [example])
    return {
        "consistent_traces": len(additions),
        "relation_count_before": len(
            {operation.relation for operation in operations}
        ),
        "relation_count_after": expanded.relation_count,
        "rules_added": len(expanded.rules) - len(base.rules),
        "description_bits_added": (
            expanded.description_bits - base.description_bits
        ),
        "heldout_cross_combination": evaluation,
    }


def run() -> dict[str, object]:
    records, _world = _training_records()
    inferred: list[LatentOperation] = []
    true_positive = 0
    false_positive = 0
    expected_count = 0
    recovery_by_kind: dict[str, dict[str, int]] = {}
    for trace, expected, kind in records:
        operation = infer_operation(trace)
        if operation is not None:
            inferred.append(operation)
        bucket = recovery_by_kind.setdefault(
            kind,
            {"correct": 0, "total": 0},
        )
        bucket["total"] += 1
        if expected is not None:
            expected_count += 1
            predicted = (
                None
                if operation is None
                else ParseResult(
                    operation.operation,
                    operation.relation,
                    operation.key,
                    operation.value,
                )
            )
            if predicted == expected:
                true_positive += 1
                bucket["correct"] += 1
        elif operation is None:
            bucket["correct"] += 1
        else:
            false_positive += 1

    traces = [record[0] for record in records]
    validation = _validation()
    exact = ExactSurfaceSchema(inferred)
    naive = fit_schema(
        inferred,
        traces,
        min_support=1,
        min_confidence_sum=0.0,
    )
    robust = fit_schema(
        inferred,
        traces,
        min_support=2,
        min_confidence_sum=1.4,
    )

    exact_eval = _evaluate(exact, validation)
    naive_eval = _evaluate(naive, validation)
    robust_eval = _evaluate(robust, validation)

    hypotheses = {
        "exact_surface": {
            "description_bits": exact.description_bits,
            "validation": exact_eval,
            "lifetime_objective": _objective(exact, exact_eval),
        },
        "support_1_schema": {
            "description_bits": naive.description_bits,
            "rule_count": len(naive.rules),
            "validation": naive_eval,
            "lifetime_objective": _objective(naive, naive_eval),
        },
        "robust_multi_relation_schema": {
            "description_bits": robust.description_bits,
            "relation_count": robust.relation_count,
            "rule_count": len(robust.rules),
            "index_bits": robust.index_bits,
            "validation": robust_eval,
            "lifetime_objective": _objective(robust, robust_eval),
        },
    }
    selected = min(
        hypotheses,
        key=lambda name: hypotheses[name]["lifetime_objective"],
    )

    return {
        "trace_count": len(records),
        "expected_operation_count": expected_count,
        "raw_operation_inference": {
            "inferred_count": len(inferred),
            "true_positive": true_positive,
            "false_positive": false_positive,
            "precision": true_positive / len(inferred),
            "recall": true_positive / expected_count,
            "recovery_by_kind": recovery_by_kind,
        },
        "hypotheses": hypotheses,
        "selected_hypothesis": selected,
        "noise_filtering": {
            "raw_false_positive_templates": [
                operation.template
                for operation in inferred
                if "雑談" in operation.template
            ],
            "support_1_retains_accidental_rule": any(
                "雑談" in rule.template for rule in naive.rules
            ),
            "robust_rejects_accidental_rule": not any(
                "雑談" in rule.template for rule in robust.rules
            ),
        },
        "routing_efficiency": {
            "total_rules": len(robust.rules),
            "linear_scan_rule_checks_per_input": len(robust.rules),
            "indexed_average_rule_checks": robust_eval[
                "average_rule_checks"
            ],
            "indexed_average_symbol_checks": robust_eval[
                "average_symbol_checks"
            ],
        },
        "new_relation_bootstrap": _new_relation_bootstrap(records, inferred),
        "limitations": [
            "opaque effect-channel identifiers are observable even though their semantics are not named",
            "surface-rule candidates remain a restricted template language",
            "noise handling is support-based and does not model adversarial or correlated noise",
            "delayed effects span one step only",
            "the experiment does not yet infer arbitrary goals or repository-scale programs",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    inference = payload["raw_operation_inference"]
    hypotheses = payload["hypotheses"]
    routing = payload["routing_efficiency"]
    bootstrap = payload["new_relation_bootstrap"]
    lines = [
        "# Phase 8c results: multiple latent relations under partial, noisy, delayed traces",
        "",
        "The learner receives opaque state-effect channels rather than semantic relation names.",
        "It must map language to reusable SET/GET schemas while distinguishing missing observations",
        "from deletions, recovering one-step delayed effects, and rejecting unsupported accidental correlations.",
        "",
        f"- traces: **{payload['trace_count']}**",
        f"- expected operations: **{payload['expected_operation_count']}**",
        f"- raw inference precision: **{inference['precision']:.1%}**",
        f"- raw inference recall: **{inference['recall']:.1%}**",
        "",
        "## Representation competition",
        "",
        "| hypothesis | bits | validation | lifetime objective |",
        "|---|---:|---:|---:|",
    ]
    for name in (
        "exact_surface",
        "support_1_schema",
        "robust_multi_relation_schema",
    ):
        item = hypotheses[name]
        lines.append(
            f"| {name} | {item['description_bits']:,} | "
            f"{item['validation']['accuracy']:.1%} | "
            f"{item['lifetime_objective']:,} |"
        )
    lines.extend(
        [
            "",
            f"Selected: **{payload['selected_hypothesis']}**.",
            "",
            "The support-1 learner memorizes a single accidental `雑談` correlation and fails a held-out distractor.",
            "The support-2 schema removes it while preserving all direct, partial-observation, delayed-effect, and query rules.",
            "",
            "## Indexed routing",
            "",
            f"- compiled rules: **{routing['total_rules']}**",
            f"- linear scan: **{routing['linear_scan_rule_checks_per_input']:.1f} rule checks/input**",
            f"- cue index: **{routing['indexed_average_rule_checks']:.3f} rule checks/input**",
            f"- symbol checks after routing: **{routing['indexed_average_symbol_checks']:.3f}/input**",
            "",
            "The index cost is included in the serialized description length.",
            "",
            "## New relation bootstrap",
            "",
            f"Two consistent traces expand the opaque relation count from **{bootstrap['relation_count_before']}** to **{bootstrap['relation_count_after']}**.",
            f"They add **{bootstrap['rules_added']} rule** and **{bootstrap['description_bits_added']:,} bits**.",
            f"A held-out key/value recombination is handled at **{bootstrap['heldout_cross_combination']['accuracy']:.1%}**.",
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["limitations"])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = run()
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase8c.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "phase8c.md").write_text(
        render_markdown(payload),
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
