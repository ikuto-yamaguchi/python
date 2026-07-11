from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .raw_event_program import (
    EffectTrace,
    OPERATIONS,
    execute_transform_workflow,
    exact_surface_accuracy,
    grounding_accuracy,
    induce_raw_grounder,
    infer_operation,
)


def _trace(source: str, raw: str, operation: str) -> EffectTrace:
    before = (("value", "old"),)
    if operation == "SET":
        return EffectTrace(source, raw, before, (("value", "new"),))
    if operation == "VERIFY":
        return EffectTrace(source, raw, before, before, observed=True)
    if operation == "RETRACT":
        return EffectTrace(source, raw, (("value", "new"),), before, restored=True)
    if operation == "EMIT":
        return EffectTrace(source, raw, before, before, emitted=True)
    raise ValueError(operation)


def _traces(specification: dict[str, list[tuple[str, str]]]) -> list[EffectTrace]:
    return [
        _trace(source, raw, operation)
        for operation, examples in specification.items()
        for source, raw in examples
    ]


TRAINING_SPECIFICATION = {
    "SET": [
        ("text", "transform関数を修正してください"),
        ("text", "計算処理を修正する"),
        ("writing", "段落の結論を追加する"),
        ("writing", "文章に主張を追加してください"),
        ("ast", "Returnノードを書き換える"),
        ("ast", "ASTのReturnを書き換える"),
        ("tool", "apply_patchでファイルを更新する"),
        ("tool", "update_fileで内容を更新する"),
    ],
    "VERIFY": [
        ("text", "テストを実行してください"),
        ("text", "テスト結果を確認する"),
        ("writing", "根拠を検証する"),
        ("writing", "引用元を検証してください"),
        ("ast", "pytestを呼び出す"),
        ("ast", "pytest Callを作る"),
        ("tool", "コマンド結果を照合する"),
        ("tool", "実行結果を照合してください"),
        ("tool", "FAILED test_transform expected=5 got=3"),
        ("tool", "PASSED test_transform"),
    ],
    "RETRACT": [
        ("text", "変更を元に戻す"),
        ("text", "修正前の状態に戻してください"),
        ("writing", "追加した文を取り消す"),
        ("writing", "未確認の段落を取り消してください"),
        ("ast", "Restoreノードで変更を復元する"),
        ("ast", "AST Restoreで元を復元する"),
        ("tool", "git restoreでファイルを戻す"),
        ("tool", "restoreコマンドで操作を戻す"),
    ],
    "EMIT": [
        ("text", "作業結果を報告してください"),
        ("text", "変更内容を報告する"),
        ("writing", "完成した文章を出力する"),
        ("writing", "最終稿を出力してください"),
        ("ast", "diff summaryを生成する"),
        ("ast", "patch summaryを生成してください"),
        ("tool", "結果メッセージを送信する"),
        ("tool", "summaryを送信してください"),
    ],
}


NEAR_HELDOUT_SPECIFICATION = {
    "SET": [
        ("text", "transform関数を修正して"),
        ("writing", "結論を追加して"),
        ("ast", "Returnを書き換えて"),
        ("tool", "update_fileで設定を更新して"),
    ],
    "VERIFY": [
        ("text", "テストをもう一度実行して"),
        ("writing", "引用の根拠を検証して"),
        ("ast", "pytest Callを追加して"),
        ("tool", "結果を照合して"),
        ("tool", "FAILED test_transform expected=10 got=4"),
        ("tool", "PASSED 2 tests"),
    ],
    "RETRACT": [
        ("text", "変更前に戻して"),
        ("writing", "追加した段落を取り消して"),
        ("ast", "Restoreで元を復元して"),
        ("tool", "git restoreで戻して"),
    ],
    "EMIT": [
        ("text", "作業内容を報告して"),
        ("writing", "最終文章を出力して"),
        ("ast", "patch summaryを生成して"),
        ("tool", "結果を送信して"),
    ],
}


DISTANT_SPECIFICATION = {
    "SET": [
        ("text", "transformのバグを直して"),
        ("writing", "結末を付け足して"),
        ("ast", "ReplaceNode old=Return new=Expr"),
        ("tool", "put_file content=data"),
    ],
    "VERIFY": [
        ("text", "試験を走らせて"),
        ("writing", "出典が正しいか調べて"),
        ("ast", "run_checks()"),
        ("tool", "compare_result"),
    ],
    "RETRACT": [
        ("text", "変更前へ巻き戻して"),
        ("writing", "その一文を消して"),
        ("ast", "UndoPatch()"),
        ("tool", "revert_file"),
    ],
    "EMIT": [
        ("text", "作業結果を知らせて"),
        ("writing", "原稿を公開して"),
        ("ast", "PrintChangeLog()"),
        ("tool", "reply_message"),
    ],
}


