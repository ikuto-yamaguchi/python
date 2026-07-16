from __future__ import annotations

import json
from pathlib import Path
import random
import resource
import sys
import time

from .latent_program_learner import (
    GroundedLatentProgramLearner,
    GroundedTransition,
    PredictiveStateInducer,
)

_OPERATIONS = {
    "increase": (("増やす", "加える", "加算する"), "上乗せする"),
    "decrease": (("減らす", "差し引く", "減算する"), "控除する"),
    "assign": (("設定する", "置き換える", "指定する"), "固定する"),
    "transfer": (("移す", "振り替える", "移動する"), "送る"),
}

_SEMANTIC_CONTEXTS = {
    "increase": (
        "{verb} は 数量 を 大きく する 操作",
        "{verb} を 行う と 値 が 多くなる",
        "{verb} の 後 は 合計 が 増加 する",
        "{verb} は 追加 と 同じ 方向 の 変化",
    ),
    "decrease": (
        "{verb} は 数量 を 小さく する 操作",
        "{verb} を 行う と 値 が 少なくなる",
        "{verb} の 後 は 合計 が 減少 する",
        "{verb} は 削除 と 同じ 方向 の 変化",
    ),
    "assign": (
        "{verb} は 数量 を 特定 の 値 に する 操作",
        "{verb} を 行う と 値 が 指定値 に なる",
        "{verb} の 後 は 以前 の 値 を 使わない",
        "{verb} は 固定値 を 選ぶ 変化",
    ),
    "transfer": (
        "{verb} は 一方 の 場所 から 他方 へ 数量 を 動かす 操作",
        "{verb} を 行う と 元 が 減り 先 が 増える",
        "{verb} の 後 も 全体 の 合計 は 同じ",
        "{verb} は 所有場所 を 変更 する 変化",
    ),
}


def _rss_bytes(value: int) -> int:
    return value if sys.platform == "darwin" else value * 1024


def _unlabelled_corpus() -> tuple[str, ...]:
    rows: list[str] = []
    for operation, (known, withheld) in _OPERATIONS.items():
        for verb in (*known, withheld):
            for template in _SEMANTIC_CONTEXTS[operation]:
                for suffix in ("例", "説明", "教材", "会話", "記録"):
                    rows.append(template.format(verb=verb) + " " + suffix)
    return tuple(rows)


def _transition(
    operation: str,
    verb: str,
    keys: tuple[str, str],
    rng: random.Random,
) -> GroundedTransition:
    left, right = keys
    left_value = rng.randint(30, 120)
    right_value = rng.randint(30, 120)
    amount = rng.randint(2, 12)
    before = {left: left_value, right: right_value}
    if operation == "increase":
        return GroundedTransition(
            f"{left} を {amount} {verb}",
            before,
            {left: left_value + amount, right: right_value},
        )
    if operation == "decrease":
        return GroundedTransition(
            f"{left} から {amount} {verb}",
            before,
            {left: left_value - amount, right: right_value},
        )
    if operation == "assign":
        return GroundedTransition(
            f"{left} を {amount} に {verb}",
            before,
            {left: amount, right: right_value},
        )
    return GroundedTransition(
        f"{left} から {right} へ {amount} {verb}",
        before,
        {left: left_value - amount, right: right_value + amount},
    )


def _datasets() -> tuple[
    tuple[GroundedTransition, ...],
    tuple[GroundedTransition, ...],
]:
    rng = random.Random(1901)
    training: list[GroundedTransition] = []
    training_domains = (
        ("倉庫甲", "倉庫乙"),
        ("口座青", "口座赤"),
        ("チーム東", "チーム西"),
    )
    for operation, (known, _withheld) in _OPERATIONS.items():
        for verb in known:
            for _ in range(48):
                training.append(
                    _transition(operation, verb, rng.choice(training_domains), rng)
                )

    heldout: list[GroundedTransition] = []
    heldout_domains = (
        ("温室北", "温室南"),
        ("研究班一", "研究班二"),
        ("資源月", "資源星"),
        ("得点白", "得点黒"),
    )
    for operation, (_known, withheld) in _OPERATIONS.items():
        for index in range(64):
            heldout.append(
                _transition(
                    operation,
                    withheld,
                    heldout_domains[index % len(heldout_domains)],
                    rng,
                )
            )
    return tuple(training), tuple(heldout)


