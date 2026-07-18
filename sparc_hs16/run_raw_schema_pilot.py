from __future__ import annotations

import gc
import json
import statistics
import time

from sparc_hs16.raw_schema import (
    BudgetEvaluation,
    RawCausalSchemaModel,
    SurfaceNgramBaseline,
    hidden_examples,
    role_calibration_texts,
    training_examples,
)


def accuracy(model, cases):
    rows = list(cases)
    correct = sum(model.predict(text) == target for text, target in rows)
    return correct / len(rows)


def evaluate_surface_baseline(worlds: int = 1_000) -> float:
    model = SurfaceNgramBaseline(budget_mb=16)
    for text, target in training_examples(worlds):
        model.learn(text, target)
    return accuracy(model, hidden_examples(worlds, start=0, count=worlds))


def evaluate_budget(budget_mb: int, worlds: int = 6_000) -> BudgetEvaluation:
    model = RawCausalSchemaModel(budget_mb=budget_mb)
    model.fit_roles(role_calibration_texts())
    model.fit_context_gates(list(training_examples(256)))

    started = time.perf_counter()
    for text, target in training_examples(worlds):
        model.learn(text, target)
    training_seconds = time.perf_counter() - started

    groups = {
        "early": list(hidden_examples(worlds, start=0)),
        "middle": list(hidden_examples(worlds, start=worlds // 2 - 250)),
        "late": list(hidden_examples(worlds, start=worlds - 500)),
    }
    group_accuracy = {}
    latencies = []
    for name, rows in groups.items():
        correct = 0
        for text, target in rows:
            query_started = time.perf_counter()
            predicted = model.predict(text)
            latencies.append((time.perf_counter() - query_started) * 1_000)
            correct += int(predicted == target)
        group_accuracy[name] = correct / len(rows)

    sorted_latencies = sorted(latencies)
    p95_index = max(0, int(len(sorted_latencies) * 0.95) - 1)
    overall = statistics.mean(group_accuracy.values())
    return BudgetEvaluation(
        budget_mb=budget_mb,
        early_accuracy=group_accuracy["early"],
        middle_accuracy=group_accuracy["middle"],
        late_accuracy=group_accuracy["late"],
        overall_accuracy=overall,
        p95_latency_ms=sorted_latencies[p95_index],
        training_seconds=training_seconds,
        managed_storage_bytes=model.managed_storage_bytes,
        cortical_slots=model.cortical_store.slots,
        cortical_occupied=model.cortical_store.occupied,
        cortical_utilization=(model.cortical_store.occupied / model.cortical_store.slots),
        cortical_replacements=model.cortical_store.replacements,
        candidate_collisions=model.candidate_store.collisions,
        average_features_per_query=model.average_features_per_prediction,
        average_lookup_probes=model.cortical_store.average_probes,
        estimated_active_storage_bytes_per_query=(model.estimated_active_storage_bytes_per_prediction),
        learned_context_gates=len(model.gate.schemas),
        gate_serialized_bytes=model.gate.serialized_bytes(),
    )


def main() -> None:
    baseline_accuracy = evaluate_surface_baseline()
    evaluations = []
    for budget in (16, 64, 256):
        evaluations.append(evaluate_budget(budget).to_dict())
        gc.collect()

    hs18_allocated_cortex_bytes = 201_326_592
    hs18_training_examples = 288 * 3
    hs18_branches_per_example = 25
    hs18_update_events_upper_bound = hs18_training_examples * hs18_branches_per_example
    report = {
        "experiment": "SPARC-HS19 raw causal schema and dual-timescale consolidation",
        "surface_ngram_baseline_accuracy": baseline_accuracy,
        "budget_evaluations": evaluations,
        "hs18_diagnosis": {
            "allocated_cortex_bytes": hs18_allocated_cortex_bytes,
            "training_update_events_upper_bound": hs18_update_events_upper_bound,
            "cortex_utilization_upper_bound": hs18_update_events_upper_bound / hs18_allocated_cortex_bytes,
            "counter_reads_per_query_before_episodic_scan": 75,
            "episodic_scan_bound_at_256mb": 16_384,
        },
        "raw_text_role_induction": True,
        "distributional_paraphrase_clustering": True,
        "conditional_role_gate_induction": True,
        "fast_hippocampal_candidate_memory": True,
        "slow_consistency_filtered_cortical_consolidation": True,
        "same_learning_code_all_budgets": True,
        "task_specific_field_parser": False,
        "transformer_used": False,
        "backpropagation_used": False,
        "actual_weak_smartphone_measurement": False,
        "general_intelligence_discovered": False,
        "university_exam_mastery_passed": False,
        "highschool_level_passed": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