CALIBRATION_SPECIFICATION = {
    "SET": [
        ("text", "実装を直してください"),
        ("writing", "結末を直して"),
    ],
    "VERIFY": [
        ("text", "試験を走らせて"),
        ("tool", "試験を開始する"),
    ],
    "RETRACT": [
        ("text", "変更前へ巻き戻して"),
        ("tool", "履歴を巻き戻す"),
    ],
    "EMIT": [
        ("text", "作業結果を知らせて"),
        ("tool", "完了を知らせる"),
    ],
}


FOLLOWUP_SPECIFICATION = {
    "SET": [
        ("text", "処理を直して"),
        ("writing", "末尾を直してください"),
    ],
    "VERIFY": [
        ("text", "試験を実施して"),
        ("tool", "試験結果を取得する"),
    ],
    "RETRACT": [
        ("text", "状態を巻き戻して"),
        ("tool", "一つ前へ巻き戻す"),
    ],
    "EMIT": [
        ("text", "進捗を知らせて"),
        ("tool", "終了を知らせる"),
    ],
}


def _accuracy_by_source(
    training: list[EffectTrace],
    validation: list[EffectTrace],
) -> dict[str, object]:
    sources = sorted({trace.source for trace in training})
    models = {
        source: induce_raw_grounder(
            [trace for trace in training if trace.source == source]
        )
        for source in sources
    }
    correct = 0
    for trace in validation:
        model = models[trace.source]
        correct += int(
            model.predict(trace.raw).operation == infer_operation(trace)
        )
    return {
        "sources": sources,
        "models": len(models),
        "description_bits": sum(model.description_bits for model in models.values()),
        "accuracy": correct / len(validation),
        "errors": len(validation) - correct,
    }


def _rule_payload(grounder: object) -> list[dict[str, object]]:
    return [
        {
            "operation": rule.operation,
            "feature": rule.feature,
            "support": rule.support,
        }
        for rule in grounder.rules
    ]


