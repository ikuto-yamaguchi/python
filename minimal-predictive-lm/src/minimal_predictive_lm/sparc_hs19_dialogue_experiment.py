from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import resource
import sys
import time

from .sparc_dialogue_composer import (
    DialogueDemonstration,
    DialoguePlan,
    SparseDialogueComposer,
)


def _rss_bytes(value: int) -> int:
    return value if sys.platform == "darwin" else value * 1024


def _training_rows(count: int = 10_000) -> tuple[DialogueDemonstration, ...]:
    rows: list[DialogueDemonstration] = []
    for index in range(count):
        family = index % 4
        if family == 0:
            plan = DialoguePlan(
                "explain",
                subject=f"学習主題{index}",
                answer=f"学習回答{index}",
                evidence=f"学習根拠{index}",
                caveat=f"学習留保{index}",
                source=f"学習資料{index}",
            )
            response = (
                f"{plan.subject}については、{plan.answer}。"
                f"理由は{plan.evidence}です。"
                f"ただし、{plan.caveat}。"
                f"出典は{plan.source}です。"
            )
        elif family == 1:
            plan = DialoguePlan(
                "correction",
                subject=f"訂正主題{index}",
                old_value=f"旧値{index}",
                new_value=f"新値{index}",
                evidence=f"訂正根拠{index}",
            )
            response = (
                f"{plan.subject}は、{plan.old_value}ではなく{plan.new_value}です。"
                f"根拠は{plan.evidence}です。"
            )
        elif family == 2:
            plan = DialoguePlan(
                "answer",
                subject=f"回答主題{index}",
                answer=f"結論{index}",
                evidence=f"証拠{index}",
                source=f"出典{index}",
            )
            response = (
                f"{plan.subject}への答えは{plan.answer}です。"
                f"根拠は{plan.evidence}で、出典は{plan.source}です。"
            )
        else:
            plan = DialoguePlan(
                "compare",
                subject=f"比較主題{index}",
                answer=f"比較結論{index}",
                evidence=f"比較根拠{index}",
                caveat=f"比較留保{index}",
            )
            response = (
                f"{plan.subject}を比べると、{plan.answer}。"
                f"根拠は{plan.evidence}です。"
                f"ただし、{plan.caveat}。"
            )
        rows.append(DialogueDemonstration(plan, response))
    return tuple(rows)


def _heldout_plans(count: int = 512) -> tuple[DialoguePlan, ...]:
    rows: list[DialoguePlan] = []
    for index in range(count):
        family = index % 4
        token = 100_000 + index
        if family == 0:
            rows.append(
                DialoguePlan(
                    "explain",
                    subject=f"未見主題{token}",
                    answer=f"未見回答{token}",
                    evidence=f"未見根拠{token}",
                    caveat=f"未見留保{token}",
                    source=f"未見資料{token}",
                )
            )
        elif family == 1:
            rows.append(
                DialoguePlan(
                    "correction",
                    subject=f"未見訂正主題{token}",
                    old_value=f"未見旧値{token}",
                    new_value=f"未見新値{token}",
                    evidence=f"未見訂正根拠{token}",
                )
            )
        elif family == 2:
            rows.append(
                DialoguePlan(
                    "answer",
                    subject=f"未見回答主題{token}",
                    answer=f"未見結論{token}",
                    evidence=f"未見証拠{token}",
                    source=f"未見出典{token}",
                )
            )
        else:
            rows.append(
                DialoguePlan(
                    "compare",
                    subject=f"未見比較主題{token}",
                    answer=f"未見比較結論{token}",
                    evidence=f"未見比較根拠{token}",
                    caveat=f"未見比較留保{token}",
                )
            )
    return tuple(rows)


def _contains_all_slots(text: str, plan: DialoguePlan) -> bool:
    return all(value in text for value in plan.slots().values())


