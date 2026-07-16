from __future__ import annotations

import json
import resource
import string
import time
from pathlib import Path

from .sparc_counterexamples_v2 import SPARCHS14ModelV2
from .sparc_cross_domain_plans_v2 import SPARCHS11ModelV2
from .sparc_goal_rules import SPARCHS13Model
from .sparc_hs13_experiment import configured_model as configured_hs13
from .sparc_relational_plans import SPARCHS12Model


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


def _add_training_rule(model: SPARCHS14ModelV2) -> None:
    model.ingest_fact("哺乳類の標準活動は活動である。", source_id="哺乳類活動資料")
    for animal in ("クマA", "クマB", "クマC"):
        model.ingest_fact(
            f"{animal}の分類は哺乳類である。", source_id=f"{animal}分類資料"
        )
        model.ingest_fact(
            f"{animal}の活動状態は活動である。", source_id=f"{animal}直接観測"
        )
    model.base.teach_rule(
        [
            ("クマAの活動状態は何ですか？", "活動です"),
            ("クマBの活動状態は何ですか？", "活動です"),
            ("クマCの活動状態は何ですか？", "活動です"),
        ]
    )


def _add_validation_subject(
    model: SPARCHS14ModelV2,
    subject: str,
    season: str,
    observed: str,
) -> None:
    model.ingest_fact(
        f"{subject}の分類は哺乳類である。", source_id=f"{subject}分類資料"
    )
    model.ingest_fact(
        f"{subject}の季節状態は{season}である。", source_id=f"{subject}季節資料"
    )
    model.ingest_fact(
        f"{subject}の活動状態は{observed}である。", source_id=f"{subject}観測資料"
    )


def _validate(model: SPARCHS14ModelV2) -> None:
    for subject in ("支持A", "支持B", "支持C"):
        _add_validation_subject(model, subject, "通常", "活動")
    for subject in ("反例A", "反例B", "反例C"):
        _add_validation_subject(model, subject, "冬眠中", "休止")
    model.validate_rules(
        [
            *((f"{subject}の活動状態は何ですか？", "活動です") for subject in ("支持A", "支持B", "支持C")),
            *((f"{subject}の活動状態は何ですか？", "休止です") for subject in ("反例A", "反例B", "反例C")),
        ]
    )


def configured_model() -> SPARCHS14ModelV2:
    model = SPARCHS14ModelV2(configured_hs13())
    _add_training_rule(model)
    _validate(model)
    return model


