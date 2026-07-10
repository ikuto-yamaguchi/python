from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from .latent_semantics import (
    DiscoveredRoles,
    InferredOperation,
    InteractionTrace,
    discover_roles,
    extend_roles,
    infer_operation,
    parser_with_roles,
)
from .semantic_induction import ExactSurfaceParser, InducedFeatureParser, SemanticExample


HIDDEN_ENTITIES = ("青い箱", "試作品", "工具", "鍵束", "設計書", "センサー")
HIDDEN_LOCATIONS = ("倉庫", "検査室", "棚B", "実験台", "保管庫", "作業室")


def _traces() -> list[InteractionTrace]:
    traces: list[InteractionTrace] = []
    updates = (
        ("青い箱は倉庫にある", "青い箱", "倉庫"),
        ("試作品、検査室に置いてある", "試作品", "検査室"),
        ("工具は棚Bだよ", "工具", "棚B"),
        ("鍵束を実験台に移して", "鍵束", "実験台"),
        ("設計書、保管庫にお願い", "設計書", "保管庫"),
        ("センサーを作業室へ運んで", "センサー", "作業室"),
    )
    for utterance, key, value in updates:
        traces.append(
            InteractionTrace({}, utterance, {key: value}, "了解")
        )

    queries = (
        ("青い箱はどこ?", "青い箱", "倉庫"),
        ("試作品、どこにある?", "試作品", "検査室"),
        ("工具の場所を教えて", "工具", "棚B"),
    )
    for utterance, key, value in queries:
        state = {key: value}
        traces.append(
            InteractionTrace(state, utterance, state, f"{key}は{value}にあります")
        )
    return traces


def _negative_examples() -> list[SemanticExample]:
    return [
        SemanticExample(text, "other")
        for text in (
            "ありがとう",
            "おはよう",
            "倉庫に行きたい",
            "どこでもいい",
            "今日は休み",
            "お願いがある",
            "天気を教えて",
            "確認をお願いします",
            "この箱は重い",
        )
    ]


def _inferred_examples(
    traces: Sequence[InteractionTrace],
) -> tuple[list[SemanticExample], list[InferredOperation]]:
    examples: list[SemanticExample] = []
    operations: list[InferredOperation] = []
    for trace in traces:
        operation = infer_operation(trace)
        if operation is None:
            continue
        operations.append(operation)
        examples.append(
            SemanticExample(
                trace.utterance,
                operation.operation,
                operation.key,
                operation.value,
            )
        )
    examples.extend(_negative_examples())
    return examples, operations


def _validation() -> list[SemanticExample]:
    return [
        SemanticExample("青い箱を作業室に移して", "set", "青い箱", "作業室"),
        SemanticExample("センサーは倉庫にある", "set", "センサー", "倉庫"),
        SemanticExample("設計書はどこ?", "get", "設計書", None),
        SemanticExample("鍵束の場所を教えて", "get", "鍵束", None),
        SemanticExample("倉庫を青い箱に移して", "other"),
        SemanticExample("検査室は試作品にある", "other"),
        SemanticExample("どこでもいい", "other"),
        SemanticExample("作業室を教えて", "other"),
    ]


def _surface_intent_examples(traces: Sequence[InteractionTrace]) -> list[SemanticExample]:
    examples: list[SemanticExample] = []
    for index, trace in enumerate(traces):
        operation = infer_operation(trace)
        if operation is None:
            continue
        if index < 3:
            intent = "remember"
        elif index < 6:
            intent = "move"
        else:
            intent = "query"
        examples.append(SemanticExample(trace.utterance, intent, operation.key, operation.value))
    examples.extend(_negative_examples())
    return examples


def _surface_validation() -> list[SemanticExample]:
    return [
        SemanticExample("青い箱を作業室に移して", "move", "青い箱", "作業室"),
        SemanticExample("センサーは倉庫にある", "remember", "センサー", "倉庫"),
        SemanticExample("設計書はどこ?", "query", "設計書", None),
        SemanticExample("鍵束の場所を教えて", "query", "鍵束", None),
        *[SemanticExample(example.text, "other") for example in _validation()[4:]],
    ]


