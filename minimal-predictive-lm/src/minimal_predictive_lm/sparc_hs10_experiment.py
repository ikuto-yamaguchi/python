from __future__ import annotations

import json
import resource
import string
import time
from pathlib import Path

from .sparc_hs9_experiment import configured_model as configured_hs9
from .sparc_role_induction_v2 import (
    ROLES,
    InducedDiscourseGraphV2,
    SPARCHS10ModelV2,
)


def _alpha_code(index: int) -> str:
    alphabet = string.ascii_uppercase
    output: list[str] = []
    value = index
    while True:
        output.append(alphabet[value % 26])
        value = value // 26 - 1
        if value < 0:
            break
    return "".join(reversed(output))


def _weak_document(code: str) -> str:
    return (
        f"学習計画{code}は段階的な改善を進めると考える。"
        f"なぜなら学習計画{code}では継続観測の成績が向上したからである。"
        f"例えば試行校{code}では協働課題の達成率が上がった。"
        f"しかし学習計画{code}には準備時間の負担がある。"
        f"確かに短期的な混乱は避けにくい。"
        f"したがって学習計画{code}は小規模導入から始めることが重要である。"
    )


def _cue_free_document(code: str) -> str:
    return (
        f"循環計画{code}は資源利用を見直す方針が望ましい。"
        f"導入後の観測では循環計画{code}の廃棄量が減少した。"
        f"試行地区{code}では回収材料の再利用率が上昇した。"
        f"初期設備費の負担は依然として残る。"
        f"短期的な作業混乱も完全には避けられない。"
        f"全体として循環計画{code}は段階導入を選ぶ判断が妥当だ。"
    )


def configured_model() -> SPARCHS10ModelV2:
    model = SPARCHS10ModelV2(configured_hs9())
    model.fit_role_documents(_weak_document(_alpha_code(i)) for i in range(240))
    model.ingest_learned_discourse(
        _cue_free_document("ZETA"),
        source_id="循環資料ZETA",
        title="無接続語循環論ZETA",
    )
    return model