def run_experiment(output_dir: str | Path = "results") -> dict[str, object]:
    start = time.perf_counter()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model = configured_model()

    model.ingest_fact("未知通常の分類は哺乳類である。", source_id="通常分類資料")
    model.ingest_fact("未知通常の季節状態は通常である。", source_id="通常季節資料")
    model.ingest_fact("未知冬眠の分類は哺乳類である。", source_id="冬眠分類資料")
    model.ingest_fact("未知冬眠の季節状態は冬眠中である。", source_id="冬眠季節資料")
    model.ingest_fact("直接冬眠の分類は哺乳類である。", source_id="直接分類資料")
    model.ingest_fact("直接冬眠の季節状態は冬眠中である。", source_id="直接季節資料")
    model.ingest_fact("直接冬眠の活動状態は休止である。", source_id="直接活動資料")

    answers = {
        "conversation": model.reply("こんにちは"),
        "hs13_nested": model.reply("ハヤブサの生理区分は何ですか？"),
        "normal": model.reply("未知通常の活動状態は何ですか？"),
        "hibernating": model.reply("未知冬眠の活動状態は何ですか？"),
        "direct_override": model.reply("直接冬眠の活動状態は何ですか？"),
    }
    validator_report = model.validator.report()
    state = next(iter(model.validator.states.values()))
    compact_bytes = model.to_bytes()
    restored = SPARCHS14ModelV2.from_bytes(compact_bytes)
    restored.ingest_fact("復元冬眠の分類は哺乳類である。", source_id="復元分類資料")
    restored.ingest_fact("復元冬眠の季節状態は冬眠中である。", source_id="復元季節資料")
    persistence = restored.reply("復元冬眠の活動状態は何ですか？")

    checks = {
        "conversation_retained": answers["conversation"].text.startswith("こんにちは"),
        "hs13_recursive_rules_retained": answers["hs13_nested"].text.startswith("恒温型です"),
        "support_refutation_counts": (
            validator_report["supports"] == 3
            and validator_report["refutations"] == 3
        ),
        "single_learned_guard": (
            len(state.exclusion_guards) == 1
            and state.exclusion_guards[0].relation == "季節状態"
            and state.exclusion_guards[0].value == "冬眠中"
        ),
        "ordinary_case_still_generalises": (
            answers["normal"].text.startswith("活動です")
            and answers["normal"].mechanism == "goal-directed-learned-rule"
        ),
        "counterexample_case_blocked": (
            answers["hibernating"].mechanism == "counterexample-guarded-rule"
            and "季節状態=冬眠中" in answers["hibernating"].text
        ),
        "direct_observation_priority": (
            answers["direct_override"].text.startswith("休止です")
            and answers["direct_override"].mechanism != "counterexample-guarded-rule"
        ),
        "guard_cost_accounted": answers["normal"].estimated_sparse_operations <= 24,
        "posterior_reported": abs(validator_report["posterior_support_fraction"] - 0.5) < 1e-9,
        "save_load_guard": persistence.mechanism == "counterexample-guarded-rule",
        "no_validation_scan_at_inference": validator_report["validation_scan_used_at_inference"] is False,
        "no_global_exception_scan": validator_report["global_exception_scan_used"] is False,
    }

    scale_start = time.perf_counter()
    large = SPARCHS14ModelV2(
        SPARCHS13Model(SPARCHS12Model(SPARCHS11ModelV2()))
    )
    _add_training_rule(large)
    _validate(large)
    subject_count = 50_000
    for index in range(subject_count):
        code = _alpha_code(index)
        subject = f"個体{code}"
        season = "通常" if index % 2 == 0 else "冬眠中"
        large.ingest_fact(
            f"{subject}の分類は哺乳類である。", source_id=f"分類資料{code}"
        )
        large.ingest_fact(
            f"{subject}の季節状態は{season}である。", source_id=f"季節資料{code}"
        )

    sample_queries = 512
    correct_normal = 0
    correct_blocked = 0
    max_rule_candidates = 0
    max_guard_reads = 0
    max_rule_reads = 0
    max_edge_reads = 0
    max_nodes = 0
    max_operations = 0
    for sample in range(sample_queries):
        index = (sample * 7919) % subject_count
        code = _alpha_code(index)
        reply = large.reply(f"個体{code}の活動状態は何ですか？")
        if index % 2 == 0:
            if reply.text.startswith("活動です"):
                correct_normal += 1
        else:
            if reply.mechanism == "counterexample-guarded-rule":
                correct_blocked += 1
        max_rule_candidates = max(
            max_rule_candidates, large.validator.last_rule_candidates
        )
        max_guard_reads = max(max_guard_reads, large.validator.last_guard_reads)
        max_rule_reads = max(max_rule_reads, large.rules.last_rule_reads)
        max_edge_reads = max(max_edge_reads, large.rules.last_edge_reads)
        max_nodes = max(max_nodes, large.rules.last_nodes_activated)
        max_operations = max(max_operations, reply.estimated_sparse_operations)

    large_bytes = large.to_bytes()
    large_validator = large.validator.report()
    scale_report = {
        "subjects": subject_count,
        "episodes": len(large.episodic.episodes),
        "indexed_relation_slots": large.graph.report()["indexed_relation_slots"],
        "validated_rules": large_validator["validated_rules"],
        "exclusion_guards": large_validator["exclusion_guards"],
        "sample_queries": sample_queries,
        "expected_normal_queries": sample_queries // 2,
        "correct_normal_queries": correct_normal,
        "expected_blocked_queries": sample_queries // 2,
        "correct_blocked_queries": correct_blocked,
        "max_rule_candidates": max_rule_candidates,
        "max_guard_reads": max_guard_reads,
        "max_rule_reads": max_rule_reads,
        "max_edge_reads": max_edge_reads,
        "max_nodes_activated": max_nodes,
        "max_estimated_operations": max_operations,
        "serialized_bytes": len(large_bytes),
        "build_and_query_seconds": time.perf_counter() - scale_start,
        "forward_materialisation_used": False,
        "validation_scan_used_at_inference": False,
        "global_exception_scan_used": False,
    }

    result: dict[str, object] = {
        "capability_id": "SPARC-HS14-COUNTEREXAMPLE-GUIDED-GUARDS",
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
        "compact_model": model.report(),
        "large_counterexample_memory": scale_report,
        "elapsed_seconds": time.perf_counter() - start,
        "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "claim_boundary": (
            "HS14 learns a few local exception guards from source-grounded counterexamples. "
            "It does not revise arbitrary theories, discover hidden causal variables or "
            "perform probabilistic science and is not Japanese high-school-level general intelligence."
        ),
    }
    result["passed"] = bool(
        all(checks.values())
        and scale_report["episodes"] == 100_025
        and scale_report["indexed_relation_slots"] == 100_025
        and scale_report["validated_rules"] == 1
        and scale_report["exclusion_guards"] == 1
        and correct_normal == sample_queries // 2
        and correct_blocked == sample_queries // 2
        and max_rule_candidates <= 1
        and max_guard_reads <= 1
        and max_rule_reads <= 1
        and max_edge_reads <= 2
        and max_nodes <= 4
        and max_operations <= 24
        and len(large_bytes) <= 10_000_000
        and result["peak_process_kib"] <= 1_200_000
        and result["elapsed_seconds"] <= 120.0
    )

    (output_dir / "sparc_hs14_counterexamples.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "SPARC-HS14-compact.model.zlib").write_bytes(compact_bytes)
    (output_dir / "SPARC-HS14-counterexample-large.model.zlib").write_bytes(large_bytes)
    return result


def main() -> None:
    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