def run() -> dict[str, object]:
    training = _traces(TRAINING_SPECIFICATION)
    near_heldout = _traces(NEAR_HELDOUT_SPECIFICATION)
    distant = _traces(DISTANT_SPECIFICATION)
    calibration = _traces(CALIBRATION_SPECIFICATION)
    followup = _traces(FOLLOWUP_SPECIFICATION)

    shared = induce_raw_grounder(training)
    separated = _accuracy_by_source(training, near_heldout)

    exact_near = exact_surface_accuracy(training, near_heldout)
    shared_near = grounding_accuracy(shared, near_heldout)
    distant_accuracy = grounding_accuracy(shared, distant)

    calibrated = induce_raw_grounder(training + calibration)
    followup_before = grounding_accuracy(shared, followup)
    followup_after = grounding_accuracy(calibrated, followup)
    added_description_bits = (
        calibrated.description_bits - shared.description_bits
    )

    request = (
        "transform関数を修正して。"
        "テストを実行して。"
        "失敗した場合は変更を元に戻して。"
        "別の修正を追加して。"
        "もう一度テストを実行して。"
        "最後に結果を報告して。"
    )
    workflow = execute_transform_workflow(request, shared)

    return {
        "training": {
            "examples": len(training),
            "operations": len(OPERATIONS),
            "selected_rules": len(shared.rules),
            "description_bits": shared.description_bits,
            "rules": _rule_payload(shared),
        },
        "raw_grounding": {
            "near_examples": len(near_heldout),
            "exact_surface_accuracy": exact_near,
            "shared_grounder_accuracy": shared_near,
            "distant_examples": len(distant),
            "distant_lexical_shift_accuracy": distant_accuracy,
        },
        "domain_separated": separated,
        "shared_vs_separated": {
            "shared_description_bits": shared.description_bits,
            "separated_description_bits": separated["description_bits"],
            "description_ratio": (
                separated["description_bits"] / shared.description_bits
            ),
            "shared_near_accuracy": shared_near,
            "separated_near_accuracy": separated["accuracy"],
        },
        "residual_calibration": {
            "calibration_examples": len(calibration),
            "followup_examples": len(followup),
            "accuracy_before": followup_before,
            "accuracy_after": followup_after,
            "added_description_bits": added_description_bits,
            "retention_gate": (
                "retain only when future avoided grounding loss and handoff "
                "cost exceed the added program bits"
            ),
        },
        "workflow": {
            "plan": list(workflow.plan),
            "events": [
                {
                    "operation": event.operation,
                    "request": event.request,
                    "artifact": event.artifact,
                    "artifact_operation": event.artifact_operation,
                    "expression": event.state.expression,
                    "test": event.state.last_test,
                }
                for event in workflow.events
            ],
            "request_grounding": (
                workflow.request_grounding_correct / len(workflow.plan)
            ),
            "artifact_grounding": (
                workflow.artifact_grounding_correct / len(workflow.events)
            ),
            "final_expression": workflow.final_state.expression,
            "final_test": workflow.final_state.last_test,
            "report": workflow.final_state.report,
            "tool_actions": 5,
            "rollback_actions": 1,
            "shared_internal_conversions": 0,
            "separate_internal_conversions": (
                workflow.conversion_boundaries_separate
            ),
            "separate_serialized_copy_bits": (
                workflow.serialized_copy_bits_separate
            ),
        },
        "limitations": [
            "effect traces still identify whether an event wrote, observed, restored, or emitted",
            "near paraphrases share subword evidence with training",
            "distant lexical shifts remain mostly unresolved without new interaction evidence",
            "the workflow is a synthetic one-function repair rather than a real repository",
            "the feature learner does not yet discover morphology, syntax, or world knowledge",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    grounding = payload["raw_grounding"]
    comparison = payload["shared_vs_separated"]
    calibration = payload["residual_calibration"]
    workflow = payload["workflow"]
    lines = [
        "# Phase 9a results: raw event grounding and shared repair workflow",
        "",
        "Persistent template IDs are removed. Raw Japanese, AST-like text, test output,",
        "and tool traces are mapped into one SET / VERIFY / RETRACT / EMIT event program.",
        "",
        "## Raw grounding",
        "",
        f"- training examples: **{payload['training']['examples']}**",
        f"- selected feature rules: **{payload['training']['selected_rules']}**",
        f"- shared grounding program: **{payload['training']['description_bits']} bits**",
        f"- exact-surface near-heldout: **{grounding['exact_surface_accuracy']:.1%}**",
        f"- sparse raw grounder near-heldout: **{grounding['shared_grounder_accuracy']:.1%}**",
        f"- distant lexical shift: **{grounding['distant_lexical_shift_accuracy']:.1%}**",
        "",
        "## Shared versus domain-separated grounding",
        "",
        "| model | description bits | near-heldout |",
        "|---|---:|---:|",
        f"| shared event grounding | {comparison['shared_description_bits']:,} | {comparison['shared_near_accuracy']:.1%} |",
        f"| four domain models | {comparison['separated_description_bits']:,} | {comparison['separated_near_accuracy']:.1%} |",
        "",
        f"The separated description is **{comparison['description_ratio']:.2f}x** the shared description.",
        "",
        "## Residual lexical calibration",
        "",
        f"- calibration interactions: **{calibration['calibration_examples']}**",
        f"- follow-up before calibration: **{calibration['accuracy_before']:.1%}**",
        f"- follow-up after calibration: **{calibration['accuracy_after']:.1%}**",
        f"- added program: **{calibration['added_description_bits']} bits**",
        "",
        "The added lexical program is not automatically permanent. It must repay its bits",
        "through future avoided errors or avoided external queries.",
        "",
        "## End-to-end repair workflow",
        "",
        f"- induced plan: `{workflow['plan']}`",
        f"- request-clause grounding: **{workflow['request_grounding']:.1%}**",
        f"- generated AST/test/tool/report grounding: **{workflow['artifact_grounding']:.1%}**",
        f"- final expression: `{workflow['final_expression']}`",
        f"- final test: **{workflow['final_test']}**",
        f"- rollback actions: **{workflow['rollback_actions']}**",
        f"- shared internal representation conversions: **{workflow['shared_internal_conversions']}**",
        f"- domain-separated conversions: **{workflow['separate_internal_conversions']}**",
        f"- concrete JSON hand-off copies: **{workflow['separate_serialized_copy_bits']:,} bits/workflow**",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["limitations"])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run()
    root = Path(__file__).resolve().parents[2]
    results = root / "results"
    results.mkdir(exist_ok=True)
    (results / "phase9a.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (results / "phase9a.md").write_text(
        render_markdown(payload),
        encoding="utf-8",
    )
    print(render_markdown(payload))


if __name__ == "__main__":
    main()