def run_experiment(output_dir: str | Path = "results") -> dict[str, object]:
    start = time.perf_counter()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model = configured_model()

    learned_document = model.learned_discourse.documents[0]
    learned_roles = tuple(
        model.learned_discourse.nodes[node_id].role
        for node_id in learned_document.node_ids
    )
    expected_roles = (
        "claim",
        "evidence",
        "example",
        "counter",
        "concession",
        "conclusion",
    )

    answers = {
        "conversation": model.reply("こんにちは"),
        "social": model.reply("イタリアの首都は何ですか？"),
        "units": model.reply("時速90kmで40分進む距離は何kmですか？"),
        "episodic": model.reply("青葉市の水源はどこですか？"),
        "hs9_summary": model.reply("探究学習論の筆者の主張を要約してください。"),
        "cue_free_summary": model.reply(
            "無接続語循環論ZETAの筆者の主張を要約してください。"
        ),
        "cue_free_evidence": model.reply(
            "無接続語循環論ZETAの結論の根拠は何ですか？"
        ),
        "cue_free_counter": model.reply(
            "無接続語循環論ZETAにある反対意見を教えてください。"
        ),
    }

    compact_bytes = model.to_bytes()
    restored = SPARCHS10ModelV2.from_bytes(compact_bytes)
    persistence = restored.reply(
        "無接続語循環論ZETAの筆者の主張を要約してください。"
    )
    role_report = model.learned_discourse.inducer.report()

    checks = {
        "conversation_retained": answers["conversation"].text.startswith("こんにちは"),
        "social_retained": answers["social"].text == "ローマです。",
        "unit_math_retained": answers["units"].text.startswith("60kmです"),
        "episodic_source_retained": (
            answers["episodic"].text.startswith("北岳湖です")
            and "水資源報告" in answers["episodic"].text
        ),
        "hs9_discourse_retained": (
            "段階的に増やす" in answers["hs9_summary"].text
        ),
        "cue_free_role_sequence": learned_roles == expected_roles,
        "cue_free_summary": (
            answers["cue_free_summary"].mechanism == "sparse-discourse-summary"
            and "段階導入を選ぶ判断が妥当" in answers["cue_free_summary"].text
            and "循環資料ZETA" in answers["cue_free_summary"].text
        ),
        "cue_free_evidence": (
            answers["cue_free_evidence"].mechanism == "reverse-indexed-evidence"
            and "廃棄量が減少" in answers["cue_free_evidence"].text
        ),
        "cue_free_counter": (
            answers["cue_free_counter"].mechanism
            == "local-counterargument-retrieval"
            and "初期設備費" in answers["cue_free_counter"].text
        ),
        "original_cues_absent": all(
            cue not in _cue_free_document("ZETA")
            for cue in ("なぜなら", "例えば", "しかし", "確かに", "したがって")
        ),
        "cue_removed_learning": role_report["cue_words_removed_before_learning"] is True,
        "save_load_role_model": (
            "段階導入を選ぶ判断が妥当" in persistence.text
            and restored.learned_discourse.inducer.documents_seen == 240
        ),
    }

    scale_start = time.perf_counter()
    graph = InducedDiscourseGraphV2(
        model.learned_discourse.inducer,
        max_documents=25_000,
        max_candidates=24,
        read_budget=192,
    )
    document_count = 20_000
    for index in range(document_count):
        code = _alpha_code(index)
        graph.ingest_induced(
            _cue_free_document(code),
            source_id=f"循環資料{code}",
            title=f"無接続語循環論{code}",
        )

    sample_queries = 512
    correct = 0
    correct_roles = 0
    max_candidates = 0
    max_anchor_reads = 0
    max_edge_reads = 0
    max_operations = 0
    max_role_candidates = 0
    max_feature_reads = 0
    max_transition_reads = 0
    for sample in range(sample_queries):
        index = (sample * 7919) % document_count
        code = _alpha_code(index)
        document = graph.documents[index]
        roles = tuple(graph.nodes[node_id].role for node_id in document.node_ids)
        if roles == expected_roles:
            correct_roles += 1
        reply = graph.answer(
            f"無接続語循環論{code}の筆者の主張を要約してください。"
        )
        if (
            reply is not None
            and f"循環計画{code}は段階導入を選ぶ判断が妥当" in reply.text
            and f"循環資料{code}" in reply.text
        ):
            correct += 1
        max_candidates = max(max_candidates, graph.last_candidates)
        max_anchor_reads = max(max_anchor_reads, graph.last_anchor_reads)
        max_edge_reads = max(max_edge_reads, graph.last_edge_reads)
        max_operations = max(max_operations, graph.last_estimated_operations)
        max_role_candidates = max(
            max_role_candidates, graph.inducer.last_role_candidates
        )
        max_feature_reads = max(max_feature_reads, graph.inducer.last_feature_reads)
        max_transition_reads = max(
            max_transition_reads, graph.inducer.last_transition_reads
        )

    large_bytes = graph.to_bytes()
    scale_report = {
        "documents": len(graph.documents),
        "nodes": len(graph.nodes),
        "edges": len(graph.edges),
        "posting_edges": sum(len(items) for items in graph.postings.values()),
        "sample_queries": sample_queries,
        "correct_role_sequences": correct_roles,
        "correct_summary_queries": correct,
        "max_document_candidates": max_candidates,
        "max_anchor_reads": max_anchor_reads,
        "max_edge_reads": max_edge_reads,
        "max_estimated_operations": max_operations,
        "max_role_candidates": max_role_candidates,
        "max_feature_reads": max_feature_reads,
        "max_transition_reads": max_transition_reads,
        "serialized_bytes": len(large_bytes),
        "build_and_query_seconds": time.perf_counter() - scale_start,
        "full_document_scan_used": False,
        "corpus_role_scan_used": False,
    }

    result: dict[str, object] = {
        "capability_id": "SPARC-HS10-WEAK-STRUCTURAL-ROLE-INDUCTION",
        "transformer_used": False,
        "softmax_attention_used": False,
        "growing_kv_cache_used": False,
        "corpus_role_scan_used": False,
        "checks": checks,
        "passed_checks": sum(checks.values()),
        "total_checks": len(checks),
        "learned_roles": learned_roles,
        "answers": {
            key: {"text": value.text, "mechanism": value.mechanism}
            for key, value in answers.items()
        },
        "compact_model": model.report(),
        "large_role_induced_graph": scale_report,
        "elapsed_seconds": time.perf_counter() - start,
        "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "claim_boundary": (
            "HS10 learns a small discourse-role inventory from weak cue-rich documents "
            "after removing the cue expressions, then transfers by sparse features and "
            "structural consistency. It is not unrestricted semantic role discovery or "
            "Japanese high-school-level general intelligence."
        ),
    }
    result["passed"] = bool(
        all(checks.values())
        and correct == sample_queries
        and correct_roles == sample_queries
        and len(graph.nodes) == 120_000
        and max_candidates <= 1
        and max_anchor_reads == 0
        and max_edge_reads <= 4
        and max_operations <= 128
        and max_role_candidates == len(ROLES)
        and max_feature_reads <= 5_000
        and max_transition_reads <= 300
        and len(large_bytes) <= 10_000_000
        and result["peak_process_kib"] <= 1_000_000
        and result["elapsed_seconds"] <= 120.0
    )

    (output_dir / "sparc_hs10_role_induction.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "SPARC-HS10-compact.model.zlib").write_bytes(compact_bytes)
    (output_dir / "SPARC-HS10-role-graph-large.model.zlib").write_bytes(large_bytes)
    return result


def main() -> None:
    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