def run_experiment() -> dict[str, object]:
    started = time.perf_counter()
    model = SparseDialogueComposer(max_templates=128, max_candidates=16, focus_turns=32)
    demonstrations = _training_rows()
    learned_templates = model.fit(demonstrations)

    heldout = _heldout_plans()
    correct = 0
    learned = 0
    max_candidates = 0
    max_reads = 0
    failures: list[dict[str, object]] = []
    for plan in heldout:
        result = model.compose(plan)
        if result.mechanism == "learned-slot-template":
            learned += 1
        max_candidates = max(max_candidates, result.candidates)
        max_reads = max(max_reads, result.feature_reads)
        if _contains_all_slots(result.text, plan):
            correct += 1
        elif len(failures) < 16:
            failures.append(
                {
                    "intent": plan.intent,
                    "expected_slots": plan.slots(),
                    "actual": result.text,
                    "mechanism": result.mechanism,
                }
            )

    for index in range(30):
        model.compose(
            DialoguePlan(
                "explain",
                subject=f"焦点主題{index}",
                answer=f"焦点回答{index}",
                evidence=f"焦点根拠{index}",
                caveat=f"焦点留保{index}",
                source=f"焦点資料{index}",
            )
        )
    followup = model.compose(
        DialoguePlan(
            "explain",
            answer="追加回答",
            evidence="固定長焦点を参照したため",
            caveat="履歴全体は走査していません",
            source="焦点ワークスペース",
        ),
        user_text="それについてさらに詳しく",
    )
    followup_ok = "焦点主題29" in followup.text and "焦点主題0" not in followup.text

    restored = SparseDialogueComposer.from_bytes(model.to_bytes())
    restored_followup = restored.compose(
        DialoguePlan(
            "explain",
            answer="復元後回答",
            evidence="保存された焦点を参照したため",
            caveat="全履歴は保存していません",
            source="復元ワークスペース",
        ),
        user_text="それについて詳しく",
    )
    restoration_ok = "焦点主題29" in restored_followup.text

    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    elapsed = time.perf_counter() - started
    report = model.report()
    checks = {
        "ten_thousand_training_demonstrations": len(demonstrations) == 10_000,
        "compressed_to_at_most_eight_templates": learned_templates <= 8,
        "heldout_composition_512_of_512": correct == len(heldout) == 512,
        "heldout_uses_learned_templates_512_of_512": learned == 512,
        "max_candidates_at_most_16": max_candidates <= 16,
        "max_feature_reads_at_most_256": max_reads <= 256,
        "bounded_thirty_turn_followup": followup_ok,
        "save_restore_preserves_focus": restoration_ok,
        "complete_response_selection_not_used": report["complete_response_selection_used"] is False,
        "full_history_scan_not_used": report["full_history_scan_used"] is False,
        "serialized_model_at_most_128k": report["serialized_bytes"] <= 128 * 1024,
    }
    return {
        "capability_id": "SPARC-HS19-COMPOSITIONAL-JAPANESE-DIALOGUE-SURFACE",
        "training_demonstrations": len(demonstrations),
        "learned_templates": learned_templates,
        "heldout": {
            "examples": len(heldout),
            "correct": correct,
            "learned_template_outputs": learned,
            "max_candidates": max_candidates,
            "max_feature_reads": max_reads,
            "failures": failures,
        },
        "followup": {
            "passed": followup_ok,
            "text": followup.text,
            "focus_items": len(model.focus),
            "focus_capacity": model.focus.maxlen,
        },
        "restoration": {
            "passed": restoration_ok,
            "text": restored_followup.text,
        },
        "resources": {
            "serialized_bytes": report["serialized_bytes"],
            "peak_rss_bytes": _rss_bytes(int(peak)),
            "wall_seconds": elapsed,
        },
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "HS19 composes Japanese response surfaces from explicit semantic slots. "
            "It does not yet infer all slots from unrestricted Japanese dialogue, and "
            "therefore is not a high-school-level conversational intelligence claim."
        ),
    }


def render_markdown(result: dict[str, object]) -> str:
    heldout = result["heldout"]
    resources = result["resources"]
    return "\n".join(
        [
            "# SPARC-HS19: compositional Japanese dialogue surface",
            "",
            f"Passed: **{result['passed']}**",
            f"- Training demonstrations: **{result['training_demonstrations']}**",
            f"- Learned templates: **{result['learned_templates']}**",
            f"- Heldout slot compositions: **{heldout['correct']}/{heldout['examples']}**",
            f"- Learned-template outputs: **{heldout['learned_template_outputs']}/{heldout['examples']}**",
            f"- Max candidates / reads: **{heldout['max_candidates']} / {heldout['max_feature_reads']}**",
            f"- Model bytes: **{resources['serialized_bytes']}**",
            f"- Wall seconds: **{resources['wall_seconds']:.2f}**",
            "",
            "## Claim boundary",
            "",
            str(result["claim_boundary"]),
            "",
        ]
    )


def main() -> None:
    result = run_experiment()
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    (output_dir / "sparc_hs19_dialogue.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "sparc_hs19_dialogue.md").write_text(
        render_markdown(result),
        encoding="utf-8",
    )
    (output_dir / "SPARC-HS19-dialogue.model.zlib").write_bytes(
        SparseDialogueComposer.from_bytes(
            SparseDialogueComposer().to_bytes()
        ).to_bytes()
    )
    print(render_markdown(result), end="")
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
