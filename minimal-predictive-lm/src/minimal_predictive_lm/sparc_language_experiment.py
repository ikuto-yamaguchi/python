from __future__ import annotations

import json
import random
import resource
import statistics
import time
from pathlib import Path

from .sparc_curriculum import heldout_cases, seed_sessions
from .sparc_language import SPARCLanguageModel


def _stress_rows(count: int) -> list[tuple[str, str]]:
    return [
        (
            f"知識項目{i:05d}の識別値を教えて",
            f"知識項目{i:05d}の識別値は値{i * 17 + 3:08d}です。",
        )
        for i in range(count)
    ]


def run_experiment(
    output: str | Path | None = None,
    *,
    stress_items: int = 8000,
) -> dict[str, object]:
    started = time.perf_counter()

    model = SPARCLanguageModel("ci").fit_sessions(seed_sessions())
    heldout: list[dict[str, object]] = []
    for prompt, expected in heldout_cases():
        model.reset()
        reply = model.reply(prompt)
        heldout.append(
            {
                "prompt": prompt,
                "expected": expected,
                "reply": reply.text,
                "correct": reply.text == expected,
                "confidence": reply.confidence,
                "candidates": reply.candidates_inspected,
                "operations": reply.estimated_sparse_operations,
            }
        )

    model.reset()
    running_open = model.reply("ランニングが趣味です")
    running_follow = model.reply("それについてもっと教えて")
    model.reset()
    ai_open = model.reply("AI研究をしています")
    ai_follow = model.reply("それについてもっと教えて")

    model.reset()
    before_teach = model.reply("青い箱の合言葉は？")
    model.learn("青い箱の合言葉は？", "みずいろです。")
    model.reset()
    after_teach = model.reply("青い箱の合言葉は？")
    compact_artifact = model.to_bytes()
    restored = SPARCLanguageModel.from_bytes(compact_artifact)
    persisted = restored.reply("青い箱の合言葉は？")
    restored.reset()
    unknown = restored.reply("未解決の量子重力理論を完全に証明して")

    stress_started = time.perf_counter()
    stress = SPARCLanguageModel("desktop-large").fit(_stress_rows(stress_items))
    stress_fit_seconds = time.perf_counter() - stress_started
    rng = random.Random(20260716)
    sample = rng.sample(range(stress_items), min(512, stress_items))
    stress_correct = 0
    candidate_counts: list[int] = []
    posting_reads: list[int] = []
    operation_counts: list[int] = []
    for index in sample:
        stress.reset()
        reply = stress.reply(f"知識項目{index:05d}の識別値を教えて")
        expected = f"知識項目{index:05d}の識別値は値{index * 17 + 3:08d}です。"
        stress_correct += int(reply.text == expected)
        candidate_counts.append(reply.candidates_inspected)
        posting_reads.append(stress.last_posting_reads)
        operation_counts.append(reply.estimated_sparse_operations)
    stress_artifact = stress.to_bytes()

    heldout_correct = sum(int(row["correct"]) for row in heldout)
    stress_report = stress.report()
    checks = {
        "heldout_paraphrase_accuracy": heldout_correct / len(heldout) >= 0.90,
        "contextual_running_followup": (
            running_open.text == "ランニングが好きなんですね。"
            and running_follow.text == "ランニングでは距離、強度、休養のバランスが大切です。"
        ),
        "contextual_ai_followup": (
            ai_open.text == "AI研究に取り組んでいるんですね。"
            and ai_follow.text == "AI研究では仮説、実装、反証可能な評価を分けて進めることが大切です。"
        ),
        "online_learning": "まだ十分" in before_teach.text and after_teach.text == "みずいろです。",
        "artifact_persistence": persisted.text == "みずいろです。",
        "calibrated_unknown": "まだ十分" in unknown.text,
        "large_sparse_recall": stress_correct == len(sample),
        "bounded_candidate_activation": max(candidate_counts, default=0) <= 4,
        "bounded_posting_reads": max(posting_reads, default=0) <= stress.profile.routing_bits * 2,
        "no_full_history_attention": not bool(stress_report["full_history_attention_used"]),
        "no_growing_kv_cache": not bool(stress_report["growing_kv_cache_used"]),
    }

    result: dict[str, object] = {
        "capability_id": "SPARC-HS1-LANGUAGE",
        "target": "large-capacity low-activation Japanese conversational intelligence",
        "claim_boundary": (
            "HS1 learns a variable-length Japanese chunk compiler and sparse response assemblies from dialogue examples. "
            "It supports held-out paraphrases, bounded multi-turn context, online learning and a real desktop-large stress model. "
            "It is conversational but is not yet Japanese high-school-level general intelligence; broad world knowledge, "
            "compositional generation, autonomous program induction and sustained reasoning remain future gates."
        ),
        "architecture": {
            "brain_inspired_principles": [
                "sparse distributed assemblies",
                "homeostatic inhibition of over-common routing columns",
                "bounded active workspace",
                "local Hebbian response and transition updates",
                "capacity separated from active computation",
                "explicit unknown response when activation is weak",
            ],
            "transformer_used": False,
            "softmax_attention_used": False,
            "growing_kv_cache_used": False,
            "dense_vocabulary_projection_used": False,
        },
        "conversation": {
            "heldout_correct": heldout_correct,
            "heldout_total": len(heldout),
            "heldout_accuracy": heldout_correct / len(heldout),
            "cases": heldout,
            "context_running": [running_open.text, running_follow.text],
            "context_ai": [ai_open.text, ai_follow.text],
            "before_online_teach": before_teach.text,
            "after_online_teach": after_teach.text,
            "persisted_reply": persisted.text,
            "unknown_reply": unknown.text,
            "compact_model": model.report(),
            "compact_artifact_bytes": len(compact_artifact),
        },
        "desktop_large": {
            "stress_items": stress_items,
            "sampled_queries": len(sample),
            "correct": stress_correct,
            "accuracy": stress_correct / len(sample),
            "fit_seconds": stress_fit_seconds,
            "artifact_bytes": len(stress_artifact),
            "mean_candidates": statistics.fmean(candidate_counts),
            "max_candidates": max(candidate_counts),
            "mean_posting_reads": statistics.fmean(posting_reads),
            "max_posting_reads": max(posting_reads),
            "mean_estimated_sparse_operations": statistics.fmean(operation_counts),
            "max_estimated_sparse_operations": max(operation_counts),
            "report": stress_report,
        },
        "checks": checks,
        "passed_checks": sum(checks.values()),
        "total_checks": len(checks),
        "elapsed_seconds": time.perf_counter() - started,
        "peak_process_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    result["passed"] = all(checks.values())

    if output is not None:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        path.with_suffix(".model.zlib").write_bytes(compact_artifact)
        path.with_name(path.stem + ".desktop-large.model.zlib").write_bytes(stress_artifact)
    return result


def main() -> None:
    result = run_experiment("results/sparc_hs1_language.json")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
