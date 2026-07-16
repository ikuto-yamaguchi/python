from __future__ import annotations

import json
import resource
import time
from pathlib import Path

from .sparc_schema import SPARCHS3Model, SparseSchemaInducer


def configured_model() -> SPARCHS3Model:
    model = SPARCHS3Model()
    model.teach_statement("猫は哺乳類に分類されます", "猫", "isa", "哺乳類")
    model.teach_query("猫は生物に分類されますか", "猫", "isa", "生物")
    model.teach_statement("落雷によって停電が起きました", "落雷", "causes", "停電")
    model.teach_query("落雷は装置停止につながりますか", "落雷", "causes", "装置停止")
    model.teach_statement("Aの方がBより高いです", "A", "greater:height", "B")
    model.teach_query("AはDより高いですか", "A", "greater:height", "D")
    model.renderer.teach(
        "isa",
        positive="{S}は{O}に分類できます。",
        negative="{S}は{O}には分類できません。",
        evidence="{S}は{O}",
    )
    model.renderer.teach(
        "causes",
        positive="{S}は{O}につながる原因です。",
        evidence="{S}から{O}",
    )
    model.renderer.teach(
        "greater:height",
        positive="{S}は{O}より高いです。",
        evidence="{S}>{O}",
    )
    return model


def run_experiment(output_dir: str | Path = "results") -> dict[str, object]:
    start = time.perf_counter()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model = configured_model()
    transcript: list[dict[str, object]] = []

    def turn(text: str):
        result = model.reply(text)
        transcript.append(
            {
                "user": text,
                "assistant": result.text,
                "mechanism": result.mechanism,
                "hops": len(getattr(result, "path", ())),
                "schema_candidates": model.schemas.last_candidates_inspected,
                "anchor_reads": model.schemas.last_anchor_reads,
            }
        )
        return result

    for sentence in [
        "アキラは高校生に分類されます",
        "高校生は学生に分類されます",
        "学生は人に分類されます",
        "人は生物に分類されます",
    ]:
        turn(sentence)
    taxonomy = turn("アキラは生物に分類されますか")

    for sentence in [
        "落雷によって停電が起きました",
        "停電によって冷却停止が起きました",
        "冷却停止によって装置停止が起きました",
    ]:
        turn(sentence)
    cause = turn("落雷は装置停止につながりますか")

    for sentence in [
        "Aの方がBより高いです",
        "Bの方がCより高いです",
        "Cの方がDより高いです",
    ]:
        turn(sentence)
    comparison = turn("AはDより高いですか")

    restored = SPARCHS3Model.from_bytes(model.to_bytes())
    persisted = restored.reply("アキラは生物に分類されますか")

    checks = {
        "unseen_entity_schema_transfer": taxonomy.mechanism == "learned-schema-compositional-reasoning",
        "four_hop_schema_reasoning": len(taxonomy.path) == 4,
        "novel_compositional_answer": "根拠は" in taxonomy.text,
        "learned_causal_surface": cause.text.startswith("落雷は装置停止につながる原因"),
        "learned_comparison_surface": comparison.text.startswith("AはDより高い"),
        "persistence": persisted.text.startswith("アキラは生物に分類できます"),
        "bounded_schema_candidates": max(row["schema_candidates"] for row in transcript) <= 6,
        "no_whole_response_retrieval": model.report()["whole_response_retrieval_required_for_schema_answers"] is False,
    }

    scale_start = time.perf_counter()
    bank = SparseSchemaInducer(max_schemas=50_000, max_candidates=32)
    schema_count = 10_000
    for index in range(schema_count):
        bank.teach(
            kind="statement",
            sentence=f"識別子{index}:主体{index}は対象{index}へ写像されます",
            subject=f"主体{index}",
            object_=f"対象{index}",
            relation=f"relation:{index}",
            mode="learn",
        )

    correct = 0
    max_candidates = 0
    max_reads = 0
    queries = 512
    for sample in range(queries):
        index = (sample * 7919) % schema_count
        matched = bank.match(
            f"識別子{index}:未知主体{sample}は未知対象{sample}へ写像されます",
            "statement",
        )
        if (
            matched is not None
            and matched.relation == f"relation:{index}"
            and matched.subject == f"未知主体{sample}"
            and matched.object == f"未知対象{sample}"
        ):
            correct += 1
        max_candidates = max(max_candidates, bank.last_candidates_inspected)
        max_reads = max(max_reads, bank.last_anchor_reads)

    scale_report = bank.report()
    scale_report.update(
        {
            "sample_queries": queries,
            "correct_queries": correct,
            "max_candidates_observed": max_candidates,
            "max_anchor_reads_observed": max_reads,
            "build_and_query_seconds": time.perf_counter() - scale_start,
        }
    )

    result: dict[str, object] = {
        "capability_id": "SPARC-HS3-SCHEMA-COMPOSITION",
        "transformer_used": False,
        "softmax_attention_used": False,
        "growing_kv_cache_used": False,
        "learned_surface_schemas": True,
        "compositional_generation": True,
        "transcript": transcript,
        "checks": checks,
        "passed_checks": sum(checks.values()),
        "total_checks": len(checks),
        "compact_model": model.report(),
        "large_schema_bank": scale_report,
        "elapsed_seconds": time.perf_counter() - start,
        "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "claim_boundary": (
            "HS3 learns slot templates and answer renderers from structured demonstrations. "
            "It does not yet discover semantic roles from raw unlabeled text and is not high-school-level general intelligence."
        ),
    }
    result["passed"] = bool(
        all(checks.values())
        and correct == queries
        and max_candidates <= 32
        and max_reads <= 256
        and scale_report["serialized_bytes"] <= 20_000_000
        and result["peak_process_kib"] <= 1_500_000
        and result["elapsed_seconds"] <= 120.0
    )
    (output_dir / "sparc_hs3_schema.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "SPARC-HS3-compact.model.zlib").write_bytes(model.to_bytes())
    (output_dir / "SPARC-HS3-schema-bank.model.zlib").write_bytes(bank.to_bytes())
    return result


def main() -> None:
    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