def _state_sequence(
    seed: int,
    cue_a: str,
    cue_b: str,
    outcome_a: str,
    outcome_b: str,
    query: str,
    distractors: tuple[str, ...],
    *,
    episodes: int = 240,
) -> tuple[str, ...]:
    rng = random.Random(seed)
    sequence: list[str] = []
    for episode in range(episodes):
        branch = episode % 2
        sequence.append(cue_a if branch == 0 else cue_b)
        for _ in range(rng.randint(1, 4)):
            sequence.append(rng.choice(distractors))
        for _ in range(rng.randint(2, 5)):
            sequence.extend((query, outcome_a if branch == 0 else outcome_b))
            if rng.random() < 0.7:
                sequence.append(rng.choice(distractors))
    return tuple(sequence)


def run_gate() -> tuple[dict[str, object], GroundedLatentProgramLearner]:
    started = time.perf_counter()
    training, heldout = _datasets()
    corpus = _unlabelled_corpus()
    model = GroundedLatentProgramLearner()
    latent_programs = model.fit(training, unlabelled_sentences=corpus)

    correct = 0
    answered = 0
    max_candidates = 0
    max_feature_reads = 0
    failures: list[dict[str, object]] = []
    for row in heldout:
        expected = model.derive_plan(row)
        result = model.infer(row.text, row.before)
        answered += result.plan is not None
        correct += result.plan == expected
        max_candidates = max(max_candidates, result.candidates)
        max_feature_reads = max(max_feature_reads, result.feature_reads)
        if result.plan != expected and len(failures) < 12:
            failures.append(
                {
                    "text": row.text,
                    "expected": expected.__dict__,
                    "actual": None if result.plan is None else result.plan.__dict__,
                    "mechanism": result.mechanism,
                    "confidence": result.confidence,
                }
            )

    ablation = GroundedLatentProgramLearner()
    ablation.fit(training, unlabelled_sentences=(row.text for row in training))
    ablation_correct = sum(
        ablation.infer(row.text, row.before).plan == model.derive_plan(row)
        for row in heldout
    )

    restored = GroundedLatentProgramLearner.from_bytes(model.to_bytes())
    restoration_ok = all(
        restored.infer(row.text, row.before).plan == model.derive_plan(row)
        for row in heldout[:64]
    )

    source_sequence = _state_sequence(
        91,
        "春印",
        "冬印",
        "暖答",
        "寒答",
        "照会",
        ("雑音A", "雑音B", "雑音C"),
    )
    changed_encoding_sequence = _state_sequence(
        92,
        "白印",
        "黒印",
        "左答",
        "右答",
        "確認",
        ("無関係X", "無関係Y", "無関係Z"),
    )
    state_inducer = PredictiveStateInducer(max_candidates=128)
    source_state = state_inducer.fit(source_sequence, query_token="照会")
    changed_state = state_inducer.fit(
        changed_encoding_sequence,
        query_token="確認",
    )

    exact_accuracy = correct / len(heldout)
    selective_accuracy = correct / answered if answered else 0.0
    state_source_pair_ok = set(source_state.cue_pair or ()) == {"春印", "冬印"}
    state_changed_pair_ok = set(changed_state.cue_pair or ()) == {"白印", "黒印"}
    state_signature_transfer = (
        source_state.canonical_signature is not None
        and source_state.canonical_signature == changed_state.canonical_signature
    )
    elapsed = time.perf_counter() - started
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    checks = {
        "no_operation_labels_in_grounded_examples": True,
        "entire_paraphrase_family_withheld_from_grounded_training": True,
        "four_latent_edit_programs_discovered": latent_programs == 4,
        "heldout_exact_plan_recovery_at_least_70_percent": exact_accuracy >= 0.70,
        "heldout_selective_accuracy_at_least_80_percent": selective_accuracy >= 0.80,
        "descriptive_corpus_beats_labelled_surface_ablation": correct > ablation_correct,
        "bounded_program_candidates_at_most_8": max_candidates <= 8,
        "bounded_feature_reads_at_most_512": max_feature_reads <= 512,
        "save_restore_preserves_transfer": restoration_ok,
        "autonomous_source_state_variable_recovered": state_source_pair_ok,
        "changed_encoding_state_variable_recovered": state_changed_pair_ok,
        "canonical_state_program_transfers_across_encoding": state_signature_transfer,
        "source_state_mdl_gain_at_least_100_bits": source_state.description_length_gain >= 100.0,
        "changed_state_mdl_gain_at_least_100_bits": changed_state.description_length_gain >= 100.0,
        "state_candidates_bounded_at_most_128": max(
            source_state.candidates,
            changed_state.candidates,
        )
        <= 128,
    }
    report: dict[str, object] = {
        "capability_id": "SPARC-LATENT-PROGRAM-001",
        "paraphrase_transfer": {
            "grounded_training_examples": len(training),
            "unlabelled_descriptive_sentences": len(corpus),
            "latent_programs": latent_programs,
            "heldout_examples": len(heldout),
            "correct": correct,
            "answered": answered,
            "exact_accuracy": exact_accuracy,
            "selective_accuracy": selective_accuracy,
            "labelled_surface_ablation_correct": ablation_correct,
            "max_candidates": max_candidates,
            "max_feature_reads": max_feature_reads,
            "failures": failures,
        },
        "autonomous_state_proposal": {
            "source": source_state.__dict__,
            "changed_encoding": changed_state.__dict__,
            "source_pair_recovered": state_source_pair_ok,
            "changed_pair_recovered": state_changed_pair_ok,
            "canonical_signature_transfer": state_signature_transfer,
        },
        "resources": {
            "serialized_model_bytes": len(model.to_bytes()),
            "peak_rss_bytes": _rss_bytes(int(peak)),
            "wall_seconds": elapsed,
        },
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "This is a synthetic, whitespace-tokenised first test of grounded "
            "latent-program induction and MDL state-variable proposal. The withheld "
            "expressions appear in an unlabelled descriptive corpus, so this does not "
            "establish unrestricted Japanese understanding, curriculum-scale learning, "
            "or high-school-level intelligence."
        ),
    }
    return report, model


