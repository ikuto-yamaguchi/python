from __future__ import annotations

import json
from pathlib import Path

from .connector_induction import (
    ConnectorObservation,
    induce_connector_lexicon,
    parse_with_connector_lexicon,
)
from .hierarchical_event_graph import edge_relation_recall, event_recall
from .phase9a_experiment import TRAINING_SPECIFICATION, _traces
from .raw_event_program import induce_raw_grounder


def _role_observations() -> list[ConnectorObservation]:
    return [
        ConnectorObservation("なら", True, True, False, False, False, False),
        ConnectorObservation("なら", False, False, False, False, False, False),
        ConnectorObservation("でなければ", True, False, False, False, False, False),
        ConnectorObservation("でなければ", False, True, False, False, False, False),
        ConnectorObservation("その後", None, True, True, False, False, True),
        ConnectorObservation("その後", None, True, True, False, False, True),
        ConnectorObservation("その変更を", None, True, True, True, False, False),
        ConnectorObservation("その変更を", None, True, True, True, False, False),
        ConnectorObservation("という内容で", None, True, False, False, True, False),
        ConnectorObservation("という内容で", None, True, False, False, True, False),
    ]


def _shifted_observations() -> list[ConnectorObservation]:
    return [
        ConnectorObservation("ときは", True, True, False, False, False, False),
        ConnectorObservation("ときは", False, False, False, False, False, False),
        ConnectorObservation("そうでなければ", True, False, False, False, False, False),
        ConnectorObservation("そうでなければ", False, True, False, False, False, False),
        ConnectorObservation("続いて", None, True, True, False, False, True),
        ConnectorObservation("続いて", None, True, True, False, False, True),
        ConnectorObservation("それを", None, True, True, True, False, False),
        ConnectorObservation("それを", None, True, True, True, False, False),
        ConnectorObservation("と伝えて", None, True, False, False, True, False),
        ConnectorObservation("と伝えて", None, True, False, False, True, False),
    ]


def _mapping_accuracy(lexicon: object, expected: dict[str, str]) -> float:
    return sum(lexicon.role(connector) == role for connector, role in expected.items()) / len(expected)


def run() -> dict[str, object]:
    base_result = induce_connector_lexicon(_role_observations())
    shifted_result = induce_connector_lexicon(_shifted_observations())
    combined_result = induce_connector_lexicon(_role_observations() + _shifted_observations())

    expected_base = {
        "なら": "CONDITION_TRUE",
        "でなければ": "CONDITION_FALSE",
        "その後": "SEQUENCE",
        "その変更を": "REFERENCE",
        "という内容で": "CONTENT",
    }
    expected_shifted = {
        "ときは": "CONDITION_TRUE",
        "そうでなければ": "CONDITION_FALSE",
        "続いて": "SEQUENCE",
        "それを": "REFERENCE",
        "と伝えて": "CONTENT",
    }

    grounder = induce_raw_grounder(_traces(TRAINING_SPECIFICATION))
    benchmark = (
        (
            "transform関数を修正して。その変更を元に戻して。",
            ("SET", "RETRACT"),
            ("NEXT", "REFERS_TO"),
        ),
        (
            "テストが失敗なら変更を元に戻して。",
            ("RETRACT",),
            ("CONDITION_TRUE",),
        ),
        (
            "transform関数を修正して、その後テストを実行して。",
            ("SET", "VERIFY"),
            ("NEXT",),
        ),
        (
            "「全テストに成功」という内容で結果を報告して。",
            ("EMIT",),
            ("CONTENT",),
        ),
        (
            "テストが成功ときは結果を報告して。",
            ("EMIT",),
            ("CONDITION_TRUE",),
        ),
        (
            "transform関数を修正して、続いてテストを実行して。",
            ("SET", "VERIFY"),
            ("NEXT",),
        ),
    )
    graph_details: list[dict[str, object]] = []
    for raw, operations, relations in benchmark:
        graph = parse_with_connector_lexicon(raw, grounder, combined_result.lexicon)
        graph_details.append(
            {
                "raw": raw,
                "event_recall": event_recall(graph, operations),
                "edge_recall": edge_relation_recall(graph, relations),
                "unresolved": len(graph.unresolved),
                "graph_bits": graph.description_bits,
                "feature_reads": graph.feature_reads,
            }
        )

    exact_surface_shifted = sum(
        connector in expected_base for connector in expected_shifted
    ) / len(expected_shifted)
    return {
        "base_induction": {
            "connectors": len(expected_base),
            "observations": len(_role_observations()),
            "mapping_accuracy": _mapping_accuracy(base_result.lexicon, expected_base),
            "candidate_evaluations": base_result.candidate_evaluations,
            "description_bits": base_result.lexicon.description_bits,
            "data_bits": base_result.total_data_bits,
        },
        "shifted_induction": {
            "connectors": len(expected_shifted),
            "observations": len(_shifted_observations()),
            "exact_surface_accuracy": exact_surface_shifted,
            "interaction_induced_accuracy": _mapping_accuracy(shifted_result.lexicon, expected_shifted),
            "candidate_evaluations": shifted_result.candidate_evaluations,
            "description_bits": shifted_result.lexicon.description_bits,
        },
        "graph_transfer": {
            "cases": len(graph_details),
            "event_recall": sum(item["event_recall"] for item in graph_details) / len(graph_details),
            "edge_recall": sum(item["edge_recall"] for item in graph_details) / len(graph_details),
            "unresolved": sum(item["unresolved"] for item in graph_details),
            "details": graph_details,
        },
        "combined": {
            "connectors": len(combined_result.lexicon.rules),
            "observations": combined_result.lexicon.observations,
            "description_bits": combined_result.lexicon.description_bits,
            "candidate_evaluations": combined_result.candidate_evaluations,
        },
        "limitations": [
            "candidate relation types are still supplied even though connector-to-role mappings are induced",
            "interaction traces expose execution, reference, content, and temporal effects",
            "the connector benchmark is synthetic and Japanese-only",
            "open-ended syntax and long-distance discourse relations are not solved",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    base = payload["base_induction"]
    shifted = payload["shifted_induction"]
    graph = payload["graph_transfer"]
    lines = [
        "# Phase 9c results: connector semantics induced from interaction effects",
        "",
        "Connector strings are not assigned hand-written relation labels. Their roles are",
        "selected by minimum description length from observed execution, reference, content,",
        "and temporal effects.",
        "",
        "## Connector-role induction",
        "",
        f"- base connectors / observations: **{base['connectors']} / {base['observations']}**",
        f"- base mapping accuracy: **{base['mapping_accuracy']:.1%}**",
        f"- shifted exact-surface accuracy: **{shifted['exact_surface_accuracy']:.1%}**",
        f"- shifted interaction-induced accuracy: **{shifted['interaction_induced_accuracy']:.1%}**",
        f"- shifted observations: **{shifted['observations']}**",
        "",
        "## Event-graph transfer",
        "",
        f"- cases: **{graph['cases']}**",
        f"- event recall: **{graph['event_recall']:.1%}**",
        f"- edge recall: **{graph['edge_recall']:.1%}**",
        f"- unresolved clauses: **{graph['unresolved']}**",
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
    (output / "phase9c.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "phase9c.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload))


if __name__ == "__main__":
    main()
