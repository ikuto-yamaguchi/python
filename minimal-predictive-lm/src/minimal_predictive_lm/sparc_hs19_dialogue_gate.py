from __future__ import annotations

import json
from pathlib import Path
import resource
import sys
import time

from .sparc_dialogue_composer import DialoguePlan, SparseDialogueComposer
from .sparc_hs19_dialogue_experiment import (
    _contains_all_slots,
    _heldout_plans,
    _training_rows,
)


def _rss_bytes(value: int) -> int:
    return value if sys.platform == "darwin" else value * 1024


def run_gate() -> tuple[dict[str, object], SparseDialogueComposer]:
    started = time.perf_counter()
    model = SparseDialogueComposer(max_templates=128, max_candidates=16, focus_turns=32)
    demonstrations = _training_rows()
    learned_templates = model.fit(demonstrations)

    heldout = _heldout_plans()
    correct = 0
    learned_outputs = 0
    max_candidates = 0
    max_feature_reads = 0
    failures: list[dict[str, object]] = []
    for plan in heldout:
        result = model.compose(plan)
        learned_outputs += result.mechanism == "learned-slot-template"
        max_candidates = max(max_candidates, result.candidates)
        max_feature_reads = max(max_feature_reads, result.feature_reads)
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

    report = model.report()
    elapsed = time.perf_counter() - started
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    checks = {
        "ten_thousand_training_demonstrations": len(demonstrations) == 10_000,
        "compressed_to_at_most_eight_templates": learned_templates <= 8,
        "heldout_composition_512_of_512": correct == len(heldout) == 512,
        "learned_template_outputs_512_of_512": learned_outputs == 512,
        "max_candidates_at_most_16": max_candidates <= 16,
        "max_feature_reads_at_most_256": max_feature_reads <= 256,
        "bounded_thirty_turn_followup": followup_ok,
        "save_restore_preserves_focus": restoration_ok,
        "serialized_model_at_most_128k": int(report["serialized_bytes"]) <= 128 * 1024,
        "complete_response_selection_not_used": report["complete_response_selection_used"] is False,
        "full_history_scan_not_used": report["full_history_scan_used"] is False,
    }
    result: dict[str, object] = {
        "capability_id": "SPARC-HS19-COMPOSITIONAL-JAPANESE-DIALOGUE-SURFACE",
        "training_demonstrations": len(demonstrations),
        "learned_templates": learned_templates,
        "heldout": {
            "examples": len(heldout),
            "correct": correct,
            "learned_template_outputs": learned_outputs,
            "max_candidates": max_candidates,
            "max_feature_reads": max_feature_reads,
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
            "HS19 learns reusable Japanese response surfaces over explicit semantic slots. "
            "It does not yet infer every slot from unrestricted conversation, so it is "
            "not yet a Japanese high-school-level conversational intelligence."
        ),
    }
    return result, model


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
            f"- Heldout compositions: **{heldout['correct']}/{heldout['examples']}**",
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
    result, model = run_gate()
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
    (output_dir / "SPARC-HS19-dialogue.model.zlib").write_bytes(model.to_bytes())
    print(render_markdown(result), end="")
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