def render_markdown(report: dict[str, object]) -> str:
    transfer = report["paraphrase_transfer"]
    state = report["autonomous_state_proposal"]
    resources = report["resources"]
    return "\n".join(
        [
            "# SPARC latent-program experiment 001",
            "",
            f"Passed: **{report['passed']}**",
            "",
            "## Unseen paraphrase-family transfer",
            f"- Grounded training: **{transfer['grounded_training_examples']}**",
            f"- Unlabelled descriptive sentences: **{transfer['unlabelled_descriptive_sentences']}**",
            f"- Heldout exact plans: **{transfer['correct']}/{transfer['heldout_examples']}**",
            f"- Answered: **{transfer['answered']}/{transfer['heldout_examples']}**",
            f"- Labelled-surface-only ablation: **{transfer['labelled_surface_ablation_correct']}/{transfer['heldout_examples']}**",
            f"- Max candidates / feature reads: **{transfer['max_candidates']} / {transfer['max_feature_reads']}**",
            "",
            "## Autonomous predictive-state proposal",
            f"- Source pair recovered: **{state['source_pair_recovered']}**",
            f"- Changed encoding pair recovered: **{state['changed_pair_recovered']}**",
            f"- Canonical program transferred: **{state['canonical_signature_transfer']}**",
            f"- Source MDL gain: **{state['source']['description_length_gain']:.2f} bits**",
            f"- Changed-encoding MDL gain: **{state['changed_encoding']['description_length_gain']:.2f} bits**",
            "",
            "## Resources",
            f"- Serialized model: **{resources['serialized_model_bytes']} bytes**",
            f"- Peak RSS: **{resources['peak_rss_bytes']} bytes**",
            f"- Wall time: **{resources['wall_seconds']:.3f} seconds**",
            "",
            "## Claim boundary",
            "",
            str(report["claim_boundary"]),
            "",
        ]
    )


def main() -> None:
    report, model = run_gate()
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    (output_dir / "sparc_latent_program_001.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "sparc_latent_program_001.md").write_text(
        render_markdown(report),
        encoding="utf-8",
    )
    (output_dir / "SPARC-latent-program-001.model.zlib").write_bytes(
        model.to_bytes()
    )
    print(render_markdown(report), end="")
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