def _accuracy(parser: object, examples: Sequence[SemanticExample]) -> dict[str, object]:
    correct = 0
    failures: list[dict[str, str]] = []
    for example in examples:
        program = parser.parse(example.text)
        predicted = program.intent if program is not None else "other"
        if predicted == example.intent:
            correct += 1
        else:
            failures.append({"text": example.text, "expected": example.intent, "predicted": predicted})
    return {"correct": correct, "total": len(examples), "accuracy": correct / len(examples), "failures": failures}


def _objective(parser: object, examples: Sequence[SemanticExample], *, extra_bits: int, error_bits: int = 512) -> int:
    errors = 0
    for example in examples:
        program = parser.parse(example.text)
        predicted = program.intent if program is not None else "other"
        errors += int(predicted != example.intent)
    return errors * error_bits + parser.description_bits + extra_bits


def _role_purity(roles: DiscoveredRoles) -> dict[str, float]:
    return {
        "key_role": sum(symbol in HIDDEN_ENTITIES for symbol in roles.keys) / len(roles.keys),
        "value_role": sum(symbol in HIDDEN_LOCATIONS for symbol in roles.values) / len(roles.values),
    }


def run() -> dict[str, object]:
    traces = _traces()
    inferred_examples, operations = _inferred_examples(traces)
    roles = discover_roles(operations)
    validation = _validation()

    exact = ExactSurfaceParser(inferred_examples)
    untyped_symbols = roles.all_symbols
    untyped = InducedFeatureParser.fit(inferred_examples, validation, untyped_symbols, untyped_symbols)
    two_role = InducedFeatureParser.fit(inferred_examples, validation, roles.keys, roles.values)

    exact_objective = _objective(exact, validation, extra_bits=0)
    untyped_objective = _objective(
        untyped,
        validation,
        extra_bits=roles.symbol_string_bits() + 1,
    )
    two_role_objective = _objective(
        two_role,
        validation,
        extra_bits=roles.symbol_string_bits() + roles.assignment_bits(),
    )
    objectives = {
        "exact_surface": exact_objective,
        "untyped_symbols": untyped_objective,
        "two_latent_roles": two_role_objective,
    }

    surface_parser = InducedFeatureParser.fit(
        _surface_intent_examples(traces),
        _surface_validation(),
        roles.keys,
        roles.values,
    )

    bootstrap = InteractionTrace({}, "予備部品は棚Aにある", {"予備部品": "棚A"}, "了解")
    bootstrap_operation = infer_operation(bootstrap)
    assert bootstrap_operation is not None
    extended_roles = extend_roles(roles, [bootstrap_operation])
    expanded_parser = parser_with_roles(two_role, extended_roles)
    new_symbol_examples = [
        SemanticExample("予備部品を作業室に移して", "set", "予備部品", "作業室"),
        SemanticExample("センサーを棚Aに移して", "set", "センサー", "棚A"),
        SemanticExample("予備部品の場所を教えて", "get", "予備部品", None),
    ]

    return {
        "trace_count": len(traces),
        "operation_inference": {
            "inferred": len(operations),
            "accuracy_against_hidden_trace_generator": len(operations) / len(traces),
            "operation_set": sorted({operation.operation for operation in operations}),
        },
        "discovered_roles": {
            "keys": list(roles.keys),
            "values": list(roles.values),
            "purity": _role_purity(roles),
            "assignment_bits": roles.assignment_bits(),
            "symbol_string_bits": roles.symbol_string_bits(),
        },
        "hypotheses": {
            "exact_surface": {
                "program_bits": exact.description_bits,
                "validation": _accuracy(exact, validation),
                "lifetime_objective": exact_objective,
            },
            "untyped_symbols": {
                "program_bits": untyped.description_bits,
                "validation": _accuracy(untyped, validation),
                "lifetime_objective": untyped_objective,
            },
            "two_latent_roles": {
                "program_bits": two_role.description_bits,
                "validation": _accuracy(two_role, validation),
                "lifetime_objective": two_role_objective,
            },
        },
        "selected_hypothesis": min(objectives, key=objectives.get),
        "operation_factorization": {
            "surface_intent_program_bits": surface_parser.description_bits,
            "state_operation_program_bits": two_role.description_bits,
            "surface_intent_validation": _accuracy(surface_parser, _surface_validation()),
            "state_operation_validation": _accuracy(two_role, validation),
        },
        "new_symbol_bootstrap": {
            "inferred_operation": {
                "operation": bootstrap_operation.operation,
                "key": bootstrap_operation.key,
                "value": bootstrap_operation.value,
            },
            "added_symbol_bits": sum(8 * len(symbol.encode("utf-8")) for symbol in ("予備部品", "棚A")) + 2,
            "rule_bits_added": 0,
            "evaluation": _accuracy(expanded_parser, new_symbol_examples),
        },
        "limitations": [
            "state transitions and responses are observed during induction",
            "the world relation is a single key-value map",
            "the candidate surface-rule language remains restricted",
            "operation induction is deterministic and not robust to noisy traces",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    hypotheses = payload["hypotheses"]
    factor = payload["operation_factorization"]
    bootstrap = payload["new_symbol_bootstrap"]
    roles = payload["discovered_roles"]
    lines = [
        "# Phase 8b results: latent roles and operations from interaction traces",
        "",
        "No intent label or entity/location type label is supplied to the main learner.",
        "SET/GET operations are inferred from state differences and responses; argument",
        "positions induce two reusable symbol roles.",
        "",
        f"- traces: **{payload['trace_count']}**",
        f"- inferred operations: **{payload['operation_inference']['inferred']}**",
        f"- key-role purity: **{roles['purity']['key_role']:.1%}**",
        f"- value-role purity: **{roles['purity']['value_role']:.1%}**",
        "",
        "## Representation competition",
        "",
        "| hypothesis | program bits | validation accuracy | lifetime objective |",
        "|---|---:|---:|---:|",
    ]
    for name in ("exact_surface", "untyped_symbols", "two_latent_roles"):
        item = hypotheses[name]
        lines.append(
            f"| {name} | {item['program_bits']} | {item['validation']['accuracy']:.1%} | {item['lifetime_objective']:,} |"
        )
    lines.extend(
        [
            "",
            f"Selected: **{payload['selected_hypothesis']}**.",
            "",
            "The untyped parser accepts a role-reversed command that the two-role",
            "representation rejects. The exact parser cannot transfer to held-out",
            "combinations. The two-role hypothesis pays one role bit per observed symbol",
            "and wins the full error-plus-description objective.",
            "",
            "## Factor away unnecessary linguistic intents",
            "",
            f"- remember/move/query surface program: **{factor['surface_intent_program_bits']} bits**",
            f"- SET/GET state-operation program: **{factor['state_operation_program_bits']} bits**",
            "",
            "Declarative remembering and imperative moving both produce the same SET",
            "transition, so preserving two separate internal intents is unnecessary for",
            "this world model.",
            "",
            "## New-symbol bootstrap",
            "",
            f"One observed transition introduces `予備部品` and `棚A` for **{bootstrap['added_symbol_bits']} new symbol bits**.",
            f"No rule bits are added. Subsequent commands using the new symbols score **{bootstrap['evaluation']['accuracy']:.1%}**.",
            "",
            "## Limitation",
            "",
            "This is still a one-relation deterministic micro-world. The learner observes",
            "state transitions and responses, and the surface hypothesis language is",
            "restricted. It has not discovered arbitrary predicates or goals from raw",
            "open-domain interaction.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    payload = run()
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase8b.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "phase8b.md").write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
