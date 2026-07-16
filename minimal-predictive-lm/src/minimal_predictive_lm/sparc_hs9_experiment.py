from __future__ import annotations

import json
import resource
import string
import time
from pathlib import Path

from .sparc_discourse import SPARCHS9Model, SparseDiscourseGraph
from .sparc_hs8_experiment import configured_model as configured_hs8


ARTICLE = (
    "学校は探究学習の時間を増やすべきである。"
    "なぜなら、生徒が自分で問いを立てる力を伸ばせるからである。"
    "例えば、地域の水質を調べる活動では理科と社会の知識を結び付けられる。"
    "しかし、基礎知識の授業時間が減るという懸念もある。"
    "したがって、基礎授業を維持しながら探究学習を段階的に増やすことが重要である。"
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


def configured_model() -> SPARCHS9Model:
    model = SPARCHS9Model(configured_hs8())
    model.ingest_discourse(ARTICLE, source_id="教育論A", title="探究学習論")
    model.ingest_discourse(
        "都市は自動車交通を減らすべきである。"
        "なぜなら大気汚染を抑えられるからである。"
        "したがって公共交通を優先することが重要である。",
        source_id="交通A",
        title="公共交通優先論",
    )
    model.ingest_discourse(
        "都市は道路容量を増やすべきである。"
        "なぜなら物流の遅延を減らせるからである。"
        "したがって幹線道路の整備が重要である。",
        source_id="交通B",
        title="道路整備論",
    )
    return model


def run_experiment(output_dir: str | Path = "results") -> dict[str, object]:
    start = time.perf_counter()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model = configured_model()

    answers = {
        "conversation": model.reply("こんにちは"),
        "social": model.reply("イタリアの首都は何ですか？"),
        "units": model.reply("時速90kmで40分進む距離は何kmですか？"),
        "episodic": model.reply("青葉市の水源はどこですか？"),
        "summary": model.reply("探究学習論の筆者の主張を要約してください。"),
        "evidence": model.reply("探究学習論の結論の根拠は何ですか？"),
        "counter": model.reply("探究学習論にある反対意見を教えてください。"),
        "comparison": model.reply("公共交通優先論と道路整備論の違いを比較してください。"),
    }
    generic = model.reply("この文章の要旨は何ですか？")

    compact_bytes = model.to_bytes()
    restored = SPARCHS9Model.from_bytes(compact_bytes)
    persistence = restored.reply("探究学習論の根拠を説明してください。")

    checks = {
        "conversation_retained": answers["conversation"].text.startswith("こんにちは"),
        "social_retained": answers["social"].text == "ローマです。",
        "unit_math_retained": answers["units"].text.startswith("60kmです"),
        "episodic_source_retained": (
            answers["episodic"].text.startswith("北岳湖です")
            and "水資源報告" in answers["episodic"].text
        ),
        "main_claim_summary": (
            answers["summary"].mechanism == "sparse-discourse-summary"
            and "段階的に増やす" in answers["summary"].text
            and "問いを立てる力" in answers["summary"].text
        ),
        "reverse_indexed_evidence": (
            answers["evidence"].mechanism == "reverse-indexed-evidence"
            and "問いを立てる力" in answers["evidence"].text
        ),
        "counterargument": (
            answers["counter"].mechanism == "local-counterargument-retrieval"
            and "授業時間が減る" in answers["counter"].text
        ),
        "two_document_comparison": (
            answers["comparison"].mechanism == "bounded-two-document-comparison"
            and "交通A" in answers["comparison"].text
            and "交通B" in answers["comparison"].text
        ),
        "bounded_generic_workspace": (
            "段階的に増やす" in generic.text
            and len(model.discourse.workspace) <= model.discourse.workspace.maxlen
        ),
        "save_load_reverse_indices": (
            "問いを立てる力" in persistence.text
            and restored.discourse.report()["global_edge_scan_used"] is False
        ),
    }

    scale_start = time.perf_counter()
    graph = SparseDiscourseGraph(
        max_documents=25_000,
        max_candidates=24,
        read_budget=192,
    )
    document_count = 20_000
    for index in range(document_count):
        code = _alpha_code(index)
        graph.ingest(
            f"循環計画{code}では資源循環を進めるべきである。"
            f"なぜなら循環計画{code}は廃棄物を減らせるからである。"
            f"例えば循環設備{code}は材料を再利用できる。"
            f"しかし循環計画{code}には初期費用の懸念がある。"
            f"したがって循環計画{code}は段階導入が重要である。",
            source_id=f"循環資料{code}",
            title=f"循環論{code}",
        )

    sample_queries = 512
    correct = 0
    max_candidates = 0
    max_anchor_reads = 0
    max_edge_reads = 0
    max_operations = 0
    for sample in range(sample_queries):
        index = (sample * 7919) % document_count
        code = _alpha_code(index)
        reply = graph.answer(f"循環論{code}の筆者の主張を要約してください。")
        if (
            reply is not None
            and f"循環計画{code}は段階導入が重要" in reply.text
            and f"循環資料{code}" in reply.text
        ):
            correct += 1
        max_candidates = max(max_candidates, graph.last_candidates)
        max_anchor_reads = max(max_anchor_reads, graph.last_anchor_reads)
        max_edge_reads = max(max_edge_reads, graph.last_edge_reads)
        max_operations = max(max_operations, graph.last_estimated_operations)

    large_bytes = graph.to_bytes()
    scale_report = {
        "documents": len(graph.documents),
        "nodes": len(graph.nodes),
        "edges": len(graph.edges),
        "posting_edges": sum(len(items) for items in graph.postings.values()),
        "sample_queries": sample_queries,
        "correct_queries": correct,
        "max_candidates_observed": max_candidates,
        "max_anchor_reads_observed": max_anchor_reads,
        "max_edge_reads_observed": max_edge_reads,
        "max_estimated_operations": max_operations,
        "serialized_bytes": len(large_bytes),
        "build_and_query_seconds": time.perf_counter() - scale_start,
        "global_edge_scan_used": False,
        "full_document_scan_used": False,
    }

    result: dict[str, object] = {
        "capability_id": "SPARC-HS9-SPARSE-DISCOURSE-GRAPH",
        "transformer_used": False,
        "softmax_attention_used": False,
        "growing_kv_cache_used": False,
        "global_edge_scan_used": False,
        "checks": checks,
        "passed_checks": sum(checks.values()),
        "total_checks": len(checks),
        "answers": {
            key: {"text": value.text, "mechanism": value.mechanism}
            for key, value in answers.items()
        },
        "compact_model": {
            "serialized_bytes": len(compact_bytes),
            "discourse": model.discourse.report(),
        },
        "large_discourse_graph": scale_report,
        "elapsed_seconds": time.perf_counter() - start,
        "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "claim_boundary": (
            "HS9 adds sparse claim-evidence-counterargument discourse graphs. "
            "Role classification remains a bootstrap surface mechanism and is not "
            "unrestricted Japanese reading comprehension or high-school-level AGI."
        ),
    }
    result["passed"] = bool(
        all(checks.values())
        and correct == sample_queries
        and max_candidates <= 24
        and max_anchor_reads <= 192
        and max_edge_reads <= 8
        and max_operations <= 512
        and len(large_bytes) <= 20_000_000
        and result["peak_process_kib"] <= 1_000_000
        and result["elapsed_seconds"] <= 120.0
    )

    (output_dir / "sparc_hs9_discourse.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "SPARC-HS9-compact.model.zlib").write_bytes(compact_bytes)
    (output_dir / "SPARC-HS9-discourse-large.model.zlib").write_bytes(large_bytes)
    return result


def main() -> None:
    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
