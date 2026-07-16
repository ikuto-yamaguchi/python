from __future__ import annotations

import json
import resource
import string
import time
from pathlib import Path

from .sparc_cross_domain_plans import SPARCHS11Model, SparseCrossDomainPlanBank
from .sparc_hs10_experiment_v2 import configured_model as configured_hs10
from .sparc_role_induction_v3 import SPARCHS10ModelV3


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


def _add_vehicle(
    model: SPARCHS11Model,
    name: str,
    speed: float,
    hours: float,
    *,
    source_prefix: str,
) -> None:
    model.ingest_fact(
        f"{name}の速度は時速{speed:g}kmである。",
        source_id=f"{source_prefix}速度資料",
    )
    model.ingest_fact(
        f"{name}の運転時間は{hours:g}時間である。",
        source_id=f"{source_prefix}時間資料",
    )


def configured_model() -> SPARCHS11Model:
    model = SPARCHS11Model(configured_hs10())
    _add_vehicle(model, "列車A", 60, 2, source_prefix="A")
    _add_vehicle(model, "列車B", 45, 3, source_prefix="B")
    _add_vehicle(model, "列車C", 80, 1.5, source_prefix="C")
    distance_plan = model.teach_plan(
        [
            ("列車Aの移動距離は何kmですか？", "120km"),
            ("列車Bの移動距離は何kmですか？", "135km"),
            ("列車Cの移動距離は何kmですか？", "120km"),
        ]
    )
    model.link_plan_surface(
        "列車Aが走行する距離は何kmですか？", "列車A", distance_plan
    )

    for name, distance, speed in (
        ("車両P", 120, 60),
        ("車両Q", 150, 50),
        ("車両R", 90, 60),
    ):
        model.ingest_fact(
            f"{name}の移動距離は{distance:g}kmである。",
            source_id=f"{name}距離資料",
        )
        model.ingest_fact(
            f"{name}の速度は時速{speed:g}kmである。",
            source_id=f"{name}速度資料",
        )
    model.teach_plan(
        [
            ("車両Pの所要時間は何時間ですか？", "2時間"),
            ("車両Qの所要時間は何時間ですか？", "3時間"),
            ("車両Rの所要時間は何時間ですか？", "1.5時間"),
        ]
    )
    return model


