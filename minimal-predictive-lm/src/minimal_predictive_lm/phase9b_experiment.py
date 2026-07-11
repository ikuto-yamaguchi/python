from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable

from .hierarchical_event_graph import (
    EDGE_RELATIONS,
    EventGraph,
    edge_relation_recall,
    event_recall,
    execute_graph_workflow,
    parse_event_graph,
)
from .phase9a_experiment import TRAINING_SPECIFICATION, _traces
from .raw_event_program import induce_raw_grounder


BENCHMARK = (
    {
        "name": "conditional_repair",
        "raw": (
            "transform関数を修正して。"
            "テストを実行して。"
            "失敗したらその変更を元に戻して。"
            "別の修正を追加して。"
            "成功したか確認して結果を報告して。"
        ),
        "operations": ("SET", "VERIFY", "RETRACT", "SET", "VERIFY", "EMIT"),
        "relations": ("NEXT", "CONDITION_TRUE", "REFERS_TO", "CONTENT"),
    },
    {
        "name": "mixed_report",
        "raw": "作業結果を報告します。全テストに成功しました。",
        "operations": ("EMIT",),
        "relations": ("CONTENT",),
    },
    {
        "name": "negative_condition",
        "raw": (
            "テストが失敗しなければ、その変更を元に戻さないで。"
            "結果を報告して。"
        ),
        "operations": ("RETRACT", "EMIT"),
        "relations": ("CONDITION_FALSE", "NEXT"),
    },
    {
        "name": "quotation",
        "raw": "「全テストに成功」と結果を報告して。",
        "operations": ("EMIT",),
        "relations": ("CONTENT",),
    },
    {
        "name": "reference",
        "raw": "transform関数を修正して。その変更を元に戻して。",
        "operations": ("SET", "RETRACT"),
        "relations": ("NEXT", "REFERS_TO"),
    },
)


def _single_label_recall(
    raw: str,
    expected: Iterable[str],
    grounder: object,
) -> float:
    expected_items = list(expected)
    prediction = grounder.predict(raw).operation
    if prediction is None:
        return 0.0
    return (1.0 if prediction in expected_items else 0.0) / len(expected_items)


def _graph_metrics(graph: EventGraph, case: dict[str, object]) -> dict[str, object]:
    return {
        "name": case["name"],
        "event_recall": event_recall(graph, case["operations"]),
        "edge_recall": edge_relation_recall(graph, case["relations"]),
        "unresolved": len(graph.unresolved),
        "nodes": len(graph.nodes),
        "edges": len(graph.edges),
        "active_graph_bits": graph.description_bits,
        "provenance_bits": len(str(case["raw"]).encode("utf-8")) * 8,
        "flat_json_bits": graph.flat_json_bits,
        "feature_reads": graph.feature_reads,
    }


def _representation_invention(
    single_recall: float,
    graph_recall: float,
    graphs: Iterable[EventGraph],
) -> dict[str, object]:
    graph_items = list(graphs)
    graph_schema_bits = (
        len(EDGE_RELATIONS) * 32
        + 2 * 32
        + 4 * 32
        + 7 * 32
    )
    active_bits = sum(graph.description_bits for graph in graph_items)
    additional_bits = graph_schema_bits + active_bits
    missed_single = 1.0 - single_recall
    missed_graph = 1.0 - graph_recall
    avoided_loss_per_workload = (missed_single - missed_graph) * 1024.0
    break_even = (
        math.ceil(additional_bits / avoided_loss_per_workload)
        if avoided_loss_per_workload > 0
        else None
    )
    workloads = {}
    for reuses in (1, 4, 16, 64):
        workloads[str(reuses)] = {
            "single_objective": missed_single * 1024.0 * reuses,
            "graph_objective": additional_bits + missed_graph * 1024.0 * reuses,
        }
    return {
        "graph_schema_bits": graph_schema_bits,
        "active_graph_bits": active_bits,
        "additional_representation_bits": additional_bits,
        "avoided_loss_per_workload": avoided_loss_per_workload,
        "break_even_reuses": break_even,
        "workloads": workloads,
        "gate": (
            "invent the richer representation only when expected avoided "
            "decision loss exceeds schema, migration, parsing, and verification cost"
        ),
    }


