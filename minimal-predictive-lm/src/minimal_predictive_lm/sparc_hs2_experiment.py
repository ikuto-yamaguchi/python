from __future__ import annotations

import json
import resource
import time
from pathlib import Path

from .sparc_hs2 import SPARCHS2Model
from .sparc_reasoning import SparseRelationalCortex


def run_experiment(output_dir: str | Path = "results") -> dict[str, object]:
    start = time.perf_counter()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model = SPARCHS2Model().fit_dialogues(
        [
            ("こんにちは", "こんにちは。何を一緒に考えましょうか？"),
            ("調子はどう？", "順調です。"),
            ("何ができる？", "学習した関係を局所的にたどって説明できます。"),
        ]
    )

    transcript: list[dict[str, object]] = []

    def turn(text: str):
        result = model.reply(text)
        transcript.append(
            {
                "user": text,
                "assistant": result.text,
                "mechanism": result.mechanism,
                "nodes_activated": getattr(result, "nodes_activated", 0),
                "edges_inspected": getattr(result, "edges_inspected", 0),
            }
        )
        return result

    turn("アキラは高校生です")
    turn("高校生は学生です")
    turn("学生は人です")
    turn("人は生物です")
    taxonomy = turn("アキラは生物ですか？")

    turn("ペンギンは哺乳類ではありません")
    negative = turn("ペンギンは哺乳類ですか？")

    turn("富士山の高さは3776メートルです")
    property_result = turn("富士山の高さは何ですか？")

    turn("落雷が原因で停電です")
    turn("停電が原因で冷却停止です")
    turn("冷却停止が原因で装置停止です")
    causal = turn("落雷は装置停止の原因ですか？")

    turn("AはBより高いです")
    turn("BはCより高いです")
    turn("CはDより高いです")
    comparison = turn("AとDではどちらが高いですか？")
    fallback = turn("こんにちは")

    restored = SPARCHS2Model.from_bytes(model.to_bytes())
    persistence = restored.reply("アキラは生物ですか？")

    checks = {
        "four_hop_taxonomy": taxonomy.text.startswith("はい") and len(taxonomy.path) == 4,
        "explicit_negative": negative.text.startswith("いいえ"),
        "property_recall": "3776メートル" in property_result.text,
        "three_hop_causality": causal.text.startswith("はい") and len(causal.path) == 3,
        "comparison_transitivity": comparison.text.startswith("Aの方"),
        "conversation_fallback": fallback.text.startswith("こんにちは"),
        "persistence": persistence.text.startswith("はい"),
        "bounded_small_reasoning": taxonomy.nodes_activated <= 8 and taxonomy.edges_inspected <= 8,
    }

    large_start = time.perf_counter()
    large = SparseRelationalCortex("desktop-large")
    chains = 20_000
    chain_edges = 4
    for chain in range(chains):
        for step in range(chain_edges):
            large.learn_text(f"概念{chain}_{step}は概念{chain}_{step+1}です")

    correct = 0
    max_nodes = 0
    max_edges = 0
    sample_count = 512
    for sample in range(sample_count):
        chain = (sample * 7919) % chains
        result = large.answer(f"概念{chain}_0は概念{chain}_4ですか？")
        if result is not None and result.text.startswith("はい") and len(result.path) == 4:
            correct += 1
            max_nodes = max(max_nodes, result.nodes_activated)
            max_edges = max(max_edges, result.edges_inspected)

    large_bytes = large.to_bytes()
    large_seconds = time.perf_counter() - large_start
    large_report = large.report()
    large_report.update(
        {
            "chains": chains,
            "facts_inserted": chains * chain_edges,
            "sample_queries": sample_count,
            "correct_queries": correct,
            "max_nodes_activated_observed": max_nodes,
            "max_edges_inspected_observed": max_edges,
            "build_and_query_seconds": large_seconds,
        }
    )

    result: dict[str, object] = {
        "capability_id": "SPARC-HS2-RELATIONAL",
        "target": "large-capacity low-activation Japanese relational intelligence",
        "transformer_used": False,
        "softmax_attention_used": False,
        "growing_kv_cache_used": False,
        "interactive_chat": True,
        "online_learning": True,
        "transcript": transcript,
        "checks": checks,
        "passed_checks": sum(checks.values()),
        "total_checks": len(checks),
        "compact_model": model.report(),
        "large_relational_cortex": large_report,
        "elapsed_seconds": time.perf_counter() - start,
        "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "claim_boundary": (
            "HS2 adds bounded multi-hop relational inference to the interactive sparse language model. "
            "It still uses bootstrap Japanese relation templates and is not yet high-school-level general intelligence. "
            "HS3 must learn relation induction and compositional generation from broad natural text."
        ),
    }
    result["passed"] = bool(
        all(checks.values())
        and correct == sample_count
        and max_nodes <= 8
        and max_edges <= 8
        and len(large_bytes) <= 20_000_000
        and result["peak_process_kib"] <= 2_000_000
        and result["elapsed_seconds"] <= 120.0
    )
    (output_dir / "sparc_hs2_relational.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "SPARC-HS2-compact.model.zlib").write_bytes(model.to_bytes())
    (output_dir / "SPARC-HS2-large-relational.model.zlib").write_bytes(large_bytes)
    return result


if __name__ == "__main__":
    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2))