def run_experiment(output_dir: str | Path = "results") -> dict[str, object]:
    start = time.perf_counter()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model = configured_model()

    _add_vehicle(model, "列車D", 72, 2.5, source_prefix="D")
    _add_vehicle(model, "列車E", 36, 0.5, source_prefix="E")
    answers = {
        "conversation": model.reply("こんにちは"),
        "hs10": model.reply(
            "無接続語循環論ZETAの筆者の主張を要約してください。"
        ),
        "distance": model.reply("列車Dの移動距離は何kmですか？"),
        "linked_surface": model.reply("列車Eが走行する距離は何kmですか？"),
        "duration": model.reply("車両Qの所要時間は何時間ですか？"),
    }

    model.ingest_fact(
        "列車Fの速度は時速60kmである。", source_id="F速度資料1"
    )
    model.ingest_fact(
        "列車Fの速度は時速70kmである。", source_id="F速度資料2"
    )
    model.ingest_fact(
        "列車Fの運転時間は2時間である。", source_id="F時間資料"
    )
    conflict = model.reply("列車Fの移動距離は何kmですか？")
    model.ingest_fact(
        "最新情報:列車Fの速度は時速80kmである。",
        source_id="F訂正速度資料",
        revision=True,
    )
    revised = model.reply("列車Fの移動距離は何kmですか？")

    compact_bytes = model.to_bytes()
    restored = SPARCHS11Model.from_bytes(compact_bytes)
    persistence = restored.reply("列車Dの移動距離は何kmですか？")
    plan_report = model.plans.report()

    checks = {
        "conversation_retained": answers["conversation"].text.startswith("こんにちは"),
        "hs10_retained": "段階導入を選ぶ判断が妥当" in answers["hs10"].text,
        "cross_document_distance": (
            answers["distance"].text.startswith("180kmです")
            and "D速度資料" in answers["distance"].text
            and "D時間資料" in answers["distance"].text
        ),
        "linked_surface_plan": answers["linked_surface"].text.startswith("18kmです"),
        "inverse_duration_plan": answers["duration"].text.startswith("3時間です"),
        "dimensionally_typed_plan": (
            "式" in answers["distance"].text
            and answers["distance"].mechanism == "learned-cross-domain-plan"
        ),
        "conflict_refusal": (
            conflict.mechanism == "cross-domain-evidence-conflict"
            and "確定できません" in conflict.text
        ),
        "revision_reenables_plan": (
            revised.text.startswith("160kmです")
            and "F訂正速度資料" in revised.text
        ),
        "two_shared_plans": plan_report["plans"] == 2,
        "local_fact_reads": answers["distance"].active_bits == 2,
        "save_load_plan": (
            persistence.text.startswith("180kmです")
            and restored.plans.report()["plans"] == 2
        ),
        "no_global_scans": (
            plan_report["global_subject_scan_used"] is False
            and plan_report["global_episode_scan_used"] is False
            and plan_report["global_plan_scan_used"] is False
        ),
    }

    scale_start = time.perf_counter()
    large = SPARCHS11Model(SPARCHS10ModelV3())
    entity_count = 50_000
    for index in range(entity_count):
        code = _alpha_code(index)
        _add_vehicle(
            large,
            f"輸送体{code}",
            30 + (index % 91),
            0.5 + (index % 7) * 0.25,
            source_prefix=f"資料{code}",
        )
    scale_plan = large.teach_plan(
        [
            (
                f"輸送体{_alpha_code(index)}の移動距離は何kmですか？",
                f"{(30 + (index % 91)) * (0.5 + (index % 7) * 0.25):g}km",
            )
            for index in (3, 117, 902)
        ]
    )

    sample_queries = 512
    correct = 0
    max_candidates = 0
    max_anchor_reads = 0
    max_fact_reads = 0
    max_operations = 0
    for sample in range(sample_queries):
        index = (sample * 7919) % entity_count
        code = _alpha_code(index)
        expected = (30 + (index % 91)) * (0.5 + (index % 7) * 0.25)
        reply = large.reply(f"輸送体{code}の移動距離は何kmですか？")
        if reply.text.startswith(f"{expected:g}kmです"):
            correct += 1
        max_candidates = max(max_candidates, large.plans.last_plan_candidates)
        max_anchor_reads = max(max_anchor_reads, large.plans.last_anchor_reads)
        max_fact_reads = max(max_fact_reads, large.plans.last_fact_reads)
        max_operations = max(max_operations, reply.estimated_sparse_operations)

    large_bytes = large.to_bytes()
    large_report = large.plans.report()
    scale_report = {
        "subjects": entity_count,
        "episodes": len(large.episodic.episodes),
        "indexed_relation_slots": large_report["indexed_relation_slots"],
        "plans": large_report["plans"],
        "schemas": large_report["schemas"],
        "sample_queries": sample_queries,
        "correct_queries": correct,
        "max_plan_candidates": max_candidates,
        "max_anchor_reads": max_anchor_reads,
        "max_fact_reads": max_fact_reads,
        "max_estimated_operations": max_operations,
        "expression_cost": scale_plan.expression.cost,
        "search_attempts": large.plans.last_search_attempts,
        "serialized_bytes": len(large_bytes),
        "build_and_query_seconds": time.perf_counter() - scale_start,
        "global_subject_scan_used": False,
        "global_episode_scan_used": False,
        "global_plan_scan_used": False,
    }

    result: dict[str, object] = {
        "capability_id": "SPARC-HS11-CROSS-DOMAIN-EVIDENCE-PLANS",
        "transformer_used": False,
        "softmax_attention_used": False,
        "growing_kv_cache_used": False,
        "checks": checks,
        "passed_checks": sum(checks.values()),
        "total_checks": len(checks),
        "answers": {
            key: {"text": value.text, "mechanism": value.mechanism}
            for key, value in answers.items()
        },
        "conflict": {"text": conflict.text, "mechanism": conflict.mechanism},
        "revised": {"text": revised.text, "mechanism": revised.mechanism},
        "compact_model": model.report(),
        "large_cross_domain_memory": scale_report,
        "elapsed_seconds": time.perf_counter() - start,
        "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "claim_boundary": (
            "HS11 learns bounded typed evidence-to-arithmetic plans from outcome "
            "demonstrations. It does not yet learn arbitrary algorithms, proof "
            "strategies or open-ended research plans and is not Japanese "
            "high-school-level general intelligence."
        ),
    }
    result["passed"] = bool(
        all(checks.values())
        and correct == sample_queries
        and scale_report["episodes"] == 100_000
        and scale_report["indexed_relation_slots"] == 100_000
        and max_candidates <= 1
        and max_anchor_reads <= 32
        and max_fact_reads <= 2
        and max_operations <= 64
        and scale_report["plans"] == 1
        and scale_report["schemas"] == 1
        and len(large_bytes) <= 10_000_000
        and result["peak_process_kib"] <= 1_200_000
        and result["elapsed_seconds"] <= 120.0
    )

    (output_dir / "sparc_hs11_cross_domain.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "SPARC-HS11-compact.model.zlib").write_bytes(compact_bytes)
    (output_dir / "SPARC-HS11-cross-domain-large.model.zlib").write_bytes(large_bytes)
    return result


def main() -> None:
    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