def run() -> dict[str, object]:
    grounder = induce_raw_grounder(_traces(TRAINING_SPECIFICATION))
    graphs = [
        parse_event_graph(str(case["raw"]), grounder)
        for case in BENCHMARK
    ]
    metrics = [
        _graph_metrics(graph, case)
        for graph, case in zip(graphs, BENCHMARK)
    ]

    graph_event_recall = sum(item["event_recall"] for item in metrics) / len(metrics)
    graph_edge_recall = sum(item["edge_recall"] for item in metrics) / len(metrics)
    single_recall = sum(
        _single_label_recall(
            str(case["raw"]),
            case["operations"],
            grounder,
        )
        for case in BENCHMARK
    ) / len(BENCHMARK)

    workflow = execute_graph_workflow(graphs[0])
    active_bits = sum(item["active_graph_bits"] for item in metrics)
    provenance_bits = sum(item["provenance_bits"] for item in metrics)
    flat_bits = sum(item["flat_json_bits"] for item in metrics)

    return {
        "benchmark": {
            "cases": len(BENCHMARK),
            "single_label_event_recall": single_recall,
            "graph_event_recall": graph_event_recall,
            "graph_edge_recall": graph_edge_recall,
            "unresolved_clauses": sum(item["unresolved"] for item in metrics),
            "details": metrics,
        },
        "memory": {
            "active_graph_bits": active_bits,
            "provenance_ledger_bits": provenance_bits,
            "graph_plus_provenance_bits": active_bits + provenance_bits,
            "flat_json_handoff_bits": flat_bits,
            "flat_to_active_ratio": flat_bits / active_bits,
            "flat_to_graph_plus_provenance_ratio": (
                flat_bits / (active_bits + provenance_bits)
            ),
            "note": (
                "active decisions use the graph; raw utterances remain in a "
                "separate provenance ledger until retraction/audit expiry"
            ),
        },
        "workflow": {
            "executed": list(workflow.executed),
            "skipped": list(workflow.skipped),
            "final_expression": workflow.state.expression,
            "final_test": workflow.state.last_test,
            "report": workflow.state.report,
            "rollbacks": workflow.rollbacks,
            "tests": workflow.tests,
        },
        "representation_invention": _representation_invention(
            single_recall,
            graph_event_recall,
            graphs,
        ),
        "limitations": [
            "the clause and connector inventory is still small and partly hand-specified",
            "raw grounding still depends on Phase 9a subword evidence",
            "world knowledge and open-ended reference resolution are not solved",
            "the benchmark is synthetic rather than an actual repository or open conversation",
            "global graph induction is not proven optimal outside the finite benchmark",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    benchmark = payload["benchmark"]
    memory = payload["memory"]
    workflow = payload["workflow"]
    invention = payload["representation_invention"]
    lines = [
        "# Phase 9b results: hierarchical sparse event graphs",
        "",
        "Single-label grounding is replaced by a sparse graph with event, proposition,",
        "condition, content, temporal, and reference edges.",
        "",
        "## Grounding",
        "",
        f"- benchmark cases: **{benchmark['cases']}**",
        f"- single-label event recall: **{benchmark['single_label_event_recall']:.1%}**",
        f"- graph event recall: **{benchmark['graph_event_recall']:.1%}**",
        f"- graph edge recall: **{benchmark['graph_edge_recall']:.1%}**",
        f"- unresolved clauses: **{benchmark['unresolved_clauses']}**",
        "",
        "## Memory accounting",
        "",
        f"- active graph: **{memory['active_graph_bits']:,} bits**",
        f"- provenance ledger: **{memory['provenance_ledger_bits']:,} bits**",
        f"- graph + provenance: **{memory['graph_plus_provenance_bits']:,} bits**",
        f"- flat JSON hand-offs: **{memory['flat_json_handoff_bits']:,} bits**",
        f"- flat / active graph: **{memory['flat_to_active_ratio']:.2f}x**",
        f"- flat / graph+provenance: **{memory['flat_to_graph_plus_provenance_ratio']:.2f}x**",
        "",
        "## Conditional repair execution",
        "",
        f"- executed: `{' → '.join(workflow['executed'])}`",
        f"- skipped: `{', '.join(workflow['skipped']) or 'none'}`",
        f"- final expression: `{workflow['final_expression']}`",
        f"- final test: **{workflow['final_test']}**",
        f"- rollbacks / tests: **{workflow['rollbacks']} / {workflow['tests']}**",
        "",
        "## Representation-invention gate",
        "",
        f"- graph schema bits: **{invention['graph_schema_bits']:,}**",
        f"- active instance bits: **{invention['active_graph_bits']:,}**",
        f"- break-even reuses: **{invention['break_even_reuses']}**",
        "",
        "The graph is not adopted merely because it is more expressive. It is retained",
        "only when avoided decision loss repays representation, parsing, migration,",
        "verification, and runtime costs.",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["limitations"])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run()
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase9b.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "phase9b.md").write_text(
        render_markdown(payload),
        encoding="utf-8",
    )
    print(render_markdown(payload))


if __name__ == "__main__":
    main()
